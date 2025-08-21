# Ruff/Black cleanup: core modules

## Summary (What)
Resolve current Ruff violations in core library modules without changing behavior.

## Why (Context)
Pre-commit is configured with `ruff` and `black`. Remaining violations block clean commits and CI discipline. Focus on library code used by users.

## Scope (How)
- Files: `chi_llm/utils.py`, `chi_llm/setup.py`, `chi_llm/analyzer.py`, `chi_llm/__init__.py`.
- Fixes:
  - Replace bare `except:` with `except Exception as e:` and handle/log appropriately.
  - Wrap long lines (E501) and split prints/strings.
  - Remove unused variables (F841) or use `_` prefix.
  - Move module-level imports to top (E402) or add minimal refactor to avoid circularity.
- Do not alter public behavior or signatures.

## Acceptance Criteria
- `ruff check chi_llm/utils.py chi_llm/setup.py chi_llm/analyzer.py chi_llm/__init__.py` passes.
- `black` passes on the same files (line length 88).
- `pre-commit run --all-files` shows no new errors for these paths.
- All tests pass: `pytest -q`.

## Non-Goals
- No feature changes. Tests and `examples/**` handled separately.

## Estimate
- Complexity: S–M (3–5 hours).

## Test Plan
- Run `pre-commit run --all-files` and `pytest -q` locally.

