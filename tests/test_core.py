"""
Tests for chi_llm.core module.
"""

import pytest
from unittest.mock import Mock, patch
import tempfile
from pathlib import Path

from chi_llm.core import MicroLLM, quick_llm, MODEL_FILE, MODEL_REPO


class TestMicroLLM:
    """Test MicroLLM class."""

    @patch("chi_llm.core.Llama")
    @patch("chi_llm.core.hf_hub_download")
    def test_initialization(self, mock_download, mock_llama):
        """Test MicroLLM initialization."""
        # Setup mocks
        mock_download.return_value = "/fake/path/model.gguf"
        mock_llama_instance = Mock()
        mock_llama.return_value = mock_llama_instance

        # Create instance
        llm = MicroLLM()

        # Verify
        assert llm.temperature == 0.7
        assert llm.max_tokens == 4096
        assert llm.llm is not None

    @patch("chi_llm.core.Llama")
    @patch("chi_llm.core.MODEL_DIR")
    def test_model_caching(self, mock_model_dir, mock_llama):
        """Test that model is cached and reused."""
        # Setup
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_model_dir.__truediv__ = lambda self, x: Path(tmpdir) / x
            model_path = Path(tmpdir) / MODEL_FILE
            model_path.touch()  # Create fake model file

            mock_llama_instance = Mock()
            mock_llama.return_value = mock_llama_instance

            # Create multiple instances
            llm1 = MicroLLM()
            llm2 = MicroLLM()

            # Model should be loaded only once (singleton)
            assert mock_llama.call_count == 1

    @patch("chi_llm.core.Llama")
    @patch("chi_llm.core.hf_hub_download")
    def test_generate(self, mock_download, mock_llama):
        """Test text generation."""
        # Setup
        mock_download.return_value = "/fake/path/model.gguf"
        mock_llama_instance = Mock()
        mock_llama_instance.return_value = {"choices": [{"text": "Generated text"}]}
        mock_llama.return_value = mock_llama_instance

        # Test
        llm = MicroLLM()
        result = llm.generate("Test prompt")

        # Verify
        assert result == "Generated text"
        mock_llama_instance.assert_called_once()

    @patch("chi_llm.core.Llama")
    @patch("chi_llm.core.hf_hub_download")
    def test_chat(self, mock_download, mock_llama):
        """Test chat functionality."""
        # Setup
        mock_download.return_value = "/fake/path/model.gguf"
        mock_llama_instance = Mock()
        mock_llama_instance.return_value = {"choices": [{"text": "Chat response"}]}
        mock_llama.return_value = mock_llama_instance

        # Test without history
        llm = MicroLLM()
        result = llm.chat("Hello")
        assert result == "Chat response"

        # Test with history
        history = [
            {"user": "Hi", "assistant": "Hello!"},
            {"user": "How are you?", "assistant": "I'm good!"},
        ]
        result = llm.chat("What's up?", history=history)
        assert result == "Chat response"

    @patch("chi_llm.core.Llama")
    @patch("chi_llm.core.hf_hub_download")
    def test_complete(self, mock_download, mock_llama):
        """Test text completion."""
        # Setup
        mock_download.return_value = "/fake/path/model.gguf"
        mock_llama_instance = Mock()
        mock_llama_instance.return_value = {
            "choices": [{"text": "jumps over the lazy dog"}]
        }
        mock_llama.return_value = mock_llama_instance

        # Test
        llm = MicroLLM()
        result = llm.complete("The quick brown fox")

        # Verify
        assert result == "jumps over the lazy dog"

    @patch("chi_llm.core.Llama")
    @patch("chi_llm.core.hf_hub_download")
    def test_ask(self, mock_download, mock_llama):
        """Test question answering."""
        # Setup
        mock_download.return_value = "/fake/path/model.gguf"
        mock_llama_instance = Mock()
        mock_llama_instance.return_value = {"choices": [{"text": "Answer to question"}]}
        mock_llama.return_value = mock_llama_instance

        # Test without context
        llm = MicroLLM()
        result = llm.ask("What is Python?")
        assert result == "Answer to question"

        # Test with context
        context = "Python is a programming language."
        result = llm.ask("What is it?", context=context)
        assert result == "Answer to question"

    @patch("chi_llm.core.Llama")
    @patch("chi_llm.core.hf_hub_download")
    def test_analyze(self, mock_download, mock_llama):
        """Test code analysis (backward compatibility)."""
        # Setup
        mock_download.return_value = "/fake/path/model.gguf"
        mock_llama_instance = Mock()
        mock_llama_instance.return_value = {"choices": [{"text": "Code analysis"}]}
        mock_llama.return_value = mock_llama_instance

        # Test
        llm = MicroLLM()
        code = "def hello(): return 'world'"
        result = llm.analyze(code)

        # Verify
        assert result == "Code analysis"

    @patch("chi_llm.core.Llama")
    @patch("chi_llm.core.hf_hub_download")
    def test_extract(self, mock_download, mock_llama):
        """Test data extraction."""
        # Setup
        mock_download.return_value = "/fake/path/model.gguf"
        mock_llama_instance = Mock()
        mock_llama_instance.return_value = {
            "choices": [{"text": '{"name": "John", "age": 30}'}]
        }
        mock_llama.return_value = mock_llama_instance

        # Test
        llm = MicroLLM()
        result = llm.extract("John is 30 years old", format="json")

        # Verify
        assert result == '{"name": "John", "age": 30}'

    @patch("chi_llm.core.Llama")
    @patch("chi_llm.core.hf_hub_download")
    def test_summarize(self, mock_download, mock_llama):
        """Test text summarization."""
        # Setup
        mock_download.return_value = "/fake/path/model.gguf"
        mock_llama_instance = Mock()
        mock_llama_instance.return_value = {"choices": [{"text": "Summary of text."}]}
        mock_llama.return_value = mock_llama_instance

        # Test
        llm = MicroLLM()
        long_text = "This is a very long text " * 50
        result = llm.summarize(long_text, max_sentences=2)

        # Verify
        assert result == "Summary of text."

    @patch("chi_llm.core.Llama")
    @patch("chi_llm.core.hf_hub_download")
    def test_translate(self, mock_download, mock_llama):
        """Test translation."""
        # Setup
        mock_download.return_value = "/fake/path/model.gguf"
        mock_llama_instance = Mock()
        mock_llama_instance.return_value = {"choices": [{"text": "Hello"}]}
        mock_llama.return_value = mock_llama_instance

        # Test
        llm = MicroLLM()
        result = llm.translate("Bonjour", target_language="English")

        # Verify
        assert result == "Hello"

    @patch("chi_llm.core.Llama")
    @patch("chi_llm.core.hf_hub_download")
    def test_classify(self, mock_download, mock_llama):
        """Test text classification."""
        # Setup
        mock_download.return_value = "/fake/path/model.gguf"
        mock_llama_instance = Mock()
        mock_llama_instance.return_value = {"choices": [{"text": "positive"}]}
        mock_llama.return_value = mock_llama_instance

        # Test
        llm = MicroLLM()
        result = llm.classify(
            "I love this!", categories=["positive", "negative", "neutral"]
        )

        # Verify
        assert result == "positive"

    @patch("chi_llm.core.Llama")
    @patch("chi_llm.core.hf_hub_download")
    def test_callable(self, mock_download, mock_llama):
        """Test that MicroLLM is callable."""
        # Setup
        mock_download.return_value = "/fake/path/model.gguf"
        mock_llama_instance = Mock()
        mock_llama_instance.return_value = {"choices": [{"text": "Response"}]}
        mock_llama.return_value = mock_llama_instance

        # Test
        llm = MicroLLM()
        result = llm("Test prompt")

        # Verify
        assert result == "Response"

    @patch("chi_llm.core.Llama")
    @patch("chi_llm.core.hf_hub_download")
    def test_custom_parameters(self, mock_download, mock_llama):
        """Test custom initialization parameters."""
        # Setup
        mock_download.return_value = "/fake/path/model.gguf"
        mock_llama_instance = Mock()
        mock_llama.return_value = mock_llama_instance

        # Test
        llm = MicroLLM(temperature=0.3, max_tokens=512, verbose=True)

        # Verify
        assert llm.temperature == 0.3
        assert llm.max_tokens == 512
        assert llm.verbose == True


