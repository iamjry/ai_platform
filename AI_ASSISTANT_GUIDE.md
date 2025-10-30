# AI Assistant Quick Reference Guide

**PURPOSE**: Enable AI assistants to quickly understand and work on this project with minimal token usage.
**LAST UPDATED**: 2025-10-30
**PROJECT**: Multi-Model AI Platform with RAG, Agent System, Contract Review

---

## 🎯 QUICK START (Read This First)

### Project Type
Docker-based microservices platform | 11 containers | Python/FastAPI/Streamlit

### Key Services & Ports
```
web-ui:          8501  (Streamlit UI - 4 language support)
agent-service:   8002  (FastAPI - Agent orchestration)
mcp-server:      8001  (FastAPI - MCP tools, 34 tools including OCR)
litellm:         4000  (LLM proxy - 15+ models)
ollama:          11434 (Local LLM)
postgres:        5433  (Main DB)
qdrant:          6333  (Vector DB)
redis:           6380  (Cache)
rabbitmq:        5672  (Message queue)
```

### Critical File Locations
```
services/web-ui/app.py                      - Main UI (1500+ lines)
services/web-ui/i18n.py                     - Translations (zh-TW, zh-CN, en, vi)
services/agent-service/main.py              - Agent orchestration
services/mcp-server/main.py                 - MCP tool registration (34 tools)
services/mcp-server/tools/                  - MCP tool implementations
services/mcp-server/tools/ocr_tools.py      - OCR tools (NEW)
services/mcp-server/utils/ocr_parser.py     - OCR engine (NEW)
services/mcp-server/utils/contract_parser.py - Document parser with OCR
config/litellm-config.yaml                  - Model configuration
config/agent_prompts.yaml                   - Agent system prompts (NEW)
docker-compose.yml                          - Service definitions
```

---

## 📋 TASK → FILE MAPPING (Most Important)

### UI Changes
| Task | Files to Modify | Note |
|------|----------------|------|
| Add new tab | `web-ui/app.py` (tabs section ~L400) | Also add to `i18n.py` |
| Add agent type | `web-ui/app.py` (agent_configs ~L1211, agent_options ~L942), `agent-service/main.py` (agent_prompts ~L605) | 4 languages |
| Add translation | `web-ui/i18n.py` (all 4 language sections) | zh-TW, zh-CN, en, vi |
| File upload | `web-ui/app.py` (use session_state!) | PyPDF2, docx, UTF-8 |
| Model visibility | `config/litellm-config.yaml` (visible: true/false) | Rebuild litellm after |

### Agent System
| Task | Files to Modify | Note |
|------|----------------|------|
| Add MCP tool | `mcp-server/tools/new_tool.py`, `mcp-server/main.py` (register) | Follow tool schema |
| Modify agent prompt | `config/agent_prompts.yaml` (centralized prompts) | Rebuild agent-service |
| Add agent type | `config/agent_prompts.yaml` + `web-ui/app.py` + `web-ui/i18n.py` | 3 files minimum |
| Add OCR language | `mcp-server/utils/ocr_parser.py` (languages param) | English default |

### Model Configuration
| Task | Files to Modify | Rebuild Required |
|------|----------------|------------------|
| Add/modify model | `config/litellm-config.yaml` | litellm service |
| Model visibility | `config/litellm-config.yaml` (visible field) | litellm service |
| API keys | `.env` file | No rebuild needed |

---

## 🚨 CRITICAL PATTERNS & GOTCHAS

### Docker & Deployment
```
⚠️ SOURCE CODE NOT MOUNTED AS VOLUMES
- Code changes require: docker-compose build <service> && docker-compose up -d <service>
- Only config files are mounted (litellm-config.yaml, docs, etc.)
- Always rebuild after code changes

✅ Deployment Steps:
1. Modify code
2. docker-compose build <service>
3. docker-compose up -d <service>
4. Verify: docker-compose ps <service>
```

### Streamlit Session State (VERY IMPORTANT)
```
⚠️ Streamlit reruns entire script on every interaction
- Use st.session_state for persistence across reruns
- File uploads MUST use session_state or content is lost
- Example: st.session_state.uploaded_file_content

✅ File Upload Pattern:
if 'file_content' not in st.session_state:
    st.session_state.file_content = ""
if uploaded_file and uploaded_file.name != st.session_state.file_name:
    st.session_state.file_content = extract_content(uploaded_file)
    st.session_state.file_name = uploaded_file.name
```

