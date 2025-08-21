"""
Tests for the 'ui' CLI command behavior without requiring Node.
"""

from types import SimpleNamespace
from unittest.mock import patch

from chi_llm.cli_modules import ui


def test_ui_no_node_prints_instructions(capsys):
    with patch("chi_llm.cli_modules.ui.which", return_value=None):
        ui.cmd_ui(SimpleNamespace(source=None, branch=None, ui_args=[]))
    out = capsys.readouterr().out
    assert "Node.js (and npx) not found" in out


def test_ui_runs_npx_with_source():
    # Simulate node and npx being present
    with patch(
        "chi_llm.cli_modules.ui.which", side_effect=["/usr/bin/node", "/usr/bin/npx"]
    ):
        with patch("subprocess.run") as run:
            ui.cmd_ui(
                SimpleNamespace(
                    source="github:org/repo", branch="dev", ui_args=["--foo"]
                )
            )
            # Expect npx to be invoked
            called = run.call_args[0][0]
            assert called[0].endswith("npx")
            assert "github:org/repo#dev" in called
            assert "--" in called
            assert "--foo" in called
