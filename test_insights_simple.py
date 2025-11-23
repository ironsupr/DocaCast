import requests
import json

# Test insights endpoint with simple text
url = "http://127.0.0.1:8001/insights"
payload = {
    "text": "Artificial intelligence is transforming healthcare. Machine learning algorithms can detect diseases from medical images with high accuracy. Deep learning models assist in drug discovery and personalized treatment plans.",
    "k": 5
}

print("Testing insights endpoint with text...")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(url, json=payload, timeout=60)
    print(f"\nStatus: {response.status_code}")
    if response.ok:
        data = response.json()
        print("\n✅ SUCCESS!")
        print(f"\nKey Insights ({len(data.get('key_insights', []))}):")
        for insight in data.get('key_insights', []):
            print(f"  - {insight}")
        print(f"\nDid You Know ({len(data.get('did_you_know_facts', []))}):")
        for fact in data.get('did_you_know_facts', []):
            print(f"  - {fact}")
        print(f"\nExamples ({len(data.get('examples', []))}):")
        for ex in data.get('examples', []):
            print(f"  - {ex}")
    else:
        print(f"\n❌ ERROR: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"\n❌ EXCEPTION: {type(e).__name__}: {e}")
