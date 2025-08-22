from unittest.mock import patch


def test_router_picks_by_tags_and_fallback():
    from chi_llm.providers.router import ProviderRouter

    class OKProv:
        def __init__(self, *_args, **_kwargs):
            pass

        def generate(self, prompt, **kwargs):
            return "OK"

        def chat(self, message, history=None):
            return "OK"

        def complete(self, text, **kwargs):
            return "OK"

    class FailProv(OKProv):
        def generate(self, prompt, **kwargs):
            raise RuntimeError("down")

    profiles = [
        {"name": "lm", "type": "lmstudio", "tags": ["general"], "priority": 10},
        {"name": "ol", "type": "ollama", "tags": ["coding"], "priority": 5},
    ]
    registry = {
        "lmstudio": lambda prof: FailProv(),
        "ollama": lambda prof: OKProv(),
    }
    r = ProviderRouter(profiles, registry=registry)
    out = r.generate("hi", tags=["coding"])
    assert out == "OK"


def test_micro_llm_uses_router_when_profiles(monkeypatch):
    import json
    from chi_llm.core import MicroLLM

    cfg = {
        "provider_profiles": [
            {"name": "lm", "type": "lmstudio", "tags": ["coding"], "priority": 1}
        ]
    }
    monkeypatch.setenv("CHI_LLM_CONFIG", json.dumps(cfg))

    # Patch registry to ensure no network or real deps are used
    from chi_llm.providers import router as router_mod

    class Dummy:
        def generate(self, prompt, **kwargs):
            return "R"

        def chat(self, message, history=None):
            return "C"

        def complete(self, text, **kwargs):
            return "P"

    monkeypatch.setattr(
        router_mod, "default_registry", lambda: {"lmstudio": lambda p: Dummy()}
    )

    llm = MicroLLM()
    llm.tags = ["coding"]
    assert llm.generate("x") == "R"
    assert llm.chat("x") == "C"
    assert llm.complete("x") == "P"
