
Behavioral guidelines to reduce common LLM coding mistakes.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## Repository Inventory

Before doing repository work, read the root-level `CURRENT_INVENTORY.md` first. It is the concise map of the main-stream project state and the files that still matter.

Keep `CURRENT_INVENTORY.md` and `OUTDATED_INVENTORY.md` synchronized with workspace contents whenever files are added, removed, renamed, moved, or repurposed. `CURRENT_INVENTORY.md` should contain only files directly related to the main stream of this work, with an outline that excludes failed attempts. Move failed attempts, wrong-model artifacts, abandoned goals, superseded reports, and unrelated historical logs under `outdated/`, and record them in `OUTDATED_INVENTORY.md`.

Inventory maintenance must optimize for a reader who hates cognitive load. Treat every entry in `CURRENT_INVENTORY.md` as a cost paid by a future human: keep the visible file structure minimal, keep only mainstream project files in current inventory, and explain each remaining item clearly enough that the reader does not need to reverse-engineer why it exists. Ignored `artifacts/` and `logs/` files still belong in `CURRENT_INVENTORY.md` when they are mainstream evidence; ignoring them in Git is not a reason to hide them from the inventory.

Inventory reasons must be specific to the file or collapsed folder. Generic filler such as "repository governance file", "active workflow source", or "retained for provenance/debugging" is banned because it does not explain why that exact item exists.

## Runnable Scripts and Scenes

`scripts/` and any still-current `docker/` entries must contain self-contained runnable workflows. Put scene files, caller-project files, and script-owned runtime inputs inside the relevant `scripts/...` workflow directory when they are required to run that workflow. Do not put new scenes or runnable inputs under `artifacts/`; `artifacts/` is for outputs and evidence. Some older work violates this rule, but new work must not.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

### Details about goal design

The strongest Goals usually define six things:

Outcome: what should be true when the work is done.
Verification surface: the test, benchmark, report, artifact, command output, or source material that proves it.
Constraints: what must not regress while Codex works.
Boundaries: which files, tools, data, repositories, or resources Codex may use.
Iteration policy: how Codex should decide what to try next after each attempt.
Blocked stop condition: when Codex should stop and report that no defensible path remains under the current limits.

We aim for very high standards in verification surface, and prefer a test-generate-report workflow, so that verification surface gets unified to a single file tree. For example, to prove that a humanoid robot motion tracking Sim2Sim is correct, you output a raw log file, a report that calculates the RMSE in joint space and verify it's below 0.2 for majority of motions, a report that calculates the phase time & wall time & sim time and verify that they're the same, a report that measures inference speed of policy and verify that it's below control rate, some smoke tests with raw logs and a report that proves the behaviour that: no policy control and release causes the robot to fall in 2 seconds, add control then release can make robot stand for more than 5 seconds, releasing control then causes the robot to fall in 2 seconds, and event logs proving that in actual Sim2Sim you've released the robot before activating motion tracking. Most importantly, we asked agents to generate side-by-side comparison video for two motion tracking methods, rendering robot inside MuJoCo with collected raw log artifact, so that human can verify if you're doing things correctly. When designing goals, you must formalize verification surface as a concrete file tree.

We also include our final goal & vision inside the outcome section. For example, we do the Sim2Sim comparison of multiple policies so that we can immediately swap simulator docker container to real robot, and the deployment will be immediately used to make real robot perform loco-manipulation tasks, assessing the performance of different policies. Informing agents our vision can align them with our actual goal, so they no longer treat the verification surface as rules to hack through, instead they make real productional progress. In every outcome section we highlight that both Claude Opus 4.6 and human experts in embodied intelligence will review your work, and that they're satisfied should be true when the work is done.

For constraints, we ask the agents to not change host environment whenever possible. We allow installing lightweight Python packages on host, but all major logic should be run inside Docker containers. Below is a self-explanatory example:

```
wbc-workspace/
├── docker/                   # Dockerfiles — pure env build, NO scripts, NO entrypoint logic
│   ├── holomotion.Dockerfile
│   ├── gear-sonic.Dockerfile
│   └── unitree_mujoco.Dockerfile
├── scripts/
│   ├── run.sh                # Entrypoint 1: build, deploy, run a policy+motion pair
│   ├── report.sh             # Entrypoint 2: generate all reports from collected logs
│   └── download.sh           # Asset downloader (excluded from script count)
├── assets/                   # Pre-formatted motion clips + model weights (build context)
├── thirdparties/             # Upstream repos (build context)
├── logs/                     # Raw runtime output per run
└── reports/                  # Final reports & video covering all 10 motions
```

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

## 5. New version of environment management (Codename: FRESH)

The FRESH environment management is based on the philosophy that, given a base distro, conda configuration, read-only set of thirdparty dependencies, and modern coding agents, an environment is already reproducible without using Docker, while bypassing problem that Docker introduces, for example rendering.

The main principle is, you should install environment in a project-agnostic manner. For example, you install thirdparty dependency inside `$HOME` folder (for example, `~/MJLab`), and install conda environment normally directly on host. You're free to install apt packages on host and do not need to freeze such list, because installing suitable apt packages to make things work is the duty of modern coding agents. Remember: a base distro, a conda conFiguration, and a REad-only Set of tHirdparty dependencies uniquely identifies an environment. Then store scripts, logs and artifacts just like the old way. The difference is just we don't depend on Docker anymore.

Important: If a thirdparty dependency can be installed with conda (for example with pip package), do not install from source. If you have to install from source, put it inside home folder and you are NOT allowed to change any byte inside it. If you have to patch a dependency (for example when reproducing DrEureka), make sure the dependency is inside project thirdparties folder, and name every single byte of change you made inside it in a sibling HTML file. This rule applies only when explicitly asked to use the FRESH way and that exact prompt requires patching thirdparty dependencies. For old changes, you do not need this operation. When using the FRESH way, if any thirdparty dependency should be patched, you must report it to user in the plan phase.

When asked to maintain environment with FRESH, override previous instructions to use Docker, and use the FRESH way instead.

When downloading packages, models, repositories, datasets, or installer payloads, use reachable China mirrors whenever possible for better speed. Test mirror availability before making it the default, especially for CUDA/NVIDIA-related channels.
