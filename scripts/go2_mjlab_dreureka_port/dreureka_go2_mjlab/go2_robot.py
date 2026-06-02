"""Vendored Unitree Go2 robot data for the DrEureka MJLab caller task."""

from __future__ import annotations

from pathlib import Path

import mujoco

from mjlab.actuator import BuiltinPositionActuatorCfg
from mjlab.entity import EntityArticulationInfoCfg, EntityCfg
from mjlab.utils.spec_config import CollisionCfg

GO2_XML = Path(__file__).parent / "assets" / "unitree_go2" / "xmls" / "go2.xml"
GO2_SCENE_XML = Path(__file__).parent / "assets" / "unitree_go2" / "xmls" / "scene_go2.xml"

_FOOT_REGEX = "^[FR][LR]_foot_collision$"

FULL_COLLISION = CollisionCfg(
  geom_names_expr=(".*_collision",),
  condim={_FOOT_REGEX: 3, ".*_collision": 1},
  priority={_FOOT_REGEX: 1},
  friction={_FOOT_REGEX: (0.6,)},
  solimp={_FOOT_REGEX: (0.9, 0.95, 0.023)},
  contype=1,
  conaffinity=0,
)


def _load_assets(asset_dir: Path, meshdir: str | None) -> dict[str, bytes]:
  assets: dict[str, bytes] = {}
  for path in asset_dir.iterdir():
    if path.is_file():
      key = f"{meshdir}/{path.name}" if meshdir else path.name
      assets[key] = path.read_bytes()
  return assets


def get_go2_spec() -> mujoco.MjSpec:
  spec = mujoco.MjSpec.from_file(str(GO2_XML))
  spec.assets = _load_assets(GO2_XML.parent / "assets", spec.meshdir)
  return spec


def get_go2_robot_cfg() -> EntityCfg:
  return EntityCfg(
    init_state=EntityCfg.InitialStateCfg(
      pos=(0.0, 0.0, 0.32),
      joint_pos={
        ".*thigh_joint": 0.9,
        ".*calf_joint": -1.8,
        ".*R_hip_joint": 0.1,
        ".*L_hip_joint": -0.1,
      },
      joint_vel={".*": 0.0},
    ),
    collisions=(FULL_COLLISION,),
    spec_fn=get_go2_spec,
    articulation=EntityArticulationInfoCfg(
      actuators=(
        BuiltinPositionActuatorCfg(
          target_names_expr=(".*hip_.*",),
          stiffness=20.0,
          damping=1.0,
          effort_limit=23.5,
          armature=0.01,
        ),
        BuiltinPositionActuatorCfg(
          target_names_expr=(".*thigh_.*",),
          stiffness=20.0,
          damping=1.0,
          effort_limit=23.5,
          armature=0.01,
        ),
        BuiltinPositionActuatorCfg(
          target_names_expr=(".*calf_.*",),
          stiffness=40.0,
          damping=2.0,
          effort_limit=45,
          armature=0.02,
        ),
      ),
      soft_joint_pos_limit_factor=0.9,
    ),
  )
