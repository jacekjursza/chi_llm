"""
Tests for config get/set CLI under the 'config' command.
"""

import json
import os
from types import SimpleNamespace
from unittest.mock import patch

from chi_llm.cli_modules import ui as ui_cli


def test_config_set_and_get_local_json(tmp_path, capsys, monkeypatch):
    # Work in a clean temp dir
    old = os.getcwd()
    os.chdir(tmp_path)
    try:
        # Set a value locally
        args_set = SimpleNamespace(
            key="default_model", value="gemma-270m", scope="local"
        )
        with patch.object(ui_cli, "ModelManager") as MM:
            # Mock manager to avoid touching real global config
            MM.return_value.config = {
                "default_model": "gemma-270m",
                "downloaded_models": [],
                "preferred_context": 8192,
                "preferred_max_tokens": 4096,
            }
            MM.return_value.config_file = tmp_path / "model_config.json"
            ui_cli.cmd_config_set(args_set)
        # Clear capture of the success message
        capsys.readouterr()

        # Get merged config as JSON
        args_get = SimpleNamespace(json=True)
        # Use real ModelManager to read merged config (local takes precedence)
        ui_cli.cmd_config_get(args_get)

        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["default_model"] == "gemma-270m"
        # Verify the local file was written
        assert (tmp_path / ".chi_llm.json").exists()
    finally:
        os.chdir(old)
