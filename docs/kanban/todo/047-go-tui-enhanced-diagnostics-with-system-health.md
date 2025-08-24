# 047: Go TUI Enhanced Diagnostics with System Health

## Goal
Enhance the diagnostics screen with full system health check using `chi-llm diagnostics --json` API, showing Python/Node environment, cache status, model fitness, and network connectivity.

## Scope
- Integrate full diagnostics from `chi-llm diagnostics --json` command
- Display Python/Node environment validation with versions
- Show cache directory status (path, writable, size)
- Current model fitness analysis (RAM requirements vs available)
- Network connectivity check (HuggingFace, latency)
- Visual health indicators with actionable recommendations

## Technical Implementation
- Update diagnostics collection to call `chi-llm diagnostics --json`
- Parse comprehensive diagnostics response:
  ```go
  type SystemDiagnostics struct {
      Python  EnvironmentInfo `json:"python"`
      Node    EnvironmentInfo `json:"node"` 
      Cache   CacheInfo       `json:"cache"`
      Model   ModelFitness    `json:"model"`
      Network NetworkStatus   `json:"network"`
  }
  
  type EnvironmentInfo struct {
      Version    string `json:"version"`
      Installed  bool   `json:"installed"`
      OK         bool   `json:"ok"`
  }
  
  type CacheInfo struct {
      Path     string `json:"path"`
      Exists   bool   `json:"exists"`
      Writable bool   `json:"writable"`
      OK       bool   `json:"ok"`
  }
  
  type ModelFitness struct {
      Current           string  `json:"current"`
      RecommendedRAMGB  float64 `json:"recommended_ram_gb"`
      AvailableRAMGB    float64 `json:"available_ram_gb"`
      Fits              bool    `json:"fits"`
      OK                bool    `json:"ok"`
  }
  ```

## Visual Design
- Color-coded health indicators: ✅ Green (OK), ⚠️ Yellow (Warning), ❌ Red (Error)
- Expandable sections for detailed information
- Actionable recommendations for issues found
- System resource usage visualization (RAM, disk space)

## Diagnostic Categories
1. **Environment Health**
   - Python version and implementation
   - Node.js and NPM availability
   - Required dependencies status

2. **Storage Health**  
   - Cache directory accessibility
   - Available disk space
   - Download directory permissions

3. **Model Health**
   - Current model loaded status
   - RAM fitness analysis  
   - Model file integrity (if applicable)

4. **Network Health**
   - Internet connectivity
   - HuggingFace API accessibility
   - Connection latency measurements

## Acceptance Criteria
- Diagnostics screen shows comprehensive system health overview
- Each diagnostic category has clear OK/Warning/Error status
- Detailed information expandable for each section  
- Actionable recommendations for any issues found
- Refresh capability (press 'R' to re-run diagnostics)
- Export diagnostics to JSON file (press 'e')
- Performance: diagnostics complete within 10 seconds

## Error Handling & Recovery
- Graceful handling of missing chi-llm binary
- Fallback to basic diagnostics if JSON parsing fails
- Clear error messages for each diagnostic failure
- Suggestion of fix actions where possible

## Dependencies
- `chi-llm diagnostics --json` command availability
- JSON parsing for complex nested structure
- System resource detection capabilities

## Notes
- Cache diagnostics results for 30 seconds to avoid repeated calls
- Consider background health monitoring for critical issues
- Keep UI responsive during diagnostic collection

## Non-Goals
- Automatic issue fixing (just detection and recommendations)
- Real-time system monitoring (just snapshot diagnostics)
- Performance benchmarking beyond basic fitness