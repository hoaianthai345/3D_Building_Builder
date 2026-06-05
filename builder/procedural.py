"""Procedural building generator: BuildingSpec (+ Structure) -> GLB (trimesh, CPU).

Dollhouse massing built from the Structure tree: stacked floor plates, each
subdivided into rooms with low partition walls and a per-type floor color, plus a
roof. Each room's selectable floor mesh is named exactly after its Room.id
(``room_<floor>_<idx>``) so the web explorer can pick it and drill in.

Coordinate frame: Y up (glTF), meters. Building centered on the origin.
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

# Room floor tint per functional type (blue-family + warm neutrals).
_ROOM_HEX = {
    "reception": "#cdd9f5",
    "meeting": "#9db4e8",
    "open_work": "#dfe6f6",
    "manager": "#b6c6ee",
    "service": "#e3e0d6",
    "apartment": "#dfe6f6",
    "shop": "#cdd9f5",
    "fnb": "#ecdcc4",
    "classroom": "#d7e3d6",
    "lab": "#cfe0e6",
    "office": "#dfe6f6",
    "default": "#dde2ea",
}
_WALL_HEX = "#efece4"
_PLATE_HEX = "#cfcabc"
_ROOF_HEX = "#3a4250"

_WALL_T = 0.12  # partition thickness (m)


def _hex_rgba(hex_str: str, alpha: float = 1.0) -> list[float]:
    h = hex_str.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
    return [r, g, b, alpha]


def _box(extents: Sequence[float], center: Sequence[float], rgba: list[float],
         roughness: float = 0.9) -> trimesh.Trimesh:
    mesh = trimesh.creation.box(extents=list(extents))
    mesh.apply_translation(list(center))
    mesh.visual = TextureVisuals(
        material=PBRMaterial(baseColorFactor=rgba, metallicFactor=0.0, roughnessFactor=roughness)
    )
    return mesh


def build_scene(spec: BuildingSpec, structure: Optional[Structure] = None) -> trimesh.Scene:
    structure = structure or uniform_structure(spec)
    W, D = float(spec.footprint_w), float(spec.footprint_d)
    fh = float(spec.floor_height)
    H = spec.total_height
    scene = trimesh.Scene()

    for floor in structure.floors:
        y0 = floor.elevation
        scene.add_geometry(
            _box((W, 0.12, D), (0, y0 + 0.06, 0), _hex_rgba(_PLATE_HEX)),
            geom_name=f"floorplate_{floor.index}",
        )
        hw = fh * 0.82
        wall_y = y0 + 0.12 + hw / 2
        for room in floor.rooms:
            cx, cz = room.x + room.w / 2, room.z + room.d / 2
            # selectable room floor (named exactly = room.id)
            scene.add_geometry(
                _box((max(room.w - 0.04, 0.2), 0.06, max(room.d - 0.04, 0.2)),
                     (cx, y0 + 0.15, cz), _hex_rgba(_ROOM_HEX.get(room.type, _ROOM_HEX["default"]))),
                geom_name=room.id,
            )
            # four partition walls
            wall_rgba = _hex_rgba(_WALL_HEX)
            edges = [
                ((room.w, hw, _WALL_T), (cx, wall_y, room.z)),
                ((room.w, hw, _WALL_T), (cx, wall_y, room.z + room.d)),
                ((_WALL_T, hw, room.d), (room.x, wall_y, cz)),
                ((_WALL_T, hw, room.d), (room.x + room.w, wall_y, cz)),
            ]
            for k, (ext, ctr) in enumerate(edges):
                scene.add_geometry(_box(ext, ctr, wall_rgba), geom_name=f"wall_{room.id}_{k}")

    scene.add_geometry(_box((W * 1.02, 0.25, D * 1.02), (0, H + 0.12, 0), _hex_rgba(_ROOF_HEX)),
                       geom_name="roof")
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
