#!/usr/bin/env python3
import requests
import json

# Test models
models_to_test = [
    ("qwen2.5", "Qwen 2.5 (local)"),
    ("llama31-taidelx-8b-32k", "Taiwan Gov - Llama 3.1 TaideLX"),
    ("llama3-taiwan-70b-8k", "Taiwan Gov - Llama 3 Taiwan"),
]

web_search_tasks = [
    "搜索人工智能最新趨勢的文章",
    "search latest AI technology",
    "找關於機器學習的資料",
    "搜尋台灣AI發展現況",
]

print("Testing web search functionality across different models...\n")
print("=" * 80)

for model_id, model_name in models_to_test:
    print(f"\n🧪 Testing: {model_name} ({model_id})")
    print("-" * 80)

    for task in web_search_tasks:
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

                # Check if web search was successful
                if '網頁搜索完成' in result or 'web search' in result.lower():
                    # Extract number of results
                    import re
                    match = re.search(r'找到\s*(\d+)\s*個結果', result)
                    if match:
                        count = match.group(1)
                        print(f"    ✅ Success: Found {count} results")
                    else:
                        print(f"    ✅ Success (web search completed)")

                    # Show first result title if available
                    title_match = re.search(r'\*\*([^*]+)\*\*', result)
                    if title_match:
                        print(f"    📄 First result: {title_match.group(1)[:60]}...")
                else:
                    print(f"    ⚠️  Result: {result[:150]}...")

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
print("Web search testing completed!")
