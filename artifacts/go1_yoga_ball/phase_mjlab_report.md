# Go1 Yoga-Ball MJLab Port Report

Generated: 2026-05-25 18:58:39 +0800

## Phase Gate

- ok: `False`
- status: `task_port_smoke_only`
- MJLab dependency present: `True`
- MJLab Docker image present: `True`
- MJLab runtime smoke ok: `True`
- MJLab yoga-ball task smoke ok: `True`
- MJLab yoga-ball training smoke ok: `True`
- task port complete: `False`
- training complete: `False`
- default playback complete: `False`
- MuJoCo Sim2Sim complete: `False`

## Runtime Smoke

- artifact: `artifacts/go1_yoga_ball/mjlab_runtime_smoke.json`
- ok: `True`
- stage: `step`
- task: `Mjlab-Velocity-Flat-Unitree-Go1`
- device: `cuda:0`
- steps: `25`
- env_step_dt_s: `0.02`
- sim_wall_ratio: `2.086522183192247`
- raw_log: `logs/go1_yoga_ball/mjlab_train/default_playback/mjlab_builtin_go1_zero_policy_smoke.csv`

## Yoga-Ball Task Smoke

- artifact: `artifacts/go1_yoga_ball/mjlab_yoga_ball_task_smoke.json`
- ok: `True`
- stage: `step`
- task: `Mjlab-Go1-YogaBall-PortSmoke`
- device: `cuda:0`
- steps: `50`
- actor observation shape: `[1, 57]`
- min base minus ball z: `0.5044856667518616`
- raw_log: `logs/go1_yoga_ball/mjlab_train/default_playback/mjlab_yoga_ball_task_smoke.csv`

## Yoga-Ball Training Smoke

- artifact: `artifacts/go1_yoga_ball/mjlab_yoga_ball_train_smoke.json`
- ok: `True`
- stage: `train`
- task: `Mjlab-Go1-YogaBall-PortSmoke`
- iterations: `1`
- num_envs: `8`
- num_steps_per_env: `4`
- selected run: `logs/go1_yoga_ball/mjlab_train/train/rsl_rl/go1_yoga_ball_port_smoke/2026-05-25_10-57-55_train_smoke`
- checkpoints: `['logs/go1_yoga_ball/mjlab_train/train/rsl_rl/go1_yoga_ball_port_smoke/2026-05-25_10-57-55_train_smoke/model_0.pt']`

## Port Strategy

Use MJLab as an installed dependency inside `go1-yoga-ball-mjlab`. Keep the yoga-ball task adapter root-owned until the API boundary is clear, then register it at runtime through MJLab's task registry. Start from MJLab's built-in Go1 velocity task only for robot/entity/action patterns; do not treat the flat-ground velocity task as yoga-ball evidence.

The next required increment is a minimal registered MJLab yoga-ball task with a dynamic sphere, Go1 reset on the ball, DrEureka-compatible action timing, and raw default-playback logs. Only after that should training be scaled.
