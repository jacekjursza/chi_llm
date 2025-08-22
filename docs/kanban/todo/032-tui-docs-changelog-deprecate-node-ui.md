# Docs & Changelog: Textual TUI default; Node UI deprecation

## Summary (What)
Update documentation to make the Textual TUI the default `chi-llm config` UI, document installation, and deprecate the Node UI path with `--legacy-node`.

## Why (Context)
- Communicate the new default experience and reduce confusion about Node requirements.

## Scope (How)
- README: replace UI section with Textual-first instructions; add `pip install "chi-llm[ui]"` snippet.
- docs/CLI.md: update `config` command behavior, flags, and troubleshooting.
- Changelog: add entry with migration notes and rationale.
- Note deprecation timeline for Node UI; keep for one release as fallback.

## Acceptance Criteria
- Updated docs rendered clearly; commands are accurate.
- Node UI path labeled as legacy; `--legacy-node` documented.
- Changelog entry added under `docs/changelog/` with concise context.
- Pre-task API check: confirm final CLI flag names and Textual version guidance before editing docs.

## Out of Scope
- Removing Node UI implementation (future cleanup after deprecation window).

## Dependencies
- Completion of MVP (027) to confirm CLI behavior.

## Risks
- Users depending on Node UI; provide clear fallback and instructions.

## Test Plan
- CLI docs examples validated manually; link check for install hints.

