#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

usage() {
  echo "Usage: $0 [isaacgym|mujoco_sim2sim|mjlab|all]"
}

build_one() {
  local name="$1"
  docker build \
    -f "$ROOT_DIR/docker/go1_yoga_ball/${name}.Dockerfile" \
    -t "go1-yoga-ball-${name}" \
    "$ROOT_DIR"
}

cmd="${1:-all}"
case "$cmd" in
  isaacgym|mujoco_sim2sim|mjlab)
    build_one "$cmd"
    ;;
  all)
    build_one isaacgym
    build_one mujoco_sim2sim
    build_one mjlab
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
