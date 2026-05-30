"""Observation terms matching DrEureka's yoga-ball sensor contract."""

from __future__ import annotations

import torch

from mjlab.utils.lab_api.math import quat_apply, quat_apply_inverse


def previous_action(env) -> torch.Tensor:
  return env.action_manager.prev_action


def clock_input(env) -> torch.Tensor:
  return torch.zeros((env.num_envs, 4), device=env.device)


def yaw(env) -> torch.Tensor:
  robot = env.scene["robot"]
  forward = quat_apply(robot.data.root_link_quat_w, robot.data.forward_vec_b)
  return torch.atan2(forward[:, 1], forward[:, 0]).unsqueeze(1)


def object_local_pos(env) -> torch.Tensor:
  robot = env.scene["robot"]
  ball = env.scene["ball"]
  vec = ball.data.root_link_pos_w - robot.data.root_link_pos_w
  local = quat_apply_inverse(robot.data.root_link_quat_w, vec)
  local[:, 2] = 0.0
  return local


def object_lin_vel(env) -> torch.Tensor:
  return env.scene["ball"].data.root_link_lin_vel_w


def ball_restitution(env) -> torch.Tensor:
  low, high = 0.4, 0.9
  value = getattr(
    env,
    "dreureka_ball_restitution",
    torch.full((env.num_envs,), (low + high) / 2.0, device=env.device),
  )
  return ((value - (low + high) / 2.0) * (2.0 / (high - low))).unsqueeze(1)


def ball_friction(env) -> torch.Tensor:
  low, high = 0.5, 2.5
  value = getattr(
    env,
    "dreureka_ball_friction",
    torch.full((env.num_envs,), (low + high) / 2.0, device=env.device),
  )
  return ((value - (low + high) / 2.0) * (2.0 / (high - low))).unsqueeze(1)
