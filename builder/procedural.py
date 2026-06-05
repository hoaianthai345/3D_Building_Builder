"""Procedural building generator: BuildingSpec (+ Structure) -> GLB (trimesh, CPU).

Two layers, both exported with named nodes so the web explorer can switch between
them:

  INTERIOR (drill-down): floor plates + per-room floors (named ``room_<f>_<i>``) +
  partition walls. Revealed when the exterior shell is hidden / a floor is isolated.

  EXTERIOR SHELL (``shell_*``): a curtain-wall facade (glass panels + vertical
  mullions), overhanging floor slabs, a roof parapet, an entrance canopy and a
  ground plane. Shown by default so the building reads as real architecture rather
  than bare boxes.

Y up (glTF), meters, centered on the origin.
"""

from __future__ import annotations

import os
import time
from typing import Optional, Sequence

import trimesh
from trimesh.visual.material import PBRMaterial
from trimesh.visual import TextureVisuals

from .schemas import BuildingSpec, ModelInfo, Structure
from .structure import uniform_structure

# Interior tints per room type.
_ROOM_HEX = {
    "reception": "#cdd9f5", "meeting": "#9db4e8", "open_work": "#dfe6f6",
    "manager": "#b6c6ee", "service": "#e3e0d6", "apartment": "#dfe6f6",
    "shop": "#cdd9f5", "fnb": "#ecdcc4", "classroom": "#d7e3d6",
    "lab": "#cfe0e6", "office": "#dfe6f6", "default": "#dde2ea",
}
_WALL_HEX = "#efece4"
_PLATE_HEX = "#cfcabc"

# Exterior shell materials.
_GLASS_HEX = "#3a64c8"     # curtain-wall glazing (accent blue)
_MULLION_HEX = "#9aa0a8"   # metal frame / mullion
_SLAB_HEX = "#d8d4c8"      # concrete floor band
_PARAPET_HEX = "#c4c0b4"
_CANOPY_HEX = "#1f4fc4"    # entrance canopy (accent)
_GROUND_HEX = "#d2d5cf"

_WALL_T = 0.12


def _hex_rgba(hex_str: str, alpha: float = 1.0) -> list[float]:
    h = hex_str.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
    return [r, g, b, alpha]


def _box(extents: Sequence[float], center: Sequence[float], rgba: list[float],
         roughness: float = 0.9, metallic: float = 0.0) -> trimesh.Trimesh:
    mesh = trimesh.creation.box(extents=list(extents))
    mesh.apply_translation(list(center))
    mesh.visual = TextureVisuals(material=PBRMaterial(
        baseColorFactor=rgba, metallicFactor=metallic, roughnessFactor=roughness,
        alphaMode="BLEND" if rgba[3] < 1.0 else "OPAQUE",
    ))
    return mesh


def _add_interior(scene: trimesh.Scene, spec: BuildingSpec, structure: Structure) -> None:
    W, D, fh = spec.footprint_w, spec.footprint_d, spec.floor_height
    for floor in structure.floors:
        y0 = floor.elevation
        scene.add_geometry(_box((W, 0.12, D), (0, y0 + 0.06, 0), _hex_rgba(_PLATE_HEX)),
                           geom_name=f"floorplate_{floor.index}")
        hw = fh * 0.82
        wall_y = y0 + 0.12 + hw / 2
        for room in floor.rooms:
            cx, cz = room.x + room.w / 2, room.z + room.d / 2
            scene.add_geometry(
                _box((max(room.w - 0.04, 0.2), 0.06, max(room.d - 0.04, 0.2)),
                     (cx, y0 + 0.15, cz), _hex_rgba(_ROOM_HEX.get(room.type, _ROOM_HEX["default"]))),
                geom_name=room.id)
            wr = _hex_rgba(_WALL_HEX)
            for k, (ext, ctr) in enumerate([
                ((room.w, hw, _WALL_T), (cx, wall_y, room.z)),
                ((room.w, hw, _WALL_T), (cx, wall_y, room.z + room.d)),
                ((_WALL_T, hw, room.d), (room.x, wall_y, cz)),
                ((_WALL_T, hw, room.d), (room.x + room.w, wall_y, cz)),
            ]):
                scene.add_geometry(_box(ext, ctr, wr), geom_name=f"wall_{room.id}_{k}")


