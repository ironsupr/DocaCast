import requests
import json

# Test insights endpoint
url = "http://127.0.0.1:8001/insights"
payload = {
    "filename": "p171.pdf",
    "page_number": 1,
    "k": 5
}

print("Testing insights endpoint...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("\nSending request...")

try:
    response = requests.post(url, json=payload, timeout=60)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"\nResponse Body:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"\nError: {type(e).__name__}: {e}")
    if hasattr(e, 'response'):
        print(f"Response text: {e.response.text}")
