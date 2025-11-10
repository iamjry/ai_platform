# Manufacturing Demo Database - Testing Guide

## Overview
This guide provides examples of how to test the SQL database tools using the manufacturing demo database through the Web UI with AI Agents.

**Created**: 2025-11-10

---

## Database Schema Summary

### Tables Created
1. **customers** (客戶資料表) - 15 customers
2. **products** (產品資料表) - 30 products across 9 categories
3. **sales_orders** (銷售訂單主檔) - 18 orders with various statuses
4. **order_items** (訂單明細表) - 53 order line items
5. **production_orders** (生產工單表) - 18 production orders
6. **inventory_transactions** (庫存異動表) - 30 transaction records
7. **shipments** (出貨記錄表) - 8 shipment records

### Sample Data Statistics
- **Customers**: 15 major Taiwan electronics manufacturers
- **Products**: 30 items (semiconductors, PCBs, modules, sensors, displays, batteries, etc.)
- **Orders**: 18 sales orders totaling ~650M NTD
- **Production**: 9 active production orders, 9 completed
- **Order Statuses**: pending, confirmed, manufacturing, shipped, delivered
- **Payment Statuses**: unpaid, partial, paid

---

## Testing Through Web UI

### Step 1: Access the Web UI
1. Open browser and navigate to: `http://localhost:8501`
2. Login with your credentials
3. Go to the **聊天 (Chat)** tab

### Step 2: Test Basic Queries
Ask the AI Agent questions that require database queries. The agent will automatically use the SQL tools.

---

## Example Questions for Testing

### 1. Customer Queries (客戶查詢)

**Example Question**:
```
請問目前有哪些客戶？列出信用額度最高的5家公司。
```

**Expected Agent Behavior**:
- Use `sql_query` tool
- Query: `SELECT customer_name, city, credit_limit FROM customers ORDER BY credit_limit DESC LIMIT 5`
- Display results showing:
  1. 鴻海精密 (80M)
  2. 日月光 (60M)
  3. 廣達電腦 (55M)
  4. 友達光電 (52M)
  5. 台積電 (50M)

---

### 2. Product Queries (產品查詢)

**Example Question**:
```
半導體類產品有哪些？各有多少庫存？
```

**Expected Agent Behavior**:
- Use `sql_query` tool
- Query: `SELECT product_name, unit_price, stock_quantity FROM products WHERE category = '半導體' ORDER BY unit_price DESC`
- Display 3 semiconductor products with prices and stock levels

**Example Question**:
```
目前庫存低於再訂購點的產品有哪些？需要補貨嗎？
```

**Expected SQL**:
```sql
SELECT product_code, product_name, stock_quantity, reorder_point
FROM products
WHERE stock_quantity < reorder_point
```

---

### 3. Sales Order Queries (訂單查詢)

**Example Question**:
```
最近的5筆訂單狀態如何？哪些還在生產中？
```

**Expected Agent Behavior**:
- Use `sql_query` tool with JOIN
- Query joins `sales_orders` and `customers`
- Shows order number, customer name, status, payment status, amount

**Example Question**:
```
有哪些訂單的付款狀態是「已付款」的？總金額多少？
```

**Expected SQL**:
```sql
SELECT order_number, customer_name, final_amount, payment_status
FROM sales_orders so
JOIN customers c ON so.customer_id = c.id
WHERE payment_status = 'paid'
ORDER BY order_date DESC
```

**Example Question**:
```
台積電的訂單有哪些？目前進度如何？
```

**Expected SQL**:
```sql
SELECT so.order_number, so.order_date, so.status, so.final_amount
FROM sales_orders so
JOIN customers c ON so.customer_id = c.id
WHERE c.customer_name LIKE '%台積電%'
ORDER BY so.order_date DESC
```

---

### 4. Production Queries (生產查詢)

**Example Question**:
```
目前有哪些生產工單正在進行中？進度如何？
```

**Expected Agent Behavior**:
- Use `sql_query` tool with JOIN
- Query joins `production_orders` and `products`
- Shows production number, product name, quantity, status, priority
- Calculates progress percentage: `(actual_quantity / planned_quantity * 100)`

