"""DrEureka EurekaReward terms in MJLab form."""

from __future__ import annotations

import torch


def _ball_radius(env) -> torch.Tensor:
  if hasattr(env, "dreureka_ball_radius"):
    return env.dreureka_ball_radius
  return torch.full((env.num_envs,), 0.4, device=env.device)


def reward_height(env) -> torch.Tensor:
  robot = env.scene["robot"]
  radius = _ball_radius(env)
  threshold = 2.0 * radius
  height_temperature = 7.0
  height_exp = torch.exp((robot.data.root_link_pos_w[:, 2] - threshold) / height_temperature)
  return 1.5 * torch.where(
    robot.data.root_link_pos_w[:, 2] >= threshold,
    height_exp,
    torch.zeros_like(height_exp),
  )


def reward_balance(env, foot_site_names: tuple[str, ...]) -> torch.Tensor:
  robot = env.scene["robot"]
  ball = env.scene["ball"]
  _, site_names = robot.find_sites(foot_site_names, preserve_order=True)
  name_to_idx = {name: idx for idx, name in enumerate(robot.site_names)}
  site_ids = torch.tensor([name_to_idx[name] for name in site_names], device=env.device)
  radius = _ball_radius(env)
  ball_top = ball.data.root_link_pos_w.clone()
  ball_top[:, 2] += radius
  foot_pos = robot.data.site_pos_w[:, site_ids, :]
  dist = torch.norm(foot_pos - ball_top.unsqueeze(1), dim=-1)
  return 2.0 * torch.mean(torch.exp(-dist / 5.0), dim=-1)


def reward_smooth_actions(env) -> torch.Tensor:
  return -torch.mean(
    torch.abs(env.action_manager.action - env.action_manager.prev_action),
    dim=-1,
  )


def reward_penalize_large_actions(env) -> torch.Tensor:
  return -0.3 * torch.mean(torch.abs(env.action_manager.action), dim=-1)


def reward_joint_limit_barrier(env) -> torch.Tensor:
  robot = env.scene["robot"]
  lower = robot.data.soft_joint_pos_limits[..., 0]
  upper = robot.data.soft_joint_pos_limits[..., 1]
  span = torch.clamp(upper - lower, min=1e-3)
  clearance = torch.minimum(robot.data.joint_pos - lower, upper - robot.data.joint_pos) / span

  margin = 0.15
  distance_to_margin = clearance.clamp(min=0.0, max=margin)
  proximity_penalty = -4.0 * (1.0 - distance_to_margin / margin).pow(2)
  return torch.mean(proximity_penalty, dim=-1)


def reward_keep_ball_stationary(env) -> torch.Tensor:
  ball = env.scene["ball"]
  ball_speed = torch.norm(ball.data.root_link_lin_vel_w, dim=-1)
  return -2.0 * ball_speed


def reward_penalize_action_jerk(env) -> torch.Tensor:
  jerk = (
    env.action_manager.action
    - 2.0 * env.action_manager.prev_action
    + env.action_manager.prev_prev_action
  )
  return -0.15 * torch.mean(torch.abs(jerk), dim=-1)
