import json
from types import SimpleNamespace

import chi_llm.cli_modules.providers_discovery as disc


class _StubResp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status = status
        self.headers = {}

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_discover_models_lmstudio_json(monkeypatch, capsys):
    # Arrange stubbed urlopen returning LM Studio-like models list
    payload = {"data": [{"id": "qwen2.5:latest"}, {"id": "gemma-270m"}]}

    def _stub_urlopen(url, timeout=3):
        assert "/v1/models" in url
        return _StubResp(payload, status=200)

    monkeypatch.setattr(disc._request, "urlopen", _stub_urlopen)
    args = SimpleNamespace(ptype="lmstudio", host="127.0.0.1", port=1234, json=True)

    # Act
    disc.cmd_discover_models(args)
    out = capsys.readouterr().out
    data = json.loads(out)

    # Assert
    assert data["provider"] == "lmstudio"
    assert len(data["models"]) == 2
    assert data["models"][0]["id"] == "qwen2.5:latest"


def test_discover_models_openai_headers_and_json(monkeypatch, capsys):
    # Capture headers from Request and return two models
    seen = {"auth": None, "org": None, "url": None}

    def _stub_urlopen(req, timeout=5):
        # req can be urllib.request.Request
        seen["url"] = getattr(
            req, "full_url", getattr(req, "get_full_url", lambda: None)()
        )
        # Python's Request stores headers in .headers
        headers = getattr(req, "headers", {})

        # Case-insensitive lookup
        def _h(name):
            for k, v in headers.items():
                if k.lower() == name.lower():
                    return v
            return None

        seen["auth"] = _h("Authorization")
        seen["org"] = _h("OpenAI-Organization")
        payload = {"data": [{"id": "gpt-4o-mini"}, {"id": "o3-mini"}]}
        return _StubResp(payload, status=200)

    monkeypatch.setattr(disc._request, "urlopen", _stub_urlopen)
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

    assert data["provider"] == "openai"
    assert len(data["models"]) == 2
    assert seen["auth"] == "Bearer test-key"
    assert seen["org"] == "org-123"
    assert "/v1/models" in (seen["url"] or "")
