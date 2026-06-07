"""LLM interface + a fallback wrapper.

``complete_json`` is intentionally generic. The caller (spec_agent / describer)
builds a text ``prompt`` for real providers AND passes a structured ``context``
(the raw inputs/spec) so the offline MockLLM can produce deterministic output
without parsing the prompt.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class LLMClient(ABC):
    name: str = "base"

    @abstractmethod
    def complete_json(self, *, purpose: str, context: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Return a JSON-like dict. ``purpose`` is "spec" / "describe" / "rooms"."""
        raise NotImplementedError

    def complete_json_vision(self, *, purpose: str, context: Dict[str, Any], prompt: str,
                             image_b64: str, media_type: str) -> Dict[str, Any]:
        """Multimodal variant. Default ignores the image and falls back to text
        (so a text-only provider still works via ``context``)."""
        return self.complete_json(purpose=purpose, context=context, prompt=prompt)


class FallbackLLM(LLMClient):
    """Try ``primary``; on any error fall back to ``fallback`` (usually MockLLM)."""

    def __init__(self, primary: LLMClient, fallback: LLMClient):
        self.primary = primary
        self.fallback = fallback
        self.name = f"{primary.name}->{fallback.name}"

    def complete_json(self, *, purpose: str, context: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        try:
            return self.primary.complete_json(purpose=purpose, context=context, prompt=prompt)
        except Exception as exc:  # noqa: BLE001 - intentional broad fallback
            print(f"[llm] primary '{self.primary.name}' failed ({exc}); falling back to '{self.fallback.name}'")
            return self.fallback.complete_json(purpose=purpose, context=context, prompt=prompt)

    def complete_json_vision(self, *, purpose: str, context: Dict[str, Any], prompt: str,
                             image_b64: str, media_type: str) -> Dict[str, Any]:
        try:
            return self.primary.complete_json_vision(
                purpose=purpose, context=context, prompt=prompt, image_b64=image_b64, media_type=media_type)
        except Exception as exc:  # noqa: BLE001
            print(f"[llm] primary vision '{self.primary.name}' failed ({exc}); falling back")
            return self.fallback.complete_json_vision(
                purpose=purpose, context=context, prompt=prompt, image_b64=image_b64, media_type=media_type)
