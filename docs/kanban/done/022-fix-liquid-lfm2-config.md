Title: Fix Liquid LFM2 1.2B model repo/filename (Done)

Outcome:
- Updated model registry to use `LiquidAI/LFM2-1.2B-GGUF` and `LFM2-1.2B-Q8_0.gguf`.
- Avoids 404 on download; no changes to tests required.

Scope:
- Update `MODELS['liquid-lfm2-1.2b']` to use repo `LiquidAI/LFM2-1.2B-GGUF`.
- Update filename to `LFM2-1.2B-Q8_0.gguf` to avoid 404.

Acceptance Criteria:
- The model manager returns correct (repo, filename) for `liquid-lfm2-1.2b`.
- No failing tests; no network calls in CI.
