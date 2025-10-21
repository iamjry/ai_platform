#!/bin/bash
set -e

# AI平台MVP一鍵部署腳本 (macOS版本)
# 使用方法: ./deploy-macos.sh [start|stop|restart|status|clean]

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 檢查先決條件 (macOS版本)
check_prerequisites() {
    log_info "檢查系統需求..."
    
    # 檢查是否為macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_warning "檢測到非macOS系統，某些功能可能不可用"
    fi
    
    # 檢查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安裝，請先安裝Docker Desktop for Mac"
        echo "下載地址: https://www.docker.com/products/docker-desktop"
        exit 1
    fi
    log_success "Docker已安裝: $(docker --version)"
    
    # 檢查Docker是否運行
    if ! docker info &> /dev/null; then
        log_error "Docker未運行，請啟動Docker Desktop"
        exit 1
    fi
    
    # 檢查Docker Compose
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose未安裝"
        exit 1
    fi
    log_success "Docker Compose已安裝: $(docker compose version)"
    
    # 檢查磁碟空間 (macOS版本)
    available_space=$(df -g . | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 20 ]; then
        log_warning "可用磁碟空間不足20GB，當前: ${available_space}GB"
        log_info "建議釋放一些空間後繼續"
    else
        log_success "磁碟空間充足: ${available_space}GB"
    fi
    
    # 檢查記憶體 (macOS版本)
    total_mem_bytes=$(sysctl -n hw.memsize)
    total_mem_gb=$((total_mem_bytes / 1024 / 1024 / 1024))
    
    if [ "$total_mem_gb" -lt 8 ]; then
        log_warning "系統記憶體不足8GB，當前: ${total_mem_gb}GB"
    else
        log_success "系統記憶體: ${total_mem_gb}GB"
    fi
    
    # macOS不支持NVIDIA GPU
    log_info "macOS環境將使用CPU模式（這是正常的）"
    ENABLE_GPU=false
    
    # 檢查Docker Desktop資源分配
    log_info "請確保Docker Desktop分配了足夠的資源："
    log_info "  - CPU: 至少4核心"
    log_info "  - 記憶體: 至少8GB"
    log_info "  - 磁碟: 至少50GB"
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
        log_warning ".env文件已存在，是否覆蓋？(y/n)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_info "保留現有.env文件"
            return
        fi
    fi
    
    log_info "生成.env配置文件..."
    
    # 讀取API Keys
    echo ""
    log_info "請輸入API金鑰（可選，按Enter跳過）："
    read -p "OpenAI API Key: " OPENAI_KEY
    read -p "Anthropic API Key: " ANTHROPIC_KEY
    
    # 生成隨機密碼 (macOS版本)
    POSTGRES_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    REDIS_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    RABBITMQ_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    cat > .env << EOF
# API金鑰
OPENAI_API_KEY=${OPENAI_KEY:-sk-your-openai-api-key-here}
ANTHROPIC_API_KEY=${ANTHROPIC_KEY:-sk-ant-your-anthropic-api-key-here}

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
ENVIRONMENT=development
LOG_LEVEL=info
MAX_CONCURRENT_REQUESTS=50

# GPU配置 (macOS不支持GPU)
ENABLE_GPU=false
GPU_MEMORY_UTILIZATION=0.9
EOF
    
    log_success ".env文件創建完成"
    log_warning "密碼已保存在.env文件中，請妥善保管！"
    
    # 顯示密碼（首次部署時）
    echo ""
    log_info "生成的密碼（請記錄）："
    echo "  PostgreSQL: ${POSTGRES_PASS}"
    echo "  Redis: ${REDIS_PASS}"
    echo "  RabbitMQ: ${RABBITMQ_PASS}"
    echo ""
}

