#!/bin/bash

###############################################################################
# AI Platform - Step 1: Package Deployment Files
# 打包所有部署所需的文件
###############################################################################

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  AI Platform - 打包部署文件${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# 配置
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACKAGE_DIR="${PROJECT_DIR}/deployment_package"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE_NAME="ai_platform_${TIMESTAMP}.tar.gz"

cd "${PROJECT_DIR}"

echo -e "${YELLOW}步驟 1: 檢查必要文件...${NC}"

# 必要文件列表
REQUIRED_FILES=(
    "docker-compose.production.yml"
    ".env.production.example"
    "deploy-rhel-production.sh"
    "PRODUCTION_DEPLOYMENT.md"
    "STEP_BY_STEP_DEPLOYMENT.md"
)

# 檢查文件是否存在
MISSING_FILES=()
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "${file}" ]; then
        MISSING_FILES+=("${file}")
    fi
done

if [ ${#MISSING_FILES[@]} -ne 0 ]; then
    echo -e "${RED}錯誤: 缺少以下文件:${NC}"
    printf '%s\n' "${MISSING_FILES[@]}"
    exit 1
fi

echo -e "${GREEN}✓ 所有必要文件都存在${NC}"
echo ""

echo -e "${YELLOW}步驟 2: 創建打包目錄...${NC}"

# 清理舊的打包目錄
rm -rf "${PACKAGE_DIR}"
mkdir -p "${PACKAGE_DIR}"

echo -e "${GREEN}✓ 打包目錄已創建: ${PACKAGE_DIR}${NC}"
echo ""

echo -e "${YELLOW}步驟 3: 複製核心部署文件...${NC}"

# 複製核心文件
cp docker-compose.production.yml "${PACKAGE_DIR}/"
cp .env.production.example "${PACKAGE_DIR}/"
cp deploy-rhel-production.sh "${PACKAGE_DIR}/"
cp PRODUCTION_DEPLOYMENT.md "${PACKAGE_DIR}/"
cp STEP_BY_STEP_DEPLOYMENT.md "${PACKAGE_DIR}/"
cp DEPLOYMENT_PACKAGE_SUMMARY.md "${PACKAGE_DIR}/" 2>/dev/null || true
cp ADDITIONAL_RESOURCES_SUMMARY.md "${PACKAGE_DIR}/" 2>/dev/null || true

echo -e "${GREEN}✓ 核心文件已複製 (6 個文件)${NC}"

echo -e "${YELLOW}步驟 4: 複製服務代碼...${NC}"

# 複製服務目錄
if [ -d "services" ]; then
    cp -r services "${PACKAGE_DIR}/"
    echo -e "${GREEN}✓ 服務代碼已複製${NC}"
else
    echo -e "${YELLOW}⚠ 警告: services 目錄不存在${NC}"
fi

echo -e "${YELLOW}步驟 5: 複製配置文件...${NC}"

# 複製配置目錄
if [ -d "config" ]; then
    cp -r config "${PACKAGE_DIR}/"
    echo -e "${GREEN}✓ 配置文件已複製 (nginx, grafana, prometheus)${NC}"
else
    echo -e "${YELLOW}⚠ 警告: config 目錄不存在${NC}"
fi

echo -e "${YELLOW}步驟 6: 複製 Systemd 文件...${NC}"

# 複製 systemd 目錄
if [ -d "systemd" ]; then
    cp -r systemd "${PACKAGE_DIR}/"
    chmod +x "${PACKAGE_DIR}/systemd/"*.sh 2>/dev/null || true
    echo -e "${GREEN}✓ Systemd 文件已複製${NC}"
else
    echo -e "${YELLOW}⚠ 警告: systemd 目錄不存在${NC}"
fi

echo -e "${YELLOW}步驟 7: 複製負載測試腳本...${NC}"

# 複製 load-tests 目錄
if [ -d "load-tests" ]; then
    cp -r load-tests "${PACKAGE_DIR}/"
    chmod +x "${PACKAGE_DIR}/load-tests/"*.sh 2>/dev/null || true
    echo -e "${GREEN}✓ 負載測試腳本已複製${NC}"
else
    echo -e "${YELLOW}⚠ 警告: load-tests 目錄不存在${NC}"
fi

echo -e "${YELLOW}步驟 8: 複製部署腳本...${NC}"

# 複製 scripts 目錄（包含這個腳本本身）
if [ -d "scripts" ]; then
    cp -r scripts "${PACKAGE_DIR}/"
    chmod +x "${PACKAGE_DIR}/scripts/"*.sh 2>/dev/null || true
    echo -e "${GREEN}✓ 部署腳本已複製${NC}"
else
    echo -e "${YELLOW}⚠ 警告: scripts 目錄不存在${NC}"
fi

echo -e "${YELLOW}步驟 9: 設置執行權限...${NC}"

# 設置腳本執行權限
chmod +x "${PACKAGE_DIR}/deploy-rhel-production.sh" 2>/dev/null || true
chmod +x "${PACKAGE_DIR}/systemd/"*.sh 2>/dev/null || true
chmod +x "${PACKAGE_DIR}/load-tests/"*.sh 2>/dev/null || true
chmod +x "${PACKAGE_DIR}/scripts/"*.sh 2>/dev/null || true

echo -e "${GREEN}✓ 執行權限已設置${NC}"

echo -e "${YELLOW}步驟 10: 清理不需要的文件...${NC}"

# 刪除不需要的文件和目錄
cd "${PACKAGE_DIR}"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type f -name ".DS_Store" -delete 2>/dev/null || true
find . -type d -name ".git" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "venv" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".venv" -exec rm -rf {} + 2>/dev/null || true

cd "${PROJECT_DIR}"

echo -e "${GREEN}✓ 臨時文件已清理${NC}"

echo -e "${YELLOW}步驟 11: 創建部署清單...${NC}"

# 創建部署清單
cat > "${PACKAGE_DIR}/DEPLOYMENT_MANIFEST.txt" << EOF
AI Platform Deployment Package
==============================

Package Information:
-------------------
Package Name: ${PACKAGE_NAME}
Created: $(date)
Version: 2.0.0

Contents:
---------
$(cd "${PACKAGE_DIR}" && find . -type f | sort)

Directory Structure:
-------------------
$(cd "${PACKAGE_DIR}" && tree -L 2 2>/dev/null || ls -R)

File Count:
----------
Total Files: $(cd "${PACKAGE_DIR}" && find . -type f | wc -l)
Total Directories: $(cd "${PACKAGE_DIR}" && find . -type d | wc -l)

Package Size:
------------
$(du -sh "${PACKAGE_DIR}" | awk '{print $1}')

Checksums (MD5):
---------------
$(cd "${PACKAGE_DIR}" && find . -type f -exec md5sum {} \; 2>/dev/null | sort -k 2)

Installation Instructions:
-------------------------
1. Upload this package to /opt/ai_platform/
2. Extract: tar -xzf ${PACKAGE_NAME}
3. Run: sudo ./deploy-rhel-production.sh
4. Follow STEP_BY_STEP_DEPLOYMENT.md for detailed instructions

Support:
--------
Documentation: PRODUCTION_DEPLOYMENT.md
Step-by-Step Guide: STEP_BY_STEP_DEPLOYMENT.md
Load Testing: load-tests/README.md
EOF

echo -e "${GREEN}✓ 部署清單已創建${NC}"

echo -e "${YELLOW}步驟 12: 打包壓縮...${NC}"

# 創建 tar.gz 壓縮包
cd "${PROJECT_DIR}"
tar -czf "${PACKAGE_NAME}" -C deployment_package .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 打包完成: ${PACKAGE_NAME}${NC}"
else
    echo -e "${RED}✗ 打包失敗${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  打包完成！${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# 顯示摘要
PACKAGE_SIZE=$(du -sh "${PACKAGE_NAME}" | awk '{print $1}')
FILE_COUNT=$(tar -tzf "${PACKAGE_NAME}" | wc -l)

echo "打包摘要:"
echo "  ├─ 壓縮包名稱: ${PACKAGE_NAME}"
echo "  ├─ 壓縮包大小: ${PACKAGE_SIZE}"
echo "  ├─ 文件數量: ${FILE_COUNT}"
echo "  ├─ 位置: ${PROJECT_DIR}/${PACKAGE_NAME}"
echo "  └─ MD5: $(md5sum "${PACKAGE_NAME}" | awk '{print $1}')"
echo ""

echo "下一步:"
echo "  執行上傳腳本:"
echo "  ${YELLOW}./scripts/2-upload-to-server.sh <server-ip>${NC}"
echo ""

# 創建快速部署腳本
cat > "${PROJECT_DIR}/quick-deploy.sh" << 'EOFQUICK'
#!/bin/bash
# 快速部署腳本
set -e

if [ $# -eq 0 ]; then
    echo "使用方法: ./quick-deploy.sh <server-ip> [ssh-user]"
    echo "範例: ./quick-deploy.sh 192.168.1.100 root"
    exit 1
fi

SERVER_IP=$1
SSH_USER=${2:-root}
PACKAGE=$(ls -t ai_platform_*.tar.gz 2>/dev/null | head -1)

if [ -z "${PACKAGE}" ]; then
    echo "錯誤: 找不到部署包，請先執行 ./scripts/1-package-deployment.sh"
    exit 1
fi

echo "快速部署到 ${SSH_USER}@${SERVER_IP}"
echo "使用部署包: ${PACKAGE}"
echo ""

# 上傳
./scripts/2-upload-to-server.sh "${SERVER_IP}" "${SSH_USER}"

# 遠端執行
ssh "${SSH_USER}@${SERVER_IP}" "cd /opt/ai_platform && sudo ./deploy-rhel-production.sh"

echo ""
echo "部署完成！"
EOFQUICK

chmod +x "${PROJECT_DIR}/quick-deploy.sh"

echo -e "${GREEN}✓ 快速部署腳本已創建: quick-deploy.sh${NC}"
echo ""
