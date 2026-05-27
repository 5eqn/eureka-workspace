#!/usr/bin/env python3
"""Generate the Go2 asset inventory for the migration goal."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
THIRDPARTIES = ROOT / "thirdparties"
ARTIFACT_ROOT = ROOT / "artifacts" / "go2_yoga_ball"

SOURCES = {
    "unitree_mujoco": {
        "path": THIRDPARTIES / "unitree_mujoco",
        "authoritative_for": ["mujoco_sim2sim_real_swap_contract"],
        "model": "unitree_robots/go2/go2.xml",
        "scene": "unitree_robots/go2/scene.xml",
        "license": "LICENSE",
    },
    "go2_description": {
        "path": THIRDPARTIES / "go2_description",
        "authoritative_for": ["isaac_gym_urdf_import_source"],
        "model": "urdf/go2_description.urdf",
        "license": "LICENSE",
    },
    "unitree_rl_mjlab": {
        "path": THIRDPARTIES / "unitree_rl_mjlab",
        "authoritative_for": ["mjlab_go2_asset_and_pd_reference"],
        "model": "src/assets/robots/unitree_go2/xmls/go2.xml",
        "scene": "src/assets/robots/unitree_go2/xmls/scene_go2.xml",
        "constants": "src/assets/robots/unitree_go2/go2_constants.py",
        "license": None,
    },
    "mujoco_menagerie": {
        "path": THIRDPARTIES / "mujoco_menagerie",
        "authoritative_for": ["secondary_mjcf_cross_check"],
        "model": "unitree_go2/go2.xml",
        "scene": "unitree_go2/scene.xml",
        "license": "LICENSE",
    },
}

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


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def run_git(path: Path, *args: str) -> str | None:
    if not path.exists():
        return None
    try:
        return subprocess.run(
            ["git", "-C", str(path), *args],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def text_preview(path: Path | None, limit: int = 240) -> str | None:
    if path is None or not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    return re.sub(r"\s+", " ", text).strip()[:limit]


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


def parse_mjcf(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    joint_defaults = default_attrs(root, "joint")
    motor_defaults = default_attrs(root, "motor")
    compiler = root.find("compiler")
    joints = []
    for joint in root.findall(".//joint"):
        name = joint.attrib.get("name")
        if not name:
            continue
        attrs = dict(joint_defaults.get(joint.attrib.get("class", ""), {}))
        attrs.update(joint.attrib)
        joints.append(
            {
                "name": name,
                "class": joint.attrib.get("class"),
                "axis": floats(attrs.get("axis")),
                "range": floats(attrs.get("range")),
                "damping": float(attrs["damping"]) if "damping" in attrs else None,
                "armature": float(attrs["armature"]) if "armature" in attrs else None,
                "frictionloss": float(attrs["frictionloss"]) if "frictionloss" in attrs else None,
            }
        )
    actuators = []
    for motor in root.findall(".//actuator/motor"):
        attrs = dict(motor_defaults.get(motor.attrib.get("class", ""), {}))
        attrs.update(motor.attrib)
        actuators.append(
            {
                "name": motor.attrib.get("name"),
                "joint": motor.attrib.get("joint"),
                "class": motor.attrib.get("class"),
                "ctrlrange": floats(attrs.get("ctrlrange")),
            }
        )
    bodies = []
    for body in root.findall(".//body"):
        inertial = body.find("inertial")
        if inertial is not None:
            bodies.append(
                {
                    "name": body.attrib.get("name"),
                    "mass": float(inertial.attrib["mass"]) if "mass" in inertial.attrib else None,
                    "inertia": floats(inertial.attrib.get("diaginertia")),
                }
            )
    return {
        "path": rel(path),
        "sha256": sha256(path),
        "compiler_meshdir": compiler.attrib.get("meshdir") if compiler is not None else None,
        "mesh_files": sorted(
            mesh.attrib["file"] for mesh in root.findall(".//asset/mesh") if "file" in mesh.attrib
        ),
        "joints": joints,
        "actuators": actuators,
        "bodies_with_inertia": bodies,
        "keyframes": [
            {
                "name": key.attrib.get("name"),
                "qpos": floats(key.attrib.get("qpos")),
                "ctrl": floats(key.attrib.get("ctrl")),
            }
            for key in root.findall(".//key")
        ],
    }


def parse_urdf(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    joints = []
    for joint in root.findall("joint"):
        limit = joint.find("limit")
        axis = joint.find("axis")
        joints.append(
            {
                "name": joint.attrib.get("name"),
                "type": joint.attrib.get("type"),
                "axis": floats(axis.attrib.get("xyz")) if axis is not None else None,
                "lower": float(limit.attrib["lower"]) if limit is not None and "lower" in limit.attrib else None,
                "upper": float(limit.attrib["upper"]) if limit is not None and "upper" in limit.attrib else None,
                "effort": float(limit.attrib["effort"]) if limit is not None and "effort" in limit.attrib else None,
                "velocity": float(limit.attrib["velocity"]) if limit is not None and "velocity" in limit.attrib else None,
            }
        )
    links = []
    for link in root.findall("link"):
        inertial = link.find("inertial")
        if inertial is None:
            continue
        mass = inertial.find("mass")
        inertia = inertial.find("inertia")
        links.append(
            {
                "name": link.attrib.get("name"),
                "mass": float(mass.attrib["value"]) if mass is not None and "value" in mass.attrib else None,
                "inertia": dict(inertia.attrib) if inertia is not None else None,
            }
        )
    return {
        "path": rel(path),
        "sha256": sha256(path),
        "joints": joints,
        "links_with_inertia": links,
        "mesh_files": sorted(
            mesh.attrib["filename"] for mesh in root.findall(".//mesh") if "filename" in mesh.attrib
        ),
    }


def parse_mjlab_constants(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    return {
        "path": rel(path),
        "sha256": sha256(path),
        "init_state_excerpt": re.findall(r"INIT_STATE = .*?\n\)", text, flags=re.S)[:1],
        "actuator_excerpts": re.findall(r"GO2_ACTUATOR_[A-Z]+ = .*?\n\)", text, flags=re.S),
        "collision_excerpts": re.findall(r"(?:FEET_ONLY_COLLISION|FULL_COLLISION) = .*?\n\)", text, flags=re.S),
    }


def source_entry(name: str, cfg: dict[str, Any]) -> dict[str, Any]:
    path = cfg["path"]
    license_rel = cfg.get("license")
    license_path = path / license_rel if license_rel else None
    model_rel = cfg.get("model")
    scene_rel = cfg.get("scene")
    constants_rel = cfg.get("constants")
    return {
        "name": name,
        "path": rel(path),
        "exists": path.exists(),
        "remote": run_git(path, "remote", "get-url", "origin"),
        "commit": run_git(path, "rev-parse", "HEAD"),
        "authoritative_for": cfg["authoritative_for"],
        "license_path": rel(license_path) if license_path else None,
        "license_exists": license_path.exists() if license_path else False,
        "license_preview": text_preview(license_path),
        "model_path": rel(path / model_rel) if model_rel else None,
        "model_sha256": sha256(path / model_rel) if model_rel else None,
        "scene_path": rel(path / scene_rel) if scene_rel else None,
        "scene_sha256": sha256(path / scene_rel) if scene_rel else None,
        "constants_path": rel(path / constants_rel) if constants_rel else None,
        "constants_sha256": sha256(path / constants_rel) if constants_rel else None,
    }


def main() -> int:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    unitree_mujoco_xml = THIRDPARTIES / "unitree_mujoco" / "unitree_robots" / "go2" / "go2.xml"
    urdf = THIRDPARTIES / "go2_description" / "urdf" / "go2_description.urdf"
    mjlab_xml = THIRDPARTIES / "unitree_rl_mjlab" / "src" / "assets" / "robots" / "unitree_go2" / "xmls" / "go2.xml"
    mjlab_constants = THIRDPARTIES / "unitree_rl_mjlab" / "src" / "assets" / "robots" / "unitree_go2" / "go2_constants.py"
    menagerie_xml = THIRDPARTIES / "mujoco_menagerie" / "unitree_go2" / "go2.xml"

    inventory = {
        "generated_at_unix": time.time(),
        "goal": "Go2 yoga-ball Sim2Real migration asset inventory",
        "sources": {name: source_entry(name, cfg) for name, cfg in SOURCES.items()},
        "selected_authoritative_sources": {
            "mujoco_sim2sim": "unitree_mujoco",
            "isaac_gym_urdf_import": "go2_description",
            "mjlab_reference": "unitree_rl_mjlab",
            "secondary_cross_check": "mujoco_menagerie",
        },
        "joint_orders": {
            "dr_eureka_policy_order": POLICY_JOINT_ORDER,
            "unitree_low_level_motor_order": UNITREE_MOTOR_ORDER,
            "policy_to_unitree_low_level_indices": [POLICY_JOINT_ORDER.index(name) for name in UNITREE_MOTOR_ORDER],
        },
        "unitree_mujoco_go2": parse_mjcf(unitree_mujoco_xml),
        "go2_description_urdf": parse_urdf(urdf),
        "unitree_rl_mjlab_go2": {
            "mjcf": parse_mjcf(mjlab_xml),
            "constants": parse_mjlab_constants(mjlab_constants),
        },
        "mujoco_menagerie_go2": parse_mjcf(menagerie_xml),
        "actuator_policy": {
            "go2_actuator_network": None,
            "fallback": "PD/BuiltinPositionActuator reference from unitree_rl_mjlab until a Go2 actuator network is obtained or trained.",
            "not_actuator_equivalent_until_validated": True,
        },
    }
    out = ARTIFACT_ROOT / "go2_asset_inventory.json"
    out.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {rel(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
