#!/usr/bin/env python3
"""Test script for all MCP server tools"""

import requests
import json
import base64
import io

BASE_URL = "http://localhost:8001"

def test_tool(name, endpoint, payload=None):
    """Test a single tool endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")

    try:
        if payload:
            response = requests.post(f"{BASE_URL}{endpoint}", json=payload, timeout=10)
        else:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)

        print(f"Status: {response.status_code}")

        if response.ok:
            result = response.json()
            print(f"✅ SUCCESS")
            print(f"Response: {json.dumps(result, indent=2)[:500]}...")
            return True
        else:
            print(f"❌ FAILED")
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return False

def main():
    print("="*60)
    print("MCP Server Tools Testing Suite")
    print("="*60)

    results = []

    # Test 1: Health Check
    results.append(test_tool("Health Check", "/health"))

    # Test 2: List Tools
    results.append(test_tool("List Tools", "/tools/list"))

    # Test 3: Vector Search (original)
    results.append(test_tool(
        "Vector Search",
        "/tools/search",
        {"query": "test query", "collection": "documents", "limit": 5}
    ))

    # Test 4: Document Retrieval (original) - use existing document ID
    results.append(test_tool(
        "Document Retrieval",
        "/resources/document/2",
        None
    ))

    # Test 6: Analyze Data
    results.append(test_tool(
        "Analyze Data",
        "/tools/analyze_data",
        {
            "data_source": "sales_data",
            "analysis_type": "descriptive",
            "filters": {"year": 2024}
        }
    ))

    # Test 7: Process CSV
    csv_content = "name,age,city\nJohn,30,NYC\nJane,25,LA\nBob,35,Chicago"
    csv_base64 = base64.b64encode(csv_content.encode()).decode()

    results.append(test_tool(
        "Process CSV",
        "/tools/process_csv",
        {
            "csv_data": csv_base64,
            "operation": "filter",
            "params": {"column": "city", "value": "NYC"}
        }
    ))

    # Test 8: Create Chart/Visualization
    results.append(test_tool(
        "Create Chart/Visualization",
        "/tools/generate_chart",
        {
            "data": [
                {"category": "A", "value": 10},
                {"category": "B", "value": 20},
                {"category": "C", "value": 30},
                {"category": "D", "value": 40},
                {"category": "E", "value": 50}
            ],
            "chart_type": "bar",
            "title": "Test Chart",
            "x_field": "category",
            "y_field": "value"
        }
    ))

    # Test 9: Semantic Search
    results.append(test_tool(
        "Semantic Search",
        "/tools/semantic_search",
        {
            "query": "product documentation",
            "context": "technical documentation",
            "limit": 10
        }
    ))

    # Test 10: Web Search
    results.append(test_tool(
        "Web Search",
        "/tools/web_search",
        {
            "query": "artificial intelligence trends 2024",
            "max_results": 5,
            "filters": {"date_range": "last_month"}
        }
    ))

    # Test 11: Find Similar Documents - use existing document ID
    results.append(test_tool(
        "Find Similar Documents",
        "/tools/find_similar_documents/2",
        None
    ))

    # Test 12: Generate Report
    results.append(test_tool(
        "Generate Report",
        "/tools/generate_report",
        {
            "template": "monthly_sales",
            "data": {"total_sales": 150000, "growth": 12.5},
            "format": "pdf"
        }
    ))

    # Test 13: Summarize Document - use existing document_id
    results.append(test_tool(
        "Summarize Document",
        "/tools/summarize_document",
        {
            "document_id": 2,
            "summary_length": 100,
            "language": "zh-TW"
        }
    ))

    # Test 14: Translate Text - field names must match model
    results.append(test_tool(
        "Translate Text",
        "/tools/translate_text",
        {
            "text": "Hello, how are you?",
            "source_lang": "en",
            "target_lang": "zh-TW"
        }
    ))

    # Test 15: Scan Sensitive Data
    results.append(test_tool(
        "Scan Sensitive Data",
        "/tools/scan_sensitive_data",
        {
            "text": "Contact John at john.doe@example.com or call 123-456-7890. SSN: 123-45-6789",
            "data_types": ["email", "phone", "ssn"]
        }
    ))

    # Test 16: Check Permissions - use resource_id not resource
    results.append(test_tool(
        "Check Permissions",
        "/tools/check_permissions",
        {
            "user_id": "user-123",
            "resource_id": "doc-789"
        }
    ))

    # Test 17: Audit Log - use action_type not action
    results.append(test_tool(
        "Audit Log",
        "/tools/audit_log",
        {
            "action_type": "data_access",
            "user_id": "user-123"
        }
    ))

    # Test 18: Create Task
    results.append(test_tool(
        "Create Task",
        "/tools/create_task",
        {
            "title": "Review Q4 Report",
            "description": "Review and approve Q4 financial report",
            "assignee": "user-456",
            "due_date": "2025-10-31",
            "priority": "high"
        }
    ))

    # Test 19: Send Notification - use recipients not user_id
    results.append(test_tool(
        "Send Notification",
        "/tools/send_notification",
        {
            "recipients": ["user-123", "user-456"],
            "message": "Task completed successfully",
            "channel": "email",
            "priority": "high"
        }
    ))

    # Test 20: Schedule Meeting - use duration and time_preferences
    results.append(test_tool(
        "Schedule Meeting",
        "/tools/schedule_meeting",
        {
            "participants": ["user-123", "user-456"],
            "duration": 60,
            "time_preferences": ["2025-10-20T10:00:00", "2025-10-20T14:00:00"]
        }
    ))

    # Test 21: Call API
    results.append(test_tool(
        "Call API",
        "/tools/call_api",
        {
            "url": "https://api.github.com/zen",
            "method": "GET",
            "headers": {},
            "timeout": 5
        }
    ))

    # Test 22: Execute SQL - query existing data
    results.append(test_tool(
        "Execute SQL",
        "/tools/execute_sql",
        {
            "query": "SELECT id, username, email FROM users LIMIT 3",
            "database": "default",
            "timeout": 30
        }
    ))

    # Test 23: Run Script - use script_code not code
    results.append(test_tool(
        "Run Script",
        "/tools/run_script",
        {
            "script_code": "print('Hello from script')",
            "input_params": {},
            "timeout": 30
        }
    ))

    # Test 24: Send Email
    results.append(test_tool(
        "Send Email",
        "/tools/send_email",
        {
            "to": ["user@example.com"],
            "subject": "Test Email",
            "body": "This is a test email",
            "attachments": []
        }
    ))

    # Test 25: Create Slack Message
    results.append(test_tool(
        "Create Slack Message",
        "/tools/create_slack_message",
        {
            "channel": "#general",
            "message": "Task completed successfully",
            "thread_id": None
        }
    ))

    # Test 26: Upload File
    results.append(test_tool(
        "Upload File",
        "/tools/upload_file",
        {
            "file_name": "test.txt",
            "file_data": base64.b64encode(b"test file content").decode(),
            "metadata": {"type": "document", "owner": "user-123"}
        }
    ))

    # Test 27: Download File
    results.append(test_tool(
        "Download File",
        "/tools/download_file",
        {
            "file_id": "file-789"
        }
    ))

    # Test 28: List Files
    results.append(test_tool(
        "List Files",
        "/tools/list_files",
        {
            "folder": "/documents",
            "filters": {"type": "pdf"},
            "sort_by": "date"
        }
    ))

    # Test 29: Calculate Metrics - use data_range not data
    results.append(test_tool(
        "Calculate Metrics",
        "/tools/calculate_metrics",
        {
            "metric_type": "revenue",
            "data_range": {"start_date": "2025-01-01", "end_date": "2025-10-16"},
            "dimensions": ["region", "product"]
        }
    ))

    # Test 30: Financial Calculator
    results.append(test_tool(
        "Financial Calculator",
        "/tools/financial_calculator",
        {
            "operation": "roi",
            "values": {"gain": 15000, "cost": 10000}
        }
    ))

    # Print Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(results)
    total = len(results)

    print(f"Total Tests: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {total - passed} ❌")
    print(f"Success Rate: {(passed/total)*100:.1f}%")

    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")

if __name__ == "__main__":
    main()
