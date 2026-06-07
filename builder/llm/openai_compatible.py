"""Minimal OpenAI-compatible provider using the Chat Completions API.

This avoids adding a hard SDK dependency. It supports text JSON generation and
image input via data URLs, then lets FallbackLLM degrade to MockLLM on failure.
"""

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
            raise ValueError("no JSON object found in model output")
        return json.loads(match.group(0))


class OpenAICompatibleLLM(LLMClient):
    name = "openai"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        provider_name: str = "openai",
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.name = provider_name

    def _post(self, messages: list[dict[str, Any]], max_tokens: int = 1200) -> Dict[str, Any]:
        res = requests.post(
            f"{self.base_url}/chat/completions",
            timeout=45,
            headers={
                "authorization": f"Bearer {self.api_key}",
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.4,
                "response_format": {"type": "json_object"},
            },
        )
        if res.status_code >= 400:
            raise RuntimeError(f"OpenAI-compatible API returned {res.status_code}: {res.text[:300]}")
        body = res.json()
        return _extract_json(body["choices"][0]["message"]["content"])

    def complete_json(self, *, purpose: str, context: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        return self._post([
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": prompt},
        ])

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
            {"role": "system", "content": _SYSTEM},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{media_type};base64,{image_b64}"},
                    },
                ],
            },
        ])
