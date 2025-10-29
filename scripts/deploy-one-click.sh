#!/bin/bash

###############################################################################
# AI Platform - One-Click Deployment
# 一鍵部署腳本 (打包 + 上傳 + 部署 + 驗證)
###############################################################################

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

clear

cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║         AI Platform - One-Click Deployment Script            ║
║                                                               ║
║         快速部署 AI 平台到生產環境                            ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF

echo ""

# 檢查參數
if [ $# -lt 1 ]; then
    echo -e "${RED}錯誤: 缺少必要參數${NC}"
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

# 獲取腳本目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  部署配置${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
echo ""
echo "  伺服器 IP: ${YELLOW}${SERVER_IP}${NC}"
echo "  SSH 用戶: ${YELLOW}${SSH_USER}${NC}"
echo "  SSH 金鑰: ${YELLOW}${SSH_KEY:-密碼登入}${NC}"
echo "  專案目錄: ${YELLOW}${PROJECT_DIR}${NC}"
echo ""

echo -e "${YELLOW}確認要開始部署嗎? (y/n)${NC}"
read -r CONFIRM

if [ "${CONFIRM}" != "y" ] && [ "${CONFIRM}" != "Y" ]; then
    echo "部署已取消"
    exit 0
fi

echo ""

# 計時開始
START_TIME=$(date +%s)

# 步驟 1: 打包
echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  步驟 1/5: 打包部署文件${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
echo ""

cd "${PROJECT_DIR}"

if [ -f "${SCRIPT_DIR}/1-package-deployment.sh" ]; then
    bash "${SCRIPT_DIR}/1-package-deployment.sh"
    PACKAGE_EXIT_CODE=$?

    if [ ${PACKAGE_EXIT_CODE} -ne 0 ]; then
        echo -e "${RED}✗ 打包失敗${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ 找不到打包腳本${NC}"
    exit 1
fi

echo ""
sleep 2

# 步驟 2: 上傳
echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  步驟 2/5: 上傳到伺服器${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
echo ""

if [ -f "${SCRIPT_DIR}/2-upload-to-server.sh" ]; then
    bash "${SCRIPT_DIR}/2-upload-to-server.sh" "${SERVER_IP}" "${SSH_USER}" "${SSH_KEY}"
    UPLOAD_EXIT_CODE=$?

    if [ ${UPLOAD_EXIT_CODE} -ne 0 ]; then
        echo -e "${RED}✗ 上傳失敗${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ 找不到上傳腳本${NC}"
    exit 1
fi

echo ""
sleep 2

# 步驟 3: 配置環境變數
echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  步驟 3/5: 配置環境變數${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
echo ""

if [ -n "${SSH_KEY}" ]; then
    SSH_CMD="ssh -i ${SSH_KEY}"
else
    SSH_CMD="ssh"
fi

# 檢查 .env 是否存在
ENV_EXISTS=$(${SSH_CMD} ${SSH_USER}@${SERVER_IP} "[ -f /opt/ai_platform/.env ] && echo 'yes' || echo 'no'")

if [ "${ENV_EXISTS}" = "no" ]; then
    echo -e "${YELLOW}未找到 .env 文件，使用範例配置${NC}"
    ${SSH_CMD} ${SSH_USER}@${SERVER_IP} "cp /opt/ai_platform/.env.production.example /opt/ai_platform/.env"

    echo ""
    echo -e "${YELLOW}⚠ 重要提示:${NC}"
    echo "在部署前，需要配置以下環境變數:"
    echo "  - OPENAI_API_KEY"
    echo "  - ANTHROPIC_API_KEY"
    echo "  - GOOGLE_API_KEY"
    echo "  - POSTGRES_PASSWORD"
    echo "  - REDIS_PASSWORD"
    echo "  - RABBITMQ_DEFAULT_PASS"
    echo ""
    echo "選項:"
    echo "  1) 現在編輯環境變數"
    echo "  2) 使用預設值繼續 (僅測試用)"
    echo "  3) 取消部署"
    echo ""
    echo -n "請選擇 (1-3): "
    read -r ENV_CHOICE

    case ${ENV_CHOICE} in
        1)
            ${SSH_CMD} -t ${SSH_USER}@${SERVER_IP} "vim /opt/ai_platform/.env"
            ;;
        2)
            echo -e "${YELLOW}⚠ 使用預設值，請在生產環境中修改！${NC}"
            ;;
        3)
            echo "部署已取消"
            exit 0
            ;;
        *)
            echo "無效選項，使用預設值繼續"
            ;;
    esac
