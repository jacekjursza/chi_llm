"""
Provider model discovery utilities.

Lists locally available models for LM Studio and Ollama providers.
Uses requests if available, falling back to urllib.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import json


def _http_get(url: str, timeout: float = 5.0) -> Dict[str, Any]:
    try:
        try:
            import requests  # type: ignore

            r = requests.get(url, timeout=timeout)
            if r.status_code >= 400:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
            return r.json()
        except ModuleNotFoundError:
            from urllib import request, error

            req = request.Request(url, headers={"Accept": "application/json"})
            try:
                with request.urlopen(req, timeout=timeout) as resp:
                    body = resp.read().decode("utf-8")
                    return json.loads(body)
            except error.HTTPError as he:  # pragma: no cover
                msg = he.read().decode("utf-8")
                raise RuntimeError(f"HTTP {he.code}: {msg[:200]}") from he
    except Exception as e:
        raise RuntimeError(str(e))


def list_lmstudio_models(
    host: str = "127.0.0.1", port: int | str = 1234
) -> List[Dict[str, Any]]:
    """List models exposed by LM Studio's local server.

    Tries OpenAI-style endpoint: GET /v1/models
    Returns: list of {id, name, size} (best-effort; size may be None)
    """
    url = f"http://{host}:{port}/v1/models"
    try:
        data = _http_get(url)
        items = []
        for m in data.get("data") or []:
            mid = m.get("id") or m.get("root") or "unknown"
            items.append({"id": mid, "name": mid, "size": None})
        return items
    except Exception:
        return []


def _bytes_to_mb_str(n: Optional[int | float]) -> Optional[str]:
    if n is None:
        return None
    try:
        mb = float(n) / (1024 * 1024)
        return f"{mb:.0f}MB"
    except Exception:
        return None


def list_ollama_models(
    host: str = "127.0.0.1", port: int | str = 11434
) -> List[Dict[str, Any]]:
    """List models installed in Ollama (GET /api/tags).

    Returns: list of {id, name, size} where size prefers parameter_size
    or falls back to file size in MB.
    """
    url = f"http://{host}:{port}/api/tags"
    try:
        data = _http_get(url)
        out: List[Dict[str, Any]] = []
        for m in data.get("models") or []:
            name = m.get("name") or "unknown"
            details = m.get("details") or {}
            param_size = details.get("parameter_size")  # e.g., "7B"
            size_bytes = m.get("size")
            size = param_size or _bytes_to_mb_str(size_bytes)
            out.append({"id": name, "name": name, "size": size})
        return out
    except Exception:
        return []


def list_provider_models(
    provider: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """List models for the configured external provider.

    If provider is None, uses chi_llm.utils.load_config() to resolve.
    Returns a list of dicts: {id, name, size}
    """
    if provider is None:
        try:
            from ..utils import load_config

            cfg = load_config() or {}
            provider = cfg.get("provider") or {}
        except Exception:
            provider = {}

    ptype = (provider or {}).get("type")
    if ptype == "lmstudio":
        host = str(provider.get("host", "127.0.0.1"))
        port = provider.get("port", 1234)
        return list_lmstudio_models(host, port)
    if ptype == "ollama":
        host = str(provider.get("host", "127.0.0.1"))
        port = provider.get("port", 11434)
        return list_ollama_models(host, port)
    # For local or unknown providers, return empty list
    return []
