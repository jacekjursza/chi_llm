Title: Go TUI – Models management parity

Problem
- Models view parity: show available/local models, filter downloaded-only, remove model, progress/ETA.

Scope
- Add a Models screen with listing and a downloaded-only toggle.
- Remove model action (deletes file, updates state); open models directory action.
- Show download progress with percentage/ETA when known.

Acceptance Criteria
- Downloaded-only filter persists within session; unit test covers store logic.
- Remove updates UI state and file system (mocked in tests).
- Progress shows percentage or pulse when unknown.

Notes
- Use goroutines for IO; keep UI responsive.
- Reuse Python models registry data where reasonable (via JSON bridge or duplication kept minimal).

