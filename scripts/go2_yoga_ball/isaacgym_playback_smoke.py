#!/usr/bin/env python3
"""Go2-correct Isaac Gym playback smoke for a trained yoga-ball policy."""

from __future__ import annotations

import argparse
import csv
import json
import pickle
from pathlib import Path
import sys
import time

import isaacgym  # noqa: F401
import imageio
import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[2]
DREUREKA = ROOT / "thirdparties" / "DrEureka"
if str(DREUREKA) not in sys.path:
    sys.path.insert(0, str(DREUREKA))
if str(DREUREKA / "globe_walking") not in sys.path:
    sys.path.insert(0, str(DREUREKA / "globe_walking"))

from globe_walking.go1_gym.envs.base.legged_robot_config import Cfg  # noqa: E402
from globe_walking.go1_gym.envs.go2.go2_config import config_go2  # noqa: E402
from globe_walking.go1_gym.envs.go1.velocity_tracking import VelocityTrackingEasyEnv  # noqa: E402
from globe_walking.go1_gym.envs.wrappers.history_wrapper import HistoryWrapper  # noqa: E402


POLICY_JOINT_ORDER = [
    "FL_hip_joint",
    "FL_thigh_joint",
    "FL_calf_joint",
    "FR_hip_joint",
    "FR_thigh_joint",
    "FR_calf_joint",
    "RL_hip_joint",
    "RL_thigh_joint",
    "RL_calf_joint",
    "RR_hip_joint",
    "RR_thigh_joint",
    "RR_calf_joint",
]


