#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

usage() {
  echo "Usage: $0 [init-artifacts|validate-deps|inspect-policy|write-contract|smoke-mujoco-assets|smoke-direct-release|play-pretrained-isaacgym|train-default-isaacgym|play-default-train-isaacgym|smoke-pretrained-mujoco-sim2sim|smoke-default-train-mujoco-sim2sim|repeat-pretrained-mujoco-sim2sim|control-removal-pretrained-mujoco-sim2sim|render-pretrained-mujoco-video|render-default-train-mujoco-video|render-mujoco-marked-videos|smoke-mjlab-runtime|smoke-mjlab-yoga-ball-task|smoke-mjlab-yoga-ball-train|play-mjlab-yoga-ball-trained|phase-mjlab-report|preflight|all]"
}

cmd="${1:-preflight}"
case "$cmd" in
  init-artifacts)
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go1_yoga_ball/runner.py" init-artifacts
    ;;
  validate-deps)
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go1_yoga_ball/runner.py" validate-deps
    ;;
  inspect-policy)
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go1_yoga_ball/runner.py" inspect-policy
    ;;
  write-contract)
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go1_yoga_ball/runner.py" write-contract
    ;;
  smoke-mujoco-assets)
    docker run --rm \
      --user "$(id -u):$(id -g)" \
      -e MUJOCO_GL=osmesa \
      -v "$ROOT_DIR:/workspace/eureka-workspace" \
      -w /workspace/eureka-workspace \
      eureka-mujoco_sim2sim \
      python3 scripts/go1_yoga_ball/runner.py smoke-mujoco-assets
    ;;
  smoke-direct-release)
    docker run --rm \
      --user "$(id -u):$(id -g)" \
      -e MUJOCO_GL=osmesa \
      -v "$ROOT_DIR:/workspace/eureka-workspace" \
      -w /workspace/eureka-workspace \
      eureka-mujoco_sim2sim \
      python3 scripts/go1_yoga_ball/runner.py smoke-direct-release
    ;;
  play-pretrained-isaacgym)
    log_dir="$ROOT_DIR/logs/go1_yoga_ball/pretrained/isaacgym_playback"
    mkdir -p "$log_dir"
    docker run --rm --gpus all \
      -e ITERATIONS="${ITERATIONS:-100}" \
      -e WANDB_MODE=offline \
      -e PYTHONPATH=/workspace/eureka-workspace/thirdparties/DrEureka:/workspace/eureka-workspace/thirdparties/DrEureka/globe_walking:/workspace/eureka-workspace/thirdparties/DrEureka/forward_locomotion \
      -v "$ROOT_DIR:/workspace/eureka-workspace" \
      -w /workspace/eureka-workspace/thirdparties/DrEureka \
      eureka-isaacgym \
      bash -lc "set -o pipefail; python globe_walking/scripts/play.py --run globe_walking/runs/globe_walking/dr_eureka_best --dr-config load --headless --iterations \"\$ITERATIONS\" --no-video 2>&1 | tee /workspace/eureka-workspace/logs/go1_yoga_ball/pretrained/isaacgym_playback/play_pretrained_isaacgym.log"
    ;;
  train-default-isaacgym)
    iterations="${ITERATIONS:-10}"
    log_dir="$ROOT_DIR/logs/go1_yoga_ball/default_train/train"
    mkdir -p "$log_dir"
    train_extra_args=()
    if [ -n "${TRAIN_NUM_ENVS:-}" ]; then
      train_extra_args+=(--num-envs "$TRAIN_NUM_ENVS")
    fi
    if [ "${TRAIN_NO_VIDEO:-0}" = "1" ]; then
      train_extra_args+=(--no-video)
    fi
    if [ -n "${TRAIN_SAVE_VIDEO_INTERVAL:-}" ]; then
      train_extra_args+=(--save-video-interval "$TRAIN_SAVE_VIDEO_INTERVAL")
    fi
    if [ -n "${TRAIN_SAVE_INTERVAL:-}" ]; then
      train_extra_args+=(--save-interval "$TRAIN_SAVE_INTERVAL")
    fi
    if [ -n "${TRAIN_NUM_STEPS_PER_ENV:-}" ]; then
      train_extra_args+=(--num-steps-per-env "$TRAIN_NUM_STEPS_PER_ENV")
    fi
    if [ -n "${TRAIN_DOMAIN_RAND_PROFILE:-}" ]; then
      train_extra_args+=(--domain-rand-profile "$TRAIN_DOMAIN_RAND_PROFILE")
    fi
    find "$ROOT_DIR/thirdparties/DrEureka/globe_walking/runs" -mindepth 1 -maxdepth 5 -type d -name checkpoints -printf '%h\n' | sort > "$log_dir/runs_before.txt"
    docker run --rm --gpus all \
      -e WANDB_MODE=disabled \
      -e PYTHONPATH=/workspace/eureka-workspace/thirdparties/DrEureka:/workspace/eureka-workspace/thirdparties/DrEureka/globe_walking:/workspace/eureka-workspace/thirdparties/DrEureka/forward_locomotion \
      -v "$ROOT_DIR:/workspace/eureka-workspace" \
      -w /workspace/eureka-workspace/thirdparties/DrEureka \
      eureka-isaacgym \
      bash -lc "set -o pipefail; git config --global --add safe.directory /workspace/eureka-workspace/thirdparties/DrEureka || true; python globe_walking/scripts/train.py --dr-config eureka --reward-config eureka --iterations '$iterations' --no-wandb --wandb-group go1_yoga_ball_default_train ${train_extra_args[*]} 2>&1 | tee /workspace/eureka-workspace/logs/go1_yoga_ball/default_train/train/train.log"
    find "$ROOT_DIR/thirdparties/DrEureka/globe_walking/runs" -mindepth 1 -maxdepth 5 -type d -name checkpoints -printf '%h\n' | sort > "$log_dir/runs_after.txt"
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go1_yoga_ball/runner.py" record-default-train-run
    ;;
  play-default-train-isaacgym)
    log_dir="$ROOT_DIR/logs/go1_yoga_ball/default_train/isaacgym_playback"
    mkdir -p "$log_dir"
    run_path="$(cat "$ROOT_DIR/artifacts/go1_yoga_ball/default_train_selected_run.txt")"
    rel_run="${run_path#"$ROOT_DIR/thirdparties/DrEureka/"}"
    docker run --rm --gpus all \
      -e ITERATIONS="${ITERATIONS:-100}" \
      -e WANDB_MODE=offline \
      -e PYTHONPATH=/workspace/eureka-workspace/thirdparties/DrEureka:/workspace/eureka-workspace/thirdparties/DrEureka/globe_walking:/workspace/eureka-workspace/thirdparties/DrEureka/forward_locomotion \
      -v "$ROOT_DIR:/workspace/eureka-workspace" \
      -w /workspace/eureka-workspace/thirdparties/DrEureka \
      eureka-isaacgym \
      bash -lc "set -o pipefail; python globe_walking/scripts/play.py --run '$rel_run' --dr-config load --headless --iterations \"\$ITERATIONS\" --no-video 2>&1 | tee /workspace/eureka-workspace/logs/go1_yoga_ball/default_train/isaacgym_playback/play_default_train_isaacgym.log"
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go1_yoga_ball/runner.py" summarize-default-train-isaacgym
    ;;
  smoke-pretrained-mujoco-sim2sim)
    duration_s="${DURATION_S:-8}"
    log_dir="$ROOT_DIR/logs/go1_yoga_ball/pretrained/mujoco_sim2sim"
    mkdir -p "$log_dir"
    rm -f "$log_dir/sequence_events.csv"
    "$0" smoke-mujoco-assets >/dev/null
    docker run --rm --network host \
      --user "$(id -u):$(id -g)" \
      -e MUJOCO_GL=osmesa \
      -e PYTHONPATH=/workspace/eureka-workspace/thirdparties/DrEureka/globe_walking:/workspace/eureka-workspace/thirdparties/DrEureka/globe_walking/go1_gym_deploy \
      -v "$ROOT_DIR:/workspace/eureka-workspace" \
      -w /workspace/eureka-workspace \
      eureka-mujoco_sim2sim \
      bash -lc "set -o pipefail; python3 scripts/go1_yoga_ball/go1_mujoco_lcm_bridge.py --scene /workspace/eureka-workspace/artifacts/go1_yoga_ball/build/go1_yoga_ball_scene.xml --duration-s '$duration_s' --out-dir /workspace/eureka-workspace/logs/go1_yoga_ball/pretrained/mujoco_sim2sim --event-log /workspace/eureka-workspace/logs/go1_yoga_ball/pretrained/mujoco_sim2sim/sequence_events.csv 2>&1 | tee /workspace/eureka-workspace/logs/go1_yoga_ball/pretrained/mujoco_sim2sim/sim_bridge.log" &
    sim_pid="$!"
    sleep 0.5
    set +e
    docker run --rm --network host \
      --user "$(id -u):$(id -g)" \
      -e HOME=/tmp \
      -e PYTHONPATH=/workspace/eureka-workspace/thirdparties/DrEureka:/workspace/eureka-workspace/thirdparties/DrEureka/globe_walking:/workspace/eureka-workspace/thirdparties/DrEureka/globe_walking/go1_gym_deploy \
      -v "$ROOT_DIR:/workspace/eureka-workspace" \
      -w /workspace/eureka-workspace \
      eureka-isaacgym \
      bash -lc "set -o pipefail; python scripts/go1_yoga_ball/deploy_lcm_policy.py --run /workspace/eureka-workspace/thirdparties/DrEureka/globe_walking/runs/globe_walking/dr_eureka_best --duration-s '$duration_s' --out-dir /workspace/eureka-workspace/logs/go1_yoga_ball/pretrained/mujoco_sim2sim --event-log /workspace/eureka-workspace/logs/go1_yoga_ball/pretrained/mujoco_sim2sim/sequence_events.csv 2>&1 | tee /workspace/eureka-workspace/logs/go1_yoga_ball/pretrained/mujoco_sim2sim/policy.log"
    policy_status="$?"
    wait "$sim_pid"
    sim_status="$?"
    set -e
    if [ "$policy_status" -ne 0 ] || [ "$sim_status" -ne 0 ]; then
      echo "Sim2Sim smoke failed: policy_status=$policy_status sim_status=$sim_status" >&2
      exit 1
    fi
    ;;
  smoke-default-train-mujoco-sim2sim)
    duration_s="${DURATION_S:-8}"
    run_path="$(cat "$ROOT_DIR/artifacts/go1_yoga_ball/default_train_selected_run.txt")"
    container_run_path="/workspace/eureka-workspace/${run_path#"$ROOT_DIR/"}"
    log_dir="$ROOT_DIR/logs/go1_yoga_ball/default_train/mujoco_sim2sim"
    mkdir -p "$log_dir"
    rm -f "$log_dir/sequence_events.csv"
    "$0" smoke-mujoco-assets >/dev/null
    docker run --rm --network host \
      --user "$(id -u):$(id -g)" \
      -e MUJOCO_GL=osmesa \
      -e PYTHONPATH=/workspace/eureka-workspace/thirdparties/DrEureka/globe_walking:/workspace/eureka-workspace/thirdparties/DrEureka/globe_walking/go1_gym_deploy \
      -v "$ROOT_DIR:/workspace/eureka-workspace" \
      -w /workspace/eureka-workspace \
      eureka-mujoco_sim2sim \
      bash -lc "set -o pipefail; python3 scripts/go1_yoga_ball/go1_mujoco_lcm_bridge.py --scene /workspace/eureka-workspace/artifacts/go1_yoga_ball/build/go1_yoga_ball_scene.xml --run '$container_run_path' --duration-s '$duration_s' --out-dir /workspace/eureka-workspace/logs/go1_yoga_ball/default_train/mujoco_sim2sim --event-log /workspace/eureka-workspace/logs/go1_yoga_ball/default_train/mujoco_sim2sim/sequence_events.csv 2>&1 | tee /workspace/eureka-workspace/logs/go1_yoga_ball/default_train/mujoco_sim2sim/sim_bridge.log" &
    sim_pid="$!"
    sleep 0.5
    set +e
    docker run --rm --network host \
      --user "$(id -u):$(id -g)" \
      -e HOME=/tmp \
      -e PYTHONPATH=/workspace/eureka-workspace/thirdparties/DrEureka:/workspace/eureka-workspace/thirdparties/DrEureka/globe_walking:/workspace/eureka-workspace/thirdparties/DrEureka/globe_walking/go1_gym_deploy \
      -v "$ROOT_DIR:/workspace/eureka-workspace" \
      -w /workspace/eureka-workspace \
      eureka-isaacgym \
      bash -lc "set -o pipefail; python scripts/go1_yoga_ball/deploy_lcm_policy.py --run '$container_run_path' --duration-s '$duration_s' --out-dir /workspace/eureka-workspace/logs/go1_yoga_ball/default_train/mujoco_sim2sim --event-log /workspace/eureka-workspace/logs/go1_yoga_ball/default_train/mujoco_sim2sim/sequence_events.csv 2>&1 | tee /workspace/eureka-workspace/logs/go1_yoga_ball/default_train/mujoco_sim2sim/policy.log"
    policy_status="$?"
    wait "$sim_pid"
    sim_status="$?"
    set -e
    if [ "$policy_status" -ne 0 ] || [ "$sim_status" -ne 0 ]; then
      echo "Default-train Sim2Sim smoke failed: policy_status=$policy_status sim_status=$sim_status" >&2
      exit 1
    fi
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go1_yoga_ball/runner.py" summarize-default-train-mujoco-sim2sim
    ;;
  repeat-pretrained-mujoco-sim2sim)
    repeats="${REPEATS:-3}"
    duration_s="${DURATION_S:-22}"
    for run_id in $(seq 1 "$repeats"); do
      DURATION_S="$duration_s" "$0" smoke-pretrained-mujoco-sim2sim
      "$PYTHON_BIN" "$ROOT_DIR/scripts/go1_yoga_ball/runner.py" summarize-pretrained-mujoco-sim2sim
      repeat_log_dir="$ROOT_DIR/logs/go1_yoga_ball/pretrained/mujoco_sim2sim_repeats/run_${run_id}"
      mkdir -p "$repeat_log_dir"
      cp "$ROOT_DIR"/logs/go1_yoga_ball/pretrained/mujoco_sim2sim/* "$repeat_log_dir"/
      cp "$ROOT_DIR/artifacts/go1_yoga_ball/pretrained_mujoco_sim2sim_smoke.json" \
        "$ROOT_DIR/artifacts/go1_yoga_ball/pretrained_mujoco_sim2sim_repeat_run_${run_id}.json"
    done
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go1_yoga_ball/runner.py" aggregate-pretrained-mujoco-repeats
    ;;
  control-removal-pretrained-mujoco-sim2sim)
    duration_s="${DURATION_S:-12}"
    remove_after_s="${REMOVE_AFTER_RELEASE_S:-5}"
    log_dir="$ROOT_DIR/logs/go1_yoga_ball/pretrained/mujoco_sim2sim_control_removal"
    mkdir -p "$log_dir"
    rm -f "$log_dir/sequence_events.csv"
    "$0" smoke-mujoco-assets >/dev/null
    docker run --rm --network host \
      --user "$(id -u):$(id -g)" \
      -e MUJOCO_GL=osmesa \
      -e PYTHONPATH=/workspace/eureka-workspace/thirdparties/DrEureka/globe_walking:/workspace/eureka-workspace/thirdparties/DrEureka/globe_walking/go1_gym_deploy \
      -v "$ROOT_DIR:/workspace/eureka-workspace" \
      -w /workspace/eureka-workspace \
      eureka-mujoco_sim2sim \
      bash -lc "set -o pipefail; python3 scripts/go1_yoga_ball/go1_mujoco_lcm_bridge.py --scene /workspace/eureka-workspace/artifacts/go1_yoga_ball/build/go1_yoga_ball_scene.xml --duration-s '$duration_s' --remove-control-after-release-s '$remove_after_s' --out-dir /workspace/eureka-workspace/logs/go1_yoga_ball/pretrained/mujoco_sim2sim_control_removal --event-log /workspace/eureka-workspace/logs/go1_yoga_ball/pretrained/mujoco_sim2sim_control_removal/sequence_events.csv 2>&1 | tee /workspace/eureka-workspace/logs/go1_yoga_ball/pretrained/mujoco_sim2sim_control_removal/sim_bridge.log" &
    sim_pid="$!"
    sleep 0.5
    set +e
    docker run --rm --network host \
      --user "$(id -u):$(id -g)" \
      -e HOME=/tmp \
      -e PYTHONPATH=/workspace/eureka-workspace/thirdparties/DrEureka:/workspace/eureka-workspace/thirdparties/DrEureka/globe_walking:/workspace/eureka-workspace/thirdparties/DrEureka/globe_walking/go1_gym_deploy \
      -v "$ROOT_DIR:/workspace/eureka-workspace" \
      -w /workspace/eureka-workspace \
      eureka-isaacgym \
      bash -lc "set -o pipefail; python scripts/go1_yoga_ball/deploy_lcm_policy.py --run /workspace/eureka-workspace/thirdparties/DrEureka/globe_walking/runs/globe_walking/dr_eureka_best --duration-s '$duration_s' --out-dir /workspace/eureka-workspace/logs/go1_yoga_ball/pretrained/mujoco_sim2sim_control_removal --event-log /workspace/eureka-workspace/logs/go1_yoga_ball/pretrained/mujoco_sim2sim_control_removal/sequence_events.csv 2>&1 | tee /workspace/eureka-workspace/logs/go1_yoga_ball/pretrained/mujoco_sim2sim_control_removal/policy.log"
    policy_status="$?"
    wait "$sim_pid"
    sim_status="$?"
    set -e
    if [ "$policy_status" -ne 0 ] || [ "$sim_status" -ne 0 ]; then
      echo "Control-removal Sim2Sim failed: policy_status=$policy_status sim_status=$sim_status" >&2
      exit 1
    fi
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go1_yoga_ball/runner.py" summarize-control-removal-pretrained-mujoco-sim2sim
    ;;
  render-pretrained-mujoco-video)
    docker run --rm \
      --user "$(id -u):$(id -g)" \
      -e MUJOCO_GL=osmesa \
      -v "$ROOT_DIR:/workspace/eureka-workspace" \
      -w /workspace/eureka-workspace \
      eureka-mujoco_sim2sim \
      python3 scripts/go1_yoga_ball/runner.py render-pretrained-mujoco-video
    ;;
  render-default-train-mujoco-video)
    docker run --rm \
      --user "$(id -u):$(id -g)" \
      -e MUJOCO_GL=osmesa \
      -v "$ROOT_DIR:/workspace/eureka-workspace" \
      -w /workspace/eureka-workspace \
      eureka-mujoco_sim2sim \
      python3 scripts/go1_yoga_ball/runner.py render-default-train-mujoco-video
    ;;
  render-mujoco-marked-videos)
    docker run --rm \
      --user "$(id -u):$(id -g)" \
      -e MUJOCO_GL=osmesa \
      -v "$ROOT_DIR:/workspace/eureka-workspace" \
      -w /workspace/eureka-workspace \
      eureka-mujoco_sim2sim \
      python3 scripts/go1_yoga_ball/runner.py render-mujoco-marked-videos
    ;;
  smoke-mjlab-runtime)
    log_dir="$ROOT_DIR/logs/go1_yoga_ball/mjlab_train/default_playback"
    mkdir -p "$log_dir"
    docker run --rm --gpus all \
      --user "$(id -u):$(id -g)" \
      -e HOME=/tmp \
      -e MUJOCO_GL=egl \
      -v "$ROOT_DIR:/workspace/eureka-workspace" \
      -w /workspace/eureka-workspace \
      eureka-mjlab \
      /workspace/thirdparties/MJLab/.venv/bin/python scripts/go1_yoga_ball/runner.py smoke-mjlab-runtime
    ;;
  smoke-mjlab-yoga-ball-task)
    log_dir="$ROOT_DIR/logs/go1_yoga_ball/mjlab_train/default_playback"
    mkdir -p "$log_dir"
    docker run --rm --gpus all \
      --user "$(id -u):$(id -g)" \
      -e HOME=/tmp \
      -e MUJOCO_GL=egl \
      -v "$ROOT_DIR:/workspace/eureka-workspace" \
      -w /workspace/eureka-workspace \
      eureka-mjlab \
      /workspace/thirdparties/MJLab/.venv/bin/python scripts/go1_yoga_ball/runner.py smoke-mjlab-yoga-ball-task
    ;;
  smoke-mjlab-yoga-ball-train)
    log_dir="$ROOT_DIR/logs/go1_yoga_ball/mjlab_train/train"
    mkdir -p "$log_dir"
    docker run --rm --gpus all \
      --user "$(id -u):$(id -g)" \
      -e HOME=/tmp \
      -e MUJOCO_GL=egl \
      -e WANDB_MODE=disabled \
      -v "$ROOT_DIR:/workspace/eureka-workspace" \
      -w /workspace/eureka-workspace \
      eureka-mjlab \
      /workspace/thirdparties/MJLab/.venv/bin/python scripts/go1_yoga_ball/runner.py smoke-mjlab-yoga-ball-train
    ;;
  play-mjlab-yoga-ball-trained)
    log_dir="$ROOT_DIR/logs/go1_yoga_ball/mjlab_train/default_playback"
    mkdir -p "$log_dir"
    docker run --rm --gpus all \
      --user "$(id -u):$(id -g)" \
      -e HOME=/tmp \
      -e MUJOCO_GL=egl \
      -e WANDB_MODE=disabled \
      -v "$ROOT_DIR:/workspace/eureka-workspace" \
      -w /workspace/eureka-workspace \
      eureka-mjlab \
      /workspace/thirdparties/MJLab/.venv/bin/python scripts/go1_yoga_ball/runner.py play-mjlab-yoga-ball-trained
    ;;
  phase-mjlab-report)
    "$PYTHON_BIN" "$ROOT_DIR/scripts/go1_yoga_ball/runner.py" phase-mjlab-report
    ;;
  preflight|all)
    "$0" init-artifacts
    "$0" validate-deps
    "$0" inspect-policy
    "$0" write-contract
    "$0" smoke-mujoco-assets
    "$0" smoke-direct-release
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
