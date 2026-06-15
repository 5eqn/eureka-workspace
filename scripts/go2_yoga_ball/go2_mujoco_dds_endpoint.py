#!/usr/bin/env python3
"""Headless Unitree-Go2 DDS MuJoCo endpoint for yoga-ball Sim2Sim."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import pickle
import sys
import time
from typing import Any

import mujoco
import numpy as np
from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelPublisher, ChannelSubscriber
from unitree_sdk2py.idl.default import unitree_go_msg_dds__LowState_
from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowCmd_, LowState_


ROOT = Path(__file__).resolve().parents[2]
UNITREE_MUJOCO_GO2 = ROOT / "thirdparties" / "unitree_mujoco" / "unitree_robots" / "go2" / "go2.xml"
BALL_URDF = ROOT / "thirdparties" / "DrEureka" / "globe_walking" / "resources" / "objects" / "ball.urdf"
BUILD_ROOT = ROOT / "artifacts" / "go2_yoga_ball" / "build"

UNITREE_MOTOR_ORDER = [
    "FR_hip_joint",
    "FR_thigh_joint",
    "FR_calf_joint",
    "FL_hip_joint",
    "FL_thigh_joint",
    "FL_calf_joint",
    "RR_hip_joint",
    "RR_thigh_joint",
    "RR_calf_joint",
    "RL_hip_joint",
    "RL_thigh_joint",
    "RL_calf_joint",
]
POLICY_JOINT_ORDER = [
    "FL_hip_joint",
    "FL_thigh_joint",
    "FL_calf_joint",
    "FR_hip_joint",
    "FR_thigh_joint",
    "FR_calf_joint",
    "RL_hip_joint",
    "RL_thigh_joint",
    "RL_calf_joint",
    "RR_hip_joint",
    "RR_thigh_joint",
    "RR_calf_joint",
]
EVENT_FIELDS = ["event", "monotonic_s", "wall_time_s", "sim_time_s", "support_active", "detail"]


class Command:
    def __init__(self) -> None:
        self.msg: LowCmd_ | None = None
        self.count = 0
        self.last_monotonic: float | None = None
        self.first_monotonic: float | None = None

    def callback(self, msg: LowCmd_) -> None:
        self.msg = msg
        self.count += 1
        self.last_monotonic = time.monotonic()
        if self.first_monotonic is None:
            self.first_monotonic = self.last_monotonic


def append_event(path: Path, event: str, start_mono: float, *, sim_time: float, support: bool, detail: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EVENT_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(
            {
                "event": event,
                "monotonic_s": f"{time.monotonic() - start_mono:.6f}",
                "wall_time_s": f"{time.time():.6f}",
                "sim_time_s": f"{sim_time:.6f}",
                "support_active": int(support),
                "detail": detail,
            }
        )


def quat_to_rpy(q: Any) -> tuple[float, float, float]:
    w, x, y, z = [float(v) for v in q]
    roll = math.atan2(2.0 * (w * x + y * z), 1.0 - 2.0 * (x * x + y * y))
    sinp = 2.0 * (w * y - z * x)
    pitch = math.asin(max(-1.0, min(1.0, sinp)))
    yaw = math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))
    return roll, pitch, yaw


def write_scene(
    ball_radius: float,
    ball_mass: float = 1.0,
    ball_inertia: float = 0.108,
    ball_friction: tuple[float, float, float] = (1.0, 0.02, 0.001),
    floor_z: float = 0.0,
) -> Path:
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    sanitized_go2 = BUILD_ROOT / "go2_unitree_sanitized.xml"
    go2_text = UNITREE_MUJOCO_GO2.read_text(encoding="utf-8")
    meshdir = UNITREE_MUJOCO_GO2.parent / "assets"
    go2_text = go2_text.replace('meshdir="assets"', f'meshdir="{meshdir}"')
    sanitized_go2.write_text(go2_text, encoding="utf-8")
    scene = BUILD_ROOT / "go2_yoga_ball_scene.xml"
    scene.write_text(
        f"""<mujoco model="go2 yoga ball scene">
  <include file="{sanitized_go2}"/>
  <statistic center="0 0 0.5" extent="1.2"/>
  <visual>
    <headlight diffuse="0.6 0.6 0.6" ambient="0.3 0.3 0.3" specular="0 0 0"/>
    <global azimuth="-130" elevation="-20"/>
  </visual>
  <asset>
    <material name="ballmat" rgba="0.05 0.35 0.75 1"/>
  </asset>
  <worldbody>
    <light pos="0 0 3" dir="0 0 -1" directional="true"/>
    <geom name="floor" type="plane" pos="0 0 {floor_z:.9f}" size="0 0 0.05"/>
    <body name="yoga_ball" pos="0 0 {ball_radius}">
      <freejoint name="yoga_ball_free"/>
      <inertial pos="0 0 0" mass="{ball_mass:.9f}" diaginertia="{ball_inertia:.9f} {ball_inertia:.9f} {ball_inertia:.9f}"/>
      <geom name="yoga_ball_geom" type="sphere" size="{ball_radius}" material="ballmat" friction="{ball_friction[0]:.9f} {ball_friction[1]:.9f} {ball_friction[2]:.9f}" condim="3"/>
    </body>
  </worldbody>
