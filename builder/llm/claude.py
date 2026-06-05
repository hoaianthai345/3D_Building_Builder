"""Claude provider (Anthropic). Activated by LLM_PROVIDER=claude + ANTHROPIC_API_KEY.

Kept deliberately small: send the caller-built prompt, ask for strict JSON, parse
it. Any failure raises so FallbackLLM degrades to MockLLM (see base.py / factory.py).
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict

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
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not m:
            raise ValueError("no JSON object found in model output")
        return json.loads(m.group(0))


class ClaudeLLM(LLMClient):
    name = "claude"

    def __init__(self, model: str | None = None):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        from anthropic import Anthropic  # lazy import; optional dependency

        self.client = Anthropic(api_key=api_key)
        self.model = model or os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

    def complete_json(self, *, purpose: str, context: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=1200,
            system=_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in resp.content if getattr(block, "type", None) == "text")
        return _extract_json(text)
