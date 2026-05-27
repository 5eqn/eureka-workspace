# Go1 Yoga-Ball Pretrained Policy Report

Generated: 2026-05-25 13:54:01 +0800

## Phase Gate

- ok: `True`
- Isaac Gym playback ok: `True`
- MuJoCo target-duration run ok: `True`
- MuJoCo repeated starts ok: `True`
- MuJoCo control-removal proof ok: `True`
- MuJoCo raw-replay video ok: `True`
- caveat: Isaac Gym playback was validated headless without video because graphics-enabled headless playback is unstable in this Docker/runtime path.

## Dependency Status

- DrEureka: present (`thirdparties/DrEureka`)
- IsaacGym: present (`thirdparties/IsaacGym`)
- MJLab: present (`thirdparties/MJLab`)
- wbc-unitree_mujoco: present (`thirdparties/wbc-workspace/thirdparties/unitree_mujoco`)
- wbc-workspace: present (`thirdparties/wbc-workspace`)

## Policy Registry

- dr_eureka_best_pretrained: `thirdparties/DrEureka/globe_walking/runs/globe_walking/dr_eureka_best`

## Docker Images

- isaacgym: built (`go1-yoga-ball-isaacgym`)
- mjlab: missing (`go1-yoga-ball-mjlab`)
- mujoco_sim2sim: built (`go1-yoga-ball-mujoco_sim2sim`)

## MuJoCo Asset Smoke

- ok: `True`
- model dimensions: nq=19, nv=18, nu=12
- sanitized model: `artifacts/go1_yoga_ball/build/go1_sanitized.xml`

## Release Validation Smoke

- ok: `True`
- kind: `direct_release_no_control`
- fall_time_s: `2.9079999999999013`
- raw_log: `logs/go1_yoga_ball/pretrained/mujoco_sim2sim/direct_release_smoke.csv`
- active_policy_release_ok: `True`
- active_policy_release_window_s: `21.09`
- control_removal_ok: `True`
- stable_before_control_removal_s: `5.002`
- fall_after_control_removal_s: `0.8440000000000003`

## Pretrained Isaac Gym Playback

- ok: `True`
- iterations: `1000/1000`
- GPU PhysX: `True`
- graphics disabled: `True`
- raw_log: `logs/go1_yoga_ball/pretrained/isaacgym_playback/play_pretrained_isaacgym.log`

## Pretrained MuJoCo Sim2Sim Target Run

- smoke ok: `True`
- target duration ok: `True`
- release_window_s: `21.09`
- sim_wall_ratio: `0.9999848525058365`
- policy_time_wall_ratio: `0.9934046294291713`
- policy_loop_period_s: `{'max': 0.021678654, 'mean': 0.020088254173833486, 'p95': 0.020233931}`
- released_base_height: `{'below_threshold_fraction': 0.0, 'below_threshold_samples': 0, 'min': 0.903498407, 'ok': True, 'samples': 1055, 'threshold': 0.9}`
- joint_limit_violation_frames_released: `0`
- joint_limit_max_magnitude_rad: `0.0`

## Pretrained MuJoCo Repeated Starts

- ok: `True`
- clean_target_duration_runs: `3/3`
- run 1: ok=`True`, release_window_s=`21.124`, min_height=`0.900835366`, joint_violations=`0`, sim_wall_ratio=`0.9999852580794034`
- run 2: ok=`True`, release_window_s=`21.094`, min_height=`0.906009156`, joint_violations=`0`, sim_wall_ratio=`0.9999852414007548`
- run 3: ok=`True`, release_window_s=`21.09`, min_height=`0.903498407`, joint_violations=`0`, sim_wall_ratio=`0.9999848525058365`

## Pretrained MuJoCo Control Removal

- ok: `True`
- stable_released_control_before_removal_s: `5.002`
- fall_after_control_removal_s: `0.8440000000000003`
- direct_release_fall_time_s: `2.9079999999999013`
- raw_events: `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_control_removal/sequence_events.csv`

## Pretrained MuJoCo Video

- ok: `True`
- video: `artifacts/go1_yoga_ball/videos/pretrained_mujoco.mp4`
- rendered_from_raw_replay: `True`
- frames_written: `551`

## Next Step

Phase 1 pretrained policy validation is now strong enough to proceed to Phase 2 default DrEureka training. Remaining caveat: Isaac Gym playback was validated headless without video to avoid graphics instability; MuJoCo Sim2Sim has raw-log-rendered video evidence.
