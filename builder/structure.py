"""Assemble the Structure tree (building -> floors -> rooms).

The room program (types + weights) comes from room_agent; the geometric packing
comes from layout.plate_rooms. Room ids match the GLB node names exactly so the
frontend explorer can map a clicked mesh back to its Room.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .layout import plate_rooms
from .schemas import BuildingSpec, Floor, Room, Structure


def build_structure(spec: BuildingSpec, room_templates: List[Dict[str, Any]]) -> Structure:
    weights = [float(t["weight"]) for t in room_templates]
    rects = plate_rooms(spec.footprint_w, spec.footprint_d, weights)

    floors: List[Floor] = []
    for i in range(spec.floors):
        rooms: List[Room] = []
        for j, (t, (x, z, w, d)) in enumerate(zip(room_templates, rects)):
            rooms.append(Room(
                id=f"room_{i}_{j}",
                name=f"{t['name']} (T{i + 1})",
                type=t["type"],
                x=round(x, 2), z=round(z, 2), w=round(w, 2), d=round(d, 2),
                area=round(w * d, 1),
                description=t.get("description", ""),
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
    """LLM-free fallback (equal-size rooms). Lets the builder run standalone."""
    templates = [
        {"name": f"Phòng {j + 1}", "type": "default", "weight": 1.0, "description": ""}
        for j in range(spec.rooms_per_floor)
    ]
    return build_structure(spec, templates)
