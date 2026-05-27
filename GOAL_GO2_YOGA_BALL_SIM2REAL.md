# Goal: Go2 Yoga-Ball Sim2Real Migration

## Outcome

Migrate the Go1 yoga-ball Sim2Real pipeline to Unitree Go2 while preserving the same standard of evidence:

1. A MuJoCo Go2-on-yoga-ball simulator smoke path that is designed to be swapped with the real Go2 robot bridge without policy-code changes.
2. DrEureka/Isaac Gym training configured for Go2 model geometry, joint limits, default pose, actuator/PD behavior, torque limits, action scale, observation order, and deployment joint order.
3. Baseline Go2 training smoke tests that compare reward curves before committing to a full run.
4. A smoke-tested Go2 baseline under a 20-minute wall-clock budget, followed by a one-shot 1/8-budget training run that is checked for 5 minutes of healthy execution, with artifacts proving what did and did not pass.

The final result should be reviewable by human embodied-intelligence experts without relying on console claims.
This goal is allowed to finish only after the 20-minute smoke-test gate passes, then the one-shot 1/8-budget run has been started with pretrained-matching settings as closely as possible and verified healthy for 5 minutes, and the evidence files are written. Full-scale Go2 training is a follow-up goal, not required for this goal to complete.

## Current Evidence And Constraints

- Current Go1 state is committed in root commit `9d3adf4`.
- Current DrEureka submodule source changes are committed in `thirdparties/DrEureka` commit `aacfbf9`.
- The existing checked-out DrEureka tree contains Go1 assets only under `globe_walking/resources/robots/go1/`.
- The current MJLab checkout contains Unitree Go1 and G1 assets, but no Go2 asset was found under `src/mjlab/asset_zoo/robots/`.
- The checked-out `thirdparties/wbc-workspace` reference contains an official Unitree MuJoCo dependency at `thirdparties/wbc-workspace/thirdparties/unitree_mujoco`, commit `c598f103acb87a5fd3de7c9037f4dab6aa7f232b`, including `unitree_robots/go2/go2.xml` and `unitree_robots/go2/scene.xml`.
- Do not treat Go1 actuator net `unitree_go1.pt`, Go1 joint limits, Go1 default pose, or Go1 LCM/SDK details as valid for Go2 without evidence.
- Heavy dependencies and fetched Go2 assets belong under root `thirdparties/` or Docker images. Major logic should keep running inside Docker.
- Preferred Go2 asset/source candidates:
  - MuJoCo simulator/real-robot swap contract: fetch `https://github.com/unitreerobotics/unitree_mujoco` into root `thirdparties/unitree_mujoco`, using `unitree_robots/go2/` and the SDK2 low-level command/state path. The nested copy in `thirdparties/wbc-workspace/thirdparties/unitree_mujoco` is a reference, not the root build-context dependency.
  - DrEureka/Isaac Gym asset import: fetch `https://github.com/Unitree-Go2-Robot/go2_description` or the underlying `unitreerobotics/go2_urdf` model into root `thirdparties/`, with documented collision edits for Isaac Gym-style training.
  - MJLab Go2 reference: fetch `https://github.com/unitreerobotics/unitree_rl_mjlab` into root `thirdparties/` or vendor only its Go2 asset/config with provenance. The current `thirdparties/MJLab` dependency lacks a Go2 asset, so MJLab Go2 support must be added as an explicit dependency, the same way DrEureka consumes Isaac Gym as an external dependency.
  - Secondary MuJoCo model reference: `https://github.com/google-deepmind/mujoco_menagerie`, which includes a `unitree_go2/scene.xml` model useful for cross-checking MJCF parameters.

## Required Artifact Tree

```text
scripts/go2_yoga_ball/
  run.sh
  reward_curve_compare.py
  go2_mujoco_lcm_bridge.py

docker/
  isaacgym.Dockerfile          # shared by Go1 and Go2
  mujoco_sim2sim.Dockerfile    # shared by Go1 and Go2
  mjlab.Dockerfile             # shared by Go1 and Go2

thirdparties/
  IsaacGym/                  # fetched by agent if absent, accepted license required
  DrEureka/
  MJLab/
  unitree_mujoco/            # root build-context copy, not only nested under wbc-workspace
  go2_description_or_urdf/   # exact name may follow upstream repo
  unitree_rl_mjlab/          # optional if needed for authoritative MJLab Go2 config

artifacts/go2_yoga_ball/
  manifest.json
  go2_asset_inventory.json
  sim2sim_contract.md
  reward_curve_comparison.csv
  reward_curve_comparison.json
  reward_curve_comparison.md
  reward_curve_total.svg
  phase_go2_train_report.md
  mujoco_sim2sim_health_report.md
  videos/
    go2_mujoco_1_8_budget.mp4

logs/go2_yoga_ball/
  train_smoke/
  train_1_8_budget/
  mujoco_sim2sim/
```

Dockerfile rule: use shared environment Dockerfiles directly under `docker/`; do not create robot-prefixed Dockerfiles such as `go1_*` or `go2_*` unless the runtime dependencies genuinely diverge. Build shared images as `eureka-isaacgym`, `eureka-mujoco_sim2sim`, and `eureka-mjlab`, then keep robot/task-specific behavior in mounted scripts and runtime arguments. Use suitable base images for the stack, for example CUDA/PyTorch for Isaac Gym training and Ubuntu/MuJoCo for Sim2Sim. Build from the repository root so `thirdparties/` is available as Docker build context. Keep stable base-image, system dependency, and heavy dependency install layers before source `COPY` lines. Only copy root source and frequently changing scripts after those stable layers so Docker build cache survives normal code/report edits. Once those pre-`COPY` layers work, avoid changing them unless the dependency set itself changes.

