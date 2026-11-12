#!/usr/bin/env python3
"""Bridge DrEureka LCM policy messages to the Unitree Go2 SDK2 DDS contract."""

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
from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelPublisher, ChannelSubscriber  # noqa: E402
from unitree_sdk2py.idl.default import unitree_go_msg_dds__LowCmd_  # noqa: E402
from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowCmd_, LowState_  # noqa: E402
from unitree_sdk2py.utils.crc import CRC  # noqa: E402


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

EVENT_FIELDS = ["event", "monotonic_s", "wall_time_s", "detail"]


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if p <= 0:
        return ordered[0]
    if p >= 100:
        return ordered[-1]
    idx = (len(ordered) - 1) * (p / 100.0)
    lo = math.floor(idx)
    hi = math.ceil(idx)
    if lo == hi:
        return ordered[lo]
    weight = idx - lo
    return ordered[lo] * (1.0 - weight) + ordered[hi] * weight


def summarize_series(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "avg": None, "min": None, "p50": None, "p95": None, "p99": None, "max": None}
    return {
        "count": len(values),
        "avg": sum(values) / len(values),
        "min": min(values),
        "p50": percentile(values, 50.0),
        "p95": percentile(values, 95.0),
        "p99": percentile(values, 99.0),
        "max": max(values),
    }


def append_event(path: Path | None, event: str, start_mono: float, detail: str = "") -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = (not path.exists()) or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EVENT_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(
            {
                "event": event,
                "monotonic_s": f"{time.monotonic() - start_mono:.6f}",
                "wall_time_s": f"{time.time():.6f}",
                "detail": detail,
            }
        )


def quat_to_rpy(quat: list[float] | tuple[float, ...]) -> list[float]:
    w, x, y, z = [float(v) for v in quat]
    roll = math.atan2(2.0 * (w * x + y * z), 1.0 - 2.0 * (x * x + y * y))
    pitch = math.asin(max(-1.0, min(1.0, 2.0 * (w * y - z * x))))
    yaw = math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))
    return [roll, pitch, yaw]


