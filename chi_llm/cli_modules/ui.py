"""
UI launcher command (Textual-only).

Launches the Textual (Python) TUI when available. If Textual is not installed,
prints a concise install hint.
"""

from argparse import _SubParsersAction
from pathlib import Path
import json
import importlib.util

try:  # Import lazily to avoid heavy deps when not used
    from ..models import ModelManager
except Exception:  # pragma: no cover
    ModelManager = None  # type: ignore


def _print_textual_instructions():
    print("❌ Textual UI is not installed.")
    print("\nInstall it with one of:")
    print("  • pip install 'chi-llm[ui]'")
    print("  • pip install textual")
    print("\nThen run: chi-llm config")


def _try_launch_textual(ui_args):
    # Detect textual without importing our TUI module (keeps deps optional)
    if importlib.util.find_spec("textual") is None:
        _print_textual_instructions()
        return
    try:
        from ..tui.app import launch_tui  # type: ignore

        launch_tui(ui_args)
    except Exception as e:
        print(f"❌ Failed to launch Textual UI: {e}")
        print("Tip: pip install 'chi-llm[ui]' to install the recommended version.")


def cmd_ui(args):
    # Launch Textual app or print instructions
    _try_launch_textual(getattr(args, "ui_args", []) or [])


def _atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def cmd_config_get(args):
    if ModelManager is None:
        print("{}" if getattr(args, "json", False) else "No configuration available.")
        return
    mgr = ModelManager()
    cfg = dict(mgr.config)
    if getattr(args, "json", False):
        print(json.dumps(cfg, indent=2))
    else:
        for k, v in cfg.items():
            print(f"{k}: {v}")


def cmd_config_set(args):
    if ModelManager is None:
        print("❌ Model management not available")
        return
    key = args.key
    val = args.value
    mgr = ModelManager()

    # Coerce simple types for known keys
    if key in {"preferred_context", "preferred_max_tokens"}:
        try:
            val = int(val)
        except ValueError:
            pass

    # Update in-memory and write atomically
    cfg = dict(mgr.config)
    cfg[key] = val

    scope = getattr(args, "scope", "local")
    if scope == "local":
        target = Path.cwd() / ".chi_llm.json"
    else:
        target = mgr.config_file
    _atomic_write_json(target, cfg)
    print(f"✅ Set {key} in {scope} config: {val}")


def _register_common(parser):
    # Collect any arguments after "--" and pass them to the UI
    # Using REMAINDER avoids conflicts with subparsers.
    import argparse as _argparse

    parser.add_argument(
        "ui_args",
        nargs=_argparse.REMAINDER,
        help="Arguments to pass through to the UI (after --)",
    )
    parser.set_defaults(func=cmd_ui)


def register(subparsers: _SubParsersAction):
    # Preferred command name
    cfg = subparsers.add_parser(
        "config",
        help="Open the interactive configuration UI (Textual)",
    )
    # Subcommands for config management: get/set
    cfg_sub = cfg.add_subparsers(dest="config_command")
    cfg_get = cfg_sub.add_parser("get", help="Get configuration (merged)")
    cfg_get.add_argument("--json", action="store_true", help="Output JSON")
    cfg_get.set_defaults(func=cmd_config_get)

    cfg_set = cfg_sub.add_parser("set", help="Set a configuration key")
    cfg_set.add_argument("key", help="Key to set (e.g., default_model)")
    cfg_set.add_argument("value", help="Value to set")
    cfg_set.add_argument(
        "--scope",
        choices=["local", "global"],
        default="local",
        help="Write to project (.chi_llm.json) or global config",
    )
    cfg_set.set_defaults(func=cmd_config_set)

    # No subcommand: launch the UI (default)
    _register_common(cfg)

    # Alias for convenience/back-compat
    ui = subparsers.add_parser("ui", help="Open the configuration UI (Textual)")
    _register_common(ui)
