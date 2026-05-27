# Go1 Yoga-Ball Default DrEureka Training Report

Generated: 2026-05-27 08:05:08 +0800

## Phase Gate

- ok: `False`
- status: `not_equivalent_yet`
- selected run: `thirdparties/DrEureka/globe_walking/runs/globe_walking/2026-05-25/train/235148.012034`
- Isaac Gym playback ok: `True`
- MuJoCo smoke ok: `False`
- MuJoCo target-duration ok: `False`
- release_window_s: `21.07`

## Training Run

- run record: `artifacts/go1_yoga_ball/default_train_run.json`
- selected run exists: `True`
- env num envs: `4096`
- env num observations: `56`
- history length: `15`
- control dt: `0.02`

## Isaac Gym Playback

- ok: `True`
- iterations: `1000/1000`
- GPU PhysX: `True`
- raw log: `logs/go1_yoga_ball/default_train/isaacgym_playback/play_default_train_isaacgym.log`

## MuJoCo Sim2Sim

- smoke ok: `False`
- target duration ok: `False`
- missing events: `[]`
- release_window_s: `21.07`
- sim_wall_ratio: `0.9999887947168625`
- policy_time_wall_ratio: `0.9915965599870248`
- released_base_height: `{'below_threshold_fraction': 0.0, 'below_threshold_samples': 0, 'min': 0.903801342, 'ok': True, 'samples': 1054, 'threshold': 0.9}`
- joint_limit_summary_released: `{'criterion': 'pass if zero violations, or violation_frames / joint_frames < 0.001 and no joint violation persists longer than 0.1s', 'first_violations': [{'joint': 'FR_calf_joint', 'limit_high': -0.916298, 'limit_low': -2.69653, 'magnitude_rad': 0.2003567839999999, 'q': -0.715941216, 'sim_time_s': 0.94}, {'joint': 'RL_calf_joint', 'limit_high': -0.916298, 'limit_low': -2.69653, 'magnitude_rad': 0.13398808100000004, 'q': -2.830518081, 'sim_time_s': 1.34}, {'joint': 'RL_calf_joint', 'limit_high': -0.916298, 'limit_low': -2.69653, 'magnitude_rad': 0.10237010899999976, 'q': -2.798900109, 'sim_time_s': 1.36}, {'joint': 'RL_calf_joint', 'limit_high': -0.916298, 'limit_low': -2.69653, 'magnitude_rad': 0.06799143499999971, 'q': -2.764521435, 'sim_time_s': 1.66}, {'joint': 'RL_calf_joint', 'limit_high': -0.916298, 'limit_low': -2.69653, 'magnitude_rad': 0.05249528799999981, 'q': -2.749025288, 'sim_time_s': 1.68}, {'joint': 'RL_calf_joint', 'limit_high': -0.916298, 'limit_low': -2.69653, 'magnitude_rad': 0.02213130899999971, 'q': -2.718661309, 'sim_time_s': 3.44}, {'joint': 'RL_calf_joint', 'limit_high': -0.916298, 'limit_low': -2.69653, 'magnitude_rad': 0.017540875999999983, 'q': -2.714070876, 'sim_time_s': 3.46}, {'joint': 'RR_calf_joint', 'limit_high': -0.916298, 'limit_low': -2.69653, 'magnitude_rad': 0.031939594999999876, 'q': -2.728469595, 'sim_time_s': 4.44}, {'joint': 'RL_calf_joint', 'limit_high': -0.916298, 'limit_low': -2.69653, 'magnitude_rad': 0.036009468000000044, 'q': -2.732539468, 'sim_time_s': 4.64}, {'joint': 'RL_calf_joint', 'limit_high': -0.916298, 'limit_low': -2.69653, 'magnitude_rad': 0.027987804999999977, 'q': -2.724517805, 'sim_time_s': 4.66}], 'joint_frames': 12648, 'max_contiguous_duration_s': 0.06, 'max_contiguous_frames': 3, 'max_magnitude_rad': 0.2003567839999999, 'passes_numerical_margin_rule': False, 'per_joint_counts': {'FR_calf_joint': 1, 'RL_calf_joint': 22, 'RR_calf_joint': 1}, 'per_joint_max_magnitude_rad': {'FR_calf_joint': 0.2003567839999999, 'RL_calf_joint': 0.13398808100000004, 'RR_calf_joint': 0.031939594999999876}, 'samples': 1054, 'violation_fraction': 0.0018975332068311196, 'violation_frames': 24}`
- raw logs: `{'events': 'logs/go1_yoga_ball/default_train/mujoco_sim2sim/sequence_events.csv', 'policy_timing': 'logs/go1_yoga_ball/default_train/mujoco_sim2sim/policy_timing.csv', 'replay': 'logs/go1_yoga_ball/default_train/mujoco_sim2sim/replay.csv', 'sim_bridge_summary': 'logs/go1_yoga_ball/default_train/mujoco_sim2sim/sim_bridge_summary.json', 'simulator_status': 'logs/go1_yoga_ball/default_train/mujoco_sim2sim/simulator_status.csv'}`

## Config Comparison Against Pretrained

- comparison artifact: `artifacts/go1_yoga_ball/default_train_config_comparison.json`
- differing fields: `1`
- multi_gpu: pretrained=`True`, default_train=`False`

## Interpretation

The current selected default DrEureka policy is validated in built-in Isaac Gym playback.
MuJoCo Sim2Sim is not equivalent yet; observed failure evidence: released-control window `21.07` seconds, released joint-limit violations `24` frames.
