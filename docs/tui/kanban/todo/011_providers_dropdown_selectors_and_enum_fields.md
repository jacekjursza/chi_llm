# 011: Providers – Dropdown selectors and enum fields

## Summary (What)
- Add a proper dropdown selector widget for provider “Type” (already partially implemented) and extend it to any schema field that declares an enum of allowed values.

## Why
- Consistent, discoverable UX for categorical values; reduces input errors and speeds up configuration.

## Scope (How)
- Detect enum-like fields in `providers schema --json` (e.g., `options`, `enum`, or `choices` property when present in schema).
- Render inline form fields with a dropdown affordance; Enter opens overlay; Up/Down navigates; Enter confirms; Esc cancels.
- Reuse current dropdown overlay machinery; generalize it to accept source list + title.
- Keep keyboard map consistent with Type selector; mouse support optional/non-goal.

## Acceptance Criteria
- Pressing Enter on a field with enum/options opens a dropdown and updates the field upon selection.
- Dropdown is navigable via Up/Down/Enter/Esc and respects current theme.
- No regressions to existing Type dropdown and Save/Cancel flow.

## Notes
- Schema may not yet expose enums — add tolerant detection (future-proof key names) and fallback to text input when missing.
- Keep fields ≤600 lines per module; no re-aggregation into a single file.

