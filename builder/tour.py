"""Tour assembler: ordered stops (each with a StopDescribe) -> a narrated Tour.

The deterministic ``assemble_tour`` is the fallback. ``generate_tour`` asks the
configured LLM to write guide-style narration, then validates and falls back to
the deterministic path if the provider returns unusable JSON.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Optional

from .llm import get_llm
from .llm.base import LLMClient
from .schemas import IndustryTone, StopDescribe, Tour, TourStop

_INTRO = {
    IndustryTone.real_estate: "Xin chào và chào mừng quý khách đến với {name}. Mời quý khách cùng tham quan {n} không gian nổi bật của dự án.",
    IndustryTone.retail: "Chào mừng đến với {name}. Mời bạn dạo qua {n} khu vực ấn tượng của không gian này.",
    IndustryTone.exhibition: "Chào mừng bạn đến với {name}. Hành trình tham quan gồm {n} điểm dừng đang chờ bạn khám phá.",
}
_OUTRO = {
    IndustryTone.real_estate: "Cảm ơn quý khách đã tham quan {name}. Hẹn gặp lại quý khách tại không gian thực tế.",
    IndustryTone.retail: "Cảm ơn bạn đã dạo qua {name}. Chúc bạn có những trải nghiệm thật thú vị.",
    IndustryTone.exhibition: "Cảm ơn bạn đã đồng hành cùng hành trình tại {name}. Hẹn gặp lại ở những triển lãm tiếp theo.",
}


def _slug(text: str) -> str:
    norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9]+", "-", norm).strip("-").lower() or "tour"


def _narration(d: StopDescribe) -> str:
    hi = " ".join(f"Điểm nổi bật: {h.rstrip('.')}." for h in d.highlights[:3])
    return f"{d.title}. {d.description} {hi}".strip()


def assemble_tour(project_name: str, industry: IndustryTone,
                  stops_in: List[Dict[str, Any]]) -> Tour:
    stops: List[TourStop] = []
    for s in stops_in:
        d = s["describe"]
        d = d if isinstance(d, StopDescribe) else StopDescribe.model_validate(d)
        stops.append(TourStop(
            id=str(s["id"]), image=str(s["image"]), kind=str(s.get("kind", "photo")),
            describe=d, narration=_narration(d),
        ))
    n = len(stops)
    return Tour(
        id=f"{_slug(project_name)}-tour",
        project_name=project_name,
        industry=industry,
        intro=_INTRO.get(industry, _INTRO[IndustryTone.real_estate]).format(name=project_name, n=n),
        outro=_OUTRO.get(industry, _OUTRO[IndustryTone.real_estate]).format(name=project_name),
        stops=stops,
    )


def _tour_prompt(project_name: str, industry: IndustryTone, stops: List[Dict[str, Any]]) -> str:
    lines = []
    for i, stop in enumerate(stops, start=1):
        d = stop["describe"]
        d = d if isinstance(d, StopDescribe) else StopDescribe.model_validate(d)
        lines.append(
            f"{i}. id={stop['id']}\n"
            f"   title={d.title}\n"
            f"   description={d.description}\n"
            f"   highlights={'; '.join(d.highlights)}"
        )
    return (
        "Bạn là hướng dẫn viên ảo cho một tour tham quan 3D. "
        "Dựa trên các điểm dừng đã được AI vision mô tả, hãy viết lời dẫn tự nhiên, "
        "có chuyển cảnh giữa các điểm, phù hợp để đọc thành giọng nói tiếng Việt.\n\n"
        "Trả DUY NHẤT một JSON object với schema:\n"
        "{ \"intro\": string, \"stops\": [{\"id\": string, \"narration\": string}], \"outro\": string }\n\n"
        "Yêu cầu:\n"
        "- intro 2-3 câu, giới thiệu mục tiêu hành trình.\n"
        "- mỗi narration 3-5 câu, nhắc đúng điểm nổi bật, không phóng đại quá mức.\n"
        "- outro 1-2 câu, kết lại như hướng dẫn viên.\n"
        "- Không markdown, không bullet trong narration.\n\n"
        f"Tên dự án: {project_name}\n"
        f"Ngành/tone: {industry.value}\n"
        "Các điểm dừng:\n"
        + "\n".join(lines)
    )


def generate_tour(project_name: str, industry: IndustryTone,
                  stops_in: List[Dict[str, Any]],
                  llm: Optional[LLMClient] = None) -> Tour:
    fallback = assemble_tour(project_name, industry, stops_in)
    if not stops_in:
        return fallback

    llm = llm or get_llm()
    context_stops = []
    for s in stops_in:
        d = s["describe"]
        d = d if isinstance(d, StopDescribe) else StopDescribe.model_validate(d)
        context_stops.append({
            "id": str(s["id"]),
            "image": str(s["image"]),
            "kind": str(s.get("kind", "photo")),
            "describe": d.model_dump(mode="json"),
        })

    data = llm.complete_json(
        purpose="tour",
        context={
            "project_name": project_name,
            "industry": industry.value,
            "stops": context_stops,
        },
        prompt=_tour_prompt(project_name, industry, context_stops),
    )

    by_id = {
        str(item.get("id")): str(item.get("narration") or "").strip()
        for item in data.get("stops", [])
        if isinstance(item, dict)
    }

    stops: List[TourStop] = []
    for fallback_stop in fallback.stops:
        narration = by_id.get(fallback_stop.id) or fallback_stop.narration
        stops.append(fallback_stop.model_copy(update={"narration": narration}))

    intro = str(data.get("intro") or "").strip() or fallback.intro
    outro = str(data.get("outro") or "").strip() or fallback.outro
    return fallback.model_copy(update={"intro": intro, "stops": stops, "outro": outro})
