"""Reset/randomization terms mirroring DrEureka yoga-ball placement."""

from __future__ import annotations

from types import MethodType

import torch

from mjlab.managers.event_manager import RecomputeLevel, requires_model_fields
from mjlab.managers.scene_entity_config import SceneEntityCfg
from mjlab.utils.lab_api.math import quat_from_euler_xyz


def _resolve_env_ids(env, env_ids: torch.Tensor | None) -> torch.Tensor:
  if env_ids is None:
    return torch.arange(env.num_envs, device=env.device, dtype=torch.int64)
  return env_ids


def _sample(env, env_ids: torch.Tensor, value_range: tuple[float, float]) -> torch.Tensor:
  low, high = value_range
  return torch.empty(len(env_ids), device=env.device).uniform_(float(low), float(high))


def _ids(env, ids) -> torch.Tensor:
  return torch.as_tensor(ids, device=env.device, dtype=torch.long)


def _ensure_dr_state(env, domain_rand: dict) -> None:
  defaults = {
    "dreureka_ball_radius": sum(domain_rand["ball_radius_range"]) / 2.0,
    "dreureka_ball_mass": sum(domain_rand["ball_mass_range"]) / 2.0,
    "dreureka_ball_friction": sum(domain_rand["ball_friction_range"]) / 2.0,
    "dreureka_ball_restitution": sum(domain_rand["ball_restitution_range"]) / 2.0,
    "dreureka_ball_compliance": sum(domain_rand["ball_compliance_range"]) / 2.0,
    "dreureka_ball_drag": sum(domain_rand["ball_drag_range"]) / 2.0,
    "dreureka_robot_motor_strength": sum(domain_rand["robot_motor_strength_range"]) / 2.0,
    "dreureka_action_lag_timesteps": int(sum(domain_rand["lag_timesteps_range"]) / 2),
  }
  for name, value in defaults.items():
    if not hasattr(env, name):
      dtype = torch.long if name == "dreureka_action_lag_timesteps" else torch.float
      setattr(
        env,
        name,
        torch.full((env.num_envs,), value, device=env.device, dtype=dtype),
      )
  if not hasattr(env, "dreureka_robot_motor_offset"):
    env.dreureka_robot_motor_offset = torch.zeros(
      (env.num_envs, env.single_action_space.shape[0]), device=env.device
    )
  if not hasattr(env, "dreureka_gravity_offset"):
    env.dreureka_gravity_offset = torch.zeros((env.num_envs, 3), device=env.device)
  if not hasattr(env, "dreureka_action_lag_buffer"):
    max_lag = int(domain_rand["lag_timesteps_range"][1])
    env.dreureka_action_lag_buffer = torch.zeros(
      (max_lag + 1, env.num_envs, env.single_action_space.shape[0]),
      device=env.device,
    )


def _recompute_sphere_geom_bounds(env, env_ids: torch.Tensor, geom_ids: torch.Tensor) -> None:
  env_grid, geom_grid = torch.meshgrid(env_ids, geom_ids, indexing="ij")
  radius = env.sim.model.geom_size[env_grid, geom_grid, 0]
  env.sim.model.geom_rbound[env_grid, geom_grid] = radius
  env.sim.model.geom_aabb[env_grid, geom_grid, 1, :] = radius.unsqueeze(-1)


def install_dreureka_action_lag(
  env,
  env_ids: torch.Tensor | None,
  domain_rand: dict,
) -> None:
  del env_ids
  _ensure_dr_state(env, domain_rand)
  if getattr(env.action_manager, "_dreureka_lag_installed", False):
    return
  original = env.action_manager.process_action

  def process_action_with_lag(manager, action: torch.Tensor) -> None:
    buffer = env.dreureka_action_lag_buffer
    buffer[:-1] = buffer[1:].clone()
    buffer[-1] = action.to(env.device)
    lag = env.dreureka_action_lag_timesteps.clamp(0, buffer.shape[0] - 1)
    buffer_idx = buffer.shape[0] - lag - 1
    lagged = buffer[buffer_idx, torch.arange(env.num_envs, device=env.device)]
    original(action)
    idx = 0
    for term in manager._terms.values():
      term_actions = lagged[:, idx : idx + term.action_dim]
      term.process_actions(term_actions)
      idx += term.action_dim

  env.action_manager.process_action = MethodType(process_action_with_lag, env.action_manager)
  env.action_manager._dreureka_lag_installed = True


