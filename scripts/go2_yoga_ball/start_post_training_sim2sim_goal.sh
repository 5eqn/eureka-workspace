#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ART_DIR="$ROOT_DIR/artifacts/go2_yoga_ball/post_training_sim2sim"
LOG_DIR="$ROOT_DIR/logs/go2_yoga_ball/post_training_sim2sim"
GOAL_FILE="$ROOT_DIR/GOAL_GO2_YOGA_BALL_POST_TRAINING_SIM2SIM.md"
RESUME_LAUNCH="$ROOT_DIR/artifacts/go2_yoga_ball/train_1_8_budget_resume_launch.json"
ORIGINAL_LAUNCH="$ROOT_DIR/artifacts/go2_yoga_ball/train_1_8_budget_launch.json"
CODEX_BIN="${CODEX_BIN:-/usr/bin/codex}"
PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}"

mkdir -p "$ART_DIR" "$LOG_DIR"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')" "$*" | tee -a "$LOG_DIR/scheduler.log"
}

launch_json="$RESUME_LAUNCH"
if [[ ! -f "$launch_json" ]]; then
  launch_json="$ORIGINAL_LAUNCH"
fi

if [[ ! -f "$launch_json" ]]; then
  log "No training launch metadata found; cannot decide when to start post-training Sim2Sim."
  exit 1
fi

read -r container_id training_log requested_iterations < <(
  python3 - "$launch_json" <<'PY'
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(data.get("container_id", ""), data.get("log", ""), data.get("iterations", ""))
PY
)

if [[ -z "$container_id" ]]; then
  log "Training launch metadata has no container_id: $launch_json"
  exit 1
fi

inspect_output="$(docker inspect -f '{{.State.Running}} {{.State.Status}} {{.State.ExitCode}}' "$container_id" 2>/dev/null || true)"
if [[ -z "$inspect_output" ]]; then
  log "Training container $container_id is not inspectable. Treating as ended and starting post-training agent."
else
  read -r is_running status exit_code <<<"$inspect_output"
  if [[ "$is_running" == "true" ]]; then
    log "Training container $container_id still running; deferring post-training Sim2Sim."
    exit 0
  fi
  log "Training container $container_id ended with status=$status exit_code=$exit_code."
fi

triggered_marker="$ART_DIR/codex_goal_triggered.json"
if [[ -f "$triggered_marker" ]]; then
  log "Post-training Codex goal already triggered: $triggered_marker"
  exit 0
fi

lock_dir="$ART_DIR/codex_goal.lock"
if ! mkdir "$lock_dir" 2>/dev/null; then
  log "Another scheduler instance is already starting the post-training Codex goal."
  exit 0
fi
trap 'rmdir "$lock_dir" 2>/dev/null || true' EXIT

completion_json="$ART_DIR/training_completion.json"
python3 - "$ROOT_DIR" "$launch_json" "$training_log" "$requested_iterations" "$inspect_output" > "$completion_json" <<'PY'
import json
import re
import sys
import time
from pathlib import Path

root = Path(sys.argv[1])
launch_path = Path(sys.argv[2])
log_rel = sys.argv[3]
requested = sys.argv[4]
inspect_output = sys.argv[5] if len(sys.argv) > 5 else ""
log_path = root / log_rel if log_rel else None
latest = {}
if log_path and log_path.exists():
    text = log_path.read_text(encoding="utf-8", errors="replace")
    patterns = {
        "iterations": r"iterations\s*[^0-9-]*(-?\d+)",
        "time_iter_mean_s": r"time iter/mean\s*[^0-9.-]*([0-9.]+)",
        "time_elapsed_mean_s": r"time elapsed/mean\s*[^0-9.-]*([0-9.]+)",
        "total_reward_mean": r"rew total/mean\s*[^0-9.-]*([0-9.-]+)",
        "episode_length_mean": r"episode length/mean\s*[^0-9.-]*([0-9.]+)",
    }
    for key, pattern in patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            value = matches[-1]
            latest[key] = int(value) if key == "iterations" else float(value)
    latest["has_traceback"] = "Traceback (most recent call last)" in text
    latest["has_nan_token"] = bool(re.search(r"\bnan\b", text, flags=re.IGNORECASE))

launch = json.loads(launch_path.read_text(encoding="utf-8"))
print(json.dumps({
    "generated_at_unix": time.time(),
    "launch_metadata": str(launch_path.relative_to(root)),
    "container_id": launch.get("container_id"),
    "container_name": launch.get("container_name"),
    "docker_inspect_state": inspect_output,
    "training_log": log_rel,
    "requested_iterations": int(requested) if str(requested).isdigit() else requested,
    "latest_log_metrics": latest,
}, indent=2, sort_keys=True))
PY

prompt_file="$ART_DIR/codex_prompt.txt"
cat > "$prompt_file" <<'PROMPT'
Read AGENTS.md first. Start and execute the root-level goal in GOAL_GO2_YOGA_BALL_POST_TRAINING_SIM2SIM.md.

Context: the scheduler is starting this only after the Go2 1/8-budget training container has stopped. Do not launch another long training run. Use the final/latest Go2 checkpoint or exported JIT policy from the current training run. Sim2Sim must use the Unitree MuJoCo Go2 DDS endpoint plus scripts/go2_yoga_ball/lcm_to_dds_bridge.py, so the simulator side remains directly swappable to real Go2 and the policy/deploy side owns LCM-to-DDS conversion.

Verification requirements are in the goal file: release before motion, proof of actual release, wall-clock/sim/policy timing consistency, LCM-to-DDS runtime proof, joint-limit and base-height reports, bounded best-effort attempts, and a failure report if the policy appears wrong.
PROMPT

python3 - "$triggered_marker" "$completion_json" "$prompt_file" <<'PY'
import json
import sys
import time
from pathlib import Path

marker = Path(sys.argv[1])
completion = Path(sys.argv[2])
prompt = Path(sys.argv[3])
marker.write_text(json.dumps({
    "triggered_at_unix": time.time(),
    "training_completion": str(completion),
    "prompt": str(prompt),
    "status": "started",
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

log "Starting Codex post-training Sim2Sim goal from $GOAL_FILE"
cd "$ROOT_DIR"
set +e
"$CODEX_BIN" exec --cd "$ROOT_DIR" --sandbox danger-full-access --ask-for-approval never "$(cat "$prompt_file")" \
  > "$LOG_DIR/codex_exec.log" 2>&1
codex_status=$?
set -e

python3 - "$triggered_marker" "$codex_status" <<'PY'
import json
import sys
import time
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))
data["finished_at_unix"] = time.time()
data["codex_exit_status"] = int(sys.argv[2])
data["status"] = "finished" if int(sys.argv[2]) == 0 else "failed"
path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

exit "$codex_status"
