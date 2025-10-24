#!/usr/bin/env python3
import requests
import json

print("Testing knowledge base search...\n")
print("=" * 80)

# Test with keywords that should trigger knowledge base search
kb_search_tasks = [
    "搜索文檔中關於 API 的內容",
    "search for documents about security",
    "找知識庫中的資料",
]

model_id = "qwen2.5"

for task in kb_search_tasks:
    print(f"\n📝 Task: '{task}'")
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
            metadata = data.get('metadata', {})

            tool_called = metadata.get('tool_called', 'unknown')

            # Check which tool was used
            if tool_called == "search_knowledge_base":
                print(f"    ✅ Correct: Using knowledge base search")
            elif tool_called == "web_search":
                print(f"    ⚠️  Used web_search instead of search_knowledge_base")
            else:
                print(f"    ❓ Tool called: {tool_called}")

            # Show results
            import re
            match = re.search(r'找到\s*(\d+)\s*個結果', result)
            if match:
                count = match.group(1)
                print(f"    📊 Results: {count}")

            print(f"    🔧 Tool: {tool_called}")

        else:
            print(f"    ❌ Error: Status {response.status_code}")

    except Exception as e:
        print(f"    ❌ Exception: {str(e)}")

print("\n" + "=" * 80)
print("Knowledge base search testing completed!")
