#!/bin/bash

echo "🔧 自動創建所有服務代碼..."

# ============================================
# 1. MCP Server
# ============================================
echo "創建 MCP Server..."

# Dockerfile
cat > services/mcp-server/Dockerfile << 'DOCKERFILE'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
DOCKERFILE

# requirements.txt
cat > services/mcp-server/requirements.txt << 'REQUIREMENTS'
fastapi==0.110.0
uvicorn[standard]==0.29.0
pydantic==2.7.0
pydantic-settings==2.2.1
asyncpg==0.29.0
qdrant-client==1.9.0
redis==5.0.3
aiohttp==3.9.5
python-multipart==0.0.9
REQUIREMENTS

# main.py
cat > services/mcp-server/main.py << 'MAINPY'
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncpg
from qdrant_client import QdrantClient
import redis.asyncio as redis
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP Server", version="1.0.0")

# 全局變量
db_pool = None
vector_db = None
redis_client = None

class SearchRequest(BaseModel):
    query: str
    collection: str = "documents"
    limit: int = 5

class SearchResult(BaseModel):
    content: str
    score: float
    metadata: Dict

class ToolResponse(BaseModel):
    tools: List[Dict]

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

@app.get("/tools/list", response_model=ToolResponse)
async def list_tools():
    """列出可用工具"""
    return {
        "tools": [
            {
                "name": "search_knowledge_base",
                "description": "搜尋企業知識庫",
                "parameters": {
                    "query": "string",
                    "collection": "string",
                    "limit": "integer"
                }
            },
            {
                "name": "query_database",
                "description": "查詢企業資料庫",
                "parameters": {
                    "query_type": "string",
                    "parameters": "object"
                }
            },
            {
                "name": "get_document",
                "description": "獲取文件內容",
                "parameters": {
                    "document_id": "string"
                }
            }
        ]
    }

@app.post("/tools/search", response_model=List[Dict])
async def search_knowledge_base(request: SearchRequest):
    """搜尋知識庫"""
    try:
        # 檢查快取
        cache_key = f"search:{request.collection}:{request.query}"
        cached = await redis_client.get(cache_key)
        
        if cached:
            import json
            logger.info(f"Cache hit for query: {request.query}")
            return json.loads(cached)
        
        # 從資料庫搜尋（簡化版）
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
        
        # 快取結果
        if results:
            import json
            await redis_client.setex(cache_key, 300, json.dumps(results))
        
        return results
        
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

@app.get("/")
async def root():
    return {
        "service": "MCP Server",
        "version": "1.0.0",
        "status": "running"
    }
MAINPY

echo "✓ MCP Server 創建完成"

# ============================================
# 2. Agent Service
# ============================================
echo "創建 Agent Service..."

# Dockerfile
cat > services/agent-service/Dockerfile << 'DOCKERFILE'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
DOCKERFILE

# requirements.txt
cat > services/agent-service/requirements.txt << 'REQUIREMENTS'
fastapi==0.110.0
uvicorn[standard]==0.29.0
langchain==0.2.0
langchain-openai==0.1.7
langchain-community==0.2.0
aiohttp==3.9.5
redis==5.0.3
pydantic==2.7.0
httpx==0.27.0
REQUIREMENTS

# main.py
cat > services/agent-service/main.py << 'MAINPY'
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import aiohttp
import os
import logging
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agent Service", version="1.0.0")

# 配置
LLM_PROXY_URL = os.getenv("LLM_PROXY_URL", "http://litellm:4000")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://mcp-server:8000")

class AgentRequest(BaseModel):
    task: str
    context: Optional[Dict] = None
    agent_type: str = "general"

class AgentResponse(BaseModel):
    result: str
    steps: List[Dict]
    metadata: Dict

class ChatRequest(BaseModel):
    message: str
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7

class ChatResponse(BaseModel):
    response: str
    model: str

