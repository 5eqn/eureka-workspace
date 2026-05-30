#!/usr/bin/env python3
"""Caller-project utilities for the DrEureka Go2 MJLab port."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = ROOT / "scripts" / "go2_mjlab_dreureka_port"
LOG_ROOT = ROOT / "logs" / "go2_mjlab_dreureka_port"
ARTIFACT_ROOT = ROOT / "artifacts" / "go2_mjlab_dreureka_port"

MJLAB_HOME = Path(os.environ.get("MJLAB_HOME", str(Path.home() / "MJLab")))
UNITREE_RL_MJLAB_HOME = Path(
    os.environ.get("UNITREE_RL_MJLAB_HOME", str(Path.home() / "unitree_rl_mjlab"))
)

UNITREE_GO2_ENV = UNITREE_RL_MJLAB_HOME / "src/tasks/velocity/config/go2/env_cfgs.py"
UNITREE_GO2_RL = UNITREE_RL_MJLAB_HOME / "src/tasks/velocity/config/go2/rl_cfg.py"
UNITREE_GO2_XML = UNITREE_RL_MJLAB_HOME / "src/assets/robots/unitree_go2/xmls/go2.xml"
UNITREE_GO2_SCENE = UNITREE_RL_MJLAB_HOME / "src/assets/robots/unitree_go2/xmls/scene_go2.xml"
MJLAB_PYPROJECT = MJLAB_HOME / "pyproject.toml"

BASELINE_LOG = ROOT / "logs/go2_yoga_ball/train_original_settings_1_8_budget/train.log"
BASELINE_LAUNCH = ROOT / "artifacts/go2_yoga_ball/train_original_settings_1_8_budget_launch.json"
CONDA_ENV_NAME = os.environ.get("GO2_MJLAB_CONDA_ENV", "go2-mjlab")
ENV_RECORD = ARTIFACT_ROOT / "fresh_env_record.json"
IMPORT_SMOKE_JSON = ARTIFACT_ROOT / "import_smoke.json"
IMPORT_SMOKE_MD = ARTIFACT_ROOT / "import_smoke.md"
TASK_CONFIG_SMOKE_JSON = ARTIFACT_ROOT / "task_config_smoke.json"
TASK_CONFIG_SMOKE_MD = ARTIFACT_ROOT / "task_config_smoke.md"
SMOKE_20MIN_HEALTH_JSON = ARTIFACT_ROOT / "smoke_20min_health.json"
SMOKE_20MIN_HEALTH_MD = ARTIFACT_ROOT / "smoke_20min_health.md"
SMOKE_20MIN_CURVE_CSV = ARTIFACT_ROOT / "smoke_20min_reward_curve.csv"
SMOKE_20MIN_CURVE_SVG = ARTIFACT_ROOT / "smoke_20min_reward_curve.svg"
TRAIN_1_8_LAUNCH_JSON = ARTIFACT_ROOT / "train_1_8_budget_launch.json"
TRAIN_1_8_HEALTH_JSON = ARTIFACT_ROOT / "train_1_8_budget_health.json"
TRAIN_1_8_HEALTH_MD = ARTIFACT_ROOT / "train_1_8_budget_health.md"
TRAIN_1_8_CURVE_CSV = ARTIFACT_ROOT / "train_1_8_budget_reward_curve.csv"
TRAIN_1_8_CURVE_SVG = ARTIFACT_ROOT / "train_1_8_budget_reward_curve.svg"

TASK_ID = "DrEureka-Go2-YogaBall"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def ensure_dirs() -> None:
    for path in [
        LOG_ROOT,
        LOG_ROOT / "smoke_20min",
        LOG_ROOT / "train_1_8_budget",
        ARTIFACT_ROOT,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def run(cmd: list[str], cwd: Path | None = None) -> str:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


def run_capture(cmd: list[str], cwd: Path | None = None) -> dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return {
        "cmd": cmd,
        "cwd": str(cwd) if cwd else None,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def run_stream_to_log(cmd: list[str], log_path: Path, cwd: Path | None = None) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write("$ " + " ".join(cmd) + "\n")
        log.flush()
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd) if cwd else None,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            log.write(line)
            log.flush()
        return proc.wait()


def conda_python(code: str, cwd: Path | None = None) -> dict[str, Any]:
    return run_capture(["conda", "run", "-n", CONDA_ENV_NAME, "python", "-c", code], cwd=cwd)


def conda_python_script(script: Path, *args: str) -> list[str]:
    return ["conda", "run", "--no-capture-output", "-n", CONDA_ENV_NAME, "python", str(script), *args]


def git_head(path: Path) -> str | None:
    try:
        return run(["git", "-C", str(path), "rev-parse", "HEAD"])
    except (OSError, subprocess.CalledProcessError):
        return None


def git_status(path: Path) -> str | None:
    try:
        return run(["git", "-C", str(path), "status", "--short"])
    except (OSError, subprocess.CalledProcessError):
        return None


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def excerpt(path: Path, start: int, end: int) -> dict[str, Any]:
    lines = read_lines(path)
    return {
        "path": rel(path),
        "start_line": start,
        "end_line": end,
        "text": "\n".join(lines[start - 1 : end]),
    }


def find_excerpt(path: Path, pattern: str, context_before: int = 0, context_after: int = 0) -> dict[str, Any]:
    regex = re.compile(pattern)
    for index, line in enumerate(read_lines(path), start=1):
        if regex.search(line):
            return excerpt(path, max(1, index - context_before), index + context_after)
    return {"path": rel(path), "pattern": pattern, "missing": True}


def package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for pkg in ["mjlab", "mujoco", "mujoco_warp", "torch", "rsl_rl"]:
        code = (
            "import importlib.metadata as m; "
            f"print(m.version('{pkg.replace('_', '-')}'))"
        )
        try:
            versions[pkg] = run(["python3", "-c", code])
        except (OSError, subprocess.CalledProcessError):
            versions[pkg] = None
    return versions


def conda_package_versions() -> dict[str, Any]:
    code = (
        "import importlib.metadata as m, torch, json; "
        "pkgs=['mjlab','mujoco','mujoco-warp','warp-lang','torch','rsl-rl-lib','unitree-rl-mjlab','scipy']; "
        "data={p:m.version(p) for p in pkgs}; "
        "data['torch_cuda_available']=torch.cuda.is_available(); "
        "data['torch_cuda_version']=torch.version.cuda; "
        "data['gpu_name']=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None; "
        "print(json.dumps(data, sort_keys=True))"
    )
    result = conda_python(code, cwd=ROOT)
    if result["returncode"] != 0:
        return {"ok": False, "result": result}
    return {"ok": True, "versions": json.loads(result["stdout"])}


def baseline_tail_metrics() -> dict[str, Any]:
    if not BASELINE_LOG.exists():
        return {"missing": rel(BASELINE_LOG)}
    text = BASELINE_LOG.read_text(encoding="utf-8", errors="replace")
    pairs = re.findall(r"train/episode/([^│]+?)\s*│\s*([-+0-9.]+)", text)
    iterations = re.findall(r"iterations\s*│\s*([0-9]+)", text)
    latest: dict[str, float] = {}
    for key, value in pairs:
        latest[key.strip()] = float(value)
    return {
        "path": rel(BASELINE_LOG),
        "size_bytes": BASELINE_LOG.stat().st_size,
        "last_iteration": int(iterations[-1]) if iterations else None,
        "latest_episode_metrics": latest,
    }


def source_contract() -> dict[str, Any]:
    required = [
        MJLAB_HOME,
        UNITREE_RL_MJLAB_HOME,
        UNITREE_GO2_ENV,
        UNITREE_GO2_RL,
        UNITREE_GO2_XML,
        UNITREE_GO2_SCENE,
        MJLAB_PYPROJECT,
        BASELINE_LOG,
        BASELINE_LAUNCH,
    ]
    missing = [rel(path) for path in required if not path.exists()]

    return {
        "generated_at_unix": time.time(),
        "ok": not missing,
        "missing": missing,
        "fresh_sources": {
            "mjlab_home": str(MJLAB_HOME),
            "mjlab_head": git_head(MJLAB_HOME),
            "mjlab_status_short": git_status(MJLAB_HOME),
            "unitree_rl_mjlab_home": str(UNITREE_RL_MJLAB_HOME),
            "unitree_rl_mjlab_head": git_head(UNITREE_RL_MJLAB_HOME),
            "unitree_rl_mjlab_status_short": git_status(UNITREE_RL_MJLAB_HOME),
        },
        "installed_package_versions": package_versions(),
        "baseline_launch": json.loads(BASELINE_LAUNCH.read_text()) if BASELINE_LAUNCH.exists() else None,
        "baseline_tail_metrics": baseline_tail_metrics(),
        "script_local_contract": {
            "env_cfg": excerpt(SCRIPT_ROOT / "dreureka_go2_mjlab/env_cfg.py", 1, 230),
            "events": excerpt(SCRIPT_ROOT / "dreureka_go2_mjlab/mdp/events.py", 1, 80),
            "observations": excerpt(SCRIPT_ROOT / "dreureka_go2_mjlab/mdp/observations.py", 1, 220),
            "rewards": excerpt(SCRIPT_ROOT / "dreureka_go2_mjlab/mdp/rewards.py", 1, 80),
            "terminations": excerpt(SCRIPT_ROOT / "dreureka_go2_mjlab/mdp/terminations.py", 1, 80),
        },
        "unitree_rl_mjlab_go2_data": {
            "go2_env_config": excerpt(UNITREE_GO2_ENV, 1, 158),
            "go2_rl_config": excerpt(UNITREE_GO2_RL, 1, 43),
            "go2_xml": rel(UNITREE_GO2_XML),
            "go2_scene_xml": rel(UNITREE_GO2_SCENE),
        },
        "mjlab_runtime_contract": {
            "pyproject": excerpt(MJLAB_PYPROJECT, 1, 80),
            "unitree_setup_dependency_pin": excerpt(UNITREE_RL_MJLAB_HOME / "setup.py", 1, 17),
            "train_entrypoint": excerpt(UNITREE_RL_MJLAB_HOME / "scripts/train.py", 1, 180),
        },
        "port_requirements": [
            "Implement a caller-project MJLab task, not upstream edits.",
            "Use Unitree MJLab Go2 XML/model constants as the robot data source.",
            "Keep DrEureka-derived yoga-ball, observation, reward, and termination constants inline under scripts.",
            "Use MJLab native single-patch random_rough heightfield terrain with reset-time env-origin randomization; flat-plane fallback is invalid for training.",
            "Mirror 4096 envs, 20000 iterations, save interval 1000 for 1/8-budget launch.",
        ],
    }


def write_source_contract() -> None:
    ensure_dirs()
    contract = source_contract()
    json_path = ARTIFACT_ROOT / "source_contract.json"
    json_path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Go2 MJLab DrEureka Source Contract",
        "",
        f"- Status: {'PASS' if contract['ok'] else 'FAIL'}",
        f"- MJLab home: `{contract['fresh_sources']['mjlab_home']}`",
        f"- Unitree RL MJLab home: `{contract['fresh_sources']['unitree_rl_mjlab_home']}`",
        f"- Baseline log: `{contract['baseline_tail_metrics'].get('path')}`",
        f"- Baseline last iteration: `{contract['baseline_tail_metrics'].get('last_iteration')}`",
        "",
        "## Required Port Semantics",
        "",
    ]
    lines.extend(f"- {item}" for item in contract["port_requirements"])
    lines.extend(["", "## Baseline Latest Metrics", ""])
    for key, value in sorted(contract["baseline_tail_metrics"].get("latest_episode_metrics", {}).items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Source Excerpts", ""])
    for section, items in [
        ("Script-local MJLab Port", contract["script_local_contract"]),
        ("Unitree RL MJLab", contract["unitree_rl_mjlab_go2_data"]),
        ("MJLab Runtime", contract["mjlab_runtime_contract"]),
    ]:
        lines.extend([f"### {section}", ""])
        for name, value in items.items():
            if not isinstance(value, dict) or "text" not in value:
                lines.append(f"- `{name}`: `{value}`")
                continue
            lines.extend(
                [
                    f"#### {name}",
                    "",
                    f"- Source: `{value['path']}:{value['start_line']}`",
                    "",
                    "```text",
                    value["text"],
                    "```",
                    "",
                ]
            )
    (ARTIFACT_ROOT / "source_contract.md").write_text("\n".join(lines), encoding="utf-8")
    if not contract["ok"]:
        raise SystemExit(f"source contract missing required paths: {contract['missing']}")


def preflight() -> None:
    ensure_dirs()
    log_path = LOG_ROOT / "preflight.log"
    with log_path.open("w", encoding="utf-8") as log:
        log.write("go2_mjlab_dreureka_port preflight\n")
        log.write(f"root={ROOT}\n")
        log.write(f"mjlab_home={MJLAB_HOME}\n")
        log.write(f"unitree_rl_mjlab_home={UNITREE_RL_MJLAB_HOME}\n")
    write_source_contract()


def setup_env_record() -> None:
    ensure_dirs()
    apt_packages = [
        "libyaml-cpp-dev",
        "libboost-all-dev",
        "libeigen3-dev",
        "libspdlog-dev",
        "libfmt-dev",
    ]
    apt_status = {}
    for package in apt_packages:
        apt_status[package] = run_capture(
            ["dpkg-query", "-W", "-f=${Package} ${Status} ${Version}\\n", package],
            cwd=ROOT,
        )
    env_list = run_capture(["conda", "env", "list"], cwd=ROOT)
    versions = conda_package_versions()
    record = {
        "generated_at_unix": time.time(),
        "ok": all(item["returncode"] == 0 for item in apt_status.values()) and versions.get("ok") is True,
        "conda_env_name": CONDA_ENV_NAME,
        "fresh_sources": {
            "mjlab_home": str(MJLAB_HOME),
            "unitree_rl_mjlab_home": str(UNITREE_RL_MJLAB_HOME),
        },
        "reproduction_commands": [
            "sudo apt-get install -y libyaml-cpp-dev libboost-all-dev libeigen3-dev libspdlog-dev libfmt-dev",
            f"conda create -y -n {CONDA_ENV_NAME} python=3.11 pip",
            f"conda run -n {CONDA_ENV_NAME} python -m pip install -e /home/seqn/unitree_rl_mjlab",
            f"conda run -n {CONDA_ENV_NAME} python -m pip install mujoco==3.5.0 scipy",
            f"conda run -n {CONDA_ENV_NAME} python -m pip install warp-lang==1.12.1",
        ],
        "why_extra_pins_exist": [
            "unitree_rl_mjlab pins mujoco-warp==3.5.0 but lets mujoco float; mujoco==3.9.0 broke import because mjENBL_MULTICCD is absent for that pair.",
            "mjlab==1.2.0 imports scipy terrain helpers but scipy was not installed by unitree_rl_mjlab's dependency set.",
            "mjlab==1.2.0 declares warp-lang>=1.12.0 but its CUDA-graph driver check expects wp.context.runtime.driver_version; warp-lang==1.13.0 removed that path, so warp-lang==1.12.1 is pinned.",
        ],
        "apt_status": apt_status,
        "conda_env_list": env_list,
        "package_versions": versions,
    }
    ENV_RECORD.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not record["ok"]:
        raise SystemExit(f"FRESH env record failed; see {ENV_RECORD}")


def import_smoke() -> None:
    ensure_dirs()
    setup_env_record()
    checks = {
        "runtime_versions": conda_package_versions(),
        "unitree_go2_task": conda_python(
            "import json, mjlab, src.tasks; "
            "from mjlab.tasks.registry import list_tasks, load_env_cfg, load_rl_cfg; "
            "cfg=load_env_cfg('Unitree-Go2-Flat'); rl=load_rl_cfg('Unitree-Go2-Flat'); "
            "data={'mjlab_file': mjlab.__file__, 'task_count': len(list_tasks()), "
            "'has_unitree_go2_flat': 'Unitree-Go2-Flat' in list_tasks(), "
            "'has_unitree_go2_rough': 'Unitree-Go2-Rough' in list_tasks(), "
            "'num_envs': cfg.scene.num_envs, 'episode_length_s': cfg.episode_length_s, "
            "'agent_iterations': rl.max_iterations, 'experiment_name': rl.experiment_name}; "
            "print(json.dumps(data, sort_keys=True))",
            cwd=UNITREE_RL_MJLAB_HOME,
        ),
        "unitree_go2_robot_data": conda_python(
            "import json; "
            "from src.assets.robots.unitree_go2.go2_constants import get_go2_robot_cfg, GO2_XML; "
            "cfg=get_go2_robot_cfg(); "
            "data={'go2_xml': str(GO2_XML), 'init_pos': list(cfg.init_state.pos), "
            "'collision_count': len(cfg.collisions), 'actuator_group_count': len(cfg.articulation.actuators)}; "
            "print(json.dumps(data, sort_keys=True))",
            cwd=UNITREE_RL_MJLAB_HOME,
        ),
    }
    parsed: dict[str, Any] = {}
    ok = True
    for name, result in checks.items():
        if name == "runtime_versions":
            parsed[name] = result
            ok = ok and result.get("ok") is True
            continue
        parsed[name] = result
        ok = ok and result["returncode"] == 0
        if result["returncode"] == 0:
            parsed[name]["json"] = json.loads(result["stdout"])
    report = {
        "generated_at_unix": time.time(),
        "ok": ok,
        "checks": parsed,
        "next_port_step": "Implement a caller-project MJLab task that uses Unitree Go2 robot data but replaces velocity-task semantics with DrEureka yoga-ball reward/object/observation semantics.",
    }
    IMPORT_SMOKE_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Go2 MJLab Import Smoke",
        "",
        f"- Status: {'PASS' if ok else 'FAIL'}",
        f"- Conda env: `{CONDA_ENV_NAME}`",
        f"- Environment record: `{rel(ENV_RECORD)}`",
        "",
    ]
    if parsed["runtime_versions"].get("ok"):
        lines.append("## Runtime Versions")
        lines.append("")
        for key, value in sorted(parsed["runtime_versions"]["versions"].items()):
            lines.append(f"- `{key}`: `{value}`")
        lines.append("")
    for name in ["unitree_go2_task", "unitree_go2_robot_data"]:
        result = parsed[name]
        lines.extend([f"## {name}", "", f"- Return code: `{result['returncode']}`", ""])
        if "json" in result:
            for key, value in sorted(result["json"].items()):
                lines.append(f"- `{key}`: `{value}`")
            lines.append("")
        if result["stderr"].strip():
            lines.extend(["```text", result["stderr"].strip(), "```", ""])
    IMPORT_SMOKE_MD.write_text("\n".join(lines), encoding="utf-8")
    if not ok:
        raise SystemExit(f"import smoke failed; see {IMPORT_SMOKE_JSON}")


def task_config_smoke() -> None:
    ensure_dirs()
    setup_env_record()
    code = r"""
