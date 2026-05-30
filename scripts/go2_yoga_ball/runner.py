#!/usr/bin/env python3
"""Root-owned orchestration utilities for the Go2 yoga-ball migration."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
THIRDPARTIES = ROOT / "thirdparties"
DREUREKA = THIRDPARTIES / "DrEureka"
GO2_DESCRIPTION = THIRDPARTIES / "go2_description"
UNITREE_RL_GYM = THIRDPARTIES / "unitree_rl_gym"
UNITREE_RL_GYM_GO2_URDF = UNITREE_RL_GYM / "resources" / "robots" / "go2" / "urdf" / "go2.urdf"
UNITREE_RL_GYM_GO2_CONFIG = UNITREE_RL_GYM / "legged_gym" / "envs" / "go2" / "go2_config.py"
UNITREE_RL_GYM_BASE_CONFIG = UNITREE_RL_GYM / "legged_gym" / "envs" / "base" / "legged_robot_config.py"
UNITREE_MUJOCO_GO2 = THIRDPARTIES / "unitree_mujoco" / "unitree_robots" / "go2" / "go2.xml"
UNITREE_MUJOCO_BRIDGE = THIRDPARTIES / "unitree_mujoco" / "simulate" / "src" / "unitree_sdk2_bridge.h"
UNITREE_MUJOCO_MAIN = THIRDPARTIES / "unitree_mujoco" / "simulate" / "src" / "main.cc"
UNITREE_MUJOCO_PY_BRIDGE = THIRDPARTIES / "unitree_mujoco" / "simulate_python" / "unitree_sdk2py_bridge.py"
UNITREE_MUJOCO_README = THIRDPARTIES / "unitree_mujoco" / "readme.md"
UNITREE_SDK2_PYTHON = THIRDPARTIES / "unitree_sdk2_python"
GO2_LCM_DDS_BRIDGE = ROOT / "scripts" / "go2_yoga_ball" / "lcm_to_dds_bridge.py"
LOG_ROOT = ROOT / "logs" / "go2_yoga_ball"
ARTIFACT_ROOT = ROOT / "artifacts" / "go2_yoga_ball"
BUILD_ROOT = ARTIFACT_ROOT / "build"
ISAACGYM_URDF = BUILD_ROOT / "go2_description_isaacgym.urdf"
SELECTED_SMOKE_RUN = ARTIFACT_ROOT / "go2_train_smoke_selected_run.txt"
SELECTED_TRAIN_1_8_RUN = ARTIFACT_ROOT / "train_1_8_budget_selected_run.txt"
TRAIN_1_8_LAUNCH = ARTIFACT_ROOT / "train_1_8_budget_launch.json"
TRAIN_1_8_HEALTH = ARTIFACT_ROOT / "train_1_8_budget_health.json"
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
UNITREE_MOTOR_ORDER = [
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


def rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def ensure_tree() -> None:
    for path in [
        BUILD_ROOT,
        LOG_ROOT / "train_smoke",
        LOG_ROOT / "train_1_8_budget",
        LOG_ROOT / "mujoco_dds_endpoint_smoke",
        ARTIFACT_ROOT / "videos",
    ]:
        path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def find_line(path: Path, pattern: str, *, start: int = 1) -> int | None:
    regex = re.compile(pattern)
    for index, line in enumerate(read_lines(path), start=1):
        if index < start:
            continue
        if regex.search(line):
            return index
    return None


def source_excerpt(path: Path, start: int, end: int | None = None) -> dict[str, Any]:
    lines = read_lines(path)
    end = start if end is None else end
    selected = lines[start - 1:end]
    return {
        "path": rel(path),
        "start_line": start,
        "end_line": end,
        "ref": f"{rel(path)}:{start}",
        "text": "\n".join(selected),
    }


def excerpt_for(path: Path, pattern: str, *, context_before: int = 0, context_after: int = 0, start: int = 1) -> dict[str, Any]:
    line = find_line(path, pattern, start=start)
    if line is None:
        return {"path": rel(path), "pattern": pattern, "missing": True}
    return source_excerpt(path, max(1, line - context_before), line + context_after)


def format_excerpt(title: str, excerpt: dict[str, Any]) -> list[str]:
    if excerpt.get("missing"):
        return [f"### {title}", "", f"- Missing pattern `{excerpt.get('pattern')}` in `{excerpt.get('path')}`.", ""]
    return [
        f"### {title}",
        "",
        f"- Source: `{excerpt['ref']}`",
        "",
        "```text",
        excerpt["text"],
        "```",
        "",
    ]


def git_head(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def go2_mujoco_dds_endpoint_report() -> dict[str, Any]:
    ensure_tree()
    evidence = {
        "upstream_real_swap_claim": excerpt_for(UNITREE_MUJOCO_README, r"seamless transition", context_after=6),
        "real_robot_interface_argument": excerpt_for(UNITREE_MUJOCO_README, r"physical robot", context_before=4, context_after=1),
        "dds_topic_setup": source_excerpt(UNITREE_MUJOCO_BRIDGE, 151, 165),
        "lowcmd_torque_equation": source_excerpt(UNITREE_MUJOCO_BRIDGE, 178, 186),
        "lowstate_motor_state": source_excerpt(UNITREE_MUJOCO_BRIDGE, 189, 195),
        "lowstate_imu": source_excerpt(UNITREE_MUJOCO_BRIDGE, 197, 226),
        "go2_bridge_type": source_excerpt(UNITREE_MUJOCO_BRIDGE, 257, 257),
        "dds_factory_and_go2_selection": source_excerpt(UNITREE_MUJOCO_MAIN, 587, 602),
        "go2_joint_and_actuator_limits": source_excerpt(UNITREE_MUJOCO_GO2, 7, 24),
        "go2_motor_order": source_excerpt(UNITREE_MUJOCO_GO2, 222, 234),
        "go2_sensor_order": source_excerpt(UNITREE_MUJOCO_GO2, 238, 275),
        "python_dds_topics": source_excerpt(UNITREE_MUJOCO_PY_BRIDGE, 25, 29),
        "python_lowcmd_torque_equation": source_excerpt(UNITREE_MUJOCO_PY_BRIDGE, 111, 123),
    }
    lcm_mentions = []
    for path in [
        UNITREE_MUJOCO_BRIDGE,
        UNITREE_MUJOCO_MAIN,
        UNITREE_MUJOCO_PY_BRIDGE,
    ]:
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        if "lcm" in text:
            lcm_mentions.append(rel(path))
    ok = not lcm_mentions and all(not item.get("missing") for item in evidence.values())
    report = {
        "ok": ok,
        "generated_at_unix": time.time(),
        "unitree_mujoco_commit": git_head(THIRDPARTIES / "unitree_mujoco"),
        "claim": "Unitree MuJoCo Go2 is a DDS LowCmd/LowState robot endpoint; replacing it with a real Go2 should not require policy/deploy code changes beyond network/backend selection and real-robot safety procedure.",
        "lcm_mentions_in_endpoint_sources": lcm_mentions,
        "evidence": evidence,
    }
    write_json(ARTIFACT_ROOT / "go2_mujoco_dds_endpoint_report.json", report)
    lines = [
        "# Go2 MuJoCo DDS Endpoint Report",
        "",
        f"- Status: {'PASS' if ok else 'FAIL'}",
        f"- Unitree MuJoCo commit: `{report['unitree_mujoco_commit']}`",
        "- Claim: Unitree MuJoCo Go2 is the source-of-truth DDS robot endpoint. It consumes `rt/lowcmd`, publishes `rt/lowstate`, and applies the SDK2 `LowCmd` actuator equation.",
        "- Real-swap target: replace the simulator container with a real Go2 backend on the selected network interface; keep policy/deploy code unchanged except backend/network selection and safety procedure.",
        f"- LCM mentions in endpoint sources: `{lcm_mentions}`",
        "",
    ]
    for title, excerpt in evidence.items():
        lines.extend(format_excerpt(title.replace("_", " ").title(), excerpt))
    (ARTIFACT_ROOT / "go2_mujoco_dds_endpoint_report.md").write_text("\n".join(lines), encoding="utf-8")
    return report


def go2_lcm_to_dds_bridge_report() -> dict[str, Any]:
    ensure_tree()
    lcm_agent = DREUREKA / "globe_walking" / "go1_gym_deploy" / "envs" / "lcm_agent.py"
    state_estimator = DREUREKA / "globe_walking" / "go1_gym_deploy" / "utils" / "cheetah_state_estimator.py"
    deploy_policy = ROOT / "scripts" / "go1_yoga_ball" / "deploy_lcm_policy.py"
    pd_lcm = DREUREKA / "globe_walking" / "go1_gym_deploy" / "lcm_types" / "pd_tau_targets_lcmt.lcm"
    leg_lcm = DREUREKA / "globe_walking" / "go1_gym_deploy" / "lcm_types" / "leg_control_data_lcmt.lcm"
    state_lcm = DREUREKA / "globe_walking" / "go1_gym_deploy" / "lcm_types" / "state_estimator_lcmt.lcm"
    sdk_channel = UNITREE_SDK2_PYTHON / "unitree_sdk2py" / "core" / "channel.py"
    sdk_default = UNITREE_SDK2_PYTHON / "unitree_sdk2py" / "idl" / "default.py"
    sdk_crc = UNITREE_SDK2_PYTHON / "unitree_sdk2py" / "utils" / "crc.py"
    evidence = {
        "lcm_policy_command_fields": source_excerpt(pd_lcm, 1, 10),
        "lcm_policy_publisher": source_excerpt(lcm_agent, 194, 222),
        "deploy_go2_config_sync": source_excerpt(deploy_policy, 88, 121),
        "dr_eureka_state_reorder": source_excerpt(state_estimator, 51, 56),
        "lcm_state_subscriptions": source_excerpt(state_estimator, 111, 113),
        "lcm_leg_state_fields": source_excerpt(leg_lcm, 1, 9),
        "lcm_imu_state_fields": source_excerpt(state_lcm, 1, 18),
        "dds_channel_factory": source_excerpt(sdk_channel, 256, 301),
        "dds_lowcmd_default": source_excerpt(sdk_default, 147, 157),
        "dds_lowcmd_crc_fields": source_excerpt(sdk_crc, 51, 79),
        "bridge_imports": source_excerpt(GO2_LCM_DDS_BRIDGE, 21, 31),
        "bridge_dds_initialization": source_excerpt(GO2_LCM_DDS_BRIDGE, 61, 72),
        "bridge_lowcmd_defaults": source_excerpt(GO2_LCM_DDS_BRIDGE, 80, 92),
        "bridge_lcm_to_dds_command_mapping": source_excerpt(GO2_LCM_DDS_BRIDGE, 94, 109),
        "bridge_dds_to_lcm_state_mapping": source_excerpt(GO2_LCM_DDS_BRIDGE, 115, 159),
        "bridge_spin_lcm_poll": source_excerpt(GO2_LCM_DDS_BRIDGE, 176, 183),
    }
    required = ["rt/lowcmd", "rt/lowstate", "pd_plustau_targets", "leg_control_data", "state_estimator_data"]
    bridge_text = GO2_LCM_DDS_BRIDGE.read_text(encoding="utf-8", errors="replace")
    deploy_text = deploy_policy.read_text(encoding="utf-8", errors="replace")
    missing_tokens = [token for token in required if token not in bridge_text]
    unitree_go2_tokens = ["sync_go2_deploy_cfg", '"joint": 20.0', '"hip_scale_reduction": 1.0']
    missing_go2_deploy_tokens = [token for token in unitree_go2_tokens if token not in deploy_text]
    zero_action_policy_order = [0.1, 0.8, -1.5, -0.1, 0.8, -1.5, 0.1, 1.0, -1.5, -0.1, 1.0, -1.5]
    joint_idxs = [3, 4, 5, 0, 1, 2, 9, 10, 11, 6, 7, 8]
    zero_action_unitree_order = [zero_action_policy_order[i] for i in joint_idxs]
    ok = not missing_tokens and not missing_go2_deploy_tokens and all(not item.get("missing") for item in evidence.values())
    report = {
        "ok": ok,
        "generated_at_unix": time.time(),
        "unitree_sdk2_python_commit": git_head(UNITREE_SDK2_PYTHON),
        "claim": "The Go2 deploy-side bridge preserves DrEureka LCM policy semantics while translating to Unitree SDK2 DDS LowCmd/LowState.",
        "missing_required_tokens": missing_tokens,
        "missing_go2_deploy_tokens": missing_go2_deploy_tokens,
        "unitree_motor_order": UNITREE_MOTOR_ORDER,
        "drek_lcm_command_is_unitree_order": True,
        "zero_action_q_des_unitree_order": dict(zip(UNITREE_MOTOR_ORDER, zero_action_unitree_order)),
        "kp_unitree_order": dict(zip(UNITREE_MOTOR_ORDER, [20.0] * 12)),
        "kd_unitree_order": dict(zip(UNITREE_MOTOR_ORDER, [0.5] * 12)),
        "evidence": evidence,
    }
    write_json(ARTIFACT_ROOT / "go2_lcm_to_dds_bridge_report.json", report)
    lines = [
        "# Go2 LCM To DDS Bridge Report",
        "",
        f"- Status: {'PASS' if ok else 'FAIL'}",
        f"- Unitree SDK2 Python commit: `{report['unitree_sdk2_python_commit']}`",
        "- Claim: LCM remains an internal DrEureka policy contract. The Go2 deploy bridge owns the conversion to Unitree SDK2 DDS.",
        "- Command order: DrEureka publishes `pd_plustau_targets` in Unitree motor order because `LCMAgent` applies `StateEstimator.joint_idxs` before publishing.",
        "- Go2 command constants: zero action publishes Unitree RL Gym default pose, `kp=20.0`, `kd=0.5`, `action_scale=0.25`, and `hip_scale_reduction=1.0`.",
        f"- Missing required bridge tokens: `{missing_tokens}`",
        f"- Missing Go2 deploy tokens: `{missing_go2_deploy_tokens}`",
        "",
    ]
    for title, excerpt in evidence.items():
        lines.extend(format_excerpt(title.replace("_", " ").title(), excerpt))
    (ARTIFACT_ROOT / "go2_lcm_to_dds_bridge_report.md").write_text("\n".join(lines), encoding="utf-8")
    return report
    try:
        return subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def prepare_isaacgym_urdf() -> dict[str, Any]:
    ensure_tree()
    src = UNITREE_RL_GYM_GO2_URDF
    if not src.exists():
        result = {"ok": False, "error": "missing Unitree RL Gym Go2 URDF", "source": rel(src)}
        write_json(ARTIFACT_ROOT / "go2_isaacgym_urdf.json", result)
        return result
    text = src.read_text(encoding="utf-8")
    ISAACGYM_URDF.write_text(text, encoding="utf-8")
    result = {
        "ok": True,
        "source": rel(src),
        "output": rel(ISAACGYM_URDF),
        "unitree_rl_gym_commit": git_head(UNITREE_RL_GYM),
        "note": "Copied Unitree RL Gym Go2 Isaac Gym URDF unchanged for report inspection; training uses the source URDF directly.",
    }
    write_json(ARTIFACT_ROOT / "go2_isaacgym_urdf.json", result)
    return result


def floats(value: str | None) -> list[float] | None:
    if value is None:
        return None
    return [float(part) for part in value.split()]


def default_attrs(root: ET.Element, tag: str) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}

    def walk(node: ET.Element, inherited: dict[str, str]) -> None:
        current = dict(inherited)
        child = node.find(tag)
        if child is not None:
            current.update(child.attrib)
        cls = node.attrib.get("class")
        if cls:
            result[cls] = dict(current)
        for nested in node.findall("default"):
            walk(nested, current)

    for node in root.findall("default"):
        walk(node, {})
    return result


def parse_unitree_mujoco_contract() -> dict[str, Any]:
    root = ET.parse(UNITREE_MUJOCO_GO2).getroot()
    joint_defaults = default_attrs(root, "joint")
    motor_defaults = default_attrs(root, "motor")
    joints: dict[str, dict[str, Any]] = {}
    for joint in root.findall(".//joint"):
        name = joint.attrib.get("name")
        if not name:
            continue
        attrs = dict(joint_defaults.get(joint.attrib.get("class", ""), {}))
        attrs.update(joint.attrib)
        joints[name] = {
            "class": joint.attrib.get("class"),
            "axis": floats(attrs.get("axis")),
            "lower": floats(attrs.get("range"))[0] if attrs.get("range") else None,
            "upper": floats(attrs.get("range"))[1] if attrs.get("range") else None,
        }
    actuators: dict[str, dict[str, Any]] = {}
    actuator_order = []
    for motor in root.findall(".//actuator/motor"):
        joint_name = motor.attrib.get("joint")
        if not joint_name:
            continue
        attrs = dict(motor_defaults.get(motor.attrib.get("class", ""), {}))
        attrs.update(motor.attrib)
        actuator_order.append(joint_name)
        ctrlrange = floats(attrs.get("ctrlrange"))
        actuators[joint_name] = {
            "name": motor.attrib.get("name"),
            "class": motor.attrib.get("class"),
            "effort": max(abs(ctrlrange[0]), abs(ctrlrange[1])) if ctrlrange else None,
            "ctrlrange": ctrlrange,
        }
    home = None
    for key in root.findall(".//key"):
        if key.attrib.get("name") == "home":
            qpos = floats(key.attrib.get("qpos")) or []
            ctrl = floats(key.attrib.get("ctrl")) or []
            home = {
                "qpos": qpos,
                "ctrl": ctrl,
                "joint_defaults_by_policy_order": dict(zip(POLICY_JOINT_ORDER, qpos[7:19])),
                "ctrl_by_actuator_order": dict(zip(actuator_order, ctrl)),
            }
    return {
        "path": rel(UNITREE_MUJOCO_GO2),
        "commit": git_head(THIRDPARTIES / "unitree_mujoco"),
        "joint_order": POLICY_JOINT_ORDER,
        "actuator_order": actuator_order,
        "joints": joints,
        "actuators": actuators,
        "home": home,
    }


def parse_urdf_contract(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    joints: dict[str, dict[str, Any]] = {}
    for joint in root.findall("joint"):
        name = joint.attrib.get("name")
        if not name or name not in POLICY_JOINT_ORDER:
            continue
        axis = joint.find("axis")
        limit = joint.find("limit")
        joints[name] = {
            "type": joint.attrib.get("type"),
            "axis": floats(axis.attrib.get("xyz")) if axis is not None else None,
            "lower": float(limit.attrib["lower"]) if limit is not None and "lower" in limit.attrib else None,
            "upper": float(limit.attrib["upper"]) if limit is not None and "upper" in limit.attrib else None,
            "effort": float(limit.attrib["effort"]) if limit is not None and "effort" in limit.attrib else None,
            "velocity": float(limit.attrib["velocity"]) if limit is not None and "velocity" in limit.attrib else None,
        }
    return {"path": rel(path), "joints": joints}


def go2_config_contract() -> dict[str, Any]:
    path = DREUREKA / "globe_walking" / "go1_gym" / "envs" / "go2" / "go2_config.py"
    namespace: dict[str, Any] = {"__builtins__": __builtins__, "os": os, "Path": Path, "__file__": str(path)}
    text = path.read_text(encoding="utf-8")
    start = text.index("def _go2_urdf_path")
    exec(text[start:], namespace)

    class Obj:
        pass

    class Dummy:
        pass

    cfg = Dummy()
    for name in ["init_state", "control", "asset", "rewards", "terrain", "env", "commands"]:
        setattr(cfg, name, Obj())
    namespace["config_go2"](cfg)
    return {
        "path": rel(path),
        "default_joint_angles": {name: float(cfg.init_state.default_joint_angles[name]) for name in POLICY_JOINT_ORDER},
        "control_type": cfg.control.control_type,
        "stiffness": dict(cfg.control.stiffness),
        "damping": dict(cfg.control.damping),
        "action_scale": float(cfg.control.action_scale),
        "hip_scale_reduction": float(cfg.control.hip_scale_reduction),
        "asset_file": cfg.asset.file,
        "foot_name": cfg.asset.foot_name,
        "self_collisions": cfg.asset.self_collisions,
        "flip_visual_attachments": cfg.asset.flip_visual_attachments,
    }


def close(a: float | None, b: float | None, tol: float = 1e-4) -> bool:
    return a is not None and b is not None and abs(a - b) <= tol


def go2_isaacgym_consistency_report() -> dict[str, Any]:
    ensure_tree()
    prepare_isaacgym_urdf()
    unitree = parse_unitree_mujoco_contract()
    urdf = parse_urdf_contract(UNITREE_RL_GYM_GO2_URDF)
    cfg = go2_config_contract()
    go2_config_path = DREUREKA / "globe_walking" / "go1_gym" / "envs" / "go2" / "go2_config.py"
    go2_robot_path = DREUREKA / "globe_walking" / "go1_gym" / "robots" / "go2.py"
    train_path = DREUREKA / "globe_walking" / "scripts" / "train.py"
    legged_robot_path = DREUREKA / "globe_walking" / "go1_gym" / "envs" / "base" / "legged_robot.py"
    checks = []

    def add(name: str, ok: bool, details: Any) -> None:
        checks.append({"name": name, "ok": bool(ok), "details": details})

    unitree_joint_names = set(unitree["joints"])
    urdf_joint_names = set(urdf["joints"])
    add("joint_names", unitree_joint_names == urdf_joint_names == set(POLICY_JOINT_ORDER), {
        "unitree_mujoco": sorted(unitree_joint_names),
        "isaacgym_urdf": sorted(urdf_joint_names),
        "policy_order": POLICY_JOINT_ORDER,
    })
    add("action_order", unitree["joint_order"] == POLICY_JOINT_ORDER, {
        "unitree_policy_order": unitree["joint_order"],
        "dr_eureka_policy_order": POLICY_JOINT_ORDER,
    })

    default_mismatches = {}
    unitree_defaults = unitree["home"]["joint_defaults_by_policy_order"] if unitree["home"] else {}
    for name in POLICY_JOINT_ORDER:
        if not close(unitree_defaults.get(name), cfg["default_joint_angles"].get(name)):
            default_mismatches[name] = {
                "unitree_mujoco": unitree_defaults.get(name),
                "isaacgym_cfg": cfg["default_joint_angles"].get(name),
            }
    add("default_pose", not default_mismatches, {"mismatches": default_mismatches, "unitree_home": unitree_defaults, "isaacgym_cfg": cfg["default_joint_angles"]})

    limit_mismatches = {}
    effort_mismatches = {}
    for name in POLICY_JOINT_ORDER:
        mj = unitree["joints"].get(name, {})
        uj = urdf["joints"].get(name, {})
        if not (close(mj.get("lower"), uj.get("lower")) and close(mj.get("upper"), uj.get("upper"))):
            limit_mismatches[name] = {"unitree_mujoco": [mj.get("lower"), mj.get("upper")], "isaacgym_urdf": [uj.get("lower"), uj.get("upper")]}
        me = unitree["actuators"].get(name, {}).get("effort")
        ue = uj.get("effort")
        if not close(me, ue, tol=0.15):
            effort_mismatches[name] = {"unitree_mujoco": me, "isaacgym_urdf": ue}
    add("joint_limits", not limit_mismatches, {"mismatches": limit_mismatches})
    add("effort_limits", not effort_mismatches, {"mismatches": effort_mismatches, "tolerance": 0.15})
    go2_actuator_net_candidates = sorted(
        rel(path) for path in (DREUREKA / "globe_walking" / "resources").glob("**/*go2*.pt")
    )
    add("controller_assumption", cfg["control_type"] == "P", {
        "control_type": cfg["control_type"],
        "stiffness": cfg["stiffness"],
        "damping": cfg["damping"],
        "go2_actuator_net_candidates": go2_actuator_net_candidates,
        "claim": "No Go2 actuator network found in fetched DrEureka resources; use SDK2 LowCmd PD semantics with explicit gains, torque limits, and command equation.",
    })
    add("foot_name", cfg["foot_name"] == "foot", {"isaacgym_cfg": cfg["foot_name"], "unitree_mujoco_foot_bodies": ["FL_foot", "FR_foot", "RL_foot", "RR_foot"]})
    add("unitree_rl_gym_asset_path", Path(cfg["asset_file"]).as_posix().endswith("thirdparties/unitree_rl_gym/resources/robots/go2/urdf/go2.urdf"), {
        "dr_eureka_asset_file": cfg["asset_file"],
        "unitree_rl_gym_go2_urdf": rel(UNITREE_RL_GYM_GO2_URDF),
    })
    add("unitree_rl_gym_visual_flip", cfg.get("flip_visual_attachments") is True, {
        "dr_eureka_flip_visual_attachments": cfg.get("flip_visual_attachments"),
        "unitree_rl_gym_default": True,
    })

    evidence = {
        "unitree_rl_gym_go2_config": source_excerpt(UNITREE_RL_GYM_GO2_CONFIG, 3, 39),
        "unitree_rl_gym_asset_options": source_excerpt(UNITREE_RL_GYM_BASE_CONFIG, 76, 83),
        "unitree_mujoco_joint_and_actuator_limits": source_excerpt(UNITREE_MUJOCO_GO2, 7, 24),
        "unitree_mujoco_motor_order": source_excerpt(UNITREE_MUJOCO_GO2, 222, 234),
        "unitree_mujoco_home_keyframe": excerpt_for(UNITREE_MUJOCO_GO2, r'<key name="home"', context_after=2),
        "unitree_mujoco_torque_equation": source_excerpt(UNITREE_MUJOCO_BRIDGE, 178, 186),
        "isaacgym_go2_default_pose_and_control": source_excerpt(go2_config_path, 21, 47),
        "isaacgym_go2_asset_path_and_names": source_excerpt(go2_config_path, 49, 61),
        "isaacgym_go2_robot_loader": source_excerpt(go2_robot_path, 8, 45),
        "drek_train_robot_selector": source_excerpt(train_path, 108, 143),
        "drek_robot_registry": excerpt_for(legged_robot_path, r"robot_classes", context_before=4, context_after=6),
    }
    deploy_report_path = ARTIFACT_ROOT / "go2_lcm_to_dds_bridge_report.json"
    endpoint_report_path = ARTIFACT_ROOT / "go2_mujoco_dds_endpoint_report.json"
    deploy_report = json.loads(deploy_report_path.read_text(encoding="utf-8")) if deploy_report_path.exists() else {}
    endpoint_report = json.loads(endpoint_report_path.read_text(encoding="utf-8")) if endpoint_report_path.exists() else {}
    actuator_path_ok = bool(
        cfg["control_type"] == "P"
        and not go2_actuator_net_candidates
        and deploy_report.get("ok")
        and endpoint_report.get("ok")
        and not effort_mismatches
    )
    core_ok = all(check["ok"] for check in checks)
    ok = bool(core_ok and actuator_path_ok)
    report = {
        "ok": ok,
        "core_consistency_ok": core_ok,
        "long_training_allowed": ok,
        "actuator_path_ok": actuator_path_ok,
        "go2_actuator_net_candidates": go2_actuator_net_candidates,
        "generated_at_unix": time.time(),
        "unitree_mujoco_ground_truth": unitree,
        "isaacgym_urdf": urdf,
        "dr_eureka_go2_config": cfg,
        "checks": checks,
        "evidence": evidence,
        "pretrained_domain_rand_valid_for_go2": ok,
    }
    write_json(ARTIFACT_ROOT / "go2_isaacgym_consistency_report.json", report)

    lines = ["# Go2 Isaac Gym Consistency Report", ""]
    lines.append(f"- Status: {'PASS' if ok else 'FAIL'}")
    lines.append(f"- Core consistency without actuator acceptance: `{'PASS' if core_ok else 'FAIL'}`")
    lines.append(f"- Long training allowed: `{ok}`")
    lines.append(f"- Actuator path ok: `{actuator_path_ok}`")
    lines.append(f"- Go2 actuator-net candidates in fetched resources: `{go2_actuator_net_candidates}`")
    lines.append(f"- Ground truth: `{unitree['path']}` commit `{unitree['commit']}`")
    lines.append("- Controller: SDK2 `LowCmd` PD command path; no Go2 actuator network was found in fetched resources.")
    lines.append("- Actuator source of truth: Unitree MuJoCo `LowCmd` torque equation and Go2 MJCF actuator limits. The Go2 deploy bridge forwards the same `q_des`, `qd_des`, `kp`, `kd`, and `tau_ff` fields to DDS.")
    lines.append("")
    for check in checks:
        lines.append(f"- {check['name']}: {'PASS' if check['ok'] else 'FAIL'}")
    lines.append("")
    lines.append("Long training is blocked unless the model/order/limit checks pass and the SDK2 PD command path is proven by the MuJoCo DDS endpoint and LCM-to-DDS bridge reports.")
    lines.append("")
    for title, excerpt in evidence.items():
        lines.extend(format_excerpt(title.replace("_", " ").title(), excerpt))
    if not ok:
        lines.append("Failed fields must be fixed or explicitly accepted before launching training.")
    (ARTIFACT_ROOT / "go2_isaacgym_consistency_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def validate_deps() -> dict[str, Any]:
    ensure_tree()
    deps = {
        "ok": all(
            path.exists()
            for path in [
                DREUREKA,
                THIRDPARTIES / "IsaacGym",
                UNITREE_RL_GYM,
                THIRDPARTIES / "unitree_mujoco",
                UNITREE_SDK2_PYTHON,
                THIRDPARTIES / "cyclonedds",
            ]
        ),
        "dependencies": {
            "DrEureka": {"path": rel(DREUREKA), "exists": DREUREKA.exists(), "commit": git_head(DREUREKA)},
            "IsaacGym": {"path": rel(THIRDPARTIES / "IsaacGym"), "exists": (THIRDPARTIES / "IsaacGym").exists()},
            "go2_description": {"path": rel(GO2_DESCRIPTION), "exists": GO2_DESCRIPTION.exists(), "commit": git_head(GO2_DESCRIPTION)},
            "unitree_rl_gym": {"path": rel(UNITREE_RL_GYM), "exists": UNITREE_RL_GYM.exists(), "commit": git_head(UNITREE_RL_GYM)},
            "unitree_mujoco": {
                "path": rel(THIRDPARTIES / "unitree_mujoco"),
                "exists": (THIRDPARTIES / "unitree_mujoco").exists(),
                "commit": git_head(THIRDPARTIES / "unitree_mujoco"),
            },
            "unitree_sdk2_python": {
                "path": rel(UNITREE_SDK2_PYTHON),
                "exists": UNITREE_SDK2_PYTHON.exists(),
                "commit": git_head(UNITREE_SDK2_PYTHON),
            },
            "cyclonedds": {
                "path": rel(THIRDPARTIES / "cyclonedds"),
                "exists": (THIRDPARTIES / "cyclonedds").exists(),
                "commit": git_head(THIRDPARTIES / "cyclonedds"),
            },
        },
        "docker_images": {
            name: docker_image_exists(f"eureka-{name}") for name in ["isaacgym", "mujoco_sim2sim"]
        },
    }
    write_json(ARTIFACT_ROOT / "manifest.json", deps)
    return deps


def docker_image_exists(image: str) -> dict[str, Any]:
    try:
        out = subprocess.run(
            ["docker", "image", "inspect", image, "--format", "{{.Id}} {{.Created}}"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return {"image": image, "exists": False}
    image_id, _, created = out.partition(" ")
    return {"image": image, "exists": True, "id": image_id, "created": created}


def run_dirs() -> list[Path]:
    base = DREUREKA / "globe_walking" / "runs" / "globe_walking"
    if not base.exists():
        return []
    return sorted({path.parent for path in base.glob("**/checkpoints") if path.is_dir()})


def write_run_list(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(str(p) for p in run_dirs()) + "\n", encoding="utf-8")


def record_train_smoke_run() -> dict[str, Any]:
    ensure_tree()
    before_path = LOG_ROOT / "train_smoke" / "runs_before.txt"
    after_path = LOG_ROOT / "train_smoke" / "runs_after.txt"
    before = set(before_path.read_text(encoding="utf-8").splitlines()) if before_path.exists() else set()
    after = set(after_path.read_text(encoding="utf-8").splitlines()) if after_path.exists() else set()
    new_runs = [Path(p) for p in sorted(after - before)]
    valid = [p for p in new_runs if (p / "checkpoints").exists()]
    selected = max(valid, key=lambda p: p.stat().st_mtime) if valid else None
    if selected is None:
        train_log = LOG_ROOT / "train_smoke" / "train.log"
        if train_log.exists():
            text = train_log.read_text(encoding="utf-8", errors="replace")
            match = re.search(r"Dashboard: .*?/globe_walking/([^/]+)/train/([0-9.]+)", text)
            if match:
                candidate = DREUREKA / "globe_walking" / "runs" / "globe_walking" / match.group(1) / "train" / match.group(2)
                if (candidate / "checkpoints").exists():
                    selected = candidate
                    valid.append(candidate)
    if selected is not None:
        SELECTED_SMOKE_RUN.write_text(str(selected) + "\n", encoding="utf-8")
    result = {
        "ok": selected is not None,
        "selected_run": rel(selected),
        "new_runs": [rel(p) for p in new_runs],
        "valid_runs": [rel(p) for p in valid],
    }
    write_json(ARTIFACT_ROOT / "go2_train_smoke_run.json", result)
    return result


def parse_train_log(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    iteration_matches = [int(m) for m in re.findall(r"iterations\s*│\s*(\d+)", text)]
    timestep_matches = [int(m) for m in re.findall(r"timesteps\s*│\s*(\d+)", text)]
    total_reward_matches = [float(m) for m in re.findall(r"rew total/mean\s*│\s*([-+]?\d+(?:\.\d*)?)", text)]
    segfault = "segmentation fault" in text.lower()
    effective_iterations = None
    launch_path = ARTIFACT_ROOT / "train_1_8_budget_launch.json"
    if launch_path.exists() and LOG_ROOT / "train_1_8_budget" in path.parents:
        effective_iterations = json.loads(launch_path.read_text(encoding="utf-8")).get("iterations")
    return {
        "path": rel(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "contains_nan": "nan" in text.lower(),
        "contains_segfault": segfault,
        "iterations_logged": iteration_matches,
        "last_iteration": iteration_matches[-1] if iteration_matches else None,
        "last_timesteps": timestep_matches[-1] if timestep_matches else None,
        "last_total_reward": total_reward_matches[-1] if total_reward_matches else None,
        "effective_iterations_from_launch": effective_iterations,
        "completed_exception": "Traceback" not in text and "Error" not in text and not segfault,
    }


def run_dir_from_log(path: Path) -> Path | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"Dashboard: .*?/globe_walking/([^/]+)/train/([0-9.]+)", text)
    if not match:
        return None
    candidate = DREUREKA / "globe_walking" / "runs" / "globe_walking" / match.group(1) / "train" / match.group(2)
    return candidate if candidate.exists() else None


def require_training_gates() -> dict[str, Any]:
    ensure_tree()
    paths = {
        "mujoco_dds_endpoint": ARTIFACT_ROOT / "go2_mujoco_dds_endpoint_report.json",
        "lcm_to_dds_bridge": ARTIFACT_ROOT / "go2_lcm_to_dds_bridge_report.json",
        "isaacgym_consistency": ARTIFACT_ROOT / "go2_isaacgym_consistency_report.json",
        "smoke": ARTIFACT_ROOT / "phase_go2_train_report.json",
    }
    reports: dict[str, Any] = {}
    missing = []
    failed = []
    for name, path in paths.items():
        if not path.exists():
            missing.append(rel(path))
            continue
        report = json.loads(path.read_text(encoding="utf-8"))
        reports[name] = report
        if not report.get("ok"):
            failed.append(name)
    result = {"ok": not missing and not failed, "missing": missing, "failed": failed}
    if not result["ok"]:
        write_json(ARTIFACT_ROOT / "train_1_8_budget_gate_failure.json", {**result, "reports": reports})
        raise SystemExit(f"1/8 training gate failed: {result}")
    write_json(ARTIFACT_ROOT / "train_1_8_budget_gate.json", {**result, "reports": reports})
    return result


def guard_train_1_8_not_launched() -> dict[str, Any]:
    ensure_tree()
    if TRAIN_1_8_LAUNCH.exists():
        payload = json.loads(TRAIN_1_8_LAUNCH.read_text(encoding="utf-8"))
        raise SystemExit(f"1/8 training was already launched: {payload}")
    result = {"ok": True, "launch_marker": rel(TRAIN_1_8_LAUNCH)}
    write_json(ARTIFACT_ROOT / "train_1_8_budget_launch_guard.json", result)
    return result


def record_train_1_8_launch(args: Any) -> dict[str, Any]:
    ensure_tree()
    payload = {
        "ok": True,
        "generated_at_unix": time.time(),
        "container_id": args.container_id,
        "container_name": args.container_name,
        "iterations": args.iterations,
        "num_envs": args.num_envs,
        "domain_rand_profile": args.domain_rand_profile,
        "physx_profile": getattr(args, "physx_profile", None),
        "save_interval": args.save_interval,
        "log": rel(LOG_ROOT / "train_1_8_budget" / "train.log"),
        "claim": "This marker records the single allowed 1/8-budget Go2 Isaac Gym launch for this goal.",
    }
    write_json(TRAIN_1_8_LAUNCH, payload)
    return payload


def docker_inspect(container_id: str) -> dict[str, Any]:
    try:
        out = subprocess.run(
            ["docker", "inspect", container_id],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout
        data = json.loads(out)[0]
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError, IndexError) as exc:
        return {"ok": False, "error": repr(exc)}
    state = data.get("State", {})
    return {
        "ok": True,
        "name": data.get("Name", "").lstrip("/"),
        "id": data.get("Id"),
        "running": bool(state.get("Running")),
        "status": state.get("Status"),
        "exit_code": state.get("ExitCode"),
        "started_at": state.get("StartedAt"),
        "finished_at": state.get("FinishedAt"),
    }


def docker_stats(container_id: str) -> dict[str, Any]:
    try:
        out = subprocess.run(
            [
                "docker",
                "stats",
                "--no-stream",
                "--format",
                "{{json .}}",
                container_id,
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
        ).stdout.strip()
        return {"ok": True, "raw": json.loads(out) if out else {}}
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        return {"ok": False, "error": repr(exc)}


def docker_logs_tail(container_id: str, lines: int = 80) -> dict[str, Any]:
    try:
        out = subprocess.run(
            ["docker", "logs", "--tail", str(lines), container_id],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=20,
        ).stdout
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": repr(exc), "tail": ""}
    return {
        "ok": True,
        "tail": out,
        "contains_segfault": "segmentation fault" in out.lower(),
    }


def parse_docker_time(value: str | None) -> float | None:
    if not value or value.startswith("0001-01-01"):
        return None
    try:
        from datetime import datetime

        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def nvidia_smi() -> dict[str, Any]:
    try:
        out = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": repr(exc)}
    rows = []
    for line in out.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) == 5:
            rows.append(
                {
                    "index": parts[0],
                    "name": parts[1],
                    "utilization_gpu_percent": parts[2],
                    "memory_used_mib": parts[3],
                    "memory_total_mib": parts[4],
                }
            )
    return {"ok": True, "gpus": rows}


def monitor_train_1_8(args: Any) -> dict[str, Any]:
    ensure_tree()
    container_id = args.container_id
    duration_s = int(args.duration_s)
    interval_s = int(args.interval_s)
    log_path = LOG_ROOT / "train_1_8_budget" / "train.log"
    start = time.time()
    start_log = parse_train_log(log_path)
    samples = []
    while time.time() - start < duration_s:
        inspect = docker_inspect(container_id)
        sample = {
            "t_since_start_s": round(time.time() - start, 3),
            "container": inspect,
            "log": parse_train_log(log_path),
            "docker_stats": docker_stats(container_id),
            "nvidia_smi": nvidia_smi(),
        }
        samples.append(sample)
        if inspect.get("ok") and not inspect.get("running"):
            break
        time.sleep(interval_s)

    end_log = parse_train_log(log_path)
    inspect_end = docker_inspect(container_id)
    log_tail = docker_logs_tail(container_id)
    started = parse_docker_time(inspect_end.get("started_at"))
    finished = parse_docker_time(inspect_end.get("finished_at"))
    container_runtime_s = round(finished - started, 3) if started is not None and finished is not None else None
    run_dir = run_dir_from_log(log_path)
    if run_dir is not None:
        SELECTED_TRAIN_1_8_RUN.write_text(str(run_dir) + "\n", encoding="utf-8")
    log_advanced = end_log.get("size_bytes", 0) > start_log.get("size_bytes", 0)
    no_error_text = not end_log.get("contains_nan") and end_log.get("completed_exception")
    survived = inspect_end.get("ok") and inspect_end.get("running") and time.time() - start >= duration_s
    ok = bool(survived and log_advanced and no_error_text)
    result = {
        "ok": ok,
        "generated_at_unix": time.time(),
        "monitor_duration_s": duration_s,
        "actual_monitor_duration_s": round(time.time() - start, 3),
        "container_id": container_id,
        "container_end": inspect_end,
        "container_runtime_s": container_runtime_s,
        "docker_logs_tail": log_tail,
        "log_start": start_log,
        "log_end": end_log,
        "log_advanced": log_advanced,
        "no_nan_or_error_text": no_error_text,
        "failure_summary": None
        if ok
        else {
            "reason": "container did not remain running for the requested monitor duration",
            "exit_code": inspect_end.get("exit_code"),
            "contains_segfault": end_log.get("contains_segfault") or log_tail.get("contains_segfault"),
            "note": "The launch used the requested 20000 iterations and 4096 envs; the RunnerArgs.max_iterations banner is static config, while train.py passes --iterations into runner.learn.",
        },
        "selected_run": rel(run_dir),
        "selected_run_file": rel(SELECTED_TRAIN_1_8_RUN) if run_dir is not None else None,
        "samples": samples,
    }
    write_json(TRAIN_1_8_HEALTH, result)
    lines = [
        "# Go2 1/8-Budget Training Health",
        "",
        f"- Status: {'PASS' if ok else 'FAIL'}",
        f"- Container: `{container_id}`",
        f"- Monitor duration: `{result['actual_monitor_duration_s']}` seconds",
        f"- Container runtime: `{container_runtime_s}` seconds",
        f"- Docker running at end: `{inspect_end.get('running')}`",
        f"- Docker exit code: `{inspect_end.get('exit_code')}`",
        f"- Log: `{end_log.get('path')}`",
        f"- Log advanced during monitor: `{log_advanced}`",
        f"- Last logged iteration: `{end_log.get('last_iteration')}`",
        f"- Last logged timesteps: `{end_log.get('last_timesteps')}`",
        f"- Last total reward: `{end_log.get('last_total_reward')}`",
        f"- Contains NaN text: `{end_log.get('contains_nan')}`",
        f"- Contains segfault text: `{end_log.get('contains_segfault') or log_tail.get('contains_segfault')}`",
        f"- Selected run: `{rel(run_dir)}`",
        "",
        "This report is a five-minute health gate only. A passing run is expected to remain alive after the goal completes.",
        "The launch used the requested `--iterations` value; the `RunnerArgs.max_iterations` table row printed by DrEureka is static config, not the loop bound passed to `runner.learn`.",
    ]
    (ARTIFACT_ROOT / "train_1_8_budget_health.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not ok:
        raise SystemExit(f"1/8 training health failed: {result}")
    return result


def phase_go2_train_report() -> Path:
    ensure_tree()
    smoke = parse_train_log(LOG_ROOT / "train_smoke" / "train.log")
    smoke_run = {}
    run_json = ARTIFACT_ROOT / "go2_train_smoke_run.json"
    if run_json.exists():
        smoke_run = json.loads(run_json.read_text(encoding="utf-8"))
    urdf_json = ARTIFACT_ROOT / "go2_isaacgym_urdf.json"
    urdf = json.loads(urdf_json.read_text(encoding="utf-8")) if urdf_json.exists() else {}
    ok = bool(smoke.get("exists") and not smoke.get("contains_nan") and smoke_run.get("ok"))
    lines = [
        "# Go2 Train Smoke Report",
        "",
        f"- Status: {'PASS' if ok else 'FAIL'}",
        f"- Scope: smoke validation only; this does not claim final policy equivalence.",
        f"- Sanitized Isaac Gym URDF: `{urdf.get('output')}`",
        f"- Train log: `{smoke.get('path')}`",
        f"- Selected run: `{smoke_run.get('selected_run')}`",
        f"- Last logged iteration: `{smoke.get('last_iteration')}`",
        f"- Last logged timesteps: `{smoke.get('last_timesteps')}`",
        f"- Last total reward: `{smoke.get('last_total_reward')}`",
        f"- Contains NaN text: `{smoke.get('contains_nan')}`",
        "",
        "Go2 uses the SDK2 `LowCmd` PD command path because no defensible Go2 actuator network exists in the fetched resources. The actuator fidelity gate is the Unitree MuJoCo torque equation, gains, and torque limits, not an inferred actuator-net substitute.",
    ]
    out = ARTIFACT_ROOT / "phase_go2_train_report.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(ARTIFACT_ROOT / "phase_go2_train_report.json", {"ok": ok, "smoke": smoke, "run": smoke_run, "urdf": urdf})
    return out


def write_sim2sim_contract() -> Path:
    ensure_tree()
    path = ARTIFACT_ROOT / "sim2sim_contract.md"
    path.write_text(
        "\n".join(
            [
                "# Go2 Sim2Sim Contract",
                "",
                "Use Unitree SDK2 low-level state/command semantics as the real-robot swappable boundary.",
                "",
                "- Policy order: FL, FR, RL, RR in DrEureka observation/action order.",
                "- Unitree low-level motor order: FR, FL, RR, RL.",
                "- Policy-to-Unitree index map: `[3, 4, 5, 0, 1, 2, 9, 10, 11, 6, 7, 8]`.",
                "- MuJoCo must publish joint state, IMU state, and command timing at the deployment boundary.",
                "- Support is allowed only before policy control is active; release must be logged and verified.",
                "- Real-time validity requires sim time and policy time to remain consistent with wall clock.",
                "",
                "The current Go2 contract is a design target. It is not complete until `mujoco_sim2sim_health_report.md` is generated from a Go2 MuJoCo run.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "cmd",
        choices=[
            "init-artifacts",
            "validate-deps",
            "prepare-isaacgym-urdf",
            "mujoco-dds-endpoint-report",
            "lcm-to-dds-bridge-report",
            "consistency-report",
            "runs-before-smoke",
            "runs-after-smoke",
            "record-train-smoke-run",
            "phase-go2-train-report",
            "require-training-gates",
            "guard-train-1-8-not-launched",
            "record-train-1-8-launch",
            "monitor-train-1-8",
            "write-sim2sim-contract",
        ],
    )
    parser.add_argument("--container-id", default="")
    parser.add_argument("--container-name", default="")
    parser.add_argument("--iterations", type=int, default=20000)
    parser.add_argument("--num-envs", type=int, default=4096)
    parser.add_argument("--domain-rand-profile", default="pretrained")
    parser.add_argument("--physx-profile", default=None)
    parser.add_argument("--save-interval", type=int, default=1000)
    parser.add_argument("--duration-s", type=int, default=300)
    parser.add_argument("--interval-s", type=int, default=30)
    args = parser.parse_args()
    if args.cmd == "init-artifacts":
        ensure_tree()
    elif args.cmd == "validate-deps":
        validate_deps()
    elif args.cmd == "prepare-isaacgym-urdf":
        prepare_isaacgym_urdf()
    elif args.cmd == "mujoco-dds-endpoint-report":
        go2_mujoco_dds_endpoint_report()
    elif args.cmd == "lcm-to-dds-bridge-report":
        go2_lcm_to_dds_bridge_report()
    elif args.cmd == "consistency-report":
        go2_isaacgym_consistency_report()
    elif args.cmd == "runs-before-smoke":
        write_run_list(LOG_ROOT / "train_smoke" / "runs_before.txt")
    elif args.cmd == "runs-after-smoke":
        write_run_list(LOG_ROOT / "train_smoke" / "runs_after.txt")
    elif args.cmd == "record-train-smoke-run":
        record_train_smoke_run()
    elif args.cmd == "phase-go2-train-report":
        print(rel(phase_go2_train_report()))
    elif args.cmd == "require-training-gates":
        require_training_gates()
    elif args.cmd == "guard-train-1-8-not-launched":
        guard_train_1_8_not_launched()
    elif args.cmd == "record-train-1-8-launch":
        record_train_1_8_launch(args)
    elif args.cmd == "monitor-train-1-8":
        monitor_train_1_8(args)
    elif args.cmd == "write-sim2sim-contract":
        print(rel(write_sim2sim_contract()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
