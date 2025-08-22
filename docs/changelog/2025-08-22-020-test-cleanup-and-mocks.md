# 020 – Test cleanup: constants sync and network mocks

## Summary
Hardened tests to run fully offline and faster by centralizing mocks for model download and Llama, without changing runtime behavior.

## Changes
- tests/conftest.py: added autouse fixture to
  - monkeypatch `hf_hub_download` to return a temp model path
  - replace `Llama` with a lightweight fake callable
  - disable HF telemetry via env
- Verified constants remain aligned with current code (legacy Q4_K_M constant kept for BC; registry uses Q8_0 per product choices).

## Outcome
- Tests are deterministic and network-free; 130/130 green locally, coverage ~86%.

Card-Id: 020
Refs: docs/kanban/done/020-test-cleanup-sync-and-mocks.md
