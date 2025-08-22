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

try:
    from ..models import ModelManager, MODEL_DIR
except Exception:  # pragma: no cover - optional
    ModelManager = None  # type: ignore
    MODEL_DIR = Path.home() / ".cache" / "chi_llm"  # type: ignore

SUPPORTED = [
    {"type": "local", "implemented": True, "notes": "Default llama.cpp"},
    {"type": "lmstudio", "implemented": True, "notes": "Local UI/server"},
    {"type": "ollama", "implemented": True, "notes": "Local server"},
    {"type": "openai", "implemented": False},
    {"type": "anthropic", "implemented": False},
    {"type": "groq", "implemented": False},
    {"type": "gemini", "implemented": False},
]


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

    if sub == "current":
        cfg = load_config()
        provider = cfg.get("provider") or {}
        provider_type = provider.get("type", "local")
        info: Dict[str, Any] = {
            "type": provider_type,
            "host": provider.get("host"),
            "port": provider.get("port"),
            "model": provider.get("model"),
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
        if getattr(args, "api_key", None):
            provider_cfg["api_key"] = args.api_key

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
        # Intentionally silent to keep JSON-friendly pipelines when chained.
        # The 'current' command provides confirmation/output.


def register(subparsers: _SubParsersAction):
    sub = subparsers.add_parser("providers", help="Manage provider configuration")
    providers_sub = sub.add_subparsers(dest="providers_command", help="Provider cmds")

    lst = providers_sub.add_parser("list", help="List supported providers")
    lst.add_argument("--json", action="store_true", help="Output JSON")
    sub.set_defaults(func=cmd_providers)

    cur = providers_sub.add_parser("current", help="Show current provider settings")
    cur.add_argument("--json", action="store_true", help="Output JSON")

    setp = providers_sub.add_parser("set", help="Set provider settings")
    setp.add_argument("type", help="Provider type (e.g., lmstudio, ollama, local)")
    setp.add_argument("--host", help="Provider host", default=None)
    setp.add_argument("--port", help="Provider port", default=None)
    setp.add_argument("--model", help="Default model for the provider", default=None)
    setp.add_argument("--api-key", dest="api_key", help="API key (if required)")
    setp.add_argument("--local", action="store_true", help="Write to project config")
