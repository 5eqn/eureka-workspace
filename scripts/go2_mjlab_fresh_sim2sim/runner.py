#!/usr/bin/env python3
"""Workflow runner for FRESH Go2 MJLab Sim2Sim."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

from common import (
  ACTION_SCALE,
  ARTIFACT_ROOT,
  CHECKPOINT,
  DEFAULT_JOINT_ANGLES,
  KD_BY_JOINT,
  KP_BY_JOINT,
  LOG_ROOT,
  MJLAB_CONTRACT_ORDER,
  RUN_LOG_DIR,
  ROOT,
  SCRIPT_ROOT,
  UNITREE_MOTOR_ORDER,
)


def rel(path: Path | str) -> str:
  p = Path(path)
  try:
    return str(p.resolve().relative_to(ROOT))
  except ValueError:
    return str(p)


def write_json(path: Path, data: dict[str, Any]) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_capture(cmd: list[str], *, cwd: Path = ROOT, timeout: int = 60) -> dict[str, Any]:
  try:
    out = subprocess.run(
      cmd,
      cwd=cwd,
      text=True,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      timeout=timeout,
    )
  except Exception as exc:  # noqa: BLE001 - evidence should capture any launch failure.
    return {"ok": False, "cmd": cmd, "error": repr(exc), "stdout": "", "stderr": ""}
  return {
    "ok": out.returncode == 0,
    "cmd": cmd,
    "returncode": out.returncode,
    "stdout": out.stdout,
    "stderr": out.stderr,
  }


def ensure_tree() -> None:
  ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
  LOG_ROOT.mkdir(parents=True, exist_ok=True)


def import_status() -> dict[str, Any]:
  mods = ["mujoco", "torch", "mjlab", "rsl_rl", "cyclonedds", "unitree_sdk2py", "cv2"]
  result: dict[str, Any] = {}
  for name in mods:
    try:
      mod = importlib.import_module(name)
      result[name] = {
        "ok": True,
        "file": getattr(mod, "__file__", ""),
        "version": getattr(mod, "__version__", ""),
      }
    except Exception as exc:  # noqa: BLE001
      result[name] = {"ok": False, "error": repr(exc)}
  return result


def preflight() -> None:
  ensure_tree()
  data = {
    "ok": True,
    "generated_at_unix": time.time(),
    "python": sys.executable,
    "checkpoint": rel(CHECKPOINT),
    "checkpoint_exists": CHECKPOINT.exists(),
    "run_log_dir": rel(RUN_LOG_DIR),
    "run_log_dir_exists": RUN_LOG_DIR.exists(),
    "home_dependencies": {
      "cyclonedds": "/home/seqn/cyclonedds",
      "unitree_sdk2_python": "/home/seqn/unitree_sdk2_python",
      "note": "Read-only home source dependencies; CycloneDDS runtime was installed into the go2-mjlab conda prefix.",
    },
    "env": {
      "CYCLONEDDS_HOME": os.environ.get("CYCLONEDDS_HOME", ""),
      "CMAKE_PREFIX_PATH": os.environ.get("CMAKE_PREFIX_PATH", ""),
      "LD_LIBRARY_PATH": os.environ.get("LD_LIBRARY_PATH", ""),
    },
    "imports": import_status(),
  }
  data["ok"] = bool(data["checkpoint_exists"] and data["run_log_dir_exists"] and all(v.get("ok") for v in data["imports"].values()))
  write_json(ARTIFACT_ROOT / "source_contract.json", data)
  lines = [
    "# Go2 MJLab FRESH Sim2Sim Preflight",
    "",
    f"- Status: `{'PASS' if data['ok'] else 'FAIL'}`",
    f"- Python: `{data['python']}`",
    f"- Checkpoint: `{data['checkpoint']}` exists `{data['checkpoint_exists']}`",
    f"- Run log dir: `{data['run_log_dir']}` exists `{data['run_log_dir_exists']}`",
    f"- CycloneDDS home source: `{data['home_dependencies']['cyclonedds']}`",
    f"- Unitree SDK2 Python home source: `{data['home_dependencies']['unitree_sdk2_python']}`",
    "",
    "## Imports",
  ]
  for name, status in data["imports"].items():
    lines.append(f"- `{name}`: `{'OK' if status.get('ok') else 'FAIL'}` {status.get('version', status.get('error', ''))}")
  (ARTIFACT_ROOT / "source_contract.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
  if not data["ok"]:
    raise SystemExit(f"preflight failed; see {ARTIFACT_ROOT / 'source_contract.json'}")


def inspect_mjlab_contract() -> dict[str, Any]:
  sys.path.insert(0, str(ROOT / "scripts" / "go2_mjlab_dreureka_port"))
  import src.tasks  # noqa: F401
  import dreureka_go2_mjlab  # noqa: F401
  import torch
  from dataclasses import asdict
  from dreureka_go2_mjlab.env_cfg import TASK_ID
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg
  from mjlab.utils.torch import configure_torch_backends

  configure_torch_backends()
  device = "cuda:0" if torch.cuda.is_available() else "cpu"
  cfg = load_env_cfg(TASK_ID, play=True)
  rl = load_rl_cfg(TASK_ID)
  cfg.scene.num_envs = 1
  env = ManagerBasedRlEnv(cfg=cfg, device=device)
  wrapped = RslRlVecEnvWrapper(env, clip_actions=rl.clip_actions)
  runner = MjlabOnPolicyRunner(wrapped, asdict(rl), str(RUN_LOG_DIR), device)
  runner.load(str(CHECKPOINT), load_cfg={"actor": True}, strict=True, map_location=device)
  policy = runner.get_inference_policy(device=device)
  action_term = env.action_manager.get_term("joint_pos")
  action_order = list(action_term.target_names)
  action_target_ids = [int(x) for x in action_term.target_ids.detach().cpu().tolist()]
  obs_terms = list(env.observation_manager.active_terms["actor"])
  obs_dim = list(env.observation_manager.group_obs_dim["actor"])
  obs = wrapped.get_observations()
  with torch.no_grad():
    action = policy(obs, stochastic_output=False)
  result = {
    "task_id": TASK_ID,
    "device": device,
    "checkpoint": rel(CHECKPOINT),
    "action_order": action_order,
    "action_target_ids": action_target_ids,
    "actor_observation_terms": obs_terms,
    "actor_observation_dim": obs_dim,
    "policy_output_shape": list(action.shape),
    "policy_output_finite": bool(torch.isfinite(action).all().item()),
    "policy_output_abs_max": float(action.abs().max().item()),
  }
  env.close()
  return result


def joint_order_contract() -> None:
  ensure_tree()
  mjlab = inspect_mjlab_contract()
  mjlab_to_unitree = [UNITREE_MOTOR_ORDER.index(name) for name in mjlab["action_order"]]
  unitree_to_mjlab = [mjlab["action_order"].index(name) for name in UNITREE_MOTOR_ORDER]
  zero_action_mjlab = {name: DEFAULT_JOINT_ANGLES[name] for name in mjlab["action_order"]}
  zero_action_unitree = {name: DEFAULT_JOINT_ANGLES[name] for name in UNITREE_MOTOR_ORDER}
  checks = {
    "checkpoint_policy_loads": mjlab["policy_output_finite"],
    "action_order_names_match": set(mjlab["action_order"]) == set(UNITREE_MOTOR_ORDER),
    "actor_observation_dim_840": mjlab["actor_observation_dim"] == [840],
    "expected_terms": mjlab["actor_observation_terms"] == ["orientation", "joint_pos", "joint_vel", "action", "last_action", "clock", "yaw"],
  }
  data = {
    "ok": all(checks.values()),
    "generated_at_unix": time.time(),
    "checks": checks,
    "mjlab": mjlab,
    "unitree_motor_order": UNITREE_MOTOR_ORDER,
    "mjlab_contract_order": MJLAB_CONTRACT_ORDER,
    "mjlab_to_unitree_indices": mjlab_to_unitree,
    "unitree_to_mjlab_indices": unitree_to_mjlab,
    "zero_action_default_pose_mjlab_order": zero_action_mjlab,
    "zero_action_default_pose_unitree_order": zero_action_unitree,
    "pd": {"kp_by_joint": KP_BY_JOINT, "kd_by_joint": KD_BY_JOINT, "action_scale": ACTION_SCALE},
  }
  encoded = json.dumps(data, sort_keys=True).encode()
  data["sha256"] = hashlib.sha256(encoded).hexdigest()
  write_json(ARTIFACT_ROOT / "joint_order_contract.json", data)
  lines = [
    "# Joint Order Contract",
    "",
    f"- Status: `{'PASS' if data['ok'] else 'FAIL'}`",
    f"- MJLab action order: `{mjlab['action_order']}`",
    f"- Unitree DDS order: `{UNITREE_MOTOR_ORDER}`",
    f"- MJLab to Unitree indices: `{mjlab_to_unitree}`",
    f"- Unitree to MJLab indices: `{unitree_to_mjlab}`",
    f"- Actor observation dim: `{mjlab['actor_observation_dim']}`",
    f"- Actor terms: `{mjlab['actor_observation_terms']}`",
    f"- Contract SHA256: `{data['sha256']}`",
  ]
  (ARTIFACT_ROOT / "joint_order_contract.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
  if not data["ok"]:
    raise SystemExit(f"joint order contract failed; see {ARTIFACT_ROOT / 'joint_order_contract.json'}")


def deployer_smoke() -> None:
  ensure_tree()
  out = ARTIFACT_ROOT / "deployer_smoke.json"
  cmd = [
    sys.executable,
    str(SCRIPT_ROOT / "mjlab_dds_deployer.py"),
    "--checkpoint",
    str(CHECKPOINT),
    "--log-dir",
    str(RUN_LOG_DIR),
    "--out-dir",
    str(LOG_ROOT / "deployer_smoke"),
    "--summary",
    str(out),
    "--smoke-only",
  ]
  result = run_capture(cmd, timeout=180)
  if not out.exists():
    write_json(out, {"ok": False, "subprocess": result})
  data = json.loads(out.read_text(encoding="utf-8"))
  data["subprocess"] = result
  write_json(out, data)
  lines = [
    "# Deployer Smoke",
    "",
    f"- Status: `{'PASS' if data.get('ok') else 'FAIL'}`",
    f"- Checkpoint: `{rel(CHECKPOINT)}`",
    f"- Actor obs shape: `{data.get('actor_obs_shape')}`",
    f"- Action shape: `{data.get('action_shape')}`",
    f"- Action abs max: `{data.get('action_abs_max')}`",
  ]
  (ARTIFACT_ROOT / "deployer_smoke.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
  if not data.get("ok"):
    raise SystemExit(f"deployer smoke failed; see {out}")


def quat_to_rpy(q: list[float]) -> tuple[float, float, float]:
  import math

  w, x, y, z = q
  roll = math.atan2(2.0 * (w * x + y * z), 1.0 - 2.0 * (x * x + y * y))
  pitch = math.asin(max(-1.0, min(1.0, 2.0 * (w * y - z * x))))
  yaw = math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))
  return roll, pitch, yaw


def mjlab_playback(args: argparse.Namespace) -> None:
  ensure_tree()
  sys.path.insert(0, str(ROOT / "scripts" / "go2_mjlab_dreureka_port"))
  import src.tasks  # noqa: F401
  import dreureka_go2_mjlab  # noqa: F401
  import torch
  from dataclasses import asdict
  from dreureka_go2_mjlab.env_cfg import TASK_ID
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg
  from mjlab.utils.torch import configure_torch_backends

  configure_torch_backends()
  device = args.device or ("cuda:0" if torch.cuda.is_available() else "cpu")
  cfg = load_env_cfg(TASK_ID, play=True)
  rl = load_rl_cfg(TASK_ID)
  cfg.scene.num_envs = 1
  cfg.auto_reset = False
  log_dir = LOG_ROOT / "mjlab_playback"
  log_dir.mkdir(parents=True, exist_ok=True)
  csv_path = log_dir / "playback.csv"
  env = ManagerBasedRlEnv(cfg=cfg, device=device)
  wrapped = RslRlVecEnvWrapper(env, clip_actions=rl.clip_actions)
  runner = MjlabOnPolicyRunner(wrapped, asdict(rl), str(RUN_LOG_DIR), device)
  runner.load(str(CHECKPOINT), load_cfg={"actor": True}, strict=True, map_location=device)
  policy = runner.get_inference_policy(device=device)
  obs = wrapped.get_observations()
  robot = env.scene["robot"]
  ball = env.scene["ball"]
  rows = []
  done = False
  steps = int(args.duration_s / env.step_dt)
  with csv_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
      f,
      fieldnames=[
        "step",
        "sim_time_s",
        "reward",
        "done",
        "base_z",
        "roll",
        "pitch",
        "ball_z",
        "action_abs_max",
      ],
    )
    writer.writeheader()
    for step in range(steps):
      with torch.no_grad():
        action = policy(obs, stochastic_output=False)
      obs, rew, dones, _extras = wrapped.step(action)
      root_pos = robot.data.root_link_pos_w[0].detach().cpu().tolist()
      root_quat = robot.data.root_link_quat_w[0].detach().cpu().tolist()
      ball_pos = ball.data.root_link_pos_w[0].detach().cpu().tolist()
      roll, pitch, _ = quat_to_rpy(root_quat)
      done = bool(dones[0].item())
      row = {
        "step": step,
        "sim_time_s": f"{(step + 1) * env.step_dt:.6f}",
        "reward": f"{float(rew[0].item()):.9f}",
        "done": int(done),
        "base_z": f"{float(root_pos[2]):.9f}",
        "roll": f"{roll:.9f}",
        "pitch": f"{pitch:.9f}",
        "ball_z": f"{float(ball_pos[2]):.9f}",
        "action_abs_max": f"{float(action.abs().max().item()):.9f}",
      }
      writer.writerow(row)
      rows.append(row)
      if done:
        break
  env.close()

  last = rows[-1] if rows else {}
  summary = {
    "ok": bool(rows and not done),
    "checkpoint": rel(CHECKPOINT),
    "device": device,
    "duration_s_requested": args.duration_s,
    "steps": len(rows),
    "step_dt": env.step_dt,
    "terminated": done,
    "last": last,
    "csv": rel(csv_path),
  }
  write_json(ARTIFACT_ROOT / "mjlab_playback_smoke.json", summary)
  lines = [
    "# MJLab Playback Smoke",
    "",
    f"- Status: `{'PASS' if summary['ok'] else 'FAIL'}`",
    f"- Checkpoint: `{rel(CHECKPOINT)}`",
    f"- Steps: `{summary['steps']}`",
    f"- Terminated: `{summary['terminated']}`",
    f"- Last base_z: `{last.get('base_z')}`",
    f"- Last roll/pitch: `{last.get('roll')}` / `{last.get('pitch')}`",
    f"- Last action abs max: `{last.get('action_abs_max')}`",
    f"- CSV: `{rel(csv_path)}`",
  ]
  (ARTIFACT_ROOT / "mjlab_playback_smoke.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
  if not summary["ok"]:
    raise SystemExit(f"MJLab playback failed; see {ARTIFACT_ROOT / 'mjlab_playback_smoke.json'}")


def stream_process(cmd: list[str], log_path: Path) -> subprocess.Popen:
  log_path.parent.mkdir(parents=True, exist_ok=True)
  f = log_path.open("w", encoding="utf-8")
  return subprocess.Popen(cmd, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT, text=True)


def summarize_attempt(attempt_dir: Path, process_status: dict[str, Any]) -> dict[str, Any]:
  endpoint_summary_path = attempt_dir / "summary.json"
  endpoint = json.loads(endpoint_summary_path.read_text(encoding="utf-8")) if endpoint_summary_path.exists() else {}
  timing_path = attempt_dir / "deployer_timing.csv"
  timing_rows = []
  if timing_path.exists():
    with timing_path.open(newline="", encoding="utf-8") as f:
      timing_rows = list(csv.DictReader(f))
  inference_vals = [float(r["inference_s"]) for r in timing_rows if r.get("inference_s")]
  action_vals = [float(r["action_abs_max"]) for r in timing_rows if r.get("action_abs_max")]
  return {
    "ok": bool(
      endpoint.get("ok")
      and not endpoint.get("fall_detected")
      and process_status.get("endpoint_returncode") == 0
      and process_status.get("deployer_returncode") == 0
    ),
    "checkpoint": rel(CHECKPOINT),
    "attempt_dir": rel(attempt_dir),
    "process_status": process_status,
    "endpoint": endpoint,
    "deployer_steps": len(timing_rows),
    "deployer_inference_mean_s": sum(inference_vals) / len(inference_vals) if inference_vals else None,
    "deployer_inference_max_s": max(inference_vals) if inference_vals else None,
    "action_abs_max": max(action_vals) if action_vals else None,
  }


def attempt(args: argparse.Namespace) -> None:
  ensure_tree()
  joint_order_contract()
  deployer_smoke()
  attempt_name = args.name
  attempt_dir = LOG_ROOT / attempt_name
  attempt_dir.mkdir(parents=True, exist_ok=True)
  event_log = attempt_dir / "events.csv"
  duration_s = float(args.duration_s)
  endpoint_cmd = [
    sys.executable,
    str(ROOT / "scripts" / "go2_yoga_ball" / "go2_mujoco_dds_endpoint.py"),
    "--run",
    str(ROOT / "thirdparties" / "DrEureka" / "globe_walking" / "runs" / "globe_walking" / "2026-05-28" / "train" / "063234.884668"),
    "--duration-s",
    str(duration_s),
    "--out-dir",
    str(attempt_dir),
    "--event-log",
    str(event_log),
    "--dds-domain",
    str(args.dds_domain),
    "--network-interface",
    args.network_interface,
    "--base-z",
    str(args.base_z),
    "--ball-radius",
    str(args.ball_radius),
  ]
  deployer_cmd = [
    sys.executable,
    str(SCRIPT_ROOT / "mjlab_dds_deployer.py"),
    "--checkpoint",
    str(CHECKPOINT),
    "--log-dir",
    str(RUN_LOG_DIR),
    "--out-dir",
    str(attempt_dir),
    "--summary",
    str(attempt_dir / "deployer_summary.json"),
    "--dds-domain",
    str(args.dds_domain),
    "--network-interface",
    args.network_interface,
    "--duration-s",
    str(duration_s),
  ]
  endpoint = stream_process(endpoint_cmd, attempt_dir / "mujoco_dds_endpoint.log")
  time.sleep(2.0)
  deployer = stream_process(deployer_cmd, attempt_dir / "mjlab_dds_deployer.log")
  deployer_rc = deployer.wait(timeout=int(duration_s + 120))
  endpoint_rc = endpoint.wait(timeout=int(duration_s + 120))
  status = {
    "endpoint_returncode": endpoint_rc,
    "deployer_returncode": deployer_rc,
    "endpoint_cmd": endpoint_cmd,
    "deployer_cmd": deployer_cmd,
  }
  write_json(attempt_dir / "process_status.json", status)
  summary = summarize_attempt(attempt_dir, status)
  write_json(attempt_dir / "fresh_summary.json", summary)

  video = ARTIFACT_ROOT / "videos" / f"go2_mjlab_fresh_sim2sim_{attempt_name}.mp4"
  video_summary = ARTIFACT_ROOT / f"go2_mjlab_fresh_sim2sim_{attempt_name}_video.json"
  render_cmd = [
    sys.executable,
    str(ROOT / "scripts" / "go2_yoga_ball" / "render_mujoco_replay_video.py"),
    "--replay",
    str(attempt_dir / "replay.csv"),
    "--events",
    str(event_log),
    "--output",
    str(video),
    "--artifact",
    str(video_summary),
  ]
  render = run_capture(render_cmd, timeout=180)
  summary["video"] = rel(video)
  summary["video_summary"] = rel(video_summary)
  summary["render"] = render
  write_json(attempt_dir / "fresh_summary.json", summary)
  write_json(ARTIFACT_ROOT / "summary.json", summary)
  report(summary)
  if not summary.get("ok"):
    raise SystemExit(f"attempt failed; see {attempt_dir / 'fresh_summary.json'}")


def report(summary: dict[str, Any] | None = None) -> None:
  ensure_tree()
  if summary is None:
    summary_path = ARTIFACT_ROOT / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {"ok": False}
  endpoint = summary.get("endpoint", {})
  lines = [
    "# Go2 MJLab FRESH Sim2Sim Report",
    "",
    f"- Status: `{'PASS' if summary.get('ok') else 'FAIL'}`",
    f"- Checkpoint: `{summary.get('checkpoint', rel(CHECKPOINT))}`",
    f"- Attempt dir: `{summary.get('attempt_dir')}`",
    f"- DDS command count: `{endpoint.get('cmd_count')}`",
    f"- Release confirmed: `{endpoint.get('release_confirmed')}`",
    f"- Fall detected: `{endpoint.get('fall_detected')}`",
    f"- Sim elapsed: `{endpoint.get('sim_elapsed_s')}`",
    f"- Deployer steps: `{summary.get('deployer_steps')}`",
    f"- Deployer inference mean/max: `{summary.get('deployer_inference_mean_s')}` / `{summary.get('deployer_inference_max_s')}`",
    f"- Action abs max: `{summary.get('action_abs_max')}`",
    f"- Video: `{summary.get('video')}`",
    "",
    "Joint order proof is recorded in `joint_order_contract.json` and must be treated as part of this result.",
  ]
  (ARTIFACT_ROOT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("cmd", choices=["preflight", "joint-order-contract", "deployer-smoke", "mjlab-playback", "attempt", "report"])
  parser.add_argument("--name", default="attempt_001_faithful_host")
  parser.add_argument("--duration-s", type=float, default=12.0)
  parser.add_argument("--dds-domain", type=int, default=1)
  parser.add_argument("--network-interface", default="lo")
  parser.add_argument("--device", default=None)
  parser.add_argument("--base-z", type=float, default=0.95)
  parser.add_argument("--ball-radius", type=float, default=0.45)
  args = parser.parse_args()
  if args.cmd == "preflight":
    preflight()
  elif args.cmd == "joint-order-contract":
    joint_order_contract()
  elif args.cmd == "deployer-smoke":
    deployer_smoke()
  elif args.cmd == "mjlab-playback":
    mjlab_playback(args)
  elif args.cmd == "attempt":
    attempt(args)
  elif args.cmd == "report":
    report()
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
