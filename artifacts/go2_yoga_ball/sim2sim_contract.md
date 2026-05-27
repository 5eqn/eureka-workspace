# Go2 Sim2Sim Contract

Use Unitree SDK2 low-level state/command semantics as the real-robot swappable boundary.

- Policy order: FL, FR, RL, RR in DrEureka observation/action order.
- Unitree low-level motor order: FR, FL, RR, RL.
- Policy-to-Unitree index map: `[3, 4, 5, 0, 1, 2, 9, 10, 11, 6, 7, 8]`.
- MuJoCo must publish joint state, IMU state, and command timing at the deployment boundary.
- Support is allowed only before policy control is active; release must be logged and verified.
- Real-time validity requires sim time and policy time to remain consistent with wall clock.

The current Go2 contract is a design target. It is not complete until `mujoco_sim2sim_health_report.md` is generated from a Go2 MuJoCo run.
