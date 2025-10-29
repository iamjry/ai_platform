#!/bin/bash

###############################################################################
# AI Platform - Prepare Offline Deployment Package
# 準備離線部署包（適合無法直接連線伺服器的情況）
###############################################################################

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  AI Platform - 準備離線部署包${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# 獲取腳本目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OFFLINE_DIR="${PROJECT_DIR}/offline_deployment_${TIMESTAMP}"

echo "配置資訊:"
echo "  ├─ 專案目錄: ${PROJECT_DIR}"
echo "  ├─ 離線包目錄: ${OFFLINE_DIR}"
echo "  └─ 時間戳記: ${TIMESTAMP}"
echo ""

echo -e "${YELLOW}步驟 1: 執行標準打包...${NC}"

cd "${PROJECT_DIR}"

# 執行打包腳本
if [ -f "${SCRIPT_DIR}/1-package-deployment.sh" ]; then
    bash "${SCRIPT_DIR}/1-package-deployment.sh"
else
    echo -e "${RED}錯誤: 找不到打包腳本${NC}"
    exit 1
fi

# 尋找最新的部署包
LATEST_PACKAGE=$(ls -t ai_platform_*.tar.gz 2>/dev/null | head -1)

if [ -z "${LATEST_PACKAGE}" ]; then
    echo -e "${RED}錯誤: 找不到部署包${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 標準打包完成: ${LATEST_PACKAGE}${NC}"
echo ""

echo -e "${YELLOW}步驟 2: 創建離線部署目錄...${NC}"

mkdir -p "${OFFLINE_DIR}"
mkdir -p "${OFFLINE_DIR}/docs"
mkdir -p "${OFFLINE_DIR}/scripts"

echo -e "${GREEN}✓ 離線目錄已創建${NC}"
echo ""

echo -e "${YELLOW}步驟 3: 複製部署包...${NC}"

# 複製主要部署包
cp "${LATEST_PACKAGE}" "${OFFLINE_DIR}/"

# 計算 MD5
md5sum "${LATEST_PACKAGE}" > "${OFFLINE_DIR}/ai_platform.md5"

PACKAGE_SIZE=$(du -sh "${LATEST_PACKAGE}" | awk '{print $1}')
echo -e "${GREEN}✓ 部署包已複製 (${PACKAGE_SIZE})${NC}"
echo ""

echo -e "${YELLOW}步驟 4: 複製文檔...${NC}"

# 複製所有相關文檔
DOCS=(
    "STEP_BY_STEP_DEPLOYMENT.md"
    "PRODUCTION_DEPLOYMENT.md"
    "DEPLOYMENT_SCRIPTS_GUIDE.md"
    "DEPLOYMENT_QUICK_REFERENCE.md"
    "OFFLINE_DEPLOYMENT_GUIDE.md"
    "ADDITIONAL_RESOURCES_SUMMARY.md"
    "DEPLOYMENT_PACKAGE_SUMMARY.md"
)

for doc in "${DOCS[@]}"; do
    if [ -f "${PROJECT_DIR}/${doc}" ]; then
        cp "${PROJECT_DIR}/${doc}" "${OFFLINE_DIR}/docs/"
        echo "  ✓ ${doc}"
    fi
done

echo -e "${GREEN}✓ 文檔已複製${NC}"
echo ""

echo -e "${YELLOW}步驟 5: 創建離線安裝腳本...${NC}"

# 創建伺服器端安裝腳本
cat > "${OFFLINE_DIR}/install-on-server.sh" << 'EOFINSTALL'
#!/bin/bash

###############################################################################
# AI Platform - 伺服器端離線安裝腳本
# 在目標伺服器上執行此腳本進行部署
###############################################################################

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  AI Platform - 伺服器端離線安裝${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# 檢查是否為 root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}建議使用 root 權限執行此腳本${NC}"
    echo "請執行: sudo $0"
    echo ""
fi

INSTALL_DIR="/opt/ai_platform"
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "配置資訊:"
echo "  ├─ 當前目錄: ${CURRENT_DIR}"
echo "  └─ 安裝目錄: ${INSTALL_DIR}"
echo ""

echo -e "${YELLOW}步驟 1: 驗證檔案完整性...${NC}"

cd "${CURRENT_DIR}"

# 尋找部署包
PACKAGE=$(ls ai_platform_*.tar.gz 2>/dev/null | head -1)

if [ -z "${PACKAGE}" ]; then
    echo -e "${RED}錯誤: 找不到部署包${NC}"
    exit 1
fi

# 驗證 MD5
if [ -f "ai_platform.md5" ]; then
    if md5sum -c ai_platform.md5; then
        echo -e "${GREEN}✓ 檔案完整性驗證通過${NC}"
    else
        echo -e "${RED}✗ 檔案完整性驗證失敗${NC}"
        echo "請重新傳輸檔案"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ 警告: 找不到 MD5 校驗檔，跳過完整性驗證${NC}"
fi

echo ""

echo -e "${YELLOW}步驟 2: 創建安裝目錄...${NC}"

sudo mkdir -p "${INSTALL_DIR}"

echo -e "${GREEN}✓ 安裝目錄已創建${NC}"
echo ""

echo -e "${YELLOW}步驟 3: 解壓部署包...${NC}"

sudo tar -xzf "${PACKAGE}" -C "${INSTALL_DIR}"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 部署包已解壓${NC}"
else
    echo -e "${RED}✗ 解壓失敗${NC}"
    exit 1
fi

echo ""

echo -e "${YELLOW}步驟 4: 設置執行權限...${NC}"

cd "${INSTALL_DIR}"

sudo chmod +x deploy-rhel-production.sh 2>/dev/null || true
sudo chmod +x systemd/*.sh 2>/dev/null || true
sudo chmod +x load-tests/*.sh 2>/dev/null || true
sudo chmod +x scripts/*.sh 2>/dev/null || true

echo -e "${GREEN}✓ 執行權限已設置${NC}"
echo ""

echo -e "${YELLOW}步驟 5: 檢查系統依賴...${NC}"

# 檢查作業系統
echo "作業系統:"
cat /etc/redhat-release || echo "無法識別的作業系統"
echo ""

# 檢查 NVIDIA 驅動
echo "NVIDIA 驅動:"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=index,name,driver_version --format=csv,noheader
    echo -e "${GREEN}✓ NVIDIA 驅動已安裝${NC}"
else
    echo -e "${RED}✗ NVIDIA 驅動未安裝${NC}"
    echo "請參考 STEP_BY_STEP_DEPLOYMENT.md 步驟 4"
fi
echo ""

# 檢查 Docker
echo "Docker:"
if command -v docker &> /dev/null; then
    docker --version
    echo -e "${GREEN}✓ Docker 已安裝${NC}"
else
    echo -e "${RED}✗ Docker 未安裝${NC}"
    echo "請參考 STEP_BY_STEP_DEPLOYMENT.md 步驟 5"
fi
echo ""

# 檢查 Docker Compose
echo "Docker Compose:"
if docker compose version &> /dev/null; then
    docker compose version
    echo -e "${GREEN}✓ Docker Compose 已安裝${NC}"
else
    echo -e "${RED}✗ Docker Compose 未安裝${NC}"
fi
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  安裝準備完成！${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

echo "下一步:"
echo "  1. 配置環境變數:"
echo "     ${YELLOW}cd ${INSTALL_DIR}${NC}"
echo "     ${YELLOW}cp .env.production.example .env${NC}"
echo "     ${YELLOW}vim .env${NC}"
echo ""
echo "  2. 執行部署腳本:"
echo "     ${YELLOW}sudo ./deploy-rhel-production.sh${NC}"
echo ""
echo "  3. 或參考完整部署指南:"
echo "     ${YELLOW}less docs/STEP_BY_STEP_DEPLOYMENT.md${NC}"
echo "     ${YELLOW}less docs/OFFLINE_DEPLOYMENT_GUIDE.md${NC}"
echo ""
EOFINSTALL

chmod +x "${OFFLINE_DIR}/install-on-server.sh"

echo -e "${GREEN}✓ 離線安裝腳本已創建${NC}"
echo ""

echo -e "${YELLOW}步驟 6: 創建使用說明...${NC}"

cat > "${OFFLINE_DIR}/README.txt" << EOFREADME
AI Platform 離線部署包
=====================

版本: 2.0.0
建立時間: $(date)
包大小: ${PACKAGE_SIZE}

目錄結構:
---------
ai_platform_${TIMESTAMP}.tar.gz    主要部署包
ai_platform.md5                     MD5 校驗碼
install-on-server.sh                伺服器安裝腳本
docs/                               完整文檔
  ├─ OFFLINE_DEPLOYMENT_GUIDE.md    離線部署指南 ⭐
  ├─ STEP_BY_STEP_DEPLOYMENT.md     詳細部署步驟
  ├─ DEPLOYMENT_QUICK_REFERENCE.md  快速參考
  └─ 其他文檔...

快速開始:
---------

1. 將整個目錄複製到目標伺服器
   方式: USB隨身碟 / 跳板機 / 共享磁碟

2. 在伺服器上執行安裝腳本
   cd offline_deployment_${TIMESTAMP}
   sudo ./install-on-server.sh

3. 配置環境變數
   cd /opt/ai_platform
   cp .env.production.example .env
   vim .env

4. 執行部署
   sudo ./deploy-rhel-production.sh

詳細說明:
---------
請閱讀 docs/OFFLINE_DEPLOYMENT_GUIDE.md

支援:
-----
如有問題，請參考:
- docs/OFFLINE_DEPLOYMENT_GUIDE.md (離線部署完整指南)
- docs/STEP_BY_STEP_DEPLOYMENT.md (15步驟詳細指南)
- docs/DEPLOYMENT_QUICK_REFERENCE.md (快速參考卡片)

系統需求:
---------
- Red Hat Enterprise Linux 9.4
- 2x NVIDIA H100 GPU
- 128 GB RAM
- 500 GB SSD
- NVIDIA Driver 550+
- CUDA 12.4+
- Docker & Docker Compose
- NVIDIA Container Toolkit

檔案完整性驗證:
---------------
在伺服器上執行:
  md5sum -c ai_platform.md5

預計部署時間:
-----------
30-45 分鐘 (不含依賴安裝)

EOFREADME

echo -e "${GREEN}✓ 使用說明已創建${NC}"
echo ""

echo -e "${YELLOW}步驟 7: 創建傳輸檢查清單...${NC}"

cat > "${OFFLINE_DIR}/CHECKLIST.txt" << EOFCHECKLIST
離線部署檢查清單
==============

準備階段:
--------
[ ] 已執行 prepare-offline-deployment.sh
[ ] 已生成離線部署包
[ ] 已驗證 MD5 校驗碼
[ ] 已準備傳輸媒介 (USB/跳板機/共享磁碟)

傳輸階段:
--------
[ ] 已複製整個 offline_deployment_${TIMESTAMP} 目錄到伺服器
[ ] 已驗證檔案完整性 (md5sum -c ai_platform.md5)
[ ] 已確認所有檔案都可讀取

安裝階段:
--------
[ ] 已執行 install-on-server.sh
[ ] 已解壓部署包到 /opt/ai_platform
[ ] 已設置執行權限
[ ] 已檢查系統依賴 (NVIDIA驅動, Docker, CUDA)

配置階段:
--------
[ ] 已複製 .env.production.example 到 .env
[ ] 已修改 API 金鑰 (OpenAI, Anthropic, Gemini)
[ ] 已修改資料庫密碼 (Postgres, Redis, RabbitMQ)
[ ] 已確認 GPU 設定 (ENABLE_GPU=true, CUDA_VISIBLE_DEVICES=0,1)
[ ] 已設置 .env 權限 (chmod 600 .env)

部署階段:
--------
[ ] 已執行 deploy-rhel-production.sh
[ ] 所有 Docker 映像已拉取
[ ] 所有容器已啟動 (docker ps 檢查)
[ ] 無錯誤日誌 (docker compose logs 檢查)

驗證階段:
--------
[ ] API 端點回應正常 (curl http://localhost:8001/health)
[ ] GPU 正常運作 (nvidia-smi)
[ ] 資料庫連線正常 (docker exec ai-postgres-prod pg_isready)
[ ] 已執行煙霧測試 (load-tests/test-api-endpoints.sh)

完成階段:
--------
[ ] 已配置 Systemd 自動啟動 (systemd/install-systemd.sh)
[ ] 已訪問 Grafana 儀表板 (http://server-ip:3000)
[ ] 已設置監控告警
[ ] 已記錄部署資訊

問題記錄:
--------
(記錄部署過程中遇到的問題和解決方案)




EOFCHECKLIST

echo -e "${GREEN}✓ 檢查清單已創建${NC}"
echo ""

echo -e "${YELLOW}步驟 8: 生成離線部署摘要...${NC}"

# 計算總大小
TOTAL_SIZE=$(du -sh "${OFFLINE_DIR}" | awk '{print $1}')
FILE_COUNT=$(find "${OFFLINE_DIR}" -type f | wc -l)

cat > "${OFFLINE_DIR}/MANIFEST.txt" << EOFMANIFEST
AI Platform 離線部署包清單
=========================

建立時間: $(date)
版本: 2.0.0
總大小: ${TOTAL_SIZE}
檔案數: ${FILE_COUNT}

目錄結構:
--------
$(cd "${OFFLINE_DIR}" && tree -L 2 2>/dev/null || find . -maxdepth 2 -type f | sort)

檔案列表:
--------
$(cd "${OFFLINE_DIR}" && find . -type f -exec ls -lh {} \; | awk '{print $9, "("$5")"}' | sort)

MD5 校驗碼:
---------
$(cat "${OFFLINE_DIR}/ai_platform.md5")

使用方式:
--------
1. 複製此目錄到目標伺服器
2. 執行: sudo ./install-on-server.sh
3. 參考 docs/OFFLINE_DEPLOYMENT_GUIDE.md

EOFMANIFEST

echo -e "${GREEN}✓ 部署清單已生成${NC}"
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  離線部署包準備完成！${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

echo "離線部署包資訊:"
echo "  ├─ 目錄: ${OFFLINE_DIR}"
echo "  ├─ 大小: ${TOTAL_SIZE}"
echo "  ├─ 檔案數: ${FILE_COUNT}"
echo "  └─ 部署包: ${LATEST_PACKAGE} (${PACKAGE_SIZE})"
echo ""

echo "目錄內容:"
ls -lh "${OFFLINE_DIR}/"
echo ""

echo "下一步 - 傳輸到伺服器:"
echo ""
echo "方法 A: 使用 USB 隨身碟"
echo "  ${YELLOW}cp -r ${OFFLINE_DIR} /Volumes/USB/${NC}"
echo ""
echo "方法 B: 透過跳板機"
echo "  ${YELLOW}scp -r ${OFFLINE_DIR} user@jumphost:/tmp/${NC}"
echo "  ${YELLOW}ssh user@jumphost${NC}"
echo "  ${YELLOW}scp -r /tmp/offline_deployment_* root@target-server:/tmp/${NC}"
echo ""
echo "方法 C: 透過共享磁碟"
echo "  ${YELLOW}cp -r ${OFFLINE_DIR} /mnt/shared_storage/${NC}"
echo ""

echo "在伺服器上安裝:"
echo "  ${YELLOW}cd /tmp/offline_deployment_${TIMESTAMP}${NC}"
echo "  ${YELLOW}sudo ./install-on-server.sh${NC}"
echo ""

echo "文檔參考:"
echo "  ${YELLOW}cat ${OFFLINE_DIR}/README.txt${NC}"
echo "  ${YELLOW}less ${OFFLINE_DIR}/docs/OFFLINE_DEPLOYMENT_GUIDE.md${NC}"
echo ""

echo -e "${GREEN}✅ 離線部署包已準備就緒！${NC}"
echo ""
