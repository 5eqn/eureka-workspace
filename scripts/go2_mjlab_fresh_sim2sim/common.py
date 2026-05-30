"""Shared constants for FRESH Go2 MJLab Sim2Sim."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = ROOT / "scripts" / "go2_mjlab_fresh_sim2sim"
ARTIFACT_ROOT = ROOT / "artifacts" / "go2_mjlab_fresh_sim2sim"
LOG_ROOT = ROOT / "logs" / "go2_mjlab_fresh_sim2sim"
MJLAB_PORT = ROOT / "scripts" / "go2_mjlab_dreureka_port"
CHECKPOINT = ROOT / "logs" / "go2_mjlab_dreureka_port" / "train_1_8_budget" / "rsl_rl" / "model_19999.pt"
RUN_LOG_DIR = ROOT / "logs" / "go2_mjlab_dreureka_port" / "train_1_8_budget" / "rsl_rl"

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

MJLAB_CONTRACT_ORDER = [
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

DEFAULT_JOINT_ANGLES = {
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

KP_BY_JOINT = {
  "hip": 20.0,
  "thigh": 20.0,
  "calf": 40.0,
}
KD_BY_JOINT = {
  "hip": 1.0,
  "thigh": 1.0,
  "calf": 2.0,
}
ACTION_SCALE = 0.25


def joint_pd(name: str) -> tuple[float, float]:
  for key in ("hip", "thigh", "calf"):
    if key in name:
      return KP_BY_JOINT[key], KD_BY_JOINT[key]
  raise ValueError(f"unknown Go2 joint type in {name}")
