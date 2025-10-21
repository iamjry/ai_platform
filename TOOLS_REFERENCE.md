# AI Platform - Tools Reference Guide

**Total Tools:** 28
**Version:** 2.1.0
**Last Updated:** 2025-10-17

---

## Overview

The AI Platform provides 28 intelligent tools across 14 categories. These tools can be accessed through:
- 💬 **Chat Interface** (Web UI - Tab 1)
- 📋 **Agent Task Execution** (Web UI - Tab 2)
- 🔌 **REST API** (`/agent/execute` endpoint)

The LLM automatically selects and calls the appropriate tools based on user requests.

---

## Tool Categories

### 📊 1. DATA ANALYSIS & PROCESSING (5 tools)

#### `analyze_data`
**Category:** analysis
**Description:** 分析數據集並生成統計洞察 (Analyze datasets and generate statistical insights)

**Parameters:**
- `data_source` (string): Source of data to analyze
- `analysis_type` (string): Type of analysis (descriptive, diagnostic, predictive)
- `options` (object): Additional analysis options

**Example Usage:**
```
"Analyze sales data with descriptive statistics"
```

#### `process_csv`
**Category:** data_processing
**Description:** 處理和轉換CSV文件 (Process and transform CSV files)

**Parameters:**
- `csv_data` (string): CSV content or path
- `operation` (string): Operation (filter, sort, aggregate, transform)
- `params` (object): Operation-specific parameters

**Example Usage:**
```
"Process this CSV and filter rows where sales > 1000"
```

#### `generate_chart`
**Category:** visualization
**Description:** 從數據創建可視化圖表 (Create visualizations from data)

**Parameters:**
- `data` (array): Data to visualize
- `chart_type` (string): Chart type (bar, line, pie, scatter)
- `title` (string): Chart title

**Example Usage:**
```
"Create a bar chart showing monthly sales"
```

#### `calculate_metrics`
**Category:** analytics
**Description:** 計算業務KPI (Calculate business KPIs)

**Parameters:**
- `metric_type` (string): Metric type (conversion_rate, churn, etc.)
- `data_range` (string): Time range for calculation
- `dimensions` (object): Breakdown dimensions

**Example Usage:**
```
"Calculate conversion rate for last month"
```

#### `financial_calculator`
**Category:** finance
**Description:** 執行財務計算 (Perform financial calculations)

**Parameters:**
- `operation` (string): Operation (ROI, NPV, IRR, compound_interest)
- `values` (object): Values for calculation

**Example Usage:**
```
"Calculate ROI with gain 15000 and cost 10000"
```

**Supported Operations:**
- `ROI`: Return on Investment
- `NPV`: Net Present Value
- `IRR`: Internal Rate of Return
- `compound_interest`: Compound Interest Calculation

---

### 🔍 2. SEARCH & RETRIEVAL (4 tools)

#### `search_knowledge_base`
**Category:** search
**Description:** 搜尋企業知識庫 (Search enterprise knowledge base)

**Parameters:**
- `query` (string): Search query
- `collection` (string): Collection to search
- `limit` (integer): Maximum results

**Example Usage:**
```
"Search knowledge base for product documentation"
```

#### `semantic_search`
**Category:** search
**Description:** AI驅動的語義搜索 (AI-driven semantic search)

**Parameters:**
- `query` (string): Natural language query
- `similarity_threshold` (float): Minimum similarity score (0-1)
- `top_k` (integer): Number of results

**Example Usage:**
```
"Find documents similar to 'customer onboarding process'"
```

#### `web_search`
**Category:** search
**Description:** 搜索網絡獲取最新信息 (Search web for latest information)

**Parameters:**
- `query` (string): Search query
- `num_results` (integer): Number of results
- `time_range` (string): Time range (day, week, month, year)

**Example Usage:**
```
"Search web for latest AI news from this week"
```

#### `find_similar_documents`
**Category:** search
**Description:** 查找相似文檔 (Find similar documents)

**Parameters:**
- `document_id` (integer): Reference document ID
- `similarity_threshold` (float): Minimum similarity (0-1)

