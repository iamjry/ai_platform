#!/bin/bash

###############################################################################
# AI Platform - Step 2: Upload to Production Server
# 上傳部署包到生產伺服器
###############################################################################

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  AI Platform - 上傳到生產伺服器${NC}"
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
    SCP_CMD="scp -i ${SSH_KEY}"
    RSYNC_CMD="rsync -avz -e 'ssh -i ${SSH_KEY}'"
else
    SSH_CMD="ssh"
    SCP_CMD="scp"
    RSYNC_CMD="rsync -avz"
fi

echo "配置資訊:"
echo "  ├─ 伺服器 IP: ${SERVER_IP}"
echo "  ├─ SSH 用戶: ${SSH_USER}"
echo "  ├─ SSH 金鑰: ${SSH_KEY:-未使用 (使用密碼)}"
echo "  └─ 目標目錄: ${TARGET_DIR}"
echo ""

echo -e "${YELLOW}步驟 1: 尋找最新的部署包...${NC}"

# 尋找最新的部署包
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_DIR}"

LATEST_PACKAGE=$(ls -t ai_platform_*.tar.gz 2>/dev/null | head -1)

if [ -z "${LATEST_PACKAGE}" ]; then
    echo -e "${RED}✗ 找不到部署包${NC}"
    echo ""
    echo "請先執行打包腳本:"
    echo "  ./scripts/1-package-deployment.sh"
    echo ""
    exit 1
fi

PACKAGE_SIZE=$(du -sh "${LATEST_PACKAGE}" | awk '{print $1}')
echo -e "${GREEN}✓ 找到部署包: ${LATEST_PACKAGE} (${PACKAGE_SIZE})${NC}"
echo ""

echo -e "${YELLOW}步驟 2: 測試 SSH 連線...${NC}"

# 測試 SSH 連線
if ${SSH_CMD} -o ConnectTimeout=10 ${SSH_USER}@${SERVER_IP} "echo 'SSH 連線成功'" 2>/dev/null; then
    echo -e "${GREEN}✓ SSH 連線測試成功${NC}"
else
    echo -e "${RED}✗ SSH 連線失敗${NC}"
    echo ""
    echo "請檢查:"
    echo "  1. 伺服器 IP 是否正確"
    echo "  2. SSH 用戶是否正確"
    echo "  3. SSH 金鑰或密碼是否正確"
    echo "  4. 防火牆是否允許 SSH (port 22)"
    echo ""
    exit 1
fi
echo ""

echo -e "${YELLOW}步驟 3: 檢查伺服器磁碟空間...${NC}"

# 檢查磁碟空間 (需要至少 10GB)
REQUIRED_SPACE_MB=10240  # 10 GB
AVAILABLE_SPACE=$(${SSH_CMD} ${SSH_USER}@${SERVER_IP} "df /opt | tail -1 | awk '{print \$4}'")

if [ ${AVAILABLE_SPACE} -lt ${REQUIRED_SPACE_MB} ]; then
    echo -e "${RED}✗ 磁碟空間不足${NC}"
    echo "  需要: 10 GB"
    echo "  可用: $((AVAILABLE_SPACE / 1024)) GB"
    exit 1
fi

echo -e "${GREEN}✓ 磁碟空間充足: $((AVAILABLE_SPACE / 1024)) GB 可用${NC}"
echo ""

echo -e "${YELLOW}步驟 4: 在伺服器上創建目標目錄...${NC}"

# 創建目標目錄
${SSH_CMD} ${SSH_USER}@${SERVER_IP} "
    sudo mkdir -p ${TARGET_DIR}
    sudo chown ${SSH_USER}:${SSH_USER} ${TARGET_DIR}
" 2>/dev/null || true

echo -e "${GREEN}✓ 目標目錄已準備: ${TARGET_DIR}${NC}"
echo ""

echo -e "${YELLOW}步驟 5: 備份現有部署 (如果存在)...${NC}"

# 檢查是否有現有部署
EXISTING_DEPLOYMENT=$(${SSH_CMD} ${SSH_USER}@${SERVER_IP} "[ -f ${TARGET_DIR}/docker-compose.production.yml ] && echo 'exists' || echo 'not_exists'")

if [ "${EXISTING_DEPLOYMENT}" = "exists" ]; then
    echo "發現現有部署，進行備份..."

    BACKUP_NAME="backup_before_deploy_$(date +%Y%m%d_%H%M%S).tar.gz"

    ${SSH_CMD} ${SSH_USER}@${SERVER_IP} "
        cd ${TARGET_DIR}
        sudo tar -czf /tmp/${BACKUP_NAME} \
            --exclude='*.tar.gz' \
            --exclude='backups' \
            --exclude='logs' \
            . 2>/dev/null || true
        sudo mkdir -p ${TARGET_DIR}/backups
        sudo mv /tmp/${BACKUP_NAME} ${TARGET_DIR}/backups/
    "

    echo -e "${GREEN}✓ 現有部署已備份: ${BACKUP_NAME}${NC}"
else
    echo -e "${YELLOW}⚠ 未發現現有部署，跳過備份${NC}"
