"""Connectivity tests for providers (CLI subcommand).

Outputs normalized JSON suitable for UI consumption:
  { ok: bool, status: int|None, latency_ms: int|None, message: str }

The goal is to be lightweight and avoid mandatory external deps.
Uses requests when available, else urllib.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import json as _json
import time
import os
from urllib.parse import urljoin
import subprocess
import sys
import tempfile
import threading


def _print_json(obj: Dict[str, Any]) -> None:
    print(_json.dumps(obj, indent=2))


def _http_get(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 5.0,
) -> tuple[int, Optional[Dict[str, Any]], Optional[str]]:
    """Return (status, json_or_none, error_message_or_none)."""
    try:
        try:
            import requests  # type: ignore

            r = requests.get(url, headers=headers or {}, timeout=timeout)
            status = int(getattr(r, "status_code", 0) or 0)
            if status >= 400:
                # Try to capture concise error text
                try:
                    txt = r.text[:200]
                except Exception:
                    txt = "HTTP error"
                return status, None, txt
            try:
                return status, r.json(), None
            except Exception:
                return status, None, None
        except ModuleNotFoundError:
            from urllib import request, error

            req = request.Request(url)
            for k, v in (headers or {}).items():
                req.add_header(k, v)
            try:
                with request.urlopen(req, timeout=timeout) as resp:
                    status = int(getattr(resp, "status", 200) or 200)
                    body = resp.read().decode("utf-8", errors="ignore")
                    try:
                        data = _json.loads(body)
                    except Exception:
                        data = None
                    return status, data, None
            except error.HTTPError as he:  # pragma: no cover (network dependent)
                try:
                    msg = he.read().decode("utf-8", errors="ignore")[:200]
                except Exception:
                    msg = str(he)
                return int(getattr(he, "code", 0) or 0), None, msg
            except Exception as e:
                return 0, None, str(e)
    except Exception as e:  # pragma: no cover
        return 0, None, str(e)


def _result(
    ok: bool, status: Optional[int], latency_ms: Optional[int], message: str
) -> Dict[str, Any]:
    return {
        "ok": bool(ok),
        "status": int(status) if status is not None else None,
        "latency_ms": int(latency_ms) if latency_ms is not None else None,
        "message": str(message),
    }


def _probe_local() -> Dict[str, Any]:
    # No network for local; treat as success but informational
    return _result(True, None, None, "local: no network test")


def _probe_local_custom(model_path: Optional[str]) -> Dict[str, Any]:
    p = (model_path or "").strip()
    if not p:
        return _result(False, None, None, "local-custom: missing model_path")
    ok = os.path.exists(os.path.expanduser(p))
    return _result(
        ok,
        None,
        None,
        "local-custom: file found" if ok else "local-custom: file not found",
    )


def _probe_lmstudio(
    host: Optional[str], port: Optional[str | int], timeout: float
) -> Dict[str, Any]:
    h = (host or os.environ.get("LMSTUDIO_HOST") or "127.0.0.1").strip()
    p = int(port or os.environ.get("LMSTUDIO_PORT") or 1234)
    url = f"http://{h}:{p}/v1/models"
    t0 = time.monotonic()
    status, data, err = _http_get(url, timeout=timeout)
    dt = int((time.monotonic() - t0) * 1000)
    if status and status < 400:
        count = 0
        try:
            count = len((data or {}).get("data") or [])
        except Exception:
            count = 0
        return _result(True, status, dt, f"lmstudio: {count} models")
    return _result(False, status or None, dt, f"lmstudio: {err or 'unreachable'}")


def _probe_ollama(
    host: Optional[str], port: Optional[str | int], timeout: float
) -> Dict[str, Any]:
    h = (host or os.environ.get("OLLAMA_HOST") or "127.0.0.1").strip()
    p = int(port or os.environ.get("OLLAMA_PORT") or 11434)
    url = f"http://{h}:{p}/api/tags"
    t0 = time.monotonic()
    status, data, err = _http_get(url, timeout=timeout)
    dt = int((time.monotonic() - t0) * 1000)
    if status and status < 400:
        count = 0
        try:
            count = len((data or {}).get("models") or [])
        except Exception:
            count = 0
        return _result(True, status, dt, f"ollama: {count} models")
    return _result(False, status or None, dt, f"ollama: {err or 'unreachable'}")


def _probe_openai(
    base_url: Optional[str],
    api_key: Optional[str],
    org_id: Optional[str],
    timeout: float,
) -> Dict[str, Any]:
    key = (
        api_key
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("CHI_LLM_OPENAI_API_KEY")
        or ""
    ).strip()
    if not key:
        return _result(False, None, None, "openai: missing api_key")
    base = (
        base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com"
    ).rstrip("/")
    url = urljoin(base + "/", "v1/models")
    headers = {"Authorization": f"Bearer {key}"}
    if org_id or os.environ.get("OPENAI_ORG_ID"):
        headers["OpenAI-Organization"] = str(org_id or os.environ.get("OPENAI_ORG_ID"))
    t0 = time.monotonic()
    status, data, err = _http_get(url, headers=headers, timeout=timeout)
    dt = int((time.monotonic() - t0) * 1000)
    if status and status < 400:
        count = 0
        try:
            count = len((data or {}).get("data") or [])
        except Exception:
            count = 0
        return _result(True, status, dt, f"openai: {count} models")
    return _result(False, status or None, dt, f"openai: {err or 'unreachable'}")


def _probe_anthropic(
    base_url: Optional[str], api_key: Optional[str], timeout: float
) -> Dict[str, Any]:
    key = (
        api_key
        or os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("CHI_LLM_ANTHROPIC_API_KEY")
        or ""
    ).strip()
    if not key:
        return _result(False, None, None, "anthropic: missing api_key")
    base = (
        base_url or os.environ.get("ANTHROPIC_BASE_URL") or "https://api.anthropic.com"
    ).rstrip("/")
    url = urljoin(base + "/", "v1/models")
    headers = {
        "x-api-key": key,
        # Anthropic requires a version header; a common value is below.
        "anthropic-version": "2023-06-01",
    }
    t0 = time.monotonic()
    status, data, err = _http_get(url, headers=headers, timeout=timeout)
    dt = int((time.monotonic() - t0) * 1000)
    if status and status < 400:
        # API shape may vary; we only care about reachability
        return _result(True, status, dt, "anthropic: OK")
    return _result(False, status or None, dt, f"anthropic: {err or 'unreachable'}")


def _e2e_generate_with_temp_config(
    cfg: Dict[str, Any], prompt: str, timeout: float
) -> Dict[str, Any]:
    """Run `chi-llm generate` with CHI_LLM_CONFIG pointing to a temp file.

    Streams child stdout/stderr to this process' stderr for live logs,
    and returns a normalized result dict. Stdout remains reserved for the
    JSON result printed by this command.
    """
    # Write temp config file for both utils.load_config and ModelManager
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        import json as _json

        _json.dump(cfg, tf)
        tf.flush()
        temp_path = tf.name

    env = os.environ.copy()
    env["CHI_LLM_CONFIG"] = temp_path
    cmd = [sys.executable, "-m", "chi_llm.cli_main", "generate", prompt]
    t0 = time.monotonic()

    try:
        proc = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        out_lines: list[str] = []
        err_lines: list[str] = []

        def _pump(pipe, buf):
            try:
                if pipe is None:
                    return
                for b in iter(pipe.readline, b""):
                    try:
                        s = b.decode("utf-8", errors="ignore")
                    except Exception:
                        s = str(b)
                    buf.append(s)
                    try:
                        # Forward child output to stderr for live progress
                        sys.stderr.write(s)
                        sys.stderr.flush()
                    except Exception:
                        pass
            except Exception:
                pass

        th_out = threading.Thread(
            target=_pump, args=(proc.stdout, out_lines), daemon=True
        )
        th_err = threading.Thread(
            target=_pump, args=(proc.stderr, err_lines), daemon=True
        )
        th_out.start()
        th_err.start()

        # Poll for completion with timeout
        while True:
            rc = proc.poll()
            if rc is not None:
                break
            if (time.monotonic() - t0) > timeout:
                try:
                    proc.kill()
                except Exception:
                    pass
                dt = int((time.monotonic() - t0) * 1000)
                return _result(False, None, dt, "e2e timeout")
            time.sleep(0.05)

        th_out.join(timeout=0.2)
        th_err.join(timeout=0.2)
        dt = int((time.monotonic() - t0) * 1000)

        if proc.returncode == 0:
            out_txt = "".join(out_lines).strip()
            msg = (
                (out_txt[:120] + ("…" if len(out_txt) > 120 else ""))
                if out_txt
                else "ok"
            )
            return _result(True, 0, dt, f"e2e ok: {msg}")
        else:
            err_txt = "".join(err_lines).strip() or "".join(out_lines).strip()
            err = err_txt[:200]
            return _result(False, proc.returncode, dt, f"e2e fail: {err}")
    except Exception:
        dt = int((time.monotonic() - t0) * 1000)
        return _result(False, None, dt, "e2e error")


def cmd_test_provider(args):
    ptype = (getattr(args, "ptype", "") or "").strip().lower()
    timeout = float(getattr(args, "timeout", 5.0) or 5.0)
    host = getattr(args, "host", None)
    port = getattr(args, "port", None)
    base_url = getattr(args, "base_url", None)
    api_key = getattr(args, "api_key", None)
    org_id = getattr(args, "org_id", None)
    model_path = getattr(args, "model_path", None)

    e2e = bool(getattr(args, "e2e", False))
    model = getattr(args, "model", None)
    if e2e:
        # Compose temp config for end-to-end generate test
        provider_cfg: Dict[str, Any] = {"type": ptype}
        if host:
            provider_cfg["host"] = host
        if port:
            try:
                provider_cfg["port"] = int(port)  # type: ignore[arg-type]
            except Exception:
                provider_cfg["port"] = port
        if base_url:
            provider_cfg["base_url"] = base_url
        if api_key:
            provider_cfg["api_key"] = api_key
        if org_id:
            provider_cfg["org_id"] = org_id
        if model:
            provider_cfg["model"] = model
        if model_path:
            provider_cfg["model_path"] = model_path
        cfg: Dict[str, Any] = {"provider": provider_cfg}
        # For local-zeroconfig: rely on zero-config defaults; optional
        # model argument can be ignored by the core resolution.
        prompt = getattr(args, "prompt", None) or "Hello!"
        out = _e2e_generate_with_temp_config(cfg, str(prompt), timeout)
    else:
        if ptype in ("local",):
            out = _probe_local()
        elif ptype in ("local-custom",):
            out = _probe_local_custom(model_path)
        elif ptype == "lmstudio":
            out = _probe_lmstudio(host, port, timeout)
        elif ptype == "ollama":
            out = _probe_ollama(host, port, timeout)
        elif ptype == "openai":
            out = _probe_openai(base_url, api_key, org_id, timeout)
        elif ptype == "anthropic":
            out = _probe_anthropic(base_url, api_key, timeout)
        else:
            out = _result(False, None, None, f"{ptype}: unsupported provider type")

    if getattr(args, "json", False):
        _print_json(out)
    else:
        ok = "OK" if out["ok"] else "FAIL"
        status = out.get("status")
        status_txt = f" (HTTP {status})" if status is not None else ""
        latency = out.get("latency_ms")
        lat_txt = f" in {latency}ms" if latency is not None else ""
        print(f"{ok}{status_txt}{lat_txt}: {out['message']}")
