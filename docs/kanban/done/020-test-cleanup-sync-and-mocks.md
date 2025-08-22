# Test cleanup: constants sync and network mocks

## Summary (What)
Align tests with current model constants and prevent real network/model downloads by adding robust mocks/fixtures.

## Why (Context)
- Some tests assume older defaults (e.g., `MODEL_FILE=...Q4_K_M.gguf`) while code uses `...Q8_0.gguf`.
- At least one test (`test_model_caching`) tries to download from Hugging Face (404), causing flaky/slow CI.
- Env-based config expectations (e.g., temperature=0.9) are not reliably set in tests.

## Scope (How)
- Constants sync:
  - Decide source of truth: keep current code constants (recommended) and update tests to match `MODEL_REPO` and `MODEL_FILE`.
  - Alternatively, align code to tests if product requires Q4_K_M by default (confirm with PO).
- Network mocking:
  - Add a `conftest.py` fixture to monkeypatch `huggingface_hub.hf_hub_download` returning a temp file path.
  - Ensure all tests that indirectly trigger downloads use the fixture (can be session-scoped auto-use).
- Env/config tests:
  - Standardize env setup via fixtures to assert temperature/max_tokens coming from env or JSON snippets.
  - Avoid cross-test leakage: clear env in fixture teardown.
- Coverage (optional, if still failing):
  - Option A: Exclude `chi_llm/cli.py`, `chi_llm/setup.py`, `chi_llm/rag.py` from coverage target.
  - Option B: Add minimal smoke tests with mocks to import/execute basic code paths to raise coverage.

## Acceptance Criteria
- Tests run fully offline (no network requests or large downloads).
- All failing tests pass (constants assertions, env expectations, model caching/download tests).
- Test suite coverage meets threshold or updated config reflects intended target.

## Dependencies
- None.

## Risks
- Masking real regressions if mocks not scoped correctly; keep mocks minimal and targeted.

## Estimate
- Complexity: M (0.5–1 day).

## Test Plan
- Run `pytest -q` locally with and without internet to verify isolation.
- Verify no network calls using monkeypatch/spies or by setting `HF_HUB_DISABLE_TELEMETRY=1` and offline.

