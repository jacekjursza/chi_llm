# 044 - Go TUI Multi-Provider Configuration

**Status:** TODO  
**Priority:** High  
**Estimated effort:** 2-3 hours  

## Overview
Redesign the Configure Providers screen (page 2) to support multiple configured providers with tags instead of single provider selection per project.

## Current State
- Screen shows all available provider types
- User selects one provider for the project
- Configuration is saved to `.chi_llm.json`

## Target State
- Screen shows only **configured** providers (initially empty)
- Dropdown to add new provider types
- Each provider has type-specific fields + shared "tag" field
- Support for multiple providers with tags for categorization
- Save to `chi.tmp.json` format

## Acceptance Criteria

### UI Changes
- [ ] Rename page title: "Configure" → "Configure Providers"
- [ ] Replace provider type list with configured providers list
- [ ] Add "Add Provider" dropdown with available types (local, ollama, lmstudio, openai, etc.)
- [ ] New providers show with orange title + asterisk (*) until saved

### Provider Configuration
- [ ] Keep existing type-specific fields (host, port, api_key, base_url, org_id, model)
- [ ] Add shared **Tag** field as dropdown with predefined values
- [ ] Support multiple tags per provider
- [ ] Support multiple providers with same tag (no validation)

### Tag System
- [ ] Get available tags from Python chi_llm (create CLI command if needed)
- [ ] Implement tag dropdown UI component
- [ ] Allow multiple tag selection per provider

### Data Management
- [ ] Change from single provider to array of configured providers
- [ ] Save configuration to `chi.tmp.json` instead of `.chi_llm.json`
- [ ] Support ENV vars format `$VARIABLE_NAME` (display only, parsing for chi_llm later)
- [ ] Add "Save" button to persist provider configuration

### State Management
- [ ] Track configured vs new providers
- [ ] Visual indicators for unsaved changes (orange + asterisk)
- [ ] Remove provider functionality
- [ ] Edit existing provider functionality

## Technical Implementation

### New Data Structures
```go
type ConfiguredProvider struct {
    ID     string        `json:"id"`     // unique identifier  
    Type   string        `json:"type"`   // provider type
    Tags   []string      `json:"tags"`   // assigned tags
    Config ProviderConfig `json:"config"` // type-specific config
}

type MultiProviderConfig struct {
    Providers []ConfiguredProvider `json:"providers"`
}
```

### File Format
- Target file: `chi.tmp.json` 
- Support ENV var references: `$API_KEY`
- Multiple provider entries with unique IDs

## Dependencies
- [ ] Check if Python chi_llm has tag listing command
- [ ] Create tag listing CLI command if missing
- [ ] Update Go TUI to call Python command for tags

## Testing
- [ ] Add new provider of each type
- [ ] Assign multiple tags to provider
- [ ] Save and reload configuration
- [ ] Test ENV var format support
- [ ] Visual state indicators work correctly

## Notes
- This changes the fundamental model from "one provider per project" to "multiple tagged providers"
- Backward compatibility with existing `.chi_llm.json` may need consideration
- ENV var parsing will be handled by Python chi_llm, TUI only displays format

## Definition of Done
- User can manage multiple providers with tags
- Configuration persists to `chi.tmp.json`
- UI clearly shows configured vs new providers
- Tag system fully functional
- All existing provider types supported