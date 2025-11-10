# SQL 工具使用說明

## 重要提醒

### 模型選擇建議

SQL 資料庫查詢工具的功能會因所選模型而異：

#### ✅ 推薦模型（支援完整功能）
這些模型支援 OpenAI 格式的 Function Calling，可以執行多步驟 SQL 查詢流程：

1. **Claude 3 Opus** ⭐ 最推薦（Claude 3.5 Sonnet 目前不可用）
   - 最強的推理和 SQL 生成能力
   - 可以理解複雜查詢需求
   - 自動執行：list tables → get schema → generate SQL → execute query
   - 提供詳細的數據分析和洞察
   - **注意**: 回應速度較慢，成本較高

2. **Claude 3 Haiku** ⭐ 推薦用於日常查詢
   - 速度快，成本低
   - SQL 生成能力良好
   - 適合簡單到中等複雜度的查詢
   - 最佳性價比選擇

3. **GPT-4 系列** (gpt-4, gpt-4o, gpt-4-turbo, gpt-4o-mini)
   - Function calling 支援良好
   - SQL 生成能力強
   - 適合需要詳細解釋的場景
   - GPT-4o-mini 是快速且經濟的選擇

#### ⚠️ 功能受限模型
這些模型不支援 Function Calling，只能執行單步驟工具調用：

- **GPT-OSS 120B**
- **Qwen 2.5 系列**
- **台灣政府 LLM API 模型**

**限制**:
- 每次對話只能執行 1 個工具調用
- 無法自動生成 SQL 查詢
- 只能查看資料庫結構（list tables）
- 需要用戶手動分步驟查詢

---

## 使用方式

### 方案 A: 使用 Claude 模型（推薦）

**步驟**:
1. 在 Web UI 聊天頁面選擇模型：**Claude 3 Opus** 或 **Claude 3 Haiku**
2. 直接問問題，無需關心技術細節

**注意**: Claude 3.5 Sonnet 和 Claude 3 Sonnet 目前因 API 訂閱限制而不可用。請使用 Claude 3 Opus（最強）或 Claude 3 Haiku（最快）。

**範例問題**:
```
最近的5筆訂單狀態如何？哪些還在生產中？
```

**Agent 會自動執行**:
1. 調用 `sql_list_tables` - 查看有哪些表
2. 調用 `sql_get_schema` - 查看 sales_orders 和 customers 的結構
3. 調用 `sql_query` - 執行 JOIN 查詢
4. 格式化結果並提供分析

**輸出範例**:
```
✅ SQL 查詢結果

order_number | customer_name | order_date | status | payment_status | final_amount
-------------|---------------|------------|--------|----------------|-------------
SO-2025-0018 | 廣達電腦 | 2025-04-08 | pending | unpaid | 39700500
SO-2025-0017 | 聯發科技 | 2025-04-05 | pending | unpaid | 33416250
SO-2025-0016 | 台積電 | 2025-04-01 | pending | unpaid | 26733000
SO-2025-0015 | 力成科技 | 2025-03-28 | pending | unpaid | 31122000
SO-2025-0014 | 日月光半導體 | 2025-03-25 | manufacturing | unpaid | 52368750

(共 5 筆資料)

分析：
- 最近 5 筆訂單中，有 1 筆正在生產中（SO-2025-0014）
- 客戶：日月光半導體
- 訂單金額：52,368,750 元
- 其餘 4 筆訂單狀態為待處理（pending）
```

---

### 方案 B: 使用 GPT-OSS 120B（功能受限）

**步驟**:
1. 選擇模型：**GPT-OSS 120B**
2. **分步驟**提問

**第 1 步 - 查看資料庫結構**:
```
請問資料庫有哪些表？
```

**Agent 回應**:
```
✅ 資料庫結構

找到 7 個資料表：

• customers (15 rows, 14 columns)
  客戶資料表

• products (30 rows, 13 columns)
  產品資料表

• sales_orders (18 rows, 17 columns)
  銷售訂單主檔

• order_items (53 rows, 12 columns)
  訂單明細表

• production_orders (18 rows, 17 columns)
  生產工單表

• inventory_transactions (30 rows, 8 columns)
  庫存異動記錄表

• shipments (8 rows, 10 columns)
  出貨記錄表
```

**第 2 步 - 手動查詢**:

由於 GPT-OSS 120B 無法生成 SQL，你有兩個選擇：

**選擇 1: 切換到 Claude 模型**（推薦）
```
（切換模型到 Claude 3.5 Sonnet）
最近的5筆訂單狀態如何？哪些還在生產中？
```

**選擇 2: 使用資料庫工具直接查詢**
- 使用 pgAdmin 或其他資料庫工具
- 手動編寫 SQL 查詢

---

## 測試範例

### 測試 1: 客戶查詢（Claude）
```
問：請列出信用額度最高的5家客戶

預期：自動查詢 customers 表，返回排序結果
```

### 測試 2: 訂單分析（Claude）
```
問：分析各個客戶的訂單總金額，誰是最大客戶？

預期：GROUP BY 查詢，計算訂單總額並排序
```

### 測試 3: 生產進度（Claude）
```
問：目前有哪些生產工單正在進行中？進度如何？

預期：JOIN production_orders 和 products，計算完成百分比
```

### 測試 4: 資料庫結構（GPT-OSS 120B）
```
問：資料庫有哪些表？

預期：返回 7 個表的列表和描述
```

---

## 技術說明

### Function Calling 支援

**支援的模型**:
- Claude 3 系列（Sonnet, Opus, Haiku）
- GPT-4 系列（gpt-4, gpt-4o, gpt-4-turbo, gpt-4o-mini）
- GPT-3.5 Turbo

**不支援的模型**:
- GPT-OSS 120B
- Qwen 2.5 系列
- Ollama 本地模型
- 台灣政府 LLM API 模型

### Fallback 模式

對於不支援 Function Calling 的模型，使用模式偵測（Pattern Detection）：

**偵測關鍵字**:
- 中文：訂單、客戶、產品、庫存、銷售、生產、出貨、工單、進行中、待處理
- 英文：customers, products, orders, inventory, sales

**行為**:
- 偵測到 SQL 相關問題 → 自動調用 `sql_list_tables`
- 返回資料庫結構
- 但無法繼續執行後續查詢

---

## 故障排除

### 問題 1: Agent 說要查詢但沒有結果

**原因**: 使用了不支援 Function Calling 的模型（如 GPT-OSS 120B）

**解決**: 切換到 Claude 3.5 Sonnet 或 GPT-4

### 問題 2: SQL 查詢語法錯誤

**原因**: Agent 生成的 SQL 不正確

**解決**:
1. 在提問中提供更明確的需求
2. 指定具體的表名和欄位
3. 使用更強的模型（Claude 3.5 Sonnet）

### 問題 3: 查詢超時

**原因**: 查詢太複雜或資料量太大

**解決**:
1. 添加 LIMIT 限制
2. 優化 WHERE 條件
3. 使用 `sql_explain_query` 檢查執行計劃

---

## 最佳實踐

### 1. 模型選擇
- 複雜 SQL 查詢 → **Claude 3 Opus**
- 簡單到中等查詢 → **Claude 3 Haiku**（推薦，最佳性價比）
- 快速查詢 → GPT-4o-mini 或 Claude 3 Haiku
- 只查看結構 → 任何模型都可以

### 2. 提問技巧
- ✅ 明確需求："查詢最近 5 筆訂單"
- ✅ 指定條件："狀態為生產中的工單"
- ✅ 要求分析："分析客戶訂單總額"
- ❌ 模糊問題："告訴我一些資訊"

### 3. 安全性
- 所有 SQL 工具都是 READ-ONLY
- 不能執行 INSERT/UPDATE/DELETE/DROP
- 自動添加 LIMIT 保護
- 30 秒查詢超時保護

---

## 快速參考

| 任務類型 | 推薦模型 | 難度 | 預期執行時間 |
|---------|---------|------|------------|
| 查看表結構 | 任何模型 | ⭐ | < 1 秒 |
| 簡單查詢（單表） | Claude 3 Haiku | ⭐⭐ | 2-5 秒 |
| JOIN 查詢（多表） | Claude 3 Haiku | ⭐⭐⭐ | 5-10 秒 |
| 聚合分析 | Claude 3 Opus | ⭐⭐⭐ | 8-15 秒 |
| 複雜分析（CTE） | Claude 3 Opus | ⭐⭐⭐⭐ | 15-25 秒 |

---

**最後更新**: 2025-11-10
**版本**: 1.0
