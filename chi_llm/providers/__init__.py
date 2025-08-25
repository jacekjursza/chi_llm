"""
Provider interfaces for chi_llm.

This package defines the minimal Provider protocol used to abstract
different backends (local llama.cpp, LM Studio, Ollama, external APIs).

Implementations are added in separate tasks. For now, the interface
exists to unblock configuration schema and selection logic.
"""

from .base import Provider  # re-export for convenience


def discover_models_for_provider(ptype: str, **kwargs):
    """Unified entry point to discover models for a provider type.

    Returns a list of model IDs. Implemented via provider adapters when available.
    """
    p = (ptype or "").strip().lower()
    if p == "lmstudio":
        from .lmstudio import LmStudioProvider

        return LmStudioProvider.discover_models(**kwargs)
    if p == "ollama":
        from .ollama import OllamaProvider

        return OllamaProvider.discover_models(**kwargs)
    if p == "openai":
        from .openai import OpenAIProvider

        return OpenAIProvider.discover_models(**kwargs)
    if p == "anthropic":
        from .anthropic import AnthropicProvider

        return AnthropicProvider.discover_models(**kwargs)
    return []


__all__ = ["Provider", "discover_models_for_provider"]
