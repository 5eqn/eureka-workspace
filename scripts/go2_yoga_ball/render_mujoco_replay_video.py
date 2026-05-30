#!/usr/bin/env python3
"""Render a Go2 yoga-ball MuJoCo replay with a follow camera."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "artifacts" / "go2_yoga_ball" / "post_training_sim2sim"
BUILD_SCENE = ROOT / "artifacts" / "go2_yoga_ball" / "build" / "go2_yoga_ball_scene.xml"
UNITREE_MOTOR_ORDER = [
    "FR_hip_joint",
    "FR_thigh_joint",
    "FR_calf_joint",
    "FL_hip_joint",
    "FL_thigh_joint",
    "FL_calf_joint",
    "RR_hip_joint",
    "RR_thigh_joint",
    "RR_calf_joint",
    "RL_hip_joint",
    "RL_thigh_joint",
    "RL_calf_joint",
]


def as_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_events(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            return rows
        for raw in reader:
            if not raw:
                continue
            row = {
                "event": raw[0],
                "monotonic_s": raw[1] if len(raw) > 1 else "",
                "wall_time_s": raw[2] if len(raw) > 2 else "",
                "detail": raw[3] if len(raw) > 3 else "",
            }
            if len(raw) >= 6:
                row["sim_time_s"] = raw[3]
                row["support_active"] = raw[4]
                row["detail"] = raw[5]
            rows.append(row)
    return rows


def overlay_text(frame: Any, lines: list[str], *, alert: bool = False) -> Any:
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np

    image = Image.fromarray(frame)
    draw = ImageDraw.Draw(image, "RGBA")
    font = ImageFont.load_default()
    line_height = 14
    box_height = 10 + line_height * len(lines)
    draw.rectangle((8, 8, 560, 8 + box_height), fill=(0, 0, 0, 155))
    color = (255, 80, 80, 255) if alert else (235, 235, 235, 255)
    for i, line in enumerate(lines):
        draw.text((16, 14 + line_height * i), line, fill=color, font=font)
    if alert:
        w, h = image.size
        draw.rectangle((0, 0, w - 1, h - 1), outline=(255, 0, 0, 255), width=8)
    return np.asarray(image)


def add_joint_markers(mujoco: Any, renderer: Any, data: Any, joint_ids: list[int], violations: list[int]) -> None:
    import numpy as np

    for index in violations:
        if renderer.scene.ngeom >= renderer.scene.maxgeom:
            return
        geom = renderer.scene.geoms[renderer.scene.ngeom]
        mujoco.mjv_initGeom(
            geom,
            mujoco.mjtGeom.mjGEOM_SPHERE,
            np.array([0.055, 0.055, 0.055], dtype=float),
            np.array(data.xanchor[joint_ids[index]], dtype=float),
            np.eye(3).reshape(-1),
            np.array([1.0, 0.0, 0.0, 1.0], dtype=float),
        )
        renderer.scene.ngeom += 1


def render(args: argparse.Namespace) -> dict[str, Any]:
    import imageio.v2 as imageio
    import mujoco
    import numpy as np

    replay_path = Path(args.replay)
    events_path = Path(args.events)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = read_csv(replay_path)
    events = read_events(events_path)
    required = ["base_x", "base_qw", "ball_x", "ball_qw"]
    missing = [name for name in required if not rows or name not in rows[0]]
    if missing:
        result = {"ok": False, "error": "replay lacks full pose columns", "missing_columns": missing, "replay": str(replay_path)}
        Path(args.artifact).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return result

    release_time = None
    fall_time = None
    for event in events:
        if event.get("event") == "SUPPORT_RELEASE_CONFIRMED":
            release_time = as_float(event.get("sim_time_s"))
        if event.get("event") == "FALL_DETECTED":
            fall_time = as_float(event.get("sim_time_s"))

    model = mujoco.MjModel.from_xml_path(str(BUILD_SCENE))
    data = mujoco.MjData(model)
    qpos_addr = []
    joint_ids = []
    joint_limits = []
    for name in UNITREE_MOTOR_ORDER:
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
        qpos_addr.append(int(model.jnt_qposadr[jid]))
        joint_ids.append(int(jid))
        joint_limits.append((float(model.jnt_range[jid, 0]), float(model.jnt_range[jid, 1])))
    ball_jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "yoga_ball_free")
    ball_qpos = int(model.jnt_qposadr[ball_jid])
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.distance = 3.0
    camera.azimuth = 135.0
    camera.elevation = -18.0
    renderer = mujoco.Renderer(model, height=480, width=640)

    fps = int(args.fps)
    log_fps = float(args.log_fps)
    stride = max(1, round(log_fps / fps))
    frames = 0
    variances = []
    marked_frames = 0
    try:
        with imageio.get_writer(out_path, fps=fps, codec="libx264", quality=8, macro_block_size=16) as writer:
            for row in rows[::stride]:
                data.qpos[:] = 0.0
                data.qvel[:] = 0.0
                data.qpos[0:7] = [
                    as_float(row.get("base_x")) or 0.0,
                    as_float(row.get("base_y")) or 0.0,
                    as_float(row.get("base_z_qpos")) or as_float(row.get("base_z")) or 0.0,
                    as_float(row.get("base_qw")) or 1.0,
                    as_float(row.get("base_qx")) or 0.0,
                    as_float(row.get("base_qy")) or 0.0,
                    as_float(row.get("base_qz")) or 0.0,
                ]
                for i, addr in enumerate(qpos_addr):
                    data.qpos[addr] = as_float(row.get(f"q_{i}")) or 0.0
                data.qpos[ball_qpos : ball_qpos + 7] = [
                    as_float(row.get("ball_x")) or 0.0,
                    as_float(row.get("ball_y")) or 0.0,
                    as_float(row.get("ball_z_qpos")) or as_float(row.get("ball_z")) or 0.45,
                    as_float(row.get("ball_qw")) or 1.0,
                    as_float(row.get("ball_qx")) or 0.0,
                    as_float(row.get("ball_qy")) or 0.0,
                    as_float(row.get("ball_qz")) or 0.0,
                ]
                mujoco.mj_forward(model, data)
                base_x, base_y, base_z = data.qpos[0], data.qpos[1], data.qpos[2]
                ball_x, ball_y, ball_z = data.qpos[ball_qpos], data.qpos[ball_qpos + 1], data.qpos[ball_qpos + 2]
                camera.lookat[:] = [(base_x + ball_x) * 0.5, (base_y + ball_y) * 0.5, max(0.55, (base_z + ball_z) * 0.5)]
                renderer.update_scene(data, camera=camera)
                violations = []
                for i, (low, high) in enumerate(joint_limits):
                    q = as_float(row.get(f"q_{i}"))
                    if q is not None and (q < low - 1e-6 or q > high + 1e-6):
                        violations.append(i)
                if violations:
                    marked_frames += 1
                    add_joint_markers(mujoco, renderer, data, joint_ids, violations)
                sim_time = as_float(row.get("sim_time_s")) or 0.0
                released = release_time is not None and sim_time >= release_time
                fallen = fall_time is not None and sim_time >= fall_time
                frame = renderer.render()
                alert = bool(violations or fallen)
                status = "released" if released else "supported"
                if fallen:
                    status = "fall detected"
                lines = [
                    f"Go2 trained Sim2Sim  t={sim_time:.2f}s  {status}",
                    f"release={release_time:.2f}s fall={fall_time:.2f}s" if release_time is not None and fall_time is not None else "follow camera, raw replay render",
                ]
                if violations:
                    lines.append("joint limit: " + ", ".join(UNITREE_MOTOR_ORDER[i] for i in violations[:3]))
                frame = overlay_text(frame, lines, alert=alert)
                variances.append(float(np.var(frame)))
                writer.append_data(frame)
                frames += 1
    finally:
        renderer.close()

    result = {
        "ok": bool(out_path.exists() and out_path.stat().st_size > 1000 and frames > 0 and variances and max(variances) > 1.0),
        "video": str(out_path),
        "replay": str(replay_path),
        "events": str(events_path),
        "scene": str(BUILD_SCENE),
        "frames_written": frames,
        "fps": fps,
        "camera": "free camera following midpoint of robot base and yoga ball",
        "release_time_s": release_time,
        "fall_time_s": fall_time,
        "marked_joint_limit_frames": marked_frames,
        "file_size_bytes": out_path.stat().st_size if out_path.exists() else 0,
        "frame_variance_max": max(variances) if variances else None,
        "rendered_from_raw_replay": True,
    }
    Path(args.artifact).parent.mkdir(parents=True, exist_ok=True)
    Path(args.artifact).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay", required=True)
    parser.add_argument("--events", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--fps", type=int, default=25)
    parser.add_argument("--log-fps", type=float, default=50.0)
    result = render(parser.parse_args())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
