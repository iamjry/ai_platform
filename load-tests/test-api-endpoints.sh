#!/bin/bash

###############################################################################
# AI Platform - API Load Testing Script
# Tests all major API endpoints with concurrent users
###############################################################################

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8001}"
CONCURRENT_USERS="${CONCURRENT_USERS:-10}"
TOTAL_REQUESTS="${TOTAL_REQUESTS:-1000}"
TEST_DURATION="${TEST_DURATION:-60}"  # seconds

# Test data
TEST_QUERY="What is artificial intelligence?"
TEST_DOCUMENT_ID=1

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  AI Platform - API Load Testing${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""
echo "Configuration:"
echo "  Base URL: ${BASE_URL}"
echo "  Concurrent Users: ${CONCURRENT_USERS}"
echo "  Total Requests: ${TOTAL_REQUESTS}"
echo "  Test Duration: ${TEST_DURATION}s"
echo ""

# Check dependencies
command -v curl >/dev/null 2>&1 || { echo "Error: curl is required"; exit 1; }
command -v jq >/dev/null 2>&1 || echo "Warning: jq not found (pretty printing disabled)"

# Create results directory
RESULTS_DIR="./results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "${RESULTS_DIR}"

echo -e "${YELLOW}Starting load tests...${NC}"
echo ""

###############################################################################
# Test 1: Health Check Endpoint
###############################################################################

echo -e "${BLUE}[Test 1/6]${NC} Health Check Endpoint"
echo "  Testing: GET ${BASE_URL}/health"

ab -n ${TOTAL_REQUESTS} -c ${CONCURRENT_USERS} \
    -g "${RESULTS_DIR}/health_check.tsv" \
    "${BASE_URL}/health" > "${RESULTS_DIR}/health_check.txt" 2>&1

if [ $? -eq 0 ]; then
    REQUESTS_PER_SEC=$(grep "Requests per second" "${RESULTS_DIR}/health_check.txt" | awk '{print $4}')
    echo -e "  ${GREEN}✓ Complete${NC} - ${REQUESTS_PER_SEC} req/sec"
else
    echo -e "  ${RED}✗ Failed${NC}"
fi
echo ""

###############################################################################
# Test 2: Search Knowledge Base
###############################################################################

echo -e "${BLUE}[Test 2/6]${NC} Search Knowledge Base"
echo "  Testing: POST ${BASE_URL}/tools/search_knowledge_base"

# Create test payload
cat > "${RESULTS_DIR}/search_payload.json" << PAYLOAD
{
  "query": "${TEST_QUERY}",
  "limit": 5
}
PAYLOAD

# Run concurrent tests
for i in $(seq 1 ${CONCURRENT_USERS}); do
    (
        for j in $(seq 1 $((TOTAL_REQUESTS / CONCURRENT_USERS))); do
            curl -s -X POST "${BASE_URL}/tools/search_knowledge_base" \
                -H "Content-Type: application/json" \
                -d @"${RESULTS_DIR}/search_payload.json" \
                -w "%{http_code},%{time_total}\n" \
                -o /dev/null >> "${RESULTS_DIR}/search_results.csv"
        done
    ) &
done

wait

SUCCESSFUL=$(grep "^200" "${RESULTS_DIR}/search_results.csv" | wc -l)
AVG_TIME=$(awk -F',' '{sum+=$2; count++} END {print sum/count}' "${RESULTS_DIR}/search_results.csv")
echo -e "  ${GREEN}✓ Complete${NC} - ${SUCCESSFUL}/${TOTAL_REQUESTS} successful, avg ${AVG_TIME}s"
echo ""

###############################################################################
# Test 3: Semantic Search
###############################################################################

echo -e "${BLUE}[Test 3/6]${NC} Semantic Search"
echo "  Testing: POST ${BASE_URL}/tools/semantic_search"

cat > "${RESULTS_DIR}/semantic_payload.json" << PAYLOAD
{
  "query": "${TEST_QUERY}",
  "top_k": 5,
  "similarity_threshold": 0.7
}
PAYLOAD

for i in $(seq 1 ${CONCURRENT_USERS}); do
    (
        for j in $(seq 1 $((TOTAL_REQUESTS / CONCURRENT_USERS))); do
            curl -s -X POST "${BASE_URL}/tools/semantic_search" \
                -H "Content-Type: application/json" \
                -d @"${RESULTS_DIR}/semantic_payload.json" \
                -w "%{http_code},%{time_total}\n" \
                -o /dev/null >> "${RESULTS_DIR}/semantic_results.csv"
        done
    ) &
done

wait

SUCCESSFUL=$(grep "^200" "${RESULTS_DIR}/semantic_results.csv" | wc -l)
AVG_TIME=$(awk -F',' '{sum+=$2; count++} END {print sum/count}' "${RESULTS_DIR}/semantic_results.csv")
echo -e "  ${GREEN}✓ Complete${NC} - ${SUCCESSFUL}/${TOTAL_REQUESTS} successful, avg ${AVG_TIME}s"
echo ""

###############################################################################
# Test 4: Web Search
###############################################################################

echo -e "${BLUE}[Test 4/6]${NC} Web Search"
echo "  Testing: POST ${BASE_URL}/tools/web_search"

cat > "${RESULTS_DIR}/web_search_payload.json" << PAYLOAD
{
  "query": "latest AI developments",
  "num_results": 3
}
PAYLOAD

# Reduce requests for expensive web search
WEB_REQUESTS=$((TOTAL_REQUESTS / 10))

for i in $(seq 1 ${CONCURRENT_USERS}); do
    (
        for j in $(seq 1 $((WEB_REQUESTS / CONCURRENT_USERS))); do
            curl -s -X POST "${BASE_URL}/tools/web_search" \
                -H "Content-Type: application/json" \
                -d @"${RESULTS_DIR}/web_search_payload.json" \
                -w "%{http_code},%{time_total}\n" \
                -o /dev/null >> "${RESULTS_DIR}/web_search_results.csv"
        done
    ) &
done

wait

SUCCESSFUL=$(grep "^200" "${RESULTS_DIR}/web_search_results.csv" | wc -l)
AVG_TIME=$(awk -F',' '{sum+=$2; count++} END {print sum/count}' "${RESULTS_DIR}/web_search_results.csv")
echo -e "  ${GREEN}✓ Complete${NC} - ${SUCCESSFUL}/${WEB_REQUESTS} successful, avg ${AVG_TIME}s"
echo ""

###############################################################################
# Test 5: Get Document
###############################################################################

echo -e "${BLUE}[Test 5/6]${NC} Get Document"
echo "  Testing: POST ${BASE_URL}/tools/get_document"

cat > "${RESULTS_DIR}/get_doc_payload.json" << PAYLOAD
{
  "document_id": ${TEST_DOCUMENT_ID}
}
PAYLOAD

for i in $(seq 1 ${CONCURRENT_USERS}); do
    (
        for j in $(seq 1 $((TOTAL_REQUESTS / CONCURRENT_USERS))); do
            curl -s -X POST "${BASE_URL}/tools/get_document" \
                -H "Content-Type: application/json" \
                -d @"${RESULTS_DIR}/get_doc_payload.json" \
                -w "%{http_code},%{time_total}\n" \
                -o /dev/null >> "${RESULTS_DIR}/get_doc_results.csv"
        done
    ) &
done

wait

SUCCESSFUL=$(grep "^200" "${RESULTS_DIR}/get_doc_results.csv" | wc -l)
AVG_TIME=$(awk -F',' '{sum+=$2; count++} END {print sum/count}' "${RESULTS_DIR}/get_doc_results.csv")
echo -e "  ${GREEN}✓ Complete${NC} - ${SUCCESSFUL}/${TOTAL_REQUESTS} successful, avg ${AVG_TIME}s"
echo ""

###############################################################################
# Test 6: Query Database
###############################################################################

echo -e "${BLUE}[Test 6/6]${NC} Query Database"
echo "  Testing: POST ${BASE_URL}/tools/query_database"

cat > "${RESULTS_DIR}/query_db_payload.json" << PAYLOAD
{
  "query_type": "get_users",
  "parameters": {}
}
PAYLOAD

for i in $(seq 1 ${CONCURRENT_USERS}); do
    (
        for j in $(seq 1 $((TOTAL_REQUESTS / CONCURRENT_USERS))); do
            curl -s -X POST "${BASE_URL}/tools/query_database" \
                -H "Content-Type: application/json" \
                -d @"${RESULTS_DIR}/query_db_payload.json" \
                -w "%{http_code},%{time_total}\n" \
                -o /dev/null >> "${RESULTS_DIR}/query_db_results.csv"
        done
    ) &
done

wait

SUCCESSFUL=$(grep "^200" "${RESULTS_DIR}/query_db_results.csv" | wc -l)
AVG_TIME=$(awk -F',' '{sum+=$2; count++} END {print sum/count}' "${RESULTS_DIR}/query_db_results.csv")
echo -e "  ${GREEN}✓ Complete${NC} - ${SUCCESSFUL}/${TOTAL_REQUESTS} successful, avg ${AVG_TIME}s"
echo ""

###############################################################################
# Generate Summary Report
###############################################################################

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Test Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

cat > "${RESULTS_DIR}/SUMMARY.txt" << SUMMARY
AI Platform Load Test Summary
=============================
Date: $(date)
Configuration:
  - Base URL: ${BASE_URL}
  - Concurrent Users: ${CONCURRENT_USERS}
  - Total Requests: ${TOTAL_REQUESTS}

Results:
--------
1. Health Check: $(grep "Requests per second" "${RESULTS_DIR}/health_check.txt" | awk '{print $4}') req/sec
2. Search Knowledge Base: $(grep "^200" "${RESULTS_DIR}/search_results.csv" | wc -l)/${TOTAL_REQUESTS} successful
3. Semantic Search: $(grep "^200" "${RESULTS_DIR}/semantic_results.csv" | wc -l)/${TOTAL_REQUESTS} successful
4. Web Search: $(grep "^200" "${RESULTS_DIR}/web_search_results.csv" | wc -l)/${WEB_REQUESTS} successful
5. Get Document: $(grep "^200" "${RESULTS_DIR}/get_doc_results.csv" | wc -l)/${TOTAL_REQUESTS} successful
6. Query Database: $(grep "^200" "${RESULTS_DIR}/query_db_results.csv" | wc -l)/${TOTAL_REQUESTS} successful

All results saved to: ${RESULTS_DIR}/
SUMMARY

cat "${RESULTS_DIR}/SUMMARY.txt"

echo ""
echo -e "${GREEN}Load testing complete!${NC}"
echo -e "Results directory: ${YELLOW}${RESULTS_DIR}${NC}"
echo ""
