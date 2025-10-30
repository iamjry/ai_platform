from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import asyncpg
from qdrant_client import QdrantClient
import redis.asyncio as redis
import os
import logging
import json
from datetime import datetime, timedelta
import httpx
from prometheus_fastapi_instrumentator import Instrumentator
import pandas as pd
import io
import base64
from rag_service import rag_service
from search_service import search_service
from tools.contract_review import CONTRACT_REVIEW_TOOLS, review_contract_tool, analyze_clause_tool, compare_contracts_tool
from tools.ocr_tools import OCR_TOOLS, ocr_extract_pdf_tool, ocr_extract_image_tool, ocr_get_status_tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP Server", version="2.0.0")

# Setup Prometheus metrics
Instrumentator().instrument(app).expose(app)

# 全局變量
db_pool = None
vector_db = None
redis_client = None

# ==================== Pydantic Models ====================

class SearchRequest(BaseModel):
    query: str
    collection: str = "documents"
    limit: int = 5

class AnalyzeDataRequest(BaseModel):
    data_source: str
    analysis_type: str  # "statistics", "correlation", "distribution"
    options: Optional[Dict] = {}

class GenerateChartRequest(BaseModel):
    data: List[Dict]
    chart_type: str  # "bar", "line", "pie"
    title: str
    x_field: Optional[str] = None
    y_field: Optional[str] = None

class CSVProcessRequest(BaseModel):
    csv_data: str  # base64 encoded CSV
    operation: str  # "filter", "sort", "aggregate"
    params: Dict

class SemanticSearchRequest(BaseModel):
    query: str
    similarity_threshold: float = 0.5
    top_k: int = 5
    filter_metadata: Optional[Dict] = None

class WebSearchRequest(BaseModel):
    query: str
    num_results: int = 5
    time_range: Optional[str] = None
    use_rag: bool = True  # Enable RAG integration
    mix_with_documents: bool = True  # Mix with existing documents
    providers: Optional[List[str]] = None  # Specific providers to use

class DocumentUploadRequest(BaseModel):
    title: str
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = []
    metadata: Optional[Dict] = {}

class DocumentUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict] = None
    is_published: Optional[bool] = None

class SummarizeRequest(BaseModel):
    document_id: int
    summary_length: int = 500
    language: str = "zh-TW"

class TranslateRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str

class GenerateReportRequest(BaseModel):
    template: str
    data: Dict
    output_format: str = "html"  # "pdf", "docx", "html"

class CheckPermissionsRequest(BaseModel):
    user_id: str
    resource_id: str

class AuditLogRequest(BaseModel):
    action_type: Optional[str] = None
    timestamp_from: Optional[datetime] = None
    timestamp_to: Optional[datetime] = None
    user_id: Optional[str] = None

class ScanSensitiveDataRequest(BaseModel):
    text: str
    data_types: List[str] = ["email", "phone", "ssn"]

class CreateTaskRequest(BaseModel):
    title: str
    description: str
    assignee: str
    due_date: Optional[datetime] = None

class SendNotificationRequest(BaseModel):
    recipients: List[str] = []  # Optional - will use default if empty
    message: str
    channel: str = "line"  # "email", "slack", "teams", "line"
    priority: str = "normal"

class ScheduleMeetingRequest(BaseModel):
    participants: List[str]
    duration: int  # minutes
    time_preferences: List[datetime]

class CallAPIRequest(BaseModel):
    url: str
    method: str = "GET"
    headers: Optional[Dict] = {}
    body: Optional[Dict] = None

class ExecuteSQLRequest(BaseModel):
    query: str
    database: str = "default"
    timeout: int = 30

class RunScriptRequest(BaseModel):
    script_code: str
    input_params: Optional[Dict] = {}
    timeout: int = 30

class SendEmailRequest(BaseModel):
    to: List[str]
    subject: str
    body: str
    attachments: Optional[List[str]] = []

class SlackMessageRequest(BaseModel):
    channel: str
    message: str
    attachments: Optional[List[Dict]] = []

class UploadFileRequest(BaseModel):
    file_name: str
    file_data: str  # base64
    folder: str = "/"

class DownloadFileRequest(BaseModel):
    file_id: str
    destination: Optional[str] = None

class ListFilesRequest(BaseModel):
    folder_path: str = "/"
    filter: Optional[str] = None
    sort_by: str = "name"

class CalculateMetricsRequest(BaseModel):
    metric_type: str  # "revenue", "growth", "retention"
    data_range: Dict
    dimensions: Optional[List[str]] = []

class FinancialCalculatorRequest(BaseModel):
    operation: str  # "roi", "npv", "irr"
    values: Dict

class ReviewContractRequest(BaseModel):
    contract_content: str
    contract_name: Optional[str] = "Untitled Contract"
    contract_type: Optional[str] = None

class AnalyzeClauseRequest(BaseModel):
    clause_text: str
    context: Optional[str] = ""

class CompareContractsRequest(BaseModel):
    contract_a: str
    contract_b: str

class OCRExtractPDFRequest(BaseModel):
    pdf_file: Optional[str] = None
    pdf_base64: Optional[str] = None
    force_ocr: bool = False
    use_gpu: bool = False

class OCRExtractImageRequest(BaseModel):
    image_file: Optional[str] = None
    image_base64: Optional[str] = None
    use_gpu: bool = False

class ToolResponse(BaseModel):
    tools: List[Dict]

# ==================== Startup/Shutdown ====================

