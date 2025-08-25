# 066: TUI shipping — prebuilt binary on PATH + docs

## Summary (What)
- Ensure `chi-llm ui` can launch a prebuilt `chi-tui` binary from PATH.
- Update docs to describe installing/using a prebuilt binary vs building from source.

## Why
- Allow pip-installed users to run the TUI without the repo or Rust toolchain.

## Scope (How)
- Add PATH detection and execution for `chi-tui` in `chi_llm/cli_modules/ui.py`.
- Keep existing source-based build fallback when inside repo and Cargo is present.
- Improve error/help message when neither is available.
- Update README UI section with shipping notes.
- Add a small unit test to cover PATH detection.

## Acceptance Criteria
- `chi-llm ui` runs the `chi-tui` binary when present on PATH (no source required).
- Fallback to source build only when in repo and Cargo available.
- Helpful instructions printed when neither option is available.
- Tests pass for the detection path.

## Out of Scope
- CI pipelines for cross-platform release artifacts (tracked separately).

