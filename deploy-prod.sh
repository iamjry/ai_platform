#!/bin/bash
# Production Deployment Script for AI Platform
# Target: RHEL 9 with 2x Nvidia H100 GPUs

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  $1"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "請不要以 root 身分執行此腳本"
    exit 1
fi

print_header "AI Platform 生產環境部署腳本"

# Check prerequisites
print_info "檢查系統需求..."

# Check RHEL version
if [ -f /etc/redhat-release ]; then
    RHEL_VERSION=$(cat /etc/redhat-release)
    print_success "作業系統: $RHEL_VERSION"
else
    print_error "無法檢測 RHEL 版本"
    exit 1
fi

# Check Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    print_success "$DOCKER_VERSION"
else
    print_error "Docker 未安裝，請先安裝 Docker"
    exit 1
fi

# Check Docker Compose
if docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version)
    print_success "$COMPOSE_VERSION"
else
    print_error "Docker Compose 未安裝"
    exit 1
fi

# Check NVIDIA Driver
if command -v nvidia-smi &> /dev/null; then
    print_success "NVIDIA Driver 已安裝"
    GPU_COUNT=$(nvidia-smi --list-gpus | wc -l)
    print_info "檢測到 $GPU_COUNT 張 GPU"

    if [ "$GPU_COUNT" -lt 2 ]; then
        print_warning "預期有 2 張 GPU，但只檢測到 $GPU_COUNT 張"
        read -p "是否繼續部署？(y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    print_error "NVIDIA Driver 未安裝"
    exit 1
fi

# Check NVIDIA Container Toolkit
if docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    print_success "NVIDIA Container Toolkit 運作正常"
else
    print_error "NVIDIA Container Toolkit 無法運作"
    print_info "請執行: sudo nvidia-ctk runtime configure --runtime=docker"
    exit 1
fi

# Check environment file
print_header "檢查環境配置"

if [ ! -f .env.prod ]; then
    print_warning ".env.prod 不存在"

    if [ -f .env.prod.template ]; then
        print_info "從範本創建 .env.prod..."
        cp .env.prod.template .env.prod
        chmod 600 .env.prod

        print_warning "請編輯 .env.prod 並填入實際的配置值"
        print_info "必須配置的項目："
        echo "  - POSTGRES_PASSWORD"
        echo "  - REDIS_PASSWORD"
        echo "  - RABBITMQ_DEFAULT_PASS"
        echo "  - OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY"
        echo "  - LITELLM_MASTER_KEY"
        echo "  - GRAFANA_ADMIN_PASSWORD"
        echo ""

        read -p "是否現在編輯 .env.prod？(Y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            ${EDITOR:-vim} .env.prod
        else
            print_warning "請手動編輯 .env.prod 後再次執行此腳本"
            exit 1
        fi
    else
        print_error ".env.prod.template 也不存在"
        exit 1
    fi
fi

print_success ".env.prod 已存在"

# Verify critical environment variables
print_info "驗證關鍵環境變數..."
source .env.prod

REQUIRED_VARS=(
    "POSTGRES_PASSWORD"
    "REDIS_PASSWORD"
    "RABBITMQ_DEFAULT_PASS"
)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ] || [ "${!var}" = "<STRONG_PASSWORD_HERE>" ] || [ "${!var}" = "<STRONG_REDIS_PASSWORD_HERE>" ] || [ "${!var}" = "<STRONG_MQ_PASSWORD_HERE>" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    print_error "以下環境變數尚未配置："
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    exit 1
fi

print_success "環境變數驗證通過"

# Ask for deployment mode
print_header "選擇部署模式"

echo "1) 完整部署 (建構映像檔 + 啟動服務)"
echo "2) 僅建構映像檔"
echo "3) 僅啟動服務 (假設映像檔已建構)"
echo "4) 更新並重啟服務"
read -p "請選擇 [1-4]: " -n 1 -r DEPLOY_MODE
echo ""

case $DEPLOY_MODE in
    1)
        print_header "開始完整部署"
        SHOULD_BUILD=true
        SHOULD_START=true
        ;;
    2)
        print_header "開始建構映像檔"
        SHOULD_BUILD=true
        SHOULD_START=false
        ;;
    3)
        print_header "開始啟動服務"
        SHOULD_BUILD=false
        SHOULD_START=true
        ;;
    4)
        print_header "開始更新並重啟"
        SHOULD_BUILD=true
        SHOULD_START=true
        print_info "將執行 docker compose down 後重新建構和啟動"
        docker compose --env-file .env.prod -f docker-compose.prod.yml down
        ;;
    *)
        print_error "無效的選擇"
        exit 1
        ;;
esac

# Build images
if [ "$SHOULD_BUILD" = true ]; then
    print_header "建構 Docker 映像檔"

    print_info "此過程可能需要 20-40 分鐘 (首次建構)"
    print_info "建構 MCP Server (含 GPU 支援)..."

    docker compose --env-file .env.prod -f docker-compose.prod.yml build --no-cache

    if [ $? -eq 0 ]; then
        print_success "映像檔建構完成"
    else
        print_error "映像檔建構失敗"
        exit 1
    fi
fi

