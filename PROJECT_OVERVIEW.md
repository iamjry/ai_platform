# AI Platform - Project Overview

**快速參考文檔** - 讓 AI 助手快速了解專案架構和設計重點

---

## 📋 項目簡介

這是一個基於 Docker 的多模型 AI 對話平台，支援：
- **企業級 RAG 系統**（檢索增強生成）
- 本地模型（Ollama/Qwen）
- 台灣政府 LLM API（10 個模型）
- OpenAI GPT 系列
- Anthropic Claude 系列
- Google Gemini 系列

### ✨ 核心功能
1. **多模型對話** - 支援 15+ LLM 模型
2. **企業 RAG** - 文檔上傳、向量化、語義搜索
3. **Agent 任務** - 工具調用、網頁搜索、知識庫檢索
4. **文檔管理** - 完整 CRUD、分類、標籤系統
5. **向量搜索** - Qdrant 驅動的語義搜索
6. **OCR 解析** - 智能文檔 OCR（EasyOCR/DeepSeek-OCR）

## 🏗️ 系統架構

### 微服務架構圖
```
┌─────────────┐
│   Web UI    │ (Streamlit - Port 8501)
│ (Python)    │
└──────┬──────┘
       │
       ├──────────┐
       │          │
┌──────▼──────┐  ├─────────────┐
│Agent Service│  │  LiteLLM    │ (Proxy - Port 4000)
│(Port 8002)  │  │  Proxy      │
└──────┬──────┘  └──────┬──────┘
       │                │
┌──────▼──────┐         ├─→ Ollama (Port 11434)
│ MCP Server  │         ├─→ OpenAI API
│(Port 8001)  │         ├─→ Claude API
└──────┬──────┘         ├─→ Gemini API
       │                └─→ Taiwan Gov API
       │
       ├──────────┬──────────┬──────────┐
       │          │          │          │
   ┌───▼───┐  ┌──▼───┐  ┌──▼────┐  ┌──▼──────┐
   │Postgre│  │Qdrant│  │Redis  │  │RabbitMQ │
   │  SQL  │  │Vector│  │Cache  │  │ Queue   │
   └───────┘  └──────┘  └───────┘  └─────────┘
```

## 🔧 核心服務

### 1. Web UI (`services/web-ui/`)
- **技術**: Streamlit 1.33.0
- **端口**: 8501
- **功能**:
  - 多模型對話界面（支援中英文）
  - Agent Tasks 執行
  - 文檔上傳與分析（PDF 支援）
  - 模型配置管理
  - 系統監控儀表板
- **關鍵文件**:
  - `app.py` - 主應用
  - `i18n.py` - 多語言支援（中文/英文）
  - `requirements.txt` - Python 依賴

**重要設計決策**:
- CSS 優化：頂部空白 2rem（主內容）/ 0.3rem（sidebar）
- 使用 `st.markdown()` 代替 `st.header()` 以更好控制間距
- 從 litellm-config.yaml 動態載入模型列表
- **模型可見性控制**: 支援透過 `visible` 欄位控制模型是否顯示在選擇列表中
  - 在模型配置介面可編輯可見性狀態（checkbox）
  - 隱藏的模型不會出現在下拉選單中，但仍可在後台管理
  - 預設所有模型為可見（`visible: true`）

### 2. Agent Service (`services/agent-service/`)
- **技術**: FastAPI
- **端口**: 8002
- **功能**:
  - Agent 任務執行引擎
  - 工具調用協調（Tool Calling）
  - Fallback 模式（非 OpenAI 格式模型的模式匹配）
  - 上下文管理
- **關鍵邏輯**:
  ```python
  # 模型分類
  - function_calling_models: Claude, GPT-4o（原生支援工具調用）
  - fallback_models: Qwen, Taiwan Gov（使用模式匹配）

  # 搜索檢測
  - 網頁搜索（默認）: "搜索人工智能"
  - 知識庫搜索: "搜索文檔中的 API" （包含 documents/database 關鍵字）
  ```
- **台灣政府模型**（10 個）:
  1. llama31-taidelx-8b-32k
  2. llama3-taiwan-70b-8k
  3. llama31-foxbrain-70b-32k
  4. llama33-ffm-70b-32k
  5. phi4-reasoning-plus-32k
  6. magistral-small-2506-32k
  7. google-gemma-3-27b-32k
  8. llama4-scout-17b-16e-instruct-32k
  9. gpt-oss-20b-32k
  10. gpt-oss-120b-32k