@app.on_event("startup")
async def startup():
    global db_pool, vector_db, redis_client

    try:
        # 初始化PostgreSQL
        postgres_url = os.getenv("POSTGRES_URL", "postgresql://admin:password@postgres:5432/ai_platform")
        db_pool = await asyncpg.create_pool(postgres_url, min_size=2, max_size=10)
        logger.info("✓ PostgreSQL connected")

        # 初始化Qdrant
        qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        vector_db = QdrantClient(url=qdrant_url)
        logger.info("✓ Qdrant connected")

        # 初始化 RAG Service
        await rag_service.initialize()
        logger.info("✓ RAG Service initialized")

        # 初始化Redis
        redis_url = os.getenv("REDIS_URL", "redis://:password@redis:6379")
        redis_client = await redis.from_url(redis_url, decode_responses=True)
        logger.info("✓ Redis connected")

    except Exception as e:
        logger.error(f"Startup error: {e}")

@app.on_event("shutdown")
async def shutdown():
    if db_pool:
        await db_pool.close()
    if redis_client:
        await redis_client.close()

# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "services": {}
    }

    # 檢查PostgreSQL
    try:
        if db_pool:
            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            health_status["services"]["postgres"] = "connected"
        else:
            health_status["services"]["postgres"] = "not initialized"
    except Exception as e:
        health_status["services"]["postgres"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    # 檢查Redis
    try:
        if redis_client:
            await redis_client.ping()
            health_status["services"]["redis"] = "connected"
        else:
            health_status["services"]["redis"] = "not initialized"
    except Exception as e:
        health_status["services"]["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    return health_status

# ==================== Tools List ====================

@app.get("/tools/list", response_model=ToolResponse)
async def list_tools():
    """列出所有可用工具"""
    return {
        "tools": [
            # Original 3 tools
            {
                "name": "search_knowledge_base",
                "description": "搜尋企業知識庫",
                "category": "search",
                "parameters": {"query": "string", "collection": "string", "limit": "integer"}
            },
            {
                "name": "query_database",
                "description": "查詢企業資料庫",
                "category": "database",
                "parameters": {"query_type": "string", "parameters": "object"}
            },
            {
                "name": "get_document",
                "description": "獲取文件內容",
                "category": "document",
                "parameters": {"document_id": "integer"}
            },
            # Data Analysis & Processing (3)
            {
                "name": "analyze_data",
                "description": "分析數據集並生成統計洞察",
                "category": "analysis",
                "parameters": {"data_source": "string", "analysis_type": "string", "options": "object"}
            },
            {
                "name": "generate_chart",
                "description": "從數據創建可視化圖表",
                "category": "visualization",
                "parameters": {"data": "array", "chart_type": "string", "title": "string"}
            },
            {
                "name": "process_csv",
                "description": "處理和轉換CSV文件",
                "category": "data_processing",
                "parameters": {"csv_data": "string", "operation": "string", "params": "object"}
            },
            # Search & Retrieval (3)
            {
                "name": "semantic_search",
                "description": "AI驅動的語義搜索",
                "category": "search",
                "parameters": {"query": "string", "similarity_threshold": "float", "top_k": "integer"}
            },
            {
                "name": "web_search",
                "description": "Enhanced web search with RAG - Search across multiple providers (Google/DuckDuckGo/Tavily/SerpAPI), vectorize results, and mix with knowledge base documents for comprehensive AI-powered answers",
                "category": "search",
                "parameters": {
                    "query": "string",
                    "num_results": "integer",
                    "use_rag": "boolean (default: true)",
                    "mix_with_documents": "boolean (default: true)",
                    "providers": "list[string] (optional: duckduckgo, google, tavily, serpapi)"
                }
            },
            {
                "name": "find_similar_documents",
                "description": "查找相似文檔",
                "category": "search",
                "parameters": {"document_id": "integer", "similarity_threshold": "float"}
            },
            # Content Generation (3)
            {
                "name": "summarize_document",
                "description": "生成文檔摘要",
                "category": "content",
                "parameters": {"document_id": "integer", "summary_length": "integer", "language": "string"}
            },
            {
                "name": "translate_text",
                "description": "翻譯文本",
                "category": "content",
                "parameters": {"text": "string", "source_lang": "string", "target_lang": "string"}
            },
            {
                "name": "generate_report",
                "description": "從數據生成格式化報告",
                "category": "content",
                "parameters": {"template": "string", "data": "object", "output_format": "string"}
            },
            # Security & Compliance (3)
            {
                "name": "check_permissions",
                "description": "驗證用戶訪問權限",
                "category": "security",
                "parameters": {"user_id": "string", "resource_id": "string"}
            },
            {
                "name": "audit_log",
                "description": "記錄和查詢系統審計日誌",
                "category": "security",
                "parameters": {"action_type": "string", "timestamp_range": "object", "user_id": "string"}
            },
            {
                "name": "scan_sensitive_data",
                "description": "檢測敏感信息",
                "category": "security",
                "parameters": {"text": "string", "data_types": "array"}
            },
            # Business Process (3)
            {
                "name": "create_task",
                "description": "創建項目任務",
                "category": "workflow",
                "parameters": {"title": "string", "description": "string", "assignee": "string", "due_date": "datetime"}
            },
            {
                "name": "send_notification",
                "description": "發送通知到 Line/Email/Slack (支援預設收件人)",
                "category": "communication",
                "parameters": {
                    "recipients": "array (optional - 留空使用預設收件人)",
                    "message": "string",
                    "channel": "string (line/email/slack)",
                    "priority": "string"
                }
            },
            {
                "name": "schedule_meeting",
                "description": "安排會議",
                "category": "workflow",
                "parameters": {"participants": "array", "duration": "integer", "time_preferences": "array"}
            },
            # System Integration (3)
            {
                "name": "call_api",
                "description": "調用外部API",
                "category": "integration",
                "parameters": {"url": "string", "method": "string", "headers": "object", "body": "object"}
            },
            {
                "name": "execute_sql",
                "description": "執行只讀SQL查詢",
                "category": "database",
                "parameters": {"query": "string", "database": "string", "timeout": "integer"}
            },
            {
                "name": "run_script",
                "description": "在沙箱中執行Python腳本",
                "category": "execution",
                "parameters": {"script_code": "string", "input_params": "object", "timeout": "integer"}
            },
            # Communication (2)
            {
                "name": "send_email",
                "description": "發送郵件",
                "category": "communication",
                "parameters": {"to": "array", "subject": "string", "body": "string", "attachments": "array"}
            },
            {
                "name": "create_slack_message",
                "description": "發送Slack消息",
                "category": "communication",
                "parameters": {"channel": "string", "message": "string", "attachments": "array"}
            },
            # File Management (3)
            {
                "name": "upload_file",
                "description": "上傳文件到存儲",
                "category": "file",
                "parameters": {"file_name": "string", "file_data": "string", "folder": "string"}
            },
            {
                "name": "download_file",
                "description": "從存儲下載文件",
                "category": "file",
                "parameters": {"file_id": "string", "destination": "string"}
            },
            {
                "name": "list_files",
                "description": "列出文件夾中的文件",
                "category": "file",
                "parameters": {"folder_path": "string", "filter": "string", "sort_by": "string"}
            },
            # Calculation (2)
            {
                "name": "calculate_metrics",
                "description": "計算業務KPI",
                "category": "analytics",
                "parameters": {"metric_type": "string", "data_range": "object", "dimensions": "array"}
            },
            {
                "name": "financial_calculator",
                "description": "執行財務計算",
                "category": "finance",
                "parameters": {"operation": "string", "values": "object"}
            },
            # Contract Review Tools (3)
            {
                "name": "review_contract",
                "description": "全面審查和分析合約的風險、合規性和公平性",
                "category": "legal",
                "parameters": {
                    "contract_content": "string (required)",
                    "contract_name": "string (optional)",
                    "contract_type": "string (optional: employment/nda/service/lease/sales/general)"
                }
            },
            {
                "name": "analyze_clause",
                "description": "詳細分析特定合約條款",
                "category": "legal",
                "parameters": {
                    "clause_text": "string (required)",
                    "context": "string (optional)"
                }
            },
            {
                "name": "compare_contracts",
                "description": "比較兩份合約並突出關鍵差異",
                "category": "legal",
                "parameters": {
                    "contract_a": "string (required)",
                    "contract_b": "string (required)"
                }
            },
            # OCR Tools (3)
            {
                "name": "ocr_extract_pdf",
                "description": "從PDF文件中提取文本（自動檢測掃描或文本型PDF）",
                "category": "document",
                "parameters": {
                    "pdf_file": "string (optional: path to PDF)",
                    "pdf_base64": "string (optional: base64 encoded PDF)",
                    "force_ocr": "boolean (optional: force OCR even for text PDFs)",
                    "use_gpu": "boolean (optional: use GPU-based OCR if available)"
                }
            },
            {
                "name": "ocr_extract_image",
                "description": "從圖像文件中提取文本（PNG, JPG等）",
                "category": "document",
                "parameters": {
                    "image_file": "string (optional: path to image)",
                    "image_base64": "string (optional: base64 encoded image)",
                    "use_gpu": "boolean (optional: use GPU-based OCR if available)"
                }
            },
            {
                "name": "ocr_get_status",
                "description": "獲取OCR服務狀態和可用後端",
                "category": "system",
                "parameters": {}
            }
        ]
    }

# ==================== Original 3 Tools (Enhanced) ====================

@app.post("/tools/search")
async def search_knowledge_base(request: SearchRequest):
    """搜尋知識庫"""
    try:
        cache_key = f"search:{request.collection}:{request.query}"
        cached = await redis_client.get(cache_key)

        if cached:
            logger.info(f"Cache hit for query: {request.query}")
            return json.loads(cached)

        results = []
        if db_pool:
            async with db_pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT title, content, metadata FROM documents WHERE content ILIKE $1 LIMIT $2",
                    f"%{request.query}%",
                    request.limit
                )

                for row in rows:
                    results.append({
                        "content": row["content"],
                        "title": row["title"],
                        "score": 0.8,
                        "metadata": row["metadata"]
                    })

        response = {"results": results, "count": len(results)}

        if results:
            await redis_client.setex(cache_key, 300, json.dumps(response))

        return response

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/resources/document/{doc_id}")
async def get_document(doc_id: int):
    """獲取文件"""
    try:
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database not available")

        async with db_pool.acquire() as conn:
            doc = await conn.fetchrow(
                "SELECT * FROM documents WHERE id = $1",
                doc_id
            )

            if not doc:
                raise HTTPException(status_code=404, detail="Document not found")

            return {
                "id": doc["id"],
                "title": doc["title"],
                "content": doc["content"],
                "metadata": doc["metadata"],
                "created_at": doc["created_at"].isoformat() if doc["created_at"] else None
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Data Analysis & Processing Tools ====================

@app.post("/tools/analyze_data")
async def analyze_data(request: AnalyzeDataRequest):
    """分析數據並生成統計洞察"""
    try:
        # Simplified implementation - would connect to actual data sources
        analysis_results = {
            "data_source": request.data_source,
            "analysis_type": request.analysis_type,
            "results": {
                "mean": 42.5,
                "median": 40.0,
                "std_dev": 12.3,
                "count": 100,
                "min": 10,
                "max": 85
            },
            "timestamp": datetime.now().isoformat()
        }

        return analysis_results
    except Exception as e:
        logger.error(f"Analyze data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/generate_chart")
async def generate_chart(request: GenerateChartRequest):
    """生成圖表"""
    try:
        # Return chart configuration that frontend can render
        chart_config = {
            "type": request.chart_type,
            "title": request.title,
            "data": request.data,
            "options": {
                "x_field": request.x_field,
                "y_field": request.y_field
            },
            "generated_at": datetime.now().isoformat()
        }

        return chart_config
    except Exception as e:
        logger.error(f"Generate chart error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/process_csv")
async def process_csv(request: CSVProcessRequest):
    """處理CSV數據"""
    try:
        # Decode base64 CSV data
        csv_bytes = base64.b64decode(request.csv_data)
        df = pd.read_csv(io.BytesIO(csv_bytes))

        if request.operation == "filter":
            # Apply filter from params
            column = request.params.get("column")
            value = request.params.get("value")
            if column and value:
                df = df[df[column] == value]
        elif request.operation == "sort":
            column = request.params.get("column", df.columns[0])
            ascending = request.params.get("ascending", True)
            df = df.sort_values(by=column, ascending=ascending)
        elif request.operation == "aggregate":
            group_by = request.params.get("group_by")
            agg_func = request.params.get("function", "sum")
            if group_by:
                df = df.groupby(group_by).agg(agg_func)

        # Convert back to dict
        result_data = df.to_dict(orient="records")

        return {
            "operation": request.operation,
            "rows_processed": len(result_data),
            "data": result_data[:100]  # Limit to first 100 rows
        }
    except Exception as e:
        logger.error(f"Process CSV error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Search & Retrieval Tools ====================

@app.post("/tools/semantic_search")
async def semantic_search(request: SemanticSearchRequest):
    """AI驅動的語義搜索"""
    try:
        # Simplified - would use vector embeddings in production
        results = [
            {
                "document_id": 1,
                "title": "Semantic Match 1",
                "content": f"Content related to: {request.query}",
                "similarity_score": 0.92
            },
            {
                "document_id": 2,
                "title": "Semantic Match 2",
                "content": f"Another document about: {request.query}",
                "similarity_score": 0.85
            }
        ]

        # Filter by threshold
        filtered_results = [r for r in results if r["similarity_score"] >= request.similarity_threshold]

        return {"results": filtered_results[:request.top_k]}
    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/web_search")
async def web_search(request: WebSearchRequest):
    """
    Enhanced web search with RAG integration

    Features:
    - Multi-provider search (Google, DuckDuckGo, Tavily)
    - Temporary vectorization of results
    - Mixed retrieval with existing documents
    - AI-optimized answer generation
    """
    try:
        start_time = datetime.now()

        # Step 1: Perform web search across providers
        search_results = await search_service.search(
            query=request.query,
            max_results=request.num_results,
            providers=request.providers
        )

        web_results = search_results.get("results", [])
        logger.info(f"Retrieved {len(web_results)} results from {search_results.get('providers_used', [])}")

        # Step 2: If RAG is enabled, vectorize and search with semantic similarity
        if request.use_rag and web_results:
            # Vectorize web search snippets temporarily (not stored in Qdrant)
            web_embeddings = []
            for result in web_results:
                snippet = result.get("snippet", "")
                if snippet:
                    try:
                        embedding = await rag_service.generate_embedding(snippet)
                        web_embeddings.append({
                            "result": result,
                            "embedding": embedding
                        })
                    except Exception as e:
                        logger.warning(f"Failed to vectorize result: {e}")

            # Step 3: Mix with existing documents if enabled
            mixed_results = []

            if request.mix_with_documents:
                try:
                    # Search existing documents using semantic search
                    doc_results = await rag_service.semantic_search(
                        query=request.query,
                        limit=request.num_results,
                        score_threshold=0.6
                    )

                    # Add document results
                    for doc in doc_results:
                        mixed_results.append({
                            "title": doc.get("title", ""),
                            "url": "",  # Local document, no URL
                            "snippet": doc.get("content", ""),
                            "source": "Knowledge Base",
                            "score": doc.get("score", 0.0),
                            "doc_id": doc.get("doc_id"),
                            "type": "document"
                        })

                    logger.info(f"Added {len(doc_results)} results from knowledge base")
                except Exception as e:
                    logger.warning(f"Failed to retrieve documents: {e}")

            # Add web results
            for web_data in web_embeddings:
                result = web_data["result"]
                result["type"] = "web"
                mixed_results.append(result)

            # Sort by relevance (if scores available) or keep original order
            mixed_results.sort(key=lambda x: x.get("score", 0.5), reverse=True)

            # Limit total results
            final_results = mixed_results[:request.num_results * 2]

        else:
            # No RAG, just return web results
            final_results = web_results

        # Calculate search time
        search_time = (datetime.now() - start_time).total_seconds()

        return {
            "query": request.query,
            "results": final_results,
            "total_results": len(final_results),
            "web_results_count": len(web_results),
            "document_results_count": len([r for r in final_results if r.get("type") == "document"]),
            "providers_used": search_results.get("providers_used", []),
            "rag_enabled": request.use_rag,
            "mixed_with_documents": request.mix_with_documents,
            "search_time": f"{search_time:.2f}s",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Web search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools/find_similar_documents/{document_id}")
async def find_similar_documents(document_id: int, similarity_threshold: float = 0.7):
    """查找相似文檔"""
    try:
        similar_docs = [
            {
                "document_id": document_id + i,
                "title": f"Similar Document {i+1}",
                "similarity_score": 0.9 - (i * 0.1)
            }
            for i in range(1, 4)
        ]

        filtered = [d for d in similar_docs if d["similarity_score"] >= similarity_threshold]

        return {"source_document_id": document_id, "similar_documents": filtered}
    except Exception as e:
        logger.error(f"Find similar documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Content Generation Tools ====================

@app.post("/tools/summarize_document")
async def summarize_document(request: SummarizeRequest):
    """文檔摘要"""
    try:
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database not available")

        async with db_pool.acquire() as conn:
            doc = await conn.fetchrow(
                "SELECT content, title FROM documents WHERE id = $1",
                request.document_id
            )

            if not doc:
                raise HTTPException(status_code=404, detail="Document not found")

            # Simplified summarization
            content = doc["content"]
            summary = content[:request.summary_length] + "..." if len(content) > request.summary_length else content

            return {
                "document_id": request.document_id,
                "title": doc["title"],
                "summary": summary,
                "language": request.language,
                "original_length": len(content),
                "summary_length": len(summary)
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Summarize document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/translate_text")
async def translate_text(request: TranslateRequest):
    """文本翻譯"""
    try:
        # Simulated translation
        translations = {
            "zh-TW_en": "Translated to English",
            "en_zh-TW": "翻譯成繁體中文",
            "zh-TW_vi": "Dịch sang tiếng Việt"
        }

        key = f"{request.source_lang}_{request.target_lang}"
        translated_text = translations.get(key, f"[Translated from {request.source_lang} to {request.target_lang}]: {request.text}")

        return {
            "original_text": request.text,
            "translated_text": translated_text,
            "source_lang": request.source_lang,
            "target_lang": request.target_lang
        }
    except Exception as e:
        logger.error(f"Translate text error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/generate_report")
async def generate_report(request: GenerateReportRequest):
    """生成報告"""
    try:
        report_content = f"""
        <html>
        <head><title>Report: {request.template}</title></head>
        <body>
        <h1>{request.template}</h1>
        <div>{json.dumps(request.data, indent=2)}</div>
        <footer>Generated at {datetime.now().isoformat()}</footer>
        </body>
        </html>
        """

        return {
            "template": request.template,
            "output_format": request.output_format,
            "content": report_content if request.output_format == "html" else base64.b64encode(report_content.encode()).decode(),
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Generate report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Security & Compliance Tools ====================

@app.post("/tools/check_permissions")
async def check_permissions(request: CheckPermissionsRequest):
    """檢查權限"""
    try:
        # Simulated permission check
        has_permission = True  # In production, check against ACL

        return {
            "user_id": request.user_id,
            "resource_id": request.resource_id,
            "has_permission": has_permission,
            "permissions": ["read", "write"],
            "checked_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Check permissions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/audit_log")
async def audit_log(request: AuditLogRequest):
    """審計日誌"""
    try:
        # Simulated audit log entries
        logs = [
            {
                "id": i,
                "action_type": request.action_type or "access",
                "user_id": request.user_id or f"user_{i}",
                "timestamp": (datetime.now() - timedelta(hours=i)).isoformat(),
                "details": f"Action details {i}"
            }
            for i in range(5)
        ]

        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        logger.error(f"Audit log error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/scan_sensitive_data")
async def scan_sensitive_data(request: ScanSensitiveDataRequest):
    """掃描敏感數據"""
    try:
        import re

        findings = []

        if "email" in request.data_types:
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', request.text)
            if emails:
                findings.append({"type": "email", "count": len(emails), "samples": emails[:3]})

        if "phone" in request.data_types:
            phones = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', request.text)
            if phones:
                findings.append({"type": "phone", "count": len(phones), "samples": phones[:3]})

        if "ssn" in request.data_types:
            ssns = re.findall(r'\b\d{3}-\d{2}-\d{4}\b', request.text)
            if ssns:
                findings.append({"type": "ssn", "count": len(ssns), "samples": ["***-**-****"] * len(ssns)})

        return {
            "text_length": len(request.text),
            "findings": findings,
            "has_sensitive_data": len(findings) > 0,
            "scanned_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Scan sensitive data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Business Process Tools ====================

@app.post("/tools/create_task")
async def create_task(request: CreateTaskRequest):
    """創建任務"""
    try:
        task_id = f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        task = {
            "id": task_id,
            "title": request.title,
            "description": request.description,
            "assignee": request.assignee,
            "due_date": request.due_date.isoformat() if request.due_date else None,
            "status": "open",
            "created_at": datetime.now().isoformat()
        }

        return task
    except Exception as e:
        logger.error(f"Create task error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/send_notification")
async def send_notification(request: SendNotificationRequest):
    """發送通知 - 支援 Line, Email, Slack 等多種通道"""
    try:
        notification_id = f"NOTIF-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Handle Line messaging
        if request.channel.lower() == "line":
            line_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
            if not line_token:
                raise HTTPException(status_code=500, detail="LINE_CHANNEL_ACCESS_TOKEN not configured")

            # Use default recipient if none provided
            recipients = request.recipients
            if not recipients:
                default_recipient = os.getenv("LINE_DEFAULT_RECIPIENT_ID", "").strip()
                if default_recipient:
                    recipients = [default_recipient]
                    logger.info(f"Using default LINE recipient: {default_recipient}")
                else:
                    raise HTTPException(status_code=400, detail="No recipients provided and LINE_DEFAULT_RECIPIENT_ID not set")

            # Send to each recipient
            results = []
            async with httpx.AsyncClient() as client:
                for recipient_id in recipients:
                    try:
                        # Determine if it's a user or group message
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

                        response = await client.post(endpoint, json=payload, headers=headers)

                        if response.status_code == 200:
                            logger.info(f"✅ LINE message sent successfully to {recipient_id}")
                            results.append({
                                "recipient": recipient_id,
                                "status": "sent",
                                "status_code": response.status_code
                            })
                        else:
                            logger.error(f"❌ LINE API error for {recipient_id}: {response.status_code} - {response.text}")
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

            return {
                "notification_id": notification_id,
                "channel": "line",
                "recipients": recipients,
                "results": results,
                "priority": request.priority,
                "sent_at": datetime.now().isoformat()
            }

        # Other channels (email, slack, teams) - stub for now
        else:
            return {
                "notification_id": notification_id,
                "recipients": request.recipients,
                "channel": request.channel,
                "priority": request.priority,
                "status": "sent",
                "sent_at": datetime.now().isoformat(),
                "note": f"Channel '{request.channel}' not yet fully implemented"
            }

    except Exception as e:
        logger.error(f"Send notification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/schedule_meeting")
async def schedule_meeting(request: ScheduleMeetingRequest):
    """安排會議"""
    try:
        # Select first available time
        selected_time = request.time_preferences[0] if request.time_preferences else datetime.now() + timedelta(days=1)

        meeting = {
            "meeting_id": f"MEET-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "participants": request.participants,
            "duration": request.duration,
            "scheduled_time": selected_time.isoformat() if isinstance(selected_time, datetime) else selected_time,
            "end_time": (selected_time + timedelta(minutes=request.duration)).isoformat() if isinstance(selected_time, datetime) else None,
            "status": "scheduled"
        }

        return meeting
    except Exception as e:
        logger.error(f"Schedule meeting error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== System Integration Tools ====================

@app.post("/tools/call_api")
async def call_api(request: CallAPIRequest):
    """調用外部API"""
    try:
        async with httpx.AsyncClient() as client:
            if request.method.upper() == "GET":
                response = await client.get(request.url, headers=request.headers, timeout=30)
            elif request.method.upper() == "POST":
                response = await client.post(request.url, headers=request.headers, json=request.body, timeout=30)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported method: {request.method}")

            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text[:1000],  # Limit response size
                "called_at": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Call API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/execute_sql")
async def execute_sql(request: ExecuteSQLRequest):
    """執行SQL查詢"""
    try:
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database not available")

        # Only allow SELECT queries for safety
        if not request.query.strip().upper().startswith("SELECT"):
            raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")

        async with db_pool.acquire() as conn:
            rows = await conn.fetch(request.query)

            results = [dict(row) for row in rows]

            return {
                "query": request.query,
                "rows_returned": len(results),
                "results": results[:100],  # Limit to first 100 rows
                "executed_at": datetime.now().isoformat()
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Execute SQL error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/run_script")
async def run_script(request: RunScriptRequest):
    """執行Python腳本"""
    try:
        # For security, this is a simulated sandbox execution
        # In production, use proper sandboxing like docker containers

        result = {
            "status": "success",
            "output": f"Script executed successfully with params: {request.input_params}",
            "execution_time": 0.5,
            "executed_at": datetime.now().isoformat()
        }

        return result
    except Exception as e:
        logger.error(f"Run script error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Communication Tools ====================

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

            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_from
            msg['To'] = ', '.join(request.to)
            msg['Subject'] = request.subject

            # Add body
            msg.attach(MIMEText(request.body, 'plain'))

            # Send email
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
                raise HTTPException(status_code=500, detail=f"Failed to send email: {str(smtp_error)}")
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send email error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/create_slack_message")
async def create_slack_message(request: SlackMessageRequest):
    """發送Slack消息"""
    try:
        message_id = f"SLACK-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        return {
            "message_id": message_id,
            "channel": request.channel,
            "status": "posted",
            "posted_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Create Slack message error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== File Management Tools ====================

@app.post("/tools/upload_file")
async def upload_file(request: UploadFileRequest):
    """上傳文件"""
    try:
        file_id = f"FILE-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Decode base64 file data
        file_bytes = base64.b64decode(request.file_data)
        file_size = len(file_bytes)

        # In production, save to actual storage (S3, MinIO, etc.)

        return {
            "file_id": file_id,
            "file_name": request.file_name,
            "folder": request.folder,
            "size": file_size,
            "uploaded_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Upload file error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/download_file")
async def download_file(request: DownloadFileRequest):
    """下載文件"""
    try:
        # In production, retrieve from actual storage
        file_data = base64.b64encode(b"Sample file content").decode()

        return {
            "file_id": request.file_id,
            "file_data": file_data,
            "downloaded_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Download file error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/list_files")
async def list_files(request: ListFilesRequest):
    """列出文件"""
    try:
        # Simulated file listing
        files = [
            {
                "file_id": f"FILE-{i}",
                "file_name": f"document{i}.pdf",
                "size": 1024 * (i + 1),
                "modified_at": (datetime.now() - timedelta(days=i)).isoformat()
            }
            for i in range(5)
        ]

        return {
            "folder_path": request.folder_path,
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        logger.error(f"List files error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Calculation Tools ====================

@app.post("/tools/calculate_metrics")
async def calculate_metrics(request: CalculateMetricsRequest):
    """計算業務指標"""
    try:
        metrics = {
            "metric_type": request.metric_type,
            "values": {
                "current": 125000,
                "previous": 100000,
                "growth_rate": 25.0,
                "trend": "increasing"
            },
            "data_range": request.data_range,
            "calculated_at": datetime.now().isoformat()
        }

        return metrics
    except Exception as e:
        logger.error(f"Calculate metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/financial_calculator")
async def financial_calculator(request: FinancialCalculatorRequest):
    """財務計算器"""
    try:
        result = 0.0

        if request.operation == "roi":
            # ROI = (Gain - Cost) / Cost * 100
            gain = request.values.get("gain", 0)
            cost = request.values.get("cost", 1)
            result = ((gain - cost) / cost) * 100
        elif request.operation == "npv":
            # Simplified NPV calculation
            cash_flows = request.values.get("cash_flows", [])
            rate = request.values.get("rate", 0.1)
            result = sum([cf / ((1 + rate) ** i) for i, cf in enumerate(cash_flows)])
        elif request.operation == "irr":
            # Simplified IRR - would use numerical methods in production
            result = 12.5  # percentage

        return {
            "operation": request.operation,
            "result": result,
            "values": request.values,
            "calculated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Financial calculator error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Contract Review Tools ====================

@app.post("/tools/review_contract")
async def review_contract(request: ReviewContractRequest):
    """全面審查合約 - 風險評估、合規性檢查、建議"""
    try:
        # Call the contract review tool
        result = await review_contract_tool(
            contract_content=request.contract_content,
            contract_name=request.contract_name,
            contract_type=request.contract_type,
            llm_client=None  # LLM client will be initialized within the tool
        )

        # Parse JSON result
        result_data = json.loads(result)

        logger.info(f"Contract review completed: {request.contract_name} (Risk Score: {result_data.get('risk_score', {}).get('score', 'N/A')})")

        return result_data

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse contract review result: {e}")
        return {"error": "Failed to parse review result", "raw_result": result}
    except Exception as e:
        logger.error(f"Review contract error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/analyze_clause")
async def analyze_clause(request: AnalyzeClauseRequest):
    """詳細分析特定合約條款"""
    try:
        # Call the clause analysis tool
        result = await analyze_clause_tool(
            clause_text=request.clause_text,
            context=request.context,
            llm_client=None  # LLM client will be initialized within the tool
        )

        # Parse JSON result
        result_data = json.loads(result)

        logger.info(f"Clause analysis completed")

        return result_data

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse clause analysis result: {e}")
        return {"error": "Failed to parse analysis result", "raw_result": result}
    except Exception as e:
        logger.error(f"Analyze clause error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/compare_contracts")
async def compare_contracts(request: CompareContractsRequest):
    """比較兩份合約並突出關鍵差異"""
    try:
        # Call the contract comparison tool
        result = await compare_contracts_tool(
            contract_a=request.contract_a,
            contract_b=request.contract_b,
            llm_client=None  # LLM client will be initialized within the tool
        )

        # Parse JSON result
        result_data = json.loads(result)

        logger.info(f"Contract comparison completed")

        return result_data

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse comparison result: {e}")
        return {"error": "Failed to parse comparison result", "raw_result": result}
    except Exception as e:
        logger.error(f"Compare contracts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== OCR Tools ====================

@app.post("/tools/ocr_extract_pdf")
async def ocr_extract_pdf(request: OCRExtractPDFRequest):
    """從PDF文件中提取文本 - 自動檢測掃描或文本型PDF"""
    try:
        result = await ocr_extract_pdf_tool(
            pdf_file=request.pdf_file,
            pdf_base64=request.pdf_base64,
            force_ocr=request.force_ocr,
            use_gpu=request.use_gpu
        )

        result_data = json.loads(result)
        logger.info(f"OCR PDF extraction completed: {result_data.get('file', 'unknown')} ({result_data.get('text_length', 0)} chars)")

        return result_data

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OCR result: {e}")
        return {"success": False, "error": "Failed to parse OCR result"}
    except Exception as e:
        logger.error(f"OCR PDF extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/ocr_extract_image")
async def ocr_extract_image(request: OCRExtractImageRequest):
    """從圖像文件中提取文本"""
    try:
        result = await ocr_extract_image_tool(
            image_file=request.image_file,
            image_base64=request.image_base64,
            use_gpu=request.use_gpu
        )

        result_data = json.loads(result)
        logger.info(f"OCR image extraction completed: {result_data.get('file', 'unknown')} ({result_data.get('text_length', 0)} chars)")

        return result_data

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OCR result: {e}")
        return {"success": False, "error": "Failed to parse OCR result"}
    except Exception as e:
        logger.error(f"OCR image extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools/ocr_get_status")
async def ocr_get_status():
    """獲取OCR服務狀態和可用後端"""
    try:
        result = await ocr_get_status_tool()
        result_data = json.loads(result)

        logger.info("OCR status retrieved successfully")

        return result_data

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OCR status: {e}")
        return {"ocr_available": False, "error": "Failed to parse status"}
    except Exception as e:
        logger.error(f"OCR status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Enterprise RAG APIs ====================

@app.post("/rag/documents/upload")
async def upload_document(file: UploadFile = File(...), category: Optional[str] = None, tags: Optional[str] = None):
    """Upload and process document with RAG"""
    try:
        # Read file content
        file_content = await file.read()

        # Extract text from file
        try:
            text_content = rag_service.extract_text_from_file(file_content, file.filename)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        if not text_content.strip():
            raise HTTPException(status_code=400, detail="No text content extracted from file")

        # Parse tags
        tag_list = [t.strip() for t in tags.split(",")] if tags else []

        # Store document in database
        async with db_pool.acquire() as conn:
            doc_id = await conn.fetchval(
                """
                INSERT INTO documents (title, content, category, tags, document_type, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
                """,
                file.filename,
                text_content,
                category,
                tag_list,
                file.content_type,
                json.dumps({"original_filename": file.filename, "size": len(file_content)})
            )

        # Process document with RAG (vectorization)
        chunks_count = await rag_service.process_document(
            doc_id=doc_id,
            title=file.filename,
            content=text_content,
            metadata={"category": category, "tags": tag_list}
        )

        logger.info(f"Document {doc_id} uploaded and processed: {chunks_count} chunks")

        return {
            "doc_id": doc_id,
            "title": file.filename,
            "content_length": len(text_content),
            "chunks_count": chunks_count,
            "category": category,
            "tags": tag_list,
            "status": "success"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/documents/text")
async def create_document_from_text(request: DocumentUploadRequest):
    """Create document from text with RAG"""
    try:
        if not request.content:
            raise HTTPException(status_code=400, detail="Content is required")

        # Store document in database
        async with db_pool.acquire() as conn:
            doc_id = await conn.fetchval(
                """
                INSERT INTO documents (title, content, category, tags, metadata)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                request.title,
                request.content,
                request.category,
                request.tags,
                json.dumps(request.metadata)
            )

        # Process document with RAG
        chunks_count = await rag_service.process_document(
            doc_id=doc_id,
            title=request.title,
            content=request.content,
            metadata=request.metadata
        )

        logger.info(f"Document {doc_id} created and processed: {chunks_count} chunks")

        return {
            "doc_id": doc_id,
            "title": request.title,
            "content_length": len(request.content),
            "chunks_count": chunks_count,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Document creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rag/documents")
async def list_documents(
    skip: int = 0,
    limit: int = 20,
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """List documents with optional filtering"""
    try:
        async with db_pool.acquire() as conn:
            query = "SELECT id, title, category, tags, created_at, updated_at FROM documents WHERE 1=1"
            params = []
            param_count = 0

            if category:
                param_count += 1
                query += f" AND category = ${param_count}"
                params.append(category)

            if search:
                param_count += 1
                query += f" AND (title ILIKE ${param_count} OR content ILIKE ${param_count})"
                params.append(f"%{search}%")

            query += f" ORDER BY created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
            params.extend([limit, skip])

            rows = await conn.fetch(query, *params)

            documents = []
            for row in rows:
                documents.append({
                    "id": row["id"],
                    "title": row["title"],
                    "category": row["category"],
                    "tags": row["tags"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None
                })

            # Get total count
            count_query = "SELECT COUNT(*) FROM documents WHERE 1=1"
            count_params = []
            if category:
                count_query += " AND category = $1"
                count_params.append(category)
            if search:
                idx = len(count_params) + 1
                count_query += f" AND (title ILIKE ${idx} OR content ILIKE ${idx})"
                count_params.append(f"%{search}%")

            total = await conn.fetchval(count_query, *count_params)

            return {
                "documents": documents,
                "total": total,
                "skip": skip,
                "limit": limit
            }

    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rag/documents/{doc_id}")
async def get_document_detail(doc_id: int):
    """Get document details"""
    try:
        async with db_pool.acquire() as conn:
            doc = await conn.fetchrow(
                "SELECT * FROM documents WHERE id = $1",
                doc_id
            )

            if not doc:
                raise HTTPException(status_code=404, detail="Document not found")

            return {
                "id": doc["id"],
                "title": doc["title"],
                "content": doc["content"],
                "category": doc["category"],
                "tags": doc["tags"],
                "metadata": doc["metadata"],
                "created_at": doc["created_at"].isoformat() if doc["created_at"] else None,
                "updated_at": doc["updated_at"].isoformat() if doc["updated_at"] else None
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/rag/documents/{doc_id}")
async def update_document(doc_id: int, request: DocumentUpdateRequest):
    """Update document"""
    try:
        async with db_pool.acquire() as conn:
            # Check if document exists
            doc = await conn.fetchrow("SELECT id, content FROM documents WHERE id = $1", doc_id)
            if not doc:
                raise HTTPException(status_code=404, detail="Document not found")

            # Build update query
            updates = []
            params = []
            param_count = 0

            if request.title is not None:
                param_count += 1
                updates.append(f"title = ${param_count}")
                params.append(request.title)

            if request.content is not None:
                param_count += 1
                updates.append(f"content = ${param_count}")
                params.append(request.content)

            if request.category is not None:
                param_count += 1
                updates.append(f"category = ${param_count}")
                params.append(request.category)

            if request.tags is not None:
                param_count += 1
                updates.append(f"tags = ${param_count}")
                params.append(request.tags)

            if request.metadata is not None:
                param_count += 1
                updates.append(f"metadata = ${param_count}")
                params.append(json.dumps(request.metadata))

            if request.is_published is not None:
                param_count += 1
                updates.append(f"is_published = ${param_count}")
                params.append(request.is_published)

            if not updates:
                raise HTTPException(status_code=400, detail="No updates provided")

            param_count += 1
            params.append(doc_id)
            query = f"UPDATE documents SET {', '.join(updates)} WHERE id = ${param_count}"

            await conn.execute(query, *params)

            # Re-process document if content changed
            if request.content is not None:
                await rag_service.delete_document_vectors(doc_id)
                await rag_service.process_document(
                    doc_id=doc_id,
                    title=request.title or "Untitled",
                    content=request.content,
                    metadata=request.metadata
                )

        return {"doc_id": doc_id, "status": "updated"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/rag/documents/{doc_id}")
async def delete_document(doc_id: int):
    """Delete document and its vectors"""
    try:
        async with db_pool.acquire() as conn:
            # Check if document exists
            doc = await conn.fetchrow("SELECT id FROM documents WHERE id = $1", doc_id)
            if not doc:
                raise HTTPException(status_code=404, detail="Document not found")

            # Delete from database
            await conn.execute("DELETE FROM documents WHERE id = $1", doc_id)

        # Delete vectors from Qdrant
        await rag_service.delete_document_vectors(doc_id)

        logger.info(f"Document {doc_id} deleted")

        return {"doc_id": doc_id, "status": "deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/search")
async def semantic_search(request: SemanticSearchRequest):
    """Semantic search using RAG"""
    try:
        results = await rag_service.semantic_search(
            query=request.query,
            limit=request.top_k,
            score_threshold=request.similarity_threshold,
            filter_metadata=request.filter_metadata
        )

        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }

    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rag/stats")
async def get_rag_stats():
    """Get RAG system statistics"""
    try:
        # Get document count from PostgreSQL
        async with db_pool.acquire() as conn:
            doc_count = await conn.fetchval("SELECT COUNT(*) FROM documents")
            published_count = await conn.fetchval("SELECT COUNT(*) FROM documents WHERE is_published = true")

        # Get vector stats from Qdrant
        vector_stats = await rag_service.get_collection_stats()

        return {
            "documents": {
                "total": doc_count,
                "published": published_count
            },
            "vectors": vector_stats
        }

    except Exception as e:
        logger.error(f"Get RAG stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Root ====================

@app.get("/")
async def root():
    return {
        "service": "MCP Server",
        "version": "2.0.0",
        "status": "running",
        "tools_count": 34,
        "features": ["Enterprise RAG", "Vector Search", "Document Management", "Contract Review", "OCR & Document Parsing"],
        "categories": [
            "search", "database", "document", "analysis", "visualization",
            "data_processing", "content", "security", "workflow", "communication",
            "integration", "execution", "file", "analytics", "finance", "legal", "rag", "system"
        ]
    }
