# State

## Timeline

Dates below are tied to the surviving local artifact or entrypoint dates that anchor each era in the current checkout.

| Date | Codename | Description |
| --- | --- | --- |
| 2026-05-25 | `G1P` | Go1 pretrained yoga-ball reference line: Isaac playback, MuJoCo Sim2Sim, release/timing proofs, and replay video. |
| 2026-05-27 | `G1T` | Go1 local default-train comparison line and its report/video evidence. |
| 2026-05-27 | `S` | Shared orchestration line: Dockerfiles, shell entrypoints, playback wrappers, and report runners used across Go1, Go2, and MJLab workflows. |
| 2026-05-28 | `G2C` | Go2 train/deploy contract line: model, URDF, actuator order, DDS endpoint, and LCM-to-DDS bridge audits. |
| 2026-05-28 | `G2T` | Corrected Go2 20k-iteration, 4096-env Isaac Gym training baseline and related DrEureka training/debug evidence. |
| 2026-05-29 | `G2S` | Go2 MuJoCo/DDS Sim2Sim line: corrected baseline success, checkpoint batches, curve reviews, and follow-up reruns. |
| 2026-05-30 | `G2M` | MJLab caller-project port of the DrEureka Go2 yoga-ball task, including vendored Go2 assets and server-compatible training flow. |
| 2026-05-31 | `G2F` | FRESH host-side MJLab-to-DDS Sim2Sim line: joint-order proof, native playback, and direct deployer debug attempts. |
| 2026-06-04 | `G2P` | Saved-contract Go2 Isaac playback review line: latest-run checks and the 22-checkpoint local-plus-server batch. |
| 2026-06-15 | `P0` | Canonical repo-map sync: `STATE.md` is now the primary state tracker, with file/workflow/thirdparty audit synced to the live tree. |
| 2026-06-16 | `G2R` | Latest-completed Go2 globe-walking reward-history rerun: iter-19000 export from the 2026-06-15 run, plus Isaac playback and default-scene MuJoCo/DDS Sim2Sim evidence. |
| 2026-06-16 | `G2V` | Go2 2026-06-15-server reward-history rerun: best saved iter-13000 export from `080744.060831`, plus Isaac playback and default-scene MuJoCo/DDS Sim2Sim evidence. |
| 2026-06-16 | `G2X` | Go2 failed-env Isaac playback export line: deterministic server iter-13000 probe plus corrected target-env MP4 reruns for failed envs `4`, `6`, and `1`, explicit playback-rate reporting, and a reset-override rerun proving that `init_z=0.3` with symmetric `x/y` jitter `0.1` eliminates all failures in the same 64-env playback. |
| 2026-06-16 | `G2W` | Go2 rough-ground Sim2Sim line: deterministic rough-ground option, corrected large-footprint preview/render defaults, and the replacement rough-ground rerun for the 2026-06-15-server iter-13000 checkpoint. |
| 2026-06-16 | `G2Y` | Go2 2026-05-28 iter-19999 current-default test line: staged export from `063234.884668`, one current-default Sim2Sim run with `action_lag_steps=6`, and a follow-up rerun with `action_lag_steps=0`. |
| 2026-06-16 | `G2Z` | Go1-vs-Go2 Isaac training-route comparison: pinned the release-height formula from source, compared the saved Go1 pretrained config against the staged 2026-06-15-server Go2 deploy config including `x/y` reset ranges and the full-vs-mini routing nuance, and audited the current source paths for robot-specific control, self-collision, rewards, and privileged observations. |
| 2026-06-16 | `G2A` | Go2-vs-bundled-Go1 pretrained alignment proof: current-source faithful smoke launch plus a source-backed report proving `full` env routing, `0.3m` release-height buffer input, `0.1/0.1` `x/y` jitter, playback-default reset alignment, and the remaining Go2-specific deltas from actual launch logs. |
| 2026-06-16 | `G2D` | Go2 custom-reward faithful-train line: renamed launcher plus inline reward updates for joint-limit proximity/violation split, capped low-ball-speed reward, and stronger jerk penalty. |
| 2026-06-16 | `P1` | Repo-state consolidation: duplicate `CURRENT_INVENTORY.md` tracking is retired, and `STATE.md` is the sole active state tracker. |
| 2026-06-18 | `G2Q` | 2026-06-16 local/server reward-selected checkpoint audit: picked local iter-19000 and server iter-9000 from the latest train runs, compared their actual applied configs against stock Go1 pretrained, and stopped before Isaac playback or MuJoCo Sim2Sim because reward, asset, runner, and server spawn settings were not stock-faithful. |
| 2026-06-18 | `P2` | Repo-level agent skill line: `.agents/skills/dr-eureka-training-audit` now holds the DrEureka pretrained-parity audit skill, including the saved-artifact checker and repo-scoped parity rules; the aborted home-level copy was removed. |
| 2026-06-18 | `G2B` | Local 2026-06-16 best-saved rerun line: staged `103148.037437` iter-19000, switched Isaac playback to default probe-plus-success/failed video export, captured the local failed env set `4/23/29/49` with success video `env 0` plus failed videos `4/23/29`, and ran unchanged default-scene MuJoCo/DDS Sim2Sim. |
| 2026-06-18 | `G2L` | Sim2Sim default-zero-lag line: flipped the wrapper and MuJoCo endpoint defaults to `action_lag_steps=0`, reran the local `2026-06-16/train/103148.037437` best-saved iter-19000 checkpoint and the `2026-05-28/train/063234.884668` final iter-19999 checkpoint through the unchanged default workflow, and both survived the full `12s` window. |
| 2026-06-18 | `G2E` | Go2 custom-reward refinement: removed the joint-limit add-ons from the inline faithful-train launcher, kept the low ball-speed term, raised the jerk penalty coefficient to `1.0`, and added a matching low ball angular-velocity reward below `1 rad/s`. |
| 2026-06-20 | `G2H` | Go2 2026-06-18-server rough-default rerun line: staged `082453.814727` iter-17000 from the best saved reward checkpoint, confirmed Isaac playback, previewed the historical deterministic rough terrain, ran zero-lag rough-ground MuJoCo Sim2Sim to the full `12s` window, and flipped the default MuJoCo workflow to rough ground while pinning older flat-ground reruns explicitly. |
| 2026-07-01 | `G2I` | Offline real-DDS deploy investigation line: analyzed the saved `iter17000` real-robot bridge/policy logs without launching a new robot run, compared them against the tracked safe Sim2Sim baseline, and recorded the startup-warning root cause plus the real-path loop-stall evidence. |
| 2026-07-01 | `G2J` | Passive lowstate monitor line: added a DDS-only `rt/lowstate` subscriber for real-robot or simulator diagnostics that records arrival frequency, jitter, long gaps, and sample fields without ever creating a `lowcmd` publisher. |
| 2026-07-01 | `G2K` | Real-DDS deploy timing-instrumentation line: expanded the unchanged deploy/bridge entrypoints to emit per-step policy timing breakdowns, callback cadence/age stats, bridge callback/republish timing, and header-safe event logging for pre-created `events.csv`; the same empty-file header fix is also applied to the safe MuJoCo Sim2Sim endpoint used to validate the instrumentation before real-DDS reruns. |

## Project Map

| Code | Scope | Current state |
| --- | --- | --- |
| `P0` | Repository map | `STATE.md` is the canonical repo map and the only active state tracker for this workspace. |
| `P1` | Inventory consolidation | Duplicate `CURRENT_INVENTORY.md` tracking is retired; future state updates belong only in `STATE.md`. |
| `P2` | Repo-level agent skills | Repo-scoped Codex skills now live under `.agents/skills`; the DrEureka training-audit skill is the current repo-level reference for pretrained-parity checks. |
| `G1P` | Go1 pretrained reference | DrEureka's pretrained Go1 yoga-ball policy is validated in Isaac playback and MuJoCo Sim2Sim with release, timing, control-removal, and replay evidence. |
| `G1T` | Go1 local-train comparison | A weaker local Go1 train is preserved as the main comparison point against the pretrained Go1 reference. |
| `G2C` | Go2 contract | Go2 train/deploy contract evidence ties Unitree RL Gym URDF facts to the MuJoCo DDS endpoint and the LCM-to-DDS bridge. |
| `G2T` | Go2 corrected train | The corrected 20k-iteration, 4096-env Go2 Isaac Gym training run remains the main corrected baseline. |
| `G2D` | Go2 custom reward train | The earlier custom-reward launcher revision introduced split joint-limit metrics, capped low-ball-speed reward, and a stronger jerk penalty on top of the renamed faithful-train entrypoint. |
| `G2E` | Go2 custom reward refinement | The current custom-reward launcher keeps only `low_ball_speed`, `low_ball_angular_velocity`, and `penalize_action_jerk` beyond the first four inline terms, with jerk weighted at `1.0`. |
| `G2P` | Go2 Isaac playback | Corrected, latest-three, latest-eight, smoke, and 22-checkpoint Go2 playback bundles exist with saved-contract Isaac evidence. |
| `G2S` | Go2 MuJoCo/DDS Sim2Sim | The corrected checkpoint succeeds in Sim2Sim; later batches and reruns record fall timing, iter-14000 recovery, larger-ball-damping behavior, and cross-scene comparisons, and the current default wrapper path is zero-lag deterministic rough ground unless a workflow pins flat ground explicitly. |
| `G2R` | Latest reward-history rerun | The latest completed `2026-06-15/train/075047.107233` run now has a reward-selected iter-19000 deploy export, saved-contract Isaac playback evidence, and default-scene Sim2Sim evidence. |
| `G2V` | 2026-06-15-server reward-history rerun | The completed `2026-06-15-server/train/080744.060831` run now has a reward-selected iter-13000 deploy export, saved-contract Isaac playback evidence, and default-scene Sim2Sim evidence. |
| `G2X` | Go2 failed-env Isaac playback exports | The staged `2026-06-15-server` iter-13000 deploy now has a deterministic failed-env probe and three targeted Isaac playback MP4s for envs `4`, `6`, and `1`, each rendered from the selected env handle, stopped on the first reset after the failure frame was captured, and reported with both sim-vs-wall and exported-video playback rates; a follow-up reset-override probe with `init_z=0.3` and symmetric `x/y` jitter `0.1` survives `64/64` envs under the same seed. |
| `G2W` | Go2 rough-ground Sim2Sim | The Sim2Sim wrapper now supports a smooth deterministic rough-ground heightfield with preview rendering; the latest tracked `2026-06-15-server` iter-13000 rough rerun uses the enlarged `rough_ground_extent=12.0` scene plus the explicit legacy `action_lag_steps=6` stack, and falls around `3.82s`. |
| `G2Y` | 2026-05-28 iter-19999 current-default tests | The `063234.884668` last checkpoint now has both the explicit legacy `action_lag_steps=6` comparison run, which falls around `5.33s`, and zero-lag runs that survive the full `12s` window. |
| `G2Z` | Go1-vs-Go2 Isaac training-route comparison | The Go1 pretrained run and the staged `2026-06-15-server` Go2 deploy now have a source-backed reset-height and training-route comparison: identical active ball reset settings and robot root-velocity randomization, but Go2 starts `0.12m` higher above the ball top, uses tighter symmetric `x/y` reset jitter, and the current source also diverges on control mode, self-collision, and privileged-observation routing. |
| `G2A` | Go2-vs-bundled-Go1 pretrained alignment proof | The current Go2 training path now has an actual-log alignment report against the bundled Go1 pretrained checkpoint: `full` routing, `0.3` release-height buffer input, `0.1/0.1` reset jitter, faithful-vs-repo reward-path split, playback-default reset proof, and the remaining Go2-specific mismatches are all pinned to concrete logs and source lines. |
| `G2Q` | 2026-06-16 local/server config audit | The latest `2026-06-16` local and server Go2 reward-selected checkpoints are blocked at the stock-faithfulness audit stage: both drift on asset, reward, and runner settings, and the server run also drifts on spawn height and `x/y` jitter, so no Isaac playback or MuJoCo Sim2Sim reruns were started. |
| `G2B` | 2026-06-16 local rerun with default Isaac auto-export | The local `2026-06-16/train/103148.037437` iter-19000 deploy now has a saved-contract Isaac playback bundle with default probe plus success/failed-video export, and a legacy `action_lag_steps=6` default-scene MuJoCo/DDS Sim2Sim rerun that falls around `5.31s`. |
| `G2L` | Default-zero-lag Sim2Sim reruns | `run_sim2sim.sh` and the MuJoCo endpoint now default to `action_lag_steps=0`; the local `2026-06-16` iter-19000 best-saved rerun and the `2026-05-28` iter-19999 final-checkpoint rerun both survive the full `12s` window under the then-current flat-ground path, which now requires `GROUND_MODE=plane` to reproduce. |
| `G2H` | 2026-06-18-server rough-default rerun | The saved-faithful `2026-06-18-server/train/082453.814727` run now has a reward-selected iter-17000 deploy export, a `63/64` Isaac playback bundle with deterministic failed env `29`, a visual rough-ground preview, and a full-window MuJoCo/DDS Sim2Sim success under the current default rough-ground zero-lag path. |
| `G2I` | Offline real-DDS deploy investigation | The saved `2026-06-18-server` iter-17000 real-DDS attempt now has an offline investigation report and a reusable log analyzer: the estimator warning is pinned to startup use of zero-filled IMU timing history, while the visible real-path problem is policy-loop slowdown correlated with much burstier bridge lowstate delivery than the safe Sim2Sim baseline. |
| `G2J` | Passive lowstate monitor | The repo now includes a DDS-only lowstate monitor for safe frequency diagnostics: it subscribes to `rt/lowstate`, writes raw packet timing plus sample IMU/joint fields, and classifies rate/gap anomalies against user-provided thresholds without touching `rt/lowcmd` or the LCM policy chain. |
| `G2K` | Real-DDS deploy timing instrumentation | The unchanged real deploy command path now emits detailed timing evidence: `deploy_lcm_policy.py` records callback cadence, callback busy time, state age, per-step sleep vs. get-obs vs. inference breakdown, and split adaptation/body inference timings, while `lcm_to_dds_bridge.py` records DDS callback cost and LCM republish cost in both row-level CSV fields and a summary JSON; the policy, bridge, and safe MuJoCo Sim2Sim endpoint now all write event CSV headers correctly even when the caller pre-creates `events.csv`. |
| `G2M` | Go2 MJLab port | A caller-project MJLab reproduction exists with vendored Go2 assets, server-compatible runner assumptions, and 20x20 random-rough terrain verification. |
| `G2F` | Go2 MJLab FRESH Sim2Sim | The direct MJLab-to-DDS deployer passes joint-order and native-playback checks, but current DDS attempts still fail after support release. |
| `S` | Orchestration | Dockerfiles plus shell and Python entrypoints reproduce or extend the Go1, Go2, MJLab, and Sim2Sim workflows. |

