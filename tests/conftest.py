"""
Pytest configuration and shared fixtures for chi_llm tests.
"""

import pytest
from unittest.mock import patch, MagicMock


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
