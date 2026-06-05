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
        """Return a JSON-like dict. ``purpose`` is "spec" or "describe"."""
        raise NotImplementedError


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
