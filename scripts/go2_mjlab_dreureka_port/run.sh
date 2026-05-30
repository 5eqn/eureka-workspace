#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-go2-mjlab}"

usage() {
  echo "Usage: $0 [preflight|source-contract|setup-env-record|import-smoke|task-config-smoke|verify-terrain-4096|render-scene|smoke-20min|report-smoke-20min|train-1-8-budget|report-train-1-8-budget|play-latest]"
}

cmd="${1:-preflight}"
case "$cmd" in
  preflight|source-contract|setup-env-record|import-smoke|task-config-smoke|verify-terrain-4096|render-scene|smoke-20min|report-smoke-20min|train-1-8-budget|report-train-1-8-budget)
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go2_mjlab_dreureka_port/runner.py" "$cmd" "${@:2}"
    ;;
  play-latest)
    conda run --no-capture-output -n "$CONDA_ENV_NAME" python "$ROOT_DIR/scripts/go2_mjlab_dreureka_port/play_driver.py" "${@:2}"
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
