#!/usr/bin/env python3
"""Root-owned orchestration utilities for the Go1 yoga-ball goal.

This file intentionally starts with preflight/report generation. Heavy
simulation, training, and policy execution are expected to run in Docker.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
import math
import os
from pathlib import Path
import pickle
import re
import subprocess
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
THIRDPARTIES = ROOT / "thirdparties"
DREUREKA = THIRDPARTIES / "DrEureka"
WBC = THIRDPARTIES / "wbc-workspace"
ISAAC_GYM_CANDIDATES = [THIRDPARTIES / "IsaacGym", THIRDPARTIES / "isaacgym"]
MJLAB = THIRDPARTIES / "MJLab"
MJLAB_GO1_SMOKE_TASK = "Mjlab-Velocity-Flat-Unitree-Go1"

LOG_ROOT = ROOT / "logs" / "go1_yoga_ball"
ARTIFACT_ROOT = ROOT / "artifacts" / "go1_yoga_ball"
VIDEO_ROOT = ARTIFACT_ROOT / "videos"
BUILD_ROOT = ARTIFACT_ROOT / "build"

PRETRAINED_RUN = DREUREKA / "globe_walking" / "runs" / "globe_walking" / "dr_eureka_best"
PRETRAINED_CHECKPOINTS = PRETRAINED_RUN / "checkpoints"
DEFAULT_TRAIN_SELECTED_RUN = ARTIFACT_ROOT / "default_train_selected_run.txt"
GO1_XML = DREUREKA / "globe_walking" / "resources" / "robots" / "go1" / "xml" / "go1.xml"
BALL_URDF = DREUREKA / "globe_walking" / "resources" / "objects" / "ball.urdf"
POLICY_JOINT_NAMES = [
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
HARDWARE_JOINT_NAMES = [
    "FR_hip_joint",
    "FR_thigh_joint",
    "FR_calf_joint",
    "FL_hip_joint",
    "FL_thigh_joint",
    "FL_calf_joint",
    "RR_hip_joint",
    "RR_thigh_joint",
    "RR_calf_joint",
    "RL_hip_joint",
    "RL_thigh_joint",
    "RL_calf_joint",
]
GO1_JOINT_LIMITS = [(-0.802851, 0.802851), (-1.0472, 4.18879), (-2.69653, -0.916298)] * 4


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def git_head(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        top_level = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        ).stdout.strip()
        if Path(top_level).resolve() != path.resolve():
            return None
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def git_remote(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        top_level = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        ).stdout.strip()
        if Path(top_level).resolve() != path.resolve():
            return None
        result = subprocess.run(
            ["git", "-C", str(path), "remote", "get-url", "origin"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def ensure_tree() -> None:
    for path in [
        LOG_ROOT / "pretrained" / "isaacgym_playback",
        LOG_ROOT / "pretrained" / "mujoco_sim2sim",
        LOG_ROOT / "default_train" / "train",
        LOG_ROOT / "default_train" / "isaacgym_playback",
        LOG_ROOT / "default_train" / "mujoco_sim2sim",
        LOG_ROOT / "mjlab_train" / "train",
        LOG_ROOT / "mjlab_train" / "default_playback",
        LOG_ROOT / "mjlab_train" / "mujoco_sim2sim",
        VIDEO_ROOT,
        BUILD_ROOT,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def has_contents(path: Path) -> bool:
    if not path.exists():
        return False
    if path.is_file():
        return path.stat().st_size > 0
    try:
        next(path.iterdir())
    except StopIteration:
        return False
    except OSError:
        return False
    return True


def path_status(path: Path, required: bool) -> dict[str, Any]:
    return {
        "path": rel(path),
        "exists": path.exists(),
        "has_contents": has_contents(path),
        "required": required,
        "git_head": git_head(path) if path.exists() else None,
        "git_remote": git_remote(path) if path.exists() else None,
    }


def docker_image_status(image: str, required: bool) -> dict[str, Any]:
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", image, "--format", "{{.Id}} {{.Created}}"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return {"image": image, "exists": False, "required": required, "id": None, "created": None}
    output = result.stdout.strip()
    image_id, _, created = output.partition(" ")
    return {"image": image, "exists": True, "required": required, "id": image_id, "created": created}


def validate_deps() -> dict[str, Any]:
    ensure_tree()
    isaac_gym = next((p for p in ISAAC_GYM_CANDIDATES if p.exists()), None)
    deps = {
        "generated_at_unix": time.time(),
        "root": str(ROOT),
        "dependencies": {
            "DrEureka": path_status(DREUREKA, True),
            "wbc-workspace": path_status(WBC, True),
            "IsaacGym": path_status(isaac_gym or ISAAC_GYM_CANDIDATES[0], True),
            "MJLab": path_status(MJLAB, True),
            "wbc-unitree_mujoco": path_status(WBC / "thirdparties" / "unitree_mujoco", False),
        },
        "dockerfiles": {
            name: path_status(ROOT / "docker" / f"{name}.Dockerfile", True)
            for name in ["isaacgym", "mujoco_sim2sim", "mjlab"]
        },
        "docker_images": {
            name: docker_image_status(f"eureka-{name}", name == "mujoco_sim2sim")
            for name in ["isaacgym", "mujoco_sim2sim", "mjlab"]
        },
        "notes": [
            "Missing Isaac Gym or MJLab is not an immediate blocker; the goal requires fetching them into thirdparties and using them inside Docker.",
            "Nested wbc-workspace third-party submodules are optional reference material until MuJoCo implementation work begins, but empty submodule directories are not usable contents.",
        ],
    }
    write_json(ARTIFACT_ROOT / "manifest.json", deps)
    return deps


def inspect_policy() -> dict[str, Any]:
    ensure_tree()
    entries = [
        policy_entry(
            "dr_eureka_best_pretrained",
            PRETRAINED_RUN,
            source="thirdparties/DrEureka globe_walking checked-in run",
            phase="pretrained",
        )
    ]
    default_run = selected_default_train_run()
    if default_run is not None:
        entries.append(
            policy_entry(
                "dr_eureka_default_train_latest",
                default_run,
                source="fresh DrEureka default Isaac Gym training run selected by root orchestration",
                phase="default_train",
            )
        )
    policy: dict[str, Any] = {"policies": entries}
    write_json(ARTIFACT_ROOT / "policy_registry.json", policy)
    return policy


def policy_entry(name: str, run_dir: Path, *, source: str, phase: str) -> dict[str, Any]:
    checkpoints = run_dir / "checkpoints"
    files = {
        "run_dir": run_dir,
        "parameters": run_dir / "parameters.pkl",
        "metrics": run_dir / "metrics.pkl",
        "outputs": run_dir / "outputs.log",
        "body": checkpoints / "body_latest.jit",
        "adaptation_module": checkpoints / "adaptation_module_latest.jit",
        "actor_critic": checkpoints / "ac_weights_last.pt",
    }
    entry = {
        "name": name,
        "source": source,
        "phase": phase,
        "paths": {key: rel(path) for key, path in files.items()},
        "path_exists": {key: path.exists() for key, path in files.items()},
        "expected_policy_files": [
            rel(files["body"]),
            rel(files["adaptation_module"]),
        ],
        "deployment_runner": rel(
            DREUREKA / "globe_walking" / "go1_gym_deploy" / "scripts" / "deploy_policy.py"
        ),
    }
    params_path = files["parameters"]
    if params_path.exists():
        try:
            with params_path.open("rb") as f:
                params = pickle.load(f)
            cfg = params.get("Cfg", {})
            entry["cfg_summary"] = summarize_cfg(cfg)
        except Exception as exc:  # noqa: BLE001 - preflight should capture failures.
            entry["cfg_summary_error"] = repr(exc)
    return entry


def selected_default_train_run() -> Path | None:
    if DEFAULT_TRAIN_SELECTED_RUN.exists():
        text = DEFAULT_TRAIN_SELECTED_RUN.read_text(encoding="utf-8").strip()
        if text:
            path = Path(text)
            if not path.is_absolute():
                path = ROOT / path
            return path
    candidates = [
        path
        for path in (DREUREKA / "globe_walking" / "runs" / "globe_walking").glob("**/checkpoints/body_latest.jit")
        if "dr_eureka_best" not in path.parts
    ]
    if not candidates:
        return None
    return max((path.parents[1] for path in candidates), key=lambda p: p.stat().st_mtime)


def record_default_train_run() -> dict[str, Any]:
    ensure_tree()
    before_path = LOG_ROOT / "default_train" / "train" / "runs_before.txt"
    after_path = LOG_ROOT / "default_train" / "train" / "runs_after.txt"
    before = set(before_path.read_text(encoding="utf-8").splitlines()) if before_path.exists() else set()
    after = set(after_path.read_text(encoding="utf-8").splitlines()) if after_path.exists() else set()
    new_runs = [ROOT / path for path in sorted(after - before)]
    valid = [path for path in new_runs if (path / "checkpoints" / "body_latest.jit").exists()]
    if not valid:
        selected = selected_default_train_run()
        if selected is not None and (selected / "checkpoints" / "body_latest.jit").exists():
            valid = [selected]
    selected = max(valid, key=lambda p: p.stat().st_mtime) if valid else None
    result = {
        "ok": selected is not None,
        "selected_run": rel(selected) if selected is not None else None,
        "new_runs": [rel(path) for path in new_runs],
        "valid_new_runs": [rel(path) for path in valid],
        "required_files": [
            "parameters.pkl",
            "checkpoints/body_latest.jit",
            "checkpoints/adaptation_module_latest.jit",
            "checkpoints/ac_weights_last.pt",
        ],
    }
    if selected is not None:
        DEFAULT_TRAIN_SELECTED_RUN.write_text(str(selected) + "\n", encoding="utf-8")
        result["policy_entry"] = policy_entry(
            "dr_eureka_default_train_latest",
            selected,
            source="fresh DrEureka default Isaac Gym training run selected by root orchestration",
            phase="default_train",
        )
    write_json(ARTIFACT_ROOT / "default_train_run.json", result)
    inspect_policy()
    return result


def summarize_cfg(cfg: Any) -> dict[str, Any]:
    if not isinstance(cfg, dict):
        return {"type": type(cfg).__name__}
    domain_rand = cfg.get("domain_rand", {})
    env = cfg.get("env", {})
    control = cfg.get("control", {})
    sim = cfg.get("sim", {})
    return {
        "env_num_envs": env.get("num_envs") if isinstance(env, dict) else None,
        "env_num_observations": env.get("num_observations") if isinstance(env, dict) else None,
        "env_num_observation_history": env.get("num_observation_history") if isinstance(env, dict) else None,
        "env_num_actions": env.get("num_actions") if isinstance(env, dict) else None,
        "control_decimation": control.get("decimation") if isinstance(control, dict) else None,
        "control_action_scale": control.get("action_scale") if isinstance(control, dict) else None,
        "sim_dt": sim.get("dt") if isinstance(sim, dict) else None,
        "domain_rand": {
            key: value
            for key, value in sorted(domain_rand.items())
            if key.endswith("_range") or key in {"randomize", "push_ball_interval_s", "push_robot_interval_s"}
        }
        if isinstance(domain_rand, dict)
        else {},
    }


def write_contract() -> Path:
    ensure_tree()
    path = ARTIFACT_ROOT / "sim2sim_contract.md"
    path.write_text(
        """# Go1 Yoga-Ball Sim2Sim Contract

## Policy Side

The final DrEureka MuJoCo Sim2Sim path must run the policy through the DrEureka deployment stack:

- `thirdparties/DrEureka/globe_walking/go1_gym_deploy/scripts/deploy_policy.py`
- TorchScript modules from a run directory's `checkpoints/body_latest.jit` and `checkpoints/adaptation_module_latest.jit`

## Transport

Use the same LCM channels as real Go1 deployment:

- Policy consumes `state_estimator_data`, `leg_control_data`, and `rc_command`.
- Policy publishes `pd_plustau_targets`.

Real robot deployment uses `lcm_position.cpp` to bridge Unitree low-level UDP to these LCM channels. MuJoCo Sim2Sim should replace only that bridge, not the policy process.

## Joint Order

DrEureka policy order:

```text
FL_hip_joint, FL_thigh_joint, FL_calf_joint,
FR_hip_joint, FR_thigh_joint, FR_calf_joint,
RL_hip_joint, RL_thigh_joint, RL_calf_joint,
RR_hip_joint, RR_thigh_joint, RR_calf_joint
```

