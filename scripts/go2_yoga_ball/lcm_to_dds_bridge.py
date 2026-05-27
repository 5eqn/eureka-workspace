#!/usr/bin/env python3
"""Bridge DrEureka LCM policy messages to the Unitree Go2 SDK2 DDS contract."""

from __future__ import annotations

import argparse
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


def quat_to_rpy(quat: list[float] | tuple[float, ...]) -> list[float]:
    w, x, y, z = [float(v) for v in quat]
    roll = math.atan2(2.0 * (w * x + y * z), 1.0 - 2.0 * (x * x + y * y))
    pitch = math.asin(max(-1.0, min(1.0, 2.0 * (w * y - z * x))))
    yaw = math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))
    return [roll, pitch, yaw]


class Go2LcmDdsBridge:
    def __init__(self, *, lcm_url: str, dds_domain: int, network_interface: str | None) -> None:
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
        self.lowcmd_pub.Write(self.low_cmd)
        self.last_cmd_monotonic = time.monotonic()

    def on_lowstate(self, msg: LowState_) -> None:
        self.last_lowstate = msg
        self.last_lowstate_monotonic = time.monotonic()
        self.publish_lcm_state(msg)

    def publish_lcm_state(self, msg: LowState_) -> None:
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
        self.lc.publish("leg_control_data", leg.encode())

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
        self.lc.publish("state_estimator_data", state.encode())

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
        self.lc.publish("rc_command", rc.encode())

    def spin(self, duration_s: float | None) -> int:
        start = time.monotonic()
        while duration_s is None or time.monotonic() - start < duration_s:
            readable, _, _ = select.select([self.lc.fileno()], [], [], 0.001)
            if readable:
                self.lc.handle()
            time.sleep(0.001)
        return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lcm-url", default="udpm://239.255.76.67:7667?ttl=255")
    parser.add_argument("--dds-domain", type=int, default=0)
    parser.add_argument("--network-interface", default=None)
    parser.add_argument("--duration-s", type=float, default=None)
    args = parser.parse_args()
    bridge = Go2LcmDdsBridge(
        lcm_url=args.lcm_url,
        dds_domain=args.dds_domain,
        network_interface=args.network_interface,
    )
    return bridge.spin(args.duration_s)


if __name__ == "__main__":
    raise SystemExit(main())
