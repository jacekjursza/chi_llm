"""Find best URL (host/port) for LM Studio or Ollama with WSL-aware heuristics.

Outputs JSON suitable for UI:
{
  "provider": "ollama",
  "ok": true,
  "host": "172.22.224.1",
  "port": 11434,
  "base_url": "http://172.22.224.1:11434",
  "source": "wsl-nameserver",
  "tried": ["http://127.0.0.1:11434", ...],
  "message": "Found via WSL nameserver"
}
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import json as _json
import os
from pathlib import Path


def _print_json(obj: Dict[str, Any]) -> None:
    print(_json.dumps(obj, indent=2))


def _is_wsl(
    environ: Optional[Dict[str, str]] = None, proc_version_path: Optional[Path] = None
) -> bool:
    env = environ or os.environ
    if env.get("WSL_DISTRO_NAME"):
        return True
    try:
        p = proc_version_path or Path("/proc/version")
        if p.exists():
            s = p.read_text(encoding="utf-8", errors="ignore")
            return ("Microsoft" in s) or ("WSL" in s)
    except Exception:
        pass
    return False


def _parse_nameserver(resolv_conf_path: Optional[Path] = None) -> Optional[str]:
    try:
        p = resolv_conf_path or Path("/etc/resolv.conf")
        if not p.exists():
            return None
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[0] == "nameserver":
                return parts[1]
    except Exception:
        return None
    return None


def build_candidates(
    ptype: str,
    host_hint: Optional[str] = None,
    port_hint: Optional[str | int] = None,
    environ: Optional[Dict[str, str]] = None,
    resolv_conf_path: Optional[Path] = None,
) -> Tuple[List[str], List[int]]:
    """Return (hosts, ports) candidates respecting WSL and env hints."""
    env = environ or os.environ
    p = ptype.strip().lower()

    # Ports by precedence
    ports: List[int] = []
    if port_hint is not None and str(port_hint).strip():
        try:
            ports.append(int(port_hint))
        except Exception:
            pass
    if p == "lmstudio":
        if env.get("LMSTUDIO_PORT"):
            try:
                ports.append(int(env["LMSTUDIO_PORT"]))
            except Exception:
                pass
        if 1234 not in ports:
            ports.append(1234)
    elif p == "ollama":
        if env.get("OLLAMA_PORT"):
            try:
                ports.append(int(env["OLLAMA_PORT"]))
            except Exception:
                pass
        if 11434 not in ports:
            ports.append(11434)

    # Hosts by precedence
    hosts: List[str] = []
    if host_hint and host_hint.strip():
        hosts.append(host_hint.strip())
    # Always try loopback first
    for h in ("127.0.0.1", "localhost"):
        if h not in hosts:
            hosts.append(h)
    # WSL: add Windows host IP via resolv.conf
    if _is_wsl(env):
        ns = _parse_nameserver(resolv_conf_path)
        if ns and ns not in hosts:
            hosts.append(ns)
    # Sometimes present
    if "host.docker.internal" not in hosts:
        hosts.append("host.docker.internal")

    return hosts, ports


def _http_get(url: str, timeout: float = 1.8) -> Tuple[int, Optional[Dict[str, Any]]]:
    try:
        try:
            import requests  # type: ignore

            r = requests.get(url, timeout=timeout)
            return (
                int(getattr(r, "status_code", 0) or 0),
                r.json() if r.content else None,
            )
        except ModuleNotFoundError:
            from urllib import request

            req = request.Request(url)
            with request.urlopen(req, timeout=timeout) as resp:
                status = int(getattr(resp, "status", 200) or 200)
                try:
                    import json as _j

                    data = _j.loads(resp.read().decode("utf-8", errors="ignore"))
                except Exception:
                    data = None
                return status, data
    except Exception:
        return 0, None


def _probe(ptype: str, host: str, port: int, timeout: float) -> Tuple[bool, str]:
    p = ptype.strip().lower()
    if p == "lmstudio":
        url = f"http://{host}:{port}/v1/models"
        status, data = _http_get(url, timeout)
        if (
            status
            and status < 400
            and isinstance(data, dict)
            and (data.get("data") is not None)
        ):
            return True, "lmstudio: OK"
        return False, "lmstudio: unreachable"
    if p == "ollama":
        url = f"http://{host}:{port}/api/tags"
        status, data = _http_get(url, timeout)
        if (
            status
            and status < 400
            and isinstance(data, dict)
            and (data.get("models") is not None)
        ):
            return True, "ollama: OK"
        return False, "ollama: unreachable"
    return False, "unsupported provider"


def _base_url(ptype: str, host: str, port: int) -> str:
    if ptype.strip().lower() == "lmstudio":
        return f"http://{host}:{port}/v1"
    return f"http://{host}:{port}"


def find_url(
    ptype: str,
    host_hint: Optional[str] = None,
    port_hint: Optional[str | int] = None,
    timeout: float = 1.8,
) -> Dict[str, Any]:
    """Programmatic variant: return result dict without printing."""
    p = (ptype or "").strip().lower()
    hosts, ports = build_candidates(p, host_hint=host_hint, port_hint=port_hint)

    tried: List[str] = []
    best: Optional[Tuple[str, int, str]] = None
    source = ""

    for h in hosts:
        for prt in ports:
            bu = _base_url(p, h, prt)
            tried.append(bu)
            ok, msg = _probe(p, h, prt, timeout)
            if ok:
                best = (h, prt, msg)
                if h in ("127.0.0.1", "localhost"):
                    source = "localhost"
                elif h == "host.docker.internal":
                    source = "docker-internal"
                elif _is_wsl():
                    ns = _parse_nameserver()
                    source = "wsl-nameserver" if h == ns else "custom"
                else:
                    source = "custom"
                break
        if best:
            break

    obj: Dict[str, Any] = {"provider": p, "ok": bool(best is not None), "tried": tried}
    if best:
        host, port, msg = best
        obj.update(
            {
                "host": host,
                "port": int(port),
                "base_url": _base_url(p, host, int(port)),
                "source": source,
                "message": msg,
            }
        )
    else:
        obj.update({"message": "No reachable server found"})
    return obj


def cmd_find_url(args):
    ptype = (getattr(args, "ptype", "") or "").strip().lower()
    if ptype not in ("lmstudio", "ollama"):
        obj = {
            "provider": ptype,
            "ok": False,
            "message": "find-url only supports lmstudio and ollama",
        }
        return (
            _print_json(obj) if getattr(args, "json", False) else print(obj["message"])
        )  # noqa: E701

    timeout = 1.8
    try:
        timeout = float(getattr(args, "timeout", 1.8))
    except Exception:
        pass

    hosts, ports = build_candidates(
        ptype,
        host_hint=getattr(args, "host", None),
        port_hint=getattr(args, "port", None),
    )

    tried: List[str] = []
    best: Optional[Tuple[str, int, str]] = None
    source = ""

    # Try hinted order: host_hint, loopback, wsl-nameserver, docker internal
    for h in hosts:
        for p in ports:
            bu = _base_url(ptype, h, p)
            tried.append(bu)
            ok, msg = _probe(ptype, h, p, timeout)
            if ok:
                best = (h, p, msg)
                # Determine source label
                if h == "127.0.0.1" or h == "localhost":
                    source = "localhost"
                elif h == "host.docker.internal":
                    source = "docker-internal"
                elif _is_wsl():
                    ns = _parse_nameserver()
                    source = "wsl-nameserver" if h == ns else "custom"
                else:
                    source = "custom"
                break
        if best:
            break

    obj: Dict[str, Any] = {
        "provider": ptype,
        "ok": bool(best is not None),
        "tried": tried,
    }
    if best:
        host, port, msg = best
        obj.update(
            {
                "host": host,
                "port": int(port),
                "base_url": _base_url(ptype, host, int(port)),
                "source": source,
                "message": msg,
            }
        )
    else:
        obj.update({"message": "No reachable server found"})

    if getattr(args, "json", False):
        _print_json(obj)
    else:
        if obj["ok"]:
            src = obj.get("source", "")
            print(f"Found {ptype} at {obj['host']}:{obj['port']} ({src}).")
        else:
            print(f"Could not find a reachable {ptype} server.")
            if tried:
                print("Tried:")
                for u in tried:
                    print(f" - {u}")
