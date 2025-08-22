# Pre-commit setup and linting config

## Summary (What)
Add pre-commit hooks (black, ruff, file-length, commit-msg) and supporting config.

## Why (Context)
Automate code style, lint, file length policy, and commit message discipline to keep quality high.

## Scope (How)
- .pre-commit-config.yaml with local hooks (system black/ruff, custom scripts).
- Scripts: `scripts/check_file_lengths.py`, `scripts/validate_commit_msg.py`.
- `pyproject.toml`: sections for black/ruff; ruff ignores tests.
- `requirements-dev.txt`: add `ruff`, `pre-commit`.
- `.lengthcheckignore`: ignore `chi_llm/cli.py` until refactor.
- `AGENTS.md`: setup instructions and conventions.

## Acceptance Criteria
- `pre-commit run --all-files` passes.
- Hooks format/lint staged Python files; commit-msg validated.

## Estimate
- Complexity: S (2–3h)

## Notes
- Keep rules minimal; iterate as code evolves.

