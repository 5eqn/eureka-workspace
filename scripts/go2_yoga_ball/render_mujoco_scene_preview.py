#!/usr/bin/env python3
"""Render a still preview of the Go2 yoga-ball MuJoCo scene."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import go2_mujoco_dds_endpoint as endpoint


def render_view(renderer, data, *, azimuth: float, elevation: float, distance: float, lookat: list[float]) -> np.ndarray:
    import mujoco

    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.azimuth = azimuth
    camera.elevation = elevation
    camera.distance = distance
    camera.lookat[:] = lookat
    renderer.update_scene(data, camera=camera)
    return renderer.render()


def overlay(frame: np.ndarray, lines: list[str]) -> np.ndarray:
    image = Image.fromarray(frame)
    draw = ImageDraw.Draw(image, "RGBA")
    font = ImageFont.load_default()
    line_height = 14
    draw.rectangle((8, 8, 620, 8 + 10 + line_height * len(lines)), fill=(0, 0, 0, 155))
    for i, line in enumerate(lines):
        draw.text((16, 14 + line_height * i), line, fill=(235, 235, 235, 255), font=font)
    return np.asarray(image)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--ground-mode", choices=["plane", "rough"], default="plane")
    parser.add_argument("--ground-seed", type=int, default=endpoint.ROUGH_GROUND_SEED)
    parser.add_argument("--ball-radius", type=float, default=0.45)
    parser.add_argument("--base-z", type=float, default=1.2)
    parser.add_argument("--floor-z", type=float, default=0.0)
    args = parser.parse_args()

    import mujoco

    scene, ground = endpoint.write_scene(
        args.ball_radius,
        floor_z=args.floor_z,
        ground_mode=args.ground_mode,
        ground_seed=args.ground_seed,
    )
    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    qpos_addr, _, _, _ = endpoint.joint_addresses(model)
    endpoint.set_initial_state(
        model,
        data,
        qpos_addr,
        run_dir=Path(args.run),
        base_pos=[0.0, 0.0, args.base_z],
        base_quat=[1.0, 0.0, 0.0, 0.0],
        base_lin_vel=[0.0, 0.0, 0.0],
        base_ang_vel=[0.0, 0.0, 0.0],
        ball_pos=[0.0, 0.0, args.ball_radius],
        ball_quat=[1.0, 0.0, 0.0, 0.0],
    )
    mujoco.mj_forward(model, data)

    renderer = mujoco.Renderer(model, height=480, width=640)
    try:
        overview = render_view(
            renderer,
            data,
            azimuth=135.0,
            elevation=-18.0,
            distance=3.3,
            lookat=[0.0, 0.0, 0.55],
        )
        low_angle = render_view(
            renderer,
            data,
            azimuth=112.0,
            elevation=-7.0,
            distance=2.8,
            lookat=[0.0, 0.0, 0.42],
        )
    finally:
        renderer.close()

    panel = np.hstack([overview, low_angle])
    lines = [
        f"ground={ground['mode']} seed={ground['seed'] if ground['seed'] is not None else 'n/a'}",
        f"extent={ground.get('extent', 'flat')} height_scale={ground.get('height_scale', 'n/a')} friction={ground.get('friction', 'n/a')}",
        "left: overview, right: low-angle relief check",
    ]
    panel = overlay(panel, lines)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(panel).save(output)
    result = {
        "ok": bool(output.exists() and output.stat().st_size > 1000),
        "output": str(output),
        "scene": str(scene),
        "run": args.run,
        "ground": ground,
        "base_z": args.base_z,
        "ball_radius": args.ball_radius,
        "file_size_bytes": output.stat().st_size if output.exists() else 0,
    }
    artifact = Path(args.artifact)
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