## Files

| Path | Era | Description |
| --- | --- | --- |
| `.gitignore` | `P0` | Ignore rules for runtime evidence, fetched payloads, and local build caches. |
| `.gitmodules` | `P0` | Root submodule pins for `DrEureka`, `MJLab`, and `wbc-workspace`. |
| `AGENTS.md` | `P0` | Workspace rules for planning, verification, FRESH env use, and state tracking. |
| `CLAUDE.md` | `P0` | Symlink alias to `AGENTS.md` for tools that look for Claude-style repo instructions. |
| `STATE.md` | `P1` | Canonical repo map and sole state tracker: timeline, tracked files, workflows, and thirdparty divergence. |
| `STATE.md` | `G2L` | State tracker updated for the Sim2Sim default-zero-lag flip, rerun reports, and workflow reproducibility notes. |
| `STATE.md` | `G2E` | State tracker updated for the custom-reward refinement that drops joint-limit extras and adds low ball angular-velocity reward tracking. |
| `STATE.md` | `G2H` | State tracker updated for the 2026-06-18-server rough-default rerun, the default-rough workflow flip, and the flat-ground workflow pins needed to keep older reruns reproducible. |
| `STATE.md` | `G2I` | State tracker updated for the offline real-DDS deploy investigation workflow, report, and analyzer script. |
| `STATE.md` | `G2J` | State tracker updated for the passive lowstate monitor script and its no-control diagnostic workflow. |
| `STATE.md` | `G2K` | State tracker updated for the real-DDS deploy timing instrumentation workflow and the existing-script observability expansion. |
| `.agents/skills/dr-eureka-training-audit/**` | `P2` | Repo-level DrEureka training audit skill: trigger metadata, parity rules reference, and a saved-artifact checker that resolves best saved checkpoints and flags unexpected active-config or early-stop drift. |
| `MUJOCO_LOG.TXT` | `P0` | Root MuJoCo OpenGL warning scratch log from local rendering attempts. |
| `GOAL_GO2_YOGA_BALL_FINAL_SIM2SIM.md` | `G2S` | Goal contract for validating the corrected 2026-05-28 Go2 checkpoint in MuJoCo/DDS Sim2Sim. |
| `GOAL_GO2_MJLAB_DREUREKA_PORT.md` | `G2M` | Goal contract for reproducing the DrEureka Go2 yoga-ball baseline inside MJLab. |
| `GOAL_GO2_MJLAB_FRESH_SIM2SIM.md` | `G2F` | Goal contract for host-side MJLab checkpoint deployment through the direct DDS path. |
| `docker/*.Dockerfile` | `S` | Docker build recipes for Isaac Gym and MuJoCo/DDS workflows. |
| `scripts/AGENTS.md` | `S` | Shared script-level runtime rules, especially Go2 mount and Sim2Sim constraints. |
| `scripts/go1_yoga_ball/*` | `S` | Go1 Docker, MuJoCo, LCM, report, and orchestration entrypoints. |
| `scripts/go2_yoga_ball/{asset_inventory.py,export_iter_jit.py,go2_mujoco_dds_endpoint.py,isaacgym_playback_smoke.py,lcm_to_dds_bridge.py,render_mujoco_replay_video.py,run.sh,run_isaac_playback.sh,run_sim2sim.sh,runner.py}` | `S` | Go2 contract audits, playback, Sim2Sim, non-final checkpoint export, and batch wrappers. |
| `scripts/AGENTS.md` | `G2B` | Script-level playback instructions now describe the default probe plus success/failed-env auto-export flow of `run_isaac_playback.sh`. |
| `scripts/go2_yoga_ball/run_isaac_playback.sh` | `G2B` | Isaac playback wrapper now auto-probes env outcomes, exports one success video plus up to three failed-env videos by default, and accepts post-artifact Isaac exit `139`. |
| `scripts/go2_yoga_ball/go2_mujoco_dds_endpoint.py` | `G2L` | Headless MuJoCo DDS endpoint now defaults to zero-step action lag unless a workflow overrides it explicitly. |
| `scripts/go2_yoga_ball/run_sim2sim.sh` | `G2L` | Sim2Sim wrapper now defaults to `action_lag_steps=0`, leaving older six-step historical reruns to opt in explicitly. |
| `scripts/AGENTS.md` | `G2H` | Script-level Sim2Sim instructions now describe deterministic rough ground as the default MuJoCo scene and `GROUND_MODE=plane` as the flat-ground override for historical reruns. |
| `scripts/go1_yoga_ball/deploy_lcm_policy.py` | `G2K` | Real-DDS policy deployer now emits detailed timing breakdowns, callback cadence logs, summary JSONs, and header-safe event logging without changing its CLI or launch contract. |
| `scripts/go2_yoga_ball/go2_mujoco_dds_endpoint.py` | `G2K` | Safe MuJoCo Sim2Sim endpoint now preserves analyzable sequence logs by writing event CSV headers even when the caller pre-creates `events.csv`, matching the new deploy/bridge instrumentation expectations. |
| `scripts/go2_yoga_ball/go2_mujoco_dds_endpoint.py` | `G2H` | MuJoCo scene helpers and CLI now default to the deterministic rough-ground scene while keeping flat-ground reruns available through `--ground-mode plane`. |
| `scripts/go2_yoga_ball/render_mujoco_scene_preview.py` | `G2H` | Scene preview helper now defaults to the same deterministic rough-ground scene as the live Sim2Sim wrapper. |
| `scripts/go2_yoga_ball/run_sim2sim.sh` | `G2H` | Sim2Sim wrapper now defaults to deterministic rough ground plus zero action lag, leaving older flat-ground and/or lagged reruns to opt in explicitly. |
| `scripts/go2_yoga_ball/analyze_real_deploy_logs.py` | `G2I` | Offline analyzer for saved real-DDS and Sim2Sim deploy logs: summarizes control-loop timing, bridge command cadence, lowstate burstiness, and side-by-side comparison deltas without launching a new run. |
| `scripts/go2_yoga_ball/lcm_to_dds_bridge.py` | `G2K` | Real-DDS bridge now records DDS callback/republish timing fields, a summary JSON, and header-safe event logging while preserving the existing bridge CLI and launch contract. |
| `scripts/go2_yoga_ball/passive_lowstate_monitor.py` | `G2J` | DDS-only `rt/lowstate` monitor that emits raw packet timing plus summary rate/jitter/gap diagnostics without initializing any command publisher. |
| `logs/go2_yoga_ball/*real_dds_deploy/**` | `G2K` | Existing real-DDS deploy log roots can now include `policy_callbacks.csv`, `policy_callback_summary.json`, `policy_diagnostics.json`, and `bridge_diagnostics.json` in addition to the earlier timing CSVs. |
| `scripts/go2_globe_walking_faithful_train.sh` | `S` | Base self-contained DrEureka faithful Go2 training launcher. |
| `scripts/go2_globe_walking_faithful_train_our_designed_reward.sh` | `G2D` | Renamed self-contained DrEureka faithful Go2 training launcher with split joint-limit metrics, capped low-ball-speed reward, and stronger jerk penalty. |
| `scripts/go2_globe_walking_faithful_train_our_designed_reward.sh` | `G2E` | Inline custom reward now drops the joint-limit add-ons, keeps low ball speed, adds low ball angular velocity, and raises the jerk penalty coefficient to `1.0`. |
| `artifacts/go1_yoga_ball/{build,manifest.json,phase_pretrained_*,policy_registry.json,pretrained_*,release_validation.json,sim2sim_contract.md,timing_validation.json,videos/pretrained_mujoco.mp4}` | `G1P` | Go1 pretrained-reference artifacts, reports, and replay video. |
| `logs/go1_yoga_ball/pretrained/**` | `G1P` | Raw Go1 pretrained Isaac playback, MuJoCo Sim2Sim, repeat, and control-removal logs. |
| `artifacts/go1_yoga_ball/{default_train*,mujoco_marked_videos.json,phase_default_train_*,videos/default_train_mujoco.mp4}` | `G1T` | Go1 local-train comparison artifacts, summaries, and replay video. |
| `logs/go1_yoga_ball/default_train/**` | `G1T` | Raw Go1 local-train logs for Isaac playback, MuJoCo Sim2Sim, and train selection. |
| `artifacts/dr_eureka_rapp_checkpoint_review/**` | `G1T` | Three-checkpoint RAPP playback review bundle for stock DrEureka checkpoints. |
| `logs/dr_eureka_rapp_checkpoint_review/**` | `G1T` | Raw RAPP playback logs backing the checkpoint review bundle. |
| `logs/dr_eureka_rapp_0p8/**` | `G1T` | Relaxed-RAPP console logs for two globe-walking prompt/debug runs. |
| `artifacts/go2_yoga_ball/{build,go2_isaacgym_urdf.json,go2_isaacgym_consistency_report.*,go2_lcm_to_dds_bridge_report.*,go2_mujoco_dds_endpoint_report.*,manifest.json,sim2sim_contract.md}` | `G2C` | Go2 contract artifacts and base MuJoCo scene assets. |
| `artifacts/go2_yoga_ball/train_original_settings_1_8_budget_launch.json` | `G2T` | Launch record for the corrected Go2 20k/4096 Isaac Gym training run. |
| `logs/go2_yoga_ball/train_original_settings_1_8_budget/**` | `G2T` | Raw corrected Go2 training logs. |
| `logs/dr_eureka_phase3_ball_radius_0p45_0p55_10000x8/**` | `G2T` | Phase-3 DrEureka generation failure log for the ball-radius DR prompt variant. |
| `artifacts/go2_yoga_ball/{final_train_isaacgym_playback_no_video,final_train_isaacgym_playback_video,latest_dr_eureka_3_isaacgym_playback,latest_dr_eureka_8_isaacgym_playback,isaac_playback_2026_06_04_8plus14}/**` | `G2P` | Go2 Isaac playback bundles for corrected, latest-three, latest-eight, and 22-checkpoint reviews. |
| `logs/go2_yoga_ball/{final_train_isaacgym_playback,final_train_isaacgym_playback_no_video,final_train_isaacgym_playback_video,latest_dr_eureka_3_isaacgym_playback,latest_dr_eureka_8_isaacgym_playback,latest_dr_eureka_8_isaacgym_playback_smoke,isaac_playback_2026_06_04_8plus14}/**` | `G2P` | Raw Go2 Isaac playback logs, including the saved-contract mismatch smoke run. |
| `artifacts/go2_yoga_ball/{final_train_sim2sim,final_train_sim2sim_crosscheck_ball_r0p5_base_z1p2,latest_dr_eureka_3_sim2sim,latest_dr_eureka_3_sim2sim_robot_friction_0p7_base_z_1p0,latest_dr_eureka_8_sim2sim,latest_2026_06_04_22_sim2sim_ball_r0p5_base_z1p2,globe_walking_2026_06_05_server_013434_iter14000_sim2sim,globe_walking_2026_06_05_server_013434_iter14000_sim2sim_ball_drag3p0,globe_walking_2026_06_05_server_013434_last_sim2sim,globe_walking_ball_vel_penalty_iter16000_sim2sim,globe_walking_ball_vel_penalty_iter16000_sim2sim_ball_drag3p0,globe_walking_ball_vel_penalty_iter16000_sim2sim_ball_r0p45_base_z0p95,globe_walking_2026_06_05_server_013434_train_curve,globe_walking_ball_vel_penalty_2026_06_14_train_curve}/**` | `G2S` | Go2 Sim2Sim reports, videos, and training-curve review bundles. |
| `logs/go2_yoga_ball/{final_train_sim2sim,final_train_sim2sim_crosscheck_ball_r0p5_base_z1p2,latest_dr_eureka_3_sim2sim,latest_dr_eureka_3_sim2sim_robot_friction_0p7_base_z_1p0,latest_dr_eureka_8_sim2sim,latest_2026_06_04_22_sim2sim_ball_r0p5_base_z1p2,globe_walking_2026_06_05_server_013434_iter14000_sim2sim,globe_walking_2026_06_05_server_013434_iter14000_sim2sim_ball_drag3p0,globe_walking_2026_06_05_server_013434_last_sim2sim,globe_walking_ball_vel_penalty_iter16000_sim2sim,globe_walking_ball_vel_penalty_iter16000_sim2sim_ball_drag3p0,globe_walking_ball_vel_penalty_iter16000_sim2sim_ball_r0p45_base_z0p95}/**` | `G2S` | Raw Go2 Sim2Sim logs backing the corrected, batch-review, and rerun artifact bundles. |
| `artifacts/go2_yoga_ball/globe_walking_2026_06_15_075047_iter19000_run_report.md` | `G2R` | Combined checkpoint-selection and rerun report for the latest completed 2026-06-15 Go2 globe-walking train. |
| `artifacts/go2_yoga_ball/globe_walking_2026_06_15_075047_iter19000_deploy/**` | `G2R` | Reward-selected iter-19000 deploy staging dir with copied `parameters.pkl` and re-exported Go2 JIT modules. |
| `logs/go2_yoga_ball/globe_walking_2026_06_15_075047_iter19000_isaacgym_playback/**` | `G2R` | Raw saved-contract Isaac playback outputs for the staged iter-19000 checkpoint, including the post-artifact teardown segfault log. |
| `artifacts/go2_yoga_ball/globe_walking_2026_06_15_075047_iter19000_sim2sim/**` | `G2R` | Default-scene MuJoCo/DDS Sim2Sim artifacts for the staged iter-19000 checkpoint, including rendered replay video. |
| `logs/go2_yoga_ball/globe_walking_2026_06_15_075047_iter19000_sim2sim/**` | `G2R` | Raw MuJoCo/DDS Sim2Sim logs for the staged iter-19000 checkpoint. |
| `artifacts/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_run_report.md` | `G2V` | Combined checkpoint-selection and rerun report for the completed 2026-06-15-server Go2 globe-walking train. |
| `artifacts/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_deploy/**` | `G2V` | Reward-selected iter-13000 deploy staging dir with copied `parameters.pkl` and re-exported Go2 JIT modules. |
| `logs/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_isaacgym_playback/**` | `G2V` | Raw saved-contract Isaac playback outputs for the staged iter-13000 checkpoint, including the post-artifact teardown segfault log. |
| `artifacts/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_sim2sim/**` | `G2V` | Default-scene MuJoCo/DDS Sim2Sim artifacts for the staged iter-13000 checkpoint, including rendered replay video. |
| `logs/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_sim2sim/**` | `G2V` | Raw MuJoCo/DDS Sim2Sim logs for the staged iter-13000 checkpoint. |
| `scripts/go2_yoga_ball/isaacgym_playback_smoke.py` | `G2X` | Isaac playback runner with deterministic seeding, per-env failure bookkeeping, target-env camera capture, hold-on-reset failed-env video export, init-height and symmetric `x/y` reset-range overrides, and explicit playback-rate metrics. |
| `logs/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_failed_env_probe/**` | `G2X` | Deterministic no-video Isaac probe on the staged iter-13000 deploy that identified failed envs `4`, `6`, and `1` under seed `0`. |
| `logs/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_failed_env{1,4,6}_video/**` | `G2X` | Targeted Isaac playback reruns with MP4, CSV, summary, report, and run log for each failed env from the deterministic server iter-13000 probe. |
| `logs/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_initz0p3_xy0p1_probe/**` | `G2X` | Deterministic no-video Isaac probe on the staged iter-13000 deploy with `init_z=0.3` and symmetric `x/y` reset jitter `0.1`, showing `64/64` env survival under seed `0`. |
| `scripts/go2_yoga_ball/render_mujoco_scene_preview.py` | `G2W` | Still preview renderer for plane/rough Go2 Sim2Sim scenes before runtime reruns. |
| `artifacts/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_rough_ground_run_report.md` | `G2W` | Corrected rough-ground preview and replacement rerun report for the server iter-13000 checkpoint. |
| `artifacts/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_rough_ground_preview.{png,json}` | `G2W` | Visual preview artifacts proving the rough ground looks plausible before the runtime rerun. |
| `artifacts/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_rough_ground_sim2sim/**` | `G2W` | Rough-ground MuJoCo/DDS Sim2Sim artifacts for the staged iter-13000 checkpoint, including rendered replay video. |
| `logs/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_rough_ground_sim2sim/**` | `G2W` | Raw rough-ground MuJoCo/DDS Sim2Sim logs for the staged iter-13000 checkpoint. |
| `artifacts/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_current_default_run_report.md` | `G2Y` | Current-default Sim2Sim report for the `063234.884668` last checkpoint with the default `action_lag_steps=6` stack. |
| `artifacts/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_current_default_deploy/**` | `G2Y` | Staged deploy export for the `063234.884668` last checkpoint `ac_weights_019999.pt`. |
| `artifacts/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_current_default_sim2sim/**` | `G2Y` | Current-default MuJoCo/DDS Sim2Sim artifacts for the staged iter-19999 checkpoint, including rendered replay video. |
| `logs/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_current_default_sim2sim/**` | `G2Y` | Raw current-default MuJoCo/DDS Sim2Sim logs for the staged iter-19999 checkpoint. |
| `artifacts/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_current_default_no_action_lag_run_report.md` | `G2Y` | No-action-lag Sim2Sim report for the staged iter-19999 checkpoint under the same current-default stack. |
| `artifacts/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_current_default_no_action_lag_sim2sim/**` | `G2Y` | No-action-lag MuJoCo/DDS Sim2Sim artifacts for the staged iter-19999 checkpoint, including rendered replay video. |
| `logs/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_current_default_no_action_lag_sim2sim/**` | `G2Y` | Raw no-action-lag MuJoCo/DDS Sim2Sim logs for the staged iter-19999 checkpoint. |
| `artifacts/go2_yoga_ball/go2_vs_bundled_go1_pretrained_alignment_report.md` | `G2A` | Source-backed report comparing the bundled Go1 pretrained launch log against the current Go2 faithful and repo reward paths, explicitly covering `full` env routing, release-height buffer, `x/y` jitter, reward-path differences, and the remaining Go2-only deltas. |
| `artifacts/go2_yoga_ball/globe_walking_2026_06_16_local_server_config_audit.md` | `G2Q` | Stop-stage audit report for the latest 2026-06-16 local/server Go2 runs: reward-selected checkpoint choice, stock-faithfulness diff, and the decision to skip Isaac playback and MuJoCo Sim2Sim. |
| `artifacts/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_run_report.md` | `G2B` | Combined parity-check, checkpoint-selection, playback auto-export, and Sim2Sim report for the local `2026-06-16` run `103148.037437`. |
| `artifacts/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_deploy/**` | `G2B` | Reward-selected iter-19000 deploy staging dir for local run `103148.037437`, including copied `parameters.pkl` and re-exported Go2 JIT modules. |
| `logs/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_isaacgym_playback/**` | `G2B` | Raw local iter-19000 Isaac playback outputs: probe summary, auto-export selection/manifest, main success video, and failed-env videos for `4`, `23`, and `29`. |
| `artifacts/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_sim2sim/**` | `G2B` | Default-scene MuJoCo/DDS Sim2Sim artifacts for the local iter-19000 deploy, including rendered replay video. |
| `logs/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_sim2sim/**` | `G2B` | Raw default-scene MuJoCo/DDS Sim2Sim logs for the local iter-19000 deploy. |
| `artifacts/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_default_action_lag0_run_report.md` | `G2L` | Default-zero-lag rerun report for the local `2026-06-16` best-saved iter-19000 checkpoint. |
| `artifacts/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_default_action_lag0_sim2sim/**` | `G2L` | Default-zero-lag MuJoCo/DDS Sim2Sim artifacts for the local iter-19000 deploy, including the rendered replay video. |
| `logs/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_default_action_lag0_sim2sim/**` | `G2L` | Raw default-zero-lag MuJoCo/DDS Sim2Sim logs for the local iter-19000 deploy. |
| `artifacts/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_default_action_lag0_run_report.md` | `G2L` | Default-zero-lag rerun report for the `2026-05-28` final iter-19999 checkpoint under the current default workflow. |
| `artifacts/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_default_action_lag0_sim2sim/**` | `G2L` | Default-zero-lag MuJoCo/DDS Sim2Sim artifacts for the staged iter-19999 checkpoint under the current default workflow, including the rendered replay video. |
| `logs/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_default_action_lag0_sim2sim/**` | `G2L` | Raw default-zero-lag MuJoCo/DDS Sim2Sim logs for the staged iter-19999 checkpoint under the current default workflow. |
| `artifacts/go2_yoga_ball/globe_walking_2026_06_18_server_082453_iter17000_default_rough_run_report.md` | `G2H` | Combined parity-check, checkpoint-selection, Isaac playback, rough-ground preview, rough-default Sim2Sim, and workflow-update report for the saved-faithful `2026-06-18-server` run `082453.814727`. |
| `artifacts/go2_yoga_ball/globe_walking_2026_06_18_server_082453_iter17000_deploy/**` | `G2H` | Reward-selected iter-17000 deploy staging dir for `2026-06-18-server/train/082453.814727`, including copied `parameters.pkl` and re-exported Go2 JIT modules. |
| `logs/go2_yoga_ball/globe_walking_2026_06_18_server_082453_iter17000_isaacgym_playback/**` | `G2H` | Raw iter-17000 Isaac playback outputs: deterministic probe, main success video, and targeted failed-env video for env `29`. |
| `artifacts/go2_yoga_ball/globe_walking_2026_06_18_server_082453_iter17000_rough_ground_preview.{png,json}` | `G2H` | Visual preview artifacts confirming the default rough-ground scene before the 2026-06-18-server Sim2Sim rerun. |
| `artifacts/go2_yoga_ball/globe_walking_2026_06_18_server_082453_iter17000_default_rough_ground_sim2sim/**` | `G2H` | Rough-default MuJoCo/DDS Sim2Sim artifacts for the staged iter-17000 checkpoint, including rendered replay video. |
| `logs/go2_yoga_ball/globe_walking_2026_06_18_server_082453_iter17000_default_rough_ground_sim2sim/**` | `G2H` | Raw rough-default MuJoCo/DDS Sim2Sim logs for the staged iter-17000 checkpoint. |
| `artifacts/go2_yoga_ball/globe_walking_2026_07_01_real_dds_deploy_investigation.md` | `G2I` | Offline investigation report for the saved `iter17000` real-DDS attempt, tying the startup warning and loop-rate drop to concrete source paths and saved log evidence. |
| `logs/go2_yoga_ball/faithful_train_smoke_current_source/**` | `G2A` | Fresh current-source faithful Go2 smoke launch log used as the authoritative actual-log proof for the aligned `full/eureka/0.3/0.1` route and its remaining differences from bundled Go1 pretrained. |
| `scripts/go2_mjlab_dreureka_port/**` | `G2M` | Caller-project MJLab port: task registration, vendored Go2 assets, smoke/train/play drivers, and server-compat docs. |
| `artifacts/go2_mjlab_dreureka_port/**` | `G2M` | MJLab port source contract, task smokes, terrain checks, scene render, reward curves, and train health artifacts. |
| `logs/go2_mjlab_dreureka_port/**` | `G2M` | MJLab port preflight, terrain verification, smoke train, and 1/8-budget training logs. |
| `torchrunx_logs/**` | `G2M` | Torchrunx launcher logs captured by the server-compatible MJLab training path. |
| `scripts/go2_mjlab_fresh_sim2sim/**` | `G2F` | FRESH MJLab-to-DDS deployer, joint-order proof, playback, attempt, and report entrypoints. |
| `artifacts/go2_mjlab_fresh_sim2sim/**` | `G2F` | FRESH MJLab Sim2Sim joint-order proof, playback validation, attempt videos, and summary reports. |
| `logs/go2_mjlab_fresh_sim2sim/**` | `G2F` | FRESH MJLab Sim2Sim deployer, DDS endpoint, replay, timing, and debug-attempt logs. |
| `thirdparties/DrEureka/**` | `G2T` | Forked DrEureka training/deploy source; user-authored divergence is tracked in `Thirdparty Changes`. |
| `thirdparties/wbc-workspace/**` | `S` | User-maintained reference workspace; visible git history is entirely user-authored in this checkout. |
| `thirdparties/{IsaacGym,IsaacGym_Preview_4_Package.tar.gz,torch_wheels/**}` | `S` | Non-git binary payloads used by Isaac Gym and host training environments. |

