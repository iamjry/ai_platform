from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import aiohttp
import os
import logging
import httpx
import json
from prometheus_fastapi_instrumentator import Instrumentator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agent Service", version="1.0.0")

# Setup Prometheus metrics
Instrumentator().instrument(app).expose(app)

# 配置
LLM_PROXY_URL = os.getenv("LLM_PROXY_URL", "http://litellm:4000")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://mcp-server:8000")
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "sk-1234")

class AgentRequest(BaseModel):
    task: str
    context: Optional[Dict] = None
    agent_type: str = "general"
    model: str = "qwen2.5"  # Default to local model
    conversation_history: Optional[List[Dict]] = None  # For multi-stage conversations
    images: Optional[List[Dict]] = None  # For vision models (base64 encoded images)
    temperature: float = 0.7  # Sampling temperature
    top_p: float = 0.9  # Nucleus sampling
    top_k: int = 40  # Top-k sampling

class AgentResponse(BaseModel):
    result: str
    steps: List[Dict]
    metadata: Dict
    needs_more_info: bool = False  # Indicates if agent needs more information
    missing_parameters: Optional[List[str]] = None  # What information is missing

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
            resp = await client.get(f"{LLM_PROXY_URL}/health/readiness", timeout=5.0)
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

async def call_mcp_tool(tool_name: str, arguments: Dict) -> Dict:
    """Call an MCP server tool"""
    # Map tool names to MCP endpoints
    endpoint_map = {
        "search_knowledge_base": "/tools/search",
        "get_document": lambda args: f"/resources/document/{args.get('document_id')}",
        "analyze_data": "/tools/analyze_data",
        "generate_chart": "/tools/generate_chart",
        "process_csv": "/tools/process_csv",
        "semantic_search": "/tools/semantic_search",
        "web_search": "/tools/web_search",
        "find_similar_documents": lambda args: f"/tools/find_similar_documents/{args.get('document_id')}",
        "summarize_document": "/tools/summarize_document",
        "translate_text": "/tools/translate_text",
        "generate_report": "/tools/generate_report",
        "check_permissions": "/tools/check_permissions",
        "audit_log": "/tools/audit_log",
        "scan_sensitive_data": "/tools/scan_sensitive_data",
        "create_task": "/tools/create_task",
        "send_notification": "/tools/send_notification",
        "schedule_meeting": "/tools/schedule_meeting",
        "call_api": "/tools/call_api",
        "execute_sql": "/tools/execute_sql",
        "run_script": "/tools/run_script",
        "send_email": "/tools/send_email",
        "create_slack_message": "/tools/create_slack_message",
        "upload_file": "/tools/upload_file",
        "download_file": "/tools/download_file",
        "list_files": "/tools/list_files",
        "calculate_metrics": "/tools/calculate_metrics",
        "financial_calculator": "/tools/financial_calculator",
    }

    endpoint = endpoint_map.get(tool_name)
    if not endpoint:
        raise ValueError(f"Unknown tool: {tool_name}")

    # Handle dynamic endpoints (lambdas)
    if callable(endpoint):
        endpoint = endpoint(arguments)
        method = "GET"
    else:
        method = "POST" if not endpoint.startswith("/resources/") else "GET"

    async with httpx.AsyncClient() as client:
        if method == "GET":
            response = await client.get(f"{MCP_SERVER_URL}{endpoint}", timeout=30.0)
        else:
            response = await client.post(f"{MCP_SERVER_URL}{endpoint}", json=arguments, timeout=30.0)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()

