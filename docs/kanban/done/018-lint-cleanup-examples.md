# Ruff cleanup: examples

## Summary (What)
Fix lint issues in `examples/**` to align with repository standards.

## Why (Context)
Examples should be copy-paste friendly and pass basic linting to set a good baseline.

## Scope (How)
- Files: `examples/data_extraction.py`, `examples/config_hierarchy_demo.py` (and any others failing).
- Replace bare `except:` with `except Exception`.
- Remove unused variables (F841) or use `_` prefix.
- Keep changes minimal; ensure examples still run offline.

## Acceptance Criteria
- `ruff check examples` passes.
- `black` leaves examples formatted.

## Non-Goals
- Adding new examples or changing logic.

## Estimate
- Complexity: S (1–2 hours).

## Test Plan
- `ruff check examples` and manual quick run of examples if feasible.

