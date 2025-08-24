Title: Cleanup: ignore local config and untrack project file

Summary
- Add `.chi_llm.json/.yaml/.yml` to `.gitignore` to avoid committing developer-specific config.
- Remove tracked `.chi_llm.json` from Git index (keep file locally).
- Reinforce ignoring of local artifacts (pytest outputs, logs, tmp commit file).

Why
- Prevent accidental commits of local config or transient artifacts.

Acceptance
- `.chi_llm.json` is untracked and ignored on subsequent changes.
- `.gitignore` includes the patterns listed above.

