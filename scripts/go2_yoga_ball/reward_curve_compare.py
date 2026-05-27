#!/usr/bin/env python3
"""Compare Go1 pretrained reward curve with the current 1/8-budget train run."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "artifacts" / "go2_yoga_ball"
PRETRAINED_LOG = (
    ROOT
    / "thirdparties"
    / "DrEureka"
    / "globe_walking"
    / "runs"
    / "globe_walking"
    / "dr_eureka_best"
    / "outputs.log"
)
SELECTED_RUN_FILE = ROOT / "artifacts" / "go1_yoga_ball" / "default_train_selected_run.txt"


METRICS = {
    "balance": "train/episode/rew balance/mean",
    "height": "train/episode/rew height/mean",
    "large_actions": "train/episode/rew penalize large actions/mean",
    "smooth_actions": "train/episode/rew smooth actions/mean",
    "total": "train/episode/rew total/mean",
    "success": "train/episode/rew success/mean",
    "episode_length": "train/episode/episode length/mean",
    "elapsed_s": "time elapsed/mean",
    "timesteps": "timesteps",
    "iteration": "iterations",
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def parse_training_log(path: Path) -> list[dict[str, float]]:
    ansi = re.compile(r"\x1b\[[0-9;]*m")
    metric_line = re.compile(r"│\s*([^│]+?)\s*│\s*([-+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))\s*│")
    current: dict[str, float] = {}
    rows: list[dict[str, float]] = []
    text = ansi.sub("", path.read_text(errors="ignore"))
    for line in text.splitlines():
        match = metric_line.search(line)
        if not match:
            continue
        name = " ".join(match.group(1).split())
        value = float(match.group(2))
        current[name] = value
        if name == METRICS["iteration"]:
            rows.append({key: current[source] for key, source in METRICS.items() if source in current})
            current = {}
    return rows


def nearest_by_timestep(rows: list[dict[str, float]], timestep: float) -> dict[str, float]:
    return min(rows, key=lambda row: abs(row.get("timesteps", 0.0) - timestep))


def best_by(rows: list[dict[str, float]], key: str) -> dict[str, float]:
    return max((row for row in rows if key in row), key=lambda row: row[key])


def write_curve_csv(path: Path, pretrained: list[dict[str, float]], train_1_8: list[dict[str, float]]) -> None:
    fields = [
        "series",
        "iteration",
        "timesteps",
        "elapsed_s",
        "total",
        "success",
        "episode_length",
        "balance",
        "height",
        "large_actions",
        "smooth_actions",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for series, rows in [("go1_pretrained", pretrained), ("go1_train_1_8_budget", train_1_8)]:
            for row in rows:
                out = {field: row.get(field, "") for field in fields}
                out["series"] = series
                writer.writerow(out)


def polyline(points: list[tuple[float, float]], *, x_max: float, y_min: float, y_max: float) -> str:
    width = 900
    height = 420
    left = 70
    top = 30
    plot_w = width - 110
    plot_h = height - 90
    coords = []
    for x, y in points:
        px = left + (x / x_max) * plot_w if x_max > 0 else left
        py = top + (1.0 - ((y - y_min) / (y_max - y_min))) * plot_h if y_max > y_min else top
        coords.append(f"{px:.1f},{py:.1f}")
    return " ".join(coords)


def write_svg(path: Path, pretrained: list[dict[str, float]], train_1_8: list[dict[str, float]]) -> None:
    rows = [row for row in pretrained + train_1_8 if "total" in row and "timesteps" in row]
    x_max = max(row["timesteps"] for row in rows)
    y_min = min(row["total"] for row in rows)
    y_max = max(row["total"] for row in rows)
    pre_points = [(row["timesteps"], row["total"]) for row in pretrained if "total" in row]
    train_points = [(row["timesteps"], row["total"]) for row in train_1_8 if "total" in row]
    selected_end = train_points[-1][0] if train_points else 0.0
    selected_x = 70 + (selected_end / x_max) * (900 - 110)
    text = f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="420" viewBox="0 0 900 420">
  <rect width="900" height="420" fill="white"/>
  <text x="70" y="22" font-family="monospace" font-size="16">Go1 pretrained vs 1/8-budget train reward curve (x = logged global timesteps)</text>
  <line x1="70" y1="360" x2="860" y2="360" stroke="#222"/>
  <line x1="70" y1="30" x2="70" y2="360" stroke="#222"/>
  <line x1="{selected_x:.1f}" y1="30" x2="{selected_x:.1f}" y2="360" stroke="#999" stroke-dasharray="5 5"/>
  <text x="{selected_x + 5:.1f}" y="48" font-family="monospace" font-size="12" fill="#555">1/8 run ends</text>
  <polyline fill="none" stroke="#1f77b4" stroke-width="2" points="{polyline(pre_points, x_max=x_max, y_min=y_min, y_max=y_max)}"/>
  <polyline fill="none" stroke="#d62728" stroke-width="2" points="{polyline(train_points, x_max=x_max, y_min=y_min, y_max=y_max)}"/>
  <text x="100" y="390" font-family="monospace" font-size="13" fill="#1f77b4">blue: pretrained</text>
  <text x="300" y="390" font-family="monospace" font-size="13" fill="#d62728">red: 1/8-budget train</text>
  <text x="70" y="377" font-family="monospace" font-size="11">{y_min:.1f}</text>
  <text x="70" y="42" font-family="monospace" font-size="11">{y_max:.1f}</text>
</svg>
"""
    path.write_text(text, encoding="utf-8")