### Translations (4 Languages Required)
```
⚠️ Every UI text must have 4 translations
- zh-TW (繁體中文) - lines ~L12-250
- zh-CN (简体中文) - lines ~L252-490
- en (English) - lines ~L492-730
- vi (Tiếng Việt) - lines ~L732-970

✅ Search for existing keys first to avoid duplicates
```

### Git Commit Messages
```
✅ Required format:
feat/fix/docs: Short description

Detailed explanation...

Changes:
- Point 1
- Point 2

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## 🗂️ PROJECT STRUCTURE (Fast Reference)

```
ai_platform/
├── services/
│   ├── web-ui/              # Streamlit UI
│   │   ├── app.py          # Main UI (READ FIRST for UI tasks)
│   │   ├── i18n.py         # Translations (4 languages)
│   │   └── requirements.txt
│   ├── agent-service/       # Agent orchestration
│   │   ├── main.py         # Agent logic, system prompts
│   │   └── requirements.txt
│   ├── mcp-server/          # MCP tools server
│   │   ├── main.py         # Tool registration
│   │   ├── tools/          # Tool implementations
│   │   │   ├── contract_review.py  # Contract Review tools
│   │   │   ├── ocr_tools.py        # OCR tools (NEW)
│   │   ├── utils/          # Utilities
│   │   │   ├── contract_parser.py  # PDF/DOCX/TXT parser (OCR-enabled)
│   │   │   ├── ocr_parser.py       # OCR engine (NEW)
│   │   ├── data/
│   │   │   ├── risk_patterns.json  # Contract risk patterns
│   │   ├── prompts/
│   │   │   ├── contract_review_template.py  # Contract prompts
│   │   └── requirements.txt
├── config/
│   ├── litellm-config.yaml  # Model definitions (visible field)
│   ├── agent_prompts.yaml   # Agent system prompts (NEW)
│   └── prometheus.yml
├── docker-compose.yml       # All service definitions
├── .env                     # API keys, credentials
└── scripts/                 # Deployment, init scripts
```

---

## 🎯 RECENT MAJOR CHANGES (2025-10-30)

### 1. OCR Document Parsing System (NEW - Latest)
**Files**: `mcp-server/utils/ocr_parser.py` (480 lines), `mcp-server/tools/ocr_tools.py` (350 lines), `config/agent_prompts.yaml`

**Key Integration**: Agents can now extract text from scanned documents and images

**Tools Added**:
- `ocr_extract_pdf` - Extract text from PDF (auto-detects scanned vs text-based)
- `ocr_extract_image` - Extract text from images (PNG, JPG, etc.)
- `ocr_get_status` - Check OCR service status and backends

**Technical Stack**:
- **EasyOCR** (CPU-based, default): Available immediately, good performance
- **DeepSeek-OCR** (GPU-based, optional): Best quality, requires CUDA
- **Auto-detection**: PDFs with <100 chars/page use OCR, others use fast text extraction
- **Lazy loading**: OCR engine only initialized when first needed

**Agent Integration**:
- Updated `config/agent_prompts.yaml` with OCR usage guidance
- General, Research, and Contract Review agents all OCR-aware
- Agents automatically detect when documents need OCR
- Seamless integration with existing tools

**Key Features**:
- Multi-language support (English default, can add Chinese, Japanese, etc.)
- Base64 encoding support for remote files
- Intelligent PDF detection (text vs scanned)
- Graceful degradation (falls back to text extraction if OCR fails)

**Testing**:
- `verify_agent_ocr_integration.py` - Full integration test (4/4 passing)
- `test_ocr_simple.sh` - Quick status check
- `test_ocr_docker.sh` - Docker container test
- `OCR_TESTING_GUIDE.md` - Complete testing documentation
- `AGENT_OCR_USAGE.md` - Agent usage guide

**Usage**: Upload scanned PDF to Contract Review agent → Agent auto-uses OCR → Extracted text analyzed

### 2. Contract Review Agent
**Files**: `mcp-server/tools/contract_review.py`, `mcp-server/utils/contract_parser.py`, `mcp-server/data/risk_patterns.json`, `mcp-server/prompts/contract_review_template.py`

**Location in UI**: Agent Catalog tab (📋 icon), Agent Task dropdown (4th option)

**Tools Added**:
- `review_contract` - Full contract analysis (risk score 0-100)
- `analyze_clause` - Specific clause analysis
- `compare_contracts` - Side-by-side comparison

**Key Features**:
- Multi-format support: PDF, DOCX, TXT
- Risk scoring algorithm (100+ patterns)
- 5 contract types: employment, NDA, service, lease, sales
- Missing clause detection
- Priority-ranked recommendations

**To Modify**: See `mcp-server/data/risk_patterns.json` for patterns

### 3. File Upload in Agent Task Tab
**Files**: `web-ui/app.py` (lines ~L976-1020)

**Key Implementation**:
- Uses `st.session_state` for persistence (uploaded_file_content, uploaded_file_name)
- Extracts PDF (PyPDF2), DOCX (python-docx), TXT (UTF-8)
- Auto-adds review instruction if agent_type == "contract_review"
- File content persists across page reruns

**Translations Added**: upload_file, file_loaded, characters, file_load_error, file_content

### 4. Agent Type Selector Enhancement
**Files**: `web-ui/app.py` (lines ~L941-956)

**Change**: Now shows localized names with icons instead of raw IDs
```python
agent_options = {
    "general": f"🤖 {get_text('agent_general', lang)}",
    "research": f"🔬 {get_text('agent_research', lang)}",
    "analysis": f"📊 {get_text('agent_analysis', lang)}",
    "contract_review": f"📋 {get_text('agent_contract_review', lang)}"
}
```

### 5. Agent Catalog Layout
**Files**: `web-ui/app.py` (lines ~L1337-1376)

**Change**: Changed from 3-column to 2x2 grid layout for 4 agents

---

## 🔍 COMMON TASKS FLOWCHART

### Adding New Agent Type
```
1. Add translations to i18n.py (4 languages)
   - agent_<type>: "Name"
   - agent_<type>_desc: "Description"
   - agent_<type>_uses: "Use cases"