## Workflows

### `WF-P1` Repo state consolidation

- Environment: host shell; no runtime dependencies.
- Entry points: inspect `AGENTS.md` and `STATE.md`, delete `CURRENT_INVENTORY.md`, update `STATE.md`, and verify that no live instructions still ask agents to maintain a second inventory file.
- Initial state: `AGENTS.md` already directs agents to maintain `STATE.md`, while `CURRENT_INVENTORY.md` still duplicates the same tracking responsibility.
- Outputs: updated `STATE.md` and retirement of `CURRENT_INVENTORY.md`.
- Success: `STATE.md` remains the only active state-tracking document and repo instructions no longer present `CURRENT_INVENTORY.md` as a live file to keep in sync.

### `WF-P2` Repo-level DrEureka training audit skill

- Environment: host shell with Python pickle access; no simulation run required.
- Entry points: repo-level skill root `.agents/skills/dr-eureka-training-audit/`; run `python .agents/skills/dr-eureka-training-audit/scripts/check_training_parity.py --run <run-dir>`; read `.agents/skills/dr-eureka-training-audit/references/parity-rules.md` when classifying diffs or diagnosing a fresh launch.
- Initial state: repo-level skills live under `.agents/skills`; the built-in stock reference run is `thirdparties/DrEureka/globe_walking/runs/globe_walking/dr_eureka_best`; the checker resolves either a concrete run dir or the latest run beneath a date bucket or `train/` dir.
- Outputs: a pass/fail parity summary on stdout or JSON, including best saved checkpoint resolution, early-stop detection from `outputs.log`, allowed-diff counts, and unexpected active-config diffs.
- Success: the skill treats robot, control, asset, reward, ball-size, save-interval, early-stop-config, and parallelism differences as allowed; local `2026-06-16/train/103148.037437` passes with only allowed diffs; server `2026-06-16-server/train/103631.844719` fails only on spawn/reset drift (`init_state.pos[2]`, `terrain.x_init_range`, `terrain.y_init_range`).

