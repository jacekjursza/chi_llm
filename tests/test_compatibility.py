"""
Tests for backward compatibility with CodeAnalyzer API.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
from pathlib import Path

from chi_llm import CodeAnalyzer, load_model, analyze_code, DEFAULT_QUESTION
from chi_llm.analyzer import MODEL_DIR, MODEL_FILE, MODEL_REPO


class TestCodeAnalyzer:
    """Test CodeAnalyzer backward compatibility."""
    
    @patch('chi_llm.core.Llama')
    @patch('chi_llm.core.hf_hub_download')
    def test_code_analyzer_initialization(self, mock_download, mock_llama):
        """Test CodeAnalyzer can be initialized."""
        # Setup
        mock_download.return_value = "/fake/path/model.gguf"
        mock_llama_instance = Mock()
        mock_llama.return_value = mock_llama_instance
        
        # Test
        analyzer = CodeAnalyzer()
        
        # Verify
        assert analyzer is not None
        assert hasattr(analyzer, 'analyze')
        assert hasattr(analyzer, 'analyze_file')
    
    @patch('chi_llm.core.Llama')
    @patch('chi_llm.core.hf_hub_download')
    def test_code_analyzer_analyze(self, mock_download, mock_llama):
        """Test CodeAnalyzer.analyze method."""
        # Setup
        mock_download.return_value = "/fake/path/model.gguf"
        mock_llama_instance = Mock()
        mock_llama_instance.return_value = {
            'choices': [{'text': 'Code analysis result'}]
        }
        mock_llama.return_value = mock_llama_instance
        
        # Test
        analyzer = CodeAnalyzer()
        code = "def hello(): return 'world'"
        result = analyzer.analyze(code)
        
        # Verify
        assert result == "Code analysis result"
    
    @patch('chi_llm.core.Llama')
    @patch('chi_llm.core.hf_hub_download')
    def test_code_analyzer_with_question(self, mock_download, mock_llama):
        """Test CodeAnalyzer with custom question."""
        # Setup
        mock_download.return_value = "/fake/path/model.gguf"
        mock_llama_instance = Mock()
        mock_llama_instance.return_value = {
            'choices': [{'text': 'Custom analysis'}]
        }
        mock_llama.return_value = mock_llama_instance
        
        # Test
        analyzer = CodeAnalyzer()
        code = "def factorial(n): return 1 if n == 0 else n * factorial(n-1)"
        result = analyzer.analyze(code, question="What is the time complexity?")
        
        # Verify
        assert result == "Custom analysis"
    
    @patch('chi_llm.core.Llama')
    @patch('chi_llm.core.hf_hub_download')
    def test_code_analyzer_analyze_file(self, mock_download, mock_llama):
        """Test CodeAnalyzer.analyze_file method."""
        # Setup
        mock_download.return_value = "/fake/path/model.gguf"
        mock_llama_instance = Mock()
        mock_llama_instance.return_value = {
            'choices': [{'text': 'File analysis'}]
        }
        mock_llama.return_value = mock_llama_instance
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test(): pass")
            f.flush()
            
            # Test
            analyzer = CodeAnalyzer()
            result = analyzer.analyze_file(f.name)
            
            # Verify
            assert result == "File analysis"
            
            # Cleanup
            Path(f.name).unlink()
    
    @patch('chi_llm.core.Llama')
    @patch('chi_llm.core.hf_hub_download')
    def test_code_analyzer_custom_model_path(self, mock_download, mock_llama):
        """Test CodeAnalyzer with custom model path."""
        # Setup
        mock_llama_instance = Mock()
        mock_llama.return_value = mock_llama_instance
        
        # Test
        custom_path = "/custom/model.gguf"
        analyzer = CodeAnalyzer(model_path=custom_path)
        
        # Verify
        assert analyzer.model_path == custom_path
    
    def test_code_analyzer_file_not_found(self):
        """Test CodeAnalyzer with non-existent file."""
        with patch('chi_llm.core.Llama'), patch('chi_llm.core.hf_hub_download'):
            analyzer = CodeAnalyzer()
            
            with pytest.raises(FileNotFoundError):
                analyzer.analyze_file("/non/existent/file.py")
    
    def test_code_analyzer_not_a_file(self):
        """Test CodeAnalyzer with directory instead of file."""
        with patch('chi_llm.core.Llama'), patch('chi_llm.core.hf_hub_download'):
            analyzer = CodeAnalyzer()
            
            with tempfile.TemporaryDirectory() as tmpdir:
                with pytest.raises(ValueError) as exc_info:
                    analyzer.analyze_file(tmpdir)
                assert "Not a file" in str(exc_info.value)


class TestLegacyFunctions:
    """Test legacy convenience functions."""
    
    @patch('chi_llm.analyzer.CodeAnalyzer')
    def test_load_model(self, mock_analyzer_class):
        """Test load_model function."""
        # Setup
        mock_instance = Mock()
        mock_instance.llm = Mock()
        mock_analyzer_class.return_value = mock_instance
        
        # Test
        model_path = "/path/to/model.gguf"
        llm = load_model(model_path)
        
        # Verify
        mock_analyzer_class.assert_called_once_with(model_path=model_path)
        assert llm == mock_instance.llm
    
    @patch('chi_llm.core.MicroLLM')
    def test_analyze_code(self, mock_micro_llm_class):
        """Test analyze_code function."""
        # Setup
        mock_instance = Mock()
        mock_instance.analyze.return_value = "Analysis result"
        mock_micro_llm_class.return_value = mock_instance
        
        mock_llm = Mock()
        
        # Test
        result = analyze_code(
            mock_llm,
            "def test(): pass",
            "test.py",
            "Explain this code"
        )
        
        # Verify
        assert result == "Analysis result"
        mock_instance.analyze.assert_called_once_with(
            "def test(): pass",
            "Explain this code"
        )


class TestConstants:
    """Test that constants are properly exported."""
    
    def test_default_question(self):
        """Test DEFAULT_QUESTION is available."""
        assert DEFAULT_QUESTION is not None
        assert isinstance(DEFAULT_QUESTION, str)
        assert len(DEFAULT_QUESTION) > 0
    
    def test_model_constants(self):
        """Test model-related constants."""
        assert MODEL_DIR is not None
        assert MODEL_FILE is not None
        assert MODEL_REPO is not None
        
        assert MODEL_FILE == "gemma-3-270m-it-Q4_K_M.gguf"
        assert MODEL_REPO == "lmstudio-community/gemma-3-270m-it-GGUF"


class TestImports:
    """Test that old imports still work."""
    
    def test_import_code_analyzer(self):
        """Test importing CodeAnalyzer."""
        from chi_llm import CodeAnalyzer
        assert CodeAnalyzer is not None
    
    def test_import_load_model(self):
        """Test importing load_model."""
        from chi_llm import load_model
        assert load_model is not None
    
    def test_import_analyze_code(self):
        """Test importing analyze_code."""
        from chi_llm import analyze_code
        assert analyze_code is not None
    
    def test_import_constants(self):
        """Test importing constants."""
        from chi_llm import DEFAULT_QUESTION, MODEL_DIR, MODEL_FILE, MODEL_REPO
        assert all([DEFAULT_QUESTION, MODEL_DIR, MODEL_FILE, MODEL_REPO])
    
    def test_old_style_import(self):
        """Test old-style import from analyzer module."""
        from chi_llm.analyzer import CodeAnalyzer, load_model, analyze_code
        assert all([CodeAnalyzer, load_model, analyze_code])