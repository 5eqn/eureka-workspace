"""DrEureka Go2 yoga-ball MJLab caller-project configuration."""

from __future__ import annotations

from dataclasses import replace

import mujoco

from mjlab.actuator import BuiltinPositionActuatorCfg
from mjlab.envs import ManagerBasedRlEnvCfg
from mjlab.envs import mdp as envs_mdp
from mjlab.envs.mdp.actions import JointPositionActionCfg
from mjlab.entity import EntityArticulationInfoCfg, EntityCfg
from mjlab.managers.event_manager import EventTermCfg
from mjlab.managers.observation_manager import ObservationGroupCfg, ObservationTermCfg
from mjlab.managers.reward_manager import RewardTermCfg
from mjlab.managers.scene_entity_config import SceneEntityCfg
from mjlab.managers.termination_manager import TerminationTermCfg
from mjlab.scene import SceneCfg
from mjlab.sensor import ContactMatch, ContactSensorCfg
from mjlab.sim import MujocoCfg, SimulationCfg
from mjlab.terrains import HfRandomUniformTerrainCfg, TerrainEntityCfg
from mjlab.terrains.terrain_generator import TerrainGeneratorCfg
from mjlab.viewer import ViewerConfig
from src.assets.robots.unitree_go2.go2_constants import FULL_COLLISION, get_go2_robot_cfg

from . import mdp

TASK_ID = "DrEureka-Go2-YogaBall"

BALL_RADIUS_RANGE = (0.35, 0.45)
DEFAULT_BALL_RADIUS = sum(BALL_RADIUS_RANGE) / 2.0
TERRAIN_TILE_SIZE = (20.0, 20.0)

PRETRAINED_DOMAIN_RAND = {
  "robot_friction_range": (0.1, 1.0),
  "robot_restitution_range": (0.2, 0.8),
  "robot_payload_mass_range": (0.0, 3.0),
  "robot_com_displacement_range": (-0.05, 0.05),
  "robot_motor_strength_range": (0.95, 1.05),
  "robot_motor_offset_range": (-0.005, 0.05),
  "ball_radius_range": BALL_RADIUS_RANGE,
  "ball_mass_range": (1.0, 3.0),
  "ball_friction_range": (0.5, 2.5),
  "ball_restitution_range": (0.4, 0.9),
  "ball_compliance_range": (0.0, 1.0),
  "ball_inertia_multiplier_range": (5.0 / 3.0, 5.0 / 3.0),
  "ball_spring_coefficient_range": (0.0, 0.0),
  "ball_drag_range": (0.1, 0.5),
  "terrain_ground_friction_range": (0.2, 0.8),
  "terrain_ground_restitution_range": (0.0, 0.5),
  "terrain_tile_roughness_range": (0.02, 0.08),
  "robot_push_vel_range": (0.1, 0.4),
  "ball_push_vel_range": (0.1, 0.4),
  "gravity_range": (-0.1, 0.1),
  "lag_timesteps_range": (6, 6),
  "push_robot_interval_s": 15.0,
  "push_ball_interval_s": 10.0,
  "gravity_rand_interval_s": 10.0,
  "ball_drag_rand_interval_s": 15.0,
  "lag_timesteps_rand_interval_s": 10.0,
}

