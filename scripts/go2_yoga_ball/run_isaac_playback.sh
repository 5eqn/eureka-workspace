#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-/home/seqn/eureka-workspace}"
RUN="${RUN:?set RUN to the host or container checkpoint run directory}"
OUT="${OUT:-/tmp/go2_isaac_playback}"
NUM_ENVS="${NUM_ENVS:-64}"
DURATION="${DURATION:-12}"
DEVICE="${DEVICE:-cuda:0}"
MAX_FAILED_VIDEOS=3

case "$RUN" in
  /workspace/*) RUN_CONT="$RUN" ;;
  "$ROOT"/*) RUN_CONT="/workspace/${RUN#"$ROOT"/}" ;;
  *) RUN_CONT="$RUN" ;;
esac

mkdir -p "$OUT"

run_playback() {
  local out_dir="$1"
  shift
  local extra_args=("$@")
  local extra_args_quoted=""
  local cmd=""
  local rc=0

  mkdir -p "$out_dir"
  if ((${#extra_args[@]})); then
    printf -v extra_args_quoted " %q" "${extra_args[@]}"
  fi
  printf -v cmd "set -o pipefail; python /workspace/scripts/go2_yoga_ball/isaacgym_playback_smoke.py --run %q --out-dir %q --num-envs %q --duration-s %q --device %q --use-saved-contract --preserve-domain-rand%s 2>&1 | tee %q" \
    "$RUN_CONT" "$out_dir" "$NUM_ENVS" "$DURATION" "$DEVICE" "$extra_args_quoted" "$out_dir/run.log"

  set +e
  docker run --rm --gpus all --network host \
    -e WANDB_MODE=disabled \
    -e PYTHONPATH=/workspace/thirdparties/DrEureka:/workspace/thirdparties/DrEureka/globe_walking:/workspace/thirdparties/DrEureka/forward_locomotion \
    -e GO2_URDF=/workspace/thirdparties/unitree_rl_gym/resources/robots/go2/urdf/go2.urdf \
    -v "$ROOT:/workspace" \
    -v "$out_dir:$out_dir" \
    -w /workspace/thirdparties/DrEureka \
    eureka-isaacgym \
    bash -lc "$cmd"
  rc=$?
  set -e

  if [[ "$rc" -eq 0 ]]; then
    return 0
  fi
  if [[ "$rc" -eq 139 && -f "$out_dir/summary.json" ]]; then
    return 0
  fi
  return "$rc"
}

PROBE_DIR="$OUT/probe"
run_playback "$PROBE_DIR"

selection_env="$OUT/auto_export_selection.env"
PROBE_SUMMARY="$PROBE_DIR/summary.json" OUT="$OUT" MAX_FAILED_VIDEOS="$MAX_FAILED_VIDEOS" python - <<'PY' > "$selection_env"
import json
import os
from pathlib import Path

probe_summary = Path(os.environ["PROBE_SUMMARY"])
out_dir = Path(os.environ["OUT"])
cap = int(os.environ["MAX_FAILED_VIDEOS"])
summary = json.loads(probe_summary.read_text())
failed = [int(env_id) for env_id in summary.get("failed_env_ids", [])]
failed_set = set(failed)
num_envs = int(summary["num_envs"])
survived = [env_id for env_id in range(num_envs) if env_id not in failed_set]
payload = {
    "probe_summary": str(probe_summary),
    "num_envs": num_envs,
    "survived_env_ids": survived,
    "failed_env_ids": failed,
    "success_env_id": survived[0] if survived else None,
    "failed_env_ids_capped": failed[:cap],
}
(out_dir / "auto_export_selection.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
success = "" if payload["success_env_id"] is None else str(payload["success_env_id"])
failed_csv = ",".join(str(env_id) for env_id in payload["failed_env_ids_capped"])
print(f'SUCCESS_ENV_ID="{success}"')
print(f'FAILED_ENV_IDS_CAPPED="{failed_csv}"')
PY
source "$selection_env"

if [[ -n "$SUCCESS_ENV_ID" ]]; then
  run_playback "$OUT" --record-video --camera-env-id "$SUCCESS_ENV_ID"
else
  cp "$PROBE_DIR/summary.json" "$OUT/summary.json"
  cp "$PROBE_DIR/report.md" "$OUT/report.md"
  cp "$PROBE_DIR/playback.csv" "$OUT/playback.csv"
  cp "$PROBE_DIR/run.log" "$OUT/run.log"
fi

if [[ -n "$FAILED_ENV_IDS_CAPPED" ]]; then
  IFS=',' read -r -a failed_env_ids <<< "$FAILED_ENV_IDS_CAPPED"
  for env_id in "${failed_env_ids[@]}"; do
    run_playback "$OUT/failed_env${env_id}_video" \
      --record-video \
      --camera-env-id "$env_id" \
      --hold-failed-env \
      --stop-on-target-reset
  done
fi

OUT="$OUT" PROBE_SUMMARY="$PROBE_DIR/summary.json" python - <<'PY'
import json
import os
from pathlib import Path

out_dir = Path(os.environ["OUT"])
probe_summary = Path(os.environ["PROBE_SUMMARY"])
selection = json.loads((out_dir / "auto_export_selection.json").read_text())
payload = {
    "probe_summary": str(probe_summary),
    "probe_ok": json.loads(probe_summary.read_text()).get("ok"),
    "success_env_id": selection["success_env_id"],
    "success_summary": str(out_dir / "summary.json") if (out_dir / "summary.json").exists() else None,
    "success_video": str(out_dir / "isaacgym_playback.mp4") if (out_dir / "isaacgym_playback.mp4").exists() else None,
    "failed_env_ids_capped": selection["failed_env_ids_capped"],
    "failed_videos": [],
}
for env_id in selection["failed_env_ids_capped"]:
    failed_dir = out_dir / f"failed_env{env_id}_video"
    payload["failed_videos"].append(
        {
            "env_id": env_id,
            "summary": str(failed_dir / "summary.json"),
            "video": str(failed_dir / "isaacgym_playback.mp4"),
        }
    )
(out_dir / "auto_export_manifest.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
print(json.dumps(payload, indent=2, sort_keys=True))
PY
