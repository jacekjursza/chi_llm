#!/usr/bin/env python3
"""
Basic usage examples for chi_llm SDK.
"""

from chi_llm import CodeAnalyzer


def example_simple_analysis():
    """Simple code analysis example."""
    print("=" * 60)
    print("Example 1: Simple Analysis")
    print("=" * 60)
    
    # Initialize the analyzer
    analyzer = CodeAnalyzer()
    
    # Simple Python code to analyze
    code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
    
    # Analyze the code
    result = analyzer.analyze(code)
    print(result)
    print()


def example_custom_question():
    """Analysis with custom question."""
    print("=" * 60)
    print("Example 2: Custom Question")
    print("=" * 60)
    
    analyzer = CodeAnalyzer()
    
    code = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr
"""
    
    # Ask about time complexity
    result = analyzer.analyze(
        code, 
        question="What is the time complexity of this algorithm?"
    )
    print(result)
    print()


def example_bug_detection():
    """Example of finding bugs in code."""
    print("=" * 60)
    print("Example 3: Bug Detection")
    print("=" * 60)
    
    analyzer = CodeAnalyzer()
    
    # Code with potential issues
    buggy_code = """
def divide_numbers(a, b):
    return a / b

def find_item(items, target):
    for i in range(len(items)):
        if items[i] = target:  # Bug: should be ==
            return i
    return -1
"""
    
    result = analyzer.analyze(
        buggy_code,
        question="Find potential bugs and issues in this code"
    )
    print(result)
    print()


def example_file_analysis():
    """Example of analyzing a file directly."""
    print("=" * 60)
    print("Example 4: File Analysis")
    print("=" * 60)
    
    analyzer = CodeAnalyzer()
    
    # Analyze this script itself
    try:
        result = analyzer.analyze_file(
            __file__,
            question="What does this script demonstrate?"
        )
        print(result)
    except Exception as e:
        print(f"Error analyzing file: {e}")
    print()


def example_optimization_suggestions():
    """Example of getting optimization suggestions."""
    print("=" * 60)
    print("Example 5: Optimization Suggestions")
    print("=" * 60)
    
    analyzer = CodeAnalyzer()
    
    code = """
def find_duplicates(numbers):
    duplicates = []
    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            if numbers[i] == numbers[j] and numbers[i] not in duplicates:
                duplicates.append(numbers[i])
    return duplicates
"""
    
    result = analyzer.analyze(
        code,
        question="Suggest performance optimizations for this code"
    )
    print(result)
    print()


if __name__ == "__main__":
    print("🔍 chi_llm SDK Examples")
    print("=" * 60)
    print()
    
    # Run examples
    example_simple_analysis()
    example_custom_question()
    example_bug_detection()
    example_optimization_suggestions()
    
    # Optional: analyze a file
    # example_file_analysis()
    
    print("✨ All examples completed!")