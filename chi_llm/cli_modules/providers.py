"""
Providers CLI: list/current/set for provider configuration.

Works alongside models CLI; writes to the same config files but under
the `provider` key without disturbing model settings.
"""

from argparse import _SubParsersAction
from pathlib import Path
from typing import Dict, Any
import json

from ..utils import load_config
from .providers_schema import PROVIDER_SCHEMAS

try:
    from ..models import ModelManager, MODEL_DIR, MODELS
except Exception:  # pragma: no cover - optional
    ModelManager = None  # type: ignore
    MODEL_DIR = Path.home() / ".cache" / "chi_llm"  # type: ignore
    MODELS = {}  # type: ignore

SUPPORTED = [
    {"type": "local", "implemented": True, "notes": "Default llama.cpp (legacy alias)"},
    {
        "type": "local-zeroconfig",
        "implemented": True,
        "notes": "Curated models (one-pick)",
    },
    {
        "type": "local-custom",
        "implemented": True,
        "notes": "Custom GGUF path and tuning",
    },
    {"type": "lmstudio", "implemented": True, "notes": "Local UI/server"},
    {"type": "ollama", "implemented": True, "notes": "Local server"},
    {"type": "openai", "implemented": True, "notes": "API key required"},
    {"type": "claude-cli", "implemented": True, "notes": "Anthropic CLI bridge"},
    {"type": "openai-cli", "implemented": True, "notes": "OpenAI CLI bridge"},
    {"type": "anthropic", "implemented": True, "notes": "API key required"},
    {"type": "groq", "implemented": False},
    {"type": "gemini", "implemented": False},
]

# Provider field schema for UI/automation. This reflects what `providers set`
# accepts today. Extend here if CLI gains new fields.
PROVIDER_SCHEMAS = PROVIDER_SCHEMAS


def _print_json(obj: Any) -> None:
    print(json.dumps(obj, indent=2))


def _atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def _resolve_save_target(local: bool) -> Path:
    if local:
        return Path.cwd() / ".chi_llm.json"
    # global
    return MODEL_DIR / "model_config.json"


