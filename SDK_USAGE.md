# chi_llm SDK Usage Guide

## Installation

### From GitHub (Private Repository)

```bash
# Install directly from GitHub
pip install git+https://github.com/jacekjursza/chi_llm.git

# Or add to requirements.txt
git+https://github.com/jacekjursza/chi_llm.git

# Or in setup.py
install_requires=[
    'chi-llm @ git+https://github.com/jacekjursza/chi_llm.git',
    # other dependencies...
]
```

### For Development

```bash
# Clone and install in editable mode
git clone https://github.com/jacekjursza/chi_llm.git
cd chi_llm
pip install -e .
```

## Quick Start

### Basic Usage

```python
from chi_llm import CodeAnalyzer

# Initialize analyzer (downloads model on first use)
analyzer = CodeAnalyzer()

# Analyze code snippet
code = """
def hello_world():
    print("Hello, World!")
"""

result = analyzer.analyze(code)
print(result)
```

### Analyzing Files

```python
from chi_llm import CodeAnalyzer

analyzer = CodeAnalyzer()

# Analyze a file directly
result = analyzer.analyze_file("script.py")
print(result)

# With custom question
result = analyzer.analyze_file(
    "script.py", 
    question="Find security vulnerabilities"
)
print(result)
```

### Custom Questions

```python
from chi_llm import CodeAnalyzer

analyzer = CodeAnalyzer()

code = """
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n-1)
"""

# Ask specific questions
questions = [
    "What is the time complexity?",
    "Could this cause a stack overflow?",
    "Suggest optimizations",
    "Write unit tests for this function"
]

for question in questions:
    result = analyzer.analyze(code, question=question)
    print(f"Q: {question}")
    print(f"A: {result}\n")
```

## Advanced Usage

### Integration in CI/CD Pipeline

```python
# code_review.py
import sys
from chi_llm import CodeAnalyzer

def review_changed_files(files):
    analyzer = CodeAnalyzer()
    issues_found = False
    
    for file_path in files:
        if file_path.endswith(('.py', '.js', '.ts')):
            result = analyzer.analyze_file(
                file_path,
                question="Find bugs, security issues, and code smells"
            )
            
            if "bug" in result.lower() or "issue" in result.lower():
                print(f"⚠️  Issues found in {file_path}:")
                print(result)
                issues_found = True
    
    return 1 if issues_found else 0

if __name__ == "__main__":
    # Get changed files from git or CI system
    changed_files = sys.argv[1:]
    exit_code = review_changed_files(changed_files)
    sys.exit(exit_code)
```

### Batch Processing

```python
from pathlib import Path
from chi_llm import CodeAnalyzer
import json

def analyze_project(project_dir, output_file="analysis_report.json"):
    analyzer = CodeAnalyzer()
    results = {}
    
    # Find all Python files
    for py_file in Path(project_dir).rglob("*.py"):
        print(f"Analyzing {py_file}...")
        
        results[str(py_file)] = {
            "overview": analyzer.analyze_file(py_file),
            "security": analyzer.analyze_file(
                py_file, 
                question="Check for security vulnerabilities"
            ),
            "performance": analyzer.analyze_file(
                py_file,
                question="Identify performance issues"
            )
        }
    
    # Save results
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Analysis saved to {output_file}")
    return results

# Usage
analyze_project("./src")
```

### Custom Model Path

```python
from chi_llm import CodeAnalyzer

# Use a custom model file
analyzer = CodeAnalyzer(
    model_path="/path/to/custom/model.gguf",
    use_gpu=True  # Enable GPU if available
)
```

### Building Documentation Generator

```python
from chi_llm import CodeAnalyzer

class DocGenerator:
    def __init__(self):
        self.analyzer = CodeAnalyzer()
    
    def generate_module_docs(self, module_path):
        """Generate comprehensive documentation for a Python module."""
        
        sections = []
        
        # Module overview
        overview = self.analyzer.analyze_file(
            module_path,
            question="Provide a comprehensive overview of this module"
        )
        sections.append(f"# Module Documentation\n\n## Overview\n{overview}")
        
        # Functions and classes
        api_docs = self.analyzer.analyze_file(
            module_path,
            question="Document all functions and classes with parameters and return types"
        )
        sections.append(f"## API Reference\n{api_docs}")
        
        # Usage examples
        examples = self.analyzer.analyze_file(
            module_path,
            question="Generate usage examples for the main functions"
        )
        sections.append(f"## Examples\n{examples}")
        
        # Best practices
        practices = self.analyzer.analyze_file(
            module_path,
            question="Suggest best practices for using this code"
        )
        sections.append(f"## Best Practices\n{practices}")
        
        return "\n\n".join(sections)

# Usage
generator = DocGenerator()
docs = generator.generate_module_docs("my_module.py")
print(docs)
```

## API Reference

### CodeAnalyzer Class

```python
class CodeAnalyzer:
    def __init__(self, model_path: Optional[str] = None, use_gpu: bool = True):
        """
        Initialize the CodeAnalyzer.
        
        Args:
            model_path: Optional path to a custom model file
            use_gpu: Whether to use GPU acceleration if available
        """
    
    def analyze(self, code: str, question: Optional[str] = None, 
                filename: Optional[str] = None) -> str:
        """
        Analyze code using the Gemma model.
        
        Args:
            code: The code to analyze
            question: Optional specific question about the code
            filename: Optional filename for context
            
        Returns:
            Analysis result as string
        """
    
    def analyze_file(self, file_path: str, question: Optional[str] = None) -> str:
        """
        Analyze a code file.
        
        Args:
            file_path: Path to the file to analyze
            question: Optional specific question about the code
            
        Returns:
            Analysis result as string
        """
```

### Constants

```python
from chi_llm import (
    DEFAULT_QUESTION,  # Default analysis question
    MODEL_REPO,        # HuggingFace model repository
    MODEL_FILE,        # Model filename
    MODEL_DIR          # Local cache directory
)
```

## Troubleshooting

### Model Download Issues

The model is automatically downloaded on first use (~200MB). If download fails:

```python
# Manually specify cache directory
import os
os.environ['HF_HOME'] = '/custom/cache/path'

from chi_llm import CodeAnalyzer
analyzer = CodeAnalyzer()
```

### Memory Issues

For large files or limited memory:

```python
# The analyzer automatically truncates large files
# Maximum analyzed content: 20,000 characters
# Maximum file read: 100KB

# For very limited memory, ensure CPU mode:
analyzer = CodeAnalyzer(use_gpu=False)
```

### Import Errors

```bash
# Ensure all dependencies are installed
pip install llama-cpp-python huggingface-hub

# For GPU support (optional)
pip install torch
```

## Performance Tips

1. **Reuse analyzer instances** - Model loading is expensive:
   ```python
   analyzer = CodeAnalyzer()  # Load once
   for file in files:
       result = analyzer.analyze_file(file)  # Reuse
   ```

2. **Batch similar questions** - Group related analyses together

3. **Use specific questions** - More focused questions yield better results

4. **Consider file size** - Large files are automatically truncated

## Examples Directory

See the `examples/` directory for complete working examples:
- `basic_usage.py` - Simple usage examples
- `integration_example.py` - Integration patterns for larger applications

## Support

For issues or questions:
- GitHub Issues: https://github.com/jacekjursza/chi_llm/issues
- Model: Gemma 3 270M (Google DeepMind)