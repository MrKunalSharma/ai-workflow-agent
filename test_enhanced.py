import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*50}")
    print(f"{title}")
    print('='*50)

def test_enhanced_api():
    print_section("AI Workflow Agent - Enhanced Testing")
    
    # Test different email scenarios
    test_emails = [
        {
            "sender": "john.smith@techcorp.com",
            "subject": "Enterprise pricing inquiry",
            "content": "Hi, we're a company with 500 employees looking for an email automation solution. Can you provide details about your Enterprise plan? We need API access and on-premise deployment options. This is urgent as we need to make a decision by end of month."
        },
        {
            "sender": "sarah@startup.io",
            "subject": "Integration questions",
            "content": "Hello, I'm wondering if your platform integrates with Notion and Slack? We're a small team and these are our main tools. Also, what's your API rate limit?"
        },
        {
            "sender": "angry.customer@email.com",
            "subject": "Service not working!!!",
            "content": "I'm extremely disappointed with your service. The email automation stopped working yesterday and I've lost important customer messages. This is unacceptable and I want a full refund immediately!"
        },
        {
            "sender": "developer@company.com",
            "subject": "API documentation",
            "content": "Hi team, I'm trying to integrate your API but can't find documentation about webhooks. Do you support real-time notifications when emails are processed? Thanks for your help!"
        }
    ]
    
    processed = []
    
    for i, email in enumerate(test_emails, 1):
        print(f"\n{i}. Processing: {email['subject']}")
        
        response = requests.post(f"{BASE_URL}/api/test-email", json=email)
        if response.status_code == 200:
            result = response.json()
            processed.append(result)
            
            print(f"   Intent: {result['intent']}")
            print(f"   Priority: {result['priority']}")
            print(f"   Sentiment: {result['sentiment']}")
            print(f"   Requires Human: {result.get('requires_human', False)}")
            print(f"   Knowledge Used: {', '.join(result.get('knowledge_used', []))}")
            
            # Show first 150 chars of response
            response_preview = result['suggested_response'][:150] + "..."
            print(f"   Response Preview: {response_preview}")
        else:
            print(f"   ERROR: {response.status_code}")
        
        time.sleep(0.5)  # Small delay
    
    # Get statistics
    print_section("Processing Statistics")
    
    stats_response = requests.get(f"{BASE_URL}/api/stats")
    if stats_response.status_code == 200:
        stats = stats_response.json()
        print(json.dumps(stats, indent=2))
    
    # Show system status
    print_section("System Status")
    
    status_response = requests.get(f"{BASE_URL}/")
    if status_response.status_code == 200:
        print(json.dumps(status_response.json(), indent=2))

if __name__ == "__main__":
    test_enhanced_api()
