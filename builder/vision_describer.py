"""Vision describer: an uploaded view image -> StopDescribe (title + description +
3-5 highlights), in a tone appropriate to the industry (real estate / retail /
exhibition). Claude multimodal "sees" the image; MockLLM falls back to
industry-templated copy so it still runs offline.
"""

from __future__ import annotations

from typing import Optional

from .llm import get_llm
from .llm.base import LLMClient
from .schemas import IndustryTone, StopDescribe

_INDUSTRY_VI = {
    IndustryTone.real_estate: "bất động sản",
    IndustryTone.retail: "bán lẻ",
    IndustryTone.exhibition: "triển lãm",
}


def vision_prompt(industry: IndustryTone, hint: str = "") -> str:
    vi = _INDUSTRY_VI.get(industry, "không gian")
    extra = f" Bối cảnh thêm: {hint}." if hint else ""
    return (
        f"Bạn là chuyên gia thuyết minh không gian cho ngành {vi}. Nhìn kỹ ảnh không gian "
        "và trả về DUY NHẤT một JSON với khóa: title (tiêu đề ngắn), description (1 đoạn "
        "mô tả hấp dẫn, đúng tone ngành, để đọc thành thuyết minh tour), highlights (mảng "
        f"3-5 điểm nổi bật của không gian, AI tự đề xuất). Toàn bộ tiếng Việt.{extra}"
    )


def describe_image(image_b64: str, media_type: str, industry: IndustryTone,
                   llm: Optional[LLMClient] = None, hint: str = "") -> StopDescribe:
    llm = llm or get_llm()
    data = llm.complete_json_vision(
        purpose="vision_describe",
        context={"industry": industry.value, "hint": hint},
        prompt=vision_prompt(industry, hint),
        image_b64=image_b64,
        media_type=media_type,
    )
    if isinstance(data.get("highlights"), list) and len(data["highlights"]) > 5:
        data["highlights"] = data["highlights"][:5]
    return StopDescribe.model_validate(data)
