import json
import subprocess
import sys


def run_cli_json(args):
    cmd = [sys.executable, "-m", "chi_llm.cli_main", *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def test_providers_schema_json_shape():
    data = run_cli_json(["providers", "schema", "--json"])  # type: ignore
    assert isinstance(data, dict)
    assert "providers" in data
    providers = data["providers"]
    assert isinstance(providers, list)

    # Ensure expected core providers are present
    types = {p.get("type") for p in providers}
    for t in {"local", "lmstudio", "ollama", "openai"}:
        assert t in types

    # Validate fields structure for a couple of providers
    pmap = {p.get("type"): p for p in providers}
    local_fields = {f.get("name") for f in pmap["local"].get("fields", [])}
    assert "model" in local_fields or "model_path" in local_fields

    openai_fields = {f.get("name") for f in pmap["openai"].get("fields", [])}
    assert "api_key" in openai_fields
