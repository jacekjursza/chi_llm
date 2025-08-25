#!/usr/bin/env python3
"""
Minimal E2E smoke for TUI core flow using CLI (non-interactive):

1) providers test --type local-zeroconfig --model <MODEL_ID> --e2e --timeout <TIMEOUT>
2) providers set --type local --model <MODEL_ID> --local --json (write .chi_llm.json)
3) models current --explain --json (verify effective_model == MODEL_ID)

Env vars:
- MODEL_ID: default 'gemma-270m'
- TIMEOUT_SEC: default '90'

Exits 0 on success, non-zero on failure.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys


def run_cli(args: list[str]) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-m", "chi_llm.cli_main", *args]
    return subprocess.run(cmd, capture_output=True, text=True)


def main() -> int:
    model_id = os.environ.get("MODEL_ID", "gemma-270m")
    timeout = os.environ.get("TIMEOUT_SEC", "90")

    print(
        f"[1/3] E2E providers: local-zeroconfig, model={model_id}, "
        f"timeout={timeout}s..."
    )
    p = run_cli(
        [
            "providers",
            "test",
            "--type",
            "local-zeroconfig",
            "--model",
            model_id,
            "--e2e",
            "--timeout",
            str(timeout),
            "--json",
        ]
    )
    if p.returncode != 0:
        sys.stderr.write(p.stderr or p.stdout or "\n")
        print("❌ providers test failed")
        return 1
    try:
        v = json.loads(p.stdout)
    except Exception:
        sys.stderr.write(p.stdout)
        print("❌ providers test: invalid JSON")
        return 1
    if not v.get("ok"):
        print(f"❌ providers test not ok: {v.get('message')}")
        return 1
    print(f"✅ providers test: {v.get('message')}")

    print(f"[2/3] Write local project provider (.chi_llm.json) -> local:{model_id}...")
    p2 = run_cli(
        [
            "providers",
            "set",
            "--type",
            "local",
            "--model",
            model_id,
            "--local",
            "--json",
        ]
    )
    if p2.returncode != 0:
        sys.stderr.write(p2.stderr or p2.stdout or "\n")
        print("❌ providers set failed")
        return 1
    print("✅ providers set (local project config)")

    print("[3/3] Verify models current --explain...")
    p3 = run_cli(["models", "current", "--explain", "--json"])
    if p3.returncode != 0:
        sys.stderr.write(p3.stderr or p3.stdout or "\n")
        print("❌ models current failed")
        return 1
    try:
        cur = json.loads(p3.stdout)
    except Exception:
        sys.stderr.write(p3.stdout)
        print("❌ models current: invalid JSON")
        return 1
    eff = cur.get("effective_model")
    if eff != model_id:
        print(f"❌ effective_model mismatch: got {eff}, expected {model_id}")
        return 2
    print(f"✅ effective_model = {eff}")
    print("🎉 Smoke TUI flow OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
