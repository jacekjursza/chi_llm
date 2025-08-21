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
            # Prefer reproducible install when lockfile is present
            lock_ci = (ui_dir / "package-lock.json").exists() or (
                ui_dir / "npm-shrinkwrap.json"
            ).exists()
            if lock_ci:
                subprocess.run(
                    [npm_path, "ci", "--no-fund", "--no-audit"],
                    cwd=str(ui_dir),
                    check=False,
                )
            else:
                subprocess.run(
                    [npm_path, "install", "--no-fund", "--no-audit"],
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


def _register_common(parser):
    parser.add_argument(
        "ui_args",
        nargs="*",
        help="Arguments to pass through to the UI (after --)",
    )
    parser.set_defaults(func=cmd_ui)


def register(subparsers: _SubParsersAction):
    # Preferred command name
    cfg = subparsers.add_parser(
        "config", help="Open the interactive configuration UI (requires Node.js)"
    )
    _register_common(cfg)

    # Alias for convenience/back-compat
    ui = subparsers.add_parser(
        "ui", help="Run the Ink-based UI via npx (requires Node.js)"
    )
    _register_common(ui)
