#!/bin/bash
# AI平台維護工具集

# 1. 健康檢查腳本
cat > scripts/health-check.sh << 'HEALTH_EOF'
#!/bin/bash
# 詳細健康檢查

echo "=== AI平台健康檢查報告 ==="
echo "時間: $(date)"
echo ""

# 檢查容器狀態
echo "📦 容器狀態:"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
echo ""

# 檢查資源使用
echo "💻 資源使用:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
echo ""

# 檢查磁碟使用
echo "💾 磁碟使用:"
df -h | grep -E "Filesystem|/dev/"
echo ""
echo "Docker資料:"
docker system df
echo ""

# 檢查服務響應時間
echo "⏱️  服務響應時間:"

test_endpoint() {
    local name=$1
    local url=$2
    local start=$(date +%s%N)
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    local end=$(date +%s%N)
    local duration=$(((end - start) / 1000000))
    
    if [ "$response" = "200" ] || [ "$response" = "000" ]; then
        echo "  ✓ $name: ${duration}ms"
    else
        echo "  ✗ $name: 無響應 (HTTP $response)"
    fi
}

test_endpoint "LiteLLM" "http://localhost:4000/health"
test_endpoint "MCP Server" "http://localhost:8001/health"
test_endpoint "Agent Service" "http://localhost:8002/health"
test_endpoint "Web UI" "http://localhost:8501"
test_endpoint "Grafana" "http://localhost:3000/api/health"
test_endpoint "Prometheus" "http://localhost:9090/-/healthy"
test_endpoint "Qdrant" "http://localhost:6333/health"

echo ""

# 檢查日誌錯誤
echo "❌ 最近的錯誤 (最近10條):"
docker compose logs --tail=100 2>&1 | grep -i "error" | tail -10

echo ""
echo "=== 檢查完成 ==="
HEALTH_EOF

chmod +x scripts/health-check.sh

# 2. 日誌分析腳本
cat > scripts/analyze-logs.sh << 'LOG_EOF'
#!/bin/bash
# 日誌分析工具

SERVICE=${1:-all}
LINES=${2:-100}

echo "=== 日誌分析: $SERVICE (最近 $LINES 行) ==="
echo ""

if [ "$SERVICE" = "all" ]; then
    # 分析所有服務
    for service in litellm mcp-server agent-service web-ui; do
        echo "--- $service ---"
        docker compose logs --tail=$LINES $service 2>&1 | \
            awk '{print $0}' | \
            grep -iE "(error|warn|fail)" | \
            tail -5
        echo ""
    done
else
    # 分析特定服務
    docker compose logs --tail=$LINES $SERVICE
fi

# 統計錯誤類型
echo "=== 錯誤統計 ==="
docker compose logs --tail=1000 2>&1 | \
    grep -i "error" | \
    awk '{print $NF}' | \
    sort | uniq -c | sort -rn | head -10

echo ""
echo "=== API錯誤統計 ==="
docker compose logs litellm --tail=1000 2>&1 | \
    grep -oP 'status_code":\d+' | \
    sort | uniq -c | sort -rn
LOG_EOF

chmod +x scripts/analyze-logs.sh

# 3. 備份腳本
cat > scripts/backup.sh << 'BACKUP_EOF'
#!/bin/bash
# 資料備份工具

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "🔄 開始備份到: $BACKUP_DIR"

# 備份PostgreSQL
echo "備份PostgreSQL..."
docker compose exec -T postgres pg_dump -U admin ai_platform > "$BACKUP_DIR/postgres.sql"

# 備份Qdrant
echo "備份Qdrant..."
docker compose exec -T qdrant tar czf - /qdrant/storage > "$BACKUP_DIR/qdrant.tar.gz"

# 備份配置文件
echo "備份配置..."
cp .env "$BACKUP_DIR/.env.backup"
cp docker-compose.yml "$BACKUP_DIR/docker-compose.yml.backup"
cp -r config "$BACKUP_DIR/config_backup"

# 備份模型快取
if [ -d "./models" ]; then
    echo "備份模型快取..."
    tar czf "$BACKUP_DIR/models.tar.gz" ./models
fi

# 創建備份清單
cat > "$BACKUP_DIR/MANIFEST.txt" << EOF
備份時間: $(date)
備份內容:
- PostgreSQL資料庫
- Qdrant向量資料庫
- 配置文件
- 模型快取

還原命令:
docker compose exec -T postgres psql -U admin ai_platform < postgres.sql
EOF

