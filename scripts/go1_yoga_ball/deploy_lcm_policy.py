#!/usr/bin/env python3
"""DrEureka deployment-compatible policy loop for Go1 yoga-ball Sim2Sim."""

from __future__ import annotations

import argparse
import csv
import copy
import pickle
from pathlib import Path
import sys
import threading
import time

import lcm
import torch


ROOT = Path(__file__).resolve().parents[2]
DREUREKA = ROOT / "thirdparties" / "DrEureka"
if str(DREUREKA / "globe_walking") not in sys.path:
    sys.path.insert(0, str(DREUREKA / "globe_walking"))

from go1_gym_deploy.envs.history_wrapper import HistoryWrapper  # noqa: E402
from go1_gym_deploy.envs.lcm_agent import LCMAgent  # noqa: E402
from go1_gym_deploy.utils.cheetah_state_estimator import StateEstimator  # noqa: E402
from go1_gym_deploy.utils.command_profile import RCControllerProfile  # noqa: E402


EVENT_FIELDS = ["event", "monotonic_s", "wall_time_s", "sim_time_s", "support_active", "detail"]


class ZeroClockAgent:
    def __init__(self, agent):
        self.agent = agent

    def __getattr__(self, name):
        return getattr(self.agent, name)

    def _zero_clock(self):
        self.agent.clock_inputs[:] = 0
        self.agent.gait_indices[:] = 0

    def reset(self):
        obs = self.agent.reset()
        self._zero_clock()
        return obs

    def step(self, action):
        obs, rew, done, info = self.agent.step(action)
        self._zero_clock()
        obs = self.agent.get_obs()
        if info is not None:
            info["clock_inputs"] = self.agent.clock_inputs
        return obs, rew, done, info


def append_event(path: Path, event: str, start_mono: float, *, detail: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists()
    elapsed = time.monotonic() - start_mono
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EVENT_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(
            {
                "event": event,
                "monotonic_s": f"{elapsed:.6f}",
                "wall_time_s": f"{time.time():.6f}",
                "sim_time_s": "",
                "support_active": "",
                "detail": detail,
            }
        )


def load_policy(run_dir: Path):
    body = torch.jit.load(str(run_dir / "checkpoints" / "body_latest.jit"), map_location="cpu")
    adaptation_module = torch.jit.load(
        str(run_dir / "checkpoints" / "adaptation_module_latest.jit"),
        map_location="cpu",
    )

    def policy(obs, info):
        latent = adaptation_module.forward(obs["obs_history"].to("cpu"))
        action = body.forward(torch.cat((obs["obs_history"].to("cpu"), latent), dim=-1))
        info["latent"] = latent
        return action

    return policy


def sync_go2_deploy_cfg(cfg: dict) -> dict:
    cfg = copy.deepcopy(cfg)
    if cfg.get("robot", {}).get("name") != "go2":
        return cfg
    cfg.setdefault("init_state", {})["default_joint_angles"] = {
        "FL_hip_joint": 0.1,
        "FL_thigh_joint": 0.8,
        "FL_calf_joint": -1.5,
        "FR_hip_joint": -0.1,
        "FR_thigh_joint": 0.8,
        "FR_calf_joint": -1.5,
        "RL_hip_joint": 0.1,
        "RL_thigh_joint": 1.0,
        "RL_calf_joint": -1.5,
        "RR_hip_joint": -0.1,
        "RR_thigh_joint": 1.0,
        "RR_calf_joint": -1.5,
    }
    cfg.setdefault("control", {}).update(
        {
            "control_type": "P",
            "stiffness": {"joint": 20.0},
            "damping": {"joint": 0.5},
            "action_scale": 0.25,
            "hip_scale_reduction": 1.0,
            "decimation": 4,
        }
    )
    return cfg


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--duration-s", type=float, default=8.0)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--event-log", required=True)
    parser.add_argument("--lcm-url", default="udpm://239.255.76.67:7667?ttl=255")
    parser.add_argument("--startup-timeout-s", type=float, default=5.0)
    parser.add_argument("--zero-clock", action="store_true")
    args = parser.parse_args()

    run_dir = Path(args.run)
    out_dir = Path(args.out_dir)
    event_log = Path(args.event_log)
    out_dir.mkdir(parents=True, exist_ok=True)
    start_mono = time.monotonic()
    append_event(event_log, "POLICY_START", start_mono, detail=f"run={run_dir}")

    lc = lcm.LCM(args.lcm_url)
    se = StateEstimator(lc, use_cameras=False)
    se.run_thread = threading.Thread(target=se.poll, daemon=True)
    se.run_thread.start()

    wait_start = time.monotonic()
    while not se.received_first_legdata:
        if time.monotonic() - wait_start > args.startup_timeout_s:
            append_event(event_log, "POLICY_FAILED", start_mono, detail="timeout waiting for leg_control_data")
            return 2
        time.sleep(0.01)

    with (run_dir / "parameters.pkl").open("rb") as f:
        cfg = pickle.load(f)["Cfg"]
    cfg = sync_go2_deploy_cfg(cfg)

    control_dt = 0.02
    command_profile = RCControllerProfile(
        dt=control_dt,
        state_estimator=se,
        x_scale=3.5,
        y_scale=0.6,
        yaw_scale=5.0,
    )
    base_agent = LCMAgent(cfg, se, command_profile)
    if args.zero_clock:
        base_agent = ZeroClockAgent(base_agent)
    agent = HistoryWrapper(base_agent)
    policy = load_policy(run_dir)
    obs = agent.reset()

    timing_path = out_dir / "policy_timing.csv"
    fieldnames = [
        "step",
        "monotonic_s",
        "wall_time_s",
        "policy_time_s",
        "inference_latency_s",
        "loop_period_s",
        "action_max_abs",
    ]
    with timing_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        append_event(event_log, "POLICY_OBS_READY", start_mono)
        last_loop = time.monotonic()
        step = 0
        while time.monotonic() - start_mono < args.duration_s:
            policy_info = {}
            infer_start = time.monotonic()
            with torch.no_grad():
                action = policy(obs, policy_info)
            infer_elapsed = time.monotonic() - infer_start
            obs, _, _, _ = agent.step(action)
            now = time.monotonic()
            if step == 0:
                append_event(event_log, "CONTROL_ACTIVE", start_mono)
            writer.writerow(
                {
                    "step": step,
                    "monotonic_s": f"{now - start_mono:.6f}",
                    "wall_time_s": f"{time.time():.6f}",
                    "policy_time_s": f"{step * control_dt:.6f}",
                    "inference_latency_s": f"{infer_elapsed:.9f}",
                    "loop_period_s": f"{now - last_loop:.9f}",
                    "action_max_abs": f"{float(torch.max(torch.abs(action)).item()):.9f}",
                }
            )
            f.flush()
            last_loop = now
            step += 1

    append_event(event_log, "POLICY_STOP", start_mono, detail=f"steps={step}")
    se.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