def _add_shell(scene: trimesh.Scene, spec: BuildingSpec) -> None:
    W, D, fh = spec.footprint_w, spec.footprint_d, spec.floor_height
    H = spec.total_height
    cols = spec.rooms_per_floor
    glass = _hex_rgba(_GLASS_HEX, 0.7)
    mull = _hex_rgba(_MULLION_HEX)
    slab = _hex_rgba(_SLAB_HEX)

    # ground plane
    scene.add_geometry(_box((W * 3.4, 0.2, D * 3.4), (0, -0.1, 0), _hex_rgba(_GROUND_HEX)),
                       geom_name="shell_ground")

    margin = 0.3
    cw = (W - 2 * margin) / cols
    dcols = max(2, round((D - 2 * margin) / max(cw, 0.1)))
    dw = (D - 2 * margin) / dcols

    for i in range(spec.floors):
        y0 = i * fh
        # overhanging floor slab band at the top of each storey
        scene.add_geometry(_box((W + 0.5, 0.16, D + 0.5), (0, y0 + fh - 0.08, 0), slab),
                           geom_name=f"shell_slab_{i}")
        gy = y0 + fh * 0.5
        gh = fh * 0.74
        # glazing on front/back (+Z/-Z)
        for c in range(cols):
            cx = -W / 2 + margin + cw * (c + 0.5)
            for zs in (1, -1):
                scene.add_geometry(
                    _box((cw * 0.86, gh, 0.1), (cx, gy, zs * (D / 2 + 0.02)), glass,
                         roughness=0.2, metallic=0.1),
                    geom_name=f"shell_glassZ_{i}_{c}_{'f' if zs > 0 else 'b'}")
        # glazing on left/right (+X/-X)
        for c in range(dcols):
            cz = -D / 2 + margin + dw * (c + 0.5)
            for xs in (1, -1):
                scene.add_geometry(
                    _box((0.1, gh, dw * 0.86), (xs * (W / 2 + 0.02), gy, cz), glass,
                         roughness=0.2, metallic=0.1),
                    geom_name=f"shell_glassX_{i}_{c}_{'r' if xs > 0 else 'l'}")

    # vertical mullions full height (front/back columns + side columns)
    for c in range(cols + 1):
        x = -W / 2 + margin + cw * c
        for zs in (1, -1):
            scene.add_geometry(_box((0.14, H, 0.14), (x, H / 2, zs * (D / 2 + 0.02)), mull, metallic=0.3),
                               geom_name=f"shell_mullZ_{c}_{'f' if zs > 0 else 'b'}")
    for c in range(dcols + 1):
        z = -D / 2 + margin + dw * c
        for xs in (1, -1):
            scene.add_geometry(_box((0.14, H, 0.14), (xs * (W / 2 + 0.02), H / 2, z), mull, metallic=0.3),
                               geom_name=f"shell_mullX_{c}_{'r' if xs > 0 else 'l'}")

    # roof slab + parapet ring
    scene.add_geometry(_box((W + 0.3, 0.18, D + 0.3), (0, H + 0.09, 0), slab), geom_name="shell_roof")
    ph, py = 0.5, H + 0.25
    par = _hex_rgba(_PARAPET_HEX)
    scene.add_geometry(_box((W + 0.5, ph, 0.18), (0, py, D / 2 + 0.16), par), geom_name="shell_parapet_f")
    scene.add_geometry(_box((W + 0.5, ph, 0.18), (0, py, -D / 2 - 0.16), par), geom_name="shell_parapet_b")
    scene.add_geometry(_box((0.18, ph, D + 0.5), (W / 2 + 0.16, py, 0), par), geom_name="shell_parapet_r")
    scene.add_geometry(_box((0.18, ph, D + 0.5), (-W / 2 - 0.16, py, 0), par), geom_name="shell_parapet_l")

    # entrance canopy at the ground floor front
    scene.add_geometry(_box((W * 0.34, 0.12, 1.3), (0, fh * 0.92, D / 2 + 0.7), _hex_rgba(_CANOPY_HEX)),
                       geom_name="shell_canopy")


def build_scene(spec: BuildingSpec, structure: Optional[Structure] = None) -> trimesh.Scene:
    structure = structure or uniform_structure(spec)
    scene = trimesh.Scene()
    _add_interior(scene, spec, structure)
    _add_shell(scene, spec)
    return scene


def build_glb(spec: BuildingSpec, out_path: str, structure: Optional[Structure] = None) -> ModelInfo:
    t0 = time.perf_counter()
    scene = build_scene(spec, structure)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    scene.export(out_path)
    build_ms = (time.perf_counter() - t0) * 1000.0

    tri_count = int(sum(int(g.faces.shape[0]) for g in scene.geometry.values()))
    size_kb = round(os.path.getsize(out_path) / 1024.0, 1)
    info = ModelInfo(glb=os.path.basename(out_path), backend="procedural",
                     tri_count=tri_count, size_kb=size_kb)
    setattr(info, "_build_ms", build_ms)
    return info
