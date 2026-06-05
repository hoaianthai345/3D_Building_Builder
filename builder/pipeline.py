"""Orchestration: GenerateRequest -> SceneBundle (+ .glb + .json on disk).

    spec_agent  -> BuildingSpec
    procedural  -> GLB (ModelInfo)
    describer   -> DescriberOutput
    assemble    -> SceneBundle, written next to the GLB as <id>.json

Both the CLI (run.py) and the FastAPI backend call ``generate``.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from typing import Optional

from . import procedural
from .describer import describe
from .llm import get_llm
from .llm.base import LLMClient
from .room_agent import plan_rooms
from .schemas import ArtifactIndex, GenerateRequest, RunMeta, SceneBundle
from .spec_agent import build_spec
from .structure import build_structure


def slugify(text: str) -> str:
    norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    norm = re.sub(r"[^a-zA-Z0-9]+", "-", norm).strip("-").lower()
    return norm or "scene"


def make_id(req: GenerateRequest, floors: int, rooms: int) -> str:
    return f"{slugify(req.project_name)}-{floors}f-{rooms}r"[:80]


def generate(
    req: GenerateRequest,
    out_dir: str = "artifacts",
    llm: Optional[LLMClient] = None,
    update_index: bool = True,
) -> SceneBundle:
    llm = llm or get_llm()
    spec = build_spec(req, llm)
    room_templates = plan_rooms(spec, req, llm)
    structure = build_structure(spec, room_templates)

    os.makedirs(out_dir, exist_ok=True)
    bundle_id = make_id(req, spec.floors, spec.rooms_per_floor)
    glb_path = os.path.join(out_dir, f"{bundle_id}.glb")

    model_info = procedural.build_glb(spec, glb_path, structure)
    describer_out = describe(spec, req, llm)

    bundle = SceneBundle(
        id=bundle_id,
        input=req,
        spec=spec,
        describer=describer_out,
        model=model_info,
        meta=RunMeta(llm_provider=llm.name, build_ms=round(getattr(model_info, "_build_ms", 0.0), 1)),
        structure=structure,
    )

    with open(os.path.join(out_dir, f"{bundle_id}.json"), "w", encoding="utf-8") as fh:
        json.dump(bundle.model_dump(mode="json"), fh, ensure_ascii=False, indent=2)

    if update_index:
        _refresh_index(out_dir)
    return bundle


def _refresh_index(out_dir: str) -> None:
    ids = sorted(
        os.path.splitext(f)[0]
        for f in os.listdir(out_dir)
        if f.endswith(".json") and f != "index.json"
    )
    index = ArtifactIndex(scenes=ids)
    with open(os.path.join(out_dir, "index.json"), "w", encoding="utf-8") as fh:
        json.dump(index.model_dump(mode="json"), fh, ensure_ascii=False, indent=2)
