#!/usr/bin/env python3
"""
Code assistant examples using chi_llm.
"""

from chi_llm import MicroLLM, PromptTemplates


def code_review_example():
    """Perform a code review."""
    llm = MicroLLM(temperature=0.3)
    templates = PromptTemplates()
    
    code = """
    def calculate_discount(price, discount_percent):
        discount = price * discount_percent / 100
        final_price = price - discount
        return final_price
    
    def process_order(items, customer_type):
        total = 0
        for item in items:
            total = total + item['price']
        
        if customer_type == 'premium':
            total = calculate_discount(total, 20)
        elif customer_type == 'regular':
            total = calculate_discount(total, 10)
        
        return total
    """
    
    print("📝 Code to Review:")
    print(code)
    print("\n" + "=" * 50)
    
    # Perform code review
    review_prompt = templates.code_review(code, language="Python")
    review = llm.generate(review_prompt)
    
    print("\n🔍 Code Review:")
    print(review)


def generate_unit_tests():
    """Generate unit tests for a function."""
    llm = MicroLLM(temperature=0.5)
    templates = PromptTemplates()
    
    code = """
    def validate_email(email):
        if not email or '@' not in email:
            return False
        
        parts = email.split('@')
        if len(parts) != 2:
            return False
        
        local, domain = parts
        if not local or not domain:
            return False
        
        if '.' not in domain:
            return False
        
        return True
    """
    
    print("\n🧪 Function to Test:")
    print(code)
    print("\n" + "=" * 50)
    
    # Generate tests
    test_prompt = templates.write_tests(code, framework="pytest")
    tests = llm.generate(test_prompt)
    
    print("\n✅ Generated Tests:")
    print(tests)


def optimize_code():
    """Optimize inefficient code."""
    llm = MicroLLM(temperature=0.3)
    templates = PromptTemplates()
    
    code = """
    def find_duplicates(numbers):
        duplicates = []
        for i in range(len(numbers)):
            for j in range(i + 1, len(numbers)):
                if numbers[i] == numbers[j]:
                    if numbers[i] not in duplicates:
                        duplicates.append(numbers[i])
        return duplicates
    """
    
    print("\n🐌 Slow Code:")
    print(code)
    print("\n" + "=" * 50)
    
    # Optimize
    optimize_prompt = templates.optimize_code(code)
    optimized = llm.generate(optimize_prompt)
    
    print("\n⚡ Optimized Version:")
    print(optimized)


def explain_code():
    """Explain complex code."""
    llm = MicroLLM(temperature=0.5)
    templates = PromptTemplates()
    
    code = """
    def quick_sort(arr):
        if len(arr) <= 1:
            return arr
        
        pivot = arr[len(arr) // 2]
        left = [x for x in arr if x < pivot]
        middle = [x for x in arr if x == pivot]
        right = [x for x in arr if x > pivot]
        
        return quick_sort(left) + middle + quick_sort(right)
    """
    
    print("\n🤔 Complex Code:")
    print(code)
    print("\n" + "=" * 50)
    
    # Explain
    explain_prompt = templates.explain_code(code)
    explanation = llm.generate(explain_prompt)
    
    print("\n💡 Explanation:")
    print(explanation)


def fix_bug():
    """Fix a bug in code."""
    llm = MicroLLM(temperature=0.2)
    templates = PromptTemplates()
    
    buggy_code = """
    def calculate_average(numbers):
        total = 0
        for num in numbers:
            total += num
        average = total / len(numbers)
        return average
    """
    
    error = "ZeroDivisionError: division by zero (when numbers list is empty)"
    
    print("\n🐛 Buggy Code:")
    print(buggy_code)
    print(f"\n❌ Error: {error}")
    print("\n" + "=" * 50)
    
    # Fix bug
    fix_prompt = templates.fix_error(buggy_code, error)
    fixed = llm.generate(fix_prompt)
    
    print("\n✅ Fixed Code:")
    print(fixed)


def generate_documentation():
    """Generate documentation for code."""
    llm = MicroLLM(temperature=0.3)
    templates = PromptTemplates()
    
    code = """
    class TaskQueue:
        def __init__(self, max_size=100):
            self.tasks = []
            self.max_size = max_size
        
        def add_task(self, task, priority=0):
            if len(self.tasks) >= self.max_size:
                raise Exception("Queue is full")
            self.tasks.append((priority, task))
            self.tasks.sort(key=lambda x: x[0], reverse=True)
        
        def get_next_task(self):
            if not self.tasks:
                return None
            return self.tasks.pop(0)[1]
        
        def is_empty(self):
            return len(self.tasks) == 0
    """
    
    print("\n📚 Code to Document:")
    print(code)
    print("\n" + "=" * 50)
    
    # Generate docs
    doc_prompt = templates.document_code(code, style="docstring")
    documented = llm.generate(doc_prompt)
    
    print("\n📝 Documented Code:")
    print(documented)


def sql_from_description():
    """Generate SQL from natural language."""
    llm = MicroLLM(temperature=0.2)
    templates = PromptTemplates()
    
    descriptions = [
        "Get all users who registered in the last 30 days",
        "Find the top 5 products by sales volume this month",
        "Show customers who have made more than 3 purchases"
    ]
    
    print("\n🗃️ SQL Generation:")
    print("=" * 50)
    
    for desc in descriptions:
        print(f"\n📝 Description: {desc}")
        sql_prompt = templates.sql_from_description(desc)
        sql = llm.generate(sql_prompt)
        print(f"💾 SQL:\n{sql}")


def main():
    """Run all code assistant examples."""
    print("💻 chi_llm Code Assistant Examples")
    print("=" * 50)
    
    print("\n1️⃣ Code Review")
    code_review_example()
    
    print("\n\n2️⃣ Generate Unit Tests")
    generate_unit_tests()
    
    print("\n\n3️⃣ Optimize Code")
    optimize_code()
    
    print("\n\n4️⃣ Explain Code")
    explain_code()
    
    print("\n\n5️⃣ Fix Bug")
    fix_bug()
    
    print("\n\n6️⃣ Generate Documentation")
    generate_documentation()
    
    print("\n\n7️⃣ SQL Generation")
    sql_from_description()
    
    print("\n\n✨ All examples completed!")


if __name__ == "__main__":
    main()