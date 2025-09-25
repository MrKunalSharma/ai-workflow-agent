import requests
import json

# Test one specific case
test_email = {
    "sender": "ceo@fortune500.com",
    "subject": "URGENT!!! COMPLETE SYSTEM FAILURE",
    "content": "This is ABSOLUTELY UNACCEPTABLE!!!! Your system has been down for 6 HOURS! We've lost $2 MILLION! If not fixed in 30 MINUTES, expect a LAWSUIT!"
}

print("Sending test email...")
response = requests.post("http://localhost:8000/api/test-email", json=test_email)

print(f"\nStatus Code: {response.status_code}")
print(f"\nResponse:")
print(json.dumps(response.json(), indent=2))