</mujoco>
""",
        encoding="utf-8",
    )
    return scene


def parse_vec(text: str, n: int) -> list[float]:
    values = [float(x) for x in text.split(",")]
    if len(values) != n:
        raise ValueError(f"expected {n} comma-separated values, got {len(values)}: {text}")
    return values


def load_seed_state(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    with Path(path).open(encoding="utf-8") as f:
        return json.load(f)


def joint_addresses(model: Any) -> tuple[list[int], list[int], list[int], list[tuple[float, float]]]:
    qpos, qvel, actuators, limits = [], [], [], []
    for joint_name in UNITREE_MOTOR_ORDER:
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
        aid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, joint_name.removesuffix("_joint"))
        if jid < 0 or aid < 0:
            raise RuntimeError(f"missing Go2 joint/actuator: {joint_name}")
        qpos.append(int(model.jnt_qposadr[jid]))
        qvel.append(int(model.jnt_dofadr[jid]))
        actuators.append(int(aid))
        limits.append((float(model.jnt_range[jid, 0]), float(model.jnt_range[jid, 1])))
    return qpos, qvel, actuators, limits


def default_angles(run_dir: Path) -> dict[str, float]:
    with (run_dir / "parameters.pkl").open("rb") as f:
        cfg = pickle.load(f)["Cfg"]
    return {name: float(cfg["init_state"]["default_joint_angles"][name]) for name in POLICY_JOINT_ORDER}


def set_initial_state(
    model: Any,
    data: Any,
    qpos_addr: list[int],
    *,
    run_dir: Path,
    base_pos: list[float],
    base_quat: list[float],
    base_lin_vel: list[float],
    base_ang_vel: list[float],
    ball_pos: list[float],
    ball_quat: list[float],
) -> None:
    angles = default_angles(run_dir)
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    data.qpos[0:3] = base_pos
    data.qpos[3:7] = base_quat
    data.qvel[0:3] = base_lin_vel
    data.qvel[3:6] = base_ang_vel
    for i, name in enumerate(UNITREE_MOTOR_ORDER):
        data.qpos[qpos_addr[i]] = angles[name]
    ball_jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "yoga_ball_free")
    if ball_jid >= 0:
        ball_qpos = int(model.jnt_qposadr[ball_jid])
        data.qpos[ball_qpos : ball_qpos + 7] = ball_pos + ball_quat
    mujoco.mj_forward(model, data)


def apply_scene_overrides(model: Any, *, robot_friction: float | None, base_mass: float | None, base_ipos: list[float] | None) -> None:
    ball_body = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "yoga_ball")
    base_body = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "base_link")
    if robot_friction is not None:
        for geom_id in range(model.ngeom):
            body_id = int(model.geom_bodyid[geom_id])
            if body_id not in (0, ball_body):
                model.geom_friction[geom_id, 0] = robot_friction
    if base_mass is not None and base_body >= 0:
        model.body_mass[base_body] = base_mass
    if base_ipos is not None and base_body >= 0:
        model.body_ipos[base_body, :] = base_ipos


def pin_supported_pose(data: Any, support_qpos: np.ndarray, support_qvel: np.ndarray, ball_qpos: int, ball_qvel: int, support_ball_qpos: np.ndarray, support_ball_qvel: np.ndarray) -> None:
    data.qpos[:7] = support_qpos
    data.qvel[:6] = support_qvel
    if ball_qpos >= 0 and ball_qvel >= 0:
        data.qpos[ball_qpos : ball_qpos + 7] = support_ball_qpos
        data.qvel[ball_qvel : ball_qvel + 6] = support_ball_qvel


def compute_command_torques(command: LowCmd_ | None, q: list[float], dq: list[float]) -> list[float] | None:
    if command is None:
        return None
    torques = []
    for i in range(12):
        motor = command.motor_cmd[i]
        torques.append(float(motor.tau) + float(motor.kp) * (float(motor.q) - q[i]) + float(motor.kd) * (float(motor.dq) - dq[i]))
    return torques


def apply_command(data: Any, command: LowCmd_ | None, qpos_addr: list[int], qvel_addr: list[int], actuator_ids: list[int], motor_strength: float) -> tuple[bool, list[float]]:
    data.ctrl[:] = 0.0
    q = [float(data.qpos[i]) for i in qpos_addr]
    dq = [float(data.qvel[i]) for i in qvel_addr]
    raw_torques = compute_command_torques(command, q, dq)
    if command is None:
        return False, [0.0] * 12
    raw_torques = [motor_strength * value for value in raw_torques]
    for i in range(12):
        data.ctrl[actuator_ids[i]] = raw_torques[i]
    return True, raw_torques


def publish_lowstate(pub: ChannelPublisher, low_state: LowState_, data: Any, qpos_addr: list[int], qvel_addr: list[int], actuator_ids: list[int]) -> None:
    for i in range(12):
        low_state.motor_state[i].q = float(data.qpos[qpos_addr[i]])
        low_state.motor_state[i].dq = float(data.qvel[qvel_addr[i]])
        low_state.motor_state[i].tau_est = float(data.actuator_force[actuator_ids[i]])
    quat = [float(v) for v in data.qpos[3:7]]
    roll, pitch, yaw = quat_to_rpy(quat)
    for i, value in enumerate(quat):
        low_state.imu_state.quaternion[i] = value
    try:
        low_state.imu_state.rpy[0] = roll
        low_state.imu_state.rpy[1] = pitch
        low_state.imu_state.rpy[2] = yaw
    except AttributeError:
        pass
    for i in range(3):
        low_state.imu_state.gyroscope[i] = float(data.qvel[3 + i])
        low_state.imu_state.accelerometer[i] = 0.0
    for i in range(4):
        low_state.foot_force[i] = 300
        low_state.foot_force_est[i] = 300
    pub.Write(low_state)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--duration-s", type=float, default=22.0)
    parser.add_argument("--release-after-command-s", type=float, default=0.25)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--event-log", required=True)
    parser.add_argument("--dds-domain", type=int, default=1)
    parser.add_argument("--network-interface", default="lo")
    parser.add_argument("--dt", type=float, default=0.002)
    parser.add_argument("--log-hz", type=float, default=50.0)
    parser.add_argument("--ball-radius", type=float, default=0.45)
    parser.add_argument("--ball-mass", type=float, default=None)
    parser.add_argument("--ball-inertia", type=float, default=None)
    parser.add_argument("--ball-friction", default=None)
    parser.add_argument("--ball-drag", type=float, default=None)
    parser.add_argument("--floor-z", type=float, default=0.0)
    parser.add_argument("--base-z", type=float, default=0.95)
    parser.add_argument("--base-pos", default=None)
    parser.add_argument("--base-quat", default=None)
    parser.add_argument("--base-lin-vel", default=None)
    parser.add_argument("--base-ang-vel", default=None)
    parser.add_argument("--ball-pos", default=None)
    parser.add_argument("--ball-quat", default=None)
    parser.add_argument("--robot-friction", type=float, default=None)
    parser.add_argument("--robot-base-mass", type=float, default=None)
    parser.add_argument("--robot-base-ipos", default=None)
    parser.add_argument("--motor-strength", type=float, default=1.0)
    parser.add_argument("--seed-state", default=None)
    parser.add_argument("--fall-base-z", type=float, default=0.75)
    parser.add_argument("--cmd-timeout-s", type=float, default=0.1)
    parser.add_argument("--disable-motor-limits", action="store_true")
    parser.add_argument("--torque-limit-scale", type=float, default=1.0)
    parser.add_argument("--zero-passive-joint-forces", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    event_log = Path(args.event_log)
    seed_state = load_seed_state(args.seed_state)
    ball_radius = float(seed_state.get("ball_radius", args.ball_radius))
    ball_mass = float(seed_state.get("ball_mass", args.ball_mass if args.ball_mass is not None else 1.0))
    ball_inertia = float(seed_state.get("ball_inertia", args.ball_inertia if args.ball_inertia is not None else 0.108))
    ball_friction_value = seed_state.get("ball_friction", args.ball_friction)
    ball_drag = float(seed_state.get("ball_drag", args.ball_drag if args.ball_drag is not None else 0.0))
    ball_friction = (float(ball_friction_value), 0.02, 0.001) if ball_friction_value is not None else (1.0, 0.02, 0.001)
    floor_z = float(seed_state.get("floor_z", args.floor_z))
    scene = write_scene(ball_radius, ball_mass=ball_mass, ball_inertia=ball_inertia, ball_friction=ball_friction, floor_z=floor_z)
    model = mujoco.MjModel.from_xml_path(str(scene))
    model.opt.timestep = args.dt
    robot_base_ipos = seed_state.get("robot_base_ipos")
    if args.robot_base_ipos is not None:
        robot_base_ipos = parse_vec(args.robot_base_ipos, 3)
    apply_scene_overrides(
        model,
        robot_friction=seed_state.get("robot_friction", args.robot_friction),
        base_mass=seed_state.get("robot_base_mass", args.robot_base_mass),
        base_ipos=robot_base_ipos,
    )
    if args.disable_motor_limits:
        model.actuator_ctrllimited[:] = 0
        model.actuator_ctrlrange[:, 0] = -1.0e9
        model.actuator_ctrlrange[:, 1] = 1.0e9
    elif args.torque_limit_scale != 1.0:
        model.actuator_ctrlrange[:, :] *= args.torque_limit_scale
    if args.zero_passive_joint_forces:
        for joint_name in UNITREE_MOTOR_ORDER:
            jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
            if jid >= 0:
                dof_id = int(model.jnt_dofadr[jid])
                model.dof_damping[dof_id] = 0.0
                model.dof_armature[dof_id] = 0.0
                model.dof_frictionloss[dof_id] = 0.0
    data = mujoco.MjData(model)
    qpos_addr, qvel_addr, actuator_ids, joint_limits = joint_addresses(model)
    base_pos = seed_state.get("robot_root_pos", parse_vec(args.base_pos, 3) if args.base_pos else [0.0, 0.0, args.base_z])
    base_quat = seed_state.get("robot_root_quat", parse_vec(args.base_quat, 4) if args.base_quat else [1.0, 0.0, 0.0, 0.0])
    base_lin_vel = seed_state.get("robot_root_lin_vel", parse_vec(args.base_lin_vel, 3) if args.base_lin_vel else [0.0, 0.0, 0.0])
    base_ang_vel = seed_state.get("robot_root_ang_vel", parse_vec(args.base_ang_vel, 3) if args.base_ang_vel else [0.0, 0.0, 0.0])
    ball_pos = seed_state.get("ball_root_pos", parse_vec(args.ball_pos, 3) if args.ball_pos else [0.0, 0.0, ball_radius])
    ball_quat = seed_state.get("ball_root_quat", parse_vec(args.ball_quat, 4) if args.ball_quat else [1.0, 0.0, 0.0, 0.0])
    motor_strength = float(seed_state.get("robot_motor_strength", args.motor_strength))
    set_initial_state(
        model,
        data,
        qpos_addr,
        run_dir=Path(args.run),
        base_pos=base_pos,
        base_quat=base_quat,
        base_lin_vel=base_lin_vel,
        base_ang_vel=base_ang_vel,
        ball_pos=ball_pos,
        ball_quat=ball_quat,
    )
    support_qpos = data.qpos[:7].copy()
    support_qvel = data.qvel[:6].copy()
    ball_jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "yoga_ball_free")
    ball_qpos = int(model.jnt_qposadr[ball_jid]) if ball_jid >= 0 else -1
    ball_qvel = int(model.jnt_dofadr[ball_jid]) if ball_jid >= 0 else -1
    ball_body = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "yoga_ball")
    support_ball_qpos = data.qpos[ball_qpos : ball_qpos + 7].copy() if ball_qpos >= 0 else np.zeros(7)
    support_ball_qvel = data.qvel[ball_qvel : ball_qvel + 6].copy() if ball_qvel >= 0 else np.zeros(6)

    ChannelFactoryInitialize(args.dds_domain, args.network_interface)
    low_state = unitree_go_msg_dds__LowState_()
    lowstate_pub = ChannelPublisher("rt/lowstate", LowState_)
    lowstate_pub.Init()
    command = Command()
    lowcmd_sub = ChannelSubscriber("rt/lowcmd", LowCmd_)
    lowcmd_sub.Init(command.callback, 10)

    start_mono = time.monotonic()
    append_event(event_log, "SIM_START", start_mono, sim_time=float(data.time), support=True, detail=f"scene={scene}")
    telemetry_fields = [
        "step",
        "monotonic_s",
        "wall_time_s",
        "sim_time_s",
        "support_active",
        "cmd_count",
        "cmd_active",
        "cmd_age_s",
        "base_z",
        "roll",
        "pitch",
        "ball_z",
        "joint_limit_violations",
    ]
    command_fields = ["count", "monotonic_s", "wall_time_s"] + [f"q_des_{i}" for i in range(12)] + [f"kp_{i}" for i in range(12)] + [f"kd_{i}" for i in range(12)]
    lowstate_fields = ["count", "monotonic_s", "wall_time_s"] + [f"q_{i}" for i in range(12)] + [f"dq_{i}" for i in range(12)] + [f"tau_{i}" for i in range(12)]
    replay_fields = (
        telemetry_fields
        + [f"q_{i}" for i in range(12)]
        + [f"dq_{i}" for i in range(12)]
        + [f"ctrl_{i}" for i in range(12)]
        + [f"actuator_force_{i}" for i in range(12)]
        + [f"raw_torque_{i}" for i in range(12)]
        + [f"torque_clip_margin_{i}" for i in range(12)]
    )
    pose_fields = [
        "base_x",
        "base_y",
        "base_z_qpos",
        "base_qw",
        "base_qx",
        "base_qy",
        "base_qz",
        "ball_x",
        "ball_y",
        "ball_z_qpos",
        "ball_qw",
        "ball_qx",
        "ball_qy",
        "ball_qz",
    ]
    replay_fields = replay_fields + pose_fields
    telemetry_f = (out_dir / "telemetry.csv").open("w", newline="", encoding="utf-8")
    commands_f = (out_dir / "commands.csv").open("w", newline="", encoding="utf-8")
    lowstate_f = (out_dir / "lowstate.csv").open("w", newline="", encoding="utf-8")
    replay_f = (out_dir / "replay.csv").open("w", newline="", encoding="utf-8")
    telemetry_writer = csv.DictWriter(telemetry_f, fieldnames=telemetry_fields)
    command_writer = csv.DictWriter(commands_f, fieldnames=command_fields)
    lowstate_writer = csv.DictWriter(lowstate_f, fieldnames=lowstate_fields)
    replay_writer = csv.DictWriter(replay_f, fieldnames=replay_fields)
    for writer in [telemetry_writer, command_writer, lowstate_writer, replay_writer]:
        writer.writeheader()

    support_active = True
    release_requested = False
    release_confirmed = False
    control_active_mono: float | None = None
    first_lowstate_logged = False
    last_logged_command_count = 0
    next_log_t = 0.0
    log_dt = 1.0 / args.log_hz
    sync_mono = start_mono
    sync_sim = float(data.time)
    fall_detected = False
    raw_torques = [0.0] * 12
    torque_clip_counts = [0] * 12
    raw_torque_abs_max = [0.0] * 12
    actuator_force_abs_max = [0.0] * 12
    step = 0

    try:
        while time.monotonic() - start_mono < args.duration_s:
            now = time.monotonic()
            cmd_age = None if command.last_monotonic is None else now - command.last_monotonic
            cmd_active = command.msg is not None and cmd_age is not None and cmd_age <= args.cmd_timeout_s
            if cmd_active and control_active_mono is None:
                control_active_mono = now
                append_event(event_log, "FIRST_DDS_LOWCMD", start_mono, sim_time=float(data.time), support=support_active)
                append_event(event_log, "CONTROL_ACTIVE_OBSERVED_BY_SIM", start_mono, sim_time=float(data.time), support=support_active)
            if support_active and control_active_mono is not None and now - control_active_mono >= args.release_after_command_s:
                append_event(event_log, "SUPPORT_RELEASE_REQUESTED", start_mono, sim_time=float(data.time), support=True)
                support_active = False
                release_requested = True
                release_confirmed = True
                append_event(event_log, "SUPPORT_RELEASE_CONFIRMED", start_mono, sim_time=float(data.time), support=False)
                append_event(event_log, "BALANCE_WINDOW_START", start_mono, sim_time=float(data.time), support=False)

            _, raw_torques = apply_command(data, command.msg if cmd_active else None, qpos_addr, qvel_addr, actuator_ids, motor_strength)
            data.xfrc_applied[:] = 0.0
            if ball_drag != 0.0 and ball_body >= 0 and ball_qvel >= 0:
                ball_lin_vel = np.asarray(data.qvel[ball_qvel : ball_qvel + 3], dtype=float)
                data.xfrc_applied[ball_body, 0] = -ball_drag * ball_lin_vel[0] * abs(ball_lin_vel[0])
                data.xfrc_applied[ball_body, 1] = -ball_drag * ball_lin_vel[1] * abs(ball_lin_vel[1])
            for i, raw_torque in enumerate(raw_torques):
                raw_torque_abs_max[i] = max(raw_torque_abs_max[i], abs(raw_torque))
                if model.actuator_ctrllimited[actuator_ids[i]]:
                    low, high = model.actuator_ctrlrange[actuator_ids[i]]
                    if raw_torque < float(low) or raw_torque > float(high):
                        torque_clip_counts[i] += 1
            if support_active:
                pin_supported_pose(data, support_qpos, support_qvel, ball_qpos, ball_qvel, support_ball_qpos, support_ball_qvel)
                mujoco.mj_forward(model, data)
            mujoco.mj_step(model, data)
            for i, actuator_id in enumerate(actuator_ids):
                actuator_force_abs_max[i] = max(actuator_force_abs_max[i], abs(float(data.actuator_force[actuator_id])))
            if support_active:
                pin_supported_pose(data, support_qpos, support_qvel, ball_qpos, ball_qvel, support_ball_qpos, support_ball_qvel)
                mujoco.mj_forward(model, data)
            publish_lowstate(lowstate_pub, low_state, data, qpos_addr, qvel_addr, actuator_ids)
            if not first_lowstate_logged:
                append_event(event_log, "FIRST_DDS_LOWSTATE", start_mono, sim_time=float(data.time), support=support_active)
                first_lowstate_logged = True

            if command.count > last_logged_command_count and command.msg is not None:
                row = {"count": command.count, "monotonic_s": f"{time.monotonic() - start_mono:.6f}", "wall_time_s": f"{time.time():.6f}"}
                for i in range(12):
                    row[f"q_des_{i}"] = f"{float(command.msg.motor_cmd[i].q):.9f}"
                    row[f"kp_{i}"] = f"{float(command.msg.motor_cmd[i].kp):.9f}"
                    row[f"kd_{i}"] = f"{float(command.msg.motor_cmd[i].kd):.9f}"
                command_writer.writerow(row)
                commands_f.flush()
                last_logged_command_count = command.count

            if float(data.time) + 1e-12 >= next_log_t:
                q = [float(data.qpos[i]) for i in qpos_addr]
                dq = [float(data.qvel[i]) for i in qvel_addr]
                ctrl = [float(data.ctrl[i]) for i in actuator_ids]
                actuator_force = [float(data.actuator_force[i]) for i in actuator_ids]
                roll, pitch, _ = quat_to_rpy(data.qpos[3:7])
                joint_violations = sum(int(q[i] < joint_limits[i][0] - 1e-6 or q[i] > joint_limits[i][1] + 1e-6) for i in range(12))
                base = {
                    "step": step,
                    "monotonic_s": f"{time.monotonic() - start_mono:.6f}",
                    "wall_time_s": f"{time.time():.6f}",
                    "sim_time_s": f"{float(data.time):.6f}",
                    "support_active": int(support_active),
                    "cmd_count": command.count,
                    "cmd_active": int(cmd_active),
                    "cmd_age_s": "" if cmd_age is None else f"{cmd_age:.6f}",
                    "base_z": f"{float(data.qpos[2]):.9f}",
                    "roll": f"{roll:.9f}",
                    "pitch": f"{pitch:.9f}",
                    "ball_z": "" if ball_qpos < 0 else f"{float(data.qpos[ball_qpos + 2]):.9f}",
                    "joint_limit_violations": joint_violations,
                }
                telemetry_writer.writerow(base)
                lowstate_row = {"count": step, "monotonic_s": base["monotonic_s"], "wall_time_s": base["wall_time_s"]}
                replay_row = dict(base)
                replay_row.update(
                    {
                        "base_x": f"{float(data.qpos[0]):.9f}",
                        "base_y": f"{float(data.qpos[1]):.9f}",
                        "base_z_qpos": f"{float(data.qpos[2]):.9f}",
                        "base_qw": f"{float(data.qpos[3]):.9f}",
                        "base_qx": f"{float(data.qpos[4]):.9f}",
                        "base_qy": f"{float(data.qpos[5]):.9f}",
                        "base_qz": f"{float(data.qpos[6]):.9f}",
                        "ball_x": "" if ball_qpos < 0 else f"{float(data.qpos[ball_qpos]):.9f}",
                        "ball_y": "" if ball_qpos < 0 else f"{float(data.qpos[ball_qpos + 1]):.9f}",
                        "ball_z_qpos": "" if ball_qpos < 0 else f"{float(data.qpos[ball_qpos + 2]):.9f}",
                        "ball_qw": "" if ball_qpos < 0 else f"{float(data.qpos[ball_qpos + 3]):.9f}",
                        "ball_qx": "" if ball_qpos < 0 else f"{float(data.qpos[ball_qpos + 4]):.9f}",
                        "ball_qy": "" if ball_qpos < 0 else f"{float(data.qpos[ball_qpos + 5]):.9f}",
                        "ball_qz": "" if ball_qpos < 0 else f"{float(data.qpos[ball_qpos + 6]):.9f}",
                    }
                )
                for i in range(12):
                    lowstate_row[f"q_{i}"] = f"{q[i]:.9f}"
                    lowstate_row[f"dq_{i}"] = f"{dq[i]:.9f}"
                    lowstate_row[f"tau_{i}"] = f"{float(data.actuator_force[actuator_ids[i]]):.9f}"
                    replay_row[f"q_{i}"] = f"{q[i]:.9f}"
                    replay_row[f"dq_{i}"] = f"{dq[i]:.9f}"
                    replay_row[f"ctrl_{i}"] = f"{ctrl[i]:.9f}"
                    replay_row[f"actuator_force_{i}"] = f"{actuator_force[i]:.9f}"
                    replay_row[f"raw_torque_{i}"] = f"{raw_torques[i]:.9f}"
                    replay_row[f"torque_clip_margin_{i}"] = f"{abs(raw_torques[i]) - abs(actuator_force[i]):.9f}"
                lowstate_writer.writerow(lowstate_row)
                replay_writer.writerow(replay_row)
                telemetry_f.flush()
                lowstate_f.flush()
                replay_f.flush()
                next_log_t += log_dt

            roll, pitch, _ = quat_to_rpy(data.qpos[3:7])
            if release_confirmed and (float(data.qpos[2]) < args.fall_base_z or abs(roll) > 1.0 or abs(pitch) > 1.0):
                append_event(event_log, "FALL_DETECTED", start_mono, sim_time=float(data.time), support=False, detail=f"base_z={float(data.qpos[2]):.4f},roll={roll:.4f},pitch={pitch:.4f}")
                fall_detected = True
                break

            sleep_s = sync_mono + (float(data.time) - sync_sim) - time.monotonic()
            if sleep_s > 0:
                time.sleep(sleep_s)
            step += 1
    finally:
        for f in [telemetry_f, commands_f, lowstate_f, replay_f]:
            f.close()

    if release_confirmed and not fall_detected:
        append_event(event_log, "BALANCE_WINDOW_END", start_mono, sim_time=float(data.time), support=False)
    summary = {
        "ok": bool(release_confirmed and command.count > 0),
        "scene": str(scene),
        "run": args.run,
        "sim_elapsed_s": float(data.time),
        "wall_elapsed_s": time.monotonic() - start_mono,
        "release_requested": release_requested,
        "release_confirmed": release_confirmed,
        "fall_detected": fall_detected,
        "cmd_count": command.count,
        "disable_motor_limits": args.disable_motor_limits,
        "torque_limit_scale": args.torque_limit_scale,
        "zero_passive_joint_forces": args.zero_passive_joint_forces,
        "seed_state": args.seed_state,
        "scene_overrides": {
            "ball_radius": ball_radius,
            "ball_mass": ball_mass,
                "ball_inertia": ball_inertia,
                "ball_drag": ball_drag,
                "ball_friction": ball_friction[0],
            "floor_z": floor_z,
            "robot_friction": seed_state.get("robot_friction", args.robot_friction),
            "robot_base_mass": seed_state.get("robot_base_mass", args.robot_base_mass),
            "robot_base_ipos": robot_base_ipos,
            "robot_motor_strength": motor_strength,
            "robot_root_pos": base_pos,
            "robot_root_quat": base_quat,
            "robot_root_lin_vel": base_lin_vel,
            "robot_root_ang_vel": base_ang_vel,
            "ball_root_pos": ball_pos,
            "ball_root_quat": ball_quat,
        },
        "torque_clip_counts": torque_clip_counts,
        "raw_torque_abs_max": raw_torque_abs_max,
        "actuator_force_abs_max": actuator_force_abs_max,
        "event_log": str(event_log),
        "telemetry": "telemetry.csv",
        "commands": "commands.csv",
        "lowstate": "lowstate.csv",
        "replay": "replay.csv",
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_event(event_log, "SIM_STOP", start_mono, sim_time=float(data.time), support=False, detail=json.dumps(summary, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
