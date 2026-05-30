#!/usr/bin/env python3
"""Play the caller-project DrEureka Go2 MJLab task in a MuJoCo viewer."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
import re
import sys

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import src.tasks  # noqa: F401,E402
import dreureka_go2_mjlab  # noqa: F401,E402
from dreureka_go2_mjlab.env_cfg import TASK_ID  # noqa: E402
from mjlab.envs import ManagerBasedRlEnv  # noqa: E402
from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper  # noqa: E402
from mjlab.tasks.registry import load_env_cfg, load_rl_cfg  # noqa: E402
from mjlab.utils.torch import configure_torch_backends  # noqa: E402
from mjlab.viewer import NativeMujocoViewer, ViserPlayViewer  # noqa: E402


def _checkpoint_sort_key(path: Path) -> int:
  match = re.fullmatch(r"model_(\d+)\.pt", path.name)
  if match is None:
    return -1
  return int(match.group(1))


def _latest_checkpoint(log_dir: Path) -> Path:
  checkpoints = sorted(log_dir.glob("model_*.pt"), key=_checkpoint_sort_key)
  if not checkpoints:
    raise FileNotFoundError(f"No model_*.pt checkpoints found in {log_dir}")
  return checkpoints[-1]


def main() -> None:
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "--log-dir",
    type=Path,
    default=Path("logs/go2_mjlab_dreureka_port/train_1_8_budget/rsl_rl"),
  )
  parser.add_argument("--checkpoint", type=Path, default=None)
  parser.add_argument("--num-envs", type=int, default=1)
  parser.add_argument("--device", default=None)
  parser.add_argument("--viewer", choices=("native", "viser"), default="native")
  parser.add_argument("--no-terminations", action="store_true")
  args = parser.parse_args()

  configure_torch_backends()
  device = args.device or ("cuda:0" if torch.cuda.is_available() else "cpu")
  checkpoint = args.checkpoint or _latest_checkpoint(args.log_dir)

  cfg = load_env_cfg(TASK_ID, play=True)
  rl = load_rl_cfg(TASK_ID)
  cfg.scene.num_envs = args.num_envs
  if args.no_terminations:
    cfg.terminations = {}

  print(f"[INFO] task={TASK_ID}")
  print(f"[INFO] checkpoint={checkpoint}")
  print("[INFO] viewer starts at 1x real time; use viewer speed controls to change it.")

  env = ManagerBasedRlEnv(cfg=cfg, device=device)
  wrapped = RslRlVecEnvWrapper(env, clip_actions=rl.clip_actions)
  runner = MjlabOnPolicyRunner(wrapped, asdict(rl), str(args.log_dir), device)
  runner.load(str(checkpoint), load_cfg={"actor": True}, strict=True, map_location=device)
  policy = runner.get_inference_policy(device=device)

  try:
    if args.viewer == "native":
      NativeMujocoViewer(wrapped, policy).run()
    else:
      ViserPlayViewer(wrapped, policy).run()
  finally:
    env.close()


if __name__ == "__main__":
  main()
