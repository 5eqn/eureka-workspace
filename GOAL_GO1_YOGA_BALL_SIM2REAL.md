# Goal: Go1 Yoga-Ball Sim2Real Validation And Training

## Outcome

Build a reproducible pipeline for the DrEureka Go1 yoga-ball task that proves three policies are functionally equivalent across training and deployment surfaces:

1. The pre-existing DrEureka globe-walking policy works in the built-in Isaac Gym playback and in MuJoCo Sim2Sim.
2. A freshly trained policy from the default DrEureka Isaac Gym training setup reaches equivalent behavior and passes the same built-in playback and MuJoCo Sim2Sim checks.
3. An MJLab-trained equivalent policy reaches equivalent behavior and passes the same default playback and MuJoCo Sim2Sim checks.

The final evidence must be strong enough for Claude Opus 4.6 and human embodied-intelligence experts to review without relying on console claims. Raw logs, reports, and videos should show what actually happened.

## Repositories And Dependencies

- DrEureka lives at `thirdparties/DrEureka`.
- MuJoCo Sim2Sim implementation may use `thirdparties/wbc-workspace` as reference material, especially its simulator bridge, release proof, wall-clock timing checks, report layout, and video/report workflow.
- Isaac Gym must be treated as a fetched dependency, not a host precondition. Store the extracted NVIDIA Isaac Gym Preview 4 package under `thirdparties/IsaacGym/` or `thirdparties/isaacgym/`, then install/use it inside the Isaac Gym Docker image.
- MJLab must be treated as a fetched simulator/training dependency, analogous to how DrEureka depends on Isaac Gym. Store the `https://github.com/mujocolab/mjlab.git` checkout under `thirdparties/MJLab/`. It should not be vendored into project scripts or reimplemented casually.
- Heavy dependencies must live under `thirdparties/` as source checkouts or inside Docker images built from those checkouts. Use proper upstream/base Docker images for CUDA, PyTorch, MuJoCo, Isaac Gym-compatible runtimes, and MJLab where possible.
- All major logic must run inside Docker containers. The host should only need Docker, bash, git, and lightweight orchestration/report viewing tools.
- Docker build contexts should include the root workspace plus the relevant `thirdparties/` directories, following the orchestration style of `thirdparties/wbc-workspace`: thin host scripts build images, launch containers, collect logs, and generate reports from mounted workspace paths.
- Prefer scripts and adapters in this repository over modifying third-party source. Keep third-party changes minimal, explicit, and reviewable.

Dependency and project-owned paths:

- Dependency checkouts/packages: `thirdparties/DrEureka`, `thirdparties/wbc-workspace`, `thirdparties/IsaacGym` or `thirdparties/isaacgym`, and `thirdparties/MJLab`.
- Dockerfiles: `docker/go1_yoga_ball/`.
- Orchestration scripts: `scripts/go1_yoga_ball/`.
- Runtime logs: `logs/go1_yoga_ball/`.
- Final reports and videos: `artifacts/go1_yoga_ball/`.

## Primary DrEureka Interfaces

- Pre-existing policy run: `thirdparties/DrEureka/globe_walking/runs/globe_walking/dr_eureka_best`
- Built-in playback: `thirdparties/DrEureka/globe_walking/scripts/play.py`
- Default training: `thirdparties/DrEureka/globe_walking/scripts/train.py`
- Deployment policy runner: `thirdparties/DrEureka/globe_walking/go1_gym_deploy/scripts/deploy_policy.py`
- Go1 deployment transport: LCM channels `pd_plustau_targets`, `leg_control_data`, `state_estimator_data`, and `rc_command`

The default DrEureka LCM deploy stack is the preferred Sim2Sim contract because it is the real Go1 deployment contract used by the policy process. In real deployment, `lcm_position.cpp` bridges Unitree low-level UDP state/command traffic to these LCM channels. In MuJoCo Sim2Sim, the simulator must replace only that bridge: publish the same state channels, consume the same `pd_plustau_targets`, and preserve the same joint order, timing, and PD target semantics. If this is done, replacing the MuJoCo bridge with the real Unitree bridge should not require policy-code changes.

## Required Artifact Tree

All validation outputs must land under one stable tree:

```text
docker/go1_yoga_ball/
  isaacgym.Dockerfile
  mujoco_sim2sim.Dockerfile
  mjlab.Dockerfile
scripts/go1_yoga_ball/
  run.sh
  report.sh
  docker_build.sh
logs/go1_yoga_ball/
  pretrained/isaacgym_playback/
  pretrained/mujoco_sim2sim/
  default_train/train/
  default_train/isaacgym_playback/
  default_train/mujoco_sim2sim/
  mjlab_train/train/
  mjlab_train/default_playback/
  mjlab_train/mujoco_sim2sim/

artifacts/go1_yoga_ball/
  manifest.json
  policy_registry.json
  sim2sim_contract.md
  release_validation.json
  timing_validation.json
  metrics_summary.csv
  phase_pretrained_report.md
  phase_default_train_report.md
  phase_mjlab_report.md
  videos/
    pretrained_isaacgym.mp4
    pretrained_mujoco.mp4
    default_train_isaacgym.mp4
    default_train_mujoco.mp4
    mjlab_default_playback.mp4
    mjlab_mujoco.mp4
```

