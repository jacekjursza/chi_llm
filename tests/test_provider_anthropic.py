"""
Tests for AnthropicProvider adapter.
Uses a faked Anthropic SDK to avoid network/dependency.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace
import os

import pytest


class _FakeContentPart:
    def __init__(self, text: str):
        self.text = text


class _FakeMessages:
    def create(
        self, model=None, messages=None, max_tokens=None, temperature=None
    ):  # noqa: D401
        class _Resp:
            content = [_FakeContentPart("hello from anthropic")]

        return _Resp()


class _FakeAnthropicClient:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.messages = _FakeMessages()


def _install_fake_anthropic(monkeypatch):
    mod = SimpleNamespace(Anthropic=_FakeAnthropicClient)
    sys.modules["anthropic"] = mod
    return mod


def test_anthropic_provider_generate_with_fake_sdk(monkeypatch):
    _install_fake_anthropic(monkeypatch)
    from chi_llm.providers.anthropic import AnthropicProvider

    p = AnthropicProvider(api_key="sk-ant-test", model="claude-3-haiku-20240307")
    out = p.generate("hi")
    assert isinstance(out, str) and out


def test_anthropic_provider_chat_with_fake_sdk(monkeypatch):
    _install_fake_anthropic(monkeypatch)
    from chi_llm.providers.anthropic import AnthropicProvider

    p = AnthropicProvider(api_key="sk-ant-test", model="claude-3-haiku-20240307")
    out = p.chat("hi", history=[{"user": "u", "assistant": "a"}])
    assert "anthropic" in out


def test_anthropic_provider_missing_key_or_model():
    from chi_llm.providers.anthropic import AnthropicProvider

    with pytest.raises(RuntimeError):
        AnthropicProvider(api_key=None, model="claude")
    with pytest.raises(RuntimeError):
        AnthropicProvider(api_key="sk", model=None)


def test_micro_llm_integration_with_anthropic(monkeypatch):
    # Configure provider via env
    os.environ["CHI_LLM_PROVIDER_TYPE"] = "anthropic"
    os.environ["CHI_LLM_PROVIDER_API_KEY"] = "sk-ant-test"
    os.environ["CHI_LLM_PROVIDER_MODEL"] = "claude-3-haiku-20240307"
    try:
        _install_fake_anthropic(monkeypatch)
        from chi_llm import MicroLLM

        llm = MicroLLM()
        assert llm.generate("hello")
        assert llm.chat("hello")
    finally:
        # Cleanup env to not affect other tests
        os.environ.pop("CHI_LLM_PROVIDER_TYPE", None)
        os.environ.pop("CHI_LLM_PROVIDER_API_KEY", None)
        os.environ.pop("CHI_LLM_PROVIDER_MODEL", None)
