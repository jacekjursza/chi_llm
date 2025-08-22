from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List

import json


def test_store_get_and_set_config(tmp_path, monkeypatch):
    # Fake ModelManager with minimal API
    class FakeMgr:
        def __init__(self, *_):
            self.config_file = tmp_path / "global.json"
            self.config = {
                "default_model": "gemma-270m",
                "preferred_context": 8192,
                "preferred_max_tokens": 4096,
            }

        def get_model_stats(self):
            return {"config_source": "global"}

        def load_config(self):  # refresh
            if self.config_file.exists():
                self.config = json.loads(self.config_file.read_text())

    # Patch store to use FakeMgr
    from chi_llm.tui import store as store_mod

    # Inject FakeMgr as ModelManager inside TUIStore
    class FakeStore(store_mod.TUIStore):
        def __init__(self, *_):
            self._mgr = FakeMgr()

    s = FakeStore()

    cfg = s.get_config()
    assert cfg["default_model"] == "gemma-270m"
    assert cfg["preferred_context"] == 8192
    assert cfg["source"] == "global"

    # set_config should write atomically to local/global; test global
    out = s.set_config("global", "preferred_context", "123")
    assert out["preferred_context"] == 123  # coerced to int
    # verify file contents
    saved = json.loads((tmp_path / "global.json").read_text())
    assert saved["preferred_context"] == 123


def test_store_models_and_current_model(monkeypatch):
    # Build fake model objects
    Model = SimpleNamespace  # simple object with attributes

    models = [
        Model(
            id="m1",
            name="Model 1",
            size="1B",
            file_size_mb=100,
            context_window=4096,
            description="",
            recommended_ram_gb=2.0,
            tags=["tiny"],
        ),
        Model(
            id="m2",
            name="Model 2",
            size="2B",
            file_size_mb=200,
            context_window=8192,
            description="",
            recommended_ram_gb=4.0,
            tags=["small"],
        ),
    ]

    class FakeMgr:
        def __init__(self, *_):
            self.config_file = Path("/dev/null")
            self.config = {"default_model": "m1"}

        def list_models(self, show_all: bool = False):
            return models

        def is_downloaded(self, model_id: str) -> bool:
            return model_id == "m2"

        def get_current_model(self):
            return models[0]

        def get_model_stats(self):
            return {"config_source": "local"}

    from chi_llm.tui import store as store_mod

    class FakeStore(store_mod.TUIStore):
        def __init__(self, *_):
            self._mgr = FakeMgr()

    s = FakeStore()
    ms = s.list_models()
    assert len(ms) == 2
    by_id = {m["id"]: m for m in ms}
    assert by_id["m1"]["downloaded"] is False
    assert by_id["m2"]["downloaded"] is True

    cur = s.get_current_model()
    assert cur["id"] == "m1" and cur["source"] == "local"
