"""Caller-project MJLab task registration for DrEureka Go2 yoga-ball training."""

from __future__ import annotations

from mjlab.tasks.registry import register_mjlab_task

from .env_cfg import TASK_ID, make_dreureka_go2_yoga_ball_env_cfg
from .rl_cfg import make_dreureka_go2_ppo_runner_cfg


register_mjlab_task(
  task_id=TASK_ID,
  env_cfg=make_dreureka_go2_yoga_ball_env_cfg(),
  play_env_cfg=make_dreureka_go2_yoga_ball_env_cfg(play=True),
  rl_cfg=make_dreureka_go2_ppo_runner_cfg(),
  runner_cls=None,
)

