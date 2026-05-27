"""Minimal MJLab Go1 yoga-ball task registration.

This module is intentionally root-owned glue. MJLab remains an installed
dependency; the task is registered at runtime through MJLab's public registry.
"""

from __future__ import annotations

import math

import mujoco
import torch

from mjlab.asset_zoo.robots import GO1_ACTION_SCALE, get_go1_robot_cfg
from mjlab.entity import Entity, EntityCfg
from mjlab.envs import ManagerBasedRlEnv, ManagerBasedRlEnvCfg
from mjlab.envs import mdp as envs_mdp
from mjlab.envs.mdp.actions import JointPositionActionCfg
from mjlab.managers import EventTermCfg, ObservationTermCfg, RewardTermCfg, SceneEntityCfg
from mjlab.tasks.registry import list_tasks, register_mjlab_task
from mjlab.tasks.velocity import mdp
from mjlab.tasks.velocity.config.go1.env_cfgs import unitree_go1_flat_env_cfg
from mjlab.tasks.velocity.config.go1.rl_cfg import unitree_go1_ppo_runner_cfg
from mjlab.tasks.velocity.rl import VelocityOnPolicyRunner


TASK_ID = "Mjlab-Go1-YogaBall-PortSmoke"
BALL_RADIUS = 0.45
ROBOT_BASE_Z = 2.0 * BALL_RADIUS


def get_yoga_ball_spec(
    radius: float = BALL_RADIUS,
    mass: float = 1.0,
    rgba: tuple[float, float, float, float] = (0.1, 0.25, 0.9, 1.0),
) -> mujoco.MjSpec:
    spec = mujoco.MjSpec()
    body = spec.worldbody.add_body(name="yoga_ball", pos=(0.0, 0.0, radius))
    body.add_freejoint(name="yoga_ball_free")
    body.add_geom(
        name="yoga_ball_geom",
        type=mujoco.mjtGeom.mjGEOM_SPHERE,
        size=(radius,),
        mass=mass,
        rgba=rgba,
        condim=3,
        friction=(1.0, 0.02, 0.001),
    )
    return spec


def reset_go1_on_yoga_ball(
    env: ManagerBasedRlEnv,
    env_ids: torch.Tensor | None,
    *,
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
    ball_cfg: SceneEntityCfg = SceneEntityCfg("ball"),
) -> None:
    env_ids = envs_mdp.resolve_env_ids(env, env_ids)
    robot: Entity = env.scene[robot_cfg.name]
    ball: Entity = env.scene[ball_cfg.name]
    origins = env.scene.env_origins[env_ids]

    robot_pose = torch.zeros((len(env_ids), 7), device=env.device)
    robot_pose[:, :3] = origins + torch.tensor([0.0, 0.0, ROBOT_BASE_Z], device=env.device)
    robot_pose[:, 3] = 1.0
    robot.write_root_link_pose_to_sim(robot_pose, env_ids=env_ids)
    robot.write_root_link_velocity_to_sim(torch.zeros((len(env_ids), 6), device=env.device), env_ids=env_ids)

    default_joint_pos = robot.data.default_joint_pos[env_ids].clone()
    default_joint_vel = torch.zeros_like(default_joint_pos)
    robot.write_joint_state_to_sim(default_joint_pos, default_joint_vel, env_ids=env_ids)

    ball_pose = torch.zeros((len(env_ids), 7), device=env.device)
    ball_pose[:, :3] = origins + torch.tensor([0.0, 0.0, BALL_RADIUS], device=env.device)
    ball_pose[:, 3] = 1.0
    ball.write_root_link_pose_to_sim(ball_pose, env_ids=env_ids)
    ball.write_root_link_velocity_to_sim(torch.zeros((len(env_ids), 6), device=env.device), env_ids=env_ids)


def ball_position_relative_to_robot(env: ManagerBasedRlEnv) -> torch.Tensor:
    robot: Entity = env.scene["robot"]
    ball: Entity = env.scene["ball"]
    return ball.data.root_link_pos_w - robot.data.root_link_pos_w


def ball_velocity(env: ManagerBasedRlEnv) -> torch.Tensor:
    ball: Entity = env.scene["ball"]
    return ball.data.root_link_vel_w


def root_height_above_ball(env: ManagerBasedRlEnv) -> torch.Tensor:
    robot: Entity = env.scene["robot"]
    ball: Entity = env.scene["ball"]
    return robot.data.root_link_pos_w[:, 2] - ball.data.root_link_pos_w[:, 2]


def height_above_ball_reward(env: ManagerBasedRlEnv, target_height: float = BALL_RADIUS) -> torch.Tensor:
    err = root_height_above_ball(env) - target_height
    return torch.exp(-(err * err) / 0.04)


def make_go1_yoga_ball_env_cfg(play: bool = False) -> ManagerBasedRlEnvCfg:
    cfg = unitree_go1_flat_env_cfg(play=play)
    cfg.scene.entities = {
        "robot": get_go1_robot_cfg(),
        "ball": EntityCfg(
            init_state=EntityCfg.InitialStateCfg(
                pos=(0.0, 0.0, BALL_RADIUS),
                rot=(1.0, 0.0, 0.0, 0.0),
                lin_vel=(0.0, 0.0, 0.0),
                ang_vel=(0.0, 0.0, 0.0),
                joint_pos={},
                joint_vel={},
            ),
            spec_fn=get_yoga_ball_spec,
        ),
    }

    joint_pos_action = cfg.actions["joint_pos"]
    assert isinstance(joint_pos_action, JointPositionActionCfg)
    joint_pos_action.scale = GO1_ACTION_SCALE

    cfg.events["reset_base"] = EventTermCfg(
        func=reset_go1_on_yoga_ball,
        mode="reset",
        params={},
    )
    cfg.events.pop("reset_robot_joints", None)
    cfg.events.pop("randomize_terrain", None)
    cfg.events.pop("push_robot", None)

    cfg.observations["actor"].terms["ball_relative_position"] = ObservationTermCfg(
        func=ball_position_relative_to_robot
    )
    cfg.observations["actor"].terms["ball_velocity"] = ObservationTermCfg(func=ball_velocity)
    cfg.observations["critic"].terms["ball_relative_position"] = ObservationTermCfg(
        func=ball_position_relative_to_robot
    )
    cfg.observations["critic"].terms["ball_velocity"] = ObservationTermCfg(func=ball_velocity)

    cfg.rewards["height_above_ball"] = RewardTermCfg(
        func=height_above_ball_reward,
        weight=1.0,
        params={"target_height": BALL_RADIUS},
    )
    cfg.terminations["base_below_ball_top"] = cfg.terminations["fell_over"].__class__(
        func=envs_mdp.root_height_below_minimum,
        params={
            "minimum_height": 2.0 * BALL_RADIUS - 0.05,
            "asset_cfg": SceneEntityCfg("robot"),
        },
    )
    cfg.terminations["fell_over"].params["limit_angle"] = math.radians(75.0)

    cfg.scene.extent = 2.0
    cfg.episode_length_s = int(1e9) if play else 20.0
    cfg.curriculum = {}
    return cfg


def register_task() -> None:
    if TASK_ID in list_tasks():
        return
    register_mjlab_task(
        task_id=TASK_ID,
        env_cfg=make_go1_yoga_ball_env_cfg(play=False),
        play_env_cfg=make_go1_yoga_ball_env_cfg(play=True),
        rl_cfg=unitree_go1_ppo_runner_cfg(),
        runner_cls=VelocityOnPolicyRunner,
    )
