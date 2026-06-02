# Current Inventory

Read this file first. It is the low-cognitive-load map of the main project line. It lists every file outside `thirdparties/`, cache folders, and `outdated/`, including ignored runtime evidence under `artifacts/` and `logs/`. If a file does not directly support one of these stages, move it to `outdated/` and update `OUTDATED_INVENTORY.md`.

## Project Outline

- `P0` Repository Map: rules, ignore policy, and this inventory system.
- `G1P` Go1 Pretrained Reference: DrEureka's pretrained Go1 yoga-ball policy works in Isaac Gym playback and MuJoCo Sim2Sim, with release/timing/control-removal evidence and replay video.
- `G1T` Go1 Default 1/8 Training: locally trained Go1 policy is kept as a mainstream comparison point against the pretrained Go1 reference, even though its policy quality is weaker.
- `G2C` Go2 Contract: Go2 train/deploy contract uses Unitree RL Gym Go2 URDF for Isaac Gym and Unitree MuJoCo/DDS plus LCM-to-DDS bridge reports for deployment consistency.
- `G2T` Go2 Corrected 1/8 Training: final corrected Go2 20k-iteration, 4096-env Isaac Gym training completed from the Unitree RL Gym Go2 model with train-time boxes_tm terrain.
- `G2P` Go2 Isaac Playback: final corrected Go2 trained-policy Isaac-side playback is complete.
- `G2S` Go2 MuJoCo/DDS Sim2Sim: corrected Go2 1/8 trained checkpoint succeeded in MuJoCo/DDS Sim2Sim on attempt 1, was rerun on 2026-05-31 inside the containerized stack, and also succeeded with host MuJoCo plus Docker policy/bridge using the default DrEureka LCM URL and no `MUJOCO_GL` override.
- `G2M` Go2 MJLab Port: FRESH host-side MJLab reproduction has a self-contained caller-project task using vendored Unitree RL MJLab Go2 XML/meshes/model constants and PD gains, MJLab term-major actor history with DrEureka/Isaac-side sensor terms, an RSL-RL critic input of actor history plus 10 physically-applied privileged values, 20x20 MJLab native 5m `HfRandomUniformTerrainCfg` hfield tiles, per-tile terrain-build roughness sampled from previous MJLab roughness max `0.08m` divided to `0.005..0.02m`, stock DrEureka `boxes_tm` startup env-origin assignment across middle rows 5..14 and columns 5..14 for 4096 envs, Isaac-style `+-0.05m` robot XY reset jitter, DrEureka Go2 `0.42m` robot init root height, and robot/ball-scoped pretrained-style DrEureka domain randomization.
- `G2F` Go2 MJLab FRESH Sim2Sim: host-side pure-DDS Go2 MuJoCo Sim2Sim runtime now targets the MJLab `model_10000.pt` checkpoint because it survived 12s in MJLab-native playback, but current DDS Sim2Sim evidence still fails after support release, so the remaining issue is deployment-scene/bridge semantics rather than checkpoint viability inside MJLab.
- `S` Orchestration: Dockerfiles and scripts that reproduce or extend the Go1 and Go2 workflows.

## Files