import json
import sys
from dataclasses import asdict

import torch

sys.path.insert(0, "/home/seqn/eureka-workspace/scripts/go2_mjlab_dreureka_port")
import src.tasks  # noqa: F401
import dreureka_go2_mjlab  # noqa: F401

from dreureka_go2_mjlab.env_cfg import DREUREKA_CONTRACT, TASK_ID
from mjlab.envs import ManagerBasedRlEnv
from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
from mjlab.tasks.registry import list_tasks, load_env_cfg, load_rl_cfg

cfg = load_env_cfg(TASK_ID)
rl = load_rl_cfg(TASK_ID)
registered = TASK_ID in list_tasks()

cfg.scene.num_envs = 2
if cfg.scene.terrain.terrain_generator is not None:
  cfg.scene.terrain.terrain_generator.num_rows = 1
  cfg.scene.terrain.terrain_generator.num_cols = 1
env = ManagerBasedRlEnv(cfg=cfg, device="cuda:0" if torch.cuda.is_available() else "cpu")
obs, extras = env.reset()
action = torch.zeros((env.num_envs, env.single_action_space.shape[0]), device=env.device)
obs, reward, terminated, timeout, extras = env.step(action)
wrapped = RslRlVecEnvWrapper(env, clip_actions=rl.clip_actions)
runner = MjlabOnPolicyRunner(wrapped, asdict(rl), None, env.device)
actuators = cfg.scene.entities["robot"].articulation.actuators
actuator_gains = {
  actuator.target_names_expr[0]: {
    "stiffness": actuator.stiffness,
    "damping": actuator.damping,
  }
  for actuator in actuators
}