### `WF-G1P` Go1 pretrained reference

- Environment: Docker `eureka-isaacgym` plus `eureka-mujoco_sim2sim`.
- Entry points: `scripts/go1_yoga_ball/run.sh preflight`, `play-pretrained-isaacgym`, `smoke-pretrained-mujoco-sim2sim`, `repeat-pretrained-mujoco-sim2sim`, `control-removal-pretrained-mujoco-sim2sim`, `render-pretrained-mujoco-video`, `scripts/go1_yoga_ball/report.sh`.
- Initial state: `thirdparties/DrEureka/globe_walking/runs/globe_walking/dr_eureka_best` exists and Docker images are available.
- Outputs: `artifacts/go1_yoga_ball/phase_pretrained_*`, `artifacts/go1_yoga_ball/videos/pretrained_mujoco.mp4`, `logs/go1_yoga_ball/pretrained/**`.
- Success: release-before-motion, synced timing, fall after control removal, and replay video.

### `WF-G1T` Go1 local-train comparison

- Environment: same Docker stack as `WF-G1P`.
- Entry points: `scripts/go1_yoga_ball/run.sh train-default-isaacgym`, `play-default-train-isaacgym`, `smoke-default-train-mujoco-sim2sim`, `render-default-train-mujoco-video`, `scripts/go1_yoga_ball/report.sh`.
- Initial state: a local Go1 run is selected through `artifacts/go1_yoga_ball/default_train_selected_run.txt`.
- Outputs: `artifacts/go1_yoga_ball/phase_default_train_*`, comparison JSONs, and `logs/go1_yoga_ball/default_train/**`.
- Success: selected run is recorded, Isaac and MuJoCo summaries exist, and the comparison remains distinct from the pretrained reference.

### `WF-G2C-T` Go2 contract audit and corrected Isaac train

- Environment: Docker `eureka-isaacgym`; host Python for audit scripts.
- Entry points: `scripts/go2_yoga_ball/run.sh preflight`, `train-smoke-isaacgym`, `train-1-8-isaacgym`, `phase-go2-train-report`.
- Initial state: Unitree RL Gym Go2 URDF and the corrected DrEureka Go2 training path are present.
- Outputs: `artifacts/go2_yoga_ball/go2_*`, `artifacts/go2_yoga_ball/train_original_settings_1_8_budget_launch.json`, and `logs/go2_yoga_ball/train_original_settings_1_8_budget/train.log`.
- Success: asset, order, and bridge audits pass and the corrected 20k/4096 run completes with reports.

### `WF-G2D` Go2 custom-reward faithful train

- Environment: Docker `eureka-isaacgym`.
- Entry points: `scripts/go2_globe_walking_faithful_train_our_designed_reward.sh`.
- Initial state: the Go2 DrEureka faithful-training path is present, the `eureka-isaacgym` image is available, and the workspace is mounted at `/workspace`.
- Outputs: a standard DrEureka run under `thirdparties/DrEureka/globe_walking/runs/globe_walking/YYYY-MM-DD/train/RUN_ID`, with reward logs for `low_ball_speed`, `low_ball_angular_velocity`, and `penalize_action_jerk`.
- Success: the launcher starts a `go2-globe-our-designed-reward-*` container, training uses the renamed entrypoint, `low_ball_speed` only rewards speeds below `0.4 m/s`, `low_ball_angular_velocity` only rewards speeds below `1 rad/s`, and the jerk penalty coefficient is `1.0`.

### `WF-G2P` Go2 Isaac playback reviews

- Environment: Docker `eureka-isaacgym`, typically through `scripts/go2_yoga_ball/run_isaac_playback.sh`.
- Entry points: `scripts/go2_yoga_ball/run_isaac_playback.sh` and direct batch calls to `scripts/go2_yoga_ball/isaacgym_playback_smoke.py`.
- Initial state: corrected checkpoint plus latest-three, latest-eight, and 2026-06-04 22-checkpoint DrEureka run sets.
- Outputs: `artifacts/go2_yoga_ball/*isaac*` and `logs/go2_yoga_ball/*isaac*`.
- Success: the wrapper first writes `probe/summary.json`, then writes the main success-camera `summary.json` plus `isaacgym_playback.mp4` when any env survives, exports up to three failed-env videos under `failed_env*_video/` when failures occur, and any Isaac graphics teardown failure happens only after artifacts are complete.

### `WF-G2S` Go2 MuJoCo/DDS Sim2Sim and reruns

- Environment: host `go2-mjlab` conda plus Docker `eureka-mujoco_sim2sim` and `eureka-isaacgym`.
- Entry points: `scripts/go2_yoga_ball/run_sim2sim.sh`, `scripts/go2_yoga_ball/export_iter_jit.py`, and `scripts/go2_yoga_ball/render_mujoco_replay_video.py`.
- Initial state: corrected 2026-05-28 checkpoint, latest-three and latest-eight reviews, the 22-checkpoint batch, and later `013434.178402` / `120119.272700` reruns; the current default wrapper stack is `ground_mode=rough`, `ground_seed=17`, `ground_friction=0.5`, `base_z=1.2`, `ball_drag=0.3`, and `action_lag_steps=0`, while older flat-ground reruns must pass `GROUND_MODE=plane` explicitly.
- Outputs: `artifacts/go2_yoga_ball/*sim2sim*` and matching `logs/go2_yoga_ball/*sim2sim*`.
- Success: DDS command-before-release ordering, replay and timing logs, rendered video, and either full survival or explicit fall timing/root-cause evidence.

