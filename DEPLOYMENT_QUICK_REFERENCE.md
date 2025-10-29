# AI Platform 部署快速參考卡

**快速上手指南 - 5 分鐘了解所有部署命令**

---

## 🚀 一鍵部署（推薦）

```bash
# 完整部署到生產環境
./scripts/deploy-one-click.sh <server-ip> [ssh-user] [ssh-key]

# 範例
./scripts/deploy-one-click.sh 192.168.1.100 root ~/.ssh/production.pem
```

**耗時:** 40-60 分鐘
**包含:** 打包 + 上傳 + 部署 + 驗證

---

## 📦 分步驟部署

### 1️⃣ 打包部署文件

```bash
./scripts/1-package-deployment.sh
```

**輸出:** `ai_platform_YYYYMMDD_HHMMSS.tar.gz`

### 2️⃣ 上傳到伺服器

```bash
./scripts/2-upload-to-server.sh <server-ip> [ssh-user] [ssh-key]

# 範例
./scripts/2-upload-to-server.sh 192.168.1.100 root
```

**目標:** `/opt/ai_platform/`

### 3️⃣ 遠端部署

```bash
./scripts/3-remote-deploy.sh <server-ip> [ssh-user] [ssh-key]
```

**耗時:** 20-30 分鐘

### 4️⃣ 驗證部署

```bash
./scripts/4-verify-deployment.sh <server-ip> [ssh-user] [ssh-key]
```

**檢查項:** 25+ 項健康檢查

### 5️⃣ 負載測試

```bash
# 煙霧測試（快速驗證）
./scripts/5-run-load-tests.sh <server-ip> <ssh-user> '' smoke

# 負載測試（正常流量）
./scripts/5-run-load-tests.sh <server-ip> <ssh-user> '' load

# 壓力測試（高峰流量）
./scripts/5-run-load-tests.sh <server-ip> <ssh-user> '' stress

# 全部測試
./scripts/5-run-load-tests.sh <server-ip> <ssh-user> '' all
```

---

## 🔧 常用命令

### 連線到伺服器

```bash
ssh root@<server-ip>
cd /opt/ai_platform
```

### 查看容器狀態

```bash
docker ps
docker ps -a
docker stats
```

### 查看日誌

```bash
# 所有服務
docker compose logs -f

# 特定服務
docker compose logs -f agent-service
docker compose logs -f mcp-server
docker compose logs -f ollama

# 最近 100 行
docker logs ai-agent-service-1 --tail=100
```

### 重啟服務

```bash
# 重啟特定容器
docker restart ai-agent-service-1

# 重啟所有服務
docker compose restart

# 完全重啟
docker compose down
docker compose up -d
```

### 檢查 GPU

```bash
# 主機 GPU
nvidia-smi
watch -n 1 nvidia-smi

# 容器 GPU
docker exec ai-ollama-prod nvidia-smi
```

### 檢查健康狀態

```bash
# API 健康檢查
curl http://localhost:8001/health
curl http://localhost:8000/health
curl http://localhost:4000/health

# 資料庫連線
docker exec ai-postgres-prod pg_isready
docker exec ai-redis-prod redis-cli ping
```

### 查看系統資源

```bash
# CPU 和記憶體
htop
top

# 磁碟空間
df -h

# 容器資源
docker stats --no-stream
```

---

## 📊 訪問服務

| 服務 | URL | 預設帳密 |
|------|-----|---------|
| **Web UI** | http://server-ip:8501 | - |
| **API (MCP)** | http://server-ip:8001 | - |
| **Agent Service** | http://server-ip:8000 | - |
| **Grafana** | http://server-ip:3000 | admin / (見 .env) |
| **Prometheus** | http://server-ip:9090 | - |
| **Ollama** | http://server-ip:11434 | - |

---

## 🔥 緊急命令

### 快速重啟

```bash
ssh root@<server-ip> 'cd /opt/ai_platform && docker compose restart'
```

### 停止所有服務

```bash
ssh root@<server-ip> 'cd /opt/ai_platform && docker compose down'
```

### 查看最新錯誤

```bash
ssh root@<server-ip> 'cd /opt/ai_platform && docker compose logs --tail=50 | grep -i error'
```

### 檢查服務狀態

```bash
./scripts/4-verify-deployment.sh <server-ip> root
```

### 回滾部署

```bash
ssh root@<server-ip>
cd /opt/ai_platform
docker compose down
tar -xzf backups/backup_before_deploy_*.tar.gz -C /tmp/restore/
cp -r /tmp/restore/* .
docker compose up -d
```

---

## 🛠️ 配置 Systemd 自動啟動

```bash
# 在伺服器上執行
ssh root@<server-ip>
cd /opt/ai_platform/systemd
sudo ./install-systemd.sh

# 檢查狀態
sudo systemctl status ai-platform

# 重啟測試
sudo reboot
```

---

## 📝 環境變數配置

```bash
# 在伺服器上編輯
ssh root@<server-ip>
cd /opt/ai_platform
vim .env

# 必填項目:
# OPENAI_API_KEY=sk-xxx
# ANTHROPIC_API_KEY=sk-ant-xxx
# GOOGLE_API_KEY=AIzaxxx
# POSTGRES_PASSWORD=xxx
# REDIS_PASSWORD=xxx
# RABBITMQ_DEFAULT_PASS=xxx
```

---

## 🎯 測試目標

| 測試類型 | 用戶數 | 持續時間 | p95 目標 | 錯誤率目標 |
|---------|--------|---------|---------|-----------|
| **煙霧** | 5 | 2 分鐘 | < 500ms | < 1% |
| **負載** | 50 | 10 分鐘 | < 1s | < 2% |
| **壓力** | 200 | 15 分鐘 | < 2s | < 5% |

---

## 📞 故障排除

### SSH 連線失敗
```bash
ssh -v root@<server-ip>
ping <server-ip>
```

### 容器無法啟動
```bash
docker compose down
docker compose up -d
docker compose logs -f
```

### GPU 無法訪問
```bash
nvidia-smi
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### API 無回應
```bash
docker logs ai-mcp-server-1 --tail=100
curl -v http://localhost:8001/health
sudo firewall-cmd --list-all
```

---

## 📚 完整文檔

- **Step by Step 部署:** `STEP_BY_STEP_DEPLOYMENT.md`
- **腳本使用指南:** `DEPLOYMENT_SCRIPTS_GUIDE.md`
- **生產部署文檔:** `PRODUCTION_DEPLOYMENT.md`
- **負載測試指南:** `load-tests/README.md`

---

## ⚡ 快速腳本

```bash
# 創建快捷別名（在本地 .bashrc 或 .zshrc）
alias aip-deploy='./scripts/deploy-one-click.sh'
alias aip-verify='./scripts/4-verify-deployment.sh'
alias aip-test='./scripts/5-run-load-tests.sh'
alias aip-connect='ssh root@<server-ip>'

# 使用
aip-deploy 192.168.1.100 root
aip-verify 192.168.1.100 root
aip-test 192.168.1.100 root '' smoke
```

---

**版本:** 2.0.0 | **更新:** 2025-10-29
