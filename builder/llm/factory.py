"""Choose the LLM provider from the environment.

    LLM_PROVIDER=mock    (default) -> MockLLM, fully offline
    LLM_PROVIDER=claude            -> ClaudeLLM with MockLLM as runtime fallback

If claude is requested but unavailable (no key / no SDK), we log and use mock so the
pipeline never hard-fails during a demo.
"""

from __future__ import annotations

import os

from .base import FallbackLLM, LLMClient
from .mock import MockLLM


def get_llm() -> LLMClient:
    provider = os.getenv("LLM_PROVIDER", "mock").lower()
    mock = MockLLM()
    if provider == "claude":
        try:
            from .claude import ClaudeLLM

            return FallbackLLM(ClaudeLLM(), mock)
        except Exception as exc:  # noqa: BLE001
            print(f"[llm] claude unavailable ({exc}); using mock")
            return mock
    return mock
