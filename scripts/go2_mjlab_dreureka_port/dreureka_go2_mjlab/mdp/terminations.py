"""Termination terms for the DrEureka yoga-ball task."""

from __future__ import annotations

import torch


def base_below_ball_radius(env) -> torch.Tensor:
  robot = env.scene["robot"]
  if hasattr(env, "dreureka_ball_radius"):
    radius = env.dreureka_ball_radius
  else:
    radius = torch.full((env.num_envs,), 0.4, device=env.device)
  return robot.data.root_link_pos_w[:, 2] < radius

