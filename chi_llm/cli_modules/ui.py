"""
UI launcher command.

Runs the bundled Ink (Node.js) UI from this repository. Requires Node.js.
On first run, installs dependencies in the UI folder, then launches the UI.
If Node.js is not available, prints clear installation instructions.
"""

from argparse import _SubParsersAction
from shutil import which
import subprocess
import os
import platform
from pathlib import Path
import json

try:  # Import lazily to avoid heavy deps when not used
    from ..models import ModelManager
except Exception:  # pragma: no cover
    ModelManager = None  # type: ignore


def _print_node_instructions():
    print("❌ Node.js (and npx) not found.")
    print("\nInstall Node.js: https://nodejs.org/en/download/")
    sys_name = platform.system().lower()
    if "linux" in sys_name:
        print("Linux quick options:")
        print("  • Debian/Ubuntu: sudo apt-get install -y nodejs npm")
        print("  • Or via nvm: https://github.com/nvm-sh/nvm")
    elif "darwin" in sys_name or "mac" in sys_name:
        print("macOS quick options:")
        print("  • Homebrew: brew install node")
        print("  • Or via nvm: https://github.com/nvm-sh/nvm")
    elif "windows" in sys_name:
        print("Windows quick options:")
        print("  • Winget: winget install OpenJS.NodeJS")
        print("  • Chocolatey: choco install nodejs-lts")
        print("  • Scoop: scoop install nodejs-lts")
    print("\nAfter installation, try: chi-llm config")


def _get_ui_dir() -> Path:
    # Locate the bundled UI folder under the installed package
    here = Path(__file__).resolve()
    ui_dir = here.parent.parent / "ui_frontend"
    return ui_dir


def cmd_ui(args):
    node_path = which("node")
    npm_path = which("npm")

    if not node_path or not npm_path:
        _print_node_instructions()
        return

    ui_dir = _get_ui_dir()
    if not ui_dir.exists():
        print("❌ UI assets are not bundled with this version.")
        print("Please update chi-llm or consult the documentation.")
        return

    print("🚀 Launching chi-llm UI...")
    try:
        # Install deps once (skip if node_modules exists)
        node_modules = ui_dir / "node_modules"
        if not node_modules.exists() and not os.environ.get("CHI_LLM_UI_SKIP_INSTALL"):
            # Prefer reproducible installs when lockfile exists
            lockfile = ui_dir / "package-lock.json"
            if lockfile.exists():
                subprocess.run(
                    [npm_path, "ci", "--no-fund", "--no-audit"],
                    cwd=str(ui_dir),
                    check=False,
                )
            else:
                # Smoother first-run across Node/npm variants:
                # ignore peer dependency conflicts
                subprocess.run(
                    [
                        npm_path,
                        "install",
                        "--no-fund",
                        "--no-audit",
                        "--legacy-peer-deps",
                    ],
                    cwd=str(ui_dir),
                    check=False,
                )

        # Pass-through any remaining args
        ui_args = getattr(args, "ui_args", []) or []
        cmd = [npm_path, "run", "start"]
        if ui_args:
            cmd += ["--", *ui_args]
        subprocess.run(cmd, cwd=str(ui_dir), check=False)
    except KeyboardInterrupt:
        print("\n👋 UI closed.")
    except Exception as e:
        print(f"❌ Failed to launch UI: {e}")


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
        "config", help="Open the interactive configuration UI (requires Node.js)"
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
    ui = subparsers.add_parser(
        "ui", help="Run the Ink-based UI via npx (requires Node.js)"
    )
    _register_common(ui)
