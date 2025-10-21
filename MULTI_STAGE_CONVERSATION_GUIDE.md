# Multi-Stage Conversation Guide

**Version:** 1.0.0
**Last Updated:** 2025-10-17
**Feature Status:** ✅ Production Ready

---

## Overview

The AI Platform now supports **multi-stage conversational interactions**, allowing the agent to intelligently gather missing information through follow-up questions rather than failing or using default values. This creates a natural, conversational user experience.

### Key Features

- 🔄 **Stateful Conversations**: Maintains context across multiple interactions
- 🤔 **Smart Missing Parameter Detection**: Automatically identifies required information
- 💬 **Natural Language Interactions**: Asks follow-up questions in a conversational manner
- 🎯 **Progressive Information Gathering**: Collects one piece of information at a time
- ✅ **Automatic Execution**: Executes tasks once all required parameters are collected

## How It Works

### Architecture

```
User Request (incomplete info)
         ↓
    Agent Service
         ↓
    LLM Analysis → Missing parameters?
         ↓
    Yes: Ask follow-up question
         ↓
    User provides information
         ↓
    Agent Service (with conversation history)
         ↓
    LLM Analysis → All parameters present?
         ↓
    Yes: Execute tool
         ↓
    Return result
```

### Example Flow

**Stage 1: Initial Request**
```
User: "send email"
Agent: "I can help you send an email. First, please tell me:
        Who do you want to send this email to? Please provide
        the recipient's email address."
```

**Stage 2: Provide Recipient**
```
User: "jerry@example.com"
Agent: "Thank you for providing the recipient's email address.
        Now I need: What is the email subject?"
```

**Stage 3: Provide Subject**
```
User: "Test Email Subject"
Agent: "Great! One more thing: What is the email body content?"
```

**Stage 4: Provide Body**
```
User: "This is a test email body."
Agent: "Email successfully sent!
        - Recipient: jerry@example.com
        - Subject: Test Email Subject
        - Email ID: EMAIL-20251017061137
        - Status: Sent"
```

## API Usage

### Request Format

```json
{
  "task": "User's message or request",
  "model": "claude-3-sonnet",
  "agent_type": "general",
  "conversation_history": [
    {
      "role": "user",
      "content": "Previous user message"
    },
    {
      "role": "assistant",
      "content": "Previous assistant response"
    }
  ]
}
```

### Response Format

```json
{
  "result": "Agent's response or result",
  "steps": [
    {
      "step": "fetch_tools",
      "result": "Found 28 tools",
      "status": "success"
    },
    {
      "step": "llm_response_1",
      "result": "Asking for more information",
      "status": "success"
    }
  ],
  "metadata": {
    "agent_type": "general",
    "model_used": "claude-3-sonnet",
    "iterations": 1,
    "tokens_used": 3492,
    "conversation_active": true
  },
  "needs_more_info": true,
  "missing_parameters": null
}
```

### Key Response Fields

- **`needs_more_info`**: Boolean indicating if the agent needs more information
- **`conversation_active`**: Metadata flag showing if conversation is ongoing
- **`result`**: The agent's response (question or final result)
- **`steps`**: Execution steps taken by the agent

## Usage Examples

### Example 1: Send Email (Multi-Stage)

**Request 1:**
```bash
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "send email",
    "model": "claude-3-sonnet"
  }'
```

**Response 1:**
```json
{
  "result": "Who do you want to send this email to? Please provide the recipient's email address.",
  "needs_more_info": true,
  "metadata": {
    "conversation_active": true
  }
}
```

**Request 2:**
```bash
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "jerry@example.com",
    "model": "claude-3-sonnet",
    "conversation_history": [
      {"role": "user", "content": "send email"},
      {"role": "assistant", "content": "Who do you want to send this email to? Please provide the recipient'\''s email address."}
    ]
  }'
```

**Response 2:**
```json
{
  "result": "Thank you! What is the email subject?",
  "needs_more_info": true,
  "metadata": {
    "conversation_active": true
  }
}
```

