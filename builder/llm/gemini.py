"""Google Gemini provider via the official generateContent REST endpoint."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict

import requests

from .base import LLMClient

_SYSTEM = (
    "Bạn là trợ lý tạo nội dung cho công cụ số hóa 3D. "
    "Luôn trả về DUY NHẤT một đối tượng JSON hợp lệ, không kèm giải thích, không markdown. "
    "Toàn bộ giá trị chuỗi phải bằng tiếng Việt tự nhiên."
)


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ValueError("no JSON object found in Gemini output")
        return json.loads(match.group(0))


class GeminiLLM(LLMClient):
    name = "gemini"

    def __init__(self, *, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY not set")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

    def _post(self, parts: list[dict[str, Any]], max_tokens: int = 1200) -> Dict[str, Any]:
        res = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
            timeout=45,
            headers={
                "content-type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            json={
                "system_instruction": {"parts": [{"text": _SYSTEM}]},
                "contents": [{"role": "user", "parts": parts}],
                "generationConfig": {
                    "temperature": 0.4,
                    "maxOutputTokens": max_tokens,
                    "responseMimeType": "application/json",
                },
            },
        )
        if res.status_code >= 400:
            raise RuntimeError(f"Gemini API returned {res.status_code}: {res.text[:300]}")
        body = res.json()
        parts_out = body["candidates"][0]["content"].get("parts", [])
        text = "".join(str(part.get("text", "")) for part in parts_out)
        return _extract_json(text)

    def complete_json(self, *, purpose: str, context: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        return self._post([{"text": prompt}])

    def complete_json_vision(
        self,
        *,
        purpose: str,
        context: dict,
        prompt: str,
        image_b64: str,
        media_type: str,
    ) -> dict:
        return self._post([
            {"inline_data": {"mime_type": media_type, "data": image_b64}},
            {"text": prompt},
        ])
