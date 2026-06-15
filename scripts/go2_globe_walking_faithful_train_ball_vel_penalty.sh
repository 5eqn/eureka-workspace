#!/usr/bin/env bash
#
# Run the DrEureka globe_walking Go2 faithful training with the reward inlined
# and three additions on top of the original four-term Eureka reward:
#   1. steep joint-limit proximity penalty
#   2. ball-stationarity shaping
#   3. jerk penalty
#
# The file name is kept for workflow compatibility, but this is no longer the
# old ball-velocity-only experiment.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${ROOT:-$(cd -- "${SCRIPT_DIR}/.." && pwd)}"

if [[ -n "${CUDA_VISIBLE_DEVICES:-}" && "${CUDA_VISIBLE_DEVICES}" != "all" ]]; then
  IFS=',' read -r -a GPU_IDS <<<"${CUDA_VISIBLE_DEVICES}"
  GPU_COUNT="${#GPU_IDS[@]}"
  DOCKER_GPUS="device=${CUDA_VISIBLE_DEVICES}"
else
  if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "nvidia-smi not found and CUDA_VISIBLE_DEVICES is unset; cannot detect GPU count." >&2
    exit 1
  fi
  GPU_COUNT="$(nvidia-smi --query-gpu=index --format=csv,noheader | wc -l | tr -d ' ')"
  DOCKER_GPUS="all"
fi

NPROC_PER_NODE="${PARALLEL_COUNT:-${NPROC_PER_NODE:-$GPU_COUNT}}"
if ! [[ "${NPROC_PER_NODE}" =~ ^[0-9]+$ ]] || (( NPROC_PER_NODE < 1 )); then
  echo "NPROC_PER_NODE must be a positive integer, got: ${NPROC_PER_NODE}" >&2
  exit 1
fi

CONTAINER_NAME="go2-globe-jointlimit-stationary-jerk-$(date +%Y%m%d-%H%M%S)"

docker run -d --gpus "${DOCKER_GPUS}" \
  --ipc=host \
  --runtime=nvidia \
  --name "${CONTAINER_NAME}" \
  -e WANDB_MODE=disabled \
  -e NPROC_PER_NODE="${NPROC_PER_NODE}" \
  -e PYTHONPATH=/workspace/thirdparties/DrEureka:/workspace/thirdparties/DrEureka/globe_walking:/workspace/thirdparties/DrEureka/forward_locomotion \
  -e GO2_URDF=/workspace/thirdparties/unitree_rl_gym/resources/robots/go2/urdf/go2.urdf \
  -v "${ROOT}:/workspace" \
  -w /workspace/thirdparties/DrEureka \
  eureka-isaacgym \
  bash -lc '
set -euo pipefail
git config --global --add safe.directory /workspace/thirdparties/DrEureka || true

cat >/tmp/eureka_reward_inline.py <<'"'"'REWARD'"'"'
import torch


class EurekaReward():
    def __init__(self, env):
        self.env = env

    def load_env(self, env):
        self.env = env

    def _reward_height(self):
        env = self.env
        height_threshold = 2.0 * env.ball_radius
        height_temperature = 7.0
        height_exp = torch.exp((env.base_pos[:, 2] - height_threshold) / height_temperature)
        height_reward = torch.where(
            env.base_pos[:, 2] >= height_threshold,
            height_exp,
            torch.zeros_like(env.base_pos[:, 2]),
        )
        return 1.5 * height_reward

    def _reward_balance(self):
        env = self.env
        balance_temperature = 5.0
        ball_top = env.object_pos_world_frame.clone()
        ball_top[:, 2] += env.ball_radius
        feet_dist_to_ball_top = torch.norm(env.foot_positions - ball_top.unsqueeze(1), dim=-1)
        balance_exp = torch.exp(-feet_dist_to_ball_top / balance_temperature)
        balance_reward = torch.mean(balance_exp, dim=-1)
        return 2.0 * balance_reward

    def _reward_smooth_actions(self):
        env = self.env
        action_diff = env.actions - env.last_actions
        smooth_actions_reward = -torch.mean(torch.abs(action_diff), dim=-1)
        return 1.0 * smooth_actions_reward

    def _reward_penalize_large_actions(self):
        env = self.env
        large_action_penalty = -torch.mean(torch.abs(env.actions), dim=-1)
        return 0.3 * large_action_penalty

    def _reward_joint_limit_barrier(self):
        env = self.env
        lower = env.dof_pos_limits[:, 0].unsqueeze(0)
        upper = env.dof_pos_limits[:, 1].unsqueeze(0)
        span = torch.clamp(upper - lower, min=1e-3)
        clearance = torch.minimum(env.dof_pos - lower, upper - env.dof_pos) / span

        margin = 0.15
        d = torch.clamp(clearance, max=margin)
        proximity_penalty = -4.0 * torch.square((margin - d) / margin)
        proximity_penalty = torch.where(d < margin, proximity_penalty, torch.zeros_like(proximity_penalty))
        return torch.mean(proximity_penalty, dim=-1)

    def _reward_keep_ball_stationary(self):
        env = self.env
        ball_speed = torch.norm(env.object_lin_vel, dim=-1)
        return -2.0 * ball_speed

    def _reward_penalize_action_jerk(self):
        env = self.env
        jerk = env.actions - 2.0 * env.last_actions + env.last_last_actions
        return -0.15 * torch.mean(torch.abs(jerk), dim=-1)

    def compute_success(self):
        return torch.ones_like(self.env.base_pos[:, 2])
REWARD

cat >/tmp/pretrained_go2_train.py <<'"'"'PY'"'"'
import os
import sys
import types
from pathlib import Path

import isaacgym

assert isaacgym

reward_source = open("/tmp/eureka_reward_inline.py", encoding="utf-8").read()
reward_module = types.ModuleType("globe_walking.go1_gym.rewards.eureka_reward")
exec(compile(reward_source, "inline_eureka_reward.py", "exec"), reward_module.__dict__)
sys.modules["globe_walking.go1_gym.rewards.eureka_reward"] = reward_module

from globe_walking.go1_gym import MINI_GYM_ROOT_DIR
from globe_walking.go1_gym.envs.base.legged_robot_config import Cfg

Cfg.multi_gpu = int(os.environ.get("NPROC_PER_NODE", "1")) > 1

import globe_walking.scripts.train as train_mod

train_mod.Path = Path
train_mod.MINI_GYM_ROOT_DIR = MINI_GYM_ROOT_DIR

train_mod.train_go1(
    iterations=20000,
    dr_config="off",
    robot="go2",
    headless=True,
    no_wandb=True,
    num_envs=4096,
    record_video=False,
    save_interval=1000,
    domain_rand_profile="pretrained",
    physx_profile="full",
    early_stop=False,
)
PY

if (( NPROC_PER_NODE > 1 )); then
  python -m torch.distributed.run --standalone --nnodes=1 --nproc_per_node="${NPROC_PER_NODE}" /tmp/pretrained_go2_train.py
else
  python /tmp/pretrained_go2_train.py
fi
'

echo "Started training container: ${CONTAINER_NAME}"
echo "Workspace mount: ${ROOT}"
echo "Visible GPUs: ${GPU_COUNT}"
echo "Training processes: ${NPROC_PER_NODE}"
echo "Follow logs with: docker logs -f ${CONTAINER_NAME}"