@app.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "services": {}
    }
    
    # 檢查LLM服務
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{LLM_PROXY_URL}/health", timeout=5.0)
            if resp.status_code == 200:
                health_status["services"]["llm"] = "connected"
            else:
                health_status["services"]["llm"] = "unavailable"
                health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["llm"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # 檢查MCP服務
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{MCP_SERVER_URL}/health", timeout=5.0)
            if resp.status_code == 200:
                health_status["services"]["mcp"] = "connected"
            else:
                health_status["services"]["mcp"] = "unavailable"
                health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["mcp"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

@app.post("/agent/execute", response_model=AgentResponse)
async def execute_agent(request: AgentRequest):
    """執行Agent任務"""
    try:
        steps = []
        
        # Step 1: 呼叫MCP獲取工具
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{MCP_SERVER_URL}/tools/list", timeout=10.0)
                tools = resp.json()
                steps.append({
                    "step": "fetch_tools",
                    "result": f"Found {len(tools.get('tools', []))} tools",
                    "status": "success"
                })
        except Exception as e:
            steps.append({
                "step": "fetch_tools",
                "result": f"Failed: {str(e)}",
                "status": "failed"
            })
        
        # Step 2: 呼叫LLM處理任務
        try:
            async with httpx.AsyncClient() as client:
                llm_response = await client.post(
                    f"{LLM_PROXY_URL}/v1/chat/completions",
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {"role": "system", "content": "你是一個企業AI助手，幫助用戶完成各種任務。"},
                            {"role": "user", "content": request.task}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1000
                    },
                    timeout=30.0
                )
                
                llm_data = llm_response.json()
                result = llm_data["choices"][0]["message"]["content"]
                
                steps.append({
                    "step": "llm_processing",
                    "result": "Task processed successfully",
                    "status": "success"
                })
                
                return AgentResponse(
                    result=result,
                    steps=steps,
                    metadata={
                        "agent_type": request.agent_type,
                        "model_used": "gpt-3.5-turbo",
                        "tokens_used": llm_data.get("usage", {}).get("total_tokens", 0)
                    }
                )
                
        except Exception as e:
            logger.error(f"LLM processing error: {e}")
            steps.append({
                "step": "llm_processing",
                "result": f"Failed: {str(e)}",
                "status": "failed"
            })
            
            return AgentResponse(
                result=f"任務處理失敗: {str(e)}",
                steps=steps,
                metadata={
                    "agent_type": request.agent_type,
                    "error": str(e)
                }
            )
        
    except Exception as e:
        logger.error(f"Agent execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """簡單的聊天介面"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LLM_PROXY_URL}/v1/chat/completions",
                json={
                    "model": request.model,
                    "messages": [
                        {"role": "user", "content": request.message}
                    ],
                    "temperature": request.temperature
                },
                timeout=30.0
            )
            
            data = response.json()
            
            return ChatResponse(
                response=data["choices"][0]["message"]["content"],
                model=request.model
            )
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="LLM服務超時，請稍後再試")
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"聊天失敗: {str(e)}")

@app.get("/")
async def root():
    return {
        "service": "Agent Service",
        "version": "1.0.0",
        "status": "running",
        "llm_proxy": LLM_PROXY_URL,
        "mcp_server": MCP_SERVER_URL
    }
MAINPY

echo "✓ Agent Service 創建完成"

# ============================================
# 3. Web UI
# ============================================
echo "創建 Web UI..."

# Dockerfile
cat > services/web-ui/Dockerfile << 'DOCKERFILE'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
DOCKERFILE

# requirements.txt
cat > services/web-ui/requirements.txt << 'REQUIREMENTS'
streamlit==1.33.0
requests==2.31.0
pandas==2.2.1
plotly==5.20.0
REQUIREMENTS

# app.py
cat > services/web-ui/app.py << 'APPPY'
import streamlit as st
import requests
import os
import time

