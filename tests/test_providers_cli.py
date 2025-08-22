"""
Tests for providers CLI: list/current/set
"""

import json
import os
from types import SimpleNamespace

from chi_llm.cli_modules import providers as prov_cli


def test_providers_list_json(capsys):
    args = SimpleNamespace(providers_command="list", json=True)
    prov_cli.cmd_providers(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    types = [p["type"] for p in data]
    assert "lmstudio" in types and "ollama" in types and "local" in types


def test_providers_set_local_and_current_json(tmp_path, capsys, monkeypatch):
    # Arrange: move CWD to temp project folder
    old = os.getcwd()
    os.chdir(tmp_path)
    try:
        # Set provider locally
        args_set = SimpleNamespace(
            providers_command="set",
            type="lmstudio",
            host="127.0.0.1",
            port="1234",
            model="qwen2.5:latest",
            api_key=None,
            local=True,
        )
        prov_cli.cmd_providers(args_set)
        # Verify file created
        cfg_path = tmp_path / ".chi_llm.json"
        assert cfg_path.exists()
        cfg = json.loads(cfg_path.read_text())
        assert cfg["provider"]["type"] == "lmstudio"
        assert cfg["provider"]["host"] == "127.0.0.1"
        assert cfg["provider"]["port"] == 1234
        assert cfg["provider"]["model"] == "qwen2.5:latest"

        # Read current (json)
        args_cur = SimpleNamespace(providers_command="current", json=True)
        prov_cli.cmd_providers(args_cur)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["type"] == "lmstudio"
        assert data["host"] == "127.0.0.1"
        assert data["port"] == 1234
        assert data["model"] == "qwen2.5:latest"
    finally:
        os.chdir(old)
