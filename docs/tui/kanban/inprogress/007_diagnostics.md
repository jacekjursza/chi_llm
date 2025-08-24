# Diagnostics (Language‑Agnostic)

Meta
- Type: Task
- Priority: P1
 - Estimate: 0.5–1.0d
 - Status: In Progress
- See also: 001_screens_keybindings_transitions_options.md (EPIC)

- Outcome: Present a concise environment/configuration snapshot and allow exporting diagnostics JSON.
- Constraints: Language/framework agnostic. Use CLI JSON outputs and local file reads only.

## Scope
- Collect data:
  - `chi-llm diagnostics --json` (if available) for environment and connectivity hints.
  - `chi-llm models current --explain --json` for config source/explanation.
  - Read nearest `.chi_llm.json` (search upward) to show effective provider/model.
- Display summary (CWD, config path/source, current model, recommended vs available RAM, basic provider hints).
- Export command (`e`): write pretty JSON to a file; show saved path.
- Optional: Trigger connection test for the active provider (reusing utilities from task 010).

## Acceptance Criteria
- Works offline; if CLI calls fail, page degrades gracefully with clear messages.
- Exported JSON contains the shown fields and is valid.

## Deliverables
- Diagnostics page integrated with skeleton routing and export.
