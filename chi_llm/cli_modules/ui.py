"""
UI launcher command.

Prefers launching the Go-based TUI (go-chi/chi-tui) when available; falls back
to the Python Textual TUI if the Go binary or toolchain isn't present.
"""

from argparse import _SubParsersAction
from pathlib import Path
import json
import importlib.util
import os
import re
import shutil
import subprocess

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


def _find_repo_root(start: Path) -> Path | None:
    # Heuristic: package is at <root>/chi_llm/..., so root is two levels up
    for p in [start, *start.parents]:
        if (p / ".git").exists() and (p / "go-chi").exists():
            return p
    # Fallback: walk up 3 levels from this file
    guess = start
    for _ in range(3):
        guess = guess.parent
    if (guess / "go-chi").exists():
        return guess
    return None


def _latest_mtime_in(dirpath: Path, patterns=("*.go",)) -> float:
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


def _parse_go_version(s: str) -> tuple[int, int]:
    m = re.search(r"go(\d+)\.(\d+)", s)
    if not m:
        return (0, 0)
    return (int(m.group(1)), int(m.group(2)))


def _resolve_go_bin() -> str | None:
    # Priority: GO_BIN env -> ~/.local/go/bin/go -> PATH
    candidates: list[str] = []
    env_bin = os.getenv("GO_BIN")
    if env_bin:
        candidates.append(env_bin)
    home_bin = os.path.expanduser("~/.local/go/bin/go")
    candidates.append(home_bin)
    path_bin = shutil.which("go")
    if path_bin:
        candidates.append(path_bin)

    best: tuple[int, int] = (0, 0)
    best_path: str | None = None
    for c in candidates:
        if not c:
            continue
        try:
            out = subprocess.check_output([c, "version"], text=True)
            ver = _parse_go_version(out)
            if ver > best:
                best, best_path = ver, c
        except Exception:
            continue
    return best_path


def _try_launch_go(ui_args, force_rebuild: bool = False) -> bool:
    """Try to launch the Go TUI. Returns True if executed (successfully or with
    process return code), False if not available and we should fallback.

    Strategy:
    - Locate repo root and go-chi directory
    - Ensure binary exists, attempt to build if missing
    - Exec the binary, forwarding args
    """
    here = Path(__file__).resolve()
    root = _find_repo_root(here)
    if root is None:
        return False
    go_dir = root / "go-chi"
    if not go_dir.exists():
        return False

    # Resolve binary path (handle Windows exe)
    bin_dir = go_dir / "bin"
    bin_dir.mkdir(exist_ok=True)
    exe = "chi-tui.exe" if os.name == "nt" else "chi-tui"
    bin_path = bin_dir / exe

    should_build = force_rebuild or (not bin_path.exists())

    if not should_build:
        # Rebuild if sources are newer than binary
        try:
            bin_mtime = bin_path.stat().st_mtime
        except OSError:
            bin_mtime = 0.0
        src_mtime = max(
            _latest_mtime_in(go_dir / "cmd"),
            _latest_mtime_in(go_dir / "internal"),
            _latest_mtime_in(go_dir, ("go.mod", "go.sum")),
        )
        if src_mtime > bin_mtime:
            should_build = True

    if should_build:
        # Attempt to build with the newest available Go
        go = _resolve_go_bin()
        if go is None:
            # No Go toolchain available; can't launch Go TUI
            print("❌ No Go toolchain found. Install Go >= 1.21 or add to PATH.")
            print('   Tip: export PATH="$HOME/.local/go/bin:$PATH"')
            return False
        try:
            subprocess.run(
                [go, "build", "-o", str(bin_path), "./cmd/chi-tui"],
                cwd=str(go_dir),
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to build Go TUI with '{go}': {e}")
            if "/usr/bin/go" in go:
                print("   System Go detected. Prefer ~/.local/go/bin/go (>= 1.21).")
                print('   Tip: export PATH="$HOME/.local/go/bin:$PATH"')
            return False

    # Launch the Go TUI interactively, forwarding any UI args
    try:
        # Inherit TTY; don't use -once/-no-alt here so users get full UI
        subprocess.run([str(bin_path), *ui_args])
        # Return True: we attempted; even if non-zero, no fallback to Textual
        return True
    except Exception as e:
        print(f"❌ Failed to launch Go TUI: {e}")
        return False


def cmd_ui(args):
    ui_args = getattr(args, "ui_args", []) or []
    force_rebuild = bool(
        getattr(args, "go_rebuild", False) or os.getenv("CHI_LLM_GO_REBUILD") == "1"
    )
    # Prefer Go TUI when available
    if _try_launch_go(ui_args, force_rebuild=force_rebuild):
        return
    # Fallback to Textual app or print instructions
    _try_launch_textual(ui_args)


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
        help="Open the interactive configuration UI (Go TUI if available)",
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
        "--go-rebuild",
        action="store_true",
        help="Force rebuild the Go TUI before launch",
    )
    _register_common(cfg)

    # Alias for convenience/back-compat
    ui = subparsers.add_parser(
        "ui",
        help="Open the configuration UI (Go TUI if available)",
    )
    ui.add_argument(
        "--go-rebuild",
        action="store_true",
        help="Force rebuild the Go TUI before launch",
    )
    _register_common(ui)
