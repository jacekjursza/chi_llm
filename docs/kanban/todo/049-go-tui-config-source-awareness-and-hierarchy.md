# 049: Go TUI Config Source Awareness and Hierarchy

## Goal
Enhance Go TUI to understand and display chi-llm's configuration hierarchy (env → project → global) using `chi-llm providers current --json` API, with clear visual indicators of config source and scope.

## Scope
- Display current configuration source: Environment, Project, Global
- Show config file paths and precedence in diagnostics
- Visual indicators for config source in provider management
- Scope-aware save operations (respect where config comes from)
- Override warnings when higher-precedence config exists
- Environment variable detection and display

## Configuration Hierarchy (chi-llm)
1. **Environment Variables** (highest priority)
   - `CHI_LLM_PROVIDER_TYPE`, `CHI_LLM_PROVIDER_HOST`, etc.
2. **Project Config** (.chi_llm.json in current/parent directories)
3. **Global Config** (~/.cache/chi_llm/model_config.json)
4. **Defaults** (local provider, gemma-270m)

## Technical Implementation
- Call `chi-llm providers current --json` to get current config state:
  ```json
  {
    "type": "local",
    "config_source": "project",
    "config_path": "/path/to/.chi_llm.json",
    "model": "gemma-270m"
  }
  ```
- Parse and display configuration hierarchy information
- Environment variable detection using Go's `os.Getenv()`
- Config source indicators in UI with icons/colors

## Visual Design
- **Config Source Indicators:**
  - 🌍 Environment (green) - highest precedence  
  - 📁 Project (blue) - local to project
  - 🏠 Global (orange) - user-wide default
  - ⚙️ Default (gray) - built-in fallback

- **Provider List Enhancement:**
  - Show current active provider with source: "local 📁 (project)"
  - Dim providers that would be overridden by higher precedence config

- **Save Operation Awareness:**
  - Build screen shows which scope will be saved to
  - Warning if saving project config when environment override exists
  - Option to save to different scope if appropriate

## User Experience Features
1. **Config Status Panel** (new section in diagnostics)
   - Current effective configuration with source
   - List of all config files found with precedence
   - Environment variable status
   - Override warnings with explanations

2. **Smart Save Recommendations**  
   - When environment variables are active: "Note: Environment variables will override this config"
   - When saving to global but project config exists: "This will only apply outside this project"
   - Suggest appropriate save scope based on current source

3. **Config Hierarchy Visualization**
   - Show config chain: "ENV → PROJECT → (Global) → Defaults"  
   - Highlight active source
   - Show which values come from which source

## Acceptance Criteria
- Provider screen shows config source for current active provider
- Save operations indicate which scope they'll affect
- Environment variable overrides clearly displayed with warnings
- Config hierarchy visualization in diagnostics is accurate
- Users understand why their changes might not take effect (due to precedence)
- Build operation suggests appropriate save scope
- No loss of existing functionality - pure enhancement

## Error Handling
- Handle missing chi-llm binary gracefully
- Fallback when config detection fails
- Clear error messages for config parsing issues
- Guidance when config files are malformed

## Implementation Phases
1. **Phase 1**: Basic config source detection and display
2. **Phase 2**: Smart save scope recommendations  
3. **Phase 3**: Full hierarchy visualization
4. **Phase 4**: Environment variable management UI

## Dependencies
- `chi-llm providers current --json` API integration  
- Environment variable detection capabilities
- Enhanced diagnostics integration
- Config file path detection and parsing

## Notes
- Respect chi-llm's precedence rules exactly
- Help users understand config system without overwhelming them
- Consider power users who want full control vs beginners who want simplicity

## Non-Goals
- Environment variable editing (too complex/dangerous)
- Config file merging or advanced manipulation
- Real-time config watching/reloading