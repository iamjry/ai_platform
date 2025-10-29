#!/bin/bash

###############################################################################
# AI Platform - Step 4: Verify Deployment
# 驗證部署狀態
###############################################################################

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  AI Platform - 驗證部署${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# 檢查參數
if [ $# -lt 1 ]; then
    echo -e "${RED}錯誤: 缺少伺服器 IP 參數${NC}"
    echo ""
    echo "使用方法:"
    echo "  $0 <server-ip> [ssh-user] [ssh-key]"
    echo ""
    exit 1
fi

SERVER_IP=$1
SSH_USER=${2:-root}
SSH_KEY=${3:-}
TARGET_DIR="/opt/ai_platform"

# 構建 SSH 命令
if [ -n "${SSH_KEY}" ]; then
    SSH_CMD="ssh -i ${SSH_KEY}"
else
    SSH_CMD="ssh"
fi

# 計數器
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# 檢查函數
check_item() {
    local description=$1
    local command=$2
    local expected=$3

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    echo -n "  檢查 ${description}... "

    result=$(${SSH_CMD} ${SSH_USER}@${SERVER_IP} "${command}" 2>/dev/null || echo "ERROR")

    if [[ "${result}" == *"${expected}"* ]]; then
        echo -e "${GREEN}✓ 通過${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}✗ 失敗${NC}"
        echo -e "    預期: ${expected}"
        echo -e "    實際: ${result}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

echo -e "${YELLOW}步驟 1: 測試連線...${NC}"

if ${SSH_CMD} ${SSH_USER}@${SERVER_IP} "echo 'OK'" &>/dev/null; then
    echo -e "${GREEN}✓ SSH 連線正常${NC}"
else
    echo -e "${RED}✗ SSH 連線失敗${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}步驟 2: 檢查系統服務...${NC}"

# 檢查 Docker
check_item "Docker 服務" "systemctl is-active docker" "active"

# 檢查 AI Platform 服務
check_item "AI Platform 服務" "systemctl is-active ai-platform 2>/dev/null || echo 'not_installed'" "active"

# 檢查備份定時器
check_item "備份定時器" "systemctl is-active ai-platform-backup.timer 2>/dev/null || echo 'not_installed'" "active"

# 檢查健康檢查定時器
check_item "健康檢查定時器" "systemctl is-active ai-platform-healthcheck.timer 2>/dev/null || echo 'not_installed'" "active"

echo ""

echo -e "${YELLOW}步驟 3: 檢查 Docker 容器...${NC}"

# 獲取容器狀態
${SSH_CMD} ${SSH_USER}@${SERVER_IP} "
    echo '容器狀態:'
    docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E 'ai-|NAMES'
    echo ''
    echo '容器統計:'
    echo \"  運行中: \$(docker ps -q | wc -l)\"
    echo \"  已停止: \$(docker ps -aq --filter 'status=exited' | wc -l)\"
"
echo ""

# 檢查關鍵容器
REQUIRED_CONTAINERS=(
    "ai-postgres-prod"
    "ai-redis-prod"
    "ai-qdrant-prod"
    "ai-rabbitmq-prod"
    "ai-ollama-prod"
    "ai-litellm-prod"
)

echo "檢查關鍵容器:"
for container in "${REQUIRED_CONTAINERS[@]}"; do
    check_item "${container}" "docker ps --filter name=${container} --format '{{.Status}}'" "Up"
done

echo ""

echo -e "${YELLOW}步驟 4: 檢查 GPU 狀態...${NC}"

${SSH_CMD} ${SSH_USER}@${SERVER_IP} "
    if command -v nvidia-smi &> /dev/null; then
        echo 'GPU 資訊:'
        nvidia-smi --query-gpu=index,name,driver_version,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv
        echo ''

        # 檢查 Ollama 容器的 GPU 訪問
        echo '檢查 Ollama 容器 GPU 訪問:'
        docker exec ai-ollama-prod nvidia-smi --query-gpu=index,name --format=csv,noheader 2>/dev/null && echo '✓ GPU 可訪問' || echo '✗ GPU 無法訪問'
    else
        echo '⚠ NVIDIA 驅動未安裝'
    fi
"
echo ""

echo -e "${YELLOW}步驟 5: 檢查服務健康端點...${NC}"

# 健康檢查端點列表
declare -A HEALTH_ENDPOINTS=(
    ["MCP Server"]="http://localhost:8001/health"
    ["Agent Service"]="http://localhost:8000/health"
    ["LiteLLM"]="http://localhost:4000/health"
    ["Web UI"]="http://localhost:8501"
    ["Grafana"]="http://localhost:3000/api/health"
)

for service in "${!HEALTH_ENDPOINTS[@]}"; do
    endpoint="${HEALTH_ENDPOINTS[$service]}"
    check_item "${service}" "curl -sf ${endpoint} -o /dev/null && echo 'OK' || echo 'FAIL'" "OK"
done

echo ""

echo -e "${YELLOW}步驟 6: 檢查資料庫連線...${NC}"

# PostgreSQL
check_item "PostgreSQL 連線" "docker exec ai-postgres-prod pg_isready" "accepting connections"

# Redis
check_item "Redis 連線" "docker exec ai-redis-prod redis-cli ping" "PONG"

echo ""

echo -e "${YELLOW}步驟 7: 檢查磁碟空間...${NC}"

${SSH_CMD} ${SSH_USER}@${SERVER_IP} "
    echo '磁碟使用情況:'
    df -h ${TARGET_DIR} | tail -1
    echo ''

    # 檢查日誌大小
    echo '日誌大小:'
    du -sh ${TARGET_DIR}/logs 2>/dev/null || echo '  無日誌目錄'
    echo ''

    # 檢查備份大小
    echo '備份大小:'
    du -sh ${TARGET_DIR}/backups 2>/dev/null || echo '  無備份目錄'
"
echo ""

echo -e "${YELLOW}步驟 8: 檢查網路端口...${NC}"

${SSH_CMD} ${SSH_USER}@${SERVER_IP} "
    echo '監聽端口:'
    ss -tlnp | grep -E ':(8000|8001|8501|3000|5432|6379|11434|4000)' || echo '  未找到監聽端口'
"
echo ""

echo -e "${YELLOW}步驟 9: 檢查最近日誌...${NC}"

${SSH_CMD} ${SSH_USER}@${SERVER_IP} "
    echo '最近的錯誤日誌 (Agent Service):'
    docker logs ai-agent-service-1 --tail=20 2>&1 | grep -i error | tail -5 || echo '  無錯誤'
    echo ''

    echo '最近的警告日誌 (MCP Server):'
    docker logs ai-mcp-server-1 --tail=20 2>&1 | grep -i warning | tail -5 || echo '  無警告'
"
echo ""

echo -e "${YELLOW}步驟 10: 執行功能測試...${NC}"

echo "測試 API 端點:"

# 測試 MCP Server 健康檢查
TEST_RESULT=$(${SSH_CMD} ${SSH_USER}@${SERVER_IP} "curl -s http://localhost:8001/health")
if [[ "${TEST_RESULT}" == *"healthy"* ]] || [[ "${TEST_RESULT}" == *"ok"* ]]; then
    echo -e "  ${GREEN}✓ MCP Server API 回應正常${NC}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "  ${RED}✗ MCP Server API 回應異常${NC}"
    echo "    回應: ${TEST_RESULT}"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

# 測試 Ollama
TEST_OLLAMA=$(${SSH_CMD} ${SSH_USER}@${SERVER_IP} "docker exec ai-ollama-prod ollama list 2>/dev/null | wc -l")
if [ "${TEST_OLLAMA}" -gt 0 ]; then
    echo -e "  ${GREEN}✓ Ollama 服務正常${NC}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "  ${YELLOW}⚠ Ollama 尚未下載模型${NC}"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""

echo -e "${YELLOW}步驟 11: 檢查資源使用情況...${NC}"

${SSH_CMD} ${SSH_USER}@${SERVER_IP} "
    echo '系統資源使用:'
    echo ''
    echo 'CPU 使用率:'
    top -bn1 | grep 'Cpu(s)' | awk '{print \"  \" \$2 \" (user) \" \$4 \" (system)\"}'
    echo ''
    echo '記憶體使用:'
    free -h | grep Mem | awk '{print \"  使用: \" \$3 \" / \" \$2 \" (\" int(\$3/\$2*100) \"%)\"}'
    echo ''
    echo '容器資源 (前 5 名):'
    docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}' | head -6
"
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  驗證完成！${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# 顯示摘要
echo "檢查摘要:"
echo "  ├─ 總檢查項目: ${TOTAL_CHECKS}"
echo "  ├─ 通過: ${GREEN}${PASSED_CHECKS}${NC}"
echo "  └─ 失敗: ${RED}${FAILED_CHECKS}${NC}"
echo ""

# 計算通過率
PASS_RATE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))

if [ ${FAILED_CHECKS} -eq 0 ]; then
    echo -e "${GREEN}✓ 所有檢查項目都通過！${NC}"
    echo ""
    echo "系統狀態: ${GREEN}健康${NC}"
    echo "通過率: ${PASS_RATE}%"
    echo ""

    echo "建議下一步:"
    echo "  1. 執行負載測試:"
    echo "     ${YELLOW}./scripts/5-run-load-tests.sh ${SERVER_IP} ${SSH_USER}${NC}"
    echo ""
    echo "  2. 查看 Grafana 儀表板:"
    echo "     ${YELLOW}http://${SERVER_IP}:3000${NC}"
    echo ""
    echo "  3. 訪問 Web UI:"
    echo "     ${YELLOW}http://${SERVER_IP}:8501${NC}"
    echo ""

    exit 0
elif [ ${FAILED_CHECKS} -le 2 ]; then
    echo -e "${YELLOW}⚠ 部分檢查項目失敗${NC}"
    echo ""
    echo "系統狀態: ${YELLOW}需要注意${NC}"
    echo "通過率: ${PASS_RATE}%"
    echo ""

    echo "請檢查失敗的項目並修復"
    echo ""

    exit 1
else
    echo -e "${RED}✗ 多個檢查項目失敗${NC}"
    echo ""
    echo "系統狀態: ${RED}不健康${NC}"
    echo "通過率: ${PASS_RATE}%"
    echo ""

    echo "請檢查以下項目:"
    echo "  1. 查看部署日誌:"
    echo "     ssh ${SSH_USER}@${SERVER_IP} 'cat ${TARGET_DIR}/deploy.log'"
    echo ""
    echo "  2. 查看容器日誌:"
    echo "     ssh ${SSH_USER}@${SERVER_IP} 'cd ${TARGET_DIR} && docker compose logs --tail=100'"
    echo ""
    echo "  3. 重新部署:"
    echo "     ./scripts/3-remote-deploy.sh ${SERVER_IP} ${SSH_USER}"
    echo ""

    exit 2
fi
