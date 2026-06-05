"""Assemble the Structure tree (building -> floors -> rooms).

Each floor gets its own room program (a list of templates: name/type/weight/
description), so mixed-use towers can vary by floor band. The geometric packing
comes from layout.plate_rooms. Room ids match the GLB node names exactly so the
frontend explorer can map a clicked mesh back to its Room. Every room is seeded
with a 360 panorama prompt (phase-2 asset hook).
"""

from __future__ import annotations

from typing import Any, Dict, List

from .layout import plate_rooms
from .schemas import BuildingSpec, Floor, Panorama, Room, Structure

# English scene phrases for seeding text-to-360 prompts (Skybox-style models).
_PANO_SCENE = {
    "reception": "a modern building reception lobby with a welcome desk",
    "meeting": "a modern meeting room with a conference table and chairs",
    "open_work": "a modern open-plan office workspace with rows of desks",
    "manager": "a private manager office with a desk and window",
    "service": "a building service and pantry utility room",
    "apartment": "a modern furnished apartment living space",
    "shop": "a modern retail shop interior with display shelves",
    "fnb": "a modern cafe and food court interior with seating",
    "classroom": "a modern classroom with desks and a whiteboard",
    "lab": "a modern laboratory with workbenches and equipment",
    "office": "a modern office room with desks and chairs",
    "default": "a modern building interior room",
}


def _seed_panorama(room_type: str) -> Panorama:
    scene = _PANO_SCENE.get(room_type, _PANO_SCENE["default"])
    prompt = (
        f"360 equirectangular interior panorama of {scene}, natural daylight, "
        "photorealistic, wide angle, no people"
    )
    return Panorama(prompt=prompt, image="", status="pending")


def build_structure(spec: BuildingSpec, floor_programs: List[List[Dict[str, Any]]]) -> Structure:
    floors: List[Floor] = []
    for i in range(spec.floors):
        templates = floor_programs[i] if i < len(floor_programs) else floor_programs[-1]
        weights = [float(t["weight"]) for t in templates]
        rects = plate_rooms(spec.footprint_w, spec.footprint_d, weights)

        rooms: List[Room] = []
        for j, (t, (x, z, w, d)) in enumerate(zip(templates, rects)):
            rooms.append(Room(
                id=f"room_{i}_{j}",
                name=f"{t['name']} (T{i + 1})",
                type=t["type"],
                x=round(x, 2), z=round(z, 2), w=round(w, 2), d=round(d, 2),
                area=round(w * d, 1),
                description=t.get("description", ""),
                panorama=_seed_panorama(t["type"]),
            ))
        floors.append(Floor(
            index=i,
            name=f"Tầng {i + 1}",
            elevation=round(i * spec.floor_height, 2),
            rooms=rooms,
        ))

    room_types = sorted({r.type for f in floors for r in f.rooms})
    return Structure(floors=floors, room_types=room_types)


def uniform_structure(spec: BuildingSpec) -> Structure:
    """LLM-free fallback (equal-size rooms, same program every floor)."""
    program = [
        {"name": f"Phòng {j + 1}", "type": "default", "weight": 1.0, "description": ""}
        for j in range(spec.rooms_per_floor)
    ]
    return build_structure(spec, [program] * spec.floors)
