#!/usr/bin/env python3
"""Go1 yoga-ball MuJoCo bridge for DrEureka LCM deployment policy."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import select
import sys
import time
from typing import Any

import lcm
import mujoco
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
DREUREKA = ROOT / "thirdparties" / "DrEureka"
if str(DREUREKA / "globe_walking") not in sys.path:
    sys.path.insert(0, str(DREUREKA / "globe_walking"))
if str(DREUREKA / "globe_walking" / "go1_gym_deploy") not in sys.path:
    sys.path.insert(0, str(DREUREKA / "globe_walking" / "go1_gym_deploy"))

from go1_gym_deploy.lcm_types.leg_control_data_lcmt import leg_control_data_lcmt  # noqa: E402
from go1_gym_deploy.lcm_types.pd_tau_targets_lcmt import pd_tau_targets_lcmt  # noqa: E402
from go1_gym_deploy.lcm_types.rc_command_lcmt import rc_command_lcmt  # noqa: E402
from go1_gym_deploy.lcm_types.state_estimator_lcmt import state_estimator_lcmt  # noqa: E402


HARDWARE_JOINT_NAMES = [
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
POLICY_JOINT_NAMES = [
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


class CommandState:
    def __init__(self) -> None:
        self.msg: pd_tau_targets_lcmt | None = None
        self.count = 0
        self.last_monotonic: float | None = None

    def callback(self, channel: str, data: bytes) -> None:
        del channel
        self.msg = pd_tau_targets_lcmt.decode(data)
        self.count += 1
        self.last_monotonic = time.monotonic()


def append_event(path: Path, event: str, start_mono: float, *, sim_time: float, support: bool, detail: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists()
    elapsed = time.monotonic() - start_mono
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EVENT_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(
            {
                "event": event,
                "monotonic_s": f"{elapsed:.6f}",
                "wall_time_s": f"{time.time():.6f}",
                "sim_time_s": f"{sim_time:.6f}",
                "support_active": int(support),
                "detail": detail,
            }
        )


def quat_to_rpy(q: Any) -> tuple[float, float, float]:
    w, x, y, z = [float(v) for v in q]
    roll = math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    sinp = 2 * (w * y - z * x)
    pitch = math.asin(max(-1.0, min(1.0, sinp)))
    yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
    return roll, pitch, yaw


def joint_addresses(model: Any) -> tuple[list[int], list[int], list[int], list[tuple[float, float]]]:
    qpos, qvel, actuator, limits = [], [], [], []
    for name in HARDWARE_JOINT_NAMES:
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
        aid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, name.removesuffix("_joint"))
        if jid < 0 or aid < 0:
            raise RuntimeError(f"missing joint/actuator for {name}")
        qpos.append(int(model.jnt_qposadr[jid]))
        qvel.append(int(model.jnt_dofadr[jid]))
        actuator.append(int(aid))
        limits.append((float(model.jnt_range[jid, 0]), float(model.jnt_range[jid, 1])))
    return qpos, qvel, actuator, limits


def default_angles(run_dir: Path) -> dict[str, float]:
    import pickle

    path = run_dir / "parameters.pkl"
    with path.open("rb") as f:
        cfg = pickle.load(f)["Cfg"]
    return {name: float(cfg["init_state"]["default_joint_angles"][name]) for name in POLICY_JOINT_NAMES}


def set_initial_state(model: Any, data: Any, qpos_addr: list[int], *, run_dir: Path, base_z: float, ball_radius: float) -> None:
    angles = default_angles(run_dir)
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    data.qpos[0:3] = [0.0, 0.0, base_z]
    data.qpos[3:7] = [1.0, 0.0, 0.0, 0.0]
    for i, name in enumerate(HARDWARE_JOINT_NAMES):
        data.qpos[qpos_addr[i]] = angles[name]
    ball_jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "yoga_ball_free")
    if ball_jid >= 0:
        ball_qpos = int(model.jnt_qposadr[ball_jid])
        data.qpos[ball_qpos : ball_qpos + 7] = [0.0, 0.0, ball_radius, 1.0, 0.0, 0.0, 0.0]
    mujoco.mj_forward(model, data)


def publish_state(lc: lcm.LCM, data: Any, qpos_addr: list[int], qvel_addr: list[int], actuator_ids: list[int]) -> None:
    now_us = int(time.time() * 1e6)
    leg = leg_control_data_lcmt()
    leg.q = [float(data.qpos[i]) for i in qpos_addr]
    leg.qd = [float(data.qvel[i]) for i in qvel_addr]
    leg.p = [0.0] * 12
    leg.v = [0.0] * 12
    leg.tau_est = [float(data.actuator_force[i]) for i in actuator_ids]
    leg.timestamp_us = now_us
    leg.id = 0
    leg.robot_id = 0
    lc.publish("leg_control_data", leg.encode())

    rpy = quat_to_rpy(data.qpos[3:7])
    se = state_estimator_lcmt()
    se.p = [float(v) for v in data.qpos[0:3]]
    se.vWorld = [float(v) for v in data.qvel[0:3]]
    se.vBody = [float(v) for v in data.qvel[0:3]]
    se.rpy = list(rpy)
    se.omegaBody = [float(v) for v in data.qvel[3:6]]
    se.omegaWorld = [float(v) for v in data.qvel[3:6]]
    se.quat = [float(v) for v in data.qpos[3:7]]
    se.contact_estimate = [300.0] * 4
    se.aBody = [0.0, 0.0, 0.0]
    se.aWorld = [0.0, 0.0, 0.0]
    se.timestamp_us = now_us
    se.id = 0
    se.robot_id = 0
    lc.publish("state_estimator_data", se.encode())

    rc = rc_command_lcmt()
    rc.mode = 0
    rc.left_stick = [0.0, 0.0]
    rc.right_stick = [0.0, 0.0]
    rc.knobs = [0.0, 0.0]
    rc.left_upper_switch = 0
    rc.left_lower_left_switch = 0
    rc.left_lower_right_switch = 0
    rc.right_upper_switch = 0
    rc.right_lower_left_switch = 0
    rc.right_lower_right_switch = 0
    lc.publish("rc_command", rc.encode())


def apply_command(data: Any, cmd: pd_tau_targets_lcmt | None, qpos_addr: list[int], qvel_addr: list[int], actuator_ids: list[int]) -> bool:
    data.ctrl[:] = 0.0
    if cmd is None:
        return False
    for i in range(12):
        q = float(data.qpos[qpos_addr[i]])
        dq = float(data.qvel[qvel_addr[i]])
        data.ctrl[actuator_ids[i]] = (
            float(cmd.tau_ff[i])
            + float(cmd.kp[i]) * (float(cmd.q_des[i]) - q)
            + float(cmd.kd[i]) * (float(cmd.qd_des[i]) - dq)
        )
    return True


def write_csv_header(path: Path, fields: list[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    f = path.open("w", newline="", encoding="utf-8")
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    return f, writer


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", required=True)
    parser.add_argument(
        "--run",
        default=str(DREUREKA / "globe_walking" / "runs" / "globe_walking" / "dr_eureka_best"),
    )
    parser.add_argument("--duration-s", type=float, default=8.0)
    parser.add_argument("--release-after-command-s", type=float, default=0.25)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--event-log", required=True)
    parser.add_argument("--lcm-url", default="udpm://239.255.76.67:7667?ttl=255")
    parser.add_argument("--dt", type=float, default=0.002)
    parser.add_argument("--log-hz", type=float, default=50.0)
    parser.add_argument("--ball-radius", type=float, default=0.45)
    parser.add_argument("--fall-base-z", type=float, default=0.75)
    parser.add_argument("--cmd-timeout-s", type=float, default=0.1)
    parser.add_argument("--remove-control-after-release-s", type=float, default=-1.0)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    event_log = Path(args.event_log)
    lc = lcm.LCM(args.lcm_url)
    command = CommandState()
    lc.subscribe("pd_plustau_targets", command.callback)

    model = mujoco.MjModel.from_xml_path(args.scene)
    model.opt.timestep = args.dt
    data = mujoco.MjData(model)
    qpos_addr, qvel_addr, actuator_ids, joint_limits = joint_addresses(model)
    support_height = 2.0 * args.ball_radius + 0.0001
    set_initial_state(model, data, qpos_addr, run_dir=Path(args.run), base_z=support_height, ball_radius=args.ball_radius)
    support_qpos = data.qpos[:7].copy()
    support_qvel = data.qvel[:6].copy()

    start_mono = time.monotonic()
    append_event(event_log, "SIM_START", start_mono, sim_time=float(data.time), support=True, detail=f"scene={args.scene}")

    status_fields = [
        "step",
        "monotonic_s",
        "wall_time_s",
        "sim_time_s",
        "support_active",
        "cmd_received",
        "cmd_active",
        "cmd_count",
        "cmd_age_s",
        "base_z",
        "ball_z",
        "roll",
        "pitch",
        "joint_limit_violations",
    ]
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
    replay_fields = (
        status_fields
        + pose_fields
        + [f"q_{i}" for i in range(12)]
        + [f"dq_{i}" for i in range(12)]
        + [f"q_des_{i}" for i in range(12)]
        + [f"ctrl_{i}" for i in range(12)]
    )
    status_f, status_writer = write_csv_header(out_dir / "simulator_status.csv", status_fields)
    replay_f, replay_writer = write_csv_header(out_dir / "replay.csv", replay_fields)

    sync_mono = start_mono
    sync_sim = float(data.time)
    next_log_t = 0.0
    log_dt = 1.0 / args.log_hz
    support_active = True
    release_requested = False
    release_confirmed = False
    control_active_mono: float | None = None
    release_mono: float | None = None
    control_removed = False
    fall_detected = False
    step = 0

    try:
        while time.monotonic() - start_mono < args.duration_s:
            while True:
                readable, _, _ = select.select([lc.fileno()], [], [], 0.0)
                if not readable:
                    break
                lc.handle()
            now_mono = time.monotonic()
            cmd_age = None if command.last_monotonic is None else now_mono - command.last_monotonic
            cmd_active = command.msg is not None and cmd_age is not None and cmd_age <= args.cmd_timeout_s
            if cmd_active and control_active_mono is None:
                control_active_mono = now_mono
                append_event(event_log, "CONTROL_ACTIVE_OBSERVED_BY_SIM", start_mono, sim_time=float(data.time), support=support_active)
            if (
                support_active
                and control_active_mono is not None
                and now_mono - control_active_mono >= args.release_after_command_s
            ):
                append_event(event_log, "SUPPORT_RELEASE_REQUESTED", start_mono, sim_time=float(data.time), support=True)
                support_active = False
                release_requested = True
                append_event(event_log, "SUPPORT_RELEASE_CONFIRMED", start_mono, sim_time=float(data.time), support=False)
                append_event(event_log, "BALANCE_WINDOW_START", start_mono, sim_time=float(data.time), support=False)
                release_confirmed = True
                release_mono = now_mono

            if (
                release_mono is not None
                and args.remove_control_after_release_s >= 0.0
                and not control_removed
                and now_mono - release_mono >= args.remove_control_after_release_s
            ):
                append_event(event_log, "CONTROL_REMOVAL_REQUESTED", start_mono, sim_time=float(data.time), support=False)
                control_removed = True
                append_event(event_log, "CONTROL_REMOVED", start_mono, sim_time=float(data.time), support=False)

            active_command = None if control_removed else (command.msg if cmd_active else None)
            apply_command(data, active_command, qpos_addr, qvel_addr, actuator_ids)
            if support_active:
                data.qpos[:7] = support_qpos
                data.qvel[:6] = support_qvel
                mujoco.mj_forward(model, data)
            mujoco.mj_step(model, data)
            if support_active:
                data.qpos[:7] = support_qpos
                data.qvel[:6] = support_qvel
                mujoco.mj_forward(model, data)
            publish_state(lc, data, qpos_addr, qvel_addr, actuator_ids)

            if data.time + 1e-12 >= next_log_t:
                roll, pitch, _ = quat_to_rpy(data.qpos[3:7])
                ball_jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "yoga_ball_free")
                ball_z = ""
                if ball_jid >= 0:
                    ball_qpos = int(model.jnt_qposadr[ball_jid])
                    ball_z = f"{float(data.qpos[ball_qpos + 2]):.9f}"
                else:
                    ball_qpos = -1
                q = [float(data.qpos[i]) for i in qpos_addr]
                dq = [float(data.qvel[i]) for i in qvel_addr]
                q_des = [float(command.msg.q_des[i]) if command.msg is not None else 0.0 for i in range(12)]
                ctrl = [float(data.ctrl[i]) for i in actuator_ids]
                joint_violations = sum(
                    int(q[i] < joint_limits[i][0] - 1e-6 or q[i] > joint_limits[i][1] + 1e-6)
                    for i in range(12)
                )
                row = {
                    "step": step,
                    "monotonic_s": f"{time.monotonic() - start_mono:.6f}",
                    "wall_time_s": f"{time.time():.6f}",
                    "sim_time_s": f"{float(data.time):.6f}",
                    "support_active": int(support_active),
                    "cmd_received": int(command.msg is not None),
                    "cmd_active": int(cmd_active and not control_removed),
                    "cmd_count": command.count,
                    "cmd_age_s": "" if cmd_age is None else f"{cmd_age:.6f}",
                    "base_z": f"{float(data.qpos[2]):.9f}",
                    "ball_z": ball_z,
                    "roll": f"{roll:.9f}",
                    "pitch": f"{pitch:.9f}",
                    "joint_limit_violations": joint_violations,
                }
                status_writer.writerow(row)
                replay_row = dict(row)
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
                    replay_row[f"q_{i}"] = f"{q[i]:.9f}"
                    replay_row[f"dq_{i}"] = f"{dq[i]:.9f}"
                    replay_row[f"q_des_{i}"] = f"{q_des[i]:.9f}"
                    replay_row[f"ctrl_{i}"] = f"{ctrl[i]:.9f}"
                replay_writer.writerow(replay_row)
                status_f.flush()
                replay_f.flush()
                next_log_t += log_dt

            if release_confirmed and (float(data.qpos[2]) < args.fall_base_z or abs(roll) > 1.0 or abs(pitch) > 1.0):
                append_event(event_log, "FALL_DETECTED", start_mono, sim_time=float(data.time), support=False, detail=f"base_z={float(data.qpos[2]):.4f},roll={roll:.4f},pitch={pitch:.4f}")
                fall_detected = True
                break

            sleep_s = sync_mono + (float(data.time) - sync_sim) - time.monotonic()
            if sleep_s > 0:
                time.sleep(sleep_s)
            step += 1
    finally:
        status_f.close()
        replay_f.close()

    if release_confirmed and not fall_detected:
        append_event(event_log, "BALANCE_WINDOW_END", start_mono, sim_time=float(data.time), support=False)
    summary = {
        "scene": args.scene,
        "duration_s": args.duration_s,
        "sim_elapsed_s": float(data.time),
        "wall_elapsed_s": time.monotonic() - start_mono,
        "release_requested": release_requested,
        "release_confirmed": release_confirmed,
        "control_removed": control_removed,
        "fall_detected": fall_detected,
        "cmd_count": command.count,
        "event_log": str(event_log),
        "status_log": "simulator_status.csv",
        "replay_log": "replay.csv",
    }
    (out_dir / "sim_bridge_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return 0 if release_confirmed and command.count > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
