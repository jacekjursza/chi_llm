"""
Pre-built prompt templates for common use cases.
"""

from typing import Dict, Optional


class PromptTemplates:
    """Collection of ready-to-use prompt templates."""

    @staticmethod
    def code_review(code: str, language: Optional[str] = None) -> str:
        """Generate a code review prompt."""
        lang = f" {language}" if language else ""
        return f"""Review this{lang} code for:
1. Potential bugs and issues
2. Performance optimizations
3. Best practices
4. Security concerns

Code:
{code}

Review:"""

    @staticmethod
    def explain_code(code: str) -> str:
        """Generate a code explanation prompt."""
        return f"""Explain what this code does in simple terms:

{code}

Explanation:"""

    @staticmethod
    def fix_error(code: str, error: str) -> str:
        """Generate a bug fix prompt."""
        return f"""This code has an error:

Code:
{code}

Error message:
{error}

Please explain the issue and provide a fix:"""

    @staticmethod
    def write_tests(code: str, framework: str = "pytest") -> str:
        """Generate unit tests for code."""
        return f"""Write comprehensive unit tests for this code using {framework}:

{code}

Tests:"""

    @staticmethod
    def optimize_code(code: str) -> str:
        """Generate optimization suggestions."""
        return f"""Optimize this code for better performance:

{code}

Optimized version with explanations:"""

    @staticmethod
    def document_code(code: str, style: str = "docstring") -> str:
        """Generate documentation for code."""
        return f"""Add comprehensive {style} documentation to this code:

{code}

Documented code:"""

    @staticmethod
    def sql_from_description(description: str) -> str:
        """Generate SQL from natural language."""
        return f"""Convert this description to SQL:

{description}

SQL query:"""

    @staticmethod
    def regex_from_description(description: str) -> str:
        """Generate regex from description."""
        return f"""Create a regular expression for:

{description}

Regex pattern with explanation:"""

    @staticmethod
    def json_from_text(text: str, schema: Optional[Dict] = None) -> str:
        """Extract JSON from text."""
        schema_str = f"\n\nExpected structure: {schema}" if schema else ""
        return f"""Extract structured JSON data from this text:{schema_str}

Text:
{text}

JSON:"""

    @staticmethod
    def email_draft(context: str, tone: str = "professional") -> str:
        """Draft an email."""
        return f"""Write a {tone} email based on this context:

{context}

Email:"""

    @staticmethod
    def meeting_notes(transcript: str) -> str:
        """Summarize meeting notes."""
        return f"""Create structured meeting notes from this transcript:

{transcript}

Meeting Notes:
- Key Points:
- Action Items:
- Decisions Made:
- Next Steps:"""

    @staticmethod
    def pros_cons(topic: str) -> str:
        """Generate pros and cons list."""
        return f"""List the pros and cons of {topic}:

Pros:
- 

Cons:
-"""

    @staticmethod
    def explain_concept(concept: str, level: str = "beginner") -> str:
        """Explain a concept."""
        return f"""Explain {concept} for a {level} level audience:

Explanation:"""

    @staticmethod
    def creative_ideas(topic: str, count: int = 5) -> str:
        """Generate creative ideas."""
        return f"""Generate {count} creative ideas for {topic}:

Ideas:
1."""

    @staticmethod
    def refactor_code(code: str, goal: str = "cleaner and more maintainable") -> str:
        """Refactor code."""
        return f"""Refactor this code to be {goal}:

Original code:
{code}

Refactored code:"""

    @staticmethod
    def api_from_description(description: str) -> str:
        """Design API from description."""
        return f"""Design a RESTful API based on this description:

{description}

API Design:
Endpoints:"""

    @staticmethod
    def user_story(feature: str) -> str:
        """Create user story."""
        return f"""Create a detailed user story for: {feature}

User Story:
As a [type of user],
I want [goal],
So that [benefit].

Acceptance Criteria:
-"""

    @staticmethod
    def commit_message(changes: str) -> str:
        """Generate commit message."""
        return f"""Write a clear, conventional commit message for these changes:

{changes}

Commit message:"""

    @staticmethod
    def cli_command(task: str, tool: Optional[str] = None) -> str:
        """Generate CLI command."""
        tool_str = f" using {tool}" if tool else ""
        return f"""What command should I run{tool_str} to: {task}

Command:"""


# Convenience functions for common prompts
def code_prompt(code: str, task: str = "explain") -> str:
    """
    Generate appropriate prompt for code-related tasks.

    Args:
        code: The code to analyze
        task: Task type (explain, review, optimize, document, test)

    Returns:
        Formatted prompt string
    """
    templates = PromptTemplates()

    task_map = {
        "explain": templates.explain_code,
        "review": templates.code_review,
        "optimize": templates.optimize_code,
        "document": templates.document_code,
        "test": templates.write_tests,
        "refactor": templates.refactor_code,
    }

    if task in task_map:
        return task_map[task](code)
    else:
        return f"{task}:\n\n{code}\n\nResult:"


def data_prompt(data: str, task: str = "extract") -> str:
    """
    Generate appropriate prompt for data-related tasks.

    Args:
        data: The data to process
        task: Task type (extract, summarize, classify)

    Returns:
        Formatted prompt string
    """
    if task == "extract":
        return PromptTemplates.json_from_text(data)
    elif task == "summarize":
        return f"Summarize this data:\n\n{data}\n\nSummary:"
    elif task == "classify":
        return f"Classify this data:\n\n{data}\n\nClassification:"
    else:
        return f"{task} this data:\n\n{data}\n\nResult:"
