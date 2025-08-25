from types import SimpleNamespace
from pathlib import Path
import os

from chi_llm.cli_modules import providers_url as urlmod


def test_build_candidates_wsl_nameserver(tmp_path, monkeypatch):
    # Simulate WSL via env var and a resolv.conf with a nameserver
    monkeypatch.setenv("WSL_DISTRO_NAME", "Ubuntu-22.04")
    rc = tmp_path / "resolv.conf"
    rc.write_text("nameserver 172.22.224.1\n", encoding="utf-8")

    hosts, ports = urlmod.build_candidates(
        "ollama", environ=os.environ, resolv_conf_path=rc
    )
    assert "172.22.224.1" in hosts
    assert 11434 in ports


def test_cmd_find_url_json_shape(monkeypatch, capsys):
    # Avoid real network: make _probe always fail and _is_wsl False
    monkeypatch.setenv("WSL_DISTRO_NAME", "")

    def fake_probe(ptype, host, port, timeout):
        return False, "nope"

    monkeypatch.setattr(urlmod, "_probe", fake_probe)

    args = SimpleNamespace(
        ptype="lmstudio", host=None, port=None, timeout="0.1", json=True
    )
    urlmod.cmd_find_url(args)
    out = capsys.readouterr().out
    assert '"provider": "lmstudio"' in out
    assert '"tried"' in out
