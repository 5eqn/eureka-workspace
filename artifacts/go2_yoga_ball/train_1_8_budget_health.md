# Go2 1/8-Budget Training Health

- Status: FAIL
- Container: `7ce1c1f64cc471fce043b09dd983cf1a1efbaf9cc0815128c830a8d0895ff9a9`
- Monitor duration: `0.064` seconds
- Container runtime: `22.402` seconds
- Docker running at end: `False`
- Docker exit code: `139`
- Log: `logs/go2_yoga_ball/train_1_8_budget/train.log`
- Log advanced during monitor: `False`
- Last logged iteration: `1500`
- Last logged timesteps: `None`
- Last total reward: `None`
- Contains NaN text: `False`
- Contains segfault text: `True`
- Selected run: `thirdparties/DrEureka/globe_walking/runs/globe_walking/2026-05-27/train/034559.754542`

This report is a five-minute health gate only. A passing run is expected to remain alive after the goal completes.
The launch used the requested `--iterations` value; the `RunnerArgs.max_iterations` table row printed by DrEureka is static config, not the loop bound passed to `runner.learn`.