### `WF-G2R` Latest reward-history-selected Go2 rerun

- Environment: host `go2-mjlab` conda plus Docker `eureka-isaacgym` and `eureka-mujoco_sim2sim`.
- Entry points: parse `thirdparties/DrEureka/globe_walking/runs/globe_walking/2026-06-15/train/075047.107233/outputs.log` for saved-checkpoint reward history; `conda run -n go2-mjlab python scripts/go2_yoga_ball/export_iter_jit.py --run .../075047.107233 --ckpt ac_weights_019000.pt --out artifacts/go2_yoga_ball/globe_walking_2026_06_15_075047_iter19000_deploy`; `RUN=...iter19000_deploy OUT=logs/go2_yoga_ball/globe_walking_2026_06_15_075047_iter19000_isaacgym_playback bash scripts/go2_yoga_ball/run_isaac_playback.sh`; `RUN=...iter19000_deploy LOG_DIR=logs/go2_yoga_ball/globe_walking_2026_06_15_075047_iter19000_sim2sim ART_DIR=artifacts/go2_yoga_ball/globe_walking_2026_06_15_075047_iter19000_sim2sim GROUND_MODE=plane ACTION_LAG_STEPS=6 bash scripts/go2_yoga_ball/run_sim2sim.sh`.
- Initial state: the latest started 2026-06-15 run `072804.964139` is incomplete (only through iter `190`), so the latest completed run is `075047.107233`; the best saved checkpoint by both reward and episode length is iter `19000`, while the absolute peak at iter `19220` was not saved.
- Outputs: `artifacts/go2_yoga_ball/globe_walking_2026_06_15_075047_iter19000_run_report.md`, `artifacts/go2_yoga_ball/globe_walking_2026_06_15_075047_iter19000_deploy/**`, `logs/go2_yoga_ball/globe_walking_2026_06_15_075047_iter19000_isaacgym_playback/**`, `artifacts/go2_yoga_ball/globe_walking_2026_06_15_075047_iter19000_sim2sim/**`, and `logs/go2_yoga_ball/globe_walking_2026_06_15_075047_iter19000_sim2sim/**`.
- Success: the staged iter-19000 export passes the exact JIT self-check, Isaac playback writes summary/CSV/video even if the known teardown segfault happens afterward, and Sim2Sim records release ordering plus either full survival or explicit fall timing with rendered replay video.

### `WF-G2V` 2026-06-15-server reward-history-selected Go2 rerun

- Environment: host `go2-mjlab` conda plus Docker `eureka-isaacgym` and `eureka-mujoco_sim2sim`.
- Entry points: inspect `thirdparties/DrEureka/globe_walking/runs/globe_walking/2026-06-15-server/train/*`; reject `075203.405696` because it lacks saved checkpoints; parse `.../080744.060831/outputs.log` for saved-checkpoint reward history; `conda run -n go2-mjlab python scripts/go2_yoga_ball/export_iter_jit.py --run .../080744.060831 --ckpt ac_weights_013000.pt --out artifacts/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_deploy`; `RUN=...iter13000_deploy OUT=logs/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_isaacgym_playback bash scripts/go2_yoga_ball/run_isaac_playback.sh`; `RUN=...iter13000_deploy LOG_DIR=logs/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_sim2sim ART_DIR=artifacts/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_sim2sim VIDEO_NAME=globe_walking_2026_06_15_server_080744_iter13000_sim2sim.mp4 GROUND_MODE=plane ACTION_LAG_STEPS=6 bash scripts/go2_yoga_ball/run_sim2sim.sh`.
- Initial state: `2026-06-15-server/train/075203.405696` has no saved checkpoint ladder, while `080744.060831` is the completed saved-checkpoint run; the best saved checkpoint by both reward and episode length is iter `13000`, and the final logged point at iter `19990` is worse.
- Outputs: `artifacts/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_run_report.md`, `artifacts/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_deploy/**`, `logs/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_isaacgym_playback/**`, `artifacts/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_sim2sim/**`, and `logs/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_sim2sim/**`.
- Success: the staged iter-13000 export passes the exact JIT self-check, Isaac playback writes summary/CSV/video even if the known teardown segfault happens afterward, and Sim2Sim records release ordering plus explicit fall timing around `9.48s` with a rendered replay video.

### `WF-G2X` 2026-06-15-server failed-env Isaac playback exports

- Environment: Docker `eureka-isaacgym`.
- Entry points: `python /workspace/scripts/go2_yoga_ball/isaacgym_playback_smoke.py --run /workspace/artifacts/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_deploy --out-dir /workspace/logs/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_failed_env_probe --num-envs 64 --duration-s 12 --device cuda:0 --seed 0 --use-saved-contract --preserve-domain-rand`; rerun the same staged deploy with `--record-video --hold-failed-env --stop-on-target-reset --camera-env-id 4|6|1` into the matching `failed_env*_video` log dir; and run `--override-init-z 0.3 --override-xy-init-range 0.1` into `globe_walking_2026_06_15_server_080744_iter13000_initz0p3_xy0p1_probe`.
- Initial state: the staged deploy dir from `WF-G2V` already exists with `checkpoints/body_latest.jit`, `checkpoints/adaptation_module_latest.jit`, and `parameters.pkl`; the playback runner supports deterministic seeding plus failed-env targeting.
- Outputs: `logs/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_failed_env_probe/**`, `logs/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_failed_env{1,4,6}_video/**`, and `logs/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_initz0p3_xy0p1_probe/**`.
- Success: the baseline probe reproduces failed envs `4`, `6`, and `1` at about `0.80s`, `0.84s`, and `1.62s` respectively under seed `0`; each targeted rerun writes MP4/CSV/summary/report/run-log artifacts before the known Isaac graphics teardown segfault, the MP4 visibly shows the selected env's dog plus ball instead of env `0`, the summary shows `stopped_on_target_reset=true`, the reported exported-video playback rate is `0.5x` realtime because `video_fps=25` against the `50 Hz` sim step, and the reset-override rerun with `init_z=0.3` plus symmetric `x/y` jitter `0.1` shows zero failed envs out of `64`.

### `WF-G2W` Rough-ground Go2 Sim2Sim rerun

- Environment: host `go2-mjlab` conda plus Docker `eureka-isaacgym` and `eureka-mujoco_sim2sim`.
- Entry points: `MUJOCO_GL=egl conda run -n go2-mjlab python scripts/go2_yoga_ball/render_mujoco_scene_preview.py --run artifacts/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_deploy --ground-mode rough --output artifacts/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_rough_ground_preview.png --artifact artifacts/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_rough_ground_preview.json`; visually inspect the PNG; `GROUND_MODE=rough RUN=...iter13000_deploy LOG_DIR=logs/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_rough_ground_sim2sim ART_DIR=artifacts/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_rough_ground_sim2sim VIDEO_NAME=globe_walking_2026_06_15_server_080744_iter13000_rough_ground_sim2sim.mp4 ACTION_LAG_STEPS=6 bash scripts/go2_yoga_ball/run_sim2sim.sh`.
- Initial state: the staged `iter13000` deploy dir from `WF-G2V` already exists; the endpoint and wrapper support `GROUND_MODE=rough` with deterministic seed `17`, enlarged default rough extent `12.0m`; the current default action lag is `0`, so this historical rough-ground rerun keeps the legacy `ACTION_LAG_STEPS=6` stack explicit.
- Outputs: `artifacts/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_rough_ground_preview.{png,json}`, `artifacts/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_rough_ground_run_report.md`, `artifacts/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_rough_ground_sim2sim/**`, and `logs/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_rough_ground_sim2sim/**`.
- Success: the preview PNG shows smooth non-flat non-jagged terrain with a footprint large enough to cover the trajectory and a sane spawn pose, and the rough-ground Sim2Sim run records release ordering plus explicit fall timing with a rendered replay video.

### `WF-G2Y` 2026-05-28 iter-19999 current-default tests

- Environment: host `go2-mjlab` conda plus Docker `eureka-isaacgym` and `eureka-mujoco_sim2sim`.
- Entry points: `conda run -n go2-mjlab python scripts/go2_yoga_ball/export_iter_jit.py --run thirdparties/DrEureka/globe_walking/runs/globe_walking/2026-05-28/train/063234.884668 --ckpt ac_weights_019999.pt --out artifacts/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_current_default_deploy`; `RUN=...current_default_deploy LOG_DIR=logs/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_current_default_no_action_lag_sim2sim ART_DIR=artifacts/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_current_default_no_action_lag_sim2sim GROUND_MODE=plane bash scripts/go2_yoga_ball/run_sim2sim.sh`; `RUN=...current_default_deploy LOG_DIR=logs/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_current_default_sim2sim ART_DIR=artifacts/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_current_default_sim2sim GROUND_MODE=plane ACTION_LAG_STEPS=6 bash scripts/go2_yoga_ball/run_sim2sim.sh`.
- Initial state: the source run `063234.884668` exists with `ac_weights_019999.pt` as the last numbered checkpoint and `ac_weights_last.pt` aliasing the same endpoint, and the historical flat-ground comparison recorded here now requires `GROUND_MODE=plane` because the live wrapper default has since moved to deterministic rough ground while keeping `ground_friction=0.5`, `base_z=1.2`, `ball_drag=0.3`, and `action_lag_steps=0`.
- Outputs: `artifacts/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_current_default_run_report.md`, `artifacts/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_current_default_deploy/**`, `artifacts/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_current_default_sim2sim/**`, `logs/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_current_default_sim2sim/**`, `artifacts/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_current_default_no_action_lag_run_report.md`, `artifacts/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_current_default_no_action_lag_sim2sim/**`, and `logs/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_current_default_no_action_lag_sim2sim/**`.
- Success: the staged export passes the exact JIT self-check, the current-default zero-lag run completes with all process return codes `0` and no fall during the `12s` window, and the explicit `ACTION_LAG_STEPS=6` comparison run still reproduces the rendered replay plus fall timing around `5.33s`.

### `WF-G2Z` Go1-vs-Go2 Isaac reset comparison

- Environment: host shell with Python pickle access; no simulation run required.
- Entry points: inspect [thirdparties/DrEureka/globe_walking/go1_gym/envs/base/legged_robot.py](/home/seqn/eureka-workspace/thirdparties/DrEureka/globe_walking/go1_gym/envs/base/legged_robot.py:887) for reset logic, [thirdparties/DrEureka/globe_walking/go1_gym/envs/base/legged_robot.py](/home/seqn/eureka-workspace/thirdparties/DrEureka/globe_walking/go1_gym/envs/base/legged_robot.py:1328) for reward assembly, [thirdparties/DrEureka/globe_walking/scripts/train.py](/home/seqn/eureka-workspace/thirdparties/DrEureka/globe_walking/scripts/train.py:106) for `dr-config` and `robot` routing, and [thirdparties/DrEureka/globe_walking/go1_gym/envs/base/base_task.py](/home/seqn/eureka-workspace/thirdparties/DrEureka/globe_walking/go1_gym/envs/base/base_task.py:41) plus [thirdparties/DrEureka/globe_walking/go1_gym_learn/ppo_cse/actor_critic.py](/home/seqn/eureka-workspace/thirdparties/DrEureka/globe_walking/go1_gym_learn/ppo_cse/actor_critic.py:26) for privileged-observation sizing; load `thirdparties/DrEureka/globe_walking/runs/globe_walking/dr_eureka_best/parameters.pkl` and `artifacts/go2_yoga_ball/globe_walking_2026_06_15_server_080744_iter13000_deploy/parameters.pkl`; compare active `init_state`, `terrain`, `ball`, `domain_rand`, `control`, `asset`, `env`, and reward settings.
- Initial state: the saved Go1 pretrained run and the staged Go2 iter-13000 deploy both exist locally.
- Outputs: source-backed release-height formulas, a human-readable diff of the active training settings including symmetric `x/y` reset jitter ranges, and a source-backed summary of robot-specific routing for control, self-collision, rewards, and privileged observations.
- Success: the comparison identifies that base release relative to the ball top is `init_state.pos[2]`, confirms identical ball reset and robot root-velocity randomization paths, distinguishes `--robot` effects from `--dr-config` effects, captures the saved pretrained `full` versus current `mini`-derived privileged-observation split, and enumerates the active setting differences that remain after excluding the robot swap.

