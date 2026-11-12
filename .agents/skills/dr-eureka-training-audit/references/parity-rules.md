# Parity Rules

## Ground truth

Use these in order:

1. `parameters.pkl` for the applied training config
2. `outputs.log` for the printed config, reward history, and early-stop events
3. launcher scripts and live container state only to explain why a new run differs

Historical runs do not change after source fixes. A source change only affects newly created date-stamped run directories.

## Allowed differences

These are expected and do not block playback or Sim2Sim by themselves:

- `Cfg.robot.*`
- `Cfg.control.*`
- `Cfg.asset.*`
- `Cfg.rewards.*`
- `Cfg.reward_scales.*`
- `Cfg.curriculum_thresholds.dribbling_ball_vel`
- `Cfg.domain_rand.ball_radius_range`
- `Cfg.multi_gpu`
- `RunnerArgs.save_interval`
- `RunnerArgs.early_stop_*`

Interpretation:

- Robot swap is allowed.
- Actuator or control differences are allowed.
- Go2 asset inheritance differences are allowed.
- Ball size differences are allowed.
- Reward-config differences are allowed.
- Save-interval differences are allowed.
- Early-stop configuration differences are allowed only if early stop did not actually fire.
- Parallelism differences are allowed.

## Blocking differences

Any unexpected difference in the active applied config outside the allowlist blocks the run.

Pay extra attention to spawn and reset settings:

- `Cfg.init_state.pos`
- `Cfg.terrain.x_init_range`
- `Cfg.terrain.y_init_range`
- `Cfg.terrain.x_init_offset`
- `Cfg.terrain.y_init_offset`
- active ball reset settings under `Cfg.ball.*`

An actual early-stop event also blocks the run. Detect it from `outputs.log` containing `Early stopping:`.

## Active surfaces to compare

The active comparison surface is:

- `AC_Args`
- `PPO_Args`
- `Cfg.env`
- `Cfg.sensors`
- `Cfg.terrain`
- `Cfg.commands`
- `Cfg.curriculum_thresholds`
- `Cfg.ball`
- `Cfg.domain_rand`
- `Cfg.sim`
- `Cfg.init_state`
- `Cfg.normalization`
- `Cfg.obs_scales`
- `Cfg.noise`
- `Cfg.noise_scales`
- `Cfg.perception`
- `Cfg.robot`
- `Cfg.control`
- `Cfg.asset`
- `Cfg.rewards`
- `Cfg.reward_scales`
- `Cfg.multi_gpu`
- `RunnerArgs`

Ignore inactive template sections such as `Cfg.env_full`, `Cfg.env_mini`, `Cfg.terrain_full`, `Cfg.terrain_mini`, and inactive domain-rand profiles unless the task explicitly asks for a broader source audit.