def cmd_providers(args):
    sub = args.providers_command
    if sub == "list":
        if getattr(args, "json", False):
            _print_json(SUPPORTED)
        else:
            print("Supported providers:\n")
            for p in SUPPORTED:
                mark = "✓" if p.get("implemented") else "-"
                note = f" ({p.get('notes')})" if p.get("notes") else ""
                print(f"• {p['type']}: {mark}{note}")
        return

    if sub == "schema":
        # Output provider field schemas for UI/automation
        out = {"providers": []}
        for p in SUPPORTED:
            ptype = p.get("type")
            if not ptype:
                continue
            schema = PROVIDER_SCHEMAS.get(ptype, {"fields": []})
            fields = list(schema.get("fields", []))
            # Augment zeroconfig with recommended options when available
            if ptype == "local-zeroconfig":
                try:
                    # Provide a small curated list for dropdowns (ids only)
                    rec_ids = []
                    for mid, mi in MODELS.items():  # type: ignore
                        tags = getattr(mi, "tags", []) or []
                        if "recommended" in tags or "default" in tags:
                            rec_ids.append(mid)
                    if rec_ids:
                        for f in fields:
                            if f.get("name") == "model":
                                f["options"] = rec_ids  # UI can use as enum source
                                break
                except Exception:
                    pass
            out["providers"].append(
                {
                    "type": ptype,
                    "implemented": bool(p.get("implemented")),
                    "fields": fields,
                }
            )
        if getattr(args, "json", False):
            _print_json(out)
        else:
            print("Provider schemas:\n")
            for prov in out["providers"]:
                mark = "✓" if prov.get("implemented") else "-"
                print(f"• {prov['type']} {mark}")
                for f in prov.get("fields", []):
                    req = " (required)" if f.get("required") else ""
                    default = f" [default: {f['default']}]" if "default" in f else ""
                    print(f"   - {f['name']}: {f['type']}{req}{default}")
            print()
        return

    if sub == "current":
        cfg = load_config()
        provider = cfg.get("provider") or {}
        provider_type = provider.get("type", "local")
        info: Dict[str, Any] = {
            "type": provider_type,
            "host": provider.get("host"),
            "port": provider.get("port"),
            "model": provider.get("model"),
            "model_path": provider.get("model_path"),
            "context_window": provider.get("context_window"),
            "n_gpu_layers": provider.get("n_gpu_layers"),
            "output_tokens": provider.get("output_tokens"),
            "api_key": bool(provider.get("api_key"))
            if provider.get("api_key")
            else False,
        }
        if ModelManager:
            stats = ModelManager().get_model_stats()
            info.update(
                {
                    "config_source": stats.get("config_source"),
                    "config_path": stats.get("config_path"),
                }
            )
        if getattr(args, "json", False):
            _print_json(info)
        else:
            print(f"Provider: {info['type']}")
            if info.get("host"):
                print(f"Host: {info['host']}:{info.get('port')}")
            if info.get("model"):
                print(f"Model: {info['model']}")
            if info.get("model_path"):
                print(f"Model path: {info['model_path']}")
            if info.get("context_window"):
                print(f"Context window: {info['context_window']}")
            if info.get("n_gpu_layers") is not None:
                print(f"n_gpu_layers: {info['n_gpu_layers']}")
            if info.get("output_tokens"):
                print(f"Output tokens: {info['output_tokens']}")
            if info.get("config_source"):
                print(f"Config: {info['config_source']} -> {info.get('config_path')}")
        return

    if sub == "set":
        ptype = args.type
        if ptype not in [p["type"] for p in SUPPORTED]:
            print(f"❌ Unknown provider type: {ptype}")
            print("Supported:", ", ".join([p["type"] for p in SUPPORTED]))
            return
        provider_cfg: Dict[str, Any] = {"type": ptype}
        # Optional: auto-detect host/port for lmstudio/ollama
        if getattr(args, "auto_url", False) and ptype in {"lmstudio", "ollama"}:
            try:
                from .providers_url import find_url as _find_url  # type: ignore

                res = _find_url(ptype)
                if not res.get("ok"):
                    if getattr(args, "json", False):
                        _print_json(
                            {
                                "ok": False,
                                "message": f"auto-url: no reachable {ptype} server",
                                "tried": res.get("tried", []),
                            }
                        )
                        return
                    else:
                        print(f"❌ auto-url: no reachable {ptype} server")
                        return
                # Apply detected host/port as defaults; explicit flags override below
                provider_cfg["host"] = res.get("host")
                provider_cfg["port"] = res.get("port")
            except Exception as e:
                if getattr(args, "json", False):
                    _print_json({"ok": False, "message": f"auto-url failed: {e}"})
                else:
                    print(f"❌ auto-url failed: {e}")
                return
        if getattr(args, "host", None):
            provider_cfg["host"] = args.host
        if getattr(args, "port", None):
            # store int when possible
            try:
                provider_cfg["port"] = int(args.port)
            except Exception:
                provider_cfg["port"] = args.port
        if getattr(args, "model", None):
            provider_cfg["model"] = args.model
        if getattr(args, "model_path", None):
            provider_cfg["model_path"] = args.model_path
        if getattr(args, "api_key", None):
            provider_cfg["api_key"] = args.api_key
        if getattr(args, "context_window", None) is not None:
            try:
                provider_cfg["context_window"] = int(args.context_window)
            except Exception:
                provider_cfg["context_window"] = args.context_window
        if getattr(args, "n_gpu_layers", None) is not None:
            try:
                provider_cfg["n_gpu_layers"] = int(args.n_gpu_layers)
            except Exception:
                provider_cfg["n_gpu_layers"] = args.n_gpu_layers
        if getattr(args, "output_tokens", None) is not None:
            try:
                provider_cfg["output_tokens"] = int(args.output_tokens)
            except Exception:
                provider_cfg["output_tokens"] = args.output_tokens

        # Determine write target
        target = _resolve_save_target(getattr(args, "local", False))
        # Merge with existing file if present
        existing = {}
        if target.exists():
            try:
                existing = json.loads(target.read_text(encoding="utf-8"))
            except Exception:
                existing = {}
        existing["provider"] = provider_cfg
        _atomic_write_json(target, existing)
        scope = "local" if getattr(args, "local", False) else "global"
        if getattr(args, "json", False):
            _print_json(
                {
                    "provider": {
                        "type": provider_cfg.get("type"),
                        "host": provider_cfg.get("host"),
                        "port": provider_cfg.get("port"),
                        "model": provider_cfg.get("model"),
                        "model_path": provider_cfg.get("model_path"),
                        "context_window": provider_cfg.get("context_window"),
                        "n_gpu_layers": provider_cfg.get("n_gpu_layers"),
                        "output_tokens": provider_cfg.get("output_tokens"),
                        "api_key_set": bool(provider_cfg.get("api_key")),
                    },
                    "scope": scope,
                    "path": str(target),
                }
            )
        # Otherwise remain silent to keep pipelines clean.


def cmd_list_tags(args):
    """List all available provider tags from the models catalog."""
    if not MODELS:
        print("No models loaded")
        return

    # Collect all unique tags from models
    all_tags = set()
    for model in MODELS.values():
        if hasattr(model, "tags") and model.tags:
            all_tags.update(model.tags)

    # Sort tags for consistent output
    sorted_tags = sorted(all_tags)

    if args.json:
        _print_json({"tags": sorted_tags})
    else:
        print("Available provider tags:")
        print()
        for tag in sorted_tags:
            print(f"• {tag}")


