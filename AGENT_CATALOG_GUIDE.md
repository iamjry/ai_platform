# Agent Catalog Implementation Analysis

## Executive Summary

The AI platform uses a **decentralized agent catalog system** where agent types are:
1. Defined as configuration dictionaries in the Web UI (`services/web-ui/app.py`)
2. Associated with system prompts in the backend (agent-service)
3. Displayed in the "Agents Catalog" tab with multilingual support (i18n.py)

Currently, there are **3 pre-configured agents**:
- **General Assistant** (`general`) - Multi-purpose tool usage
- **Research Assistant** (`research`) - Information gathering & analysis
- **Data Analysis** (`analysis`) - Data processing & visualization

---

## 1. Agent Catalog Definition Locations

### Frontend (Web UI) - `/path/to/your/ai_platform/services/web-ui/app.py`

**Lines 941-945**: Agent type selector in the UI
```python
agent_type = st.selectbox(
    get_text("agent_type", lang),
    ["general", "research", "analysis"],  # Agent list - EDIT THIS TO ADD NEW AGENTS
    help=get_text("agent_type_help", lang)
)
```

**Lines 1211-1285**: Agent configurations with full metadata
```python
agent_configs = {
    "general": {
        "name": get_text("agent_general", lang),
        "icon": "🤖",
        "description": get_text("agent_general_desc", lang),
        "use_cases": get_text("agent_general_uses", lang),
        "prompt": """System prompt content here..."""
    },
    "research": {...},
    "analysis": {...}
}
```

**Structure for each agent**:
- `name`: Display name (localized via i18n)
- `icon`: Emoji icon for UI display
- `description`: Short description (localized)
- `use_cases`: Bullet points of use cases (localized)
- `prompt`: Full system prompt used by the agent

### Backend (Agent Service) - `/path/to/your/ai_platform/services/agent-service/main.py`

**Lines 605-696**: Agent-specific system prompts
```python
agent_prompts = {
    "general": """System prompt...""",
    "research": """System prompt...""",
    "analysis": """System prompt..."""
}

system_prompt = agent_prompts.get(request.agent_type, agent_prompts["general"])
```

### Localization (i18n) - `/path/to/your/ai_platform/services/web-ui/i18n.py`

**Lines 94-102**: Agent-related translations (example for Traditional Chinese)
```python
"agent_general": "通用助手",
"agent_general_desc": "多功能AI助手，可處理各種任務",
"agent_general_uses": "• 問答與對話\n• 發送郵件\n• 創建任務\n• 文件分析",

"agent_research": "研究助手",
"agent_research_desc": "專注於信息收集和研究分析",
"agent_research_uses": "• 深度研究\n• 文檔搜索\n• 信息整合\n• 來源驗證",

"agent_analysis": "數據分析",
"agent_analysis_desc": "專注於數據處理和可視化",
"agent_analysis_uses": "• 統計分析\n• 數據處理\n• 圖表生成\n• 業務指標計算"
```

**Supported languages** (Line 4-9):
- `zh-TW` - Traditional Chinese
- `zh-CN` - Simplified Chinese  
- `en` - English
- `vi` - Vietnamese

---

## 2. Agent Configuration & Registration

### Data Structure

Each agent requires these fields:

```python
{
    "agent_id": {
        "name": str,              # Display name (should have i18n key)
        "icon": str,              # Emoji icon
        "description": str,       # Short description (i18n key)
        "use_cases": str,         # Bullet-point list (i18n key)
        "prompt": str             # Full system prompt (can be literal or template)
    }
}
```

### Registration Process

1. **Frontend Setup** (app.py):
   - Add agent ID to line 943: `["general", "research", "analysis", "your_agent"]`
   - Add config entry in `agent_configs` dict (lines 1211-1285)

2. **Backend Setup** (agent-service/main.py):
   - Add system prompt to `agent_prompts` dict (lines 605-696)
   - Prompt will be automatically matched by `agent_type`

3. **Localization** (i18n.py):
   - Add translations for agent labels
   - Required keys:
     - `agent_{id}` → display name
     - `agent_{id}_desc` → description
     - `agent_{id}_uses` → use cases
   - Repeat for each language: `zh-TW`, `zh-CN`, `en`, `vi`

