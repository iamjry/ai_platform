# 生產環境快速啟動指南
**目標**: Red Hat Enterprise Linux v9 + 2x Nvidia H100 GPUs

---

## 🚀 快速部署 (5 步驟)

### 1. 前置檢查
```bash
# 確認系統
cat /etc/redhat-release  # 應顯示 RHEL 9.x

# 確認 GPU
nvidia-smi  # 應看到 2 張 H100

# 確認 Docker
docker --version  # 24.0+
docker compose version  # 2.20+

# 測試 GPU in Docker
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

### 2. 配置環境變數
```bash
cd /opt/ai-platform  # 或您的部署目錄

# 複製並編輯環境變數
cp .env.prod.template .env.prod
vim .env.prod

# 必須修改的值:
# - POSTGRES_PASSWORD
# - REDIS_PASSWORD
# - RABBITMQ_DEFAULT_PASS
# - OPENAI_API_KEY
# - ANTHROPIC_API_KEY
# - LITELLM_MASTER_KEY
# - GRAFANA_ADMIN_PASSWORD
```

### 3. 執行部署腳本
```bash
# 給予執行權限
chmod +x deploy-prod.sh health-check.sh

# 開始部署（完整模式）
./deploy-prod.sh

# 選擇選項 1: 完整部署
# 預計時間: 30-40 分鐘（首次）
```

### 4. 驗證部署
```bash
# 執行健康檢查
./health-check.sh

# 預期結果: 所有服務 ✅ Healthy
```

### 5. 訪問服務
```bash
# 獲取伺服器 IP
hostname -I

# 訪問 Web UI
http://<SERVER_IP>:8501
```

---

## 📊 GPU 配置

### GPU 分配
- **GPU 0**: Ollama (本地 LLM)
- **GPU 1**: MCP Server (DeepSeek-OCR)

### 驗證 GPU 使用
```bash
# 持續監控
watch -n 1 nvidia-smi

# 檢查容器 GPU
docker inspect ai-ollama-prod | jq '.[0].HostConfig.DeviceRequests'
docker inspect ai-mcp-server-prod | jq '.[0].HostConfig.DeviceRequests'
```

### 測試 OCR GPU 後端
```bash
curl http://localhost:8001/tools/ocr_get_status | jq .

# 預期看到:
# "DeepSeek-OCR": {
#   "available": true,
#   "cuda_available": true
# }
```

---

## 🔧 常用指令

### 服務管理
```bash
# 啟動
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d

# 停止
docker compose --env-file .env.prod -f docker-compose.prod.yml down

# 重啟特定服務
docker compose --env-file .env.prod -f docker-compose.prod.yml restart mcp-server

# 查看日誌
docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f mcp-server
```

### 監控
```bash
# 健康檢查
./health-check.sh

# GPU 監控
nvidia-smi -l 1

# 容器資源
docker stats

# 系統資源
htop
```

### 維護
```bash
# 備份資料庫
docker exec ai-postgres-prod pg_dump -U ai_platform_user ai_platform_prod > backup.sql

# 清理未使用映像檔
docker system prune -a

# 查看磁碟使用
df -h
docker system df
```

---

## 🎯 服務端口

| 服務 | 端口 | 說明 |
|------|------|------|
| Web UI | 8501 | 主要使用者界面 |
| Agent Service | 8002 | Agent 執行引擎 |
| MCP Server | 8001 | 工具與 OCR 服務 |
| LiteLLM | 4000 | LLM 代理 |
| Grafana | 3000 | 監控儀表板 |
| Prometheus | 9090 | 指標收集 |
| PostgreSQL | 5433 | 資料庫 |
| Redis | 6380 | 快取 |
| RabbitMQ | 5672, 15672 | 訊息佇列 |

---

## ⚡ 效能指標

### GPU OCR 效能
- **DeepSeek-OCR**: 0.5-1 秒/頁
- **EasyOCR (CPU fallback)**: 2-5 秒/頁
- **記憶體**: ~10-15 GB VRAM

### 系統資源
- **總記憶體**: 建議 128GB+
- **CPU**: 建議 16+ cores
- **儲存**: 2TB+ NVMe SSD

### 並發能力
- **Web UI**: 50+ 並發用戶
- **API**: 100+ requests/sec
- **OCR**: 10+ 並發處理

---

## ❗ 疑難排解

### 問題: GPU 無法使用

```bash
# 重新配置 NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# 驗證
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

### 問題: DeepSeek-OCR 未啟用

```bash
# 檢查日誌
docker logs ai-mcp-server-prod | grep -i cuda

# 進入容器測試
docker exec -it ai-mcp-server-prod python3 -c "import torch; print(torch.cuda.is_available())"

# 重啟服務
docker compose --env-file .env.prod -f docker-compose.prod.yml restart mcp-server
```

### 問題: 服務無法啟動

```bash
# 檢查日誌
docker compose --env-file .env.prod -f docker-compose.prod.yml logs <service>

# 檢查資源
free -h
df -h

# 檢查端口占用
ss -tulpn | grep -E "8501|8002|8001|4000"
```

### 問題: SELinux 阻止

```bash
# 查看 SELinux 狀態
getenforce

# 臨時關閉（測試用）
sudo setenforce 0

# 永久配置（建議）
sudo chcon -R -t container_file_t /opt/ai-platform
```

---

## 🔒 安全檢查清單

- [ ] 修改所有預設密碼
- [ ] .env.prod 權限設為 600
- [ ] 配置防火牆規則
- [ ] 啟用 SSL/TLS (Nginx + Let's Encrypt)
- [ ] 限制外部訪問端口
- [ ] 啟用日誌審計
- [ ] 定期安全更新
- [ ] 備份策略已設定

---

## 📚 完整文檔

詳細資訊請參考:

- **完整部署指南**: `RHEL9_DEPLOYMENT_GUIDE.md`
- **平台狀況**: `PLATFORM_STATUS.md`
- **OCR 測試**: `OCR_TESTING_GUIDE.md`
- **專案總覽**: `PROJECT_OVERVIEW.md`

---

## 🆘 獲取幫助

### 查看日誌
```bash
# 所有服務
docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f

# 特定服務
docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f mcp-server

# 最近 100 行
docker logs --tail 100 ai-mcp-server-prod
```

### 檢查配置
```bash
# Docker Compose 配置
docker compose --env-file .env.prod -f docker-compose.prod.yml config

# 環境變數
docker exec ai-mcp-server-prod env | grep -i cuda
```

---

**部署支援**: 參考 `RHEL9_DEPLOYMENT_GUIDE.md` 獲取詳細說明

**部署時間**: 首次 ~40 分鐘 | 後續 ~10 分鐘

**系統就緒**: 執行 `./health-check.sh` 確認所有服務健康 ✅
