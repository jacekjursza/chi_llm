import requests
from unittest.mock import patch


def _env_provider(monkeypatch, model="llama3.2:latest"):
    monkeypatch.setenv("CHI_LLM_PROVIDER_TYPE", "ollama")
    monkeypatch.setenv("CHI_LLM_PROVIDER_HOST", "127.0.0.1")
    monkeypatch.setenv("CHI_LLM_PROVIDER_PORT", "11434")
    monkeypatch.setenv("CHI_LLM_PROVIDER_MODEL", model)


def test_ollama_generate_happy_path(monkeypatch):
    _env_provider(monkeypatch)

    class Resp:
        status_code = 200

        def json(self):
            return {"response": "Hello from Ollama"}

    def fake_post(url, json=None, timeout=30):  # noqa: A002
        assert url.endswith("/api/generate")
        assert json["prompt"] == "Ping"
        assert json["stream"] is False
        return Resp()

    with patch("requests.post", side_effect=fake_post):
        from chi_llm.core import MicroLLM

        llm = MicroLLM()
        out = llm.generate("Ping")
        assert out == "Hello from Ollama"


def test_ollama_chat_happy_path(monkeypatch):
    _env_provider(monkeypatch, model="my-ollama-model")

    class Resp:
        status_code = 200

        def json(self):
            return {"message": {"role": "assistant", "content": "Pong"}}

    def fake_post(url, json=None, timeout=30):  # noqa: A002
        assert url.endswith("/api/chat")
        msgs = json["messages"]
        assert msgs[-1]["role"] == "user" and msgs[-1]["content"] == "Ping"
        return Resp()

    with patch("requests.post", side_effect=fake_post):
        from chi_llm.core import MicroLLM

        llm = MicroLLM()
        out = llm.chat("Ping", history=[{"user": "Hi"}, {"assistant": "Hello"}])
        assert out == "Pong"


def test_ollama_connection_error_surface(monkeypatch):
    _env_provider(monkeypatch)

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
            assert "Ollama" in msg
            assert "http://127.0.0.1:11434" in msg
