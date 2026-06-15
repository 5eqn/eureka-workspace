#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-/home/seqn/eureka-workspace}"
RUN="${RUN:?set RUN to the host or container checkpoint run directory}"
LOG_DIR="${LOG_DIR:?set LOG_DIR for Sim2Sim logs}"
ART_DIR="${ART_DIR:?set ART_DIR for Sim2Sim artifacts}"
DDS_DOMAIN="${DDS_DOMAIN:-191}"
DURATION="${DURATION:-12}"
LCM_URL="${LCM_URL:-udpm://239.255.76.67:7667?ttl=255}"
NETWORK_INTERFACE="${NETWORK_INTERFACE:-lo}"
BASE_Z="${BASE_Z:-0.95}"
BALL_RADIUS="${BALL_RADIUS:-0.45}"
DT="${DT:-0.002}"
RELEASE_AFTER_COMMAND_S="${RELEASE_AFTER_COMMAND_S:-0.0}"
VIDEO_NAME="${VIDEO_NAME:-sim2sim.mp4}"
# The render step runs on the host `go2-mjlab` conda env (not inside Docker), so it
# needs an explicit headless GL backend. EGL works on this NVIDIA host; override with
# MUJOCO_GL=osmesa if no EGL device is available.
MUJOCO_GL="${MUJOCO_GL:-egl}"

