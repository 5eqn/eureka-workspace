"""Isaac-style DrEureka rough terrain for the MJLab caller project."""

from __future__ import annotations

from dataclasses import dataclass
import uuid

import mujoco
import numpy as np

from mjlab.terrains.terrain_generator import SubTerrainCfg, TerrainGeometry, TerrainOutput
from mjlab.terrains.terrain_generator import TerrainGenerator
from mjlab.terrains.heightfield_terrains import _compute_flat_patches
from mjlab.utils.color import HSV, hsv_to_rgb


def _fade(t: np.ndarray) -> np.ndarray:
  return 6 * t**5 - 15 * t**4 + 10 * t**3


def _lerp(a: np.ndarray, b: np.ndarray, x: np.ndarray) -> np.ndarray:
  return a + x * (b - a)


def _gradient(h: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
  vectors = np.array([[0, 1], [0, -1], [1, 0], [-1, 0]])
  g = vectors[h % 4]
  return g[:, :, 0] * x + g[:, :, 1] * y


def dreureka_perlin(x: np.ndarray, y: np.ndarray, seed: int = 0) -> np.ndarray:
  """DrEureka's exact Perlin function from globe_walking/go1_gym/utils/terrain.py."""
  state = np.random.get_state()
  try:
    np.random.seed(seed)
    p = np.arange(256, dtype=int)
    np.random.shuffle(p)
  finally:
    np.random.set_state(state)
  p = np.stack([p, p]).flatten()
  xi, yi = x.astype(int), y.astype(int)
  xf, yf = x - xi, y - yi
  u, v = _fade(xf), _fade(yf)
  n00 = _gradient(p[p[xi] + yi], xf, yf)
  n01 = _gradient(p[p[xi] + yi + 1], xf, yf - 1)
  n11 = _gradient(p[p[xi + 1] + yi + 1], xf - 1, yf - 1)
  n10 = _gradient(p[p[xi + 1] + yi], xf - 1, yf)
  x1 = _lerp(n00, n10, u)
  x2 = _lerp(n01, n11, u)
  return _lerp(x1, x2, v)


def _color_by_height(
  spec: mujoco.MjSpec, normalized_elevation: np.ndarray, unique_id: str
) -> str:
  if normalized_elevation.size == 0:
    rgba = (0.5, 0.5, 0.5, 1.0)
  else:
    value = float(np.mean(normalized_elevation))
    hue = 0.30 - 0.12 * value
    saturation = 0.35
    brightness = 0.38 + 0.36 * value
    rgba = (*hsv_to_rgb(HSV(hue, saturation, brightness)), 1.0)
  material = spec.add_material(name=f"isaac_perlin_mat_{unique_id}", rgba=rgba)
  return material.name


@dataclass(kw_only=True)
class IsaacPerlinHFieldTerrainCfg(SubTerrainCfg):
  """DrEureka boxes_tm flat/rough tile emitted through MuJoCo hfield collision.

  Isaac Gym's DrEureka ``boxes_tm`` first generates a signed heightfield with
  per-tile roughness and then converts it to triangle mesh collision. MuJoCo does
  not expose an equivalent non-convex triangle-soup terrain geom through MJLab;
  this config keeps the Isaac height samples exactly and relies on an increased
  MuJoCo Warp hfield contact-pair cap for the ball contacts.
  """

  roughness_range: tuple[float, float]
  horizontal_scale: float = 0.05
  vertical_scale: float = 0.005
  perlin_scale: float = 20.0
  tile_rows: int = 20
  tile_cols: int = 20
  base_thickness: float = 0.5

  def function(
    self, difficulty: float, spec: mujoco.MjSpec, rng: np.random.Generator
  ) -> TerrainOutput:
    del difficulty
    body = spec.body("terrain")
    width_pixels = int(self.size[0] / self.horizontal_scale)
    length_pixels = int(self.size[1] / self.horizontal_scale)
    if width_pixels <= 1 or length_pixels <= 1:
      raise ValueError("IsaacPerlinHFieldTerrainCfg requires at least 2 samples per axis.")

    row = int(getattr(self, "_mjlab_sub_row", 0))
    col = int(getattr(self, "_mjlab_sub_col", 0))
    roughness = float(rng.uniform(*self.roughness_range))
    lin_x = np.linspace(0, self.perlin_scale, width_pixels, endpoint=False)
    lin_y = np.linspace(0, self.perlin_scale, length_pixels, endpoint=False)
    x, y = np.meshgrid(lin_x, lin_y)
    physical_heights = dreureka_perlin(x, y, seed=row * self.tile_cols + col) * roughness

    height_abs_max = float(max(abs(physical_heights.min()), abs(physical_heights.max()), 1e-6))
    normalized = ((physical_heights / height_abs_max) + 1.0) * 0.5
    unique_id = uuid.uuid4().hex
    field = spec.add_hfield(
      name=f"isaac_perlin_hfield_{unique_id}",
      size=[
        self.size[0] / 2,
        self.size[1] / 2,
        2.0 * height_abs_max,
        self.base_thickness,
      ],
      nrow=normalized.shape[0],
      ncol=normalized.shape[1],
      userdata=normalized.astype(np.float32).flatten().tolist(),
    )
    material_name = _color_by_height(spec, normalized, unique_id)
    hfield_geom = body.add_geom(
      type=mujoco.mjtGeom.mjGEOM_HFIELD,
      hfieldname=field.name,
      pos=[
        self.size[0] / 2,
        self.size[1] / 2,
        -height_abs_max,
      ],
      material=material_name,
    )

    flat_patches = _compute_flat_patches(
      physical_heights,
      1.0,
      self.horizontal_scale,
      0,
      self.flat_patch_sampling,
      rng,
    )
    origin = np.array([self.size[0] / 2, self.size[1] / 2, 0.0])
    return TerrainOutput(
      origin=origin,
      geometries=[TerrainGeometry(geom=hfield_geom, hfield=field)],
      flat_patches=flat_patches,
    )


def install_mjlab_tile_index_patch() -> None:
  """Expose MJLab terrain row/col to script-local terrain configs.

  MJLab's public ``SubTerrainCfg.function`` signature receives only difficulty,
  spec, and rng. DrEureka's Perlin seed is tile-index based, so the caller project
  records the generator's current row/column on configs that opt into it.
  """
  if getattr(TerrainGenerator, "_dreureka_tile_index_patch", False):
    return
  original = TerrainGenerator._create_terrain_geom

  def _create_terrain_geom_with_tile_index(
    self,
    spec,
    world_position,
    difficulty,
    cfg,
    sub_row,
    sub_col,
  ):
    if isinstance(cfg, IsaacPerlinHFieldTerrainCfg):
      cfg._mjlab_sub_row = int(sub_row)
      cfg._mjlab_sub_col = int(sub_col)
    return original(self, spec, world_position, difficulty, cfg, sub_row, sub_col)

  TerrainGenerator._create_terrain_geom = _create_terrain_geom_with_tile_index
  TerrainGenerator._dreureka_tile_index_patch = True
