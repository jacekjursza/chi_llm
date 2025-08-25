# chi_llm - Zero Configuration Micro-LLM Library

🚀 **The simplest way to add AI to your Python project**  
No API keys. No cloud dependencies. No complex setup. Just import and use.

```python
from chi_llm import MicroLLM

llm = MicroLLM()
response = llm.generate("Hello, how are you?")
print(response)
```

## Why chi_llm?

- **🔌 Zero Configuration** - Works out of the box, no setup required
- **🏠 100% Local** - Your data never leaves your machine
- **🎯 Simple API** - One import, intuitive methods
- **⚡ Multiple Models** - From 270M to 9B, choose what fits your needs
- **🔒 Private** - No API keys, no telemetry, no tracking
- **📦 Self-Contained** - Automatically downloads and manages models
- **🎮 Interactive Setup** - Easy model selection and management

## 🚀 Installation

### Quick Install (One-Liner)

**Linux/macOS:**
```bash
curl -sSL https://raw.githubusercontent.com/jacekjursza/chi_llm/master/install.sh | bash
```

**Windows PowerShell:**
```powershell
iwr -useb https://raw.githubusercontent.com/jacekjursza/chi_llm/master/install.ps1 | iex
```

**Windows Command Prompt:**
```cmd
curl -sSL https://raw.githubusercontent.com/jacekjursza/chi_llm/master/install.bat -o install.bat && install.bat
```

### Manual Installation

chi_llm requires Python 3.8+ and automatically manages model downloads.

```bash
# Basic installation
pip install git+https://github.com/jacekjursza/chi_llm.git

# With RAG support (FastEmbed only - recommended)
pip install "git+https://github.com/jacekjursza/chi_llm.git#egg=chi-llm[rag]"

# RAG with sentence-transformers compatibility  
pip install "git+https://github.com/jacekjursza/chi_llm.git#egg=chi-llm[rag-st]"

# Full installation (all features)
pip install "git+https://github.com/jacekjursza/chi_llm.git#egg=chi-llm[full]"

# Development installation
git clone https://github.com/jacekjursza/chi_llm.git
cd chi_llm
pip install -e ".[dev]"
```

### Installation Features

✅ **Automatic dependency management**  
✅ **Cross-platform compatibility**  
✅ **Error handling and diagnostics**  
✅ **PATH configuration assistance**  
✅ **Zero-config first run experience**

## Quick Start

### 🚀 First-Time Setup (Choose Your Model)

```bash
# Run interactive setup to choose your model
chi-llm setup

# Or use the default tiny model (270M)
# It will auto-download on first use
```

### The Simplest Example

```python
from chi_llm import quick_llm

print(quick_llm("Write a haiku about Python"))
```

For using chi_llm as a configuration provider in external apps, see the "Config Provider API (SDK)" section in `SDK_USAGE.md`.

### Basic Usage

```python
from chi_llm import MicroLLM

# Initialize (one-time model download happens here)
llm = MicroLLM()

# Generate text
response = llm.generate("Explain quantum computing in simple terms")
print(response)

# Have a conversation
response = llm.chat("What's the weather like?")
print(response)

# Complete text
response = llm.complete("The quick brown fox")
print(response)

# Ask questions
response = llm.ask("What is the capital of France?")
print(response)
```

## Common Use Cases

### 💬 Chatbot

```python
from chi_llm import MicroLLM

llm = MicroLLM()
history = []

while True:
    user_input = input("You: ")
    if user_input.lower() == 'quit':
        break
    
    response = llm.chat(user_input, history=history)
    print(f"AI: {response}")
    
    history.append({"user": user_input, "assistant": response})
```

### 📝 Text Generation

```python
# Creative writing
story = llm.generate("Write a short story about a robot learning to paint")

# Email drafting
email = llm.generate("Write a professional email declining a meeting invitation")

# Product descriptions
description = llm.generate("Write a product description for wireless headphones")
```

### 🔍 Data Extraction

```python
# Extract structured data
text = "John Doe is 30 years old and works as a software engineer in New York."
json_data = llm.extract(text, format="json")
print(json_data)
# Output: {"name": "John Doe", "age": 30, "occupation": "software engineer", "location": "New York"}
```