echo "✅ 備份完成: $BACKUP_DIR"
echo "備份大小: $(du -sh $BACKUP_DIR | cut -f1)"
BACKUP_EOF

chmod +x scripts/backup.sh

# 4. 還原腳本
cat > scripts/restore.sh << 'RESTORE_EOF'
#!/bin/bash
# 資料還原工具

if [ -z "$1" ]; then
    echo "使用方法: ./restore.sh <backup_directory>"
    echo "可用備份:"
    ls -la backups/
    exit 1
fi

BACKUP_DIR=$1

if [ ! -d "$BACKUP_DIR" ]; then
    echo "錯誤: 備份目錄不存在: $BACKUP_DIR"
    exit 1
fi

echo "⚠️  警告: 這將覆蓋現有資料！"
read -p "確定要繼續嗎？(yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "取消還原"
    exit 0
fi

echo "🔄 從備份還原: $BACKUP_DIR"

# 停止服務
echo "停止服務..."
docker compose down

# 還原PostgreSQL
if [ -f "$BACKUP_DIR/postgres.sql" ]; then
    echo "還原PostgreSQL..."
    docker compose up -d postgres
    sleep 10
    docker compose exec -T postgres psql -U admin ai_platform < "$BACKUP_DIR/postgres.sql"
fi

# 還原Qdrant
if [ -f "$BACKUP_DIR/qdrant.tar.gz" ]; then
    echo "還原Qdrant..."
    docker compose up -d qdrant
    sleep 5
    docker compose exec -T qdrant tar xzf - -C / < "$BACKUP_DIR/qdrant.tar.gz"
fi

# 還原配置
if [ -d "$BACKUP_DIR/config_backup" ]; then
    echo "還原配置..."
    cp -r "$BACKUP_DIR/config_backup/"* ./config/
fi

# 重啟所有服務
echo "重啟服務..."
docker compose up -d

echo "✅ 還原完成"
RESTORE_EOF

chmod +x scripts/restore.sh

# 5. 效能測試腳本
cat > scripts/performance-test.sh << 'PERF_EOF'
#!/bin/bash
# 效能測試工具

echo "=== AI平台效能測試 ==="
echo ""

# 測試LLM延遲
echo "📊 測試LLM服務延遲..."
for i in {1..5}; do
    start=$(date +%s%N)
    curl -s -X POST http://localhost:8002/agent/chat \
        -H "Content-Type: application/json" \
        -d '{"message": "Hello", "model": "gpt-3.5-turbo"}' > /dev/null
    end=$(date +%s%N)
    duration=$(((end - start) / 1000000))
    echo "  請求 $i: ${duration}ms"
done

echo ""

# 測試並發處理
echo "📊 測試並發處理 (10個並發請求)..."
start=$(date +%s)
for i in {1..10}; do
    curl -s -X POST http://localhost:8002/agent/chat \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"Test $i\", \"model\": \"gpt-3.5-turbo\"}" > /dev/null &
done
wait
end=$(date +%s)
duration=$((end - start))
echo "  完成時間: ${duration}秒"
echo "  平均吞吐量: $((10 / duration)) 請求/秒"

echo ""

# 測試向量搜尋
echo "📊 測試向量搜尋..."
for i in {1..5}; do
    start=$(date +%s%N)
    curl -s "http://localhost:6333/collections" > /dev/null
    end=$(date +%s%N)
    duration=$(((end - start) / 1000000))
    echo "  查詢 $i: ${duration}ms"
done

echo ""
echo "=== 測試完成 ==="
PERF_EOF

chmod +x scripts/performance-test.sh

# 6. 監控腳本
cat > scripts/monitor.sh << 'MONITOR_EOF'
#!/bin/bash
# 實時監控

echo "開始實時監控 (按 Ctrl+C 停止)..."
echo ""

while true; do
    clear
    echo "=== AI平台實時監控 ==="
    echo "時間: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # 容器狀態
    echo "📦 容器狀態:"
    docker compose ps --format "table {{.Name}}\t{{.Status}}" | head -10
    echo ""
    
    # CPU和記憶體
    echo "💻 資源使用:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemPerc}}" | head -10
    echo ""
    
    # 網路流量
    echo "🌐 網路流量:"
    docker stats --no-stream --format "table {{.Name}}\t{{.NetIO}}" | head -10
    echo ""
    
    # 最新日誌
    echo "📝 最新事件 (最後3條):"
    docker compose logs --tail=3 --since=10s 2>&1 | grep -v "^$"
    
    sleep 5
done
MONITOR_EOF

chmod +x scripts/monitor.sh

