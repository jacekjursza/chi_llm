"""
Test that when a prebuilt 'chi-tui' is available on PATH, the
UI launcher prefers it and executes it without attempting to build from source.
"""

import os
import stat
from pathlib import Path
from types import SimpleNamespace

from chi_llm.cli_modules import ui as ui_cli


def _make_stub_chi_tui(tmpdir: Path) -> Path:
    exe = "chi-tui.exe" if os.name == "nt" else "chi-tui"
    stub = tmpdir / exe
    if os.name == "nt":
        # Simple batch file for Windows environments
        stub.write_text("""@echo off\necho OK PATH chi-tui\n""", encoding="utf-8")
    else:
        stub.write_text(
            """#!/usr/bin/env bash\necho OK PATH chi-tui\n""", encoding="utf-8"
        )
        stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
    return stub


def test_ui_prefers_prebuilt_on_path(tmp_path, monkeypatch, capsys):
    # Create a stub chi-tui on PATH
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    _make_stub_chi_tui(stub_dir)

    # Prepend stub_dir to PATH
    old_path = os.environ.get("PATH", "")
    monkeypatch.setenv("PATH", f"{stub_dir}{os.pathsep}{old_path}")

    # Ensure rebuild is not forced
    monkeypatch.delenv("CHI_LLM_UI_REBUILD", raising=False)

    # Run UI launcher with no extra args; should call our stub and print marker
    args = SimpleNamespace(ui_args=[], rebuild=False)
    ui_cli.cmd_ui(args)

    out = capsys.readouterr().out
    assert "OK PATH chi-tui" in out
