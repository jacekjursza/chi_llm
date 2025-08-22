# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

chi_llm is a zero-configuration micro-LLM library for Python. It provides instant AI capabilities with no API keys, no cloud dependencies, and automatic model management. The library supports multiple small language models (270M to 9B parameters) and includes features like RAG, prompt templates, and flexible configuration management.

## Common Commands

### CLI Usage
```bash
# Interactive setup (choose and download models)
chi-llm setup

# Generate text
chi-llm generate "Your prompt here"

# Interactive chat
chi-llm chat

# Analyze code
chi-llm analyze file.py -q "What does this do?"

# Model management
chi-llm models list              # List all available models
chi-llm models current           # Show current model and config source
chi-llm models set phi3-mini     # Set default model globally
chi-llm models set phi3-mini --local  # Set for current project only

# RAG operations
chi-llm rag query "question" --documents doc1.txt doc2.txt
chi-llm rag add doc.txt --db knowledge.db
```

### Python API
```python
from chi_llm import MicroLLM, quick_llm

# Zero configuration
llm = MicroLLM()
response = llm.generate("Hello!")

# Quick one-liner
print(quick_llm("Write a haiku"))

# With specific model
llm = MicroLLM(model_id="phi3-mini")

# RAG usage
from chi_llm.rag import quick_rag
answer = quick_rag("question", ["doc1", "doc2"])
```

### Installation & Setup
```bash
# Basic installation
pip install git+https://github.com/jacekjursza/chi_llm.git

# With RAG support
pip install "git+https://github.com/jacekjursza/chi_llm.git#egg=chi-llm[rag]"

# Full installation
pip install "git+https://github.com/jacekjursza/chi_llm.git#egg=chi-llm[full]"

# Development
pip install -e ".[dev]"
```

### Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_core.py -v

# With coverage
python -m pytest tests/ --cov=chi_llm --cov-report=html
```

## Architecture & Key Components

### Core Module: `chi_llm/core.py`
- **MicroLLM class**: Main interface for all LLM operations
- **Singleton pattern**: Model loaded once, reused across instances
- **Model management**: Auto-downloads models from HuggingFace
- **Key methods**:
  - `generate()`: Text generation with prompts
  - `chat()`: Conversational interface with history
  - `complete()`: Text completion
  - `ask()`: Question answering with optional context
  - `analyze()`: Code analysis (backward compatibility)
  - `extract()`: Structured data extraction
  - `summarize()`: Text summarization
  - `translate()`: Language translation
  - `classify()`: Text classification

### Model Management: `chi_llm/models.py`
- **ModelInfo dataclass**: Model metadata (size, RAM, context, etc.)
- **MODELS registry**: 18 curated models from 270M to 9B (including coding & reasoning models)
- **ModelManager class**: Handles downloads, switching, configuration
- **Configuration hierarchy**:
  1. Environment variables (CHI_LLM_MODEL, etc.)
  2. Local project config (.chi_llm.json)
  3. Parent project config (searches up directories)
  4. Global user config (~/.cache/chi_llm/model_config.json)
  5. Built-in defaults (gemma-270m)

### CLI: `chi_llm/cli.py`
- **500+ lines**: Comprehensive command-line interface
- **Commands**: generate, chat, complete, ask, analyze, extract, summarize, translate, classify, template, rag, setup, models, interactive
- **Model management**: List, switch, info commands
- **RAG integration**: Query, add, search operations

### Setup Wizard: `chi_llm/setup.py`
- **Interactive setup**: User-friendly model selection
- **System detection**: RAM-based recommendations
- **Download management**: HuggingFace integration
- **Quick & advanced modes**: Different user expertise levels

### RAG Module: `chi_llm/rag.py` (optional)
- **MicroRAG class**: Vector-based document retrieval
- **SQLite-vec backend**: Local vector storage
- **Embeddings**: sentence-transformers models
- **YAML config**: Configuration file support

### Prompt Templates: `chi_llm/prompts.py`
- **Pre-built templates**: Code review, SQL generation, etc.
- **Customizable**: Easy to extend with new templates

## Model Configuration

### Default Model
- **gemma-270m**: Ultra-lightweight (200MB), works everywhere
- **Context**: 32,768 tokens (full capacity)
- **Max tokens**: 4,096 (default response length)

### Available Models
- **Tiny (270M-0.6B)**: gemma-270m, qwen3-0.6b, qwen2.5-coder-0.5b - Fast, minimal RAM
- **Small (1-2B)**: qwen3-1.7b, stablelm-2-1.6b, liquid-lfm2-1.2b, deepseek-r1-1.5b, qwen2.5-coder-1.5b
- **Medium (2-4B)**: gemma2-2b, phi2-2.7b, stablelm-3b, qwen2.5-coder-3b, qwen3-4b (256K context!)
- **Large (3-9B)**: phi3-mini, qwen3-8b, gemma2-9b, qwen2.5-coder-7b

### Model Storage
- **Location**: `~/.cache/chi_llm/`
- **Format**: GGUF quantized (4-bit or 2-bit)
- **Auto-download**: First use triggers download

## Configuration Management

### File Locations
- **Global**: `~/.cache/chi_llm/model_config.json`
- **Project**: `.chi_llm.json` (current or parent directories)
- **Custom**: Via CHI_LLM_CONFIG environment variable

### Configuration Schema
```json
{
  "default_model": "model_id",
  "downloaded_models": ["list", "of", "models"],
  "preferred_context": 32768,
  "preferred_max_tokens": 4096
}
```

### Environment Variables
- `CHI_LLM_MODEL`: Override default model
- `CHI_LLM_CONFIG`: Custom config path
- `CHI_LLM_CONTEXT`: Context window size
- `CHI_LLM_MAX_TOKENS`: Max response tokens

## Important Notes

- **Zero configuration**: Works out of the box with defaults
- **100% local**: No API keys, no cloud dependencies
- **Auto-caching**: Models downloaded once, reused forever
- **CPU-friendly**: All models work on CPU (GPU optional)
- **Context limits**: Respect model-specific context windows
- **Prompt format**: Uses Gemma-style chat format
- **Singleton pattern**: Model loaded once per process
- **Thread-safe**: Uses locks for model loading

## Testing Guidelines

- **Use smallest model**: gemma-270m for fast tests
- **Mock model loading**: Use fixtures in tests/
- **Check all methods**: Core has 10+ public methods
- **Test configuration**: Verify hierarchy works
- **CLI testing**: Test all subcommands