# Agent Catalog Documentation Index

## Overview

This directory contains comprehensive documentation about the AI Platform's Agent Catalog implementation, along with a complete guide for adding new agents (using "Contract Review Agent" as the example).

## Documentation Files

### 1. **AGENT_CATALOG_SUMMARY.txt** (RECOMMENDED STARTING POINT)
- **Size**: ~7KB, formatted for easy terminal viewing
- **Content**: 
  - Quick findings and overview
  - Where to make changes (specific line numbers)
  - How it works (architecture and data flow)
  - Key insights and design patterns
  - Complete implementation effort estimate
  - Testing checklist
- **Best For**: First-time readers, understanding the big picture

### 2. **AGENT_CATALOG_GUIDE.md** (DETAILED REFERENCE)
- **Size**: ~18KB, comprehensive markdown
- **Content**:
  - Executive summary
  - Agent catalog definition locations (with code snippets)
  - Agent configuration & registration process
  - Agent data schema (request/response structures)
  - Web UI display mechanism
  - Existing agent examples (3 agents analyzed)
  - Complete Contract Review Agent implementation guide
  - File modification checklist
  - Testing procedures
  - Architecture diagram
  - Key insights and design decisions
- **Best For**: Implementation, reference, deep understanding

### 3. **AGENT_CATALOG_QUICK_REF.md** (ONE-PAGE REFERENCE)
- **Size**: ~5KB, concise and actionable
- **Content**:
  - Current agents table
  - Quick implementation checklist (3 files, 15 changes)
  - Key file locations
  - Data flow diagram
  - System prompt template
  - Testing commands
  - Translation key templates
  - Important notes
  - Related existing code
  - Troubleshooting table
- **Best For**: Developers actively implementing, quick lookups

---

## Quick Navigation

### I want to...

**Understand the Agent Catalog system**
→ Start with `AGENT_CATALOG_SUMMARY.txt`
→ Then read "Architecture" section in `AGENT_CATALOG_GUIDE.md`

**Add a new agent**
→ Open `AGENT_CATALOG_QUICK_REF.md`
→ Follow the checklist section
→ Reference `AGENT_CATALOG_GUIDE.md` for detailed code

**See where agents are defined**
→ Check `AGENT_CATALOG_GUIDE.md` section 1
→ Or `AGENT_CATALOG_QUICK_REF.md` "Key Files" section

**Understand data structures**
→ See section 3 in `AGENT_CATALOG_GUIDE.md`
→ Or `AGENT_CATALOG_SUMMARY.txt` "Data Structures" section

**Get translation templates**
→ Jump to `AGENT_CATALOG_QUICK_REF.md` "Translation Keys Template"
→ Or section 6 in `AGENT_CATALOG_GUIDE.md`

**Test a new agent**
→ See section 8 in `AGENT_CATALOG_GUIDE.md`
→ Or use commands in `AGENT_CATALOG_QUICK_REF.md`

---

## Key Files to Edit (Summary)

```
services/
├── web-ui/
│   ├── app.py
│   │   ├── Line 943: Agent selectbox list
│   │   └── Lines 1211-1285: agent_configs dictionary
│   │
│   └── i18n.py
│       ├── zh-TW section: 3 translation keys
│       ├── zh-CN section: 3 translation keys
│       ├── en section: 3 translation keys
│       └── vi section: 3 translation keys
│
└── agent-service/
    └── main.py
        └── Lines 605-696: agent_prompts dictionary
```

---

## Current Agents

| Icon | ID | Name | Purpose |
|------|----|----- |---------|
| 🤖 | `general` | General Assistant | Multi-purpose AI assistant |
| 🔬 | `research` | Research Assistant | Deep research and analysis |
| 📊 | `analysis` | Data Analysis | Data processing & visualization |

---

## Implementation Quick Facts

- **Total Changes**: 15 edits across 3 files
- **Estimated Time**: 30-45 minutes
- **Complexity**: LOW (configuration only, no code changes)
- **Risk**: MINIMAL (isolated changes, easy to rollback)
- **API Changes Needed**: NONE (uses existing `/agent/execute` endpoint)
- **Database Changes**: NONE
- **Dependencies**: NONE

---

## Architecture Overview

```
Web UI (Streamlit)
    ↓
Agent Type Selection
    ↓
POST /agent/execute
    ↓
Agent Service
    ↓
System Prompt Lookup (agent_prompts dict)
    ↓
LLM + Tools
    ↓
Response
    ↓
Display in UI
```

---

## Key Insights

1. **System Prompt is Key**: The agent's behavior is determined entirely by its system prompt
2. **Tool Access is Universal**: All agents access the same 25+ MCP tools
3. **Prompts Must Be in Sync**: Same prompt appears in frontend and backend - keep them consistent
4. **Language Support is Built-in**: 4 languages supported (zh-TW, zh-CN, en, vi)
5. **Multi-turn Conversations**: Platform automatically supports iterative interactions

---

## Related Project Files

Contract Review Tools (already implemented):
- `/services/mcp-server/tools/contract_review.py` - Full implementation
- `/services/mcp-server/utils/contract_parser.py` - Parsing utilities
- `/services/mcp-server/prompts/contract_review_template.py` - Prompt templates
- `/services/mcp-server/data/risk_patterns.json` - Risk pattern database

---

## Getting Started Checklist

- [ ] Read `AGENT_CATALOG_SUMMARY.txt` (5 minutes)
- [ ] Review `AGENT_CATALOG_QUICK_REF.md` (5 minutes)
- [ ] Prepare contract review system prompt
- [ ] Prepare translations for 4 languages
- [ ] Open `AGENT_CATALOG_GUIDE.md` for detailed guidance
- [ ] Edit 3 files with 15 total changes
- [ ] Test frontend, backend, integration, and languages
- [ ] Commit changes with clear message

---

## Common Questions

**Q: Do I need to change the API?**
A: No. The `/agent/execute` endpoint already supports any agent type.

**Q: Will my new agent have access to tools?**
A: Yes, automatically. All agents access the same 25+ MCP tools.

**Q: Can I test locally?**
A: Yes. Use the commands in `AGENT_CATALOG_QUICK_REF.md` under "Testing Commands".

**Q: What if I miss a translation?**
A: The system will show the English key name (e.g., "agent_contract_review") as fallback.

**Q: Can agents be removed later?**
A: Yes, just remove the entries from the three files. Changes are easily reversible.

**Q: Do system prompts affect all users?**
A: Yes, they're global agent configurations. All users get the same prompt.

---

## Support & References

- **Detailed Implementation**: See Section 6 in `AGENT_CATALOG_GUIDE.md`
- **Code Snippets**: All 15 changes are provided in `AGENT_CATALOG_GUIDE.md`
- **Troubleshooting**: See troubleshooting table in `AGENT_CATALOG_QUICK_REF.md`
- **Examples**: Three existing agents documented in `AGENT_CATALOG_GUIDE.md` Section 5

---

## Document Metadata

- **Created**: 2025-10-29
- **Project**: AI Platform (Multi-model AI Assistant Platform)
- **Technology Stack**: FastAPI, Streamlit, LiteLLM, MCP Server
- **Languages Supported**: Chinese (Traditional/Simplified), English, Vietnamese
- **Target Users**: Backend developers, AI/ML engineers, platform administrators

---

Generated with Analysis Tools | Latest Update: 2025-10-29
