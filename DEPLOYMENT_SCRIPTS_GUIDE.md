# AI Platform 部署腳本使用指南

**版本:** 2.0.0
**更新日期:** 2025-10-29

---

## 📋 目錄

1. [概述](#概述)
2. [腳本列表](#腳本列表)
3. [快速開始](#快速開始)
4. [詳細使用說明](#詳細使用說明)
5. [部署流程圖](#部署流程圖)
6. [常見使用場景](#常見使用場景)
7. [故障排除](#故障排除)
8. [最佳實踐](#最佳實踐)

---

## 概述

本指南提供一套完整的自動化部署腳本，可以將 AI Platform 從開發環境部署到生產環境（Red Hat Enterprise Linux 9.4 + 2x H100 GPU）。

### 核心功能

✅ **自動化打包** - 收集所有必要文件並打包
✅ **智能上傳** - 支援 SSH 金鑰和斷點續傳
✅ **遠端部署** - 在生產伺服器上執行部署
✅ **完整驗證** - 多層次健康檢查
✅ **負載測試** - 自動化效能測試
✅ **一鍵部署** - 整合所有步驟的快速部署

---

## 腳本列表

| 腳本名稱 | 功能 | 執行環境 | 預計時間 |
|---------|------|---------|---------|
| `1-package-deployment.sh` | 打包部署文件 | 本地開發機 | 2-3 分鐘 |
| `2-upload-to-server.sh` | 上傳到生產伺服器 | 本地開發機 | 5-10 分鐘 |
| `3-remote-deploy.sh` | 遠端執行部署 | 本地開發機 | 20-30 分鐘 |
| `4-verify-deployment.sh` | 驗證部署狀態 | 本地開發機 | 5-8 分鐘 |
| `5-run-load-tests.sh` | 執行負載測試 | 本地開發機 | 10-60 分鐘 |
| `deploy-one-click.sh` | 一鍵完整部署 | 本地開發機 | 40-60 分鐘 |

所有腳本位於: `/path/to/your/ai_platform/scripts/`

---

## 快速開始

### 方法 A: 一鍵部署（推薦）

```bash
# 導航到專案目錄
cd /path/to/your/ai_platform

# 設置腳本執行權限
chmod +x scripts/*.sh

# 執行一鍵部署
./scripts/deploy-one-click.sh <server-ip> [ssh-user] [ssh-key]

# 範例
./scripts/deploy-one-click.sh 192.168.1.100 root ~/.ssh/production.pem
```

**預期時間:** 40-60 分鐘（包含所有步驟）

### 方法 B: 分步驟部署

```bash
# 步驟 1: 打包
./scripts/1-package-deployment.sh

# 步驟 2: 上傳
./scripts/2-upload-to-server.sh 192.168.1.100 root

# 步驟 3: 遠端部署
./scripts/3-remote-deploy.sh 192.168.1.100 root

# 步驟 4: 驗證
./scripts/4-verify-deployment.sh 192.168.1.100 root

# 步驟 5: 負載測試
./scripts/5-run-load-tests.sh 192.168.1.100 root
```

**預期時間:** 每個步驟 2-30 分鐘不等

---

## 詳細使用說明

### 1. 打包部署文件 (`1-package-deployment.sh`)

#### 功能

- 收集所有必要的部署文件
- 複製服務代碼、配置文件、腳本
- 清理不需要的臨時文件
- 創建壓縮包 (`ai_platform_YYYYMMDD_HHMMSS.tar.gz`)
- 生成部署清單 (`DEPLOYMENT_MANIFEST.txt`)

#### 使用方法

```bash
cd /path/to/your/ai_platform
./scripts/1-package-deployment.sh
```

#### 輸出

```
ai_platform_20251029_153045.tar.gz  # 壓縮包
deployment_package/                 # 臨時目錄
quick-deploy.sh                     # 快速部署腳本
```

#### 檢查點

✓ 所有必要文件都存在
✓ 服務代碼已複製
✓ 配置文件已複製
✓ 腳本權限已設置
✓ 臨時文件已清理
✓ 壓縮包已創建

#### 打包內容

- `docker-compose.production.yml` - 生產環境 Docker Compose
- `.env.production.example` - 環境變數範本
- `deploy-rhel-production.sh` - RHEL 部署腳本
- `services/` - 所有微服務代碼
- `config/` - Nginx、Grafana、Prometheus 配置
- `systemd/` - Systemd 服務文件
- `load-tests/` - 負載測試腳本
- `PRODUCTION_DEPLOYMENT.md` - 部署文檔
- `STEP_BY_STEP_DEPLOYMENT.md` - 步驟指南

---

### 2. 上傳到伺服器 (`2-upload-to-server.sh`)

#### 功能

- 測試 SSH 連線
- 檢查磁碟空間（需要 10 GB+）
- 備份現有部署（如果存在）
- 上傳壓縮包（支援 rsync 斷點續傳）
- 驗證檔案完整性（MD5）
- 解壓並設置權限

#### 使用方法

```bash
# 基本用法（使用密碼）
./scripts/2-upload-to-server.sh 192.168.1.100

# 指定用戶
./scripts/2-upload-to-server.sh 192.168.1.100 root

# 使用 SSH 金鑰
./scripts/2-upload-to-server.sh 192.168.1.100 root ~/.ssh/production.pem
```

#### 參數說明

| 參數 | 必填 | 說明 | 預設值 |
|------|------|------|--------|
| `server-ip` | ✓ | 生產伺服器 IP 地址 | - |
| `ssh-user` | ✗ | SSH 登入用戶 | root |
| `ssh-key` | ✗ | SSH 私鑰路徑 | 使用密碼 |

#### 檢查點

✓ SSH 連線成功
✓ 磁碟空間充足
✓ 現有部署已備份
✓ 檔案上傳完成
✓ MD5 驗證通過
✓ 檔案已解壓
✓ 權限已設置

#### 輸出文件（在生產伺服器上）

```
/opt/ai_platform/
├── docker-compose.production.yml
├── .env.production.example
├── deploy-rhel-production.sh
├── services/
├── config/
├── systemd/
├── load-tests/
└── backups/
    └── backup_before_deploy_YYYYMMDD_HHMMSS.tar.gz
```

---

### 3. 遠端部署 (`3-remote-deploy.sh`)

#### 功能

- 檢查部署文件完整性
- 配置 `.env` 環境變數
- 顯示系統資訊（CPU、RAM、GPU）
- 執行遠端部署腳本
- 實時顯示部署進度

#### 使用方法

```bash
# 基本用法
./scripts/3-remote-deploy.sh 192.168.1.100

# 使用 SSH 金鑰
./scripts/3-remote-deploy.sh 192.168.1.100 root ~/.ssh/production.pem
```

#### 互動式流程

1. **檢查 .env 文件**
   - 如果不存在，詢問是否使用範例配置
   - 提供即時編輯選項

2. **顯示系統資訊**
   - 作業系統版本
   - CPU 和記憶體
   - GPU 資訊
   - 磁碟空間

3. **確認部署**
   - 顯示配置摘要
   - 等待用戶確認

4. **執行部署**
   - 檢查系統依賴
   - 安裝 Docker 和 NVIDIA 工具包（如需要）
   - 拉取 Docker 映像
   - 啟動服務（分階段）
   - 驗證服務狀態

#### 部署階段

```
1. 檢查依賴 (OS, GPU, Docker, CUDA)
2. 配置防火牆
3. 拉取 Docker 映像 (10-15 分鐘)
4. 啟動基礎設施服務 (Postgres, Redis, Qdrant, RabbitMQ)
5. 啟動 LLM 服務 (Ollama, LiteLLM)
6. 啟動應用服務 (MCP, Agent, Web UI)
7. 啟動監控服務 (Prometheus, Grafana, Nginx)
8. 驗證服務狀態
```

#### 檢查點

✓ 部署腳本存在
✓ .env 配置完成
✓ 系統資源充足
✓ 所有依賴已安裝
✓ Docker 映像已拉取
✓ 所有服務已啟動
✓ 健康檢查通過

---

### 4. 驗證部署 (`4-verify-deployment.sh`)

#### 功能

- 多層次健康檢查（系統、容器、服務、網路）
- GPU 狀態檢查
- 資料庫連線測試
- API 端點測試
- 資源使用監控
- 生成驗證報告

#### 使用方法

```bash
# 基本用法
./scripts/4-verify-deployment.sh 192.168.1.100

# 使用 SSH 金鑰
./scripts/4-verify-deployment.sh 192.168.1.100 root ~/.ssh/production.pem
```

#### 驗證項目（共 20+ 項）

##### 系統服務檢查
- ✓ Docker 服務運行中
- ✓ AI Platform 服務啟用
- ✓ 備份定時器啟用
- ✓ 健康檢查定時器啟用

##### Docker 容器檢查
- ✓ PostgreSQL 運行中
- ✓ Redis 運行中
- ✓ Qdrant 運行中
- ✓ RabbitMQ 運行中
- ✓ Ollama 運行中
- ✓ LiteLLM 運行中
- ✓ MCP Server 副本運行中
- ✓ Agent Service 副本運行中
- ✓ Web UI 副本運行中

##### GPU 狀態檢查
- ✓ NVIDIA 驅動正常
- ✓ 2x H100 GPU 偵測到
- ✓ GPU 溫度正常 (< 85°C)
- ✓ GPU 記憶體可用
- ✓ 容器可訪問 GPU

##### 服務健康檢查
- ✓ MCP Server API (http://localhost:8001/health)
- ✓ Agent Service API (http://localhost:8000/health)
- ✓ LiteLLM API (http://localhost:4000/health)
- ✓ Web UI (http://localhost:8501)
- ✓ Grafana (http://localhost:3000)

##### 資料庫連線檢查
- ✓ PostgreSQL 接受連線
- ✓ Redis 回應 PING

##### 資源使用檢查
- ✓ CPU 使用率 < 80%
- ✓ 記憶體使用率 < 85%
- ✓ 磁碟空間 > 20%

#### 輸出格式

```
檢查摘要:
  ├─ 總檢查項目: 25
  ├─ 通過: 25
  └─ 失敗: 0

系統狀態: 健康
通過率: 100%
```

#### 退出碼

- `0` - 所有檢查通過
- `1` - 部分檢查失敗（1-2 項）
- `2` - 多個檢查失敗（3+ 項）

---

### 5. 執行負載測試 (`5-run-load-tests.sh`)

#### 功能

- 安裝測試工具（Apache Bench、Locust）
- 執行多種測試場景
- 實時監控測試進度
- 生成測試報告

#### 使用方法

```bash
# 執行所有測試
./scripts/5-run-load-tests.sh 192.168.1.100

# 執行特定測試
./scripts/5-run-load-tests.sh 192.168.1.100 root '' smoke
./scripts/5-run-load-tests.sh 192.168.1.100 root '' load
./scripts/5-run-load-tests.sh 192.168.1.100 root '' stress
```

#### 測試類型

##### 1. 煙霧測試 (Smoke Test)

**目的:** 快速驗證基本功能

**配置:**
- 並發用戶: 5
- 總請求數: 100
- 持續時間: ~2 分鐘

**預期結果:**
- ✓ 所有請求通過
- ✓ 錯誤率 < 1%
- ✓ 回應時間 < 500ms

**使用場景:**
- 部署後快速驗證
- CI/CD 管道
- 每日健康檢查

##### 2. 負載測試 (Load Test)

**目的:** 模擬正常生產流量

**配置:**
- 並發用戶: 50
- 持續時間: 10 分鐘
- 漸增速率: 5 用戶/秒

**預期結果:**
- ✓ p95 回應時間 < 1s
- ✓ 錯誤率 < 2%
- ✓ 系統資源使用 < 70%

**使用場景:**
- 驗證正常容量
- 效能基準測試
- 每週效能檢查

##### 3. 壓力測試 (Stress Test)

**目的:** 測試系統極限

**配置:**
- 並發用戶: 200
- 持續時間: 15 分鐘
- 漸增速率: 20 用戶/秒

**預期結果:**
- ✓ p95 回應時間 < 2s
- ✓ 錯誤率 < 5%
- ✓ 無服務崩潰
- ✓ 系統可恢復

**使用場景:**
- 找出系統瓶頸
- 驗證擴展能力
- 災難恢復測試

#### 測試端點

所有測試都會測試以下 API 端點：

1. **Health Check** - `/health`
2. **Search Knowledge Base** - `/tools/search_knowledge_base`
3. **Semantic Search** - `/tools/semantic_search`
4. **Web Search** - `/tools/web_search`
5. **Get Document** - `/tools/get_document`
6. **Query Database** - `/tools/query_database`

#### 測試報告

測試完成後會生成以下報告：

```
/opt/ai_platform/load-tests/results/
├── smoke_test_YYYYMMDD_HHMMSS/
│   └── SUMMARY.txt
├── load_test_YYYYMMDD_HHMMSS_stats.csv
├── load_test_YYYYMMDD_HHMMSS_failures.csv
└── stress_test_YYYYMMDD_HHMMSS_stats.csv
```

#### 下載測試結果

```bash
# 下載到本地
scp -r root@192.168.1.100:/opt/ai_platform/load-tests/results/ ./test_results/
```

---

### 6. 一鍵部署 (`deploy-one-click.sh`)

#### 功能

整合上述所有步驟，提供單一命令完整部署：

1. 打包部署文件
2. 上傳到伺服器
3. 配置環境變數
4. 執行遠端部署
5. 驗證部署狀態

#### 使用方法

```bash
# 最簡單的方式
./scripts/deploy-one-click.sh 192.168.1.100

# 完整參數
./scripts/deploy-one-click.sh 192.168.1.100 root ~/.ssh/production.pem
```

#### 互動式流程

1. **確認部署配置**
   ```
   伺服器 IP: 192.168.1.100
   SSH 用戶: root
   SSH 金鑰: ~/.ssh/production.pem
   專案目錄: /path/to/your/ai_platform

   確認要開始部署嗎? (y/n)
   ```

2. **執行打包**
   - 顯示打包進度
   - 創建壓縮包

3. **上傳文件**
   - 測試連線
   - 顯示上傳進度
   - 驗證完整性

4. **配置環境**
   ```
   未找到 .env 文件，使用範例配置

   選項:
     1) 現在編輯環境變數
     2) 使用預設值繼續 (僅測試用)
     3) 取消部署

   請選擇 (1-3):
   ```

5. **執行部署**
   - 實時顯示部署日誌
   - 階段性進度更新

6. **驗證部署**
   - 自動運行驗證腳本
   - 顯示健康檢查結果

#### 完成摘要

```
═══════════════════════════════════════════════
  部署完成！
═══════════════════════════════════════════════

部署摘要:
  ├─ 伺服器: 192.168.1.100
  ├─ 用戶: root
  ├─ 耗時: 45 分 23 秒
  └─ 狀態: 完成

訪問服務:
  ├─ Web UI:   http://192.168.1.100:8501
  ├─ API:      http://192.168.1.100:8001/health
  ├─ Grafana:  http://192.168.1.100:3000
  └─ 如使用域名: https://your-domain.com

Grafana 登入資訊:
  ├─ 用戶名: admin
  └─ 密碼: (在 .env 文件中的 GRAFANA_ADMIN_PASSWORD)

下一步建議:
  1. 查看 Grafana 儀表板監控系統狀態
  2. 執行負載測試驗證效能
  3. 設置 Systemd 自動啟動
  4. 配置告警通知
```

---

## 部署流程圖

```
┌─────────────────────────────────────────────────────────────┐
│                      本地開發環境                            │
│                  /path/to/your/ai_platform         │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 1. 執行打包腳本
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 1-package-deployment.sh                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ • 收集部署文件                                        │  │
│  │ • 複製服務代碼、配置                                  │  │
│  │ • 清理臨時文件                                        │  │
│  │ • 創建壓縮包                                          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 輸出: ai_platform_*.tar.gz
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 2-upload-to-server.sh                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ • 測試 SSH 連線                                       │  │
│  │ • 檢查磁碟空間                                        │  │
│  │ • 備份現有部署                                        │  │
│  │ • 上傳壓縮包 (rsync/scp)                             │  │
│  │ • 驗證完整性 (MD5)                                    │  │
│  │ • 解壓並設置權限                                      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ SSH 連線
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   生產伺服器 (RHEL 9.4)                      │
│                    /opt/ai_platform                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 3. 執行遠端部署
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 3-remote-deploy.sh                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ • 檢查 .env 配置                                      │  │
│  │ • 顯示系統資訊                                        │  │
│  │ • 執行 deploy-rhel-production.sh                     │  │
│  │   ├─ 檢查依賴 (Docker, CUDA, GPU)                    │  │
│  │   ├─ 配置防火牆                                       │  │
│  │   ├─ 拉取 Docker 映像                                │  │
│  │   ├─ 啟動基礎設施服務                                │  │
│  │   ├─ 啟動 LLM 服務                                   │  │
│  │   ├─ 啟動應用服務                                     │  │
│  │   └─ 啟動監控服務                                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 4. 驗證部署
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 4-verify-deployment.sh                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ • 檢查系統服務                                        │  │
│  │ • 檢查 Docker 容器                                    │  │
│  │ • 檢查 GPU 狀態                                       │  │
│  │ • 檢查服務健康端點                                    │  │
│  │ • 檢查資料庫連線                                      │  │
│  │ • 檢查資源使用                                        │  │
│  │ • 生成驗證報告                                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 5. 負載測試 (可選)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 5-run-load-tests.sh                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ • 煙霧測試 (5 用戶, 100 請求)                         │  │
│  │ • 負載測試 (50 用戶, 10 分鐘)                         │  │
│  │ • 壓力測試 (200 用戶, 15 分鐘)                        │  │
│  │ • 生成測試報告                                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                         ✅ 部署完成
```

---

## 常見使用場景

### 場景 1: 首次部署到新伺服器

```bash
# 步驟 1: 一鍵部署
./scripts/deploy-one-click.sh 192.168.1.100 root ~/.ssh/production.pem

# 步驟 2: 配置 Systemd 自動啟動
ssh root@192.168.1.100
cd /opt/ai_platform/systemd
sudo ./install-systemd.sh

# 步驟 3: 執行負載測試
./scripts/5-run-load-tests.sh 192.168.1.100 root ~/.ssh/production.pem smoke
```

### 場景 2: 更新現有部署

```bash
# 步驟 1: 打包最新代碼
./scripts/1-package-deployment.sh

# 步驟 2: 上傳並部署
./scripts/2-upload-to-server.sh 192.168.1.100 root
./scripts/3-remote-deploy.sh 192.168.1.100 root

# 步驟 3: 驗證更新
./scripts/4-verify-deployment.sh 192.168.1.100 root
```

### 場景 3: 只更新配置文件

```bash
# 步驟 1: 連線到伺服器
ssh root@192.168.1.100

# 步驟 2: 編輯 .env
cd /opt/ai_platform
vim .env

# 步驟 3: 重啟服務
docker compose down
docker compose up -d

# 步驟 4: 驗證（從本地）
./scripts/4-verify-deployment.sh 192.168.1.100 root
```

### 場景 4: 回滾到之前的版本

```bash
# 步驟 1: 連線到伺服器
ssh root@192.168.1.100
cd /opt/ai_platform

# 步驟 2: 查看備份
ls -lh backups/

# 步驟 3: 停止服務
docker compose down

# 步驟 4: 還原備份
tar -xzf backups/backup_before_deploy_20251029.tar.gz -C /tmp/restore/
cp -r /tmp/restore/* .

# 步驟 5: 重啟服務
docker compose up -d

# 步驟 6: 驗證（從本地）
./scripts/4-verify-deployment.sh 192.168.1.100 root
```

### 場景 5: 部署到多個伺服器

```bash
# 創建伺服器列表
SERVERS=(
    "192.168.1.100"
    "192.168.1.101"
    "192.168.1.102"
)

# 步驟 1: 打包一次
./scripts/1-package-deployment.sh

# 步驟 2: 部署到所有伺服器
for server in "${SERVERS[@]}"; do
    echo "部署到 ${server}..."
    ./scripts/2-upload-to-server.sh "${server}" root
    ./scripts/3-remote-deploy.sh "${server}" root
    ./scripts/4-verify-deployment.sh "${server}" root
done

echo "所有伺服器部署完成！"
```

### 場景 6: CI/CD 自動化部署

```bash
#!/bin/bash
# .github/workflows/deploy.sh

set -e

# 環境變數
SERVER_IP=${PRODUCTION_SERVER_IP}
SSH_USER=${PRODUCTION_SSH_USER}
SSH_KEY_PATH="/tmp/ssh_key"

# 保存 SSH 金鑰
echo "${PRODUCTION_SSH_KEY}" > "${SSH_KEY_PATH}"
chmod 600 "${SSH_KEY_PATH}"

# 執行部署
cd /workspace/ai_platform
./scripts/1-package-deployment.sh
./scripts/2-upload-to-server.sh "${SERVER_IP}" "${SSH_USER}" "${SSH_KEY_PATH}"
./scripts/3-remote-deploy.sh "${SERVER_IP}" "${SSH_USER}" "${SSH_KEY_PATH}"
./scripts/4-verify-deployment.sh "${SERVER_IP}" "${SSH_USER}" "${SSH_KEY_PATH}"

# 執行煙霧測試
./scripts/5-run-load-tests.sh "${SERVER_IP}" "${SSH_USER}" "${SSH_KEY_PATH}" smoke

# 清理
rm -f "${SSH_KEY_PATH}"

echo "✅ CI/CD 部署完成！"
```

---

## 故障排除

### 問題 1: SSH 連線失敗

**症狀:**
```
✗ SSH 連線失敗
```

**原因:**
- 伺服器 IP 錯誤
- SSH 服務未啟動
- 防火牆阻擋
- SSH 金鑰權限錯誤

**解決方案:**
```bash
# 檢查伺服器可達性
ping 192.168.1.100

# 檢查 SSH 服務
ssh -v root@192.168.1.100

# 檢查金鑰權限
chmod 600 ~/.ssh/production.pem
ls -l ~/.ssh/production.pem

# 測試不同端口
ssh -p 22 root@192.168.1.100
```

### 問題 2: 磁碟空間不足

**症狀:**
```
✗ 磁碟空間不足
  需要: 10 GB
  可用: 5 GB
```

**解決方案:**
```bash
# 連線到伺服器
ssh root@192.168.1.100

# 檢查磁碟使用
df -h

# 清理 Docker
docker system prune -a -f

# 清理舊日誌
find /var/log -type f -name "*.log" -mtime +30 -delete

# 清理舊備份
find /opt/ai_platform/backups -type f -mtime +30 -delete
```

### 問題 3: Docker 容器無法啟動

**症狀:**
```
✗ PostgreSQL 運行中
✗ Redis 運行中
```

**解決方案:**
```bash
# 連線到伺服器
ssh root@192.168.1.100
cd /opt/ai_platform

# 查看容器狀態
docker ps -a

# 查看容器日誌
docker logs ai-postgres-prod --tail=100
docker logs ai-redis-prod --tail=100

# 檢查 .env 配置
cat .env | grep -E "POSTGRES|REDIS"

# 重新啟動容器
docker compose down
docker compose up -d

# 查看啟動日誌
docker compose logs -f
```

### 問題 4: GPU 無法訪問

**症狀:**
```
✗ GPU 無法訪問
```

**解決方案:**
```bash
# 連線到伺服器
ssh root@192.168.1.100

# 檢查 NVIDIA 驅動
nvidia-smi

# 檢查 NVIDIA Container Toolkit
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi

# 重新配置 Docker runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# 重啟 Ollama 容器
docker restart ai-ollama-prod

# 驗證 GPU 訪問
docker exec ai-ollama-prod nvidia-smi
```

### 問題 5: API 端點無回應

**症狀:**
```
✗ MCP Server API
  預期: OK
  實際: Connection refused
```

**解決方案:**
```bash
# 連線到伺服器
ssh root@192.168.1.100

# 檢查容器狀態
docker ps | grep mcp

# 檢查端口綁定
ss -tlnp | grep 8001

# 查看服務日誌
docker logs ai-mcp-server-1 --tail=100 -f

# 測試內部連線
curl http://localhost:8001/health

# 檢查防火牆
sudo firewall-cmd --list-all

# 重啟服務
docker restart ai-mcp-server-1
```

### 問題 6: 負載測試失敗

**症狀:**
```
錯誤率: 15%
p95 回應時間: 5s
```

**解決方案:**
```bash
# 連線到伺服器
ssh root@192.168.1.100

# 檢查系統資源
top
free -h
df -h

# 檢查 GPU 使用
nvidia-smi

# 檢查容器資源
docker stats

# 調整資源限制
vim docker-compose.production.yml
# 增加 CPU/Memory limits

# 調整並發設定
vim .env
# 降低 MAX_CONCURRENT_REQUESTS

# 重新部署
docker compose down
docker compose up -d

# 重新測試
# 從本地執行
./scripts/5-run-load-tests.sh 192.168.1.100 root '' smoke
```

---

## 最佳實踐

### 1. 部署前檢查清單

```bash
# ✓ 檢查本地代碼是否已提交
git status
git log -1

# ✓ 檢查環境變數是否已準備
cat .env.production.example

# ✓ 檢查 SSH 連線
ssh root@192.168.1.100 "echo 'Connection OK'"

# ✓ 檢查伺服器磁碟空間
ssh root@192.168.1.100 "df -h /opt"

# ✓ 檢查伺服器 GPU
ssh root@192.168.1.100 "nvidia-smi"
```

### 2. 備份策略

```bash
# 部署前手動備份
ssh root@192.168.1.100 "
    cd /opt/ai_platform
    tar -czf backups/manual_backup_\$(date +%Y%m%d_%H%M%S).tar.gz \
        --exclude='backups' \
        --exclude='logs' \
        --exclude='*.tar.gz' \
        .
"

# 設置自動備份保留期
# 保留最近 7 天的每日備份
# 保留最近 4 週的每週備份
# 保留最近 6 個月的每月備份
```

### 3. 分階段部署

```bash
# 階段 1: 部署到測試環境
./scripts/deploy-one-click.sh 192.168.1.200 root

# 階段 2: 執行完整測試
./scripts/5-run-load-tests.sh 192.168.1.200 root '' all

# 階段 3: 驗證通過後部署到生產環境
./scripts/deploy-one-click.sh 192.168.1.100 root

# 階段 4: 執行生產環境煙霧測試
./scripts/5-run-load-tests.sh 192.168.1.100 root '' smoke
```

### 4. 監控和告警

```bash
# 部署後立即檢查 Grafana
open http://192.168.1.100:3000

# 設置關鍵指標告警:
# - GPU 溫度 > 85°C
# - 錯誤率 > 5%
# - 回應時間 p95 > 2s
# - 磁碟空間 < 20%
# - 記憶體使用 > 85%
```

### 5. 文檔記錄

```bash
# 記錄每次部署
cat >> deployment_history.txt << EOF
Date: $(date)
Version: $(git rev-parse --short HEAD)
Server: 192.168.1.100
Deployed by: $(whoami)
Notes: 更新了 xxx 功能
Status: Success
EOF
```

### 6. 安全最佳實踐

```bash
# 使用 SSH 金鑰而非密碼
ssh-keygen -t rsa -b 4096 -f ~/.ssh/production

# 限制 SSH 金鑰權限
chmod 600 ~/.ssh/production

# 定期輪換密碼
# 每 90 天更新以下密碼:
# - POSTGRES_PASSWORD
# - REDIS_PASSWORD
# - RABBITMQ_DEFAULT_PASS
# - GRAFANA_ADMIN_PASSWORD

# 使用環境變數而非硬編碼
# 不要在代碼中包含 API 金鑰
```

---

## 附錄

### A. 腳本執行權限設置

```bash
# 一次性設置所有腳本權限
cd /path/to/your/ai_platform
chmod +x scripts/*.sh
chmod +x systemd/*.sh
chmod +x load-tests/*.sh
chmod +x deploy-rhel-production.sh
```

### B. 環境變數範本

```bash
# 最小必填項目
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
GOOGLE_API_KEY=AIzaxxx
POSTGRES_PASSWORD=xxx
REDIS_PASSWORD=xxx
RABBITMQ_DEFAULT_PASS=xxx
```

### C. 快速命令參考

```bash
# 查看部署包
ls -lh ai_platform_*.tar.gz

# 連線到伺服器
ssh root@192.168.1.100

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

# 查看系統資源
htop
```

---

## 支援與聯絡

如有問題，請參考：

- **詳細部署文檔:** `PRODUCTION_DEPLOYMENT.md`
- **Step by Step 指南:** `STEP_BY_STEP_DEPLOYMENT.md`
- **負載測試指南:** `load-tests/README.md`

---

**版本:** 2.0.0
**最後更新:** 2025-10-29
**文檔維護:** AI Platform DevOps Team
