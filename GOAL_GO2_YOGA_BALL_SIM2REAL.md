# Goal: Go2 Yoga-Ball Migration With Real-Swappable Sim2Sim Boundary

## Outcome

Migrate the DrEureka Go1 yoga-ball setup to Unitree Go2 without wasting an 11-hour training run on a mismatched robot contract.

The target architecture is deliberately simple:

```text
Go2 policy/deploy container
  DrEureka policy
  LCM policy contract
  LCM -> Unitree SDK2 DDS bridge

Go2 robot endpoint
  either Unitree MuJoCo Go2 DDS simulator container
  or real Unitree Go2 on the robot network interface
```

For Go2, the simulator container must have one responsibility: behave like a real Go2 low-level DDS endpoint. It must not consume DrEureka LCM directly. LCM-to-DDS translation belongs inside the policy/deploy side, so a successful Sim2Sim run proves the same translation path needed for real Go2 deployment.

After that boundary is faithful, add Go2 model, actuator, joint-order, default-pose, limits, and controller/actuator assumptions inside DrEureka/Isaac Gym so training uses the same robot contract. Actuator consistency is especially important: the source of truth is the fetched `unitree_mujoco` implementation, including both `unitree_robots/go2/go2.xml` actuator metadata and the SDK2 bridge code that maps `LowCmd` fields into MuJoCo torques. Both MuJoCo deploy-time fidelity and Isaac Gym train-time fidelity must be proven by reports containing concrete source excerpts with filename and line references. A single mismatch can waste the long run, so the 1/8-budget training must not be launched until these reports pass.

Human embodied-intelligence reviewers should be able to inspect the reports and see the exact code that proves each claim, what is approximated, and what remains unproven without relying on console claims.

## Scope

In scope:

- Fetching and using `thirdparties/unitree_mujoco` as the authoritative Go2 real-robot low-level contract.
- Building a faithful Go2 DDS MuJoCo simulator endpoint that is directly swappable with a real Go2 backend.
- Implementing or wiring a Go2 policy/deploy bridge that converts DrEureka LCM policy messages to Unitree SDK2 DDS `LowCmd`/`LowState`.
- Porting DrEureka Isaac Gym training to Go2 as a separate robot/config path, not by mutating Go1 constants in place.
- Adding Go2 model and actuator configuration in DrEureka. If a defensible Go2 actuator network exists in fetched resources, use it. If not, the PD command path may pass only if reports prove it is the actual `unitree_mujoco`/SDK2 actuator interface: deploy sends `q_des`, `qd_des`, `kp`, `kd`, and `tau_ff`, and both MuJoCo and Isaac Gym use the same torque equation, gains, and torque limits.
- Running Isaac Gym smoke training and exactly one 1/8-budget training health check only after fidelity reports pass.
- Generating reports under `artifacts/go2_yoga_ball/`.

Out of scope for this goal:

- MJLab training or MJLab smoke tests.
- Real Go2 robot testing.
- Full-budget training.
- Reworking the legacy Go1 deploy path. Go1 may stay LCM -> Unitree Go1 SDK UDP.

## Current Evidence And Constraints

- DrEureka lives at `thirdparties/DrEureka`.
- Isaac Gym is a dependency under `thirdparties/IsaacGym/` and is used inside `docker/isaacgym.Dockerfile`.
- Unitree MuJoCo Go2 source lives at `thirdparties/unitree_mujoco`; its Go2 MJCF and SDK2 bridge implementation are the authoritative Go2 robot and actuator contract.
- Go2 URDF source lives at `thirdparties/go2_description`; use it for Isaac Gym import only after proving consistency against `unitree_mujoco`.
- Heavy fetched dependencies stay under root `thirdparties/` and are ignored by git.
- Major logic runs inside Docker containers.
- Shared Docker environment remains under `docker/`; do not create Go1/Go2-prefixed Dockerfiles unless dependency requirements actually diverge.

