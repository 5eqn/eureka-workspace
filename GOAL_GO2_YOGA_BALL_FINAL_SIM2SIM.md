# Goal: Go2 Corrected 1/8 Checkpoint Sim2Sim

## Outcome

Run MuJoCo/DDS Sim2Sim for the corrected Go2 1/8 trained checkpoint:

`thirdparties/DrEureka/globe_walking/runs/globe_walking/2026-05-28/train/063234.884668/checkpoints/ac_weights_last.pt`

The work is done when the repository contains a current evidence set showing either:

- success: the Go2 policy runs through the Unitree MuJoCo Go2 DDS endpoint, releases before motion, receives and sends live commands, keeps sim/policy/wall time consistent, and produces a follow-camera video; or
- best-effort failure: three distinct attempts were made, the most likely failing subsystem is identified from logs, and a follow-camera video is generated for the final failed attempt.

## Verification Surface

Write final evidence under:

```text
artifacts/go2_yoga_ball/final_train_sim2sim/
logs/go2_yoga_ball/final_train_sim2sim/
```

Required files:

- `artifacts/go2_yoga_ball/final_train_sim2sim/report.md`
- `artifacts/go2_yoga_ball/final_train_sim2sim/summary.json`
- one video under `artifacts/go2_yoga_ball/final_train_sim2sim/videos/`
- per-attempt logs under `logs/go2_yoga_ball/final_train_sim2sim/attempt_*`

Each attempt must record process logs, event logs, policy timing, bridge command/lowstate logs, MuJoCo telemetry, MuJoCo replay CSV, and a summary.

## Constraints

- Use the corrected 2026-05-28 Go2 1/8 training run, not archived 2026-05-27 wrong-model runs.
- Run major logic inside Docker containers.
- Preserve the real-swappable boundary: MuJoCo Go2 DDS endpoint is the simulator side; LCM-to-DDS conversion stays on the policy/deploy side.
- Do not start new training.
- Do not move failed attempts into `outdated/` during this goal; they are current evidence for this goal until a final conclusion is written.

## Iteration Policy

Attempt up to three distinct runs:

1. faithful baseline using current Go2 DDS endpoint and bridge settings;
2. a targeted fix based on attempt 1 logs;
3. a final targeted fix based on attempt 2 logs.

After each attempt, inspect release events, command counts, timing ratio, fall time, torque clipping, joint-limit rows, and policy action magnitude before choosing the next change.

## Stop Condition

Stop after a successful Sim2Sim run, or after three distinct failed attempts with a defensible root-cause report and a rendered follow-camera video for the final attempt.