### 3. MCP Server (`services/mcp-server/`)
- **技術**: FastAPI
- **端口**: 8001
- **功能**:
  - **企業 RAG 系統** 🆕
    - 文檔上傳與處理（PDF、DOCX、TXT）
    - 自動向量化（sentence-transformers）
    - 語義搜索（Qdrant）
    - 文檔管理 CRUD
  - 34 工具提供（搜索、數據處理、通知、OCR 等）
  - 向量搜索（Qdrant）
  - 文檔管理（PostgreSQL）
  - OCR 文檔解析（EasyOCR/DeepSeek-OCR）
  - Redis 緩存
- **RAG 組件**:
  - **rag_service.py** - 核心 RAG 服務類
    - 嵌入模型：all-MiniLM-L6-v2（384維）
    - 文本提取：PDF、DOCX、TXT
    - 分塊策略：500 words/chunk，50 words overlap
    - 向量存儲：Qdrant (cosine distance)
- **重要 API 端點**:
  - `POST /rag/documents/upload` - 文檔上傳（支援文件）
  - `POST /rag/documents/text` - 文檔創建（純文本）
  - `GET /rag/documents` - 列出文檔（支援篩選）
  - `GET /rag/documents/{id}` - 獲取文檔詳情
  - `PUT /rag/documents/{id}` - 更新文檔
  - `DELETE /rag/documents/{id}` - 刪除文檔及向量
  - `POST /rag/search` - 語義搜索
  - `GET /rag/stats` - RAG 系統統計
  - `search_knowledge_base` - 知識庫搜索
  - `web_search` - 網頁搜索（模擬）
  - `send_email` - 郵件發送
  - `create_task` - 任務創建
  - `analyze_data` - 數據分析
  - `generate_chart` - 圖表生成
  - `ocr_extract_pdf` - PDF OCR 提取（自動檢測）
  - `ocr_extract_image` - 圖片 OCR 提取
  - `ocr_get_status` - OCR 服務狀態

**已修復的 Bug**:
- ✅ 搜索緩存問題（2025-10）：緩存返回 list 而非 dict，已修正為緩存完整 response 對象

### 4. LiteLLM Proxy
- **配置**: `config/litellm-config.yaml`
- **端口**: 4000
- **功能**:
  - 統一 API 代理層
  - 支援多個 LLM 提供商
  - API Key 管理
  - 請求路由

## 📁 關鍵配置文件

### `config/litellm-config.yaml`
```yaml
model_list:
  - model_name: qwen2.5
    display_name: "Qwen 2.5 (本地)"
    litellm_params:
      model: ollama/qwen2.5

  - model_name: llama31-taidelx-8b-32k
    display_name: "Taiwan Gov - Llama 3.1 TaideLX"
    litellm_params:
      model: Taiwan_LLM/Llama-3.1-TaideLX-8B-32K
      api_base: https://...
      api_key: os.environ/TAIWAN_GOV_API_KEY
```

### `docker-compose.yml`
- 定義所有服務、網絡、數據卷
- 健康檢查配置
- 依賴關係管理

## 🔄 最近重大變更（2025-10）

### 1. 企業級 RAG 系統 ✅ 🆕
- **新功能**:
  - 創建 `rag_service.py` - 核心 RAG 服務類
  - 文檔上傳與處理（PDF、DOCX、TXT）
  - 自動向量化使用 sentence-transformers
  - 語義搜索集成 Qdrant
  - 完整文檔管理 CRUD API
  - 8 個新的 RAG API 端點
- **技術棧**:
  - sentence-transformers 2.6.1（all-MiniLM-L6-v2 模型）
  - PyPDF2 3.0.1（PDF 處理）
  - python-docx 1.1.0（DOCX 處理）
  - openpyxl 3.1.2（Excel 處理）
- **測試**:
  - `tests/test_rag.py` - 完整 RAG 功能測試
- **依賴更新**:
  - `services/mcp-server/requirements.txt` - 添加 RAG 依賴
  - Docker 構建時間增加（需下載大型模型）

### 2. 網頁搜索功能 ✅
- **Commit**: `0c321a9`
- **變更**:
  - 修改 `detect_tool_intent()` 支援 web_search
  - 默認使用網頁搜索（除非明確指定 documents/database）
  - 添加 web_search 結果格式化
  - 測試腳本：`tests/test_web_search.py`

### 3. UI 間距優化 ✅
- **Commits**: `1c0e65e`, `2d3141b`, `1b735cd`, `d20b593`, `745b0af`
- **變更**:
  - 主內容區域：padding-top 2rem
  - Sidebar：padding-top 0.3rem
  - 減少所有元素間距（headers, dividers, alerts）
  - 修正 Logo 容器負邊距問題

