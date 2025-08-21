"""
Tests for bootstrap CLI command (non-interactive paths).
"""

from pathlib import Path
from types import SimpleNamespace

from chi_llm.cli_modules import bootstrap


def test_bootstrap_local_json(tmp_path):
    args = SimpleNamespace(
        path=str(tmp_path),
        provider="local",
        model_id="gemma-270m",
        yaml=False,
        extras="none",
    )
    bootstrap.cmd_bootstrap(args)

    # Files should be created
    assert (tmp_path / ".chi_llm.json").exists()
    assert (tmp_path / ".env.sample").exists()
    assert (tmp_path / "llm-requirements.txt").exists()

    # JSON should contain default_model
    content = (tmp_path / ".chi_llm.json").read_text(encoding="utf-8")
    assert "default_model" in content and "gemma-270m" in content


def test_bootstrap_yaml_and_extras(tmp_path):
    args = SimpleNamespace(
        path=str(tmp_path),
        provider="local",
        model_id="qwen3-1.7b",
        yaml=True,
        extras="rag",
    )
    bootstrap.cmd_bootstrap(args)

    assert (tmp_path / ".chi_llm.yaml").exists()
    # Requirements should reflect extras
    req = (tmp_path / "llm-requirements.txt").read_text(encoding="utf-8")
    assert "chi-llm[rag]" in req


def test_bootstrap_external_provider(tmp_path):
    args = SimpleNamespace(
        path=str(tmp_path),
        provider="openai",
        model_id="gpt-4o-mini",
        yaml=False,
        extras="none",
    )
    bootstrap.cmd_bootstrap(args)

    cfg = (tmp_path / ".chi_llm.json").read_text(encoding="utf-8")
    env = (tmp_path / ".env.sample").read_text(encoding="utf-8")

    assert '"provider"' in cfg and "openai" in cfg
    assert "OPENAI_API_KEY" in env and "CHI_LLM_PROVIDER_TYPE=openai" in env
