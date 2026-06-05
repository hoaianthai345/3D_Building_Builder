"""room_agent: propose the room program PER FLOOR (LLM-driven).

For a single-use building every floor shares one program. For a mixed-use tower
the floors are split into bands (retail podium -> office -> residential) and each
band gets its own program. Each program is a list (length rooms_per_floor) of
{name, type, weight, description}; weight drives the non-uniform layout.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .llm.base import LLMClient
from .prompts import rooms_prompt
from .schemas import BuildingSpec, GenerateRequest, SpaceType

_VALID_TYPES = {
    "reception", "meeting", "open_work", "manager", "service",
    "apartment", "shop", "fnb", "classroom", "lab", "office", "default",
}


def _normalize(rooms: Any, n: int) -> List[Dict[str, Any]]:
    if not isinstance(rooms, list) or not rooms:
        rooms = [{"name": "Phòng", "type": "default", "weight": 1.0, "description": ""}]
    out: List[Dict[str, Any]] = []
    for i in range(n):
        r = dict(rooms[i % len(rooms)])
        out.append({
            "name": str(r.get("name") or "Phòng"),
            "type": r.get("type") if r.get("type") in _VALID_TYPES else "default",
            "weight": max(0.3, float(r.get("weight") or 1.0)),
            "description": str(r.get("description") or ""),
        })
    return out


def _ask_program(llm: LLMClient, band_type: str, spec: BuildingSpec, req: GenerateRequest) -> List[Dict[str, Any]]:
    ctx = {
        "space_type": band_type,
        "rooms_per_floor": spec.rooms_per_floor,
        "project_name": req.project_name,
        "description": req.description,
    }
    data = llm.complete_json(purpose="rooms", context=ctx, prompt=rooms_prompt(spec, req))
    return _normalize(data.get("rooms") if isinstance(data, dict) else None, spec.rooms_per_floor)


def _mixed_bands(floors: int) -> List[Tuple[int, str]]:
    """(count, band_type) covering all floors: retail podium -> office -> residential."""
    retail = max(1, round(floors * 0.10))
    residential = max(1, round(floors * 0.33))
    office = max(1, floors - retail - residential)
    # fix rounding so the bands sum to exactly `floors`
    total = retail + office + residential
    office += floors - total
    return [(retail, "retail"), (office, "office"), (residential, "residential")]


def plan_floor_programs(spec: BuildingSpec, req: GenerateRequest, llm: LLMClient) -> List[List[Dict[str, Any]]]:
    if spec.space_type == SpaceType.mixed:
        programs: List[List[Dict[str, Any]]] = []
        for count, band_type in _mixed_bands(spec.floors):
            prog = _ask_program(llm, band_type, spec, req)
            programs.extend([prog] * count)
        return programs[: spec.floors]

    prog = _ask_program(llm, spec.space_type.value, spec, req)
    return [prog] * spec.floors