def detect_tool_intent(task: str) -> Optional[tuple]:
    """Fallback: Detect tool intent from user message when function calling not supported"""
    import re
    task_lower = task.lower()

    # First, check if there's an email address in the text
    # This helps with context-based detection like "contact John at jerry@email.com"
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
        if emails:
            # Try to extract subject and body
            subject = "來自AI助手的訊息"
            body = task

            # Try to extract the message content after "表達" or similar keywords
            content_keywords = ["表達", "表达", "告訴", "告诉", "說", "说", "內容", "内容", "message", "tell them"]
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
                        # Extract text between quotes or until next keyword
                        subject_match = re.search(r'[是:：]?\s*[「『"]?([^」』"，,。]+)', parts[1])
                        if subject_match:
                            subject = subject_match.group(1).strip()

            # If no explicit subject, try to infer from context
            if subject == "來自AI助手的訊息" and "關心" in task:
                subject = "問候與祝福"

            # Look for body keywords explicitly
            for keyword in ["內容是", "正文是", "内容是", "body is", "content is"]:
                if keyword in task_lower:
                    parts = task.split(keyword, 1)
                    if len(parts) > 1:
                        body_match = re.search(r':?\s*[「『"]?([^」』"]+)', parts[1])
                        if body_match:
                            body = body_match.group(1).strip()

            return ("send_email", {
                "to": emails,
                "subject": subject,
                "body": body
            })

    # Task creation patterns
    if any(keyword in task_lower for keyword in ["創建任務", "建立任務", "create task", "新增任務", "add task"]):
        return ("create_task", {
            "title": task[:100],
            "description": task,
            "assignee": "system"
        })

    # Search patterns - extract the actual search term
    search_keywords = ["搜索", "搜尋", "search", "查找", "find", "搜", "找", "尋找", "寻找"]
    for keyword in search_keywords:
        if keyword in task_lower:
            # Extract search query by removing the search keyword and common connecting words
            query = task
            # Remove search keywords with common patterns - updated to handle more cases
            query = re.sub(r'(搜索|搜尋|search\s+for|search|查找|find|搜|找|尋找|寻找)\s*(關於|关于|about|for)?\s*', '', query, flags=re.IGNORECASE)
            # Remove common Chinese article/connecting words at the end
            query = re.sub(r'[的之]?(文檔|文档|檔案|档案|資料|资料|內容|内容|信息|資訊|资讯)$', '', query)
            # Clean up
            query = query.strip().lstrip('的之').rstrip('的之').strip()
            # If query is empty or too short, use original task
            if len(query) < 2:
                query = task
            logger.info(f"Search detected - Original: '{task}', Extracted query: '{query}'")
            return ("search_knowledge_base", {
                "query": query,
                "limit": 5
            })

    return None

