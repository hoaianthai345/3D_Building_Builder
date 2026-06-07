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
    if provider == "openai":
        try:
            from .openai_compatible import OpenAICompatibleLLM

            return FallbackLLM(OpenAICompatibleLLM(), mock)
        except Exception as exc:  # noqa: BLE001
            print(f"[llm] openai unavailable ({exc}); using mock")
            return mock
    if provider == "groq":
        try:
            from .openai_compatible import OpenAICompatibleLLM

            return FallbackLLM(
                OpenAICompatibleLLM(
                    api_key=os.getenv("GROQ_API_KEY"),
                    model=os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct"),
                    base_url="https://api.groq.com/openai/v1",
                    provider_name="groq",
                ),
                mock,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[llm] groq unavailable ({exc}); using mock")
            return mock
    if provider in {"gemini", "google"}:
        try:
            from .gemini import GeminiLLM

            return FallbackLLM(GeminiLLM(), mock)
        except Exception as exc:  # noqa: BLE001
            print(f"[llm] gemini unavailable ({exc}); using mock")
            return mock
    return mock


def llm_from_runtime_key(provider: str, api_key: str, model: str = "") -> LLMClient:
    """Create a per-request LLM from a user-supplied API key.

    The key is never written to disk. Unknown/empty providers use OpenAI because
    it is the most common vision-capable JSON API for this demo. Unlike env-based
    providers, runtime user keys fail loudly so the UI can show API/key errors.
    """
    provider = (provider or "openai").strip().lower()
    api_key = api_key.strip()
    model = model.strip()
    if not api_key:
        return get_llm()

    if provider in {"anthropic", "claude"}:
        from .claude import ClaudeLLM

        return ClaudeLLM(model=model or None, api_key=api_key)
    if provider in {"openai", "openai_compatible"}:
        from .openai_compatible import OpenAICompatibleLLM

        return OpenAICompatibleLLM(api_key=api_key, model=model or None)
    if provider == "groq":
        from .openai_compatible import OpenAICompatibleLLM

        return OpenAICompatibleLLM(
            api_key=api_key,
            model=model or "meta-llama/llama-4-scout-17b-16e-instruct",
            base_url="https://api.groq.com/openai/v1",
            provider_name="groq",
        )
    if provider in {"gemini", "google"}:
        from .gemini import GeminiLLM

        return GeminiLLM(api_key=api_key, model=model or None)
    raise ValueError("unsupported llm provider")
