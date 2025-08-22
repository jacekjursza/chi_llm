"""
Pytest configuration and shared fixtures for chi_llm tests.
"""

import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def _offline_and_fast_llama(monkeypatch, tmp_path_factory):
    """Ensure tests run offline and avoid heavy model loads.

    - Monkeypatch hf_hub_download to return a temp model path
    - Replace Llama with a lightweight fake implementation
    - Disable HF telemetry to keep CI logs clean
    """
    # Disable any telemetry
    monkeypatch.setenv("HF_HUB_DISABLE_TELEMETRY", "1")

    # Temp model file path returned by mocked download
    tmp_dir = tmp_path_factory.mktemp("models")
    fake_model = tmp_dir / "model.gguf"
    fake_model.write_bytes(b"")

    def _fake_hf_download(**kwargs):  # type: ignore[no-redef]
        return str(fake_model)

    # Patch both the place used in core and the original symbol
    try:
        monkeypatch.setattr(
            "chi_llm.core.hf_hub_download", _fake_hf_download, raising=True
        )
    except Exception:
        pass
    try:
        import huggingface_hub  # type: ignore

        monkeypatch.setattr(
            huggingface_hub, "hf_hub_download", _fake_hf_download, raising=False
        )
    except Exception:
        pass

    # Lightweight fake Llama to avoid native loading
    class _FakeLlama:
        def __init__(self, *args, **kwargs):
            pass

        def __call__(self, *args, **kwargs):
            return {"choices": [{"text": "Mocked response"}]}

    try:
        monkeypatch.setattr("chi_llm.core.Llama", _FakeLlama, raising=True)
    except Exception:
        pass


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the model singleton before each test."""
    import chi_llm.core

    chi_llm.core._model_instance = None
    yield
    chi_llm.core._model_instance = None


@pytest.fixture
def mock_llama_response():
    """Create a mock Llama response."""
    mock = MagicMock()

    # Make it callable and return proper response structure
    def side_effect(*args, **kwargs):
        return {"choices": [{"text": "Mocked response"}]}

    mock.side_effect = side_effect
    mock.__call__ = side_effect

    return mock


@pytest.fixture
def mock_model_download():
    """Mock model download."""
    with patch("chi_llm.core.hf_hub_download") as mock:
        mock.return_value = "/fake/path/model.gguf"
        yield mock
