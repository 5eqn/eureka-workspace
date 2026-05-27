# Go2 Isaac Gym Consistency Report

- Status: PASS
- Core consistency without actuator acceptance: `PASS`
- Long training allowed: `True`
- Actuator path ok: `True`
- Go2 actuator-net candidates in fetched resources: `[]`
- Ground truth: `thirdparties/unitree_mujoco/unitree_robots/go2/go2.xml` commit `c598f103acb87a5fd3de7c9037f4dab6aa7f232b`
- Controller: SDK2 `LowCmd` PD command path; no Go2 actuator network was found in fetched resources.
- Actuator source of truth: Unitree MuJoCo `LowCmd` torque equation and Go2 MJCF actuator limits. The Go2 deploy bridge forwards the same `q_des`, `qd_des`, `kp`, `kd`, and `tau_ff` fields to DDS.

- joint_names: PASS
- action_order: PASS
- default_pose: PASS
- joint_limits: PASS
- effort_limits: PASS
- controller_assumption: PASS
- foot_name: PASS

Long training is blocked unless the model/order/limit checks pass and the SDK2 PD command path is proven by the MuJoCo DDS endpoint and LCM-to-DDS bridge reports.

### Unitree Mujoco Joint And Actuator Limits

- Source: `thirdparties/unitree_mujoco/unitree_robots/go2/go2.xml:7`

```text
    <default class="go2">
      <geom friction="0.4" margin="0.001" condim="1"/>
      <joint axis="0 1 0" damping="0.1" armature="0.01" frictionloss="0.2"/>
      <motor ctrlrange="-23.7 23.7"/>
      <default class="abduction">
        <joint axis="1 0 0" range="-1.0472 1.0472"/>
      </default>
      <default class="hip">
        <default class="front_hip">
          <joint range="-1.5708 3.4907"/>
        </default>
        <default class="back_hip">
          <joint range="-0.5236 4.5379"/>
        </default>
      </default>
      <default class="knee">
        <joint range="-2.7227 -0.83776"/>
        <motor ctrlrange="-45.43 45.43"/>
```

### Unitree Mujoco Motor Order

- Source: `thirdparties/unitree_mujoco/unitree_robots/go2/go2.xml:222`

```text
  <actuator>
    <motor class="abduction" name="FR_hip" joint="FR_hip_joint" />
    <motor class="hip" name="FR_thigh" joint="FR_thigh_joint" />
    <motor class="knee" name="FR_calf" joint="FR_calf_joint" />
    <motor class="abduction" name="FL_hip" joint="FL_hip_joint" />
    <motor class="hip" name="FL_thigh" joint="FL_thigh_joint" />
    <motor class="knee" name="FL_calf" joint="FL_calf_joint" />
    <motor class="abduction" name="RR_hip" joint="RR_hip_joint" />
    <motor class="hip" name="RR_thigh" joint="RR_thigh_joint" />
    <motor class="knee" name="RR_calf" joint="RR_calf_joint" />
    <motor class="abduction" name="RL_hip" joint="RL_hip_joint" />
    <motor class="hip" name="RL_thigh" joint="RL_thigh_joint" />
    <motor class="knee" name="RL_calf" joint="RL_calf_joint" />
```

### Unitree Mujoco Home Keyframe

- Source: `thirdparties/unitree_mujoco/unitree_robots/go2/go2.xml:286`

```text
    <key name="home" qpos="0 0 0.27 1 0 0 0 0 0.9 -1.8 0 0.9 -1.8 0 0.9 -1.8 0 0.9 -1.8"
      ctrl="0 0.9 -1.8 0 0.9 -1.8 0 0.9 -1.8 0 0.9 -1.8" />
  </keyframe>
```

### Unitree Mujoco Torque Equation

- Source: `thirdparties/unitree_mujoco/simulate/src/unitree_sdk2_bridge.h:178`

```text
        // lowcmd
        {
            std::lock_guard<std::mutex> lock(lowcmd->mutex_);
            for(int i(0); i<num_motor_; i++) {
                auto & m = lowcmd->msg_.motor_cmd()[i];
                mj_data_->ctrl[i] = m.tau() +
                                    m.kp() * (m.q() - mj_data_->sensordata[i]) +
                                    m.kd() * (m.dq() - mj_data_->sensordata[i + num_motor_]);
            }
```

### Isaacgym Go2 Default Pose And Control

- Source: `thirdparties/DrEureka/globe_walking/go1_gym/envs/go2/go2_config.py:21`

```text
def config_go2(Cnfg: Union[Cfg, Meta]):
    _ = Cnfg.init_state

    # Unitree MuJoCo Go2 home keyframe:
    # qpos joints are [hip, thigh, calf] * 4 with hip=0, thigh=0.9, calf=-1.8.
    _.default_joint_angles = {
        "FL_hip_joint": 0.0,
        "FL_thigh_joint": 0.9,
        "FL_calf_joint": -1.8,
        "FR_hip_joint": 0.0,
        "FR_thigh_joint": 0.9,
        "FR_calf_joint": -1.8,
        "RL_hip_joint": 0.0,
        "RL_thigh_joint": 0.9,
        "RL_calf_joint": -1.8,
        "RR_hip_joint": 0.0,
        "RR_thigh_joint": 0.9,
        "RR_calf_joint": -1.8,
    }

    _ = Cnfg.control
    _.control_type = "P"
    _.stiffness = {"hip": 20.0, "thigh": 20.0, "calf": 40.0}
    _.damping = {"hip": 1.0, "thigh": 1.0, "calf": 2.0}
    _.action_scale = 0.25
    _.hip_scale_reduction = 0.5
    _.decimation = 4
```

