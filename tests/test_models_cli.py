"""
Tests for models CLI JSON outputs and setup recommend.
"""

import json
from types import SimpleNamespace
from unittest.mock import patch

from chi_llm.cli_modules import models as models_cli
from chi_llm.models import MODELS


def test_models_info_json(capsys):
    # Use an existing model from registry
    model_id = "gemma-270m"

    class FakeMgr:
        def is_downloaded(self, mid):
            return mid == model_id

        def get_current_model(self):
            return MODELS[model_id]

    with patch.object(models_cli, "ModelManager", return_value=FakeMgr()):
        args = SimpleNamespace(models_command="info", model_id=model_id, json=True)
        models_cli.cmd_models(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["id"] == model_id
    assert data["downloaded"] is True


def test_setup_recommend_json(capsys):
    # Recommend a known model id
    reco = MODELS["gemma-270m"]

    class FakeMgr:
        def recommend_model(self):
            return reco

    with patch.object(models_cli, "ModelManager", return_value=FakeMgr()):
        args = SimpleNamespace(setup_command="recommend", json=True)
        models_cli.cmd_setup(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["id"] == "gemma-270m"
