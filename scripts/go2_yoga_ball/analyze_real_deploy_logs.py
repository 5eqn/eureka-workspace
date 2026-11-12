#!/usr/bin/env python3
"""Summarize Go2 deploy logs and compare a real-DDS run against a safe baseline."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_events(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        first = next(reader, None)
        if first is None:
            return rows
        remaining = list(reader)
        if first and first[0] == "event":
            raw_rows = remaining
        else:
            raw_rows = [first, *remaining]
        for raw in raw_rows:
            if not raw:
                continue
            row = {
                "event": raw[0],
                "monotonic_s": raw[1] if len(raw) > 1 else "",
                "wall_time_s": raw[2] if len(raw) > 2 else "",
                "detail": raw[3] if len(raw) > 3 else "",
            }
            if len(raw) >= 6:
                row["sim_time_s"] = raw[3]
                row["support_active"] = raw[4]
                row["detail"] = raw[5]
            rows.append(row)
    return rows


def float_values(rows: list[dict[str, str]], key: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        raw = row.get(key, "")
        if raw == "":
            continue
        values.append(float(raw))
    return values


def summarize_series(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "avg": None, "min": None, "max": None}
    return {
        "count": len(values),
        "avg": mean(values),
        "min": min(values),
        "max": max(values),
    }


def summarize_gap_series(values: list[float], *, threshold: float) -> dict[str, object]:
    summary = summarize_series(values)
    if not values:
        summary["gap_count"] = 0
        summary["gap_threshold_s"] = threshold
        summary["gap_examples"] = []
        return summary
    gap_examples = [(index, gap) for index, gap in enumerate(values) if gap > threshold][:10]
    summary["gap_count"] = sum(1 for gap in values if gap > threshold)
    summary["gap_threshold_s"] = threshold
    summary["gap_examples"] = gap_examples
    return summary


def contiguous_ranges(indices: list[int]) -> list[list[int]]:
    if not indices:
        return []
    ranges: list[list[int]] = []
    start = indices[0]
    prev = indices[0]
    for index in indices[1:]:
        if index == prev + 1:
            prev = index
            continue
        ranges.append([start, prev])
        start = index
        prev = index
    ranges.append([start, prev])
    return ranges


def summarize_log_dir(log_dir: Path) -> dict[str, object]:
    events = read_events(log_dir / "events.csv")
    policy_rows = read_csv(log_dir / "policy_timing.csv")
    bridge_command_rows = read_csv(log_dir / "bridge_commands.csv")
    bridge_lowstate_rows = read_csv(log_dir / "bridge_lowstate.csv")

    loop_periods = float_values(policy_rows, "loop_period_s")
    inference_latencies = float_values(policy_rows, "inference_latency_s")
    action_max_abs = float_values(policy_rows, "action_max_abs")

    command_times = float_values(bridge_command_rows, "monotonic_s")
    command_intervals = [b - a for a, b in zip(command_times, command_times[1:])]

    lowstate_times = float_values(bridge_lowstate_rows, "monotonic_s")
    lowstate_intervals = [b - a for a, b in zip(lowstate_times, lowstate_times[1:])]

    slow_indices = [index for index, value in enumerate(inference_latencies) if value >= 0.02]
    slow_clusters = contiguous_ranges(slow_indices)

    first_event: dict[str, float] = {}
    for row in events:
        event = row.get("event", "")
        if event and event not in first_event:
            first_event[event] = float(row["monotonic_s"])

    return {
        "log_dir": str(log_dir),
        "events": {
            "count": len(events),
            "first_monotonic_s": first_event,
        },
        "policy": {
            "steps": len(policy_rows),
            "loop_period_s": summarize_series(loop_periods),
            "inference_latency_s": {
                **summarize_series(inference_latencies),
                "bins": {
                    "<1ms": sum(1 for value in inference_latencies if value < 0.001),
                    "1-10ms": sum(1 for value in inference_latencies if 0.001 <= value < 0.01),
                    "10-20ms": sum(1 for value in inference_latencies if 0.01 <= value < 0.02),
                    ">=20ms": sum(1 for value in inference_latencies if value >= 0.02),
                },
                "slow_clusters": slow_clusters[:20],
            },
            "action_max_abs": summarize_series(action_max_abs),
        },
        "bridge_commands": {
            "count": len(bridge_command_rows),
            "first_monotonic_s": command_times[0] if command_times else None,
            "last_monotonic_s": command_times[-1] if command_times else None,
            "interval_s": summarize_series(command_intervals),
        },
        "bridge_lowstate": {
            "count": len(bridge_lowstate_rows),
            "interval_s": summarize_gap_series(lowstate_intervals, threshold=0.005),
        },
    }


def compare_summaries(primary: dict[str, object], baseline: dict[str, object]) -> dict[str, object]:
    primary_policy = primary["policy"]  # type: ignore[index]
    baseline_policy = baseline["policy"]  # type: ignore[index]
    primary_inf = primary_policy["inference_latency_s"]  # type: ignore[index]
    baseline_inf = baseline_policy["inference_latency_s"]  # type: ignore[index]
    primary_low = primary["bridge_lowstate"]  # type: ignore[index]
    baseline_low = baseline["bridge_lowstate"]  # type: ignore[index]
    return {
        "policy_step_delta": primary_policy["steps"] - baseline_policy["steps"],  # type: ignore[operator]
        "avg_loop_period_delta_s": primary_policy["loop_period_s"]["avg"] - baseline_policy["loop_period_s"]["avg"],  # type: ignore[index,operator]
        "avg_inference_latency_delta_s": primary_inf["avg"] - baseline_inf["avg"],  # type: ignore[index,operator]
        "slow_inference_delta": primary_inf["bins"][">=20ms"] - baseline_inf["bins"][">=20ms"],  # type: ignore[index,operator]
        "lowstate_gap_delta": primary_low["interval_s"]["gap_count"] - baseline_low["interval_s"]["gap_count"],  # type: ignore[index,operator]
    }


def format_seconds(value: float | int | None) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "n/a"
    return f"{float(value):.6f}"


def render_text(summary: dict[str, object], baseline: dict[str, object] | None) -> str:
    policy = summary["policy"]  # type: ignore[index]
    bridge_commands = summary["bridge_commands"]  # type: ignore[index]
    bridge_lowstate = summary["bridge_lowstate"]  # type: ignore[index]
    policy_inf = policy["inference_latency_s"]  # type: ignore[index]
    policy_loop = policy["loop_period_s"]  # type: ignore[index]
    cmd_interval = bridge_commands["interval_s"]  # type: ignore[index]
    low_interval = bridge_lowstate["interval_s"]  # type: ignore[index]

    lines = [
        f"log_dir: {summary['log_dir']}",
        f"policy steps: {policy['steps']}",
        (
            "policy loop period (s): "
            f"avg={format_seconds(policy_loop['avg'])} "
            f"min={format_seconds(policy_loop['min'])} "
            f"max={format_seconds(policy_loop['max'])}"
        ),
        (
            "policy inference latency (s): "
            f"avg={format_seconds(policy_inf['avg'])} "
            f"min={format_seconds(policy_inf['min'])} "
            f"max={format_seconds(policy_inf['max'])}"
        ),
        f"policy inference bins: {json.dumps(policy_inf['bins'], sort_keys=True)}",
        f"policy slow clusters: {json.dumps(policy_inf['slow_clusters'])}",
        (
            "bridge commands: "
            f"count={bridge_commands['count']} "
            f"first={format_seconds(bridge_commands['first_monotonic_s'])} "
            f"last={format_seconds(bridge_commands['last_monotonic_s'])} "
            f"avg_interval={format_seconds(cmd_interval['avg'])}"
        ),
        (
            "bridge lowstate: "
            f"count={bridge_lowstate['count']} "
            f"avg_interval={format_seconds(low_interval['avg'])} "
            f"gap_count>{format_seconds(low_interval['gap_threshold_s'])}={low_interval['gap_count']}"
        ),
    ]
    if baseline is not None:
        lines.append(f"comparison: {json.dumps(compare_summaries(summary, baseline), sort_keys=True)}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-dir", required=True, type=Path)
    parser.add_argument("--compare-log-dir", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()

    summary = summarize_log_dir(args.log_dir)
    baseline = summarize_log_dir(args.compare_log_dir) if args.compare_log_dir else None

    if args.format == "json":
        payload: dict[str, object] = {"summary": summary}
        if baseline is not None:
            payload["baseline"] = baseline
            payload["comparison"] = compare_summaries(summary, baseline)
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_text(summary, baseline), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
