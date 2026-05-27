# Go2 Train Smoke Report

- Status: PASS
- Scope: smoke validation only; this does not claim final policy equivalence.
- Sanitized Isaac Gym URDF: `artifacts/go2_yoga_ball/build/go2_description_isaacgym.urdf`
- Train log: `logs/go2_yoga_ball/train_smoke/train.log`
- Selected run: `thirdparties/DrEureka/globe_walking/runs/globe_walking/2026-05-27/train/034503.132326`
- Last logged iteration: `0`
- Last logged timesteps: `1536`
- Last total reward: `0.0`
- Contains NaN text: `False`

Go2 uses the SDK2 `LowCmd` PD command path because no defensible Go2 actuator network exists in the fetched resources. The actuator fidelity gate is the Unitree MuJoCo torque equation, gains, and torque limits, not an inferred actuator-net substitute.