DREUREKA_CONTRACT = {
  "robot": {
    "init_pos": (0.0, 0.0, 0.42),
    "default_joint_angles": {
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
    },
    "control_type": "P",
    "actuator_gains": {
      "hip": {"stiffness": 20.0, "damping": 1.0},
      "thigh": {"stiffness": 20.0, "damping": 1.0},
      "calf": {"stiffness": 40.0, "damping": 2.0},
    },
    "action_scale": 0.25,
    "decimation": 4,
    "soft_dof_pos_limit": 0.9,
    "unitree_data_source": "/home/seqn/unitree_rl_mjlab/src/assets/robots/unitree_go2",
  },
  "task": {
    "add_balls": True,
    "commands_num_commands": 0,
    "episode_length_s": 40.0,
    "num_observations": 56,
    "num_privileged_obs": 11,
    "num_observation_history": 15,
    "terrain_mesh_type": "mjlab_random_rough_hfield",
    "terrain_num_rows": 1,
    "terrain_num_cols": 1,
    "terrain_tile_size": TERRAIN_TILE_SIZE,
    "terrain_noise_range": PRETRAINED_DOMAIN_RAND["terrain_tile_roughness_range"],
    "terrain_noise_step": 0.02,
    "terrain_curriculum": False,
    "terrain_note": "Uses one MJLab native HfRandomUniformTerrainCfg random_rough patch with reset-time env-origin randomization. Terrain material DR is intentionally disabled to avoid per-world terrain-geom expansion.",
    "use_terminal_body_height": True,
    "terminal_body_height": 0.20,
    "terminate_after_contacts_on": (),
  },
  "domain_rand": PRETRAINED_DOMAIN_RAND,
  "ball": {
    "radius_range": BALL_RADIUS_RANGE,
    "default_radius": DEFAULT_BALL_RADIUS,
    "vision_receive_prob": 0.7,
    "init_pos_range": (0.0, 0.0, 0.0),
    "init_vel_range": (0.0, 0.0, 0.0),
  },
  "rewards": {
    "height": {"weight": 1.0, "internal_scale": 1.5},
    "balance": {"weight": 1.0, "internal_scale": 2.0},
    "smooth_actions": {"weight": 1.0, "internal_scale": 1.0},
    "penalize_large_actions": {"weight": 1.0, "internal_scale": 0.3},
  },
}


def _make_ball_spec() -> mujoco.MjSpec:
  spec = mujoco.MjSpec()
  body = spec.worldbody.add_body(name="ball")
  body.add_freejoint(name="floating_base_joint")
  body.add_geom(
    name="ball_collision",
    type=mujoco.mjtGeom.mjGEOM_SPHERE,
    size=(DEFAULT_BALL_RADIUS,),
    mass=1.0,
    friction=(1.0, 0.005, 0.0001),
    rgba=(0.1, 0.45, 0.9, 1.0),
  )
  return spec


def _dreureka_go2_robot_cfg() -> EntityCfg:
  cfg = get_go2_robot_cfg()
  cfg.init_state = EntityCfg.InitialStateCfg(
    pos=DREUREKA_CONTRACT["robot"]["init_pos"],
    joint_pos=DREUREKA_CONTRACT["robot"]["default_joint_angles"],
    joint_vel={".*": 0.0},
  )
  cfg.articulation = EntityArticulationInfoCfg(
    actuators=(
      BuiltinPositionActuatorCfg(
        target_names_expr=(".*hip_joint",),
        stiffness=20.0,
        damping=1.0,
        effort_limit=23.5,
        armature=0.01,
      ),
      BuiltinPositionActuatorCfg(
        target_names_expr=(".*thigh_joint",),
        stiffness=20.0,
        damping=1.0,
        effort_limit=23.5,
        armature=0.01,
      ),
      BuiltinPositionActuatorCfg(
        target_names_expr=(".*calf_joint",),
        stiffness=40.0,
        damping=2.0,
        effort_limit=45.0,
        armature=0.02,
      ),
    ),
    soft_joint_pos_limit_factor=0.9,
  )
  cfg.collisions = (FULL_COLLISION,)
  return cfg


def _yoga_ball_cfg() -> EntityCfg:
  return EntityCfg(
    init_state=EntityCfg.InitialStateCfg(
      pos=(0.0, 0.0, DEFAULT_BALL_RADIUS + 0.0001),
      joint_pos={},
      joint_vel={},
    ),
    spec_fn=_make_ball_spec,
  )


def _terrain_cfg() -> TerrainEntityCfg:
  terrain_generator = TerrainGeneratorCfg(
    seed=42,
    curriculum=False,
    size=TERRAIN_TILE_SIZE,
    border_width=0.0,
    num_rows=1,
    num_cols=1,
    color_scheme="height",
    sub_terrains={
      "random_rough": HfRandomUniformTerrainCfg(
        proportion=1.0,
        noise_range=PRETRAINED_DOMAIN_RAND["terrain_tile_roughness_range"],
        noise_step=0.02,
        horizontal_scale=0.25,
        vertical_scale=0.005,
        downsampled_scale=0.25,
        border_width=0.5,
      ),
    },
    add_lights=True,
  )
  return TerrainEntityCfg(
    terrain_type="generator",
    terrain_generator=terrain_generator,
    max_init_terrain_level=1,
  )


