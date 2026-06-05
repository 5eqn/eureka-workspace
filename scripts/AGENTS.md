# Scripts Local Instructions

When running this workspace in Docker, mount the workspace root at `/workspace`:

```bash
-v /home/seqn/eureka-workspace:/workspace
```

Do not mount it at `/workspace/eureka-workspace`. Overlaying Docker image content under `/workspace` is expected. Current Go2 scripts and replay artifacts should use `/workspace/thirdparties/...` container paths. Some older saved checkpoint configs may still contain `/workspace/eureka-workspace/...`; fix compatibility in the runner/helper code instead of changing the Docker mount.

## Go2 Isaac Playback

Use the Go2-specific playback helper through the wrapper script:

```bash
ROOT=/home/seqn/eureka-workspace \
RUN=/home/seqn/eureka-workspace/thirdparties/DrEureka/globe_walking/runs/globe_walking/YYYY-MM-DD/train/RUN_ID \
OUT=/tmp/go2_isaac_playback \
NUM_ENVS=64 \
DURATION=12 \
/home/seqn/eureka-workspace/scripts/go2_yoga_ball/run_isaac_playback.sh
```

The wrapper runs Docker with `-v /home/seqn/eureka-workspace:/workspace`, `--network host`, `eureka-isaacgym`, `--use-saved-contract`, and `--preserve-domain-rand`.

Do not use `globe_walking/scripts/play.py` for these Go2 PD checkpoints. The generic play script forces the wrong actuator-net control path.

Report Isaac playback as `survived_envs/64` from `summary.json`, along with whether the video was written. A Docker exit status of `139` can occur during Isaac graphics teardown after artifacts are written; judge the run by `summary.json`, `playback.csv`, and the video file.

## Go2 Isaac Policy Sim2Sim

Use the three-process Sim2Sim wrapper:

```bash
ROOT=/home/seqn/eureka-workspace \
RUN=/home/seqn/eureka-workspace/thirdparties/DrEureka/globe_walking/runs/globe_walking/YYYY-MM-DD/train/RUN_ID \
LOG_DIR=/tmp/go2_sim2sim/logs \
ART_DIR=/tmp/go2_sim2sim/artifacts \
DDS_DOMAIN=191 \
DURATION=12 \
/home/seqn/eureka-workspace/scripts/go2_yoga_ball/run_sim2sim.sh
```

The wrapper runs:

- host MuJoCo DDS endpoint in conda env `go2-mjlab`
- Docker LCM-to-DDS bridge in `eureka-mujoco_sim2sim`
- Docker DrEureka policy deployer in `eureka-isaacgym`
- host replay renderer in conda env `go2-mjlab`

Keep the default LCM URL unless the task explicitly requires otherwise:

```bash
udpm://239.255.76.67:7667?ttl=255
```

Do not invent a custom LCM URL for normal Go2 Sim2Sim runs. The DrEureka deployment stack includes a module-level LCM handle using the default URL, so changing only part of the command path can result in zero or stale commands.

Useful wrapper overrides:

- `BASE_Z=1.0` sets the robot release height through `go2_mujoco_dds_endpoint.py --base-z`.
- `ROBOT_FRICTION=0.7` sets whole-robot MuJoCo geom primary friction through `--robot-friction`.
- `BALL_MASS`, `BALL_FRICTION`, and `BALL_INERTIA` pass through to the endpoint when explicitly set.
- `VIDEO_NAME=RUN_ID_sim2sim.mp4` controls the rendered output name under `$ART_DIR/videos`.

Use existing scripts and endpoint flags for experiments; do not edit policy code, gains, physics, or scene parameters unless the task explicitly asks for that change.

For Sim2Sim results, report process return codes, `cmd_count`, `release_confirmed`, `fall_detected`, simulated elapsed time, and the video directory.
