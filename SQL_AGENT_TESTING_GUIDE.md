# SQL Database Query Tools - Agent Testing Guide

## 更新摘要 (2025-11-10)

已成功為 AI Agents 啟用 SQL 資料庫查詢功能，解決了 GPT-OSS 120B 等模型無法調用 SQL 工具的問題。

---

## 問題診斷

### 原始問題
用戶使用 GPT-OSS 120B 模型在聊天中查詢 "最近的5筆訂單狀態如何？哪些還在生產中？"，但 AI 不知道要調用 SQL 工具。

### 根本原因
1. **系統提示詞缺失**: `general` 和 `analysis` agent 的系統提示詞中沒有提到 SQL 工具
2. **工具映射不完整**: `agent-service/main.py` 中只有 `execute_sql`，缺少新的 4 個 SQL 工具
3. **模式偵測不足**: `detect_tool_intent()` 函數沒有 SQL 查詢的模式偵測（用於不支持 function calling 的模型）

---

## 解決方案

### 1. 更新系統提示詞 (`config/agent_prompts.yaml`)

#### General Agent 新增內容：
```yaml
💾 **資料庫查詢工具**：

當用戶需要查詢資料庫信息時，使用SQL工具：
- sql_list_tables: 列出所有資料表
- sql_get_schema: 查看特定資料表的結構
- sql_query: 執行SQL查詢（僅支援SELECT）
- sql_explain_query: 分析查詢效能

使用流程範例：
1. 用戶問"有哪些客戶？" → 先用 sql_list_tables → sql_get_schema → sql_query
2. 用戶問"訂單狀態如何？" → 用 sql_query 查詢 sales_orders 表
3. 用戶問"庫存情況？" → 用 sql_query 查詢 products 表
```

#### Analysis Agent 新增內容：
```yaml
💾 **SQL資料庫分析工具**：

SQL分析模式：
1. 探索階段：使用 sql_list_tables 和 sql_get_schema
2. 描述性統計：使用 COUNT, SUM, AVG, MIN, MAX
3. 分組分析：使用 GROUP BY
4. 趨勢分析：使用日期函數分析時間序列
5. 關聯分析：使用 JOIN 合併多表數據
6. 複雜邏輯：使用 CTE (WITH子句)

SQL查詢範例：
- 客戶分析: SELECT customer_name, COUNT(*) as order_count, SUM(final_amount) ...
- 產品庫存分析: SELECT category, SUM(stock_quantity) ...
- 生產效率分析: SELECT assigned_to, AVG(actual_quantity::numeric / planned_quantity * 100) ...
```

### 2. 添加工具端點映射 (`services/agent-service/main.py`)

```python
endpoint_map = {
    # ... 其他工具 ...
    "sql_query": "/tools/sql_query",
    "sql_get_schema": "/tools/sql_get_schema",
    "sql_list_tables": "/tools/sql_list_tables",
    "sql_explain_query": "/tools/sql_explain_query",
}
```

### 3. 添加 SQL 模式偵測 (`detect_tool_intent()` 函數)

```python
# SQL query patterns - detect database queries
sql_keywords = [
    "查詢資料庫", "訂單", "客戶", "產品", "庫存",
    "銷售", "生產", "出貨", "工單",
    "有哪些", "多少筆", "統計", "總額",
    "最近.*訂單", "進行中", "待處理",
    "customers", "products", "orders", "inventory", "sales"
]

if has_sql_keyword:
    # Route to appropriate SQL tool
    return ("sql_query", {...})
```

---

## 測試方法

### 步驟 1: 訪問 Web UI
1. 打開瀏覽器: `http://localhost:8501`
2. 登入系統
3. 進入 **聊天 (Chat)** 標籤

### 步驟 2: 選擇模型
在設定中選擇：
- **GPT-OSS 120B** (本地模型，通過模式偵測)
- 或 **Claude** 系列 (支援 function calling)

### 步驟 3: 測試查詢

#### 測試 1: 基本客戶查詢
```
問: 請問目前有哪些客戶？列出信用額度最高的5家公司
```

**預期行為**:
- Agent 偵測到「客戶」關鍵字
- 調用 `sql_query` 工具
- 執行: `SELECT customer_name, city, credit_limit FROM customers ORDER BY credit_limit DESC LIMIT 5`
- 顯示結果:
  1. 鴻海精密 (80M)
  2. 日月光半導體 (60M)
  3. 廣達電腦 (55M)
  4. 友達光電 (52M)
  5. 台積電 (50M)

#### 測試 2: 訂單狀態查詢
```
問: 最近的5筆訂單狀態如何？哪些還在生產中？
```

**預期行為**:
- Agent 偵測到「訂單」「生產中」關鍵字
- 調用 `sql_query` 工具
- 執行 JOIN 查詢合併 `sales_orders` 和 `customers` 表
- 顯示訂單編號、客戶名稱、狀態、金額
- 特別標註 status = 'manufacturing' 的訂單

#### 測試 3: 庫存分析
```
問: 半導體類產品有哪些？各有多少庫存？
```

**預期行為**:
- Agent 偵測到「產品」「庫存」關鍵字
- 調用 `sql_query` 工具
- 執行: `SELECT product_name, unit_price, stock_quantity FROM products WHERE category = '半導體'`
- 顯示 3 種半導體產品及庫存

#### 測試 4: 生產狀態查詢
```
問: 目前有哪些生產工單正在進行中？進度如何？
```

**預期行為**:
- Agent 偵測到「生產」「工單」「進行中」關鍵字
- 調用 `sql_query` 工具
- JOIN `production_orders` 和 `products` 表
- 計算進度百分比: `(actual_quantity / planned_quantity * 100)`
- 按優先級分組顯示

