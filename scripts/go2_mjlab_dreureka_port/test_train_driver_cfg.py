#!/usr/bin/env python3
"""Smoke tests for train_driver RL config schema compatibility."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parent))

from train_driver import _runner_cfg_dict  # noqa: E402


@dataclass
class PolicyCfg:
  actor_hidden_dims: tuple[int, ...] = (512, 256, 128)
  critic_hidden_dims: tuple[int, ...] = (512, 256, 128)
  activation: str = "elu"
  actor_obs_normalization: bool = True
  critic_obs_normalization: bool = True
  init_noise_std: float = 1.0
  noise_std_type: str = "scalar"
  class_name: str = "ActorCritic"


@dataclass
class PolicyRunnerCfg:
  policy: PolicyCfg = field(default_factory=PolicyCfg)
  algorithm: dict = field(default_factory=dict)


def test_policy_schema_passthrough() -> None:
  cfg = _runner_cfg_dict(PolicyRunnerCfg())
  assert cfg["policy"]["class_name"] == "ActorCritic"
  assert cfg["policy"]["actor_hidden_dims"] == (512, 256, 128)
  assert cfg["policy"]["critic_hidden_dims"] == (512, 256, 128)
  assert "actor" not in cfg
  assert "critic" not in cfg


if __name__ == "__main__":
  test_policy_schema_passthrough()
  print("ok")