def reset_robot_on_ball(
  env,
  env_ids: torch.Tensor | None,
  domain_rand: dict,
  asset_cfg: SceneEntityCfg,
  ball_cfg: SceneEntityCfg,
) -> None:
  env_ids = _resolve_env_ids(env, env_ids)
  robot = env.scene[asset_cfg.name]
  ball = env.scene[ball_cfg.name]
  _ensure_dr_state(env, domain_rand)

  radius = _sample(env, env_ids, domain_rand["ball_radius_range"])
  env.dreureka_ball_radius[env_ids] = radius

  ball_state = ball.data.default_root_state[env_ids].clone()
  ball_state[:, 0:3] += env.scene.env_origins[env_ids]
  ball_state[:, 2] = env.scene.env_origins[env_ids, 2] + radius + 0.0001
  ball_state[:, 7:13] = 0.0
  ball.write_root_state_to_sim(ball_state, env_ids=env_ids)

  robot_state = robot.data.default_root_state[env_ids].clone()
  robot_state[:, 0:3] += env.scene.env_origins[env_ids]
  robot_state[:, 2] += 2.0 * radius + 0.0001
  yaw = torch.empty(len(env_ids), device=env.device).uniform_(-3.14, 3.14)
  robot_state[:, 3:7] = quat_from_euler_xyz(
    torch.zeros_like(yaw), torch.zeros_like(yaw), yaw
  )
  robot_state[:, 7:13] = torch.empty(
    (len(env_ids), 6), device=env.device
  ).uniform_(-0.5, 0.5)
  robot.write_root_state_to_sim(robot_state, env_ids=env_ids)


@requires_model_fields(
  "geom_friction",
  "geom_size",
  "geom_rbound",
  "geom_aabb",
  "body_mass",
  "body_inertia",
  "body_ipos",
  "actuator_gainprm",
  "actuator_biasprm",
  recompute=RecomputeLevel.set_const,
)
def randomize_dreureka_physics(
  env,
  env_ids: torch.Tensor | None,
  domain_rand: dict,
  asset_cfg: SceneEntityCfg,
  ball_cfg: SceneEntityCfg,
) -> None:
  env_ids = _resolve_env_ids(env, env_ids)
  _ensure_dr_state(env, domain_rand)
  robot = env.scene[asset_cfg.name]
  ball = env.scene[ball_cfg.name]

  robot_friction = _sample(env, env_ids, domain_rand["robot_friction_range"])
  robot_restitution = _sample(env, env_ids, domain_rand["robot_restitution_range"])
  ball_friction = _sample(env, env_ids, domain_rand["ball_friction_range"])
  ball_restitution = _sample(env, env_ids, domain_rand["ball_restitution_range"])

  env.dreureka_ball_friction[env_ids] = ball_friction
  env.dreureka_ball_restitution[env_ids] = ball_restitution
  env.dreureka_ball_compliance[env_ids] = _sample(
    env, env_ids, domain_rand["ball_compliance_range"]
  )
  env.dreureka_ball_mass[env_ids] = _sample(env, env_ids, domain_rand["ball_mass_range"])
  env.dreureka_robot_motor_strength[env_ids] = _sample(
    env, env_ids, domain_rand["robot_motor_strength_range"]
  )
  offset_low, offset_high = domain_rand["robot_motor_offset_range"]
  env.dreureka_robot_motor_offset[env_ids] = torch.empty(
    (len(env_ids), env.single_action_space.shape[0]), device=env.device
  ).uniform_(float(offset_low), float(offset_high))

  env_grid, robot_geom_grid = torch.meshgrid(
    env_ids, _ids(env, robot.indexing.geom_ids), indexing="ij"
  )
  env.sim.model.geom_friction[env_grid, robot_geom_grid, 0] = robot_friction[:, None]
  env.dreureka_robot_restitution = getattr(
    env,
    "dreureka_robot_restitution",
    torch.zeros(env.num_envs, device=env.device),
  )
  env.dreureka_robot_restitution[env_ids] = robot_restitution

  env_grid, ball_geom_grid = torch.meshgrid(
    env_ids, _ids(env, ball.indexing.geom_ids), indexing="ij"
  )
  env.sim.model.geom_friction[env_grid, ball_geom_grid, 0] = ball_friction[:, None]
  env.sim.model.geom_size[env_grid, ball_geom_grid, 0] = env.dreureka_ball_radius[
    env_ids
  ][:, None]
  _recompute_sphere_geom_bounds(env, env_ids, _ids(env, ball.indexing.geom_ids))

  base_body_id = int(robot.indexing.body_ids[0])
  env.sim.model.body_mass[env_ids, base_body_id] = (
    env.sim.get_default_field("body_mass")[base_body_id]
    + _sample(env, env_ids, domain_rand["robot_payload_mass_range"])
  )
  com_low, com_high = domain_rand["robot_com_displacement_range"]
  env.sim.model.body_ipos[env_ids, base_body_id, :] = torch.empty(
    (len(env_ids), 3), device=env.device
  ).uniform_(float(com_low), float(com_high))

  ball_body_id = int(ball.indexing.body_ids[0])
  env.sim.model.body_mass[env_ids, ball_body_id] = env.dreureka_ball_mass[env_ids]
  inertia_multiplier = _sample(env, env_ids, domain_rand["ball_inertia_multiplier_range"])
  radius = env.dreureka_ball_radius[env_ids]
  solid_sphere_inertia = (2.0 / 5.0) * env.dreureka_ball_mass[env_ids] * radius.square()
  env.sim.model.body_inertia[env_ids, ball_body_id, :] = (
    solid_sphere_inertia * inertia_multiplier
  ).unsqueeze(1)

  joint_pos_action = env.action_manager.get_term("joint_pos")
  if hasattr(joint_pos_action, "_offset") and not isinstance(joint_pos_action._offset, float):
    joint_pos_action._offset[env_ids] = (
      robot.data.default_joint_pos[env_ids][:, joint_pos_action.target_ids]
      + env.dreureka_robot_motor_offset[env_ids]
    )
  ctrl_ids = _ids(env, robot.indexing.ctrl_ids)
  default_gainprm = env.sim.get_default_field("actuator_gainprm")
  default_biasprm = env.sim.get_default_field("actuator_biasprm")
  strength = env.dreureka_robot_motor_strength[env_ids].unsqueeze(1)
  env.sim.model.actuator_gainprm[env_ids[:, None], ctrl_ids, 0] = (
    default_gainprm[ctrl_ids, 0] * strength
  )
  env.sim.model.actuator_biasprm[env_ids[:, None], ctrl_ids, 1] = (
    default_biasprm[ctrl_ids, 1] * strength
  )
  env.sim.model.actuator_biasprm[env_ids[:, None], ctrl_ids, 2] = (
    default_biasprm[ctrl_ids, 2] * strength
  )


