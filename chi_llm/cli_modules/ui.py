"""
UI launcher command.

Prefers the new Rust/ratatui TUI (tui/chi-tui) when available. Falls back to
the (retired) Go TUI only if present. The legacy Python/Textual UI has been
removed.
"""

from argparse import _SubParsersAction
from pathlib import Path
import json
import os
import re
import shutil
import subprocess

try:  # Import lazily to avoid heavy deps when not used
    from ..models import ModelManager
except Exception:  # pragma: no cover
    ModelManager = None  # type: ignore


def _print_ui_instructions():
    print("❌ Interactive UI not available in this install.")
    print("   For development, build and run the Rust TUI:")
    print("     • cd tui/chi-tui && cargo run")
    print("     • or build: cd tui/chi-tui && cargo build --release")
    print("       then: ./tui/chi-tui/target/release/chi-tui")


def _find_repo_root(start: Path) -> Path | None:
    # Heuristic: package is at <root>/chi_llm/..., so root is two levels up
    for p in [start, *start.parents]:
        if (p / ".git").exists() and (p / "tui" / "chi-tui").exists():
            return p
    # Fallback: walk up 3 levels from this file
    guess = start
    for _ in range(3):
        guess = guess.parent
    if (guess / "tui" / "chi-tui").exists():
        return guess
    return None


def _latest_mtime_in(dirpath: Path, patterns=("*.rs",)) -> float:
    latest = 0.0
    for root, _, _ in os.walk(dirpath):
        p = Path(root)
        for pat in patterns:
            for f in p.glob(pat):
                try:
                    latest = max(latest, f.stat().st_mtime)
                except OSError:
                    pass
    return latest


def _parse_go_version(s: str) -> tuple[int, int]:  # kept for historical reasons
    m = re.search(r"go(\d+)\.(\d+)", s)
    if not m:
        return (0, 0)
    return (int(m.group(1)), int(m.group(2)))


def _resolve_cargo_bin() -> str | None:
    # Priority: CARGO env -> PATH
    candidates: list[str] = []
    env_bin = os.getenv("CARGO")
    if env_bin:
        candidates.append(env_bin)
    path_bin = shutil.which("cargo")
    if path_bin:
        candidates.append(path_bin)
    return candidates[0] if candidates else None


def _try_launch_rust(ui_args, force_rebuild: bool = False) -> bool:
    """Try to launch the Rust TUI from source tree. Returns True if executed
    (regardless of exit code), False if not available.

    Strategy:
    - Locate repo root with tui/chi-tui
    - Ensure binary exists or (re)build with cargo when stale
    - Launch built binary, forwarding args
    """
    here = Path(__file__).resolve()
    root = _find_repo_root(here)
    if root is None:
        return False
    tui_dir = root / "tui" / "chi-tui"
    if not tui_dir.exists():
        return False

    exe = "chi-tui.exe" if os.name == "nt" else "chi-tui"
    bin_path = tui_dir / "target" / "release" / exe

    should_build = force_rebuild or (not bin_path.exists())
    if not should_build:
        try:
            bin_mtime = bin_path.stat().st_mtime
        except OSError:
            bin_mtime = 0.0
        src_mtime = max(
            _latest_mtime_in(tui_dir, ("*.rs",)),
            _latest_mtime_in(tui_dir, ("Cargo.toml",)),
        )
        if src_mtime > bin_mtime:
            should_build = True

    if should_build:
        cargo = _resolve_cargo_bin()
        if cargo is None:
            print("❌ No Rust toolchain found. Install Rust (cargo) and try again.")
            return False
        try:
            subprocess.run([cargo, "build", "--release"], cwd=str(tui_dir), check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to build Rust TUI with '{cargo}': {e}")
            return False

    # Launch binary
    try:
        subprocess.run([str(bin_path), *ui_args])
        return True
    except Exception as e:
        print(f"❌ Failed to launch Rust TUI: {e}")
        return False


def _try_launch_go(ui_args, force_rebuild: bool = False) -> bool:
    """Try to launch the Go TUI. Returns True if executed (successfully or with
    process return code), False if not available and we should fallback.

    Strategy:
    - Locate repo root and go-chi directory
    - Ensure binary exists, attempt to build if missing
    - Exec the binary, forwarding args
    """
    # Disabled: Go TUI retired and removed from repo.
    return False


def cmd_ui(args):
    ui_args = getattr(args, "ui_args", []) or []
    force_rebuild = bool(
        getattr(args, "rebuild", False) or os.getenv("CHI_LLM_UI_REBUILD") == "1"
    )
    # Try Rust TUI first
    if _try_launch_rust(ui_args, force_rebuild=force_rebuild):
        return
    # Fallback to Go (retired) — currently disabled
    if _try_launch_go(ui_args, force_rebuild=force_rebuild):
        return
    _print_ui_instructions()


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
        help="Open the interactive configuration UI (Rust/ratatui)",
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
    cfg.add_argument(
        "--rebuild",
        action="store_true",
        help="Force rebuild the UI before launch",
    )
    _register_common(cfg)

    # Alias for convenience/back-compat
    ui = subparsers.add_parser(
        "ui",
        help="Open the configuration UI (Rust/ratatui)",
    )
    ui.add_argument(
        "--rebuild",
        action="store_true",
        help="Force rebuild the UI before launch",
    )
    _register_common(ui)
