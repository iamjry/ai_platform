#!/bin/bash

###############################################################################
# AI Platform - Step 3: Remote Deploy
# 遠端執行部署腳本
###############################################################################

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  AI Platform - 遠端部署${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# 檢查參數
if [ $# -lt 1 ]; then
    echo -e "${RED}錯誤: 缺少伺服器 IP 參數${NC}"
    echo ""
    echo "使用方法:"
    echo "  $0 <server-ip> [ssh-user] [ssh-key]"
    echo ""
    echo "範例:"
    echo "  $0 192.168.1.100"
    echo "  $0 192.168.1.100 root"
    echo "  $0 192.168.1.100 root ~/.ssh/production.pem"
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

echo "配置資訊:"
echo "  ├─ 伺服器 IP: ${SERVER_IP}"
echo "  ├─ SSH 用戶: ${SSH_USER}"
echo "  ├─ SSH 金鑰: ${SSH_KEY:-未使用}"
echo "  └─ 目標目錄: ${TARGET_DIR}"
echo ""

echo -e "${YELLOW}步驟 1: 測試連線...${NC}"

if ${SSH_CMD} ${SSH_USER}@${SERVER_IP} "echo 'SSH 連線成功'" 2>/dev/null; then
    echo -e "${GREEN}✓ SSH 連線正常${NC}"
else
    echo -e "${RED}✗ SSH 連線失敗${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}步驟 2: 檢查部署文件...${NC}"

# 檢查部署文件是否存在
DEPLOY_SCRIPT_EXISTS=$(${SSH_CMD} ${SSH_USER}@${SERVER_IP} "[ -f ${TARGET_DIR}/deploy-rhel-production.sh ] && echo 'yes' || echo 'no'")

if [ "${DEPLOY_SCRIPT_EXISTS}" = "no" ]; then
    echo -e "${RED}✗ 找不到部署腳本${NC}"
    echo ""
    echo "請先執行上傳腳本:"
    echo "  ./scripts/2-upload-to-server.sh ${SERVER_IP} ${SSH_USER}"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ 部署腳本已就位${NC}"
echo ""

echo -e "${YELLOW}步驟 3: 檢查 .env 配置文件...${NC}"

# 檢查是否已配置 .env
ENV_EXISTS=$(${SSH_CMD} ${SSH_USER}@${SERVER_IP} "[ -f ${TARGET_DIR}/.env ] && echo 'yes' || echo 'no'")

if [ "${ENV_EXISTS}" = "no" ]; then
    echo -e "${YELLOW}⚠ 警告: 未找到 .env 文件${NC}"
    echo ""
    echo "是否使用範例配置? (y/n)"
    read -r USE_EXAMPLE

    if [ "${USE_EXAMPLE}" = "y" ] || [ "${USE_EXAMPLE}" = "Y" ]; then
        ${SSH_CMD} ${SSH_USER}@${SERVER_IP} "cp ${TARGET_DIR}/.env.production.example ${TARGET_DIR}/.env"
        echo -e "${GREEN}✓ 已複製範例配置${NC}"
        echo ""
        echo -e "${YELLOW}⚠ 重要: 請在部署前編輯 .env 文件，修改以下項目:${NC}"
        echo "  - OPENAI_API_KEY"
        echo "  - ANTHROPIC_API_KEY"
        echo "  - GOOGLE_API_KEY"
        echo "  - POSTGRES_PASSWORD"
        echo "  - REDIS_PASSWORD"
        echo "  - RABBITMQ_DEFAULT_PASS"
        echo ""
        echo "是否現在編輯? (y/n)"
        read -r EDIT_NOW

        if [ "${EDIT_NOW}" = "y" ] || [ "${EDIT_NOW}" = "Y" ]; then
            ${SSH_CMD} -t ${SSH_USER}@${SERVER_IP} "vim ${TARGET_DIR}/.env"
        else
            echo ""
            echo "請稍後手動編輯 .env 文件"
            echo "  ssh ${SSH_USER}@${SERVER_IP}"
            echo "  vim ${TARGET_DIR}/.env"
            echo ""
            exit 0
        fi
    else
        echo ""
        echo "部署已取消。請先配置 .env 文件。"
        echo ""
        exit 0
    fi
else
    echo -e "${GREEN}✓ .env 配置文件已存在${NC}"
fi
echo ""

echo -e "${YELLOW}步驟 4: 顯示系統資訊...${NC}"

${SSH_CMD} ${SSH_USER}@${SERVER_IP} "
    echo '作業系統:'
    cat /etc/redhat-release
    echo ''
    echo 'CPU:'
    lscpu | grep -E '^CPU\(s\)|^Model name'
    echo ''
    echo '記憶體:'
    free -h | grep -E '^Mem'
    echo ''
    echo '磁碟空間:'
    df -h /opt | tail -1
    echo ''
    echo 'NVIDIA GPU:'
    nvidia-smi --query-gpu=index,name,driver_version,memory.total --format=csv,noheader 2>/dev/null || echo '未安裝 NVIDIA 驅動'
"
echo ""

echo -e "${YELLOW}確認要開始部署嗎? (y/n)${NC}"
read -r CONFIRM

if [ "${CONFIRM}" != "y" ] && [ "${CONFIRM}" != "Y" ]; then
    echo "部署已取消"
    exit 0
fi
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  開始遠端部署...${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# 執行遠端部署
${SSH_CMD} -t ${SSH_USER}@${SERVER_IP} "
    cd ${TARGET_DIR}
    sudo ./deploy-rhel-production.sh
"

DEPLOY_EXIT_CODE=$?

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"

if [ ${DEPLOY_EXIT_CODE} -eq 0 ]; then
    echo -e "${GREEN}  遠端部署完成！${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
    echo ""

    echo "下一步:"
    echo "  1. 驗證部署狀態:"
    echo "     ${YELLOW}./scripts/4-verify-deployment.sh ${SERVER_IP} ${SSH_USER}${NC}"
    echo ""
    echo "  2. 執行負載測試:"
    echo "     ${YELLOW}./scripts/5-run-load-tests.sh ${SERVER_IP} ${SSH_USER}${NC}"
    echo ""
    echo "  3. 訪問服務:"
    echo "     Web UI: ${YELLOW}http://${SERVER_IP}:8501${NC}"
    echo "     Grafana: ${YELLOW}http://${SERVER_IP}:3000${NC}"
    echo "     API: ${YELLOW}http://${SERVER_IP}:8001/health${NC}"
    echo ""
else
    echo -e "${RED}  遠端部署失敗！${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
    echo ""

    echo "請檢查部署日誌:"
    echo "  ${YELLOW}ssh ${SSH_USER}@${SERVER_IP} 'cat ${TARGET_DIR}/deploy.log'${NC}"
    echo ""

    exit 1
fi
