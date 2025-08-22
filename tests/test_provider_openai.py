"""
Tests for OpenAIProvider adapter.
Uses mocked OpenAI SDK to avoid network and dependency requirements.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace
import builtins
import os

import pytest


class _FakeChatCompletions:
    def create(self, model, messages, temperature=None, max_tokens=None):  # noqa: D401
        class _Resp:
            class _Choice:
                class _Msg:
                    content = "hello from openai"

                message = _Msg()

            choices = [_Choice()]

        return _Resp()


class _FakeOpenAIClient:
    def __init__(self, api_key=None, base_url=None):  # noqa: D401
        self.api_key = api_key
        self.base_url = base_url
        self.chat = SimpleNamespace(completions=_FakeChatCompletions())


def _install_fake_openai(monkeypatch):
    mod = SimpleNamespace(OpenAI=_FakeOpenAIClient)
    sys.modules["openai"] = mod
    return mod


def test_openai_provider_generate_with_fake_sdk(monkeypatch):
    _install_fake_openai(monkeypatch)
    from chi_llm.providers.openai import OpenAIProvider

    p = OpenAIProvider(api_key="sk-test", model="gpt-test")
    out = p.generate("hi")
    assert isinstance(out, str) and out


def test_openai_provider_chat_with_fake_sdk(monkeypatch):
    _install_fake_openai(monkeypatch)
    from chi_llm.providers.openai import OpenAIProvider

    p = OpenAIProvider(api_key="sk-test", model="gpt-test")
    out = p.chat("hi", history=[{"user": "u", "assistant": "a"}])
    assert "openai" in out


def test_openai_provider_missing_key_or_model():
    from chi_llm.providers.openai import OpenAIProvider

    with pytest.raises(RuntimeError):
        OpenAIProvider(api_key=None, model="gpt")
    with pytest.raises(RuntimeError):
        OpenAIProvider(api_key="sk", model=None)


def test_micro_llm_integration_with_openai(monkeypatch):
    # Configure provider via env
    os.environ["CHI_LLM_PROVIDER_TYPE"] = "openai"
    os.environ["CHI_LLM_PROVIDER_API_KEY"] = "sk-test"
    os.environ["CHI_LLM_PROVIDER_MODEL"] = "gpt-test"
    try:
        _install_fake_openai(monkeypatch)
        from chi_llm import MicroLLM

        llm = MicroLLM()
        assert llm.generate("hello")
        assert llm.chat("hello")
    finally:
        # Cleanup env to not affect other tests
        os.environ.pop("CHI_LLM_PROVIDER_TYPE", None)
        os.environ.pop("CHI_LLM_PROVIDER_API_KEY", None)
        os.environ.pop("CHI_LLM_PROVIDER_MODEL", None)
