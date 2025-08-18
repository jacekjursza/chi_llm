# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a code analyzer tool that uses Google's Gemma 3 270M model (local LLM) to analyze code files. It runs completely offline after initial model download and provides AI-powered code analysis without requiring API keys.

## Common Commands

### Running the Analyzer
```bash
# Basic usage
python main.py <file_path>

# With custom question
python main.py <file_path> -q "Your specific question about the code"

# Force CPU mode
python main.py <file_path> --no-gpu
```

### Installation & Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Install as system-wide command (optional)
pip install .

# Add GPU support (optional)
pip install torch
```

### Development Tasks
```bash
# Run tests (when available)
python -m pytest test_example.py

# Install development dependencies
pip install -e ".[dev]"
```

## Architecture & Key Components

### Core Module: `main.py`
- **Entry point**: CLI interface for code analysis
- **Model management**: Downloads and caches Gemma 3 270M model (~200MB) in `~/.cache/gemma_analyzer/`
- **Key functions**:
  - `download_model()`: Handles one-time model download from HuggingFace
  - `load_model()`: Initializes Llama.cpp with optimized settings
  - `analyze_code()`: Generates AI analysis using specific prompt format
  - `read_file()`: Handles file reading with size limits (100KB warning, 20K char truncation for analysis)

### Model Configuration
- Uses GGUF quantized format (Q4_K_M) for optimal size/quality
- Context window: 8192 tokens (reduced from 32K for stability)
- Inference engine: llama-cpp-python
- Temperature: 0.3 (low for accurate analysis)

### Prompt Format
The model expects Gemma-specific chat format:
```
<start_of_turn>user
[content]
<end_of_turn>
<start_of_turn>model
```

## Important Notes

- Model is downloaded from HuggingFace on first run
- GPU detection is currently disabled in code (`check_gpu_available()` returns False)
- File size limits: 100KB for reading, 20K characters for analysis
- The tool uses llama.cpp warnings suppression for cleaner output