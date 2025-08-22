# Provider bridge: Claude CLI and OpenAI CLI

## Summary (What)
Add optional providers that shell out to `claude` (Anthropic CLI) and `openai` CLI tools, enabling U-5 “agent as a llm provider”.

## Why (Context)
- docs_tmp U-5: leverage locally authenticated vendor CLIs (MAX users).

## Scope (How)
- Implement CLI providers that invoke subprocess with prompt/stdin and parse stdout.
- Config flags: `provider.type=claude-cli` or `openai-cli`, optional model override.
- Detect missing binaries with helpful install guidance.

## Acceptance Criteria
- With respective type set and CLI installed, `generate/chat` returns text.
- Clear error if CLI missing.

## Dependencies
- 002 Provider schema.

## Risks
- CLI output format changes; keep robust parsing and version check.

## Estimate
- Complexity: M (0.5–1 day)

## Test Plan
- Mock subprocess; golden output parsing tests.

