from types import SimpleNamespace


def test_models_controller_set_default_calls_store_with_scope(monkeypatch):
    calls = []

    class FakeStore:
        def set_default_model(self, model_id: str, scope: str = "local"):
            calls.append((model_id, scope))
            return {
                "id": model_id,
                "name": f"Model {model_id}",
                "context_window": 8192,
                "recommended_ram_gb": 4.0,
                "source": "local" if scope == "local" else "global",
            }

    from chi_llm.tui.views.models import ModelsController

    c = ModelsController(FakeStore())
    cur = c.set_default("mX", scope="global")
    assert cur["id"] == "mX"
    assert ("mX", "global") in calls


def test_models_controller_download_calls_store(monkeypatch, tmp_path):
    class FakeStore:
        def download_model(self, model_id: str) -> str:
            return str(tmp_path / f"{model_id}.gguf")

    from chi_llm.tui.views.models import ModelsController

    c = ModelsController(FakeStore())
    out = c.download("m1")
    assert out.endswith("m1.gguf")


def test_formatting_helpers_include_mark_and_fields():
    from chi_llm.tui.views.models import _format_model_row, format_model_details

    m = {
        "id": "m1",
        "name": "Model 1",
        "size": "1B",
        "file_size_mb": 100,
        "context_window": 4096,
        "recommended_ram_gb": 2.0,
        "tags": ["tiny"],
        "downloaded": True,
    }
    row = _format_model_row(m)
    assert "✅" in row and "ctx=4096" in row and "RAM≈2.0GB" in row

    details = "\n".join(format_model_details(m))
    assert "ID: m1" in details and "Downloaded: yes" in details