## Implementation Requirements

1. Acquire or create a defensible Go2 model source.
   - Prefer official Unitree Go2 URDF/MJCF or a widely used upstream model with clear provenance.
   - Store fetched model assets under root `thirdparties/` or a documented project-owned asset path if generated.
   - Fetch missing Isaac Gym and MJLab-related dependencies during the goal; do not require manual host installation except for license-gated archive availability.
   - Record source URL, commit/hash, license, joint names, limits, masses, inertias, actuator configuration, and mesh paths in `artifacts/go2_yoga_ball/go2_asset_inventory.json`.
   - Do not proceed with training edits until the inventory proves which model is authoritative for MuJoCo, Isaac Gym, and MJLab.

2. Update DrEureka training for Go2.
   - Add a Go2 robot config rather than mutating Go1 constants in place.
   - Change asset file, default joint angles, joint limits, torque limits, action scale, hip scale reduction, PD gains or actuator model, foot/body contact names, and deployment joint order.
   - If no Go2 actuator network exists, use a documented PD fallback first and mark it as not actuator-equivalent until validated.

3. Prove MuJoCo Sim2Sim is swappable with real Go2.
   - Use the same deployment-level contract style as the Go1 pipeline: policy process publishes PD/torque targets and consumes robot state.
   - Document any Go2 bridge differences from the Go1 LCM contract before using them.
   - Prove support release, actual release, control removal, and wall-clock consistency.
   - For any policy described as working, report released-window duration, joint-limit violation count, base-height-below-threshold frames, policy step timing, sim step timing, and wall-clock drift. Expected behavior is no or very few released-window joint-limit violations and no sustained height-below-threshold interval.

4. Compare reward curves before scaling.
   - Run short smoke training tests with the Go2 config and compare reward curves against the Go1 pretrained curve and the existing Go1 1/8-budget curve.
   - Preserve `reward_curve_comparison.csv`, `.json`, `.md`, and `.svg`.
   - Do not report "training is effective" or "training failed" from a tiny non-equivalent run. The smoke run only proves the pipeline can train, log, export, and be inspected.

5. Run smoke-budget Go2 training, then start the one-shot 1/8-budget run.
   - Target wall-clock budget: 20 minutes.
   - Use a small env count and iteration count sufficient to prove model load, reset, stepping, reward logging, checkpoint export, and curve generation.
   - After the smoke gate passes, start exactly one 1/8-budget run with settings as consistent with the pretrained model as possible. Use `ITERATIONS=20000` and `TRAIN_NUM_ENVS=4096` because only one GPU card is available, and treat this as the single allowed shot for that budget level.
   - Verify the 1/8-budget run stays healthy for 5 minutes of wall-clock time after launch, then stop the goal and rate it from the training results.
   - Treat any full-budget run as follow-up work once this goal completes.

## Verification Gates

- Go2 asset inventory exists and proves the model/actuator source.
- Isaac Gym can load the Go2 model, reset on the yoga ball, and run a smoke train within the 20-minute budget without NaNs or immediate termination.
- Reward curves are generated from raw smoke training logs, not manually transcribed values.
- The smoke run produces at least one checkpoint/export artifact or clearly reports why export is not available at the chosen smoke length.
- After the smoke gate passes, exactly one 1/8-budget run is launched with the closest defensible pretrained-matching settings, including `ITERATIONS=20000`, `TRAIN_NUM_ENVS=4096`, `TRAIN_NO_VIDEO=1`, `TRAIN_SAVE_INTERVAL=1000`, and the pretrained domain-randomization profile if it remains valid for Go2.
- The 1/8-budget run is monitored for 5 minutes and has evidence that training is healthy: process still alive, no NaNs, iteration/log output advancing, GPU utilization/memory stable enough for the run, and artifacts/log paths recorded. The goal completes after this health check; final rating comes from the resulting training curve/checkpoint quality.
- MuJoCo Go2 model loads, support/release mechanics execute in a smoke run, and the bridge design is documented against the real Go2 SDK2 low-level state/command contract.
- Videos are rendered from raw replay logs and mark joint-limit violations when a MuJoCo smoke replay exists.
- `mujoco_sim2sim_health_report.md` reports release timing, actual release state, joint-limit violation counts, base-height-below-threshold counts, policy timing, sim timing, and wall-clock drift. If the smoke policy is untrained or unstable, the report must say that explicitly rather than treating the smoke as a successful walking policy.
- `phase_go2_train_report.md` explicitly says this is smoke validation only and does not claim final policy equivalence.

## Blocked Stop Conditions

Stop with evidence if:

- No defensible Go2 model/actuator source can be fetched or created under the allowed dependency constraints.
- The Go2 model cannot be loaded in Isaac Gym or MuJoCo after concrete fixes.
- Go2 deployment semantics cannot be mapped to a real-robot-swappable bridge without changing policy-code behavior.
- The 20-minute smoke training repeatedly produces NaNs or immediate termination after correcting model, joint order, and action scaling issues.