class Go2LcmDdsBridge:
    def __init__(
        self,
        *,
        lcm_url: str,
        dds_domain: int,
        network_interface: str | None,
        out_dir: Path | None = None,
        event_log: Path | None = None,
    ) -> None:
        self.start_mono = time.monotonic()
        self.event_log = event_log
        self.out_dir = out_dir
        self.command_count = 0
        self.lowstate_count = 0
        self.command_intervals: list[float] = []
        self.command_callback_durations: list[float] = []
        self.lowcmd_write_durations: list[float] = []
        self.lowstate_intervals: list[float] = []
        self.lowstate_callback_durations: list[float] = []
        self.publish_lcm_state_durations: list[float] = []
        self.leg_publish_durations: list[float] = []
        self.state_publish_durations: list[float] = []
        self.rc_publish_durations: list[float] = []
        self.command_writer = None
        self.command_file = None
        self.lowstate_writer = None
        self.lowstate_file = None
        self.summary_path = None if out_dir is None else out_dir / "bridge_diagnostics.json"
        if out_dir is not None:
            out_dir.mkdir(parents=True, exist_ok=True)
            self.command_file = (out_dir / "bridge_commands.csv").open("w", newline="", encoding="utf-8")
            self.command_writer = csv.DictWriter(
                self.command_file,
                fieldnames=[
                    "count",
                    "monotonic_s",
                    "wall_time_s",
                    "interval_s",
                    "callback_s",
                    "dds_write_s",
                    "q0",
                    "kp0",
                    "kd0",
                    "tau0",
                ],
            )
            self.command_writer.writeheader()
            self.lowstate_file = (out_dir / "bridge_lowstate.csv").open("w", newline="", encoding="utf-8")
            self.lowstate_writer = csv.DictWriter(
                self.lowstate_file,
                fieldnames=[
                    "count",
                    "monotonic_s",
                    "wall_time_s",
                    "interval_s",
                    "callback_s",
                    "publish_lcm_state_s",
                    "leg_publish_s",
                    "state_publish_s",
                    "rc_publish_s",
                    "q0",
                    "dq0",
                    "tau0",
                    "quat_w",
                    "quat_x",
                    "quat_y",
                    "quat_z",
                ],
            )
            self.lowstate_writer.writeheader()
        append_event(self.event_log, "BRIDGE_START", self.start_mono, f"dds_domain={dds_domain},interface={network_interface},lcm_url={lcm_url}")
        ChannelFactoryInitialize(dds_domain, network_interface)
        self.lc = lcm.LCM(lcm_url)
        self.crc = CRC()
        self.low_cmd = unitree_go_msg_dds__LowCmd_()
        self.lowcmd_pub = ChannelPublisher("rt/lowcmd", LowCmd_)
        self.lowcmd_pub.Init()
        self.lowstate_sub = ChannelSubscriber("rt/lowstate", LowState_)
        self.lowstate_sub.Init(self.on_lowstate, 10)
        self.lc.subscribe("pd_plustau_targets", self.on_lcm_command)
        self.last_lowstate: Any | None = None
        self.last_lowstate_monotonic: float | None = None
        self.last_cmd_monotonic: float | None = None
        self.init_lowcmd()

    def init_lowcmd(self) -> None:
        self.low_cmd.head[0] = 0xFE
        self.low_cmd.head[1] = 0xEF
        self.low_cmd.level_flag = 0xFF
        self.low_cmd.gpio = 0
        for i in range(20):
            motor = self.low_cmd.motor_cmd[i]
            motor.mode = 0x01
            motor.q = 2.146e9
            motor.dq = 16000.0
            motor.kp = 0.0
            motor.kd = 0.0
            motor.tau = 0.0

    def on_lcm_command(self, channel: str, data: bytes) -> None:
        del channel
        callback_start = time.monotonic()
        interval_s = None if self.last_cmd_monotonic is None else callback_start - self.last_cmd_monotonic
        msg = pd_tau_targets_lcmt.decode(data)
        for i in range(12):
            motor = self.low_cmd.motor_cmd[i]
            motor.mode = 0x01
            motor.q = float(msg.q_des[i])
            motor.dq = float(msg.qd_des[i])
            motor.tau = float(msg.tau_ff[i])
            motor.kp = float(msg.kp[i])
            motor.kd = float(msg.kd[i])
        self.low_cmd.crc = self.crc.Crc(self.low_cmd)
        write_start = time.monotonic()
        self.lowcmd_pub.Write(self.low_cmd)
        dds_write_s = time.monotonic() - write_start
        callback_s = time.monotonic() - callback_start
        self.last_cmd_monotonic = callback_start
        self.command_count += 1
        if interval_s is not None:
            self.command_intervals.append(interval_s)
        self.command_callback_durations.append(callback_s)
        self.lowcmd_write_durations.append(dds_write_s)
        if self.command_count == 1:
            append_event(self.event_log, "BRIDGE_FIRST_LCM_COMMAND", self.start_mono)
            append_event(self.event_log, "BRIDGE_FIRST_DDS_LOWCMD", self.start_mono)
        if self.command_writer is not None:
            self.command_writer.writerow(
                {
                    "count": self.command_count,
                    "monotonic_s": f"{time.monotonic() - self.start_mono:.6f}",
                    "wall_time_s": f"{time.time():.6f}",
                    "interval_s": "" if interval_s is None else f"{interval_s:.9f}",
                    "callback_s": f"{callback_s:.9f}",
                    "dds_write_s": f"{dds_write_s:.9f}",
                    "q0": f"{float(msg.q_des[0]):.9f}",
                    "kp0": f"{float(msg.kp[0]):.9f}",
                    "kd0": f"{float(msg.kd[0]):.9f}",
                    "tau0": f"{float(msg.tau_ff[0]):.9f}",
                }
            )
            self.command_file.flush()

    def on_lowstate(self, msg: LowState_) -> None:
        callback_start = time.monotonic()
        interval_s = None if self.last_lowstate_monotonic is None else callback_start - self.last_lowstate_monotonic
        self.last_lowstate = msg
        self.last_lowstate_monotonic = callback_start
        self.lowstate_count += 1
        if self.lowstate_count == 1:
            append_event(self.event_log, "BRIDGE_FIRST_DDS_LOWSTATE", self.start_mono)
            append_event(self.event_log, "BRIDGE_FIRST_LCM_STATE", self.start_mono)
        publish_stats = self.publish_lcm_state(msg)
        callback_s = time.monotonic() - callback_start
        if interval_s is not None:
            self.lowstate_intervals.append(interval_s)
        self.lowstate_callback_durations.append(callback_s)
        self.publish_lcm_state_durations.append(publish_stats["publish_lcm_state_s"])
        self.leg_publish_durations.append(publish_stats["leg_publish_s"])
        self.state_publish_durations.append(publish_stats["state_publish_s"])
        self.rc_publish_durations.append(publish_stats["rc_publish_s"])
        if self.lowstate_writer is not None:
            self.lowstate_writer.writerow(
                {
                    "count": self.lowstate_count,
                    "monotonic_s": f"{time.monotonic() - self.start_mono:.6f}",
                    "wall_time_s": f"{time.time():.6f}",
                    "interval_s": "" if interval_s is None else f"{interval_s:.9f}",
                    "callback_s": f"{callback_s:.9f}",
                    "publish_lcm_state_s": f"{publish_stats['publish_lcm_state_s']:.9f}",
                    "leg_publish_s": f"{publish_stats['leg_publish_s']:.9f}",
                    "state_publish_s": f"{publish_stats['state_publish_s']:.9f}",
                    "rc_publish_s": f"{publish_stats['rc_publish_s']:.9f}",
                    "q0": f"{float(msg.motor_state[0].q):.9f}",
                    "dq0": f"{float(msg.motor_state[0].dq):.9f}",
                    "tau0": f"{float(msg.motor_state[0].tau_est):.9f}",
                    "quat_w": f"{float(msg.imu_state.quaternion[0]):.9f}",
                    "quat_x": f"{float(msg.imu_state.quaternion[1]):.9f}",
                    "quat_y": f"{float(msg.imu_state.quaternion[2]):.9f}",
                    "quat_z": f"{float(msg.imu_state.quaternion[3]):.9f}",
                }
            )
            self.lowstate_file.flush()

    def publish_lcm_state(self, msg: LowState_) -> dict[str, float]:
        total_start = time.monotonic()
        now_us = int(time.time() * 1e6)
        leg = leg_control_data_lcmt()
        leg.q = [float(msg.motor_state[i].q) for i in range(12)]
        leg.qd = [float(msg.motor_state[i].dq) for i in range(12)]
        leg.p = [0.0] * 12
        leg.v = [0.0] * 12
        leg.tau_est = [float(msg.motor_state[i].tau_est) for i in range(12)]
        leg.timestamp_us = now_us
        leg.id = 0
        leg.robot_id = 1
        leg_start = time.monotonic()
        self.lc.publish("leg_control_data", leg.encode())
        leg_publish_s = time.monotonic() - leg_start

        state = state_estimator_lcmt()
        state.p = [0.0, 0.0, 0.0]
        state.vWorld = [0.0, 0.0, 0.0]
        state.vBody = [0.0, 0.0, 0.0]
        state.quat = [float(v) for v in msg.imu_state.quaternion]
        state.rpy = [float(v) for v in msg.imu_state.rpy]
        if state.rpy == [0.0, 0.0, 0.0] and state.quat != [0.0, 0.0, 0.0, 0.0]:
            state.rpy = quat_to_rpy(state.quat)
        state.omegaBody = [float(v) for v in msg.imu_state.gyroscope]
        state.omegaWorld = list(state.omegaBody)
        state.aBody = [float(v) for v in msg.imu_state.accelerometer]
        state.aWorld = list(state.aBody)
        state.contact_estimate = [float(v) for v in msg.foot_force_est]
        if not any(state.contact_estimate):
            state.contact_estimate = [float(v) for v in msg.foot_force]
        state.timestamp_us = now_us
        state.id = 0
        state.robot_id = 1
        state_start = time.monotonic()
        self.lc.publish("state_estimator_data", state.encode())
        state_publish_s = time.monotonic() - state_start

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
        rc_start = time.monotonic()
        self.lc.publish("rc_command", rc.encode())
        rc_publish_s = time.monotonic() - rc_start
        return {
            "publish_lcm_state_s": time.monotonic() - total_start,
            "leg_publish_s": leg_publish_s,
            "state_publish_s": state_publish_s,
            "rc_publish_s": rc_publish_s,
        }

    def spin(self, duration_s: float | None) -> int:
        start = time.monotonic()
        while duration_s is None or time.monotonic() - start < duration_s:
            readable, _, _ = select.select([self.lc.fileno()], [], [], 0.001)
            if readable:
                self.lc.handle()
            time.sleep(0.001)
        append_event(self.event_log, "BRIDGE_STOP", self.start_mono, f"commands={self.command_count},lowstates={self.lowstate_count}")
        if self.summary_path is not None:
            self.summary_path.write_text(
                json.dumps(
                    {
                        "command_count": self.command_count,
                        "lowstate_count": self.lowstate_count,
                        "command_interval_s": summarize_series(self.command_intervals),
                        "command_callback_s": summarize_series(self.command_callback_durations),
                        "lowcmd_write_s": summarize_series(self.lowcmd_write_durations),
                        "lowstate_interval_s": summarize_series(self.lowstate_intervals),
                        "lowstate_callback_s": summarize_series(self.lowstate_callback_durations),
                        "publish_lcm_state_s": summarize_series(self.publish_lcm_state_durations),
                        "leg_publish_s": summarize_series(self.leg_publish_durations),
                        "state_publish_s": summarize_series(self.state_publish_durations),
                        "rc_publish_s": summarize_series(self.rc_publish_durations),
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
        if self.command_file is not None:
            self.command_file.close()
        if self.lowstate_file is not None:
            self.lowstate_file.close()
        return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lcm-url", default="udpm://239.255.76.67:7667?ttl=255")
    parser.add_argument("--dds-domain", type=int, default=0)
    parser.add_argument("--network-interface", default=None)
    parser.add_argument("--duration-s", type=float, default=None)
    parser.add_argument("--out-dir", default=None)
    parser.add_argument("--event-log", default=None)
    args = parser.parse_args()
    bridge = Go2LcmDdsBridge(
        lcm_url=args.lcm_url,
        dds_domain=args.dds_domain,
        network_interface=args.network_interface,
        out_dir=Path(args.out_dir) if args.out_dir else None,
        event_log=Path(args.event_log) if args.event_log else None,
    )
    return bridge.spin(args.duration_s)


if __name__ == "__main__":
    raise SystemExit(main())