**Example SQL**:
```sql
SELECT
    po.production_number,
    p.product_name,
    po.planned_quantity,
    po.actual_quantity,
    po.scrap_quantity,
    po.status,
    po.priority,
    po.assigned_to,
    ROUND((po.actual_quantity::numeric / po.planned_quantity * 100), 1) as progress_percent
FROM production_orders po
JOIN products p ON po.product_id = p.id
WHERE po.status = 'in_progress'
ORDER BY po.priority DESC, po.start_date
```

**Example Question**:
```
緊急優先級的生產工單有幾個？分別是什麼產品？
```

**Expected SQL**:
```sql
SELECT production_number, product_name, status, priority, start_date
FROM production_orders po
JOIN products p ON po.product_id = p.id
WHERE priority = 'urgent'
ORDER BY start_date
```

---

### 5. Inventory Queries (庫存查詢)

**Example Question**:
```
最近有哪些庫存異動記錄？
```

**Expected SQL**:
```sql
SELECT
    it.transaction_type,
    p.product_name,
    it.quantity,
    it.reference_number,
    it.transaction_date,
    it.notes
FROM inventory_transactions it
JOIN products p ON it.product_id = p.id
ORDER BY it.transaction_date DESC
LIMIT 10
```

**Example Question**:
```
報廢的產品有哪些？數量多少？
```

**Expected SQL**:
```sql
SELECT
    p.product_name,
    ABS(it.quantity) as scrap_quantity,
    it.notes,
    it.transaction_date
FROM inventory_transactions it
JOIN products p ON it.product_id = p.id
WHERE it.transaction_type = 'scrap'
ORDER BY it.transaction_date DESC
```

---

### 6. Shipment Queries (出貨查詢)

**Example Question**:
```
目前有哪些貨物在運送中？預計何時送達？
```

**Expected SQL**:
```sql
SELECT
    s.shipment_number,
    so.order_number,
    c.customer_name,
    s.shipment_date,
    s.carrier,
    s.tracking_number,
    s.status
FROM shipments s
JOIN sales_orders so ON s.order_id = so.id
JOIN customers c ON so.customer_id = c.id
WHERE s.status IN ('shipped', 'in_transit')
ORDER BY s.shipment_date DESC
```

---

### 7. Complex Analytical Queries (複雜分析查詢)

**Example Question**:
```
分析各個客戶的訂單總金額，誰是最大客戶？
```

**Expected SQL**:
```sql
SELECT
    c.customer_name,
    COUNT(so.id) as order_count,
    SUM(so.final_amount) as total_amount,
    AVG(so.final_amount) as avg_order_amount
FROM customers c
LEFT JOIN sales_orders so ON c.id = so.customer_id
GROUP BY c.id, c.customer_name
HAVING COUNT(so.id) > 0
ORDER BY total_amount DESC
LIMIT 10
```

**Example Question**:
```
各個產品類別的銷售情況如何？
```

**Expected SQL**:
```sql
SELECT
    p.category,
    COUNT(oi.id) as items_sold,
    SUM(oi.quantity) as total_quantity,
    SUM(oi.line_total) as total_revenue
FROM products p
JOIN order_items oi ON p.id = oi.product_id
GROUP BY p.category
ORDER BY total_revenue DESC
```

**Example Question**:
```
生產線的工作負載如何？哪條生產線最忙？
```

**Expected SQL**:
```sql
SELECT
    assigned_to,
    COUNT(*) as order_count,
    SUM(planned_quantity) as total_planned,
    SUM(actual_quantity) as total_produced,
    SUM(scrap_quantity) as total_scrap
FROM production_orders
WHERE status IN ('in_progress', 'released')
GROUP BY assigned_to
ORDER BY order_count DESC
```

**Example Question**:
```
哪些訂單已經超過預定交貨日期但還沒出貨？
```

**Expected SQL**:
```sql
SELECT
    so.order_number,
    c.customer_name,
    so.order_date,
    so.required_date,
    so.status,
    (CURRENT_DATE - so.required_date) as days_overdue
FROM sales_orders so
JOIN customers c ON so.customer_id = c.id
WHERE so.required_date < CURRENT_DATE
    AND so.status NOT IN ('shipped', 'delivered')
ORDER BY days_overdue DESC
```

