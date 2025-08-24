Title: Restore normal testing policy

Context:
- The temporary skip-tests policy is no longer needed; we identified and
  removed the blocking Textual UI path. Tests can run as part of the normal
  workflow again.

Scope:
- Update AGENTS.md to restore: run full test suite before moving to Done.
- Remove the temporary testing policy section.

Acceptance Criteria:
- AGENTS.md reflects normal testing flow; Quick Start no longer skips tests.