### 📊 Text Analysis

```python
# Summarization
long_article = "..." # Your long text here
summary = llm.summarize(long_article, max_sentences=3)

# Classification
sentiment = llm.classify(
    "I absolutely love this product! Best purchase ever!",
    categories=["positive", "negative", "neutral"]
)
print(sentiment)  # Output: "positive"

# Translation
translated = llm.translate("Bonjour le monde", target_language="English")
print(translated)  # Output: "Hello world"
```

### 💻 Code Analysis

```python
code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""

# Analyze code
explanation = llm.analyze(code)
print(explanation)

# Ask specific questions
complexity = llm.ask("What is the time complexity?", context=code)
print(complexity)
```

### 📋 Using Prompt Templates

```python
from chi_llm import MicroLLM, PromptTemplates

llm = MicroLLM()
templates = PromptTemplates()

# Code review
code = "def add(a, b): return a + b"
review_prompt = templates.code_review(code, language="Python")
review = llm.generate(review_prompt)

# Generate SQL from description
sql_prompt = templates.sql_from_description("Get all users who signed up last month")
sql = llm.generate(sql_prompt)

# Create user story
story_prompt = templates.user_story("dark mode toggle feature")
user_story = llm.generate(story_prompt)
```

## 🧠 RAG (Retrieval Augmented Generation)

**New in v2.1!** Add knowledge base capabilities to your LLM with zero configuration.

**Default embeddings:** FastEmbed with `intfloat/multilingual-e5-base` (280MB, 768 dims, 100+ languages 🌍)

### Quick RAG Example

```python
from chi_llm.rag import quick_rag

# Your documents
documents = [
    "Python was created by Guido van Rossum in 1991.",
    "Python emphasizes code readability and uses indentation.",
    "Python 3.0 was released on December 3, 2008."
]

# Ask questions about your documents
answer = quick_rag("When was Python 3.0 released?", documents)
print(answer)  # Output: Python 3.0 was released on December 3, 2008.
```

### Persistent Knowledge Base

```python
from chi_llm.rag import MicroRAG

# Initialize RAG with persistent storage
rag = MicroRAG(db_path="./knowledge.db")

# Add documents
rag.add_document("The Earth orbits around the Sun.")
rag.add_document("The Moon orbits around the Earth.")
rag.add_document("A year is the time Earth takes to orbit the Sun.")

# Query your knowledge base
answer = rag.query("What orbits around the Earth?")
print(answer)  # Output: The Moon orbits around the Earth.

# Get answers with sources
result = rag.query("How long is a year?", include_sources=True)
print(f"Answer: {result['answer']}")
print(f"Based on {len(result['sources'])} sources")
```

### RAG with YAML Configuration

Create a `rag_config.yaml`:

```yaml
db_path: ./my_knowledge.db
embedding_model: sentence-transformers/all-MiniLM-L6-v2

documents:
  - content: "chi_llm is a zero-configuration micro-LLM library."
    metadata: {type: "definition"}
  - content: "It uses Gemma 3 270M model for text generation."
    metadata: {type: "technical"}
```

Use it in your code:

```python
from chi_llm.rag import MicroRAG

# Load from config
rag = MicroRAG.from_config("rag_config.yaml")

# Ready to answer questions!
answer = rag.query("What model does chi_llm use?")
```

### RAG Features

- 🗄️ **SQLite Vector Store** - Efficient local storage with sqlite-vec
- 🔍 **Semantic Search** - Find relevant documents using embeddings
- 📚 **Document Management** - Add, search, and manage documents
- 🏷️ **Metadata Support** - Tag documents with custom metadata
- ⚡ **Fast & Local** - Everything runs on your machine
- 📝 **YAML Config** - Configure via simple YAML files

## Advanced Features

### Configuration Options

```python
# Custom configuration
llm = MicroLLM(
    temperature=0.3,  # Lower = more focused, Higher = more creative
    max_tokens=1024,  # Maximum response length
    verbose=True      # Show loading progress
)
```

### Configuration Hierarchy

chi_llm looks for configuration in this order (highest priority first):

