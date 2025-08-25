# 067: Providers — find-url (WSL/Windows bridge)

## Summary (What)
- Add `chi-llm providers find-url --type {lmstudio|ollama}` that probes common endpoints and returns the best host/port (JSON).
- Heuristics include WSL2 ↔ Windows host scenarios (LM Studio/Ollama running on Windows, script in WSL).

## Why
- Frequent confusion when running CLI in WSL2 while servers run on Windows. This auto-detection improves DX and reduces setup friction.

## Scope (How)
- Detect WSL via env (`WSL_DISTRO_NAME`) or `/proc/version`.
- Candidate hosts: `127.0.0.1`, `localhost`, (WSL only) first `nameserver` from `/etc/resolv.conf`, and `host.docker.internal`.
- Candidate ports: hint → env (`LMSTUDIO_PORT`/`OLLAMA_PORT`) → defaults (1234/11434).
- Probe endpoints with short timeouts: LM Studio `/v1/models`, Ollama `/api/tags`.
- Output JSON: `{provider, ok, host, port, base_url, source, tried[], message}`.

## Acceptance Criteria
- `chi-llm providers find-url --type ollama --json` returns a working endpoint when reachable on any candidate.
- On WSL, includes the Windows host IP (from `/etc/resolv.conf`) in candidates.
- Tolerates no network/servers → `ok=false` with informative `tried` list.
- Unit tests cover candidate building and JSON shape.

## Out of Scope
- Firewall/port-forwarding configuration automation.
- Auto-write to config (can be follow-up: `providers set --auto`).

