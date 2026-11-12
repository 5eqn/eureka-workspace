---
name: dr-eureka-training-audit
description: Verify whether a DrEureka globe_walking training run matches the built-in pretrained training contract using saved run artifacts first (`parameters.pkl`, `outputs.log`, checkpoint ladder) and live source or container state only when a fresh launch needs diagnosis. Use when selecting the best saved checkpoint, deciding whether a run is faithful enough to proceed to Isaac playback or MuJoCo Sim2Sim, or checking whether a newly launched run actually picked up the intended spawn and reset settings. This skill treats robot, control, asset, reward, ball-size, save-interval, early-stop-config, and parallelism differences as allowed, but flags unexpected active env, domain-rand, and spawn-reset drift or an actual early-stop event.
---

# DrEureka Training Audit

## Workflow

1. Identify the run directory to audit.
   - Prefer the newly created date-stamped run under `thirdparties/DrEureka/globe_walking/runs/globe_walking/YYYY-MM-DD/train/...`.
   - Do not use an older historical run to validate a new launch.

2. Start with saved artifacts, not launcher intent.
   - `parameters.pkl` is the ground truth for the applied training config.
   - `outputs.log` is the ground truth for the printed config, reward history, and early-stop events.
   - The launcher script and live container are only for explaining a mismatch after the saved artifacts disagree.

3. Run the checker.

```bash
python .agents/skills/dr-eureka-training-audit/scripts/check_training_parity.py --run <run-dir>
```

   - Add `--show-allowed` to inspect permitted deltas.
   - Add `--json` for machine-readable output.
   - The script also resolves the best saved reward checkpoint from `outputs.log` plus the local checkpoint ladder.

4. Stop/continue rule.
   - If the checker reports unexpected diffs or `early_stop_triggered=true`, stop before playback or Sim2Sim.
   - If only allowed diffs remain, the run is configuration-faithful enough to continue.

5. For a fresh launch that still looks wrong, inspect the live container and then re-check the new saved run dir.

```bash
docker inspect <container> --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'
docker exec <container> bash -lc "sed -n '1,40p' /workspace/thirdparties/DrEureka/globe_walking/go1_gym/envs/go2/go2_config.py"
docker exec <container> bash -lc "sed -n '196,205p' /workspace/thirdparties/DrEureka/globe_walking/scripts/train.py"
```

Then re-run:

```bash
RUN=$(find thirdparties/DrEureka/globe_walking/runs/globe_walking/$(date +%F)/train -maxdepth 1 -mindepth 1 -type d | sort | tail -n 1)
python .agents/skills/dr-eureka-training-audit/scripts/check_training_parity.py --run "$RUN"
```

## Reference

Read [references/parity-rules.md](references/parity-rules.md) when you need the allowed-difference policy, the blocking spawn/reset fields, or the rationale for using saved artifacts over launch scripts.
