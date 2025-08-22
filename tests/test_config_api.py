"""
Tests for chi_llm.config helper API (card 009).
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from chi_llm import resolve_model, get_provider_settings, MODELS


def test_resolve_model_basic_shape():
    eff = resolve_model()
    assert isinstance(eff, dict)
    assert set(["model_id", "model_path", "context_window", "source"]).issubset(
        eff.keys()
    )
    # Model id should be a known model (or at least a non-empty string)
    assert isinstance(eff["model_id"], str) and len(eff["model_id"]) > 0
    assert eff["model_id"] in MODELS
    assert isinstance(eff["context_window"], int)
    assert eff["source"] in {"default", "local", "project", "global", "env", "custom"}


def test_get_provider_settings_defaults():
    # Without explicit provider config, defaults to local and infers model
    ps = get_provider_settings()
    assert ps["type"] == "local"
    assert isinstance(ps.get("model"), (str, type(None)))


@patch.dict(
    "os.environ",
    {
        "CHI_LLM_PROVIDER_TYPE": "ollama",
        "CHI_LLM_PROVIDER_HOST": "127.0.0.1",
        "CHI_LLM_PROVIDER_PORT": "11434",
        "CHI_LLM_PROVIDER_MODEL": "qwen2.5-coder-1.5b",
    },
)
def test_get_provider_settings_env_override():
    ps = get_provider_settings()
    assert ps["type"] == "ollama"
    assert ps["host"] == "127.0.0.1"
    assert ps["port"] in (11434, "11434")
    assert ps["model"] == "qwen2.5-coder-1.5b"


def test_get_provider_settings_from_file(tmp_path: Path):
    cfg = {
        "provider": {
            "type": "lmstudio",
            "host": "localhost",
            "port": 1234,
            "model": "some-model",
            "timeout": 10.0,
        }
    }
    p = tmp_path / "conf.json"
    p.write_text(json.dumps(cfg))
    ps = get_provider_settings(str(p))
    assert ps["type"] == "lmstudio"
    assert ps["host"] == "localhost"
    assert ps["port"] == 1234
    assert ps["model"] == "some-model"
    assert ps["timeout"] == 10.0
