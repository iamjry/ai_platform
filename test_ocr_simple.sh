#!/bin/bash
# Simple OCR Testing Script (using curl)

echo "=========================================="
echo "OCR Testing Suite (curl-based)"
echo "=========================================="

MCP_SERVER="http://localhost:8001"

# Test 1: Check OCR Status
echo ""
echo "Test 1: OCR Service Status"
echo "=========================================="
curl -s $MCP_SERVER/tools/ocr_get_status | jq '{
  available: .ocr_available,
  backends: [.backends[] | {name: .name, available: .available}]
}'

# Test 2: Check if tools are registered
echo ""
echo "Test 2: OCR Tools Registration"
echo "=========================================="
curl -s $MCP_SERVER/tools/list | jq '[.tools[] | select(.name | startswith("ocr_"))] | .[] | {name, description, category}'

# Test 3: Check MCP server root
echo ""
echo "Test 3: MCP Server Info"
echo "=========================================="
curl -s $MCP_SERVER/ | jq '{
  service,
  version,
  status,
  tools_count,
  features
}'

echo ""
echo "=========================================="
echo "Basic tests complete!"
echo "=========================================="
echo ""
echo "To test with actual documents:"
echo "  1. Copy a PDF into the container:"
echo "     docker cp your-file.pdf ai-mcp-server:/tmp/test.pdf"
echo ""
echo "  2. Test OCR on the PDF:"
echo "     curl -X POST $MCP_SERVER/tools/ocr_extract_pdf \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"pdf_file\": \"/tmp/test.pdf\"}' | jq ."
echo ""