### `WF-G2A` Go2-vs-bundled-Go1 pretrained alignment proof

- Environment: host shell plus Docker `eureka-isaacgym`.
- Entry points: inspect [thirdparties/DrEureka/globe_walking/runs/globe_walking/dr_eureka_best/outputs.log](/home/seqn/eureka-workspace/thirdparties/DrEureka/globe_walking/runs/globe_walking/dr_eureka_best/outputs.log:47), [logs/go2_yoga_ball/train_smoke/train.log](/home/seqn/eureka-workspace/logs/go2_yoga_ball/train_smoke/train.log:72), [thirdparties/DrEureka/globe_walking/scripts/train.py](/home/seqn/eureka-workspace/thirdparties/DrEureka/globe_walking/scripts/train.py:8), and [thirdparties/DrEureka/globe_walking/go1_gym/envs/base/legged_robot.py](/home/seqn/eureka-workspace/thirdparties/DrEureka/globe_walking/go1_gym/envs/base/legged_robot.py:890); launch a one-off faithful smoke inside `eureka-isaacgym` that mirrors [scripts/go2_globe_walking_faithful_train.sh](/home/seqn/eureka-workspace/scripts/go2_globe_walking_faithful_train.sh:121) but uses `iterations=1`, `num_envs=64`, and writes [logs/go2_yoga_ball/faithful_train_smoke_current_source/train.log](/home/seqn/eureka-workspace/logs/go2_yoga_ball/faithful_train_smoke_current_source/train.log:72); then write [artifacts/go2_yoga_ball/go2_vs_bundled_go1_pretrained_alignment_report.md](/home/seqn/eureka-workspace/artifacts/go2_yoga_ball/go2_vs_bundled_go1_pretrained_alignment_report.md:1).
- Initial state: the bundled Go1 pretrained run exists locally; the Go2 source tree already contains the `0.3` reset-height input, `0.1/0.1` Go2 jitter defaults, full-env routing updates, and faithful launchers.
- Outputs: the fresh faithful smoke log plus a report proving from actual logs that the current Go2 path now uses the `full` route, `0.3` release-height buffer input, `0.1/0.1` jitter, and the current faithful-vs-repo reward-path split, while also enumerating the remaining Go2-only differences.
- Success: the report cites actual launch logs for the bundled Go1 checkpoint, the current Go2 faithful path, and the current Go2 repo reward path; explicitly compares `env full`, release-height buffer, and `x/y` jitter; and states whether the current Go2 route is truly identical or only as close as possible under the remaining active differences.

### `WF-G2Q` 2026-06-16 local/server stock-faithfulness audit

- Environment: host shell with Python pickle access; no simulation run unless the audit passes.
- Entry points: identify the latest train run under `thirdparties/DrEureka/globe_walking/runs/globe_walking/2026-06-16/train/` and `.../2026-06-16-server/train/`; parse each `outputs.log` for reward history and select the best saved checkpoint from the available `ac_weights_*.pt` ladder; compare `parameters.pkl` from those runs against `thirdparties/DrEureka/globe_walking/runs/globe_walking/dr_eureka_best/parameters.pkl`; write [artifacts/go2_yoga_ball/globe_walking_2026_06_16_local_server_config_audit.md](/home/seqn/eureka-workspace/artifacts/go2_yoga_ball/globe_walking_2026_06_16_local_server_config_audit.md:1).
- Initial state: the stock Go1 pretrained run exists at `dr_eureka_best`; the latest local train run is `2026-06-16/train/103148.037437`; the latest server train run is `2026-06-16-server/train/103631.844719`; both latest runs have a full saved checkpoint ladder through `ac_weights_019999.pt`.
- Outputs: the audit report records local/server best saved checkpoints, the active-config diff against stock, and whether playback/Sim2Sim may proceed.
- Success: the audit either proves that only the allowed deltas remain and greenlights Isaac playback plus MuJoCo Sim2Sim, or it records the unexpected config deltas and stops before any playback/Sim2Sim execution. The current recorded result is the stop path because both runs drift on asset, reward, and runner settings, and the server run also drifts on spawn height and `x/y` jitter.

### `WF-G2B` 2026-06-16 local reward-selected rerun with default Isaac auto-export

- Environment: host `go2-mjlab` conda plus Docker `eureka-isaacgym` and `eureka-mujoco_sim2sim`.
- Entry points: `python .agents/skills/dr-eureka-training-audit/scripts/check_training_parity.py --run thirdparties/DrEureka/globe_walking/runs/globe_walking/2026-06-16/train/103148.037437 --show-allowed --json`; `conda run -n go2-mjlab python scripts/go2_yoga_ball/export_iter_jit.py --run thirdparties/DrEureka/globe_walking/runs/globe_walking/2026-06-16/train/103148.037437 --ckpt ac_weights_019000.pt --out artifacts/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_deploy`; `RUN=...iter19000_deploy OUT=logs/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_isaacgym_playback NUM_ENVS=64 DURATION=12 bash scripts/go2_yoga_ball/run_isaac_playback.sh`; `RUN=...iter19000_deploy LOG_DIR=logs/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_sim2sim ART_DIR=artifacts/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_sim2sim VIDEO_NAME=globe_walking_2026_06_16_103148_iter19000_sim2sim.mp4 GROUND_MODE=plane ACTION_LAG_STEPS=6 bash scripts/go2_yoga_ball/run_sim2sim.sh`.
- Initial state: the local `2026-06-16/train/103148.037437` run exists with a full checkpoint ladder; the current repo-level parity checker resolves `ac_weights_019000.pt` as the best saved reward checkpoint and reports only allowed diffs; `run_isaac_playback.sh` now defaults to probe plus success/failed video export; the current Sim2Sim default action lag is `0`, so this historical fall-case rerun keeps the prior `ACTION_LAG_STEPS=6` stack explicit.
- Outputs: [artifacts/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_run_report.md](/home/seqn/eureka-workspace/artifacts/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_run_report.md:1), `artifacts/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_deploy/**`, `logs/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_isaacgym_playback/**`, `artifacts/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_sim2sim/**`, and `logs/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_sim2sim/**`.
- Success: the staged iter-19000 export passes the exact JIT self-check; the Isaac probe shows failed envs `4`, `23`, `29`, and `49` with `60/64` survivors under seed `0`; the wrapper exports the main success video from env `0` plus failed-env videos for `4`, `23`, and `29` and records the selection in `auto_export_manifest.json`; and the explicit `ACTION_LAG_STEPS=6` default-scene Sim2Sim rerun returns `0` from all three runtime processes plus render, confirms release, sends `132` commands, falls around `5.308s`, and writes a rendered replay video.

### `WF-G2L` Default-zero-lag Sim2Sim reruns

- Environment: host `go2-mjlab` conda plus Docker `eureka-mujoco_sim2sim` and `eureka-isaacgym`.
- Entry points: `python .agents/skills/dr-eureka-training-audit/scripts/check_training_parity.py --run thirdparties/DrEureka/globe_walking/runs/globe_walking/2026-06-16 --json`; `RUN=/home/seqn/eureka-workspace/artifacts/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_deploy LOG_DIR=/home/seqn/eureka-workspace/logs/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_default_action_lag0_sim2sim ART_DIR=/home/seqn/eureka-workspace/artifacts/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_default_action_lag0_sim2sim VIDEO_NAME=globe_walking_2026_06_16_103148_iter19000_default_action_lag0_sim2sim.mp4 GROUND_MODE=plane bash scripts/go2_yoga_ball/run_sim2sim.sh`; `RUN=/home/seqn/eureka-workspace/artifacts/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_current_default_deploy LOG_DIR=/home/seqn/eureka-workspace/logs/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_default_action_lag0_sim2sim ART_DIR=/home/seqn/eureka-workspace/artifacts/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_default_action_lag0_sim2sim VIDEO_NAME=globe_walking_2026_05_28_063234_iter19999_default_action_lag0_sim2sim.mp4 GROUND_MODE=plane bash scripts/go2_yoga_ball/run_sim2sim.sh`.
- Initial state: `scripts/go2_yoga_ball/run_sim2sim.sh` and `scripts/go2_yoga_ball/go2_mujoco_dds_endpoint.py` now default to `ground_mode=rough` plus `action_lag_steps=0`; the `2026-06-16` date bucket resolves to local run `train/103148.037437` with best saved checkpoint `ac_weights_019000.pt`; the local iter-19000 deploy dir and the staged `2026-05-28` iter-19999 deploy dir already exist and pass their JIT self-checks, so these historical flat-ground reruns pin `GROUND_MODE=plane` explicitly.
- Outputs: [artifacts/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_default_action_lag0_run_report.md](/home/seqn/eureka-workspace/artifacts/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_default_action_lag0_run_report.md:1), `artifacts/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_default_action_lag0_sim2sim/**`, `logs/go2_yoga_ball/globe_walking_2026_06_16_103148_iter19000_default_action_lag0_sim2sim/**`, [artifacts/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_default_action_lag0_run_report.md](/home/seqn/eureka-workspace/artifacts/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_default_action_lag0_run_report.md:1), `artifacts/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_default_action_lag0_sim2sim/**`, and `logs/go2_yoga_ball/globe_walking_2026_05_28_063234_iter19999_default_action_lag0_sim2sim/**`.
- Success: both runs return `0` from endpoint, bridge, policy, and render; both confirm release; both send `461` commands with `action_lag_steps=0`; both survive the full `12s` window with rendered replay videos; and the local `2026-06-16` iter-19000 rerun specifically flips from the earlier `5.308s` fall under six-step lag to full-window survival under the new default.

### `WF-G2H` 2026-06-18-server rough-default rerun

