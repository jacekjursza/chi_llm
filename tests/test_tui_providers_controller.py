def test_providers_controller_set_and_test(monkeypatch):
    class FakeStore:
        def __init__(self):
            self.set_calls = []
            self._prov = {"type": "local", "host": "127.0.0.1", "port": None}

        def get_provider(self):
            return dict(self._prov)

        def set_provider(self, scope, provider):
            self.set_calls.append((scope, dict(provider)))
            self._prov = dict(provider)
            return dict(self._prov)

        def test_connection(self, provider=None):
            p = provider or self._prov
            if p.get("type") == "lmstudio":
                return {"ok": True, "models_count": 3}
            if p.get("type") == "ollama":
                return {"ok": False, "models_count": 0}
            return {"ok": True, "models_count": 0}

    from chi_llm.tui.views.providers import ProvidersController

    s = FakeStore()
    c = ProvidersController(s)

    assert c.get()["type"] == "local"
    out = c.set("local", {"type": "lmstudio", "host": "h", "port": 1})
    assert out["type"] == "lmstudio"
    assert ("local", {"type": "lmstudio", "host": "h", "port": 1}) in s.set_calls

    res = c.test({"type": "lmstudio", "host": "h", "port": 1})
    assert res["ok"] is True and res["models_count"] == 3
