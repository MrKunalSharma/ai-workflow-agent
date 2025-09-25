import requests

BASE_URL = "http://localhost:8000"

# Test all cases and show only differences
test_cases = [
    ("Angry CEO", {"sender": "ceo@fortune500.com", "subject": "URGENT!!! COMPLETE SYSTEM FAILURE", "content": "This is ABSOLUTELY UNACCEPTABLE!!!! Your system has been down for 6 HOURS! We've lost $2 MILLION! If not fixed in 30 MINUTES, expect a LAWSUIT!"}, {"intent": "complaint", "priority": "urgent", "sentiment": "negative", "requires_human": True}),
    ("Enterprise Sales", {"sender": "cto@bigtech.com", "subject": "Enterprise deployment for 50,000 users", "content": "We're evaluating solutions for our global deployment. Need to handle 1M+ emails/day. Budget is $500K-$1M annually. Need proposal by month-end."}, {"intent": "sales_opportunity", "priority": "high", "sentiment": "neutral", "requires_human": True}),
    ("API Issue", {"sender": "dev@startup.com", "subject": "API Authentication Error", "content": "Getting 401 error when calling your API. I've checked the API key multiple times. Can you help troubleshoot?"}, {"intent": "support_request", "priority": "normal", "sentiment": "neutral", "requires_human": False}),
    ("Pricing", {"sender": "info@smallbiz.com", "subject": "Pricing information", "content": "Hi, what are your pricing plans? We're a team of 10 people."}, {"intent": "pricing_inquiry", "priority": "normal", "sentiment": "neutral", "requires_human": False}),
    ("Urgent Support", {"sender": "admin@company.com", "subject": "URGENT: Integration broken", "content": "Our Salesforce integration stopped working this morning! This is urgent as our sales team can't work. Please help ASAP!"}, {"intent": "support_request", "priority": "urgent", "sentiment": "negative", "requires_human": True}),
    ("Positive Feedback", {"sender": "happy@customer.com", "subject": "Great product!", "content": "Just wanted to say thanks! Your product is amazing and has saved us so much time. The team loves it!"}, {"intent": "general_inquiry", "priority": "normal", "sentiment": "positive", "requires_human": False}),
    ("Technical Requirements", {"sender": "architect@enterprise.com", "subject": "Technical evaluation questions", "content": "We need: Kubernetes deployment, 99.99% SLA, GDPR compliance, SOC2, multi-region support, custom ML models, 10k requests/sec. Also need on-premise option. What's your enterprise pricing?"}, {"intent": "sales_opportunity", "priority": "high", "sentiment": "neutral", "requires_human": True}),
    ("Mixed Sentiment", {"sender": "user@company.com", "subject": "Issue but love the product", "content": "I love your product and it's been great, but recently we've had issues with the API timing out. This is frustrating as we rely on it. Can you help fix this?"}, {"intent": "support_request", "priority": "normal", "sentiment": "neutral", "requires_human": False})
]

print("🔍 Diagnosing failures...\n")

failed_count = 0
for name, email, expected in test_cases:
    response = requests.post(f"{BASE_URL}/api/test-email", json=email)
    actual = response.json()
    
    differences = []
    for key in expected:
        if actual.get(key) != expected[key]:
            differences.append(f"{key}: expected={expected[key]}, actual={actual.get(key)}")
    
    if differences:
        failed_count += 1
        print(f"❌ {name}:")
        for diff in differences:
            print(f"   - {diff}")
        print(f"   Model: {actual.get('ai_model', 'unknown')}\n")

print(f"\nSummary: {len(test_cases) - failed_count}/{len(test_cases)} passed ({((len(test_cases) - failed_count)/len(test_cases)*100):.1f}%)")
