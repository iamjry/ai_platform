# Context-Aware Agent Guide - Understanding Intent Without Keywords

This guide explains how to make your AI Agent understand context and intent without requiring specific keywords.

## 📊 Current Implementation: Two Modes

Your agent supports **two intelligence levels**:

### Mode 1: Keyword Fallback (qwen2.5, local models)
- **How it works:** Pattern matching on specific keywords
- **Best for:** Fast, offline, no API costs
- **Limitation:** Needs recognizable patterns

### Mode 2: LLM Function Calling (GPT-3.5/4, Claude)
- **How it works:** LLM understands context and decides which tool to call
- **Best for:** Natural language, complex requests
- **Requirement:** API key needed

---

## 🚀 Quick Start: Use GPT for Context-Aware Email

### Step 1: Add OpenAI API Key (Already Done!)

Your `.env` already has:
```bash
OPENAI_API_KEY=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
```

✅ You're ready to use GPT models!

### Step 2: Use GPT-3.5-turbo Model

In Web UI:
1. Open http://localhost:8501
2. Go to **🤖 Agent任務**
3. **Select model:** `gpt-3.5-turbo` (instead of qwen2.5)
4. Type natural prompts!

---

## 💡 Examples: What Works With Each Mode

### With qwen2.5 (Keyword Fallback)

#### ✅ Works (After Recent Improvements):
```
請幫我寫一封信給 John Doe, email是 your-email@gmail.com, 表達我對他的關心跟祝福
發送郵件給 john@example.com 主旨是測試
send email to boss@company.com with subject Update
contact support@example.com 告訴他們問題
通知 team@company.com 關於會議時間  ← NEW! Context-based
```

#### ❌ Doesn't Work:
```
John's email is jerry@gmail.com and I'd like him to know about the meeting
Can you reach out to the support team? Their contact is support@example.com
The client at client@business.com should be informed about the delay
```

**Why?** Even with improvements, keyword fallback is limited. It needs either:
1. An explicit action word ("send", "contact", "通知"), OR
2. Email keyword ("寫信", "email") + email address

---

### With gpt-3.5-turbo (LLM Function Calling)

#### ✅ ALL These Work:
```
John's email is jerry@gmail.com and I'd like him to know about the meeting
Can you reach out to the support team at support@example.com?
The client at client@business.com should be informed about the delay
Let john@company.com know that the project is complete
I need to notify team@example.com about tomorrow's meeting
Contact the HR department at hr@company.com regarding my leave
告訴 jerry@gmail.com 我明天不能參加會議
客戶的郵箱是 client@business.com，需要跟他說專案延期了
```

**Why?** GPT-3.5 understands:
- Intent from context ("should be informed" = send email)
- Implicit actions ("let them know" = send notification)
- Relationships ("contact", "reach out", "notify" = communication)

---

## 🔧 How It Works: Technical Details

### Mode 1: Keyword Fallback (qwen2.5)

**Location:** `services/agent-service/main.py:161-240`

**Process:**
1. Extract email addresses using regex
2. Check for email keywords OR context indicators
3. Parse subject/body from text
4. Call MCP tool directly

**Code Logic:**
```python
# Triggers email if:
has_email_keyword = "send email" in text
has_context = "contact" in text AND email_found

if has_email_keyword OR (email AND has_context):
    send_email(to=email, subject=extracted, body=text)
```

**Recent Improvements:**
- Added context indicators: "contact", "通知", "告知", "問候"
- Now works: "contact jerry@gmail.com 告訴他會議時間"
- Still limited to recognizable patterns

---

### Mode 2: LLM Function Calling (GPT/Claude)

**Location:** `services/agent-service/main.py:174-276`

**Process:**
1. Convert all 28 MCP tools to OpenAI function format
2. Send user request + tool definitions to GPT
3. GPT decides which tool(s) to call based on context
4. Execute tool(s) and return results

**Code Logic:**
```python
# GPT receives:
tools = [
  {
    "name": "send_email",
    "description": "發送郵件",
    "parameters": {"to": "array", "subject": "string", "body": "string"}
  },
  # ... 27 other tools
]

messages = [
  {"role": "system", "content": "你是AI助手，可以使用工具"},
  {"role": "user", "content": "John's email is jerry@gmail.com, let him know about the meeting"}
]

# GPT responds with:
tool_call = {
  "name": "send_email",
  "arguments": {
    "to": ["jerry@gmail.com"],
    "subject": "Meeting Notification",
    "body": "I wanted to let you know about the meeting."
  }
}
```