## Required Artifact Tree

```text
scripts/go2_yoga_ball/
  run.sh
  asset_inventory.py
  runner.py
  reward_curve_compare.py

docker/
  isaacgym.Dockerfile
  mujoco_sim2sim.Dockerfile

thirdparties/
  IsaacGym/
  DrEureka/
  unitree_mujoco/
  go2_description/

artifacts/go2_yoga_ball/
  manifest.json
  go2_asset_inventory.json
  go2_mujoco_dds_endpoint_report.json
  go2_mujoco_dds_endpoint_report.md
  go2_lcm_to_dds_bridge_report.json
  go2_lcm_to_dds_bridge_report.md
  go2_isaacgym_consistency_report.json
  go2_isaacgym_consistency_report.md
  go2_isaacgym_urdf.json
  phase_go2_train_report.json
  phase_go2_train_report.md
  go2_train_smoke_run.json
  go2_train_smoke_selected_run.txt
  train_1_8_budget_health.json
  train_1_8_budget_health.md
  reward_curve_comparison.csv
  reward_curve_comparison.json
  reward_curve_comparison.md
  reward_curve_total.svg

logs/go2_yoga_ball/
  mujoco_dds_endpoint_smoke/
  train_smoke/
  train_1_8_budget/
```

## Implementation Requirements

1. Treat `unitree_mujoco` as the Go2 ground truth before training.
   - Parse `thirdparties/unitree_mujoco/unitree_robots/go2/go2.xml`.
   - Record commit, license, joint names, motor order, default/home joint pose, joint limits, torque limits, mesh paths, actuator classes, and sensor order in `go2_asset_inventory.json`.
   - Do not train until the inventory is generated.

2. Build the Go2 MuJoCo simulator as a DDS robot endpoint.
   - The simulator container must consume Unitree SDK2 DDS `LowCmd` and publish DDS `LowState`, matching the real Go2 low-level interface.
   - It must not subscribe to DrEureka LCM policy topics.
   - It must use Unitree Go2 joint order, joint names, default pose, motor command semantics, torque limits, and state ordering from `unitree_mujoco`.
   - For actuator semantics, the source of truth is the `unitree_mujoco` implementation of `LowCmd` handling and torque application, not an inferred or hand-written PD convention.
   - `go2_mujoco_dds_endpoint_report.md` must include inline source excerpts and line references proving the DDS topics, command fields, PD/torque equation, motor order, joint limits, and actuator limits. Example format:
     - `thirdparties/unitree_mujoco/simulate/src/unitree_sdk2_bridge.h:183`: `mj_data_->ctrl[i] = m.tau() + ...`
   - The report must state whether replacing the simulator container with a real Go2 on `eth0` should require policy/deploy code changes. The target answer is no, except for network/backend selection and safety procedures.

3. Put LCM-to-DDS conversion in the Go2 policy/deploy side.
   - DrEureka policy may keep its LCM policy contract internally.
   - The Go2 deploy container must convert DrEureka LCM command/state contract to Unitree SDK2 DDS, not rely on a simulator that understands LCM.
   - `go2_lcm_to_dds_bridge_report.md` must include inline source excerpts and line references proving:
     - input LCM channels and fields,
     - output DDS topics and fields,
     - joint-order mapping,
     - PD gain forwarding,
     - `q_des`, `qd_des`, `kp`, `kd`, and `tau_ff` mapping into DDS `LowCmd`,
     - DDS `LowState` mapping back into the LCM state used by DrEureka.