# 下載配置文件
download_configs() {
    log_info "準備配置文件..."
    
    # Grafana數據源
    cat > config/grafana/datasources/prometheus.yml << 'GRFEOF'
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
GRFEOF
    
    # Grafana儀表板
    cat > config/grafana/dashboards/dashboard.yml << 'GRFEOF'
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
GRFEOF

    # Prometheus配置
    cat > config/prometheus.yml << 'PROMEOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'litellm'
    static_configs:
      - targets: ['litellm:4000']

  - job_name: 'agent-service'
    static_configs:
      - targets: ['agent-service:8000']

  - job_name: 'mcp-server'
    static_configs:
      - targets: ['mcp-server:8000']
PROMEOF

    # LiteLLM配置
    cat > config/litellm-config.yaml << 'LITEEOF'
model_list:
  # OpenAI模型
  - model_name: gpt-4
    litellm_params:
      model: openai/gpt-4
      api_key: os.environ/OPENAI_API_KEY
  
  - model_name: gpt-3.5-turbo
    litellm_params:
      model: openai/gpt-3.5-turbo
      api_key: os.environ/OPENAI_API_KEY
  
  # Anthropic模型
  - model_name: claude-3-opus
    litellm_params:
      model: anthropic/claude-3-opus-20240229
      api_key: os.environ/ANTHROPIC_API_KEY
  
  - model_name: claude-3-sonnet
    litellm_params:
      model: anthropic/claude-3-sonnet-20240229
      api_key: os.environ/ANTHROPIC_API_KEY
  
  # 本地Ollama模型
  - model_name: llama3
    litellm_params:
      model: ollama/llama3
      api_base: http://ollama:11434

litellm_settings:
  drop_params: true
  set_verbose: true
  cache: true
  cache_params:
    type: redis
    host: redis
    port: 6379
    password: os.environ/REDIS_PASSWORD

general_settings:
  master_key: sk-1234
  database_url: os.environ/DATABASE_URL
LITEEOF

    # 資料庫初始化腳本
    cat > scripts/init-db.sql << 'SQLEOF'
-- 創建文件表
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 創建使用記錄表
CREATE TABLE IF NOT EXISTS usage_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100),
    model VARCHAR(100),
    tokens_used INTEGER,
    cost DECIMAL(10, 6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 創建索引
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents USING gin(metadata);
CREATE INDEX IF NOT EXISTS idx_usage_logs_user_id ON usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_created_at ON usage_logs(created_at);

-- 插入測試數據
INSERT INTO documents (title, content, metadata) 
VALUES 
('歡迎文件', '歡迎使用企業AI平台MVP', '{"category": "welcome"}'),
('使用指南', '這是一個MVP版本的AI平台，支援多種LLM模型', '{"category": "guide"}')
ON CONFLICT DO NOTHING;
SQLEOF
    
    log_success "配置文件準備完成"
}

# 檢查服務代碼
check_service_code() {
    log_info "檢查服務代碼..."
    
    local missing_files=0
    local services=("mcp-server" "agent-service" "web-ui")
    
    for service in "${services[@]}"; do
        if [ ! -f "services/${service}/Dockerfile" ]; then
            log_error "缺少: services/${service}/Dockerfile"
            missing_files=$((missing_files + 1))
        fi
        if [ ! -f "services/${service}/main.py" ] && [ ! -f "services/${service}/app.py" ]; then
            log_error "缺少: services/${service}/ 主程式文件"
            missing_files=$((missing_files + 1))
        fi
    done
    
    if [ $missing_files -gt 0 ]; then
        log_error "缺少 $missing_files 個必要文件"
        log_info "請確保已按文檔創建所有服務代碼"
        log_info "是否要自動創建範例代碼？(y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            create_sample_services
        else
            exit 1
        fi
    else
        log_success "服務代碼檢查通過"
    fi
}

# 創建範例服務（簡化版）
create_sample_services() {
    log_info "創建範例服務代碼..."
    
    # 這裡可以添加創建範例代碼的邏輯
    log_warning "請手動創建服務代碼或參考文檔"
}

# 構建服務鏡像
build_images() {
    log_info "構建Docker鏡像（這可能需要幾分鐘）..."
    
    docker compose build --no-cache 2>&1 | grep -v "^$" || true
    
    if [ $? -eq 0 ]; then
        log_success "鏡像構建完成"
    else
        log_error "鏡像構建失敗"
        exit 1
    fi
}

