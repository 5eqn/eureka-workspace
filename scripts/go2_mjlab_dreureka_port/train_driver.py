#!/usr/bin/env python3
"""Train the caller-project DrEureka Go2 MJLab task."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import logging
import os
from pathlib import Path
import sys

import torch
from rsl_rl.runners import OnPolicyRunner

sys.path.insert(0, str(Path(__file__).resolve().parent))

import dreureka_go2_mjlab  # noqa: F401,E402
from dreureka_go2_mjlab.env_cfg import TASK_ID  # noqa: E402
from mjlab.envs import ManagerBasedRlEnv  # noqa: E402
from mjlab.rl import RslRlVecEnvWrapper  # noqa: E402
from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls  # noqa: E402
from mjlab.utils.gpu import select_gpus  # noqa: E402
from mjlab.utils.torch import configure_torch_backends  # noqa: E402


def _runner_cfg_dict(rl) -> dict:
  cfg = asdict(rl)
  if "actor" in cfg and "critic" in cfg:
    return cfg

  policy = cfg.pop("policy")
  distribution_cfg = {
    "class_name": "GaussianDistribution",
    "init_std": policy.pop("init_noise_std", 1.0),
    "std_type": policy.pop("noise_std_type", "scalar"),
  }
  cfg["actor"] = {
    "class_name": "MLPModel",
    "hidden_dims": policy.pop("actor_hidden_dims"),
    "activation": policy["activation"],
    "obs_normalization": policy.pop("actor_obs_normalization", False),
    "distribution_cfg": distribution_cfg,
  }
  cfg["critic"] = {
    "class_name": "MLPModel",
    "hidden_dims": policy.pop("critic_hidden_dims"),
    "activation": policy["activation"],
    "obs_normalization": policy.pop("critic_obs_normalization", False),
  }
  cfg["algorithm"].setdefault("share_cnn_encoders", False)
  cfg.setdefault("multi_gpu", None)
  return cfg


def _device_and_seed(seed: int, selected_gpus: list[int] | None) -> tuple[str, int, int]:
  local_rank = int(os.environ.get("LOCAL_RANK", "0"))
  rank = int(os.environ.get("RANK", "0"))
  musa_visible = os.environ.get("MUSA_VISIBLE_DEVICES", "")
  if musa_visible:
    os.environ["MUJOCO_EGL_DEVICE_ID"] = str(local_rank)
    local_gpu_id = (
      selected_gpus[local_rank]
      if selected_gpus is not None
      else local_rank
    )
    return f"musa:{local_gpu_id}", seed + rank, rank
  if torch.cuda.is_available():
    return f"cuda:{local_rank}", seed + rank, rank
  return "cpu", seed, 0


def _run_train(args: argparse.Namespace, selected_gpus: list[int] | None = None) -> None:
  import dreureka_go2_mjlab  # noqa: F401,PLC0415

  configure_torch_backends()
  cfg = load_env_cfg(TASK_ID)
  rl = load_rl_cfg(TASK_ID)
  cfg.scene.num_envs = args.num_envs
  device, seed, rank = _device_and_seed(args.seed, selected_gpus)
  cfg.seed = seed
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
  rl.seed = seed

  launch = {
    "task_id": TASK_ID,
    "log_dir": args.log_dir,
    "num_envs": args.num_envs,
    "iterations": args.iterations,
    "steps_per_env": args.steps_per_env,
    "save_interval": args.save_interval,
    "seed": seed,
    "rank": rank,
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
    "terrain_runtime": "mjlab_native_20x20_5m_random_rough_tiles_no_terrain_material_dr",
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
  if rank == 0:
    launch_path = Path(args.launch_json)
    launch_path.parent.mkdir(parents=True, exist_ok=True)
    launch_path.write_text(json.dumps(launch, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"launch": launch}, sort_keys=True), flush=True)

  env = ManagerBasedRlEnv(cfg=cfg, device=device)
  wrapped = RslRlVecEnvWrapper(env, clip_actions=rl.clip_actions)
  runner_cls = load_runner_cls(TASK_ID)
  if runner_cls is None:
    runner_cls = OnPolicyRunner
  runner = runner_cls(wrapped, _runner_cfg_dict(rl), args.log_dir, device)
  runner.add_git_repo_to_log(__file__)
  runner.learn(num_learning_iterations=args.iterations, init_at_random_ep_len=True)
  env.close()


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
  parser.add_argument("--torchrunx-log-dir", default=None)
  args = parser.parse_args()

  selected_gpus, num_gpus = select_gpus("all")
  if "MUSA_VISIBLE_DEVICES" in os.environ:
    os.environ["MUSA_VISIBLE_DEVICES"] = (
      "" if selected_gpus is None else ",".join(map(str, selected_gpus))
    )
    os.environ["MUJOCO_RENDERER"] = ""
  if num_gpus <= 1:
    _run_train(args, selected_gpus)
    return

  import torchrunx

  logging.basicConfig(level=logging.INFO)
  if "TORCHRUNX_LOG_DIR" not in os.environ:
    os.environ["TORCHRUNX_LOG_DIR"] = (
      args.torchrunx_log_dir
      if args.torchrunx_log_dir is not None
      else str(Path(args.log_dir) / "torchrunx")
    )
  print(f"[INFO] Launching training with {num_gpus} GPUs", flush=True)
  torchrunx.Launcher(
    hostnames=["localhost"],
    workers_per_host=num_gpus,
    backend=None,
    copy_env_vars=torchrunx.DEFAULT_ENV_VARS_FOR_COPY + ("MUJOCO*", "MCCL*",),
  ).run(_run_train, args, selected_gpus)


if __name__ == "__main__":
  main()
