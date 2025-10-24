#!/usr/bin/env python3
import requests
import json

# Test models
models_to_test = [
    ("qwen2.5", "Qwen 2.5 (local)"),
    ("llama31-taidelx-8b-32k", "Taiwan Gov - Llama 3.1 TaideLX"),
    ("llama3-taiwan-70b-8k", "Taiwan Gov - Llama 3 Taiwan"),
]

search_tasks = [
    "搜索 API",
    "search security",
    "找 customer feedback",
]

print("Testing search functionality across different models...\n")
print("=" * 80)

for model_id, model_name in models_to_test:
    print(f"\n🧪 Testing: {model_name} ({model_id})")
    print("-" * 80)

    for task in search_tasks:
        print(f"\n  Task: '{task}'")
        try:
            response = requests.post(
                "http://localhost:8002/agent/execute",
                json={
                    "task": task,
                    "model": model_id,
                    "agent_type": "general"
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                result = data.get('result', '')

                # Check if search was successful
                if '找到' in result or 'found' in result.lower():
                    # Extract number of results
                    import re
                    match = re.search(r'找到\s*(\d+)\s*個結果|found\s*(\d+)\s*results', result, re.IGNORECASE)
                    if match:
                        count = match.group(1) or match.group(2)
                        print(f"    ✅ Success: Found {count} results")
                    else:
                        print(f"    ✅ Success (results found)")
                else:
                    print(f"    ⚠️  Result: {result[:100]}...")

                # Show metadata
                metadata = data.get('metadata', {})
                if metadata.get('fallback_mode'):
                    print(f"    📌 Mode: Fallback (pattern matching)")
                if metadata.get('tool_called'):
                    print(f"    🔧 Tool: {metadata['tool_called']}")

            else:
                print(f"    ❌ Error: Status {response.status_code}")
                print(f"    Response: {response.text[:200]}")

        except Exception as e:
            print(f"    ❌ Exception: {str(e)}")

print("\n" + "=" * 80)
print("Testing completed!")
