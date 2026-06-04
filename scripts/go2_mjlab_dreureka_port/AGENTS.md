# Go2 MJLab Port Instructions

This caller project prioritizes server-side compatibility over local host
convenience.

The target server has only MJLab 1.0.0 and cannot be upgraded because it uses a
different compute architecture. Do not require newer MJLab APIs in this folder.
When local host MJLab is newer, keep code compatible with the server-side
MJLab 1.0.0 / legacy RSL-RL runtime unless the user explicitly asks to abandon
server compatibility.

Avoid compatibility shims that make the main code path depend on newer MJLab
features. If a checkpoint or runner API differs across versions, prefer the
low-version server behavior and document the exact old-format assumption in the
nearby code or report.
