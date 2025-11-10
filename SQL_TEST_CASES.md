# SQL 工具測試案例集

## 📋 目錄
1. [基礎查詢測試](#基礎查詢測試)
2. [進階分析測試](#進階分析測試)
3. [業務場景測試](#業務場景測試)
4. [效能測試](#效能測試)
5. [錯誤處理測試](#錯誤處理測試)

---

## 🎯 測試前準備

### 1. 選擇適合的模型
- **推薦**: Claude 3 Opus 或 Claude 3 Haiku
- **原因**: 支援 Function Calling，可以自動執行多步驟 SQL 查詢

### 2. 訪問 Web UI
- URL: `http://localhost:8501`
- 進入「聊天 (Chat)」標籤
- 在模型選單中選擇 Claude 3 Opus 或 Claude 3 Haiku

---

## 1️⃣ 基礎查詢測試

### 測試案例 1.1: 查看資料庫結構
**目的**: 測試 `sql_list_tables` 工具

**提問**:
```
請問資料庫有哪些資料表？
```

**預期結果**:
- Agent 調用 `sql_list_tables`
- 返回 7 個資料表：
  - customers (客戶資料表)
  - products (產品資料表)
  - sales_orders (銷售訂單主檔)
  - order_items (訂單明細表)
  - production_orders (生產工單表)
  - inventory_transactions (庫存異動記錄表)
  - shipments (出貨記錄表)

---

### 測試案例 1.2: 查看表結構
**目的**: 測試 `sql_get_schema` 工具

**提問**:
```
請告訴我 customers 表的欄位結構
```

**預期結果**:
- Agent 調用 `sql_get_schema`
- 顯示欄位名稱、類型、說明
- 包含主鍵、外鍵資訊

---

### 測試案例 1.3: 簡單查詢
**目的**: 測試 `sql_query` 工具 - 單表查詢

**提問**:
```
請列出信用額度最高的 5 家客戶
```

**預期 SQL**:
```sql
SELECT customer_name, city, credit_limit
FROM customers
ORDER BY credit_limit DESC
LIMIT 5
```

**預期結果**:
| customer_name | city | credit_limit |
|--------------|------|--------------|
| 鴻海精密 | 新北市 | 80,000,000 |
| 日月光半導體 | 高雄市 | 60,000,000 |
| 廣達電腦 | 桃園市 | 55,000,000 |
| 友達光電 | 新竹市 | 52,000,000 |
| 台積電 | 新竹市 | 50,000,000 |

---

### 測試案例 1.4: WHERE 條件查詢
**目的**: 測試條件過濾

**提問**:
```
半導體類產品有哪些？各有多少庫存？
```

**預期 SQL**:
```sql
SELECT product_name, unit_price, stock_quantity
FROM products
WHERE category = '半導體'
ORDER BY unit_price DESC
```

**預期結果**:
- 顯示 3 種半導體產品
- 包含產品名稱、單價、庫存數量

---

## 2️⃣ 進階分析測試

### 測試案例 2.1: JOIN 查詢
**目的**: 測試多表關聯查詢

**提問**:
```
最近的 5 筆訂單狀態如何？分別是哪些客戶的？
```

**預期 SQL**:
```sql
SELECT
    so.order_number,
    c.customer_name,
    so.order_date,
    so.status,
    so.payment_status,
    so.final_amount
FROM sales_orders so
JOIN customers c ON so.customer_id = c.id
ORDER BY so.order_date DESC
LIMIT 5
```

**預期結果**:
- 顯示訂單編號、客戶名稱、日期、狀態、金額
- 按日期降序排列
- 限制 5 筆

---

### 測試案例 2.2: GROUP BY 聚合分析
**目的**: 測試分組統計

**提問**:
```
分析各個客戶的訂單總金額，誰是最大客戶？
```

**預期 SQL**:
```sql
SELECT
    c.customer_name,
    COUNT(so.id) as order_count,
    SUM(so.final_amount) as total_amount,
    AVG(so.final_amount) as avg_amount
FROM customers c
LEFT JOIN sales_orders so ON c.id = so.customer_id
GROUP BY c.id, c.customer_name
ORDER BY total_amount DESC
LIMIT 10
```

**預期結果**:
- 顯示客戶名稱、訂單數量、總金額、平均金額
- 按總金額降序排列
- Agent 應指出最大客戶並提供分析

---

### 測試案例 2.3: 子查詢
**目的**: 測試複雜查詢邏輯

**提問**:
```
哪些客戶的訂單總額超過 4000 萬？
```

**預期 SQL**:
```sql
SELECT
    c.customer_name,
    c.city,
    SUM(so.final_amount) as total_amount
FROM customers c
JOIN sales_orders so ON c.id = so.customer_id
GROUP BY c.id, c.customer_name, c.city
HAVING SUM(so.final_amount) > 40000000
ORDER BY total_amount DESC
```

**預期結果**:
- 顯示符合條件的客戶
- 包含總金額統計

---

### 測試案例 2.4: 複雜 JOIN (多表)
**目的**: 測試多表關聯

**提問**:
```
目前有哪些生產工單正在進行中？進度如何？
```

**預期 SQL**:
```sql
SELECT
    po.production_number,
    p.product_name,
    po.planned_quantity,
    po.actual_quantity,
    po.status,
    po.priority,
    ROUND((po.actual_quantity::numeric / po.planned_quantity * 100), 2) as progress_percent
FROM production_orders po
JOIN products p ON po.product_id = p.id
WHERE po.status IN ('in_progress', 'scheduled')
ORDER BY po.priority DESC, po.start_date
```

**預期結果**:
- 顯示生產工單編號、產品名稱、計劃數量、實際數量
- 計算進度百分比
- 按優先級排序

---

### 測試案例 2.5: CTE (Common Table Expression)
**目的**: 測試複雜分析查詢

**提問**:
```
分析每個產品類別的銷售情況，包括訂單數量、銷售總額、平均單價
```

**預期 SQL**:
```sql
WITH product_sales AS (
    SELECT
        p.category,
        p.product_name,
        oi.quantity,
        oi.line_total
    FROM order_items oi
    JOIN products p ON oi.product_id = p.id
    JOIN sales_orders so ON oi.order_id = so.id
    WHERE so.status != 'cancelled'
)
SELECT
    category,
    COUNT(*) as order_count,
    SUM(quantity) as total_quantity,
    SUM(line_total) as total_sales,
    ROUND(AVG(line_total / quantity), 2) as avg_unit_price
FROM product_sales
GROUP BY category
ORDER BY total_sales DESC
```

**預期結果**:
- 顯示各類別的銷售統計
- 包含業務分析見解

---

## 3️⃣ 業務場景測試

### 測試案例 3.1: 庫存管理
**目的**: 測試庫存警示查詢

**提問**:
```
目前哪些產品庫存低於再訂購點？需要補貨嗎？
```

**預期 SQL**:
```sql
SELECT
    product_code,
    product_name,
    category,
    stock_quantity,
    reorder_point,
    (reorder_point - stock_quantity) as shortage,
    lead_time_days
FROM products
WHERE stock_quantity < reorder_point
ORDER BY (reorder_point - stock_quantity) DESC
```

**預期結果**:
- 顯示需要補貨的產品
- 計算缺貨數量
- 提供補貨建議

---

### 測試案例 3.2: 訂單追蹤
**目的**: 測試特定客戶訂單查詢

**提問**:
```
台積電的訂單有哪些？目前進度如何？
```

**預期 SQL**:
```sql
SELECT
    so.order_number,
    so.order_date,
    so.required_date,
    so.status,
    so.payment_status,
    so.final_amount,
    COUNT(oi.id) as item_count
FROM sales_orders so
JOIN customers c ON so.customer_id = c.id
LEFT JOIN order_items oi ON so.id = oi.order_id
WHERE c.customer_name LIKE '%台積電%'
GROUP BY so.id, so.order_number, so.order_date, so.required_date,
         so.status, so.payment_status, so.final_amount
ORDER BY so.order_date DESC
```

**預期結果**:
- 顯示台積電的所有訂單
- 包含訂單狀態和金額
- 提供進度摘要

---

### 測試案例 3.3: 應收帳款分析
**目的**: 測試財務相關查詢

**提問**:
```
目前有哪些訂單還沒付款？總金額多少？
```

**預期 SQL**:
```sql
SELECT
    c.customer_name,
    so.order_number,
    so.order_date,
    so.final_amount,
    so.payment_status,
    (CURRENT_DATE - so.order_date) as days_outstanding
FROM sales_orders so
JOIN customers c ON so.customer_id = c.id
WHERE so.payment_status IN ('unpaid', 'partial')
ORDER BY so.order_date ASC
```

**預期結果**:
- 顯示未付款訂單列表
- 計算帳齡（天數）
- 統計總應收金額
- 提供催收建議

---

### 測試案例 3.4: 生產效率分析
**目的**: 測試生產數據分析

**提問**:
```
各個負責人的生產效率如何？完成率多少？
```

**預期 SQL**:
```sql
SELECT
    assigned_to,
    COUNT(*) as total_orders,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_orders,
    ROUND(
        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100,
        2
    ) as completion_rate,
    AVG(actual_quantity::numeric / planned_quantity * 100) as avg_efficiency
FROM production_orders
GROUP BY assigned_to
ORDER BY completion_rate DESC
```

**預期結果**:
- 顯示各負責人的生產統計
- 計算完成率和效率
- 提供績效分析

---

### 測試案例 3.5: 出貨狀態追蹤
**目的**: 測試物流相關查詢

**提問**:
```
最近有哪些訂單已經出貨？物流狀態如何？
```

**預期 SQL**:
```sql
SELECT
    s.shipment_number,
    so.order_number,
    c.customer_name,
    s.shipment_date,
    s.carrier,
    s.tracking_number,
    s.status,
    s.total_weight,
    (CURRENT_DATE - s.shipment_date) as days_since_shipment
FROM shipments s
JOIN sales_orders so ON s.order_id = so.id
JOIN customers c ON so.customer_id = c.id
ORDER BY s.shipment_date DESC
LIMIT 10
```

**預期結果**:
- 顯示最近出貨記錄
- 包含物流商、追蹤號碼
- 計算出貨天數

---

## 4️⃣ 效能測試

### 測試案例 4.1: EXPLAIN 查詢計劃
**目的**: 測試 `sql_explain_query` 工具

**提問**:
```
請分析這個查詢的效能：查詢所有訂單及其客戶資訊
```

**預期行為**:
- Agent 調用 `sql_explain_query`
- 顯示查詢執行計劃
- 提供優化建議（如果需要）

---

### 測試案例 4.2: 大數據量查詢
**目的**: 測試自動 LIMIT 保護

**提問**:
```
列出所有訂單明細
```

**預期行為**:
- 自動添加 `LIMIT 100`
- 提示用戶結果已限制
- 建議如何查看更多數據

---

## 5️⃣ 錯誤處理測試

### 測試案例 5.1: 嘗試非法操作 (DELETE)
**目的**: 測試安全性保護

**提問**:
```
刪除所有已取消的訂單
```

**預期行為**:
- Agent 拒絕執行 DELETE 操作
- 說明只支援 SELECT 查詢
- 提供替代方案（如查看取消的訂單）

---

### 測試案例 5.2: 嘗試非法操作 (UPDATE)
**目的**: 測試寫入保護

**提問**:
```
把所有未付款的訂單狀態改成已付款
```

**預期行為**:
- Agent 拒絕執行 UPDATE 操作
- 說明數據庫為唯讀模式
- 建議使用應用程式介面進行修改

---

### 測試案例 5.3: 表不存在
**目的**: 測試錯誤處理

**提問**:
```
查詢 employees 表的資料
```

**預期行為**:
- 返回錯誤訊息：表不存在
- 提供可用的表列表
- 建議正確的查詢方式

---

### 測試案例 5.4: 語法錯誤
**目的**: 測試 SQL 錯誤處理

**提問**:
```
(直接提供錯誤的 SQL)
SELECT * FROM customers WHERE
```

**預期行為**:
- 檢測到 SQL 語法錯誤
- 提供錯誤說明
- 建議正確的查詢語法

---

## 📊 測試結果記錄模板

### 測試案例執行記錄

| 案例編號 | 測試項目 | 使用模型 | 結果 | 執行時間 | 備註 |
|---------|---------|---------|------|---------|------|
| 1.1 | 查看資料庫結構 | Claude 3 Opus | ✅ | 2s | - |
| 1.2 | 查看表結構 | Claude 3 Opus | ✅ | 3s | - |
| 1.3 | 簡單查詢 | Claude 3 Haiku | ✅ | 4s | - |
| ... | ... | ... | ... | ... | ... |

### 評估標準

- ✅ **通過**: Agent 正確識別需求、生成正確 SQL、返回預期結果
- ⚠️ **部分通過**: 功能完成但有小問題（如格式、效能）
- ❌ **失敗**: 無法完成任務或結果錯誤

---

## 🎯 進階測試建議

### 1. 壓力測試
- 連續提問 10 個複雜查詢
- 觀察響應時間和準確性

### 2. 複雜場景測試
- 提出需要多步驟推理的問題
- 測試 Agent 的邏輯理解能力

### 3. 模型對比測試
- 同一問題分別用 Claude 3 Opus、Claude 3 Haiku、GPT-4o 測試
- 比較生成的 SQL 質量和執行效率

### 4. 中文/英文測試
- 用中文和英文分別提問
- 驗證多語言支援

---

## 🔧 故障排除

### 問題 1: Agent 不調用 SQL 工具
**解決方案**:
- 確認使用支援 Function Calling 的模型（Claude 或 GPT-4）
- 重新措辭問題，明確提到「查詢」或「資料庫」

### 問題 2: SQL 語法錯誤
**解決方案**:
- 查看錯誤訊息
- 使用 `sql_get_schema` 檢查表結構
- 嘗試更明確的問題描述

### 問題 3: 查詢結果為空
**解決方案**:
- 檢查 WHERE 條件是否過於嚴格
- 使用 `sql_list_tables` 確認表中有資料
- 嘗試更寬鬆的查詢條件

---

## 📝 測試完成檢查清單

- [ ] 基礎查詢測試全部通過
- [ ] 進階分析測試全部通過
- [ ] 業務場景測試全部通過
- [ ] 效能測試完成
- [ ] 錯誤處理測試完成
- [ ] 測試結果已記錄
- [ ] 發現的問題已記錄並回報

---

**文檔版本**: 1.0
**最後更新**: 2025-11-10
**作者**: FENC AI Platform Team
