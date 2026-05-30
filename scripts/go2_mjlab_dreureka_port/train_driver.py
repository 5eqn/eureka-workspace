#!/usr/bin/env python3
"""Train the caller-project DrEureka Go2 MJLab task."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

import mujoco
import torch

mujoco.mjMAXCONPAIR = 512

sys.path.insert(0, str(Path(__file__).resolve().parent))

import src.tasks  # noqa: F401,E402
import dreureka_go2_mjlab  # noqa: F401,E402
from dreureka_go2_mjlab.env_cfg import TASK_ID  # noqa: E402
from mjlab.envs import ManagerBasedRlEnv  # noqa: E402
from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper  # noqa: E402
from mjlab.tasks.registry import load_env_cfg, load_rl_cfg  # noqa: E402
from mjlab.utils.torch import configure_torch_backends  # noqa: E402


def main() -> None:
  parser = argparse.ArgumentParser()
  parser.add_argument("--log-dir", required=True)
  parser.add_argument("--num-envs", type=int, required=True)
  parser.add_argument("--iterations", type=int, required=True)
  parser.add_argument("--steps-per-env", type=int, default=24)
  parser.add_argument("--save-interval", type=int, default=1000)
  parser.add_argument("--run-name", default="")
  parser.add_argument("--terrain-rows", type=int, default=None)
  parser.add_argument("--terrain-cols", type=int, default=None)
  parser.add_argument("--seed", type=int, default=42)
  parser.add_argument("--launch-json", required=True)
  args = parser.parse_args()

  configure_torch_backends()
  cfg = load_env_cfg(TASK_ID)
  rl = load_rl_cfg(TASK_ID)
  cfg.scene.num_envs = args.num_envs
  cfg.seed = args.seed
  if args.terrain_rows is not None and cfg.scene.terrain.terrain_generator is not None:
    cfg.scene.terrain.terrain_generator.num_rows = args.terrain_rows
  if args.terrain_cols is not None and cfg.scene.terrain.terrain_generator is not None:
    cfg.scene.terrain.terrain_generator.num_cols = args.terrain_cols
  actuators = cfg.scene.entities["robot"].articulation.actuators
  actuator_gains = {
    actuator.target_names_expr[0]: {
      "stiffness": actuator.stiffness,
      "damping": actuator.damping,
    }
    for actuator in actuators
  }
  rl.max_iterations = args.iterations
  rl.num_steps_per_env = args.steps_per_env
  rl.save_interval = args.save_interval
  rl.run_name = args.run_name
  rl.logger = "tensorboard"
  rl.upload_model = False
  rl.seed = args.seed

  device = "cuda:0" if torch.cuda.is_available() else "cpu"
  launch = {
    "task_id": TASK_ID,
    "log_dir": args.log_dir,
    "num_envs": args.num_envs,
    "iterations": args.iterations,
    "steps_per_env": args.steps_per_env,
    "save_interval": args.save_interval,
    "seed": args.seed,
    "device": device,
    "terrain_rows": (
      cfg.scene.terrain.terrain_generator.num_rows
      if cfg.scene.terrain.terrain_generator is not None
      else args.terrain_rows
    ),
    "terrain_cols": (
      cfg.scene.terrain.terrain_generator.num_cols
      if cfg.scene.terrain.terrain_generator is not None
      else args.terrain_cols
    ),
    "terrain_size": (
      list(cfg.scene.terrain.terrain_generator.size)
      if cfg.scene.terrain.terrain_generator is not None
      else None
    ),
    "terrain_runtime": "mjlab_isaac_perlin_hfield_exact_samples_mjmaxconpair_512",
    "mujoco_mjmaxconpair": mujoco.mjMAXCONPAIR,
    "actuator_gains": actuator_gains,
    "domain_rand_profile": "pretrained",
    "episode_length_s": cfg.episode_length_s,
    "decimation": cfg.decimation,
    "sim": {
      "nconmax": cfg.sim.nconmax,
      "njmax": cfg.sim.njmax,
      "contact_sensor_maxmatch": cfg.sim.contact_sensor_maxmatch,
      "ccd_iterations": cfg.sim.mujoco.ccd_iterations,
    },
  }
  launch_path = Path(args.launch_json)
  launch_path.parent.mkdir(parents=True, exist_ok=True)
  launch_path.write_text(json.dumps(launch, indent=2, sort_keys=True) + "\n")
  print(json.dumps({"launch": launch}, sort_keys=True), flush=True)

  env = ManagerBasedRlEnv(cfg=cfg, device=device)
  wrapped = RslRlVecEnvWrapper(env, clip_actions=rl.clip_actions)
  runner = MjlabOnPolicyRunner(wrapped, asdict(rl), args.log_dir, device)
  runner.add_git_repo_to_log(__file__)
  runner.learn(num_learning_iterations=args.iterations, init_at_random_ep_len=True)
  env.close()


if __name__ == "__main__":
  main()
