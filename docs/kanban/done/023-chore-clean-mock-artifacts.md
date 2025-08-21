# Cleanup MagicMock artifact directories in repo root (Done)

## Summary (What)
Removed stray directories named like `<MagicMock name='MODEL_DIR' id='...'>` created during tests/mocks.

## Outcome
- Deleted 5 artifact directories from repo root.
- No code changes.

## Notes
Consider reviewing tests that patch `MODEL_DIR` to avoid accidental path creation in future runs.