2. Add to web-ui/app.py:
   - agent_configs dict (~L1285): UI catalog card
   - agent_options dict (~L942): Dropdown selector

3. Add to config/agent_prompts.yaml:
   - Add new agent_prompts.<type> section with system prompt
   - Include OCR tool guidance if agent should use OCR

4. Rebuild & restart:
   docker-compose build web-ui agent-service
   docker-compose up -d web-ui agent-service
```

### Adding New MCP Tool
```
1. Create tool file:
   services/mcp-server/tools/my_tool.py

2. Implement tool function:
   async def my_tool_function(param1: str, param2: int, llm_client=None):
       # Implementation
       return json.dumps({"result": "..."})

3. Define tool schema:
   MY_TOOL_CONFIG = {
       "name": "my_tool",
       "description": "...",
       "parameters": {...},
       "handler": my_tool_function
   }

4. Register in mcp-server/main.py:
   from tools.my_tool import MY_TOOL_CONFIG
   # Add to registration loop

5. Rebuild:
   docker-compose build mcp-server
   docker-compose up -d mcp-server
```

### Modifying UI Text
```
1. Find key in i18n.py (use grep/search)
2. Modify all 4 language sections
3. Rebuild web-ui:
   docker-compose build web-ui
   docker-compose up -d web-ui
```

---

## ⚡ PERFORMANCE TIPS

### Minimize Token Usage
1. **Read selectively**: Use line ranges with Read tool
2. **Search first**: Use Grep/Glob before reading entire files
3. **Reference this guide**: Instead of re-reading code
4. **Check git log**: `git log --oneline -20` for recent changes

### Quick Verification Commands
```bash
# Check service status
docker-compose ps

# View logs (last 50 lines)
docker logs ai-web-ui --tail 50
docker logs ai-agent-service --tail 50
docker logs ai-mcp-server --tail 50

# Verify file in container
docker exec ai-web-ui grep -c "search_term" /app/app.py

# Check OCR integration
python3 verify_agent_ocr_integration.py
curl http://localhost:8001/tools/ocr_get_status | jq .

