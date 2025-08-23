from types import SimpleNamespace


def test_store_list_provider_models_uses_discovery(monkeypatch):
    # Fake mgr to provide provider config
    class FakeMgr:
        def __init__(self, *_):
            self.config_file = None
            self.config = {"provider": {"type": "lmstudio", "host": "h", "port": 1}}

        def get_model_stats(self):
            return {"config_source": "local"}

        def load_config(self):
            pass

    from chi_llm.tui import store as store_mod
    from chi_llm.providers import discovery as disc

    class FakeStore(store_mod.TUIStore):
        def __init__(self, *_):
            self._mgr = FakeMgr()

    monkeypatch.setattr(
        disc,
        "list_provider_models",
        lambda provider=None: [{"id": "m1", "name": "m1", "size": "1B"}],
    )

    s = FakeStore()
    out = s.list_provider_models()
    assert isinstance(out, list) and out and out[0]["id"] == "m1"
