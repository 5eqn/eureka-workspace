#!/usr/bin/env python3
"""Export a non-final DrEureka globe_walking checkpoint to deployable JITs.

`scripts/go1_yoga_ball/deploy_lcm_policy.py::load_policy` hardcodes
`checkpoints/body_latest.jit` + `checkpoints/adaptation_module_latest.jit`,
which the go1_gym training writes only for the *last* checkpoint. To deploy a
specific intermediate checkpoint (e.g. `ac_weights_016000.pt`), this script
rebuilds the two deployable `nn.Sequential`s (`actor_body`, `adaptation_module`)
straight from the checkpoint state_dict and re-exports them as JITs into a
staging deploy dir that `run_sim2sim.sh` can point `RUN` at.

The module structure is reconstructed *from the checkpoint* (Linear layer shapes
and their index positions), so no config guesswork is involved; `load_state_dict
(strict=True)` is a hard gate that fails loudly on any mismatch. A numerical
self-check proves the scripted JITs reproduce the loaded weights.

Runs on the host `go2-mjlab` conda env (needs only torch; the ActorCritic class
is not imported, so isaacgym/params_proto are not required).
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import torch
import torch.nn as nn


def rebuild_sequential(sd: dict, prefix: str) -> nn.Sequential:
    """Rebuild an `nn.Sequential` of Linear/ELU from checkpoint keys.

    The go1_gym ActorCritic lays out both `adaptation_module` and `actor_body`
    as Linear -> activation -> Linear -> ... where activation is ELU (a module
    with no parameters, so it occupies an index with no state_dict entry).
    We read which indices carry a Linear (`.weight`/`.bias`) and infer the
    in/out features from the weight shapes; gaps between Linears are ELU.
    """
    linear: dict[int, tuple[int, int]] = {}
    for key, val in sd.items():
        if not key.startswith(prefix + "."):
            continue
        rest = key[len(prefix) + 1:]
        parts = rest.split(".")
        if len(parts) == 2 and parts[1] == "weight":
            idx = int(parts[0])
            out_f, in_f = val.shape
            linear[idx] = (in_f, out_f)
    if not linear:
        raise ValueError(f"no Linear layers found under prefix {prefix!r}")
    last = max(linear)
    modules = []
    for i in range(last + 1):
        if i in linear:
            in_f, out_f = linear[i]
            modules.append(nn.Linear(in_f, out_f))
        else:
            modules.append(nn.ELU())
    return nn.Sequential(*modules)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True, type=Path,
                    help="training run dir (contains parameters.pkl + checkpoints/)")
    ap.add_argument("--ckpt", default="ac_weights_016000.pt",
                    help="checkpoint filename under run/checkpoints/")
    ap.add_argument("--out", required=True, type=Path,
                    help="staging deploy dir to write (parameters.pkl + checkpoints/*.jit)")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    ckpt_path = args.run / "checkpoints" / args.ckpt
    if not ckpt_path.exists():
        raise FileNotFoundError(ckpt_path)

    sd = torch.load(ckpt_path, map_location="cpu")
    # Be tolerant of wrappers, though DrEureka saves a bare state_dict.
    if isinstance(sd, dict) and "model_state_dict" in sd:
        sd = sd["model_state_dict"]
    if isinstance(sd, dict) and "actor_critic" in sd and isinstance(sd["actor_critic"], dict):
        sd = sd["actor_critic"]

    adaptation_module = rebuild_sequential(sd, "adaptation_module")
    actor_body = rebuild_sequential(sd, "actor_body")

    # Hard gate: every parameter must match the checkpoint exactly.
    adaptation_module.load_state_dict(
        {k[len("adaptation_module."):]: v for k, v in sd.items()
         if k.startswith("adaptation_module.")}, strict=True)
    actor_body.load_state_dict(
        {k[len("actor_body."):]: v for k, v in sd.items()
         if k.startswith("actor_body.")}, strict=True)
    adaptation_module.eval()
    actor_body.eval()

    # Numerical self-check: scripted modules must equal the eager modules.
    gen = torch.Generator().manual_seed(args.seed)
    num_obs_history = adaptation_module[0].in_features
    x = torch.randn(64, num_obs_history, generator=gen)
    with torch.no_grad():
        latent_eager = adaptation_module(x)
        action_eager = actor_body(torch.cat((x, latent_eager), dim=-1))

    ckpt_dir = args.out / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    body_path = ckpt_dir / "body_latest.jit"
    adapt_path = ckpt_dir / "adaptation_module_latest.jit"
    torch.jit.script(actor_body).save(body_path)
    torch.jit.script(adaptation_module).save(adapt_path)

    body_jit = torch.jit.load(body_path, map_location="cpu")
    adapt_jit = torch.jit.load(adapt_path, map_location="cpu")
    with torch.no_grad():
        latent_jit = adapt_jit(x)
        action_jit = body_jit(torch.cat((x, latent_jit), dim=-1))

    latent_match = torch.allclose(latent_eager, latent_jit, atol=1e-6, rtol=0)
    action_match = torch.allclose(action_eager, action_jit, atol=1e-6, rtol=0)
    max_action_err = (action_eager - action_jit).abs().max().item()

    # Stage parameters.pkl so deploy_lcm_policy reads the right Go2 contract.
    src_params = args.run / "parameters.pkl"
    if not src_params.exists():
        raise FileNotFoundError(src_params)
    shutil.copy2(src_params, args.out / "parameters.pkl")

    selfcheck = {
        "checkpoint": str(ckpt_path),
        "deploy_dir": str(args.out),
        "num_obs_history": num_obs_history,
        "num_privileged_obs": int(adaptation_module[-1].out_features),
        "num_actions": int(actor_body[-1].out_features),
        "actor_body_layers": [type(m).__name__ for m in actor_body],
        "adaptation_module_layers": [type(m).__name__ for m in adaptation_module],
        "body_latest_jit": str(body_path),
        "adaptation_module_latest_jit": str(adapt_path),
        "latent_allclose": latent_match,
        "action_allclose": action_match,
        "max_action_abs_err": max_action_err,
        "ok": bool(latent_match and action_match),
    }
    (args.out / "export_jit_selfcheck.json").write_text(
        json.dumps(selfcheck, indent=2, sort_keys=True) + "\n")
    print(json.dumps(selfcheck, indent=2, sort_keys=True))
    return 0 if selfcheck["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