**Example Usage:**
```
"Find documents similar to document 42"
```

---

### 📝 3. CONTENT GENERATION (3 tools)

#### `summarize_document`
**Category:** content
**Description:** 生成文檔摘要 (Generate document summaries)

**Parameters:**
- `document_id` (integer): Document to summarize
- `summary_length` (integer): Target length (words)
- `language` (string): Output language

**Example Usage:**
```
"Summarize document 15 in 200 words"
```

#### `translate_text`
**Category:** content
**Description:** 翻譯文本 (Translate text)

**Parameters:**
- `text` (string): Text to translate
- `source_lang` (string): Source language code
- `target_lang` (string): Target language code

**Example Usage:**
```
"Translate 'Hello World' from English to Chinese"
```

#### `generate_report`
**Category:** content
**Description:** 從數據生成格式化報告 (Generate formatted reports from data)

**Parameters:**
- `template` (string): Report template name
- `data` (object): Data for report
- `output_format` (string): Format (PDF, HTML, Markdown)

**Example Usage:**
```
"Generate monthly sales report in PDF format"
```

---

### 🔐 4. SECURITY & COMPLIANCE (3 tools)

#### `check_permissions`
**Category:** security
**Description:** 驗證用戶訪問權限 (Verify user access permissions)

**Parameters:**
- `user_id` (string): User identifier
- `resource_id` (string): Resource identifier

**Example Usage:**
```
"Check if user john@example.com can access document 42"
```

#### `audit_log`
**Category:** security
**Description:** 記錄和查詢系統審計日誌 (Record and query audit logs)

**Parameters:**
- `action_type` (string): Type of action (create, read, update, delete)
- `timestamp_range` (string): Time range for query
- `user_id` (string): User to filter by

**Example Usage:**
```
"Show audit logs for last 24 hours"
```

#### `scan_sensitive_data`
**Category:** security
**Description:** 檢測敏感信息 (Detect sensitive information)

**Parameters:**
- `text` (string): Text to scan
- `data_types` (array): Types to detect (email, phone, ssn, credit_card)

**Example Usage:**
```
"Scan this text for email addresses and phone numbers"
```

---

### 💼 5. BUSINESS PROCESS (3 tools)

#### `create_task`
**Category:** workflow
**Description:** 創建項目任務 (Create project tasks)

**Parameters:**
- `title` (string): Task title
- `description` (string): Task description
- `assignee` (string): Assigned user
- `due_date` (string): Due date (ISO format)

**Example Usage:**
```
"Create task 'Update documentation' assigned to john@example.com"
```

#### `send_notification`
**Category:** communication
**Description:** 發送通知 (Send notifications)

**Parameters:**
- `recipients` (array): List of recipients
- `message` (string): Notification message
- `channel` (string): Channel (email, slack, teams, sms)
- `priority` (string): Priority (low, normal, high, urgent)

**Example Usage:**
```
"Send urgent notification to team about system maintenance"
```

#### `schedule_meeting`
**Category:** workflow
**Description:** 安排會議 (Schedule meetings)

**Parameters:**
- `participants` (array): Meeting participants
- `duration` (integer): Duration in minutes
- `time_preferences` (array): Preferred time slots

**Example Usage:**
```
"Schedule 30-minute meeting with john@example.com tomorrow at 2pm"
```

---

### 🔗 6. SYSTEM INTEGRATION (3 tools)

#### `call_api`
**Category:** integration
**Description:** 調用外部API (Call external APIs)

**Parameters:**
- `url` (string): API endpoint URL
- `method` (string): HTTP method (GET, POST, PUT, DELETE)
- `headers` (object): Request headers
- `body` (object): Request body

**Example Usage:**
```
"Call GitHub API to get repository information"
```

#### `execute_sql`
**Category:** database
**Description:** 執行只讀SQL查詢 (Execute read-only SQL queries)

**Parameters:**
- `query` (string): SQL query (SELECT only)
- `database` (string): Database name
- `timeout` (integer): Query timeout in seconds