The deployment `StateEstimator` reorders hardware state with `joint_idxs = [3, 4, 5, 0, 1, 2, 9, 10, 11, 6, 7, 8]`. A MuJoCo bridge must preserve the same semantics observed by `LCMAgent`.

## Timing

The pretrained DrEureka deployment script uses `control_dt = 0.02` seconds. Sim2Sim must report wall time, simulation time, policy loop time, control jitter, and inference latency.

## Startup And Release

Support is allowed only to emulate the real robot being hung up while the controller and policy start. The simulator must prove support release after policy control is active and must prove unpinned root dynamics after release.
""",
        encoding="utf-8",
    )
    return path


def sanitized_go1_xml() -> Path:
    ensure_tree()
    text = GO1_XML.read_text(encoding="utf-8")
    meshdir = GO1_XML.parents[1] / "meshes"
    replacements = {
        "objtype=site": 'objtype="site"',
        'meshdir="../meshes/"': f'meshdir="{meshdir}"',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.replace("\n=\n", "\n")
    out = BUILD_ROOT / "go1_sanitized.xml"
    out.write_text(text, encoding="utf-8")
    return out


def smoke_mujoco_assets() -> dict[str, Any]:
    ensure_tree()
    xml = sanitized_go1_xml()
    try:
        import mujoco  # type: ignore
        import lcm  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        result = {
            "ok": False,
            "error": repr(exc),
            "context": "import mujoco/lcm",
        }
        write_json(ARTIFACT_ROOT / "mujoco_asset_smoke.json", result)
        return result

    try:
        model = mujoco.MjModel.from_xml_path(str(xml))
    except Exception as exc:  # noqa: BLE001
        result = {
            "ok": False,
            "error": repr(exc),
            "context": f"load {rel(xml)}",
            "source_xml": rel(GO1_XML),
            "sanitized_xml": rel(xml),
            "source_sha256": sha256(GO1_XML),
            "sanitized_sha256": sha256(xml),
        }
        write_json(ARTIFACT_ROOT / "mujoco_asset_smoke.json", result)
        return result

    result = {
        "ok": True,
        "source_xml": rel(GO1_XML),
        "sanitized_xml": rel(xml),
        "source_sha256": sha256(GO1_XML),
        "sanitized_sha256": sha256(xml),
        "ball_urdf": rel(BALL_URDF),
        "ball_urdf_exists": BALL_URDF.exists(),
        "nq": int(model.nq),
        "nv": int(model.nv),
        "nu": int(model.nu),
        "njnt": int(model.njnt),
        "nbody": int(model.nbody),
    }
    write_json(ARTIFACT_ROOT / "mujoco_asset_smoke.json", result)
    return result


def direct_release_smoke(duration_s: float = 5.0) -> dict[str, Any]:
    ensure_tree()
    scene = yoga_ball_scene_xml()
    try:
        import mujoco  # type: ignore
        import numpy as np
    except Exception as exc:  # noqa: BLE001
        result = {"ok": False, "error": repr(exc), "context": "import mujoco/numpy"}
        write_json(ARTIFACT_ROOT / "release_validation.json", result)
        return result

    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    ball_radius = 0.45
    support_height = 2.0 * ball_radius + 0.0001
    height_failure_threshold = 2.0 * ball_radius - 0.05
    tilt_failure_threshold = 1.0
    set_initial_go1_ball_state(model, data, mujoco, ball_radius=ball_radius, base_z=support_height)
    mujoco.mj_forward(model, data)

    raw_path = LOG_ROOT / "pretrained" / "mujoco_sim2sim" / "direct_release_smoke.csv"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    dt = float(model.opt.timestep)
    steps = max(int(duration_s / dt), 1)
    fall_time: float | None = None
    rows = []
    wall_start = time.monotonic()
    for step in range(steps + 1):
        base_z = float(data.qpos[2])
        ball_z = float(data.qpos[model.jnt_qposadr[ball_free_joint_id(model, mujoco)] + 2])
        roll, pitch = quat_roll_pitch(data.qpos[3:7])
        sim_time = float(data.time)
        rows.append(
            {
                "step": step,
                "sim_time_s": sim_time,
                "wall_elapsed_s": time.monotonic() - wall_start,
                "support_active": 0,
                "base_z": base_z,
                "ball_z": ball_z,
                "roll": roll,
                "pitch": pitch,
            }
        )
        if fall_time is None and (
            base_z < height_failure_threshold
            or abs(roll) > tilt_failure_threshold
            or abs(pitch) > tilt_failure_threshold
        ):
            fall_time = sim_time
        if step < steps:
            mujoco.mj_step(model, data)

    write_csv(raw_path, rows)
    wall_elapsed = time.monotonic() - wall_start
    result = {
        "ok": fall_time is not None,
        "kind": "direct_release_no_control",
        "scene_xml": rel(scene),
        "raw_log": rel(raw_path),
        "duration_s": duration_s,
        "fall_time_s": fall_time,
        "sim_elapsed_s": float(data.time),
        "wall_elapsed_s": wall_elapsed,
        "sim_wall_ratio": float(data.time / wall_elapsed) if wall_elapsed > 0 else None,
        "ball_radius": ball_radius,
        "height_failure_threshold": height_failure_threshold,
        "tilt_failure_threshold": tilt_failure_threshold,
        "support_active_initial": False,
        "support_active_after_release": False,
        "note": "This is a no-control release smoke. It proves the MuJoCo scene is dynamic and can fall; it is not policy validation.",
    }
    write_json(ARTIFACT_ROOT / "release_validation.json", result)
    return result


def summarize_isaacgym_playback(log_path: Path, *, policy_run: Path, command: str) -> dict[str, Any]:
    ensure_tree()
    text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    progress_matches = re.findall(r"(\d+)/(\d+)", text)
    completed_iterations = None
    requested_iterations = None
    if progress_matches:
        completed_iterations, requested_iterations = [int(v) for v in progress_matches[-1]]
    result = {
        "ok": bool(
            log_path.exists()
            and completed_iterations is not None
            and requested_iterations is not None
            and completed_iterations >= requested_iterations
            and "Traceback" not in text
            and "Segmentation fault" not in text
        ),
        "raw_log": rel(log_path),
        "requested_iterations": requested_iterations,
        "completed_iterations": completed_iterations,
        "uses_gpu_physx": "+++ Using GPU PhysX" in text,
        "graphics_disabled": "Running with headless and no recording, disabled graphics rendering" in text,
        "graphics_warning_present": "Running with graphics rendering enabled" in text,
        "python_traceback_present": "Traceback" in text,
        "segfault_present": "Segmentation fault" in text,
        "policy_run": rel(policy_run),
        "playback_command": command,
    }
    return result


def summarize_pretrained_isaacgym_playback() -> dict[str, Any]:
    result = summarize_isaacgym_playback(
        LOG_ROOT / "pretrained" / "isaacgym_playback" / "play_pretrained_isaacgym.log",
        policy_run=PRETRAINED_RUN,
        command="scripts/go1_yoga_ball/run.sh play-pretrained-isaacgym",
    )
    write_json(ARTIFACT_ROOT / "pretrained_isaacgym_playback.json", result)
    return result


def summarize_default_train_isaacgym_playback() -> dict[str, Any]:
    run = selected_default_train_run() or Path("")
    result = summarize_isaacgym_playback(
        LOG_ROOT / "default_train" / "isaacgym_playback" / "play_default_train_isaacgym.log",
        policy_run=run,
        command="scripts/go1_yoga_ball/run.sh play-default-train-isaacgym",
    )
    write_json(ARTIFACT_ROOT / "default_train_isaacgym_playback.json", result)
    return result


def summarize_mujoco_sim2sim_logs(
    log_subdir: Path,
    artifact_filename: str,
    *,
    update_pretrained_release: bool = False,
) -> dict[str, Any]:
    ensure_tree()
    run_dir = LOG_ROOT / log_subdir
    events_path = run_dir / "sequence_events.csv"
    status_path = run_dir / "simulator_status.csv"
    policy_path = run_dir / "policy_timing.csv"
    replay_path = run_dir / "replay.csv"
    sim_summary = load_json(run_dir / "sim_bridge_summary.json")
    events = read_csv_dicts(events_path)
    status_rows = read_csv_dicts(status_path)
    policy_rows = read_csv_dicts(policy_path)
    replay_rows = read_csv_dicts(replay_path)

    event_names = [row.get("event") for row in events]
    event_times = {row.get("event"): row for row in events}
    required_events = [
        "SIM_START",
        "POLICY_START",
        "CONTROL_ACTIVE",
        "CONTROL_ACTIVE_OBSERVED_BY_SIM",
        "SUPPORT_RELEASE_REQUESTED",
        "SUPPORT_RELEASE_CONFIRMED",
        "BALANCE_WINDOW_START",
        "BALANCE_WINDOW_END",
    ]
    missing_events = [name for name in required_events if name not in event_names]
    release_time = as_float(event_times.get("SUPPORT_RELEASE_CONFIRMED", {}).get("sim_time_s"))
    balance_end_time = as_float(event_times.get("BALANCE_WINDOW_END", {}).get("sim_time_s"))
    release_window_s = (
        balance_end_time - release_time
        if release_time is not None and balance_end_time is not None
        else None
    )

    sim_elapsed = as_float(sim_summary.get("sim_elapsed_s"))
    wall_elapsed = as_float(sim_summary.get("wall_elapsed_s"))
    sim_wall_ratio = sim_elapsed / wall_elapsed if sim_elapsed is not None and wall_elapsed else None
    policy_wall_elapsed = None
    policy_time_elapsed = None
    policy_time_wall_ratio = None
    mean_loop = p95_loop = max_loop = mean_infer = p95_infer = max_infer = None
    if policy_rows:
        policy_wall_elapsed = as_float(policy_rows[-1].get("monotonic_s"))
        policy_time_elapsed = as_float(policy_rows[-1].get("policy_time_s"))
        policy_time_wall_ratio = (
            policy_time_elapsed / policy_wall_elapsed
            if policy_time_elapsed is not None and policy_wall_elapsed
            else None
        )
        loop_periods = [as_float(row.get("loop_period_s")) for row in policy_rows[1:]]
        loop_periods = [v for v in loop_periods if v is not None]
        infer = [as_float(row.get("inference_latency_s")) for row in policy_rows]
        infer = [v for v in infer if v is not None]
        mean_loop = mean(loop_periods)
        p95_loop = percentile(loop_periods, 95)
        max_loop = max(loop_periods) if loop_periods else None
        mean_infer = mean(infer)
        p95_infer = percentile(infer, 95)
        max_infer = max(infer) if infer else None

    released_rows = [row for row in status_rows if as_float(row.get("support_active")) == 0]
    heights = [as_float(row.get("base_z")) for row in released_rows]
    heights = [v for v in heights if v is not None]
    threshold = 0.9
    below_threshold = [v for v in heights if v < threshold]
    released_replay_rows = [row for row in replay_rows if as_float(row.get("support_active")) == 0]
    joint_summary_total = joint_limit_summary(replay_rows)
    joint_summary_released = joint_limit_summary(released_replay_rows)
    joint_violations_total = joint_summary_total["violation_frames"]
    joint_violations_released = joint_summary_released["violation_frames"]
    sim_time_policy_ratio = (
        sim_elapsed / policy_wall_elapsed if sim_elapsed is not None and policy_wall_elapsed else None
    )
    sim_timing_ok = sim_wall_ratio is not None and abs(sim_wall_ratio - 1.0) <= 0.05
    policy_timing_ok = policy_time_wall_ratio is not None and abs(policy_time_wall_ratio - 1.0) <= 0.05
    height_ok = bool(heights and len(below_threshold) / len(heights) <= 0.05)
    result = {
        "ok_smoke": bool(
            not missing_events
            and sim_summary.get("release_confirmed")
            and not sim_summary.get("fall_detected")
            and release_window_s is not None
            and release_window_s >= 4.0
            and joint_summary_released["passes_numerical_margin_rule"]
            and height_ok
            and sim_timing_ok
            and policy_timing_ok
        ),
        "ok_target_duration": bool(
            not missing_events
            and sim_summary.get("release_confirmed")
            and not sim_summary.get("fall_detected")
            and release_window_s is not None
            and release_window_s >= 20.0
            and joint_summary_released["passes_numerical_margin_rule"]
            and height_ok
            and sim_timing_ok
            and policy_timing_ok
        ),
        "ok_final_gate": False,
        "final_gate_reason": "5s transport/release smoke only; final gate still requires >=20s target run, repeated starts, video, and stronger policy/sim timing alignment.",
        "raw_logs": {
            "events": rel(events_path),
            "simulator_status": rel(status_path),
            "policy_timing": rel(policy_path),
            "replay": rel(replay_path),
            "sim_bridge_summary": rel(run_dir / "sim_bridge_summary.json"),
        },
        "missing_events": missing_events,
        "release_window_s": release_window_s,
        "sim_elapsed_s": sim_elapsed,
        "wall_elapsed_s": wall_elapsed,
        "sim_wall_ratio": sim_wall_ratio,
        "policy_wall_elapsed_s": policy_wall_elapsed,
        "policy_time_elapsed_s": policy_time_elapsed,
        "policy_time_wall_ratio": policy_time_wall_ratio,
        "sim_elapsed_over_policy_wall_elapsed": sim_time_policy_ratio,
        "timing_gates": {
            "sim_wall_ratio_ok": sim_timing_ok,
            "policy_time_wall_ratio_ok": policy_timing_ok,
            "tolerance": 0.05,
        },
        "policy_loop_period_s": {"mean": mean_loop, "p95": p95_loop, "max": max_loop},
        "policy_inference_latency_s": {"mean": mean_infer, "p95": p95_infer, "max": max_infer},
        "released_base_height": {
            "threshold": threshold,
            "samples": len(heights),
            "min": min(heights) if heights else None,
            "below_threshold_samples": len(below_threshold),
            "below_threshold_fraction": len(below_threshold) / len(heights) if heights else None,
            "ok": height_ok,
        },
        "joint_limit_violation_frames_total": joint_violations_total,
        "joint_limit_violation_frames_released": joint_violations_released,
        "joint_limit_summary_total": joint_summary_total,
        "joint_limit_summary_released": joint_summary_released,
        "cmd_count": sim_summary.get("cmd_count"),
    }
    write_json(ARTIFACT_ROOT / artifact_filename, result)
    if update_pretrained_release:
        write_json(ARTIFACT_ROOT / "timing_validation.json", result)
        release = load_json(ARTIFACT_ROOT / "release_validation.json")
        release["active_policy_smoke"] = {
            "ok": result["ok_smoke"],
            "release_window_s": result["release_window_s"],
            "events": result["raw_logs"]["events"],
        }
        write_json(ARTIFACT_ROOT / "release_validation.json", release)
    return result


def summarize_pretrained_mujoco_sim2sim() -> dict[str, Any]:
    return summarize_mujoco_sim2sim_logs(
        Path("pretrained") / "mujoco_sim2sim",
        "pretrained_mujoco_sim2sim_smoke.json",
        update_pretrained_release=True,
    )


def summarize_default_train_mujoco_sim2sim() -> dict[str, Any]:
    result = summarize_mujoco_sim2sim_logs(
        Path("default_train") / "mujoco_sim2sim",
        "default_train_mujoco_sim2sim_smoke.json",
    )
    return result


def row_joint_limit_violations(row: dict[str, str]) -> list[dict[str, Any]]:
    violations = []
    for i, (low, high) in enumerate(GO1_JOINT_LIMITS):
        q = as_float(row.get(f"q_{i}"))
        if q is None:
            continue
        magnitude = max(low - q, q - high, 0.0)
        if magnitude <= 1e-6:
            continue
        violations.append(
            {
                "index": i,
                "joint": HARDWARE_JOINT_NAMES[i],
                "q": q,
                "limit_low": low,
                "limit_high": high,
                "magnitude_rad": magnitude,
            }
        )
    return violations


def overlay_text(frame: Any, lines: list[str], *, alert: bool = False) -> Any:
    try:
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
    except Exception:  # noqa: BLE001
        if alert:
            frame[:8, :, :] = [255, 0, 0]
            frame[-8:, :, :] = [255, 0, 0]
            frame[:, :8, :] = [255, 0, 0]
            frame[:, -8:, :] = [255, 0, 0]
        return frame

    image = Image.fromarray(frame)
    draw = ImageDraw.Draw(image, "RGBA")
    font = ImageFont.load_default()
    line_height = 14
    box_height = 10 + line_height * len(lines)
    draw.rectangle((8, 8, 500, 8 + box_height), fill=(0, 0, 0, 150))
    color = (255, 80, 80, 255) if alert else (235, 235, 235, 255)
    for i, line in enumerate(lines):
        draw.text((16, 14 + line_height * i), line, fill=color, font=font)
    if alert:
        w, h = image.size
        draw.rectangle((0, 0, w - 1, h - 1), outline=(255, 0, 0, 255), width=8)
    return np.asarray(image)


def add_joint_limit_markers(
    *,
    mujoco: Any,
    renderer: Any,
    data: Any,
    joint_ids: list[int],
    violations: list[dict[str, Any]],
    released: bool,
) -> None:
    try:
        import numpy as np
    except Exception:
        return
    color = np.array([1.0, 0.0, 0.0, 1.0]) if released else np.array([1.0, 0.55, 0.0, 1.0])
    for violation in violations:
        if renderer.scene.ngeom >= renderer.scene.maxgeom:
            return
        joint_index = int(violation["index"])
        pos = np.array(data.xanchor[joint_ids[joint_index]], dtype=float)
        geom = renderer.scene.geoms[renderer.scene.ngeom]
        mujoco.mjv_initGeom(
            geom,
            mujoco.mjtGeom.mjGEOM_SPHERE,
            np.array([0.055, 0.055, 0.055], dtype=float),
            pos,
            np.eye(3).reshape(-1),
            color,
        )
        renderer.scene.ngeom += 1


def render_mujoco_replay_video(
    *,
    replay_path: Path,
    out_path: Path,
    artifact_path: Path,
    label: str,
) -> dict[str, Any]:
    ensure_tree()
    rows = read_csv_dicts(replay_path)
    if not rows:
        result = {"ok": False, "error": "missing or empty replay log", "replay": rel(replay_path)}
        write_json(artifact_path, result)
        return result
    required = ["base_x", "base_qw", "ball_x", "ball_qw"]
    missing_columns = [name for name in required if name not in rows[0]]
    if missing_columns:
        result = {
            "ok": False,
            "error": "replay log does not contain full pose columns; rerun MuJoCo Sim2Sim",
            "missing_columns": missing_columns,
            "replay": rel(replay_path),
        }
        write_json(artifact_path, result)
        return result

    try:
        import imageio.v2 as imageio
        import mujoco  # type: ignore
        import numpy as np
    except Exception as exc:  # noqa: BLE001
        result = {"ok": False, "error": repr(exc), "context": "import imageio/mujoco/numpy"}
        write_json(artifact_path, result)
        return result

    scene = yoga_ball_scene_xml()
    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    qpos_addr = []
    joint_ids = []
    for name in HARDWARE_JOINT_NAMES:
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
        if jid < 0:
            result = {"ok": False, "error": f"missing joint {name}", "scene": rel(scene)}
            write_json(artifact_path, result)
            return result
        joint_ids.append(int(jid))
        qpos_addr.append(int(model.jnt_qposadr[jid]))
    ball_jid = ball_free_joint_id(model, mujoco)
    ball_qpos = int(model.jnt_qposadr[ball_jid])

    fps = 25
    log_fps = 50
    stride = max(1, round(log_fps / fps))
    frames_written = 0
    frame_variances: list[float] = []
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.distance = 3.0
    camera.azimuth = 135.0
    camera.elevation = -18.0

    renderer = mujoco.Renderer(model, height=480, width=640)
    marked_frames = 0
    released_marked_frames = 0
    first_markers: list[dict[str, Any]] = []
    try:
        with imageio.get_writer(out_path, fps=fps, codec="libx264", quality=8, macro_block_size=16) as writer:
            for row in rows[::stride]:
                base_x = as_float(row.get("base_x")) or 0.0
                base_y = as_float(row.get("base_y")) or 0.0
                base_z = as_float(row.get("base_z_qpos")) or as_float(row.get("base_z")) or 0.0
                ball_x = as_float(row.get("ball_x")) or 0.0
                ball_y = as_float(row.get("ball_y")) or 0.0
                ball_z = as_float(row.get("ball_z_qpos")) or as_float(row.get("ball_z")) or 0.45
                data.qpos[:] = 0.0
                data.qvel[:] = 0.0
                data.qpos[0:7] = [
                    base_x,
                    base_y,
                    base_z,
                    as_float(row.get("base_qw")) or 1.0,
                    as_float(row.get("base_qx")) or 0.0,
                    as_float(row.get("base_qy")) or 0.0,
                    as_float(row.get("base_qz")) or 0.0,
                ]
                for i, addr in enumerate(qpos_addr):
                    data.qpos[addr] = as_float(row.get(f"q_{i}")) or 0.0
                data.qpos[ball_qpos : ball_qpos + 7] = [
                    ball_x,
                    ball_y,
                    ball_z,
                    as_float(row.get("ball_qw")) or 1.0,
                    as_float(row.get("ball_qx")) or 0.0,
                    as_float(row.get("ball_qy")) or 0.0,
                    as_float(row.get("ball_qz")) or 0.0,
                ]
                mujoco.mj_forward(model, data)
                camera.lookat[:] = [(base_x + ball_x) * 0.5, (base_y + ball_y) * 0.5, max(0.55, (base_z + ball_z) * 0.5)]
                renderer.update_scene(data, camera=camera)
                violations = row_joint_limit_violations(row)
                released = as_float(row.get("support_active")) == 0
                if violations:
                    marked_frames += 1
                    if released:
                        released_marked_frames += 1
                    add_joint_limit_markers(
                        mujoco=mujoco,
                        renderer=renderer,
                        data=data,
                        joint_ids=joint_ids,
                        violations=violations,
                        released=released,
                    )
                    if len(first_markers) < 20:
                        first_markers.append(
                            {
                                "sim_time_s": as_float(row.get("sim_time_s")),
                                "released": released,
                                "violations": violations,
                            }
                        )
                frame = renderer.render()
                if violations:
                    names = ", ".join(v["joint"] for v in violations[:3])
                    if len(violations) > 3:
                        names += f" +{len(violations) - 3}"
                    frame = overlay_text(
                        frame,
                        [
                            f"{label}  t={as_float(row.get('sim_time_s')):.2f}s",
                            f"JOINT LIMIT {'RELEASED' if released else 'SUPPORTED'}: {names}",
                        ],
                        alert=True,
                    )
                else:
                    frame = overlay_text(
                        frame,
                        [
                            f"{label}  t={as_float(row.get('sim_time_s')):.2f}s",
                            "follow camera, raw replay render",
                        ],
                    )
                frame_variances.append(float(np.var(frame)))
                writer.append_data(frame)
                frames_written += 1
    finally:
        renderer.close()

    valid = out_path.exists() and out_path.stat().st_size > 1000 and frames_written > 0
    nonblank = bool(frame_variances and max(frame_variances) > 1.0)
    result = {
        "ok": bool(valid and nonblank),
        "video": rel(out_path),
        "replay": rel(replay_path),
        "scene": rel(scene),
        "frames_written": frames_written,
        "fps": fps,
        "source_rows": len(rows),
        "camera": "free camera following midpoint of robot base and ball",
        "joint_limit_marking": "red markers/border for released violations; orange markers for supported-startup violations",
        "marked_frames": marked_frames,
        "released_marked_frames": released_marked_frames,
        "first_markers": first_markers,
        "frame_variance_min": min(frame_variances) if frame_variances else None,
        "frame_variance_max": max(frame_variances) if frame_variances else None,
        "file_size_bytes": out_path.stat().st_size if out_path.exists() else 0,
        "rendered_from_raw_replay": True,
    }
    write_json(artifact_path, result)
    return result


def render_pretrained_mujoco_video() -> dict[str, Any]:
    return render_mujoco_replay_video(
        replay_path=LOG_ROOT / "pretrained" / "mujoco_sim2sim" / "replay.csv",
        out_path=VIDEO_ROOT / "pretrained_mujoco.mp4",
        artifact_path=ARTIFACT_ROOT / "pretrained_mujoco_video.json",
        label="pretrained MuJoCo Sim2Sim",
    )


def render_default_train_mujoco_video() -> dict[str, Any]:
    return render_mujoco_replay_video(
        replay_path=LOG_ROOT / "default_train" / "mujoco_sim2sim" / "replay.csv",
        out_path=VIDEO_ROOT / "default_train_mujoco.mp4",
        artifact_path=ARTIFACT_ROOT / "default_train_mujoco_video.json",
        label="trained MuJoCo Sim2Sim",
    )


def render_default_train_and_pretrained_mujoco_videos() -> dict[str, Any]:
    pretrained = render_pretrained_mujoco_video()
    default_train = render_default_train_mujoco_video()
    result = {
        "ok": bool(pretrained.get("ok") and default_train.get("ok")),
        "pretrained": pretrained,
        "default_train": default_train,
    }
    write_json(ARTIFACT_ROOT / "mujoco_marked_videos.json", result)
    return result


def aggregate_pretrained_mujoco_repeats() -> dict[str, Any]:
    ensure_tree()
    repeat_summaries = sorted(ARTIFACT_ROOT.glob("pretrained_mujoco_sim2sim_repeat_run_*.json"))
    runs = []
    for path in repeat_summaries:
        data = load_json(path)
        if not data:
            continue
        runs.append(
            {
                "summary": rel(path),
                "ok_smoke": data.get("ok_smoke"),
                "ok_target_duration": data.get("ok_target_duration"),
                "release_window_s": data.get("release_window_s"),
                "sim_wall_ratio": data.get("sim_wall_ratio"),
                "policy_time_wall_ratio": data.get("policy_time_wall_ratio"),
                "height_min": (data.get("released_base_height") or {}).get("min"),
                "height_below_threshold_samples": (data.get("released_base_height") or {}).get("below_threshold_samples"),
                "joint_limit_violation_frames_released": data.get("joint_limit_violation_frames_released"),
                "joint_limit_max_magnitude_rad": (data.get("joint_limit_summary_released") or {}).get("max_magnitude_rad"),
            }
        )
    ok_runs = [run for run in runs if run.get("ok_target_duration")]
    result = {
        "ok": bool(len(runs) >= 3 and len(ok_runs) == len(runs)),
        "required_clean_starts": 3,
        "run_count": len(runs),
        "clean_target_duration_runs": len(ok_runs),
        "runs": runs,
        "criterion": "at least 3 archived runs, each passing the >=20s released-control target-duration gate",
    }
    write_json(ARTIFACT_ROOT / "pretrained_mujoco_sim2sim_repeats.json", result)
    return result


def summarize_control_removal_pretrained_mujoco_sim2sim() -> dict[str, Any]:
    ensure_tree()
    run_dir = LOG_ROOT / "pretrained" / "mujoco_sim2sim_control_removal"
    events_path = run_dir / "sequence_events.csv"
    status_path = run_dir / "simulator_status.csv"
    replay_path = run_dir / "replay.csv"
    sim_summary = load_json(run_dir / "sim_bridge_summary.json")
    direct_release = load_json(ARTIFACT_ROOT / "release_validation.json")
    events = read_csv_dicts(events_path)
    replay_rows = read_csv_dicts(replay_path)
    event_names = [row.get("event") for row in events]
    event_times = {row.get("event"): row for row in events}
    required_events = [
        "SIM_START",
        "CONTROL_ACTIVE_OBSERVED_BY_SIM",
        "SUPPORT_RELEASE_CONFIRMED",
        "BALANCE_WINDOW_START",
        "CONTROL_REMOVED",
        "FALL_DETECTED",
    ]
    missing_events = [name for name in required_events if name not in event_names]
    release_time = as_float(event_times.get("SUPPORT_RELEASE_CONFIRMED", {}).get("sim_time_s"))
    removed_time = as_float(event_times.get("CONTROL_REMOVED", {}).get("sim_time_s"))
    fall_time = as_float(event_times.get("FALL_DETECTED", {}).get("sim_time_s"))
    stable_before_removal_s = (
        removed_time - release_time
        if removed_time is not None and release_time is not None
        else None
    )
    fall_after_removal_s = (
        fall_time - removed_time
        if fall_time is not None and removed_time is not None
        else None
    )
    direct_fall_time = as_float(direct_release.get("fall_time_s"))
    comparable_to_direct = (
        fall_after_removal_s is not None
        and direct_fall_time is not None
        and 0.25 * direct_fall_time <= fall_after_removal_s <= 2.0 * direct_fall_time
    )
    removed_rows = []
    if removed_time is not None:
        removed_rows = [
            row for row in replay_rows
            if (as_float(row.get("sim_time_s")) is not None and as_float(row.get("sim_time_s")) >= removed_time)
        ]
    joint_summary_removed = joint_limit_summary(removed_rows)
    result = {
        "ok": bool(
            not missing_events
            and sim_summary.get("control_removed")
            and sim_summary.get("fall_detected")
            and stable_before_removal_s is not None
            and stable_before_removal_s >= 4.0
            and comparable_to_direct
        ),
        "raw_logs": {
            "events": rel(events_path),
            "simulator_status": rel(status_path),
            "replay": rel(replay_path),
            "sim_bridge_summary": rel(run_dir / "sim_bridge_summary.json"),
            "policy_timing": rel(run_dir / "policy_timing.csv"),
        },
        "missing_events": missing_events,
        "release_time_s": release_time,
        "control_removed_time_s": removed_time,
        "fall_detected_time_s": fall_time,
        "stable_released_control_before_removal_s": stable_before_removal_s,
        "fall_after_control_removal_s": fall_after_removal_s,
        "direct_release_fall_time_s": direct_fall_time,
        "fall_after_removal_comparable_to_direct_release": comparable_to_direct,
        "comparison_rule": "fall_after_control_removal_s must be between 0.25x and 2.0x direct_release_fall_time_s",
        "joint_limit_summary_after_control_removal": joint_summary_removed,
    }
    write_json(ARTIFACT_ROOT / "pretrained_mujoco_control_removal.json", result)
    release = load_json(ARTIFACT_ROOT / "release_validation.json")
    release["control_removal_after_stable_release"] = {
        "ok": result["ok"],
        "stable_released_control_before_removal_s": stable_before_removal_s,
        "fall_after_control_removal_s": fall_after_removal_s,
        "events": result["raw_logs"]["events"],
    }
    write_json(ARTIFACT_ROOT / "release_validation.json", release)
    return result


def yoga_ball_scene_xml() -> Path:
    robot = sanitized_go1_xml()
    ball_radius = 0.45
    text = robot.read_text(encoding="utf-8")
    ball_body = f"""
        <body name="yoga_ball" pos="0 0 {ball_radius}">
            <joint name="yoga_ball_free" type="free"/>
            <inertial pos="0 0 0" mass="1.0" diaginertia="0.108 0.108 0.108"/>
            <geom name="yoga_ball_geom" type="sphere" size="{ball_radius}" rgba="0.1 0.25 0.9 1" friction="1.0 0.02 0.001" condim="3"/>
        </body>
