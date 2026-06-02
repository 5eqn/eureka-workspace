#!/usr/bin/env python3
"""Direct MJLab checkpoint to Unitree SDK2 DDS deployer."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import json
import math
from pathlib import Path
import select
import sys
import time
from typing import Any

import torch
from tensordict import TensorDict

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "go2_mjlab_dreureka_port"))

import src.tasks  # noqa: F401,E402
import dreureka_go2_mjlab  # noqa: F401,E402
from dreureka_go2_mjlab.env_cfg import TASK_ID  # noqa: E402
from mjlab.envs import ManagerBasedRlEnv  # noqa: E402
from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper  # noqa: E402
from mjlab.tasks.registry import load_env_cfg, load_rl_cfg  # noqa: E402
from mjlab.utils.torch import configure_torch_backends  # noqa: E402
from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelPublisher, ChannelSubscriber  # noqa: E402
from unitree_sdk2py.idl.default import unitree_go_msg_dds__LowCmd_  # noqa: E402
from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowCmd_, LowState_  # noqa: E402
from unitree_sdk2py.utils.crc import CRC  # noqa: E402

from common import ACTION_SCALE, DEFAULT_JOINT_ANGLES, MJLAB_CONTRACT_ORDER, UNITREE_MOTOR_ORDER, joint_pd  # noqa: E402


def quat_to_rpy(q: list[float]) -> tuple[float, float, float]:
  w, x, y, z = q
  roll = math.atan2(2.0 * (w * x + y * z), 1.0 - 2.0 * (x * x + y * y))
  pitch = math.asin(max(-1.0, min(1.0, 2.0 * (w * y - z * x))))
  yaw = math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))
  return roll, pitch, yaw


def projected_gravity_from_quat(q: list[float]) -> list[float]:
  w, x, y, z = q
  # Body-frame gravity direction R^T * [0, 0, -1].
  return [
    2.0 * (w * y - x * z),
    -2.0 * (y * z + w * x),
    2.0 * (x * x + y * y) - 1.0,
  ]


def load_seed_state(path: str | None) -> dict[str, Any]:
  if not path:
    return {}
  with Path(path).open(encoding="utf-8") as f:
    return json.load(f)


class LowStateBuffer:
  def __init__(self) -> None:
    self.msg: LowState_ | None = None
    self.count = 0
    self.first_monotonic: float | None = None
    self.last_monotonic: float | None = None

  def callback(self, msg: LowState_) -> None:
    self.msg = msg
    self.count += 1
    self.last_monotonic = time.monotonic()
    if self.first_monotonic is None:
      self.first_monotonic = self.last_monotonic


class ObservationBuilder:
  def __init__(self, device: str, clip_actions: float | None) -> None:
    self.device = device
    self.clip_actions = clip_actions
    self.action = torch.zeros((1, 12), device=device)
    self.prev_action = torch.zeros((1, 12), device=device)
    self.history: dict[str, list[torch.Tensor]] = {}
    self.unitree_to_mjlab = [UNITREE_MOTOR_ORDER.index(name) for name in MJLAB_CONTRACT_ORDER]

  def _single_terms(self, msg: LowState_ | None) -> dict[str, torch.Tensor]:
    if msg is None:
      quat = [1.0, 0.0, 0.0, 0.0]
      q_unitree = [DEFAULT_JOINT_ANGLES[name] for name in UNITREE_MOTOR_ORDER]
      dq_unitree = [0.0] * 12
    else:
      quat = [float(v) for v in msg.imu_state.quaternion]
      if not any(abs(v) > 1e-9 for v in quat):
        quat = [1.0, 0.0, 0.0, 0.0]
      q_unitree = [float(msg.motor_state[i].q) for i in range(12)]
      dq_unitree = [float(msg.motor_state[i].dq) for i in range(12)]
    q = [q_unitree[i] for i in self.unitree_to_mjlab]
    dq = [dq_unitree[i] for i in self.unitree_to_mjlab]
    joint_pos_rel = [q[i] - DEFAULT_JOINT_ANGLES[MJLAB_CONTRACT_ORDER[i]] for i in range(12)]
    joint_vel_rel = [v * 0.05 for v in dq]
    _, _, yaw = quat_to_rpy(quat)
    clock = [0.0, 0.0, 0.0, 0.0]
    return {
      "orientation": torch.tensor(projected_gravity_from_quat(quat), dtype=torch.float32, device=self.device).unsqueeze(0),
      "joint_pos": torch.tensor(joint_pos_rel, dtype=torch.float32, device=self.device).unsqueeze(0),
      "joint_vel": torch.tensor(joint_vel_rel, dtype=torch.float32, device=self.device).unsqueeze(0),
      "action": self.action.clone(),
      "last_action": self.prev_action.clone(),
      "clock": torch.tensor(clock, dtype=torch.float32, device=self.device).unsqueeze(0),
      "yaw": torch.tensor([yaw], dtype=torch.float32, device=self.device).unsqueeze(0),
    }

  def actor_obs(self, msg: LowState_ | None) -> torch.Tensor:
    terms = self._single_terms(msg)
    if not self.history:
      self.history = {name: [value.clone() for _ in range(15)] for name, value in terms.items()}
    else:
      for name, value in terms.items():
        self.history[name] = self.history[name][1:] + [value]
    # MJLab ObservationManager uses term-major flattened history:
    # [orientation_t0..t14, joint_pos_t0..t14, ...].
    return torch.cat(
      [
        torch.cat(self.history[name], dim=1)
        for name in ["orientation", "joint_pos", "joint_vel", "action", "last_action", "clock", "yaw"]
      ],
      dim=1,
    )

  def clip_action(self, action: torch.Tensor) -> torch.Tensor:
    if self.clip_actions is None:
      return action
    return torch.clamp(action, -self.clip_actions, self.clip_actions)

  def update_action(self, action: torch.Tensor) -> None:
    self.prev_action[:] = self.action
    self.action[:] = self.clip_action(action)


def load_policy(checkpoint: Path, log_dir: Path, device: str) -> tuple[Any, list[str], list[str]]:
  configure_torch_backends()
  cfg = load_env_cfg(TASK_ID, play=True)
  rl = load_rl_cfg(TASK_ID)
  cfg.scene.num_envs = 1
  env = ManagerBasedRlEnv(cfg=cfg, device=device)
  wrapped = RslRlVecEnvWrapper(env, clip_actions=rl.clip_actions)
  runner = MjlabOnPolicyRunner(wrapped, asdict(rl), str(log_dir), device)
  runner.load(str(checkpoint), load_cfg={"actor": True}, strict=True, map_location=device)
  policy = runner.get_inference_policy(device=device)
  action_term = env.action_manager.get_term("joint_pos")
  action_order = list(action_term.target_names)
  obs_terms = list(env.observation_manager.active_terms["actor"])
  env.close()
  return policy, action_order, obs_terms


def init_lowcmd() -> Any:
  cmd = unitree_go_msg_dds__LowCmd_()
  cmd.head[0] = 0xFE
  cmd.head[1] = 0xEF
  cmd.level_flag = 0xFF
  cmd.gpio = 0
  for i in range(20):
    motor = cmd.motor_cmd[i]
    motor.mode = 0x01
    motor.q = 2.146e9
    motor.dq = 16000.0
    motor.kp = 0.0
    motor.kd = 0.0
    motor.tau = 0.0
  return cmd


def write_lowcmd(cmd: Any, action_mjlab: torch.Tensor, action_order: list[str], crc: CRC, motor_offset_by_name: dict[str, float]) -> list[float]:
  action_by_name = {name: float(action_mjlab[0, i].item()) for i, name in enumerate(action_order)}
  q_des = []
  for i, name in enumerate(UNITREE_MOTOR_ORDER):
    motor = cmd.motor_cmd[i]
    q = DEFAULT_JOINT_ANGLES[name] + motor_offset_by_name.get(name, 0.0) + ACTION_SCALE * action_by_name[name]
    motor.mode = 0x01
    motor.q = float(q)
    motor.dq = 0.0
    motor.kp, motor.kd = joint_pd(name)
    motor.tau = 0.0
    q_des.append(float(q))
  cmd.crc = crc.Crc(cmd)
  return q_des


def run(args: argparse.Namespace) -> int:
  out_dir = Path(args.out_dir)
  out_dir.mkdir(parents=True, exist_ok=True)
  device = args.device or ("cuda:0" if torch.cuda.is_available() else "cpu")
  policy, action_order, obs_terms = load_policy(Path(args.checkpoint), Path(args.log_dir), device)
  rl = load_rl_cfg(TASK_ID)
  builder = ObservationBuilder(device, rl.clip_actions)
  seed_state = load_seed_state(args.seed_state)
  offset_values = seed_state.get("robot_motor_offset_mjlab_order", [0.0] * 12)
  motor_offset_by_name = {
    name: float(offset_values[i])
    for i, name in enumerate(MJLAB_CONTRACT_ORDER)
  }

  if args.smoke_only:
    obs = builder.actor_obs(None)
    with torch.no_grad():
      action = policy(TensorDict({"actor": obs}, batch_size=[1]), stochastic_output=False)
    action = builder.clip_action(action)
    q_des = [
      DEFAULT_JOINT_ANGLES[name]
      + motor_offset_by_name.get(name, 0.0)
      + ACTION_SCALE * float(action[0, action_order.index(name)].item())
      for name in UNITREE_MOTOR_ORDER
    ]
    result = {
      "ok": bool(torch.isfinite(action).all().item() and obs.shape == (1, 840)),
      "checkpoint": str(args.checkpoint),
      "device": device,
      "actor_obs_shape": list(obs.shape),
      "action_shape": list(action.shape),
      "action_abs_max": float(action.abs().max().item()),
      "action_order": action_order,
      "actor_observation_terms": obs_terms,
      "unitree_motor_order": UNITREE_MOTOR_ORDER,
      "q_des_unitree_order": dict(zip(UNITREE_MOTOR_ORDER, q_des)),
      "seed_state": args.seed_state,
      "motor_offset_by_name": motor_offset_by_name,
    }
    Path(args.summary).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result["ok"] else 1

  ChannelFactoryInitialize(args.dds_domain, args.network_interface)
  lowstate = LowStateBuffer()
  sub = ChannelSubscriber("rt/lowstate", LowState_)
  sub.Init(lowstate.callback, 10)
  pub = ChannelPublisher("rt/lowcmd", LowCmd_)
  pub.Init()
  cmd = init_lowcmd()
  crc = CRC()
  timing_path = out_dir / "deployer_timing.csv"
  with timing_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
      f,
      fieldnames=[
        "step",
        "monotonic_s",
        "wall_time_s",
        "lowstate_count",
        "inference_s",
        "loop_s",
        "obs_abs_max",
        "action_abs_max",
        "q_des_0",
        "q_des_1",
        "q_des_2",
        "lowstate_q0",
        "lowstate_dq0",
        "quat_w",
        "quat_x",
        "quat_y",
        "quat_z",
      ],
    )
    writer.writeheader()
    start = time.monotonic()
    step = 0
    next_t = start
    while time.monotonic() - start < args.duration_s:
      loop_start = time.monotonic()
      obs = builder.actor_obs(lowstate.msg)
      infer_start = time.monotonic()
      with torch.no_grad():
        action = policy(TensorDict({"actor": obs}, batch_size=[1]), stochastic_output=False)
      action = builder.clip_action(action)
      infer_s = time.monotonic() - infer_start
      builder.update_action(action)
      q_des = write_lowcmd(cmd, action, action_order, crc, motor_offset_by_name)
      pub.Write(cmd)
      if lowstate.msg is None:
        lowstate_q0 = ""
        lowstate_dq0 = ""
        quat = ["", "", "", ""]
      else:
        lowstate_q0 = f"{float(lowstate.msg.motor_state[0].q):.9f}"
        lowstate_dq0 = f"{float(lowstate.msg.motor_state[0].dq):.9f}"
        quat = [f"{float(v):.9f}" for v in lowstate.msg.imu_state.quaternion]
      writer.writerow(
        {
          "step": step,
          "monotonic_s": f"{time.monotonic() - start:.6f}",
          "wall_time_s": f"{time.time():.6f}",
          "lowstate_count": lowstate.count,
          "inference_s": f"{infer_s:.9f}",
          "loop_s": f"{time.monotonic() - loop_start:.9f}",
          "obs_abs_max": f"{float(obs.abs().max().item()):.9f}",
          "action_abs_max": f"{float(action.abs().max().item()):.9f}",
          "q_des_0": f"{q_des[0]:.9f}",
          "q_des_1": f"{q_des[1]:.9f}",
          "q_des_2": f"{q_des[2]:.9f}",
          "lowstate_q0": lowstate_q0,
          "lowstate_dq0": lowstate_dq0,
          "quat_w": quat[0],
          "quat_x": quat[1],
          "quat_y": quat[2],
          "quat_z": quat[3],
        }
      )
      f.flush()
      step += 1
      next_t += 1.0 / args.policy_hz
      sleep_s = next_t - time.monotonic()
      if sleep_s > 0:
        time.sleep(sleep_s)
  summary = {
    "ok": step > 0,
    "steps": step,
    "lowstate_count": lowstate.count,
    "checkpoint": str(args.checkpoint),
    "action_order": action_order,
    "unitree_motor_order": UNITREE_MOTOR_ORDER,
    "timing": str(timing_path),
    "seed_state": args.seed_state,
    "motor_offset_by_name": motor_offset_by_name,
  }
  Path(args.summary).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
  return 0 if summary["ok"] else 1


def main() -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("--checkpoint", required=True)
  parser.add_argument("--log-dir", required=True)
  parser.add_argument("--out-dir", required=True)
  parser.add_argument("--summary", required=True)
  parser.add_argument("--device", default=None)
  parser.add_argument("--dds-domain", type=int, default=1)
  parser.add_argument("--network-interface", default="lo")
  parser.add_argument("--duration-s", type=float, default=12.0)
  parser.add_argument("--policy-hz", type=float, default=50.0)
  parser.add_argument("--smoke-only", action="store_true")
  parser.add_argument("--seed-state", default=None)
  return run(parser.parse_args())


if __name__ == "__main__":
  raise SystemExit(main())
