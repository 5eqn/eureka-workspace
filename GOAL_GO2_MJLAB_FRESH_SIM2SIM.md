# Goal: Go2 MJLab Checkpoint FRESH Sim2Sim

## Outcome

Run host-side MuJoCo/DDS Sim2Sim for the completed MJLab Go2 checkpoint using the FRESH environment, with no Docker containers in the runtime path.

Primary checkpoint:

`logs/go2_mjlab_dreureka_port/train_1_8_budget/rsl_rl/model_19999.pt`

The first target is plain Go2 movement in MuJoCo through the Unitree DDS boundary. Do not change policy behavior, reward logic, observation semantics, action scaling, PD gains, or simulator-side command semantics to make the result look better. Move the already proven pure-DDS Dockerized MuJoCo Sim2Sim runtime to host, and add only the deployment adapter needed for an MJLab/RSL-RL checkpoint to publish directly to DDS.

Both Claude Opus 4.6 and human experts in embodied intelligence should be able to review the source contract, joint-order proof, raw DDS logs, timing logs, replay, and video and agree that the MJLab checkpoint is being tested through a real-swappable Go2 DDS deployment path, not through a convenient training-only playback path.

## Current Result To Build From

- MJLab 1/8-budget train finished at iteration 19999 with final checkpoint `logs/go2_mjlab_dreureka_port/train_1_8_budget/rsl_rl/model_19999.pt`.
- Generated MJLab health artifacts show the run reached final iteration, had finite/nonzero scalar rewards, and had no traceback or NaN text.
- The health report currently marks `FAIL` only because `curve_points` is false: TensorBoard extraction produced 10000 curve rows rather than the report threshold. This is a reporting gate issue to inspect, not evidence that training crashed.
- Prior Go2 Dockerized Sim2Sim succeeded on attempt 1 through the Unitree DDS endpoint, with release, timing, command, torque, telemetry, replay, and video evidence under `artifacts/go2_yoga_ball/final_train_sim2sim/` and `logs/go2_yoga_ball/final_train_sim2sim/attempt_001_faithful_baseline/`.

## Verification Surface

All new runnable inputs must live under:

```text
scripts/go2_mjlab_fresh_sim2sim/
```

Runtime evidence must be written under:

```text
artifacts/go2_mjlab_fresh_sim2sim/
├── source_contract.json
├── source_contract.md
├── joint_order_contract.json
├── joint_order_contract.md
├── deployer_smoke.json
├── deployer_smoke.md
├── report.md
├── summary.json
└── videos/
    └── go2_mjlab_fresh_sim2sim_attempt_*.mp4

logs/go2_mjlab_fresh_sim2sim/
└── attempt_*/
    ├── mjlab_dds_deployer.log
    ├── mujoco_dds_endpoint.log
    ├── process_status.json
    ├── events.csv
    ├── deployer_timing.csv
    ├── commands.csv
    ├── lowstate.csv
    ├── telemetry.csv
    ├── replay.csv
    └── summary.json
```

The final report must state clearly whether the checkpoint passed plain-movement Sim2Sim or failed after three attempts, and it must name the most likely failing subsystem if it fails.

## Constraints

- Use FRESH: host conda environment and project-agnostic home-space upstream dependencies. Do not use Docker for this goal.
- Do not modify `/home/seqn/MJLab`, `/home/seqn/unitree_rl_mjlab`, or `thirdparties/DrEureka`.
- Do not start new training.
- Do not tune policy outputs, reward terms, PPO settings, observation history, action scale, PD gains, default joint angles, or termination logic for Sim2Sim performance.
- Preserve the real-swappable boundary: MuJoCo is only the Unitree Go2 DDS endpoint; the MJLab deployer owns policy inference and DDS `LowCmd` publication.
- Prefer a direct MJLab-to-DDS deployer over the old DrEureka LCM-to-DDS bridge. LCM may be used only as a diagnostic fallback, not as the primary target.
- Keep the pure-DDS MuJoCo endpoint logic behaviorally unchanged when moving it from Docker to host. Changes are limited to FRESH imports, paths, launch orchestration, and evidence output.
- Keep workspace inventory synchronized whenever files are added, moved, removed, or repurposed.

