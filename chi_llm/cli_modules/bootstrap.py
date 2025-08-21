"""
Bootstrap command to scaffold per-project configuration for chi_llm.

Generates:
- .chi_llm.json (canonical project config)
- .env.sample (API keys / provider env placeholders)
- llm-requirements.txt (optional minimal requirements)

Interactive prompts are used when flags are not provided.
"""

from argparse import _SubParsersAction
from pathlib import Path
from typing import Optional, Dict, List

import json

try:
    from ..models import ModelManager  # type: ignore

    HAS_MODELS = True
except Exception:  # pragma: no cover - optional at runtime
    HAS_MODELS = False


def _choose_provider_interactive() -> str:
    providers = [
        "local",
        "ollama",
        "lmstudio",
        "openai",
        "anthropic",
        "groq",
        "gemini",
    ]
    print("Select provider:")
    for i, p in enumerate(providers, 1):
        print(f"  {i}. {p}")
    while True:
        raw = input("Provider [1]: ").strip() or "1"
        if raw.isdigit() and 1 <= int(raw) <= len(providers):
            return providers[int(raw) - 1]
        print("Invalid selection. Please choose a number from the list.")


def _choose_model_interactive() -> str:
    if not HAS_MODELS:
        return "gemma-270m"
    mgr = ModelManager()
    items: List = mgr.list_models(show_all=False)
    print("Select local model (recommended for your system):")
    for i, m in enumerate(items, 1):
        print(f"  {i}. {m.name} [{m.id}] — {m.size}, ctx {m.context_window}")
    default = 1
    while True:
        raw = input(f"Model [default {default}]: ").strip() or str(default)
        if raw.isdigit() and 1 <= int(raw) <= len(items):
            return items[int(raw) - 1].id
        print("Invalid selection. Please choose a number from the list.")


def _write_text_file(path: Path, content: str, force: bool = False) -> bool:
    if path.exists() and not force:
        print(f"⚠️  {path.name} already exists. Skipping (use --force to overwrite).")
        return False
    path.write_text(content, encoding="utf-8")
    print(f"✅ Wrote {path}")
    return True


def _emit_project_config(
    target: Path, provider: str, model_id: Optional[str], use_yaml: bool
) -> None:
    # Canonical JSON by default (YAML optional flag)
    cfg: Dict = {}
    if provider == "local":
        if not model_id:
            model_id = "gemma-270m"
        cfg = {"default_model": model_id}
    else:
        # External providers: encode provider config; keep minimal
        cfg = {"provider": {"type": provider}}
        if model_id:
            cfg["provider"]["model"] = model_id

    if use_yaml:
        try:
            import yaml  # type: ignore

            text = yaml.safe_dump(cfg, sort_keys=False)
            _write_text_file(target / ".chi_llm.yaml", text)
        except Exception as e:  # pragma: no cover - optional
            print(f"YAML not available, writing JSON instead ({e}).")
            text = json.dumps(cfg, indent=2)
            _write_text_file(target / ".chi_llm.json", text)
    else:
        text = json.dumps(cfg, indent=2)
        _write_text_file(target / ".chi_llm.json", text)


def _emit_env_sample(target: Path, provider: str, model_id: Optional[str]) -> None:
    lines: List[str] = [
        "# Copy to .env and 'source .env' or use python-dotenv\n",
    ]
    if provider == "local":
        # Optional override example
        if model_id:
            lines += [f"#CHI_LLM_MODEL={model_id}\n"]
        else:
            lines += ["#CHI_LLM_MODEL=gemma-270m\n"]
    else:
        # Generic provider env keys supported by utils.load_config
        lines += [
            f"CHI_LLM_PROVIDER_TYPE={provider}\n",
            f"CHI_LLM_PROVIDER_MODEL={model_id or ''}\n",
        ]
        if provider in {"openai", "anthropic", "groq", "gemini"}:
            key_map = {
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "groq": "GROQ_API_KEY",
                "gemini": "GEMINI_API_KEY",
            }
            lines += [f"{key_map[provider]}=\n", "CHI_LLM_PROVIDER_API_KEY=\n"]
        if provider == "ollama":
            lines += [
                "CHI_LLM_PROVIDER_HOST=localhost\n",
                "CHI_LLM_PROVIDER_PORT=11434\n",
            ]
        if provider == "lmstudio":
            lines += [
                "CHI_LLM_PROVIDER_HOST=localhost\n",
                "CHI_LLM_PROVIDER_PORT=1234\n",
            ]
    _write_text_file(target / ".env.sample", "".join(lines))


def _emit_requirements(target: Path, extras: str) -> None:
    # Minimal project requirements for LLM usage
    # Keep lean; users can swap to rag/full as needed
    pkg = "chi-llm"
    if extras and extras != "none":
        pkg = f"chi-llm[{extras}]"
    content = f"{pkg}\n"
    _write_text_file(target / "llm-requirements.txt", content)


def cmd_bootstrap(args):
    dest = Path(args.path or ".").resolve()
    dest.mkdir(parents=True, exist_ok=True)

    provider = (args.provider or "").strip().lower()
    model_id = args.model_id
    use_yaml = bool(getattr(args, "yaml", False))
    extras = (args.extras or "none").strip().lower()

    if not provider:
        provider = _choose_provider_interactive()

    if provider == "local" and not model_id:
        model_id = _choose_model_interactive() if HAS_MODELS else "gemma-270m"

    _emit_project_config(dest, provider, model_id, use_yaml)
    _emit_env_sample(dest, provider, model_id)
    _emit_requirements(dest, extras)

    print("\n🎉 Bootstrap complete!")
    cfg_path = (dest / ".chi_llm.yaml") if use_yaml else (dest / ".chi_llm.json")
    print(f"  • Config: {cfg_path}")
    print(f"  • Env sample: {dest / '.env.sample'}")
    print(f"  • Requirements: {dest / 'llm-requirements.txt'}")


def register(subparsers: _SubParsersAction):
    sub = subparsers.add_parser(
        "bootstrap",
        help="Scaffold project config (.chi_llm.json) and .env.sample",
    )
    sub.add_argument(
        "path", nargs="?", default=".", help="Target directory (default: current)"
    )
    sub.add_argument(
        "--provider",
        choices=[
            "local",
            "ollama",
            "lmstudio",
            "openai",
            "anthropic",
            "groq",
            "gemini",
        ],
        help="Provider to configure (default: interactive)",
    )
    sub.add_argument("--model-id", help="Model id for local or external provider")
    sub.add_argument(
        "--yaml",
        action="store_true",
        help="Write YAML config (.chi_llm.yaml) instead of JSON",
    )
    sub.add_argument(
        "--extras",
        choices=["none", "standard", "rag", "rag-st", "full"],
        default="none",
        help="Choose chi-llm extras for llm-requirements.txt",
    )
    sub.set_defaults(func=cmd_bootstrap)