#### 測試 5: 複雜分析查詢
```
問: 分析各個客戶的訂單總金額，誰是最大客戶？
```

**預期行為**:
- Agent 識別這是分析型查詢
- 使用 `GROUP BY` 和聚合函數
- 執行: `SELECT customer_name, COUNT(*) as order_count, SUM(final_amount) as total FROM ...`
- 提供業務洞察和建議

---

## 驗證清單

測試每個場景後，確認：

- [ ] Agent 正確識別需要查詢資料庫
- [ ] Agent 使用了適當的 SQL 工具 (`sql_query`, `sql_get_schema`, `sql_list_tables`)
- [ ] SQL 查詢語法正確
- [ ] 查詢返回了預期結果
- [ ] Agent 以自然語言呈現結果（不只是原始數據）
- [ ] Agent 提供了見解或建議（分析型查詢）
- [ ] 查詢在 30 秒內完成
- [ ] 沒有嘗試危險的 SQL 操作（INSERT/UPDATE/DELETE）

---

## 支援的查詢類型

### 1. 簡單 SELECT
```sql
SELECT * FROM customers LIMIT 10
```

### 2. WHERE 過濾
```sql
SELECT * FROM products WHERE category = '半導體'
```

### 3. JOIN 操作
```sql
SELECT so.order_number, c.customer_name, so.final_amount
FROM sales_orders so
JOIN customers c ON so.customer_id = c.id
```

### 4. 聚合函數
```sql
SELECT category, COUNT(*), AVG(unit_price)
FROM products
GROUP BY category
```

### 5. 子查詢
```sql
SELECT customer_name
FROM customers
WHERE id IN (
    SELECT customer_id
    FROM sales_orders
    WHERE final_amount > 40000000
)
```

### 6. CTE (Common Table Expressions)
```sql
WITH order_stats AS (
    SELECT customer_id, COUNT(*) as order_count
    FROM sales_orders
    GROUP BY customer_id
)
SELECT c.customer_name, os.order_count
FROM customers c
JOIN order_stats os ON c.id = os.customer_id
```

---

## 安全功能

### 查詢驗證
- ✅ 只允許 `SELECT` 查詢
- ✅ 允許 `WITH...SELECT` (CTE)
- ❌ 阻止 `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`
- ❌ 阻止多條語句（偵測分號）
- ❌ 阻止危險關鍵字：`EXEC`, `EXECUTE`, `GRANT`, `REVOKE`

### 自動保護
- 自動添加 `LIMIT 100`（如果查詢中沒有 LIMIT）
- 語句超時保護（預設 30 秒）
- 連接池管理

### 測試安全性
嘗試這些查詢應該被拒絕：

```
❌ "刪除所有訂單" → 應該被拒絕（DELETE 關鍵字）
❌ "把訂單狀態改成已完成" → 應該被拒絕（UPDATE 關鍵字）
❌ "DROP TABLE customers;" → 應該被拒絕（DROP 關鍵字）
```

---

## 故障排除

### 問題: Agent 不使用 SQL 工具
**原因**: 問題描述不夠明確
**解決**: 重新措辭問題，明確提到「查詢」「資料庫」或具體表名

### 問題: 查詢超時
**原因**: 查詢太複雜或缺少索引
**解決**:
- 使用 `sql_explain_query` 工具分析查詢計劃
- 添加 `LIMIT` 子句
- 確保 WHERE 條件使用索引欄位

### 問題: 查詢結果不正確
**原因**: JOIN 條件錯誤或 WHERE 過濾不當
**解決**:
- 使用 `sql_get_schema` 檢查表結構
- 分步測試查詢組件
- 檢查 NULL 值處理

### 問題: Agent 不理解資料庫結構
**原因**: 沒有先探索 schema
**解決**: 明確要求 "先檢查資料庫結構"

---

## 效能提示

1. **使用索引**: 所有外鍵和常用搜尋欄位都已建立索引
2. **限制結果數**: 總是使用 `LIMIT`
3. **避免 SELECT ***: 只選擇需要的欄位
4. **使用 EXPLAIN**: 用 `sql_explain_query` 測試效能
5. **聰明聚合**: 在索引欄位上進行 `GROUP BY`

---

## 資料庫參考

### 製造業示範資料庫

**7 個資料表**:
1. `customers` - 15 家客戶（台灣電子製造業）
2. `products` - 30 種產品（9 個類別）
3. `sales_orders` - 18 筆訂單（各種狀態）
4. `order_items` - 53 筆訂單明細
5. `production_orders` - 18 個生產工單
6. `inventory_transactions` - 30 筆庫存異動記錄
7. `shipments` - 8 筆出貨記錄

**總數據量**: ~650M NTD 訂單總額

詳細資料庫文檔請參考：
- Schema: `database/manufacturing_demo_schema.sql`
- Sample Data: `database/manufacturing_demo_data.sql`
- Testing Guide: `MANUFACTURING_DEMO_TESTING.md`

---

## 下一步

測試成功後，可以考慮：

1. **擴展功能**
   - 添加查詢歷史記錄
   - 實作查詢範本（常用查詢）
   - 創建儀表板小工具

2. **提升體驗**
   - 添加查詢結果視覺化（圖表）
   - 實作查詢結果匯出（CSV, Excel）
   - 添加自然語言轉 SQL 改進

3. **生產就緒**
   - 添加查詢結果快取
   - 實作速率限制
   - 建立審計日誌
   - 設定監控和告警

---

**文檔版本**: 1.0
**最後更新**: 2025-11-10
**作者**: FENC AI Platform Team