def register(subparsers: _SubParsersAction):
    sub = subparsers.add_parser("providers", help="Manage provider configuration")
    providers_sub = sub.add_subparsers(dest="providers_command", help="Provider cmds")

    lst = providers_sub.add_parser("list", help="List supported providers")
    lst.add_argument("--json", action="store_true", help="Output JSON")
    sub.set_defaults(func=cmd_providers)

    cur = providers_sub.add_parser("current", help="Show current provider settings")
    cur.add_argument("--json", action="store_true", help="Output JSON")

    sch = providers_sub.add_parser("schema", help="Show provider field schemas")
    sch.add_argument("--json", action="store_true", help="Output JSON")

    setp = providers_sub.add_parser("set", help="Set provider settings")
    setp.add_argument("type", help="Provider type (e.g., lmstudio, ollama, local)")
    setp.add_argument("--host", help="Provider host", default=None)
    setp.add_argument("--port", help="Provider port", default=None)
    setp.add_argument("--model", help="Default model for the provider", default=None)
    setp.add_argument(
        "--model-path",
        dest="model_path",
        help="Absolute path to a local GGUF model file (local provider)",
        default=None,
    )
    setp.add_argument(
        "--context-window",
        dest="context_window",
        help="Override context window (n_ctx) for local provider",
        default=None,
    )
    setp.add_argument(
        "--n-gpu-layers",
        dest="n_gpu_layers",
        help="Number of layers offloaded to GPU for local provider",
        default=None,
    )
    setp.add_argument(
        "--output-tokens",
        dest="output_tokens",
        help="Default max output tokens for local provider",
        default=None,
    )
    setp.add_argument("--api-key", dest="api_key", help="API key (if required)")
    setp.add_argument("--local", action="store_true", help="Write to project config")
    setp.add_argument("--json", action="store_true", help="Echo saved config as JSON")
    setp.add_argument(
        "--auto-url",
        action="store_true",
        help="For lmstudio/ollama: auto-detect host/port using find-url",
    )

    tags = providers_sub.add_parser("tags", help="List available provider tags")
    tags.add_argument("--json", action="store_true", help="Output JSON")
    tags.set_defaults(func=cmd_list_tags)

    # Discover models for certain providers (e.g., lmstudio, ollama)
    disc = providers_sub.add_parser(
        "discover-models", help="Discover available models for a provider"
    )
    disc.add_argument("--type", dest="ptype", required=True, help="Provider type")
    disc.add_argument("--host", default="localhost", help="Provider host")
    disc.add_argument("--port", default=None, help="Provider port (int)")
    disc.add_argument("--json", action="store_true", help="Output JSON")
    disc.add_argument(
        "--base-url", dest="base_url", default=None, help="API base URL (OpenAI)"
    )
    disc.add_argument(
        "--api-key", dest="api_key", default=None, help="API key (OpenAI)"
    )
    disc.add_argument(
        "--org-id", dest="org_id", default=None, help="Organization ID (OpenAI)"
    )
    disc.set_defaults(func=cmd_discover_models)

    # Find best URL (host/port) for certain providers (WSL-aware)
    findu = providers_sub.add_parser(
        "find-url", help="Try to find reachable URL for a provider"
    )
    findu.add_argument("--type", dest="ptype", required=True, help="Provider type")
    findu.add_argument("--host", default=None, help="Hint host (try first)")
    findu.add_argument("--port", default=None, help="Hint port (try first)")
    findu.add_argument(
        "--timeout", default="1.8", help="Probe timeout (seconds) per endpoint"
    )
    findu.add_argument("--json", action="store_true", help="Output JSON")
    from .providers_url import cmd_find_url as _cmd_find_url  # type: ignore

    findu.set_defaults(func=_cmd_find_url)

    # Probe/test provider connectivity
    testp = providers_sub.add_parser(
        "test", help="Test provider connectivity (HTTP/API)"
    )
    testp.add_argument("--type", dest="ptype", required=True, help="Provider type")
    testp.add_argument("--host", default=None, help="Provider host")
    testp.add_argument("--port", default=None, help="Provider port (int)")
    testp.add_argument("--base-url", dest="base_url", default=None, help="API base URL")
    testp.add_argument(
        "--api-key", dest="api_key", default=None, help="API key (if required)"
    )
    testp.add_argument(
        "--org-id", dest="org_id", default=None, help="Organization (OpenAI)"
    )
    testp.add_argument(
        "--model-path",
        dest="model_path",
        default=None,
        help="Model path (local-custom)",
    )
    testp.add_argument(
        "--model", dest="model", default=None, help="Model id (when required)"
    )
    testp.add_argument(
        "--timeout", dest="timeout", default="5.0", help="Timeout seconds"
    )
    testp.add_argument(
        "--e2e", action="store_true", help="Run end-to-end generate('Hello!') test"
    )
    testp.add_argument(
        "--prompt", dest="prompt", default=None, help="Custom test prompt for --e2e"
    )
    testp.add_argument("--json", action="store_true", help="Output JSON")
    from .providers_test import cmd_test_provider as _cmd_test_provider  # type: ignore

    testp.set_defaults(func=_cmd_test_provider)


def cmd_discover_models(args):
    # Forward to split module to keep this file within size limits
    from .providers_discovery import cmd_discover_models as _impl

    return _impl(args)
