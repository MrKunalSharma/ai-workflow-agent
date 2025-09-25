import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_health():
    """Test if API is running"""
    response = requests.get(f"{BASE_URL}/")
    print("Health Check:", response.json())
    return response.status_code == 200

def test_status():
    """Get system status"""
    response = requests.get(f"{BASE_URL}/api/status")
    print("\nSystem Status:", json.dumps(response.json(), indent=2))
    return response.status_code == 200

def test_email_processing():
    """Test email processing without sending"""
    test_email = {
        "sender": "customer@example.com",
        "subject": "Question about pricing",
        "content": "Hello, I'm interested in your enterprise plan. Can you provide more details about the pricing and features included? Also, do you offer any discounts for annual subscriptions?"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/test-email",
        json=test_email
    )
    
    print("\nEmail Processing Test:")
    print(f"Input: {test_email['subject']}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_knowledge_search():
    """Test knowledge base search"""
    query = "pricing information"
    response = requests.get(
        f"{BASE_URL}/api/search",
        params={"query": query}
    )
    
    print(f"\nKnowledge Base Search for '{query}':")
    print(json.dumps(response.json(), indent=2))
    return response.status_code == 200

def main():
    print("="*50)
    print("AI Workflow Agent Test Suite")
    print("="*50)
    
    tests = [
        ("Health Check", test_health),
        ("System Status", test_status),
        ("Email Processing", test_email_processing),
        ("Knowledge Search", test_knowledge_search)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"\n✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"\n❌ {test_name} FAILED")
        except Exception as e:
            print(f"\n❌ {test_name} ERROR: {str(e)}")
    
    print(f"\n{'='*50}")
    print(f"Tests Passed: {passed}/{len(tests)}")
    print("="*50)

if __name__ == "__main__":
    main()