st.set_page_config(
    page_title="企業AI平台 MVP",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://agent-service:8000")
LITELLM_URL = os.getenv("LITELLM_URL", "http://litellm:4000")

# 自定義CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .status-healthy {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
    }
    .status-unhealthy {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🤖 企業AI共用平台 MVP</p>', unsafe_allow_html=True)

# 側邊欄
with st.sidebar:
    st.header("⚙️ 設定")
    
    model_choice = st.selectbox(
        "選擇模型",
        ["gpt-3.5-turbo", "gpt-4", "claude-3-sonnet", "llama3"],
        help="選擇要使用的LLM模型"
    )
    
    temperature = st.slider(
        "Temperature", 
        0.0, 1.0, 0.7,
        help="控制回答的創造性。較高的值會產生更多樣化的回答"
    )
    
    st.divider()
    
    # 系統狀態
    st.header("📊 系統狀態")
    
    with st.spinner("檢查服務狀態..."):
        # 檢查Agent服務
        try:
            resp = requests.get(f"{AGENT_SERVICE_URL}/health", timeout=3)
            if resp.ok:
                st.success("✅ Agent服務正常")
                health_data = resp.json()
                if "services" in health_data:
                    for service, status in health_data["services"].items():
                        if "connected" in str(status):
                            st.text(f"  └─ {service}: ✓")
                        else:
                            st.text(f"  └─ {service}: ✗")
            else:
                st.error("❌ Agent服務異常")
        except Exception as e:
            st.error(f"❌ Agent服務離線")
            st.caption(f"錯誤: {str(e)}")
    
    st.divider()
    
    # 快速操作
    st.header("🚀 快速操作")
    if st.button("🔄 清除對話記錄"):
        st.session_state.messages = []
        st.rerun()
    
    if st.button("📥 導出對話"):
        if "messages" in st.session_state and st.session_state.messages:
            conversation = "\n\n".join([
                f"{msg['role'].upper()}: {msg['content']}" 
                for msg in st.session_state.messages
            ])
            st.download_button(
                "下載對話記錄",
                conversation,
                file_name="conversation.txt",
                mime="text/plain"
            )
        else:
            st.info("暫無對話記錄")

# 主要內容
tab1, tab2, tab3, tab4 = st.tabs(["💬 對話", "🤖 Agent任務", "📊 監控", "ℹ️ 關於"])

with tab1:
    st.header("💬 AI對話介面")
    st.caption("與AI助手進行自然語言對話")
    
    # 初始化對話記錄
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # 顯示對話記錄
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 輸入框
    if prompt := st.chat_input("輸入您的問題..."):
        # 添加用戶消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 生成回覆
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                try:
                    start_time = time.time()
                    
                    response = requests.post(
                        f"{AGENT_SERVICE_URL}/agent/chat",
                        json={
                            "message": prompt,
                            "model": model_choice,
                            "temperature": temperature
                        },
                        timeout=60
                    )
                    
                    elapsed_time = time.time() - start_time
                    
                    if response.ok:
                        result = response.json()
                        answer = result["response"]
                        st.markdown(answer)
                        
                        # 顯示元數據
                        with st.expander("查看詳細資訊"):
                            st.json({
                                "model": result["model"],
                                "response_time": f"{elapsed_time:.2f}秒"
                            })
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer
                        })
                    else:
                        error_msg = f"❌ 錯誤: {response.text}"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg
                        })
                        
                except requests.exceptions.Timeout:
                    error_msg = "⏱️ 請求超時，請稍後再試"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
                except Exception as e:
                    error_msg = f"❌ 請求失敗: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })

with tab2:
    st.header("🤖 Agent任務執行")
    st.caption("執行複雜的多步驟AI任務")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        task = st.text_area(
            "描述您的任務",
            height=150,
            placeholder="例如：分析我們公司的季度銷售數據並生成報告"
        )
    
    with col2:
        agent_type = st.selectbox(
            "Agent類型",
            ["general", "research", "analysis"],
            help="選擇適合任務類型的Agent"
        )
        
        execute_button = st.button("▶️ 執行任務", use_container_width=True)
    
    if execute_button and task:
        with st.spinner("執行中，請稍候..."):
            try:
                start_time = time.time()
                
                response = requests.post(
                    f"{AGENT_SERVICE_URL}/agent/execute",
                    json={
                        "task": task,
                        "agent_type": agent_type
                    },
                    timeout=120
                )
                
                elapsed_time = time.time() - start_time
                
                if response.ok:
                    result = response.json()
                    
                    st.success(f"✅ 任務完成！(耗時: {elapsed_time:.2f}秒)")
                    
                    # 顯示結果
                    st.subheader("📄 執行結果")
                    st.write(result["result"])
                    
                    # 顯示執行步驟
                    with st.expander("🔍 查看執行步驟", expanded=True):
                        for i, step in enumerate(result["steps"], 1):
                            status_icon = "✅" if step.get("status") == "success" else "❌"
                            st.write(f"{status_icon} **步驟 {i}: {step['step']}**")
                            st.caption(step["result"])
                    
                    # 顯示元數據
                    with st.expander("ℹ️ 任務詳情"):
                        st.json(result["metadata"])
                else:
                    st.error(f"❌ 任務執行失敗: {response.text}")
                    
            except requests.exceptions.Timeout:
                st.error("⏱️ 任務執行超時，請嘗試簡化任務或稍後再試")
            except Exception as e:
                st.error(f"❌ 執行失敗: {str(e)}")
    
    elif execute_button:
        st.warning("⚠️ 請輸入任務描述")
    
    # 範例任務
    st.divider()
    st.subheader("💡 範例任務")
    
    examples = [
        "總結今天的重要新聞",
        "分析電商網站的用戶行為數據",
        "生成一份市場調研報告",
        "比較三種產品的特性和價格"
    ]
    
    cols = st.columns(2)
    for i, example in enumerate(examples):
        with cols[i % 2]:
            if st.button(f"📋 {example}", key=f"example_{i}"):
                st.rerun()

