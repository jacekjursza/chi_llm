Title: Testing DX — Makefile shortcuts and docs

Context:
- Running/diagnosing tests was cumbersome with coverage defaults and potential
  interactive hangs. Provide convenient Make targets and documentation.

Scope:
- Add a `Makefile` with test targets (fast, diagnose, timeout, UI CLI, etc.).
- Update TESTING.md with a "Makefile Shortcuts" section and examples.

Acceptance Criteria:
- `make test-fast` runs tests without coverage thresholds.
- `make test-diagnose` shows durations and verbose logs.
- `make test-ui-cli` and `make test-cli` split UI vs non-UI CLI tests.
- TESTING.md documents the new targets and usage patterns.

