# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

chi_llm is a zero-configuration micro-LLM library for Python providing instant AI capabilities with no API keys or cloud dependencies. It supports multiple models (270M to 9B parameters) and includes RAG, prompt templates, provider routing, and TUI configuration.

## Common Development Commands

### Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_core.py -v

# Run with coverage
python -m pytest tests/ --cov=chi_llm --cov-report=html

# Run specific test categories
python -m pytest tests/test_provider_*.py -v  # Provider tests
python -m pytest tests/test_tui_*.py -v       # TUI tests
python -m pytest tests/test_*_cli.py -v       # CLI tests
```

### Code Quality
```bash
# Format code
black chi_llm/ tests/ --line-length 88

# Lint code
ruff check chi_llm/ --fix

# Run pre-commit hooks manually
pre-commit run --all-files

# Install pre-commit hooks
pre-commit install
```

### Building & Installation
```bash
# Development installation
pip install -e ".[dev]"

# Install with TUI support
pip install -e ".[ui]"

# Install with all features
pip install -e ".[full]"

# Build distribution
python -m build
```

### Go TUI Development
```bash
# Run Go TUI
cd go-chi && go run ./cmd/chi-tui

# Run Go tests
cd go-chi && go test ./...

# Build Go TUI binary
cd go-chi && go build -o chi-tui ./cmd/chi-tui
```

## Architecture & Key Components

### Provider System Architecture
The library uses a flexible provider system enabling multiple backend support:

**Provider Router** (`chi_llm/providers/router.py`):
- Central orchestrator selecting appropriate provider based on configuration
- Falls back through provider hierarchy: Environment → Local → Global config
- Manages provider lifecycle and error handling

**Provider Types**:
- `local`: Default llama.cpp provider using local GGUF models
- `ollama`: Integration with Ollama server
- `lmstudio`: LM Studio server integration
- `openai`: OpenAI API (requires key)
- `claude-cli`/`openai-cli`: CLI bridge providers

**Provider Discovery** (`chi_llm/providers/discovery.py`):
- Auto-detects available providers on system
- Checks for Ollama/LMStudio servers
- Validates API keys and connectivity

### Configuration Hierarchy
Configuration resolution order (highest priority first):
1. Environment variables (`CHI_LLM_MODEL`, `CHI_LLM_PROVIDER`)
2. Local project config (`.chi_llm.json` in current directory)
3. Parent project configs (searches up directory tree)
4. Global user config (`~/.cache/chi_llm/model_config.json`)
5. Built-in defaults (gemma-270m with local provider)

### TUI System

**Go TUI** (`go-chi/`):
- Primary and only interactive TUI using Bubble Tea framework
- Located in `go-chi/internal/tui/`
- Models, providers, diagnostics views
- Mouse support, theming, animations

Note: The legacy Python/Textual UI has been removed.

### Core Module Organization

**Core LLM** (`chi_llm/core.py`):
- `MicroLLM` class: Main interface, singleton pattern
- Methods: generate, chat, complete, ask, analyze, extract, summarize, translate, classify
- Handles both local and external providers

**Model Management** (`chi_llm/models.py`):
- `ModelInfo` dataclass: Model metadata
- `ModelManager`: Downloads, switching, configuration
- 20+ curated models including specialized coding models

**CLI System** (`chi_llm/cli_modules/`):
- Modular command structure
- `basic.py`: Core generation commands
- `models.py`: Model management
- `providers.py`: Provider configuration
- `bootstrap.py`: Project initialization
- `diagnostics.py`: System diagnostics
- `ui.py`: TUI launcher (prefers Go, falls back to Python)

### RAG System (`chi_llm/rag.py`)
- `MicroRAG` class: Vector-based retrieval
- SQLite-vec backend for embeddings
- FastEmbed/sentence-transformers support
- YAML configuration support

## Development Patterns & Conventions

### Error Handling
- Provider fallback chain for resilience
- Graceful degradation when optional features unavailable
- Clear error messages with actionable fixes

### Testing Strategy
- Mock model loading in tests using fixtures
- Test provider discovery and routing separately
- UI tests focus on store/controller logic
- Integration tests for CLI commands

### Code Organization
- CLI modules are self-contained with argument parsers
- Providers implement base interface
- TUI uses MVC with reactive store
- Configuration uses atomic file writes

### Adding New Features

**New Provider**:
1. Create provider class in `chi_llm/providers/`
2. Implement `BaseProvider` interface
3. Add to router's provider map
4. Add discovery logic if auto-detectable
5. Write tests in `tests/test_provider_*.py`

**New CLI Command**:
1. Create module in `chi_llm/cli_modules/`
2. Add `register_args()` and handler functions
3. Import in `chi_llm/cli.py`
4. Add to main argument parser
5. Write tests in `tests/test_*_cli.py`

**New Model**:
1. Add to `MODELS` dict in `chi_llm/models.py`
2. Include metadata: size, RAM, context, URL
3. Test with smallest variant first
4. Document in README's model section

## Important Notes

- **Singleton Pattern**: Model loaded once per process, reused across instances
- **Thread Safety**: Uses locks for model loading operations
- **Config Atomicity**: All config writes use temp file + rename
- **Provider Priority**: Local models preferred over external APIs
- **Context Limits**: Respect model-specific context windows (8K-256K)
- **Pre-commit Hooks**: Validate commit messages and file lengths
- **Go Version**: Requires Go 1.25+ for TUI development

## Development Workflow & Standards

### Kanban Workflow
Track work using the Kanban system in `docs/kanban/`:
- **TODO**: Plan tasks in `docs/kanban/todo/*.md` (one file per feature)
- **In Progress**: Move file to `docs/kanban/inprogress/` when starting work
- **Done**: Move to `docs/kanban/done/` when completed

### Commit Standards
Use Conventional Commits format:
```
type(scope): short imperative summary

Body explaining what and why (wrap at 72 chars)

Card-Id: XXX
Refs: docs/kanban/todo/XXX-feature-name.md
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `build`, `ci`, `revert`

### Code Quality Requirements
- **File Size**: Maximum 600 lines per file
- **Testing**: Unit tests required for all new features
- **Principles**: Apply Single Responsibility Principle and YAGNI
- **Architecture**: Modular, extensible with clear interfaces
- **Simplicity**: Avoid heavy plugin frameworks; prefer focused modules

### Pre-commit Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
pre-commit install --hook-type commit-msg

# Run on all files (optional first run)
pre-commit run --all-files
```

### Documentation Standards
- **Product Truth**: `README.md` (product overview), `CLAUDE.md` (dev reference)
- **Supporting Docs**: `docs/CLI.md`, `docs/configuration.md`, `docs/architecture-principles.md`
- **Roadmap**: Maintain in `docs/product/current/roadmap.md`
- **Changelog**: Create in `docs/changelog/<timestamp>-<brief>.md`
- **Language**: Code, comments, and permanent docs in English

### Execution Protocol
1. Create/update TODO card with scope and acceptance criteria
2. Move card to In Progress when starting
3. Before completing:
   - Run full test suite: `python -m pytest tests -v`
   - Format code: `black chi_llm/ tests/`
   - Lint: `ruff check chi_llm/`
   - Update relevant documentation
4. Move card to Done and add changelog entry
5. Commit atomically (one feature per commit)
6. Push to `master` after validation (early development phase)

### Environment & Permissions
- Virtualenv is already configured and active
- May install required Python packages for app operation
- May run shell commands for development/maintenance
- GitHub access available for direct `master` pushes (early phase)
- Ask before force-pushing or changing repo visibility