## Universal Verification Gates

Every evaluated policy must produce raw logs with timestamps, base pose, ball pose, joint position, joint velocity, action target, torque or PD target when available, contact/fall state, reward or success signal when available, and simulator time.

Each policy/simulator pair must pass or explicitly fail with evidence:

- The episode survives for the declared target duration. MuJoCo Sim2Sim should first measure direct-release fall time; controlled balance must be evidently longer than direct release. Smoke success is at least 5 seconds of released control, and target success is at least 20 seconds. The pre-existing baseline is expected to exceed 20 seconds unless evidence shows otherwise.
- The robot remains on or near the ball top and does not pass by floating, root pinning, or hidden stabilization.
- The ball is dynamic and physically interacts with the feet.
- Joint limits, action magnitudes, and torques remain within defensible safety bounds.
- Policy control dt matches the intended control period within tolerance.
- Generated videos are rendered from raw simulator logs, not from inferred traces or plots.

## Policy Equivalence Metrics

Use the same metrics for the pre-existing DrEureka policy, the freshly trained DrEureka policy, and the MJLab-trained policy. These thresholds define "equivalent policy" unless a report justifies changing them before running the full validation:

- Released balance duration: target success is at least 20 seconds; smoke success is at least 5 seconds. Controlled balance duration must be clearly longer than direct no-control release.
- Height threshold: for the yoga-ball task, the robot base should remain at or above `2 * ball_radius` for almost all of the released-control window. Count and report every frame below this threshold. Expect no or very few below-threshold frames; default pass criterion is at least 95% of released-control frames above threshold, with no continuous below-threshold segment longer than 0.5 seconds unless the run is marked failed.
- Fall/loss-of-balance: any fall before the target duration is a failure for that run. Fall detection must be based on base height, roll/pitch, and loss of ball-top contact behavior, not only a simulator `done` flag.
- Joint limits: expect no or very few joint-limit violations. Count every joint and frame where position exceeds the configured limit. Default pass criterion is zero hard violations; a run with brief numerical-margin violations may pass only if total violating frames are less than 0.1% of joint-frames, no violation persists longer than 0.1 seconds, and the report shows the max violation magnitude.
- Action/torque smoothness: report max and p95 action magnitude, action delta, PD target, and torque estimate when available. Large spikes must be explained and correlated with video/log evidence.
- Repeatability: full validation should run at least 3 clean starts per final policy/simulator pair when runtime permits. A policy is not equivalent if it passes only one lucky run and fails repeated starts under the same declared setup.
- Timing: Sim2Sim timing must satisfy the wall-clock consistency gates in this document. A policy that balances only because the simulator or policy loop is lagging is not equivalent.

## MuJoCo Sim2Sim Hard Gates

MuJoCo Sim2Sim must prove release behavior, actual release, and timing consistency. A Sim2Sim result is not valid without all three.

Release is required because the simulator may start before the policy and low-level control loop are ready. This is the Sim2Sim equivalent of DrEureka's real-robot deployment guidance that the Go1 should be hung up while the controller starts, calibrates, and enters policy control. If Sim2Sim lets the robot fall freely before the policy is active, it is testing startup timing rather than the policy. If Sim2Sim keeps support active after policy control begins, it is not testing real balance. Therefore support is allowed only as a startup synchronization mechanism, and the run must prove the transition from supported startup to fully dynamic released control.

### Release Behavior

For each Sim2Sim implementation, run clean-start release tests and store raw logs plus `artifacts/go1_yoga_ball/release_validation.json`:

1. No-control direct release: start from the supported initial pose, release support before policy control, and measure the uncontrolled fall/loss-of-balance time.
2. Active policy release: start supported, wait until policy control is active and producing valid actions, release support, and prove the robot remains balanced for the target duration.
3. Control removal after stable release: after a stable released-control run, stop sending valid policy commands and prove the robot falls or loses balance on a timescale comparable to the no-control direct-release case.

### Actual Release Proof

Raw Sim2Sim logs must include explicit support state and event records:

- `SIM_START`
- `POLICY_START`
- `CONTROL_ACTIVE`
- `SUPPORT_RELEASE_REQUESTED`
- `SUPPORT_RELEASE_CONFIRMED`
- `BALANCE_WINDOW_START`
- `BALANCE_WINDOW_END` or `FALL_DETECTED`

The report must prove that after `SUPPORT_RELEASE_CONFIRMED`, the root is not pinned, teleport-held, or otherwise overwritten except by normal MuJoCo dynamics. Event-order logs alone are insufficient; the proof must include simulator state showing unpinned root dynamics after release.

### Wall-Clock Consistency

MuJoCo Sim2Sim must prove that the simulator and policy are not silently lagging behind wall clock. Store `artifacts/go1_yoga_ball/timing_validation.json` with:

- Wall-clock elapsed time.
- MuJoCo simulation elapsed time.
- Policy loop elapsed time and control-step count.
- Mean, p95, and max policy inference latency.
- Mean, p95, and max control-period jitter.
- Ratio `sim_time / wall_time`.
- Ratio `policy_control_time / wall_time`.

The report must fail if simulation or policy control falls outside the declared tolerance. Default tolerance: `abs(sim_time / wall_time - 1.0) <= 0.05` and `abs(policy_control_time / wall_time - 1.0) <= 0.05`, unless a tighter or better-justified tolerance is declared before running.

## Phase 1: Pre-Existing Policy

Validate `thirdparties/DrEureka/globe_walking/runs/globe_walking/dr_eureka_best`.

1. Run built-in Isaac Gym playback with the saved run config.
2. Implement or adapt Go1 yoga-ball MuJoCo Sim2Sim through DrEureka's deployment contract.
3. Run the pre-existing TorchScript policy through the stock DrEureka deployment path where practical.
4. Produce raw logs, metrics, timing proof, release proof, and videos.

Success: the pre-existing policy passes built-in playback and MuJoCo Sim2Sim, or failures are explained with raw evidence.

## Phase 2: Default DrEureka Training

Train an equivalent policy inside the default DrEureka Isaac Gym environment.

1. Run `globe_walking/scripts/train.py` with the Eureka reward and the intended domain-randomization setup.
2. Preserve full training logs, config, checkpoints, exported TorchScript modules, and final policy registry entry.
3. Validate the trained policy with the same built-in playback harness used in phase 1.
4. Validate the trained policy with the same MuJoCo Sim2Sim harness used in phase 1.
5. Compare behavior against the pre-existing policy using the same metrics.

Success: the freshly trained policy reaches equivalent behavior under both playback and Sim2Sim, or the report identifies the training budget/configuration gap with evidence.

## Phase 3: MJLab Training

Port the training setup to MJLab while treating MJLab as a dependency, not as code to be re-created inside this repository.

1. Use the supplied MJLab checkout and install/runtime instructions.
2. Port the Go1 yoga-ball task semantics: Go1 model, dynamic ball, reset distribution, observations, observation history, action scaling, reward terms, termination logic, and domain randomization.
3. Train an equivalent MJLab policy.
4. Export the policy to the same deployment-level action/observation contract where possible. If an adapter is required, document the exact observation order, normalization, action scaling, and timing assumptions in `sim2sim_contract.md`.
5. Validate the MJLab policy in its default playback path.
6. Validate the MJLab policy in the same MuJoCo Sim2Sim harness and with the same release/timing proof.

Success: the MJLab-trained policy behaves equivalently to the DrEureka policies under default playback and MuJoCo Sim2Sim.

## Constraints

- Do not change host environment beyond lightweight tools unless explicitly needed. Heavy runtimes belong in Docker images and dependency checkouts under `thirdparties/`.
- Use suitable CUDA/PyTorch/MuJoCo/Isaac Gym/MJLab base images rather than hand-building major runtime stacks when a proper base exists.
- Do not bypass policy deployment logic with a policy-specific simulator shortcut unless the report explicitly marks it as a temporary diagnostic, not final Sim2Sim evidence.
- Do not hard-code policy-specific stabilizers in MuJoCo. The simulator must be a physical Go1-on-ball endpoint, not a per-policy plant.
- Do not make Sim2Sim depend on a policy-specific interface. For DrEureka policies, the final MuJoCo path must be swappable with the real Go1 by replacing the MuJoCo LCM bridge with the real Unitree LCM/UDP bridge.
- Preserve raw evidence before summarizing it.
- Keep changes surgical and prefer adding thin orchestration/reporting code over refactoring third-party packages.

## Iteration Policy

Work one phase at a time. For each phase:

1. Validate one short smoke run.
2. Inspect raw logs and timing.
3. Fix only the smallest identified issue.
4. Re-run the same smoke case.
5. Scale to the full validation duration only after release and timing proofs pass.

If behavior diverges between Isaac Gym, MJLab, and MuJoCo, first check observation order, action scaling, joint order, control dt, default pose, ball physical parameters, and support-release semantics before changing rewards or policy code.

## Blocked Stop Conditions

Stop and report with evidence if:

- Isaac Gym cannot be fetched, extracted, installed in Docker, or made to run DrEureka playback/training after concrete attempts. Missing Isaac Gym at the start is not a stop condition; the agent is expected to acquire it into `thirdparties/IsaacGym/` or `thirdparties/isaacgym/`.
- MJLab cannot be fetched, installed in Docker, or made to run the ported training task after concrete attempts. Missing MJLab at the start is not a stop condition; the agent is expected to acquire it into `thirdparties/MJLab/`.
- The MuJoCo Go1 yoga-ball model cannot represent the required dynamic ball interaction without hidden root support after release.
- Sim2Sim cannot keep simulation time and policy control time synchronized with wall clock under the declared tolerance.
- A trained policy cannot reach equivalent behavior after the declared training budget and at least one defensible retry.
