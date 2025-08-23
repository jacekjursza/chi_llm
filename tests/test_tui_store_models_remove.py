from pathlib import Path


def test_remove_model_deletes_file_and_updates_config(tmp_path, monkeypatch):
    class FakeMgr:
        def __init__(self, *_):
            self.config = {"downloaded_models": ["m1", "m2"]}
            self._saved = 0

        def get_download_info(self, model_id: str):
            return ("repo/x", "file.gguf")

        def save_config(self, target: str = "global"):
            self._saved += 1

    from chi_llm.tui import store as store_mod
    import chi_llm.models as models_mod

    # Point models dir to tmp
    monkeypatch.setattr(models_mod, "MODEL_DIR", tmp_path)
    # Prepare existing file
    (tmp_path / "file.gguf").write_bytes(b"x")

    class FakeStore(store_mod.TUIStore):
        def __init__(self, *_):
            self._mgr = FakeMgr()

    s = FakeStore()
    removed = s.remove_model("m1")
    assert removed is True
    assert not (tmp_path / "file.gguf").exists()
    assert "m1" not in s._mgr.config["downloaded_models"]  # type: ignore[attr-defined]
    assert s._mgr._saved > 0  # type: ignore[attr-defined]


def test_get_models_dir_returns_existing_dir(tmp_path, monkeypatch):
    from chi_llm.tui import store as store_mod
    import chi_llm.models as models_mod

    monkeypatch.setattr(models_mod, "MODEL_DIR", tmp_path)

    s = store_mod.TUIStore()
    d = s.get_models_dir()
    assert Path(d) == tmp_path and tmp_path.exists()
