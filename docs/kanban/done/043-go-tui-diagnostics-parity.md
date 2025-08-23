Title: Go TUI – Diagnostics view parity

Problem
- Parity for Diagnostics view and export report to JSON.

Scope
- Add Diagnostics screen showing provider status, config source, environment hints.
- Export diagnostics to `chi_llm_diagnostics.json` from the UI.

Acceptance Criteria
- Diagnostics screen renders key info.
- Export command writes file and shows confirmation.
- No external network dependency.

Notes
- Reuse Python CLI diagnostics gathering via subprocess or reimplement a small subset in Go.

