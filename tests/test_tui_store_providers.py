from pathlib import Path


def test_provider_get_set_local_and_global(tmp_path, monkeypatch):
    class FakeMgr:
        def __init__(self, *_):
            self.config_file = tmp_path / "global.json"
            self.config = {}

        def load_config(self):
            # simulate reload from global file
            import json, os

            cfg = {}
            if self.config_file.exists():
                cfg = json.loads(self.config_file.read_text())
            # local overrides
            local = Path.cwd() / ".chi_llm.json"
            if local.exists():
                lc = json.loads(local.read_text())
                cfg.update(lc)
            self.config = cfg

        def get_model_stats(self):
            return {"config_source": "global"}

    from chi_llm.tui import store as store_mod

    class FakeStore(store_mod.TUIStore):
        def __init__(self, *_):
            self._mgr = FakeMgr()

    s = FakeStore()

    # Write to global
    out = s.set_provider(
        "global", {"type": "lmstudio", "host": "127.0.0.1", "port": 1234}
    )
    assert out["type"] == "lmstudio"
    # File written
    assert (tmp_path / "global.json").exists()

    # Write to local (cwd)
    monkeypatch.chdir(tmp_path)
    out = s.set_provider(
        "local", {"type": "ollama", "host": "127.0.0.1", "port": 11434}
    )
    assert out["type"] == "ollama"
    assert (tmp_path / ".chi_llm.json").exists()


def test_provider_test_connection(monkeypatch):
    class FakeMgr:
        def __init__(self, *_):
            self.config_file = Path("/dev/null")
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

    # success
    monkeypatch.setattr(disc, "list_lmstudio_models", lambda host, port: [{"id": "x"}])
    s = FakeStore()
    res = s.test_connection()
    assert res["ok"] is True and res["models_count"] == 1

    # failure (empty)
    monkeypatch.setattr(disc, "list_lmstudio_models", lambda host, port: [])
    res = s.test_connection()
    assert res["ok"] is False
