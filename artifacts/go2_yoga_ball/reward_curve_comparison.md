# Reward Curve Comparison

- pretrained log: `thirdparties/DrEureka/globe_walking/runs/globe_walking/dr_eureka_best/outputs.log`
- 1/8-budget train log: `thirdparties/DrEureka/globe_walking/runs/globe_walking/2026-05-25/train/235148.012034/outputs.log`
- CSV: `artifacts/go2_yoga_ball/reward_curve_comparison.csv`
- SVG: `artifacts/go2_yoga_ball/reward_curve_total.svg`

## Final Points

- pretrained final: `{'iteration': 19990.0, 'timesteps': 15721562112.0, 'elapsed_s': 60804.434, 'total': 1192.482, 'success': 558.73, 'episode_length': 560.255}`
- 1/8-budget train final: `{'iteration': 19990.0, 'timesteps': 1965195264.0, 'elapsed_s': 39755.204, 'total': 270.346, 'success': 0.0, 'episode_length': 171.005}`
- pretrained nearest same global timesteps: `{'iteration': 2500.0, 'timesteps': 1966866432.0, 'elapsed_s': 13231.912, 'total': 263.379, 'success': 146.553, 'episode_length': 146.824}`

## Ratios

- final timestep ratio pretrained/train: `8.0`
- final total reward train / pretrained at same global timesteps: `1.0264523747147647`
- best total reward train / pretrained best: `0.19648987275296956`

## Interpretation

The current selected Go1 retrain is treated as 1/8-budget because the pretrained log records exactly 8x more global timesteps at the same nominal 20k iterations.