summary = {
  "registered": registered,
  "task_id": TASK_ID,
  "num_envs_train": load_env_cfg(TASK_ID).scene.num_envs,
  "num_envs_smoke": env.num_envs,
  "terrain_type": cfg.scene.terrain.terrain_type,
  "terrain_generator_class": type(cfg.scene.terrain.terrain_generator).__name__ if cfg.scene.terrain.terrain_generator is not None else None,
  "terrain_rows": cfg.scene.terrain.terrain_generator.num_rows if cfg.scene.terrain.terrain_generator is not None else None,
  "terrain_cols": cfg.scene.terrain.terrain_generator.num_cols if cfg.scene.terrain.terrain_generator is not None else None,
  "terrain_size": list(cfg.scene.terrain.terrain_generator.size) if cfg.scene.terrain.terrain_generator is not None else None,
  "terrain_sub_terrains": list(cfg.scene.terrain.terrain_generator.sub_terrains.keys()) if cfg.scene.terrain.terrain_generator is not None else [],
  "terrain_origin_shape": list(env.scene.terrain.terrain_origins.shape) if env.scene.terrain.terrain_origins is not None else None,
  "actuator_gains": actuator_gains,
  "episode_length_s": cfg.episode_length_s,
  "max_episode_length_steps": env.max_episode_length,
  "decimation": cfg.decimation,
  "physics_dt": cfg.sim.mujoco.timestep,
  "step_dt": env.step_dt,
  "commands": list(cfg.commands.keys()),
  "actor_terms": list(cfg.observations["actor"].terms.keys()),
  "critic_terms": list(cfg.observations["critic"].terms.keys()),
  "actor_obs_shape": list(obs["actor"].shape),
  "critic_obs_shape": list(obs["critic"].shape),
  "actor_model_obs_groups": runner.alg.actor.obs_groups,
  "critic_model_obs_groups": runner.alg.critic.obs_groups,
  "actor_model_input_dim": runner.alg.actor.obs_dim,
  "critic_model_input_dim": runner.alg.critic.obs_dim,
  "action_shape": list(action.shape),
  "reward_terms": list(cfg.rewards.keys()),
  "termination_terms": list(cfg.terminations.keys()),
  "rl_max_iterations": rl.max_iterations,
  "rl_save_interval": rl.save_interval,
  "rl_num_steps_per_env": rl.num_steps_per_env,
  "rl_obs_groups": rl.obs_groups,
  "rl_logger": rl.logger,
  "rl_upload_model": rl.upload_model,
  "ball_radius_min": float(env.dreureka_ball_radius.min().item()),
  "ball_radius_max": float(env.dreureka_ball_radius.max().item()),
  "ball_friction_min": float(env.dreureka_ball_friction.min().item()),
  "ball_friction_max": float(env.dreureka_ball_friction.max().item()),
  "ball_restitution_min": float(env.dreureka_ball_restitution.min().item()),
  "ball_restitution_max": float(env.dreureka_ball_restitution.max().item()),
  "motor_strength_min": float(env.dreureka_robot_motor_strength.min().item()),
  "motor_strength_max": float(env.dreureka_robot_motor_strength.max().item()),
  "action_lag_unique": sorted(set(int(x) for x in env.dreureka_action_lag_timesteps.detach().cpu().tolist())),
  "reward_mean": float(reward.mean().item()),
  "terminated_any": bool(terminated.any().item()),
  "timeout_any": bool(timeout.any().item()),
  "contract": DREUREKA_CONTRACT,
}
env.close()
print(json.dumps(summary, sort_keys=True))
"""
    result = conda_python(code, cwd=UNITREE_RL_MJLAB_HOME)
    ok = result["returncode"] == 0
    parsed: dict[str, Any] | None = None
    if ok:
        stdout_lines = [line for line in result["stdout"].splitlines() if line.strip()]
        parsed = json.loads(stdout_lines[-1])
        expected = {
            "registered": True,
            "num_envs_train": 4096,
            "episode_length_s": 40.0,
            "commands": [],
            "actor_terms": ["orientation", "joint_pos", "joint_vel", "action", "last_action", "clock", "yaw"],
            "critic_terms": ["object", "body_velocity", "object_velocity", "restitution", "friction"],
            "actor_obs_width": 56 * 15,
            "privileged_obs_width": 11,
            "actor_model_input_dim": 56 * 15,
            "critic_model_input_dim": 56 * 15 + 11,
            "actor_model_obs_groups": ["actor"],
            "critic_model_obs_groups": ["actor", "critic"],
            "reward_terms": [
                "height",
                "balance",
                "smooth_actions",
                "penalize_large_actions",
            ],
            "terrain_type": "generator",
            "terrain_rows": 1,
            "terrain_cols": 1,
            "terrain_size": [20.0, 20.0],
            "terrain_sub_terrains": ["random_rough"],
            "actuator_gains": {
                ".*hip_joint": {"stiffness": 20.0, "damping": 1.0},
                ".*thigh_joint": {"stiffness": 20.0, "damping": 1.0},
                ".*calf_joint": {"stiffness": 40.0, "damping": 2.0},
            },
            "rl_max_iterations": 20000,
            "rl_save_interval": 1000,
            "rl_obs_groups": {"actor": ["actor"], "critic": ["actor", "critic"]},
        }
        checks = {
            "registered": parsed["registered"] is expected["registered"],
            "num_envs_train": parsed["num_envs_train"] == expected["num_envs_train"],
            "episode_length_s": parsed["episode_length_s"] == expected["episode_length_s"],
            "commands_removed": parsed["commands"] == expected["commands"],
            "actor_terms": parsed["actor_terms"] == expected["actor_terms"],
            "critic_terms": parsed["critic_terms"] == expected["critic_terms"],
            "actor_obs_width": parsed["actor_obs_shape"][1] == expected["actor_obs_width"],
            "privileged_obs_width": parsed["critic_obs_shape"][1] == expected["privileged_obs_width"],
            "actor_model_input_dim": parsed["actor_model_input_dim"] == expected["actor_model_input_dim"],
            "critic_model_input_dim": parsed["critic_model_input_dim"] == expected["critic_model_input_dim"],
            "actor_model_obs_groups": parsed["actor_model_obs_groups"] == expected["actor_model_obs_groups"],
            "critic_model_obs_groups": parsed["critic_model_obs_groups"] == expected["critic_model_obs_groups"],
            "reward_terms": parsed["reward_terms"] == expected["reward_terms"],
            "terrain_type": parsed["terrain_type"] == expected["terrain_type"],
            "terrain_rows": parsed["terrain_rows"] == expected["terrain_rows"],
            "terrain_cols": parsed["terrain_cols"] == expected["terrain_cols"],
            "terrain_size": parsed["terrain_size"] == expected["terrain_size"],
            "terrain_sub_terrains": parsed["terrain_sub_terrains"] == expected["terrain_sub_terrains"],
            "terrain_origin_shape": parsed["terrain_origin_shape"] == [1, 1, 3],
            "actuator_gains": parsed["actuator_gains"] == expected["actuator_gains"],
            "rl_max_iterations": parsed["rl_max_iterations"] == expected["rl_max_iterations"],
            "rl_save_interval": parsed["rl_save_interval"] == expected["rl_save_interval"],
            "rl_obs_groups": parsed["rl_obs_groups"] == expected["rl_obs_groups"],
            "ball_radius_range": 0.35 <= parsed["ball_radius_min"] <= parsed["ball_radius_max"] <= 0.45,
            "ball_friction_range": 0.5 <= parsed["ball_friction_min"] <= parsed["ball_friction_max"] <= 2.5,
            "ball_restitution_range": 0.4 <= parsed["ball_restitution_min"] <= parsed["ball_restitution_max"] <= 0.9,
            "motor_strength_range": 0.95 <= parsed["motor_strength_min"] <= parsed["motor_strength_max"] <= 1.05,
            "action_lag": parsed["action_lag_unique"] == [6],
        }
        parsed["checks"] = checks
        ok = all(checks.values())
    report = {
        "generated_at_unix": time.time(),
        "ok": ok,
        "command": result["cmd"],
        "returncode": result["returncode"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "summary": parsed,
    }
    TASK_CONFIG_SMOKE_JSON.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Go2 MJLab Task Config Smoke",
        "",
        f"- Status: {'PASS' if ok else 'FAIL'}",
        f"- Conda env: `{CONDA_ENV_NAME}`",
        f"- JSON evidence: `{rel(TASK_CONFIG_SMOKE_JSON)}`",
        "",
    ]
    if parsed is not None:
        lines.extend(
            [
                "## Summary",
                "",
                f"- Task: `{parsed['task_id']}`",
                f"- Registered: `{parsed['registered']}`",
                f"- Train env count: `{parsed['num_envs_train']}`",
                f"- Smoke env count: `{parsed['num_envs_smoke']}`",
                f"- Terrain: `{parsed['terrain_type']}` `{parsed['terrain_generator_class']}` rows/cols `{parsed['terrain_rows']}`/`{parsed['terrain_cols']}` size `{parsed['terrain_size']}` sub-terrains `{parsed['terrain_sub_terrains']}`",
                f"- Actuator gains: `{parsed['actuator_gains']}`",
                f"- Actor observation shape: `{parsed['actor_obs_shape']}`",
                f"- Privileged observation group shape: `{parsed['critic_obs_shape']}`",
                f"- Actor model input dim: `{parsed['actor_model_input_dim']}` groups `{parsed['actor_model_obs_groups']}`",
                f"- Critic model input dim: `{parsed['critic_model_input_dim']}` groups `{parsed['critic_model_obs_groups']}`",
                f"- Actor terms: `{parsed['actor_terms']}`",
                f"- Critic terms: `{parsed['critic_terms']}`",
                f"- Reward terms: `{parsed['reward_terms']}`",
                f"- Termination terms: `{parsed['termination_terms']}`",
                f"- PPO iterations/save interval: `{parsed['rl_max_iterations']}` / `{parsed['rl_save_interval']}`",
                f"- Ball radius range sampled: `{parsed['ball_radius_min']:.6f}`..`{parsed['ball_radius_max']:.6f}`",
                f"- Ball friction range sampled: `{parsed['ball_friction_min']:.6f}`..`{parsed['ball_friction_max']:.6f}`",
                f"- Ball restitution range sampled: `{parsed['ball_restitution_min']:.6f}`..`{parsed['ball_restitution_max']:.6f}`",
                f"- Motor strength range sampled: `{parsed['motor_strength_min']:.6f}`..`{parsed['motor_strength_max']:.6f}`",
                f"- Action lag samples: `{parsed['action_lag_unique']}`",
                "",
                "## Checks",
                "",
            ]
        )
        for key, value in sorted(parsed["checks"].items()):
            lines.append(f"- `{key}`: `{value}`")
        lines.append("")
    if result["stderr"].strip():
        lines.extend(["## stderr", "", "```text", result["stderr"].strip(), "```", ""])
    TASK_CONFIG_SMOKE_MD.write_text("\n".join(lines), encoding="utf-8")
    if not ok:
        raise SystemExit(f"task config smoke failed; see {TASK_CONFIG_SMOKE_JSON}")


def write_training_driver() -> Path:
    return SCRIPT_ROOT / "train_driver.py"


def launch_train(
    *,
    run_name: str,
    num_envs: int,
    iterations: int,
    steps_per_env: int,
    save_interval: int,
    terrain_rows: int | None,
    terrain_cols: int | None,
    console_log: Path,
    launch_json: Path,
) -> None:
    ensure_dirs()
    setup_env_record()
    driver = write_training_driver()
    log_dir = LOG_ROOT / run_name / "rsl_rl"
    if log_dir.exists():
        shutil.rmtree(log_dir)
    cmd = conda_python_script(
        driver,
        "--log-dir",
        str(log_dir),
        "--num-envs",
        str(num_envs),
        "--iterations",
        str(iterations),
        "--steps-per-env",
        str(steps_per_env),
        "--save-interval",
        str(save_interval),
        "--run-name",
        run_name,
        "--seed",
        "42",
        "--launch-json",
        str(launch_json),
    )
    if terrain_rows is not None:
        cmd.extend(["--terrain-rows", str(terrain_rows)])
    if terrain_cols is not None:
        cmd.extend(["--terrain-cols", str(terrain_cols)])
    rc = run_stream_to_log(cmd, console_log, cwd=UNITREE_RL_MJLAB_HOME)
    if rc != 0:
        raise SystemExit(f"{run_name} training failed with exit code {rc}; see {console_log}")


def train_dry_run() -> None:
    launch_train(
        run_name="train_dry_run",
        num_envs=2,
        iterations=1,
        steps_per_env=2,
        save_interval=100,
        terrain_rows=1,
        terrain_cols=1,
        console_log=LOG_ROOT / "train_dry_run" / "train.log",
        launch_json=ARTIFACT_ROOT / "train_dry_run_launch.json",
    )
    report_training_run(
        run_name="train_dry_run",
        console_log=LOG_ROOT / "train_dry_run" / "train.log",
        curve_csv=ARTIFACT_ROOT / "train_dry_run_reward_curve.csv",
        curve_svg=ARTIFACT_ROOT / "train_dry_run_reward_curve.svg",
        health_json=ARTIFACT_ROOT / "train_dry_run_health.json",
        health_md=ARTIFACT_ROOT / "train_dry_run_health.md",
        min_points=1,
        require_nonzero_reward=False,
    )


def smoke_20min() -> None:
    iterations = int(os.environ.get("GO2_MJLAB_SMOKE_ITERATIONS", "300"))
    launch_train(
        run_name="smoke_20min",
        num_envs=4096,
        iterations=iterations,
        steps_per_env=24,
        save_interval=1000,
        terrain_rows=1,
        terrain_cols=1,
        console_log=LOG_ROOT / "smoke_20min" / "train.log",
        launch_json=ARTIFACT_ROOT / "smoke_20min_launch.json",
    )
    report_smoke_20min()


def train_1_8_budget() -> None:
    launch = {
        "task_id": TASK_ID,
        "num_envs": 4096,
        "iterations": 20000,
        "steps_per_env": 24,
        "save_interval": 1000,
        "log": rel(LOG_ROOT / "train_1_8_budget" / "train.log"),
        "note": "Established single-RTX3090 1/8-budget MJLab train after smoke health gate.",
    }
    TRAIN_1_8_LAUNCH_JSON.write_text(
        json.dumps(launch, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    launch_train(
        run_name="train_1_8_budget",
        num_envs=4096,
        iterations=20000,
        steps_per_env=24,
        save_interval=1000,
        terrain_rows=1,
        terrain_cols=1,
        console_log=LOG_ROOT / "train_1_8_budget" / "train.log",
        launch_json=TRAIN_1_8_LAUNCH_JSON,
    )


def _extract_baseline_curve() -> list[dict[str, float]]:
    if not BASELINE_LOG.exists():
        return []
    rows: list[dict[str, float]] = []
    current: dict[str, float] = {}
    metric_map = {
        "train/episode/rew total/mean": "total",
        "train/episode/episode length/mean": "episode_length",
        "train/episode/rew height/mean": "height",
        "train/episode/rew balance/mean": "balance",
        "train/episode/rew smooth actions/mean": "smooth_actions",
        "train/episode/rew penalize large actions/mean": "penalize_large_actions",
        "iterations": "iteration",
    }
    row_re = re.compile(r"│\s*(.*?)\s*│\s*([-+0-9.eE]+)\s*│")
    for line in BASELINE_LOG.read_text(encoding="utf-8", errors="replace").splitlines():
        match = row_re.search(line)
        if not match:
            continue
        key, value = match.group(1).strip(), float(match.group(2))
        if key not in metric_map:
            continue
        current[metric_map[key]] = value
        if key == "iterations" and "total" in current:
            rows.append(dict(current))
            current = {}
    return rows


def _read_tensorboard_scalars(log_dir: Path) -> dict[str, list[dict[str, float]]]:
    code = (
        "import json, sys; "
        "from pathlib import Path; "
        "from tensorboard.backend.event_processing.event_accumulator import EventAccumulator; "
        "out={}; "
        "paths=list(Path(sys.argv[1]).glob('events.out.tfevents.*')); "
        "\nfor p in paths:\n"
        "  ea=EventAccumulator(str(p)); ea.Reload();\n"
        "  for tag in ea.Tags().get('scalars', []):\n"
        "    out.setdefault(tag, []);\n"
        "    out[tag].extend({'step': e.step, 'wall_time': e.wall_time, 'value': e.value} for e in ea.Scalars(tag));\n"
        "print(json.dumps(out, sort_keys=True))"
    )
    result = run_capture(["conda", "run", "-n", CONDA_ENV_NAME, "python", "-c", code, str(log_dir)], cwd=ROOT)
    if result["returncode"] != 0:
        return {}
    return json.loads(result["stdout"])


def _build_curve(log_dir: Path) -> list[dict[str, float]]:
    scalars = _read_tensorboard_scalars(log_dir)
    terms = {
        "height": "Episode_Reward/height",
        "balance": "Episode_Reward/balance",
        "smooth_actions": "Episode_Reward/smooth_actions",
        "penalize_large_actions": "Episode_Reward/penalize_large_actions",
    }
    by_step: dict[int, dict[str, float]] = {}
    for name, tag in terms.items():
        for event in scalars.get(tag, []):
            step = int(event["step"])
            by_step.setdefault(step, {"iteration": float(step)})[name] = float(event["value"])
    rows: list[dict[str, float]] = []
    for step in sorted(by_step):
        row = by_step[step]
        if all(name in row for name in terms):
            row["total"] = sum(row[name] for name in terms)
            rows.append(row)
    return rows


def _write_curve_csv(rows: list[dict[str, float]], path: Path) -> None:
    fields = ["iteration", "total", "height", "balance", "smooth_actions", "penalize_large_actions", "episode_length"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _write_curve_svg(rows: list[dict[str, float]], baseline: list[dict[str, float]], path: Path) -> None:
    width, height = 900, 420
    margin = 50
    all_points = [(r["iteration"], r["total"]) for r in rows]
    max_iteration = max((r["iteration"] for r in rows), default=0)
    baseline_window = [r for r in baseline if r["iteration"] <= max_iteration]
    all_points += [(r["iteration"], r["total"]) for r in baseline_window]
    if not all_points:
        path.write_text("<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"900\" height=\"420\"/>\n", encoding="utf-8")
        return
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    if xmax == xmin:
        xmax = xmin + 1
    if ymax == ymin:
        ymax = ymin + 1

    def pt(x: float, y: float) -> tuple[float, float]:
        sx = margin + (x - xmin) / (xmax - xmin) * (width - 2 * margin)
        sy = height - margin - (y - ymin) / (ymax - ymin) * (height - 2 * margin)
        return sx, sy

    def poly(points: list[tuple[float, float]], color: str) -> str:
        if not points:
            return ""
        coords = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        return f"<polyline fill=\"none\" stroke=\"{color}\" stroke-width=\"2\" points=\"{coords}\"/>"

    smoke_pts = [pt(r["iteration"], r["total"]) for r in rows]
    base_pts = [pt(r["iteration"], r["total"]) for r in baseline_window]
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="white"/>
<line x1="{margin}" y1="{height-margin}" x2="{width-margin}" y2="{height-margin}" stroke="#333"/>
<line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height-margin}" stroke="#333"/>
{poly(base_pts, "#888")}
{poly(smoke_pts, "#0b6")}
<text x="{margin}" y="25" font-family="monospace" font-size="16">MJLab smoke total reward vs DrEureka early baseline</text>
<text x="{width-margin-210}" y="45" font-family="monospace" font-size="12" fill="#0b6">green: MJLab smoke</text>
<text x="{width-margin-210}" y="62" font-family="monospace" font-size="12" fill="#888">gray: DrEureka baseline</text>
<text x="{margin}" y="{height-12}" font-family="monospace" font-size="12">iteration {xmin:.0f}..{xmax:.0f}</text>
<text x="8" y="{margin}" font-family="monospace" font-size="12" transform="rotate(-90 8,{margin})">reward {ymin:.2f}..{ymax:.2f}</text>
</svg>
"""
    path.write_text(svg, encoding="utf-8")


