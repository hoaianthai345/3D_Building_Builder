"""LLM abstraction. MockLLM runs the whole pipeline offline; ClaudeLLM plugs in
when LLM_PROVIDER=claude and ANTHROPIC_API_KEY is set. Use ``get_llm()``."""

from .base import LLMClient, FallbackLLM
from .mock import MockLLM
from .factory import get_llm

__all__ = ["LLMClient", "FallbackLLM", "MockLLM", "get_llm"]
