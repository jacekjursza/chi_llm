# Chi_LLM CLI Documentation

Chi_LLM provides a powerful command-line interface for all its features.

## Installation

After installing chi_llm, the CLI is available as:
- `chi-llm` (main command)
- `code-analyzer` (backward compatibility)

## Quick Examples

```bash
# Generate text
chi-llm generate "Write a haiku about Python"

# Interactive chat
chi-llm chat

# Ask a question
chi-llm ask "What is the capital of France?"

# Analyze code
chi-llm analyze script.py -q "Find potential bugs"

# Summarize text
chi-llm summarize "Long text here..." -s 3

# Interactive mode
chi-llm interactive
```

## Available Commands

### 📝 `generate` - Generate text from prompt

```bash
# Simple generation
chi-llm generate "Write a story about a robot"

# From file
chi-llm generate -f prompt.txt

# With parameters
chi-llm generate "Explain quantum computing" -t 0.3 -m 500
```

**Options:**
- `-f, --file` - Read prompt from file
- `-t, --temperature` - Creativity level (0.0-1.0, default: 0.7)
- `-m, --max-tokens` - Maximum response length (default: 4096)

### 💬 `chat` - Interactive chat mode

```bash
# Start chat session
chi-llm chat

# With custom settings
chi-llm chat -t 0.8 -m 1024
```

**Features:**
- Maintains conversation context
- Type `exit`, `quit`, or `bye` to stop
- Remembers last 10 exchanges

### ✏️ `complete` - Complete/continue text

```bash
# Complete text
chi-llm complete "The quick brown fox"

# From file
chi-llm complete -f story.txt
```

### ❓ `ask` - Ask questions

```bash
# Simple question
chi-llm ask "What is machine learning?"

# With context
chi-llm ask "What does this do?" -c "def factorial(n): return 1 if n==0 else n*factorial(n-1)"

# Context from file
chi-llm ask "Summarize this" -cf document.txt
```

**Options:**
- `-c, --context` - Provide context for the question
- `-cf, --context-file` - Read context from file

### 🔍 `analyze` - Analyze code files

```bash
# Basic analysis
chi-llm analyze main.py

# Custom question
chi-llm analyze script.js -q "Find security issues"

# Force CPU mode
chi-llm analyze app.cpp --no-gpu
```

### 📊 `extract` - Extract structured data

```bash
# Extract JSON
chi-llm extract "John is 30 years old" --format json

# With schema
chi-llm extract "Meeting at 3pm tomorrow" --schema '{"time": "string", "date": "string"}'

# Save to file
chi-llm extract -f email.txt --format json -o data.json
```

**Options:**
- `--format` - Output format: `json` or `yaml`
- `--schema` - JSON schema for extraction
- `-o, --output` - Save to file

### 📄 `summarize` - Summarize text

```bash
# Summarize text
chi-llm summarize "Long article text..."

# From file
chi-llm summarize -f article.txt -s 5

# Control length
chi-llm summarize "Text" -s 3  # Max 3 sentences
```

### 🌐 `translate` - Translate text

```bash
# Translate to English (default)
chi-llm translate "Bonjour le monde"

# Specify target language
chi-llm translate "Hello world" -l Spanish

# From file
chi-llm translate -f document.txt -l German
```

### 🏷️ `classify` - Classify text

```bash
# Sentiment analysis
chi-llm classify "I love this product!" -c "positive,negative,neutral"

# Topic classification
chi-llm classify -f article.txt -c "tech,sports,politics,entertainment"
```

### 📋 `template` - Use prompt templates

```bash
# Code review
chi-llm template code-review "def add(a,b): return a+b" --language Python

# Write tests
chi-llm template write-tests -f function.py --framework pytest

# Generate SQL
chi-llm template sql "Get all users who signed up last month"

# Email draft
chi-llm template email "Meeting reschedule request" --tone friendly

# Commit message
chi-llm template commit "Added login functionality and fixed bugs"
```

**Available Templates:**
- `code-review` - Review code for issues
- `explain-code` - Explain how code works
- `fix-error` - Fix code errors
- `write-tests` - Generate unit tests
- `optimize` - Optimize code performance
- `document` - Add documentation
- `sql` - Generate SQL from description
- `regex` - Create regex patterns
- `email` - Draft professional emails
- `commit` - Generate commit messages
- `user-story` - Create user stories

### 📦 `models` - Manage local models

