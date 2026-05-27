# Go2 1/8-Budget Training Health

- Status: FAIL
- Container: `32c9e4edf186534f9ef64cbb33d08f855e832689c83fb4c089895f93eaf6ea87`
- Monitor duration: `31.13` seconds
- Container runtime: `21.754` seconds
- Docker running at end: `False`
- Docker exit code: `139`
- Log: `logs/go2_yoga_ball/train_1_8_budget/train.log`
- Log advanced during monitor: `True`
- Last logged iteration: `1500`
- Last logged timesteps: `None`
- Last total reward: `None`
- Contains NaN text: `False`
- Contains segfault text: `True`
- Selected run: `thirdparties/DrEureka/globe_walking/runs/globe_walking/2026-05-27/train/043005.243837`

This report is a five-minute health gate only. A passing run is expected to remain alive after the goal completes.
The launch used the requested `--iterations` value; the `RunnerArgs.max_iterations` table row printed by DrEureka is static config, not the loop bound passed to `runner.learn`.
