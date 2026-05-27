# Lessons Learned

## Training Budget Claims Must Match Evidence

- Do not run a tiny or materially under-budget training pass, observe that it is not equivalent to a pretrained policy, and then imply the training setup is ineffective.
- Before judging a training recipe, compare the actual env count, iteration count, rollout steps per env, total environment transitions, optimizer update count, multi-GPU setting, and relevant curriculum/domain-randomization schedule against the reference run.
- A smoke training run only proves that the training pipeline executes and produces checkpoints. It is not evidence about final policy quality unless its compute budget and validation gates are comparable to the reference policy.
- Reports should phrase under-budget failures as "not equivalent under this attempted budget/configuration" rather than as a failure of the training method.

Example from the DrEureka Go1 yoga-ball work:

- Reference pretrained run evidence showed about `20000` iterations, `4096` envs, and `24` rollout steps per env, for `20000 * 4096 * 24 = 1,966,080,000` environment steps.
- The attempted reproduction used about `3000` iterations, `1024` envs, and `24` rollout steps per env, for `3000 * 1024 * 24 = 73,728,000` environment steps. That is only about `3.75%` of the reference sample budget and should be reported as an under-budget pipeline/behavior check, not as evidence that training is ineffective.
- If the GPU can only fit `2048` live envs, `40000 * 2048 * 24` matches the raw sample count but is not algorithmically identical because it doubles PPO update count and halves rollout batch size per update.
- The closer algorithmic reproduction is `20000` PPO updates with an effective rollout batch of `4096 * 24`, implemented as two `2048`-env rollout collections at fixed policy weights before each PPO update.
- When choosing between a domain-randomization profile similar to the pretrained policy and a fresh repo-default profile, choose the pretrained-similar profile first because it is closer to the known successful run.

`TRAIN_ROLLOUT_ACCUMULATION` is not implemented in the current DrEureka/Isaac Gym path. Do not put it in a runnable command until the PPO runner and `scripts/go1_yoga_ball/run.sh` actually support it.

Runnable same-sample-budget approximation with the current scripts:

```bash
cd /home/seqn/eureka-workspace
ITERATIONS=20000 TRAIN_NUM_ENVS=4096 TRAIN_NO_VIDEO=1 TRAIN_SAVE_INTERVAL=1000 TRAIN_DOMAIN_RAND_PROFILE=pretrained \
  ./scripts/go1_yoga_ball/run.sh train-default-isaacgym
```

Unattended variant:

```bash
cd /home/seqn/eureka-workspace
mkdir -p logs/go1_yoga_ball/default_train/train
nohup bash -lc 'ITERATIONS=40000 TRAIN_NUM_ENVS=2048 TRAIN_NO_VIDEO=1 TRAIN_SAVE_INTERVAL=1000 ./scripts/go1_yoga_ball/run.sh train-default-isaacgym' \
  > logs/go1_yoga_ball/default_train/train/train_40k_2048.nohup.log 2>&1 &
```

Estimated train time:

- Observed `3000 * 1024 * 24` run took about `49.1` minutes, or about `0.986` seconds per PPO iteration at `1024` envs.
- A rough linear estimate for `40000 * 2048 * 24` is `40000 * 0.986 * 2 = 78,880` seconds, or about `21.9` hours.
- Treat this as an order-of-magnitude estimate. Actual time depends on GPU memory pressure, Isaac Gym throughput at `2048` envs, Docker/GPU contention, checkpoint save cost, and whether the process starts from a cold extension build/cache.

Training artifacts from the runnable command:

- Console/train log from orchestration: `logs/go1_yoga_ball/default_train/train/train.log`. This file is overwritten by each `train-default-isaacgym` run because the script writes through `tee`.
- Unattended wrapper log, if using the `nohup` command above: `logs/go1_yoga_ball/default_train/train/train_40k_2048.nohup.log`.
- DrEureka run directory: `thirdparties/DrEureka/globe_walking/runs/globe_walking/<YYYY-MM-DD>/train/<HHMMSS.microseconds>/`.
- Policy/checkpoint files inside the selected run: `checkpoints/ac_weights_last.pt`, `checkpoints/body_latest.jit`, and `checkpoints/adaptation_module_latest.jit`.
- Saved run metadata inside the selected run: `parameters.pkl`, `metrics.pkl`, `outputs.log`, and any videos/checkpoints DrEureka emits according to the configured save intervals.
- Root orchestration selection artifacts after the command finishes: `artifacts/go1_yoga_ball/default_train_selected_run.txt`, `artifacts/go1_yoga_ball/default_train_run.json`, and updated `artifacts/go1_yoga_ball/policy_registry.json`.

## Go2 Isaac Gym 4096-Env Segfault Was PhysX Buffer Profile

- Symptom: Go2 `--dr-config off --num-envs 4096` exited `139` before the first PPO iteration, while Go1 training and smaller Go2 smoke runs succeeded.
- Reproduction sweep: Go2 completed one iteration at `512`, `1024`, and `2048` envs with `physx_mini`; the same command at `4096` envs segfaulted before iteration logging.
- Fix: run high-env Go2 training with the `physx_full` profile (`max_gpu_contact_pairs=16777216`, `default_buffer_size_multiplier=64`) instead of `physx_mini` (`8388608`, `5`).
- Validation: `4096` Go2 envs completed one iteration with `--physx-profile full`, logging total reward and saving iteration `0`.

Relevant logs:

- `logs/go2_yoga_ball/debug_segfault/env_4096/train.log` and `status.txt`: failing `physx_mini` case, `status=139`.
- `logs/go2_yoga_ball/debug_segfault/env_4096_physx_full/train.log` and `status.txt`: passing `physx_full` case, `status=0`.

Runnable validation command:

```bash
cd /home/seqn/eureka-workspace
docker run --rm --gpus all \
  -e WANDB_MODE=disabled \
  -e PYTHONPATH=/workspace/eureka-workspace/thirdparties/DrEureka:/workspace/eureka-workspace/thirdparties/DrEureka/globe_walking:/workspace/eureka-workspace/thirdparties/DrEureka/forward_locomotion \
  -e GO2_DESCRIPTION_URDF=/workspace/eureka-workspace/artifacts/go2_yoga_ball/build/go2_description_isaacgym.urdf \
  -v /home/seqn/eureka-workspace:/workspace/eureka-workspace \
  -w /workspace/eureka-workspace/thirdparties/DrEureka \
  eureka-isaacgym \
  bash -lc 'python globe_walking/scripts/train.py --robot go2 --dr-config off --reward-config eureka --iterations 1 --num-envs 4096 --no-video --no-wandb --domain-rand-profile pretrained --physx-profile full --save-interval 1000'
```
