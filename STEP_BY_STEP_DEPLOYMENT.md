# AI Platform Production 部署指南 - Step by Step

**目標環境:** Red Hat Enterprise Linux 9.4 + 2x NVIDIA H100 GPU
**預計部署時間:** 45-60 分鐘
**版本:** 2.0.0

---

## 目錄

1. [前置準備](#步驟-1-前置準備)
2. [系統環境檢查](#步驟-2-系統環境檢查)
3. [上傳部署文件](#步驟-3-上傳部署文件)
4. [安裝 NVIDIA 驅動](#步驟-4-安裝-nvidia-驅動)
5. [安裝 Docker](#步驟-5-安裝-docker)
6. [安裝 NVIDIA Container Toolkit](#步驟-6-安裝-nvidia-container-toolkit)
7. [配置環境變數](#步驟-7-配置環境變數)
8. [準備 SSL 憑證](#步驟-8-準備-ssl-憑證)
9. [執行自動部署腳本](#步驟-9-執行自動部署腳本)
10. [配置 Systemd 自動啟動](#步驟-10-配置-systemd-自動啟動)
11. [驗證部署狀態](#步驟-11-驗證部署狀態)
12. [設置監控告警](#步驟-12-設置監控告警)
13. [執行負載測試](#步驟-13-執行負載測試)
14. [配置防火牆](#步驟-14-配置防火牆)
15. [設置備份計畫](#步驟-15-設置備份計畫)

---

## 步驟 1: 前置準備

### 1.1 準備資訊清單

在開始部署前，請準備以下資訊：

```bash
# 伺服器資訊
生產伺服器 IP: _________________
SSH 用戶名稱: _________________
SSH 密鑰路徑: _________________
域名 (可選): _________________

# API 金鑰
OpenAI API Key: _________________
Anthropic API Key: _________________
Google Gemini API Key: _________________

# 資料庫密碼 (建議使用強密碼)
PostgreSQL 密碼: _________________
Redis 密碼: _________________
RabbitMQ 密碼: _________________

# SSL 憑證 (如果使用 HTTPS)
憑證文件路徑: _________________
私鑰文件路徑: _________________
```

### 1.2 確認硬體需求

```bash
最低需求:
✓ CPU: 32 cores
✓ RAM: 128 GB
✓ Storage: 500 GB SSD
✓ GPU: 2x NVIDIA H100 (80GB)
✓ Network: 10 Gbps
```

### 1.3 準備本地工作環境

```bash
# 在本地開發機器上
cd /path/to/your/ai_platform

# 確認所有文件都存在
ls -la docker-compose.production.yml
ls -la .env.production.example
ls -la deploy-rhel-production.sh
ls -la systemd/
ls -la config/
ls -la load-tests/
```

**完成確認:** ✓ 所有資訊已準備
**預計時間:** 10 分鐘

---

## 步驟 2: 系統環境檢查

### 2.1 SSH 連線到生產伺服器

```bash
# 從本地連線到生產伺服器
ssh -i ~/.ssh/your-key.pem root@your-production-server-ip

# 或使用密碼登入
ssh root@your-production-server-ip
```

### 2.2 確認作業系統版本

```bash
# 檢查 RHEL 版本 (應該是 9.4)
cat /etc/redhat-release

# 預期輸出：
# Red Hat Enterprise Linux release 9.4 (Plow)
```

### 2.3 檢查硬體資源

```bash
# 檢查 CPU
lscpu | grep -E "^CPU\(s\)|^Model name"

# 檢查記憶體
free -h

# 檢查磁碟空間
df -h /

# 檢查 GPU (如果驅動已安裝)
nvidia-smi || echo "NVIDIA 驅動尚未安裝"
```

### 2.4 更新系統套件

```bash
# 更新套件列表
sudo dnf update -y

# 安裝基本工具
sudo dnf install -y \
    wget curl git vim \
    tar unzip gcc make \
    kernel-devel kernel-headers
```

**完成確認:** ✓ 系統環境符合需求
**預計時間:** 5 分鐘

---

## 步驟 3: 上傳部署文件

### 3.1 在生產伺服器上建立目錄

```bash
# 在生產伺服器上執行
sudo mkdir -p /opt/ai_platform
sudo chown $USER:$USER /opt/ai_platform
cd /opt/ai_platform
```

### 3.2 從本地上傳文件

```bash
# 在本地開發機器上執行
cd /path/to/your/ai_platform

# 方法 1: 使用 SCP 上傳整個專案
scp -r \
    docker-compose.production.yml \
    .env.production.example \
    deploy-rhel-production.sh \
    systemd \
    config \
    load-tests \
    services \
    PRODUCTION_DEPLOYMENT.md \
    root@your-production-server-ip:/opt/ai_platform/

# 方法 2: 使用 rsync (更快，支援斷點續傳)
rsync -avz --progress \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    . root@your-production-server-ip:/opt/ai_platform/

# 方法 3: 打包後上傳 (適合網路不穩定)
tar -czf ai_platform_deployment.tar.gz \
    docker-compose.production.yml \
    .env.production.example \
    deploy-rhel-production.sh \
    systemd \
    config \
    load-tests \
    services \
    PRODUCTION_DEPLOYMENT.md

scp ai_platform_deployment.tar.gz root@your-production-server-ip:/tmp/

# 在生產伺服器上解壓
ssh root@your-production-server-ip
cd /opt/ai_platform
tar -xzf /tmp/ai_platform_deployment.tar.gz
rm /tmp/ai_platform_deployment.tar.gz
```

### 3.3 驗證文件完整性

```bash
# 在生產伺服器上執行
cd /opt/ai_platform

# 檢查主要文件
ls -lh docker-compose.production.yml
ls -lh deploy-rhel-production.sh
ls -lh .env.production.example

# 檢查目錄結構
tree -L 2 || ls -R
```

### 3.4 設置執行權限

```bash
# 設置腳本執行權限
chmod +x deploy-rhel-production.sh
chmod +x systemd/*.sh
chmod +x load-tests/*.sh
```

**完成確認:** ✓ 所有文件已上傳並驗證
**預計時間:** 10 分鐘

---

## 步驟 4: 安裝 NVIDIA 驅動

### 4.1 檢查 GPU 是否被偵測

```bash
# 檢查 PCI 設備
lspci | grep -i nvidia

# 預期輸出應包含兩個 H100
# 例如：
# 17:00.0 3D controller: NVIDIA Corporation Device 2330 (rev a1)
# 65:00.0 3D controller: NVIDIA Corporation Device 2330 (rev a1)
```

### 4.2 安裝 NVIDIA 官方驅動庫

```bash
# 添加 NVIDIA 驅動庫
sudo dnf config-manager --add-repo \
    https://developer.download.nvidia.com/compute/cuda/repos/rhel9/x86_64/cuda-rhel9.repo

# 更新套件索引
sudo dnf clean all
sudo dnf makecache
```

### 4.3 安裝 NVIDIA 驅動

```bash
# 安裝 NVIDIA 驅動 (550+ 版本支援 H100)
sudo dnf install -y nvidia-driver-latest-dkms

# 或指定版本
sudo dnf install -y nvidia-driver-550-dkms

# 安裝 CUDA 工具包 (12.0+)
sudo dnf install -y cuda-toolkit-12-4
```

### 4.4 重新啟動系統

```bash
# 重啟以載入驅動
sudo reboot

# 等待 2-3 分鐘後重新連線
# ssh root@your-production-server-ip
```

### 4.5 驗證 GPU 驅動

```bash
# 檢查驅動版本
nvidia-smi

# 預期輸出應顯示:
# - Driver Version: 550.x 或更高
# - CUDA Version: 12.4 或更高
# - 2x NVIDIA H100 80GB GPU
# - GPU 溫度、功耗、記憶體使用情況

# 檢查 CUDA 版本
nvcc --version
```

**完成確認:** ✓ NVIDIA 驅動已安裝，nvidia-smi 正常運作
**預計時間:** 15 分鐘 (含重啟)

---

## 步驟 5: 安裝 Docker

### 5.1 移除舊版本 Docker (如果存在)

```bash
sudo dnf remove -y \
    docker \
    docker-client \
    docker-client-latest \
    docker-common \
    docker-latest \
    docker-latest-logrotate \
    docker-logrotate \
    docker-engine \
    podman \
    runc
```

### 5.2 安裝 Docker CE

```bash
# 添加 Docker 官方庫
sudo dnf config-manager --add-repo \
    https://download.docker.com/linux/rhel/docker-ce.repo

# 安裝 Docker
sudo dnf install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin
```

### 5.3 啟動 Docker 服務

```bash
# 啟動並設置開機自動啟動
sudo systemctl start docker
sudo systemctl enable docker

# 檢查 Docker 狀態
sudo systemctl status docker

# 驗證 Docker 安裝
docker --version
docker compose version
```

### 5.4 測試 Docker 運作

```bash
# 執行測試容器
sudo docker run hello-world

# 預期輸出：
# Hello from Docker!
# This message shows that your installation appears to be working correctly.
```

### 5.5 將當前用戶加入 docker 群組 (可選)

```bash
# 加入 docker 群組 (避免每次都要 sudo)
sudo usermod -aG docker $USER

# 重新登入以生效
exit
ssh root@your-production-server-ip
```

**完成確認:** ✓ Docker 已安裝並正常運作
**預計時間:** 5 分鐘

---

## 步驟 6: 安裝 NVIDIA Container Toolkit

### 6.1 添加 NVIDIA Container Toolkit 庫

```bash
# 添加 NVIDIA 容器工具庫
curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | \
    sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo

# 更新套件索引
sudo dnf makecache
```

### 6.2 安裝 NVIDIA Container Toolkit

```bash
# 安裝工具包
sudo dnf install -y nvidia-container-toolkit
```

### 6.3 配置 Docker 使用 NVIDIA Runtime

```bash
# 配置 Docker daemon
sudo nvidia-ctk runtime configure --runtime=docker

# 重啟 Docker 服務
sudo systemctl restart docker
```

### 6.4 驗證 GPU 容器訪問

```bash
# 測試 GPU 容器
sudo docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi

# 預期輸出應顯示兩個 H100 GPU

# 測試指定單個 GPU
sudo docker run --rm --gpus '"device=0"' nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi

# 測試指定兩個 GPU
sudo docker run --rm --gpus '"device=0,1"' nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```

**完成確認:** ✓ Docker 容器可以訪問 GPU
**預計時間:** 5 分鐘

---

## 步驟 7: 配置環境變數

### 7.1 複製環境變數模板

```bash
cd /opt/ai_platform

# 複製模板文件
cp .env.production.example .env
```

### 7.2 編輯環境變數

```bash
# 使用 vim 或 nano 編輯
vim .env
# 或
nano .env
```

### 7.3 必填配置項目

**重要：請務必修改以下項目**

```bash
# === API 金鑰 (必須填寫) ===
OPENAI_API_KEY=sk-your-actual-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key
GOOGLE_API_KEY=your-actual-gemini-api-key

# === 資料庫密碼 (必須修改，使用強密碼) ===
POSTGRES_PASSWORD=YourSuperSecurePassword123!
REDIS_PASSWORD=YourRedisSecurePassword456!
RABBITMQ_DEFAULT_PASS=YourRabbitMQSecurePassword789!

# === 域名設定 ===
# 如果有域名，修改這個
DOMAIN=your-domain.com
# 如果只使用 IP，設為 localhost
DOMAIN=localhost

# === SSL/TLS 設定 ===
# 如果使用 HTTPS，設為 true
ENABLE_SSL=true
# 如果只用 HTTP，設為 false
ENABLE_SSL=false

# === GPU 設定 (已預設為雙 GPU) ===
ENABLE_GPU=true
CUDA_VISIBLE_DEVICES=0,1
OLLAMA_NUM_PARALLEL=4
OLLAMA_MAX_LOADED_MODELS=2

# === 效能調整 ===
MAX_CONCURRENT_REQUESTS=200
RATE_LIMIT_PER_MINUTE=60
```

### 7.4 生成安全密碼工具

```bash
# 生成強密碼 (32 字元)
openssl rand -base64 32

# 或使用 Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 生成多組密碼
for i in {1..3}; do
    echo "Password $i: $(openssl rand -base64 32)"
done
```

### 7.5 驗證環境變數

```bash
# 檢查必要變數是否已設定
grep -E "^(OPENAI_API_KEY|ANTHROPIC_API_KEY|POSTGRES_PASSWORD)" .env

# 確保沒有使用預設值
if grep -q "your-openai-api-key" .env; then
    echo "警告: 請修改 OPENAI_API_KEY!"
fi

if grep -q "changeme" .env; then
    echo "警告: 請修改資料庫密碼!"
fi
```

### 7.6 保護環境變數文件

```bash
# 設置只有 root 可讀
sudo chmod 600 .env
sudo chown root:root .env

# 驗證權限
ls -la .env
# 應顯示: -rw------- 1 root root
```

**完成確認:** ✓ 環境變數已配置並保護
**預計時間:** 10 分鐘

---

## 步驟 8: 準備 SSL 憑證

### 8.1 選擇 SSL 憑證方案

**方案 A: 使用 Let's Encrypt 免費憑證 (推薦)**

```bash
# 安裝 Certbot
sudo dnf install -y certbot

# 取得憑證 (需要停止其他佔用 80/443 port 的服務)
sudo certbot certonly --standalone -d your-domain.com

# 憑證位置:
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem
```

**方案 B: 使用自簽憑證 (僅測試用)**

```bash
# 建立憑證目錄
sudo mkdir -p /opt/ai_platform/certs

# 生成自簽憑證
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /opt/ai_platform/certs/privkey.pem \
    -out /opt/ai_platform/certs/fullchain.pem \
    -subj "/C=TW/ST=Taipei/L=Taipei/O=AI Platform/CN=your-domain.com"
```

**方案 C: 上傳現有憑證**

```bash
# 在本地機器上傳憑證
scp /path/to/your/fullchain.pem root@your-server:/opt/ai_platform/certs/
scp /path/to/your/privkey.pem root@your-server:/opt/ai_platform/certs/
```

### 8.2 設置憑證權限

```bash
# 設置憑證權限
sudo chmod 644 /opt/ai_platform/certs/fullchain.pem
sudo chmod 600 /opt/ai_platform/certs/privkey.pem
sudo chown root:root /opt/ai_platform/certs/*
```

### 8.3 更新 nginx 配置

```bash
# 如果使用自訂憑證路徑，編輯 nginx.conf
vim /opt/ai_platform/config/nginx/nginx.conf

# 修改憑證路徑 (找到這兩行並修改)
ssl_certificate /opt/ai_platform/certs/fullchain.pem;
ssl_certificate_key /opt/ai_platform/certs/privkey.pem;
```

### 8.4 不使用 SSL (HTTP only)

```bash
# 如果不使用 SSL，編輯 .env
vim /opt/ai_platform/.env

# 設置為 false
ENABLE_SSL=false

# 並註解掉 nginx.conf 中的 SSL 相關設定
```

**完成確認:** ✓ SSL 憑證已準備 (或已選擇 HTTP only)
**預計時間:** 10 分鐘

---

## 步驟 9: 執行自動部署腳本

### 9.1 檢查部署腳本

```bash
cd /opt/ai_platform

# 查看腳本內容 (可選)
less deploy-rhel-production.sh

# 確認腳本有執行權限
ls -l deploy-rhel-production.sh
```

### 9.2 執行部署腳本

```bash
# 執行自動部署 (會自動檢查所有依賴)
sudo ./deploy-rhel-production.sh

# 腳本會自動執行以下步驟:
# 1. 檢查 OS 版本
# 2. 檢查硬體資源 (CPU, RAM, Disk)
# 3. 檢查 NVIDIA 驅動
# 4. 檢查 CUDA
# 5. 檢查 Docker
# 6. 檢查 NVIDIA Container Toolkit
# 7. 配置防火牆
# 8. 拉取 Docker 映像
# 9. 啟動服務 (依序: 基礎設施 → LLM → 應用 → 監控)
# 10. 驗證服務狀態
```

### 9.3 監控部署過程

```bash
# 部署過程會顯示進度，例如:
# ✓ OS version check passed
# ✓ Hardware resources check passed
# ✓ NVIDIA drivers found (2 GPUs)
# ✓ CUDA toolkit found
# ✓ Docker running
# ✓ NVIDIA Container Toolkit found
# ⏳ Pulling Docker images...
# ⏳ Starting infrastructure services...
# ⏳ Starting LLM services...
# ⏳ Starting application services...
# ⏳ Starting monitoring services...
# ✓ Deployment completed successfully!
```

### 9.4 如果部署腳本失敗

```bash
# 查看詳細錯誤日誌
cat deploy.log

# 手動檢查各項依賴
./deploy-rhel-production.sh --check-only

# 重試部署
sudo ./deploy-rhel-production.sh --force
```

### 9.5 手動部署 (如果自動腳本失敗)

```bash
# 1. 拉取所有映像
sudo docker compose -f docker-compose.production.yml pull

# 2. 啟動基礎設施服務
sudo docker compose -f docker-compose.production.yml up -d \
    postgres redis qdrant rabbitmq

# 等待 15 秒讓資料庫初始化
sleep 15

# 3. 啟動 LLM 服務
sudo docker compose -f docker-compose.production.yml up -d \
    ollama litellm

# 等待 30 秒讓 LLM 服務就緒
sleep 30

# 4. 啟動應用服務
sudo docker compose -f docker-compose.production.yml up -d \
    mcp-server agent-service web-ui

# 5. 啟動監控服務
sudo docker compose -f docker-compose.production.yml up -d \
    prometheus grafana nginx
```

**完成確認:** ✓ 所有服務已啟動
**預計時間:** 15-20 分鐘 (含下載映像)

---

## 步驟 10: 配置 Systemd 自動啟動

### 10.1 安裝 Systemd 服務

```bash
cd /opt/ai_platform/systemd

# 執行安裝腳本
sudo ./install-systemd.sh

# 腳本會:
# 1. 複製服務文件到 /etc/systemd/system/
# 2. 重新載入 systemd
# 3. 啟用所有服務和定時器
# 4. 顯示使用說明
```

### 10.2 驗證 Systemd 服務

```bash
# 檢查主服務狀態
sudo systemctl status ai-platform

# 檢查備份定時器
sudo systemctl status ai-platform-backup.timer

# 檢查健康檢查定時器
sudo systemctl status ai-platform-healthcheck.timer

# 列出所有 AI Platform 相關服務
sudo systemctl list-units "ai-platform*"
```

### 10.3 測試自動重啟功能

```bash
# 停止平台
sudo systemctl stop ai-platform

# 等待幾秒後檢查 (應自動重啟)
sleep 10
sudo systemctl status ai-platform

# 檢查容器狀態
sudo docker ps
```

### 10.4 查看服務日誌

```bash
# 查看主服務日誌
sudo journalctl -u ai-platform -f

# 查看備份日誌
sudo journalctl -u ai-platform-backup -n 50

# 查看健康檢查日誌
sudo journalctl -u ai-platform-healthcheck -n 50
```

**完成確認:** ✓ Systemd 服務已啟用，重啟後自動啟動
**預計時間:** 5 分鐘

---

## 步驟 11: 驗證部署狀態

### 11.1 檢查所有容器狀態

```bash
# 查看所有容器
sudo docker ps -a

# 應該看到以下服務都是 Up 狀態:
# - postgres
# - redis
# - qdrant
# - rabbitmq
# - ollama
# - litellm
# - mcp-server (3 個副本)
# - agent-service (3 個副本)
# - web-ui (2 個副本)
# - prometheus
# - grafana
# - nginx
```

### 11.2 檢查服務健康狀態

```bash
# 健康檢查端點
curl -s http://localhost:8001/health | jq .

# 預期輸出:
# {
#   "status": "healthy",
#   "services": {
#     "postgres": "up",
#     "redis": "up",
#     "qdrant": "up",
#     "ollama": "up"
#   }
# }

# 檢查 MCP Server
curl -s http://localhost:8002/health

# 檢查 Agent Service
curl -s http://localhost:8000/health

# 檢查 LiteLLM
curl -s http://localhost:4000/health
```

### 11.3 檢查 GPU 使用情況

```bash
# 查看 GPU 狀態
nvidia-smi

# 持續監控 GPU
watch -n 1 nvidia-smi

# 檢查 Ollama 容器的 GPU 訪問
sudo docker exec ai-ollama-prod nvidia-smi
```

### 11.4 測試 Ollama 模型

```bash
# 進入 Ollama 容器
sudo docker exec -it ai-ollama-prod bash

# 拉取測試模型 (qwen2.5:7b)
ollama pull qwen2.5:7b

# 測試模型推理
ollama run qwen2.5:7b "Hello, how are you?"

# 離開容器
exit
```

### 11.5 檢查網路連線

```bash
# 測試內部網路
curl http://localhost:8501  # Web UI
curl http://localhost:8000  # Agent Service
curl http://localhost:8001  # MCP Server
curl http://localhost:3000  # Grafana

# 如果使用 NGINX (HTTPS)
curl https://localhost/health
# 或
curl https://your-domain.com/health
```

### 11.6 檢查日誌

```bash
# 查看所有服務日誌
sudo docker compose -f /opt/ai_platform/docker-compose.production.yml logs --tail=50

# 查看特定服務日誌
sudo docker compose -f /opt/ai_platform/docker-compose.production.yml logs agent-service --tail=100 -f

# 查看 Ollama 日誌
sudo docker logs ai-ollama-prod --tail=50 -f
```

**完成確認:** ✓ 所有服務健康，GPU 可訪問，端點正常回應
**預計時間:** 10 分鐘

---

## 步驟 12: 設置監控告警

### 12.1 訪問 Grafana

```bash
# 1. 取得 Grafana 管理員密碼
grep GRAFANA_ADMIN_PASSWORD /opt/ai_platform/.env

# 2. 在瀏覽器訪問 Grafana
http://localhost:3000
# 或
https://your-domain.com/grafana

# 3. 登入
# 用戶名: admin
# 密碼: (從上面取得)
```

### 12.2 驗證儀表板

```bash
# Grafana 應自動載入兩個儀表板:
# 1. AI Platform Overview (系統總覽)
# 2. GPU Monitoring (GPU 監控)

# 導航: Dashboards → Browse → AI Platform
```

### 12.3 配置告警規則

在 Grafana 中設置告警:

**高 GPU 溫度告警:**
```
條件: GPU 溫度 > 85°C 持續 5 分鐘
嚴重度: 警告
動作: 發送通知
```

**高錯誤率告警:**
```
條件: 錯誤率 > 5% 持續 5 分鐘
嚴重度: 嚴重
動作: 發送通知 + 自動重啟
```

**低 GPU 利用率告警:**
```
條件: GPU 利用率 < 10% 持續 30 分鐘
嚴重度: 資訊
動作: 記錄日誌
```

### 12.4 配置通知渠道

```bash
# 在 Grafana 中設置通知:
# Settings → Alerting → Contact points

# 支援的通知方式:
# - Email
# - Slack
# - Discord
# - Webhook
# - PagerDuty
```

### 12.5 測試告警

```bash
# 手動觸發測試告警
# 在 Grafana Alert 規則中點擊 "Test"

# 或手動製造高負載
stress --cpu 16 --timeout 60s
```

**完成確認:** ✓ Grafana 可訪問，儀表板顯示數據，告警已配置
**預計時間:** 15 分鐘

---

## 步驟 13: 執行負載測試

### 13.1 安裝測試工具

```bash
cd /opt/ai_platform/load-tests

# 安裝 Apache Bench
sudo dnf install -y httpd-tools

# 安裝 Python 依賴
pip3 install -r requirements.txt

# 驗證安裝
ab -V
locust --version
```

### 13.2 執行煙霧測試 (Smoke Test)

```bash
# 快速驗證測試 (5 用戶, 100 請求)
BASE_URL=http://localhost:8001 \
CONCURRENT_USERS=5 \
TOTAL_REQUESTS=100 \
./test-api-endpoints.sh

# 查看結果
cat results_*/SUMMARY.txt
```

### 13.3 執行負載測試 (Load Test)

```bash
# 模擬正常流量 (50 用戶, 10 分鐘)
locust -f locustfile.py \
    --host=http://localhost:8001 \
    --users 50 \
    --spawn-rate 5 \
    --run-time 10m \
    --headless \
    --csv=results/load_test

# 查看結果
cat results/load_test_stats.csv
```

### 13.4 執行壓力測試 (Stress Test)

```bash
# 模擬高峰流量 (200 用戶, 15 分鐘)
locust -f locustfile.py \
    --host=http://localhost:8001 \
    --users 200 \
    --spawn-rate 20 \
    --run-time 15m \
    --headless \
    --csv=results/stress_test
```

### 13.5 分析測試結果

```bash
# 檢查關鍵指標:
# - Response Time p95 < 1s ✓
# - Error Rate < 2% ✓
# - Throughput > 500 RPS ✓

# 如果測試失敗，檢查:
# 1. 服務是否全部啟動
sudo docker ps

# 2. 資源使用情況
htop
nvidia-smi

# 3. 服務日誌
sudo docker compose logs --tail=100
```

### 13.6 監控測試期間的指標

```bash
# 在另一個終端視窗監控:

# GPU 使用率
watch -n 1 nvidia-smi

# 容器資源使用
watch -n 1 'docker stats --no-stream'

# 服務日誌
sudo docker compose logs -f agent-service
```

**完成確認:** ✓ 負載測試通過，效能符合預期
**預計時間:** 20 分鐘

---

## 步驟 14: 配置防火牆

### 14.1 開放必要端口

```bash
# 如果使用 firewalld
sudo systemctl start firewalld
sudo systemctl enable firewalld

# 開放 HTTP (80)
sudo firewall-cmd --permanent --add-service=http

# 開放 HTTPS (443)
sudo firewall-cmd --permanent --add-service=https

# 開放 SSH (22) - 確保已開放
sudo firewall-cmd --permanent --add-service=ssh

# 開放 Grafana (3000) - 僅限信任 IP
sudo firewall-cmd --permanent --add-rich-rule='
  rule family="ipv4"
  source address="YOUR_OFFICE_IP/32"
  port protocol="tcp" port="3000" accept'

# 重新載入防火牆
sudo firewall-cmd --reload

# 查看開放的端口
sudo firewall-cmd --list-all
```

### 14.2 使用 iptables (替代方案)

```bash
# 如果不使用 firewalld，使用 iptables
sudo systemctl stop firewalld
sudo systemctl disable firewalld

# 開放端口
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# 保存規則
sudo iptables-save | sudo tee /etc/sysconfig/iptables
```

### 14.3 配置 SELinux

```bash
# 檢查 SELinux 狀態
getenforce

# 如果是 Enforcing，設置 Docker 相關權限
sudo setsebool -P container_manage_cgroup on
sudo setsebool -P docker_connect_any on

# 或暫時設為 Permissive (不建議生產環境)
sudo setenforce 0

# 永久修改 (編輯 /etc/selinux/config)
sudo vim /etc/selinux/config
# 改為: SELINUX=permissive
```

### 14.4 限制來源 IP (安全加固)

```bash
# 只允許特定 IP 訪問 (辦公室/VPN)
ALLOWED_IP="203.0.113.10"  # 替換為您的 IP

sudo firewall-cmd --permanent --add-rich-rule="
  rule family='ipv4'
  source address='${ALLOWED_IP}/32'
  port protocol='tcp' port='443' accept"

# 拒絕其他所有 IP
sudo firewall-cmd --permanent --add-rich-rule="
  rule family='ipv4'
  port protocol='tcp' port='443' reject"

sudo firewall-cmd --reload
```

**完成確認:** ✓ 防火牆已配置，只開放必要端口
**預計時間:** 5 分鐘

---

## 步驟 15: 設置備份計畫

### 15.1 驗證自動備份

```bash
# 檢查備份定時器狀態
sudo systemctl status ai-platform-backup.timer

# 查看下次備份時間
sudo systemctl list-timers ai-platform-backup.timer

# 手動執行備份測試
sudo systemctl start ai-platform-backup.service

# 查看備份日誌
sudo journalctl -u ai-platform-backup.service -n 50
```

### 15.2 檢查備份文件

```bash
# 備份位置
ls -lh /opt/ai_platform/backups/

# 應該包含:
# - backup_YYYYMMDD_HHMMSS.tar.gz (完整備份)
# - postgres_YYYYMMDD_HHMMSS.sql (資料庫備份)

# 檢查備份大小
du -sh /opt/ai_platform/backups/
```

### 15.3 測試備份還原

```bash
# 解壓備份測試
cd /tmp
sudo tar -xzf /opt/ai_platform/backups/backup_*.tar.gz

# 測試資料庫還原 (在測試環境)
# 警告: 不要在生產環境直接執行
sudo docker exec -i ai-postgres-prod psql -U ai_platform < /opt/ai_platform/backups/postgres_*.sql
```

### 15.4 設置遠端備份

```bash
# 方案 A: 複製到遠端伺服器 (rsync)
BACKUP_SERVER="backup-server.example.com"
BACKUP_PATH="/mnt/backups/ai_platform/"

# 設置 SSH 免密登入後執行
rsync -avz --delete \
    /opt/ai_platform/backups/ \
    ${BACKUP_SERVER}:${BACKUP_PATH}

# 方案 B: 上傳到 S3
# 安裝 AWS CLI
pip3 install awscli

# 配置 AWS 憑證
aws configure

# 同步到 S3
aws s3 sync /opt/ai_platform/backups/ s3://your-bucket/ai-platform-backups/

# 方案 C: 使用 Google Cloud Storage
# 安裝 gsutil
curl https://sdk.cloud.google.com | bash

# 同步到 GCS
gsutil -m rsync -r /opt/ai_platform/backups/ gs://your-bucket/ai-platform-backups/
```

### 15.5 配置備份保留策略

```bash
# 編輯備份腳本，添加保留策略
sudo vim /etc/systemd/system/ai-platform-backup.service

# 在 ExecStart 中添加清理舊備份 (保留 30 天)
find /opt/ai_platform/backups/ -type f -mtime +30 -delete
```

### 15.6 設置備份監控

```bash
# 創建備份監控腳本
cat > /opt/ai_platform/scripts/check-backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/ai_platform/backups"
LATEST_BACKUP=$(ls -t ${BACKUP_DIR}/backup_*.tar.gz | head -1)
BACKUP_AGE=$(find ${LATEST_BACKUP} -mtime +1 | wc -l)

if [ ${BACKUP_AGE} -gt 0 ]; then
    echo "WARNING: Latest backup is older than 24 hours!"
    exit 1
else
    echo "OK: Backup is current"
    exit 0
fi
EOF

sudo chmod +x /opt/ai_platform/scripts/check-backup.sh

# 測試執行
sudo /opt/ai_platform/scripts/check-backup.sh
```

**完成確認:** ✓ 自動備份已啟用，備份測試成功
**預計時間:** 10 分鐘

---

## 部署完成檢查清單

### 核心服務檢查

- [ ] 所有 Docker 容器都在運行 (`docker ps`)
- [ ] GPU 驅動正常 (`nvidia-smi`)
- [ ] GPU 在容器中可訪問 (`docker exec ollama nvidia-smi`)
- [ ] 所有健康檢查端點返回 200 OK
- [ ] Ollama 模型可以正常推理

### 網路與安全檢查

- [ ] HTTPS 正常運作 (如果啟用)
- [ ] 防火牆規則已配置
- [ ] 只開放必要端口 (80, 443, 22)
- [ ] 內部服務綁定到 localhost
- [ ] 環境變數文件權限正確 (600)

### 自動化與監控檢查

- [ ] Systemd 服務已啟用 (`systemctl list-units "ai-platform*"`)
- [ ] 重啟後服務自動啟動
- [ ] 備份定時器正常運作
- [ ] 健康檢查定時器正常運作
- [ ] Grafana 可訪問並顯示數據
- [ ] 告警規則已配置

### 效能與測試檢查

- [ ] 煙霧測試通過 (100 請求, 錯誤率 < 1%)
- [ ] 負載測試通過 (50 用戶, p95 < 1s)
- [ ] 壓力測試通過 (200 用戶, 無崩潰)
- [ ] GPU 利用率正常 (> 70% 在負載時)
- [ ] 記憶體使用正常 (< 85%)

### 備份與恢復檢查

- [ ] 自動備份已執行
- [ ] 備份文件完整
- [ ] 備份還原測試成功 (在測試環境)
- [ ] 遠端備份已配置 (如果需要)

---

## 常見問題排查

### Q1: Docker 容器無法啟動

```bash
# 檢查日誌
sudo docker compose logs service-name

# 檢查資源
docker stats

# 檢查網路
docker network inspect ai_platform_network

# 重新建立
sudo docker compose down
sudo docker compose up -d
```

### Q2: GPU 無法在容器中訪問

```bash
# 檢查驅動
nvidia-smi

# 檢查 NVIDIA Container Toolkit
sudo docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi

# 重新配置
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Q3: 服務啟動後無法訪問

```bash
# 檢查端口綁定
sudo netstat -tlnp | grep -E ':(8000|8001|8501|3000|443)'

# 檢查防火牆
sudo firewall-cmd --list-all

# 檢查 SELinux
sudo setenforce 0  # 暫時關閉測試
```

### Q4: Ollama 模型推理失敗

```bash
# 檢查 GPU 記憶體
nvidia-smi

# 檢查 Ollama 日誌
sudo docker logs ai-ollama-prod -f

# 重啟 Ollama
sudo docker restart ai-ollama-prod

# 重新拉取模型
sudo docker exec -it ai-ollama-prod ollama pull qwen2.5:7b
```

### Q5: 資料庫連線失敗

```bash
# 檢查 PostgreSQL 狀態
sudo docker exec ai-postgres-prod pg_isready

# 檢查連線
sudo docker exec -it ai-postgres-prod psql -U ai_platform -c "SELECT version();"

# 查看日誌
sudo docker logs ai-postgres-prod --tail=100
```

### Q6: 負載測試失敗

```bash
# 調整資源限制
vim docker-compose.production.yml
# 增加 CPU/Memory limits

# 調整並發數
vim .env
MAX_CONCURRENT_REQUESTS=100  # 降低

# 重新部署
sudo docker compose down
sudo docker compose up -d
```

---

## 生產環境維護建議

### 日常維護 (每天)

```bash
# 檢查服務狀態
sudo systemctl status ai-platform

# 檢查 GPU 狀態
nvidia-smi

# 查看最新日誌
sudo docker compose logs --tail=100 --since 24h
```

### 每週維護

```bash
# 檢查磁碟空間
df -h

# 清理舊日誌
sudo docker system prune -f

# 檢查備份
ls -lh /opt/ai_platform/backups/

# 查看 Grafana 儀表板
# 檢查效能趨勢
```

### 每月維護

```bash
# 更新 Docker 映像
sudo docker compose pull
sudo docker compose up -d

# 執行負載測試
cd /opt/ai_platform/load-tests
./test-api-endpoints.sh

# 檢查安全更新
sudo dnf check-update

# 審查告警日誌
sudo journalctl -u ai-platform --since "30 days ago" | grep -i error
```

### 安全更新

```bash
# 定期更新系統
sudo dnf update -y

# 更新 NVIDIA 驅動 (謹慎執行)
sudo dnf update nvidia-driver-latest-dkms

# 更新 Docker
sudo dnf update docker-ce docker-compose-plugin
```

---

## 緊急回復程序

### 完全重新部署

```bash
# 1. 停止所有服務
sudo systemctl stop ai-platform
sudo docker compose down

# 2. 清除所有容器和卷 (警告: 會刪除數據)
sudo docker compose down -v
sudo docker system prune -a -f

# 3. 從備份還原配置
sudo tar -xzf /opt/ai_platform/backups/backup_YYYYMMDD.tar.gz -C /opt/ai_platform/

# 4. 還原資料庫
sudo docker compose up -d postgres
sleep 10
sudo docker exec -i ai-postgres-prod psql -U ai_platform < backups/postgres_YYYYMMDD.sql

# 5. 重新部署
sudo ./deploy-rhel-production.sh
```

---

## 聯絡資訊與支援

### 部署支援

- **技術文檔:** `/opt/ai_platform/PRODUCTION_DEPLOYMENT.md`
- **故障排除:** `/opt/ai_platform/TROUBLESHOOTING_GUIDE.md`
- **負載測試:** `/opt/ai_platform/load-tests/README.md`

### 系統管理

```bash
# 快速狀態檢查腳本
cat > /usr/local/bin/ai-platform-status << 'EOF'
#!/bin/bash
echo "=== AI Platform Status ==="
echo ""
echo "System Services:"
systemctl is-active ai-platform
echo ""
echo "Docker Containers:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep ai-
echo ""
echo "GPU Status:"
nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used --format=csv,noheader
echo ""
echo "Disk Usage:"
df -h /opt/ai_platform
EOF

sudo chmod +x /usr/local/bin/ai-platform-status

# 使用: ai-platform-status
```

---

## 總結

恭喜！您已成功完成 AI Platform 的生產環境部署！

### 已完成的設置

✅ NVIDIA H100 GPU 驅動與 CUDA
✅ Docker 與 NVIDIA Container Toolkit
✅ 雙 GPU 加速的 AI 服務
✅ 高可用性服務副本
✅ Systemd 自動啟動
✅ 自動備份與健康檢查
✅ Grafana 監控儀表板
✅ 負載測試驗證
✅ 防火牆與安全加固
✅ SSL/TLS 加密 (如果啟用)

### 下一步建議

1. **監控運行 7 天**，觀察穩定性
2. **配置告警通知**到 Slack/Email
3. **執行定期負載測試**
4. **建立運維文檔**記錄常見問題
5. **設置異地備份**
6. **規劃擴展方案** (需要時增加節點)

### 重要提醒

⚠️ 定期檢查 GPU 溫度 (< 85°C)
⚠️ 監控磁碟空間 (保持 > 20% 可用)
⚠️ 每週檢查備份完整性
⚠️ 保持 NVIDIA 驅動更新
⚠️ 定期審查安全日誌

---

**部署完成！系統已準備好處理生產流量！** 🚀

**版本:** 2.0.0
**最後更新:** 2025-10-29
**文檔維護:** AI Platform DevOps Team