# Start services
if [ "$SHOULD_START" = true ]; then
    print_header "啟動服務"

    # Start in phases
    print_info "階段 1: 啟動資料庫服務..."
    docker compose --env-file .env.prod -f docker-compose.prod.yml up -d postgres redis qdrant rabbitmq

    print_info "等待資料庫就緒 (30秒)..."
    sleep 30

    print_info "階段 2: 啟動 LiteLLM 和 Ollama..."
    docker compose --env-file .env.prod -f docker-compose.prod.yml up -d litellm ollama

    print_info "等待 LLM 服務就緒 (20秒)..."
    sleep 20

    print_info "階段 3: 啟動 MCP Server (含 GPU)..."
    docker compose --env-file .env.prod -f docker-compose.prod.yml up -d mcp-server

    print_info "等待 MCP Server 初始化 (可能需要載入 GPU 模型，最多 2 分鐘)..."
    sleep 60

    print_info "階段 4: 啟動 Agent Service 和 Web UI..."
    docker compose --env-file .env.prod -f docker-compose.prod.yml up -d agent-service web-ui

    print_info "階段 5: 啟動監控服務..."
    docker compose --env-file .env.prod -f docker-compose.prod.yml up -d prometheus grafana

    print_success "所有服務已啟動"

    print_info "等待服務完全就緒 (30秒)..."
    sleep 30
fi

# Health check
print_header "健康檢查"

check_service() {
    local url=$1
    local name=$2

    if curl -sf "$url" > /dev/null 2>&1; then
        print_success "$name: Healthy"
        return 0
    else
        print_error "$name: Unhealthy"
        return 1
    fi
}

HEALTH_STATUS=0

check_service "http://localhost:8501/_stcore/health" "Web UI" || HEALTH_STATUS=1
check_service "http://localhost:8002/health" "Agent Service" || HEALTH_STATUS=1
check_service "http://localhost:8001/health" "MCP Server" || HEALTH_STATUS=1
check_service "http://localhost:4000/health/readiness" "LiteLLM" || HEALTH_STATUS=1
check_service "http://localhost:9090/-/healthy" "Prometheus" || HEALTH_STATUS=1
check_service "http://localhost:3000/api/health" "Grafana" || HEALTH_STATUS=1

# Check GPU usage
print_header "GPU 狀態"

if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader

    print_info "檢查容器 GPU 配置..."

    # Check Ollama GPU
    OLLAMA_GPU=$(docker inspect ai-ollama-prod 2>/dev/null | jq -r '.[0].HostConfig.DeviceRequests[0].DeviceIDs[0]' 2>/dev/null || echo "N/A")
    if [ "$OLLAMA_GPU" != "N/A" ]; then
        print_success "Ollama 使用 GPU: $OLLAMA_GPU"
    else
        print_warning "Ollama GPU 配置未檢測到"
    fi

    # Check MCP Server GPU
    MCP_GPU=$(docker inspect ai-mcp-server-prod 2>/dev/null | jq -r '.[0].HostConfig.DeviceRequests[0].DeviceIDs[0]' 2>/dev/null || echo "N/A")
    if [ "$MCP_GPU" != "N/A" ]; then
        print_success "MCP Server 使用 GPU: $MCP_GPU"
    else
        print_warning "MCP Server GPU 配置未檢測到"
    fi
fi

# Test OCR
print_header "OCR 功能測試"

OCR_STATUS=$(curl -s http://localhost:8001/tools/ocr_get_status 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "$OCR_STATUS" | jq .

    DEEPSEEK_AVAILABLE=$(echo "$OCR_STATUS" | jq -r '.backends[] | select(.name=="DeepSeek-OCR") | .available' 2>/dev/null)
    if [ "$DEEPSEEK_AVAILABLE" = "true" ]; then
        print_success "DeepSeek-OCR (GPU) 已啟用"
    else
        print_warning "DeepSeek-OCR (GPU) 未啟用，使用 EasyOCR (CPU) 作為後備"
    fi
else
    print_error "無法測試 OCR 功能"
fi

# Display service URLs
print_header "部署完成"

if [ $HEALTH_STATUS -eq 0 ]; then
    print_success "所有服務健康運行"
else
    print_warning "部分服務未能通過健康檢查，請查看日誌"
fi

echo ""
echo "服務訪問地址："
echo "  Web UI:        http://$(hostname -I | awk '{print $1}'):8501"
echo "  Agent Service: http://$(hostname -I | awk '{print $1}'):8002"
echo "  MCP Server:    http://$(hostname -I | awk '{print $1}'):8001"
echo "  LiteLLM:       http://$(hostname -I | awk '{print $1}'):4000"
echo "  Grafana:       http://$(hostname -I | awk '{print $1}'):3000"
echo "  Prometheus:    http://$(hostname -I | awk '{print $1}'):9090"
echo ""

print_info "查看服務日誌："
echo "  docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f <service_name>"
echo ""

print_info "查看所有服務狀態："
echo "  docker compose --env-file .env.prod -f docker-compose.prod.yml ps"
echo ""

print_info "監控 GPU 使用："
echo "  watch -n 1 nvidia-smi"
echo ""

print_success "部署完成！🎉"
