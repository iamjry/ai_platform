#!/usr/bin/env python3
import requests
import json

# Test search with qwen
print("Testing search with qwen2.5...")
response = requests.post(
    "http://localhost:8002/agent/execute",
    json={
        "task": "搜索 API",
        "model": "qwen2.5",
        "agent_type": "general"
    },
    timeout=30
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