# Git status
git status
git log --oneline -10
```

---

## 🔐 SECURITY & CREDENTIALS

**Location**: `.env` file (root directory)

**Key Variables**:
- `OPENAI_API_KEY` - OpenAI models
- `ANTHROPIC_API_KEY` - Claude models
- `GOOGLE_API_KEY` - Gemini models
- `TAIWAN_LLM_API_KEY` - Taiwan Gov models
- `LINE_CHANNEL_ACCESS_TOKEN` - LINE notifications
- `SMTP_*` - Email notifications
- Database passwords for postgres, redis, rabbitmq

**⚠️ Never commit .env file or expose keys in code**

---

## 🐛 DEBUGGING CHECKLIST

### UI Not Updating
- [ ] Did you rebuild? `docker-compose build web-ui`
- [ ] Did you restart? `docker-compose up -d web-ui`
- [ ] Did you force refresh browser? `Ctrl+F5`
- [ ] Check logs: `docker logs ai-web-ui --tail 50`

### Translation Missing
- [ ] Added to all 4 language sections in i18n.py?
- [ ] Used `get_text("key", lang)` in app.py?
- [ ] Rebuilt web-ui?

### File Upload Not Working
- [ ] Using `st.session_state` for persistence?
- [ ] Checking file type correctly?
- [ ] Required library installed? (PyPDF2, python-docx)

### MCP Tool Not Available
- [ ] Tool registered in mcp-server/main.py?
- [ ] Tool schema correct (name, parameters, handler)?
- [ ] Rebuilt mcp-server?
- [ ] Check mcp-server logs for errors

### Agent Not Calling Tool
- [ ] Tool name in system prompt (config/agent_prompts.yaml)?
- [ ] Using function-calling model (GPT-4o, Claude)?
- [ ] Tool parameters match schema?
- [ ] Check agent-service logs

### OCR Not Working
- [ ] EasyOCR installed? Check: `docker exec ai-mcp-server pip list | grep easyocr`
- [ ] MCP server has OCR tools? `curl http://localhost:8001/tools/list | jq '[.tools[] | select(.name | startswith("ocr_"))]'`
- [ ] Agent prompts mention OCR? `grep -i ocr config/agent_prompts.yaml`
- [ ] Run verification: `python3 verify_agent_ocr_integration.py`
- [ ] First run may take 5-10 min (EasyOCR model download)

---

## 📊 ARCHITECTURE DECISIONS (Why Things Are This Way)

### Why No Source Code Volumes?
- Simpler production deployment
- Consistent environment (no host path issues)
- Explicit rebuild ensures freshness
- Trade-off: Slower dev iteration

### Why Streamlit for UI?
- Rapid prototyping
- Python-native (team expertise)
- Built-in components (file upload, charts)
- Trade-off: Page reruns require session_state

### Why LiteLLM Proxy?
- Unified interface for 15+ models
- Automatic retry, fallback
- Cost tracking, rate limiting
- Easy to add new models (just YAML config)

### Why Separate Agent Service?
- Isolate complex orchestration logic
- Independent scaling
- Can swap orchestration strategies
- Cleaner separation of concerns

### Why MCP Tools Pattern?
- Standardized tool interface
- Easy to add new tools
- LLM-friendly tool definitions
- Reusable across agents

---

## 🎓 LEARNING RESOURCES

### Understanding the Codebase
1. **Start here**: `docker-compose.yml` (service overview)
2. **UI flow**: `web-ui/app.py` (top to bottom)
3. **Agent flow**: `agent-service/main.py` → `/agent/execute` endpoint
4. **Tools**: `mcp-server/main.py` (registration), `mcp-server/tools/` (implementations)

### Key Dependencies
- **Streamlit**: Web UI framework
- **FastAPI**: API services (agent, mcp)
- **LiteLLM**: LLM proxy
- **Qdrant**: Vector database
- **PyPDF2, python-docx**: Document parsing

### External Docs
- Streamlit session state: Critical for file uploads
- LiteLLM config: `config/litellm-config.yaml` format
- Qdrant: Vector operations in RAG implementation

---

## 🎯 QUICK CHECKLIST FOR NEW AI ASSISTANTS

When you first open this project:
1. ✅ Read this guide (you're doing it!)
2. ✅ Check `git log --oneline -20` for recent work
3. ✅ Run `docker-compose ps` to see service status
4. ✅ Understand: Code changes = rebuild required
5. ✅ Remember: 4 languages for every UI text
6. ✅ Know: Session state for Streamlit persistence
7. ✅ Reference this guide to save tokens

When user asks for changes:
1. 🔍 Check "TASK → FILE MAPPING" section
2. 📝 Read only required files (use line ranges)
3. ⚙️ Make changes
4. 🔨 Rebuild: `docker-compose build <service>`
5. 🚀 Restart: `docker-compose up -d <service>`
6. ✅ Verify: Check logs, test in UI
7. 💾 Commit: Use standard format

---

## 📝 MAINTENANCE NOTES

### When Adding New Features
1. Update this guide (TASK → FILE MAPPING, RECENT MAJOR CHANGES)
2. Add to appropriate section
3. Include file paths and line numbers if possible
4. Note any gotchas or patterns to follow

### When Refactoring
1. Update architecture decisions if approach changes
2. Update file structure if moved
3. Update critical patterns if changed

### This Guide Should Be Updated When:
- New service added
- New agent type added
- New major feature (like Contract Review)
- Architecture decision changed
- Common gotcha discovered
- Critical pattern changed

---

**END OF GUIDE**

**Remember**: This guide exists to save tokens. Reference it first before reading code. Update it when making significant changes.
