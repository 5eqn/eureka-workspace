#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-/home/seqn/eureka-workspace}"
RUN="${RUN:?set RUN to the host or container checkpoint run directory}"
OUT="${OUT:-/tmp/go2_isaac_playback}"
NUM_ENVS="${NUM_ENVS:-64}"
DURATION="${DURATION:-12}"
DEVICE="${DEVICE:-cuda:0}"

case "$RUN" in
  /workspace/*) RUN_CONT="$RUN" ;;
  "$ROOT"/*) RUN_CONT="/workspace/${RUN#"$ROOT"/}" ;;
  *) RUN_CONT="$RUN" ;;
esac

mkdir -p "$OUT"

docker run --rm --gpus all --network host \
  -e WANDB_MODE=disabled \
  -e PYTHONPATH=/workspace/thirdparties/DrEureka:/workspace/thirdparties/DrEureka/globe_walking:/workspace/thirdparties/DrEureka/forward_locomotion \
  -e GO2_URDF=/workspace/thirdparties/unitree_rl_gym/resources/robots/go2/urdf/go2.urdf \
  -v "$ROOT:/workspace" \
  -v "$OUT:$OUT" \
  -w /workspace/thirdparties/DrEureka \
  eureka-isaacgym \
  bash -lc "set -o pipefail; python /workspace/scripts/go2_yoga_ball/isaacgym_playback_smoke.py \
    --run '$RUN_CONT' \
    --out-dir '$OUT' \
    --num-envs '$NUM_ENVS' \
    --duration-s '$DURATION' \
    --device '$DEVICE' \
    --record-video \
    --use-saved-contract \
    --preserve-domain-rand 2>&1 | tee '$OUT/run.log'"
