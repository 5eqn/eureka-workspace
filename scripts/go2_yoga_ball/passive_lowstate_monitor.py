#!/usr/bin/env python3
"""Passively monitor Unitree Go2 DDS lowstate frequency without publishing commands."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean
import threading
import time

from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelSubscriber
from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowState_


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    if p <= 0:
        return min(values)
    if p >= 100:
        return max(values)
    ordered = sorted(values)
    index = (len(ordered) - 1) * (p / 100.0)
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    weight = index - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


class LowStateMonitor:
    def __init__(self, *, out_dir: Path, gap_threshold_s: float) -> None:
        self.out_dir = out_dir
        self.gap_threshold_s = gap_threshold_s
        self.start_mono = time.monotonic()
        self.lock = threading.Lock()
        self.packet_count = 0
        self.first_packet_mono: float | None = None
        self.last_packet_mono: float | None = None
        self.last_callback_mono: float | None = None
        self.gap_count = 0
        self.max_gap_s = 0.0
        self.accepting = True
        self.csv_path = out_dir / "packets.csv"
        self.csv_file = self.csv_path.open("w", newline="", encoding="utf-8")
        self.writer = csv.DictWriter(
            self.csv_file,
            fieldnames=[
                "count",
                "monotonic_s",
                "wall_time_s",
                "interval_s",
                "q0",
                "dq0",
                "tau0",
                "quat_w",
                "quat_x",
                "quat_y",
                "quat_z",
                "gyro_x",
                "gyro_y",
                "gyro_z",
            ],
        )
        self.writer.writeheader()
        self.interval_samples: list[float] = []

    def callback(self, msg: LowState_) -> None:
        now = time.monotonic()
        wall = time.time()
        with self.lock:
            if not self.accepting:
                return
            interval_s = None if self.last_callback_mono is None else now - self.last_callback_mono
            if interval_s is not None:
                self.interval_samples.append(interval_s)
                if interval_s > self.gap_threshold_s:
                    self.gap_count += 1
                self.max_gap_s = max(self.max_gap_s, interval_s)
            self.last_callback_mono = now
            self.packet_count += 1
            if self.first_packet_mono is None:
                self.first_packet_mono = now
            self.last_packet_mono = now
            self.writer.writerow(
                {
                    "count": self.packet_count,
                    "monotonic_s": f"{now - self.start_mono:.6f}",
                    "wall_time_s": f"{wall:.6f}",
                    "interval_s": "" if interval_s is None else f"{interval_s:.9f}",
                    "q0": f"{float(msg.motor_state[0].q):.9f}",
                    "dq0": f"{float(msg.motor_state[0].dq):.9f}",
                    "tau0": f"{float(msg.motor_state[0].tau_est):.9f}",
                    "quat_w": f"{float(msg.imu_state.quaternion[0]):.9f}",
                    "quat_x": f"{float(msg.imu_state.quaternion[1]):.9f}",
                    "quat_y": f"{float(msg.imu_state.quaternion[2]):.9f}",
                    "quat_z": f"{float(msg.imu_state.quaternion[3]):.9f}",
                    "gyro_x": f"{float(msg.imu_state.gyroscope[0]):.9f}",
                    "gyro_y": f"{float(msg.imu_state.gyroscope[1]):.9f}",
                    "gyro_z": f"{float(msg.imu_state.gyroscope[2]):.9f}",
                }
            )
            self.csv_file.flush()

    def summary(
        self,
        *,
        duration_s: float,
        expected_rate_hz: float,
        min_rate_ratio: float,
    ) -> dict[str, object]:
        with self.lock:
            packet_count = self.packet_count
            first_packet_mono = self.first_packet_mono
            last_packet_mono = self.last_packet_mono
            interval_samples = list(self.interval_samples)
            gap_count = self.gap_count
            max_gap_s = self.max_gap_s

        active_window_s = None
        measured_rate_hz = None
        if first_packet_mono is not None and last_packet_mono is not None and last_packet_mono > first_packet_mono:
            active_window_s = last_packet_mono - first_packet_mono
            measured_rate_hz = (packet_count - 1) / active_window_s if packet_count > 1 else None

        duration_rate_hz = packet_count / duration_s if duration_s > 0 else None
        warnings: list[str] = []
        if packet_count == 0:
            warnings.append("no lowstate packets received")
        if measured_rate_hz is not None and measured_rate_hz < expected_rate_hz * min_rate_ratio:
            warnings.append(
                f"measured lowstate rate {measured_rate_hz:.2f} Hz is below "
                f"{min_rate_ratio:.2f}x expected {expected_rate_hz:.2f} Hz"
            )
        if gap_count > 0:
            warnings.append(f"observed {gap_count} inter-packet gaps above {self.gap_threshold_s * 1000.0:.3f} ms")

        return {
            "ok": len(warnings) == 0,
            "warnings": warnings,
            "packet_count": packet_count,
            "requested_duration_s": duration_s,
            "capture_window_s": active_window_s,
            "rate_hz_over_active_window": measured_rate_hz,
            "rate_hz_over_requested_duration": duration_rate_hz,
            "expected_rate_hz": expected_rate_hz,
            "min_rate_ratio": min_rate_ratio,
            "gap_threshold_s": self.gap_threshold_s,
            "gap_count": gap_count,
            "interval_s": {
                "count": len(interval_samples),
                "avg": mean(interval_samples) if interval_samples else None,
                "min": min(interval_samples) if interval_samples else None,
                "p50": percentile(interval_samples, 50.0),
                "p95": percentile(interval_samples, 95.0),
                "p99": percentile(interval_samples, 99.0),
                "max": max_gap_s if interval_samples else None,
            },
            "artifacts": {
                "packets_csv": str(self.csv_path),
            },
        }

    def close(self) -> None:
        self.csv_file.close()

    def freeze(self) -> None:
        with self.lock:
            self.accepting = False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dds-domain", type=int, default=0)
    parser.add_argument("--network-interface", default=None)
    parser.add_argument("--duration-s", type=float, default=20.0)
    parser.add_argument("--expected-rate-hz", type=float, default=500.0)
    parser.add_argument("--min-rate-ratio", type=float, default=0.9)
    parser.add_argument("--gap-threshold-ms", type=float, default=5.0)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    monitor = LowStateMonitor(out_dir=out_dir, gap_threshold_s=args.gap_threshold_ms / 1000.0)

    # Subscriber only: this script never initializes a lowcmd publisher.
    ChannelFactoryInitialize(args.dds_domain, args.network_interface)
    sub = ChannelSubscriber("rt/lowstate", LowState_)
    sub.Init(monitor.callback, 10)

    start = time.monotonic()
    try:
        while time.monotonic() - start < args.duration_s:
            time.sleep(0.1)
    finally:
        monitor.freeze()

    summary = monitor.summary(
        duration_s=args.duration_s,
        expected_rate_hz=args.expected_rate_hz,
        min_rate_ratio=args.min_rate_ratio,
    )
    summary["dds_domain"] = args.dds_domain
    summary["network_interface"] = args.network_interface
    summary["script"] = str(Path(__file__).resolve())
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    monitor.close()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