### Data Flow

```
User selects agent type in UI
    ↓
Frontend sends request to /agent/execute with agent_type
    ↓
Backend receives AgentRequest with agent_type field
    ↓
Backend looks up system prompt from agent_prompts dict
    ↓
System prompt injected into LLM call
    ↓
LLM responds with appropriate agent behavior
```

---

## 3. Agent Data Schema

### Request Schema (from agent-service/main.py, lines 24-33)

```python
class AgentRequest(BaseModel):
    task: str                           # User's task description
    context: Optional[Dict] = None      # Optional context data
    agent_type: str = "general"         # Agent type selector
    model: str = "qwen2.5"             # Model choice
    conversation_history: Optional[List[Dict]] = None  # Multi-turn context
    images: Optional[List[Dict]] = None # Base64 encoded images for vision
    temperature: float = 0.7            # Sampling parameter
    top_p: float = 0.9                 # Nucleus sampling
    top_k: int = 40                    # Top-k sampling
```

### Response Schema (lines 35-40)

```python
class AgentResponse(BaseModel):
    result: str                         # Final agent response
    steps: List[Dict]                   # Execution steps with status
    metadata: Dict                      # Execution metadata
    needs_more_info: bool = False      # Multi-turn conversation flag
    missing_parameters: Optional[List[str]] = None
```

### Metadata Structure

```json
{
    "agent_type": "research",
    "model_used": "gpt-4o",
    "iterations": 2,
    "tokens_used": 1245,
    "conversation_active": false,
    "mcp_usage": {
        "tools_used": [
            {
                "name": "web_search",
                "arguments": {"query": "AI trends"},
                "result_summary": "Found 5 results..."
            }
        ],
        "resources_accessed": [
            {"type": "search", "query": "AI trends"}
        ],
        "system_prompt": "Full system prompt text...",
        "sampling_parameters": {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40
        }
    }
}
```

---

## 4. Web UI Agent Display

### Display Location
**Web UI Tab: "Agents Catalog"** (Lines 1204-1299 in app.py)

```
👥 Agents Catalog
└─ 🤖 General Assistant | 🔬 Research Assistant | 📊 Data Analysis
   [Description]        | [Description]        | [Description]
   
   Use Cases:           | Use Cases:           | Use Cases:
   • Q&A & Chat        | • Deep research      | • Statistical analysis
   • Send emails       | • Document search    | • Data processing
   • Create tasks      | • Info synthesis     | • Chart generation
   • File analysis     | • Source verify      | • Metrics calculation
   
   [View System Prompt ▼]
```

### UI Components

**Agent Display Code** (lines 1287-1299):
```python
cols = st.columns(3)  # 3-column layout
for idx, (agent_id, config) in enumerate(agent_configs.items()):
    with cols[idx]:
        st.markdown(f"### {config['icon']} {config['name']}")
        st.caption(config['description'])
        st.markdown(f"**{get_text('use_cases', lang)}:**")
        st.markdown(config['use_cases'])
        
        with st.expander(get_text("view_system_prompt", lang)):
            st.text_area(
                label="",
                value=config['prompt'],
                height=200,
                disabled=True
            )
```

**Multi-language Support**:
- Language selector in sidebar (line 265-275)
- All text uses `get_text()` function for localization
- Catalog automatically updates based on selected language

---

## 5. Existing Agent Examples

### 1. General Assistant
- **Purpose**: Multi-purpose AI assistant for diverse tasks
- **Capabilities**:
  - Q&A and conversations
  - Email sending with smart recipient detection
  - Task creation
  - File analysis (PDF, text)
- **System Prompt Focus**: 
  - Document analysis mode (direct file content reading)
  - Tool usage mode (with parameter validation)
  - LINE messaging with smart recipient detection

### 2. Research Assistant
- **Purpose**: Information gathering and analysis
- **Capabilities**:
  - Deep research with multiple search strategies
  - Document search and extraction
  - Information synthesis from multiple sources
  - Source verification and citation
- **System Prompt Focus**:
  - Planning search strategy
  - Cross-verifying information
  - Structured information presentation
  - Document summarization

