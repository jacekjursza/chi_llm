import json
from unittest.mock import patch


def test_discovery_ollama_parses_tags():
    from chi_llm.providers import discovery as disc

    sample = {
        "models": [
            {
                "name": "llama3.2:latest",
                "size": 123456789,
                "details": {"parameter_size": "3B"},
            }
        ]
    }

    with patch.object(disc, "_http_get", return_value=sample):
        items = disc.list_ollama_models("127.0.0.1", 11434)
    assert items and items[0]["id"] == "llama3.2:latest"
    assert items[0]["size"] in {"3B", "118MB"}  # param_size or MB fallback


def test_discovery_lmstudio_parses_v1_models():
    from chi_llm.providers import discovery as disc

    sample = {"data": [{"id": "qwen2.5:latest"}, {"id": "phi3-mini"}]}
    with patch.object(disc, "_http_get", return_value=sample):
        items = disc.list_lmstudio_models("127.0.0.1", 1234)
    ids = [i["id"] for i in items]
    assert "qwen2.5:latest" in ids and "phi3-mini" in ids


def test_sdk_list_provider_models_uses_given_provider():
    from chi_llm import list_provider_models

    provider = {"type": "ollama", "host": "127.0.0.1", "port": 11434}

    with patch(
        "chi_llm.providers.discovery.list_ollama_models",
        return_value=[{"id": "m", "name": "m", "size": "2B"}],
    ):
        items = list_provider_models(provider)
    assert items and items[0]["id"] == "m"
