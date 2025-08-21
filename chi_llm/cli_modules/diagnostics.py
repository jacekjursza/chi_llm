"""
Diagnostics command producing environment checks for UI/automation.

Outputs JSON (or human-readable) with checks for:
- Python version
- Node/npm presence
- Cache dir existence and writability
- Current model vs available RAM
- Basic network reachability for Hugging Face
"""

from argparse import _SubParsersAction
from shutil import which
from pathlib import Path
import json
import os
import platform
import sys
import time

try:
    from ..models import ModelManager, MODELS, MODEL_DIR as MODELS_DIR
except Exception:  # pragma: no cover
    ModelManager = None  # type: ignore
    MODELS = {}  # type: ignore
    MODELS_DIR = Path.home() / ".cache" / "chi_llm"  # type: ignore


def _check_python() -> dict:
    return {
        "version": platform.python_version(),
        "implementation": platform.python_implementation(),
        "ok": True,
    }


def _check_node() -> dict:
    node = which("node")
    npm = which("npm")
    return {"installed": bool(node), "npm": bool(npm), "ok": bool(node and npm)}


def _check_cache() -> dict:
    p = MODELS_DIR
    exists = p.exists()
    writable = os.access(p if exists else p.parent, os.W_OK)
    return {"path": str(p), "exists": exists, "writable": writable, "ok": exists and writable}


def _check_model() -> dict:
    if ModelManager is None:
        return {"ok": False, "error": "model-manager-unavailable"}
    mgr = ModelManager()
    cur = mgr.get_current_model()
    stats = mgr.get_model_stats()
    avail = float(stats.get("available_ram_gb", 0.0))
    fits = avail >= float(cur.recommended_ram_gb)
    return {
        "current": cur.id,
        "name": cur.name,
        "recommended_ram_gb": cur.recommended_ram_gb,
        "available_ram_gb": avail,
        "fits": fits,
        "ok": True,
    }


def _check_network(timeout: float = 2.0) -> dict:
    # Try a quick HEAD/GET to huggingface.co if requests is available
    start = time.time()
    try:
        import requests  # type: ignore

        try:
            r = requests.get("https://huggingface.co/robots.txt", timeout=timeout)
            ok = r.status_code < 500
            return {
                "hf": True,
                "ok": bool(ok),
                "status": r.status_code,
                "latency_ms": int((time.time() - start) * 1000),
            }
        except Exception as e:  # pragma: no cover (network dependent)
            return {"hf": True, "ok": False, "error": str(e)}
    except Exception:
        # requests not available; mark unknown but not failing
        return {"hf": False, "ok": True, "note": "requests not installed"}


def _gather() -> dict:
    return {
        "python": _check_python(),
        "node": _check_node(),
        "cache": _check_cache(),
        "model": _check_model(),
        "network": _check_network(),
    }


def cmd_diagnostics(args):
    data = _gather()
    if getattr(args, "json", False):
        print(json.dumps(data, indent=2))
        return
    # Human-readable summary
    print("Environment diagnostics:\n")
    print(f"Python: {data['python']['version']} ({data['python']['implementation']})")
    print(f"Node: {'ok' if data['node']['ok'] else 'missing'}")
    cache = data["cache"]
    print(f"Cache: {cache['path']} | exists={cache['exists']} writable={cache['writable']}")
    model = data["model"]
    if model.get("ok"):
        print(
            f"Model: {model['current']} | RAM {model['available_ram_gb']:.1f}GB vs "
            f"{model['recommended_ram_gb']}GB -> {'fits' if model['fits'] else 'tight'}"
        )
    net = data["network"]
    print(f"Network (HF): {'ok' if net.get('ok') else 'fail'}")


def register(subparsers: _SubParsersAction):
    sub = subparsers.add_parser("diagnostics", help="Show environment diagnostics")
    sub.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    sub.set_defaults(func=cmd_diagnostics)

