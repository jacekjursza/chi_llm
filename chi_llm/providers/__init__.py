"""
Provider interfaces for chi_llm.

This package defines the minimal Provider protocol used to abstract
different backends (local llama.cpp, LM Studio, Ollama, external APIs).

Implementations are added in separate tasks. For now, the interface
exists to unblock configuration schema and selection logic.
"""

from .base import Provider  # re-export for convenience
from pathlib import Path
from typing import List
import os
from chi_llm.utils import load_config


def discover_models_for_provider(ptype: str, **kwargs):
    """Unified entry point to discover models for a provider type.

    Returns a list of model IDs. Implemented via provider adapters when available.
    """
    p = (ptype or "").strip().lower()
    if p == "local":
        # Return curated catalog model ids only (auto-download friendly)
        try:
            from chi_llm.models import MODELS

            return list(MODELS.keys())
        except Exception:
            return []
    if p == "local-custom":
        # Return only discovered GGUF file paths from configured roots
        try:
            cfg = load_config()
            roots = cfg.get("auto_discovery_gguf_paths") or []
            ids: List[str] = []
            if isinstance(roots, str):
                roots = [roots]
            for root in roots:
                try:
                    rp = Path(os.path.expanduser(str(root))).resolve()
                    if rp.exists() and rp.is_dir():
                        for pth in rp.rglob("*.gguf"):
                            try:
                                s = str(pth)
                                ids.append(s)
                            except Exception:
                                continue
                except Exception:
                    continue
            return ids
        except Exception:
            return []
    if p in ("local-zeroconfig", "local-no-config"):
        # Return recommended/default subset for zero-config
        try:
            from chi_llm.models import MODELS

            ids = []
            for mid, mi in MODELS.items():
                tags = getattr(mi, "tags", []) or []
                if "recommended" in tags or "default" in tags:
                    ids.append(mid)
            return ids
        except Exception:
            return []
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