def report_training_run(
    *,
    run_name: str,
    console_log: Path,
    curve_csv: Path,
    curve_svg: Path,
    health_json: Path,
    health_md: Path,
    min_points: int,
    require_nonzero_reward: bool,
    required_final_iteration: int | None = None,
) -> None:
    log_dir = LOG_ROOT / run_name / "rsl_rl"
    rows = _build_curve(log_dir)
    baseline = _extract_baseline_curve()
    _write_curve_csv(rows, curve_csv)
    _write_curve_svg(rows, baseline, curve_svg)
    text = console_log.read_text(encoding="utf-8", errors="replace") if console_log.exists() else ""
    latest = rows[-1] if rows else {}
    max_iteration = max((row["iteration"] for row in rows), default=0)
    baseline_same = [row for row in baseline if row["iteration"] <= max_iteration]
    baseline_latest = baseline_same[-1] if baseline_same else {}
    finite = all(all(value == value and abs(value) != float("inf") for value in row.values()) for row in rows)
    reward_nonzero = bool(rows) and any(abs(row["total"]) > 1e-9 for row in rows)
    total_delta = rows[-1]["total"] - rows[0]["total"] if len(rows) >= 2 else None
    checks = {
        "process_log_exists": console_log.exists(),
        "no_traceback": "Traceback (most recent call last)" not in text,
        "no_nan_text": "nan" not in text.lower(),
        "curve_points": len(rows) >= min_points,
        "finite_curve": finite,
    }
    if required_final_iteration is not None:
        checks["final_iteration_reached"] = bool(rows) and rows[-1]["iteration"] >= required_final_iteration
    if require_nonzero_reward:
        checks["reward_nonzero"] = reward_nonzero
    ok = all(checks.values())
    report = {
        "generated_at_unix": time.time(),
        "ok": ok,
        "run_name": run_name,
        "log_dir": str(log_dir),
        "console_log": rel(console_log),
        "curve_csv": rel(curve_csv),
        "curve_svg": rel(curve_svg),
        "num_curve_points": len(rows),
        "latest": latest,
        "first": rows[0] if rows else {},
        "total_delta": total_delta,
        "baseline_points_compared": len(baseline_same),
        "baseline_latest": baseline_latest,
        "checks": checks,
    }
    health_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        f"# {run_name} Health",
        "",
        f"- Status: {'PASS' if ok else 'FAIL'}",
        f"- Curve points: `{len(rows)}`",
        f"- Latest total reward: `{latest.get('total')}`",
        f"- Total reward delta: `{total_delta}`",
        f"- Baseline latest compared total: `{baseline_latest.get('total')}`",
        f"- Console log: `{rel(console_log)}`",
        f"- Curve CSV: `{rel(curve_csv)}`",
        f"- Curve SVG: `{rel(curve_svg)}`",
        "",
        "## Checks",
        "",
    ]
    for key, value in sorted(checks.items()):
        lines.append(f"- `{key}`: `{value}`")
    health_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not ok:
        raise SystemExit(f"{run_name} health failed; see {health_json}")