@app.post("/agent/execute", response_model=AgentResponse)
async def execute_agent(request: AgentRequest):
    """執行Agent任務 - 支持工具調用"""
    try:
        steps = []

        # Track MCP usage
        mcp_usage = {
            "tools_used": [],  # List of tools that were called
            "resources_accessed": [],  # List of resources accessed
            "system_prompt": "",  # The system prompt used
            "sampling_parameters": {
                "temperature": request.temperature,
                "top_p": request.top_p,
                "top_k": request.top_k
            }
        }

        # Map model aliases to actual model names for LiteLLM
        # LiteLLM handles provider prefixes, we just pass the model name configured in litellm-config.yaml
        model_name_map = {
            "claude-3-sonnet": "claude-3-sonnet",
            "claude-3-5-sonnet": "claude-3-5-sonnet",
            "claude-3-opus": "claude-3-opus",
            "claude-3-haiku": "claude-3-haiku",
            "gpt-3.5-turbo": "gpt-3.5-turbo",
            "gpt-4": "gpt-4",
            "gpt-4o": "gpt-4o",
            "gpt-4o-mini": "gpt-4o-mini",
            "gpt-4-turbo": "gpt-4-turbo",
            "gemini-1.5-pro": "gemini-1.5-pro",
            "gemini-1.5-flash": "gemini-1.5-flash",
            "qwen2.5": "qwen2.5",
            "qwen2.5-7b": "qwen2.5-7b",
            # Taiwan Government LLM API models
            "llama31-taidelx-8b-32k": "llama31-taidelx-8b-32k",
            "llama3-taiwan-70b-8k": "llama3-taiwan-70b-8k",
            "llama31-foxbrain-70b-32k": "llama31-foxbrain-70b-32k",
            "llama33-ffm-70b-32k": "llama33-ffm-70b-32k",
            "phi4-reasoning-plus-32k": "phi4-reasoning-plus-32k",
            "magistral-small-2506-32k": "magistral-small-2506-32k",
            "google-gemma-3-27b-32k": "google-gemma-3-27b-32k",
            "llama4-scout-17b-16e-instruct-32k": "llama4-scout-17b-16e-instruct-32k",
            "gpt-oss-20b-32k": "gpt-oss-20b-32k",
            "gpt-oss-120b-32k": "gpt-oss-120b-32k"
        }

        # Get actual model name for API calls
        actual_model = model_name_map.get(request.model, request.model)

        # Step 1: 獲取可用工具
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{MCP_SERVER_URL}/tools/list", timeout=10.0)
                tools_data = resp.json()
                tools = tools_data.get('tools', [])
                steps.append({
                    "step": "fetch_tools",
                    "result": f"Found {len(tools)} tools",
                    "status": "success"
                })

                # Convert to function calling format
                functions = convert_tools_to_functions(tools)
        except Exception as e:
            logger.error(f"Failed to fetch tools: {e}")
            steps.append({
                "step": "fetch_tools",
                "result": f"Failed: {str(e)}",
                "status": "failed"
            })
            functions = []

        # List of models that support function calling
        # Note: Ollama models (qwen2.5) don't support OpenAI-style function calling
        # They use the fallback pattern matching approach in detect_tool_intent()
        function_calling_models = [
            "gpt-3.5-turbo", "gpt-4", "gpt-4o", "gpt-4o-mini", "gpt-4-turbo",
            "claude-3-sonnet", "claude-3-5-sonnet", "claude-3-opus", "claude-3-haiku"
        ]

        # Check if this is a simple tool action that can be handled directly
        # This is a fallback for models that don't support function calling
        tool_intent = detect_tool_intent(request.task)
        if tool_intent and request.model not in function_calling_models:
            tool_name, tool_args = tool_intent

            steps.append({
                "step": "intent_detection",
                "tool": tool_name,
                "arguments": tool_args,
                "status": "detected"
            })

            try:
                # Log tool call for debugging
                logger.info(f"Calling tool in fallback mode: {tool_name} with args: {tool_args}")

                # Call the tool directly
                tool_result = await call_mcp_tool(tool_name, tool_args)

                logger.info(f"Tool result: {tool_result}")

                steps.append({
                    "step": "tool_execution",
                    "tool": tool_name,
                    "result": tool_result,
                    "status": "success"
                })

                # Format a nice response
                if tool_name == "send_email":
                    result = f"✅ 郵件已成功發送！\n\n收件人: {', '.join(tool_args['to'])}\n主旨: {tool_args['subject']}\n郵件ID: {tool_result.get('email_id')}\n發送時間: {tool_result.get('sent_at')}"
                elif tool_name == "create_task":
                    result = f"✅ 任務已創建！\n\n任務ID: {tool_result.get('id')}\n標題: {tool_args['title']}\n狀態: {tool_result.get('status')}"
                elif tool_name == "search_knowledge_base":
                    results = tool_result.get('results', [])
                    if len(results) > 0:
                        result_items = []
                        for i, r in enumerate(results[:5], 1):
                            title = r.get('title', 'N/A')
                            content = r.get('content', '')[:200]  # First 200 chars
                            result_items.append(f"{i}. **{title}**\n   {content}...")
                        result = f"✅ 搜索完成！找到 {len(results)} 個結果。\n\n" + "\n\n".join(result_items)
                    else:
                        result = f"✅ 搜索完成！找到 0 個結果。\n\n搜尋詞: \"{tool_args.get('query', 'N/A')}\"\n\n資料庫中可能沒有相關文檔，請嘗試其他搜尋詞。"
                else:
                    result = f"✅ 工具執行成功！\n\n{json.dumps(tool_result, ensure_ascii=False, indent=2)}"

                # Track fallback tool usage
                mcp_usage["tools_used"].append({
                    "name": tool_name,
                    "arguments": tool_args,
                    "result_summary": str(tool_result)[:200] + "..." if len(str(tool_result)) > 200 else str(tool_result)
                })

                return AgentResponse(
                    result=result,
                    steps=steps,
                    metadata={
                        "agent_type": request.agent_type,
                        "model_used": request.model,
                        "tool_called": tool_name,
                        "fallback_mode": True,
                        "mcp_usage": mcp_usage
                    }
                )

            except Exception as tool_error:
                logger.error(f"Tool execution error: {tool_error}")
                steps.append({
                    "step": "tool_execution",
                    "tool": tool_name,
                    "error": str(tool_error),
                    "status": "failed"
                })

                return AgentResponse(
                    result=f"❌ 工具執行失敗: {str(tool_error)}",
                    steps=steps,
                    metadata={
                        "agent_type": request.agent_type,
                        "error": str(tool_error),
                        "fallback_mode": True,
                        "mcp_usage": mcp_usage
                    }
                )

        # Step 2: 呼叫LLM with function calling (for supported models)
        # Enhanced system prompt for multi-stage conversations - specialized by agent type
        agent_prompts = {
            "general": """你是一個企業AI助手，可以直接回答問題或使用各種工具來幫助用戶完成任務。

重要指南：

📄 **文件分析模式**：
- 如果用戶上傳了文件（PDF、文本等）並詢問內容，直接分析文件並回答問題
- 不需要使用工具，直接閱讀提供的文件內容並進行分析
- 示例：用戶上傳PDF並問"描述這份文件" → 直接分析文件內容並詳細描述

🛠️ **工具使用模式**：
1. 當用戶要求執行某個操作時（如發送郵件、創建任務、搜索等），請調用相應的工具
2. 在調用工具之前，檢查是否有所有必需的參數
3. 如果缺少必需參數（如email地址、subject、body等），不要猜測或使用默認值
4. 如果信息不足，請禮貌地詢問用戶提供缺少的信息
5. 一次只詢問缺少的信息，不要問不必要的問題
6. 收集到所有必需信息後，立即執行操作

示例：
- 用戶說"send email"但沒有提供收件人 → 詢問收件人email地址
- 用戶說"send email to john@example.com"但沒有主旨和內容 → 詢問郵件主旨和內容
- 用戶提供了所有信息 → 直接執行發送郵件""",

            "research": """你是一個專業的研究助手，擅長信息收集、分析和整理。

你的專長：
1. 使用搜索工具（search_knowledge_base, web_search, semantic_search）深入研究主題
2. 找到相關文檔並提取關鍵信息
3. 整合多個來源的信息，提供全面的研究報告
4. 驗證信息的準確性和相關性
5. 提供引用和來源

工作方式：
- 收到研究任務時，先規劃搜索策略
- 使用多個搜索工具交叉驗證信息
- 整理發現的信息，以結構化方式呈現
- 必要時使用 summarize_document 工具總結長文檔
- 提供清晰的研究結論和建議

重點：深度、準確性、來源可靠性""",

            "analysis": """你是一個數據分析專家，專注於數據處理、分析和可視化。

你的專長：
1. 使用 analyze_data 工具進行統計分析
2. 使用 process_csv 處理和清理數據
3. 使用 generate_chart 創建數據可視化
4. 使用 calculate_metrics 計算業務指標
5. 使用 financial_calculator 進行財務分析

工作流程：
- 理解數據分析需求
- 檢查數據質量和完整性
- 選擇適當的分析方法
- 生成清晰的圖表和報表
- 提供數據驅動的見解和建議

重點：數據準確性、分析深度、可視化清晰度、actionable insights"""
        }

        system_prompt = agent_prompts.get(request.agent_type, agent_prompts["general"])

        # Store system prompt in MCP usage
        mcp_usage["system_prompt"] = system_prompt

        # Check if document analysis is needed (documents are marked with special tags)
        has_document = "===== IMPORTANT: DOCUMENT ANALYSIS REQUIRED =====" in request.task or "---BEGIN DOCUMENT CONTENT---" in request.task

        if has_document:
            # PRIORITY: Document analysis mode - override other behaviors
            system_prompt = """📄 你正在處理文件分析任務。

**重要指示**：
1. 用戶已經上傳了文件內容（PDF、文本等），內容已經包含在用戶的消息中
2. 你的任務是直接閱讀和分析提供的文件內容
3. 不要使用任何工具（web_search、search_knowledge_base等）
4. 不要說"我無法找到"或"我未能找到" - 文件內容就在用戶消息中
5. 直接分析文件內容並詳細回答用戶的問題

**工作流程**：
- 仔細閱讀 "---BEGIN DOCUMENT CONTENT---" 和 "---END DOCUMENT CONTENT---" 之間的內容
- 根據文件內容回答用戶的問題
- 提供具體、詳細的分析和見解

記住：文件內容已經提供給你了，不需要搜索或使用工具！"""
            actual_task = request.task
        else:
            # Check if web search is enabled
            web_search_enabled = request.task.startswith("[WEB_SEARCH_ENABLED]")
            if web_search_enabled:
                # Remove the flag from the task
                actual_task = request.task.replace("[WEB_SEARCH_ENABLED]", "").strip()
                # Enhance system prompt to use web search
                system_prompt += "\n\n🌐 **WEB SEARCH MODE ENABLED**\n重要: 用戶要求使用網路搜索。請務必使用 web_search 工具來獲取最新的即時信息。步驟:\n1. 使用 web_search 工具搜索相關資訊\n2. 分析搜索結果\n3. 基於搜索結果回答用戶的問題\n\n如果沒有搜索到相關結果，請明確告知用戶。"
            else:
                actual_task = request.task

        # Build messages array with conversation history
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history if provided
        if request.conversation_history:
            messages.extend(request.conversation_history)

        # Add current user message with optional images (use actual_task without flag)
        if request.images and len(request.images) > 0:
            # Vision models: format message with images
            content = []
            content.append({"type": "text", "text": actual_task})

            # Add images in proper format
            for img in request.images:
                # OpenAI/Claude format
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{img['mime_type']};base64,{img['data']}"
                    }
                })

            messages.append({"role": "user", "content": content})
        else:
            # Text-only message
            messages.append({"role": "user", "content": actual_task})

        max_iterations = 5  # Prevent infinite loops
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            try:
                # Call LLM with functions
                async with httpx.AsyncClient() as client:
                    llm_payload = {
                        "model": actual_model,  # Use actual model name for LiteLLM
                        "messages": messages,
                        "temperature": request.temperature,
                        "top_p": request.top_p,
                        "max_tokens": 2000
                    }

                    # Add top_k if supported (mainly for local models like qwen)
                    if request.model.startswith("qwen"):
                        llm_payload["top_k"] = request.top_k

                    # Add functions if model supports it
                    if functions and request.model in function_calling_models:
                        llm_payload["tools"] = [{"type": "function", "function": f} for f in functions]
                        # Claude doesn't need tool_choice parameter, LiteLLM handles it
                        if not request.model.startswith("claude"):
                            llm_payload["tool_choice"] = "auto"

                    llm_response = await client.post(
                        f"{LLM_PROXY_URL}/v1/chat/completions",
                        headers={"Authorization": f"Bearer {LITELLM_API_KEY}"},
                        json=llm_payload,
                        timeout=60.0
                    )

                    if llm_response.status_code != 200:
                        llm_data = llm_response.json()
                        error_detail = str(llm_data)
                        if isinstance(llm_data, dict) and "error" in llm_data:
                            error_detail = llm_data["error"].get("message", str(llm_data["error"]))

                        steps.append({
                            "step": f"llm_call_{iteration}",
                            "result": f"Failed: {error_detail}",
                            "status": "failed"
                        })

                        return AgentResponse(
                            result=f"LLM錯誤: {error_detail}",
                            steps=steps,
                            metadata={"agent_type": request.agent_type, "error": error_detail, "mcp_usage": mcp_usage}
                        )

                    llm_data = llm_response.json()
                    assistant_message = llm_data["choices"][0]["message"]

                    # Add assistant message to history
                    messages.append(assistant_message)

                    # Check if function was called
                    tool_calls = assistant_message.get("tool_calls", [])

                    if not tool_calls:
                        # No tool call - could be asking for more info or final answer
                        result = assistant_message.get("content", "")

                        # Detect if agent is asking for more information
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

                        steps.append({
                            "step": f"llm_response_{iteration}",
                            "result": "Asking for more information" if needs_more_info else "Task completed",
                            "status": "success"
                        })

                        return AgentResponse(
                            result=result,
                            steps=steps,
                            metadata={
                                "agent_type": request.agent_type,
                                "model_used": request.model,
                                "iterations": iteration,
                                "tokens_used": llm_data.get("usage", {}).get("total_tokens", 0),
                                "conversation_active": needs_more_info,
                                "mcp_usage": mcp_usage
                            },
                            needs_more_info=needs_more_info
                        )

                    # Execute each tool call
                    for tool_call in tool_calls:
                        function_name = tool_call["function"]["name"]
                        function_args = json.loads(tool_call["function"]["arguments"])

                        steps.append({
                            "step": f"tool_call_{iteration}",
                            "tool": function_name,
                            "arguments": function_args,
                            "status": "executing"
                        })

                        try:
                            # Call the MCP tool
                            tool_result = await call_mcp_tool(function_name, function_args)

                            # Track tool usage
                            tool_usage_record = {
                                "name": function_name,
                                "arguments": function_args,
                                "result_summary": str(tool_result)[:200] + "..." if len(str(tool_result)) > 200 else str(tool_result)
                            }
                            mcp_usage["tools_used"].append(tool_usage_record)

                            # Track resource access
                            if function_name == "get_document" and "document_id" in function_args:
                                mcp_usage["resources_accessed"].append({
                                    "type": "document",
                                    "id": function_args["document_id"]
                                })
                            elif function_name in ["search_knowledge_base", "semantic_search", "web_search"]:
                                mcp_usage["resources_accessed"].append({
                                    "type": "search",
                                    "query": function_args.get("query", "N/A")
                                })

                            steps.append({
                                "step": f"tool_result_{iteration}",
                                "tool": function_name,
                                "result": tool_result,
                                "status": "success"
                            })

                            # Add function result to messages
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call["id"],
                                "content": json.dumps(tool_result)
                            })

                        except Exception as tool_error:
                            logger.error(f"Tool execution error for {function_name}: {tool_error}")
                            steps.append({
                                "step": f"tool_error_{iteration}",
                                "tool": function_name,
                                "error": str(tool_error),
                                "status": "failed"
                            })

                            # Add error to messages
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call["id"],
                                "content": json.dumps({"error": str(tool_error)})
                            })

                    # Continue loop to get LLM's response with tool results

            except Exception as e:
                logger.error(f"LLM processing error: {e}")
                steps.append({
                    "step": f"llm_error_{iteration}",
                    "result": f"Failed: {str(e)}",
                    "status": "failed"
                })

                return AgentResponse(
                    result=f"處理失敗: {str(e)}",
                    steps=steps,
                    metadata={"agent_type": request.agent_type, "error": str(e), "mcp_usage": mcp_usage}
                )

        # Max iterations reached
        return AgentResponse(
            result="任務處理超過最大迭代次數",
            steps=steps,
            metadata={"agent_type": request.agent_type, "max_iterations_reached": True, "mcp_usage": mcp_usage}
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
                headers={
                    "Authorization": f"Bearer {LITELLM_API_KEY}"
                },
                json={
                    "model": request.model,
                    "messages": [
                        {"role": "user", "content": request.message}
                    ],
                    "temperature": request.temperature,
                    "max_tokens": 2000
                },
                timeout=30.0
            )
            
            data = response.json()

            if response.status_code != 200:
                # Parse detailed error from LiteLLM response
                error_detail = str(data)
                original_error = ""

                # Try to extract meaningful error message from nested structures
                if isinstance(data, dict):
                    if "error" in data:
                        error_obj = data["error"]
                        if isinstance(error_obj, dict):
                            error_detail = error_obj.get("message", str(error_obj))
                            # Try to get the original error message if available
                            if "error" in error_obj and isinstance(error_obj["error"], dict):
                                original_error = error_obj["error"].get("message", "")
                        else:
                            error_detail = str(error_obj)
                    elif "detail" in data:
                        error_detail = data["detail"]

                # Combine all error text for matching
                full_error_text = f"{error_detail} {original_error}".lower()

                # Provide user-friendly error messages for common issues
                if "credit balance is too low" in full_error_text or "insufficient_quota" in full_error_text:
                    user_message = f"❌ API配額不足\n\n您的 {request.model} API帳戶餘額不足或配額已用完。\n\n解決方法:\n1. 前往API提供商的控制台充值\n2. 升級您的API方案\n3. 或使用本地模型 'qwen2.5' (無需API金鑰)"
                elif "authentication" in full_error_text or "api key" in full_error_text or "invalid_api_key" in full_error_text:
                    user_message = f"❌ 認證失敗\n\n{request.model} 的API金鑰無效或已過期。\n\n解決方法:\n1. 檢查.env檔案中的API金鑰配置\n2. 確認API金鑰有效且未過期\n3. 或使用本地模型 'qwen2.5' (無需API金鑰)"
                elif "rate limit" in full_error_text or "too many requests" in full_error_text or "429" in str(response.status_code):
                    user_message = f"❌ 請求過於頻繁\n\n{request.model} API已達到速率限制。\n\n解決方法:\n1. 稍後再試\n2. 升級您的API方案以獲得更高速率限制\n3. 或使用本地模型 'qwen2.5' (無速率限制)"
                elif ("model" in full_error_text and "not found" in full_error_text) or "model_not_found" in full_error_text:
                    user_message = f"❌ 模型不存在\n\n模型 '{request.model}' 不可用。\n\n解決方法:\n1. 檢查模型名稱是否正確\n2. 確認您的API帳戶有權訪問該模型\n3. 使用可用的模型: qwen2.5 (本地), gpt-3.5-turbo, gpt-4, claude-3-sonnet"
                elif "timeout" in full_error_text:
                    user_message = f"⏱️ 請求超時\n\n{request.model} API響應超時，請稍後重試。"
                else:
                    # Show truncated error for better readability
                    error_preview = error_detail[:200] + "..." if len(error_detail) > 200 else error_detail
                    user_message = f"❌ API錯誤 ({request.model})\n\n{error_preview}\n\n提示: 可以使用本地模型 'qwen2.5' 避免API問題"

                logger.error(f"LLM API error for model {request.model}: {error_detail}")
                raise HTTPException(status_code=response.status_code, detail=user_message)

            return ChatResponse(
                response=data["choices"][0]["message"]["content"],
                model=request.model
            )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="LLM服務超時，請稍後再試")
    except HTTPException:
        raise
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
