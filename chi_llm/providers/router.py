"""
Multi-provider router with tag-based selection and fallback.

Reads provider profiles from configuration and routes calls to the first
matching provider. On error, falls back to the next candidate.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional


class ProviderRouter:
    """
    Lightweight router for multiple providers.

    profiles: list of dicts with keys like:
      - name: str (identifier)
      - type: str (local|lmstudio|ollama|...)
      - host, port, model, api_key, timeout: optional, provider-specific
      - tags: list[str]
      - priority: int (lower runs first; default 100)

    registry: mapping provider type -> factory(profile_dict) -> Provider
    """

    def __init__(
        self,
        profiles: List[Dict[str, Any]],
        registry: Optional[Dict[str, Callable[[Dict[str, Any]], Any]]] = None,
    ) -> None:
        self.profiles = list(profiles or [])
        self.registry = registry or default_registry()

    # --- public API ---
    def generate(self, prompt: str, tags: Optional[List[str]] = None, **kwargs) -> str:
        for prov, meta in self._iter_candidates(tags):
            try:
                return prov.generate(prompt, **kwargs)
            except Exception:
                continue
        raise RuntimeError("All providers failed for generate()")

    def chat(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        for prov, meta in self._iter_candidates(tags):
            try:
                return prov.chat(message, history=history)
            except Exception:
                continue
        raise RuntimeError("All providers failed for chat()")

    def complete(self, text: str, tags: Optional[List[str]] = None, **kwargs) -> str:
        for prov, meta in self._iter_candidates(tags):
            try:
                return prov.complete(text, **kwargs)
            except Exception:
                continue
        raise RuntimeError("All providers failed for complete()")

    # --- internals ---
    def _iter_candidates(self, tags: Optional[List[str]]):
        for profile in self._sorted_profiles(tags):
            ptype = profile.get("type")
            factory = self.registry.get(str(ptype))
            if not factory:
                continue
            try:
                yield factory(profile), profile
            except Exception:
                # If factory fails (e.g., missing deps), move on
                continue

    def _sorted_profiles(
        self, tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        wanted = set((tags or [])[:])
        for p in self.profiles:
            ptags = set(p.get("tags") or [])
            if not wanted or ptags.intersection(wanted):
                candidates.append(p)
        return sorted(candidates, key=lambda p: int(p.get("priority", 100)))


def default_registry() -> Dict[str, Callable[[Dict[str, Any]], Any]]:
    """Default provider factories by type."""
    reg: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
    try:
        from .lmstudio import LmStudioProvider  # type: ignore

        reg["lmstudio"] = lambda prof: LmStudioProvider(
            host=str(prof.get("host", "127.0.0.1")),
            port=prof.get("port", 1234),
            model=prof.get("model"),
            timeout=float(prof.get("timeout", 30.0)),
        )
    except Exception:
        pass
    try:
        from .ollama import OllamaProvider  # type: ignore

        reg["ollama"] = lambda prof: OllamaProvider(
            host=str(prof.get("host", "127.0.0.1")),
            port=prof.get("port", 11434),
            model=prof.get("model"),
            timeout=float(prof.get("timeout", 30.0)),
        )
    except Exception:
        pass
    # 'local' intentionally lacks factory here; handled by MicroLLM
    return reg
