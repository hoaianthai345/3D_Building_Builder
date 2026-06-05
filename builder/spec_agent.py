"""spec_agent: GenerateRequest -> BuildingSpec.

The LLM (mock or claude) fills missing numeric params from the natural-language
description; explicit form fields always win. Footprint is derived from the room
count so the 3D massing scales with the input.
"""

from __future__ import annotations

import math

from .llm.base import LLMClient
from .prompts import spec_prompt
from .schemas import BuildingSpec, GenerateRequest

_ROOM_AREA_M2 = 18.0      # usable area assumed per room
_CORE_FACTOR = 1.25       # circulation/core overhead on the floor plate
_ASPECT = 1.5             # footprint width:depth ratio


def _footprint(rooms_per_floor: int) -> tuple[float, float]:
    plate = rooms_per_floor * _ROOM_AREA_M2 * _CORE_FACTOR
    width = math.sqrt(plate * _ASPECT)
    depth = plate / width
    # keep within schema bounds and avoid absurdly thin plates
    width = max(8.0, min(width, 400.0))
    depth = max(6.0, min(depth, 400.0))
    return round(width, 1), round(depth, 1)


def build_spec(req: GenerateRequest, llm: LLMClient) -> BuildingSpec:
    hints = llm.complete_json(
        purpose="spec",
        context=req.model_dump(mode="json"),
        prompt=spec_prompt(req),
    )

    floors = req.floors or int(hints.get("floors") or 3)
    rooms = req.rooms_per_floor or int(hints.get("rooms_per_floor") or 4)
    occupancy = req.occupancy if req.occupancy is not None else int(hints.get("occupancy") or rooms * floors * 4)

    width, depth = _footprint(rooms)
    return BuildingSpec(
        space_type=req.space_type,
        floors=floors,
        rooms_per_floor=rooms,
        occupancy=occupancy,
        footprint_w=width,
        footprint_d=depth,
        layout_hint=str(hints.get("layout_hint") or "central-core")[:120],
        palette="blue",
    )