- Environment: host `go2-mjlab` conda plus Docker `eureka-isaacgym` and `eureka-mujoco_sim2sim`.
- Entry points: `python .agents/skills/dr-eureka-training-audit/scripts/check_training_parity.py --run thirdparties/DrEureka/globe_walking/runs/globe_walking/2026-06-18-server/train/082453.814727 --json`; `conda run -n go2-mjlab python scripts/go2_yoga_ball/export_iter_jit.py --run thirdparties/DrEureka/globe_walking/runs/globe_walking/2026-06-18-server/train/082453.814727 --ckpt ac_weights_017000.pt --out artifacts/go2_yoga_ball/globe_walking_2026_06_18_server_082453_iter17000_deploy`; `RUN=...iter17000_deploy OUT=logs/go2_yoga_ball/globe_walking_2026_06_18_server_082453_iter17000_isaacgym_playback NUM_ENVS=64 DURATION=12 bash scripts/go2_yoga_ball/run_isaac_playback.sh`; `MUJOCO_GL=egl conda run -n go2-mjlab python scripts/go2_yoga_ball/render_mujoco_scene_preview.py --run artifacts/go2_yoga_ball/globe_walking_2026_06_18_server_082453_iter17000_deploy --output artifacts/go2_yoga_ball/globe_walking_2026_06_18_server_082453_iter17000_rough_ground_preview.png --artifact artifacts/go2_yoga_ball/globe_walking_2026_06_18_server_082453_iter17000_rough_ground_preview.json`; `RUN=...iter17000_deploy LOG_DIR=logs/go2_yoga_ball/globe_walking_2026_06_18_server_082453_iter17000_default_rough_ground_sim2sim ART_DIR=artifacts/go2_yoga_ball/globe_walking_2026_06_18_server_082453_iter17000_default_rough_ground_sim2sim VIDEO_NAME=globe_walking_2026_06_18_server_082453_iter17000_default_rough_ground_sim2sim.mp4 bash scripts/go2_yoga_ball/run_sim2sim.sh`.
- Initial state: `2026-06-18-server/train/082453.814727` is the only saved run under that date bucket; the parity checker resolves `ac_weights_017000.pt` as the best saved reward checkpoint with only allowed diffs; and the live MuJoCo default path now uses deterministic rough ground with seed `17`, `ground_friction=0.5`, `base_z=1.2`, `ball_drag=0.3`, and `action_lag_steps=0`.
- Outputs: `artifacts/go2_yoga_ball/globe_walking_2026_06_18_server_082453_iter17000_default_rough_run_report.md`, `artifacts/go2_yoga_ball/globe_walking_2026_06_18_server_082453_iter17000_deploy/**`, `logs/go2_yoga_ball/globe_walking_2026_06_18_server_082453_iter17000_isaacgym_playback/**`, `artifacts/go2_yoga_ball/globe_walking_2026_06_18_server_082453_iter17000_rough_ground_preview.{png,json}`, `artifacts/go2_yoga_ball/globe_walking_2026_06_18_server_082453_iter17000_default_rough_ground_sim2sim/**`, and `logs/go2_yoga_ball/globe_walking_2026_06_18_server_082453_iter17000_default_rough_ground_sim2sim/**`.
- Success: parity passes with no unexpected diffs or early stop; the staged export passes the exact JIT self-check; Isaac playback records `63/64` survivors with the single deterministic failed env `29` plus success and failed-env videos; the preview PNG shows the expected smooth low-relief rough field; and the default rough-ground Sim2Sim run returns `0` from endpoint, bridge, policy, and render, confirms release, sends `460+` commands in the tracked rerun, survives the full `12s` window without a fall, and writes a rendered replay video.

### `WF-G2I` Offline real-DDS deploy investigation

- Environment: host shell with Python 3; no new robot or simulator runtime is required.
- Entry points: `python scripts/go2_yoga_ball/analyze_real_deploy_logs.py --log-dir /tmp/globe_walking_2026_06_18_server_082453_iter17000_real_dds_deploy/logs --compare-log-dir logs/go2_yoga_ball/globe_walking_2026_06_18_server_082453_iter17000_default_rough_ground_sim2sim`; inspect `scripts/go1_yoga_ball/deploy_lcm_policy.py`, `scripts/go2_yoga_ball/lcm_to_dds_bridge.py`, and `thirdparties/DrEureka/globe_walking/go1_gym_deploy/{envs/lcm_agent.py,utils/cheetah_state_estimator.py}` for the source-backed explanation.
- Initial state: the saved `iter17000` deploy export already exists; the user-created real-DDS logs live under `/tmp/globe_walking_2026_06_18_server_082453_iter17000_real_dds_deploy/logs`; and the tracked safe baseline for the same checkpoint exists under `logs/go2_yoga_ball/globe_walking_2026_06_18_server_082453_iter17000_default_rough_ground_sim2sim`.
- Outputs: `artifacts/go2_yoga_ball/globe_walking_2026_07_01_real_dds_deploy_investigation.md` plus console or JSON output from `scripts/go2_yoga_ball/analyze_real_deploy_logs.py`.
- Success: the workflow explains, without launching a new robot run, that the startup warning comes from zero-filled IMU timing history being used before enough callbacks arrive, that this warning also reproduces in the safe Sim2Sim baseline, and that the real-path rate drop is evidenced by many more `>=20 ms` policy-wall-time stalls and many more `>5 ms` bridge lowstate gaps than the safe baseline.

### `WF-G2J` Passive lowstate frequency monitor

- Environment: Docker `eureka-mujoco_sim2sim` with host networking; no policy, bridge, or `lowcmd` publisher should be running from this workflow.
- Entry points: `docker run --rm --network host -v /home/seqn/eureka-workspace:/workspace -w /workspace eureka-mujoco_sim2sim python3 /workspace/scripts/go2_yoga_ball/passive_lowstate_monitor.py --dds-domain 0 --network-interface eno1 --duration-s 20 --expected-rate-hz 500 --gap-threshold-ms 5 --out-dir /workspace/logs/go2_yoga_ball/passive_lowstate_monitor_real_dds`.
- Initial state: the target DDS source, real robot or simulator, is already publishing `rt/lowstate`; this workflow starts no policy, no bridge, and no command publisher, and the monitor script itself imports only `ChannelSubscriber` from SDK2.
- Outputs: chosen `--out-dir` containing `summary.json` and `packets.csv`.
- Success: the run proves the passive path receives packets at all, reports whole-window and active-window rate, interval percentiles, and count of gaps above the configured threshold, and exits without ever creating a `rt/lowcmd` publisher.

### `WF-G2K` Real-DDS deploy timing instrumentation

- Environment: same as the existing real-DDS deploy attempt: Docker `eureka-mujoco_sim2sim` for the bridge and Docker `eureka-isaacgym` for the policy, launched by the user's existing shell snippet with no CLI changes.
- Entry points: run the same three-process real-DDS deploy shell snippet the user already uses; then inspect the chosen log dir for `policy_timing.csv`, `policy_callbacks.csv`, `policy_callback_summary.json`, `policy_diagnostics.json`, `bridge_lowstate.csv`, `bridge_commands.csv`, and `bridge_diagnostics.json`.
- Initial state: the staged deploy export exists and the user is already launching the real-DDS bridge plus policy path manually; this instrumentation adds observability only and does not change that launch contract.
- Outputs: expanded `policy_timing.csv` columns for step breakdown and callback ages, `policy_callbacks.csv`, `policy_callback_summary.json`, `policy_diagnostics.json`, and `bridge_diagnostics.json` inside the same log root already passed to `--out-dir`.
- Success: the unchanged real deploy command produces enough evidence to distinguish adaptation/body inference time from sleep overruns, `get_obs` time, callback busy time, callback freshness, and bridge DDS-to-LCM republish cost without requiring a different runtime invocation.

### `WF-RAPP` DrEureka RAPP and prompt-debug review

- Environment: Docker Isaac playback path for the reviewed checkpoints; log-only for the prompt/debug runs.
- Entry points: existing review bundles under `artifacts/dr_eureka_rapp_checkpoint_review/**` and `logs/dr_eureka_rapp_checkpoint_review/**`; auxiliary logs under `logs/dr_eureka_rapp_0p8/**` and `logs/dr_eureka_phase3_ball_radius_0p45_0p55_10000x8/**`.
- Initial state: stock DrEureka checkpoints plus RAPP and phase-3 prompt/debug runs.
- Outputs: checkpoint review videos, manifests, copied reward code, and prompt/debug console logs.
- Success: each reviewed checkpoint ties back to playback height evidence or to a concrete prompt/runtime failure log.

### `WF-G2M` MJLab caller-project port

- Environment: FRESH host conda env `go2-mjlab`; server-compatible MJLab and RSL-RL assumptions documented in `scripts/go2_mjlab_dreureka_port/MUSA_COMPATIBILITY.md`.
- Entry points: `scripts/go2_mjlab_dreureka_port/run.sh preflight|source-contract|setup-env-record|import-smoke|task-config-smoke|verify-terrain-4096|render-scene|smoke-20min|report-smoke-20min|train-1-8-budget|report-train-1-8-budget|play-latest`.
- Initial state: installed `mjlab`, vendored Go2 assets under `dreureka_go2_mjlab/assets/unitree_go2/`, and read-only thirdparty baselines.
- Outputs: `artifacts/go2_mjlab_dreureka_port/**`, `logs/go2_mjlab_dreureka_port/**`, and `torchrunx_logs/**`.
- Success: caller task loads without upstream patches, terrain and reset semantics match the intended DrEureka contract, and the 1/8-budget train finishes with health reports.

### `WF-G2F` MJLab FRESH Sim2Sim

- Environment: FRESH host conda env `go2-mjlab`; no Docker in the runtime path.
- Entry points: `scripts/go2_mjlab_fresh_sim2sim/run.sh preflight|joint-order-contract|deployer-smoke|mjlab-playback|mjlab-playback-video|attempt|report`.
- Initial state: `logs/go2_mjlab_dreureka_port/train_1_8_budget/rsl_rl/model_19999.pt` exists, with the selected fallback `model_10000.pt` also tracked by the workflow.
- Outputs: `artifacts/go2_mjlab_fresh_sim2sim/**` and `logs/go2_mjlab_fresh_sim2sim/**`.
- Success: joint order is proven from executable state, native playback survives, the DDS deployer emits finite commands, and attempts either pass plain movement or fail with subsystem evidence.

## Repo Cleanliness

All initialized nested git repos are clean as of this sync. The only dirty git worktree is the root repo, because this state update, the new real-DDS timing instrumentation in existing scripts, the new passive lowstate monitor, the new offline real-DDS investigation script/report, the updated Isaac playback wrapper/docs, the local 2026-06-16 rerun report/artifacts, the new 2026-06-18-server rough-default rerun report/artifacts, earlier failed-env Isaac playback work, the latest rough-ground and current-default rerun reports, the Go2-vs-Go1 alignment report plus faithful smoke log, the MuJoCo default-path edits, and the duplicate-inventory retirement are uncommitted, the root already had user-side instruction-script changes, and the new runtime artifacts/logs are untracked.

| Repo | Status |
| --- | --- |
| `.` | Dirty: `STATE.md` update, real-DDS timing instrumentation in existing scripts, passive lowstate monitor, offline real-DDS investigation script/report, updated Isaac playback wrapper/docs, local 2026-06-16 rerun report/artifacts, new 2026-06-18-server rough-default rerun report/artifacts, failed-env Isaac playback runner/logs, deleted `CURRENT_INVENTORY.md`, reward-launcher rename/update, MuJoCo default-path edits, Go2-vs-Go1 alignment report plus faithful smoke log, latest rerun report/state artifacts, pre-existing `AGENTS.md` modification, and untracked runtime artifacts/logs. |
| `thirdparties/DrEureka` | Clean. |
| `thirdparties/MJLab` | Clean. |
| `thirdparties/wbc-workspace` | Clean. |
| `thirdparties/cyclonedds` | Clean. |
| `thirdparties/go2_description` | Clean. |
| `thirdparties/mujoco_menagerie` | Clean. |
| `thirdparties/unitree_mujoco` | Clean. |
| `thirdparties/unitree_rl_gym` | Clean. |
| `thirdparties/unitree_rl_mjlab` | Clean. |
| `thirdparties/unitree_sdk2_python` | Clean. |
| `thirdparties/wbc-workspace/thirdparties/unitree_mujoco` | Clean. |
| `thirdparties/wbc-workspace/thirdparties/{GR00T-WholeBodyControl,HoloMotion,run-sonic}` | Not initialized; pointer-only submodule entries, so no local worktree exists to audit. |

## Thirdparty Map