1. **Environment Variables**
   ```bash
   export CHI_LLM_MODEL=phi3-mini        # Override default model
   export CHI_LLM_CONFIG=/path/to/config # Custom config path
   export CHI_LLM_CONTEXT=16384          # Context window size
   export CHI_LLM_MAX_TOKENS=2048        # Max response tokens
   ```

2. **Local Project Config** (`.chi_llm.json` in current directory)
   ```json
   {
     "default_model": "qwen3-1.7b",
     "preferred_context": 32768,
     "preferred_max_tokens": 4096
   }
   ```

3. **Parent Project Config** (searches up directories for `.chi_llm.json`)
   - Useful for monorepos or nested projects

4. **Global User Config** (`~/.cache/chi_llm/model_config.json`)
   - Set via `chi-llm models set <model-id>`
   - Or `chi-llm setup`

5. **Built-in Defaults**
   - Model: gemma-270m (ultra-lightweight, 200MB)
   - Context: 32,768 tokens (full model capacity)
   - Max tokens: 4,096 (default response length)

### Managing Configuration

```bash
# Set model globally (for all projects)
chi-llm models set phi3-mini

# Set model locally (for current project only)
chi-llm models set phi3-mini --local

# Check current configuration source
chi-llm models current
```

This allows you to:
- Have different models per project
- Override settings via environment variables in CI/CD
- Share team settings via committed `.chi_llm.json`
- Keep personal preferences in global config

## 🧠 Available Models

chi_llm now supports multiple models! Choose based on your needs:

### Recommended Models

| Model | Size | RAM | Best For |
|-------|------|-----|----------|
| **Phi-3 Mini** | 3.8B | 5GB | Best quality, recommended for most users |
| **Qwen3 1.7B** | 1.7B | 3GB | Best small model with thinking mode |
| **Liquid LFM2** | 1.2B | 2.5GB | Blazingly fast, excels at math & multilingual |
| **Gemma 2 2B** | 2B | 4GB | Google's efficient model, good balance |

### 🚀 New Cutting-Edge Models

#### Long Context Models (256K tokens!)
| Model | Size | RAM | Special Features |
|-------|------|-----|-----------------|
| **Qwen3 4B Thinking** | 4B | 5GB | Advanced reasoning with thinking capability |
| **Qwen3 4B Instruct** | 4B | 5GB | Enhanced general capabilities |

#### Specialized Coding Models
| Model | Size | RAM | Best For |
|-------|------|-----|----------|
| **Qwen2.5 Coder 0.5B** | 0.5B | 1.5GB | IDE integration, instant completions |
| **Qwen2.5 Coder 1.5B** | 1.5B | 2.5GB | Balanced coding assistant |
| **Qwen2.5 Coder 3B** | 3B | 4GB | Complex coding tasks |
| **Qwen2.5 Coder 7B** | 7B | 8GB | Professional development |

#### Latest Additions
| Model | Size | RAM | Special Features |
|-------|------|-----|-----------------|
| **DeepSeek R1 Distill** | 1.5B | 3GB | Distilled reasoning capabilities |
| **Liquid LFM2** | 1.2B | 2.5GB | Hybrid CPU/GPU architecture |

### All Available Models

```bash
# List all available models
chi-llm models list

# Show current model
chi-llm models current

# Set default model (after downloading via setup)
chi-llm models set phi3-mini
```

**Model Categories:**
- **Tiny (270M)**: Ultra-fast, minimal RAM, basic tasks
- **Small (1-2B)**: Good quality, runs on most devices
- **Medium (2-3B)**: Better quality, still efficient
- **Large (3-9B)**: Best quality, needs more RAM

### Using Specific Models in Code

```python
from chi_llm import MicroLLM

# Use specific model
llm = MicroLLM(model_id="phi3-mini")

# Or use the default (configured via setup)
llm = MicroLLM()
```

## Model Information

The default model is **Gemma 3 270M**, but you can choose from:

- **Size**: ~200MB (downloads automatically on first use)
- **Parameters**: 270 million
- **Quantization**: 4-bit (Q4_K_M)
- **Context**: 32,768 tokens (full model capacity)
- **Requirements**: 4GB RAM minimum

The model is cached locally in `~/.cache/chi_llm/` and only downloads once.

