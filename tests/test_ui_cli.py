"""
Tests for the 'config/ui' CLI behavior with Textual UI.
"""

from types import SimpleNamespace
from unittest.mock import patch

from chi_llm.cli_modules import ui


def test_config_textual_missing_prints_hint(capsys):
    # No textual installed -> print install hint
    with patch("importlib.util.find_spec", return_value=None):
        ui.cmd_ui(SimpleNamespace(ui_args=[]))
    out = capsys.readouterr().out
    assert "Textual UI is not installed" in out


def test_config_textual_present_calls_launcher(monkeypatch):
    # Simulate textual present and ensure we call our launcher
    calls = {"count": 0, "args": None}

    def fake_launch(args):
        calls["count"] = calls["count"] + 1
        calls["args"] = args

    monkeypatch.setattr("importlib.util.find_spec", lambda name: object())
    # Ensure import of launcher works and we can patch it
    from chi_llm.tui import app as tui_app

    monkeypatch.setattr(tui_app, "launch_tui", fake_launch)
    ui.cmd_ui(SimpleNamespace(ui_args=["--foo"]))
    assert calls["count"] == 1
    assert calls["args"] == ["--foo"]