**Request 3:**
```bash
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Test Subject",
    "model": "claude-3-sonnet",
    "conversation_history": [
      {"role": "user", "content": "send email"},
      {"role": "assistant", "content": "Who do you want to send this email to? Please provide the recipient'\''s email address."},
      {"role": "user", "content": "jerry@example.com"},
      {"role": "assistant", "content": "Thank you! What is the email subject?"}
    ]
  }'
```

**Response 3:**
```json
{
  "result": "Great! What is the email body content?",
  "needs_more_info": true,
  "metadata": {
    "conversation_active": true
  }
}
```

**Request 4:**
```bash
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "This is the email body",
    "model": "claude-3-sonnet",
    "conversation_history": [
      {"role": "user", "content": "send email"},
      {"role": "assistant", "content": "Who do you want to send this email to? Please provide the recipient'\''s email address."},
      {"role": "user", "content": "jerry@example.com"},
      {"role": "assistant", "content": "Thank you! What is the email subject?"},
      {"role": "user", "content": "Test Subject"},
      {"role": "assistant", "content": "Great! What is the email body content?"}
    ]
  }'
```

**Response 4:**
```json
{
  "result": "Email successfully sent! Email ID: EMAIL-20251017061137",
  "needs_more_info": false,
  "metadata": {
    "conversation_active": false
  }
}
```

### Example 2: Complete Information Provided Upfront

**Request:**
```bash
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Send an email to john@example.com with subject '\''Meeting Tomorrow'\'' and body '\''Let'\''s meet at 10 AM'\''",
    "model": "claude-3-sonnet"
  }'
```

**Response:**
```json
{
  "result": "Email successfully sent!",
  "needs_more_info": false,
  "steps": [
    {
      "step": "tool_call_1",
      "tool": "send_email",
      "status": "success"
    }
  ]
}
```

## Implementation Details

### Data Models

#### AgentRequest
```python
class AgentRequest(BaseModel):
    task: str  # User's current message
    context: Optional[Dict] = None
    agent_type: str = "general"
    model: str = "qwen2.5"
    conversation_history: Optional[List[Dict]] = None  # NEW!
```

#### AgentResponse
```python
class AgentResponse(BaseModel):
    result: str
    steps: List[Dict]
    metadata: Dict
    needs_more_info: bool = False  # NEW!
    missing_parameters: Optional[List[str]] = None  # NEW!
```

### System Prompt

The agent uses an enhanced system prompt that instructs it to:

1. Check for all required parameters before executing tools
2. Ask for missing information rather than guessing
3. Ask one question at a time
4. Execute the task once all information is collected

```python
system_prompt = """You are an enterprise AI assistant with access to various tools.

Important Guidelines:
1. When a user requests an action (send email, create task, search, etc.), call the appropriate tool
2. Before calling a tool, check if you have all required parameters
3. If required parameters are missing (email address, subject, body, etc.), do not guess or use defaults
4. If information is insufficient, politely ask the user for the missing information
5. Ask for only one piece of missing information at a time
6. Once all required information is collected, immediately execute the action

Examples:
- User says "send email" without recipient → Ask for recipient email address
- User says "send email to john@example.com" without subject/body → Ask for subject and body
- User provides all information → Execute send email immediately
"""
```

### Missing Information Detection

The system detects when the agent is asking questions using:

1. **Keyword Detection**: Looks for asking keywords in multiple languages
   - English: "please provide", "what is", "could you", "tell me"
   - Chinese: "請提供", "需要", "請告訴"

2. **Question Mark Detection**: Checks for `?` or `？` in the response

3. **Contextual Analysis**: Examines if tools were called vs. text response

```python
asking_keywords = [
    "請提供", "请提供", "please provide", "what is", "what's",
    "需要", "缺少", "could you", "can you provide",
    "請告訴", "请告诉", "tell me", "who", "which",
    "email地址", "email address", "收件人", "recipient",
    "主旨", "subject", "內容", "content", "body"
]

is_asking = any(keyword in result.lower() for keyword in asking_keywords)
has_question = "?" in result or "？" in result
needs_more_info = is_asking or has_question
```

