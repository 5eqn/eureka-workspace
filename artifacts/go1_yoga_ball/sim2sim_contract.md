# Go1 Yoga-Ball Sim2Sim Contract

## Policy Side

The final DrEureka MuJoCo Sim2Sim path must run the policy through the DrEureka deployment stack:

- `thirdparties/DrEureka/globe_walking/go1_gym_deploy/scripts/deploy_policy.py`
- TorchScript modules from a run directory's `checkpoints/body_latest.jit` and `checkpoints/adaptation_module_latest.jit`

## Transport

Use the same LCM channels as real Go1 deployment:

- Policy consumes `state_estimator_data`, `leg_control_data`, and `rc_command`.
- Policy publishes `pd_plustau_targets`.

Real robot deployment uses `lcm_position.cpp` to bridge Unitree low-level UDP to these LCM channels. MuJoCo Sim2Sim should replace only that bridge, not the policy process.

## Joint Order

DrEureka policy order:

```text
FL_hip_joint, FL_thigh_joint, FL_calf_joint,
FR_hip_joint, FR_thigh_joint, FR_calf_joint,
RL_hip_joint, RL_thigh_joint, RL_calf_joint,
RR_hip_joint, RR_thigh_joint, RR_calf_joint
```

The deployment `StateEstimator` reorders hardware state with `joint_idxs = [3, 4, 5, 0, 1, 2, 9, 10, 11, 6, 7, 8]`. A MuJoCo bridge must preserve the same semantics observed by `LCMAgent`.

## Timing

The pretrained DrEureka deployment script uses `control_dt = 0.02` seconds. Sim2Sim must report wall time, simulation time, policy loop time, control jitter, and inference latency.

## Startup And Release

Support is allowed only to emulate the real robot being hung up while the controller and policy start. The simulator must prove support release after policy control is active and must prove unpinned root dynamics after release.