def class_to_dict(obj):
    if isinstance(obj, dict):
        return {key: class_to_dict(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [class_to_dict(value) for value in obj]
    if not hasattr(obj, "__dict__"):
        return obj
    result = {}
    for key in dir(obj):
        if key.startswith("_") or key == "terrain":
            continue
        result[key] = class_to_dict(getattr(obj, key))
    return result


def set_cfg_recursive(target, loaded: dict) -> None:
    for key, value in loaded.items():
        if not hasattr(target, key):
            continue
        current = getattr(target, key)
        if isinstance(value, dict) and hasattr(current, "__dict__"):
            set_cfg_recursive(current, value)
        else:
            setattr(target, key, value)


def midpoint_domain_rand(cfg) -> None:
    cfg.domain_rand.randomize = False
    for key in dir(cfg.domain_rand):
        if key.startswith("_"):
            continue
        value = getattr(cfg.domain_rand, key)
        if isinstance(value, list) and len(value) == 2 and all(isinstance(x, (int, float)) for x in value):
            midpoint = float(value[0] + value[1]) / 2.0
            setattr(cfg.domain_rand, key, [midpoint, midpoint])


def load_saved_cfg(run_dir: Path) -> dict:
    with (run_dir / "parameters.pkl").open("rb") as f:
        payload = pickle.load(f)
    return payload["Cfg"]


def load_policy(run_dir: Path, device: str):
    body = torch.jit.load(str(run_dir / "checkpoints" / "body_latest.jit"), map_location=device)
    adaptation_module = torch.jit.load(str(run_dir / "checkpoints" / "adaptation_module_latest.jit"), map_location=device)
    body.eval()
    adaptation_module.eval()

    def policy(obs):
        history = obs["obs_history"].to(device)
        latent = adaptation_module.forward(history)
        return body.forward(torch.cat((history, latent), dim=-1))

    return policy


def tensor_stats(values: torch.Tensor) -> dict:
    values = values.detach().float().cpu()
    return {
        "min": float(values.min().item()),
        "mean": float(values.mean().item()),
        "max": float(values.max().item()),
    }


def frame_to_rgb(frame: np.ndarray) -> np.ndarray:
    image = np.asarray(frame)
    if image.ndim != 3 or image.shape[-1] < 3:
        raise ValueError(f"unexpected rendered frame shape: {image.shape}")
    return np.ascontiguousarray(image[:, :, :3].astype(np.uint8))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--num-envs", type=int, default=64)
    parser.add_argument("--duration-s", type=float, default=8.0)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--record-video", action="store_true")
    parser.add_argument("--video-fps", type=int, default=25)
    parser.add_argument("--visual-only-plane", action="store_true")
    parser.add_argument("--preserve-domain-rand", action="store_true")
    parser.add_argument("--use-saved-contract", action="store_true")
    args = parser.parse_args()

    run_dir = Path(args.run)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    saved_cfg = load_saved_cfg(run_dir)
    Cfg.env = Cfg.env_mini
    Cfg.sensors = Cfg.sensors_mini
    Cfg.terrain = Cfg.terrain_mini
    Cfg.domain_rand = Cfg.domain_rand_off
    Cfg.sim.physx = Cfg.sim.physx_mini
    if not args.use_saved_contract:
        config_go2(Cfg)
    set_cfg_recursive(Cfg, saved_cfg)
    if not args.use_saved_contract:
        Cfg.robot.name = "go2"
    if args.visual_only_plane:
        Cfg.env.num_observations = int(saved_cfg["env"]["num_observations"])
        Cfg.env.num_observation_history = int(saved_cfg["env"]["num_observation_history"])
        Cfg.env.num_privileged_obs = int(saved_cfg["env"]["num_privileged_obs"])

    Cfg.env.num_envs = int(args.num_envs)
    Cfg.env.record_video = bool(args.record_video)
    Cfg.env.num_recording_envs = 1 if args.record_video else 0
    Cfg.env.recording_width_px = 640
    Cfg.env.recording_height_px = 480
    Cfg.terrain.num_rows = 4
    Cfg.terrain.num_cols = 4
    Cfg.terrain.border_size = 0
    Cfg.terrain.num_border_boxes = 0
    Cfg.terrain.center_robots = True
    Cfg.terrain.center_span = 1
    Cfg.terrain.teleport_robots = True
    if args.visual_only_plane:
        Cfg.terrain.mesh_type = "plane"
        Cfg.terrain.teleport_robots = False
    Cfg.multi_gpu = False
    if not args.preserve_domain_rand:
        midpoint_domain_rand(Cfg)

    contract = {
        "run": str(run_dir),
        "robot_name": Cfg.robot.name,
        "control_type": Cfg.control.control_type,
        "asset_file": Cfg.asset.file,
        "action_scale": Cfg.control.action_scale,
        "hip_scale_reduction": Cfg.control.hip_scale_reduction,
        "stiffness": dict(Cfg.control.stiffness),
        "damping": dict(Cfg.control.damping),
        "num_envs": Cfg.env.num_envs,
        "num_observations": Cfg.env.num_observations,
        "num_observation_history": Cfg.env.num_observation_history,
        "domain_rand_randomize": bool(Cfg.domain_rand.randomize),
        "domain_rand_mode": "saved_ranges" if args.preserve_domain_rand else "midpoint_deterministic",
        "ball_radius_range": list(Cfg.domain_rand.ball_radius_range),
        "ball_mass_range": list(Cfg.domain_rand.ball_mass_range),
        "playback_contract_mode": "saved" if args.use_saved_contract else "go2_pd",
    }
    if not args.use_saved_contract and (Cfg.robot.name != "go2" or Cfg.control.control_type != "P"):
        (out_dir / "summary.json").write_text(json.dumps({"ok": False, "contract": contract}, indent=2) + "\n")
        raise SystemExit(f"not a Go2 PD run: {contract}")

    env = VelocityTrackingEasyEnv(sim_device=args.device, headless=True, cfg=Cfg)
    wrapped = HistoryWrapper(env)
    policy = load_policy(run_dir, args.device)
    obs = wrapped.reset()

    dt = float(env.dt)
    steps = int(args.duration_s / dt)
    csv_path = out_dir / "playback.csv"
    fieldnames = [
        "step",
        "sim_time_s",
        "wall_time_s",
        "reset_count",
        "alive_count",
        "reward_mean",
        "base_z_min",
        "base_z_mean",
        "action_abs_mean",
        "action_abs_max",
        "torque_abs_mean",
        "torque_abs_max",
        "joint_limit_rows",
        "action_delta_abs_mean",
        "action_delta_abs_max",
    ]
    reset_counts = torch.zeros(env.num_envs, device=env.device)
    joint_limit_rows = 0
    start_wall = time.time()
    action_abs_max = 0.0
    torque_abs_max = 0.0
    torque_limit_hits = 0
    base_z_min = float("inf")
    reward_means = []
    action_delta_abs_max = 0.0
    action_delta_abs_means = []
    prev_actions: torch.Tensor | None = None
    video_path = out_dir / "isaacgym_playback.mp4"
    video_writer = imageio.get_writer(str(video_path), fps=args.video_fps) if args.record_video else None

    try:
      with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for step in range(steps):
            with torch.no_grad():
                actions = policy(obs)
                obs, reward, done, _ = wrapped.step(actions)
            if args.record_video:
                frame = env.render(mode="rgb_array")
                video_writer.append_data(frame_to_rgb(frame))
            reset_counts += done.to(env.device).float()
            limits_low = env.dof_pos_limits[:, 0].unsqueeze(0)
            limits_high = env.dof_pos_limits[:, 1].unsqueeze(0)
            violated = torch.logical_or(env.dof_pos < limits_low, env.dof_pos > limits_high)
            joint_limit_rows += int(torch.any(violated, dim=1).sum().item())
            action_abs = torch.abs(actions)
            if prev_actions is None:
                action_delta_abs = torch.zeros_like(action_abs)
            else:
                action_delta_abs = torch.abs(actions - prev_actions)
            prev_actions = actions.detach().clone()
            torque_abs = torch.abs(env.torques[:, : env.num_actuated_dof])
            torque_limits = env.torque_limits[: env.num_actuated_dof].unsqueeze(0)
            torque_limit_hits += int(torch.sum(torque_abs >= torque_limits - 1e-5).item())
            base_z = env.base_pos[:, 2]
            action_abs_max = max(action_abs_max, float(action_abs.max().item()))
            action_delta_abs_max = max(action_delta_abs_max, float(action_delta_abs.max().item()))
            action_delta_abs_means.append(float(action_delta_abs.mean().item()))
            torque_abs_max = max(torque_abs_max, float(torque_abs.max().item()))
            base_z_min = min(base_z_min, float(base_z.min().item()))
            reward_means.append(float(reward.mean().item()))
            if step % 25 == 0 or step == steps - 1:
                writer.writerow(
                    {
                        "step": step,
                        "sim_time_s": f"{step * dt:.6f}",
                        "wall_time_s": f"{time.time() - start_wall:.6f}",
                        "reset_count": int(reset_counts.sum().item()),
                        "alive_count": int((reset_counts == 0).sum().item()),
                        "reward_mean": f"{float(reward.mean().item()):.9f}",
                        "base_z_min": f"{float(base_z.min().item()):.9f}",
                        "base_z_mean": f"{float(base_z.mean().item()):.9f}",
                        "action_abs_mean": f"{float(action_abs.mean().item()):.9f}",
                        "action_abs_max": f"{float(action_abs.max().item()):.9f}",
                        "torque_abs_mean": f"{float(torque_abs.mean().item()):.9f}",
                        "torque_abs_max": f"{float(torque_abs.max().item()):.9f}",
                        "joint_limit_rows": joint_limit_rows,
                        "action_delta_abs_mean": f"{float(action_delta_abs.mean().item()):.9f}",
                        "action_delta_abs_max": f"{float(action_delta_abs.max().item()):.9f}",
                    }
                )
                f.flush()
    finally:
        if video_writer is not None:
            video_writer.close()

    summary = {
        "ok": bool(int((reset_counts == 0).sum().item()) > 0),
        "contract": contract,
        "dof_names": list(env.dof_names),
        "num_steps": steps,
        "sim_dt_s": dt,
        "sim_duration_s": steps * dt,
        "wall_duration_s": time.time() - start_wall,
        "survived_envs": int((reset_counts == 0).sum().item()),
        "num_envs": int(env.num_envs),
        "reset_count_total": int(reset_counts.sum().item()),
        "base_z": {"min": base_z_min},
        "reward_mean_over_steps": float(np.mean(reward_means)) if reward_means else None,
        "action_abs_max": action_abs_max,
        "action_delta_abs_max": action_delta_abs_max,
        "action_delta_abs_mean_over_steps": float(np.mean(action_delta_abs_means)) if action_delta_abs_means else None,
        "torque_abs_max": torque_abs_max,
        "torque_limit_hits": torque_limit_hits,
        "torque_limit_values": [float(x) for x in env.torque_limits[: env.num_actuated_dof].detach().cpu().tolist()],
        "joint_limit_rows": joint_limit_rows,
        "csv": str(csv_path),
        "video": str(video_path) if args.record_video else None,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Go2 Isaac Gym Playback Smoke",
        "",
        f"- OK: `{summary['ok']}`",
        f"- Run: `{run_dir}`",
        f"- Robot/control: `{Cfg.robot.name}` / `{Cfg.control.control_type}`",
        f"- Playback contract mode: `{contract['playback_contract_mode']}`",
        f"- Survived envs without reset: `{summary['survived_envs']}/{summary['num_envs']}`",
        f"- Total resets: `{summary['reset_count_total']}`",
        f"- Min base z: `{base_z_min:.6f}`",
        f"- Max action abs: `{action_abs_max:.6f}`",
        f"- Max action delta abs: `{action_delta_abs_max:.6f}`",
        f"- Max torque abs: `{torque_abs_max:.6f}`",
        f"- Joint-limit env-row count: `{joint_limit_rows}`",
        f"- CSV: `{csv_path}`",
        "",
        "This playback intentionally bypasses `scripts/play.py` because that file unconditionally forces `Cfg.control.control_type = \"actuator_net\"`, which is wrong for this Go2 PD checkpoint.",
    ]
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
