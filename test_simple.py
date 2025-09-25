import requests
import json

BASE_URL = "http://localhost:8000"

def test_api():
    print("Testing Simplified AI Workflow Agent\n")
    
    # Test 1: Health check
    response = requests.get(f"{BASE_URL}/")
    print("1. Health Check:", response.json())
    
    # Test 2: Add knowledge base
    kb_data = {
        "title": "Pricing Guide",
        "content": "Our plans: Starter $49, Pro $149, Enterprise custom"
    }
    response = requests.post(
        f"{BASE_URL}/api/knowledge-base/add",
        params=kb_data
    )
    print("\n2. Add Knowledge Base:", response.json())
    
    # Test 3: Process email
    email_data = {
        "sender": "customer@example.com",
        "subject": "Question about pricing",
        "content": "Hi, I'm interested in your pricing plans. Can you help?"
    }
    response = requests.post(
        f"{BASE_URL}/api/test-email",
        json=email_data
    )
    print("\n3. Process Email:")
    print(json.dumps(response.json(), indent=2))
    
    # Test 4: Get processed emails
    response = requests.get(f"{BASE_URL}/api/processed-emails")
    print("\n4. Processed Emails:", response.json()['total'], "emails processed")

if __name__ == "__main__":
    test_api()
