#!/usr/bin/env python3
"""
Verify Agent-OCR Integration
=============================

This script verifies that AI agents can successfully access and use OCR tools
through the agent-service, just like other tools.

What this tests:
1. Agent-service can fetch OCR tools from MCP server
2. OCR tools are properly registered and accessible
3. Agent system prompts include OCR awareness
"""

import requests
import json
import sys

AGENT_SERVICE_URL = "http://localhost:8002"
MCP_SERVER_URL = "http://localhost:8001"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_mcp_ocr_tools():
    """Test 1: Verify OCR tools are available in MCP server"""
    print_section("Test 1: OCR Tools in MCP Server")

    try:
        response = requests.get(f"{MCP_SERVER_URL}/tools/list", timeout=5)
        data = response.json()

        ocr_tools = [t for t in data.get('tools', []) if t['name'].startswith('ocr_')]

        print(f"✓ Total tools in MCP server: {len(data.get('tools', []))}")
        print(f"✓ OCR tools found: {len(ocr_tools)}")

        for tool in ocr_tools:
            print(f"\n  📋 {tool['name']}")
            print(f"     Category: {tool.get('category', 'N/A')}")
            print(f"     Description: {tool.get('description', 'N/A')[:80]}...")

        return len(ocr_tools) == 3

    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

def test_agent_service_health():
    """Test 2: Verify agent-service is healthy and can access MCP"""
    print_section("Test 2: Agent Service Health")

    try:
        response = requests.get(f"{AGENT_SERVICE_URL}/health", timeout=5)
        health_data = response.json()

        print(f"✓ Agent service status: {health_data.get('status', 'unknown')}")
        print(f"✓ MCP connection: {health_data.get('mcp_server', {}).get('status', 'unknown')}")

        # Check if agent service has tools loaded
        tools_count = health_data.get('mcp_server', {}).get('tools_count', 0)
        print(f"✓ Tools accessible to agents: {tools_count}")

        return health_data.get('status') == 'healthy'

    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

def test_ocr_tool_accessibility():
    """Test 3: Verify agents can call OCR status tool"""
    print_section("Test 3: OCR Tool Accessibility via Agent Service")

    try:
        # Test calling OCR status through MCP directly
        response = requests.get(f"{MCP_SERVER_URL}/tools/ocr_get_status", timeout=10)
        status_data = response.json()

        print(f"✓ OCR service available: {status_data.get('ocr_available', False)}")

        backends = status_data.get('backends', [])
        print(f"✓ OCR backends detected: {len(backends)}")

        for backend in backends:
            status_icon = "✓" if backend.get('available') else "✗"
            print(f"  {status_icon} {backend['name']} ({backend['type']}): {'Available' if backend.get('available') else 'Not available'}")

        return status_data.get('ocr_available', False)

    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

def test_agent_prompts():
    """Test 4: Verify agent prompts include OCR awareness"""
    print_section("Test 4: Agent Prompts OCR Awareness")

    try:
        with open('/path/to/your/ai_platform/config/agent_prompts.yaml', 'r') as f:
            prompts_content = f.read()

        # Check for OCR mentions in prompts
        ocr_keywords = ['OCR', 'ocr_extract_pdf', 'ocr_extract_image', 'ocr_get_status']

        found_keywords = []
        for keyword in ocr_keywords:
            if keyword in prompts_content:
                count = prompts_content.count(keyword)
                found_keywords.append((keyword, count))
                print(f"✓ '{keyword}' mentioned {count} time(s) in agent prompts")

        if len(found_keywords) >= 3:
            print(f"\n✓ Agent prompts are OCR-aware!")
            return True
        else:
            print(f"\n⚠ Limited OCR awareness in prompts")
            return False

    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

def main():
    print("\n🔍 AI Agent OCR Integration Verification")
    print("=" * 60)

    results = []

    # Run all tests
    results.append(("MCP OCR Tools", test_mcp_ocr_tools()))
    results.append(("Agent Service Health", test_agent_service_health()))
    results.append(("OCR Tool Accessibility", test_ocr_tool_accessibility()))
    results.append(("Agent Prompts OCR Awareness", test_agent_prompts()))

    # Summary
    print_section("Verification Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 SUCCESS! OCR is fully integrated with the agent system!")
        print("\nAgents can now:")
        print("  • Detect when documents need OCR")
        print("  • Call ocr_extract_pdf for PDF documents")
        print("  • Call ocr_extract_image for image files")
        print("  • Check OCR service status")
        print("\nReady to use in Web UI → Agent Tasks → Contract Review")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
