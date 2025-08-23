Title: Go TUI – Bootstrap Wizard

Problem
- Port the project bootstrap wizard to Go TUI for better onboarding.

Scope
- Step-by-step wizard: provider → model/settings → extras → summary.
- Generate `.chi_llm.(json|yaml)`, `.env.sample`, `llm-requirements.txt`.

Acceptance Criteria
- Wizard completes and writes files to chosen directory.
- Reuses existing bootstrap helpers or shared logic (no duplication where possible).
- Unit tests cover non-TUI logic; no network calls.

Notes
- Keep UI minimal; styling later.

