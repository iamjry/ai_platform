# Agent Catalog - Quick Reference

## Current Agents

| Icon | ID | Name | Purpose |
|------|----|----- |---------|
| 🤖 | `general` | General Assistant | Multi-purpose tasks, emails, file analysis |
| 🔬 | `research` | Research Assistant | Deep research, document search, synthesis |
| 📊 | `analysis` | Data Analysis | Statistical analysis, data processing, charts |
| ⚖️ | `contract_review` | Contract Review | Risk analysis, clause review, recommendations |

---

## Quick Implementation Checklist

### 1. Frontend (`services/web-ui/app.py`)

**Location A - Line 943** (Agent selector dropdown):
```python
["general", "research", "analysis", "contract_review"]  # ADD HERE
```

**Location B - Lines 1284-1285** (Agent config dict):
```python
"contract_review": {
    "name": get_text("agent_contract_review", lang),
    "icon": "⚖️",
    "description": get_text("agent_contract_review_desc", lang),
    "use_cases": get_text("agent_contract_review_uses", lang),
    "prompt": """SYSTEM PROMPT TEXT HERE"""
}
```

### 2. Backend (`services/agent-service/main.py`)

**Location - Lines 605-696** (Agent prompts dict):
```python
"contract_review": """SYSTEM PROMPT TEXT HERE"""
```

### 3. Localization (`services/web-ui/i18n.py`)

**For each language** (4 sections: zh-TW, zh-CN, en, vi):
```python
"agent_contract_review": "Display Name",
"agent_contract_review_desc": "Short description",
"agent_contract_review_uses": "• Use case 1\n• Use case 2\n• Use case 3"
```

---

## Key Files

```
services/
├── web-ui/
│   ├── app.py              ← Lines 943, 1211-1285
│   └── i18n.py             ← Translation keys
├── agent-service/
│   └── main.py             ← Lines 605-696
└── mcp-server/
    └── tools/
        └── contract_review.py ← Already exists!
```

---

## Data Flow

```
User UI
   ↓ selects agent_type
web-ui/app.py
   ↓ sends POST /agent/execute
agent-service/main.py
   ↓ looks up agent_prompts[agent_type]
LLM + System Prompt
   ↓ executes with appropriate behavior
Response
```

---

## System Prompt Template

```
你是一個專業的[ROLE]，擅長[SKILLS]。

你的專長：
1. [CAPABILITY 1]
2. [CAPABILITY 2]
3. [CAPABILITY 3]

工作流程：
- [STEP 1]
- [STEP 2]
- [STEP 3]

重點：[KEY FOCUS AREAS]
```

---

## Testing Commands

### Test Frontend Selection
```
Visit: http://localhost:8501
Tab: 👥 Agents Catalog
Check: "contract_review" appears in dropdown
```

### Test Backend
```bash
curl -X POST http://localhost:8002/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Review this contract",
    "agent_type": "contract_review",
    "model": "gpt-4o"
  }'
```

---

## Translation Keys Template

### Traditional Chinese (zh-TW)
```python
"agent_contract_review": "合約審查",
"agent_contract_review_desc": "專業的合約分析和風險識別",
"agent_contract_review_uses": "• 合約風險分析\n• 條款審查和解釋\n• 缺失條款檢查\n• 修改建議",
```

### Simplified Chinese (zh-CN)
```python
"agent_contract_review": "合同审查",
"agent_contract_review_desc": "专业的合同分析和风险识别",
"agent_contract_review_uses": "• 合同风险分析\n• 条款审查和解释\n• 缺失条款检查\n• 修改建议",
```

### English (en)
```python
"agent_contract_review": "Contract Review",
"agent_contract_review_desc": "Professional contract analysis and risk identification",
"agent_contract_review_uses": "• Contract risk analysis\n• Clause review and interpretation\n• Missing clause detection\n• Revision suggestions",
```

### Vietnamese (vi)
```python
"agent_contract_review": "Xem xét Hợp đồng",
"agent_contract_review_desc": "Phân tích hợp đồng chuyên nghiệp và xác định rủi ro",
"agent_contract_review_uses": "• Phân tích rủi ro hợp đồng\n• Xem xét và giải thích điều khoản\n• Phát hiện điều khoản thiếu\n• Đề xuất sửa đổi",
```

---

## Important Notes

1. **System Prompt Duplication**: The same prompt appears in 2 places:
   - `app.py`: For display in Agents Catalog
   - `agent-service/main.py`: For actual LLM execution
   - Keep them consistent!

2. **Automatic Tool Access**: The new agent automatically gets access to all MCP tools:
   - contract_review (custom tool)
   - web_search, knowledge_base_search
   - send_email, send_notification
   - and 20+ more tools

3. **No API Changes**: The `/agent/execute` endpoint already supports any agent type through the dictionary lookup pattern.

4. **Multi-turn Support**: Agents support conversation history automatically.

5. **Language-Aware**: UI automatically translates based on selected language.

---

## Related Existing Code

Contract review tools already implemented:
- `/services/mcp-server/tools/contract_review.py` - Full implementation
- `/services/mcp-server/utils/contract_parser.py` - Parsing utilities
- `/services/mcp-server/data/risk_patterns.json` - Risk patterns database
- `/services/mcp-server/prompts/contract_review_template.py` - Prompt templates

The new agent will automatically have access to these!

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Agent not in dropdown | Check app.py line 943 |
| Not displaying in catalog | Check agent_configs dict in app.py |
| Backend not recognizing agent | Check agent_prompts dict in agent-service/main.py |
| Translations missing | Check all 4 language sections in i18n.py |
| Prompts not matching | Keep frontend and backend prompts in sync |

