"""Store layer for the Textual TUI.

Encapsulates configuration reads/writes and access to models metadata via
ModelManager, keeping UI widgets thin and testable.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json


def _atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


class TUIStore:
    """Thin facade over ModelManager for the TUI.

    Notes:
        - Avoid heavy imports at module import time in UI modules; importing
          ModelManager is fine here because the store is used by the TUI runtime.
        - Keep conversions to plain dicts so views don't depend on dataclasses.
    """

    def __init__(self, config_path: Optional[str] = None):
        from ..models import ModelManager  # local import to keep boundaries light

        self._mgr = ModelManager(config_path)

    # ----- Config API -----
    def get_config(self, merged: bool = True) -> Dict[str, Any]:
        """Return (merged) configuration and source info.

        Returns at least keys: default_model, preferred_context,
        preferred_max_tokens, provider (if present), source.
        """
        cfg = dict(self._mgr.config) if merged else {}
        try:
            stats = self._mgr.get_model_stats()
            cfg["source"] = stats.get("config_source", "default")
        except Exception:
            cfg["source"] = "default"
        return cfg

    def set_config(self, scope: str, key: str, value: Any) -> Dict[str, Any]:
        """Set a configuration key and write atomically.

        Args:
            scope: 'local' or 'global'
            key: config key to set
            value: new value; basic int coercion for known numeric keys
        Returns:
            Updated config dict (merged)
        """
        # Coerce simple numeric types
        if key in {"preferred_context", "preferred_max_tokens"}:
            try:
                value = int(value)
            except Exception:
                pass

        cfg = dict(self._mgr.config)
        cfg[key] = value

        if scope == "local":
            target = Path.cwd() / ".chi_llm.json"
        else:
            target = self._mgr.config_file

        _atomic_write_json(target, cfg)

        # Reload manager config to keep memory state in sync
        self._mgr.load_config()
        return dict(self._mgr.config)

    # ----- Models API -----
    def list_models(self, show_all: bool = False) -> List[Dict[str, Any]]:
        """List models summarized for UI consumption."""
        from ..models import ModelInfo  # type: ignore

        items: List[Dict[str, Any]] = []
        for m in self._mgr.list_models(show_all=show_all):
            # m is ModelInfo (dataclass)
            if isinstance(m, ModelInfo):
                d = asdict(m)
            else:  # pragma: no cover - defensive if API mocked differently
                d = {
                    "id": getattr(m, "id", None),
                    "name": getattr(m, "name", None),
                    "size": getattr(m, "size", None),
                    "file_size_mb": getattr(m, "file_size_mb", None),
                    "context_window": getattr(m, "context_window", None),
                    "recommended_ram_gb": getattr(m, "recommended_ram_gb", None),
                    "tags": list(getattr(m, "tags", []) or []),
                }
            d["downloaded"] = bool(self._mgr.is_downloaded(d["id"]))
            items.append(d)
        return items

    def get_current_model(self) -> Dict[str, Any]:
        """Return the current effective model summary and source info."""
        cur = self._mgr.get_current_model()
        stats = {}
        try:
            stats = self._mgr.get_model_stats()
        except Exception:
            stats = {"config_source": "default"}
        return {
            "id": getattr(cur, "id", None),
            "name": getattr(cur, "name", None),
            "context_window": getattr(cur, "context_window", None),
            "recommended_ram_gb": getattr(cur, "recommended_ram_gb", None),
            "source": stats.get("config_source", "default"),
        }

    def set_default_model(self, model_id: str, scope: str = "local") -> Dict[str, Any]:
        """Set the default model and persist to requested scope."""
        self._mgr.set_default_model(model_id, save_target=scope)
        # Reload to reflect new config
        self._mgr.load_config()
        return self.get_current_model()

    def is_downloaded(self, model_id: str) -> bool:
        """Return whether the model is downloaded."""
        return self._mgr.is_downloaded(model_id)

    def download_model(self, model_id: str) -> str:
        """Download a model via Hugging Face and mark as downloaded.

        Returns the local file path on success.
        Raises RuntimeError on failure with a user-friendly message.
        """
        try:
            # Lazy imports to keep dependencies optional until needed
            from huggingface_hub import hf_hub_download
            from ..models import MODEL_DIR  # type: ignore
        except Exception as e:  # pragma: no cover - import error path
            raise RuntimeError(f"Download prerequisites missing: {e}")

        repo, filename = self._mgr.get_download_info(model_id)
        try:
            MODEL_DIR.mkdir(parents=True, exist_ok=True)
            path = hf_hub_download(
                repo_id=repo,
                filename=filename,
                local_dir=str(MODEL_DIR),
                resume_download=True,
            )
            self._mgr.mark_downloaded(model_id)
            return path
        except Exception as e:  # pragma: no cover - network dependent
            raise RuntimeError(f"Failed to download model '{model_id}': {e}")

    # ----- Provider config API -----
    def get_provider(self) -> Dict[str, Any]:
        """Return normalized provider configuration from merged config.

        Keys: type, model, host, port, api_key (masked/None), timeout
        """
        cfg = self.get_config()
        raw = dict(cfg.get("provider") or {})
        ptype = str(raw.get("type") or "local")
        out = {
            "type": ptype,
            "model": raw.get("model"),
            "host": raw.get("host", "127.0.0.1"),
            "port": raw.get("port"),
            "timeout": raw.get("timeout"),
            "api_key": raw.get("api_key"),
        }
        return out

    def set_provider(self, scope: str, provider: Dict[str, Any]) -> Dict[str, Any]:
        """Persist provider configuration atomically and reload manager config."""
        if scope == "local":
            target = Path.cwd() / ".chi_llm.json"
        else:
            target = self._mgr.config_file
        existing: Dict[str, Any] = {}
        if target.exists():
            try:
                existing = json.loads(target.read_text(encoding="utf-8"))
            except Exception:
                existing = {}
        existing["provider"] = dict(provider)
        _atomic_write_json(target, existing)
        # Reload in-memory
        self._mgr.load_config()
        return self.get_provider()

    def test_connection(
        self, provider: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Test connectivity for known providers (lmstudio/ollama).

        Returns dict: {type, host, port, ok, models_count}
        """
        prov = dict(provider or self.get_provider() or {})
        ptype = prov.get("type")
        host = str(prov.get("host", "127.0.0.1"))
        port = prov.get("port", 0)
        try:
            if ptype == "lmstudio":
                from ..providers.discovery import list_lmstudio_models

                models = list_lmstudio_models(host, port)
                return {
                    "type": ptype,
                    "host": host,
                    "port": port,
                    "ok": bool(models),
                    "models_count": len(models),
                }
            if ptype == "ollama":
                from ..providers.discovery import list_ollama_models

                models = list_ollama_models(host, port)
                return {
                    "type": ptype,
                    "host": host,
                    "port": port,
                    "ok": bool(models),
                    "models_count": len(models),
                }
        except Exception as e:  # pragma: no cover - network dependent
            return {
                "type": ptype,
                "host": host,
                "port": port,
                "ok": False,
                "error": str(e),
            }
        # Default for local/unknown: not applicable but ok
        return {
            "type": ptype or "local",
            "host": host,
            "port": port,
            "ok": True,
            "models_count": 0,
        }

    # ----- Diagnostics API -----
    def get_diagnostics(self) -> Dict[str, Any]:
        """Return environment diagnostics (delegates to diagnostics module)."""
        try:
            from ..cli_modules import diagnostics as diag  # type: ignore

            if hasattr(diag, "_gather"):
                return diag._gather()  # type: ignore[attr-defined]
        except Exception:
            pass
        return {
            "python": {"ok": True},
            "node": {"ok": False},
            "cache": {},
            "model": {},
            "network": {},
        }

    def export_diagnostics(self, path: Union[str, Path]) -> Path:
        """Export diagnostics as JSON to the given path and return it."""
        p = Path(path)
        data = self.get_diagnostics()
        _atomic_write_json(p, data)
        return p
