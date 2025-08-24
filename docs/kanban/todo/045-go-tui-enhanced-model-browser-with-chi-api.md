# 045: Go TUI Enhanced Model Browser with Chi-LLM API Integration

## Goal
Enhance the Go TUI model browser to use rich data from `chi-llm models list --json` API, showing download status, resource requirements, tags, and intelligent filtering.

## Scope
- Integrate full model data from `chi-llm models list --json` command
- Show download status with visual indicators (✅ downloaded, 📥 available)  
- Display model metadata: file size, RAM requirements, context window
- Add tag-based filtering and search (coding, tiny, fast, reasoning, etc.)
- Smart recommendations based on available system RAM
- Model fitness indicators (fits in RAM, recommended, etc.)

## Technical Implementation
- Update `fetchModelsCmd()` to call `chi-llm models list --json`
- Parse JSON response with full ModelInfo struct:
  ```go
  type ModelInfo struct {
      ID               string   `json:"id"`
      Name             string   `json:"name"`
      Size             string   `json:"size"`
      FileSizeMB       int      `json:"file_size_mb"`
      ContextWindow    int      `json:"context_window"`
      RecommendedRAMGB float64  `json:"recommended_ram_gb"`
      Tags             []string `json:"tags"`
      Downloaded       bool     `json:"downloaded"`
      Current          bool     `json:"current"`
  }
  ```
- Add filtering UI: press 'f' to filter by tags, 'r' to show only downloaded
- Visual enhancements: color coding by size category, RAM fitness indicators

## Acceptance Criteria
- Model browser shows download status with clear visual indicators
- File size and RAM requirements displayed for each model
- Tag filtering works with 34+ available tags from chi-llm
- Models show fitness indicator (green=fits, yellow=tight, red=too big)
- Current model highlighted with special indicator
- Filter modes: All, Downloaded Only, Fits RAM, By Tag
- Press 'i' on model shows detailed info popup

## Dependencies
- Requires `chi-llm` binary available in PATH
- JSON parsing for model metadata
- Enhanced UI layout for additional information

## Notes  
- Keep UX responsive - cache results to avoid repeated CLI calls
- Consider lazy loading for large model lists
- Maintain backward compatibility with existing model browser

## Non-Goals
- Model downloading/management (separate card)
- Provider-specific model discovery (separate card) 
- Model performance benchmarking