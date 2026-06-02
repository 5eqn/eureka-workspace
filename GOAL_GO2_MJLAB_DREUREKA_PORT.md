# Goal: DrEureka Go2 Training Inside MJLab

## Outcome

Reproduce the corrected DrEureka Go2 yoga-ball baseline inside MJLab using the FRESH host workflow. The result must be a faithful baseline port, not a tuned MJLab variant: Go2 model data is vendored from `unitree_rl_mjlab` into the caller project, reward/observation/reset/training logic mirrors DrEureka, and only reproduction fixes are allowed.

Both Claude Opus 4.6 and human experts in embodied intelligence should be able to review the source contract, smoke evidence, reward curve, and final 1/8-budget train and agree that this is a defensible MJLab reproduction of the existing DrEureka Go2 baseline.

## Source Baseline

- DrEureka source: `/home/seqn/eureka-workspace/thirdparties/DrEureka`, read-only for this goal.
- MJLab runtime: installed `mjlab==1.2.0` package in the FRESH conda environment.
- Unitree MJLab Go2 data: vendored XML, meshes, collision config, and robot factory under `scripts/go2_mjlab_dreureka_port/dreureka_go2_mjlab/`; a new machine does not need to clone `unitree_rl_mjlab` for training.
- Reward-health baseline: `logs/go2_yoga_ball/train_original_settings_1_8_budget/train.log`.
- Existing launch baseline: `artifacts/go2_yoga_ball/train_original_settings_1_8_budget_launch.json`, with 4096 envs and 20000 iterations on one RTX3090.

## Verification Surface

All new runnable inputs live under `scripts/go2_mjlab_dreureka_port/`. Runtime evidence is written under:

```text
logs/go2_mjlab_dreureka_port/
├── preflight.log
├── smoke_20min/
│   └── train.log
└── train_1_8_budget/
    └── train.log

artifacts/go2_mjlab_dreureka_port/
├── source_contract.json
├── source_contract.md
├── smoke_20min_reward_curve.csv
├── smoke_20min_reward_curve.svg
├── smoke_20min_health.json
├── smoke_20min_health.md
├── train_1_8_budget_launch.json
├── train_1_8_budget_reward_curve.csv
├── train_1_8_budget_reward_curve.svg
├── train_1_8_budget_health.json
└── train_1_8_budget_health.md
```

The source contract must explicitly account for DrEureka Go2 robot configuration, yoga-ball scene/object logic, observation dimensions/history, reward terms, termination conditions, domain-randomization profile, PPO hyperparameters, save interval, env count, and iteration count.

## Constraints

- Use FRESH: host conda and project-agnostic home-space upstream dependencies, not Docker.
- Use China mirrors whenever possible for package downloads, after testing reachability.
- Do not patch `/home/seqn/MJLab`, `/home/seqn/unitree_rl_mjlab`, or `thirdparties/DrEureka`.
- Do not tune rewards, curriculum, PPO hyperparameters, or model behavior for performance. Changes are allowed only when needed to faithfully reproduce DrEureka semantics in MJLab.
- Put scenes and caller-project runtime inputs under `scripts/go2_mjlab_dreureka_port/`, not under `artifacts/`.
- Keep workspace inventory synchronized whenever files are added, moved, removed, or repurposed.

## Plan

1. Establish the source contract.
   - Verify: `scripts/go2_mjlab_dreureka_port/run.sh preflight` writes `artifacts/go2_mjlab_dreureka_port/source_contract.{json,md}` and confirms the installed MJLab runtime plus vendored Go2 data are available.

2. Build the MJLab caller project.
   - Verify: an import/config smoke instantiates the MJLab Go2 DrEureka task at small env count without editing upstream repositories.

3. Run a 20-minute smoke train.
   - Verify: `logs/go2_mjlab_dreureka_port/smoke_20min/train.log` plus reward-curve CSV/SVG and health report show no NaNs, regular iterations, sane episode length, and reward trend comparable to the early segment of `logs/go2_yoga_ball/train_original_settings_1_8_budget/train.log`.

4. Iterate only on faithful-reproduction defects.
   - Verify: every change is tied to a source-contract mismatch or runtime reproduction failure, and the health report names the exact mismatch fixed.

5. Launch the established 1/8-budget train.
   - Verify: `train_1_8_budget_launch.json` records 4096 envs, 20000 iterations, save interval 1000, one RTX3090, and the same single-GPU budget interpretation used by the corrected DrEureka train.

## Iteration Policy

If smoke health is poor, first compare the source contract against the MJLab implementation. Fix missing or mismatched DrEureka semantics before considering any simulator-specific adaptation. Do not adjust reward weights or PPO knobs to make the curve look better.

## Blocked Stop Condition

Stop and report blocked if faithful reproduction requires patching MJLab, unitree_rl_mjlab, DrEureka, MuJoCo Warp, or another upstream dependency, or if MJLab lacks a required physics feature for the yoga-ball task and no caller-project-only implementation path is defensible.