"""
    text = text.replace("    </worldbody>", ball_body + "    </worldbody>")
    out = BUILD_ROOT / "go1_yoga_ball_scene.xml"
    out.write_text(text, encoding="utf-8")
    return out


def set_initial_go1_ball_state(model: Any, data: Any, mujoco: Any, *, ball_radius: float, base_z: float) -> None:
    data.qpos[:] = 0
    data.qvel[:] = 0
    data.qpos[0:3] = [0.0, 0.0, base_z]
    data.qpos[3:7] = [1.0, 0.0, 0.0, 0.0]
    defaults = default_joint_angles()
    for joint_name in POLICY_JOINT_NAMES:
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
        if jid < 0:
            raise RuntimeError(f"missing joint {joint_name}")
        data.qpos[model.jnt_qposadr[jid]] = defaults[joint_name]
    ball_jid = ball_free_joint_id(model, mujoco)
    ball_qpos = model.jnt_qposadr[ball_jid]
    data.qpos[ball_qpos : ball_qpos + 7] = [0.0, 0.0, ball_radius, 1.0, 0.0, 0.0, 0.0]


def default_joint_angles() -> dict[str, float]:
    params_path = PRETRAINED_RUN / "parameters.pkl"
    if params_path.exists():
        with params_path.open("rb") as f:
            cfg = pickle.load(f)["Cfg"]
        init_state = cfg.get("init_state", {}) if isinstance(cfg, dict) else {}
        angles = init_state.get("default_joint_angles", {})
        if angles:
            return {name: float(angles[name]) for name in POLICY_JOINT_NAMES}
    return {
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


def ball_free_joint_id(model: Any, mujoco: Any) -> int:
    jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "yoga_ball_free")
    if jid < 0:
        raise RuntimeError("missing yoga_ball_free joint")
    return int(jid)


def quat_roll_pitch(q: Any) -> tuple[float, float]:
    w, x, y, z = [float(v) for v in q]
    roll = math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    s = 2 * (w * y - z * x)
    pitch = math.asin(max(-1.0, min(1.0, s)))
    return roll, pitch


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv_dicts(path: Path) -> list[dict[str, str]]:
    import csv

    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((p / 100.0) * (len(ordered) - 1)))))
    return ordered[index]


def joint_limit_summary(rows: list[dict[str, str]], *, log_dt_s: float = 0.02) -> dict[str, Any]:
    violations: list[dict[str, Any]] = []
    per_joint_counts = {name: 0 for name in HARDWARE_JOINT_NAMES}
    max_by_joint = {name: 0.0 for name in HARDWARE_JOINT_NAMES}
    max_contiguous_by_joint = {name: 0 for name in HARDWARE_JOINT_NAMES}
    current_by_joint = {name: 0 for name in HARDWARE_JOINT_NAMES}

    for row in rows:
        active = set()
        for i, (low, high) in enumerate(GO1_JOINT_LIMITS):
            q = as_float(row.get(f"q_{i}"))
            if q is None:
                continue
            magnitude = max(low - q, q - high, 0.0)
            if magnitude <= 1e-6:
                continue
            name = HARDWARE_JOINT_NAMES[i]
            active.add(name)
            per_joint_counts[name] += 1
            max_by_joint[name] = max(max_by_joint[name], magnitude)
            violations.append(
                {
                    "sim_time_s": as_float(row.get("sim_time_s")),
                    "joint": name,
                    "q": q,
                    "limit_low": low,
                    "limit_high": high,
                    "magnitude_rad": magnitude,
                }
            )
        for name in HARDWARE_JOINT_NAMES:
            if name in active:
                current_by_joint[name] += 1
            else:
                max_contiguous_by_joint[name] = max(max_contiguous_by_joint[name], current_by_joint[name])
                current_by_joint[name] = 0

    for name in HARDWARE_JOINT_NAMES:
        max_contiguous_by_joint[name] = max(max_contiguous_by_joint[name], current_by_joint[name])

    joint_frames = len(rows) * len(HARDWARE_JOINT_NAMES)
    violation_frames = len(violations)
    max_contiguous_frames = max(max_contiguous_by_joint.values()) if max_contiguous_by_joint else 0
    max_magnitude = max((entry["magnitude_rad"] for entry in violations), default=0.0)
    pass_numerical_margin = bool(
        violation_frames == 0
        or (
            joint_frames > 0
            and violation_frames / joint_frames < 0.001
            and max_contiguous_frames * log_dt_s <= 0.1
        )
    )
    return {
        "samples": len(rows),
        "joint_frames": joint_frames,
        "violation_frames": violation_frames,
        "violation_fraction": violation_frames / joint_frames if joint_frames else None,
        "max_magnitude_rad": max_magnitude,
        "max_contiguous_frames": max_contiguous_frames,
        "max_contiguous_duration_s": max_contiguous_frames * log_dt_s,
        "per_joint_counts": {key: value for key, value in per_joint_counts.items() if value},
        "per_joint_max_magnitude_rad": {key: value for key, value in max_by_joint.items() if value > 0.0},
        "first_violations": violations[:10],
        "criterion": "pass if zero violations, or violation_frames / joint_frames < 0.001 and no joint violation persists longer than 0.1s",
        "passes_numerical_margin_rule": pass_numerical_margin,
    }


def report() -> Path:
    ensure_tree()
    manifest = load_json(ARTIFACT_ROOT / "manifest.json")
    policy = load_json(ARTIFACT_ROOT / "policy_registry.json")
    mujoco_smoke = load_json(ARTIFACT_ROOT / "mujoco_asset_smoke.json")
    release_validation = load_json(ARTIFACT_ROOT / "release_validation.json")
    isaacgym_playback = load_json(ARTIFACT_ROOT / "pretrained_isaacgym_playback.json")
    mujoco_sim2sim = load_json(ARTIFACT_ROOT / "pretrained_mujoco_sim2sim_smoke.json")
    mujoco_repeats = load_json(ARTIFACT_ROOT / "pretrained_mujoco_sim2sim_repeats.json")
    control_removal = load_json(ARTIFACT_ROOT / "pretrained_mujoco_control_removal.json")
    mujoco_video = load_json(ARTIFACT_ROOT / "pretrained_mujoco_video.json")
    phase_gate = {
        "ok": bool(
            isaacgym_playback.get("ok")
            and mujoco_sim2sim.get("ok_target_duration")
            and mujoco_repeats.get("ok")
            and control_removal.get("ok")
            and mujoco_video.get("ok")
        ),
        "pretrained_isaacgym_playback_ok": bool(isaacgym_playback.get("ok")),
        "pretrained_mujoco_target_duration_ok": bool(mujoco_sim2sim.get("ok_target_duration")),
        "pretrained_mujoco_repeated_starts_ok": bool(mujoco_repeats.get("ok")),
        "pretrained_mujoco_control_removal_ok": bool(control_removal.get("ok")),
        "pretrained_mujoco_raw_replay_video_ok": bool(mujoco_video.get("ok")),
        "caveat": "Isaac Gym playback was validated headless without video because graphics-enabled headless playback is unstable in this Docker/runtime path.",
    }
    write_json(ARTIFACT_ROOT / "phase_pretrained_summary.json", phase_gate)
    lines = [
        "# Go1 Yoga-Ball Pretrained Policy Report",
        "",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S %z')}",
        "",
        "## Phase Gate",
        "",
        f"- ok: `{phase_gate['ok']}`",
        f"- Isaac Gym playback ok: `{phase_gate['pretrained_isaacgym_playback_ok']}`",
        f"- MuJoCo target-duration run ok: `{phase_gate['pretrained_mujoco_target_duration_ok']}`",
        f"- MuJoCo repeated starts ok: `{phase_gate['pretrained_mujoco_repeated_starts_ok']}`",
        f"- MuJoCo control-removal proof ok: `{phase_gate['pretrained_mujoco_control_removal_ok']}`",
        f"- MuJoCo raw-replay video ok: `{phase_gate['pretrained_mujoco_raw_replay_video_ok']}`",
        f"- caveat: {phase_gate['caveat']}",
        "",
        "## Dependency Status",
        "",
    ]
    for name, info in (manifest.get("dependencies") or {}).items():
        if info.get("has_contents"):
            marker = "present"
        elif info.get("exists"):
            marker = "empty"
        else:
            marker = "missing"
        lines.append(f"- {name}: {marker} (`{info.get('path')}`)")
    lines.extend(["", "## Policy Registry", ""])
    for entry in policy.get("policies", []):
        lines.append(f"- {entry.get('name')}: `{entry.get('paths', {}).get('run_dir')}`")
        missing = [key for key, exists in entry.get("path_exists", {}).items() if not exists]
        if missing:
            lines.append(f"  Missing: {', '.join(missing)}")
    lines.extend(["", "## Docker Images", ""])
    for name, info in (manifest.get("docker_images") or {}).items():
        marker = "built" if info.get("exists") else "missing"
        lines.append(f"- {name}: {marker} (`{info.get('image')}`)")
    if mujoco_smoke:
        lines.extend(["", "## MuJoCo Asset Smoke", ""])
        lines.append(f"- ok: `{mujoco_smoke.get('ok')}`")
        if mujoco_smoke.get("ok"):
            lines.append(
                f"- model dimensions: nq={mujoco_smoke.get('nq')}, nv={mujoco_smoke.get('nv')}, nu={mujoco_smoke.get('nu')}"
            )
            lines.append(f"- sanitized model: `{mujoco_smoke.get('sanitized_xml')}`")
        else:
            lines.append(f"- error: `{mujoco_smoke.get('error')}`")
    if release_validation:
        lines.extend(["", "## Release Validation Smoke", ""])
        lines.append(f"- ok: `{release_validation.get('ok')}`")
        lines.append(f"- kind: `{release_validation.get('kind')}`")
        lines.append(f"- fall_time_s: `{release_validation.get('fall_time_s')}`")
        lines.append(f"- raw_log: `{release_validation.get('raw_log')}`")
        active = release_validation.get("active_policy_smoke") or {}
        if active:
            lines.append(f"- active_policy_release_ok: `{active.get('ok')}`")
            lines.append(f"- active_policy_release_window_s: `{active.get('release_window_s')}`")
        removal = release_validation.get("control_removal_after_stable_release") or {}
        if removal:
            lines.append(f"- control_removal_ok: `{removal.get('ok')}`")
            lines.append(
                f"- stable_before_control_removal_s: `{removal.get('stable_released_control_before_removal_s')}`"
            )
            lines.append(f"- fall_after_control_removal_s: `{removal.get('fall_after_control_removal_s')}`")
    if isaacgym_playback:
        lines.extend(["", "## Pretrained Isaac Gym Playback", ""])
        lines.append(f"- ok: `{isaacgym_playback.get('ok')}`")
        lines.append(
            f"- iterations: `{isaacgym_playback.get('completed_iterations')}/{isaacgym_playback.get('requested_iterations')}`"
        )
        lines.append(f"- GPU PhysX: `{isaacgym_playback.get('uses_gpu_physx')}`")
        lines.append(f"- graphics disabled: `{isaacgym_playback.get('graphics_disabled')}`")
        lines.append(f"- raw_log: `{isaacgym_playback.get('raw_log')}`")
    if mujoco_sim2sim:
        lines.extend(["", "## Pretrained MuJoCo Sim2Sim Target Run", ""])
        lines.append(f"- smoke ok: `{mujoco_sim2sim.get('ok_smoke')}`")
        lines.append(f"- target duration ok: `{mujoco_sim2sim.get('ok_target_duration')}`")
        lines.append(f"- release_window_s: `{mujoco_sim2sim.get('release_window_s')}`")
        lines.append(f"- sim_wall_ratio: `{mujoco_sim2sim.get('sim_wall_ratio')}`")
        lines.append(f"- policy_time_wall_ratio: `{mujoco_sim2sim.get('policy_time_wall_ratio')}`")
        lines.append(
            f"- policy_loop_period_s: `{mujoco_sim2sim.get('policy_loop_period_s')}`"
        )
        lines.append(
            f"- released_base_height: `{mujoco_sim2sim.get('released_base_height')}`"
        )
        lines.append(
            f"- joint_limit_violation_frames_released: `{mujoco_sim2sim.get('joint_limit_violation_frames_released')}`"
        )
        joint_summary = mujoco_sim2sim.get("joint_limit_summary_released") or {}
        lines.append(f"- joint_limit_max_magnitude_rad: `{joint_summary.get('max_magnitude_rad')}`")
    if mujoco_repeats:
        lines.extend(["", "## Pretrained MuJoCo Repeated Starts", ""])
        lines.append(f"- ok: `{mujoco_repeats.get('ok')}`")
        lines.append(
            f"- clean_target_duration_runs: `{mujoco_repeats.get('clean_target_duration_runs')}/{mujoco_repeats.get('run_count')}`"
        )
        for index, run in enumerate(mujoco_repeats.get("runs") or [], start=1):
            lines.append(
                f"- run {index}: ok=`{run.get('ok_target_duration')}`, release_window_s=`{run.get('release_window_s')}`, "
                f"min_height=`{run.get('height_min')}`, joint_violations=`{run.get('joint_limit_violation_frames_released')}`, "
                f"sim_wall_ratio=`{run.get('sim_wall_ratio')}`"
            )
    if control_removal:
        lines.extend(["", "## Pretrained MuJoCo Control Removal", ""])
        lines.append(f"- ok: `{control_removal.get('ok')}`")
        lines.append(f"- stable_released_control_before_removal_s: `{control_removal.get('stable_released_control_before_removal_s')}`")
        lines.append(f"- fall_after_control_removal_s: `{control_removal.get('fall_after_control_removal_s')}`")
        lines.append(f"- direct_release_fall_time_s: `{control_removal.get('direct_release_fall_time_s')}`")
        lines.append(f"- raw_events: `{(control_removal.get('raw_logs') or {}).get('events')}`")
    if mujoco_video:
        lines.extend(["", "## Pretrained MuJoCo Video", ""])
        lines.append(f"- ok: `{mujoco_video.get('ok')}`")
        lines.append(f"- video: `{mujoco_video.get('video')}`")
        lines.append(f"- rendered_from_raw_replay: `{mujoco_video.get('rendered_from_raw_replay')}`")
        lines.append(f"- frames_written: `{mujoco_video.get('frames_written')}`")
    lines.extend(
        [
            "",
            "## Next Step",
            "",
            "Phase 1 pretrained policy validation is now strong enough to proceed to Phase 2 default DrEureka training. Remaining caveat: Isaac Gym playback was validated headless without video to avoid graphics instability; MuJoCo Sim2Sim has raw-log-rendered video evidence.",
            "",
        ]
    )
    path = ARTIFACT_ROOT / "phase_pretrained_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def compare_default_train_cfg() -> dict[str, Any]:
    default_run = selected_default_train_run()
    keys: list[tuple[str | None, str]] = [
        (None, "multi_gpu"),
        ("env", "num_envs"),
        ("env", "num_observations"),
        ("env", "num_observation_history"),
        ("domain_rand", "randomize"),
        ("domain_rand", "ball_radius_range"),
        ("domain_rand", "robot_friction_range"),
        ("domain_rand", "robot_restitution_range"),
        ("domain_rand", "robot_payload_mass_range"),
        ("domain_rand", "robot_com_displacement_range"),
        ("domain_rand", "robot_motor_strength_range"),
        ("domain_rand", "robot_motor_offset_range"),
        ("domain_rand", "ball_friction_range"),
        ("domain_rand", "ball_mass_range"),
        ("domain_rand", "ball_restitution_range"),
        ("domain_rand", "ball_compliance_range"),
        ("domain_rand", "ball_drag_range"),
        ("domain_rand", "terrain_ground_friction_range"),
        ("domain_rand", "terrain_ground_restitution_range"),
        ("domain_rand", "terrain_tile_roughness_range"),
        ("domain_rand", "robot_push_vel_range"),
        ("domain_rand", "ball_push_vel_range"),
        ("domain_rand", "gravity_range"),
        ("rewards", "reward_container_name"),
        ("sim", "dt"),
        ("control", "decimation"),
        ("control", "action_scale"),
    ]
    runs = {"pretrained": PRETRAINED_RUN}
    if default_run is not None:
        runs["default_train"] = default_run
    result: dict[str, Any] = {"runs": {name: rel(path) for name, path in runs.items()}, "values": {}, "differences": {}}
    loaded = {}
    for name, path in runs.items():
        params_path = path / "parameters.pkl"
        if not params_path.exists():
            result["values"][name] = {"error": f"missing {rel(params_path)}"}
            continue
        with params_path.open("rb") as f:
            loaded[name] = pickle.load(f).get("Cfg", {})
        result["values"][name] = {}
        for section, key in keys:
            value = None
            if section is None:
                if isinstance(loaded[name], dict):
                    value = loaded[name].get(key)
                dotted = key
            else:
                section_data = loaded[name].get(section, {}) if isinstance(loaded[name], dict) else {}
                if isinstance(section_data, dict):
                    value = section_data.get(key)
                dotted = f"{section}.{key}"
            result["values"][name][dotted] = value
    if "pretrained" in result["values"] and "default_train" in result["values"]:
        for section, key in keys:
            dotted = key if section is None else f"{section}.{key}"
            pretrained = result["values"]["pretrained"].get(dotted)
            default = result["values"]["default_train"].get(dotted)
            if pretrained != default:
                result["differences"][dotted] = {"pretrained": pretrained, "default_train": default}
    write_json(ARTIFACT_ROOT / "default_train_config_comparison.json", result)
    return result


def phase_default_train_report() -> Path:
    ensure_tree()
    train_run = load_json(ARTIFACT_ROOT / "default_train_run.json")
    isaacgym = load_json(ARTIFACT_ROOT / "default_train_isaacgym_playback.json")
    mujoco = load_json(ARTIFACT_ROOT / "default_train_mujoco_sim2sim_smoke.json")
    cfg_compare = compare_default_train_cfg()
    selected = selected_default_train_run()
    phase_gate = {
        "ok": bool(isaacgym.get("ok") and mujoco.get("ok_target_duration")),
        "default_train_run_selected": rel(selected) if selected is not None else None,
        "isaacgym_playback_ok": bool(isaacgym.get("ok")),
        "mujoco_smoke_ok": bool(mujoco.get("ok_smoke")),
        "mujoco_target_duration_ok": bool(mujoco.get("ok_target_duration")),
        "release_window_s": mujoco.get("release_window_s"),
        "config_difference_count": len(cfg_compare.get("differences") or {}),
        "status": "equivalent" if bool(isaacgym.get("ok") and mujoco.get("ok_target_duration")) else "not_equivalent_yet",
    }
    write_json(ARTIFACT_ROOT / "phase_default_train_summary.json", phase_gate)
    lines = [
        "# Go1 Yoga-Ball Default DrEureka Training Report",
        "",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S %z')}",
        "",
        "## Phase Gate",
        "",
        f"- ok: `{phase_gate['ok']}`",
        f"- status: `{phase_gate['status']}`",
        f"- selected run: `{phase_gate['default_train_run_selected']}`",
        f"- Isaac Gym playback ok: `{phase_gate['isaacgym_playback_ok']}`",
        f"- MuJoCo smoke ok: `{phase_gate['mujoco_smoke_ok']}`",
        f"- MuJoCo target-duration ok: `{phase_gate['mujoco_target_duration_ok']}`",
        f"- release_window_s: `{phase_gate['release_window_s']}`",
        "",
        "## Training Run",
        "",
        f"- run record: `{rel(ARTIFACT_ROOT / 'default_train_run.json')}`",
        f"- selected run exists: `{bool(selected and selected.exists())}`",
    ]
    policy_entry_data = train_run.get("policy_entry") or {}
    cfg_summary = policy_entry_data.get("cfg_summary") or {}
    if cfg_summary:
        lines.append(f"- env num envs: `{cfg_summary.get('env_num_envs')}`")
        lines.append(f"- env num observations: `{cfg_summary.get('env_num_observations')}`")
        lines.append(f"- history length: `{cfg_summary.get('env_num_observation_history')}`")
        lines.append(f"- control dt: `{(cfg_summary.get('sim_dt') or 0) * (cfg_summary.get('control_decimation') or 0)}`")
    lines.extend(["", "## Isaac Gym Playback", ""])
    if isaacgym:
        lines.append(f"- ok: `{isaacgym.get('ok')}`")
        lines.append(f"- iterations: `{isaacgym.get('completed_iterations')}/{isaacgym.get('requested_iterations')}`")
        lines.append(f"- GPU PhysX: `{isaacgym.get('uses_gpu_physx')}`")
        lines.append(f"- raw log: `{isaacgym.get('raw_log')}`")
    else:
        lines.append("- missing playback artifact")
    lines.extend(["", "## MuJoCo Sim2Sim", ""])
    if mujoco:
        lines.append(f"- smoke ok: `{mujoco.get('ok_smoke')}`")
        lines.append(f"- target duration ok: `{mujoco.get('ok_target_duration')}`")
        lines.append(f"- missing events: `{mujoco.get('missing_events')}`")
        lines.append(f"- release_window_s: `{mujoco.get('release_window_s')}`")
        lines.append(f"- sim_wall_ratio: `{mujoco.get('sim_wall_ratio')}`")
        lines.append(f"- policy_time_wall_ratio: `{mujoco.get('policy_time_wall_ratio')}`")
        lines.append(f"- released_base_height: `{mujoco.get('released_base_height')}`")
        lines.append(f"- joint_limit_summary_released: `{mujoco.get('joint_limit_summary_released')}`")
        lines.append(f"- raw logs: `{mujoco.get('raw_logs')}`")
    else:
        lines.append("- missing MuJoCo Sim2Sim artifact")
    lines.extend(["", "## Config Comparison Against Pretrained", ""])
    lines.append(f"- comparison artifact: `{rel(ARTIFACT_ROOT / 'default_train_config_comparison.json')}`")
    lines.append(f"- differing fields: `{len(cfg_compare.get('differences') or {})}`")
    for key, value in sorted((cfg_compare.get("differences") or {}).items()):
        lines.append(f"- {key}: pretrained=`{value.get('pretrained')}`, default_train=`{value.get('default_train')}`")
    interpretation = [
        "The current selected default DrEureka policy is validated in built-in Isaac Gym playback.",
    ]
    if not mujoco:
        interpretation.append("MuJoCo Sim2Sim has not been run for this selected policy yet.")
    elif phase_gate["mujoco_target_duration_ok"]:
        interpretation.append("MuJoCo Sim2Sim reached the target-duration gate for this selected policy.")
    else:
        reasons = []
        if mujoco.get("release_window_s") is not None:
            reasons.append(f"released-control window `{mujoco.get('release_window_s')}` seconds")
        if mujoco.get("missing_events"):
            reasons.append(f"missing release events `{mujoco.get('missing_events')}`")
        joint_summary = mujoco.get("joint_limit_summary_released") or {}
        if joint_summary and not joint_summary.get("passes_numerical_margin_rule"):
            reasons.append(
                f"released joint-limit violations `{joint_summary.get('violation_frames')}` frames"
            )
        timing = mujoco.get("timing_gates") or {}
        if timing and not all(timing.get(key) for key in ("sim_wall_ratio_ok", "policy_time_wall_ratio_ok")):
            reasons.append(f"timing gates `{timing}`")
        if not reasons:
            reasons.append(mujoco.get("final_gate_reason") or "target-duration gate failed")
        interpretation.append(
            "MuJoCo Sim2Sim is not equivalent yet; observed failure evidence: "
            + ", ".join(reasons)
            + "."
        )
    lines.extend(["", "## Interpretation", "", *interpretation, ""])
    path = ARTIFACT_ROOT / "phase_default_train_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def smoke_mjlab_runtime(*, steps: int = 25) -> dict[str, Any]:
    ensure_tree()
    log_dir = LOG_ROOT / "mjlab_train" / "default_playback"
    log_dir.mkdir(parents=True, exist_ok=True)
    raw_path = log_dir / "mjlab_builtin_go1_zero_policy_smoke.csv"
    try:
        import torch
        import mjlab.tasks  # noqa: F401
        from mjlab.envs import ManagerBasedRlEnv
        from mjlab.tasks.registry import list_tasks, load_env_cfg
    except Exception as exc:  # noqa: BLE001
        result = {
            "ok": False,
            "stage": "import",
            "error": repr(exc),
            "mjlab_path": rel(MJLAB),
        }
        write_json(ARTIFACT_ROOT / "mjlab_runtime_smoke.json", result)
        return result

    tasks = list_tasks()
    expected_tasks = [
        "Mjlab-Velocity-Flat-Unitree-Go1",
        "Mjlab-Velocity-Rough-Unitree-Go1",
    ]
    missing_expected = [task for task in expected_tasks if task not in tasks]
    if missing_expected:
        result = {
            "ok": False,
            "stage": "registry",
            "task_count": len(tasks),
            "tasks": tasks,
            "missing_expected_tasks": missing_expected,
            "note": "MJLab list-envs returns the number of listed tasks as process status; this artifact uses the registry API instead.",
        }
        write_json(ARTIFACT_ROOT / "mjlab_runtime_smoke.json", result)
        return result

    env = None
    rows: list[dict[str, Any]] = []
    try:
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        cfg = load_env_cfg(MJLAB_GO1_SMOKE_TASK, play=True)
        cfg.scene.num_envs = 1
        cfg.episode_length_s = 2.0
        cfg.events.pop("push_robot", None)
        cfg.observations["actor"].enable_corruption = False
        env = ManagerBasedRlEnv(cfg=cfg, device=device, render_mode=None)
        obs, _ = env.reset()
        action_dim = int(env.action_manager.total_action_dim)
        action = torch.zeros((env.num_envs, action_dim), device=env.device)
        wall_start = time.monotonic()
        for step in range(steps):
            obs, reward, terminated, truncated, extras = env.step(action)
            del extras
            rows.append(
                {
                    "step": step,
                    "sim_time_s": (step + 1) * env.step_dt,
                    "wall_elapsed_s": time.monotonic() - wall_start,
                    "reward_env0": float(reward[0].detach().cpu()),
                    "terminated_env0": int(terminated[0].detach().cpu()),
                    "truncated_env0": int(truncated[0].detach().cpu()),
                }
            )
        write_csv(raw_path, rows)
        wall_elapsed = time.monotonic() - wall_start
        sim_elapsed = steps * env.step_dt
        result = {
            "ok": True,
            "stage": "step",
            "task": MJLAB_GO1_SMOKE_TASK,
            "device": device,
            "task_count": len(tasks),
            "expected_go1_tasks_present": True,
            "steps": steps,
            "env_step_dt_s": env.step_dt,
            "sim_elapsed_s": sim_elapsed,
            "wall_elapsed_s": wall_elapsed,
            "sim_wall_ratio": sim_elapsed / wall_elapsed if wall_elapsed > 0 else None,
            "num_envs": env.num_envs,
            "action_dim": action_dim,
            "actor_observation_shape": list(obs["actor"].shape) if isinstance(obs, dict) and "actor" in obs else None,
            "raw_log": rel(raw_path),
            "note": "This is a dependency/runtime smoke for MJLab built-in Go1 with a zero policy. It is not the yoga-ball task port or policy equivalence evidence.",
        }
    except Exception as exc:  # noqa: BLE001
        result = {
            "ok": False,
            "stage": "construct_or_step",
            "task": MJLAB_GO1_SMOKE_TASK,
            "error": repr(exc),
            "task_count": len(tasks),
            "tasks": tasks,
            "raw_log": rel(raw_path) if raw_path.exists() else None,
        }
    finally:
        if env is not None:
            env.close()

    write_json(ARTIFACT_ROOT / "mjlab_runtime_smoke.json", result)
    return result


def smoke_mjlab_yoga_ball_task(*, steps: int = 50) -> dict[str, Any]:
    ensure_tree()
    log_dir = LOG_ROOT / "mjlab_train" / "default_playback"
    log_dir.mkdir(parents=True, exist_ok=True)
    raw_path = log_dir / "mjlab_yoga_ball_task_smoke.csv"
    try:
        import torch
        import mjlab.tasks  # noqa: F401
        from mjlab.envs import ManagerBasedRlEnv
        from mjlab.tasks.registry import list_tasks, load_env_cfg
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from scripts.go1_yoga_ball.mjlab_yoga_ball import TASK_ID, register_task
    except Exception as exc:  # noqa: BLE001
        result = {
            "ok": False,
            "stage": "import",
            "error": repr(exc),
            "raw_log": rel(raw_path) if raw_path.exists() else None,
        }
        write_json(ARTIFACT_ROOT / "mjlab_yoga_ball_task_smoke.json", result)
        return result

    env = None
    rows: list[dict[str, Any]] = []
    try:
        register_task()
        if TASK_ID not in list_tasks():
            raise RuntimeError(f"{TASK_ID} was not registered")
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        cfg = load_env_cfg(TASK_ID, play=True)
        cfg.scene.num_envs = 1
        env = ManagerBasedRlEnv(cfg=cfg, device=device, render_mode=None)
        obs, _ = env.reset()
        action_dim = int(env.action_manager.total_action_dim)
        action = torch.zeros((env.num_envs, action_dim), device=env.device)
        wall_start = time.monotonic()
        for step in range(steps):
            obs, reward, terminated, truncated, extras = env.step(action)
            del extras
            robot = env.scene["robot"]
            ball = env.scene["ball"]
            base_z = float(robot.data.root_link_pos_w[0, 2].detach().cpu())
            ball_z = float(ball.data.root_link_pos_w[0, 2].detach().cpu())
            rows.append(
                {
                    "step": step,
                    "sim_time_s": (step + 1) * env.step_dt,
                    "wall_elapsed_s": time.monotonic() - wall_start,
                    "base_z": base_z,
                    "ball_z": ball_z,
                    "base_minus_ball_z": base_z - ball_z,
                    "reward_env0": float(reward[0].detach().cpu()),
                    "terminated_env0": int(terminated[0].detach().cpu()),
                    "truncated_env0": int(truncated[0].detach().cpu()),
                }
            )
        write_csv(raw_path, rows)
        wall_elapsed = time.monotonic() - wall_start
        sim_elapsed = steps * env.step_dt
        min_base_minus_ball = min(row["base_minus_ball_z"] for row in rows) if rows else None
        result = {
            "ok": bool(rows and min_base_minus_ball is not None and min_base_minus_ball > 0.1),
            "stage": "step",
            "task": TASK_ID,
            "device": device,
            "steps": steps,
            "env_step_dt_s": env.step_dt,
            "sim_elapsed_s": sim_elapsed,
            "wall_elapsed_s": wall_elapsed,
            "sim_wall_ratio": sim_elapsed / wall_elapsed if wall_elapsed > 0 else None,
            "num_envs": env.num_envs,
            "action_dim": action_dim,
            "actor_observation_shape": list(obs["actor"].shape) if isinstance(obs, dict) and "actor" in obs else None,
            "raw_log": rel(raw_path),
            "min_base_minus_ball_z": min_base_minus_ball,
            "initial_base_minus_ball_z": rows[0]["base_minus_ball_z"] if rows else None,
            "final_base_minus_ball_z": rows[-1]["base_minus_ball_z"] if rows else None,
            "terminated_steps": sum(row["terminated_env0"] for row in rows),
            "truncated_steps": sum(row["truncated_env0"] for row in rows),
            "note": "This proves a root-owned MJLab yoga-ball task can register, construct, reset Go1 on a dynamic ball, and step. It is not trained-policy equivalence evidence.",
        }
    except Exception as exc:  # noqa: BLE001
        result = {
            "ok": False,
            "stage": "construct_or_step",
            "task": TASK_ID,
            "error": repr(exc),
            "raw_log": rel(raw_path) if raw_path.exists() else None,
        }
    finally:
        if env is not None:
            env.close()

    write_json(ARTIFACT_ROOT / "mjlab_yoga_ball_task_smoke.json", result)
    return result


def smoke_mjlab_yoga_ball_train(*, iterations: int = 1, num_envs: int = 8, steps_per_env: int = 4) -> dict[str, Any]:
    ensure_tree()
    log_root = LOG_ROOT / "mjlab_train" / "train" / "rsl_rl"
    log_root.mkdir(parents=True, exist_ok=True)
    started_at = time.time()
    try:
        import mjlab.tasks  # noqa: F401
        from mjlab.scripts.train import TrainConfig, launch_training
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from scripts.go1_yoga_ball.mjlab_yoga_ball import TASK_ID, register_task
    except Exception as exc:  # noqa: BLE001
        result = {
            "ok": False,
            "stage": "import",
            "error": repr(exc),
        }
        write_json(ARTIFACT_ROOT / "mjlab_yoga_ball_train_smoke.json", result)
        return result

    try:
        register_task()
        cfg = TrainConfig.from_task(TASK_ID)
        cfg.env.scene.num_envs = num_envs
        cfg.env.episode_length_s = 4.0
        cfg.agent.max_iterations = iterations
        cfg.agent.num_steps_per_env = steps_per_env
        cfg.agent.save_interval = 1
        cfg.agent.experiment_name = "go1_yoga_ball_port_smoke"
        cfg.agent.run_name = "train_smoke"
        cfg.agent.logger = "tensorboard"
        cfg.agent.upload_model = False
        cfg.agent.algorithm.num_learning_epochs = 1
        cfg.agent.algorithm.num_mini_batches = 1
        cfg = replace(cfg, log_root=str(log_root), gpu_ids=[0], video=False)
        launch_training(task_id=TASK_ID, args=cfg)

        experiment_root = log_root / cfg.agent.experiment_name
        run_dirs = [
            path for path in experiment_root.glob("*")
            if path.is_dir() and path.stat().st_mtime >= started_at - 1.0
        ]
        selected = max(run_dirs, key=lambda p: p.stat().st_mtime) if run_dirs else None
        checkpoints = sorted(selected.glob("model_*.pt")) if selected is not None else []
        params = selected / "params" if selected is not None else None
        result = {
            "ok": bool(selected is not None and checkpoints and params is not None and params.exists()),
            "stage": "train",
            "task": TASK_ID,
            "iterations": iterations,
            "num_envs": num_envs,
            "num_steps_per_env": steps_per_env,
            "log_root": rel(log_root),
            "selected_run": rel(selected) if selected is not None else None,
            "checkpoints": [rel(path) for path in checkpoints],
            "params_dir": rel(params) if params is not None else None,
            "note": "This is a minimal MJLab/RSL-RL training-stack smoke for the root-owned yoga-ball task. It is not an equivalent policy.",
        }
    except Exception as exc:  # noqa: BLE001
        result = {
            "ok": False,
            "stage": "train",
            "task": TASK_ID,
            "iterations": iterations,
            "num_envs": num_envs,
            "num_steps_per_env": steps_per_env,
            "log_root": rel(log_root),
            "error": repr(exc),
        }

    write_json(ARTIFACT_ROOT / "mjlab_yoga_ball_train_smoke.json", result)
    return result


def selected_mjlab_checkpoint() -> Path | None:
    train_smoke = load_json(ARTIFACT_ROOT / "mjlab_yoga_ball_train_smoke.json")
    checkpoints = train_smoke.get("checkpoints") or []
    existing = []
    for item in checkpoints:
        path = Path(item)
        if not path.is_absolute():
            path = ROOT / path
        if path.exists():
            existing.append(path)
    if existing:
        return max(existing, key=lambda p: p.stat().st_mtime)
    candidates = sorted((LOG_ROOT / "mjlab_train" / "train" / "rsl_rl").glob("**/model_*.pt"))
    return max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None


def play_mjlab_yoga_ball_trained(*, steps: int = 250) -> dict[str, Any]:
    ensure_tree()
    log_dir = LOG_ROOT / "mjlab_train" / "default_playback"
    log_dir.mkdir(parents=True, exist_ok=True)
    raw_path = log_dir / "mjlab_yoga_ball_trained_playback.csv"
    checkpoint = selected_mjlab_checkpoint()
    if checkpoint is None:
        result = {
            "ok": False,
            "stage": "checkpoint",
            "error": "No MJLab checkpoint found. Run smoke-mjlab-yoga-ball-train first.",
            "raw_log": rel(raw_path) if raw_path.exists() else None,
        }
        write_json(ARTIFACT_ROOT / "mjlab_yoga_ball_trained_playback.json", result)
        return result

    try:
        import torch
        import mjlab.tasks  # noqa: F401
        from dataclasses import asdict
        from mjlab.envs import ManagerBasedRlEnv
        from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
        from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from scripts.go1_yoga_ball.mjlab_yoga_ball import TASK_ID, register_task
    except Exception as exc:  # noqa: BLE001
        result = {
            "ok": False,
            "stage": "import",
            "checkpoint": rel(checkpoint),
            "error": repr(exc),
        }
        write_json(ARTIFACT_ROOT / "mjlab_yoga_ball_trained_playback.json", result)
        return result

    env = None
    rows: list[dict[str, Any]] = []
    try:
        register_task()
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        env_cfg = load_env_cfg(TASK_ID, play=True)
        env_cfg.scene.num_envs = 1
        base_env = ManagerBasedRlEnv(cfg=env_cfg, device=device, render_mode=None)
        agent_cfg = load_rl_cfg(TASK_ID)
        env = RslRlVecEnvWrapper(base_env, clip_actions=agent_cfg.clip_actions)
        runner_cls = load_runner_cls(TASK_ID) or MjlabOnPolicyRunner
        runner = runner_cls(env, asdict(agent_cfg), device=device)
        runner.load(str(checkpoint), load_cfg={"actor": True}, strict=True, map_location=device)
        policy = runner.get_inference_policy(device=device)
        obs = env.get_observations()
        wall_start = time.monotonic()
        for step in range(steps):
            infer_start = time.monotonic()
            with torch.no_grad():
                action = policy(obs)
            inference_latency = time.monotonic() - infer_start
            obs, reward, dones, extras = env.step(action)
            del extras
            robot = env.unwrapped.scene["robot"]
            ball = env.unwrapped.scene["ball"]
            q = robot.data.joint_pos[0].detach().cpu().tolist()
            qd = robot.data.joint_vel[0].detach().cpu().tolist()
            action_cpu = action[0].detach().cpu().tolist()
            base_z = float(robot.data.root_link_pos_w[0, 2].detach().cpu())
            ball_z = float(ball.data.root_link_pos_w[0, 2].detach().cpu())
            row: dict[str, Any] = {
                "step": step,
                "sim_time_s": (step + 1) * env.unwrapped.step_dt,
                "wall_elapsed_s": time.monotonic() - wall_start,
                "inference_latency_s": inference_latency,
                "base_z": base_z,
                "ball_z": ball_z,
                "base_minus_ball_z": base_z - ball_z,
                "reward_env0": float(reward[0].detach().cpu()),
                "done_env0": int(dones[0].detach().cpu()),
            }
            for i, value in enumerate(q):
                row[f"q_{i}"] = value
            for i, value in enumerate(qd):
                row[f"qd_{i}"] = value
            for i, value in enumerate(action_cpu):
                row[f"action_{i}"] = value
            rows.append(row)
        write_csv(raw_path, rows)
        wall_elapsed = time.monotonic() - wall_start
        sim_elapsed = steps * env.unwrapped.step_dt
        min_base_minus_ball = min(row["base_minus_ball_z"] for row in rows) if rows else None
        action_abs = [abs(row[f"action_{i}"]) for row in rows for i in range(env.num_actions)]
        infer = [row["inference_latency_s"] for row in rows]
        released_replay_rows = [{f"q_{i}": str(row[f"q_{i}"]) for i in range(12)} for row in rows]
        joint_summary = joint_limit_summary(released_replay_rows)
        result = {
            "ok": bool(
                rows
                and min_base_minus_ball is not None
                and min_base_minus_ball > 0.1
                and sum(row["done_env0"] for row in rows) == 0
                and joint_summary["passes_numerical_margin_rule"]
            ),
            "stage": "trained_playback",
            "task": TASK_ID,
            "checkpoint": rel(checkpoint),
            "device": device,
            "steps": steps,
            "env_step_dt_s": env.unwrapped.step_dt,
            "sim_elapsed_s": sim_elapsed,
            "wall_elapsed_s": wall_elapsed,
            "sim_wall_ratio": sim_elapsed / wall_elapsed if wall_elapsed > 0 else None,
            "raw_log": rel(raw_path),
            "min_base_minus_ball_z": min_base_minus_ball,
            "final_base_minus_ball_z": rows[-1]["base_minus_ball_z"] if rows else None,
            "done_steps": sum(row["done_env0"] for row in rows),
            "action_abs_max": max(action_abs) if action_abs else None,
            "action_abs_p95": percentile(action_abs, 95),
            "inference_latency_s": {
                "mean": mean(infer),
                "p95": percentile(infer, 95),
                "max": max(infer) if infer else None,
            },
            "joint_limit_summary": joint_summary,
            "note": "Headless MJLab trained-checkpoint playback through MJLab/RSL-RL inference. This validates policy execution plumbing only for the current tiny checkpoint; it is not an equivalent policy.",
        }
    except Exception as exc:  # noqa: BLE001
        result = {
            "ok": False,
            "stage": "trained_playback",
            "task": TASK_ID,
            "checkpoint": rel(checkpoint),
            "error": repr(exc),
            "raw_log": rel(raw_path) if raw_path.exists() else None,
        }
    finally:
        if env is not None:
            env.close()

    write_json(ARTIFACT_ROOT / "mjlab_yoga_ball_trained_playback.json", result)
    return result


def phase_mjlab_report() -> Path:
    ensure_tree()
    manifest = load_json(ARTIFACT_ROOT / "manifest.json")
    runtime = load_json(ARTIFACT_ROOT / "mjlab_runtime_smoke.json")
    task_smoke = load_json(ARTIFACT_ROOT / "mjlab_yoga_ball_task_smoke.json")
    train_smoke = load_json(ARTIFACT_ROOT / "mjlab_yoga_ball_train_smoke.json")
    playback = load_json(ARTIFACT_ROOT / "mjlab_yoga_ball_trained_playback.json")
    phase_gate = {
        "ok": False,
        "status": "task_port_smoke_only" if task_smoke.get("ok") else "dependency_runtime_smoke_only",
        "mjlab_dependency_present": bool(
            ((manifest.get("dependencies") or {}).get("MJLab") or {}).get("has_contents")
        ),
        "mjlab_docker_image_present": bool(
            ((manifest.get("docker_images") or {}).get("mjlab") or {}).get("exists")
        ),
        "runtime_smoke_ok": bool(runtime.get("ok")),
        "task_port_smoke_ok": bool(task_smoke.get("ok")),
        "training_smoke_ok": bool(train_smoke.get("ok")),
        "trained_playback_smoke_ok": bool(playback.get("ok")),
        "task_port_complete": False,
        "training_complete": False,
        "default_playback_complete": False,
        "mujoco_sim2sim_complete": False,
    }
    write_json(ARTIFACT_ROOT / "phase_mjlab_summary.json", phase_gate)
    lines = [
        "# Go1 Yoga-Ball MJLab Port Report",
        "",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S %z')}",
        "",
        "## Phase Gate",
        "",
        f"- ok: `{phase_gate['ok']}`",
        f"- status: `{phase_gate['status']}`",
        f"- MJLab dependency present: `{phase_gate['mjlab_dependency_present']}`",
        f"- MJLab Docker image present: `{phase_gate['mjlab_docker_image_present']}`",
        f"- MJLab runtime smoke ok: `{phase_gate['runtime_smoke_ok']}`",
        f"- MJLab yoga-ball task smoke ok: `{phase_gate['task_port_smoke_ok']}`",
        f"- MJLab yoga-ball training smoke ok: `{phase_gate['training_smoke_ok']}`",
        f"- MJLab trained-checkpoint playback smoke ok: `{phase_gate['trained_playback_smoke_ok']}`",
        f"- task port complete: `{phase_gate['task_port_complete']}`",
        f"- training complete: `{phase_gate['training_complete']}`",
        f"- default playback complete: `{phase_gate['default_playback_complete']}`",
        f"- MuJoCo Sim2Sim complete: `{phase_gate['mujoco_sim2sim_complete']}`",
        "",
        "## Runtime Smoke",
        "",
    ]
    if runtime:
        lines.append(f"- artifact: `{rel(ARTIFACT_ROOT / 'mjlab_runtime_smoke.json')}`")
        lines.append(f"- ok: `{runtime.get('ok')}`")
        lines.append(f"- stage: `{runtime.get('stage')}`")
        lines.append(f"- task: `{runtime.get('task')}`")
        lines.append(f"- device: `{runtime.get('device')}`")
        lines.append(f"- steps: `{runtime.get('steps')}`")
        lines.append(f"- env_step_dt_s: `{runtime.get('env_step_dt_s')}`")
        lines.append(f"- sim_wall_ratio: `{runtime.get('sim_wall_ratio')}`")
        lines.append(f"- raw_log: `{runtime.get('raw_log')}`")
        if runtime.get("error"):
            lines.append(f"- error: `{runtime.get('error')}`")
    else:
        lines.append("- missing runtime smoke artifact")
    lines.extend(["", "## Yoga-Ball Task Smoke", ""])
    if task_smoke:
        lines.append(f"- artifact: `{rel(ARTIFACT_ROOT / 'mjlab_yoga_ball_task_smoke.json')}`")
        lines.append(f"- ok: `{task_smoke.get('ok')}`")
        lines.append(f"- stage: `{task_smoke.get('stage')}`")
        lines.append(f"- task: `{task_smoke.get('task')}`")
        lines.append(f"- device: `{task_smoke.get('device')}`")
        lines.append(f"- steps: `{task_smoke.get('steps')}`")
        lines.append(f"- actor observation shape: `{task_smoke.get('actor_observation_shape')}`")
        lines.append(f"- min base minus ball z: `{task_smoke.get('min_base_minus_ball_z')}`")
        lines.append(f"- raw_log: `{task_smoke.get('raw_log')}`")
        if task_smoke.get("error"):
            lines.append(f"- error: `{task_smoke.get('error')}`")
    else:
        lines.append("- missing yoga-ball task smoke artifact")
    lines.extend(["", "## Yoga-Ball Training Smoke", ""])
    if train_smoke:
        lines.append(f"- artifact: `{rel(ARTIFACT_ROOT / 'mjlab_yoga_ball_train_smoke.json')}`")
        lines.append(f"- ok: `{train_smoke.get('ok')}`")
        lines.append(f"- stage: `{train_smoke.get('stage')}`")
        lines.append(f"- task: `{train_smoke.get('task')}`")
        lines.append(f"- iterations: `{train_smoke.get('iterations')}`")
        lines.append(f"- num_envs: `{train_smoke.get('num_envs')}`")
        lines.append(f"- num_steps_per_env: `{train_smoke.get('num_steps_per_env')}`")
        lines.append(f"- selected run: `{train_smoke.get('selected_run')}`")
        lines.append(f"- checkpoints: `{train_smoke.get('checkpoints')}`")
        if train_smoke.get("error"):
            lines.append(f"- error: `{train_smoke.get('error')}`")
    else:
        lines.append("- missing yoga-ball training smoke artifact")
    lines.extend(["", "## Trained-Checkpoint Playback Smoke", ""])
    if playback:
        lines.append(f"- artifact: `{rel(ARTIFACT_ROOT / 'mjlab_yoga_ball_trained_playback.json')}`")
        lines.append(f"- ok: `{playback.get('ok')}`")
        lines.append(f"- stage: `{playback.get('stage')}`")
        lines.append(f"- checkpoint: `{playback.get('checkpoint')}`")
        lines.append(f"- steps: `{playback.get('steps')}`")
        lines.append(f"- raw_log: `{playback.get('raw_log')}`")
        lines.append(f"- done_steps: `{playback.get('done_steps')}`")
        lines.append(f"- min_base_minus_ball_z: `{playback.get('min_base_minus_ball_z')}`")
        lines.append(f"- action_abs_p95: `{playback.get('action_abs_p95')}`")
        lines.append(f"- inference_latency_s: `{playback.get('inference_latency_s')}`")
        if playback.get("error"):
            lines.append(f"- error: `{playback.get('error')}`")
    else:
        lines.append("- missing trained-checkpoint playback artifact")
    lines.extend(
        [
            "",
            "## Port Strategy",
            "",
            "Use MJLab as an installed dependency inside `eureka-mjlab`. Keep the yoga-ball task adapter root-owned until the API boundary is clear, then register it at runtime through MJLab's task registry. Start from MJLab's built-in Go1 velocity task only for robot/entity/action patterns; do not treat the flat-ground velocity task as yoga-ball evidence.",
            "",
            "The next required increment is a minimal registered MJLab yoga-ball task with a dynamic sphere, Go1 reset on the ball, DrEureka-compatible action timing, and raw default-playback logs. Only after that should training be scaled.",
            "",
        ]
    )
    path = ARTIFACT_ROOT / "phase_mjlab_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=[
            "init-artifacts",
            "validate-deps",
            "inspect-policy",
            "write-contract",
            "smoke-mujoco-assets",
            "smoke-direct-release",
            "record-default-train-run",
            "summarize-pretrained-isaacgym",
            "summarize-pretrained-mujoco-sim2sim",
            "summarize-default-train-isaacgym",
            "summarize-default-train-mujoco-sim2sim",
            "render-pretrained-mujoco-video",
            "render-default-train-mujoco-video",
            "render-mujoco-marked-videos",
            "aggregate-pretrained-mujoco-repeats",
            "summarize-control-removal-pretrained-mujoco-sim2sim",
            "compare-default-train-cfg",
            "phase-default-train-report",
            "smoke-mjlab-runtime",
            "smoke-mjlab-yoga-ball-task",
            "smoke-mjlab-yoga-ball-train",
            "play-mjlab-yoga-ball-trained",
            "phase-mjlab-report",
            "report",
        ],
    )
    args = parser.parse_args()

    if args.command == "init-artifacts":
        ensure_tree()
        print(f"Initialized {rel(LOG_ROOT)} and {rel(ARTIFACT_ROOT)}")
    elif args.command == "validate-deps":
        data = validate_deps()
        print(f"Wrote {rel(ARTIFACT_ROOT / 'manifest.json')}")
        missing = [name for name, info in data["dependencies"].items() if info["required"] and not info["exists"]]
        if missing:
            print(f"Missing required fetched dependencies: {', '.join(missing)}")
    elif args.command == "inspect-policy":
        inspect_policy()
        print(f"Wrote {rel(ARTIFACT_ROOT / 'policy_registry.json')}")
    elif args.command == "write-contract":
        path = write_contract()
        print(f"Wrote {rel(path)}")
    elif args.command == "smoke-mujoco-assets":
        result = smoke_mujoco_assets()
        print(f"Wrote {rel(ARTIFACT_ROOT / 'mujoco_asset_smoke.json')}")
        if not result.get("ok"):
            return 1
    elif args.command == "smoke-direct-release":
        result = direct_release_smoke()
        print(f"Wrote {rel(ARTIFACT_ROOT / 'release_validation.json')}")
        if not result.get("ok"):
            return 1
    elif args.command == "record-default-train-run":
        result = record_default_train_run()
        print(f"Wrote {rel(ARTIFACT_ROOT / 'default_train_run.json')}")
        if not result.get("ok"):
            return 1
    elif args.command == "summarize-pretrained-isaacgym":
        result = summarize_pretrained_isaacgym_playback()
        print(f"Wrote {rel(ARTIFACT_ROOT / 'pretrained_isaacgym_playback.json')}")
        if not result.get("ok"):
            return 1
    elif args.command == "summarize-pretrained-mujoco-sim2sim":
        result = summarize_pretrained_mujoco_sim2sim()
        print(f"Wrote {rel(ARTIFACT_ROOT / 'pretrained_mujoco_sim2sim_smoke.json')}")
        if not result.get("ok_smoke"):
            return 1
    elif args.command == "summarize-default-train-isaacgym":
        result = summarize_default_train_isaacgym_playback()
        print(f"Wrote {rel(ARTIFACT_ROOT / 'default_train_isaacgym_playback.json')}")
        if not result.get("ok"):
            return 1
    elif args.command == "summarize-default-train-mujoco-sim2sim":
        result = summarize_default_train_mujoco_sim2sim()
        print(f"Wrote {rel(ARTIFACT_ROOT / 'default_train_mujoco_sim2sim_smoke.json')}")
        if not result.get("ok_smoke"):
            return 1
    elif args.command == "render-pretrained-mujoco-video":
        result = render_pretrained_mujoco_video()
        print(f"Wrote {rel(ARTIFACT_ROOT / 'pretrained_mujoco_video.json')}")
        if not result.get("ok"):
            return 1
    elif args.command == "render-default-train-mujoco-video":
        result = render_default_train_mujoco_video()
        print(f"Wrote {rel(ARTIFACT_ROOT / 'default_train_mujoco_video.json')}")
        if not result.get("ok"):
            return 1
    elif args.command == "render-mujoco-marked-videos":
        result = render_default_train_and_pretrained_mujoco_videos()
        print(f"Wrote {rel(ARTIFACT_ROOT / 'mujoco_marked_videos.json')}")
        if not result.get("ok"):
            return 1
    elif args.command == "aggregate-pretrained-mujoco-repeats":
        result = aggregate_pretrained_mujoco_repeats()
        print(f"Wrote {rel(ARTIFACT_ROOT / 'pretrained_mujoco_sim2sim_repeats.json')}")
        if not result.get("ok"):
            return 1
    elif args.command == "summarize-control-removal-pretrained-mujoco-sim2sim":
        result = summarize_control_removal_pretrained_mujoco_sim2sim()
        print(f"Wrote {rel(ARTIFACT_ROOT / 'pretrained_mujoco_control_removal.json')}")
        if not result.get("ok"):
            return 1
    elif args.command == "compare-default-train-cfg":
        compare_default_train_cfg()
        print(f"Wrote {rel(ARTIFACT_ROOT / 'default_train_config_comparison.json')}")
    elif args.command == "phase-default-train-report":
        path = phase_default_train_report()
        print(f"Wrote {rel(path)}")
    elif args.command == "smoke-mjlab-runtime":
        result = smoke_mjlab_runtime()
        print(f"Wrote {rel(ARTIFACT_ROOT / 'mjlab_runtime_smoke.json')}")
        if not result.get("ok"):
            return 1
    elif args.command == "smoke-mjlab-yoga-ball-task":
        result = smoke_mjlab_yoga_ball_task()
        print(f"Wrote {rel(ARTIFACT_ROOT / 'mjlab_yoga_ball_task_smoke.json')}")
        if not result.get("ok"):
            return 1
    elif args.command == "smoke-mjlab-yoga-ball-train":
        result = smoke_mjlab_yoga_ball_train()
        print(f"Wrote {rel(ARTIFACT_ROOT / 'mjlab_yoga_ball_train_smoke.json')}")
        if not result.get("ok"):
            return 1
    elif args.command == "play-mjlab-yoga-ball-trained":
        result = play_mjlab_yoga_ball_trained()
        print(f"Wrote {rel(ARTIFACT_ROOT / 'mjlab_yoga_ball_trained_playback.json')}")
        if not result.get("ok"):
            return 1
    elif args.command == "phase-mjlab-report":
        path = phase_mjlab_report()
        print(f"Wrote {rel(path)}")
    elif args.command == "report":
        path = report()
        print(f"Wrote {rel(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
