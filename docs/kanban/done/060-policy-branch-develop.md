# Policy: Use `devel` as working branch

## Summary (What)
Update agents policy to reflect that day-to-day work happens on `devel` and commits/pushes go there by default.

## Why (Context)
We want to decouple integration/release (`master`) from ongoing development and reduce risk on mainline.

## Scope (How)
- Update `AGENTS.md`:
  - Environment & Permissions: default push target is `devel`.
  - Execution Protocol: push to `devel` by default.
  - Branching & Pushing Policy: working branch `devel`, `master` for releases.

## Acceptance Criteria
- `AGENTS.md` clearly states `devel` as the working branch. (Done)
- Notes on using PRs/coordination when targeting `master`. (Done)

Status: Done

## Risks
- Contributors may still target `master`; mitigate with docs clarity.

## Estimate
- S (10–15 min)
