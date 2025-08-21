"""
Tests for the diagnostics CLI command.
"""

import json
from types import SimpleNamespace
from unittest.mock import patch

from chi_llm.cli_modules import diagnostics as diag
from chi_llm.models import MODELS


def test_diagnostics_json_basic(capsys, tmp_path, monkeypatch):
    # Make cache dir point to temp and writable
    monkeypatch.setattr(diag, "MODELS_DIR", tmp_path)

    # Simulate no node/npm
    with patch("chi_llm.cli_modules.diagnostics.which", side_effect=[None, None]):
        # Fake ModelManager
        class FakeMgr:
            def get_model_stats(self):
                return {"available_ram_gb": 1.0}

            def get_current_model(self):
                return MODELS["gemma-270m"]

        with patch.object(diag, "ModelManager", return_value=FakeMgr()):
            # Stub network check
            with patch.object(diag, "_check_network", return_value={"hf": True, "ok": True}):
                args = SimpleNamespace(json=True)
                diag.cmd_diagnostics(args)

    out = capsys.readouterr().out
    data = json.loads(out)
    assert "python" in data and data["python"]["ok"] is True
    assert data["node"]["installed"] is False
    assert data["cache"]["exists"] is True and data["cache"]["writable"] is True
    assert data["model"]["current"] == "gemma-270m"
    # available_ram 1.0GB vs recommended >=2.0GB => fits False
    assert data["model"]["fits"] is False
    assert data["network"]["ok"] is True

