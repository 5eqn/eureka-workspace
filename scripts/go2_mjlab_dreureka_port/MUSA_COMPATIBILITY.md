# MUSA Compatibility Guide

This repo keeps the source in MJLab form. The MUSA server carries the same API
under the package name `lambdalab`, so package-name edits happen only on the
server and are not committed here.

This port is server-first. Local MJLab runs are only a debugging aid for the
MUSA/lambdalab deployment path, not the environment contract this port optimizes
for.

## Runtime Versions

The intended server runtime is:

- lambdalab port corresponding to MJLab `v1.0.0`
- `rsl-rl-lib==3.1.0`

Keep the runner config in the legacy `policy=RslRlPpoActorCriticCfg(...)`
schema expected by `rsl-rl-lib==3.1.0`. Do not convert this port to the newer
RSL-RL `actor`/`critic` config shape for local convenience.

## Assumption: Multi-GPU Training

`select_gpus("all")` and `torchrunx` are not MUSA-specific. Treat them as the
general multi-GPU training path for both CUDA and MUSA:

- `select_gpus("all")` chooses the visible devices.
- `torchrunx` launches one worker per selected device when more than one device
  is selected.
- Each worker uses `LOCAL_RANK`; global `RANK` is added to the seed.
- Rank 0 writes launch metadata.

This is a training-scale assumption, not a CUDA-to-MUSA port rule.

## Server-Side Rename

Run this from the workspace root on the MUSA server:

```bash
rg -l -0 --glob '*.py' '^\s*(from|import)\s+mjlab(\b|\.)' \
  | xargs -0 perl -pi -e 's/^(\s*from\s+)mjlab(?=\.|\s+import\b)/${1}lambdalab/g; s/^(\s*import\s+)mjlab(?=\.|\b)/${1}lambdalab/g'
rg -l -0 --glob '*.py' '\bregister_mjlab_task\b' \
  | xargs -0 perl -pi -e 's/\bregister_mjlab_task\b/register_lambdalab_task/g'
```

Use the lambdalab port corresponding to MJLab `v1.0.0`, installed without
dependency resolution so ported architecture-specific packages are preserved:

```bash
python -m pip install --no-deps -e /workspace/lambda-lab
```

## CUDA-To-MUSA Differences

Only these parts are MUSA-port-specific:

- Package names are rewritten from `mjlab` to `lambdalab` on the server.
- Training must not import `MjlabOnPolicyRunner` from `lambdalab.rl`; use the
  task registry runner when available, otherwise `rsl_rl.runners.OnPolicyRunner`.
- If `MUSA_VISIBLE_DEVICES` exists, rewrite it from `selected_gpus` and set
  `MUJOCO_RENDERER=""`.
- Worker device selection uses `musa:{selected_gpus[LOCAL_RANK]}` when
  `MUSA_VISIBLE_DEVICES` is nonempty; otherwise the same code uses CUDA or CPU.

## MuJoCo Spec Size Compatibility

The lambdalab/MUSA runtime may reject `MjSpec.add_geom` sizes that compile under
the CUDA/MuJoCo stack:

- `size` sequences may need MuJoCo's full internal three-slot `geom_size` shape.
- Every authored `size` element may need to be positive, even slots that MuJoCo
  treats as unused for the geom type.
- Avoid zero-width generated terrain boxes; for example, keep
  `TerrainGeneratorCfg.border_width` positive when the generator still emits
  border geoms.

```python
body.add_geom(
  type=mujoco.mjtGeom.mjGEOM_SPHERE,
  size=(radius,) * 3,
)
```

For `mjGEOM_SPHERE`, MuJoCo uses `size[0]` as the radius. The repeated values
are a compiler-compatibility representation, not x/y/z axis radii; use
`mjGEOM_ELLIPSOID` for axis-specific radii.

The source should stay minimal and explicit:

```python
selected_gpus, num_gpus = select_gpus("all")
if "MUSA_VISIBLE_DEVICES" in os.environ:
  os.environ["MUSA_VISIBLE_DEVICES"] = (
    "" if selected_gpus is None else ",".join(map(str, selected_gpus))
  )
  os.environ["MUJOCO_RENDERER"] = ""
```
