# AI Platform Troubleshooting Guide

Complete guide covering all problems encountered and their solutions during development and deployment.

**Last Updated:** 2025-10-17
**Version:** 1.0.0

---

## Table of Contents

1. [Email Functionality Issues](#1-email-functionality-issues)
2. [Web UI Display Problems](#2-web-ui-display-problems)
3. [SMTP Configuration](#3-smtp-configuration)
4. [Natural Language Processing](#4-natural-language-processing)
5. [Claude Function Calling](#5-claude-function-calling)

---

## 1. Email Functionality Issues

### Problem 1.1: Agent Not Sending Emails from Web UI

**Symptom:**
- User clicks "發送郵件給 test@example.com 主旨是測試" example in Web UI
- Agent responds with text but doesn't actually send email
- No email tool execution visible in response

**Root Cause:**
The Web UI's example task buttons didn't include email sending as an example, making it non-obvious to users how to trigger email functionality.

**Solution:**

**File Modified:** `/path/to/your/ai_platform/services/web-ui/i18n.py`

Updated example tasks to prioritize email sending:

```python
# Chinese (zh-TW)
"example_1": "發送郵件給 test@example.com 主旨是測試",
"example_2": "創建任務：完成季度報告",
"example_3": "搜尋關於AI的文檔",

# English
"example_1": "send email to test@example.com with subject Test",
"example_2": "create task: Complete quarterly report",
"example_3": "search for AI documentation",

# Vietnamese
"example_1": "gửi email đến test@example.com với tiêu đề Test",
"example_2": "tạo nhiệm vụ: Hoàn thành báo cáo quý",
"example_3": "tìm kiếm tài liệu về AI",
```

**Commands to Apply Fix:**

```bash
# Rebuild web-ui container (NOT just restart!)
docker compose build web-ui && docker compose up -d web-ui

# Verify changes were applied
docker compose exec web-ui cat /app/i18n.py | grep -A 5 '"example_1"'
```

**Key Learning:** Always use `docker compose build` when code changes are made. Using `docker compose restart` only restarts the container with old code still in the image.

---

### Problem 1.2: Mock Email vs Real Email Sending

**Symptom:**
- Agent reports "Email sent successfully"
- User doesn't receive any email
- MCP server returns mock responses instead of sending real emails

**Root Cause:**
The MCP server's `send_email` function was initially implemented with mock mode only, returning simulated responses without actually sending emails via SMTP.

**Solution:**

**File Modified:** `/path/to/your/ai_platform/services/mcp-server/main.py:933-999`

Updated `send_email` endpoint to support real SMTP:

```python
@app.post("/tools/send_email")
async def send_email(request: SendEmailRequest):
    """發送郵件"""
    try:
        email_id = f"EMAIL-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Check if SMTP is configured
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        smtp_from = os.getenv("SMTP_FROM_EMAIL", smtp_username)

        if smtp_server and smtp_username and smtp_password:
            # Send real email via SMTP
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg['From'] = smtp_from
            msg['To'] = ', '.join(request.to)
            msg['Subject'] = request.subject
            msg.attach(MIMEText(request.body, 'plain'))

            try:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
                server.quit()

                logger.info(f"✅ Email sent successfully to {request.to}")

                return {
                    "email_id": email_id,
                    "to": request.to,
                    "subject": request.subject,
                    "status": "sent",
                    "sent_at": datetime.now().isoformat(),
                    "method": "smtp"
                }
            except Exception as smtp_error:
                logger.error(f"SMTP error: {smtp_error}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to send email: {str(smtp_error)}"
                )
        else:
            # Fallback to mock mode
            logger.warning("SMTP not configured - returning mock response")
            return {
                "email_id": email_id,
                "to": request.to,
                "subject": request.subject,
                "status": "sent (simulated)",
                "sent_at": datetime.now().isoformat(),
                "method": "mock",
                "note": "Configure SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD to send real emails"
            }

    except Exception as e:
        logger.error(f"Send email error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Key Features:**
1. **Automatic fallback:** If SMTP not configured, returns mock response
2. **Error handling:** Catches and logs SMTP errors
3. **Logging:** Clear success/failure indicators in logs
4. **Method indicator:** Returns `method: "smtp"` or `method: "mock"` so you know which was used

---

## 2. Web UI Display Problems

### Problem 2.1: KeyError When Displaying Execution Steps

**Symptom:**
```
Execution failed: 'result'
Step 2: intent_detection Execution failed: 'result'
```

**Root Cause:**
The Web UI blindly accessed `step["result"]` for all step types, but different steps have different key structures:
- `intent_detection` steps have: `tool`, `arguments`, `status`
- `tool_execution` steps have: `result`, `status`
- `llm_call` steps have: `result`, `status`

**Solution:**

**File Modified:** `/path/to/your/ai_platform/services/web-ui/app.py:275-306`

Added conditional logic to handle different step types:

```python
with st.expander(get_text("view_steps", lang), expanded=True):
    for i, step in enumerate(result["steps"], 1):
        # Map status to icon
        status = step.get("status", "unknown")
        if status == "success":
            status_icon = "✅"
        elif status == "failed":
            status_icon = "❌"
        elif status in ["detected", "executing"]:
            status_icon = "🔍"
        else:
            status_icon = "ℹ️"

        st.write(f"{status_icon} **{get_text('step', lang)} {i}: {step['step']}**")

        # Display step details based on what's available
        if "result" in step:
            # Steps with result (tool_execution, llm_call, etc.)
            if isinstance(step["result"], dict):
                st.json(step["result"])
            else:
                st.caption(step["result"])
        elif "tool" in step:
            # Steps with tool info (intent_detection)
            st.caption(f"🔧 Tool: **{step['tool']}**")
            if "arguments" in step:
                with st.container():
                    st.caption("Arguments:")
                    st.json(step["arguments"])
        elif "error" in step:
            # Steps with errors
            st.error(f"❌ Error: {step['error']}")
```

**Commands to Apply Fix:**

```bash
docker compose build web-ui && docker compose up -d web-ui
```

---

### Problem 2.2: Nested Expanders Error

**Symptom:**
```
Execution failed: Expanders may not be nested inside other expanders
```

**Root Cause:**
Streamlit doesn't allow nested `st.expander()` components. The code was trying to create an expander for "View arguments" inside the "view_steps" expander.

**Solution:**

**File Modified:** `/path/to/your/ai_platform/services/web-ui/app.py:300-304`

Replaced nested expander with simple container:

```python
# Before (broken):
with st.expander("View arguments"):
    st.json(step["arguments"])

# After (working):
with st.container():
    st.caption("Arguments:")
    st.json(step["arguments"])
```

**Debugging Technique:**
When encountering Streamlit errors, check the component hierarchy. Streamlit has strict rules about nesting certain components.

---

### Problem 2.3: Model Selection Confusion

**Symptom:**
Users select models that require API keys (like claude-3-sonnet) without realizing they need configuration, leading to authentication errors.

**Solution:**

**File Modified:** `/path/to/your/ai_platform/services/web-ui/app.py:74-78`

Added visual indicators for model requirements:

```python
if model_choice == "qwen2.5":
    st.success("✅ 本地模型 - 無需API金鑰")
else:
    st.warning("⚠️ 需要API金鑰！建議使用 qwen2.5")
```

**Result:** Users now see clear warnings before selecting models that require API keys.

---

## 3. SMTP Configuration

### Problem 3.1: Gmail SMTP Setup

**Objective:** Configure real email sending via Gmail SMTP.

**Step-by-Step Solution:**

#### Step 1: Generate Gmail App Password

1. Go to [Google Account Security Settings](https://myaccount.google.com/security)
2. Enable 2-Factor Authentication (required for App Passwords)
3. Navigate to **Security** → **2-Step Verification** → **App passwords**
4. Create new app password for "Mail" on "Other device"
5. Copy the 16-character password (example: `xxxx xxxx xxxx xxxx`)

#### Step 2: Update Environment Variables

**File Modified:** `/path/to/your/ai_platform/.env`

Add SMTP configuration:

```bash
# SMTP Email Configuration (for real email sending)
# Gmail SMTP example
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password-here
SMTP_FROM_EMAIL=your-email@gmail.com
```

**Security Note:** The App Password shown here is for demonstration. In production:
- Use environment-specific `.env` files
- Never commit `.env` to git (add to `.gitignore`)
- Rotate passwords regularly
- Use secrets management (AWS Secrets Manager, HashiCorp Vault, etc.)

#### Step 3: Map Environment Variables to Container

**File Modified:** `/path/to/your/ai_platform/docker-compose.yml:139-143`

Add SMTP variables to `mcp-server` service:

```yaml
mcp-server:
  environment:
    POSTGRES_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
    QDRANT_URL: http://qdrant:6333
    REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379
    SMTP_SERVER: ${SMTP_SERVER}
    SMTP_PORT: ${SMTP_PORT}
    SMTP_USERNAME: ${SMTP_USERNAME}
    SMTP_PASSWORD: ${SMTP_PASSWORD}
    SMTP_FROM_EMAIL: ${SMTP_FROM_EMAIL}
```

**Key Learning:** Environment variables in `.env` must be explicitly mapped in `docker-compose.yml` to be accessible inside containers.

#### Step 4: Restart Services

```bash
# Recreate mcp-server with new environment variables
docker compose up -d mcp-server

# Verify environment variables are loaded
docker compose exec mcp-server printenv | grep SMTP
```

**Expected Output:**
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password-here
SMTP_FROM_EMAIL=your-email@gmail.com
```

#### Step 5: Test Email Sending

```bash
# Test via Web UI
# 1. Open http://localhost:8501
# 2. Go to 🤖 Agent任務
# 3. Click "發送郵件給 test@example.com 主旨是測試"
# 4. Check email inbox

# Or test via API
curl -X POST http://localhost:8002/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "發送郵件給 your-email@gmail.com 主旨是測試 內容是Hello from AI Platform",
    "model": "qwen2.5"
  }'
```

#### Step 6: Verify in Logs

```bash
# Check MCP server logs for SMTP confirmation
docker compose logs mcp-server --tail 20 | grep "Email sent"
```

**Success Output:**
```
ai-mcp-server  | INFO:main:✅ Email sent successfully to ['your-email@gmail.com']
```

---

### Problem 3.2: Other SMTP Providers

The system supports any SMTP provider. Here are common configurations:

#### SendGrid (Production Recommended)

```bash
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=SG.your_sendgrid_api_key_here
SMTP_FROM_EMAIL=noreply@yourdomain.com
```

#### AWS SES

```bash
SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=your_ses_smtp_username
SMTP_PASSWORD=your_ses_smtp_password
SMTP_FROM_EMAIL=verified@yourdomain.com
```

#### Outlook/Office 365

```bash
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=your_email@outlook.com
SMTP_PASSWORD=your_password
SMTP_FROM_EMAIL=your_email@outlook.com
```

---

## 4. Natural Language Processing

### Problem 4.1: Specific Keywords Required for Email

**Symptom:**
User prompt: "請幫我寫一封信給 John Doe, email是 your-email@gmail.com, 表達我對他的關心跟祝福, 我是Jerry"

Agent response: Just generates text, doesn't send email

**Root Cause:**
The agent's keyword detection only looked for "發送郵件" or "send email", but not natural variations like "寫一封信" (write a letter).

**Solution:**

**File Modified:** `/path/to/your/ai_platform/services/agent-service/main.py:161-234`

#### Extended Keyword List

```python
def detect_tool_intent(task: str) -> Optional[tuple]:
    """Fallback: Detect tool intent from user message when function calling not supported"""
    import re
    task_lower = task.lower()

    # First, check if there's an email address in the text
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', task)

    # Email sending patterns - now includes context-based detection
    email_keywords = [
        "發送郵件", "发送邮件", "send email", "寄信", "傳送email",
        "寫一封信", "写一封信", "write email", "email to", "mail to",
        "寄email", "送信", "幫我寫信", "帮我写信", "send mail",
        "發email", "发email"
    ]

    # Context-based email indicators (even without direct "send" words)
    context_indicators = [
        "contact", "聯絡", "联络", "通知", "告知", "告诉", "inform",
        "reach out", "get in touch", "let them know", "告訴",
        "問候", "问候", "祝福", "關心", "关心"
    ]

    has_email_keyword = any(keyword in task_lower for keyword in email_keywords)
    has_context_indicator = any(indicator in task_lower for indicator in context_indicators)

    # Trigger email if: explicit keyword OR (email address + context indicator)
    if has_email_keyword or (emails and has_context_indicator):
        # Process email...
```

#### Intelligent Content Extraction

```python
        if emails:
            # Try to extract subject and body
            subject = "來自AI助手的訊息"
            body = task

            # Try to extract the message content after "表達" or similar keywords
            content_keywords = [
                "表達", "表达", "告訴", "告诉", "說", "说",
                "內容", "内容", "message", "tell them"
            ]
            for keyword in content_keywords:
                if keyword in task:
                    parts = task.split(keyword, 1)
                    if len(parts) > 1:
                        content = parts[1].strip()
                        # Remove trailing sender info like "我是XXX"
                        content = re.sub(r',?\s*我是.*$', '', content)
                        if content:
                            body = content

            # Look for subject keywords
            for keyword in ["主旨", "主題", "標題", "subject", "題目"]:
                if keyword in task_lower:
                    parts = task.split(keyword, 1)
                    if len(parts) > 1:
                        subject_match = re.search(
                            r'[是:：]?\s*[「『"]?([^」』"，,。]+)',
                            parts[1]
                        )
                        if subject_match:
                            subject = subject_match.group(1).strip()

            # If no explicit subject, try to infer from context
            if subject == "來自AI助手的訊息" and "關心" in task:
                subject = "問候與祝福"

            return ("send_email", {
                "to": emails,
                "subject": subject,
                "body": body
            })
```

**Commands to Apply Fix:**

```bash
docker compose build agent-service && docker compose up -d agent-service

# Wait for service to be healthy
sleep 5 && docker compose ps agent-service

# Test with natural language
curl -X POST http://localhost:8002/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "請幫我寫一封信給 John Doe, email是 your-email@gmail.com, 表達我對他的關心跟祝福",
    "model": "qwen2.5"
  }'
```

**Result:**
- Email successfully sent
- Subject: "問候與祝福" (inferred from context)
- Body: "我對他的關心跟祝福" (extracted content)

---

### Problem 4.2: Context-Aware Detection Without Keywords

**Symptom:**
User wants: "John at jerry@gmail.com should be informed about the meeting"

But agent doesn't recognize this as email request because no "send email" keyword.

**Solution:**

The keyword fallback approach (used by qwen2.5) has limitations. For true context-aware understanding, use LLM function calling.

**Model Comparison:**

| Feature | qwen2.5 (Keyword Fallback) | gpt-3.5-turbo / claude-3-sonnet (Function Calling) |
|---------|---------------------------|--------------------------------------------------|
| **Cost** | Free | ~$0.001 per request |
| **Speed** | < 500ms | 1-3s |
| **Context Understanding** | Limited (needs keywords or patterns) | Excellent (understands natural language) |
| **Subject Generation** | Basic extraction | Smart, contextual generation |
| **Body Composition** | Uses prompt as-is | Composes professional text |

**Recommendation:**
- **Development/Testing:** Use `qwen2.5` (free, fast)
- **Production:** Use `gpt-3.5-turbo` or `claude-3-sonnet` (better UX)

**Test Command (GPT-3.5):**

```bash
curl -X POST http://localhost:8002/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "John at your-email@gmail.com should be informed about the meeting tomorrow at 2pm",
    "model": "gpt-3.5-turbo"
  }'
```

**GPT-3.5 Response:**
- Automatically understands "should be informed" = send email
- Extracts: recipient, meeting details
- Generates subject: "Meeting Reminder: Tomorrow at 2pm"
- Composes professional email body
- Sends via SMTP

---

## 5. Claude Function Calling

### Problem 5.1: Claude 400 Bad Request with Tools

**Symptom:**
```
LLM錯誤: Client error '400 Bad Request' for url 'https://api.anthropic.com/v1/messages'
```

- Claude chat works fine without tools
- Claude with tools returns 400 error
- No detailed error message from Anthropic API

**Debugging Process:**

#### Step 1: Verify Claude Chat Works Without Tools

```bash
# Test simple chat
curl -X POST http://localhost:8002/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "model": "claude-3-sonnet"
  }'
```

**Result:** ✅ Works perfectly
**Conclusion:** API key valid, model accessible. Problem is specific to tool calling.

#### Step 2: Check LiteLLM Version and Claude Support

```bash
# Check LiteLLM container
docker compose ps litellm

# Check LiteLLM logs
docker compose logs litellm --tail 100 | grep -i claude
```

**Finding:** LiteLLM version 1.40.0 supports Claude tool calling

#### Step 3: Inspect Actual Request Payload

```bash
# Clear logs and make fresh request
docker compose restart litellm
sleep 15

# Make tool calling request
curl -X POST http://localhost:8002/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Send email to test@example.com",
    "model": "claude-3-sonnet"
  }'

# Check detailed logs
docker compose logs litellm --tail 200 | grep -A 20 "tools"
```

**Finding:** Tools are being sent in correct OpenAI format:
```python
tools=[
    {
        'type': 'function',
        'function': {
            'name': 'create_task',
            'description': '創建項目任務',
            'parameters': {
                'type': 'object',
                'properties': {
                    'due_date': {'type': 'datetime'},  # ❌ INVALID!
                    'title': {'type': 'string'}
                }
            }
        }
    }
]
```

**Root Cause Identified:** Parameter type `'datetime'` is not a valid JSON Schema type! Claude's API rejects it.

---

### Problem 5.2: Invalid JSON Schema Types in Tool Definitions

**Root Cause:**

The MCP server defines tools with custom types that aren't valid in JSON Schema:
- `datetime` (should be `string`)
- `float` (should be `number`)

When LiteLLM tries to convert these to Claude's tool format, Anthropic API rejects them with 400 error.

**Solution:**

**File Modified:** `/path/to/your/ai_platform/services/agent-service/main.py:79-117`

Add type mapping in `convert_tools_to_functions()`:

```python
def convert_tools_to_functions(mcp_tools: List[Dict]) -> List[Dict]:
    """Convert MCP tools to OpenAI function calling format"""
    functions = []
    for tool in mcp_tools:
        # Create properties from parameters
        properties = {}
        required = []

        # Map of parameter types to valid JSON Schema types
        type_mapping = {
            "datetime": "string",  # Claude doesn't support datetime type
            "float": "number",      # Map float to number for consistency
        }

        for param_name, param_type in tool.get("parameters", {}).items():
            # Convert invalid types to valid JSON Schema types
            mapped_type = type_mapping.get(param_type, param_type)
            properties[param_name] = {"type": mapped_type}

            # Add description for datetime fields
            if param_type == "datetime":
                properties[param_name]["description"] = "ISO 8601 datetime string"

            # Make certain parameters required
            if param_name in ["query", "to", "subject", "body", "title", "message"]:
                required.append(param_name)

        function_def = {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
        functions.append(function_def)

    return functions
```

**Key Changes:**
1. **Type mapping dictionary** converts invalid types to valid ones
2. **Description annotation** for datetime fields explains format
3. **Preserves all other types** that are already valid

---

### Problem 5.3: Model Name Aliasing

**Additional Issue Found:**

The agent was using model alias `"claude-3-sonnet"` instead of full model name `"claude-3-5-sonnet-20240620"`, which LiteLLM needs for proper tool format conversion.

**Solution:**

**File Modified:** `/path/to/your/ai_platform/services/agent-service/main.py:259-271`

Add model name mapping:

```python
@app.post("/agent/execute", response_model=AgentResponse)
async def execute_agent(request: AgentRequest):
    """執行Agent任務 - 支持工具調用"""
    try:
        steps = []

        # Map model aliases to actual model names for LiteLLM
        # LiteLLM needs the actual model name to properly handle tool calling
        model_name_map = {
            "claude-3-sonnet": "claude-3-5-sonnet-20240620",
            "claude-3-opus": "claude-3-opus-20240229",
            "gpt-3.5-turbo": "gpt-3.5-turbo",
            "gpt-4": "gpt-4",
            "gpt-4-turbo": "gpt-4-turbo",
            "qwen2.5": "qwen2.5"
        }

        # Get actual model name for API calls
        actual_model = model_name_map.get(request.model, request.model)
```

Then use `actual_model` in LLM payload:

```python
llm_payload = {
    "model": actual_model,  # Use actual model name for LiteLLM
    "messages": messages,
    "temperature": 0.7,
    "max_tokens": 2000
}
```

---

### Final Solution: Complete Fix

**Commands to Apply Fix:**

```bash
# Rebuild agent-service with both fixes
docker compose build agent-service && docker compose up -d agent-service

# Wait for service to be healthy
sleep 10 && docker compose ps agent-service
```

**Test Claude Function Calling:**

```bash
# Test context-aware email with Claude
curl -X POST http://localhost:8002/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "John at your-email@gmail.com should be informed about the meeting tomorrow at 2pm",
    "model": "claude-3-sonnet"
  }'
```

**✅ Expected Success Response:**

```json
{
  "result": "Great! I've sent an email to John...",
  "steps": [
    {
      "step": "fetch_tools",
      "result": "Found 28 tools",
      "status": "success"
    },
    {
      "step": "tool_call_1",
      "tool": "send_email",
      "arguments": {
        "to": ["your-email@gmail.com"],
        "subject": "Meeting Reminder: Tomorrow at 2pm",
        "body": "Dear John,\n\nThis is a friendly reminder about the meeting scheduled for tomorrow at 2pm..."
      },
      "status": "executing"
    },
    {
      "step": "tool_result_1",
      "tool": "send_email",
      "result": {
        "email_id": "EMAIL-20251017025355",
        "to": ["your-email@gmail.com"],
        "subject": "Meeting Reminder: Tomorrow at 2pm",
        "status": "sent",
        "sent_at": "2025-10-17T02:53:57.530600",
        "method": "smtp"
      },
      "status": "success"
    }
  ],
  "metadata": {
    "agent_type": "general",
    "model_used": "claude-3-sonnet",
    "iterations": 2,
    "tokens_used": 3615
  }
}
```

**Verify Email Received:**

```bash
# Check MCP server logs
docker compose logs mcp-server --tail 5 | grep "Email sent"
```

**Success Output:**
```
ai-mcp-server  | INFO:main:✅ Email sent successfully to ['your-email@gmail.com']
```

---

## Debugging Best Practices

### 1. Docker Container Management

**Always rebuild after code changes:**
```bash
# ❌ Wrong - only restarts, doesn't apply code changes
docker compose restart service-name

# ✅ Correct - rebuilds image with new code
docker compose build service-name && docker compose up -d service-name
```

**Verify changes were applied:**
```bash
# Check file contents inside container
docker compose exec service-name cat /path/to/file

# Check environment variables
docker compose exec service-name printenv | grep VARIABLE_NAME
```

### 2. Log Analysis

**View real-time logs:**
```bash
# Follow logs from specific service
docker compose logs -f service-name

# Last N lines
docker compose logs service-name --tail 50

# Grep for specific patterns
docker compose logs service-name | grep -i "error\|warning"
```

**Search across all services:**
```bash
# Find which service has errors
docker compose logs | grep -i "error" | head -20
```

### 3. Service Health Checks

**Check service status:**
```bash
# View all services
docker compose ps

# Check specific service
docker compose ps service-name

# View health status
docker compose ps --format json | jq '.[] | {name: .Name, status: .Status}'
```

**Test service endpoints:**
```bash
# Health check
curl http://localhost:8002/health

# Service info
curl http://localhost:8002/
```

### 4. API Testing

**Test with curl:**
```bash
# POST with JSON
curl -X POST http://localhost:8002/agent/execute \
  -H "Content-Type: application/json" \
  -d '{"task":"your task","model":"gpt-3.5-turbo"}'

# Pretty print response
curl -X POST http://localhost:8002/agent/execute \
  -H "Content-Type: application/json" \
  -d '{"task":"your task","model":"gpt-3.5-turbo"}' | jq '.'
```

**Test response time:**
```bash
time curl -X POST http://localhost:8002/agent/execute \
  -H "Content-Type: application/json" \
  -d '{"task":"your task","model":"qwen2.5"}'
```

### 5. Incremental Testing

**Test in isolation:**
1. Test individual components first
2. Test integration between components
3. Test end-to-end workflow

**Example: Testing email functionality**

```bash
# Step 1: Test MCP server directly
curl -X POST http://localhost:8001/tools/send_email \
  -H "Content-Type: application/json" \
  -d '{"to":["test@example.com"],"subject":"Test","body":"Hello"}'

# Step 2: Test agent service with simple model
curl -X POST http://localhost:8002/agent/execute \
  -H "Content-Type: application/json" \
  -d '{"task":"發送郵件給 test@example.com 主旨是測試","model":"qwen2.5"}'

# Step 3: Test with GPT function calling
curl -X POST http://localhost:8002/agent/execute \
  -H "Content-Type: application/json" \
  -d '{"task":"Send email to test@example.com","model":"gpt-3.5-turbo"}'

# Step 4: Test with Claude function calling
curl -X POST http://localhost:8002/agent/execute \
  -H "Content-Type: application/json" \
  -d '{"task":"Send email to test@example.com","model":"claude-3-sonnet"}'
```

---

## Common Issues Quick Reference

### Issue: "Docker compose restart doesn't apply changes"

**Solution:** Use `docker compose build` to rebuild the image

```bash
docker compose build service-name && docker compose up -d service-name
```

---

### Issue: "Environment variables not loading in container"

**Solution:** Check three places:

1. **`.env` file** - variable defined
2. **`docker-compose.yml`** - variable mapped
3. **Container** - variable accessible

```bash
# Verify mapping in docker-compose.yml
grep -A 10 "service-name:" docker-compose.yml

# Recreate container
docker compose up -d service-name

# Verify inside container
docker compose exec service-name printenv | grep VARIABLE_NAME
```

---

### Issue: "400 Bad Request from LLM API"

**Debugging steps:**

1. **Test without tools**
```bash
curl -X POST http://localhost:8002/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","model":"your-model"}'
```

2. **Check LiteLLM logs**
```bash
docker compose logs litellm --tail 100 | grep -i "error\|400"
```

3. **Verify API key**
```bash
docker compose exec litellm printenv | grep API_KEY
```

4. **Check tool definitions**
- Invalid JSON Schema types?
- Missing required fields?
- Proper format conversion?

---

### Issue: "Email reports success but not received"

**Debugging steps:**

1. **Check MCP server logs**
```bash
docker compose logs mcp-server | grep -i "email\|smtp"
```

2. **Verify SMTP configuration**
```bash
docker compose exec mcp-server printenv | grep SMTP
```

3. **Check email method**
Look for `"method": "smtp"` or `"method": "mock"` in response

4. **Test SMTP directly**
```bash
curl -X POST http://localhost:8001/tools/send_email \
  -H "Content-Type: application/json" \
  -d '{"to":["your-email@gmail.com"],"subject":"Test","body":"Test"}'
```

---

### Issue: "Streamlit UI errors"

**Common causes:**
- Nested expanders
- Missing keys in dictionaries
- Type mismatches

**Solution:** Check Streamlit logs
```bash
docker compose logs web-ui --tail 50
```

---

## Performance Optimization

### Model Selection for Production

| Use Case | Recommended Model | Reason |
|----------|------------------|--------|
| **Simple keyword-based tasks** | qwen2.5 | Free, fast (< 500ms) |
| **Context-aware tasks** | gpt-3.5-turbo | Good balance of cost/performance |
| **Complex reasoning** | gpt-4 or claude-3-sonnet | Best quality |
| **High volume** | gpt-3.5-turbo | Most cost-effective |

### Caching Strategy

LiteLLM has built-in Redis caching:

```yaml
litellm_settings:
  cache: true
  cache_params:
    type: redis
    host: redis
    port: 6379
    password: os.environ/REDIS_PASSWORD
```

**Benefits:**
- Faster responses for repeated queries
- Reduced API costs
- Better rate limit management

### Monitoring

Check service metrics:

```bash
# Prometheus metrics
curl http://localhost:8002/metrics

# LiteLLM health
curl http://localhost:4000/health/readiness

# Agent service health
curl http://localhost:8002/health
```

---

## Security Considerations

### API Key Management

**❌ Never:**
- Commit API keys to git
- Share API keys in documentation
- Use production keys in development

**✅ Always:**
- Use environment variables
- Rotate keys regularly
- Use different keys per environment
- Monitor API usage

### Email Security

**Best practices:**
- Use App Passwords (not account passwords)
- Validate recipient addresses
- Sanitize email content
- Rate limit email sending
- Log all email operations

### SMTP Security

**Recommended:**
- Use TLS/STARTTLS
- Authenticate properly
- Monitor for abuse
- Implement sending limits

---

## Additional Resources

### Documentation

- **Project README:** `/README.md`
- **Database Schema:** `/DATABASE_SCHEMA.md`
- **Deployment Guide:** `/DEPLOYMENT_GUIDE.md`
- **Context-Aware Agent:** `/CONTEXT_AWARE_AGENT_GUIDE.md`
- **SMTP Configuration:** `/SMTP_CONFIGURATION_GUIDE.md`

### Web UI Access

All documentation available at: **http://localhost:8501** → 📚 Documentation tab

### API Endpoints

- **Agent Service:** http://localhost:8002
- **MCP Server:** http://localhost:8001
- **LiteLLM Proxy:** http://localhost:4000
- **Web UI:** http://localhost:8501

---

## Support

If you encounter issues not covered in this guide:

1. **Check logs:** `docker compose logs service-name`
2. **Verify configuration:** Review `.env` and `docker-compose.yml`
3. **Test incrementally:** Isolate the problem component
4. **Review this guide:** Search for similar issues

---

**End of Troubleshooting Guide**

*This guide is continuously updated based on production issues and solutions. Last major update: 2025-10-17*
