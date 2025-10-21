#!/bin/bash
set -e

# AI平台MVP一鍵部署腳本
# 使用方法: ./deploy.sh [start|stop|restart|status|clean]

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 項目名稱
PROJECT_NAME="ai-platform-mvp"

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查先決條件
check_prerequisites() {
    log_info "檢查系統需求..."
    
    # 檢查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安裝，請先安裝Docker"
        exit 1
    fi
    log_success "Docker已安裝: $(docker --version)"
    
    # 檢查Docker Compose
    if ! command -v docker compose &> /dev/null; then
        log_error "Docker Compose未安裝"
        exit 1
    fi
    log_success "Docker Compose已安裝: $(docker compose version)"
    
    # 檢查磁碟空間（至少需要20GB）
    available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -lt 20 ]; then
        log_warning "可用磁碟空間不足20GB，當前: ${available_space}GB"
    fi
    
    # 檢查記憶體（至少需要8GB）
    total_mem=$(free -g | awk 'NR==2 {print $2}')
    if [ "$total_mem" -lt 8 ]; then
        log_warning "系統記憶體不足8GB，當前: ${total_mem}GB"
    fi
    
    # 檢查GPU（可選）
    if command -v nvidia-smi &> /dev/null; then
        log_success "檢測到NVIDIA GPU"
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
        ENABLE_GPU=true
    else
        log_warning "未檢測到GPU，將使用CPU模式"
        ENABLE_GPU=false
    fi
}

# 創建目錄結構
create_directory_structure() {
    log_info "創建目錄結構..."
    
    mkdir -p {config,data,logs,models,scripts,services/{gateway,mcp-server,agent-service,web-ui}}
    mkdir -p config/grafana/{dashboards,datasources}
    
    log_success "目錄結構創建完成"
}

# 生成.env文件
generate_env_file() {
    if [ -f .env ]; then
        log_warning ".env文件已存在，跳過生成"
        return
    fi
    
    log_info "生成.env配置文件..."
    
    # 讀取API Keys（如果有）
    read -p "請輸入OpenAI API Key (按Enter跳過): " OPENAI_KEY
    read -p "請輸入Anthropic API Key (按Enter跳過): " ANTHROPIC_KEY
    
    # 生成隨機密碼
    POSTGRES_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    REDIS_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    RABBITMQ_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    cat > .env << EOF
# API金鑰
OPENAI_API_KEY=${OPENAI_KEY:-sk-your-openai-api-key}
ANTHROPIC_API_KEY=${ANTHROPIC_KEY:-sk-ant-your-anthropic-api-key}

# 資料庫配置
POSTGRES_USER=admin
POSTGRES_PASSWORD=${POSTGRES_PASS}
POSTGRES_DB=ai_platform

# Redis配置
REDIS_PASSWORD=${REDIS_PASS}

# RabbitMQ配置
RABBITMQ_DEFAULT_USER=admin
RABBITMQ_DEFAULT_PASS=${RABBITMQ_PASS}

# 應用配置
ENVIRONMENT=production
LOG_LEVEL=info
MAX_CONCURRENT_REQUESTS=100

# GPU配置
ENABLE_GPU=${ENABLE_GPU}
GPU_MEMORY_UTILIZATION=0.9
EOF
    
    log_success ".env文件創建完成"
    log_warning "重要: 請妥善保管.env文件中的密碼！"
}

# 下載配置文件
download_configs() {
    log_info "準備配置文件..."
    
    # 這裡可以從遠端倉庫下載或使用預設配置
    # 為簡化，我們使用內嵌配置
    
    # Grafana數據源配置
    cat > config/grafana/datasources/prometheus.yml << 'EOF'
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF
    
    # Grafana儀表板配置
    cat > config/grafana/dashboards/dashboard.yml << 'EOF'
apiVersion: 1
providers:
  - name: 'Default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF
    
    log_success "配置文件準備完成"
}

# 構建服務鏡像
build_images() {
    log_info "構建Docker鏡像..."
    
    # 檢查服務目錄是否包含必要文件
    local services=("mcp-server" "agent-service" "web-ui")
    
    for service in "${services[@]}"; do
        if [ ! -f "services/${service}/Dockerfile" ]; then
            log_error "缺少 services/${service}/Dockerfile"
            log_info "請確保已按文檔創建所有服務代碼"
            exit 1
        fi
    done
    
    docker compose build --no-cache
    
    log_success "鏡像構建完成"
}

# 啟動服務
start_services() {
    log_info "啟動服務..."
    
    # 首先啟動基礎設施服務
    log_info "啟動基礎設施層..."
    docker compose up -d postgres redis qdrant rabbitmq
    
    # 等待基礎設施就緒
    log_info "等待基礎設施就緒..."
    sleep 10
    
    # 啟動LLM服務
    log_info "啟動LLM服務層..."
    docker compose up -d ollama litellm
    
    # 等待LLM服務就緒
    sleep 10
    
    # 下載Ollama模型（可選）
    if [ "${DOWNLOAD_MODELS:-true}" = "true" ]; then
        log_info "下載Ollama模型（這可能需要幾分鐘）..."
        docker exec ai-ollama ollama pull llama3 || log_warning "Ollama模型下載失敗，可稍後手動下載"
    fi
    
    # Initialize database
    log_info "初始化數據庫..."
    ./scripts/init-db.sh init || log_warning "數據庫初始化失敗，請稍後手動運行 ./scripts/init-db.sh"

    # 啟動應用服務
    log_info "啟動應用服務層..."
    docker compose up -d mcp-server agent-service web-ui

    # 啟動監控服務
    log_info "啟動監控服務..."
    docker compose up -d prometheus grafana

    log_success "所有服務已啟動"
}

