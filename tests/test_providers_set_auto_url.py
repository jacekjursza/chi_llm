from types import SimpleNamespace
from unittest.mock import patch
import json
import os

from chi_llm.cli_modules import providers as prov_cli


def test_providers_set_auto_url_local_json(tmp_path, capsys, monkeypatch):
    # Work in temp project dir
    old = os.getcwd()
    os.chdir(tmp_path)
    try:
        # Stub find_url to return a fixed host/port
        with patch("chi_llm.cli_modules.providers_url.find_url") as find_url:
            find_url.return_value = {
                "provider": "ollama",
                "ok": True,
                "host": "172.22.224.1",
                "port": 11434,
            }
            args = SimpleNamespace(
                providers_command="set",
                type="ollama",
                host=None,
                port=None,
                model=None,
                model_path=None,
                api_key=None,
                context_window=None,
                n_gpu_layers=None,
                output_tokens=None,
                local=True,
                json=True,
                auto_url=True,
            )
            prov_cli.cmd_providers(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["provider"]["host"] == "172.22.224.1"
        assert data["provider"]["port"] == 11434
        # Verify file was written
        assert (tmp_path / ".chi_llm.json").exists()
    finally:
        os.chdir(old)
