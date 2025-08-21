"""
Tests for the 'ui' CLI command behavior without requiring Node.
"""

from types import SimpleNamespace
from unittest.mock import patch

from chi_llm.cli_modules import ui


def test_ui_no_node_prints_instructions(capsys):
    with patch("chi_llm.cli_modules.ui.which", return_value=None):
        ui.cmd_ui(SimpleNamespace(ui_args=[]))
    out = capsys.readouterr().out
    assert "Node.js (and npx) not found" in out


def test_ui_runs_local_npm_commands(tmp_path, monkeypatch):
    # Simulate node and npm present
    with patch(
        "chi_llm.cli_modules.ui.which", side_effect=["/usr/bin/node", "/usr/bin/npm"]
    ):
        # Prepare temp UI dir
        ui_dir = tmp_path / "ui_frontend"
        (ui_dir / "bin").mkdir(parents=True)
        (ui_dir / "package.json").write_text(
            '{"name":"x","version":"1.0.0","scripts":{"start":"node ./bin/index.js"}}'
        )
        (ui_dir / "bin/index.js").write_text('console.log("ok")')

        # Patch resolver to return temp ui dir
        monkeypatch.setattr(ui, "_get_ui_dir", lambda: ui_dir)
        with patch("subprocess.run") as run:
            ui.cmd_ui(SimpleNamespace(ui_args=["--foo"]))
            # Verify npm ci then npm run start -- --foo executed
            assert run.call_count >= 2
            first = run.call_args_list[0][0][0]
            second = run.call_args_list[-1][0][0]
            assert first[0].endswith("npm") and first[1] == "ci"
            assert second[0].endswith("npm") and second[1:3] == ["run", "start"]
