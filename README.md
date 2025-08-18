# Code Analyzer - Gemma 3 270M

🔍 AI-powered code analysis tool using Google's Gemma 3 270M model. Analyze, understand, and get insights about your code files instantly.

## Features

- 🚀 **Ultra-fast analysis** using compact 270M parameter model
- 💻 **Cross-platform** support (Windows, Linux, macOS)
- 🎯 **GPU & CPU support** - automatically detects and uses available hardware
- 📦 **No API keys required** - runs completely offline
- 🔒 **Privacy-first** - your code never leaves your machine
- 📏 **32K context window** - analyze large code files

## Installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/code-analyzer-gemma.git
cd code-analyzer-gemma

# Install dependencies
pip install -r requirements.txt
```

### Install with GPU Support

```bash
# For GPU acceleration (optional)
pip install -r requirements.txt
pip install torch  # Adds GPU detection capability
```

### System-wide Installation

```bash
# Install as a command-line tool
pip install .

# Now you can use it from anywhere:
code-analyzer /path/to/file.py
```

## Usage

### Basic Usage

```bash
# Analyze a Python file
python main.py script.py

# Analyze a JavaScript file
python main.py app.js

# Analyze any code file
python main.py /path/to/code.cpp
```

### Custom Questions

```bash
# Ask specific questions about the code
python main.py main.py -q "What design patterns are used here?"
python main.py script.js -q "Find potential security issues"
python main.py app.cpp -q "Suggest performance optimizations"
python main.py func.py -q "Write unit tests for this function"
```

### Force CPU Mode

```bash
# Disable GPU even if available
python main.py file.py --no-gpu
```

## Examples

### Example 1: Analyze a Python Function

```bash
$ python main.py fibonacci.py
🔍 Code Analyzer powered by Gemma 3 270M
============================================================
📄 Analyzing: fibonacci.py
📏 File size: 245 characters
🤖 Loading AI model...
   Using CPU mode
✅ Model ready!

🔎 Analyzing code...
❓ Question: Describe what this code does and explain its main functionality.

------------------------------------------------------------

💡 Analysis Result:
------------------------------------------------------------
This code implements a Fibonacci sequence generator. The function calculates 
the nth Fibonacci number using recursion. It includes a base case for n <= 1 
and recursively calls itself to compute the sum of the two preceding numbers.

Key aspects:
- Time complexity: O(2^n) due to recursive calls
- Space complexity: O(n) for the call stack
- Could be optimized using memoization or iterative approach
------------------------------------------------------------

✨ Analysis complete!
```

### Example 2: Find Bugs

```bash
$ python main.py buggy_code.js -q "Find potential bugs and issues"
```

### Example 3: Code Review

```bash
$ python main.py pull_request.py -q "Perform a code review and suggest improvements"
```

## System Requirements

### Minimum Requirements
- Python 3.8+
- 4GB RAM
- 1GB free disk space (for model storage)

### Recommended
- Python 3.10+
- 8GB+ RAM
- NVIDIA GPU with 4GB+ VRAM (optional, for faster processing)
- SSD storage

## Model Information

- **Model**: Gemma 3 270M Instruction-Tuned
- **Size**: ~200MB (quantized GGUF format)
- **Parameters**: 270 million
- **Context**: 32,768 tokens
- **Format**: Q4_K_M quantization (optimal quality/size ratio)

## First Run

On first run, the tool will automatically download the model (~200MB). The model is cached in:
- Linux/Mac: `~/.cache/gemma_analyzer/`
- Windows: `%USERPROFILE%\.cache\gemma_analyzer\`

## Supported File Types

The analyzer works with any text-based code file:
- Python (.py)
- JavaScript/TypeScript (.js, .ts, .jsx, .tsx)
- C/C++ (.c, .cpp, .h, .hpp)
- Java (.java)
- Go (.go)
- Rust (.rs)
- Ruby (.rb)
- PHP (.php)
- Shell scripts (.sh, .bash)
- And many more...

## Advanced Usage

### Integration with IDEs

```python
from main import load_model, analyze_code

# Load model once
model_path = "~/.cache/gemma_analyzer/gemma-3-270m-it-Q4_K_M.gguf"
llm = load_model(model_path)

# Analyze multiple files
code = open("myfile.py").read()
result = analyze_code(llm, code, "myfile.py", "Explain this code")
print(result)
```

### Batch Processing

```bash
# Analyze all Python files in a directory
for file in *.py; do
    echo "Analyzing $file..."
    python main.py "$file" -q "Find code smells" > "reviews/${file%.py}_review.txt"
done
```

## Troubleshooting

### Issue: Model download fails
**Solution**: Check internet connection and try again. The model is downloaded from HuggingFace.

### Issue: Out of memory error
**Solution**: Use `--no-gpu` flag to run in CPU mode, which uses less memory.

### Issue: Slow performance
**Solution**: 
1. Ensure you have llama-cpp-python compiled with acceleration
2. Consider using GPU mode (install torch)
3. Reduce context size in the code if needed

### Issue: Import errors on Windows
**Solution**: Install Visual C++ Redistributable:
```bash
# Install with conda (recommended for Windows)
conda install -c conda-forge llama-cpp-python
```

## Performance Tips

1. **GPU Acceleration**: Install PyTorch for automatic GPU detection
2. **CPU Optimization**: The tool automatically uses all available CPU cores
3. **Memory Usage**: The model uses ~1-2GB RAM in normal operation
4. **First Run**: Initial model download happens only once

## Privacy & Security

- ✅ **100% Offline**: No internet connection required after model download
- ✅ **No Telemetry**: No data is sent anywhere
- ✅ **Local Processing**: All analysis happens on your machine
- ✅ **Open Source**: Fully auditable code

## Contributing

Contributions are welcome! Please feel free to submit pull requests.

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Google DeepMind for the Gemma 3 model
- LM Studio Community for GGUF quantization
- llama.cpp team for the inference engine

## Changelog

### v1.0.0 (2024)
- Initial release
- Basic code analysis functionality
- CLI interface
- Cross-platform support
- GPU/CPU auto-detection

---

Made with ❤️ for developers who love clean, analyzed code!