## Joint Order Requirements

Joint order is a blocker-level issue. Before any balancing or movement result can be trusted, write and pass `joint_order_contract.{json,md}` proving:

- Unitree SDK2 DDS motor order is:
  `FR_hip_joint, FR_thigh_joint, FR_calf_joint, FL_hip_joint, FL_thigh_joint, FL_calf_joint, RR_hip_joint, RR_thigh_joint, RR_calf_joint, RL_hip_joint, RL_thigh_joint, RL_calf_joint`.
- MJLab policy action order and observation joint order are discovered from the loaded MJLab environment/checkpoint at runtime, not assumed from comments.
- The deployer maps MJLab policy outputs to Unitree DDS motor indices by joint name.
- DDS `LowState` joint positions/velocities are mapped back into the exact MJLab observation/action state order expected by the policy.
- A zero-action/default-pose smoke shows each named joint's desired position in both MJLab order and Unitree DDS order, with mismatches called out explicitly.

If the order cannot be proven by executable inspection of the MJLab environment and Unitree model, stop before running Sim2Sim and report blocked.

## Plan

1. Inspect and record the completed MJLab train.
   - Verify: `artifacts/go2_mjlab_dreureka_port/train_1_8_budget_health.{json,md}` and the final checkpoint exist; document the `curve_points` threshold issue without treating it as a training crash.

2. Create the FRESH Sim2Sim caller workflow.
   - Verify: `scripts/go2_mjlab_fresh_sim2sim/run.sh preflight` checks the `go2-mjlab` conda environment, MJLab imports, Unitree SDK2 Python imports, MuJoCo imports, and host DDS interface availability.

3. Move the pure-DDS MuJoCo endpoint to host without behavioral changes.
   - Verify: endpoint smoke publishes `rt/lowstate`, subscribes to `rt/lowcmd`, writes `lowstate.csv`, `commands.csv`, `telemetry.csv`, `events.csv`, and exits cleanly without Docker.

4. Add the direct MJLab DDS deployer.
   - Verify: `deployer_smoke.{json,md}` loads `model_19999.pt`, constructs the MJLab policy runner, performs one deterministic inference step from a synthetic/default lowstate, maps action outputs by joint name into DDS `LowCmd`, records loop/inference timing, and proves the emitted `LowCmd` fields are finite.

5. Prove joint order before motion.
   - Verify: `joint_order_contract.{json,md}` names MJLab action order, MJLab observation joint order, Unitree DDS order, MuJoCo actuator order, and the explicit permutation tables in both directions.

6. Run up to three plain-movement Sim2Sim attempts.
   - Verify per attempt: live DDS lowstate/lowcmd counts, command activation before support release, wall-clock-consistent timing, no process crash, replay CSV, telemetry CSV, and rendered follow-camera video.

7. Write the final report.
   - Verify: `summary.json` contains pass/fail, attempts used, checkpoint path, joint-order contract hash or path, command counts, timing stats, base-height range, fall detection, torque clip counts, replay path, and video path.

## Iteration Policy

Attempt up to three distinct runs:

1. faithful FRESH host port of the successful Dockerized pure-DDS MuJoCo endpoint plus direct MJLab DDS deployer;
2. one targeted fix based on logs from attempt 1;
3. one final targeted fix based on logs from attempt 2.

After each attempt, inspect joint-order evidence, command counts, first-command timing, release timing, fall timing, base height, torque clipping, joint-limit rows, policy action magnitude, deployer timing, and process exit status before choosing the next change.

Do not adjust behavior parameters to compensate for bad movement until the deployment contract is proven. If plain movement fails with correct DDS wiring and correct joint order, report the policy/simulator behavior honestly.

## Blocked Stop Condition

Stop and report blocked if any of these are true:

- host DDS cannot be made to run in FRESH without patching upstream dependencies;
- MJLab checkpoint inference cannot be loaded outside training without patching MJLab or unitree_rl_mjlab;
- joint order cannot be proven from executable runtime state;
- direct DDS deployment requires changing the policy logic rather than adding an adapter;
- three attempts fail and the logs point to a reproducible subsystem failure with no defensible caller-project-only fix.
