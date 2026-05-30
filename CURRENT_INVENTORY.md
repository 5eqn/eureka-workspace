# Current Inventory

Read this file first. It is the low-cognitive-load map of the main project line. It lists every file outside `thirdparties/`, cache folders, and `outdated/`, including ignored runtime evidence under `artifacts/` and `logs/`. If a file does not directly support one of these stages, move it to `outdated/` and update `OUTDATED_INVENTORY.md`.

## Project Outline

- `P0` Repository Map: rules, ignore policy, and this inventory system.
- `G1P` Go1 Pretrained Reference: DrEureka's pretrained Go1 yoga-ball policy works in Isaac Gym playback and MuJoCo Sim2Sim, with release/timing/control-removal evidence and replay video.
- `G1T` Go1 Default 1/8 Training: locally trained Go1 policy is kept as a mainstream comparison point against the pretrained Go1 reference, even though its policy quality is weaker.
- `G2C` Go2 Contract: Go2 train/deploy contract uses Unitree RL Gym Go2 URDF for Isaac Gym and Unitree MuJoCo/DDS plus LCM-to-DDS bridge reports for deployment consistency.
- `G2T` Go2 Corrected 1/8 Training: final corrected Go2 20k-iteration, 4096-env Isaac Gym training completed from the Unitree RL Gym Go2 model with train-time boxes_tm terrain.
- `G2P` Go2 Isaac Playback: final corrected Go2 trained-policy Isaac-side playback is complete.
- `G2S` Go2 MuJoCo/DDS Sim2Sim: corrected Go2 1/8 trained checkpoint succeeded in MuJoCo/DDS Sim2Sim on attempt 1, with confirmed release, live LCM-to-DDS command path, wall-clock-consistent timing, and follow-camera success video.
- `G2M` Go2 MJLab Port: FRESH host-side MJLab reproduction has a self-contained caller-project task using Unitree RL MJLab Go2 PD gains, MJLab term-major actor history with DrEureka/Isaac-side sensor terms, an RSL-RL critic input of actor history plus 11 privileged values, MJLab built-in `HfPerlinNoiseTerrainCfg` at Isaac-side 20x20 5m-tile/0.05m-grid scale, Isaac-like fixed terrain-origin assignment over rows/cols 5..14 with robot XY reset jitter, and robot/ball-scoped pretrained-style DrEureka domain randomization; the interrupted random-uniform training is archived and the built-in-Perlin dry run passes.
- `G2F` Go2 MJLab FRESH Sim2Sim: host-side pure-DDS Go2 MuJoCo Sim2Sim runtime and direct MJLab checkpoint-to-DDS deployer are available for the next corrected MJLab checkpoint; old checkpoint-derived Sim2Sim evidence is archived.
- `S` Orchestration: Dockerfiles and scripts that reproduce or extend the Go1 and Go2 workflows.

## Files