**Example Usage:**
```
"Execute SQL: SELECT * FROM users WHERE active = true LIMIT 10"
```

**Security:** Only SELECT queries are allowed. No INSERT, UPDATE, or DELETE.

#### `run_script`
**Category:** execution
**Description:** 在沙箱中執行Python腳本 (Execute Python scripts in sandbox)

**Parameters:**
- `script_code` (string): Python code to execute
- `input_params` (object): Input parameters
- `timeout` (integer): Execution timeout

**Example Usage:**
```
"Run Python script to calculate fibonacci sequence"
```

**Security:** Executes in sandboxed environment with restricted imports.

---

### 💬 7. COMMUNICATION (3 tools)

#### `send_email`
**Category:** communication
**Description:** 發送郵件 (Send emails)

**Parameters:**
- `to` (array): Recipient email addresses
- `subject` (string): Email subject
- `body` (string): Email body
- `attachments` (array): File attachments (optional)

**Example Usage:**
```
"Send email to john@example.com with subject 'Meeting Tomorrow'"
```

**Multi-stage Example:**
```
User: "send email"
Agent: "Who should I send it to?"
User: "john@example.com"
Agent: "What's the subject?"
User: "Meeting Tomorrow"
Agent: "What's the email body?"
User: "Let's meet at 10 AM in conference room A"
→ Email sent successfully!
```

#### `create_slack_message`
**Category:** communication
**Description:** 發送Slack消息 (Send Slack messages)

**Parameters:**
- `channel` (string): Slack channel or user
- `message` (string): Message text
- `attachments` (array): Message attachments

**Example Usage:**
```
"Send Slack message to #general channel"
```

#### `send_notification`
(See Business Process section above)

---

### 📁 8. FILE MANAGEMENT (3 tools)

#### `upload_file`
**Category:** file
**Description:** 上傳文件到存儲 (Upload files to storage)

**Parameters:**
- `file_name` (string): File name
- `file_data` (string): Base64 encoded file data
- `folder` (string): Target folder

**Example Usage:**
```
"Upload report.pdf to documents folder"
```

#### `download_file`
**Category:** file
**Description:** 從存儲下載文件 (Download files from storage)

**Parameters:**
- `file_id` (string): File identifier
- `destination` (string): Download destination

**Example Usage:**
```
"Download file with ID file_12345"
```

#### `list_files`
**Category:** file
**Description:** 列出文件夾中的文件 (List files in folder)

**Parameters:**
- `folder_path` (string): Folder path
- `filter` (string): File filter pattern
- `sort_by` (string): Sort criteria (name, date, size)

**Example Usage:**
```
"List all PDF files in documents folder"
```

---

### 🗄️ 9. DATABASE (2 tools)

#### `query_database`
**Category:** database
**Description:** 查詢企業資料庫 (Query enterprise database)

**Parameters:**
- `query_type` (string): Query type
- `parameters` (object): Query parameters

**Example Usage:**
```
"Query database for active users"
```

#### `execute_sql`
(See System Integration section above)

---

### 📄 10. DOCUMENT (1 tool)

#### `get_document`
**Category:** document
**Description:** 獲取文件內容 (Get document content)

**Parameters:**
- `document_id` (integer): Document identifier

**Example Usage:**
```
"Get content of document 42"
```

---

## How to Use Tools

### Via Chat Interface (Web UI)

1. **Open Web UI**: http://localhost:8501
2. **Navigate to Chat Tab**
3. **Type natural language request**:
   - "Calculate ROI with gain 20000 and cost 15000"
   - "Send email to john@example.com"
   - "Search for product documentation"

### Via Agent Task Tab (Web UI)

1. **Navigate to Agent Task Execution Tab**
2. **Type task in text area**
3. **Click "Execute Task"**
4. **If multi-stage**: Provide follow-up information when asked

### Via REST API

```bash
curl -X POST http://localhost:8002/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Calculate ROI with gain 15000 and cost 10000",
    "model": "claude-3-sonnet"
  }'
```

---

## Multi-Stage Conversations

Many tools support multi-stage conversations where the agent asks for missing information:

### Example: Send Email

**Stage 1:**
```
You: "send email"
Agent: "Who should I send this email to?"
```

**Stage 2:**
```
You: "john@example.com"
Agent: "What should the subject be?"
```

**Stage 3:**
```
You: "Meeting Tomorrow"
Agent: "What should the email body say?"
```

**Stage 4:**
```
You: "Let's meet at 10 AM"
Agent: ✅ "Email sent successfully!"
```

---

## Tool Selection

The LLM automatically selects tools based on:

1. **Keywords**: "send", "calculate", "search", "create"
2. **Context**: Previous conversation history
3. **Parameters**: Available information in request
4. **Intent**: What the user is trying to accomplish

### When Tools Are Called

✅ **Tools are called when:**
- User requests specific action (send email, calculate, search)
- Required parameters are available or can be asked for
- Tool is appropriate for the task

❌ **Tools are NOT called when:**
- Simple conversational response is sufficient
- No appropriate tool exists
- User is asking general questions

---

## Best Practices

### For Users

1. **Be Specific**: "Calculate ROI with gain 15000 and cost 10000" vs "Calculate something"
2. **Provide Context**: Include relevant details in your request
3. **Allow Multi-Stage**: Respond to follow-up questions with requested information
4. **Check Results**: Review execution steps in metadata

### For Developers

1. **Use Appropriate Models**: Claude models work best for tool calling
2. **Pass Conversation History**: Enable multi-stage conversations
3. **Handle `needs_more_info`**: Check flag and prompt for more information
4. **Review Execution Steps**: Use steps array to debug tool calls

---

## Tool Response Format

All tools return responses in this format:

```json
{
  "result": "Tool execution result or agent response",
  "steps": [
    {
      "step": "tool_call_1",
      "tool": "tool_name",
      "arguments": {...},
      "status": "success"
    }
  ],
  "metadata": {
    "model_used": "claude-3-sonnet",
    "tokens_used": 3492,
    "conversation_active": false
  },
  "needs_more_info": false
}
```

---

## Supported Models

All models can use tools, but some perform better:

| Model | Tool Calling | Multi-Stage | Recommended |
|-------|-------------|-------------|-------------|
| **claude-3-opus** | ✅ Excellent | ✅ Excellent | ⭐⭐⭐ Best |
| **claude-3-sonnet** | ✅ Excellent | ✅ Excellent | ⭐⭐⭐ Best |
| **gpt-4** | ✅ Excellent | ✅ Very Good | ⭐⭐ Good |
| **gpt-3.5-turbo** | ✅ Good | ✅ Good | ⭐ OK |
| **qwen2.5** | ✅ Basic | ✅ Basic | ⭐ Local Only |

---

## Troubleshooting

### Tool Not Being Called

**Issue**: Agent responds without calling tool
**Solution**:
- Be more explicit in request
- Try: "Use the financial_calculator tool to calculate ROI"
- Check if model supports tool calling

### Missing Parameters

**Issue**: Tool call fails due to missing parameters
**Solution**:
- Enable multi-stage conversations
- Pass conversation_history in API calls
- Respond to agent's follow-up questions

### Wrong Tool Called

**Issue**: Agent calls incorrect tool
**Solution**:
- Be more specific in request
- Mention tool name explicitly
- Provide more context about intended action

---

## API Reference

### List All Tools

```bash
GET http://localhost:8001/tools/list
```

### Execute Agent with Tools

```bash
POST http://localhost:8002/agent/execute
Content-Type: application/json

{
  "task": "your request here",
  "model": "claude-3-sonnet",
  "conversation_history": []  // optional
}
```

---

## Version History

- **v2.1.0** (2025-10-17): Multi-stage conversation support added
- **v2.0.0** (2025-10-16): All 28 tools implemented
- **v1.0.0** (2025-10-15): Initial release with 3 tools

---

**For more information:**
- [Multi-Stage Conversation Guide](./MULTI_STAGE_CONVERSATION_GUIDE.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Test Results](./TEST_RESULTS.md)

**API Documentation:** http://localhost:8001/docs