### Isaacgym Go2 Asset Path And Names

- Source: `thirdparties/DrEureka/globe_walking/go1_gym/envs/go2/go2_config.py:49`

```text
    _ = Cnfg.asset
    _.file = _go2_urdf_path()
    _.foot_name = "foot"
    _.penalize_contacts_on = ["thigh", "calf"]
    _.terminate_after_contacts_on = ["base"]
    _.self_collisions = 0
    _.flip_visual_attachments = False
    _.fix_base_link = False

    _ = Cnfg.rewards
    _.soft_dof_pos_limit = 0.9

    _ = Cnfg.terrain
```

### Isaacgym Go2 Robot Loader

- Source: `thirdparties/DrEureka/globe_walking/go1_gym/robots/go2.py:8`

```text
class Go2(Robot):
    def __init__(self, env):
        super().__init__(env)

    def initialize(self):
        asset_path = self.env.cfg.asset.file
        asset_root = os.path.dirname(asset_path)
        asset_file = os.path.basename(asset_path)

        asset_config = self.env.cfg.asset

        asset_options = gymapi.AssetOptions()
        asset_options.default_dof_drive_mode = asset_config.default_dof_drive_mode
        asset_options.collapse_fixed_joints = asset_config.collapse_fixed_joints
        asset_options.replace_cylinder_with_capsule = asset_config.replace_cylinder_with_capsule
        asset_options.flip_visual_attachments = asset_config.flip_visual_attachments
        asset_options.fix_base_link = asset_config.fix_base_link
        asset_options.density = asset_config.density
        asset_options.angular_damping = asset_config.angular_damping
        asset_options.linear_damping = asset_config.linear_damping
        asset_options.max_angular_velocity = asset_config.max_angular_velocity
        asset_options.max_linear_velocity = asset_config.max_linear_velocity
        asset_options.armature = asset_config.armature
        asset_options.thickness = asset_config.thickness
        asset_options.disable_gravity = asset_config.disable_gravity
        asset_options.vhacd_enabled = True
        asset_options.vhacd_params = gymapi.VhacdParams()
        asset_options.vhacd_params.resolution = 500000

        asset = self.env.gym.load_asset(self.env.sim, asset_root, asset_file, asset_options)

        self.num_dof = self.env.gym.get_asset_dof_count(asset)
        self.num_actuated_dof = 12
        self.num_bodies = self.env.gym.get_asset_rigid_body_count(asset)
        dof_props_asset = self.env.gym.get_asset_dof_properties(asset)
        rigid_shape_props_asset = self.env.gym.get_asset_rigid_shape_properties(asset)

        return asset, dof_props_asset, rigid_shape_props_asset
```

### Drek Train Robot Selector

- Source: `thirdparties/DrEureka/globe_walking/scripts/train.py:108`

```text
        Cfg.domain_rand = Cfg.domain_rand_off
        Cfg.sim.physx = Cfg.sim.physx_mini
    else:
        raise ValueError(f"Invalid dr_config: {dr_config}")

    robot_configs = {
        "go1": config_go1,
        "go2": config_go2,
    }
    if robot not in robot_configs:
        raise ValueError(f"Invalid robot: {robot}")
    robot_configs[robot](Cfg)
    apply_domain_rand_profile(Cfg, domain_rand_profile)
    if num_envs is not None:
        Cfg.env.num_envs = int(num_envs)
    Cfg.env.record_video = bool(record_video)

    if resume_path:
        RunnerArgs.resume = True
        RunnerArgs.load_run = resume_path
        RunnerArgs.resume_checkpoint = os.path.join(RunnerArgs.load_run, "checkpoints", "ac_weights_last.pt")

    Cfg.robot.name = robot

    Cfg.commands.num_lin_vel_bins = 30
    Cfg.commands.num_ang_vel_bins = 30
    Cfg.curriculum_thresholds.tracking_ang_vel = 0.7
    Cfg.curriculum_thresholds.tracking_lin_vel = 0.8
    Cfg.curriculum_thresholds.tracking_contacts_shaped_vel = 0.90
    Cfg.curriculum_thresholds.tracking_contacts_shaped_force = 0.90

    Cfg.commands.distributional_commands = True

    if robot == "go1":
        Cfg.control.control_type = "actuator_net"

```

### Drek Robot Registry

- Source: `thirdparties/DrEureka/globe_walking/go1_gym/envs/base/legged_robot.py:1380`

```text
        # create robot
        from globe_walking.go1_gym.robots.go1 import Go1
        from globe_walking.go1_gym.robots.go2 import Go2

        robot_classes = {
            'go1': Go1,
            'go2': Go2,
        }

        self.robot = robot_classes[self.cfg.robot.name](self)
        all_assets.append(self.robot)
```

