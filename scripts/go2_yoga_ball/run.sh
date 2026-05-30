#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

usage() {
  echo "Usage: $0 [init-artifacts|validate-deps|inventory-assets|prepare-isaacgym-urdf|mujoco-dds-endpoint-report|lcm-to-dds-bridge-report|consistency-report|train-smoke-isaacgym|phase-go2-train-report|train-1-8-isaacgym|monitor-train-1-8|preflight]"
}

isaacgym_env=(
  -e WANDB_MODE=disabled
  -e PYTHONPATH=/workspace/eureka-workspace/thirdparties/DrEureka:/workspace/eureka-workspace/thirdparties/DrEureka/globe_walking:/workspace/eureka-workspace/thirdparties/DrEureka/forward_locomotion
  -e GO2_URDF=/workspace/eureka-workspace/thirdparties/unitree_rl_gym/resources/robots/go2/urdf/go2.urdf
  -v "$ROOT_DIR:/workspace/eureka-workspace"
  -w /workspace/eureka-workspace/thirdparties/DrEureka
)

cmd="${1:-preflight}"
case "$cmd" in
  init-artifacts)
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go2_yoga_ball/runner.py" init-artifacts
    ;;
  validate-deps)
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go2_yoga_ball/runner.py" validate-deps
    ;;
  inventory-assets)
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go2_yoga_ball/asset_inventory.py"
    ;;
  prepare-isaacgym-urdf)
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go2_yoga_ball/runner.py" prepare-isaacgym-urdf
    ;;
  mujoco-dds-endpoint-report)
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go2_yoga_ball/runner.py" mujoco-dds-endpoint-report
    ;;
  lcm-to-dds-bridge-report)
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go2_yoga_ball/runner.py" lcm-to-dds-bridge-report
    ;;
  consistency-report)
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go2_yoga_ball/runner.py" consistency-report
    ;;
  train-smoke-isaacgym)
    "$0" mujoco-dds-endpoint-report
    "$0" lcm-to-dds-bridge-report
    "$0" consistency-report
    "$0" prepare-isaacgym-urdf
    log_dir="$ROOT_DIR/logs/go2_yoga_ball/train_smoke"
    mkdir -p "$log_dir"
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go2_yoga_ball/runner.py" runs-before-smoke
    iterations="${ITERATIONS:-5}"
    num_envs="${TRAIN_NUM_ENVS:-64}"
    domain_rand_profile="${TRAIN_DOMAIN_RAND_PROFILE:-repo}"
    physx_profile="${TRAIN_PHYSX_PROFILE:-full}"
    docker run --rm --gpus all "${isaacgym_env[@]}" eureka-isaacgym \
      bash -lc "set -o pipefail; git config --global --add safe.directory /workspace/eureka-workspace/thirdparties/DrEureka || true; python globe_walking/scripts/train.py --robot go2 --dr-config off --reward-config eureka --iterations '$iterations' --num-envs '$num_envs' --no-video --no-wandb --domain-rand-profile '$domain_rand_profile' --physx-profile '$physx_profile' --save-interval '${TRAIN_SAVE_INTERVAL:-1}' 2>&1 | tee /workspace/eureka-workspace/logs/go2_yoga_ball/train_smoke/train.log"
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go2_yoga_ball/runner.py" runs-after-smoke
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go2_yoga_ball/runner.py" record-train-smoke-run
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go2_yoga_ball/runner.py" phase-go2-train-report
    ;;
  train-1-8-isaacgym)
    "$0" mujoco-dds-endpoint-report
    "$0" lcm-to-dds-bridge-report
    "$0" consistency-report
    "$0" prepare-isaacgym-urdf
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go2_yoga_ball/runner.py" require-training-gates
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go2_yoga_ball/runner.py" guard-train-1-8-not-launched
    log_dir="$ROOT_DIR/logs/go2_yoga_ball/train_1_8_budget"
    mkdir -p "$log_dir"
    : > "$log_dir/train.log"
    iterations="${ITERATIONS:-20000}"
    num_envs="${TRAIN_NUM_ENVS:-4096}"
    domain_rand_profile="${TRAIN_DOMAIN_RAND_PROFILE:-pretrained}"
    save_interval="${TRAIN_SAVE_INTERVAL:-1000}"
    physx_profile="${TRAIN_PHYSX_PROFILE:-full}"
    container_name="eureka-go2-train-1-8-$(date +%Y%m%d-%H%M%S)"
    container_id="$(
      docker run -d --gpus all --name "$container_name" "${isaacgym_env[@]}" eureka-isaacgym \
        bash -lc "set -o pipefail; git config --global --add safe.directory /workspace/eureka-workspace/thirdparties/DrEureka || true; python globe_walking/scripts/train.py --robot go2 --dr-config off --reward-config eureka --iterations '$iterations' --num-envs '$num_envs' --no-video --no-wandb --domain-rand-profile '$domain_rand_profile' --physx-profile '$physx_profile' --save-interval '$save_interval' 2>&1 | tee /workspace/eureka-workspace/logs/go2_yoga_ball/train_1_8_budget/train.log"
    )"
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go2_yoga_ball/runner.py" record-train-1-8-launch \
      --container-id "$container_id" \
      --container-name "$container_name" \
      --iterations "$iterations" \
      --num-envs "$num_envs" \
      --domain-rand-profile "$domain_rand_profile" \
      --physx-profile "$physx_profile" \
      --save-interval "$save_interval"
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go2_yoga_ball/runner.py" monitor-train-1-8 \
      --container-id "$container_id" \
      --duration-s "${TRAIN_HEALTH_DURATION_S:-300}" \
      --interval-s "${TRAIN_HEALTH_INTERVAL_S:-30}"
    ;;
  monitor-train-1-8)
    container_id="${TRAIN_CONTAINER_ID:-}"
    if [[ -z "$container_id" ]]; then
      container_id="$("$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path
p = Path("artifacts/go2_yoga_ball/train_1_8_budget_launch.json")
print(json.loads(p.read_text())["container_id"])
PY
)"
    fi
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go2_yoga_ball/runner.py" monitor-train-1-8 \
      --container-id "$container_id" \
      --duration-s "${TRAIN_HEALTH_DURATION_S:-300}" \
      --interval-s "${TRAIN_HEALTH_INTERVAL_S:-30}"
    ;;
  phase-go2-train-report)
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go2_yoga_ball/runner.py" phase-go2-train-report
    ;;
  preflight)
    "$0" init-artifacts
    "$0" validate-deps
    "$0" inventory-assets
    "$0" prepare-isaacgym-urdf
    "$0" mujoco-dds-endpoint-report
    "$0" lcm-to-dds-bridge-report
    "$0" consistency-report
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