# 啟動服務
start_services() {
    log_info "啟動服務..."
    
    # 創建網路
    docker network create ai-platform 2>/dev/null || true
    
    # 首先啟動基礎設施
    log_info "1/4 啟動基礎設施層..."
    docker compose up -d postgres redis qdrant rabbitmq
    
    log_info "等待基礎設施就緒（30秒）..."
    sleep 30
    
    # 啟動LLM服務
    log_info "2/4 啟動LLM服務層..."
    docker compose up -d ollama litellm
    
    log_info "等待LLM服務就緒（20秒）..."
    sleep 20
    
    # 啟動應用服務
    log_info "3/4 啟動應用服務層..."
    docker compose up -d mcp-server agent-service web-ui
    
    log_info "等待應用服務就緒（15秒）..."
    sleep 15
    
    # 啟動監控服務
    log_info "4/4 啟動監控服務..."
    docker compose up -d prometheus grafana
    
    log_success "所有服務已啟動"
}

# 等待服務就緒
wait_for_services() {
    log_info "驗證服務狀態..."
    
    local services=(
        "postgres:5432"
        "redis:6379"
        "qdrant:6333"
        "rabbitmq:15672"
        "litellm:4000"
        "mcp-server:8001"
        "agent-service:8002"
        "web-ui:8501"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r name port <<< "$service"
        echo -n "  檢查 $name ... "
        
        if nc -z localhost "$port" 2>/dev/null; then
            echo "✓"
        else
            echo "✗ (端口 $port 未就緒)"
        fi
    done
}

# 顯示狀態
show_status() {
    echo ""
    log_info "═══════════════════════════════════════"
    log_success "🎉 部署完成！"
    log_info "═══════════════════════════════════════"
    echo ""
    
    log_info "📊 服務狀態:"
    docker compose ps
    
    echo ""
    log_info "🌐 訪問地址:"
    echo ""
    echo "  主要服務:"
    echo "  ┌─────────────────────────────────────────┐"
    echo "  │ 🌐 Web UI:     http://localhost:8501   │"
    echo "  │ 📊 Grafana:    http://localhost:3000   │"
    echo "  │                (admin/admin)            │"
    echo "  └─────────────────────────────────────────┘"
    echo ""
    echo "  管理介面:"
    echo "  ┌─────────────────────────────────────────┐"
    echo "  │ 🐰 RabbitMQ:   http://localhost:15672  │"
    echo "  │ 📈 Prometheus: http://localhost:9090   │"
    echo "  │ 🔧 LiteLLM:    http://localhost:4000   │"
    echo "  └─────────────────────────────────────────┘"
    echo ""
    
    log_info "📝 常用命令:"
    echo "  查看日誌:   docker compose logs -f [service]"
    echo "  重啟服務:   ./deploy-macos.sh restart"
    echo "  停止服務:   ./deploy-macos.sh stop"
    echo "  查看狀態:   ./deploy-macos.sh status"
    echo ""
    
    log_info "💡 下一步:"
    echo "  1. 訪問 http://localhost:8501 開始使用"
    echo "  2. 如果使用OpenAI/Anthropic API，請在.env中配置金鑰"
    echo "  3. 下載本地模型: docker exec -it ai-ollama ollama pull llama3"
    echo ""
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
    wait_for_services
    log_success "服務已重啟"
}

# 顯示當前狀態
display_status() {
    log_info "服務狀態:"
    docker compose ps
    echo ""
    
    log_info "資源使用:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
}

# 清理環境
clean_environment() {
    log_warning "⚠️  這將刪除所有容器、卷和資料！"
    echo -n "確定要繼續嗎？輸入 'yes' 確認: "
    read -r confirm
    
    if [ "$confirm" = "yes" ]; then
        log_info "清理環境..."
        docker compose down -v --rmi all
        rm -rf data/* logs/* models/*
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
            echo "║   AI平台MVP - macOS部署腳本         ║"
            echo "╚══════════════════════════════════════╝"
            echo -e "${NC}"
            
            check_prerequisites
            create_directory_structure
            generate_env_file
            download_configs
            check_service_code
            build_images
            start_services
            wait_for_services
            show_status
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            display_status
            ;;
        clean)
            clean_environment
            ;;
        *)
            echo "使用方法: $0 {start|stop|restart|status|clean}"
            exit 1
            ;;
    esac
}

# 執行主函數
main "$@"