| Stage | File | Reason |
| --- | --- | --- |
| `P0` | `.gitignore` | Ignores `/artifacts/`, `/logs/`, `/outdated/`, fetched third-party payloads, and local build caches while keeping workflow scripts trackable. |
| `P0` | `.gitmodules` | Records the DrEureka fork submodule mount so recursive clones fetch the forked training code base. |
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
| `G2S` | `artifacts/go2_yoga_ball/final_train_sim2sim/rerun_isaac_trained_default_lcm_20260531_video.json` | Render validation for the 2026-05-31 rerun video of the same corrected Isaac-trained checkpoint. |
| `G2S` | `artifacts/go2_yoga_ball/final_train_sim2sim/report.md` | Human-readable final report proving corrected Go2 Sim2Sim succeeded on attempt 1. |
| `G2S` | `artifacts/go2_yoga_ball/final_train_sim2sim/summary.json` | Machine-readable metrics for corrected Go2 Sim2Sim release, timing, command path, torque, and joint-limit checks. |
| `G2S` | `artifacts/go2_yoga_ball/final_train_sim2sim/videos/go2_final_train_sim2sim_success.mp4` | Follow-camera video rendered from raw MuJoCo replay for the successful corrected Go2 Sim2Sim run. |
| `G2S` | `artifacts/go2_yoga_ball/final_train_sim2sim/videos/rerun_isaac_trained_default_lcm_20260531.mp4` | Follow-camera video rendered from the 2026-05-31 rerun raw MuJoCo replay. |
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
| `G2M` | `artifacts/go2_mjlab_dreureka_port/fresh_env_record.json` | Records the FRESH `go2-mjlab` conda environment, apt dependencies, install command for `mjlab==1.2.0` with proven MuJoCo/MJWarp/scipy/warp pins, and confirms `unitree_rl_mjlab` is no longer needed for training. |
| `G2M` | `artifacts/go2_mjlab_dreureka_port/import_smoke.json` | Machine-readable import smoke proving the `go2-mjlab` environment loads installed MJLab, CUDA torch, the caller-project task, and the vendored Go2 XML data without importing Unitree's `src` package. |
| `G2M` | `artifacts/go2_mjlab_dreureka_port/import_smoke.md` | Human-readable import smoke summary showing runtime package versions, RTX3090 CUDA availability, caller-task registration, and vendored Go2 robot-data access. |
| `G2M` | `artifacts/go2_mjlab_dreureka_port/source_contract.json` | Machine-readable source contract proving MJLab training now uses an installed MJLab package plus vendored Go2 XML/mesh/model constants, with zero third-party checkout requirements for the training path. |
| `G2M` | `artifacts/go2_mjlab_dreureka_port/source_contract.md` | Human-readable source contract excerpts for the self-contained MJLab caller task, including the local Go2 robot factory and optional upstream provenance references. |
| `G2M` | `artifacts/go2_mjlab_dreureka_port/task_config_smoke.json` | Machine-readable 4096-env task smoke proving the MJLab task registers, builds 20x20 5m `random_rough` hfield terrain, exposes actor/critic observation dimensions, and keeps PPO/RSL-RL dimensions consistent after the terrain change. |
| `G2M` | `artifacts/go2_mjlab_dreureka_port/task_config_smoke.md` | Human-readable summary of the 4096-env MJLab task smoke after switching to 20x20 5m random-rough hfield tiles. |
| `G2M` | `artifacts/go2_mjlab_dreureka_port/train_1_8_budget_launch.json` | Launch record for the MJLab 4096-env, 20000-iteration, save-interval-1000 training run using the self-contained caller project and vendored Go2 robot data. |
| `G2M` | `artifacts/go2_mjlab_dreureka_port/mjlab_scene_init_20x20_5m_random_rough.json` | Render metadata proving the current 4096-env MJLab task produced a nonblank reset-scene image from env 0 on the 20x20 native random-rough terrain. |
| `G2M` | `artifacts/go2_mjlab_dreureka_port/mjlab_scene_init_20x20_5m_random_rough.png` | Current reset-scene screenshot for the MJLab DrEureka Go2 task after switching to 20x20 5m random-rough tiles and lifting the yoga ball above the tile max height. |
| `G2M` | `artifacts/go2_mjlab_dreureka_port/reward_curve_isaac_mjlab_comparison_pretrain_full_raw_x.json` | Machine-readable source summary for the reward comparison plot, including MJLab `x50` scaling, every-10th-point MJLab downsampling before smoothing, pretrained Go1 full-run raw `x=iteration` horizontal axis, source log paths, point counts, and smoothed min/max/endpoint values for each curve. |
| `G2M` | `artifacts/go2_mjlab_dreureka_port/reward_curve_isaac_mjlab_comparison_pretrain_full_raw_x.png` | Plot comparing 9-point-smoothed MJLab Go2 mean reward, after `x50` scaling and every-10th-point downsampling, against corrected Isaac Go2, local Isaac Go1, and the full pretrained Go1 reward curve without first-2500 clamping or horizontal stretching. |
| `G2M` | `artifacts/go2_mjlab_dreureka_port/terrain_4096_verification.json` | Machine-readable proof that the current MJLab task builds 400 5m hfield tiles at 0.25m horizontal units, samples tile roughness in `0.005..0.02m`, assigns 4096 envs to stock DrEureka `boxes_tm` middle rows 5..14 and columns 5..14 with the Isaac `floor(env_id / (4096 / 10)) + 5` column formula, applies robot-only `+-0.05m` XY reset jitter, and keeps the ball bottom just above each tile's max height. |
| `G2F` | `artifacts/go2_mjlab_fresh_sim2sim/` | Current MJLab-to-DDS Sim2Sim evidence: `model_10000.pt` deployer smoke and joint-order proof pass, rendered DDS videos show the policy still falls after support release, `videos/go2_mjlab_native_playback_model_10000_seed_0.mp4` proves the same checkpoint survives 12s in MJLab-native playback, `videos/go2_mjlab_native_playback_model_10000_seed_1.mp4` captures an early MJLab-native failed reset for diagnosis, `videos/go2_mjlab_fresh_sim2sim_attempt_007_seed0_native_scene.mp4` replays the same checkpoint with seed-0 native reset/physics values passed into the Unitree endpoint, `videos/go2_mjlab_fresh_sim2sim_attempt_008_seed0_scene_release_z095.mp4` repeats that seed-0 scene with robot root height overridden to 0.95m at 200Hz endpoint PD, `videos/go2_mjlab_fresh_sim2sim_attempt_009_seed0_scene_release_z095_dt002.mp4` repeats attempt 008 at 500Hz endpoint PD and still falls, and `videos/go2_mjlab_fresh_sim2sim_flat_terrain_outdated_model_4000.mp4` is a one-off comparison using the archived flat-terrain invalid checkpoint. |
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
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/rerun_isaac_trained_default_lcm_20260531/events.csv` | Event timeline for the 2026-05-31 rerun showing command activation, release, balance window, and no fall. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/rerun_isaac_trained_default_lcm_20260531/bridge_commands.csv` | LCM-to-DDS bridge record of policy commands converted to Unitree DDS LowCmd during the 2026-05-31 rerun. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/rerun_isaac_trained_default_lcm_20260531/bridge_lowstate.csv` | LCM-to-DDS bridge record of DDS LowState messages republished to DrEureka LCM state during the 2026-05-31 rerun. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/rerun_isaac_trained_default_lcm_20260531/commands.csv` | MuJoCo endpoint record of received DDS LowCmd targets during the 2026-05-31 rerun. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/rerun_isaac_trained_default_lcm_20260531/lcm_to_dds_bridge.log` | LCM-to-DDS bridge log for the 2026-05-31 rerun using the default DrEureka LCM URL. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/rerun_isaac_trained_default_lcm_20260531/mujoco_dds_endpoint.log` | MuJoCo DDS endpoint log for the 2026-05-31 rerun. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/rerun_isaac_trained_default_lcm_20260531/policy_deploy.log` | DrEureka policy console log for the 2026-05-31 rerun using the corrected Isaac-trained checkpoint. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/rerun_isaac_trained_default_lcm_20260531/policy_timing.csv` | Policy loop and inference timing samples for the 2026-05-31 rerun. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/rerun_isaac_trained_default_lcm_20260531/process_status.json` | Exit-status record for the 2026-05-31 rerun showing policy, bridge, and endpoint all completed cleanly. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/rerun_isaac_trained_default_lcm_20260531/replay.csv` | Raw MuJoCo trajectory used to render the 2026-05-31 rerun follow-camera video. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/rerun_isaac_trained_default_lcm_20260531/summary.json` | MuJoCo endpoint summary for the 2026-05-31 rerun with release, command count, torque clipping, and no-fall result. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/rerun_isaac_trained_default_lcm_20260531/telemetry.csv` | Per-step MuJoCo timing, support, base-height, and joint-limit telemetry for the 2026-05-31 rerun. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/host_mujoco_docker_policy_20260531_retry/bridge_commands.csv` | Docker bridge record of policy commands converted to DDS during the host-MuJoCo/Docker-policy run. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/host_mujoco_docker_policy_20260531_retry/bridge_lowstate.csv` | Docker bridge record of host MuJoCo DDS LowState messages republished to DrEureka LCM during the mixed-topology run. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/host_mujoco_docker_policy_20260531_retry/commands.csv` | Host MuJoCo endpoint record of received DDS LowCmd targets during the mixed-topology run. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/host_mujoco_docker_policy_20260531_retry/events.csv` | Event timeline for the mixed-topology run showing first DDS command, support release, balance window, and no fall. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/host_mujoco_docker_policy_20260531_retry/lcm_to_dds_bridge.log` | Docker LCM-to-DDS bridge console log for the mixed-topology run. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/host_mujoco_docker_policy_20260531_retry/lowstate.csv` | Host MuJoCo endpoint record of joint state and torque estimates sent through DDS during the mixed-topology run. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/host_mujoco_docker_policy_20260531_retry/mujoco_dds_endpoint.log` | Host `go2-mjlab` Conda endpoint console log for the mixed-topology run, with no `MUJOCO_GL` override. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/host_mujoco_docker_policy_20260531_retry/policy_deploy.log` | Docker Isaac policy console log for the mixed-topology run. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/host_mujoco_docker_policy_20260531_retry/policy_timing.csv` | Policy loop and inference timing samples from the Docker policy process in the mixed-topology run. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/host_mujoco_docker_policy_20260531_retry/process_status.json` | Exit-status record for the mixed-topology run showing host endpoint, Docker bridge, and Docker policy all completed cleanly. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/host_mujoco_docker_policy_20260531_retry/replay.csv` | Raw host MuJoCo trajectory from the mixed-topology run. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/host_mujoco_docker_policy_20260531_retry/summary.json` | Host MuJoCo endpoint summary for the mixed-topology run with release, command count, torque clipping, and no-fall result. |
| `G2S` | `logs/go2_yoga_ball/final_train_sim2sim/host_mujoco_docker_policy_20260531_retry/telemetry.csv` | Per-step host MuJoCo timing, support, base-height, and joint-limit telemetry for the mixed-topology run. |
| `G2T` | `logs/go2_yoga_ball/train_original_settings_1_8_budget/train.log` | Console log for corrected Go2 original-settings 20k/4096 training run. |
| `G2M` | `logs/go2_mjlab_dreureka_port/preflight.log` | Preflight record confirming the MJLab port caller project resolved the workspace root and vendored Go2 XML path for new-machine training. |
| `G2M` | `logs/go2_mjlab_dreureka_port/terrain_4096_verification/verify.log` | Raw console log from the 4096-env terrain verification run that built the 20x20 hfield grid and emitted all terrain/origin/jitter checks as passing. |
| `G2F` | `logs/go2_mjlab_fresh_sim2sim/` | Raw playback and Sim2Sim logs for MJLab checkpoint deployment: `mjlab_playback_model_10000/playback.csv` and `mjlab_playback_video/playback.csv` prove `model_10000.pt` survives 12s natively; `attempt_003_model_10000`, `attempt_004_model_10000_mjlab_reset_height`, and later debug attempts show DDS command transport works but the robot falls after release; `attempt_007_seed0_native_scene/` records the extracted seed-0 MJLab native reset/physics state and the matched Unitree endpoint replay; `attempt_008_seed0_scene_release_z095/` records the 0.95m root-height release variant at 200Hz endpoint PD; `attempt_009_seed0_scene_release_z095_dt002/` repeats the same seed-state and checkpoint at 500Hz endpoint PD and still falls; `flat_terrain_outdated_model_4000/` records the archived flat-terrain invalid checkpoint comparison. |
| `S` | `scripts/go1_yoga_ball/deploy_lcm_policy.py` | Runs the Go1 policy process that publishes LCM commands for MuJoCo Sim2Sim. |
| `S` | `scripts/go1_yoga_ball/docker_build.sh` | Builds the Go1 Docker image entry used by the Go1 workflow scripts. |
| `S` | `scripts/go1_yoga_ball/go1_mujoco_lcm_bridge.py` | Bridges Go1 MuJoCo state and LCM commands for the working Sim2Sim reference. |
| `S` | `scripts/go1_yoga_ball/report.sh` | Generates Go1 validation reports from collected logs and artifacts. |
| `S` | `scripts/go1_yoga_ball/run.sh` | Main Go1 command entrypoint for build, train, playback, Sim2Sim, and reporting actions. |
| `S` | `scripts/go1_yoga_ball/runner.py` | Implements Go1 workflow orchestration behind `run.sh`. |
| `S` | `scripts/go2_yoga_ball/asset_inventory.py` | Audits Go2 assets and emits consistency evidence for the Unitree-derived model path. |
| `S` | `scripts/go2_yoga_ball/go2_mujoco_dds_endpoint.py` | Runs the Go2 MuJoCo DDS-side endpoint intended to mirror the real robot boundary, with optional seed-state overrides for MJLab-matched ball mass/inertia/friction, floor height, root pose/velocity, base mass/COM, robot friction, and motor strength. |
| `S` | `scripts/go2_yoga_ball/isaacgym_playback_smoke.py` | Executes corrected Go2 Isaac Gym playback and writes playback CSV/report/video artifacts. |
| `S` | `scripts/go2_yoga_ball/lcm_to_dds_bridge.py` | Converts policy LCM commands into Go2 DDS commands, including PD/action-scale mapping. |
| `S` | `scripts/go2_yoga_ball/render_mujoco_replay_video.py` | Renders MuJoCo replay CSV logs into follow-camera debug videos. |
| `S` | `scripts/go2_yoga_ball/run.sh` | Main Go2 command entrypoint for asset audit, training, playback, and Sim2Sim actions. |
| `S` | `scripts/go2_yoga_ball/runner.py` | Implements Go2 workflow orchestration behind `run.sh`. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/run.sh` | Entry point for the FRESH MJLab Go2 port caller project: preflight, source contract, environment/import/task smokes, 4096-env terrain assignment verification, reset-scene rendering, 4096-env smoke training, 1/8-budget training, report generation, and local MuJoCo viewer playback. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/runner.py` | Implements MJLab port evidence generation, source-contract/import checks for installed MJLab plus vendored Go2 data, 4096-env task smoke, 4096-env Isaac-like terrain assignment verification, reset-scene rendering, training launch orchestration from the workspace root, TensorBoard reward extraction, same-iteration baseline comparison, and health reports for smoke and 1/8-budget runs. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/play_driver.py` | Loads the caller-project DrEureka Go2 MJLab task and a saved training checkpoint into MJLab's MuJoCo viewer so the current policy can be inspected at 1x wall-clock speed without relying on Unitree's package-level `play.py` registry import. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/train_driver.py` | Runs the registered MJLab DrEureka Go2 task through `MjlabOnPolicyRunner` with CLI-controlled env count, iteration count, save interval, optional terrain rows/cols overrides, seed, launch JSON, and recorded MuJoCo solver/contact settings. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/dreureka_go2_mjlab/__init__.py` | Registers the caller-project `DrEureka-Go2-YogaBall` MJLab task without modifying MJLab, Unitree RL MJLab, or DrEureka. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/dreureka_go2_mjlab/assets/unitree_go2/` | Vendored Unitree Go2 MJCF runtime bundle: `go2.xml`, `scene_go2.xml`, and 16 OBJ meshes copied from `unitree_rl_mjlab` so MJLab training on a new machine does not require cloning that repository. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/dreureka_go2_mjlab/env_cfg.py` | Defines the MJLab Go2 yoga-ball task: vendored Unitree Go2 robot data with DrEureka pose/control overrides, DrEureka Go2 `0.42m` robot init root height, ball entity, command-free DrEureka/Isaac-side actor terms flattened by MJLab's term-major history convention, physically-applied privileged critic terms, Eureka rewards, body-height terminations, 20x20 native 5m random-rough hfield tiles with per-tile roughness sampled from `0.005..0.02m`, Isaac-like startup terrain-origin assignment, pretrained DR ranges, and 4096-env baseline settings. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/dreureka_go2_mjlab/go2_robot.py` | Local Go2 robot factory mirroring the Unitree MJLab constants used by this task: loads the vendored XML/meshes, applies full-collision settings, and exposes the three actuator groups needed by MJLab training. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/dreureka_go2_mjlab/rl_cfg.py` | Holds the MJLab RSL-RL runner settings for the baseline reproduction, including critic observation groups `actor+critic`, 20000 iterations, save interval 1000, and tensorboard/local model logging for FRESH runs. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/dreureka_go2_mjlab/mdp/__init__.py` | Exports the caller-project observation, reward, reset, terrain-origin assignment, and termination terms used by the registered DrEureka Go2 MJLab task. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/dreureka_go2_mjlab/mdp/events.py` | Implements script-local DrEureka reset, Isaac-like startup terrain-origin assignment, robot-only `+-0.05m` XY reset jitter, and robot/ball-scoped pretrained-style DR: ball radius/mass/inertia/friction, robot friction/payload/COM/motor offset/strength, action lag, pushes, gravity observation offset, and ball drag without pretending unsupported restitution/compliance or terrain material randomization is active. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/dreureka_go2_mjlab/mdp/observations.py` | Implements the caller-project observation terms not provided directly by MJLab: previous action, zero command-free gait clock, yaw, ball-relative position, ball velocity, and ball friction scalar. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/dreureka_go2_mjlab/mdp/rewards.py` | Implements the four EurekaReward terms for height, balance, smooth actions, and large-action penalty against MJLab scene state. |
| `G2M` | `scripts/go2_mjlab_dreureka_port/dreureka_go2_mjlab/mdp/terminations.py` | Adds the DrEureka ball-radius fall termination used alongside time-out and terminal body-height checks. |
| `G2F` | `scripts/go2_mjlab_fresh_sim2sim/run.sh` | Entry point for host-side MJLab checkpoint-to-DDS Sim2Sim actions: preflight, source-contract, joint-order proof, deployer smoke, MJLab-native playback/video export, attempt orchestration, reporting, and video rendering. |
| `G2F` | `scripts/go2_mjlab_fresh_sim2sim/runner.py` | Orchestrates the FRESH Sim2Sim workflow around the direct MJLab DDS deployer and Unitree MuJoCo DDS endpoint without Docker, and exports seeded MJLab-native playback videos for checkpoint viability checks. |
| `G2F` | `scripts/go2_mjlab_fresh_sim2sim/common.py` | Holds the selected `model_10000.pt` checkpoint path, joint-order constants, default joint angles, action scale, and Unitree RL MJLab hip/thigh/calf PD gains for translating between MJLab policy order and Unitree DDS motor order. |
| `G2F` | `scripts/go2_mjlab_fresh_sim2sim/mjlab_dds_deployer.py` | Loads an MJLab RSL-RL checkpoint, builds MJLab term-major actor observations from DDS LowState, reorders joints by name, and publishes Unitree DDS LowCmd actions with train-path PD gains plus optional MJLab seed-state motor offsets. |
