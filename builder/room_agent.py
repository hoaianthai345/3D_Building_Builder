"""room_agent: propose the room program for a typical floor (LLM-driven).

Returns a list of length ``rooms_per_floor`` with: name, type, weight (relative
size, drives the non-uniform layout) and a short description. MockLLM fills this
from per-space templates; a real LLM can return a richer, context-aware program.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .llm.base import LLMClient
from .prompts import rooms_prompt
from .schemas import BuildingSpec, GenerateRequest

_VALID_TYPES = {
    "reception", "meeting", "open_work", "manager", "service",
    "apartment", "shop", "fnb", "classroom", "lab", "office", "default",
}


def plan_rooms(spec: BuildingSpec, req: GenerateRequest, llm: LLMClient) -> List[Dict[str, Any]]:
    ctx = {
        "space_type": spec.space_type.value,
        "rooms_per_floor": spec.rooms_per_floor,
        "project_name": req.project_name,
        "description": req.description,
    }
    data = llm.complete_json(purpose="rooms", context=ctx, prompt=rooms_prompt(spec, req))
    rooms = data.get("rooms") if isinstance(data, dict) else None
    if not isinstance(rooms, list) or not rooms:
        rooms = [{"name": "Phòng", "type": "default", "weight": 1.0, "description": ""}]

    out: List[Dict[str, Any]] = []
    for i in range(spec.rooms_per_floor):
        r = dict(rooms[i % len(rooms)])  # cycle templates to fill the count
        out.append({
            "name": str(r.get("name") or "Phòng"),
            "type": r.get("type") if r.get("type") in _VALID_TYPES else "default",
            "weight": max(0.3, float(r.get("weight") or 1.0)),
            "description": str(r.get("description") or ""),
        })
    return out