```bash
# List all models (human-readable)
chi-llm models list

# JSON output for UI/automation
chi-llm models list --json | jq '.[0]'

# Show current model
chi-llm models current
chi-llm models current --json

# Show details for a model
chi-llm models info qwen3-1.7b
chi-llm models info qwen3-1.7b --json

# Set default model (must be downloaded)
chi-llm models set qwen3-1.7b --local   # project only
chi-llm models set phi3-mini            # global

# Validate a YAML catalog (path optional; defaults to packaged catalog)
chi-llm models validate-yaml ./chi_llm/models.yaml
chi-llm models validate-yaml ./chi_llm/models.yaml --json | jq
```

### 🧰 `setup` - Setup and recommendation

```bash
# Interactive wizard (download and choose model)
chi-llm setup

# Show recommended model for this system
chi-llm setup recommend
chi-llm setup recommend --json | jq
```

### 🔌 `providers` — Manage provider configuration

```bash
# List supported providers (JSON/human)
chi-llm providers list
chi-llm providers list --json | jq

# Show provider field schemas (for UIs)
chi-llm providers schema
chi-llm providers schema --json | jq

# Show current provider (merged from env/files)
chi-llm providers current
chi-llm providers current --json | jq

# Set provider locally for this project
chi-llm providers set lmstudio --host 127.0.0.1 --port 1234 --model qwen2.5:latest --local
# Local provider can point to a specific GGUF file
chi-llm providers set local --model-path /abs/path/to/model.gguf --local
# Optional tuning for local provider
chi-llm providers set local --context-window 32768 --n-gpu-layers 0 --output-tokens 2048 --local
# Echo saved config as JSON (path + scope)
chi-llm providers set ollama --host 127.0.0.1 --port 11434 --model llama3.2:latest --json | jq

# Set provider globally (user config)
chi-llm providers set ollama --host 127.0.0.1 --port 11434 --model llama3.2:latest
```

Notes:
- Supported now: `local`, `lmstudio`, `ollama`, `openai`, `anthropic`, `claude-cli`, `openai-cli`. Others (`groq`, `gemini`) are placeholders.
- `providers schema` exposes field schemas per type (name, type, required, default) for UIs and automation.
- Settings are written under the `provider` key in `.chi_llm.json` (local) or the global config.
- For routing across multiple providers, define `provider_profiles` in your config and set `llm.tags` in code; see `docs/configuration.md`.

### 🩺 `diagnostics` - Environment checks

```bash
# JSON summary (for UI/automation)
chi-llm diagnostics --json | jq

# Human-readable summary
chi-llm diagnostics
```

Fields include:
- python: version and implementation
- node: node/npm presence
- cache: cache path existence/writability
- model: current model, available vs recommended RAM
- network: basic reachability to Hugging Face
 - config: resolution mode, allow_global flag, config source/path, default vs effective model (decision)

Explain model selection:

```bash
# Human-readable explanation
chi-llm models current --explain

# JSON with explanation (for UIs)
chi-llm models current --explain --json | jq
```

The explanation shows:
- resolution mode (project-first/env-first) and whether global is allowed
- presence of env/project/local/global sources
- explicit default vs fallback
- effective model (provider local fallback or legacy default when no explicit default)

### 🧠 `rag` - RAG (Retrieval Augmented Generation)

**Note:** Requires installation with `pip install chi-llm[rag]`

#### Query documents

```bash
# Quick query without saving
chi-llm rag query "What is Python?" -d doc1.txt doc2.txt doc3.txt

# Query existing database
chi-llm rag query "How does it work?" --db knowledge.db

# With sources
chi-llm rag query "Explain the process" --db knowledge.db -s

# From config
chi-llm rag query "What's the purpose?" --config rag_config.yaml
```

#### Manage knowledge base

```bash
# Add documents to database
chi-llm rag add doc1.txt doc2.txt --db knowledge.db

# Search documents
chi-llm rag search "machine learning" --db knowledge.db -k 5

# Database info
chi-llm rag info --db knowledge.db
```

### 🎮 `interactive` - Interactive mode

```bash
chi-llm interactive
```

**Interactive Commands:**
- `chat` - Start chat conversation
- `generate TEXT` - Generate text
- `complete TEXT` - Complete text
- `ask QUESTION` - Ask a question
- `summarize TEXT` - Summarize text
- `translate TEXT` - Translate to English
- `help` - Show available commands
- `exit` - Exit interactive mode

## Configuration

### Using config files

Create `.chi_llm.yaml` in your project:

```yaml
model:
  temperature: 0.7
  max_tokens: 4096
verbose: false
```

### Environment variables

```bash
export CHI_LLM_CONFIG=/path/to/config.yaml
```

### Config command and UI (Rust TUI)

```bash
# Launch the interactive TUI (auto-builds if needed)
chi-llm ui

# Force rebuild before launch
chi-llm ui --rebuild

# Pass through args to the TUI (example: no alt-screen)
chi-llm ui -- --no-alt

# Read merged config as JSON
chi-llm config get --json | jq

# Set a config key (atomic write)
chi-llm config set default_model qwen3-1.7b --scope local   # project
chi-llm config set preferred_max_tokens 2048 --scope global # user
```

Note: The Python/Textual UI has been removed. The Go UI has been retired. The interactive UI is implemented in Rust/ratatui (source `tui/chi-tui/`) and launched via `chi-llm ui`.

### Configuration UI (Rust TUI)

The Diagnostics view integrates `chi-llm diagnostics --json` and `chi-llm models current --explain --json` to present:
- Environment status and basic connectivity
- Configuration resolution (sources, mode, allow_global)
- Default vs effective model and why it was chosen

## Advanced Usage

### Piping and redirection

```bash
# Pipe input
echo "Explain this code" | chi-llm generate

# Redirect output
chi-llm generate "Write a README" > README.md

# Chain commands
cat article.txt | chi-llm summarize -s 5 > summary.txt
```

### Scripting

```bash
#!/bin/bash
# Analyze all Python files
for file in *.py; do
    echo "Analyzing $file..."
    chi-llm analyze "$file" -q "Find bugs" >> analysis.log
done
```

### Aliases

Add to your `.bashrc` or `.zshrc`:

```bash
alias ai='chi-llm generate'
alias chat='chi-llm chat'
alias explain='chi-llm ask'
alias tldr='chi-llm summarize -s 3'
```

## Examples

### Code review workflow

```bash
# Review changes
git diff | chi-llm template code-review -f -

# Generate commit message
git diff --staged | chi-llm template commit -f -
```

### Documentation generation

```bash
# Document a function
chi-llm template document -f function.py --style google > function_docs.md

# Generate README
chi-llm generate "Write a README for a Python package that does X" > README.md
```

### Data processing

```bash
# Extract data from emails
chi-llm extract -f email.txt --format json | jq '.contacts'

# Classify support tickets
for ticket in tickets/*.txt; do
    category=$(chi-llm classify -f "$ticket" -c "bug,feature,question")
    echo "$ticket: $category"
done
```

### RAG for documentation

```bash
# Build knowledge base from docs
chi-llm rag add docs/*.md --db docs.db

# Query documentation
chi-llm rag query "How do I configure logging?" --db docs.db
```

## Tips and Tricks

1. **Speed vs Quality**: Lower temperature (0.1-0.3) for factual tasks, higher (0.7-0.9) for creative tasks

2. **Context Windows**: Keep prompts under 6000 characters for best performance

3. **Batch Processing**: Use shell loops for processing multiple files

4. **Output Formats**: Combine with `jq` for JSON processing, `pandoc` for format conversion

5. **Templates**: Create custom templates by combining base commands

## Troubleshooting

- **Model not loading**: First run downloads ~200MB model, ensure stable internet
- **Out of memory**: Reduce `--max-tokens` or close other applications
- **Slow generation**: Use `--no-gpu` flag if GPU is causing issues
- **RAG not working**: Install with `pip install chi-llm[rag]`

## Getting Help

```bash
# General help
chi-llm --help

# Command-specific help
chi-llm generate --help
chi-llm rag query --help
```
# Configuration UI (Rust TUI)

Primary interactive UI is implemented in Rust using `ratatui` + `crossterm` under `tui/chi-tui/` and is launched via `chi-llm ui`.

- Launch: `chi-llm ui` (auto-builds if needed)
- Force rebuild: `chi-llm ui --rebuild`
- Pass-through args: `chi-llm ui -- --no-alt`
- Sections: `1` Welcome, `2` Configure Provider, `3` (Re)Build Configuration, `4` Diagnostics
- Keys: `↑/↓` or `k/j` navigate, `enter` select, `b` back, `t` theme, `a` animation, `q` quit, `e` export (Diagnostics)
- (Re)Build: Enter writes project `.chi_llm.json` with minimal provider config

Note: The Python/Textual UI has been removed. The Go UI has been retired.