---

## Testing Scenarios

### Scenario 1: Customer Service Representative
**Context**: A customer calls asking about their order status

**Test Conversation**:
```
User: 鴻海精密的訂單目前狀態如何？

Expected Agent Actions:
1. Use sql_query to find orders for 鴻海精密
2. Query sales_orders joined with customers
3. Display order number, date, status, amount
4. Provide summary in natural language
```

---

### Scenario 2: Production Manager
**Context**: Daily production status review

**Test Conversation**:
```
User: 今天生產線A組有哪些工單在進行？進度如何？

Expected Agent Actions:
1. Use sql_query to find production orders assigned to "生產線A組"
2. Filter by status = 'in_progress'
3. Calculate progress percentage
4. Identify any at-risk orders (low progress, near deadline)
5. Provide actionable summary
```

---

### Scenario 3: Inventory Manager
**Context**: Daily inventory review

**Test Conversation**:
```
User: 檢查一下庫存狀況，有沒有需要補貨的產品？

Expected Agent Actions:
1. Use sql_query to find products where stock_quantity < reorder_point
2. Display product code, name, current stock, reorder point
3. Calculate shortage quantity
4. Prioritize by category or lead time
5. Generate reorder recommendation
```

---

### Scenario 4: Sales Manager
**Context**: Monthly sales review

**Test Conversation**:
```
User: 這個月的訂單總額多少？哪些客戶下單最多？

Expected Agent Actions:
1. Use sql_query with date filtering (March 2025)
2. Calculate total order amount
3. Group by customer to find top buyers
4. Use aggregate functions (SUM, COUNT, AVG)
5. Present insights with comparisons
```

---

## Verification Checklist

After each test, verify:

- [ ] Agent correctly identified the need to query database
- [ ] Agent used appropriate SQL tool (`sql_query`, `sql_get_schema`, `sql_list_tables`)
- [ ] SQL query is syntactically correct
- [ ] SQL query returns expected results
- [ ] Agent presents results in clear, natural language
- [ ] Agent provides insights beyond raw data (if applicable)
- [ ] Query execution completes within timeout (< 30 seconds)
- [ ] No SQL injection or dangerous queries attempted

---

## Expected Tool Usage Patterns

### Pattern 1: Schema Discovery First
```
User asks complex question →
  Agent uses sql_get_schema to understand table structure →
  Agent uses sql_query to retrieve data →
  Agent presents results
```

### Pattern 2: Direct Query
```
User asks simple question →
  Agent uses sql_query directly →
  Agent presents results
```

### Pattern 3: Multi-Step Analysis
```
User asks analytical question →
  Agent uses sql_list_tables to discover available data →
  Agent uses sql_get_schema on relevant tables →
  Agent uses sql_query with JOINs and aggregations →
  Agent uses sql_query for drill-down queries →
  Agent synthesizes insights
```

---

## Common SQL Patterns to Test

### 1. Simple SELECT
```sql
SELECT * FROM customers LIMIT 10
```

### 2. WHERE Filtering
```sql
SELECT * FROM products WHERE category = '半導體'
```

### 3. JOIN Operations
```sql
SELECT so.order_number, c.customer_name, so.final_amount
FROM sales_orders so
JOIN customers c ON so.customer_id = c.id
```

### 4. Aggregations
```sql
SELECT category, COUNT(*), AVG(unit_price)
FROM products
GROUP BY category
```

### 5. Subqueries
```sql
SELECT customer_name
FROM customers
WHERE id IN (
    SELECT customer_id
    FROM sales_orders
    WHERE final_amount > 40000000
)
```

### 6. Common Table Expressions (CTEs)
```sql
WITH order_stats AS (
    SELECT customer_id, COUNT(*) as order_count, SUM(final_amount) as total
    FROM sales_orders
    GROUP BY customer_id
)
SELECT c.customer_name, os.order_count, os.total
FROM customers c
JOIN order_stats os ON c.id = os.customer_id
ORDER BY os.total DESC
```

---

## Troubleshooting

