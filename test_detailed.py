import requests
import json

BASE_URL = "http://localhost:8000"

# Just test the failing ones
problem_cases = [
    {
        "name": "API Integration Issue",
        "email": {
            "sender": "dev@startup.com",
            "subject": "API Authentication Error",
            "content": "Getting 401 error when calling your API. I've checked the API key multiple times. Can you help troubleshoot?"
        },
        "expected": {
            "intent": "support_request",
            "priority": "normal",
            "sentiment": "neutral",
            "requires_human": False  # This is what test expects
        }
    },
    {
        "name": "Positive Feedback",
        "email": {
            "sender": "happy@customer.com",
            "subject": "Great product!",
            "content": "Just wanted to say thanks! Your product is amazing and has saved us so much time. The team loves it!"
        },
        "expected": {
            "intent": "general_inquiry",  # Test expects this
            "priority": "normal",
            "sentiment": "positive",
            "requires_human": False
        }
    }
]

for case in problem_cases:
    print(f"\n{'='*60}")
    print(f"Testing: {case['name']}")
    print(f"{'='*60}")
    
    response = requests.post(f"{BASE_URL}/api/test-email", json=case['email'])
    result = response.json()
    
    print("\nExpected vs Actual:")
    for key in case['expected']:
        expected = case['expected'][key]
        actual = result.get(key)
        match = "✅" if expected == actual else "❌"
        print(f"{match} {key}: expected={expected}, actual={actual}")
    
    print(f"\nAI Model Used: {result.get('ai_model', 'unknown')}")