# 7. 清理腳本
cat > scripts/cleanup.sh << 'CLEANUP_EOF'
#!/bin/bash
# 清理未使用資源

echo "=== 清理未使用資源 ==="
echo ""

# 清理停止的容器
echo "🗑️  清理停止的容器..."
docker container prune -f

# 清理未使用的映像
echo "🗑️  清理未使用的映像..."
docker image prune -f

# 清理未使用的網路
echo "🗑️  清理未使用的網路..."
docker network prune -f

# 清理Build快取
echo "🗑️  清理Build快取..."
docker builder prune -f

# 清理舊日誌
echo "🗑️  清理舊日誌 (保留最近7天)..."
find ./logs -type f -mtime +7 -delete 2>/dev/null || true

# 清理舊備份
echo "🗑️  清理舊備份 (保留最近30天)..."
find ./backups -type d -mtime +30 -exec rm -rf {} + 2>/dev/null || true

# 顯示清理結果
echo ""
echo "📊 清理後狀態:"
docker system df

echo ""
echo "✅ 清理完成"
CLEANUP_EOF

chmod +x scripts/cleanup.sh

# 8. 更新腳本
cat > scripts/update.sh << 'UPDATE_EOF'
#!/bin/bash
# 系統更新工具

echo "=== AI平台更新工具 ==="
echo ""

# 備份
echo "1️⃣ 創建備份..."
./scripts/backup.sh

# 拉取最新映像
echo "2️⃣ 拉取最新映像..."
docker compose pull

# 重建自定義映像
echo "3️⃣ 重建服務..."
docker compose build --no-cache

# 停止服務
echo "4️⃣ 停止服務..."
docker compose down

# 啟動服務
echo "5️⃣ 啟動服務..."
docker compose up -d

# 等待服務就緒
echo "6️⃣ 等待服務就緒..."
sleep 30

# 健康檢查
echo "7️⃣ 執行健康檢查..."
./scripts/health-check.sh

echo ""
echo "✅ 更新完成"
UPDATE_EOF

chmod +x scripts/update.sh

# 9. 故障排查腳本
cat > scripts/troubleshoot.sh << 'TROUBLE_EOF'
#!/bin/bash
# 故障排查工具

echo "=== AI平台故障排查 ==="
echo ""

SERVICE=${1:-all}

troubleshoot_service() {
    local service=$1
    echo "🔍 檢查服務: $service"
    echo ""
    
    # 檢查容器狀態
    echo "容器狀態:"
    docker compose ps $service
    echo ""
    
    # 檢查最近錯誤
    echo "最近錯誤:"
    docker compose logs --tail=50 $service 2>&1 | grep -i "error" | tail -10
    echo ""
    
    # 檢查資源使用
    echo "資源使用:"
    docker stats --no-stream $service 2>/dev/null
    echo ""
    
    # 檢查健康狀態
    echo "健康檢查:"
    docker inspect --format='{{.State.Health.Status}}' ai-$service 2>/dev/null || echo "未配置健康檢查"
    echo ""
    
    # 網路連接
    echo "網路連接:"
    docker compose exec $service ping -c 2 google.com 2>/dev/null || echo "網路不可達"
    echo ""
    
    echo "---"
    echo ""
}

if [ "$SERVICE" = "all" ]; then
    for svc in litellm ollama mcp-server agent-service web-ui postgres redis qdrant; do
        troubleshoot_service $svc
    done
else
    troubleshoot_service $SERVICE
fi

# 常見問題檢查
echo "=== 常見問題檢查 ==="
echo ""

# 檢查端口衝突
echo "🔌 端口衝突檢查:"
netstat -tuln 2>/dev/null | grep -E ":(8501|8002|8001|4000|3000|9090|6333|5432|6379|5672|15672)" | \
    awk '{print $4}' | sed 's/.*://' | sort | uniq -c

echo ""

# 檢查磁碟空間
echo "💾 磁碟空間檢查:"
df -h . | awk 'NR==2 {if ($5+0 > 80) print "⚠️  警告: 磁碟使用率過高:", $5; else print "✓ 磁碟空間充足:", $5}'

echo ""

# 檢查記憶體
echo "🧠 記憶體檢查:"
free -h | awk 'NR==2 {if ($3/$2 > 0.9) print "⚠️  警告: 記憶體使用率過高:", int($3/$2*100)"%"; else print "✓ 記憶體充足:", int($3/$2*100)"%"}'

echo ""
echo "=== 排查完成 ==="
echo ""
echo "💡 建議操作:"
echo "  - 查看詳細日誌: docker compose logs -f [service]"
echo "  - 重啟服務: docker compose restart [service]"
echo "  - 重建服務: docker compose up -d --force-recreate [service]"
TROUBLE_EOF

