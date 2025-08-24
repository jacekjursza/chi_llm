# 048: Go TUI Smart Tags and Model Recommendations

## Goal
Implement intelligent tag-based model recommendations and filtering using the 34+ available tags from `chi-llm providers tags --json`, with use-case driven model suggestions.

## Scope  
- Integrate full tag system from `chi-llm providers tags --json` 
- Smart model recommendations based on use case and system specs
- Tag-based filtering and search in model browser
- Use case wizards: "I want to..." → recommended models
- Tag descriptions and explanations for users
- Performance/resource-aware recommendations

## Available Tags (34+)
From chi-llm API: tiny, small, medium, large, fast, balanced, powerful, coding, reasoning, thinking-mode, cpu-friendly, recommended, default, microsoft, google, multilingual, math, professional, complex, etc.

## Technical Implementation
- Fetch and cache tags from `chi-llm providers tags --json`
- Tag-to-description mapping for user education
- Smart recommendation engine:
  ```go
  type RecommendationEngine struct {
      availableRAM    float64
      useCase         UseCase  
      performance     PerformancePreference
      systemSpecs     SystemSpecs
  }
  
  type UseCase int
  const (
      GeneralChat UseCase = iota
      Coding
      Reasoning  
      Writing
      Math
      Multilingual
  )
  
  func (r *RecommendationEngine) RecommendModels() []ModelRecommendation
  ```

## User Experience Features
1. **Use Case Wizard** (new screen accessible via 'w')
   - "What do you want to use the model for?"
   - Options: General Chat, Code Help, Math/Reasoning, Writing, Multilingual
   - System asks about performance preference (Speed vs Quality)
   - Shows 3-5 recommended models with explanations

2. **Tag Filter Mode** in Model Browser  
   - Press 'f' → show tag filter interface
   - Multi-select tags with checkboxes
   - Real-time filtering of model list
   - Show tag descriptions on hover/selection

3. **Smart Recommendations Bar**
   - Top of model browser: "💡 Recommended: qwen3-1.7b (fast, coding), phi3-mini (quality)"
   - Based on current provider, system RAM, and usage patterns

## Recommendation Logic
- **System-aware**: Filter by RAM requirements vs available
- **Use-case matching**: coding → models with "coding" tag
- **Performance balance**: fast vs powerful based on user preference  
- **Provider context**: local models vs API models based on provider type
- **Progressive recommendations**: tiny → small → medium as user gains experience

## Acceptance Criteria
- Tag system loads all 34+ tags from chi-llm API
- Use case wizard guides users to appropriate models
- Model browser has functional tag filtering with multi-select
- Recommendations adapt to system specs (RAM, performance preference)
- Tag descriptions help users understand model characteristics  
- Recommendation explanations: "Recommended because: fits RAM, good for coding"
- Filter persistence: remember user's preferred tags between sessions

## UI/UX Design
- Tag pills with color coding by category (performance=blue, use-case=green, size=orange)
- Recommendation confidence indicators (★★★ high confidence)
- Explanatory text for why models are recommended
- Quick access to popular combinations: "Best for coding", "Fastest", "Most capable"

## Dependencies
- `chi-llm providers tags --json` API integration
- Model metadata with tag associations
- System resource detection for smart recommendations
- User preference storage/memory

## Notes
- Start with simple heuristics, can enhance with ML later
- Consider user feedback loop to improve recommendations
- Keep recommendation engine fast (< 100ms to compute)

## Non-Goals
- Machine learning-based recommendations (use simple rules)
- User rating/review system for models
- Advanced analytics or usage tracking