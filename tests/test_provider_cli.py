from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import patch


def _setup_env(ptype: str, model: str | None = None):
    os.environ["CHI_LLM_PROVIDER_TYPE"] = ptype
    if model:
        os.environ["CHI_LLM_PROVIDER_MODEL"] = model


def _cleanup_env():
    os.environ.pop("CHI_LLM_PROVIDER_TYPE", None)
    os.environ.pop("CHI_LLM_PROVIDER_MODEL", None)


def test_claude_cli_generate_and_chat(monkeypatch):
    _setup_env("claude-cli", model="claude-3-7-sonnet")
    try:
        # Pretend binary exists
        monkeypatch.setenv("PATH", "/usr/bin:/bin")

        def fake_which(name):
            assert name == "claude"
            return "/usr/bin/claude"

        # Capture subprocess input and ensure model flag present
        calls = []

        def fake_run(
            cmd, input=None, stdout=None, stderr=None, timeout=None, check=None
        ):  # noqa: A002
            calls.append(SimpleNamespace(cmd=cmd, input=input, timeout=timeout))
            assert cmd[0] == "claude"
            assert "-m" in cmd and "claude-3-7-sonnet" in cmd
            # Return hello on first call (generate) and pong on second (chat)
            if len(calls) == 1:
                out = b"Hello from Claude"
            else:
                # Verify history is flattened
                data = (input or b"").decode("utf-8")
                assert (
                    "User: Hi" in data
                    and "Assistant: Hello" in data
                    and "User: Ping" in data
                )
                out = b"Pong"
            return SimpleNamespace(returncode=0, stdout=out, stderr=b"")

        with patch("shutil.which", side_effect=fake_which), patch(
            "subprocess.run", side_effect=fake_run
        ):
            from chi_llm import MicroLLM

            llm = MicroLLM()
            assert llm.generate("Ping").startswith("Hello")
            r = llm.chat("Ping", history=[{"user": "Hi"}, {"assistant": "Hello"}])
            assert r == "Pong"
    finally:
        _cleanup_env()


def test_claude_cli_missing_binary(monkeypatch):
    _setup_env("claude-cli", model="claude-3")
    try:

        def fake_which(name):
            return None

        with patch("shutil.which", side_effect=fake_which):
            from chi_llm import MicroLLM

            llm = MicroLLM()
            try:
                llm.generate("Hi")
                assert False, "Expected RuntimeError"
            except RuntimeError as e:
                assert "Claude CLI" in str(e)
    finally:
        _cleanup_env()


def test_openai_cli_generate_and_chat(monkeypatch):
    _setup_env("openai-cli", model="gpt-4o-mini")
    try:

        def fake_which(name):
            assert name == "openai"
            return "/usr/bin/openai"

        calls = []

        def fake_run(
            cmd, input=None, stdout=None, stderr=None, timeout=None, check=None
        ):  # noqa: A002
            calls.append(SimpleNamespace(cmd=cmd, input=input, timeout=timeout))
            assert cmd[0] == "openai"
            # With no extra args, provider adds minimal [-m model]
            assert "-m" in cmd and "gpt-4o-mini" in cmd
            if len(calls) == 1:
                out = b"Hi from OpenAI CLI"
            else:
                data = (input or b"").decode("utf-8")
                assert "User: Ping" in data
                out = b"Pong from OpenAI"
            return SimpleNamespace(returncode=0, stdout=out, stderr=b"")

        with patch("shutil.which", side_effect=fake_which), patch(
            "subprocess.run", side_effect=fake_run
        ):
            from chi_llm import MicroLLM

            llm = MicroLLM()
            assert "OpenAI" in llm.generate("Ping")
            r = llm.chat("Ping")
            assert r.startswith("Pong")
    finally:
        _cleanup_env()


def test_openai_cli_missing_binary(monkeypatch):
    _setup_env("openai-cli", model="gpt-4o-mini")
    try:
        with patch("shutil.which", return_value=None):
            from chi_llm import MicroLLM

            llm = MicroLLM()
            try:
                llm.generate("Hi")
                assert False, "Expected RuntimeError"
            except RuntimeError as e:
                assert "OpenAI CLI" in str(e)
    finally:
        _cleanup_env()