## API Reference

### MicroLLM Class

```python
llm = MicroLLM(temperature=0.7, max_tokens=4096, verbose=False)
```

**Methods:**
- `generate(prompt, **kwargs)` - Generate text from a prompt
- `chat(message, history=None)` - Chat with context
- `complete(text, **kwargs)` - Complete/continue text
- `ask(question, context=None)` - Question answering
- `analyze(code, question=None)` - Analyze code
- `extract(text, format="json", schema=None)` - Extract structured data
- `summarize(text, max_sentences=3)` - Summarize text
- `translate(text, target_language="English")` - Translate text
- `classify(text, categories)` - Classify into categories

### Quick Functions

```python
from chi_llm import quick_llm

# One-liner generation
result = quick_llm("Your prompt here")
```

## Performance Tips

1. **Reuse instances** - Create one `MicroLLM` instance and reuse it
2. **Batch processing** - Process multiple items with the same instance
3. **Lower temperature** - Use `temperature=0.1` for factual tasks
4. **Adjust max_tokens** - Lower values for faster responses

## Troubleshooting

### First Run
The model downloads automatically on first use (~200MB). This only happens once.

### Memory Issues
- Requires ~4GB RAM
- Close other applications if needed
- Use shorter prompts/contexts

### Slow Performance
- Normal on CPU: ~10-30 seconds per response
- Model loads once and stays in memory
- Subsequent calls are faster

## Examples

Check out the [`examples/`](examples/) directory for complete examples:

- [`basic_usage.py`](examples/basic_usage.py) - Simple examples to get started
- [`integration_example.py`](examples/integration_example.py) - Advanced integration patterns
- [`chatbot.py`](examples/chatbot.py) - Interactive chatbot
- [`data_extraction.py`](examples/data_extraction.py) - Extract structured data
- [`code_assistant.py`](examples/code_assistant.py) - Code analysis and generation

## Why "chi_llm"?

"Chi" (氣) represents life force or energy flow in Eastern philosophy. This library aims to provide that same effortless flow of AI capabilities into your Python projects - simple, natural, and powerful.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Google DeepMind for the Gemma 3 model
- llama.cpp team for the inference engine
- HuggingFace for model hosting

---

**Remember**: The best tool is the one that gets out of your way. chi_llm is designed to be exactly that - invisible infrastructure that just works.

```python
# That's it! You're ready to go 🚀
from chi_llm import MicroLLM
llm = MicroLLM()
print(llm.generate("Hello, World!"))
```
### Project Bootstrap

```bash
# Scaffold config and env placeholders in current directory
chi-llm bootstrap . --provider local --model-id qwen3-1.7b --extras none

# Outputs:
#  - .chi_llm.json       (project config; default_model for local)
#  - .env.sample         (API keys / provider env placeholders)
#  - llm-requirements.txt (minimal deps, extras optional)
```

Notes:
- For external providers, use e.g. `--provider openai --model-id gpt-4o-mini`.
- Copy `.env.sample` to `.env` and `source .env` (or use python-dotenv).
 - YAML config is available via `--yaml` (writes `.chi_llm.yaml`).

### UI (Rust TUI)

```bash
# Launch the interactive TUI (auto-builds if needed)
chi-llm ui

# Force rebuild before launch
chi-llm ui --rebuild

# Pass args to the TUI after -- (example: no alt-screen)
chi-llm ui -- --no-alt

# Developer run (direct):
cd tui/chi-tui && cargo run
```

Shortcuts:
- `1/2/3` — Sections (Welcome / Configure / (Re)Build)
- `4` — Diagnostics (status + export JSON)
- `↑/↓` or `k/j` — Navigate lists
- `enter` — Select / Confirm
- `Tab`/`Shift+Tab` — Switch between list and form in Providers
- `F` — Providers: open dynamic form (schema‑driven)
- `b` — Back to Welcome
- `e` — Export diagnostics to `chi_llm_diagnostics.json`
- `t` — Toggle theme, `a` — Toggle animation

Note: the previous Python/Textual UI has been removed. The Go TUI has been retired. The interactive UI is implemented in Rust/ratatui under `tui/chi-tui/` and is launched via `chi-llm ui`.
