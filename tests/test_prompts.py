"""
Tests for chi_llm.prompts module.
"""

import pytest
from chi_llm.prompts import PromptTemplates, code_prompt, data_prompt


class TestPromptTemplates:
    """Test PromptTemplates class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.templates = PromptTemplates()
        self.sample_code = "def add(a, b): return a + b"
    
    def test_code_review(self):
        """Test code review prompt generation."""
        prompt = self.templates.code_review(self.sample_code)
        
        assert "Review" in prompt
        assert "bugs" in prompt.lower()
        assert "performance" in prompt.lower()
        assert self.sample_code in prompt
    
    def test_code_review_with_language(self):
        """Test code review with language specification."""
        prompt = self.templates.code_review(self.sample_code, language="Python")
        
        assert "Python" in prompt
        assert self.sample_code in prompt
    
    def test_explain_code(self):
        """Test code explanation prompt."""
        prompt = self.templates.explain_code(self.sample_code)
        
        assert "Explain" in prompt
        assert self.sample_code in prompt
    
    def test_fix_error(self):
        """Test error fix prompt."""
        error = "NameError: name 'x' is not defined"
        prompt = self.templates.fix_error(self.sample_code, error)
        
        assert self.sample_code in prompt
        assert error in prompt
        assert "fix" in prompt.lower()
    
    def test_write_tests(self):
        """Test unit test generation prompt."""
        prompt = self.templates.write_tests(self.sample_code)
        
        assert "test" in prompt.lower()
        assert "pytest" in prompt
        assert self.sample_code in prompt
    
    def test_write_tests_custom_framework(self):
        """Test unit test generation with custom framework."""
        prompt = self.templates.write_tests(self.sample_code, framework="unittest")
        
        assert "unittest" in prompt
        assert self.sample_code in prompt
    
    def test_optimize_code(self):
        """Test code optimization prompt."""
        prompt = self.templates.optimize_code(self.sample_code)
        
        assert "Optimize" in prompt
        assert "performance" in prompt.lower()
        assert self.sample_code in prompt
    
    def test_document_code(self):
        """Test documentation generation prompt."""
        prompt = self.templates.document_code(self.sample_code)
        
        assert "documentation" in prompt.lower()
        assert "docstring" in prompt
        assert self.sample_code in prompt
    
    def test_document_code_custom_style(self):
        """Test documentation with custom style."""
        prompt = self.templates.document_code(self.sample_code, style="sphinx")
        
        assert "sphinx" in prompt
        assert self.sample_code in prompt
    
    def test_sql_from_description(self):
        """Test SQL generation prompt."""
        description = "Get all users older than 18"
        prompt = self.templates.sql_from_description(description)
        
        assert "SQL" in prompt
        assert description in prompt
    
    def test_regex_from_description(self):
        """Test regex generation prompt."""
        description = "Match email addresses"
        prompt = self.templates.regex_from_description(description)
        
        assert "regular expression" in prompt.lower() or "regex" in prompt.lower()
        assert description in prompt
    
    def test_json_from_text(self):
        """Test JSON extraction prompt."""
        text = "John is 30 years old"
        prompt = self.templates.json_from_text(text)
        
        assert "JSON" in prompt
        assert text in prompt
    
    def test_json_from_text_with_schema(self):
        """Test JSON extraction with schema."""
        text = "John is 30 years old"
        schema = {"name": "string", "age": "number"}
        prompt = self.templates.json_from_text(text, schema=schema)
        
        assert "JSON" in prompt
        assert text in prompt
        assert str(schema) in prompt
    
    def test_email_draft(self):
        """Test email drafting prompt."""
        context = "Declining a meeting invitation"
        prompt = self.templates.email_draft(context)
        
        assert "email" in prompt.lower()
        assert "professional" in prompt
        assert context in prompt
    
    def test_email_draft_custom_tone(self):
        """Test email drafting with custom tone."""
        context = "Thank you note"
        prompt = self.templates.email_draft(context, tone="friendly")
        
        assert "friendly" in prompt
        assert context in prompt
    
    def test_meeting_notes(self):
        """Test meeting notes generation."""
        transcript = "We discussed the Q4 goals..."
        prompt = self.templates.meeting_notes(transcript)
        
        assert "meeting notes" in prompt.lower()
        assert "Key Points" in prompt
        assert "Action Items" in prompt
        assert transcript in prompt
    
    def test_pros_cons(self):
        """Test pros and cons generation."""
        topic = "remote work"
        prompt = self.templates.pros_cons(topic)
        
        assert "pros" in prompt.lower()
        assert "cons" in prompt.lower()
        assert topic in prompt
    
    def test_explain_concept(self):
        """Test concept explanation."""
        concept = "machine learning"
        prompt = self.templates.explain_concept(concept)
        
        assert "Explain" in prompt
        assert concept in prompt
        assert "beginner" in prompt
    
    def test_explain_concept_custom_level(self):
        """Test concept explanation with custom level."""
        concept = "quantum computing"
        prompt = self.templates.explain_concept(concept, level="expert")
        
        assert concept in prompt
        assert "expert" in prompt
    
    def test_creative_ideas(self):
        """Test creative idea generation."""
        topic = "mobile app"
        prompt = self.templates.creative_ideas(topic)
        
        assert "ideas" in prompt.lower()
        assert topic in prompt
        assert "5" in prompt  # Default count
    
    def test_creative_ideas_custom_count(self):
        """Test creative ideas with custom count."""
        topic = "startup"
        prompt = self.templates.creative_ideas(topic, count=10)
        
        assert "10" in prompt
        assert topic in prompt
    
    def test_refactor_code(self):
        """Test code refactoring prompt."""
        prompt = self.templates.refactor_code(self.sample_code)
        
        assert "Refactor" in prompt
        assert "cleaner" in prompt
        assert self.sample_code in prompt
    
    def test_refactor_code_custom_goal(self):
        """Test refactoring with custom goal."""
        prompt = self.templates.refactor_code(self.sample_code, goal="more testable")
        
        assert "more testable" in prompt
        assert self.sample_code in prompt
    
    def test_api_from_description(self):
        """Test API design prompt."""
        description = "User management system"
        prompt = self.templates.api_from_description(description)
        
        assert "API" in prompt
        assert "RESTful" in prompt
        assert description in prompt
    
    def test_user_story(self):
        """Test user story generation."""
        feature = "password reset"
        prompt = self.templates.user_story(feature)
        
        assert "user story" in prompt.lower()
        assert feature in prompt
        assert "As a" in prompt
        assert "I want" in prompt
    
    def test_commit_message(self):
        """Test commit message generation."""
        changes = "Added login functionality"
        prompt = self.templates.commit_message(changes)
        
        assert "commit message" in prompt.lower()
        assert changes in prompt
    
    def test_cli_command(self):
        """Test CLI command generation."""
        task = "list all Python files"
        prompt = self.templates.cli_command(task)
        
        assert "command" in prompt.lower()
        assert task in prompt
    
    def test_cli_command_with_tool(self):
        """Test CLI command with specific tool."""
        task = "search for text"
        prompt = self.templates.cli_command(task, tool="grep")
        
        assert "grep" in prompt
        assert task in prompt


class TestPromptHelpers:
    """Test helper functions for prompts."""
    
    def test_code_prompt_explain(self):
        """Test code prompt for explanation."""
        code = "def test(): pass"
        prompt = code_prompt(code, task="explain")
        
        assert "Explain" in prompt
        assert code in prompt
    
    def test_code_prompt_review(self):
        """Test code prompt for review."""
        code = "def test(): pass"
        prompt = code_prompt(code, task="review")
        
        assert "Review" in prompt or "review" in prompt
        assert code in prompt
    
    def test_code_prompt_optimize(self):
        """Test code prompt for optimization."""
        code = "def test(): pass"
        prompt = code_prompt(code, task="optimize")
        
        assert "Optimize" in prompt or "optimize" in prompt
        assert code in prompt
    
    def test_code_prompt_document(self):
        """Test code prompt for documentation."""
        code = "def test(): pass"
        prompt = code_prompt(code, task="document")
        
        assert "document" in prompt.lower()
        assert code in prompt
    
    def test_code_prompt_test(self):
        """Test code prompt for test generation."""
        code = "def test(): pass"
        prompt = code_prompt(code, task="test")
        
        assert "test" in prompt.lower()
        assert code in prompt
    
    def test_code_prompt_refactor(self):
        """Test code prompt for refactoring."""
        code = "def test(): pass"
        prompt = code_prompt(code, task="refactor")
        
        assert "Refactor" in prompt or "refactor" in prompt
        assert code in prompt
    
    def test_code_prompt_unknown_task(self):
        """Test code prompt with unknown task."""
        code = "def test(): pass"
        prompt = code_prompt(code, task="unknown_task")
        
        assert "unknown_task" in prompt
        assert code in prompt
    
    def test_data_prompt_extract(self):
        """Test data prompt for extraction."""
        data = "Some data to process"
        prompt = data_prompt(data, task="extract")
        
        assert "Extract" in prompt or "extract" in prompt
        assert data in prompt
    
    def test_data_prompt_summarize(self):
        """Test data prompt for summarization."""
        data = "Long text to summarize"
        prompt = data_prompt(data, task="summarize")
        
        assert "Summarize" in prompt or "summarize" in prompt
        assert data in prompt
    
    def test_data_prompt_classify(self):
        """Test data prompt for classification."""
        data = "Text to classify"
        prompt = data_prompt(data, task="classify")
        
        assert "Classify" in prompt or "classify" in prompt
        assert data in prompt
    
    def test_data_prompt_unknown_task(self):
        """Test data prompt with unknown task."""
        data = "Some data"
        prompt = data_prompt(data, task="custom_task")
        
        assert "custom_task" in prompt
        assert data in prompt