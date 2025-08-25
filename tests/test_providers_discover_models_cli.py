import json
from types import SimpleNamespace

import chi_llm.cli_modules.providers_discovery as disc


def test_discover_models_lmstudio_json(monkeypatch, capsys):
    called = {}

    def _stub_discover(ptype, **kwargs):
        called.update({"ptype": ptype, **kwargs})
        return ["qwen2.5:latest", "gemma-270m"]

    monkeypatch.setattr(disc, "discover_models_for_provider", _stub_discover)
    args = SimpleNamespace(ptype="lmstudio", host="127.0.0.1", port=1234, json=True)

    disc.cmd_discover_models(args)
    out = capsys.readouterr().out
    data = json.loads(out)

    assert called["ptype"] == "lmstudio"
    assert called["host"] == "127.0.0.1"
    assert called["port"] == 1234
    assert data["provider"] == "lmstudio"
    assert len(data["models"]) == 2
    assert data["models"][0]["id"] == "qwen2.5:latest"


def test_discover_models_openai_args_passthrough(monkeypatch, capsys):
    called = {}

    def _stub_discover(ptype, **kwargs):
        called.update({"ptype": ptype, **kwargs})
        return ["gpt-4o-mini", "o3-mini"]

    monkeypatch.setattr(disc, "discover_models_for_provider", _stub_discover)
    args = SimpleNamespace(
        ptype="openai",
        base_url="https://api.openai.com",
        api_key="test-key",
        org_id="org-123",
        json=True,
    )

    disc.cmd_discover_models(args)
    out = capsys.readouterr().out
    data = json.loads(out)

    assert called["ptype"] == "openai"
    assert called["base_url"] == "https://api.openai.com"
    assert called["api_key"] == "test-key"
    assert called.get("org_id") == "org-123"
    assert data["provider"] == "openai"
    assert len(data["models"]) == 2