## Web UI Integration

The Web UI (v2.1.0+) automatically maintains conversation history for multi-stage interactions:

### Features

- ✅ **Automatic Conversation Tracking**: Maintains context across chat messages
- 💬 **Visual Indicators**: Shows "Waiting for more information..." when expecting follow-up
- 🔄 **Auto-Clear on Completion**: Clears conversation history when task is complete
- 📊 **Status Display**: Shows conversation status in message metadata

### Implementation

The Web UI uses Streamlit's session state to track conversations:

```python
# Initialize conversation history in session state
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

# Send request with conversation history
response = requests.post(
    f"{AGENT_SERVICE_URL}/agent/execute",
    json={
        "task": user_input,
        "model": selected_model,
        "conversation_history": st.session_state.conversation_history
    }
)

# Handle response and update conversation history
result = response.json()
needs_more_info = result.get("needs_more_info", False)

if needs_more_info:
    # Update conversation history for next message
    st.session_state.conversation_history.append({
        "role": "user",
        "content": user_input
    })
    st.session_state.conversation_history.append({
        "role": "assistant",
        "content": result["result"]
    })

    # Show indicator to user
    st.info("💬 Please provide more information...")
else:
    # Task complete, clear conversation history
    st.session_state.conversation_history = []
```

### User Experience

**In the Chat Tab:**

1. User types: "send email"
2. Agent responds: "Who do you want to send this email to?"
3. Status shows: "💬 Please provide more information..."
4. User types: "john@example.com"
5. Agent responds: "What's the email subject?"
6. Process continues until all info is collected
7. Agent executes the task and clears conversation history

**Clear Chat Button:**
- Clears both display messages and conversation history
- Resets the conversation state completely

### Accessing the Web UI

```bash
# Local development
open http://localhost:8501

# Production (replace with your server IP)
open http://your-server-ip:8501
```

### Important: Tool Access in Web UI

**Both tabs now support tool execution:**

✅ **Chat Tab (Tab 1)**
- Full tool access via `/agent/execute` endpoint
- Can execute all 28 tools
- Multi-stage conversations with tool calling
- Example: "calculate ROI with gain 15000 and cost 10000" → calls `financial_calculator` tool

✅ **Agent Task Tab (Tab 2)**
- Full tool access via `/agent/execute` endpoint
- Can execute all 28 tools
- Multi-stage conversations with tool calling
- Shows detailed execution steps

**When Tools Are Called:**
- The LLM decides when to call tools based on user request
- If the request requires a tool (calculate, send email, etc.), the tool is called
- If it's a general question, the LLM responds directly without tools
- Multi-stage conversations work for both simple chat and tool execution

**Examples:**

*Tool Execution:*
```
User: "send email to john@example.com with subject Test"
→ Calls send_email tool (may ask for missing body)
```

*Simple Chat:*
```
User: "What can you help me with?"
→ Direct response, no tool call
```

*Mixed Conversation:*
```
User: "I need to send an email"
Agent: "Who should I send it to?" (asking for info)
User: "john@example.com"
Agent: "What's the subject?" (asking for more)
User: "Meeting Tomorrow"
→ Eventually calls send_email tool
```

## Best Practices

### For Developers

1. **Always Pass Conversation History**: Include the full conversation history in subsequent requests
2. **Check `needs_more_info` Flag**: Use this to determine if conversation should continue
3. **Limit Conversation Length**: Consider truncating very long conversations to save tokens
4. **Handle Timeouts**: Implement session timeouts for abandoned conversations

### For Users

1. **Provide Complete Information When Possible**: Reduces back-and-forth
2. **Answer One Question at a Time**: The agent asks focused questions
3. **Be Specific**: Clear answers help the agent understand your intent
4. **Review Final Confirmation**: Check details before execution

## Supported Models

All models configured in LiteLLM support multi-stage conversations:

- ✅ **GPT-4** (OpenAI)
- ✅ **GPT-3.5-turbo** (OpenAI)
- ✅ **Claude-3-Opus** (Anthropic) - Recommended
- ✅ **Claude-3-Sonnet** (Anthropic) - Recommended
- ✅ **Qwen2.5** (Local Ollama)

**Note:** Claude models (Anthropic) generally perform better at conversational information gathering.

## Troubleshooting

### Issue: Agent doesn't ask follow-up questions

**Solution:**
- Verify the model supports function calling
- Check that the system prompt is being sent correctly
- Ensure `conversation_history` is included in the request

### Issue: Conversation history grows too large

**Solution:**
- Implement conversation truncation (keep last N messages)
- Use summarization for very long conversations
- Consider resetting conversation after task completion

```python
# Example: Keep only last 10 messages
if len(conversation_history) > 10:
    conversation_history = conversation_history[-10:]
```

### Issue: Agent repeats the same question

**Solution:**
- Check that conversation history is being passed correctly
- Verify the user's answer is clear and contains the requested information
- Try rephrasing the answer more explicitly

## Performance Considerations

### Token Usage

Multi-stage conversations use more tokens due to:
- Conversation history passed with each request
- Multiple LLM calls for a single task

**Optimization Tips:**
- Use smaller models for simple information gathering (e.g., GPT-3.5-turbo)
- Truncate old conversation history
- Cache common conversational patterns

### Latency

Each stage requires an LLM API call, adding latency:
- Average per stage: 2-5 seconds
- Total for 3-stage conversation: 6-15 seconds

**Optimization Tips:**
- Use streaming responses for better UX
- Show "typing" indicators
- Consider using faster models for initial questions

## Security Considerations

1. **Conversation History Storage**: Don't store sensitive data in conversation history
2. **Parameter Validation**: Always validate collected parameters before execution
3. **Rate Limiting**: Implement per-user conversation limits
4. **Timeout Policies**: Expire inactive conversations

## Future Enhancements

Planned improvements for future versions:

- 📝 **Conversation Summarization**: Automatically summarize long conversations
- 🧠 **Context Compression**: Intelligent context reduction for token efficiency
- 🎯 **Multi-Parameter Collection**: Ask for multiple related parameters at once
- 💾 **Conversation Persistence**: Store conversation history in database
- 🔄 **Conversation Branching**: Handle topic changes mid-conversation
- 📊 **Analytics Dashboard**: Track conversation patterns and completion rates

## API Reference

### POST /agent/execute

Execute an agent task with optional conversation history.

**Request Body:**
```json
{
  "task": "string (required)",
  "model": "string (optional, default: qwen2.5)",
  "agent_type": "string (optional, default: general)",
  "conversation_history": [
    {
      "role": "user|assistant",
      "content": "string"
    }
  ]
}
```

**Response:**
```json
{
  "result": "string",
  "steps": [
    {
      "step": "string",
      "result": "string",
      "status": "success|failure"
    }
  ],
  "metadata": {
    "agent_type": "string",
    "model_used": "string",
    "iterations": "number",
    "tokens_used": "number",
    "conversation_active": "boolean"
  },
  "needs_more_info": "boolean",
  "missing_parameters": ["string"] | null
}
```

## Testing

Test the multi-stage conversation feature:

```bash
# Stage 1
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{"task":"send email","model":"claude-3-sonnet"}'

# Expected: Agent asks for recipient email

# Stage 2
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task":"test@example.com",
    "model":"claude-3-sonnet",
    "conversation_history":[
      {"role":"user","content":"send email"},
      {"role":"assistant","content":"<response from stage 1>"}
    ]
  }'

# Expected: Agent asks for subject

# Continue until task is executed
```

## Support

For issues or questions:
- Check troubleshooting section above
- Review API reference
- Test with different models
- Contact support team

---

**Version:** 1.0.0
**Last Updated:** 2025-10-17
**Status:** ✅ Production Ready
