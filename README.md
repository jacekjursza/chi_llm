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
- **⚡ Lightweight** - 270M parameter model, runs on any hardware
- **🔒 Private** - No API keys, no telemetry, no tracking
- **📦 Self-Contained** - Automatically downloads and manages models

## Installation

```bash
pip install chi-llm
```

Or install from GitHub:

```bash
pip install git+https://github.com/jacekjursza/chi_llm.git
```

## Quick Start

### The Simplest Example

```python
from chi_llm import quick_llm

print(quick_llm("Write a haiku about Python"))
```

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

### Configuration File

Create a `.chi_llm.yaml` file in your project root:

```yaml
model:
  temperature: 0.7
  max_tokens: 2048
  top_p: 0.95
  top_k: 40
verbose: false
```

### Environment Variables

```bash
export CHI_LLM_CONFIG=/path/to/config.yaml
```

## Model Information

chi_llm uses Google's **Gemma 3 270M** model:

- **Size**: ~200MB (downloads automatically on first use)
- **Parameters**: 270 million
- **Quantization**: 4-bit (Q4_K_M)
- **Context**: 8,192 tokens
- **Requirements**: 4GB RAM minimum

The model is cached locally in `~/.cache/chi_llm/` and only downloads once.

## API Reference

### MicroLLM Class

```python
llm = MicroLLM(temperature=0.7, max_tokens=2048, verbose=False)
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