4. Make Isaac Gym Go2 faithful to the same Go2 contract.
   - Use the Go2 URDF only as an Isaac Gym import carrier.
   - Match the 12 actuated joint names.
   - Match Unitree MuJoCo Go2 motor/action order or explicitly document the policy-order mapping.
   - Match the Unitree MuJoCo home/default pose: hip `0.0`, thigh `0.9`, calf `-1.8` for all four legs unless the report proves a different Unitree default is more authoritative.
   - Match joint limits and effort/torque limits as closely as Isaac Gym allows.
   - Add Go2 actuator configuration in DrEureka. This is a critical fidelity gate. If a defensible Go2 actuator network is available from fetched resources, use it. If not, the documented PD command path may pass only when its gains, torque limits, and command equation are explicitly compared against `unitree_mujoco` and the Go2 deploy bridge forwards the same gains to DDS `LowCmd`.
   - `go2_isaacgym_consistency_report.md` must include inline source excerpts and line references for the MuJoCo source and the Isaac Gym/DrEureka source side by side. It must cover joint names, action order, default pose, joint limits, effort limits, actuator/controller settings, foot/body names, asset path, and training PD/actuator network selection.

5. Run the Go2 Isaac Gym smoke gate.
   - Target wall-clock budget: 20 minutes or less.
   - The run must prove model load, reset, stepping, reward logging, checkpoint export or explicit checkpoint-interval reason, and no NaNs/immediate termination.
   - The report must say this is smoke validation only, not final policy equivalence.

6. Launch exactly one 1/8-budget run after all fidelity and smoke gates pass.
   - Use settings closest to the pretrained Go1 run where defensible:
     - `ITERATIONS=20000`
     - `TRAIN_NUM_ENVS=4096`
     - `TRAIN_NO_VIDEO=1`
     - `TRAIN_SAVE_INTERVAL=1000`
     - pretrained domain-randomization profile only if the consistency report proves it remains valid for Go2.
   - This is the only allowed 1/8-budget launch for this goal.
   - Monitor for 5 minutes and record process health, log advancement, no NaNs, GPU memory/utilization, run path, and artifact paths.
   - The goal completes after this 5-minute health check and report generation. The training may continue outside the goal.

## Verification Gates

- `go2_asset_inventory.json` exists and identifies `unitree_mujoco` as the ground-truth Go2 source.
- `go2_mujoco_dds_endpoint_report.md` and `.json` prove the simulator is a DDS low-level Go2 endpoint and does not depend on DrEureka LCM.
- `go2_lcm_to_dds_bridge_report.md` and `.json` prove the Go2 deploy path owns LCM-to-DDS conversion.
- `go2_isaacgym_consistency_report.md` and `.json` prove or explicitly fail each train-time consistency field:
  - joint names
  - action order
  - default pose
  - joint limits
  - effort/torque limits
  - actuator network or PD fallback
  - foot/body names used by training
  - asset file and mesh path handling
- Each fidelity report contains concrete inline code excerpts with filename and line references for both sides of every major claim.
- DrEureka has a separate Go2 robot/config path.
- Isaac Gym smoke training completes within the 20-minute budget without NaNs or immediate termination.
- Smoke training produces at least one checkpoint/export artifact, or the report explicitly explains why the chosen smoke length cannot export.
- The one-shot 1/8-budget command is launched only after all fidelity and smoke reports pass.
- The 1/8-budget health report proves the run stayed healthy for 5 minutes.

## Blocked Stop Conditions

Stop with evidence if:

- `unitree_mujoco` Go2 cannot be fetched or parsed.
- The DDS Go2 simulator endpoint cannot be made directly swappable with a real Go2 backend under the current Docker/network constraints.
- The LCM-to-DDS bridge cannot preserve DrEureka command/state semantics and Unitree SDK2 DDS semantics.
- The Go2 URDF cannot be made consistent enough with `unitree_mujoco` for Isaac Gym training.
- No defensible Go2 actuator network exists and the PD command path cannot be proven equivalent to the `unitree_mujoco`/SDK2 `LowCmd` actuator semantics.
- Isaac Gym cannot load or step the Go2 model after concrete fixes to paths, joint order, default pose, limits, and actuator settings.
- The 20-minute smoke training repeatedly produces NaNs or immediate termination after the fidelity reports pass.
