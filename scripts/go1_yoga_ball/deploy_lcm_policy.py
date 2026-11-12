#!/usr/bin/env python3
"""DrEureka deployment-compatible policy loop for Go1 yoga-ball Sim2Sim."""

from __future__ import annotations

import argparse
import csv
import copy
import json
import math
import pickle
from pathlib import Path
import sys
import threading
import time
from types import MethodType
from typing import Any

import cv2
import lcm
import numpy as np
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
    write_header = (not path.exists()) or path.stat().st_size == 0
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


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if p <= 0:
        return ordered[0]
    if p >= 100:
        return ordered[-1]
    idx = (len(ordered) - 1) * (p / 100.0)
    lo = math.floor(idx)
    hi = math.ceil(idx)
    if lo == hi:
        return ordered[lo]
    weight = idx - lo
    return ordered[lo] * (1.0 - weight) + ordered[hi] * weight


def summarize_series(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "avg": None, "min": None, "p50": None, "p95": None, "p99": None, "max": None}
    return {
        "count": len(values),
        "avg": sum(values) / len(values),
        "min": min(values),
        "p50": percentile(values, 50.0),
        "p95": percentile(values, 95.0),
        "p99": percentile(values, 99.0),
        "max": max(values),
    }


def summarize_numeric_field(records: list[dict[str, Any]], key: str) -> dict[str, float | int | None]:
    values = [float(record[key]) for record in records if record.get(key) is not None]
    return summarize_series(values)


