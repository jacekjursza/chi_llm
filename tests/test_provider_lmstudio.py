import os
from unittest.mock import patch, MagicMock


def _env_provider(monkeypatch, model="qwen2.5:latest"):
    monkeypatch.setenv("CHI_LLM_PROVIDER_TYPE", "lmstudio")
    monkeypatch.setenv("CHI_LLM_PROVIDER_HOST", "127.0.0.1")
    monkeypatch.setenv("CHI_LLM_PROVIDER_PORT", "1234")
    monkeypatch.setenv("CHI_LLM_PROVIDER_MODEL", model)


def test_lmstudio_generate_happy_path(monkeypatch):
    _env_provider(monkeypatch)

    # Mock requests.post JSON response for /v1/completions
    class Resp:
        status_code = 200

        def json(self):
            return {"choices": [{"text": "Hello from LM Studio"}]}

    def fake_post(url, json=None, timeout=30):  # noqa: A002
        assert url.endswith("/v1/completions")
        assert json["prompt"] == "Ping"
        return Resp()

    with patch("requests.post", side_effect=fake_post):
        from chi_llm.core import MicroLLM

        llm = MicroLLM()
        out = llm.generate("Ping")
        assert out == "Hello from LM Studio"


def test_lmstudio_chat_happy_path(monkeypatch):
    _env_provider(monkeypatch, model="my-model")

    # Mock requests.post JSON response for /v1/chat/completions
    class Resp:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"role": "assistant", "content": "Pong"}}]}

    def fake_post(url, json=None, timeout=30):  # noqa: A002
        assert url.endswith("/v1/chat/completions")
        msgs = json["messages"]
        assert msgs[-1]["role"] == "user" and msgs[-1]["content"] == "Ping"
        return Resp()

    with patch("requests.post", side_effect=fake_post):
        from chi_llm.core import MicroLLM

        llm = MicroLLM()
        out = llm.chat("Ping", history=[{"user": "Hi"}, {"assistant": "Hello"}])
        assert out == "Pong"


def test_lmstudio_connection_error_surface(monkeypatch):
    _env_provider(monkeypatch)

    # Simulate a network error from requests
    import requests

    def boom(url, json=None, timeout=30):  # noqa: A002
        raise requests.ConnectionError("refused")

    with patch("requests.post", side_effect=boom):
        from chi_llm.core import MicroLLM

        llm = MicroLLM()
        try:
            llm.generate("Ping")
            assert False, "Expected RuntimeError"
        except RuntimeError as e:
            msg = str(e)
            assert "LM Studio" in msg
            assert "http://127.0.0.1:1234/v1" in msg