### 3. Data Analysis Agent
- **Purpose**: Data processing and visualization
- **Capabilities**:
  - Statistical analysis
  - Data cleaning and processing (CSV handling)
  - Chart and visualization generation
  - Business metrics calculation
  - Financial analysis
- **System Prompt Focus**:
  - Data quality checking
  - Appropriate analysis method selection
  - Clear visualization output
  - Actionable insights generation

---

## 6. Contract Review Agent - Implementation Guide

### Complete Implementation Steps

#### Step 1: Update Frontend (app.py)

**Line 943 - Add agent to selectbox**:
```python
agent_type = st.selectbox(
    get_text("agent_type", lang),
    ["general", "research", "analysis", "contract_review"],  # ADD HERE
    help=get_text("agent_type_help", lang)
)
```

**Lines 1284-1285 - Add agent config before closing brace**:
```python
        },
        "contract_review": {
            "name": get_text("agent_contract_review", lang),
            "icon": "⚖️",
            "description": get_text("agent_contract_review_desc", lang),
            "use_cases": get_text("agent_contract_review_uses", lang),
            "prompt": """你是一個專業的合約審查專家，擅長識別風險、分析條款和提供建議。

你的專長：
1. 使用 contract_review 工具進行全面的合約分析
2. 識別關鍵風險和不利條款
3. 檢查必需條款是否存在或缺失
4. 比較不同版本的合約
5. 生成詳細的審查報告和建議

工作流程：
- 接收合約文本或文件時，先使用 contract_review 工具進行初步分析
- 基於分析結果識別風險等級和關鍵問題
- 提供具體的修改建議和談判策略
- 突出任何缺失的重要條款
- 提供明確的風險評估和優先級

重點：完整性、準確性、可行的建議、合規性檢查"""
        }
```

#### Step 2: Update Backend (agent-service/main.py)

**Lines 695-696 - Add agent prompt before closing brace**:
```python
            "analysis": """...""",
            
            "contract_review": """你是一個專業的合約審查專家，擅長識別風險、分析條款和提供建議。

你的專長：
1. 全面合約分析和風險識別
2. 條款解釋和影響評估
3. 缺失條款檢查和合規性驗證
4. 修改建議和談判策略

當用戶提供合約文本時：
1. 如果可用，使用 contract_review 工具進行自動分析
2. 識別所有關鍵風險和不利條款
3. 標記缺失的重要保護條款
4. 提供優先級排序的修改建議
5. 建議潛在的談判點

工作方式：
- 系統地分析每個主要部分（定義、義務、責任等）
- 與行業標準進行比較
- 提供具體的修改語言建議
- 突出雙方權利和義務的不平衡

重點：全面性、清晰度、實用建議、風險管理"""
```

#### Step 3: Update Localization (i18n.py)

**Add translations for all languages** (repeat for each language section):

For Traditional Chinese (in `"zh-TW"` section):
```python
        "agent_contract_review": "合約審查",
        "agent_contract_review_desc": "專業的合約分析和風險識別",
        "agent_contract_review_uses": "• 合約風險分析\n• 條款審查和解釋\n• 缺失條款檢查\n• 修改建議",
```

For Simplified Chinese (in `"zh-CN"` section):
```python
        "agent_contract_review": "合同审查",
        "agent_contract_review_desc": "专业的合同分析和风险识别",
        "agent_contract_review_uses": "• 合同风险分析\n• 条款审查和解释\n• 缺失条款检查\n• 修改建议",
```

For English (in `"en"` section):
```python
        "agent_contract_review": "Contract Review",
        "agent_contract_review_desc": "Professional contract analysis and risk identification",
        "agent_contract_review_uses": "• Contract risk analysis\n• Clause review and interpretation\n• Missing clause detection\n• Revision suggestions",
```

For Vietnamese (in `"vi"` section):
```python
        "agent_contract_review": "Xem xét Hợp đồng",
        "agent_contract_review_desc": "Phân tích hợp đồng chuyên nghiệp và xác định rủi ro",
        "agent_contract_review_uses": "• Phân tích rủi ro hợp đồng\n• Xem xét và giải thích điều khoản\n• Phát hiện điều khoản thiếu\n• Đề xuất sửa đổi",
```

### Integration with Existing Contract Tools

