Title: Temporary Testing Policy — disable automatic runs

Context:
- Tests sometimes hang due to interactive flows (UI/TUI). To avoid CI/local
  friction, we temporarily disable automatic test execution unless explicitly
  requested by the user.

Scope:
- Update AGENTS.md to state that tests are not to be run by default, including
  Quick Start/"ZACZYNAMY" and the standard Execution Protocol.

Acceptance Criteria:
- AGENTS.md contains a clearly labeled temporary policy.
- Execution Protocol no longer mandates running the full suite by default.
- Code Quality & Testing section clarifies "tests on request only" for now.

Notes:
- Revert this once the timeout root cause is fixed.