class TestQuickLLM:
    """Test quick_llm function."""

    @patch("chi_llm.core.MicroLLM")
    def test_quick_llm(self, mock_micro_llm):
        """Test quick_llm convenience function."""
        # Setup
        mock_instance = Mock()
        mock_instance.generate.return_value = "Quick response"
        mock_micro_llm.return_value = mock_instance

        # Test
        result = quick_llm("Test prompt")

        # Verify
        assert result == "Quick response"
        mock_instance.generate.assert_called_once_with("Test prompt")

    @patch("chi_llm.core.MicroLLM")
    def test_quick_llm_with_kwargs(self, mock_micro_llm):
        """Test quick_llm with additional parameters."""
        # Setup
        mock_instance = Mock()
        mock_instance.generate.return_value = "Custom response"
        mock_micro_llm.return_value = mock_instance

        # Test
        result = quick_llm("Test", temperature=0.1, max_tokens=100)

        # Verify
        assert result == "Custom response"
        mock_instance.generate.assert_called_once_with(
            "Test", temperature=0.1, max_tokens=100
        )


class TestModelManagement:
    """Test model download and management."""

    @patch("chi_llm.core.hf_hub_download")
    @patch("chi_llm.core.MODEL_DIR")
    def test_model_download(self, mock_model_dir, mock_download):
        """Test model download when not cached."""
        # Setup
        with tempfile.TemporaryDirectory() as tmpdir:
            # Make MODEL_DIR return the tempdir path
            mock_model_dir.__str__ = lambda self: tmpdir
            mock_model_dir.__truediv__ = lambda self, x: Path(tmpdir) / x
            mock_model_dir.mkdir = Mock()
            mock_download.return_value = str(Path(tmpdir) / MODEL_FILE)

            # Test
            from chi_llm.core import MicroLLM

            with patch("chi_llm.core.Llama"):
                llm = MicroLLM()

            # Verify download was called (without checking exact local_dir)
            assert mock_download.called
            call_args = mock_download.call_args
            assert call_args[1]["repo_id"] == MODEL_REPO
            assert call_args[1]["filename"] == MODEL_FILE
            assert call_args[1]["resume_download"] == True

    @patch("chi_llm.core.Llama")
    def test_model_loading_error(self, mock_llama):
        """Test error handling during model loading."""
        # Setup
        mock_llama.side_effect = Exception("Model loading failed")

        # Test
        with pytest.raises(RuntimeError) as exc_info:
            with patch("chi_llm.core.hf_hub_download"):
                llm = MicroLLM()

        # Verify
        assert "Failed to load model" in str(exc_info.value)

    @patch("chi_llm.core.hf_hub_download")
    def test_default_model_from_project_config(self, mock_download, tmp_path):
        """MicroLLM should honor default_model from per-project .chi_llm.json."""
        # Write a local project config selecting a specific model
        cfg_path = tmp_path / ".chi_llm.json"
        cfg_path.write_text('{"default_model": "qwen3-1.7b"}', encoding="utf-8")

        # Change CWD to the temp project directory
        import os
        from chi_llm.models import MODELS

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            # Prepare mocks
            mock_download.return_value = str(tmp_path / MODELS["qwen3-1.7b"].filename)
            with patch("chi_llm.core.Llama"):
                from chi_llm.core import MicroLLM

                _ = MicroLLM()  # should pick qwen3-1.7b via ModelManager

            assert mock_download.called
            args, kwargs = mock_download.call_args
            assert kwargs["repo_id"] == MODELS["qwen3-1.7b"].repo
            assert kwargs["filename"] == MODELS["qwen3-1.7b"].filename
        finally:
            os.chdir(old_cwd)

    @patch.dict("os.environ", {"CHI_LLM_MODEL": "qwen3-1.7b"})
    @patch("chi_llm.core.hf_hub_download")
    def test_default_model_from_env(self, mock_download):
        """MicroLLM should honor CHI_LLM_MODEL environment variable."""
        from chi_llm.models import MODELS

        mock_download.return_value = "/fake/path/model.gguf"
        with patch("chi_llm.core.Llama"):
            from chi_llm.core import MicroLLM

            _ = MicroLLM()

        assert mock_download.called
        args, kwargs = mock_download.call_args
        assert kwargs["repo_id"] == MODELS["qwen3-1.7b"].repo
        assert kwargs["filename"] == MODELS["qwen3-1.7b"].filename