The platform already has contract review tools available:
- **Location**: `/path/to/your/ai_platform/services/mcp-server/tools/contract_review.py`
- **Features**:
  - Risk pattern detection
  - Missing clause analysis
  - LLM-powered clause analysis
  - Contract comparison
  - Report generation

The new agent will automatically have access to these tools through the MCP server.

---

## 7. File Modification Checklist

### Required Changes

```
✅ /services/web-ui/app.py
   Line 943: Add agent ID to selectbox list
   Lines 1284-1285: Add agent_configs entry with all 4 properties

✅ /services/agent-service/main.py
   Lines 695-696: Add agent system prompt to agent_prompts dict

✅ /services/web-ui/i18n.py
   - Traditional Chinese section (zh-TW): 3 keys
   - Simplified Chinese section (zh-CN): 3 keys
   - English section (en): 3 keys
   - Vietnamese section (vi): 3 keys
   = Total: 12 translation entries
```

### Files NOT Requiring Changes
- Database schema
- Docker compose
- Service configurations
- MCP server (contract tools already exist)
- Agent service routes

---

## 8. Testing the New Agent

1. **Frontend Test**:
   - Start web UI: `streamlit run services/web-ui/app.py`
   - Select "Contract Review" from agent type dropdown
   - Verify display in "Agents Catalog" tab
   - Check all languages work correctly

2. **Backend Test**:
   - Send POST request to `/agent/execute`:
   ```json
   {
       "task": "Review this contract for risks...",
       "agent_type": "contract_review",
       "model": "gpt-4o",
       "temperature": 0.7,
       "top_p": 0.9,
       "top_k": 40
   }
   ```

3. **Integration Test**:
   - Upload contract file
   - Execute with Contract Review agent
   - Verify tool calls are made
   - Check response quality

---

## 9. Architecture Diagram

```
┌─────────────────────────────────────┐
│      Web UI (Streamlit)             │
├─────────────────────────────────────┤
│ Agent Selection Dropdown             │
│ - "general"                         │
│ - "research"                        │
│ - "analysis"                        │
│ - "contract_review" [NEW]           │
└────────────────┬────────────────────┘
                 │
                 │ POST /agent/execute
                 │ {agent_type: "contract_review"}
                 ↓
┌─────────────────────────────────────┐
│   Agent Service (FastAPI)           │
├─────────────────────────────────────┤
│ agent_prompts dict lookup:          │
│  "contract_review" → system prompt  │
└────────────────┬────────────────────┘
                 │
                 │ Inject system prompt
                 ↓
┌─────────────────────────────────────┐
│    LLM (via LiteLLM Proxy)          │
├─────────────────────────────────────┤
│ System Prompt: "You are a contract│
│ review expert..."                   │
│ User Task: "Review this contract..." │
└────────────────┬────────────────────┘
                 │
                 │ May call tools
                 ↓
┌─────────────────────────────────────┐
│     MCP Server (Tool Integration)    │
├─────────────────────────────────────┤
│ contract_review (already exists)    │
│ web_search, knowledge_base, etc.    │
└─────────────────────────────────────┘
```

---

## 10. Key Insights

1. **Decentralized Configuration**: Agent definitions are split across frontend UI, backend prompts, and localization files - this allows flexibility but requires careful coordination.

2. **System Prompt Injection**: The same system prompt exists in two places (app.py and agent-service/main.py) - the frontend uses it for display, the backend uses it for LLM invocation.

3. **Tool Access**: All agents automatically have access to the same set of MCP tools (email, search, notifications, etc.) - the agent type only changes the system prompt and behavior strategy.

4. **Multi-turn Conversation**: The platform supports conversation history, so agents can iteratively ask for more information or refine results.

5. **Localization-First Design**: Every user-facing string uses the i18n system, making it easy to support new languages.

---

## Summary

The Agent Catalog is a simple but effective system based on:
- **Frontend**: Agent type selection + configuration display
- **Backend**: System prompt mapping
- **Localization**: Multi-language support

To add the Contract Review Agent, you need to:
1. Add "contract_review" to 3 locations
2. Provide system prompt twice (frontend + backend)
3. Add 12 translation entries (4 languages × 3 fields)

No backend API changes needed - the existing `/agent/execute` endpoint handles any agent type automatically through the system prompt dictionary lookup.
