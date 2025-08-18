#!/usr/bin/env python3
"""
Integration example showing how to use chi_llm in a larger application.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any
from chi_llm import CodeAnalyzer


class CodeReviewBot:
    """
    Example bot that performs automated code reviews using chi_llm.
    """
    
    def __init__(self):
        """Initialize the code review bot."""
        self.analyzer = CodeAnalyzer()
        self.review_checks = [
            ("security", "Check for security vulnerabilities and unsafe practices"),
            ("bugs", "Find potential bugs and logic errors"),
            ("performance", "Identify performance bottlenecks"),
            ("style", "Check code style and best practices"),
            ("documentation", "Assess documentation quality and completeness")
        ]
    
    def review_file(self, file_path: str) -> Dict[str, Any]:
        """
        Perform a comprehensive review of a code file.
        
        Args:
            file_path: Path to the file to review
            
        Returns:
            Dictionary containing review results
        """
        results = {
            "file": file_path,
            "reviews": {}
        }
        
        print(f"🔍 Reviewing: {file_path}")
        print("-" * 40)
        
        for check_name, question in self.review_checks:
            print(f"  ⏳ Running {check_name} check...")
            try:
                analysis = self.analyzer.analyze_file(file_path, question)
                results["reviews"][check_name] = analysis
                print(f"  ✅ {check_name} check complete")
            except Exception as e:
                results["reviews"][check_name] = f"Error: {e}"
                print(f"  ❌ {check_name} check failed: {e}")
        
        return results
    
    def review_directory(self, directory: str, pattern: str = "*.py") -> List[Dict[str, Any]]:
        """
        Review all matching files in a directory.
        
        Args:
            directory: Directory to scan
            pattern: File pattern to match (default: "*.py")
            
        Returns:
            List of review results
        """
        path = Path(directory)
        files = list(path.glob(pattern))
        
        if not files:
            print(f"No {pattern} files found in {directory}")
            return []
        
        print(f"Found {len(files)} files to review")
        results = []
        
        for file_path in files:
            results.append(self.review_file(str(file_path)))
            print()
        
        return results
    
    def generate_report(self, results: List[Dict[str, Any]]) -> str:
        """
        Generate a markdown report from review results.
        
        Args:
            results: List of review results
            
        Returns:
            Markdown formatted report
        """
        report = ["# Code Review Report", ""]
        
        for file_result in results:
            report.append(f"## {file_result['file']}")
            report.append("")
            
            for check_name, analysis in file_result['reviews'].items():
                report.append(f"### {check_name.title()} Check")
                report.append("")
                report.append(analysis)
                report.append("")
                report.append("---")
                report.append("")
        
        return "\n".join(report)


class CodeDocGenerator:
    """
    Example documentation generator using chi_llm.
    """
    
    def __init__(self):
        """Initialize the documentation generator."""
        self.analyzer = CodeAnalyzer()
    
    def generate_docs(self, file_path: str) -> str:
        """
        Generate documentation for a code file.
        
        Args:
            file_path: Path to the file to document
            
        Returns:
            Generated documentation
        """
        docs = []
        
        # Get overview
        overview = self.analyzer.analyze_file(
            file_path,
            "Provide a high-level overview of this code's purpose and functionality"
        )
        docs.append("## Overview\n")
        docs.append(overview)
        docs.append("\n")
        
        # Get function descriptions
        functions = self.analyzer.analyze_file(
            file_path,
            "List and describe all functions/methods in this code"
        )
        docs.append("## Functions\n")
        docs.append(functions)
        docs.append("\n")
        
        # Get usage examples
        examples = self.analyzer.analyze_file(
            file_path,
            "Provide usage examples for this code"
        )
        docs.append("## Usage Examples\n")
        docs.append(examples)
        docs.append("\n")
        
        return "\n".join(docs)


def demo_review_bot():
    """Demonstrate the code review bot."""
    print("=" * 60)
    print("Code Review Bot Demo")
    print("=" * 60)
    print()
    
    bot = CodeReviewBot()
    
    # Review this file itself
    results = [bot.review_file(__file__)]
    
    # Generate report
    report = bot.generate_report(results)
    
    # Save report
    report_path = "code_review_report.md"
    with open(report_path, "w") as f:
        f.write(report)
    
    print(f"📄 Report saved to: {report_path}")


def demo_doc_generator():
    """Demonstrate the documentation generator."""
    print("=" * 60)
    print("Documentation Generator Demo")
    print("=" * 60)
    print()
    
    generator = CodeDocGenerator()
    
    # Generate docs for this file
    docs = generator.generate_docs(__file__)
    
    # Save documentation
    doc_path = "generated_docs.md"
    with open(doc_path, "w") as f:
        f.write(f"# Documentation for {Path(__file__).name}\n\n")
        f.write(docs)
    
    print(f"📄 Documentation saved to: {doc_path}")
    print()
    print("Preview:")
    print("-" * 40)
    print(docs[:500] + "..." if len(docs) > 500 else docs)


if __name__ == "__main__":
    print("🔍 chi_llm Integration Examples")
    print("=" * 60)
    print()
    
    # Run demos
    demo_review_bot()
    print()
    demo_doc_generator()
    
    print()
    print("✨ Integration examples completed!")