| Path | Kind | Remote or source | HEAD or state | Notes |
| --- | --- | --- | --- | --- |
| `thirdparties/DrEureka` | Git submodule fork | `https://github.com/5eqn/DrEureka.git` | `6dc5a838154f2bb1da5c1614dd242647a48b79f7`, clean | Main DrEureka training and deploy source; 30 user commits ahead of upstream `eureka-research/DrEureka` `main` at `1d4e00700423170717654516f4ef4b24cb0f3a84`. |
| `thirdparties/MJLab` | Git submodule | `https://github.com/mujocolab/mjlab.git` | `623ca0b41792864ad126f760528b5e8c0df6d4fd`, clean | Upstream snapshot used for inspection; host runtime prefers an installed `mjlab` package. |
| `thirdparties/wbc-workspace` | Git submodule | `https://github.com/5eqn/wbc-workspace` | `127dc7d7b4b89f4bd3ec1a253811e38afc6ada00`, clean | User-owned reference workspace with nested submodule pointers. |
| `thirdparties/cyclonedds` | Git snapshot | `https://github.com/eclipse-cyclonedds/cyclonedds.git` | `5041f3560c088c99e5088b2b8520b69169621196`, clean | DDS dependency for Docker and host runtime paths. |
| `thirdparties/go2_description` | Git snapshot | `https://github.com/Unitree-Go2-Robot/go2_description.git` | `8bd6717ff0c7b5ca388c0e10e426dd9ad873ceaf`, clean | Go2 ROS description reference. |
| `thirdparties/mujoco_menagerie` | Git snapshot | `https://github.com/google-deepmind/mujoco_menagerie.git` | `b846dd12bc459d776cccb3dee0b1d02acbf7a9c7`, clean | MuJoCo model reference library. |
| `thirdparties/unitree_mujoco` | Git snapshot | `https://github.com/unitreerobotics/unitree_mujoco.git` | `c598f103acb87a5fd3de7c9037f4dab6aa7f232b`, clean | Unitree MuJoCo DDS simulator reference. |
| `thirdparties/unitree_rl_gym` | Git snapshot | `https://github.com/unitreerobotics/unitree_rl_gym.git` | `276801e46c5d433564f24658bac64f254b7d2d4b`, clean | Go2 URDF and Isaac training reference. |
| `thirdparties/unitree_rl_mjlab` | Git snapshot | `https://github.com/unitreerobotics/unitree_rl_mjlab.git` | `1425b15f73bd4095f0df53709d7c389c3eb9e790`, clean | Source of vendored Go2 MJLab XML and constants. |
| `thirdparties/unitree_sdk2_python` | Git snapshot | `https://github.com/unitreerobotics/unitree_sdk2_python.git` | `794fb2b3fd9165fd245a7b568698d9e97d8ac0a0`, clean | Python DDS client used by host and Docker deploy paths. |
| `thirdparties/IsaacGym` | Vendor payload | Local extracted package | Non-git | Isaac Gym binaries and Python package. |
| `thirdparties/IsaacGym_Preview_4_Package.tar.gz` | Vendor payload | Local tarball | Non-git | Isaac Gym package archive. |
| `thirdparties/torch_wheels/**` | Vendor payload | Local wheel cache | Non-git | Torch wheel payloads for host setup. |
| `thirdparties/wbc-workspace/thirdparties/unitree_mujoco` | Nested git submodule | `https://github.com/unitreerobotics/unitree_mujoco.git` | `c598f103acb87a5fd3de7c9037f4dab6aa7f232b`, clean | Nested mirror of the same Unitree MuJoCo snapshot. |
| `thirdparties/wbc-workspace/thirdparties/{GR00T-WholeBodyControl,HoloMotion,run-sonic}` | Nested submodule entries | URLs recorded in `thirdparties/wbc-workspace/.gitmodules` | Not initialized | Pointer-only in this checkout; no nested worktrees are present yet. |

## Thirdparty Changes

### `thirdparties/DrEureka`

- Upstream base: `https://github.com/eureka-research/DrEureka.git` `main` at `1d4e00700423170717654516f4ef4b24cb0f3a84` (`2024-08-26`, `Update README.md`).
- Local fork: `https://github.com/5eqn/DrEureka.git` `main` at `6dc5a838154f2bb1da5c1614dd242647a48b79f7`.
- Worktree audit: clean.
- Divergence rule for this repo: every commit authored by `5eqn` is a user update; relative to upstream `main`, the current checkout is exactly these 30 commits ahead:

```text
aacfbf9 2026-05-27 Support reproducible globe walking training runs
19d97a3 2026-05-27 Add Go2 yoga ball training path
05b26e5 2026-05-27 Add selectable PhysX training profile
36c7581 2026-05-27 Expose checkpoint resume for training
68da374 2026-05-27 Fix training checkpoint resume CLI scope
a863e11 2026-05-30 Align Go2 DrEureka training settings
7f14fe9 2026-05-31 Configure DrEureka for Go2 LLM generation
1bcc8c0 2026-05-31 Add Eureka import diagnostics
7cc9a75 2026-05-31 Avoid unsupported n parameter in Eureka LLM calls
93ab31a 2026-05-31 Cache Eureka LLM responses
fdb51f1 2026-05-31 Add non-Isaac DrEureka requirements
1808161 2026-05-31 Pin numpy for DrEureka environment
5858c4b 2026-05-31 Fix Go2 Eureka training imports
c5842ee 2026-05-31 Update Go2 Eureka reward terms
2f517e1 2026-06-01 Update debugging and start command
6bfc081 2026-06-01 Fix Eureka training orchestration
bbccf3b 2026-06-02 Add resume & tolerate exit code 0
d9a6f54 2026-06-02 Fix module import
dc04bdb 2026-06-02 Change height requirement
2b68635 2026-06-02 Set globe walking ball radius baseline
a9fcee1 2026-06-02 Correct LLM loop
345c16c 2026-06-03 Save generated globe walking reward and DR config
65e0d2f 2026-06-03 Early stop + raise RAPP height range
44f966a 2026-06-03 Raise height to correct range
c121448 2026-06-03 Set no video
82e7a6b 2026-06-04 Update globe walking domain randomization
4d3097e 2026-06-04 Fix RAPP & DrEureka robot
5c89595 2026-06-05 Pretrained DR profile fix
d47d9f9 2026-06-05 Fix training
6dc5a83 2026-06-15 Fix pretrained roughness range
```

### `thirdparties/wbc-workspace`

- Remote in this checkout: `https://github.com/5eqn/wbc-workspace`.
- Local repo: `main` at `127dc7d7b4b89f4bd3ec1a253811e38afc6ada00`.
- Worktree audit: clean.
- Divergence note: this checkout has no separate upstream remote configured, and the first visible commit is a `5eqn` root commit. In practice, the whole visible history below is user-maintained thirdparty state for this workspace.
- Documented `5eqn` commits:

```text
5e42f70 2026-05-20 Initial commit
da609d7 2026-05-20 Clarify requirements
b610171 2026-05-20 Reify requirements
5240837 2026-05-21 Prepare trying GPT-5.5
9a1bd2f 2026-05-21 Add run-sonic reference gate
4b47078 2026-05-21 Require release after control before playback
6583b0c 2026-05-21 Add Docker benchmark scaffold
d034960 2026-05-21 Validate support release ordering
aac0b62 2026-05-21 Require stock HoloMotion v1.3 deploy path
ae124db 2026-05-21 Add stock deploy preflight
00eda6e 2026-05-21 Stage assets for stock deploy paths
58e4368 2026-05-21 Add stock image runtime validation
ec42d3e 2026-05-21 Install stock SONIC deploy environment
74a7300 2026-05-21 Add stock deploy hard gate
e22c0c0 2026-05-21 Build stock HoloMotion deploy image
087a414 2026-05-21 Validate stock HoloMotion launcher image
f124801 2026-05-21 Stage assets before image builds
1c179a3 2026-05-21 Add stock HoloMotion launch smoke test
05d7736 2026-05-21 Build stock SONIC deploy image
5c9b4ef 2026-05-22 Report flat benchmark logs
1072c5d 2026-05-22 Tighten stock deploy motion tracking gate
63d5573 2026-05-22 Add release gate smoke validation
7b0ab29 2026-05-22 Install Unitree Python DDS bridge in simulator image
946dcdd 2026-05-22 Add headless Unitree simulator bridge smoke
ad64f90 2026-05-22 Verify simulator support release control
7c8db8f 2026-05-22 Add stock policy sequence runner
7bcacff 2026-05-22 Fix sequence runner smoke issues
bc3eac0 2026-05-22 Tighten stock deploy hard gate
4090fbd 2026-05-22 Bridge HoloMotion stock deploy to simulator
b3ea1f3 2026-05-22 Stabilize HoloMotion D-pad selection
a5ee379 2026-05-22 Gate HoloMotion release on stable hold
86f703c 2026-05-22 Pin simulator root during precontrol support
3655266 2026-05-22 Debounce HoloMotion controller selection
9f26003 2026-05-22 Seed simulator from selected motion reference
9d90b9a 2026-05-22 Use flat scene and simulator control diagnostics
d5557ef 2026-05-22 Align simulator DDS and bridge diagnostics
0eb2afa 2026-05-22 Use policy-matched support hold gains
69a7004 2026-05-22 Align SONIC simulator diagnostics
3a1fda3 2026-05-22 Align SONIC stock motion inputs
516abcc 2026-05-22 Keep simulator paced to MuJoCo time
ad0499c 2026-05-22 Use stock SONIC motion body subset
b7a2346 2026-05-22 Release SONIC support immediately after control
fcca329 2026-05-22 Add runtime validation hints
1f5755b 2026-05-22 Clean stale benchmark containers before runs
66b99e2 2026-05-22 Start HoloMotion from default pose
3a2e80e 2026-05-22 Settle sensitive SONIC motion after release
aa2c706 2026-05-22 Mark HoloMotion playback at B trigger
7a1e09a 2026-05-22 Hold HoloMotion velocity after release
073d809 2026-05-22 Fix HoloMotion init-reference quaternion order
e736353 2026-05-22 Record HoloMotion stock-deploy diagnostics
5b32457 2026-05-22 Stop fallen motion runs early
d39668b 2026-05-22 Record HoloMotion sim2sim failure diagnostics
8ed0bb7 2026-05-22 Clarify HoloMotion sim2sim diagnostic limits
54e6588 2026-05-22 Record current full-batch failure set
c40108e 2026-05-22 Expose simulator support height option
0e8347e 2026-05-22 Rigidify comparison video hard gate
1917e3e 2026-05-22 Require raw MuJoCo evidence and release proofs
6496e43 2026-05-22 Clarify benchmark hard gates
8218ea7 2026-05-22 Remove comparison ghost requirement
ed26b90 2026-05-22 Align release docs with support pinning
7352738 2026-05-22 Validate release physics and render replay videos
3bb4783 2026-05-22 Add single 29DOF robot hard gate
1438397 2026-05-22 Use shared 29DOF simulator scene
7629c7d 2026-05-22 Simplify shared simulator initialization
b7c26d3 2026-05-22 Harden benchmark reruns
ad161c7 2026-05-22 Update benchmark status evidence
127dc7d 2026-05-22 Add run-sonic reference
```

### Audited clean thirdparty snapshots with no `5eqn` commits

- `thirdparties/MJLab`
- `thirdparties/cyclonedds`
- `thirdparties/go2_description`
- `thirdparties/mujoco_menagerie`
- `thirdparties/unitree_mujoco`
- `thirdparties/unitree_rl_gym`
- `thirdparties/unitree_rl_mjlab`
- `thirdparties/unitree_sdk2_python`