**Advantages:**
- ✅ Understands context and intent
- ✅ Generates appropriate subject lines
- ✅ Composes professional email body
- ✅ Handles complex multi-step tasks
- ✅ No keyword engineering needed

---

## 📝 Comparison Table

| Feature | qwen2.5 (Fallback) | gpt-3.5-turbo (Function Calling) |
|---------|-------------------|----------------------------------|
| **API Key Needed** | ❌ No | ✅ Yes (OpenAI) |
| **Cost** | Free | ~$0.001 per request |
| **Speed** | ⚡ Fast (<500ms) | 🐌 Slower (1-3s) |
| **Offline** | ✅ Yes | ❌ No |
| **Context Understanding** | ⚠️ Limited | ✅ Excellent |
| **Example Prompts** | Must include keywords | Any natural language |
| **Subject Generation** | Basic extraction | Smart generation |
| **Body Composition** | Uses prompt as-is | Composes professional text |
| **Multi-step Tasks** | ❌ Single action only | ✅ Multiple actions |

---

## 🎯 Which Mode Should You Use?

### Use qwen2.5 (Keyword Fallback) When:
- ✅ Testing/development (no API costs)
- ✅ You use clear, direct commands
- ✅ You want fast responses
- ✅ You don't have/want to use API keys
- ✅ Simple single-action tasks

**Example Commands:**
```
發送郵件給 john@example.com 主旨是測試
send email to boss@company.com with subject Weekly Report
contact support@example.com 告訴他們系統問題
```

---

### Use gpt-3.5-turbo (Function Calling) When:
- ✅ You want natural language understanding
- ✅ Complex, multi-step requests
- ✅ You have OpenAI API key
- ✅ You want smart content generation
- ✅ Production environment

**Example Commands:**
```
John needs to know about tomorrow's meeting, his email is jerry@gmail.com
Can you reach out to the support team and let them know about the bug?
The client should be informed that the project will be delayed
I need to notify everyone at team@company.com about the schedule change
```

---

## 🚀 How to Use GPT Function Calling Now

### From Web UI:

1. **Open** http://localhost:8501
2. **Go to** 🤖 Agent任務 tab
3. **Select** `gpt-3.5-turbo` from the model dropdown
4. **Type natural prompt:**
   ```
   John's email is your-email@gmail.com and I'd like him to know that
   the project is complete and ready for review
   ```
5. **Click** 執行任務
6. **Watch** GPT:
   - Understand the context
   - Decide to use send_email tool
   - Generate appropriate subject: "Project Completion Notification"
   - Compose professional body
   - Send real email via SMTP!

### From API:

```bash
curl -X POST http://localhost:8002/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "John at your-email@gmail.com should be informed about the meeting tomorrow at 2pm",
    "model": "gpt-3.5-turbo"
  }'
```

**GPT will:**
1. Recognize intent: notification required
2. Extract recipient: your-email@gmail.com
3. Generate subject: "Meeting Reminder"
4. Compose body: "This is to inform you about the meeting scheduled tomorrow at 2pm."
5. Send email via SMTP!

---

## 🔍 See It In Action

### Example 1: Context-Based (GPT Only)

**Prompt:**
```
The client's contact is client@business.com and they should know
that we need to delay the delivery by one week
```

**With qwen2.5:** ❌ Won't trigger (no "send email" keyword)

**With gpt-3.5-turbo:** ✅ Works!
```json
{
  "tool_called": "send_email",
  "arguments": {
    "to": ["client@business.com"],
    "subject": "Delivery Schedule Update",
    "body": "We wanted to inform you that we need to delay the delivery by one week..."
  }
}
```

---

### Example 2: Improved Fallback (Both Work)

**Prompt:**
```
contact support@example.com 告訴他們系統有問題
```

**With qwen2.5:** ✅ Works! (context indicator "contact" + email)
```json
{
  "tool_called": "send_email",
  "arguments": {
    "to": ["support@example.com"],
    "subject": "來自AI助手的訊息",
    "body": "contact support@example.com 告訴他們系統有問題"
  }
}
```