chmod +x scripts/troubleshoot.sh

# 10. 使用說明
cat > scripts/README.md << 'README_EOF'
# AI平台維護工具集

## 工具列表

### 1. 健康檢查 (health-check.sh)
檢查所有服務的健康狀態、資源使用和響應時間。

```bash
./scripts/health-check.sh
```

### 2. 日誌分析 (analyze-logs.sh)
分析服務日誌，查找錯誤和警告。

```bash
# 分析所有服務
./scripts/analyze-logs.sh

# 分析特定服務（最近100行）
./scripts/analyze-logs.sh litellm 100
```

### 3. 備份 (backup.sh)
備份資料庫、配置和模型。

```bash
./scripts/backup.sh
```

### 4. 還原 (restore.sh)
從備份還原資料。

```bash
./scripts/restore.sh backups/20240315_120000
```

### 5. 效能測試 (performance-test.sh)
測試系統效能和響應時間。

```bash
./scripts/performance-test.sh
```

### 6. 實時監控 (monitor.sh)
實時監控系統狀態。

```bash
./scripts/monitor.sh
```

### 7. 清理 (cleanup.sh)
清理未使用的Docker資源和舊文件。

```bash
./scripts/cleanup.sh
```

### 8. 更新 (update.sh)
更新系統到最新版本。

```bash
./scripts/update.sh
```

### 9. 故障排查 (troubleshoot.sh)
診斷服務問題。

```bash
# 檢查所有服務
./scripts/troubleshoot.sh

# 檢查特定服務
./scripts/troubleshoot.sh litellm
```

## 日常維護建議

### 每日
- 運行健康檢查
- 檢查日誌錯誤
- 監控資源使用

### 每週
- 執行備份
- 清理未使用資源
- 檢查效能指標

### 每月
- 更新系統
- 審查安全日誌
- 驗證備份完整性

## 故障排查流程

1. 運行健康檢查: `./scripts/health-check.sh`
2. 如果發現問題，運行故障排查: `./scripts/troubleshoot.sh`
3. 查看詳細日誌: `./scripts/analyze-logs.sh [service]`
4. 嘗試重啟服務: `docker compose restart [service]`
5. 如果問題持續，檢查備份並考慮還原

## 緊急情況處理

### 服務崩潰
```bash
# 1. 檢查日誌
docker compose logs [service] --tail=100

# 2. 重啟服務
docker compose restart [service]

# 3. 如果失敗，重建服務
docker compose up -d --force-recreate [service]
```

### 資料損壞
```bash
# 1. 停止服務
docker compose down

# 2. 從備份還原
./scripts/restore.sh backups/[最近的備份]

# 3. 重啟服務
docker compose up -d
```

### 磁碟空間不足
```bash
# 1. 清理資源
./scripts/cleanup.sh

# 2. 刪除舊備份
rm -rf backups/[舊備份目錄]

# 3. 清理Docker系統
docker system prune -a --volumes
```

## 效能優化建議

### CPU優化
- 調整並發工作程序數量
- 啟用請求快取
- 使用負載均衡

### 記憶體優化
- 限制容器記憶體使用
- 增加Redis快取大小
- 優化資料庫查詢

### 磁碟優化
- 使用SSD儲存
- 定期清理日誌
- 壓縮備份文件

### 網路優化
- 使用CDN加速
- 啟用HTTP/2
- 優化Docker網路

## 監控指標

### 關鍵指標
- 響應時間 < 2秒
- CPU使用率 < 70%
- 記憶體使用率 < 80%
- 磁碟使用率 < 80%
- 錯誤率 < 1%

### 告警閾值
- 響應時間 > 5秒: 警告
- 響應時間 > 10秒: 嚴重
- 錯誤率 > 5%: 警告
- 服務離線: 緊急

## 聯絡支援

如果問題無法解決：
1. 收集日誌: `docker compose logs > debug.log`
2. 導出配置: `docker compose config > config.yml`
3. 記錄錯誤訊息
4. 聯絡技術支援
README_EOF

echo "✅ 維護工具集創建完成！"
echo ""
echo "📁 工具位置: ./scripts/"
echo "📖 使用說明: ./scripts/README.md"
echo ""
echo "快速開始:"
echo "  健康檢查: ./scripts/health-check.sh"
echo "  實時監控: ./scripts/monitor.sh"
echo "  故障排查: ./scripts/troubleshoot.sh"