"""Provider discovery helpers for CLI (split to keep file sizes small)."""

from typing import Any, List
import json as _json
import os

from chi_llm.providers import discover_models_for_provider


def _print_json(obj: Any) -> None:
    print(_json.dumps(obj, indent=2))


def _out_models(args, ptype: str, ids: List[str]):
    items = [{"id": mid} for mid in ids]
    obj = {"provider": ptype, "models": items}
    if getattr(args, "json", False):
        _print_json(obj)
    else:
        print(f"Models ({len(items)}):")
        for m in items:
            print(f" - {m['id']}")


def cmd_discover_models(args):
    ptype = (getattr(args, "ptype", "") or "").strip().lower()

    try:
        if ptype == "lmstudio":
            host = (
                getattr(args, "host", None)
                or os.environ.get("LMSTUDIO_HOST")
                or "localhost"
            )
            port = getattr(args, "port", None) or os.environ.get("LMSTUDIO_PORT")
            ids = discover_models_for_provider("lmstudio", host=host, port=port)
            return _out_models(args, ptype, ids)

        if ptype == "ollama":
            host = (
                getattr(args, "host", None)
                or os.environ.get("OLLAMA_HOST")
                or "localhost"
            )
            port = getattr(args, "port", None) or os.environ.get("OLLAMA_PORT")
            ids = discover_models_for_provider("ollama", host=host, port=port)
            return _out_models(args, ptype, ids)

        if ptype == "openai":
            base_url = (
                getattr(args, "base_url", None)
                or os.environ.get("OPENAI_BASE_URL")
                or "https://api.openai.com"
            )
            api_key = (
                getattr(args, "api_key", None)
                or os.environ.get("OPENAI_API_KEY")
                or os.environ.get("CHI_LLM_OPENAI_API_KEY")
            )
            org_id = getattr(args, "org_id", None) or os.environ.get("OPENAI_ORG_ID")
            if not api_key:
                return _out_models(args, ptype, [])
            ids = discover_models_for_provider(
                "openai", api_key=api_key, base_url=base_url, org_id=org_id
            )
            return _out_models(args, ptype, ids)

        if ptype == "anthropic":
            base_url = (
                getattr(args, "base_url", None)
                or os.environ.get("ANTHROPIC_BASE_URL")
                or "https://api.anthropic.com"
            )
            api_key = (
                getattr(args, "api_key", None)
                or os.environ.get("ANTHROPIC_API_KEY")
                or os.environ.get("CHI_LLM_ANTHROPIC_API_KEY")
            )
            if not api_key:
                return _out_models(args, ptype, [])
            ids = discover_models_for_provider(
                "anthropic", api_key=api_key, base_url=base_url
            )
            return _out_models(args, ptype, ids)

        # Default: unsupported provider or no models
        return _out_models(args, ptype, [])
    except Exception as e:  # pragma: no cover - depends on provider/network
        if getattr(args, "json", False):
            _print_json({"provider": ptype, "error": str(e), "models": []})
        else:
            print(f"Error discovering models for {ptype}: {e}")