fi
echo ""

echo -e "${YELLOW}步驟 6: 上傳部署包...${NC}"

# 選擇上傳方法
if command -v rsync &> /dev/null; then
    echo "使用 rsync 上傳 (支援斷點續傳)..."

    # 使用 rsync 上傳
    eval ${RSYNC_CMD} --progress \
        "${LATEST_PACKAGE}" \
        "${SSH_USER}@${SERVER_IP}:/tmp/"
else
    echo "使用 scp 上傳..."

    # 使用 scp 上傳
    ${SCP_CMD} "${LATEST_PACKAGE}" "${SSH_USER}@${SERVER_IP}:/tmp/"
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 上傳完成${NC}"
else
    echo -e "${RED}✗ 上傳失敗${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}步驟 7: 驗證上傳完整性...${NC}"

# 計算本地 MD5
LOCAL_MD5=$(md5sum "${LATEST_PACKAGE}" | awk '{print $1}')

# 計算遠端 MD5
REMOTE_MD5=$(${SSH_CMD} ${SSH_USER}@${SERVER_IP} "md5sum /tmp/${LATEST_PACKAGE}" | awk '{print $1}')

if [ "${LOCAL_MD5}" = "${REMOTE_MD5}" ]; then
    echo -e "${GREEN}✓ 檔案完整性驗證通過${NC}"
    echo "  MD5: ${LOCAL_MD5}"
else
    echo -e "${RED}✗ 檔案完整性驗證失敗${NC}"
    echo "  本地 MD5: ${LOCAL_MD5}"
    echo "  遠端 MD5: ${REMOTE_MD5}"
    exit 1
fi
echo ""

echo -e "${YELLOW}步驟 8: 解壓部署包...${NC}"

${SSH_CMD} ${SSH_USER}@${SERVER_IP} "
    cd ${TARGET_DIR}
    sudo tar -xzf /tmp/${LATEST_PACKAGE}
    sudo chown -R ${SSH_USER}:${SSH_USER} .
    sudo chmod +x *.sh 2>/dev/null || true
    sudo chmod +x systemd/*.sh 2>/dev/null || true
    sudo chmod +x load-tests/*.sh 2>/dev/null || true
    sudo chmod +x scripts/*.sh 2>/dev/null || true
    sudo rm -f /tmp/${LATEST_PACKAGE}
"

echo -e "${GREEN}✓ 部署包已解壓${NC}"
echo ""

echo -e "${YELLOW}步驟 9: 驗證部署文件...${NC}"

# 驗證關鍵文件
REQUIRED_FILES=(
    "docker-compose.production.yml"
    ".env.production.example"
    "deploy-rhel-production.sh"
)

MISSING_FILES=()
for file in "${REQUIRED_FILES[@]}"; do
    ${SSH_CMD} ${SSH_USER}@${SERVER_IP} "[ -f ${TARGET_DIR}/${file} ]" || MISSING_FILES+=("${file}")
done

if [ ${#MISSING_FILES[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ 所有必要文件都已就位${NC}"
else
    echo -e "${RED}✗ 缺少以下文件:${NC}"
    printf '%s\n' "${MISSING_FILES[@]}"
    exit 1
fi
echo ""

echo -e "${YELLOW}步驟 10: 顯示部署清單...${NC}"

${SSH_CMD} ${SSH_USER}@${SERVER_IP} "cat ${TARGET_DIR}/DEPLOYMENT_MANIFEST.txt 2>/dev/null | head -30 || echo '清單文件不存在'"
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  上傳完成！${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

echo "部署文件已上傳到:"
echo "  ${SERVER_IP}:${TARGET_DIR}"
echo ""

echo "下一步:"
echo "  1. 連線到生產伺服器:"
echo "     ${YELLOW}ssh ${SSH_USER}@${SERVER_IP}${NC}"
echo ""
echo "  2. 進入部署目錄:"
echo "     ${YELLOW}cd ${TARGET_DIR}${NC}"
echo ""
echo "  3. 閱讀部署指南:"
echo "     ${YELLOW}less STEP_BY_STEP_DEPLOYMENT.md${NC}"
echo ""
echo "  4. 執行部署腳本:"
echo "     ${YELLOW}sudo ./deploy-rhel-production.sh${NC}"
echo ""
echo "  或使用遠端執行腳本:"
echo "     ${YELLOW}./scripts/3-remote-deploy.sh ${SERVER_IP} ${SSH_USER}${NC}"
echo ""

# 創建快速連線腳本
CONNECT_SCRIPT="${PROJECT_DIR}/connect-to-server.sh"
cat > "${CONNECT_SCRIPT}" << EOF
#!/bin/bash
# 快速連線到生產伺服器
$([ -n "${SSH_KEY}" ] && echo "ssh -i ${SSH_KEY} ${SSH_USER}@${SERVER_IP}" || echo "ssh ${SSH_USER}@${SERVER_IP}")
EOF

chmod +x "${CONNECT_SCRIPT}"

echo -e "${GREEN}✓ 快速連線腳本已創建: connect-to-server.sh${NC}"
echo ""
