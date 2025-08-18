# Testing Guide for chi_llm

## Overview

chi_llm uses pytest for testing with comprehensive coverage requirements. All tests use mocking to avoid downloading the actual model during testing.

## Quick Start

### Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=chi_llm

# Run specific test file
pytest tests/test_core.py

# Run specific test
pytest tests/test_core.py::TestMicroLLM::test_generate

# Run tests with verbose output
pytest -v

# Run only fast tests (skip slow/integration tests)
pytest -m "not slow"
```

## Test Structure

```
tests/
├── __init__.py
├── test_core.py          # Tests for MicroLLM class
├── test_utils.py         # Tests for utility functions
├── test_prompts.py       # Tests for prompt templates
└── test_compatibility.py # Tests for backward compatibility
```

## Test Categories

Tests are marked with categories for selective execution:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow tests
- `@pytest.mark.mock` - Tests using mocks

## Coverage Requirements

- Minimum coverage: 80%
- Coverage reports are generated in:
  - Terminal: Shows missing lines
  - HTML: `htmlcov/index.html`
  - XML: `coverage.xml`

## Writing Tests

### Basic Test Example

```python
def test_example():
    """Test description."""
    # Arrange
    expected = "result"
    
    # Act
    result = function_under_test()
    
    # Assert
    assert result == expected
```

### Mocking the Model

```python
from unittest.mock import patch, Mock

@patch('chi_llm.core.Llama')
@patch('chi_llm.core.hf_hub_download')
def test_with_mock(mock_download, mock_llama):
    """Test with mocked model."""
    # Setup mocks
    mock_download.return_value = "/fake/path/model.gguf"
    mock_llama_instance = Mock()
    mock_llama_instance.return_value = {
        'choices': [{'text': 'Generated text'}]
    }
    mock_llama.return_value = mock_llama_instance
    
    # Test
    llm = MicroLLM()
    result = llm.generate("Test")
    
    # Verify
    assert result == "Generated text"
```

## Continuous Integration

Tests run automatically on GitHub Actions for:
- Every push to master/main/develop
- Every pull request
- Daily at 2 AM UTC

### Test Matrix

- **Operating Systems**: Ubuntu, Windows, macOS
- **Python Versions**: 3.8, 3.9, 3.10, 3.11, 3.12

## Local Development

### Pre-commit Checks

Run these before committing:

```bash
# Format code
black chi_llm tests

# Sort imports
isort chi_llm tests

# Check code style
flake8 chi_llm tests

# Type checking
mypy chi_llm

# Run tests
pytest
```

### Test Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=chi_llm --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Debugging Tests

```bash
# Run with debugging output
pytest -vv -s

# Run with pdb on failure
pytest --pdb

# Run with pdb on first failure
pytest -x --pdb

# Show local variables on failure
pytest -l
```

## Testing Best Practices

1. **Use Mocks**: Always mock external dependencies (model downloads, file I/O)
2. **Test Isolation**: Each test should be independent
3. **Clear Names**: Test names should describe what they test
4. **Arrange-Act-Assert**: Follow the AAA pattern
5. **Edge Cases**: Test error conditions and edge cases
6. **Documentation**: Add docstrings to complex tests

## Common Test Patterns

### Testing Exceptions

```python
def test_raises_exception():
    """Test that function raises expected exception."""
    with pytest.raises(ValueError) as exc_info:
        function_that_should_fail()
    
    assert "Expected error message" in str(exc_info.value)
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("test1", "result1"),
    ("test2", "result2"),
    ("test3", "result3"),
])
def test_multiple_cases(input, expected):
    """Test multiple input/output combinations."""
    assert function(input) == expected
```

### Fixtures

```python
@pytest.fixture
def sample_llm():
    """Create a sample LLM instance for testing."""
    with patch('chi_llm.core.Llama'):
        llm = MicroLLM()
        yield llm
```

## Troubleshooting

### Issue: Tests fail with import errors

```bash
# Install package in development mode
pip install -e .
```

### Issue: Coverage is too low

```bash
# See which lines are not covered
pytest --cov=chi_llm --cov-report=term-missing
```

### Issue: Tests hang

```bash
# Run with timeout
pytest --timeout=30
```

## Contributing

When adding new features:

1. Write tests first (TDD)
2. Ensure all tests pass
3. Maintain or improve coverage
4. Add integration tests for complex features
5. Update this documentation if needed

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)