def _foot_contact_sensor() -> ContactSensorCfg:
  return ContactSensorCfg(
    name="feet_ground_contact",
    primary=ContactMatch(
      mode="geom",
      pattern=(
        "FL_foot_collision",
        "FR_foot_collision",
        "RL_foot_collision",
        "RR_foot_collision",
      ),
      entity="robot",
    ),
    secondary=ContactMatch(mode="body", pattern="terrain"),
    fields=("found", "force"),
    reduce="netforce",
    num_slots=1,
    track_air_time=True,
  )


def make_dreureka_go2_yoga_ball_env_cfg(play: bool = False) -> ManagerBasedRlEnvCfg:
  """Create the caller-project MJLab config for DrEureka Go2 yoga-ball."""
  actor_terms = {
    "orientation": ObservationTermCfg(func=envs_mdp.projected_gravity),
    "joint_pos": ObservationTermCfg(func=envs_mdp.joint_pos_rel),
    "joint_vel": ObservationTermCfg(func=envs_mdp.joint_vel_rel, scale=0.05),
    "action": ObservationTermCfg(func=envs_mdp.last_action),
    "last_action": ObservationTermCfg(func=mdp.previous_action),
    "clock": ObservationTermCfg(func=mdp.clock_input),
    "yaw": ObservationTermCfg(func=mdp.yaw),
  }
  privileged_terms = {
    "object": ObservationTermCfg(func=mdp.object_local_pos, scale=1.0),
    "body_velocity": ObservationTermCfg(func=envs_mdp.base_lin_vel),
    "object_velocity": ObservationTermCfg(func=mdp.object_lin_vel),
    "restitution": ObservationTermCfg(func=mdp.ball_restitution),
    "friction": ObservationTermCfg(func=mdp.ball_friction),
  }
  cfg = ManagerBasedRlEnvCfg(
    scene=SceneCfg(
      terrain=_terrain_cfg(),
      entities={
        "robot": _dreureka_go2_robot_cfg(),
        "ball": _yoga_ball_cfg(),
      },
      sensors=(_foot_contact_sensor(),),
      num_envs=4096,
      extent=2.0,
    ),
    observations={
      "actor": ObservationGroupCfg(
        terms=actor_terms,
        concatenate_terms=True,
        enable_corruption=False,
        history_length=15,
      ),
      "critic": ObservationGroupCfg(
        terms=privileged_terms,
        concatenate_terms=True,
        enable_corruption=False,
        history_length=1,
      ),
    },
    actions={
      "joint_pos": JointPositionActionCfg(
        entity_name="robot",
        actuator_names=(".*",),
        scale=0.25,
        use_default_offset=True,
      )
    },
    events={
      "install_dreureka_action_lag": EventTermCfg(
        func=mdp.install_dreureka_action_lag,
        mode="startup",
        params={"domain_rand": PRETRAINED_DOMAIN_RAND},
      ),
      "reset_scene_to_default": EventTermCfg(
        func=envs_mdp.reset_scene_to_default,
        mode="reset",
      ),
      "randomize_terrain_origin": EventTermCfg(
        func=envs_mdp.randomize_terrain,
        mode="reset",
      ),
      "reset_robot_to_dreureka_ball": EventTermCfg(
        func=mdp.reset_robot_on_ball,
        mode="reset",
        params={
          "domain_rand": PRETRAINED_DOMAIN_RAND,
          "asset_cfg": SceneEntityCfg("robot"),
          "ball_cfg": SceneEntityCfg("ball"),
        },
      ),
      "randomize_dreureka_physics": EventTermCfg(
        func=mdp.randomize_dreureka_physics,
        mode="reset",
        params={
          "domain_rand": PRETRAINED_DOMAIN_RAND,
          "asset_cfg": SceneEntityCfg("robot"),
          "ball_cfg": SceneEntityCfg("ball"),
        },
      ),
      "push_robot": EventTermCfg(
        func=mdp.push_robot_like_dreureka,
        mode="interval",
        interval_range_s=(
          PRETRAINED_DOMAIN_RAND["push_robot_interval_s"],
          PRETRAINED_DOMAIN_RAND["push_robot_interval_s"],
        ),
        params={
          "velocity_range": PRETRAINED_DOMAIN_RAND["robot_push_vel_range"],
          "asset_cfg": SceneEntityCfg("robot"),
        },
      ),
      "push_ball": EventTermCfg(
        func=mdp.push_robot_like_dreureka,
        mode="interval",
        interval_range_s=(
          PRETRAINED_DOMAIN_RAND["push_ball_interval_s"],
          PRETRAINED_DOMAIN_RAND["push_ball_interval_s"],
        ),
        params={
          "velocity_range": PRETRAINED_DOMAIN_RAND["ball_push_vel_range"],
          "asset_cfg": SceneEntityCfg("ball"),
        },
      ),
      "randomize_gravity": EventTermCfg(
        func=mdp.randomize_gravity_like_dreureka,
        mode="interval",
        interval_range_s=(
          PRETRAINED_DOMAIN_RAND["gravity_rand_interval_s"],
          PRETRAINED_DOMAIN_RAND["gravity_rand_interval_s"],
        ),
        is_global_time=True,
        params={"gravity_range": PRETRAINED_DOMAIN_RAND["gravity_range"]},
      ),
      "randomize_ball_drag": EventTermCfg(
        func=mdp.randomize_ball_drag_like_dreureka,
        mode="interval",
        interval_range_s=(
          PRETRAINED_DOMAIN_RAND["ball_drag_rand_interval_s"],
          PRETRAINED_DOMAIN_RAND["ball_drag_rand_interval_s"],
        ),
        params={"drag_range": PRETRAINED_DOMAIN_RAND["ball_drag_range"]},
      ),
      "apply_ball_drag": EventTermCfg(
        func=mdp.apply_ball_drag,
        mode="step",
        params={"ball_cfg": SceneEntityCfg("ball")},
      ),
      "randomize_action_lag": EventTermCfg(
        func=mdp.randomize_action_lag_like_dreureka,
        mode="interval",
        interval_range_s=(
          PRETRAINED_DOMAIN_RAND["lag_timesteps_rand_interval_s"],
          PRETRAINED_DOMAIN_RAND["lag_timesteps_rand_interval_s"],
        ),
        params={"lag_timesteps_range": PRETRAINED_DOMAIN_RAND["lag_timesteps_range"]},
      ),
    },
    rewards={
      "height": RewardTermCfg(func=mdp.reward_height, weight=1.0),
      "balance": RewardTermCfg(
        func=mdp.reward_balance,
        weight=1.0,
        params={"foot_site_names": ("FL", "FR", "RL", "RR")},
      ),
      "smooth_actions": RewardTermCfg(func=mdp.reward_smooth_actions, weight=1.0),
      "penalize_large_actions": RewardTermCfg(
        func=mdp.reward_penalize_large_actions,
        weight=1.0,
      ),
    },
    terminations={
      "time_out": TerminationTermCfg(func=envs_mdp.time_out, time_out=True),
      "base_below_ball_radius": TerminationTermCfg(func=mdp.base_below_ball_radius),
      "terminal_body_height": TerminationTermCfg(
        func=envs_mdp.root_height_below_minimum,
        params={"minimum_height": 0.20},
      ),
    },
    commands={},
    curriculum={},
    metrics={},
    viewer=ViewerConfig(
      origin_type=ViewerConfig.OriginType.ASSET_BODY,
      entity_name="robot",
      body_name="base_link",
      distance=3.0,
      elevation=-10.0,
      azimuth=90.0,
    ),
    sim=SimulationCfg(
      nconmax=128,
      njmax=1500,
      contact_sensor_maxmatch=128,
      mujoco=MujocoCfg(
        timestep=0.005,
        iterations=10,
        ls_iterations=20,
        ccd_iterations=50,
      ),
    ),
    decimation=4,
    episode_length_s=40.0,
  )
  cfg.dreureka_contract = DREUREKA_CONTRACT
  if play:
    cfg = replace(cfg)
    cfg.scene.num_envs = 64
  return cfg
