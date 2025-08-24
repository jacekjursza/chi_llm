import json
import subprocess
import sys


def run_cli_json(args):
    cmd = [sys.executable, "-m", "chi_llm.cli_main", *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def test_providers_list_json_shape():
    data = run_cli_json(["providers", "list", "--json"])  # type: ignore
    assert isinstance(data, list)
    assert len(data) > 0
    # Each item should have a type and implemented flag
    for item in data:
        assert isinstance(item, dict)
        assert "type" in item
        assert "implemented" in item
    # Ensure core providers are present
    types = {it.get("type") for it in data}
    for t in {"local", "lmstudio", "ollama", "openai", "claude-cli", "openai-cli"}:
        assert t in types