with tab3:
    st.header("📊 系統監控")
    st.caption("實時監控系統運行狀態")
    
    col1, col2, col3 = st.columns(3)
    
    # 模擬指標（實際應該從Prometheus獲取）
    with col1:
        st.metric(
            label="Agent服務",
            value="運行中",
            delta="正常"
        )
    
    with col2:
        st.metric(
            label="LLM服務",
            value="運行中",
            delta="正常"
        )
    
    with col3:
        st.metric(
            label="MCP服務",
            value="運行中",
            delta="正常"
        )
    
    st.divider()
    
    # 監控鏈接
    st.subheader("🔗 監控工具")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Grafana 儀表板**
        - 訪問地址: http://localhost:3000
        - 帳號: admin
        - 密碼: admin
        - 功能: 視覺化監控、告警設置
        """)
    
    with col2:
        st.markdown("""
        **Prometheus**
        - 訪問地址: http://localhost:9090
        - 功能: 指標查詢、時間序列分析
        """)
    
    st.info("💡 提示: 完整的監控功能請訪問 Grafana 儀表板")

with tab4:
    st.header("ℹ️ 關於本系統")
    
    st.markdown("""
    ### 🚀 企業AI共用平台 MVP
    
    這是一個基於開源技術構建的企業級AI平台，提供統一的LLM服務介面。
    
    #### 核心特性
    - 🔄 **混合部署**: 支援雲端和地端LLM
    - 🤖 **Agent框架**: 基於MCP和A2A協議
    - 📊 **完整監控**: Prometheus + Grafana
    - 🔒 **安全可靠**: 多層安全防護
    
    #### 技術架構
    - **前端**: Streamlit
    - **後端**: FastAPI
    - **LLM閘道**: LiteLLM
    - **本地推理**: Ollama
    - **資料庫**: PostgreSQL, Redis, Qdrant
    - **監控**: Prometheus, Grafana
    
    #### 支援的模型
    - OpenAI GPT系列
    - Anthropic Claude系列
    - 本地Llama模型
    - 其他開源模型
    
    #### 使用建議
    1. 首次使用建議選擇 gpt-3.5-turbo 快速測試
    2. 複雜任務可選擇 gpt-4 或 claude-3-opus
    3. 注重隱私可使用本地 llama3 模型
    
    #### 版本資訊
    - 版本: 1.0.0 (MVP)
    - 更新日期: 2024-10-15
    - 授權: MIT License
    """)
    
    st.divider()
    
    st.markdown("""
    ### 📞 技術支援
    
    如遇問題請查看：
    - 📖 文檔: 查看 `scripts/README.md`
    - 🔧 故障排查: 運行 `./scripts/troubleshoot.sh`
    - 📝 日誌分析: 運行 `./scripts/analyze-logs.sh`
    """)
APPPY

echo "✓ Web UI 創建完成"

echo ""
echo "🎉 所有服務代碼創建完成！"
echo ""
echo "文件清單:"
echo "  services/"
echo "  ├── mcp-server/"
echo "  │   ├── Dockerfile"
echo "  │   ├── requirements.txt"
echo "  │   └── main.py"
echo "  ├── agent-service/"
echo "  │   ├── Dockerfile"
echo "  │   ├── requirements.txt"
echo "  │   └── main.py"
echo "  └── web-ui/"
echo "      ├── Dockerfile"
echo "      ├── requirements.txt"
echo "      └── app.py"
echo ""