case "$RUN" in
  /workspace/*)
    RUN_CONT="$RUN"
    RUN_HOST="$ROOT/${RUN#"/workspace/"}"
    ;;
  "$ROOT"/*)
    RUN_HOST="$RUN"
    RUN_CONT="/workspace/${RUN#"$ROOT"/}"
    ;;
  *)
    RUN_HOST="$RUN"
    RUN_CONT="$RUN"
    ;;
esac

mkdir -p "$LOG_DIR" "$ART_DIR/videos"
: > "$LOG_DIR/events.csv"
chmod 666 "$LOG_DIR/events.csv"

endpoint_args=(
  --run "$RUN_HOST"
  --duration-s "$DURATION"
  --out-dir "$LOG_DIR"
  --event-log "$LOG_DIR/events.csv"
  --dds-domain "$DDS_DOMAIN"
  --network-interface "$NETWORK_INTERFACE"
  --dt "$DT"
  --release-after-command-s "$RELEASE_AFTER_COMMAND_S"
  --base-z "$BASE_Z"
  --ball-radius "$BALL_RADIUS"
)

if [[ -n "${ROBOT_FRICTION:-}" ]]; then
  endpoint_args+=(--robot-friction "$ROBOT_FRICTION")
fi
if [[ -n "${BALL_MASS:-}" ]]; then
  endpoint_args+=(--ball-mass "$BALL_MASS")
fi
if [[ -n "${BALL_FRICTION:-}" ]]; then
  endpoint_args+=(--ball-friction "$BALL_FRICTION")
fi
if [[ -n "${BALL_INERTIA:-}" ]]; then
  endpoint_args+=(--ball-inertia "$BALL_INERTIA")
fi
if [[ -n "${BALL_DRAG:-}" ]]; then
  endpoint_args+=(--ball-drag "$BALL_DRAG")
fi
if [[ -n "${FALL_BASE_Z:-}" ]]; then
  endpoint_args+=(--fall-base-z "$FALL_BASE_Z")
fi

set +e
conda run --no-capture-output -n go2-mjlab \
  python "$ROOT/scripts/go2_yoga_ball/go2_mujoco_dds_endpoint.py" \
  "${endpoint_args[@]}" > "$LOG_DIR/endpoint.log" 2>&1 &
endpoint_pid=$!

sleep 2

docker run --rm --network host \
  -e PYTHONPATH=/workspace/thirdparties/DrEureka/globe_walking:/workspace/thirdparties/DrEureka \
  -v "$ROOT:/workspace" \
  -v "$(dirname "$LOG_DIR"):$(dirname "$LOG_DIR")" \
  -w /workspace \
  eureka-mujoco_sim2sim \
  bash -lc "python3 /workspace/scripts/go2_yoga_ball/lcm_to_dds_bridge.py \
    --lcm-url '$LCM_URL' \
    --dds-domain '$DDS_DOMAIN' \
    --network-interface '$NETWORK_INTERFACE' \
    --duration-s '$DURATION' \
    --out-dir '$LOG_DIR' \
    --event-log '$LOG_DIR/events.csv'" > "$LOG_DIR/bridge.log" 2>&1 &
bridge_pid=$!

sleep 2

docker run --rm --gpus all --network host \
  -e PYTHONPATH=/workspace/thirdparties/DrEureka/globe_walking:/workspace/thirdparties/DrEureka:/workspace/thirdparties/DrEureka/forward_locomotion \
  -v "$ROOT:/workspace" \
  -v "$(dirname "$LOG_DIR"):$(dirname "$LOG_DIR")" \
  -w /workspace/thirdparties/DrEureka \
  eureka-isaacgym \
  bash -lc "python /workspace/scripts/go1_yoga_ball/deploy_lcm_policy.py \
    --run '$RUN_CONT' \
    --duration-s '$DURATION' \
    --out-dir '$LOG_DIR' \
    --event-log '$LOG_DIR/events.csv' \
    --lcm-url '$LCM_URL'" > "$LOG_DIR/policy.log" 2>&1 &
policy_pid=$!

wait "$policy_pid"; policy_rc=$?
wait "$bridge_pid"; bridge_rc=$?
wait "$endpoint_pid"; endpoint_rc=$?

MUJOCO_GL="$MUJOCO_GL" conda run --no-capture-output -n go2-mjlab \
  python "$ROOT/scripts/go2_yoga_ball/render_mujoco_replay_video.py" \
  --replay "$LOG_DIR/replay.csv" \
  --events "$LOG_DIR/events.csv" \
  --output "$ART_DIR/videos/$VIDEO_NAME" \
  --artifact "$ART_DIR/${VIDEO_NAME%.mp4}_video.json" > "$LOG_DIR/render.log" 2>&1
render_rc=$?

ROBOT_FRICTION_VALUE="${ROBOT_FRICTION:-}" BALL_DRAG_VALUE="${BALL_DRAG:-}" python - <<PY
import json
import os
from pathlib import Path

log_dir = Path("$LOG_DIR")
art_dir = Path("$ART_DIR")
robot_friction_env = os.environ.get("ROBOT_FRICTION_VALUE", "")
ball_drag_env = os.environ.get("BALL_DRAG_VALUE", "")
status = {
    "endpoint_returncode": $endpoint_rc,
    "bridge_returncode": $bridge_rc,
    "policy_returncode": $policy_rc,
    "render_returncode": $render_rc,
    "docker_mount_contract": "$ROOT:/workspace",
    "run": "$RUN_HOST",
    "run_container": "$RUN_CONT",
    "dds_domain": int("$DDS_DOMAIN"),
    "lcm_url": "$LCM_URL",
    "base_z": float("$BASE_Z"),
    "robot_friction": float(robot_friction_env) if robot_friction_env else None,
    "ball_drag": float(ball_drag_env) if ball_drag_env else None,
}
summary_path = log_dir / "summary.json"
video_path = art_dir / "videos" / "$VIDEO_NAME"
video_artifact_path = art_dir / "${VIDEO_NAME%.mp4}_video.json"
summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}
video_artifact = json.loads(video_artifact_path.read_text()) if video_artifact_path.exists() else {}
(log_dir / "process_status.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\\n")
item = {
    "status": status,
    "summary": summary,
    "video": str(video_path),
    "video_artifact": str(video_artifact_path),
    "video_ok": video_artifact.get("ok"),
    "video_size_bytes": video_path.stat().st_size if video_path.exists() else None,
}
(log_dir / "item_manifest.json").write_text(json.dumps(item, indent=2, sort_keys=True) + "\\n")
print(json.dumps({
    "process_status": status,
    "sim2sim": {k: summary.get(k) for k in ["ok", "fall_detected", "release_confirmed", "cmd_count", "sim_elapsed_s", "wall_elapsed_s"]},
    "video": str(video_path),
    "video_ok": video_artifact.get("ok"),
}, indent=2, sort_keys=True))
PY

if [[ "$endpoint_rc" -ne 0 || "$bridge_rc" -ne 0 || "$policy_rc" -ne 0 || "$render_rc" -ne 0 ]]; then
  exit 1
fi