else
    echo -e "${GREEN}✓ .env 文件已存在${NC}"
fi

echo ""
sleep 2

# 步驟 4: 執行部署
echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  步驟 4/5: 執行部署${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
echo ""

echo "開始遠端部署..."
echo ""

${SSH_CMD} -t ${SSH_USER}@${SERVER_IP} "
    cd /opt/ai_platform
    sudo ./deploy-rhel-production.sh
"

DEPLOY_EXIT_CODE=$?

if [ ${DEPLOY_EXIT_CODE} -ne 0 ]; then
    echo ""
    echo -e "${RED}✗ 部署失敗${NC}"
    echo ""
    echo "查看部署日誌:"
    echo "  ssh ${SSH_USER}@${SERVER_IP} 'cat /opt/ai_platform/deploy.log'"
    echo ""
    exit 1
fi

echo ""
sleep 2

# 步驟 5: 驗證部署
echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  步驟 5/5: 驗證部署${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
echo ""

if [ -f "${SCRIPT_DIR}/4-verify-deployment.sh" ]; then
    bash "${SCRIPT_DIR}/4-verify-deployment.sh" "${SERVER_IP}" "${SSH_USER}" "${SSH_KEY}"
    VERIFY_EXIT_CODE=$?

    if [ ${VERIFY_EXIT_CODE} -ne 0 ]; then
        echo ""
        echo -e "${YELLOW}⚠ 驗證發現一些問題，但部署已完成${NC}"
    fi
else
    echo -e "${YELLOW}⚠ 找不到驗證腳本，跳過驗證${NC}"
fi

echo ""

# 計時結束
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED / 60))
SECONDS=$((ELAPSED % 60))

echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
echo ""

echo "部署摘要:"
echo "  ├─ 伺服器: ${SERVER_IP}"
echo "  ├─ 用戶: ${SSH_USER}"
echo "  ├─ 耗時: ${MINUTES} 分 ${SECONDS} 秒"
echo "  └─ 狀態: ${GREEN}完成${NC}"
echo ""

echo "訪問服務:"
echo "  ├─ Web UI:   ${CYAN}http://${SERVER_IP}:8501${NC}"
echo "  ├─ API:      ${CYAN}http://${SERVER_IP}:8001/health${NC}"
echo "  ├─ Grafana:  ${CYAN}http://${SERVER_IP}:3000${NC}"
echo "  └─ 如使用域名: ${CYAN}https://your-domain.com${NC}"
echo ""

echo "Grafana 登入資訊:"
echo "  ├─ 用戶名: admin"
echo "  └─ 密碼: (在 .env 文件中的 GRAFANA_ADMIN_PASSWORD)"
echo ""

echo "下一步建議:"
echo "  1. 查看 Grafana 儀表板監控系統狀態"
echo "  2. 執行負載測試驗證效能:"
echo "     ${YELLOW}./scripts/5-run-load-tests.sh ${SERVER_IP} ${SSH_USER}${NC}"
echo ""
echo "  3. 設置 Systemd 自動啟動:"
echo "     ${YELLOW}ssh ${SSH_USER}@${SERVER_IP} 'cd /opt/ai_platform/systemd && sudo ./install-systemd.sh'${NC}"
echo ""
echo "  4. 配置告警通知 (在 Grafana 中)"
echo ""

echo "故障排除:"
echo "  查看日誌:"
echo "    ${YELLOW}ssh ${SSH_USER}@${SERVER_IP} 'cd /opt/ai_platform && docker compose logs -f'${NC}"
echo ""
echo "  重新驗證部署:"
echo "    ${YELLOW}./scripts/4-verify-deployment.sh ${SERVER_IP} ${SSH_USER}${NC}"
echo ""

echo -e "${GREEN}🎉 恭喜！AI Platform 已成功部署！${NC}"
echo ""
