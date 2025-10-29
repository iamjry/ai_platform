# AI Platform 離線部署指南

**適用場景：無法透過網路直接連線到生產伺服器**

---

## 📋 目錄

1. [適用場景](#適用場景)
2. [準備部署包](#準備部署包)
3. [複製到伺服器](#複製到伺服器)
4. [伺服器上執行部署](#伺服器上執行部署)
5. [手動驗證](#手動驗證)
6. [故障排除](#故障排除)

---

## 適用場景

以下情況需要使用離線部署：

- ✅ 伺服器在內網，無法直接 SSH 連線
- ✅ 需要透過跳板機或 VPN 才能訪問
- ✅ 安全政策限制網路連線
- ✅ 使用 USB 隨身碟/外接硬碟進行實體傳輸
- ✅ 需要在隔離環境中部署

---

## 準備部署包

### 步驟 1: 在本地開發機執行打包

```bash
# 切換到專案目錄
cd /path/to/your/ai_platform

# 執行打包腳本
./scripts/1-package-deployment.sh
```

**輸出:**
```
ai_platform_20251029_220000.tar.gz  (完整部署包)
```

### 步驟 2: 確認打包內容

```bash
# 查看壓縮包大小
ls -lh ai_platform_*.tar.gz

# 查看壓縮包內容
tar -tzf ai_platform_*.tar.gz | head -20

# 計算 MD5 校驗碼（用於驗證完整性）
md5sum ai_platform_*.tar.gz > ai_platform.md5
```

### 步驟 3: 需要複製的檔案清單

**必須複製的檔案：**

```
ai_platform_YYYYMMDD_HHMMSS.tar.gz  (主要部署包)
ai_platform.md5                      (MD5 校驗碼)
```

**可選檔案（方便參考）：**

```
STEP_BY_STEP_DEPLOYMENT.md           (部署指南)
DEPLOYMENT_QUICK_REFERENCE.md        (快速參考)
OFFLINE_DEPLOYMENT_GUIDE.md          (本指南)
```

---

## 複製到伺服器

### 方法 A: 使用 USB 隨身碟/外接硬碟

#### 在本地開發機：

```bash
# 假設 USB 隨身碟掛載在 /Volumes/USB
USB_PATH="/Volumes/USB"

# 複製部署包
cp ai_platform_*.tar.gz "${USB_PATH}/"
cp ai_platform.md5 "${USB_PATH}/"

# 複製文檔（可選）
cp STEP_BY_STEP_DEPLOYMENT.md "${USB_PATH}/"
cp DEPLOYMENT_QUICK_REFERENCE.md "${USB_PATH}/"
cp OFFLINE_DEPLOYMENT_GUIDE.md "${USB_PATH}/"

# 安全退出 USB
diskutil eject /Volumes/USB
```

#### 在生產伺服器：

```bash
# 掛載 USB 隨身碟
# RHEL 通常自動掛載在 /run/media/<username>/USB_NAME
# 或手動掛載
mkdir -p /mnt/usb
mount /dev/sdb1 /mnt/usb

# 複製到伺服器
mkdir -p /opt/ai_platform
cp /mnt/usb/ai_platform_*.tar.gz /opt/ai_platform/
cp /mnt/usb/ai_platform.md5 /opt/ai_platform/

# 退出 USB
umount /mnt/usb
```

### 方法 B: 透過跳板機 (Jump Host)

```bash
# 步驟 1: 從本地複製到跳板機
scp ai_platform_*.tar.gz user@jumphost:/tmp/
scp ai_platform.md5 user@jumphost:/tmp/

# 步驟 2: 登入跳板機
ssh user@jumphost

# 步驟 3: 從跳板機複製到目標伺服器
scp /tmp/ai_platform_*.tar.gz root@target-server:/opt/ai_platform/
scp /tmp/ai_platform.md5 root@target-server:/opt/ai_platform/
```

### 方法 C: 透過共享磁碟/NFS

```bash
# 在本地複製到共享磁碟
cp ai_platform_*.tar.gz /mnt/shared_storage/
cp ai_platform.md5 /mnt/shared_storage/

# 在生產伺服器讀取
cp /mnt/shared_storage/ai_platform_*.tar.gz /opt/ai_platform/
cp /mnt/shared_storage/ai_platform.md5 /opt/ai_platform/
```

### 方法 D: 分片傳輸（檔案過大時）

```bash
# 在本地分片（每片 500MB）
split -b 500M ai_platform_*.tar.gz ai_platform_part_

# 產生分片列表
ls ai_platform_part_* > parts.list

# 傳輸所有分片到伺服器
# （透過任何可用方式）

# 在伺服器上合併
cat ai_platform_part_* > ai_platform_YYYYMMDD_HHMMSS.tar.gz

# 清理分片
rm ai_platform_part_*
```

---

## 伺服器上執行部署

### 步驟 1: 驗證檔案完整性

```bash
# 連線到生產伺服器（透過終端機或 KVM）
cd /opt/ai_platform

# 驗證 MD5
md5sum -c ai_platform.md5

# 應該看到:
# ai_platform_20251029_220000.tar.gz: OK
```

### 步驟 2: 解壓部署包

```bash
cd /opt/ai_platform

# 解壓
tar -xzf ai_platform_*.tar.gz

# 驗證解壓內容
ls -la

# 應該看到:
# docker-compose.production.yml
# .env.production.example
# deploy-rhel-production.sh
# services/
# config/
# systemd/
# load-tests/
# scripts/
```

### 步驟 3: 設置執行權限

```bash
cd /opt/ai_platform

# 設置腳本執行權限
chmod +x deploy-rhel-production.sh
chmod +x systemd/*.sh
chmod +x load-tests/*.sh
chmod +x scripts/*.sh
```

### 步驟 4: 配置環境變數

```bash
# 複製環境變數範本
cp .env.production.example .env

# 編輯環境變數
vim .env

# 或使用 nano
nano .env
```

**必須修改的項目：**

```bash
# API 金鑰
OPENAI_API_KEY=sk-your-actual-openai-key
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key
GOOGLE_API_KEY=your-actual-gemini-key

# 資料庫密碼（使用強密碼）
POSTGRES_PASSWORD=YourStrongPassword123!
REDIS_PASSWORD=YourRedisPassword456!
RABBITMQ_DEFAULT_PASS=YourRabbitMQPassword789!

# GPU 設定（確認）
ENABLE_GPU=true
CUDA_VISIBLE_DEVICES=0,1

# 域名設定
DOMAIN=your-domain.com  # 或 localhost
```

**保護環境變數檔案：**

```bash
chmod 600 .env
chown root:root .env
```

### 步驟 5: 檢查系統依賴

```bash
# 檢查作業系統
cat /etc/redhat-release

# 檢查 NVIDIA 驅動
nvidia-smi

# 檢查 Docker
docker --version
docker compose version

# 檢查 NVIDIA Container Toolkit
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```

**如果依賴缺失，請參考 `STEP_BY_STEP_DEPLOYMENT.md` 步驟 4-6 進行安裝。**

### 步驟 6: 執行部署腳本

```bash
cd /opt/ai_platform

# 執行部署
sudo ./deploy-rhel-production.sh

# 部署會執行以下步驟：
# 1. 檢查系統依賴
# 2. 配置防火牆
# 3. 拉取 Docker 映像
# 4. 啟動基礎設施服務
# 5. 啟動 LLM 服務
# 6. 啟動應用服務
# 7. 啟動監控服務
# 8. 驗證部署狀態
```

**預計時間:** 20-30 分鐘

### 步驟 7: 監控部署進度

在另一個終端視窗中：

```bash
# 查看容器狀態
watch -n 2 'docker ps --format "table {{.Names}}\t{{.Status}}"'

# 查看日誌
docker compose -f /opt/ai_platform/docker-compose.production.yml logs -f

# 查看 GPU 使用
watch -n 1 nvidia-smi
```

---

## 手動驗證

### 驗證 1: 檢查容器狀態

```bash
cd /opt/ai_platform

# 查看所有容器
docker ps

# 應該看到以下容器運行中：
# - ai-postgres-prod
# - ai-redis-prod
# - ai-qdrant-prod
# - ai-rabbitmq-prod
# - ai-ollama-prod
# - ai-litellm-prod
# - ai-mcp-server-1, ai-mcp-server-2, ai-mcp-server-3
# - ai-agent-service-1, ai-agent-service-2, ai-agent-service-3
# - ai-web-ui-1, ai-web-ui-2
# - ai-prometheus-prod
# - ai-grafana-prod
# - ai-nginx-prod

# 檢查停止的容器
docker ps -a --filter "status=exited"

# 如果有容器停止，查看日誌
docker logs <container-name>
```

### 驗證 2: 測試 API 端點

```bash
# 測試 MCP Server
curl -s http://localhost:8001/health | jq .

# 測試 Agent Service
curl -s http://localhost:8000/health | jq .

# 測試 LiteLLM
curl -s http://localhost:4000/health | jq .

# 測試 Web UI
curl -s http://localhost:8501

# 測試 Grafana
curl -s http://localhost:3000/api/health | jq .
```

### 驗證 3: 檢查 GPU 狀態

```bash
# 主機 GPU
nvidia-smi

# 檢查溫度和使用率
nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv

# 容器內 GPU
docker exec ai-ollama-prod nvidia-smi
```

### 驗證 4: 測試資料庫連線

```bash
# PostgreSQL
docker exec ai-postgres-prod pg_isready

# Redis
docker exec ai-redis-prod redis-cli ping

# 應該回應: PONG
```

### 驗證 5: 檢查日誌

```bash
# 查看最近錯誤
docker compose logs --tail=100 | grep -i error

# 查看特定服務
docker compose logs agent-service --tail=50

# 持續監控
docker compose logs -f
```

### 驗證 6: 檢查系統資源

```bash
# CPU 和記憶體
top
# 或
htop

# 磁碟空間
df -h

# 容器資源使用
docker stats --no-stream

# 網路端口
ss -tlnp | grep -E ':(8000|8001|8501|3000|11434)'
```

---

## 手動負載測試

### 快速煙霧測試

```bash
cd /opt/ai_platform/load-tests

# 執行快速測試（5 用戶, 100 請求）
BASE_URL=http://localhost:8001 \
CONCURRENT_USERS=5 \
TOTAL_REQUESTS=100 \
./test-api-endpoints.sh

# 查看結果
cat results_*/SUMMARY.txt
```

### 完整負載測試

```bash
cd /opt/ai_platform/load-tests

# 安裝測試工具
pip3 install -r requirements.txt

# 執行負載測試（50 用戶, 10 分鐘）
locust -f locustfile.py \
    --host=http://localhost:8001 \
    --users 50 \
    --spawn-rate 5 \
    --run-time 10m \
    --headless \
    --csv=results/load_test
```

---

## 配置 Systemd 自動啟動

```bash
cd /opt/ai_platform/systemd

# 執行安裝腳本
sudo ./install-systemd.sh

# 驗證服務
sudo systemctl status ai-platform
sudo systemctl status ai-platform-backup.timer
sudo systemctl status ai-platform-healthcheck.timer

# 測試重啟
sudo systemctl restart ai-platform

# 查看日誌
sudo journalctl -u ai-platform -f
```

---

## 訪問服務

### 服務 URL

| 服務 | URL | 預設帳密 |
|------|-----|---------|
| **Web UI** | http://server-ip:8501 | - |
| **API (MCP)** | http://server-ip:8001 | - |
| **Agent Service** | http://server-ip:8000 | - |
| **Grafana** | http://server-ip:3000 | admin / (見 .env) |
| **Prometheus** | http://server-ip:9090 | - |
| **Ollama** | http://server-ip:11434 | - |

### 從本地瀏覽器訪問

如果伺服器在內網，可以使用 SSH 隧道：

```bash
# 在本地機器執行
ssh -L 8501:localhost:8501 \
    -L 8001:localhost:8001 \
    -L 3000:localhost:3000 \
    root@server-ip

# 然後在瀏覽器訪問
# http://localhost:8501  (Web UI)
# http://localhost:3000  (Grafana)
```

---

## 故障排除

### 問題 1: 解壓失敗

**症狀:**
```
tar: Error opening archive: Failed to open
```

**解決方案:**
```bash
# 檢查檔案完整性
md5sum ai_platform_*.tar.gz

# 檢查磁碟空間
df -h /opt

# 重新傳輸檔案
```

### 問題 2: Docker 映像拉取失敗

**症狀:**
```
Error response from daemon: Get https://registry-1.docker.io/v2/: net/http: TLS handshake timeout
```

**解決方案:**
```bash
# 檢查網路連線
ping 8.8.8.8

# 配置 Docker 代理（如需要）
sudo mkdir -p /etc/systemd/system/docker.service.d
sudo vim /etc/systemd/system/docker.service.d/http-proxy.conf

# 添加：
# [Service]
# Environment="HTTP_PROXY=http://proxy:port"
# Environment="HTTPS_PROXY=http://proxy:port"

sudo systemctl daemon-reload
sudo systemctl restart docker
```

### 問題 3: GPU 無法訪問

**症狀:**
```
docker: Error response from daemon: could not select device driver "" with capabilities: [[gpu]].
```

**解決方案:**
```bash
# 檢查 NVIDIA 驅動
nvidia-smi

# 重新配置 NVIDIA Container Toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# 測試 GPU 訪問
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```

### 問題 4: 環境變數未生效

**症狀:**
```
容器啟動失敗，日誌顯示缺少 API 金鑰
```

**解決方案:**
```bash
# 檢查 .env 文件
cat .env | grep API_KEY

# 確認權限
ls -l .env

# 重新啟動容器
docker compose down
docker compose up -d
```

### 問題 5: 端口被佔用

**症狀:**
```
Error starting userland proxy: listen tcp4 0.0.0.0:8001: bind: address already in use
```

**解決方案:**
```bash
# 查找佔用端口的進程
sudo lsof -i :8001
# 或
sudo ss -tlnp | grep :8001

# 停止佔用進程
sudo kill -9 <PID>

# 重新啟動服務
docker compose up -d
```

---

## 離線部署檢查清單

### 準備階段
- [ ] 已執行打包腳本
- [ ] 已生成 MD5 校驗碼
- [ ] 已準備傳輸媒介（USB/跳板機/共享磁碟）
- [ ] 已複製文檔（可選）

### 傳輸階段
- [ ] 已複製部署包到伺服器
- [ ] 已複製 MD5 校驗碼
- [ ] 已驗證檔案完整性

### 部署階段
- [ ] 已解壓部署包
- [ ] 已設置執行權限
- [ ] 已配置環境變數
- [ ] 已檢查系統依賴
- [ ] 已執行部署腳本

### 驗證階段
- [ ] 所有容器運行中
- [ ] API 端點回應正常
- [ ] GPU 正常運作
- [ ] 資料庫連線正常
- [ ] 無錯誤日誌

### 完成階段
- [ ] 已配置 Systemd 自動啟動
- [ ] 已執行煙霧測試
- [ ] 已訪問 Grafana 儀表板
- [ ] 已設置監控告警

---

## 快速命令參考

```bash
# === 伺服器上的常用命令 ===

# 切換到專案目錄
cd /opt/ai_platform

# 查看容器狀態
docker ps

# 查看日誌
docker compose logs -f

# 重啟服務
docker compose restart

# 停止服務
docker compose down

# 啟動服務
docker compose up -d

# 查看 GPU
nvidia-smi

# 測試 API
curl http://localhost:8001/health

# 查看系統資源
htop
df -h
docker stats
```

---

## 總結

離線部署流程：

1. **本地** → 打包部署文件
2. **傳輸** → 複製到伺服器（USB/跳板機/共享磁碟）
3. **伺服器** → 解壓並執行部署
4. **驗證** → 確認服務正常運行
5. **完成** → 配置自動啟動和監控

**預計時間:** 30-45 分鐘（不含傳輸時間）

---

**版本:** 2.0.0
**最後更新:** 2025-10-29
**文檔維護:** AI Platform DevOps Team
