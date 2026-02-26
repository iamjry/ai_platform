# LINE 整合機制說明文件

## 目錄
1. [系統架構](#系統架構)
2. [核心功能](#核心功能)
3. [技術實作](#技術實作)
4. [設定說明](#設定說明)
5. [使用範例](#使用範例)
6. [API 參考](#api-參考)
7. [故障排除](#故障排除)

---

## 系統架構

### 整體架構圖
```
User Request
     ↓
Agent Service (main.py)
     ├── Intent Detection (Fallback Mode)
     │   └── detect_tool_intent() → 關鍵字比對
     ├── Function Calling (Claude/GPT)
     │   └── System Prompt → AI 自動判斷
     ↓
MCP Server (main.py)
     ├── /tools/send_notification
     ├── LINE API Integration
     └── Message Delivery
     ↓
LINE Messaging API
     └── Push Message to User/Group
```

### 服務元件

| 元件 | 位置 | 功能 |
|------|------|------|
| Agent Service | `services/agent-service/main.py` | 意圖偵測、智慧收件人判斷 |
| MCP Server | `services/mcp-server/main.py` | LINE API 整合、訊息發送 |
| LINE API | `https://api.line.me/v2/bot/message/push` | 訊息推送服務 |

---

## 核心功能

### 1. 智慧收件人偵測

系統支援兩種模式的收件人判斷：

#### Mode A: Function Calling (Claude/GPT)
- **適用模型**: `gpt-3.5-turbo`, `gpt-4`, `claude-3-*`, `gemini-*`
- **機制**: AI 透過 System Prompt 分析語意，自動設定收件人
- **優勢**: 理解自然語言，更準確判斷意圖

#### Mode B: Fallback Mode (Qwen/Local Models)
- **適用模型**: `qwen2.5`, `llama3`, `mistral` 等本地模型
- **機制**: 關鍵字比對 + 模式匹配
- **優勢**: 不依賴 Function Calling，相容性高

### 2. 收件人類型

| 類型 | ID 格式 | 範例 | 說明 |
|------|---------|------|------|
| 個人用戶 | `U` 開頭 | `Ud45d50ec4f060587d3a42c38e67a6008` | 個人 LINE 帳號 |
| 群組 | `C` 開頭 | `Cxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` | LINE 群組聊天 |
| 聊天室 | `R` 開頭 | `Rxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` | LINE 聊天室 |

### 3. 自動 Fallback 機制
- 未指定收件人 → 使用 `LINE_DEFAULT_RECIPIENT_ID`
- 關鍵字 "我", "提醒我" → 使用 `LINE_USER_ID` (個人)
- 關鍵字 "群組", "大家" → 使用 `LINE_DEFAULT_RECIPIENT_ID` (群組)

---

## 技術實作

### 1. Agent Service - 意圖偵測 (Fallback Mode)

**檔案位置**: `services/agent-service/main.py:243-344`

#### 關鍵函數: `detect_tool_intent()`

```python
def detect_tool_intent(task: str) -> Optional[tuple]:
    """
    偵測用戶意圖並判斷要使用的工具

    Args:
        task: 用戶輸入的文字

    Returns:
        tuple: (tool_name, tool_args) 或 None
    """
    import re
    task_lower = task.lower()

    # LINE 訊息關鍵字偵測
    line_keywords = [
        "line", "傳訊息", "传讯息", "發line", "发line",
        "传line", "傳line", "line訊息", "line讯息",
        "line消息", "line群組", "line群组", "line group"
    ]

    has_line_keyword = any(keyword in task_lower for keyword in line_keywords)

    if has_line_keyword:
        # 個人關鍵字
        personal_keywords = [
            "我", "自己", "個人", "私訊", "私讯",
            "提醒我", "告訴我", "告诉我", "your-username",
            "jerry", "我自己", "傳給我", "传给我"
        ]

        # 群組關鍵字
        group_keywords = [
            "群組", "群组", "大家", "團隊", "团队",
            "所有人", "全體", "全体", "group",
            "everyone", "team", "all"
        ]

        has_personal = any(kw in task_lower for kw in personal_keywords)
        has_group = any(kw in task_lower for kw in group_keywords)

        # 提取訊息內容
        message = extract_message_content(task)

        # 移除收件人關鍵字前綴
        message = clean_recipient_prefix(message)

        # 判斷收件人
        if has_personal:
            recipients = ["Ud45d50ec4f060587d3a42c38e67a6008"]  # your-username
        elif has_group:
            recipients = []  # 使用預設群組
        else:
            recipients = []  # 預設為群組

        return ("send_notification", {
            "message": message,
            "channel": "line",
            "recipients": recipients
        })
```

#### 訊息內容提取

```python
# 內容提取模式
content_patterns = [
    r'(?:說|说|通知|告知|傳|传|發|发|内容|內容)[：:，,]?\s*(.+)',
    r'line[：:，,]?\s*(.+)',
    r'訊息[：:，,]?\s*(.+)',
    r'讯息[：:，,]?\s*(.+)'
]

for pattern in content_patterns:
    match = re.search(pattern, task, re.IGNORECASE)
    if match:
        message = match.group(1).strip()
        # 移除標點符號
        message = re.sub(r'[，,。！!？?]+$', '', message)
        break
```

#### 收件人前綴清理

```python
# 移除 "群組 今天會下雨" → "今天會下雨"
recipient_prefixes = [
    r'^(?:群組|群组|大家|團隊|团队|所有人|全體|全体|group|everyone|team|all)[,，\s]+',
    r'^(?:我|自己|個人|私訊|私讯)[,，\s]+',
    r'^(?:your-username|jerry)[,，\s]+'
]

for prefix_pattern in recipient_prefixes:
    message = re.sub(prefix_pattern, '', message, flags=re.IGNORECASE).strip()
```

### 2. Agent Service - System Prompt (Function Calling)

**檔案位置**: `services/agent-service/main.py:564-594`

```python
# System Prompt 片段（針對 LINE 通知）
system_prompt = """
你是一個企業AI助手...

當需要發送 LINE 訊息時：
1. 分析用戶語意，判斷收件人類型
2. 個人關鍵字："我"、"提醒我"、"私訊" → 使用個人 User ID
3. 群組關鍵字："群組"、"大家"、"團隊" → 使用預設群組
4. 自動設定 recipients 參數

工具使用範例：
{
  "tool": "send_notification",
  "arguments": {
    "message": "今晚會下雨記得帶傘",
    "channel": "line",
    "recipients": ["Ud45d50ec4f060587d3a42c38e67a6008"]  // 個人
  }
}
"""
```

### 3. Agent Service - 回應格式化

**檔案位置**: `services/agent-service/main.py:592-605`

```python
# 工具執行後格式化回應
if tool_name == "send_notification" and tool_args.get("channel") == "line":
    recipients = tool_result.get('recipients', [])

    # 判斷收件人類型
    if recipients:
        if recipients[0].startswith('U'):
            recipient_type = "個人 (your-username)"
        elif recipients[0].startswith('C'):
            recipient_type = "群組"
        else:
            recipient_type = str(recipients)
    else:
        recipient_type = "預設群組"

    result = f"""✅ LINE 訊息已成功發送！

發送對象: {recipient_type}
訊息內容: {tool_args.get('message', 'N/A')}
通知ID: {tool_result.get('notification_id')}
發送時間: {tool_result.get('sent_at')}"""
```

### 4. MCP Server - LINE API 整合

**檔案位置**: `services/mcp-server/main.py:1066-1159`

#### 資料模型

```python
class SendNotificationRequest(BaseModel):
    recipients: List[str] = []  # 可選，空陣列使用預設值
    message: str                # 必填
    channel: str = "line"       # "email", "slack", "teams", "line"
    priority: str = "normal"    # "low", "normal", "high", "urgent"
```

#### API 端點實作

```python
@app.post("/tools/send_notification")
async def send_notification(request: SendNotificationRequest):
    """
    發送通知 - 支援 Line, Email, Slack 等多種通道

    Args:
        request: SendNotificationRequest

    Returns:
        dict: 發送結果
    """
    try:
        notification_id = f"NOTIF-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        if request.channel.lower() == "line":
            # 1. 檢查 Access Token
            line_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
            if not line_token:
                raise HTTPException(
                    status_code=500,
                    detail="LINE_CHANNEL_ACCESS_TOKEN not configured"
                )

            # 2. 處理預設收件人
            recipients = request.recipients
            if not recipients:
                default_recipient = os.getenv("LINE_DEFAULT_RECIPIENT_ID", "").strip()
                if default_recipient:
                    recipients = [default_recipient]
                    logger.info(f"Using default LINE recipient: {default_recipient}")
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="No recipients provided and LINE_DEFAULT_RECIPIENT_ID not set"
                    )

            # 3. 發送訊息到每個收件人
            results = []
            async with httpx.AsyncClient() as client:
                for recipient_id in recipients:
                    try:
                        endpoint = "https://api.line.me/v2/bot/message/push"

                        headers = {
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {line_token}"
                        }

                        payload = {
                            "to": recipient_id,
                            "messages": [
                                {
                                    "type": "text",
                                    "text": request.message
                                }
                            ]
                        }

                        response = await client.post(
                            endpoint,
                            json=payload,
                            headers=headers
                        )

                        if response.status_code == 200:
                            logger.info(f"✅ LINE message sent to {recipient_id}")
                            results.append({
                                "recipient": recipient_id,
                                "status": "sent",
                                "status_code": response.status_code
                            })
                        else:
                            logger.error(f"❌ LINE API error: {response.text}")
                            results.append({
                                "recipient": recipient_id,
                                "status": "failed",
                                "status_code": response.status_code,
                                "error": response.text
                            })

                    except Exception as send_error:
                        logger.error(f"Error sending to {recipient_id}: {send_error}")
                        results.append({
                            "recipient": recipient_id,
                            "status": "failed",
                            "error": str(send_error)
                        })

            # 4. 回傳結果
            return {
                "notification_id": notification_id,
                "channel": "line",
                "recipients": recipients,
                "results": results,
                "priority": request.priority,
                "sent_at": datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"Send notification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### MCP Tool Definition

**檔案位置**: `services/mcp-server/main.py:397`

```python
{
    "name": "send_notification",
    "description": "發送通知到各種通道 (LINE, Email, Slack)",
    "inputSchema": {
        "type": "object",
        "properties": {
            "recipients": {
                "type": "array",
                "items": {"type": "string"},
                "description": "收件人列表 (可選，使用預設值)"
            },
            "message": {
                "type": "string",
                "description": "訊息內容"
            },
            "channel": {
                "type": "string",
                "enum": ["line", "email", "slack", "teams"],
                "description": "通知通道"
            },
            "priority": {
                "type": "string",
                "enum": ["low", "normal", "high", "urgent"],
                "description": "優先級"
            }
        },
        "required": ["message", "channel"]
    }
}
```

---

## 設定說明

### 1. LINE Messaging API 設定

#### 步驟 1: 建立 LINE Channel

1. 前往 [LINE Developers Console](https://developers.line.biz/console/)
2. 建立 Provider (若尚未建立)
3. 建立新的 "Messaging API" Channel
4. 在 Channel 設定中，前往 "Messaging API" 分頁

#### 步驟 2: 取得 Channel Access Token

1. 點擊 "Issue" 按鈕發行 Channel Access Token
2. 選擇 "Channel Access Token (long-lived)"
3. 複製 Token (格式: 長串英數字字串)

#### 步驟 3: 取得收件人 ID

**個人用戶 ID:**
```bash
# 方法 1: 透過 Webhook 事件取得
# - 將 Bot 加為好友
# - 傳送訊息給 Bot
# - 在 Webhook 事件中會有 user ID

# 方法 2: 使用測試工具
# 可以使用 LINE 的測試 Bot 來顯示你的 User ID
```

**群組 ID:**
```bash
# 方法 1: 邀請 Bot 加入群組
# - 群組管理員邀請 Bot 加入
# - 在 Webhook 事件中會有 group ID

# 方法 2: 透過 Bot 回傳群組資訊
# Bot 收到訊息時可以記錄群組 ID
```

### 2. 環境變數設定

**檔案位置**: `.env`

```bash
# =============================================================================
# LINE NOTIFICATION CONFIGURATION
# =============================================================================

# LINE Channel Access Token (必填)
LINE_CHANNEL_ACCESS_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ...

# 預設收件人 ID - 群組 (選填，建議設定)
LINE_DEFAULT_RECIPIENT_ID=Cxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 個人用戶 ID - your-username (選填，Agent Service 會使用)
LINE_USER_ID=Ud45d50ec4f060587d3a42c38e67a6008
```

**環境變數說明:**

| 變數名稱 | 必填 | 說明 | 範例 |
|---------|------|------|------|
| `LINE_CHANNEL_ACCESS_TOKEN` | ✅ | LINE Bot 的 Access Token | `eyJhbGc...` |
| `LINE_DEFAULT_RECIPIENT_ID` | ⚠️ | 預設收件人 (未指定時使用) | `Cxxxxxx...` |
| `LINE_USER_ID` | ❌ | 個人用戶 ID (Agent 自動判斷用) | `Uxxxxxx...` |

### 3. 生產環境設定

**檔案位置**: `.env.prod.template`

```bash
# =============================================================================
# LINE NOTIFICATION CONFIGURATION
# =============================================================================
LINE_CHANNEL_ACCESS_TOKEN=<LINE_ACCESS_TOKEN>
LINE_DEFAULT_RECIPIENT_ID=<LINE_RECIPIENT_ID>
```

### 4. 服務重啟

```bash
# 僅重啟 MCP Server
docker-compose restart mcp-server

# 或重啟所有相關服務
docker-compose up -d agent-service mcp-server
```

---

## 使用範例

### 1. 自然語言使用 (透過 Agent)

#### 範例 1: 發送到預設群組

```
用戶: 傳訊息到line群組：今晚會下雨記得帶傘
```

**處理流程:**
1. Agent Service 偵測到 "line群組" 關鍵字
2. 提取訊息: "今晚會下雨記得帶傘"
3. 設定 recipients = [] (使用預設群組)
4. 呼叫 `send_notification` 工具

**回應:**
```
✅ LINE 訊息已成功發送！

發送對象: 預設群組
訊息內容: 今晚會下雨記得帶傘
通知ID: NOTIF-20251122143522
發送時間: 2025-11-22T14:35:22.123456
```

#### 範例 2: 發送到個人

```
用戶: 提醒我明天下午3點開會
```

**處理流程:**
1. Agent Service 偵測到 "提醒我" 關鍵字
2. 判斷為個人訊息
3. 設定 recipients = ["Ud45d50ec4f060587d3a42c38e67a6008"]
4. 呼叫 `send_notification` 工具

**回應:**
```
✅ LINE 訊息已成功發送！

發送對象: 個人 (your-username)
訊息內容: 明天下午3點開會
通知ID: NOTIF-20251122143545
發送時間: 2025-11-22T14:35:45.789012
```

#### 範例 3: 通知所有人

```
用戶: 通知大家專案已完成
```

**處理流程:**
1. Agent Service 偵測到 "大家" 關鍵字
2. 設定 recipients = [] (使用預設群組)
3. 呼叫 `send_notification` 工具

**回應:**
```
✅ LINE 訊息已成功發送！

發送對象: 預設群組
訊息內容: 專案已完成
通知ID: NOTIF-20251122143612
發送時間: 2025-11-22T14:36:12.345678
```

### 2. 直接 API 呼叫

#### 使用預設收件人

```bash
curl -X POST http://localhost:8000/tools/send_notification \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello from API!",
    "channel": "line"
  }'
```

**回應:**
```json
{
  "notification_id": "NOTIF-20251122143700",
  "channel": "line",
  "recipients": ["Cxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"],
  "results": [
    {
      "recipient": "Cxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
      "status": "sent",
      "status_code": 200
    }
  ],
  "priority": "normal",
  "sent_at": "2025-11-22T14:37:00.123456"
}
```

#### 指定特定收件人

```bash
curl -X POST http://localhost:8000/tools/send_notification \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": ["Ud45d50ec4f060587d3a42c38e67a6008"],
    "message": "Personal reminder: Team meeting at 3pm",
    "channel": "line",
    "priority": "high"
  }'
```

#### 發送到多個收件人

```bash
curl -X POST http://localhost:8000/tools/send_notification \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": [
      "Ud45d50ec4f060587d3a42c38e67a6008",
      "Cxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    ],
    "message": "Multi-recipient message",
    "channel": "line"
  }'
```

### 3. Python SDK 使用

```python
import httpx
import asyncio

async def send_line_message(message: str, recipients: list = None):
    """發送 LINE 訊息"""
    url = "http://mcp-server:8000/tools/send_notification"

    payload = {
        "message": message,
        "channel": "line"
    }

    if recipients:
        payload["recipients"] = recipients

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        return response.json()

# 使用範例
async def main():
    # 發送到預設群組
    result = await send_line_message("Hello Group!")
    print(result)

    # 發送到個人
    result = await send_line_message(
        "Personal message",
        recipients=["Ud45d50ec4f060587d3a42c38e67a6008"]
    )
    print(result)

asyncio.run(main())
```

---

## API 參考

### Endpoint: `/tools/send_notification`

**Method**: `POST`

**Request Body:**

```typescript
{
  recipients?: string[];      // 可選，預設使用 LINE_DEFAULT_RECIPIENT_ID
  message: string;            // 必填
  channel: "line" | "email" | "slack" | "teams";  // 必填
  priority?: "low" | "normal" | "high" | "urgent"; // 可選，預設 "normal"
}
```

**Response:**

```typescript
{
  notification_id: string;    // 格式: NOTIF-YYYYMMDDHHMMSS
  channel: string;            // "line"
  recipients: string[];       // 實際發送的收件人列表
  results: Array<{
    recipient: string;        // 收件人 ID
    status: "sent" | "failed"; // 發送狀態
    status_code?: number;     // HTTP 狀態碼
    error?: string;           // 錯誤訊息 (若失敗)
  }>;
  priority: string;           // 優先級
  sent_at: string;            // ISO 8601 格式時間戳
}
```

### HTTP Status Codes

| Status Code | 說明 |
|-------------|------|
| 200 | 成功發送 |
| 400 | 請求參數錯誤 (如未提供收件人且無預設值) |
| 500 | 伺服器錯誤 (如 Token 未設定、LINE API 錯誤) |

### LINE API Error Codes

| Error | 說明 | 解決方法 |
|-------|------|---------|
| `Invalid reply token` | Token 無效或過期 | 檢查 `LINE_CHANNEL_ACCESS_TOKEN` |
| `The property, 'to', in the request body is invalid` | 收件人 ID 格式錯誤 | 確認 ID 以 U/C/R 開頭 |
| `Not friends or not in the group` | Bot 未加好友或未在群組中 | 加入好友或群組 |

---

## 故障排除

### 問題 1: LINE_CHANNEL_ACCESS_TOKEN not configured

**錯誤訊息:**
```
HTTPException: 500 - LINE_CHANNEL_ACCESS_TOKEN not configured
```

**解決方法:**
1. 確認 `.env` 檔案中已設定 `LINE_CHANNEL_ACCESS_TOKEN`
2. 檢查環境變數格式是否正確 (無多餘空格或換行)
3. 重啟 MCP Server: `docker-compose restart mcp-server`

### 問題 2: No recipients provided and LINE_DEFAULT_RECIPIENT_ID not set

**錯誤訊息:**
```
HTTPException: 400 - No recipients provided and LINE_DEFAULT_RECIPIENT_ID not set
```

**解決方法:**
1. 在 `.env` 中設定 `LINE_DEFAULT_RECIPIENT_ID`
2. 或在 API 呼叫時明確指定 `recipients` 參數

### 問題 3: The property, 'to', in the request body is invalid

**錯誤訊息:**
```
LINE API error: The property, 'to', in the request body is invalid
```

**可能原因:**
- 收件人 ID 格式錯誤
- ID 包含多餘的空格或特殊字元
- 使用了錯誤的 ID 類型

**解決方法:**
1. 確認 User ID 以 `U` 開頭
2. 確認 Group ID 以 `C` 或 `R` 開頭
3. 移除 ID 中的空格: `LINE_DEFAULT_RECIPIENT_ID="Cxxxxxxxx"` (無空格)

### 問題 4: 訊息未收到

**檢查清單:**

1. **Bot 是否已加入好友/群組?**
   ```bash
   # 確認 Bot 狀態
   curl -X GET https://api.line.me/v2/bot/info \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

2. **收件人 ID 是否正確?**
   - 透過 Webhook 事件確認正確的 User/Group ID

3. **Token 是否有效?**
   ```bash
   # 測試 Token
   curl -X POST https://api.line.me/v2/bot/message/push \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{
       "to": "Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
       "messages": [{"type": "text", "text": "Test"}]
     }'
   ```

4. **查看 MCP Server 日誌:**
   ```bash
   docker logs ai-mcp-server --tail 50 --follow
   ```

### 問題 5: 訊息發送到錯誤收件人 (群組 vs 個人)

**可能原因:**
- 關鍵字判斷不準確
- 環境變數設定錯誤

**解決方法:**

1. **明確使用關鍵字:**
   - 個人: "提醒我", "傳給我", "私訊"
   - 群組: "群組", "大家", "通知團隊"

2. **檢查環境變數:**
   ```bash
   # 確認設定
   docker exec ai-mcp-server printenv | grep LINE
   ```

3. **使用明確 API 呼叫:**
   ```bash
   # 明確指定收件人
   curl -X POST http://localhost:8000/tools/send_notification \
     -H "Content-Type: application/json" \
     -d '{
       "recipients": ["Ud45d50ec4f060587d3a42c38e67a6008"],
       "message": "Test",
       "channel": "line"
     }'
   ```

### 問題 6: Function Calling 無法正常運作

**症狀:**
- AI 不會自動呼叫 `send_notification` 工具
- 總是觸發 Fallback Mode

**檢查清單:**

1. **確認使用支援 Function Calling 的模型:**
   ```python
   # 支援的模型
   function_calling_models = [
       "gpt-3.5-turbo",
       "gpt-4",
       "gpt-4-turbo",
       "claude-3-opus",
       "claude-3-sonnet",
       "claude-3-haiku",
       "gemini-pro",
       "gemini-1.5-pro"
   ]
   ```

2. **檢查 Agent Service 日誌:**
   ```bash
   docker logs ai-agent-service --tail 100 | grep "function_call"
   ```

3. **驗證 MCP Tool Definition:**
   ```bash
   curl http://localhost:8000/tools/list | jq '.tools[] | select(.name=="send_notification")'
   ```

---

## 測試指令

### 1. 快速測試

```bash
# 測試 MCP Server 連線
curl http://localhost:8000/health

# 測試 LINE 訊息發送 (使用預設收件人)
docker exec ai-mcp-server curl -X POST http://localhost:8000/tools/send_notification \
  -H "Content-Type: application/json" \
  -d '{"message": "測試訊息", "channel": "line"}'

# 測試指定收件人
docker exec ai-mcp-server curl -X POST http://localhost:8000/tools/send_notification \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": ["Ud45d50ec4f060587d3a42c38e67a6008"],
    "message": "個人測試訊息",
    "channel": "line"
  }'
```

### 2. 完整測試流程

```bash
#!/bin/bash
# test_line_integration.sh

echo "=== LINE 整合測試 ==="

# 1. 檢查環境變數
echo -e "\n1. 檢查環境變數..."
docker exec ai-mcp-server printenv | grep LINE

# 2. 測試 MCP Server 健康狀態
echo -e "\n2. 測試 MCP Server..."
curl -s http://localhost:8000/health | jq

# 3. 測試預設收件人發送
echo -e "\n3. 測試發送到預設收件人..."
curl -s -X POST http://localhost:8000/tools/send_notification \
  -H "Content-Type: application/json" \
  -d '{"message": "預設收件人測試", "channel": "line"}' | jq

# 4. 測試個人發送
echo -e "\n4. 測試發送到個人..."
curl -s -X POST http://localhost:8000/tools/send_notification \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": ["Ud45d50ec4f060587d3a42c38e67a6008"],
    "message": "個人訊息測試",
    "channel": "line"
  }' | jq

# 5. 查看日誌
echo -e "\n5. 查看 MCP Server 日誌..."
docker logs ai-mcp-server --tail 20

echo -e "\n=== 測試完成 ==="
```

**執行測試:**
```bash
chmod +x test_line_integration.sh
./test_line_integration.sh
```

---

## 安全性注意事項

### 1. Token 保護

⚠️ **絕對不要將 Token 提交到版本控制系統**

```bash
# .gitignore
.env
.env.local
.env.prod
.env.*.local
```

### 2. 檔案權限

```bash
# 限制 .env 檔案權限
chmod 600 .env
chmod 600 .env.prod

# 僅擁有者可讀寫
ls -la .env
# 輸出: -rw------- 1 user user 1234 Nov 22 14:00 .env
```

### 3. Token 輪替

建議定期更換 LINE Channel Access Token:

1. 前往 LINE Developers Console
2. 撤銷舊 Token
3. 發行新 Token
4. 更新 `.env` 檔案
5. 重啟服務

```bash
# 更新後重啟
docker-compose restart mcp-server
```

### 4. 訊息內容驗證

在生產環境中建議加入訊息驗證:

```python
# 範例: 訊息長度限制
MAX_MESSAGE_LENGTH = 5000

if len(request.message) > MAX_MESSAGE_LENGTH:
    raise HTTPException(
        status_code=400,
        detail=f"Message too long (max {MAX_MESSAGE_LENGTH} chars)"
    )
```

### 5. Rate Limiting

LINE API 有速率限制，建議實作 Rate Limiting:

```python
# 範例: 簡單的 Rate Limiter
from datetime import datetime, timedelta

class SimpleRateLimiter:
    def __init__(self, max_requests=100, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    def allow_request(self):
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.time_window)
        self.requests = [r for r in self.requests if r > cutoff]

        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False
```

---

## 效能最佳化

### 1. 連線池

使用 `httpx.AsyncClient` 的連線池功能:

```python
# 全域 HTTP Client (已在現有程式碼中實作)
async with httpx.AsyncClient() as client:
    # 自動管理連線池
    response = await client.post(endpoint, json=payload, headers=headers)
```

### 2. 批次發送

對於多收件人，可考慮使用 LINE Multicast API:

```python
# Multicast API (最多 500 個收件人)
endpoint = "https://api.line.me/v2/bot/message/multicast"
payload = {
    "to": ["Uxxxxx1", "Uxxxxx2", ...],  # 最多 500 個
    "messages": [{"type": "text", "text": message}]
}
```

### 3. 快取機制

對於重複的收件人驗證，可加入快取:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def validate_recipient_id(recipient_id: str) -> bool:
    """驗證收件人 ID 格式"""
    return recipient_id.startswith(('U', 'C', 'R'))
```

---

## 監控與日誌

### 1. 日誌格式

MCP Server 使用結構化日誌:

```python
logger.info(f"✅ LINE message sent to {recipient_id}")
logger.error(f"❌ LINE API error: {response.status_code} - {response.text}")
```

### 2. 查看即時日誌

```bash
# 即時監控 MCP Server
docker logs ai-mcp-server --tail 50 --follow

# 過濾 LINE 相關日誌
docker logs ai-mcp-server --tail 100 | grep -i line

# 只看錯誤
docker logs ai-mcp-server --tail 100 | grep -E "ERROR|❌"
```

### 3. Prometheus 指標

系統已整合 Prometheus，可監控:

- HTTP 請求數量
- 回應時間
- 錯誤率

```bash
# 查看 MCP Server 指標
curl http://localhost:8000/metrics
```

---

## 進階功能

### 1. 富媒體訊息

LINE 支援多種訊息類型，可擴充 `send_notification`:

```python
# 範例: 發送圖片訊息
payload = {
    "to": recipient_id,
    "messages": [
        {
            "type": "image",
            "originalContentUrl": "https://example.com/image.jpg",
            "previewImageUrl": "https://example.com/preview.jpg"
        }
    ]
}

# 範例: Flex Message (彈性訊息)
payload = {
    "to": recipient_id,
    "messages": [
        {
            "type": "flex",
            "altText": "This is a Flex Message",
            "contents": {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "Hello, World!",
                            "weight": "bold",
                            "size": "xl"
                        }
                    ]
                }
            }
        }
    ]
}
```

### 2. Quick Reply

加入快速回覆按鈕:

```python
payload = {
    "to": recipient_id,
    "messages": [
        {
            "type": "text",
            "text": "請選擇操作:",
            "quickReply": {
                "items": [
                    {
                        "type": "action",
                        "action": {
                            "type": "message",
                            "label": "確認",
                            "text": "已確認"
                        }
                    },
                    {
                        "type": "action",
                        "action": {
                            "type": "message",
                            "label": "取消",
                            "text": "已取消"
                        }
                    }
                ]
            }
        }
    ]
}
```

### 3. 訊息追蹤

實作訊息發送歷史記錄:

```python
# 儲存到資料庫
async def save_notification_history(notification_id, recipients, message, result):
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO notification_history
            (notification_id, channel, recipients, message, result, sent_at)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, notification_id, "line", recipients, message, result, datetime.now())
```

---

## 相關文件

- [LINE Messaging API 官方文件](https://developers.line.biz/en/docs/messaging-api/)
- [LINE Developers Console](https://developers.line.biz/console/)
- [AI Platform 專案 README](./README.md)
- [LINE 設定指南](./LINE_SETUP_GUIDE.md)

---

## 變更歷史

| 版本 | 日期 | 變更內容 |
|------|------|---------|
| 1.0.0 | 2025-11-22 | 初版發布 |

---

## 授權

本文件屬於 AI Platform 專案的一部分，遵循專案授權條款。
