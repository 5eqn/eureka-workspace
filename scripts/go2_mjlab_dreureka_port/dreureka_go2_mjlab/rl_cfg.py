"""RSL-RL configuration for the DrEureka Go2 MJLab reproduction."""

from __future__ import annotations

from mjlab.rl import (
  RslRlOnPolicyRunnerCfg,
  RslRlPpoActorCriticCfg,
  RslRlPpoAlgorithmCfg,
)


def make_dreureka_go2_ppo_runner_cfg() -> RslRlOnPolicyRunnerCfg:
  return RslRlOnPolicyRunnerCfg(
    policy=RslRlPpoActorCriticCfg(
      actor_hidden_dims=(512, 256, 128),
      critic_hidden_dims=(512, 256, 128),
      activation="elu",
      actor_obs_normalization=True,
      critic_obs_normalization=True,
      init_noise_std=1.0,
      noise_std_type="scalar",
    ),
    algorithm=RslRlPpoAlgorithmCfg(
      value_loss_coef=1.0,
      use_clipped_value_loss=True,
      clip_param=0.2,
      entropy_coef=0.01,
      num_learning_epochs=5,
      num_mini_batches=4,
      learning_rate=1.0e-3,
      schedule="adaptive",
      gamma=0.99,
      lam=0.95,
      desired_kl=0.01,
      max_grad_norm=1.0,
    ),
    experiment_name="dreureka_go2_yoga_ball_mjlab",
    run_name="baseline",
    obs_groups={"policy": ("actor",), "critic": ("actor", "critic")},
    logger="tensorboard",
    save_interval=1000,
    num_steps_per_env=24,
    max_iterations=20000,
  )