def compact(row: dict[str, float] | None) -> dict[str, float | None]:
    if row is None:
        return {}
    return {key: row.get(key) for key in ["iteration", "timesteps", "elapsed_s", "total", "success", "episode_length"]}


def main() -> int:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    selected_run = Path(SELECTED_RUN_FILE.read_text(encoding="utf-8").strip())
    selected_log = selected_run / "outputs.log"
    pretrained = parse_training_log(PRETRAINED_LOG)
    train_1_8 = parse_training_log(selected_log)
    if not pretrained or not train_1_8:
        raise RuntimeError("missing parsed training rows")

    selected_final = train_1_8[-1]
    pretrained_at_selected_budget = nearest_by_timestep(pretrained, selected_final["timesteps"])
    pretrained_final = pretrained[-1]
    summary: dict[str, Any] = {
        "ok": True,
        "pretrained_log": rel(PRETRAINED_LOG),
        "train_1_8_log": rel(selected_log),
        "train_1_8_run": rel(selected_run),
        "curve_csv": rel(ARTIFACT_ROOT / "reward_curve_comparison.csv"),
        "curve_svg": rel(ARTIFACT_ROOT / "reward_curve_total.svg"),
        "interpretation": (
            "The current selected Go1 retrain is treated as 1/8-budget because the pretrained log "
            "records exactly 8x more global timesteps at the same nominal 20k iterations."
        ),
        "rows": {
            "pretrained": len(pretrained),
            "train_1_8_budget": len(train_1_8),
        },
        "final": {
            "pretrained": compact(pretrained_final),
            "train_1_8_budget": compact(selected_final),
            "pretrained_nearest_same_global_timesteps": compact(pretrained_at_selected_budget),
        },
        "best_total": {
            "pretrained": compact(best_by(pretrained, "total")),
            "train_1_8_budget": compact(best_by(train_1_8, "total")),
        },
        "ratios": {
            "final_timestep_ratio_pretrained_over_train": pretrained_final["timesteps"] / selected_final["timesteps"],
            "final_total_train_over_pretrained_same_budget": selected_final.get("total", 0.0)
            / pretrained_at_selected_budget.get("total", 1.0),
            "best_total_train_over_pretrained_best": best_by(train_1_8, "total")["total"] / best_by(pretrained, "total")["total"],
        },
    }

    write_curve_csv(ARTIFACT_ROOT / "reward_curve_comparison.csv", pretrained, train_1_8)
    write_svg(ARTIFACT_ROOT / "reward_curve_total.svg", pretrained, train_1_8)
    (ARTIFACT_ROOT / "reward_curve_comparison.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    md = [
        "# Reward Curve Comparison",
        "",
        f"- pretrained log: `{summary['pretrained_log']}`",
        f"- 1/8-budget train log: `{summary['train_1_8_log']}`",
        f"- CSV: `{summary['curve_csv']}`",
        f"- SVG: `{summary['curve_svg']}`",
        "",
        "## Final Points",
        "",
        f"- pretrained final: `{summary['final']['pretrained']}`",
        f"- 1/8-budget train final: `{summary['final']['train_1_8_budget']}`",
        f"- pretrained nearest same global timesteps: `{summary['final']['pretrained_nearest_same_global_timesteps']}`",
        "",
        "## Ratios",
        "",
        f"- final timestep ratio pretrained/train: `{summary['ratios']['final_timestep_ratio_pretrained_over_train']}`",
        f"- final total reward train / pretrained at same global timesteps: `{summary['ratios']['final_total_train_over_pretrained_same_budget']}`",
        f"- best total reward train / pretrained best: `{summary['ratios']['best_total_train_over_pretrained_best']}`",
        "",
        "## Interpretation",
        "",
        summary["interpretation"],
    ]
    (ARTIFACT_ROOT / "reward_curve_comparison.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
