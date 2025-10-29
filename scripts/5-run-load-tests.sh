#!/bin/bash

###############################################################################
# AI Platform - Step 5: Run Load Tests
# 執行負載測試
###############################################################################

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  AI Platform - 負載測試${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# 檢查參數
if [ $# -lt 1 ]; then
    echo -e "${RED}錯誤: 缺少伺服器 IP 參數${NC}"
    echo ""
    echo "使用方法:"
    echo "  $0 <server-ip> [ssh-user] [ssh-key] [test-type]"
    echo ""
    echo "測試類型:"
    echo "  smoke  - 煙霧測試 (快速驗證)"
    echo "  load   - 負載測試 (正常流量)"
    echo "  stress - 壓力測試 (高峰流量)"
    echo "  all    - 全部測試 (預設)"
    echo ""
    echo "範例:"
    echo "  $0 192.168.1.100 root '' smoke"
    echo ""
    exit 1
fi

SERVER_IP=$1
SSH_USER=${2:-root}
SSH_KEY=${3:-}
TEST_TYPE=${4:-all}
TARGET_DIR="/opt/ai_platform"

# 構建 SSH 命令
if [ -n "${SSH_KEY}" ]; then
    SSH_CMD="ssh -i ${SSH_KEY}"
else
    SSH_CMD="ssh"
fi

echo "配置資訊:"
echo "  ├─ 伺服器 IP: ${SERVER_IP}"
echo "  ├─ SSH 用戶: ${SSH_USER}"
echo "  ├─ 測試類型: ${TEST_TYPE}"
echo "  └─ 目標 URL: http://${SERVER_IP}:8001"
echo ""

echo -e "${YELLOW}步驟 1: 測試連線...${NC}"

if ${SSH_CMD} ${SSH_USER}@${SERVER_IP} "echo 'OK'" &>/dev/null; then
    echo -e "${GREEN}✓ SSH 連線正常${NC}"
else
    echo -e "${RED}✗ SSH 連線失敗${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}步驟 2: 檢查測試工具...${NC}"

# 檢查 Apache Bench
AB_INSTALLED=$(${SSH_CMD} ${SSH_USER}@${SERVER_IP} "command -v ab &>/dev/null && echo 'yes' || echo 'no'")

if [ "${AB_INSTALLED}" = "no" ]; then
    echo -e "${YELLOW}⚠ Apache Bench 未安裝，正在安裝...${NC}"
    ${SSH_CMD} ${SSH_USER}@${SERVER_IP} "sudo dnf install -y httpd-tools"
    echo -e "${GREEN}✓ Apache Bench 已安裝${NC}"
else
    echo -e "${GREEN}✓ Apache Bench 已安裝${NC}"
fi

# 檢查 Locust
LOCUST_INSTALLED=$(${SSH_CMD} ${SSH_USER}@${SERVER_IP} "command -v locust &>/dev/null && echo 'yes' || echo 'no'")

if [ "${LOCUST_INSTALLED}" = "no" ]; then
    echo -e "${YELLOW}⚠ Locust 未安裝，正在安裝...${NC}"
    ${SSH_CMD} ${SSH_USER}@${SERVER_IP} "
        cd ${TARGET_DIR}/load-tests
        pip3 install -r requirements.txt
    "
    echo -e "${GREEN}✓ Locust 已安裝${NC}"
else
    echo -e "${GREEN}✓ Locust 已安裝${NC}"
fi

echo ""

echo -e "${YELLOW}步驟 3: 檢查服務狀態...${NC}"

# 檢查 API 可訪問性
API_STATUS=$(${SSH_CMD} ${SSH_USER}@${SERVER_IP} "curl -s -o /dev/null -w '%{http_code}' http://localhost:8001/health")

if [ "${API_STATUS}" = "200" ]; then
    echo -e "${GREEN}✓ API 服務正常 (HTTP ${API_STATUS})${NC}"
else
    echo -e "${RED}✗ API 服務異常 (HTTP ${API_STATUS})${NC}"
    echo ""
    echo "請先確認服務已啟動:"
    echo "  ./scripts/4-verify-deployment.sh ${SERVER_IP} ${SSH_USER}"
    echo ""
    exit 1
fi

echo ""

# 運行測試函數
run_smoke_test() {
    echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  執行煙霧測試 (Smoke Test)${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
    echo ""
    echo "配置: 5 用戶, 100 請求"
    echo "預期: 所有請求通過, 錯誤率 < 1%, 回應時間 < 500ms"
    echo ""

    ${SSH_CMD} -t ${SSH_USER}@${SERVER_IP} "
        cd ${TARGET_DIR}/load-tests
        BASE_URL=http://localhost:8001 \
        CONCURRENT_USERS=5 \
        TOTAL_REQUESTS=100 \
        ./test-api-endpoints.sh
    "

    echo ""
    echo -e "${GREEN}✓ 煙霧測試完成${NC}"
    echo ""
}

run_load_test() {
    echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  執行負載測試 (Load Test)${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
    echo ""
    echo "配置: 50 用戶, 10 分鐘"
    echo "預期: p95 < 1s, 錯誤率 < 2%, 系統資源 < 70%"
    echo ""

    ${SSH_CMD} -t ${SSH_USER}@${SERVER_IP} "
        cd ${TARGET_DIR}/load-tests
        locust -f locustfile.py \
            --host=http://localhost:8001 \
            --users 50 \
            --spawn-rate 5 \
            --run-time 10m \
            --headless \
            --csv=results/load_test_\$(date +%Y%m%d_%H%M%S)
    "

    echo ""
    echo -e "${GREEN}✓ 負載測試完成${NC}"
    echo ""
}

run_stress_test() {
    echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  執行壓力測試 (Stress Test)${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
    echo ""
    echo "配置: 200 用戶, 15 分鐘"
    echo "預期: p95 < 2s, 錯誤率 < 5%, 無服務崩潰"
    echo ""
    echo -e "${YELLOW}⚠ 警告: 這將對系統產生高負載${NC}"
    echo "是否繼續? (y/n)"
    read -r CONFIRM

    if [ "${CONFIRM}" != "y" ] && [ "${CONFIRM}" != "Y" ]; then
        echo "壓力測試已取消"
        return
    fi

    ${SSH_CMD} -t ${SSH_USER}@${SERVER_IP} "
        cd ${TARGET_DIR}/load-tests
        locust -f locustfile.py \
            --host=http://localhost:8001 \
            --users 200 \
            --spawn-rate 20 \
            --run-time 15m \
            --headless \
            --csv=results/stress_test_\$(date +%Y%m%d_%H%M%S)
    "

    echo ""
    echo -e "${GREEN}✓ 壓力測試完成${NC}"
    echo ""
}

# 執行測試
case ${TEST_TYPE} in
    smoke)
        run_smoke_test
        ;;
    load)
        run_load_test
        ;;
    stress)
        run_stress_test
        ;;
    all)
        run_smoke_test
        echo "等待 30 秒後繼續負載測試..."
        sleep 30
        run_load_test
        echo ""
        echo "是否執行壓力測試? (y/n)"
        read -r RUN_STRESS
        if [ "${RUN_STRESS}" = "y" ] || [ "${RUN_STRESS}" = "Y" ]; then
            echo "等待 60 秒後繼續壓力測試..."
            sleep 60
            run_stress_test
        fi
        ;;
    *)
        echo -e "${RED}錯誤: 未知的測試類型 '${TEST_TYPE}'${NC}"
        echo "可用類型: smoke, load, stress, all"
        exit 1
        ;;
esac

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  測試完成！${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

echo "查看測試結果:"
echo "  ${YELLOW}ssh ${SSH_USER}@${SERVER_IP} 'ls -lh ${TARGET_DIR}/load-tests/results/'${NC}"
echo ""

echo "下載測試結果:"
echo "  ${YELLOW}scp -r ${SSH_USER}@${SERVER_IP}:${TARGET_DIR}/load-tests/results/ ./test_results/${NC}"
echo ""

echo "監控系統狀態:"
echo "  Grafana: ${YELLOW}http://${SERVER_IP}:3000${NC}"
echo ""
