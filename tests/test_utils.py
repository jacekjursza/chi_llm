"""
Tests for chi_llm.utils module.
"""

import pytest
import json
import yaml
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from chi_llm.utils import (
    load_config,
    truncate_text,
    format_chat_history,
    count_tokens_approx,
    validate_response,
    clean_response,
    split_into_chunks,
    merge_responses,
    get_model_info,
    estimate_processing_time,
    is_code
)


class TestConfigLoading:
    """Test configuration loading functions."""
    
    def test_load_default_config(self):
        """Test loading default configuration."""
        config = load_config()
        
        assert "model" in config
        assert config["model"]["temperature"] == 0.7
        assert config["model"]["max_tokens"] == 4096
        assert config["verbose"] == False
    
    def test_load_yaml_config(self):
        """Test loading YAML configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"model": {"temperature": 0.5}, "verbose": True}, f)
            f.flush()
            
            config = load_config(f.name)
            
            assert config["model"]["temperature"] == 0.5
            assert config["verbose"] == True
            
            Path(f.name).unlink()
    
    def test_load_json_config(self):
        """Test loading JSON configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"model": {"temperature": 0.3}}, f)
            f.flush()
            
            config = load_config(f.name)
            
            assert config["model"]["temperature"] == 0.3
            
            Path(f.name).unlink()
    
    @patch.dict('os.environ', {'CHI_LLM_CONFIG': '{"model": {"temperature": 0.9}}'})
    def test_load_config_from_env(self):
        """Test loading configuration from environment variable."""
        config = load_config()
        assert config["model"]["temperature"] == 0.9


class TestTextUtilities:
    """Test text manipulation utilities."""
    
    def test_truncate_text(self):
        """Test text truncation."""
        text = "Hello " * 5000
        truncated = truncate_text(text, max_length=100)
        
        assert len(truncated) <= 100
        assert truncated.endswith("... (truncated)")
    
    def test_truncate_text_no_truncation(self):
        """Test text that doesn't need truncation."""
        text = "Short text"
        result = truncate_text(text, max_length=100)
        assert result == text
    
    def test_format_chat_history(self):
        """Test chat history formatting."""
        history = [
            {"user": "Hello", "assistant": "Hi there!"},
            {"user": "How are you?", "assistant": "I'm good!"}
        ]
        
        formatted = format_chat_history(history)
        
        assert "<start_of_turn>user" in formatted
        assert "Hello" in formatted
        assert "<start_of_turn>model" in formatted
        assert "Hi there!" in formatted
    
    def test_count_tokens_approx(self):
        """Test approximate token counting."""
        text = "This is a test string"
        count = count_tokens_approx(text)
        
        # Rough approximation: ~4 chars per token
        assert count == len(text) // 4
    
    def test_validate_response_valid(self):
        """Test response validation with valid response."""
        assert validate_response("Valid response") == True
        assert validate_response("A") == True
    
    def test_validate_response_invalid(self):
        """Test response validation with invalid responses."""
        assert validate_response("") == False
        assert validate_response("   ") == False
        assert validate_response("error: something failed") == False
        assert validate_response("Failed to generate") == False
    
    def test_clean_response(self):
        """Test response cleaning."""
        response = "Hello\n\n\n\nWorld<end_of_turn><eos>[END]"
        cleaned = clean_response(response)
        
        assert cleaned == "Hello\n\nWorld"
        assert "<end_of_turn>" not in cleaned
        assert "<eos>" not in cleaned
        assert "[END]" not in cleaned
    
    def test_split_into_chunks(self):
        """Test text splitting into chunks."""
        text = "A" * 50000
        chunks = split_into_chunks(text, chunk_size=15000, overlap=500)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 15000 for chunk in chunks)
    
    def test_split_into_chunks_small_text(self):
        """Test splitting small text."""
        text = "Small text"
        chunks = split_into_chunks(text, chunk_size=1000)
        
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_merge_responses_single(self):
        """Test merging single response."""
        responses = ["Single response"]
        merged = merge_responses(responses)
        assert merged == "Single response"
    
    def test_merge_responses_multiple(self):
        """Test merging multiple responses."""
        responses = ["First", "Second", "Third"]
        merged = merge_responses(responses)
        
        assert "First" in merged
        assert "Second" in merged
        assert "Third" in merged
        assert "---" in merged
    
    def test_merge_responses_summarize(self):
        """Test merging responses for summarization task."""
        responses = ["Summary 1", "Summary 2"]
        merged = merge_responses(responses, task="summarize")
        
        assert "Summary 1" in merged
        assert "Summary 2" in merged


class TestModelInfo:
    """Test model information functions."""
    
    def test_get_model_info(self):
        """Test getting model information."""
        info = get_model_info()
        
        assert info["name"] == "Gemma 3 270M"
        assert info["parameters"] == "270M"
        assert info["context_window"] == 8192
        assert info["quantization"] == "Q4_K_M"
        assert info["size_mb"] == 200
    
    def test_estimate_processing_time(self):
        """Test processing time estimation."""
        # Short text
        time_short = estimate_processing_time(100)
        assert time_short >= 1.0
        
        # Long text
        time_long = estimate_processing_time(5000)
        assert time_long > time_short


class TestCodeDetection:
    """Test code detection utility."""
    
    def test_is_code_python(self):
        """Test Python code detection."""
        python_code = """
def hello():
    return "world"

class MyClass:
    pass
"""
        assert is_code(python_code) == True
    
    def test_is_code_javascript(self):
        """Test JavaScript code detection."""
        js_code = """
function hello() {
    const x = 10;
    let y = 20;
    return x + y;
}
"""
        assert is_code(js_code) == True
    
    def test_is_code_sql(self):
        """Test SQL code detection."""
        sql_code = """
SELECT * FROM users
WHERE age > 18
ORDER BY name;
"""
        assert is_code(sql_code) == True
    
    def test_is_code_plain_text(self):
        """Test plain text (not code)."""
        plain_text = """
This is just a regular paragraph of text.
It doesn't contain any code patterns.
Just normal sentences.
"""
        assert is_code(plain_text) == False
    
    def test_is_code_mixed(self):
        """Test mixed content."""
        mixed = """
Here is some code:
def example():
    pass
And some more text.
"""
        # Should detect as code due to def statement
        assert is_code(mixed) == True