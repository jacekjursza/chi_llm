"""
Provider interfaces for chi_llm.

This package defines the minimal Provider protocol used to abstract
different backends (local llama.cpp, LM Studio, Ollama, external APIs).

Implementations are added in separate tasks. For now, the interface
exists to unblock configuration schema and selection logic.
"""

from .base import Provider  # re-export for convenience

__all__ = ["Provider"]