| Stage | File | Reason |
| --- | --- | --- |
| `P0` | `.gitignore` | Ignores `/artifacts/`, `/logs/`, `/outdated/`, fetched third-party payloads, and local build caches while keeping workflow scripts trackable. |
| `P0` | `.gitmodules` | Records the DrEureka submodule mount used as the upstream training code base. |
| `P0` | `AGENTS.md` | Defines the required working rules, especially inventory discipline and goal verification standards. |
| `P0` | `CURRENT_INVENTORY.md` | First-read map of the mainstream project state and every current workspace file. |
| `G2M` | `GOAL_GO2_MJLAB_DREUREKA_PORT.md` | Goal definition for reproducing DrEureka Go2 yoga-ball training inside MJLab with FRESH home-space dependencies and a 20-minute smoke gate before the 1/8-budget train. |
| `G2F` | `GOAL_GO2_MJLAB_FRESH_SIM2SIM.md` | Goal definition for host-side FRESH Sim2Sim of the completed MJLab Go2 checkpoint using a direct DDS deployer and joint-name-based order validation. |
| `G2S` | `GOAL_GO2_YOGA_BALL_FINAL_SIM2SIM.md` | Goal definition for validating the corrected 2026-05-28 Go2 1/8 checkpoint in MuJoCo/DDS Sim2Sim. |
| `P0` | `OUTDATED_INVENTORY.md` | Index of archived files so old attempts can be found without polluting the current tree. |
| `G1P` | `artifacts/go1_yoga_ball/build/go1_sanitized.xml` | MuJoCo Go1 model generated for the working pretrained Sim2Sim reference. |
| `G1P` | `artifacts/go1_yoga_ball/build/go1_yoga_ball_scene.xml` | MuJoCo yoga-ball scene used by the working pretrained Go1 Sim2Sim reference. |
| `G1T` | `artifacts/go1_yoga_ball/default_train_config_comparison.json` | Captures the locally trained Go1 run configuration comparison against the pretrained setup. |
| `G1T` | `artifacts/go1_yoga_ball/default_train_isaacgym_playback.json` | Summarizes Isaac Gym playback for the locally trained Go1 policy. |
| `G1T` | `artifacts/go1_yoga_ball/default_train_mujoco_sim2sim_smoke.json` | Summarizes MuJoCo Sim2Sim smoke behavior for the locally trained Go1 policy. |
| `G1T` | `artifacts/go1_yoga_ball/default_train_mujoco_video.json` | Records the rendered-video artifact for the locally trained Go1 Sim2Sim run. |
| `G1T` | `artifacts/go1_yoga_ball/default_train_run.json` | Identifies the exact local Go1 training run selected for default-trained-policy evaluation. |
| `G1T` | `artifacts/go1_yoga_ball/default_train_selected_run.txt` | Plain-text pointer to the selected local Go1 training run directory. |
| `G1P` | `artifacts/go1_yoga_ball/manifest.json` | Manifest for Go1 reference artifacts and generated scene assets. |
| `G1T` | `artifacts/go1_yoga_ball/mujoco_marked_videos.json` | Index for Go1 rendered videos with marked joint-limit events. |
| `G1T` | `artifacts/go1_yoga_ball/phase_default_train_report.md` | Human-readable report for the locally trained Go1 policy phase. |
| `G1T` | `artifacts/go1_yoga_ball/phase_default_train_summary.json` | Machine-readable summary for the locally trained Go1 policy phase. |
| `G1P` | `artifacts/go1_yoga_ball/phase_pretrained_report.md` | Human-readable report proving pretrained Go1 playback and Sim2Sim status. |
| `G1P` | `artifacts/go1_yoga_ball/phase_pretrained_summary.json` | Machine-readable summary of pretrained Go1 validation metrics. |
| `G1P` | `artifacts/go1_yoga_ball/policy_registry.json` | Maps the pretrained and local Go1 policy artifacts used by scripts and reports. |
| `G1P` | `artifacts/go1_yoga_ball/pretrained_isaacgym_playback.json` | Isaac Gym playback result for the pretrained Go1 policy. |
| `G1P` | `artifacts/go1_yoga_ball/pretrained_mujoco_control_removal.json` | Shows the pretrained Go1 Sim2Sim fails after control removal, proving policy control is active. |
| `G1P` | `artifacts/go1_yoga_ball/pretrained_mujoco_sim2sim_repeat_run_1.json` | First repeated pretrained Go1 Sim2Sim validation run. |
| `G1P` | `artifacts/go1_yoga_ball/pretrained_mujoco_sim2sim_repeat_run_2.json` | Second repeated pretrained Go1 Sim2Sim validation run. |
| `G1P` | `artifacts/go1_yoga_ball/pretrained_mujoco_sim2sim_repeat_run_3.json` | Third repeated pretrained Go1 Sim2Sim validation run. |
| `G1P` | `artifacts/go1_yoga_ball/pretrained_mujoco_sim2sim_repeats.json` | Aggregate of repeated pretrained Go1 Sim2Sim validations. |
| `G1P` | `artifacts/go1_yoga_ball/pretrained_mujoco_sim2sim_smoke.json` | Main pretrained Go1 MuJoCo Sim2Sim smoke summary. |
| `G1P` | `artifacts/go1_yoga_ball/pretrained_mujoco_video.json` | Metadata for the pretrained Go1 follow-camera replay video. |
| `G1P` | `artifacts/go1_yoga_ball/release_validation.json` | Evidence that pretrained Go1 motion starts after release rather than while pinned. |
| `G1P` | `artifacts/go1_yoga_ball/sim2sim_contract.md` | Written contract for the Go1 MuJoCo Sim2Sim release/timing/control expectations. |
| `G1P` | `artifacts/go1_yoga_ball/timing_validation.json` | Confirms pretrained Go1 simulation, policy, and wall clock stayed synchronized. |
| `G1T` | `artifacts/go1_yoga_ball/videos/default_train_mujoco.mp4` | Follow-camera video for local Go1 trained-policy MuJoCo Sim2Sim behavior. |
| `G1P` | `artifacts/go1_yoga_ball/videos/pretrained_mujoco.mp4` | Follow-camera video for working pretrained Go1 MuJoCo Sim2Sim behavior. |
| `G2C` | `artifacts/go2_yoga_ball/build/go2_unitree_sanitized.xml` | Sanitized Unitree-derived Go2 MuJoCo model used for current Go2 scene generation. |
| `G2C` | `artifacts/go2_yoga_ball/build/go2_yoga_ball_scene.xml` | Current Go2 yoga-ball MuJoCo scene built from the Unitree-derived Go2 model. |
| `G2P` | `artifacts/go2_yoga_ball/final_train_isaacgym_playback_no_video/playback.csv` | Raw per-step Isaac playback data for the corrected Go2 policy without video overhead. |
| `G2P` | `artifacts/go2_yoga_ball/final_train_isaacgym_playback_no_video/report.md` | Human-readable corrected Go2 no-video playback result, including survival count. |
| `G2P` | `artifacts/go2_yoga_ball/final_train_isaacgym_playback_no_video/summary.json` | Machine-readable corrected Go2 no-video playback summary. |
| `G2P` | `artifacts/go2_yoga_ball/final_train_isaacgym_playback_video/isaacgym_playback.mp4` | Isaac-rendered video showing corrected Go2 trained policy playback shape. |
| `G2P` | `artifacts/go2_yoga_ball/final_train_isaacgym_playback_video/playback.csv` | Raw per-step data for the corrected Go2 video playback run. |
| `G2P` | `artifacts/go2_yoga_ball/final_train_isaacgym_playback_video/report.md` | Human-readable corrected Go2 video playback report, noting graphics teardown exit behavior. |
| `G2P` | `artifacts/go2_yoga_ball/final_train_isaacgym_playback_video/summary.json` | Machine-readable corrected Go2 video playback summary. |
| `G2S` | `artifacts/go2_yoga_ball/final_train_sim2sim/go2_final_train_sim2sim_video.json` | Render validation for the successful corrected Go2 Sim2Sim follow-camera video. |
| `G2S` | `artifacts/go2_yoga_ball/final_train_sim2sim/report.md` | Human-readable final report proving corrected Go2 Sim2Sim succeeded on attempt 1. |
| `G2S` | `artifacts/go2_yoga_ball/final_train_sim2sim/summary.json` | Machine-readable metrics for corrected Go2 Sim2Sim release, timing, command path, torque, and joint-limit checks. |
| `G2S` | `artifacts/go2_yoga_ball/final_train_sim2sim/videos/go2_final_train_sim2sim_success.mp4` | Follow-camera video rendered from raw MuJoCo replay for the successful corrected Go2 Sim2Sim run. |
| `G2C` | `artifacts/go2_yoga_ball/go2_isaacgym_consistency_report.json` | Structured proof that Isaac-side Go2 config follows the Unitree RL Gym source model. |
| `G2C` | `artifacts/go2_yoga_ball/go2_isaacgym_consistency_report.md` | Human-readable proof of Go2 Isaac model, actuator, joint order, and default pose consistency. |
| `G2C` | `artifacts/go2_yoga_ball/go2_isaacgym_urdf.json` | Parsed Go2 URDF facts used to audit Isaac-side model consistency. |
| `G2C` | `artifacts/go2_yoga_ball/go2_lcm_to_dds_bridge_report.json` | Structured audit of the Go2 LCM-to-DDS command conversion path. |
| `G2C` | `artifacts/go2_yoga_ball/go2_lcm_to_dds_bridge_report.md` | Human-readable audit explaining how Go2 deployment commands are translated to DDS. |
| `G2C` | `artifacts/go2_yoga_ball/go2_mujoco_dds_endpoint_report.json` | Structured audit of the Go2 MuJoCo DDS endpoint intended to be swappable with a real robot endpoint. |
| `G2C` | `artifacts/go2_yoga_ball/go2_mujoco_dds_endpoint_report.md` | Human-readable Go2 MuJoCo DDS endpoint contract and consistency notes. |
| `G2C` | `artifacts/go2_yoga_ball/manifest.json` | Manifest for current Go2 model, scene, and contract artifacts. |
| `G2C` | `artifacts/go2_yoga_ball/sim2sim_contract.md` | Written contract for Go2 deployment boundary and Sim2Sim expectations. |
| `G2T` | `artifacts/go2_yoga_ball/train_original_settings_1_8_budget_launch.json` | Launch record for the corrected Go2 20k/4096 training run using original terrain settings. |
| `G2M` | `artifacts/go2_mjlab_dreureka_port/fresh_env_record.json` | Records the FRESH `go2-mjlab` conda environment, apt dependencies, mirror-backed install commands, and the MuJoCo/MJWarp/scipy environment fixes needed before MJLab imports work. |
| `G2M` | `artifacts/go2_mjlab_dreureka_port/import_smoke.json` | Machine-readable import smoke proving the `go2-mjlab` environment loads MJLab, CUDA torch, Unitree RL MJLab Go2 tasks, and Unitree Go2 XML data. |
| `G2M` | `artifacts/go2_mjlab_dreureka_port/import_smoke.md` | Human-readable import smoke summary showing runtime package versions, RTX3090 CUDA availability, Unitree-Go2 task registration, and Go2 robot-data access. |
| `G2M` | `artifacts/go2_mjlab_dreureka_port/source_contract.json` | Machine-readable source contract comparing DrEureka Go2 yoga-ball requirements with home-space MJLab/Unitree RL MJLab sources and the caller-project port that now uses MJLab built-in Perlin terrain at Isaac-side scale. |
| `G2M` | `artifacts/go2_mjlab_dreureka_port/source_contract.md` | Human-readable source contract naming the Go2 robot, yoga-ball task, reward/observation/termination contract, built-in MJLab Perlin terrain requirement, fixed terrain-origin reset semantics, and 1/8-budget semantics. |
| `G2M` | `artifacts/go2_mjlab_dreureka_port/task_config_smoke.json` | Machine-readable proof that `DrEureka-Go2-YogaBall` registers, steps on CUDA with 20x20 built-in `hf_perlin_noise` terrain tiles of size 5m, assigns terrain origins inside the Isaac-like row/type range, uses Unitree RL MJLab hip/thigh/calf PD gains, exposes MJLab term-major 56x15 actor observations, builds the RSL-RL critic from actor history plus an 11-D privileged group, removes velocity commands, and samples pretrained ball/friction/restitution/motor/lag ranges. |
| `G2M` | `artifacts/go2_mjlab_dreureka_port/task_config_smoke.md` | Human-readable task-config smoke summary for the corrected Unitree-PD, Isaac-scale built-in-Perlin MJLab Go2 yoga-ball task registration, terrain-origin assignment check, one-step runtime check, and actor/critic model input dimensions. |
| `G2M` | `artifacts/go2_mjlab_dreureka_port/train_dry_run_health.json` | Machine-readable health report proving the built-in-Perlin MJLab PPO dry run completed one learning iteration without NaN text or traceback. |
| `G2M` | `artifacts/go2_mjlab_dreureka_port/train_dry_run_health.md` | Human-readable health summary for the built-in-Perlin MJLab PPO dry run. |
| `G2M` | `artifacts/go2_mjlab_dreureka_port/train_dry_run_launch.json` | Launch record for the verified tiny MJLab PPO dry run using 2 envs, 20x20 built-in `hf_perlin_noise` terrain, 5m tiles, 0.05m grid scale, and raised contact capacity. |
| `G2M` | `artifacts/go2_mjlab_dreureka_port/train_dry_run_reward_curve.csv` | TensorBoard-derived reward curve for the built-in-Perlin MJLab PPO dry run, retained as evidence that reward extraction still works after the terrain change. |
| `G2M` | `artifacts/go2_mjlab_dreureka_port/train_dry_run_reward_curve.svg` | Plot of the built-in-Perlin MJLab PPO dry-run reward curve. |
| `S` | `docker/isaacgym.Dockerfile` | Docker image definition for Isaac Gym training/playback with heavy dependencies kept outside host Python. |
| `S` | `docker/mujoco_sim2sim.Dockerfile` | Docker image definition for MuJoCo Sim2Sim, LCM/DDS bridge execution, and replay rendering. |
| `G1T` | `logs/go1_yoga_ball/default_train/isaacgym_playback/play_default_train_isaacgym.log` | Console log from local Go1 trained-policy Isaac playback. |
| `G1T` | `logs/go1_yoga_ball/default_train/mujoco_sim2sim/policy.log` | Policy-process log from local Go1 trained-policy Sim2Sim. |
| `G1T` | `logs/go1_yoga_ball/default_train/mujoco_sim2sim/policy_timing.csv` | Local Go1 trained-policy inference timing data for Sim2Sim. |
| `G1T` | `logs/go1_yoga_ball/default_train/mujoco_sim2sim/replay.csv` | Local Go1 trained-policy MuJoCo replay trajectory. |
| `G1T` | `logs/go1_yoga_ball/default_train/mujoco_sim2sim/sequence_events.csv` | Release and control-event timeline for local Go1 trained-policy Sim2Sim. |
| `G1T` | `logs/go1_yoga_ball/default_train/mujoco_sim2sim/sim_bridge.log` | MuJoCo bridge console log for local Go1 trained-policy Sim2Sim. |
| `G1T` | `logs/go1_yoga_ball/default_train/mujoco_sim2sim/sim_bridge_summary.json` | Bridge-level summary for local Go1 trained-policy Sim2Sim. |
| `G1T` | `logs/go1_yoga_ball/default_train/mujoco_sim2sim/simulator_status.csv` | Wall-clock and simulation-status samples for local Go1 trained-policy Sim2Sim. |
| `G1T` | `logs/go1_yoga_ball/default_train/train/runs_after.txt` | DrEureka run-directory snapshot after local Go1 training launch. |
| `G1T` | `logs/go1_yoga_ball/default_train/train/runs_before.txt` | DrEureka run-directory snapshot before local Go1 training launch. |
| `G1T` | `logs/go1_yoga_ball/default_train/train/train.log` | Console log for the local Go1 default 1/8 training run. |
| `G1T` | `logs/go1_yoga_ball/default_train/train_config_smoke/train_config_smoke.log` | Smoke log proving the local Go1 training configuration launched before full local training. |
| `G1P` | `logs/go1_yoga_ball/pretrained/isaacgym_playback/play_pretrained_isaacgym.log` | Console log from pretrained Go1 Isaac Gym playback. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim/direct_release_smoke.csv` | Direct-release baseline showing unassisted Go1 behavior without policy control. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim/policy.log` | Policy-process log from main pretrained Go1 Sim2Sim. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim/policy_timing.csv` | Inference timing data for main pretrained Go1 Sim2Sim. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim/replay.csv` | Main pretrained Go1 MuJoCo replay trajectory. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim/sequence_events.csv` | Release and control-event timeline for main pretrained Go1 Sim2Sim. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim/sim_bridge.log` | MuJoCo bridge console log for main pretrained Go1 Sim2Sim. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim/sim_bridge_summary.json` | Bridge-level summary for main pretrained Go1 Sim2Sim. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim/simulator_status.csv` | Wall-clock and simulation-status samples for main pretrained Go1 Sim2Sim. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_control_removal/policy.log` | Policy log for the pretrained Go1 control-removal test. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_control_removal/policy_timing.csv` | Inference timing data during the pretrained Go1 control-removal test. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_control_removal/replay.csv` | Replay trajectory proving pretrained Go1 loses behavior after control removal. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_control_removal/sequence_events.csv` | Event timeline showing when pretrained Go1 control was removed. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_control_removal/sim_bridge.log` | MuJoCo bridge console log for the pretrained Go1 control-removal test. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_control_removal/sim_bridge_summary.json` | Bridge-level summary for the pretrained Go1 control-removal test. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_control_removal/simulator_status.csv` | Wall-clock and simulation-status samples for the pretrained Go1 control-removal test. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_1/direct_release_smoke.csv` | Direct-release baseline paired with repeated pretrained Go1 Sim2Sim run 1. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_1/policy.log` | Policy log for repeated pretrained Go1 Sim2Sim run 1. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_1/policy_timing.csv` | Inference timing data for repeated pretrained Go1 Sim2Sim run 1. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_1/replay.csv` | Replay trajectory for repeated pretrained Go1 Sim2Sim run 1. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_1/sequence_events.csv` | Release timeline for repeated pretrained Go1 Sim2Sim run 1. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_1/sim_bridge.log` | Bridge console log for repeated pretrained Go1 Sim2Sim run 1. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_1/sim_bridge_summary.json` | Bridge summary for repeated pretrained Go1 Sim2Sim run 1. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_1/simulator_status.csv` | Wall-clock and simulation-status samples for repeated pretrained Go1 Sim2Sim run 1. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_2/direct_release_smoke.csv` | Direct-release baseline paired with repeated pretrained Go1 Sim2Sim run 2. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_2/policy.log` | Policy log for repeated pretrained Go1 Sim2Sim run 2. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_2/policy_timing.csv` | Inference timing data for repeated pretrained Go1 Sim2Sim run 2. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_2/replay.csv` | Replay trajectory for repeated pretrained Go1 Sim2Sim run 2. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_2/sequence_events.csv` | Release timeline for repeated pretrained Go1 Sim2Sim run 2. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_2/sim_bridge.log` | Bridge console log for repeated pretrained Go1 Sim2Sim run 2. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_2/sim_bridge_summary.json` | Bridge summary for repeated pretrained Go1 Sim2Sim run 2. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_2/simulator_status.csv` | Wall-clock and simulation-status samples for repeated pretrained Go1 Sim2Sim run 2. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_3/direct_release_smoke.csv` | Direct-release baseline paired with repeated pretrained Go1 Sim2Sim run 3. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_3/policy.log` | Policy log for repeated pretrained Go1 Sim2Sim run 3. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_3/policy_timing.csv` | Inference timing data for repeated pretrained Go1 Sim2Sim run 3. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_3/replay.csv` | Replay trajectory for repeated pretrained Go1 Sim2Sim run 3. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_3/sequence_events.csv` | Release timeline for repeated pretrained Go1 Sim2Sim run 3. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_3/sim_bridge.log` | Bridge console log for repeated pretrained Go1 Sim2Sim run 3. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_3/sim_bridge_summary.json` | Bridge summary for repeated pretrained Go1 Sim2Sim run 3. |
| `G1P` | `logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_3/simulator_status.csv` | Wall-clock and simulation-status samples for repeated pretrained Go1 Sim2Sim run 3. |
| `G2P` | `logs/go2_yoga_ball/final_train_isaacgym_playback/playback.log` | Initial corrected Go2 Isaac playback console log before no-video/video split was finalized. |
| `G2P` | `logs/go2_yoga_ball/final_train_isaacgym_playback_no_video/playback.log` | Console log for corrected Go2 no-video playback that avoided graphics overhead. |
| `G2P` | `logs/go2_yoga_ball/final_train_isaacgym_playback_video/playback.log` | Console log for corrected Go2 video playback, including the Isaac graphics teardown exit. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/attempt_001_faithful_baseline/bridge_commands.csv` | LCM-to-DDS bridge record of policy commands converted to Unitree DDS LowCmd during the successful Go2 Sim2Sim run. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/attempt_001_faithful_baseline/bridge_lowstate.csv` | LCM-to-DDS bridge record of DDS LowState messages republished to DrEureka LCM state during the successful Go2 Sim2Sim run. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/attempt_001_faithful_baseline/commands.csv` | MuJoCo endpoint record of received DDS LowCmd targets during the successful Go2 Sim2Sim run. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/attempt_001_faithful_baseline/events.csv` | Cross-process event timeline proving command activation before support release and no fall event through 12 seconds. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/attempt_001_faithful_baseline/lcm_to_dds_bridge.log` | Console log from the Go2 LCM-to-DDS bridge process in the successful Sim2Sim run. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/attempt_001_faithful_baseline/lowstate.csv` | MuJoCo endpoint record of joint state and torque estimates sent through DDS during the successful Go2 Sim2Sim run. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/attempt_001_faithful_baseline/mujoco_dds_endpoint.log` | Console log from the Unitree MuJoCo Go2 DDS endpoint in the successful Sim2Sim run. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/attempt_001_faithful_baseline/policy_deploy.log` | Console log from the DrEureka Torch policy process using the corrected 2026-05-28 checkpoint. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/attempt_001_faithful_baseline/policy_timing.csv` | Policy loop and inference timing samples proving the controller did not lag wall clock. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/attempt_001_faithful_baseline/process_status.json` | Exit-status record showing policy, bridge, and MuJoCo endpoint containers all exited cleanly. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/attempt_001_faithful_baseline/replay.csv` | Raw MuJoCo trajectory used to render the successful Go2 Sim2Sim follow-camera video. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/attempt_001_faithful_baseline/summary.json` | MuJoCo endpoint summary for successful Go2 Sim2Sim, including release, command count, torque clipping, and no-fall result. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/attempt_001_faithful_baseline/telemetry.csv` | Per-step MuJoCo timing, support, base-height, and joint-limit telemetry for the successful Go2 Sim2Sim run. |
| `G2T` | `logs/go2_yoga_ball/train_original_settings_1_8_budget/train.log` | Console log for corrected Go2 original-settings 20k/4096 training run. |
| `G2M` | `logs/go2_mjlab_dreureka_port/preflight.log` | Preflight record confirming the MJLab port caller project resolved the workspace root and home-space MJLab/unitree_rl_mjlab sources. |
| `G2M` | `logs/go2_mjlab_dreureka_port/train_dry_run/rsl_rl/events.out.tfevents.1780141717.isaac.377297.0` | TensorBoard event file from the verified built-in-Perlin MJLab PPO dry run. |
| `G2M` | `logs/go2_mjlab_dreureka_port/train_dry_run/rsl_rl/git/eureka-workspace.diff` | RSL-RL snapshot of the workspace diff captured during the verified built-in-Perlin dry run. |
| `G2M` | `logs/go2_mjlab_dreureka_port/train_dry_run/rsl_rl/model_0.pt` | Checkpoint emitted by the verified one-iteration built-in-Perlin MJLab PPO dry run. |
| `G2M` | `logs/go2_mjlab_dreureka_port/train_dry_run/train.log` | Console log proving the MJLab PPO runner completed one learning iteration with the built-in Perlin terrain and raised contact capacity. |
| `S` | `scripts/go1_yoga_ball/deploy_lcm_policy.py` | Runs the Go1 policy process that publishes LCM commands for MuJoCo Sim2Sim. |
| `S` | `scripts/go1_yoga_ball/docker_build.sh` | Builds the Go1 Docker image entry used by the Go1 workflow scripts. |
| `S` | `scripts/go1_yoga_ball/go1_mujoco_lcm_bridge.py` | Bridges Go1 MuJoCo state and LCM commands for the working Sim2Sim reference. |
| `S` | `scripts/go1_yoga_ball/report.sh` | Generates Go1 validation reports from collected logs and artifacts. |
| `S` | `scripts/go1_yoga_ball/run.sh` | Main Go1 command entrypoint for build, train, playback, Sim2Sim, and reporting actions. |
| `S` | `scripts/go1_yoga_ball/runner.py` | Implements Go1 workflow orchestration behind `run.sh`. |
| `S` | `scripts/go2_yoga_ball/asset_inventory.py` | Audits Go2 assets and emits consistency evidence for the Unitree-derived model path. |
| `S` | `scripts/go2_yoga_ball/go2_mujoco_dds_endpoint.py` | Runs the Go2 MuJoCo DDS-side endpoint intended to mirror the real robot boundary. |
| `S` | `scripts/go2_yoga_ball/isaacgym_playback_smoke.py` | Executes corrected Go2 Isaac Gym playback and writes playback CSV/report/video artifacts. |
| `S` | `scripts/go2_yoga_ball/lcm_to_dds_bridge.py` | Converts policy LCM commands into Go2 DDS commands, including PD/action-scale mapping. |
| `S` | `scripts/go2_yoga_ball/render_mujoco_replay_video.py` | Renders MuJoCo replay CSV logs into follow-camera debug videos. |
| `S` | `scripts/go2_yoga_ball/run.sh` | Main Go2 command entrypoint for asset audit, training, playback, and Sim2Sim actions. |
| `S` | `scripts/go2_yoga_ball/runner.py` | Implements Go2 workflow orchestration behind `run.sh`. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/run.sh` | Entry point for the FRESH MJLab Go2 port caller project: preflight, source contract, environment/import/task smokes, dry run, 20-minute smoke, reward report, 1/8-budget train launch, and local MuJoCo viewer playback. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/runner.py` | Implements MJLab port evidence generation, training launch orchestration, TensorBoard reward extraction, same-iteration baseline comparison, and health reports without editing upstream repos. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/play_driver.py` | Loads the caller-project DrEureka Go2 MJLab task and a saved training checkpoint into MJLab's MuJoCo viewer so the current policy can be inspected at 1x wall-clock speed without relying on Unitree's package-level `play.py` registry import. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/train_driver.py` | Runs the registered MJLab DrEureka Go2 task through `MjlabOnPolicyRunner` with CLI-controlled env count, iteration count, save interval, terrain size, seed, launch JSON, and recorded MuJoCo solver/contact settings. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/dreureka_go2_mjlab/__init__.py` | Registers the caller-project `DrEureka-Go2-YogaBall` MJLab task without modifying MJLab, Unitree RL MJLab, or DrEureka. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/dreureka_go2_mjlab/env_cfg.py` | Defines the MJLab Go2 yoga-ball task: Unitree Go2 robot data with DrEureka pose/control overrides, ball entity, command-free DrEureka/Isaac-side actor terms flattened by MJLab's term-major history convention, privileged critic terms, Eureka rewards, body-height terminations, MJLab built-in `HfPerlinNoiseTerrainCfg` at Isaac-side 20x20 5m-tile/0.05m-grid scale, Isaac-like fixed terrain-origin assignment over rows/cols 5..14, pretrained DR ranges, and 4096-env baseline settings. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/dreureka_go2_mjlab/rl_cfg.py` | Holds the MJLab RSL-RL runner settings for the baseline reproduction, including critic observation groups `actor+critic`, 20000 iterations, save interval 1000, and tensorboard/local model logging for FRESH runs. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/dreureka_go2_mjlab/mdp/__init__.py` | Exports the caller-project observation, reward, reset, terrain-origin assignment, and termination terms used by the registered DrEureka Go2 MJLab task. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/dreureka_go2_mjlab/mdp/events.py` | Implements script-local DrEureka reset, Isaac-like fixed terrain-origin assignment, and robot/ball-scoped pretrained-style DR: ball radius/mass/inertia/friction observations, robot friction/payload/COM/motor offset/strength, action lag, pushes, gravity observation offset, and ball drag without terrain material randomization or custom MuJoCo contact-solver assignments. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/dreureka_go2_mjlab/mdp/observations.py` | Implements the caller-project observation terms not provided directly by MJLab: previous action, zero command-free gait clock, yaw, ball-relative position, ball velocity, and fixed ball material scalars. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/dreureka_go2_mjlab/mdp/rewards.py` | Implements the four EurekaReward terms for height, balance, smooth actions, and large-action penalty against MJLab scene state. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/dreureka_go2_mjlab/mdp/terminations.py` | Adds the DrEureka ball-radius fall termination used alongside time-out and terminal body-height checks. |
| `G2F` | `scripts/go2_mjlab_fresh_sim2sim/run.sh` | Entry point for host-side MJLab checkpoint-to-DDS Sim2Sim actions: preflight, source-contract, joint-order proof, deployer smoke, attempt orchestration, reporting, and video rendering. |
| `G2F` | `scripts/go2_mjlab_fresh_sim2sim/runner.py` | Orchestrates the FRESH Sim2Sim workflow around the direct MJLab DDS deployer and Unitree MuJoCo DDS endpoint without Docker. |
| `G2F` | `scripts/go2_mjlab_fresh_sim2sim/common.py` | Holds shared paths, joint-order constants, default joint angles, action scale, and Unitree RL MJLab hip/thigh/calf PD gains for translating between MJLab policy order and Unitree DDS motor order. |
| `G2F` | `scripts/go2_mjlab_fresh_sim2sim/mjlab_dds_deployer.py` | Loads an MJLab RSL-RL checkpoint, builds MJLab term-major actor observations from DDS LowState, reorders joints by name, and publishes Unitree DDS LowCmd actions with train-path PD gains. |