class CallbackDiagnostics:
    def __init__(self, *, start_mono: float, event_log: Path) -> None:
        self.start_mono = start_mono
        self.event_log = event_log
        self.lock = threading.Lock()
        self.records: list[dict[str, Any]] = []
        self.channels: dict[str, dict[str, Any]] = {}
        for name in ("leg_control_data", "state_estimator_data", "rc_command"):
            self.channels[name] = {
                "count": 0,
                "last_arrival": None,
                "durations": [],
                "intervals": [],
                "count_since_step": 0,
                "busy_since_step": 0.0,
                "first_event_written": False,
            }

    def wrap(self, name: str, fn):
        def wrapped(channel: str, data: bytes) -> None:
            arrival = time.monotonic()
            payload_bytes = len(data)
            with self.lock:
                state = self.channels[name]
                interval = None if state["last_arrival"] is None else arrival - state["last_arrival"]
                state["last_arrival"] = arrival
                if interval is not None:
                    state["intervals"].append(interval)
                first_event_needed = not state["first_event_written"]
                if first_event_needed:
                    state["first_event_written"] = True
            if first_event_needed:
                append_event(
                    self.event_log,
                    f"POLICY_FIRST_{name.upper()}",
                    self.start_mono,
                    detail=f"payload_bytes={payload_bytes}",
                )

            error: BaseException | None = None
            try:
                fn(channel, data)
            except BaseException as exc:  # noqa: BLE001
                error = exc
                raise
            finally:
                end = time.monotonic()
                callback_s = end - arrival
                with self.lock:
                    state = self.channels[name]
                    state["count"] += 1
                    state["count_since_step"] += 1
                    state["busy_since_step"] += callback_s
                    state["durations"].append(callback_s)
                    state["last_arrival"] = arrival
                    state_count = state["count"]
                    self.records.append(
                        {
                            "channel": name,
                            "count": state_count,
                            "monotonic_s": arrival - self.start_mono,
                            "inter_arrival_s": interval,
                            "callback_s": callback_s,
                            "payload_bytes": payload_bytes,
                            "raised": error is not None,
                        }
                    )

        return wrapped

    def snapshot_step(self) -> dict[str, float | int | None]:
        now = time.monotonic()
        snapshot: dict[str, float | int | None] = {}
        with self.lock:
            for name, state in self.channels.items():
                snapshot[f"{name}_callbacks_since_step"] = int(state["count_since_step"])
                snapshot[f"{name}_callback_busy_s"] = float(state["busy_since_step"])
                snapshot[f"{name}_age_s"] = None if state["last_arrival"] is None else now - state["last_arrival"]
                state["count_since_step"] = 0
                state["busy_since_step"] = 0.0
        return snapshot

    def write_files(self, out_dir: Path) -> None:
        callbacks_path = out_dir / "policy_callbacks.csv"
        with callbacks_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["channel", "count", "monotonic_s", "inter_arrival_s", "callback_s", "payload_bytes", "raised"],
            )
            writer.writeheader()
            with self.lock:
                for record in self.records:
                    writer.writerow(
                        {
                            "channel": record["channel"],
                            "count": record["count"],
                            "monotonic_s": f"{record['monotonic_s']:.9f}",
                            "inter_arrival_s": "" if record["inter_arrival_s"] is None else f"{record['inter_arrival_s']:.9f}",
                            "callback_s": f"{record['callback_s']:.9f}",
                            "payload_bytes": record["payload_bytes"],
                            "raised": int(bool(record["raised"])),
                        }
                    )

        summary: dict[str, Any] = {"callbacks_csv": str(callbacks_path)}
        with self.lock:
            for name, state in self.channels.items():
                summary[name] = {
                    "count": state["count"],
                    "interval_s": summarize_series(state["intervals"]),
                    "callback_s": summarize_series(state["durations"]),
                }
        (out_dir / "policy_callback_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


class ObsDiagnostics:
    def __init__(self) -> None:
        self.active = False
        self.current: dict[str, float | int] = {}
        self.last_snapshot: dict[str, float | int] = {}

    def start(self) -> None:
        self.active = True
        self.current = {}

    def finish(self, total_s: float) -> None:
        self.current["get_obs_total_s"] = total_s
        self.last_snapshot = dict(self.current)
        self.active = False

    def record(self, name: str, elapsed_s: float, result: Any | None = None) -> None:
        if not self.active:
            return
        self.current[name] = self.current.get(name, 0.0) + elapsed_s
        if name == "body_ang_vel_s" and result is not None:
            try:
                self.current["body_ang_vel_nonfinite"] = int(np.any(~np.isfinite(result)))
            except Exception:  # noqa: BLE001
                self.current["body_ang_vel_nonfinite"] = 0


class PolicyLoopDiagnostics:
    def __init__(self) -> None:
        self.last_publish_action_s = 0.0
        self.last_get_obs_snapshot: dict[str, float | int] = {}
        self.step_records: list[dict[str, Any]] = []

    def record_publish_action(self, elapsed_s: float) -> None:
        self.last_publish_action_s = elapsed_s

    def record_get_obs(self, snapshot: dict[str, float | int]) -> None:
        self.last_get_obs_snapshot = dict(snapshot)

    def record_step(self, record: dict[str, Any]) -> None:
        self.step_records.append(record)

    def write_summary(self, out_dir: Path) -> None:
        summary = {
            "step_count": len(self.step_records),
            "history_wrapper_step_s": summarize_numeric_field(self.step_records, "history_wrapper_step_s"),
            "agent_step_total_s": summarize_numeric_field(self.step_records, "agent_step_total_s"),
            "publish_action_s": summarize_numeric_field(self.step_records, "publish_action_s"),
            "requested_sleep_s": summarize_numeric_field(self.step_records, "requested_sleep_s"),
            "actual_sleep_s": summarize_numeric_field(self.step_records, "actual_sleep_s"),
            "get_obs_total_s": summarize_numeric_field(self.step_records, "get_obs_total_s"),
            "policy_inference_s": summarize_numeric_field(self.step_records, "inference_latency_s"),
            "policy_adaptation_s": summarize_numeric_field(self.step_records, "adaptation_latency_s"),
            "policy_body_s": summarize_numeric_field(self.step_records, "body_latency_s"),
            "policy_obs_copy_adapt_s": summarize_numeric_field(self.step_records, "obs_history_copy_adapt_s"),
            "policy_obs_copy_body_s": summarize_numeric_field(self.step_records, "obs_history_copy_body_s"),
            "policy_concat_s": summarize_numeric_field(self.step_records, "policy_concat_s"),
            "body_ang_vel_nonfinite_steps": sum(int(record.get("body_ang_vel_nonfinite", 0)) for record in self.step_records),
        }
        (out_dir / "policy_diagnostics.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def load_policy(run_dir: Path):
    body = torch.jit.load(str(run_dir / "checkpoints" / "body_latest.jit"), map_location="cpu")
    adaptation_module = torch.jit.load(
        str(run_dir / "checkpoints" / "adaptation_module_latest.jit"),
        map_location="cpu",
    )

    def policy(obs, info):
        copy_adapt_start = time.monotonic()
        obs_history_adapt = obs["obs_history"].to("cpu")
        copy_adapt_s = time.monotonic() - copy_adapt_start

        adaptation_start = time.monotonic()
        latent = adaptation_module.forward(obs_history_adapt)
        adaptation_s = time.monotonic() - adaptation_start

        copy_body_start = time.monotonic()
        obs_history_body = obs["obs_history"].to("cpu")
        copy_body_s = time.monotonic() - copy_body_start

        concat_start = time.monotonic()
        body_input = torch.cat((obs_history_body, latent), dim=-1)
        concat_s = time.monotonic() - concat_start

        body_start = time.monotonic()
        action = body.forward(body_input)
        body_s = time.monotonic() - body_start

        info["latent"] = latent
        info["policy_timing"] = {
            "obs_history_copy_adapt_s": copy_adapt_s,
            "adaptation_latency_s": adaptation_s,
            "obs_history_copy_body_s": copy_body_s,
            "policy_concat_s": concat_s,
            "body_latency_s": body_s,
        }
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


def instrument_state_estimator(se: StateEstimator, callback_diag: CallbackDiagnostics) -> None:
    orig_imu_cb = se._imu_cb
    orig_legdata_cb = se._legdata_cb
    orig_rc_cb = se._rc_command_cb

    se.lc.unsubscribe(se.imu_subscription)
    se.lc.unsubscribe(se.legdata_state_subscription)
    se.lc.unsubscribe(se.rc_command_subscription)

    se.imu_subscription = se.lc.subscribe("state_estimator_data", callback_diag.wrap("state_estimator_data", orig_imu_cb))
    se.legdata_state_subscription = se.lc.subscribe("leg_control_data", callback_diag.wrap("leg_control_data", orig_legdata_cb))
    se.rc_command_subscription = se.lc.subscribe("rc_command", callback_diag.wrap("rc_command", orig_rc_cb))


def instrument_state_getters(se: StateEstimator, obs_diag: ObsDiagnostics, command_profile: RCControllerProfile) -> None:
    def wrap_method(obj: Any, name: str, metric_name: str):
        original = getattr(obj, name)

        def wrapped(*args, **kwargs):
            start = time.monotonic()
            result = original(*args, **kwargs)
            obs_diag.record(metric_name, time.monotonic() - start, result=result)
            return result

        setattr(obj, name, wrapped)

    wrap_method(command_profile, "get_command", "get_command_s")
    wrap_method(se, "get_gravity_vector", "gravity_s")
    wrap_method(se, "get_dof_pos", "dof_pos_s")
    wrap_method(se, "get_dof_vel", "dof_vel_s")
    wrap_method(se, "get_body_linear_vel", "body_lin_vel_s")
    wrap_method(se, "get_body_angular_vel", "body_ang_vel_s")
    wrap_method(se, "get_yaw", "yaw_s")
    wrap_method(se, "get_contact_state", "contact_state_s")


def instrument_agent(raw_agent: LCMAgent, obs_diag: ObsDiagnostics, callback_diag: CallbackDiagnostics, loop_diag: PolicyLoopDiagnostics) -> None:
    original_publish_action = raw_agent.publish_action
    original_get_obs = raw_agent.get_obs

    def publish_action_with_timing(self, action, hard_reset=False):
        start = time.monotonic()
        result = original_publish_action(action, hard_reset=hard_reset)
        loop_diag.record_publish_action(time.monotonic() - start)
        return result

    def get_obs_with_timing(self):
        obs_diag.start()
        start = time.monotonic()
        result = original_get_obs()
        obs_diag.finish(time.monotonic() - start)
        loop_diag.record_get_obs(obs_diag.last_snapshot)
        return result

    def step_with_timing(self, actions, hard_reset=False):
        step_start = time.monotonic()
        clip_actions = self.cfg["normalization"]["clip_actions"]
        self.last_actions = self.actions[:]
        clip_start = time.monotonic()
        self.actions = torch.clip(actions[0:1, :], -clip_actions, clip_actions)
        clip_s = time.monotonic() - clip_start

        self.publish_action(self.actions, hard_reset=hard_reset)
        publish_action_s = loop_diag.last_publish_action_s

        pre_sleep_work_s = time.time() - self.time
        requested_sleep_s = max(self.dt - pre_sleep_work_s, 0)
        sleep_start = time.monotonic()
        time.sleep(requested_sleep_s)
        actual_sleep_s = time.monotonic() - sleep_start

        reported_cycle_s = time.time() - self.time
        if self.timestep % 100 == 0:
            print(f"frq: {1 / reported_cycle_s} Hz")
        self.time = time.time()

        get_obs_start = time.monotonic()
        obs = self.get_obs()
        get_obs_wrapper_s = time.monotonic() - get_obs_start
        get_obs_metrics = dict(loop_diag.last_get_obs_snapshot)

        clock_start = time.monotonic()
        frequencies = self.commands[:, 4]
        phases = self.commands[:, 5]
        offsets = self.commands[:, 6]
        if self.num_commands == 8:
            bounds = 0
            durations = self.commands[:, 7]
        else:
            bounds = self.commands[:, 7]
            durations = self.commands[:, 8]
        self.gait_indices = torch.remainder(self.gait_indices + self.dt * frequencies, 1.0)

        if "pacing_offset" in self.cfg["commands"] and self.cfg["commands"]["pacing_offset"]:
            self.foot_indices = [self.gait_indices + phases + offsets + bounds,
                                 self.gait_indices + bounds,
                                 self.gait_indices + offsets,
                                 self.gait_indices + phases]
        else:
            self.foot_indices = [self.gait_indices + phases + offsets + bounds,
                                 self.gait_indices + offsets,
                                 self.gait_indices + bounds,
                                 self.gait_indices + phases]
        self.clock_inputs[:, 0] = torch.sin(2 * np.pi * self.foot_indices[0])
        self.clock_inputs[:, 1] = torch.sin(2 * np.pi * self.foot_indices[1])
        self.clock_inputs[:, 2] = torch.sin(2 * np.pi * self.foot_indices[2])
        self.clock_inputs[:, 3] = torch.sin(2 * np.pi * self.foot_indices[3])
        clock_update_s = time.monotonic() - clock_start

        image_start = time.monotonic()
        images = {'front': self.se.get_camera_front(),
                  'bottom': self.se.get_camera_bottom(),
                  'rear': self.se.get_camera_rear(),
                  'left': self.se.get_camera_left(),
                  'right': self.se.get_camera_right()
                  }
        downscale_factor = 2
        temporal_downscale = 3

        for k, v in images.items():
            if images[k] is not None:
                images[k] = cv2.resize(images[k], dsize=(images[k].shape[0]//downscale_factor, images[k].shape[1]//downscale_factor), interpolation=cv2.INTER_CUBIC)  # noqa: F821
            if self.timestep % temporal_downscale != 0:
                images[k] = None
        image_postprocess_s = time.monotonic() - image_start

        info_start = time.monotonic()
        infos = {"joint_pos": self.dof_pos[np.newaxis, :],
                 "joint_vel": self.dof_vel[np.newaxis, :],
                 "joint_pos_target": self.joint_pos_target[np.newaxis, :],
                 "joint_vel_target": self.joint_vel_target[np.newaxis, :],
                 "body_linear_vel": self.body_linear_vel[np.newaxis, :],
                 "body_angular_vel": self.body_angular_vel[np.newaxis, :],
                 "contact_state": self.contact_state[np.newaxis, :],
                 "clock_inputs": self.clock_inputs[np.newaxis, :],
                 "body_linear_vel_cmd": self.commands[:, 0:2],
                 "body_angular_vel_cmd": self.commands[:, 2:],
                 "privileged_obs": None,
                 "camera_image_front": images['front'],
                 "camera_image_bottom": images['bottom'],
                 "camera_image_rear": images['rear'],
                 "camera_image_left": images['left'],
                 "camera_image_right": images['right'],
                 }
        info_pack_s = time.monotonic() - info_start

        callback_snapshot = callback_diag.snapshot_step()

        agent_step_total_s = time.monotonic() - step_start
        self.last_step_timing = {
            "clip_actions_s": clip_s,
            "publish_action_s": publish_action_s,
            "pre_sleep_work_s": pre_sleep_work_s,
            "requested_sleep_s": requested_sleep_s,
            "actual_sleep_s": actual_sleep_s,
            "reported_cycle_s": reported_cycle_s,
            "get_obs_wrapper_s": get_obs_wrapper_s,
            "clock_update_s": clock_update_s,
            "image_postprocess_s": image_postprocess_s,
            "info_pack_s": info_pack_s,
            "agent_step_total_s": agent_step_total_s,
            **get_obs_metrics,
            **callback_snapshot,
        }

        self.timestep += 1
        return obs, None, None, infos

    raw_agent.publish_action = MethodType(publish_action_with_timing, raw_agent)
    raw_agent.get_obs = MethodType(get_obs_with_timing, raw_agent)
    raw_agent.step = MethodType(step_with_timing, raw_agent)


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

    callback_diag = CallbackDiagnostics(start_mono=start_mono, event_log=event_log)
    loop_diag = PolicyLoopDiagnostics()
    obs_diag = ObsDiagnostics()
    se = None
    exit_code = 0

    try:
        lc = lcm.LCM(args.lcm_url)
        se = StateEstimator(lc, use_cameras=False)
        instrument_state_estimator(se, callback_diag)
        se.run_thread = threading.Thread(target=se.poll, daemon=True)
        se.run_thread.start()

        wait_start = time.monotonic()
        while not se.received_first_legdata:
            if time.monotonic() - wait_start > args.startup_timeout_s:
                append_event(event_log, "POLICY_FAILED", start_mono, detail="timeout waiting for leg_control_data")
                exit_code = 2
                return exit_code
            time.sleep(0.01)

        with (run_dir / "parameters.pkl").open("rb") as f:
            cfg = pickle.load(f)["Cfg"]
        cfg = sync_go2_deploy_cfg(cfg)
        append_event(event_log, "POLICY_CFG_READY", start_mono, detail=f"robot={cfg.get('robot', {}).get('name', 'unknown')}")

        control_dt = 0.02
        command_profile = RCControllerProfile(
            dt=control_dt,
            state_estimator=se,
            x_scale=3.5,
            y_scale=0.6,
            yaw_scale=5.0,
        )
        raw_agent = LCMAgent(cfg, se, command_profile)
        instrument_state_getters(se, obs_diag, command_profile)
        instrument_agent(raw_agent, obs_diag, callback_diag, loop_diag)
        base_agent = ZeroClockAgent(raw_agent) if args.zero_clock else raw_agent
        agent = HistoryWrapper(base_agent)
        policy = load_policy(run_dir)
        obs = agent.reset()
        append_event(event_log, "POLICY_RESET_DONE", start_mono)

        timing_path = out_dir / "policy_timing.csv"
        fieldnames = [
            "step",
            "monotonic_s",
            "wall_time_s",
            "policy_time_s",
            "history_wrapper_step_s",
            "inference_latency_s",
            "obs_history_copy_adapt_s",
            "adaptation_latency_s",
            "obs_history_copy_body_s",
            "policy_concat_s",
            "body_latency_s",
            "action_max_abs",
            "agent_step_total_s",
            "clip_actions_s",
            "publish_action_s",
            "pre_sleep_work_s",
            "requested_sleep_s",
            "actual_sleep_s",
            "reported_cycle_s",
            "get_obs_wrapper_s",
            "get_obs_total_s",
            "get_command_s",
            "gravity_s",
            "dof_pos_s",
            "dof_vel_s",
            "body_lin_vel_s",
            "body_ang_vel_s",
            "body_ang_vel_nonfinite",
            "yaw_s",
            "contact_state_s",
            "clock_update_s",
            "image_postprocess_s",
            "info_pack_s",
            "leg_control_data_callbacks_since_step",
            "leg_control_data_callback_busy_s",
            "leg_control_data_age_s",
            "state_estimator_data_callbacks_since_step",
            "state_estimator_data_callback_busy_s",
            "state_estimator_data_age_s",
            "rc_command_callbacks_since_step",
            "rc_command_callback_busy_s",
            "rc_command_age_s",
            "loop_period_s",
        ]
        with timing_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            append_event(event_log, "POLICY_OBS_READY", start_mono)
            last_loop = time.monotonic()
            step = 0
            while time.monotonic() - start_mono < args.duration_s:
                policy_info: dict[str, Any] = {}
                infer_start = time.monotonic()
                with torch.no_grad():
                    action = policy(obs, policy_info)
                infer_elapsed = time.monotonic() - infer_start

                history_step_start = time.monotonic()
                obs, _, _, _ = agent.step(action)
                history_wrapper_step_s = time.monotonic() - history_step_start

                now = time.monotonic()
                if step == 0:
                    append_event(event_log, "CONTROL_ACTIVE", start_mono)

                step_record = {
                    "step": step,
                    "monotonic_s": now - start_mono,
                    "wall_time_s": time.time(),
                    "policy_time_s": step * control_dt,
                    "history_wrapper_step_s": history_wrapper_step_s,
                    "inference_latency_s": infer_elapsed,
                    "action_max_abs": float(torch.max(torch.abs(action)).item()),
                    "loop_period_s": now - last_loop,
                }
                for key, value in policy_info.get("policy_timing", {}).items():
                    step_record[key] = value
                step_record.update(getattr(raw_agent, "last_step_timing", {}))
                loop_diag.record_step(step_record)

                csv_row: dict[str, str | int] = {}
                for field in fieldnames:
                    value = step_record.get(field)
                    if value is None:
                        csv_row[field] = ""
                    elif isinstance(value, int):
                        csv_row[field] = value
                    else:
                        csv_row[field] = f"{float(value):.9f}"
                writer.writerow(csv_row)
                f.flush()
                last_loop = now
                step += 1

        append_event(event_log, "POLICY_STOP", start_mono, detail=f"steps={step}")
    finally:
        callback_diag.write_files(out_dir)
        loop_diag.write_summary(out_dir)
        if se is not None:
            for subscription in (se.imu_subscription, se.legdata_state_subscription, se.rc_command_subscription):
                try:
                    se.lc.unsubscribe(subscription)
                except Exception:  # noqa: BLE001
                    pass

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
