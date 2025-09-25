"""
Comprehensive test suite for email processor
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

test_cases = [
    # Crisis Management
    {
        "name": "Angry CEO - System Failure",
        "email": {
            "sender": "ceo@fortune500.com",
            "subject": "URGENT!!! COMPLETE SYSTEM FAILURE",
            "content": "This is ABSOLUTELY UNACCEPTABLE!!!! Your system has been down for 6 HOURS! We've lost $2 MILLION! If not fixed in 30 MINUTES, expect a LAWSUIT!"
        },
        "expected": {
            "intent": "complaint",
            "priority": "urgent",
            "sentiment": "negative",
            "requires_human": True
        }
    },
    
    # High-Value Sales
    {
        "name": "Enterprise Sales Opportunity",
        "email": {
            "sender": "cto@bigtech.com",
            "subject": "Enterprise deployment for 50,000 users",
            "content": "We're evaluating solutions for our global deployment. Need to handle 1M+ emails/day. Budget is $500K-$1M annually. Need proposal by month-end."
        },
        "expected": {
            "intent": "sales_opportunity",
            "priority": "high",
            "sentiment": "neutral",
            "requires_human": True
        }
    },
    
    # Technical Support
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
            "requires_human": False
        }
    },
    
    # Simple Pricing
    {
        "name": "Basic Pricing Inquiry",
        "email": {
            "sender": "info@smallbiz.com",
            "subject": "Pricing information",
            "content": "Hi, what are your pricing plans? We're a team of 10 people."
        },
        "expected": {
            "intent": "pricing_inquiry",
            "priority": "normal",
            "sentiment": "neutral",
            "requires_human": False
        }
    },
    
    # Urgent Support
    {
        "name": "Urgent Technical Issue",
        "email": {
            "sender": "admin@company.com",
            "subject": "URGENT: Integration broken",
            "content": "Our Salesforce integration stopped working this morning! This is urgent as our sales team can't work. Please help ASAP!"
        },
        "expected": {
            "intent": "support_request",
            "priority": "urgent",
            "sentiment": "negative",
            "requires_human": True
        }
    },
    
    # Happy Customer
    {
        "name": "Positive Feedback",
        "email": {
            "sender": "happy@customer.com",
            "subject": "Great product!",
            "content": "Just wanted to say thanks! Your product is amazing and has saved us so much time. The team loves it!"
        },
        "expected": {
            "intent": "general_inquiry",
            "priority": "normal",
            "sentiment": "positive",
            "requires_human": False
        }
    },
    
    # Complex Requirements
    {
        "name": "Detailed Technical Requirements",
        "email": {
            "sender": "architect@enterprise.com",
            "subject": "Technical evaluation questions",
            "content": "We need: Kubernetes deployment, 99.99% SLA, GDPR compliance, SOC2, multi-region support, custom ML models, 10k requests/sec. Also need on-premise option. What's your enterprise pricing?"
        },
        "expected": {
            "intent": "sales_opportunity",  # Could also be pricing_inquiry
            "priority": "high",
            "sentiment": "neutral",
            "requires_human": True
        }
    },
    
    # Mixed Sentiment
    {
        "name": "Complaint with Appreciation",
        "email": {
            "sender": "user@company.com",
            "subject": "Issue but love the product",
            "content": "I love your product and it's been great, but recently we've had issues with the API timing out. This is frustrating as we rely on it. Can you help fix this?"
        },
        "expected": {
            "intent": "support_request",
            "priority": "normal",
            "sentiment": "neutral",  # Mixed sentiment
            "requires_human": False
        }
    }
]

def run_tests():
    """Run all test cases"""
    print("🧪 Running Comprehensive Email Processing Tests\n")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("❌ API is not running! Please start the server first.")
            return
    except:
        print("❌ Cannot connect to API at http://localhost:8000")
        print("Please start the server with: python -m uvicorn src.main_enhanced:app --reload")
        return
    
    for test in test_cases:
        print(f"\n📧 Test: {test['name']}")
        print(f"   From: {test['email']['sender']}")
        print(f"   Subject: {test['email']['subject']}")
        
        # Send request
        try:
            response = requests.post(
                f"{BASE_URL}/api/test-email",
                json=test['email']
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check expectations
                all_passed = True
                
                for key, expected_value in test['expected'].items():
                    actual_value = result.get(key)
                    if actual_value == expected_value:
                        print(f"   ✅ {key}: {actual_value}")
                    else:
                        print(f"   ❌ {key}: {actual_value} (expected: {expected_value})")
                        all_passed = False
                
                # Show response preview
                if 'suggested_response' in result:
                    response_preview = result['suggested_response'][:100] + "..."
                    print(f"   📝 Response preview: {response_preview}")
                
                if all_passed:
                    passed += 1
                    print("   ✅ TEST PASSED")
                else:
                    failed += 1
                    print("   ❌ TEST FAILED")
            else:
                print(f"   ❌ API ERROR: {response.status_code}")
                print(f"   Error details: {response.text}")
                failed += 1
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"\n📊 Test Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print(f"✨ Success Rate: {(passed/len(test_cases))*100:.1f}%")
    
    # Show summary
    if passed == len(test_cases):
        print("\n🎉 All tests passed! Your email processor is working perfectly!")
    elif passed > 0:
        print(f"\n⚠️  Some tests failed. Review the logic for failed cases.")
    else:
        print("\n❌ All tests failed. Check your implementation.")

if __name__ == "__main__":
    run_tests()
