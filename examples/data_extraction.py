#!/usr/bin/env python3
"""
Data extraction examples using chi_llm.
"""

from chi_llm import MicroLLM
import json


def extract_person_info():
    """Extract person information from text."""
    llm = MicroLLM(temperature=0.1)  # Low temperature for accuracy
    
    text = """
    Sarah Johnson is a 28-year-old software engineer living in San Francisco.
    She graduated from MIT in 2018 with a degree in Computer Science.
    Sarah works at TechCorp and specializes in machine learning.
    Her email is sarah.j@techcorp.com and her phone is (555) 123-4567.
    """
    
    print("📝 Original Text:")
    print(text)
    print("\n" + "=" * 50)
    
    # Extract as JSON
    print("\n🔍 Extracted Data (JSON):")
    result = llm.extract(text, format="json")
    print(result)
    
    # Try to parse and pretty-print
    try:
        data = json.loads(result)
        print("\n📊 Parsed Data:")
        for key, value in data.items():
            print(f"  {key}: {value}")
    except:
        pass


def extract_product_info():
    """Extract product information from description."""
    llm = MicroLLM(temperature=0.1)
    
    description = """
    The new iPhone 15 Pro Max features a 6.7-inch display, A17 Pro chip,
    and starts at $1,199. It comes in Natural Titanium, Blue Titanium,
    White Titanium, and Black Titanium colors. The phone has 256GB, 512GB,
    or 1TB storage options and includes a 48MP main camera.
    """
    
    schema = {
        "product_name": "string",
        "display_size": "string",
        "processor": "string",
        "price": "number",
        "colors": ["list of strings"],
        "storage_options": ["list"],
        "camera": "string"
    }
    
    print("\n📱 Product Description:")
    print(description)
    print("\n" + "=" * 50)
    
    print("\n🔍 Extracting with Schema:")
    result = llm.extract(description, format="json", schema=schema)
    print(result)


def extract_meeting_actions():
    """Extract action items from meeting notes."""
    llm = MicroLLM(temperature=0.1)
    
    meeting_notes = """
    Meeting Notes - Project Alpha Status Update
    Date: January 15, 2024
    
    Discussion:
    - John will finish the API documentation by Friday
    - Sarah needs to review the security audit report
    - The team agreed to move the deadline to February 1st
    - Mike will schedule interviews with three candidates next week
    - Lisa should update the project roadmap with new milestones
    - Everyone must complete the compliance training by month end
    """
    
    print("\n📋 Meeting Notes:")
    print(meeting_notes)
    print("\n" + "=" * 50)
    
    print("\n✅ Extracted Action Items:")
    prompt = """Extract all action items from these meeting notes.
    Format as a numbered list with person responsible and task."""
    
    result = llm.ask(prompt, context=meeting_notes)
    print(result)


def extract_code_info():
    """Extract information from code."""
    llm = MicroLLM(temperature=0.1)
    
    code = """
    class UserAuthentication:
        def __init__(self, db_connection):
            self.db = db_connection
            self.max_attempts = 3
            self.lockout_duration = 300  # 5 minutes
        
        def login(self, username, password):
            user = self.db.find_user(username)
            if user and self.verify_password(password, user.password_hash):
                return self.generate_token(user)
            return None
        
        def verify_password(self, password, hash):
            return bcrypt.checkpw(password.encode(), hash)
    """
    
    print("\n💻 Code Sample:")
    print(code)
    print("\n" + "=" * 50)
    
    print("\n🔍 Extracted Code Information:")
    prompt = """Extract the following from this code:
    1. Class name
    2. Methods and their parameters
    3. Configuration values
    4. Dependencies/imports used
    Format as JSON."""
    
    result = llm.ask(prompt, context=code)
    print(result)


def extract_error_info():
    """Extract information from error messages."""
    llm = MicroLLM(temperature=0.1)
    
    error_log = """
    2024-01-15 14:23:45 ERROR: Database connection failed
    File: app/database.py, Line: 45
    Function: connect_to_database
    Error: psycopg2.OperationalError: could not connect to server: Connection refused
    Is the server running on host "localhost" (127.0.0.1) and accepting
    TCP/IP connections on port 5432?
    
    Stack trace:
    File "main.py", line 12, in <module>
        app.initialize()
    File "app/core.py", line 34, in initialize
        self.db = Database()
    File "app/database.py", line 45, in __init__
        self.connection = psycopg2.connect(**config)
    """
    
    print("\n❌ Error Log:")
    print(error_log)
    print("\n" + "=" * 50)
    
    print("\n🔍 Extracted Error Information:")
    result = llm.extract(error_log, format="json")
    print(result)
    
    print("\n💡 Suggested Fix:")
    fix = llm.ask("What's the likely cause and fix for this error?", context=error_log)
    print(fix)


def main():
    """Run all extraction examples."""
    print("🔍 chi_llm Data Extraction Examples")
    print("=" * 50)
    
    print("\n1️⃣ Person Information Extraction")
    extract_person_info()
    
    print("\n\n2️⃣ Product Information Extraction")
    extract_product_info()
    
    print("\n\n3️⃣ Meeting Action Items")
    extract_meeting_actions()
    
    print("\n\n4️⃣ Code Information")
    extract_code_info()
    
    print("\n\n5️⃣ Error Analysis")
    extract_error_info()
    
    print("\n\n✨ All examples completed!")


if __name__ == "__main__":
    main()