def report_smoke_20min() -> None:
    report_training_run(
        run_name="smoke_20min",
        console_log=LOG_ROOT / "smoke_20min" / "train.log",
        curve_csv=SMOKE_20MIN_CURVE_CSV,
        curve_svg=SMOKE_20MIN_CURVE_SVG,
        health_json=SMOKE_20MIN_HEALTH_JSON,
        health_md=SMOKE_20MIN_HEALTH_MD,
        min_points=2,
        require_nonzero_reward=True,
    )


def report_train_1_8_budget() -> None:
    report_training_run(
        run_name="train_1_8_budget",
        console_log=LOG_ROOT / "train_1_8_budget" / "train.log",
        curve_csv=TRAIN_1_8_CURVE_CSV,
        curve_svg=TRAIN_1_8_CURVE_SVG,
        health_json=TRAIN_1_8_HEALTH_JSON,
        health_md=TRAIN_1_8_HEALTH_MD,
        min_points=20000,
        require_nonzero_reward=True,
        required_final_iteration=19999,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "cmd",
        choices=[
            "preflight",
            "source-contract",
            "setup-env-record",
            "import-smoke",
            "task-config-smoke",
            "train-dry-run",
            "smoke-20min",
            "report-smoke-20min",
            "train-1-8-budget",
            "report-train-1-8-budget",
        ],
    )
    args = parser.parse_args()
    if args.cmd == "preflight":
        preflight()
    elif args.cmd == "source-contract":
        write_source_contract()
    elif args.cmd == "setup-env-record":
        setup_env_record()
    elif args.cmd == "import-smoke":
        import_smoke()
    elif args.cmd == "task-config-smoke":
        task_config_smoke()
    elif args.cmd == "train-dry-run":
        train_dry_run()
    elif args.cmd == "smoke-20min":
        smoke_20min()
    elif args.cmd == "report-smoke-20min":
        report_smoke_20min()
    elif args.cmd == "train-1-8-budget":
        train_1_8_budget()
    elif args.cmd == "report-train-1-8-budget":
        report_train_1_8_budget()


if __name__ == "__main__":
    main()