def push_robot_like_dreureka(
  env,
  env_ids: torch.Tensor | None,
  velocity_range: tuple[float, float],
  asset_cfg: SceneEntityCfg,
) -> None:
  env_ids = _resolve_env_ids(env, env_ids)
  asset = env.scene[asset_cfg.name]
  low, high = velocity_range
  mag = torch.empty(len(env_ids), device=env.device).uniform_(float(low), float(high))
  direction = torch.empty((len(env_ids), 2), device=env.device).uniform_(-1.0, 1.0)
  direction = direction / torch.clamp(torch.norm(direction, dim=1, keepdim=True), min=1e-6)
  velocity = asset.data.root_link_vel_w[env_ids].clone()
  velocity[:, :2] += mag.unsqueeze(1) * direction
  asset.write_root_link_velocity_to_sim(velocity, env_ids=env_ids)


def randomize_gravity_like_dreureka(
  env,
  env_ids: torch.Tensor | None,
  gravity_range: tuple[float, float],
) -> None:
  env_ids = _resolve_env_ids(env, env_ids)
  if not hasattr(env, "dreureka_gravity_offset"):
    env.dreureka_gravity_offset = torch.zeros((env.num_envs, 3), device=env.device)
  low, high = gravity_range
  offset = torch.empty((len(env_ids), 3), device=env.device).uniform_(
    float(low), float(high)
  )
  gravity = offset + torch.tensor((0.0, 0.0, -9.8), device=env.device)
  gravity_unit = gravity / torch.norm(gravity, dim=1, keepdim=True)
  env.dreureka_gravity_offset[env_ids] = offset
  for entity in env.scene.entities.values():
    if hasattr(entity, "data") and hasattr(entity.data, "gravity_vec_w"):
      entity.data.gravity_vec_w[env_ids] = gravity_unit


def randomize_ball_drag_like_dreureka(
  env,
  env_ids: torch.Tensor | None,
  drag_range: tuple[float, float],
) -> None:
  env_ids = _resolve_env_ids(env, env_ids)
  if not hasattr(env, "dreureka_ball_drag"):
    env.dreureka_ball_drag = torch.zeros(env.num_envs, device=env.device)
  env.dreureka_ball_drag[env_ids] = _sample(env, env_ids, drag_range)


def apply_ball_drag(
  env,
  env_ids: torch.Tensor | None,
  ball_cfg: SceneEntityCfg,
) -> None:
  env_ids = _resolve_env_ids(env, env_ids)
  if not hasattr(env, "dreureka_ball_drag"):
    return
  ball = env.scene[ball_cfg.name]
  velocity = ball.data.root_link_lin_vel_w[env_ids, :2]
  force_xy = -env.dreureka_ball_drag[env_ids, None] * velocity.square() * torch.sign(velocity)
  forces = torch.zeros((len(env_ids), 1, 3), device=env.device)
  torques = torch.zeros_like(forces)
  forces[:, 0, :2] = force_xy
  ball.write_external_wrench_to_sim(forces, torques, body_ids=[0], env_ids=env_ids)


def randomize_action_lag_like_dreureka(
  env,
  env_ids: torch.Tensor | None,
  lag_timesteps_range: tuple[int, int],
) -> None:
  env_ids = _resolve_env_ids(env, env_ids)
  low, high = lag_timesteps_range
  if not hasattr(env, "dreureka_action_lag_timesteps"):
    env.dreureka_action_lag_timesteps = torch.zeros(
      env.num_envs, device=env.device, dtype=torch.long
    )
  env.dreureka_action_lag_timesteps[env_ids] = torch.randint(
    int(low), int(high) + 1, (len(env_ids),), device=env.device
  )