### 4. 台灣政府模型更新 ✅
- **變更**:
  - 從 9 個增加到 10 個模型
  - 移除：llama32-ffm-11b-v-32k
  - 新增：phi4, magistral, gemma-3, llama4, gpt-oss

### 5. Pandas 版本修正 ✅
- **問題**: `pandas==2.0.3` 與 Python 3.11 不兼容
- **解決**: 改為 `pandas>=2.0.0`

### 6. OCR 文檔解析系統 ✅ 🆕
- **日期**: 2025-10-30
- **新功能**:
  - 整合 DeepSeek-OCR (Hugging Face) 和 EasyOCR 雙後端架構
  - 智能 PDF 檢測（自動判斷文本型或掃描型 PDF）
  - 3 個新的 OCR 工具：ocr_extract_pdf, ocr_extract_image, ocr_get_status
  - Agent 系統整合（General、Research、Contract Review 皆可使用 OCR）
- **技術棧**:
  - EasyOCR 1.7.0（CPU-based，即時可用）
  - pdf2image 1.16.3（PDF 轉圖片）
  - Pillow 10.2.0（圖片處理）
  - 支援 DeepSeek-OCR（GPU-based，可選）
- **智能特性**:
  - 自動檢測 PDF 類型（<100 字符/頁 = 掃描版）
  - Lazy loading 機制（按需初始化 OCR 引擎）
  - 多語言支援（英文預設，可擴展中文、日文等）
  - Base64 編碼支援（適用於遠端文件）
- **新增文件**:
  - `services/mcp-server/utils/ocr_parser.py` - 核心 OCR 解析器（480 行）
  - `services/mcp-server/tools/ocr_tools.py` - MCP 工具包裝（350 行）
  - `OCR_TESTING_GUIDE.md` - 完整測試指南
  - `AGENT_OCR_USAGE.md` - Agent 使用指南
  - `verify_agent_ocr_integration.py` - 整合驗證腳本
  - `test_ocr_simple.sh`, `test_ocr_docker.sh` - 測試腳本
- **修改文件**:
  - `config/agent_prompts.yaml` - 新增 OCR 工具使用指引
  - `services/mcp-server/main.py` - 註冊 3 個 OCR 工具（總工具數：34）
  - `services/mcp-server/utils/contract_parser.py` - 整合 OCR 到契約審查
  - `services/mcp-server/requirements.txt` - 新增 OCR 依賴
- **使用方式**:
  - Web UI → Agent Tasks → Contract Review → 上傳掃描版 PDF
  - Agent 會自動偵測並使用 OCR 提取文字
  - 測試驗證：`python3 verify_agent_ocr_integration.py`

## 🧪 測試

### 測試文件位置
- `tests/test_rag.py` - 🆕 企業 RAG 功能測試（上傳、搜索、CRUD）
- `tests/test_all_models_search.py` - 多模型知識庫搜索測試
- `tests/test_web_search.py` - 網頁搜索功能測試
- `tests/test_knowledge_base_search.py` - 知識庫搜索檢測測試
- `tests/test_search.py` - 基本搜索測試
- `verify_agent_ocr_integration.py` - 🆕 OCR Agent 整合驗證
- `test_ocr_simple.sh` - 🆕 OCR 快速狀態檢查
- `test_ocr_docker.sh` - 🆕 OCR Docker 容器測試

### 運行測試
```bash
# RAG 系統測試
python3 tests/test_rag.py

# 搜索功能測試
python3 tests/test_web_search.py
python3 tests/test_all_models_search.py

# OCR 整合測試 🆕
python3 verify_agent_ocr_integration.py
bash test_ocr_simple.sh
bash test_ocr_docker.sh
```

## 🔑 環境變數

需要在 `.env` 或環境中設定：
```bash
# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
TAIWAN_GOV_API_KEY=...

# Service URLs
AGENT_SERVICE_URL=http://agent-service:8000
MCP_SERVER_URL=http://mcp-server:8001
LITELLM_URL=http://litellm:4000

# Database
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123
POSTGRES_DB=ai_platform
```

## 🚀 常見開發任務

### 1. 使用 RAG 系統 🆕
```bash
# 上傳文檔（文件）
curl -X POST http://localhost:8001/rag/documents/upload \
  -F "file=@document.pdf" \
  -F "category=技術文檔" \
  -F "tags=AI,機器學習"

# 創建文檔（文本）
curl -X POST http://localhost:8001/rag/documents/text \
  -H "Content-Type: application/json" \
  -d '{"title":"測試文檔","content":"內容...","category":"測試"}'

# 語義搜索
curl -X POST http://localhost:8001/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query":"機器學習","top_k":5,"similarity_threshold":0.5}'

# 獲取 RAG 統計
curl http://localhost:8001/rag/stats
```

