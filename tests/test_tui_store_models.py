from pathlib import Path
from types import SimpleNamespace


def test_set_default_model_updates_manager(monkeypatch):
    class FakeMgr:
        def __init__(self, *_):
            self.config_file = Path("/dev/null")
            self._set_calls = []
            self._model = SimpleNamespace(
                id="m1", name="Model 1", context_window=4096, recommended_ram_gb=2.0
            )

        def set_default_model(self, model_id: str, save_target: str = "global"):
            self._set_calls.append((model_id, save_target))
            self._model = SimpleNamespace(
                id=model_id,
                name=f"Model {model_id}",
                context_window=8192,
                recommended_ram_gb=4.0,
            )

        def load_config(self):
            pass

        def get_current_model(self):
            return self._model

        def get_model_stats(self):
            return {"config_source": "local"}

    from chi_llm.tui import store as store_mod

    class FakeStore(store_mod.TUIStore):
        def __init__(self, *_):
            self._mgr = FakeMgr()

    s = FakeStore()
    res = s.set_default_model("m2", scope="global")
    assert res["id"] == "m2"
    assert ("m2", "global") in s._mgr._set_calls  # type: ignore[attr-defined]


def test_download_model_marks_downloaded_and_returns_path(tmp_path, monkeypatch):
    class FakeMgr:
        def __init__(self, *_):
            self._marked = []

        def get_download_info(self, model_id: str):
            return ("repo/x", "file.gguf")

        def mark_downloaded(self, model_id: str):
            self._marked.append(model_id)

    from chi_llm.tui import store as store_mod

    # Patch MODEL_DIR to a tmp path
    import chi_llm.models as models_mod

    monkeypatch.setattr(models_mod, "MODEL_DIR", tmp_path)

    # Patch hf_hub_download to create a file and return its path
    def fake_hf_hub_download(repo_id, filename, local_dir, resume_download=True):
        p = Path(local_dir) / filename
        p.write_bytes(b"x")
        return str(p)

    import huggingface_hub as hf

    monkeypatch.setattr(hf, "hf_hub_download", fake_hf_hub_download, raising=False)

    class FakeStore(store_mod.TUIStore):
        def __init__(self, *_):
            self._mgr = FakeMgr()

    s = FakeStore()
    out = s.download_model("m1")
    assert out.endswith("file.gguf")
    assert (tmp_path / "file.gguf").exists()
    assert "m1" in s._mgr._marked  # type: ignore[attr-defined]
