# 045: Go TUI Enhanced Model Browser with Chi-LLM API Integration

Status: In Progress

## Goal
Enhance the Go TUI model browser to use rich data from `chi-llm models list --json` API, showing download status, resource requirements, tags, and intelligent filtering.

## Progress
- [x] Go TUI calls `chi-llm models list --json` for local provider (single source of truth).
- [x] Show download status/current model indicators in UI.
- [x] Display detailed metadata (RAM, context window, tags).
- [x] Tag-based filtering (cycle with `f`).
- [x] Fitness indicators (fits RAM) with inline markers.
- [ ] Filter mode: Fits RAM only (pending)

## Technical Implementation
- Updated discovery to shell out to the Python CLI for local models with a safe fallback when CLI unavailable.
- Next: extend `modelItem` and UI to render metadata and filters.

## Acceptance Criteria
- Model browser shows download status with clear visual indicators (done)
- File size and RAM requirements displayed for each model (done)
- Tag filtering works with available tags from chi-llm (done)
- Models show fitness indicator (green/yellow/red) (done)
- Current model highlighted (done)
- Filter modes: All, Downloaded Only (done), Fits RAM (pending), By Tag (done)
- Press 'i' on model shows detailed info (done)