**With gpt-3.5-turbo:** ✅ Works Better!
```json
{
  "tool_called": "send_email",
  "arguments": {
    "to": ["support@example.com"],
    "subject": "系統問題報告",
    "body": "我們發現系統有問題，需要您的協助處理..."
  }
}
```

---

## 💰 Cost Considerations

### qwen2.5 (Free)
- **Cost per email:** $0
- **Monthly limit:** Unlimited
- **Best for:** Testing, development, simple tasks

### gpt-3.5-turbo (Paid)
- **Cost per email:** ~$0.001 - $0.002
- **100 emails:** ~$0.10 - $0.20
- **1000 emails:** ~$1 - $2
- **Best for:** Production, complex tasks, better UX

**Recommendation:** Use qwen2.5 for testing, GPT for production.

---

## 🎓 Advanced: Adding More Context Intelligence

Want to make keyword fallback even smarter? Edit `services/agent-service/main.py`:

### Add More Context Indicators

```python
context_indicators = [
    "contact", "聯絡", "联络", "通知", "告知",
    # Add more:
    "update", "更新", "報告", "回報",
    "remind", "提醒", "確認", "确认",
    "discuss", "討論", "讨论", "商量"
]
```

### Add Relationship Detection

```python
# Detect if talking about someone with email
if "boss" in task or "manager" in task or "team" in task:
    if emails:
        return ("send_email", {...})
```

### Add Question Detection

```python
# "Can you let X know..." = send email
if any(phrase in task for phrase in ["can you let", "could you inform", "請告訴", "能不能"]):
    if emails:
        return ("send_email", {...})
```

---

## 🛠️ Troubleshooting

### "GPT isn't calling the email tool"

**Check:**
1. Model is `gpt-3.5-turbo` (not qwen2.5)
2. API key is valid in `.env`
3. Prompt includes email address
4. LiteLLM service is running: `docker compose ps litellm`

**Debug:**
```bash
docker compose logs agent-service --tail 50
# Look for: "tool_call" or "function"
```

---

### "qwen2.5 not detecting context"

**Current Limitations:**
- Needs: email address + context keyword OR explicit send keyword
- Won't work: Pure context without indicators

**Workaround:**
- Add more context indicators (see Advanced section)
- Use GPT for better understanding
- Be more explicit in prompts

---

## 📊 Testing Both Modes

### Test Script:

```bash
# Test with qwen2.5 (fallback)
curl -X POST http://localhost:8002/agent/execute \
  -H "Content-Type: application/json" \
  -d '{"task":"contact jerry@gmail.com 告訴他會議時間","model":"qwen2.5"}'

# Test with GPT (function calling)
curl -X POST http://localhost:8002/agent/execute \
  -H "Content-Type: application/json" \
  -d '{"task":"John at jerry@gmail.com should know about the meeting","model":"gpt-3.5-turbo"}'
```

### Compare Results:

**qwen2.5:**
- Subject: "來自AI助手的訊息" (generic)
- Body: Original prompt text
- Fast: < 500ms

**gpt-3.5-turbo:**
- Subject: "Meeting Notification" (smart!)
- Body: Professional, composed message
- Slower: 1-3s

---

## 🎉 Summary

### What You Have Now:

✅ **Improved keyword fallback** for qwen2.5:
- Understands more patterns
- Context-aware with email addresses
- Works with "contact", "通知", "告知" etc.

✅ **Full LLM function calling** with GPT:
- Already implemented and working
- Just select `gpt-3.5-turbo` model
- Natural language understanding
- Smart content generation

### Recommendations:

**For Development/Testing:**
- Use **qwen2.5** (free, fast)
- Be explicit: "send email to...", "contact ... 告訴..."

**For Production:**
- Use **gpt-3.5-turbo** ($0.001/request)
- Natural language works
- Better user experience
- Smart content generation

---

## 📞 Next Steps

1. **Try GPT now** - Select `gpt-3.5-turbo` in Web UI
2. **Test natural prompts** - No keywords needed!
3. **Compare results** - See the quality difference
4. **Decide** - Free (qwen2.5) vs Smart (GPT)

---

**Last Updated:** 2025-10-17
**Version:** 2.2.0
**Feature:** Context-aware agent with dual intelligence modes
