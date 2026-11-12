#!/usr/bin/env python3

import argparse
import json
import pickle
import re
import sys
from pathlib import Path


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

ACTIVE_PATHS = (
    "AC_Args",
    "PPO_Args",
    "Cfg.env",
    "Cfg.sensors",
    "Cfg.terrain",
    "Cfg.commands",
    "Cfg.curriculum_thresholds",
    "Cfg.ball",
    "Cfg.domain_rand",
    "Cfg.sim",
    "Cfg.init_state",
    "Cfg.normalization",
    "Cfg.obs_scales",
    "Cfg.noise",
    "Cfg.noise_scales",
    "Cfg.perception",
    "Cfg.robot",
    "Cfg.control",
    "Cfg.asset",
    "Cfg.rewards",
    "Cfg.reward_scales",
    "Cfg.multi_gpu",
    "RunnerArgs",
)

ALLOWED_PREFIXES = (
    "Cfg.robot",
    "Cfg.control",
    "Cfg.asset",
    "Cfg.rewards",
    "Cfg.reward_scales",
    "Cfg.curriculum_thresholds.dribbling_ball_vel",
    "Cfg.multi_gpu",
    "Cfg.domain_rand.ball_radius_range",
    "RunnerArgs.save_interval",
    "RunnerArgs.early_stop_",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def default_stock_run() -> Path:
    return repo_root() / "thirdparties/DrEureka/globe_walking/runs/globe_walking/dr_eureka_best"


def resolve_run_dir(path_str: str) -> Path:
    path = Path(path_str).expanduser().resolve()
    if (path / "parameters.pkl").is_file():
        return path
    if path.name == "train" and path.is_dir():
        runs = sorted(p for p in path.iterdir() if p.is_dir() and (p / "parameters.pkl").is_file())
        if runs:
            return runs[-1]
    train_dir = path / "train"
    if train_dir.is_dir():
        runs = sorted(p for p in train_dir.iterdir() if p.is_dir() and (p / "parameters.pkl").is_file())
        if runs:
            return runs[-1]
    raise FileNotFoundError(f"Could not resolve a run dir from: {path}")


def load_pickle(path: Path):
    with path.open("rb") as handle:
        return pickle.load(handle)


def read_log(path: Path) -> str:
    return ANSI_RE.sub("", path.read_text(errors="replace"))


def get_path(data, dotted: str):
    value = data
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            raise KeyError(dotted)
        value = value[part]
    return value


def diff_values(a, b, path: str):
    diffs = []
    if type(a) is not type(b):
        diffs.append((path, a, b))
        return diffs
    if isinstance(a, dict):
        keys = sorted(set(a) | set(b))
        for key in keys:
            next_path = f"{path}.{key}"
            if key not in a:
                diffs.append((next_path, "<missing>", b[key]))
            elif key not in b:
                diffs.append((next_path, a[key], "<missing>"))
            else:
                diffs.extend(diff_values(a[key], b[key], next_path))
        return diffs
    if isinstance(a, list):
        if len(a) != len(b):
            diffs.append((path, a, b))
            return diffs
        for index, (left, right) in enumerate(zip(a, b)):
            diffs.extend(diff_values(left, right, f"{path}[{index}]"))
        return diffs
    if isinstance(a, tuple):
        if len(a) != len(b):
            diffs.append((path, a, b))
            return diffs
        for index, (left, right) in enumerate(zip(a, b)):
            diffs.extend(diff_values(left, right, f"{path}[{index}]"))
        return diffs
    if a != b:
        diffs.append((path, a, b))
    return diffs


def is_allowed(path: str) -> bool:
    return any(path == prefix or path.startswith(prefix) for prefix in ALLOWED_PREFIXES)


def parse_checkpoint_summary(run_dir: Path):
    log_path = run_dir / "outputs.log"
    if not log_path.is_file():
        return None
    text = read_log(log_path)
    rewards = [float(value) for value in re.findall(r"train/episode/rew total/mean\s*│\s*([0-9.eE+-]+)", text)]
    lengths = [float(value) for value in re.findall(r"train/episode/episode length/mean\s*│\s*([0-9.eE+-]+)", text)]
    iterations = [int(value) for value in re.findall(r"│\s+iterations\s+│\s+([0-9]+)\s+│", text)]
    if not rewards or len(rewards) != len(lengths) or len(rewards) != len(iterations):
        return {
            "best_saved": None,
            "best_overall": None,
            "last_logged": None,
            "early_stop_triggered": "Early stopping:" in text,
            "parse_warning": "Could not align reward history rows in outputs.log.",
        }

    rows = list(zip(iterations, rewards, lengths))
    ckpt_rows = []
    ckpt_dir = run_dir / "checkpoints"
    if ckpt_dir.is_dir():
        for ckpt in sorted(ckpt_dir.glob("ac_weights_*.pt")):
            if ckpt.name == "ac_weights_last.pt":
                continue
            try:
                iteration = int(ckpt.stem.split("_")[-1])
            except ValueError:
                continue
            for row in rows:
                if row[0] == iteration:
                    ckpt_rows.append(
                        {
                            "checkpoint": ckpt.name,
                            "iteration": row[0],
                            "reward": row[1],
                            "episode_length": row[2],
                        }
                    )
                    break

    best_saved = max(ckpt_rows, key=lambda item: (item["reward"], item["episode_length"])) if ckpt_rows else None
    best_overall_row = max(rows, key=lambda item: (item[1], item[2]))
    last_row = rows[-1]
    return {
        "best_saved": best_saved,
        "best_overall": {
            "iteration": best_overall_row[0],
            "reward": best_overall_row[1],
            "episode_length": best_overall_row[2],
        },
        "last_logged": {
            "iteration": last_row[0],
            "reward": last_row[1],
            "episode_length": last_row[2],
        },
        "early_stop_triggered": "Early stopping:" in text,
        "parse_warning": None,
    }


def main():
    parser = argparse.ArgumentParser(description="Audit a DrEureka training run against the built-in pretrained contract.")
    parser.add_argument("--run", required=True, help="Run dir, train dir, or date bucket to audit.")
    parser.add_argument("--stock", default=str(default_stock_run()), help="Stock pretrained run dir.")
    parser.add_argument("--show-allowed", action="store_true", help="Print allowed diffs as well as unexpected diffs.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    run_dir = resolve_run_dir(args.run)
    stock_dir = resolve_run_dir(args.stock)

    run_params = load_pickle(run_dir / "parameters.pkl")
    stock_params = load_pickle(stock_dir / "parameters.pkl")

    all_diffs = []
    for dotted in ACTIVE_PATHS:
        all_diffs.extend(diff_values(get_path(stock_params, dotted), get_path(run_params, dotted), dotted))

    allowed = []
    unexpected = []
    for path, stock_value, run_value in all_diffs:
        item = {"path": path, "stock": stock_value, "run": run_value}
        if is_allowed(path):
            allowed.append(item)
        else:
            unexpected.append(item)

    checkpoint_summary = parse_checkpoint_summary(run_dir)
    result = {
        "run_dir": str(run_dir),
        "stock_dir": str(stock_dir),
        "best_saved": checkpoint_summary["best_saved"],
        "best_overall": checkpoint_summary["best_overall"],
        "last_logged": checkpoint_summary["last_logged"],
        "early_stop_triggered": checkpoint_summary["early_stop_triggered"],
        "parse_warning": checkpoint_summary["parse_warning"],
        "allowed_diff_count": len(allowed),
        "unexpected_diff_count": len(unexpected),
        "allowed_diffs": allowed if args.show_allowed or args.json else [],
        "unexpected_diffs": unexpected,
        "ok": len(unexpected) == 0 and not checkpoint_summary["early_stop_triggered"],
    }

    if args.json:
        json.dump(result, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        sys.exit(0 if result["ok"] else 1)

    print(f"run_dir: {result['run_dir']}")
    print(f"stock_dir: {result['stock_dir']}")
    if result["best_saved"] is None:
        print("best_saved_checkpoint: <not resolved>")
    else:
        best = result["best_saved"]
        print(
            "best_saved_checkpoint: "
            f"{best['checkpoint']} (iteration={best['iteration']}, reward={best['reward']:.3f}, "
            f"episode_length={best['episode_length']:.3f})"
        )
    if result["best_overall"] is not None:
        best = result["best_overall"]
        print(
            "best_overall_logged: "
            f"iteration={best['iteration']}, reward={best['reward']:.3f}, episode_length={best['episode_length']:.3f}"
        )
    if result["last_logged"] is not None:
        last = result["last_logged"]
        print(
            "last_logged: "
            f"iteration={last['iteration']}, reward={last['reward']:.3f}, episode_length={last['episode_length']:.3f}"
        )
    if result["parse_warning"]:
        print(f"parse_warning: {result['parse_warning']}")
    print(f"early_stop_triggered: {result['early_stop_triggered']}")
    print(f"allowed_diff_count: {result['allowed_diff_count']}")
    print(f"unexpected_diff_count: {result['unexpected_diff_count']}")

    if args.show_allowed and result["allowed_diffs"]:
        print("\nallowed_diffs:")
        for item in result["allowed_diffs"]:
            print(f"  - {item['path']}: {item['stock']} -> {item['run']}")

    if result["unexpected_diffs"]:
        print("\nunexpected_diffs:")
        for item in result["unexpected_diffs"]:
            print(f"  - {item['path']}: {item['stock']} -> {item['run']}")

    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