# 等待服務就緒
wait_for_services() {
    log_info "等待服務就緒（最多等待2分鐘）..."
    
    local max_attempts=24
    local attempt=0
    local all_healthy=false
    
    while [ $attempt -lt $max_attempts ] && [ "$all_healthy" = false ]; do
        attempt=$((attempt + 1))
        echo -n "."
        
        # 檢查關鍵服務
        local healthy_count=0
        local required_services=5
        
        curl -s http://localhost:5432 &> /dev/null && healthy_count=$((healthy_count + 1))
        curl -s http://localhost:6333/health | grep -q "ok" &> /dev/null && healthy_count=$((healthy_count + 1))
        curl -s http://localhost:4000/health | grep -q "healthy" &> /dev/null && healthy_count=$((healthy_count + 1))
        curl -s http://localhost:8001/health | grep -q "healthy" &> /dev/null && healthy_count=$((healthy_count + 1))
        curl -s http://localhost:8002/health | grep -q "healthy" &> /dev/null && healthy_count=$((healthy_count + 1))
        
        if [ $healthy_count -eq $required_services ]; then
            all_healthy=true
        else
            sleep 5
        fi
    done
    
    echo ""
    
    if [ "$all_healthy" = true ]; then
        log_success "所有服務已就緒"
    else
        log_warning "部分服務可能未完全就緒，請檢查日誌"
    fi
}

# 顯示狀態
show_status() {
    log_info "服務狀態:"
    docker compose ps
    
    echo ""
    log_info "資源使用:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
    
    echo ""
    log_info "訪問地址:"
    echo "  🌐 Web UI:        http://localhost:8501"
    echo "  📊 Grafana:       http://localhost:3000 (admin/admin)"
    echo "  🐰 RabbitMQ:      http://localhost:15672 (admin/<password>)"
    echo "  📈 Prometheus:    http://localhost:9090"
    echo "  🔧 LiteLLM:       http://localhost:4000"
    echo ""
    log_info "查看日誌: docker compose logs -f [service-name]"
}

# 運行測試
run_tests() {
    log_info "運行系統測試..."
    
    # 載入環境變數
    source .env
    
    local failed_tests=0
    
    # 測試1: PostgreSQL
    echo -n "測試 PostgreSQL... "
    if docker exec ai-postgres pg_isready -U admin &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        failed_tests=$((failed_tests + 1))
    fi
    
    # 測試2: Redis
    echo -n "測試 Redis... "
    if docker exec ai-redis redis-cli -a "$REDIS_PASSWORD" ping &> /dev/null | grep -q "PONG"; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        failed_tests=$((failed_tests + 1))
    fi
    
    # 測試3: Qdrant
    echo -n "測試 Qdrant... "
    if curl -s http://localhost:6333/health | grep -q "ok"; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        failed_tests=$((failed_tests + 1))
    fi
    
    # 測試4: LiteLLM
    echo -n "測試 LiteLLM... "
    if curl -s http://localhost:4000/health | grep -q "healthy"; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        failed_tests=$((failed_tests + 1))
    fi
    
    # 測試5: MCP Server
    echo -n "測試 MCP Server... "
    if curl -s http://localhost:8001/health | grep -q "healthy"; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        failed_tests=$((failed_tests + 1))
    fi
    
    # 測試6: Agent Service
    echo -n "測試 Agent Service... "
    if curl -s http://localhost:8002/health | grep -q "healthy"; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        failed_tests=$((failed_tests + 1))
    fi
    
    # 測試7: Web UI
    echo -n "測試 Web UI... "
    if curl -s http://localhost:8501 &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        failed_tests=$((failed_tests + 1))
    fi
    
    echo ""
    if [ $failed_tests -eq 0 ]; then
        log_success "所有測試通過 ✨"
    else
        log_warning "$failed_tests 個測試失敗"
    fi
    
    # API測試
    log_info "測試API端點..."
    echo -n "測試聊天API... "
    response=$(curl -s -X POST http://localhost:8002/agent/chat \
        -H "Content-Type: application/json" \
        -d '{"message": "Hello", "model": "gpt-3.5-turbo"}')
    
    if echo "$response" | grep -q "response"; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        echo "Response: $response"
    fi
}

# 停止服務
stop_services() {
    log_info "停止服務..."
    docker compose down
    log_success "服務已停止"
}

# 重啟服務
restart_services() {
    log_info "重啟服務..."
    docker compose restart
    log_success "服務已重啟"
}

# 清理環境
clean_environment() {
    log_warning "這將刪除所有容器、映像和資料！"
    read -p "確定要繼續嗎？(yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        log_info "清理環境..."
        docker compose down -v --rmi all
        rm -rf data/* logs/*
        log_success "環境已清理"
    else
        log_info "取消清理"
    fi
}

# 主函數
main() {
    case "${1:-start}" in
        start)
            echo -e "${BLUE}"
            echo "╔══════════════════════════════════════╗"
            echo "║   AI平台MVP - 一鍵部署腳本          ║"
            echo "╚══════════════════════════════════════╝"
            echo -e "${NC}"
            
            check_prerequisites
            create_directory_structure
            generate_env_file
            download_configs
            build_images
            start_services
            wait_for_services
            run_tests
            show_status
            
            echo ""
            log_success "🎉 部署完成！"
            log_info "請訪問 http://localhost:8501 開始使用"
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        test)
            run_tests
            ;;
        clean)
            clean_environment
            ;;
        *)
            echo "使用方法: $0 {start|stop|restart|status|test|clean}"
            exit 1
            ;;
    esac
}

# 執行主函數
main "$@"