"""
UI launcher command.

Runs an Ink (Node.js) UI via npx. If Node/npx are not available, prints
clear installation instructions for the current platform.
"""

from argparse import _SubParsersAction
from shutil import which
import subprocess
import os
import platform


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
    print("\nAfter installation, try: chi ui")


def cmd_ui(args):
    node_path = which("node")
    npx_path = which("npx")

    if not node_path or not npx_path:
        _print_node_instructions()
        return

    # Determine source spec for npx
    source = getattr(args, "source", None) or os.environ.get(
        "CHI_LLM_UI_SOURCE", "github:jacekjursza/chi_llm_ui"
    )
    branch = getattr(args, "branch", None) or os.environ.get(
        "CHI_LLM_UI_BRANCH", "main"
    )
    if source.startswith("github:") and branch:
        # Append #branch ref if not already present
        if "#" not in source:
            source = f"{source}#{branch}"

    print("🚀 Launching chi-llm UI via npx...")
    try:
        # Pass-through any remaining args after '--'
        ui_args = getattr(args, "ui_args", []) or []
        cmd = [npx_path, "--yes", source]
        if ui_args:
            cmd.append("--")
            cmd.extend(ui_args)
        subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        print("\n👋 UI closed.")
    except Exception as e:
        print(f"❌ Failed to launch UI: {e}")


def register(subparsers: _SubParsersAction):
    sub = subparsers.add_parser(
        "ui", help="Run the Ink-based UI via npx (requires Node.js)"
    )
    sub.add_argument(
        "--source",
        help=(
            "npx package spec (default: github:jacekjursza/chi_llm_ui). "
            "Can also be set via CHI_LLM_UI_SOURCE."
        ),
    )
    sub.add_argument(
        "--branch",
        help=(
            "Git ref for GitHub source (default: main). "
            "Can also be set via CHI_LLM_UI_BRANCH."
        ),
    )
    sub.add_argument(
        "ui_args",
        nargs="*",
        help="Arguments to pass through to the UI (after --)",
    )
    sub.set_defaults(func=cmd_ui)
