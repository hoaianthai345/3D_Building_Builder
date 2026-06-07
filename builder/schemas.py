"""Frozen data contract for the AI 3D Scene Describer.

This module is the single source of truth shared by:
    - the builder pipeline (spec_agent / procedural / describer),
    - the FastAPI backend (request + response shapes),
    - the frontend (reads SceneBundle JSON artifacts from /public/artifacts).

Rule for multi-agent work (see WORKFLOW.md): agents on the FE / DOCS lanes MUST NOT
change field names here. If the contract truly must change, bump ``SCHEMA_VERSION``
and re-sync the sample fixtures.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

SCHEMA_VERSION = "1.1"


class SpaceType(str, Enum):
    """Loại không gian số hóa. Giá trị khớp với <select> ở trang demo."""

    office = "office"
    residential = "residential"
    retail = "retail"
    mixed = "mixed"
    education = "education"


# --------------------------------------------------------------------------- #
# 1. Input — what the form / API receives                                     #
# --------------------------------------------------------------------------- #
class GenerateRequest(BaseModel):
    """Payload of ``POST /api/generate`` and the ``input`` block of a SceneBundle."""

    project_name: str = Field(..., min_length=1, max_length=120)
    space_type: SpaceType = SpaceType.office
    description: str = Field("", max_length=2000)
    target_audience: str = Field("", max_length=300)

    # Optional numeric params. When omitted, spec_agent infers them from the
    # natural-language ``description`` (e.g. "5 tầng, mỗi tầng 6 phòng").
    floors: Optional[int] = Field(None, ge=1, le=120)
    rooms_per_floor: Optional[int] = Field(None, ge=1, le=60)
    occupancy: Optional[int] = Field(None, ge=0, le=100_000)

    @field_validator("project_name")
    @classmethod
    def _project_name_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("project_name is required")
        return cleaned


# --------------------------------------------------------------------------- #
# 2. Spec — normalized building parameters that drive the 3D builder          #
# --------------------------------------------------------------------------- #
class BuildingSpec(BaseModel):
    """Fully resolved parameters. Every field is concrete (no None) so the
    procedural builder and the generative backend get the same contract."""

    space_type: SpaceType = SpaceType.office
    floors: int = Field(..., ge=1, le=120)
    rooms_per_floor: int = Field(..., ge=1, le=60)
    occupancy: int = Field(0, ge=0, le=100_000)

    # Meters. Footprint is derived from rooms/occupancy when not given.
    footprint_w: float = Field(..., gt=0, le=400)
    footprint_d: float = Field(..., gt=0, le=400)
    floor_height: float = Field(3.2, gt=2.0, le=8.0)

    layout_hint: str = Field("central-core", max_length=120)
    palette: str = Field("blue", max_length=24)

    @property
    def total_height(self) -> float:
        return self.floors * self.floor_height


# --------------------------------------------------------------------------- #
# 3. Describer — the AI marketing copy (assignment core output)               #
# --------------------------------------------------------------------------- #
class DescriberOutput(BaseModel):
    """Tiêu đề + mô tả + 3-5 điểm nổi bật + lưu ý số hóa 3D."""

    title: str = Field(..., min_length=1, max_length=200)
    summary: str = Field(..., min_length=1, max_length=1200)
    highlights: List[str] = Field(..., min_length=3, max_length=5)
    digitization_tips: List[str] = Field(..., min_length=2, max_length=8)

    @field_validator("highlights", "digitization_tips")
    @classmethod
    def _no_blank_items(cls, items: List[str]) -> List[str]:
        cleaned = [s.strip() for s in items if s and s.strip()]
        if not cleaned:
            raise ValueError("list must contain at least one non-empty item")
        return cleaned


# --------------------------------------------------------------------------- #
# 4. Model + meta — the generated 3D asset and run provenance                 #
# --------------------------------------------------------------------------- #
class ModelInfo(BaseModel):
    glb: str = Field(..., description="GLB filename, served from /artifacts/<glb>")
    backend: str = Field("procedural", description="procedural | generative")
    tri_count: int = Field(0, ge=0)
    size_kb: float = Field(0.0, ge=0)


class RunMeta(BaseModel):
    llm_provider: str = "mock"
    build_ms: float = Field(0.0, ge=0)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# --------------------------------------------------------------------------- #
# 4b. Structure tree — drives the "drill into floors/rooms" explorer (v1.1)   #
# --------------------------------------------------------------------------- #
class Panorama(BaseModel):
    """360 asset hook for the "step inside" tour (phase 2). The builder seeds a
    prompt; an image generator (e.g. Skybox AI) later fills ``image`` + status."""

    prompt: str = ""             # text-to-360 prompt for this room
    image: str = ""              # filename/URL once generated (pano/<room_id>.jpg)
    status: str = "pending"      # pending | ready


class Room(BaseModel):
    """One room on a floor plate. Rectangle in meters on the XZ plane, with the
    building centered at the origin (x,z = min corner; w along X, d along Z)."""

    id: str                      # e.g. "room_2_3" -> matches the GLB node name
    name: str                    # e.g. "Phòng họp 3-2"
    type: str                    # reception | meeting | open_work | apartment | shop | classroom | service
    x: float
    z: float
    w: float
    d: float
    area: float = Field(0.0, ge=0)
    description: str = ""
    panorama: Optional[Panorama] = None


class Floor(BaseModel):
    index: int = Field(..., ge=0)
    name: str                    # e.g. "Tầng 3"
    elevation: float             # y of the floor slab (meters)
    rooms: List[Room] = Field(default_factory=list)


class Structure(BaseModel):
    """Building -> floors -> rooms. Optional: present from schema v1.1 onward."""

    floors: List[Floor] = Field(default_factory=list)
    room_types: List[str] = Field(default_factory=list)  # legend for the explorer


# --------------------------------------------------------------------------- #
# 5. SceneBundle — the artifact the demo reads (one .json per generation)     #
# --------------------------------------------------------------------------- #
class SceneBundle(BaseModel):
    id: str = Field(..., min_length=1, max_length=80)
    version: str = SCHEMA_VERSION
    input: GenerateRequest
    spec: BuildingSpec
    describer: DescriberOutput
    model: ModelInfo
    meta: RunMeta = Field(default_factory=RunMeta)
    structure: Optional[Structure] = None


class ArtifactIndex(BaseModel):
    """`/public/artifacts/index.json` — list the frontend iterates over."""

    version: str = SCHEMA_VERSION
    scenes: List[str] = Field(default_factory=list, description="bundle ids / filenames")


# --------------------------------------------------------------------------- #
# 6. Guided tour — AI vision describe per stop + narrated walkthrough          #
# --------------------------------------------------------------------------- #
class IndustryTone(str, Enum):
    """Tone of voice for the AI narration."""

    real_estate = "real_estate"   # bất động sản
    retail = "retail"             # bán lẻ
    exhibition = "exhibition"     # triển lãm


class StopDescribe(BaseModel):
    """AI vision output for one uploaded view."""

    title: str = Field(..., min_length=1, max_length=160)
    description: str = Field(..., min_length=1, max_length=1200)
    highlights: List[str] = Field(..., min_length=3, max_length=5)

    @field_validator("highlights")
    @classmethod
    def _clean_highlights(cls, items: List[str]) -> List[str]:
        cleaned = [s.strip() for s in items if s and s.strip()]
        if len(cleaned) < 3:
            raise ValueError("need at least 3 highlights")
        return cleaned[:5]


class TourStop(BaseModel):
    id: str
    image: str                    # URL / artifact path of the view
    kind: str = "photo"           # photo | panorama
    describe: StopDescribe
    narration: str                # spoken text for this stop


class Tour(BaseModel):
    id: str
    project_name: str
    industry: IndustryTone = IndustryTone.real_estate
    intro: str
    stops: List[TourStop] = Field(default_factory=list)
    outro: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
