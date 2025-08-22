from pathlib import Path


def test_get_diagnostics_uses_cli_module(monkeypatch):
    class FakeDiag:
        def _gather(self):  # pragma: no cover - bound method form not used
            return {"python": {"version": "x"}}

    # Monkeypatch the module with a fake _gather function
    from chi_llm.tui import store as store_mod
    import types

    fake_diag_mod = types.SimpleNamespace(
        _gather=lambda: {"python": {"version": "3.10"}}
    )

    def fake_import(name):
        if name == "..cli_modules":
            raise ImportError
        return None

    # Patch import by replacing reference in sys.modules
    import sys

    sys.modules["chi_llm.cli_modules.diagnostics"] = fake_diag_mod  # type: ignore

    s = store_mod.TUIStore()
    d = s.get_diagnostics()
    assert d.get("python", {}).get("version", "").startswith("3.10")


def test_export_diagnostics_writes_file(tmp_path, monkeypatch):
    from chi_llm.tui import store as store_mod

    s = store_mod.TUIStore()
    # Stub get_diagnostics to a small dict
    monkeypatch.setattr(s, "get_diagnostics", lambda: {"ok": True})
    out = s.export_diagnostics(tmp_path / "diag.json")
    assert Path(out).exists()
    assert (tmp_path / "diag.json").read_text().strip().startswith("{")
