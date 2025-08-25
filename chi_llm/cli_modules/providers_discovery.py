"""Provider discovery helpers for CLI (split to keep file sizes small)."""

from typing import Any
import json as _json
import os
from urllib import request as _request
from urllib.error import URLError, HTTPError


def _print_json(obj: Any) -> None:
    print(_json.dumps(obj, indent=2))


def cmd_discover_models(args):
    ptype = (getattr(args, "ptype", "") or "").strip().lower()
    host = getattr(args, "host", "localhost") or "localhost"
    port = getattr(args, "port", None)
    if port is not None:
        try:
            port = int(port)
        except Exception:
            pass

    def _out(obj):
        if getattr(args, "json", False):
            _print_json(obj)
        else:
            models = obj.get("models") or []
            print(f"Models ({len(models)}):")
            for m in models:
                mid = m.get("id") or m.get("name") or ""
                print(f" - {mid}")

    try:
        if ptype == "lmstudio":
            port = 1234 if port is None else port
            url = f"http://{host}:{port}/v1/models"
            with _request.urlopen(url, timeout=3) as resp:
                if resp.status != 200:
                    raise HTTPError(
                        url, resp.status, "HTTP error", hdrs=resp.headers, fp=None
                    )
                data = _json.loads(resp.read().decode("utf-8"))
            items = []
            for it in data.get("data") or []:
                mid = it.get("id") or it.get("name") or ""
                if mid:
                    items.append({"id": mid})
            return _out({"provider": ptype, "models": items})

        if ptype == "ollama":
            port = 11434 if port is None else port
            url = f"http://{host}:{port}/api/tags"
            with _request.urlopen(url, timeout=3) as resp:
                if resp.status != 200:
                    raise HTTPError(
                        url, resp.status, "HTTP error", hdrs=resp.headers, fp=None
                    )
                data = _json.loads(resp.read().decode("utf-8"))
            items = []
            for it in data.get("models") or []:
                name = it.get("name") or ""
                if name:
                    items.append({"id": name})
            return _out({"provider": ptype, "models": items})

        if ptype == "openai":
            base_url = getattr(args, "base_url", None) or "https://api.openai.com"
            api_key = (
                getattr(args, "api_key", None)
                or os.environ.get("OPENAI_API_KEY")
                or os.environ.get("CHI_LLM_OPENAI_API_KEY")
            )
            org_id = getattr(args, "org_id", None) or os.environ.get("OPENAI_ORG_ID")
            if not api_key:
                return _out(
                    {"provider": ptype, "error": "missing api_key", "models": []}
                )
            url = f"{base_url.rstrip('/')}/v1/models"
            req = _request.Request(url)
            req.add_header("Authorization", f"Bearer {api_key}")
            if org_id:
                req.add_header("OpenAI-Organization", org_id)
            with _request.urlopen(req, timeout=5) as resp:
                if resp.status != 200:
                    raise HTTPError(
                        url, resp.status, "HTTP error", hdrs=resp.headers, fp=None
                    )
                data = _json.loads(resp.read().decode("utf-8"))
            items = []
            for it in data.get("data") or []:
                mid = it.get("id") or it.get("name") or ""
                if mid:
                    items.append({"id": mid})
            return _out({"provider": ptype, "models": items})

        return _out({"provider": ptype, "models": []})
    except (URLError, HTTPError) as e:  # pragma: no cover - network dependent
        if getattr(args, "json", False):
            _print_json({"provider": ptype, "error": str(e), "models": []})
        else:
            print(f"Error discovering models for {ptype}: {e}")
