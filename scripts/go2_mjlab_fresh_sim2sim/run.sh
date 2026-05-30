#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-go2-mjlab}"
CONDA_PREFIX_DEFAULT="$HOME/miniconda3/envs/$CONDA_ENV_NAME"
export CYCLONEDDS_HOME="${CYCLONEDDS_HOME:-$CONDA_PREFIX_DEFAULT}"
export CMAKE_PREFIX_PATH="${CMAKE_PREFIX_PATH:-$CONDA_PREFIX_DEFAULT}"
export LD_LIBRARY_PATH="$CONDA_PREFIX_DEFAULT/lib:${LD_LIBRARY_PATH:-}"

usage() {
  echo "Usage: $0 [preflight|joint-order-contract|deployer-smoke|mjlab-playback|attempt|report]"
}

cmd="${1:-preflight}"
case "$cmd" in
  preflight|joint-order-contract|deployer-smoke|mjlab-playback|attempt|report)
    conda run --no-capture-output -n "$CONDA_ENV_NAME" python "$ROOT_DIR/scripts/go2_mjlab_fresh_sim2sim/runner.py" "$cmd" "${@:2}"
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