### Issue: Agent doesn't use SQL tools
**Cause**: Question may not clearly require database access
**Solution**: Rephrase question to explicitly mention querying data, e.g., "查詢資料庫中的..."

### Issue: Query timeout
**Cause**: Query too complex or missing indexes
**Solution**:
- Check query uses indexed columns (customer_id, product_id, order_id, status, dates)
- Add LIMIT clause
- Use sql_explain_query to analyze performance

### Issue: Wrong results
**Cause**: Incorrect JOIN or WHERE conditions
**Solution**:
- Use sql_get_schema to verify column names and types
- Test query components separately
- Check for NULL values

### Issue: Agent confused about schema
**Cause**: Ambiguous table/column names
**Solution**:
- Be specific in questions (mention table names if known)
- Ask agent to "先檢查資料庫結構" before querying

---

## Performance Tips

1. **Use indexes**: All foreign keys and common search columns are indexed
2. **Limit results**: Always use LIMIT for large datasets
3. **Avoid SELECT ***: Specify only needed columns
4. **Use EXPLAIN**: Test query performance with `sql_explain_query` tool
5. **Aggregate wisely**: Group by indexed columns when possible

---

## Security Verification

Test that dangerous operations are blocked:

**Test 1: Try DELETE**
```
User: 刪除所有待處理的訂單

Expected: Agent should recognize this requires DELETE and refuse
Error: "Dangerous keyword 'DELETE' is not allowed"
```

**Test 2: Try UPDATE**
```
User: 把所有訂單的狀態改成已完成

Expected: Agent should recognize this requires UPDATE and refuse
Error: "Dangerous keyword 'UPDATE' is not allowed"
```

**Test 3: Try DROP**
```
User: DROP TABLE customers;

Expected: Immediate rejection by validator
Error: "Dangerous keyword 'DROP' is not allowed"
```

---

## Sample Output Examples

### Example 1: Customer List Query
```
User: 請列出所有客戶的名稱和城市

Agent Response:
我來查詢資料庫中的客戶資料。

[Uses sql_query tool]

根據資料庫查詢，目前系統中有15家客戶：

1. 台積電股份有限公司 - 新竹市
2. 鴻海精密工業股份有限公司 - 新北市
3. 聯發科技股份有限公司 - 新竹市
... (continues)

這些都是台灣主要的電子製造業大廠。
```

### Example 2: Production Status Query
```
User: 生產線目前的狀況如何？

Agent Response:
讓我查詢目前所有進行中的生產工單。

[Uses sql_query tool with JOIN]

目前有9個生產工單正在進行中：

緊急優先級 (4個):
- PO-2025-0010: 電源管理IC - 進度84% (生產線A組)
- PO-2025-0011: 藍牙音訊模組 - 進度85% (生產線B組)
- PO-2025-0017: 高效能微處理器晶片 - 進度76% (生產線A組)
- PO-2025-0018: 5G通訊模組 - 進度73% (生產線B組)

高優先級 (3個):
- PO-2025-0012: 高效能微處理器晶片 - 進度87% (生產線A組)
- PO-2025-0013: 5G通訊模組 - 進度83% (生產線B組)
- PO-2025-0016: 電源管理IC - 進度82% (生產線A組)

正常優先級 (2個):
- PO-2025-0014: 高效能微處理器晶片 - 進度69% (生產線A組)
- PO-2025-0015: 15.6吋LCD顯示器 - 進度69% (生產線C組)

建議: 生產線A組工作負載較重，可能需要調配資源。
```

---

## Next Steps

After successful testing:

1. **Expand Agent Capabilities**
   - Add more sophisticated query generation
   - Implement natural language to SQL translation improvements
   - Add query result visualization (charts, graphs)

2. **Add More Tools**
   - Create data export functionality
   - Add report generation tools
   - Implement scheduled queries

3. **Improve User Experience**
   - Add query history
   - Implement query templates for common scenarios
   - Create dashboard widgets

4. **Production Readiness**
   - Add query result caching
   - Implement rate limiting
   - Add audit logging for all queries
   - Set up monitoring and alerts

---

**Document Version**: 1.0
**Last Updated**: 2025-11-10
**Author**: FENC AI Platform Team
