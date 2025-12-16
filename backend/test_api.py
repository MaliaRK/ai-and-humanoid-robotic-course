#!/usr/bin/env python3
"""
Test script to call the API endpoint directly using requests
"""

import requests
import json
import time

# Test the API endpoint
url = "http://localhost:8000/api/v1/rag/query"

payload = {
    "query": "What is Artificial Intelligence?",
    "conversation_id": None
}

headers = {
    "Content-Type": "application/json"
}

print("Sending request to:", url)
print("Payload:", json.dumps(payload, indent=2))

try:
    start_time = time.time()
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    end_time = time.time()

    print(f"Response status: {response.status_code}")
    print(f"Response time: {end_time - start_time:.2f} seconds")
    print(f"Response headers: {dict(response.headers)}")
    print(f"Response body: {response.text}")

except requests.exceptions.Timeout:
    print("Request timed out after 30 seconds")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")