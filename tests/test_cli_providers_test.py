import json
from chi_llm.cli_main import main


def run_cli(args):
    import io
    import sys

    buf = io.StringIO()
    old_out = sys.stdout
    try:
        sys.stdout = buf
        main(args)
    except SystemExit as e:
        # CLI may call sys.exit; ignore normal exits
        if int(getattr(e, "code", 0) or 0) not in (0,):
            raise
    finally:
        sys.stdout = old_out
    return buf.getvalue()


def test_providers_test_local_ok():
    out = run_cli(["providers", "test", "--type", "local", "--json"])
    obj = json.loads(out)
    assert obj["ok"] is True
    assert "local" in obj["message"].lower()


def test_providers_test_local_custom_missing_path():
    out = run_cli(["providers", "test", "--type", "local-custom", "--json"])
    obj = json.loads(out)
    assert obj["ok"] is False
    assert "missing" in obj["message"].lower()


def test_providers_test_openai_missing_key():
    out = run_cli(["providers", "test", "--type", "openai", "--json"])
    obj = json.loads(out)
    assert obj["ok"] is False
    assert "missing api_key" in obj["message"].lower()


def test_providers_test_lmstudio_unreachable_fast():
    # Use an unlikely port and a tiny timeout to avoid hanging
    out = run_cli(
        [
            "providers",
            "test",
            "--type",
            "lmstudio",
            "--host",
            "127.0.0.1",
            "--port",
            "1",
            "--timeout",
            "0.2",
            "--json",
        ]
    )
    obj = json.loads(out)
    assert obj["ok"] is False
    assert obj.get("latency_ms") is not None
