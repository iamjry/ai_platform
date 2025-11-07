#!/bin/bash
# Health Check Script for AI Platform Production
# Monitors services, GPU, and system resources

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo ""
    echo "════════════════════════════════════════════════════"
    echo "  $1"
    echo "════════════════════════════════════════════════════"
}

print_check() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅${NC} $2"
    else
        echo -e "${RED}❌${NC} $2"
    fi
}

# Timestamp
echo ""
echo "Health Check at: $(date '+%Y-%m-%d %H:%M:%S')"

# Docker Services Status
print_header "Docker Services Status"

SERVICES=(
    "ai-postgres-prod:PostgreSQL"
    "ai-redis-prod:Redis"
    "ai-qdrant-prod:Qdrant"
    "ai-rabbitmq-prod:RabbitMQ"
    "ai-ollama-prod:Ollama"
    "ai-litellm-prod:LiteLLM"
    "ai-mcp-server-prod:MCP Server"
    "ai-agent-service-prod:Agent Service"
    "ai-web-ui-prod:Web UI"
    "ai-prometheus-prod:Prometheus"
    "ai-grafana-prod:Grafana"
)

for service in "${SERVICES[@]}"; do
    IFS=':' read -r container_name service_name <<< "$service"

    if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        health=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "running")

        if [ "$health" = "healthy" ] || [ "$health" = "running" ]; then
            print_check 0 "$service_name ($container_name)"
        else
            print_check 1 "$service_name ($container_name) - Status: $health"
        fi
    else
        print_check 1 "$service_name ($container_name) - Not running"
    fi
done

# HTTP Health Endpoints
print_header "HTTP Health Endpoints"

check_http() {
    local url=$1
    local name=$2

    if curl -sf "$url" > /dev/null 2>&1; then
        print_check 0 "$name - $url"
    else
        print_check 1 "$name - $url"
    fi
}

check_http "http://localhost:8501/_stcore/health" "Web UI"
check_http "http://localhost:8002/health" "Agent Service"
check_http "http://localhost:8001/health" "MCP Server"
check_http "http://localhost:4000/health/readiness" "LiteLLM"
check_http "http://localhost:9090/-/healthy" "Prometheus"
check_http "http://localhost:3000/api/health" "Grafana"

# GPU Status
if command -v nvidia-smi &> /dev/null; then
    print_header "GPU Status"

    nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,utilization.memory,memory.used,memory.total --format=csv,noheader | while IFS=, read -r idx name temp gpu_util mem_util mem_used mem_total; do
        echo "GPU $idx: $name"
        echo "  Temperature: ${temp}"
        echo "  GPU Utilization: ${gpu_util}"
        echo "  Memory Utilization: ${mem_util}"
        echo "  Memory: ${mem_used} / ${mem_total}"
        echo ""
    done

    # Check GPU assignment
    echo "GPU Assignment:"

    OLLAMA_GPU=$(docker inspect ai-ollama-prod 2>/dev/null | jq -r '.[0].HostConfig.DeviceRequests[0].DeviceIDs[0]' 2>/dev/null || echo "N/A")
    if [ "$OLLAMA_GPU" != "N/A" ]; then
        print_check 0 "Ollama assigned to GPU $OLLAMA_GPU"
    else
        print_check 1 "Ollama GPU assignment not detected"
    fi

    MCP_GPU=$(docker inspect ai-mcp-server-prod 2>/dev/null | jq -r '.[0].HostConfig.DeviceRequests[0].DeviceIDs[0]' 2>/dev/null || echo "N/A")
    if [ "$MCP_GPU" != "N/A" ]; then
        print_check 0 "MCP Server assigned to GPU $MCP_GPU"
    else
        print_check 1 "MCP Server GPU assignment not detected"
    fi
fi

# OCR Status
print_header "OCR Status"

OCR_STATUS=$(curl -s http://localhost:8001/tools/ocr_get_status 2>/dev/null)
if [ $? -eq 0 ]; then
    OCR_AVAILABLE=$(echo "$OCR_STATUS" | jq -r '.ocr_available' 2>/dev/null)

    if [ "$OCR_AVAILABLE" = "true" ]; then
        print_check 0 "OCR Service Available"

        # Check each backend
        EASYOCR=$(echo "$OCR_STATUS" | jq -r '.backends[] | select(.name=="EasyOCR") | .available' 2>/dev/null)
        DEEPSEEK=$(echo "$OCR_STATUS" | jq -r '.backends[] | select(.name=="DeepSeek-OCR") | .available' 2>/dev/null)

        [ "$EASYOCR" = "true" ] && print_check 0 "EasyOCR (CPU) Backend" || print_check 1 "EasyOCR (CPU) Backend"
        [ "$DEEPSEEK" = "true" ] && print_check 0 "DeepSeek-OCR (GPU) Backend" || print_check 1 "DeepSeek-OCR (GPU) Backend"
    else
        print_check 1 "OCR Service Unavailable"
    fi
else
    print_check 1 "Cannot query OCR status"
fi

# System Resources
print_header "System Resources"

# Disk usage
echo "Disk Usage:"
df -h | grep -E '^(/dev/|Filesystem)' | awk '{printf "  %-20s %5s %5s %5s %5s\n", $1, $2, $3, $4, $5}'

# Memory
echo ""
echo "Memory Usage:"
free -h | awk 'NR==1 || NR==2 {printf "  %-10s %7s %7s %7s\n", $1, $2, $3, $4}'

# Docker volumes
echo ""
echo "Docker Volumes:"
docker system df -v | grep -A 10 "Local Volumes" | tail -n +2 | head -n 10

# Container resource usage
print_header "Container Resource Usage"

docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" | head -n 12

# Summary
print_header "Summary"

TOTAL_SERVICES=11
RUNNING_SERVICES=$(docker ps --filter "name=ai-" --format '{{.Names}}' | wc -l)

echo "Services Running: $RUNNING_SERVICES / $TOTAL_SERVICES"

if [ $RUNNING_SERVICES -eq $TOTAL_SERVICES ]; then
    echo -e "${GREEN}✅ All services are running${NC}"
else
    echo -e "${YELLOW}⚠️  Some services are not running${NC}"
fi

# GPU Count
if command -v nvidia-smi &> /dev/null; then
    GPU_COUNT=$(nvidia-smi --list-gpus | wc -l)
    echo "GPUs Detected: $GPU_COUNT"

    if [ "$GPU_COUNT" -eq 2 ]; then
        echo -e "${GREEN}✅ Expected GPU count${NC}"
    else
        echo -e "${YELLOW}⚠️  Expected 2 GPUs, found $GPU_COUNT${NC}"
    fi
fi

echo ""
echo "Last checked: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
