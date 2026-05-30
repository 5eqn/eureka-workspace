# Outdated Inventory

This file accounts for everything under `outdated/`. Current files must not be collapsed, but outdated folders may be collapsed when that reduces reader effort without hiding why the archive exists.

- Accounted files under `outdated/`: `558`
- Inventory rows: `66`

| Path Under `outdated/` | Reason |
| --- | --- |
| `GOAL_GO1_YOGA_BALL_SIM2REAL.md` | Superseded by the current project outline in `CURRENT_INVENTORY.md`; it described the earlier Go1-only goal. |
| `GOAL_GO2_YOGA_BALL_POST_TRAINING_SIM2SIM.md` | Superseded Go2 post-training Sim2Sim goal from the wrong-model debugging period. |
| `GOAL_GO2_YOGA_BALL_SIM2REAL.md` | Superseded Go2 migration goal that still included outdated MJLab and wrong-asset assumptions. |
| `LESSONS_LEARNED.md` | Historical notes from earlier training-command discussions; not part of the current minimal project map. |
| `REPO_FILE_INVENTORY.md` | Replaced by the split `CURRENT_INVENTORY.md` and `OUTDATED_INVENTORY.md` system. |
| `artifacts/codex_session_019e5ccf_visible_transcript.md` | Compaction/debug transcript used to recover earlier context, not runtime evidence for the main workflow. |
| `artifacts/go1_yoga_ball/mjlab_runtime_smoke.json` | MJLab Go1 smoke result from the abandoned MJLab port path. |
| `artifacts/go1_yoga_ball/mjlab_yoga_ball_task_smoke.json` | MJLab Go1 task smoke result from the abandoned MJLab port path. |
| `artifacts/go1_yoga_ball/mjlab_yoga_ball_train_smoke.json` | MJLab Go1 training smoke result from the abandoned MJLab port path. |
| `artifacts/go1_yoga_ball/mjlab_yoga_ball_trained_playback.json` | MJLab Go1 trained playback result from the abandoned MJLab port path. |
| `artifacts/go1_yoga_ball/mujoco_asset_smoke.json` | Early Go1 MuJoCo asset smoke result superseded by the current pretrained/default-train evidence set. |
| `artifacts/go1_yoga_ball/phase_mjlab_report.md` | Human-readable MJLab Go1 report from the abandoned MJLab port path. |
| `artifacts/go1_yoga_ball/phase_mjlab_summary.json` | Machine-readable MJLab Go1 summary from the abandoned MJLab port path. |
| `artifacts/go2_mjlab_dreureka_port_flat_terrain_invalid_2026-05-29/` | Collapsed folder covering MJLab Go2 smoke/train/dry-run evidence from the flat-terrain attempt that the user rejected as invalid for the baseline. |
| `artifacts/go2_mjlab_dreureka_port_hfield_contact_spam_2026-05-29/` | Collapsed folder covering the launch record from the 4096-env random_rough smoke attempt that reached PPO but produced pathological hfield collision-overflow warning spam before terrain resolution was coarsened. |
| `artifacts/go2_mjlab_dreureka_port_interrupted_random_uniform_2026-05-30/` | Collapsed folder covering the launch record for the interrupted MJLab 1/8-budget run that still used the superseded random-uniform terrain instead of MJLab built-in Perlin at Isaac-side scale. |
| `artifacts/go2_mjlab_dreureka_port_exact_hfield_dry_run_2026-05-30/` | Collapsed folder covering the 2-env exact-hfield dry-run artifacts that were removed from the current workflow because tiny-env dry runs do not validate 4096-env terrain collision behavior. |
| `artifacts/go2_mjlab_dreureka_port_exact_hfield_overflow_2026-05-30/` | Collapsed folder covering the launch record for the exact DrEureka signed-Perlin hfield 4096-env run that still produced full-screen MuJoCo Warp hfield collision-overflow warnings at `mjMAXCONPAIR=512`. |
| `artifacts/go2_mjlab_dreureka_port_old_pd_terrain_2026-05-30/` | Collapsed folder covering MJLab train/dry-run/smoke artifacts from the superseded small-terrain and old-PD configuration, archived so it cannot be mistaken for the corrected Unitree-PD, 20m-terrain train line. |
| `artifacts/go2_mjlab_dreureka_port_rough_box_grid_oom_2026-05-29/` | Collapsed folder covering the killed 4096-env rough box-grid smoke launch record; superseded because the primitive-heavy terrain exhausted memory before training. |
| `artifacts/go2_mjlab_dreureka_port_rough_hfield_overflow_2026-05-29/` | Collapsed folder covering the MJLab heightfield rough-terrain dry-run evidence that failed due to contact-capacity overflow with the yoga-ball scene. |
| `artifacts/go2_mjlab_dreureka_port_short_smoke_300iter_2026-05-29/` | Collapsed folder covering the successful 300-iteration MJLab smoke artifacts that were archived only because the run finished in about 9 minutes, shorter than the requested 20-minute smoke. |
| `artifacts/go2_mjlab_fresh_sim2sim_old_checkpoint_2026-05-30/` | Collapsed folder covering host FRESH Sim2Sim reports, videos, joint-order proof, and deployer smoke from the archived old MJLab checkpoint before the corrected actor/critic and PD train path. |
| `artifacts/go2_yoga_ball/build/go2_description_isaacgym.urdf` | Invalid Go2 Isaac asset from the bad go2_description conversion; replaced by Unitree RL Gym Go2 URDF path. |
| `artifacts/go2_yoga_ball/go2_asset_inventory.json` | Early Go2 asset inventory from the wrong-asset migration phase. |
| `artifacts/go2_yoga_ball/go2_train_smoke_run.json` | Early Go2 smoke-training selection from the wrong-asset migration phase. |
| `artifacts/go2_yoga_ball/go2_train_smoke_selected_run.txt` | Pointer to the early Go2 smoke run that used superseded setup. |
| `artifacts/go2_yoga_ball/phase_go2_train_report.json` | Go2 train report from before the corrected Unitree RL Gym asset path. |
| `artifacts/go2_yoga_ball/phase_go2_train_report.md` | Human-readable Go2 train report from before the corrected Unitree RL Gym asset path. |
| `artifacts/go2_yoga_ball/post_training_sim2sim/` | Collapsed folder covering 31 wrong-model or unsuccessful Go2 Sim2Sim rendered/debug artifacts. |
| `artifacts/go2_yoga_ball/reward_curve_comparison.csv` | Reward-curve comparison generated for the superseded wrong-asset Go2 training investigation. |
| `artifacts/go2_yoga_ball/reward_curve_comparison.json` | Machine-readable reward comparison for the superseded wrong-asset Go2 training investigation. |
| `artifacts/go2_yoga_ball/reward_curve_comparison.md` | Human-readable reward comparison for the superseded wrong-asset Go2 training investigation. |
| `artifacts/go2_yoga_ball/reward_curve_total.svg` | Plot from the superseded wrong-asset Go2 reward-curve comparison. |
| `artifacts/go2_yoga_ball/train_1_8_budget_gate.json` | Health gate output for the first failed/wrong-asset Go2 1/8 run. |
| `artifacts/go2_yoga_ball/train_1_8_budget_gate_failure.json` | Failure record for the first failed/wrong-asset Go2 1/8 run. |
| `artifacts/go2_yoga_ball/train_1_8_budget_health.json` | Health summary for the first failed/wrong-asset Go2 1/8 run. |
| `artifacts/go2_yoga_ball/train_1_8_budget_health.md` | Human-readable health report for the first failed/wrong-asset Go2 1/8 run. |
| `artifacts/go2_yoga_ball/train_1_8_budget_launch.json` | Launch record for the first failed/wrong-asset Go2 1/8 run. |
| `artifacts/go2_yoga_ball/train_1_8_budget_launch_guard.json` | Guard record for the first failed/wrong-asset Go2 1/8 run. |
| `artifacts/go2_yoga_ball/train_1_8_budget_resume_launch.json` | Resume launch record for the first failed/wrong-asset Go2 1/8 run. |
| `artifacts/go2_yoga_ball/train_1_8_budget_selected_run.txt` | Selected-run pointer for the first failed/wrong-asset Go2 1/8 run. |
| `artifacts/go2_yoga_ball/train_unitree_rl_gym_1_8_budget_launch.json` | Intermediate Unitree RL Gym Go2 launch record superseded by `train_original_settings_1_8_budget_launch.json`. |
| `artifacts/go2_yoga_ball/unitree_rl_gym_asset_old_policy_playback/` | Collapsed folder covering 4 playback files for the old policy on the corrected asset; useful only as wrong-policy shape debugging. |
| `docker/mjlab.Dockerfile` | MJLab container definition from the abandoned MJLab port path. |
| `logs/go1_yoga_ball/mjlab_train/` | Collapsed folder covering 8 MJLab Go1 smoke/train/playback logs from the abandoned MJLab port path. |
| `logs/go2_mjlab_dreureka_port_flat_terrain_invalid_2026-05-29/` | Collapsed folder covering flat-terrain MJLab Go2 smoke/train/dry-run logs and TensorBoard process records that must not be mistaken for the rough-terrain baseline. |
| `logs/go2_mjlab_dreureka_port_hfield_contact_spam_2026-05-29/` | Collapsed folder covering the random_rough smoke log tree whose 0.10 m hfield grid caused multi-gigabyte hfield collision-overflow warning spam with the yoga ball. |
| `logs/go2_mjlab_dreureka_port_interrupted_random_uniform_2026-05-30/` | Collapsed folder covering the stopped MJLab 1/8-budget run logs and checkpoints from the superseded random-uniform terrain path. |
| `logs/go2_mjlab_dreureka_port_exact_hfield_dry_run_2026-05-30/` | Collapsed folder covering the 2-env exact-hfield dry-run log tree and checkpoint that were removed from the current workflow because they are not a valid gate for 4096-env MJLab rough terrain. |
| `logs/go2_mjlab_dreureka_port_exact_hfield_overflow_2026-05-30/` | Collapsed folder covering the stopped exact DrEureka signed-Perlin hfield 4096-env run, including the 882 MB console log proving the hfield collision path is not viable for the yoga-ball terrain at Isaac 0.05 m resolution. |
| `logs/go2_mjlab_dreureka_port_old_pd_terrain_2026-05-30/` | Collapsed folder covering MJLab dry-run, smoke, and 1/8-budget checkpoint logs from the old-PD/smaller-terrain configuration, including the old `model_19999.pt` now excluded from the active train path. |
| `logs/go2_mjlab_dreureka_port_rough_box_grid_oom_2026-05-29/` | Collapsed folder covering the rough box-grid full-smoke console log where the 4096-env process was killed after terrain generation. |
| `logs/go2_mjlab_dreureka_port_rough_hfield_overflow_2026-05-29/` | Collapsed folder covering earlier heightfield rough-terrain logs from the contact-overflow investigation before terrain material DR was removed and the terrain was simplified. |
| `logs/go2_mjlab_dreureka_port_short_smoke_300iter_2026-05-29/` | Collapsed folder covering the completed 300-iteration random_rough smoke log tree and checkpoints that were superseded by the later 650-iteration 20-minute smoke. |
| `logs/go2_mjlab_fresh_sim2sim_old_checkpoint_2026-05-30/` | Collapsed folder covering host FRESH DDS deployer, MuJoCo endpoint, playback, timing, telemetry, and replay logs generated from the archived old MJLab checkpoint before the corrected train contract. |
| `logs/go2_yoga_ball/debug_segfault/` | Collapsed folder covering 10 logs from diagnosing the old Go2 training segfault. |
| `logs/go2_yoga_ball/post_training_sim2sim/` | Collapsed folder covering 236 wrong-model or unsuccessful Go2 Sim2Sim attempt logs. |
| `logs/go2_yoga_ball/train_1_8_budget/` | Collapsed folder covering 2 logs from the first failed/wrong-asset Go2 1/8 training attempt. |
| `logs/go2_yoga_ball/train_1_8_budget_resume/` | Collapsed folder covering 1 resume log from the first failed/wrong-asset Go2 1/8 training attempt. |
| `logs/go2_yoga_ball/train_smoke/` | Collapsed folder covering 4 smoke logs from the superseded Go2 setup. |
| `logs/go2_yoga_ball/train_unitree_rl_gym_1_8_budget/` | Collapsed folder covering 1 stopped unhealthy intermediate Unitree RL Gym training log. |
| `logs/go2_yoga_ball_train_probe.log` | One-off Go2 training probe log from debugging, not tied to the final corrected run. |
| `scripts/go1_yoga_ball/mjlab_yoga_ball/` | Collapsed folder covering 2 MJLab Go1 task files from the abandoned MJLab port path. |
| `scripts/go2_yoga_ball/reward_curve_compare.py` | Utility used for the superseded wrong-asset reward comparison, not used by the current workflow. |
| `scripts/go2_yoga_ball/start_post_training_sim2sim_goal.sh` | Cron/trigger helper for an old Go2 post-training Sim2Sim goal that is no longer active. |
