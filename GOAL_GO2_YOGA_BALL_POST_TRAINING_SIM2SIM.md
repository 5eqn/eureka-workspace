# Goal: Go2 Yoga-Ball Post-Training Sim2Sim Verification

## Outcome

After the running Go2 1/8-budget Isaac Gym training ends, validate the resulting Go2 yoga-ball policy in MuJoCo Sim2Sim with the same behavioral contract as the Go1 Sim2Sim, plus the Go2 real-swap contract.

The target production vision is that the MuJoCo simulator container can be replaced by a real Go2 robot endpoint, while the policy/deploy side remains responsible for translating DrEureka LCM policy messages into Unitree SDK2 DDS. Both Claude Opus 4.6 and human embodied-intelligence reviewers should be able to inspect the artifacts and agree that the result either passes Sim2Sim or fails for a defensible reason, not because the test skipped release behavior, timing, joint limits, or the LCM-to-DDS boundary.

## Current Training Estimate

Current resumed training source:

- Container: `a3c66aa5304d` / `eureka-go2-train-1-8-resume-20260527-173817`
- Resume launch metadata: `artifacts/go2_yoga_ball/train_1_8_budget_resume_launch.json`
- Resume log: `logs/go2_yoga_ball/train_1_8_budget_resume/train.log`
- Resume checkpoint loaded: `thirdparties/DrEureka/globe_walking/runs/globe_walking/2026-05-27/train/044311.018107/checkpoints/ac_weights_004000.pt`
- Resume iterations requested: `16000`, approximating `4000 + 16000 = 20000` total policy-weight training iterations.

At `2026-05-27 18:13:43 CST`, the latest observed resumed iteration was `930/16000` with `time iter/mean ~= 1.94s`. Estimated remaining time was about `8.1h`, so the expected finish window starts around `2026-05-28 02:20 CST`. The scheduler is allowed to poll and defer if the container is still running.

## Boundaries

- Do not launch another long training run.
- Use the final/latest checkpoint or exported JIT policy from the current resumed training run.
- All major Sim2Sim logic must run inside Docker containers.
- Heavy dependencies stay under `thirdparties/`.
- The Unitree MuJoCo Go2 endpoint is the source of truth for the real-swappable simulator side.
- The Go2 policy/deploy side owns the LCM-to-DDS translation through `scripts/go2_yoga_ball/lcm_to_dds_bridge.py`.
- The simulator endpoint must remain directly swappable to a real Go2 endpoint: no DrEureka LCM logic inside the simulator endpoint.

## Verification Surface

Create this concrete artifact tree:

```text
artifacts/go2_yoga_ball/post_training_sim2sim/
  training_completion.json
  selected_policy.json
  sim2sim_attempts.json
  sim2sim_report.md
  sim2sim_report.json
  release_timing_report.md
  release_timing_report.json
  lcm_to_dds_runtime_report.md
  lcm_to_dds_runtime_report.json
  joint_limit_report.md
  joint_limit_report.json
  wall_clock_report.md
  wall_clock_report.json
  videos/
    go2_post_training_sim2sim_follow_camera.mp4
logs/go2_yoga_ball/post_training_sim2sim/
  attempt_*/
    mujoco_dds_endpoint.log
    lcm_to_dds_bridge.log
    policy_deploy.log
    events.csv
    telemetry.csv
    commands.csv
    lowstate.csv
    summary.json
```

The markdown reports must include the command lines used, container IDs/names, selected checkpoint path, selected run directory, and relevant source file/line references for any code paths relied on for release ordering, timing, LCM-to-DDS mapping, and Go2 DDS endpoint behavior.

## Required Checks

1. Training completion
   - Record whether the resumed container exited cleanly.
   - Parse the latest `iterations`, `time iter/mean`, total reward, episode length, NaN/traceback status, and final checkpoint/exported policy paths.
   - If the container died before producing a usable policy, write the failure report and stop.

2. Policy selection
   - Select the latest usable final checkpoint or JIT policy from the resumed run.
   - Record why it was selected.
   - Do not silently fall back to an unrelated Go1 or pretrained Go1 policy.

3. Real-swappable Go2 Sim2Sim boundary
   - Start the Unitree MuJoCo Go2 DDS endpoint as the simulator side.
   - Start the DrEureka policy/deploy process.
   - Start the Go2 LCM-to-DDS bridge.
   - Prove from runtime logs that the policy path communicates over LCM internally, the bridge publishes `rt/lowcmd`, the simulator publishes `rt/lowstate`, and the bridge republishes state back to DrEureka LCM.
   - This must exercise `scripts/go2_yoga_ball/lcm_to_dds_bridge.py`; bypassing it does not satisfy the goal.

4. Release behavior
   - Prove policy/control is active before release.
   - Prove release is requested and confirmed before motion/playback evaluation starts.
   - Prove the robot is actually released, not still held by support, while the policy is running.
   - Include event timestamps for policy-start, first command, first lowstate, bridge-active, release-requested, release-confirmed, evaluation-start, fall/end.

5. Timing
   - Prove sim time, policy/control time, and wall time are consistent.
   - The Sim2Sim run must not be lagging behind wall clock in a way that invalidates the behavior.
   - Report control-loop interval stats, inference latency stats, DDS/LCM bridge update stats, sim-time elapsed, and wall-time elapsed.

6. Behavior
   - Primary target: run released for at least `20s`.
   - Minimum acceptable diagnostic target: any released run between `5s` and `20s` can be used to debug, but it is not a strong pass unless the report explains why `20s` is unreasonable for the trained checkpoint.
   - Expected healthy result: no or very few joint-limit violations and base height stays above the fall threshold.
   - Report joint-limit violation count/rate per joint and base-height minimum/mean after release.

7. Human-verifiable media
   - Generate a follow-camera video for the best attempt.
   - Mark release time and joint-limit violation intervals in the video or in a sidecar timeline that clearly maps to video time.

## Iteration Policy

Make bounded, evidence-driven attempts to pass Sim2Sim:

- First validate wiring with a short DDS endpoint + bridge + policy smoke run.
- If no commands arrive, debug the policy export/deploy selection and LCM channel setup.
- If no DDS state arrives, debug the Unitree MuJoCo endpoint and bridge DDS domain/interface.
- If release ordering is wrong, fix orchestration before judging policy quality.
- If timing lags, reduce rendering overhead, run headless, or split video rendering from logged replay.
- If the robot falls immediately after release while wiring, timing, and release are proven correct, compare Isaac Gym Go2 model/actuator assumptions against the existing fidelity reports before suspecting policy quality.

## Stop Conditions

Stop and write `sim2sim_report.md` with a clear failure verdict when any of these hold:

- The training run ended without a usable Go2 checkpoint or policy export.
- The Unitree MuJoCo Go2 DDS endpoint cannot be started after concrete Docker/dependency fixes.
- The LCM-to-DDS bridge cannot exchange both commands and state after concrete DDS domain/interface and LCM URL fixes.
- Release-before-motion cannot be proven from logs.
- Three reasonable Sim2Sim attempts still fail after wiring, release order, and timing are proven correct; in that case report that the trained policy is suspected wrong, with likely causes such as Isaac Gym Go2 model mismatch, actuator/controller mismatch, or inadequate training quality.

## Scheduler

The scheduler entrypoint is:

```bash
scripts/go2_yoga_ball/start_post_training_sim2sim_goal.sh
```

It must check the running training container before starting Codex. If training is still running, it must defer. Once training has stopped, it should launch a non-interactive Codex agent in `/home/seqn/eureka-workspace` and ask it to execute this goal.