### 2. 添加新模型
1. 編輯 `config/litellm-config.yaml`
2. 添加 model_list 條目（model_name, display_name, litellm_params）
3. 如需 fallback 模式，更新 `services/agent-service/main.py` 的 `model_name_map`
4. 重啟服務：`docker-compose build agent-service && docker-compose up -d`

### 3. 修改 UI 樣式
1. 編輯 `services/web-ui/app.py` 的 CSS 區塊（約第 146 行）
2. 重建 Web UI：`docker-compose build web-ui && docker-compose up -d web-ui`
3. 瀏覽器硬刷新（Cmd+Shift+R）

### 4. 添加新工具
1. 在 `services/mcp-server/main.py` 添加:
   - Pydantic Request Model
   - `/tools/{tool_name}` endpoint
   - 工具描述到 `get_tool_definitions()`
2. 在 `services/agent-service/main.py` 添加:
   - `detect_tool_intent()` 的模式檢測
   - 結果格式化邏輯
3. 重建兩個服務

### 5. 調試流程
```bash
# 查看服務日誌
docker-compose logs -f agent-service
docker-compose logs -f mcp-server
docker-compose logs -f web-ui

# 進入容器
docker exec -it ai-agent-service bash
docker exec -it ai-mcp-server bash

# 重啟單一服務
docker-compose restart agent-service
docker-compose restart mcp-server
```

## 📊 數據庫架構

### PostgreSQL
- **文檔表**: 存儲上傳的文件和內容
- **用戶表**: 用戶資訊（如啟用認證）
- **對話歷史**: 對話記錄

### Qdrant（向量數據庫）🆕
- **Collection**: documents
- **向量維度**: 384（all-MiniLM-L6-v2）
- **距離度量**: Cosine similarity
- **用途**:
  - 語義搜索
  - 文檔相似度計算
  - RAG 檢索增強
- **數據結構**:
  - `id`: 唯一標識符（doc_id_chunk_id）
  - `vector`: 384維嵌入向量
  - `payload`:
    - `doc_id`: 文檔 ID
    - `chunk_id`: 分塊 ID
    - `title`: 文檔標題
    - `content`: 分塊內容
    - `metadata`: 自定義元數據
    - `created_at`: 創建時間

### Redis
- **TTL**: 300 秒（搜索緩存）
- **鍵格式**: `search:{query}`

## 🎯 設計原則

1. **微服務架構**: 每個服務專注單一職責
2. **統一代理**: LiteLLM 統一處理所有 LLM API
3. **Fallback 機制**: 非 OpenAI 格式模型使用模式匹配
4. **緩存優先**: Redis 緩存搜索結果減少重複查詢
5. **健康檢查**: 所有服務都有健康檢查端點
6. **國際化**: Web UI 支援中英文切換

## 🐛 已知問題和限制

1. **認證服務**: 目前無認證（no-auth 版本）
2. **Web 搜索**: 目前是模擬數據，未接入真實搜索 API
3. **PDF 分析**: 僅支援文本提取，不支援 OCR
4. **台灣政府 API**: 需要有效 API Key

## 📝 Git 工作流程

- **Main 分支**: 穩定版本
- **提交格式**: 使用 conventional commits
  - `feat:` - 新功能
  - `fix:` - Bug 修復
  - `style:` - 樣式調整
  - `refactor:` - 重構
  - `docs:` - 文檔更新

## 🔗 重要文件快速索引

| 文件 | 用途 |
|------|------|
| `services/web-ui/app.py` | Web UI 主程序 |
| `services/agent-service/main.py` | Agent 執行引擎 |
| `services/mcp-server/main.py` | 工具服務器 |
| `config/litellm-config.yaml` | 模型配置 |
| `docker-compose.yml` | 容器編排 |
| `tests/` | 測試腳本目錄 |

## 💡 提示

當開始新對話時，AI 應該：
1. 先閱讀本文檔了解架構
2. 根據任務需求再讀取具體文件
3. 優先使用測試腳本驗證功能
4. 修改代碼後記得重建對應的 Docker 容器
5. 重要變更需要更新本文檔

---

**最後更新**: 2025-10-25
**版本**: 2.0 (Enterprise RAG)
**維護者**: AI Platform Team

**版本歷史**:
- v2.0 (2025-10-25): 添加企業級 RAG 系統
- v1.0 (2025-10-24): 初始版本
