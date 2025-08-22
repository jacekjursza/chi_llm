# Multi-provider routing with tags and fallbacks

## Summary (What)
Allow configuring multiple providers with tags (e.g., `coding`, `reasoning`, `cheap`) and define fallback order when the primary fails.

## Why (Context)
- docs_tmp U-7: simultaneous providers + tag system + flexible fallbacks.

## Scope (How)
- Extend config to accept provider profiles array with `name`, `type`, `tags`, `priority`, `conditions`.
- Add lightweight router that picks provider based on requested tag(s) and availability.
- Fallback to next provider on error/timeouts.

## Acceptance Criteria
- `MicroLLM(..., tags=["coding"])` routes to matching provider; fallback works.
- Configurable timeout and error classes trigger fallback.
- Docs include examples.

## Dependencies
- 002 Provider schema; 003/004/010+ concrete providers.

## Risks
- Complexity creep; start with simple tag matching and linear priority.

## Estimate
- Complexity: L (1–2 days)

## Test Plan
- Unit tests for routing selection and fallback behavior with stub providers.

