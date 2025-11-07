# Red Hat Enterprise Linux v9 部署指南
## AI Platform with 2x Nvidia H100 GPUs

**目標環境**:
- Red Hat Enterprise Linux v9
- 2x Nvidia H100 80GB GPUs
- CUDA 12.2+
- Docker with GPU support

---

## 📋 目錄

1. [系統需求](#系統需求)
2. [前置準備](#前置準備)
3. [安裝步驟](#安裝步驟)
4. [GPU 配置驗證](#gpu-配置驗證)
5. [部署平台](#部署平台)
6. [監控與維護](#監控與維護)
7. [疑難排解](#疑難排解)
8. [安全建議](#安全建議)

---

## 系統需求

### 硬體需求

- **CPU**: 16+ cores (建議 32+)
- **RAM**: 128GB+ (建議 256GB)
- **GPU**: 2x Nvidia H100 80GB
- **儲存**:
  - 系統碟: 500GB+ SSD
  - 資料碟: 2TB+ NVMe SSD
  - 模型快取: 500GB+ (可選)

### 軟體需求

- **作業系統**: Red Hat Enterprise Linux 9.x
- **Kernel**: 5.14+
- **Docker**: 24.0+
- **Docker Compose**: 2.20+
- **NVIDIA Driver**: 535+ (支援 CUDA 12.2)
- **NVIDIA Container Toolkit**: Latest
- **CUDA**: 12.2+

---

## 前置準備

### 1. 更新系統

```bash
# 以 root 或 sudo 執行
sudo dnf update -y
sudo dnf install -y epel-release
```

### 2. 安裝基本工具

```bash
sudo dnf install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    iotop \
    nethogs \
    tmux \
    jq \
    python3 \
    python3-pip
```

### 3. 安裝 NVIDIA Driver

```bash
# 添加 NVIDIA 官方 repo
sudo dnf config-manager --add-repo \
    https://developer.download.nvidia.com/compute/cuda/repos/rhel9/x86_64/cuda-rhel9.repo

# 安裝 NVIDIA driver
sudo dnf module install -y nvidia-driver:latest-dkms

# 安裝 CUDA toolkit
sudo dnf install -y cuda-toolkit-12-2

# 重啟系統
sudo reboot
```

### 4. 驗證 GPU 驅動

```bash
# 檢查 GPU 狀態
nvidia-smi

# 預期輸出應顯示 2 張 H100 GPU
# GPU 0: NVIDIA H100 80GB
# GPU 1: NVIDIA H100 80GB

# 檢查 CUDA 版本
nvcc --version
# 應顯示 CUDA 12.2 或更高
```

### 5. 安裝 Docker

```bash
# 添加 Docker CE repository
sudo dnf config-manager --add-repo \
    https://download.docker.com/linux/rhel/docker-ce.repo

# 安裝 Docker
sudo dnf install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin

# 啟動 Docker 服務
sudo systemctl start docker
sudo systemctl enable docker

# 驗證 Docker 安裝
docker --version
docker compose version

# 將當前用戶加入 docker 群組（避免每次 sudo）
sudo usermod -aG docker $USER
# 重新登入或執行: newgrp docker
```

### 6. 安裝 NVIDIA Container Toolkit

```bash
# 設定 repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.repo | \
    sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo

# 安裝 NVIDIA Container Toolkit
sudo dnf install -y nvidia-container-toolkit

# 配置 Docker runtime
sudo nvidia-ctk runtime configure --runtime=docker

# 重啟 Docker
sudo systemctl restart docker
```

---

## GPU 配置驗證

### 測試 GPU 在 Docker 中的可用性

```bash
# 測試 GPU 訪問
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

# 測試指定 GPU
docker run --rm --gpus '"device=0"' nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
docker run --rm --gpus '"device=1"' nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

# 測試 CUDA 運算
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 \
    /usr/local/cuda/samples/bin/x86_64/linux/release/deviceQuery
```

**預期結果**:
- 應該看到兩張 H100 GPU
- CUDA Version 應為 12.2 或更高
- 所有測試應該 PASS

---

## 部署平台

### 1. 克隆專案

```bash
# 創建部署目錄
sudo mkdir -p /opt/ai-platform
sudo chown $USER:$USER /opt/ai-platform
cd /opt/ai-platform

# 克隆專案 (假設使用 Git)
git clone <YOUR_REPO_URL> .

# 或直接複製檔案到此目錄
```

### 2. 配置環境變數

```bash
# 複製環境變數範本
cp .env.prod.template .env.prod

# 編輯環境變數
vim .env.prod

# 必須配置的項目：
# - POSTGRES_PASSWORD
# - REDIS_PASSWORD
# - RABBITMQ_DEFAULT_PASS
# - OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY
# - LITELLM_MASTER_KEY
# - GRAFANA_ADMIN_PASSWORD
```

**安全建議**:
```bash
# 設定適當的檔案權限
chmod 600 .env.prod
chown $USER:$USER .env.prod

# 確保 .env.prod 不在版本控制中
echo ".env.prod" >> .gitignore
```

### 3. 建構 Docker 映像檔

```bash
# 使用生產環境配置
export COMPOSE_FILE=docker-compose.prod.yml

# 建構所有服務
docker compose build --no-cache

# 查看建構的映像檔
docker images | grep ai_platform
```

**預期建構時間**:
- MCP Server (含 GPU): 20-30 分鐘 (首次，需下載 CUDA 相關套件)
- Agent Service: 5-10 分鐘
- Web UI: 5-10 分鐘

### 4. 初始化資料庫

```bash
# 先啟動資料庫服務
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d postgres redis qdrant

# 等待資料庫就緒
sleep 10

# 檢查資料庫狀態
docker compose --env-file .env.prod -f docker-compose.prod.yml ps postgres
```

### 5. 啟動所有服務

```bash
# 啟動所有服務
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d

# 查看服務狀態
docker compose --env-file .env.prod -f docker-compose.prod.yml ps

# 查看日誌
docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f

# 查看特定服務日誌
docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f mcp-server
```

### 6. 驗證 GPU 使用情況

```bash
# 監控 GPU 使用
watch -n 1 nvidia-smi

# 預期看到：
# GPU 0: Ollama (處理本地 LLM 推理)
# GPU 1: MCP Server (處理 DeepSeek-OCR)

# 檢查容器 GPU 配置
docker inspect ai-mcp-server-prod | jq '.[0].HostConfig.DeviceRequests'
docker inspect ai-ollama-prod | jq '.[0].HostConfig.DeviceRequests'
```

### 7. 驗證服務健康狀態

```bash
# 檢查所有服務健康狀態
docker compose --env-file .env.prod -f docker-compose.prod.yml ps

# 使用健康檢查腳本（創建以下腳本）
cat > check_health.sh << 'EOF'
#!/bin/bash
echo "=== AI Platform Health Check ==="
echo ""

services=(
    "http://localhost:8501/_stcore/health|Web UI"
    "http://localhost:8002/health|Agent Service"
    "http://localhost:8001/health|MCP Server"
    "http://localhost:4000/health|LiteLLM"
    "http://localhost:9090/-/healthy|Prometheus"
    "http://localhost:3000/api/health|Grafana"
)

for service in "${services[@]}"; do
    IFS='|' read -r url name <<< "$service"
    if curl -sf "$url" > /dev/null 2>&1; then
        echo "✅ $name: Healthy"
    else
        echo "❌ $name: Unhealthy"
    fi
done

echo ""
echo "=== GPU Status ==="
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv
EOF

chmod +x check_health.sh
./check_health.sh
```

### 8. 測試 OCR 功能

```bash
# 測試 OCR 狀態
curl -s http://localhost:8001/tools/ocr_get_status | jq .

# 預期輸出應包含：
# {
#   "ocr_available": true,
#   "backends": [
#     {
#       "name": "EasyOCR",
#       "type": "cpu",
#       "available": true
#     },
#     {
#       "name": "DeepSeek-OCR",
#       "type": "gpu",
#       "available": true,    <-- 應為 true
#       "cuda_available": true <-- 應為 true
#     }
#   ]
# }
```

---

## 監控與維護

### 1. 系統監控

**Prometheus + Grafana**:
```bash
# 訪問 Grafana
http://<SERVER_IP>:3000

# 預設帳號: 在 .env.prod 中設定的 GRAFANA_ADMIN_USER/PASSWORD
```

**GPU 監控**:
```bash
# 持續監控 GPU
watch -n 1 nvidia-smi

# 查看 GPU 詳細資訊
nvidia-smi -l 1

# 記錄 GPU 使用到檔案
nvidia-smi --query-gpu=timestamp,name,pci.bus_id,driver_version,pstate,pcie.link.gen.max,pcie.link.gen.current,temperature.gpu,utilization.gpu,utilization.memory,memory.total,memory.free,memory.used --format=csv -l 5 > gpu_log.csv
```

### 2. 日誌管理

```bash
# 查看服務日誌
docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f --tail=100 <service_name>

# 日誌位置（JSON 格式）
# 所有容器日誌在: /var/lib/docker/containers/<container_id>/<container_id>-json.log

# 清理舊日誌（謹慎使用）
docker system prune -a --volumes
```

### 3. 備份策略

```bash
# 備份資料庫
docker exec ai-postgres-prod pg_dump -U ai_platform_user ai_platform_prod > backup_$(date +%Y%m%d).sql

# 備份 Docker Volumes
docker run --rm \
    -v ai_platform_postgres_data:/data \
    -v $(pwd)/backups:/backup \
    alpine tar czf /backup/postgres_data_$(date +%Y%m%d).tar.gz /data

# 備份配置檔案
tar czf config_backup_$(date +%Y%m%d).tar.gz \
    .env.prod \
    config/ \
    docker-compose.prod.yml
```

### 4. 定期維護

**每日**:
- 檢查服務健康狀態: `./check_health.sh`
- 監控 GPU 使用率
- 檢查日誌錯誤

**每週**:
- 檢查磁碟空間: `df -h`
- 檢查 Docker 映像檔大小: `docker system df`
- 清理未使用的映像檔: `docker image prune -a`

**每月**:
- 更新系統套件: `sudo dnf update -y`
- 輪替密鑰和憑證
- 完整備份

---

## 疑難排解

### 問題 1: GPU 無法被 Docker 識別

**症狀**:
```bash
docker: Error response from daemon: could not select device driver "" with capabilities: [[gpu]].
```

**解決方案**:
```bash
# 重新配置 NVIDIA Container Toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# 驗證配置
cat /etc/docker/daemon.json
# 應包含 "nvidia" runtime
```

### 問題 2: DeepSeek-OCR 未使用 GPU

**檢查**:
```bash
# 查看 MCP Server 日誌
docker compose logs mcp-server | grep -i "cuda\|gpu"

# 進入容器檢查
docker exec -it ai-mcp-server-prod bash
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
python3 -c "import torch; print(f'GPU count: {torch.cuda.device_count()}')"
```

**解決方案**:
```bash
# 確認環境變數
docker exec ai-mcp-server-prod env | grep -i cuda

# 重啟服務
docker compose --env-file .env.prod -f docker-compose.prod.yml restart mcp-server
```

### 問題 3: 記憶體不足 (OOM)

**症狀**:
```bash
# 容器被 killed
docker logs ai-mcp-server-prod | tail -20
# 看到: Killed
```

**解決方案**:
```bash
# 檢查系統記憶體
free -h

# 調整 Docker Compose 資源限制
# 編輯 docker-compose.prod.yml 中的 deploy.resources.limits
```

### 問題 4: SELinux 阻止容器啟動

**症狀**:
```bash
# 容器無法訪問掛載的 volumes
Permission denied
```

**解決方案**:
```bash
# 方案 1: 暫時關閉 SELinux（不建議用於生產環境）
sudo setenforce 0

# 方案 2: 配置 SELinux context（建議）
sudo chcon -R -t container_file_t /opt/ai-platform/config
sudo chcon -R -t container_file_t /var/lib/docker/volumes

# 方案 3: 使用 :z 或 :Z volume 標記
# 在 docker-compose.prod.yml 中：
# volumes:
#   - ./config:/app/config:z
```

### 問題 5: 網路連接問題

**檢查**:
```bash
# 檢查 Docker 網路
docker network ls
docker network inspect ai_platform_ai-platform

# 測試容器間連接
docker exec ai-web-ui-prod curl -v http://agent-service:8000/health
```

---

## 安全建議

### 1. 防火牆配置

```bash
# 使用 firewalld (RHEL 9 預設)
sudo systemctl start firewalld
sudo systemctl enable firewalld

# 只開放必要的端口（根據需求調整）
sudo firewall-cmd --permanent --add-port=8501/tcp  # Web UI
sudo firewall-cmd --permanent --add-port=8001/tcp  # MCP Server (如需外部訪問)
sudo firewall-cmd --permanent --add-port=8002/tcp  # Agent Service (如需外部訪問)
sudo firewall-cmd --permanent --add-port=22/tcp    # SSH

# 重新載入配置
sudo firewall-cmd --reload

# 查看開放的端口
sudo firewall-cmd --list-all
```

### 2. SSL/TLS 配置

**建議使用 Nginx 反向代理**:

```bash
# 安裝 Nginx
sudo dnf install -y nginx certbot python3-certbot-nginx

# 配置反向代理
sudo vim /etc/nginx/conf.d/ai-platform.conf
```

範例 Nginx 配置:
```nginx
upstream web_ui {
    server localhost:8501;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://web_ui;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. 定期安全更新

```bash
# 設定自動安全更新
sudo dnf install -y dnf-automatic
sudo systemctl enable --now dnf-automatic.timer

# 配置更新策略
sudo vim /etc/dnf/automatic.conf
# 設定: apply_updates = yes (僅安全更新)
```

### 4. 審計與日誌

```bash
# 啟用 auditd
sudo systemctl start auditd
sudo systemctl enable auditd

# 監控 Docker 事件
docker events &

# 設定日誌輪替
sudo vim /etc/logrotate.d/ai-platform
```

---

## 效能調校

### 1. CUDA 最佳化

```bash
# 設定 CUDA 快取
export CUDA_CACHE_PATH=/var/cache/cuda
sudo mkdir -p $CUDA_CACHE_PATH
sudo chmod 777 $CUDA_CACHE_PATH

# 設定持久化模式 (提升 GPU 效能)
sudo nvidia-smi -pm 1

# 設定 GPU 時脈 (H100 預設已優化，可選)
sudo nvidia-smi -lgc 1980  # 設定最大時脈
```

### 2. Docker 效能調校

```bash
# 編輯 Docker daemon 配置
sudo vim /etc/docker/daemon.json
```

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "5"
  },
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ],
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 64000,
      "Soft": 64000
    }
  }
}
```

### 3. 系統參數調校

```bash
# 編輯 sysctl
sudo vim /etc/sysctl.d/99-ai-platform.conf
```

```conf
# 網路優化
net.core.somaxconn = 4096
net.ipv4.tcp_max_syn_backlog = 8192
net.core.netdev_max_backlog = 5000

# 記憶體優化
vm.swappiness = 10
vm.dirty_ratio = 40
vm.dirty_background_ratio = 10

# 檔案描述符限制
fs.file-max = 2097152
```

應用配置:
```bash
sudo sysctl -p /etc/sysctl.d/99-ai-platform.conf
```

---

## 快速參考指令

### 服務管理

```bash
# 啟動所有服務
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d

# 停止所有服務
docker compose --env-file .env.prod -f docker-compose.prod.yml down

# 重啟特定服務
docker compose --env-file .env.prod -f docker-compose.prod.yml restart <service>

# 查看日誌
docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f <service>

# 進入容器
docker exec -it <container_name> bash
```

### 監控指令

```bash
# GPU 監控
nvidia-smi -l 1

# 容器資源使用
docker stats

# 系統資源
htop
iotop
nethogs
```

### 維護指令

```bash
# 更新映像檔
docker compose --env-file .env.prod -f docker-compose.prod.yml pull
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d

# 清理
docker system prune -a
docker volume prune

# 備份
./backup.sh

# 健康檢查
./check_health.sh
```

---

## 附錄

### A. 系統需求檢查清單

- [ ] RHEL 9 已安裝並更新
- [ ] 2x Nvidia H100 GPU 已識別
- [ ] NVIDIA Driver 535+ 已安裝
- [ ] CUDA 12.2+ 已安裝
- [ ] Docker 24.0+ 已安裝
- [ ] Docker Compose 2.20+ 已安裝
- [ ] NVIDIA Container Toolkit 已安裝
- [ ] GPU 在 Docker 中可用
- [ ] 環境變數已配置
- [ ] 防火牆已配置
- [ ] SSL 憑證已設定（如需）

### B. 效能基準

**H100 GPU 效能**:
- DeepSeek-OCR: ~0.5-1 秒/頁 (GPU)
- 記憶體使用: ~10-15 GB VRAM
- 並發處理: 支援多個請求

**系統整體效能**:
- Web UI 回應時間: < 200ms
- API 回應時間: < 500ms
- OCR 處理時間: 0.5-2 秒/頁
- Contract Review: 5-10 秒/契約

### C. 支援資源

- **專案文檔**: PROJECT_OVERVIEW.md, AI_ASSISTANT_GUIDE.md
- **OCR 文檔**: OCR_TESTING_GUIDE.md, AGENT_OCR_USAGE.md
- **平台狀態**: PLATFORM_STATUS.md
- **NVIDIA 文檔**: https://docs.nvidia.com/datacenter/tesla/
- **Docker GPU 文檔**: https://docs.docker.com/config/containers/resource_constraints/#gpu

---

**部署完成後，請訪問**: http://<SERVER_IP>:8501

**預設服務端口**:
- Web UI: 8501
- Agent Service: 8002
- MCP Server: 8001
- LiteLLM: 4000
- Grafana: 3000
- Prometheus: 9090

**祝部署順利！** 🚀
