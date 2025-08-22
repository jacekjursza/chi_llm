"""
Configuration provider API for external apps.

This module exposes a small, stable surface to
consume chi_llm configuration and model resolution
without importing heavier runtime pieces.

Public functions:
- load_config(config_path: Optional[str]) -> Dict[str, Any]
- resolve_model(config_path: Optional[str]) -> Dict[str, Any]
- get_provider_settings(config_path: Optional[str]) -> Dict[str, Any]
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load chi_llm configuration with precedence rules.

    Thin wrapper around chi_llm.utils.load_config to provide a
    stable import path for SDK consumers.
    """
    from .utils import load_config as _load

    return _load(config_path)


def resolve_model(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Resolve the effective local model configuration.

    Returns:
        Dict with keys:
        - model_id: str (effective model id)
        - model_path: str | None (downloaded path if available)
        - context_window: int
        - source: str (one of: default, local, project, global, env, custom)
    """
    result: Dict[str, Any] = {
        "model_id": "gemma-270m",
        "model_path": None,
        "context_window": 32768,
        "source": "default",
    }

    try:
        from .models import ModelManager, MODELS

        mgr = ModelManager(config_path)
        current = mgr.get_current_model()
        stats = mgr.get_model_stats()

        result["model_id"] = current.id
        result["context_window"] = int(getattr(current, "context_window", 32768))
        result["source"] = stats.get("config_source", "default")

        mp = mgr.get_model_path(current.id)
        result["model_path"] = str(mp) if mp else None

        # Ensure model id is known in registry; otherwise keep as-is
        if current.id not in MODELS:
            # Do not raise; return effective values for callers to handle
            pass
    except Exception:
        # Keep defaults if anything goes wrong; SDKs can still proceed
        pass

    return result


def get_provider_settings(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Return normalized provider settings for external integration.

    Respects environment and file configuration via utils.load_config.

    Returns a dict with at least:
    - type: 'local' | 'lmstudio' | 'ollama' | other string
    - model: str | None
    - host: str (for network providers; defaults to 127.0.0.1)
    - port: int | str (for network providers)
    - api_key: str | None (when applicable)
    - timeout: float | None
    """
    cfg = load_config(config_path) or {}
    provider = dict(cfg.get("provider") or {})

    ptype = str(provider.get("type") or "local")

    # Reasonable defaults per provider type
    if ptype == "lmstudio":
        host = str(provider.get("host", "127.0.0.1"))
        port = provider.get("port", 1234)
        timeout = float(provider.get("timeout", 30.0))
        model = provider.get("model")
        return {
            "type": ptype,
            "host": host,
            "port": port,
            "timeout": timeout,
            "model": model,
            "api_key": provider.get("api_key"),
        }
    if ptype == "ollama":
        host = str(provider.get("host", "127.0.0.1"))
        port = provider.get("port", 11434)
        timeout = float(provider.get("timeout", 30.0))
        model = provider.get("model")
        return {
            "type": ptype,
            "host": host,
            "port": port,
            "timeout": timeout,
            "model": model,
            "api_key": provider.get("api_key"),
        }

    # Default to local provider: infer model id if not specified
    if not provider.get("model"):
        try:
            eff = resolve_model(config_path)
            provider["model"] = eff.get("model_id")
        except Exception:
            provider["model"] = None

    return {
        "type": ptype,
        "model": provider.get("model"),
        "host": str(provider.get("host", "127.0.0.1")),
        "port": provider.get("port"),
        "timeout": provider.get("timeout"),
        "api_key": provider.get("api_key"),
    }


__all__ = ["load_config", "resolve_model", "get_provider_settings"]
