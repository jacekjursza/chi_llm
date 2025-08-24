# 046: Go TUI Provider Model Discovery Integration

## Goal  
Integrate external provider model discovery (LMStudio/Ollama) into Go TUI using chi-llm's discovery.py functionality for real-time available model detection.

## Scope
- Auto-discover available models from LMStudio (localhost:1234/v1/models) 
- Auto-discover available models from Ollama (localhost:11434/api/tags)
- Show provider-specific models in model browser when editing server providers
- Display model sizes from server (parameter size like "7B", file sizes)
- Connection testing with model list validation
- Cache discovery results with refresh capability

## Technical Implementation
- Create Go equivalent of Python's `discovery.py` functions:
  ```go
  func DiscoverLMStudioModels(host, port string) ([]ExternalModel, error)
  func DiscoverOllamaModels(host, port string) ([]ExternalModel, error)  
  ```
- HTTP clients for `/v1/models` and `/api/tags` endpoints
- Integration with provider editing workflow
- Model browser context switch: "Local Models" vs "Server Models"
- Async discovery with loading states and error handling

## User Flow
1. User edits LMStudio/Ollama provider configuration
2. Press 'm' to browse models → shows "Discovering models..." 
3. TUI calls appropriate discovery endpoint
4. Shows available models from that server with sizes
5. User selects model → updates provider config
6. Connection test validates model availability

## Acceptance Criteria
- Model browser shows server-specific models when editing LMStudio/Ollama providers
- HTTP discovery working for both LMStudio and Ollama endpoints
- Model sizes displayed correctly (7B, 3B format or MB)
- Loading states and error handling for connection failures
- Cache results for 5 minutes to avoid repeated network calls
- Refresh capability (press 'R' to re-discover)
- Clear distinction between local vs server models in UI

## Error Handling
- Connection timeout (5s default)
- Server not running (connection refused)
- Invalid JSON response  
- Empty model list
- Malformed model data

## Dependencies
- HTTP client functionality in Go
- JSON parsing for different API formats (LMStudio vs Ollama)
- Integration with existing provider editing flow

## Notes
- Keep discovery async to avoid UI blocking
- Consider background refresh for active connections
- Follow security best practices for external HTTP calls

## Non-Goals
- Model downloading from external providers
- Provider authentication (API keys handled separately)
- Advanced model metadata beyond size/name