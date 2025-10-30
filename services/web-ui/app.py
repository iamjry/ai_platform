import streamlit as st
import requests
import os
import time
import base64
import random
import yaml
from io import BytesIO
from PyPDF2 import PdfReader
from i18n import LANGUAGES, get_text

# Helper functions for agent prompts configuration
def load_agent_prompts():
    """Load agent system prompts from config/agent_prompts.yaml"""
    prompts_path = "/app/config/agent_prompts.yaml"
    default_prompts = {
        "general": "你是一個企業AI助手，可以直接回答問題或使用各種工具來幫助用戶完成任務。",
        "research": "你是一個專業的研究助手，擅長信息收集、分析和整理。",
        "analysis": "你是一個數據分析專家，專注於數據處理、分析和可視化。",
        "contract_review": "你是一個專業的契約審查助手，專注於契約分析、風險評估和合規檢查。"
    }

    try:
        if os.path.exists(prompts_path):
            with open(prompts_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and 'agent_prompts' in data:
                    return data['agent_prompts']
        return default_prompts
    except Exception as e:
        st.error(f"Error loading agent prompts: {e}")
        return default_prompts

def save_agent_prompts(prompts):
    """Save agent system prompts to config/agent_prompts.yaml"""
    prompts_path = "/app/config/agent_prompts.yaml"

    try:
        data = {
            "agent_prompts": prompts
        }
        with open(prompts_path, 'w', encoding='utf-8') as f:
            f.write("# Agent System Prompts Configuration\n")
            f.write("# Last Updated: " + time.strftime("%Y-%m-%d %H:%M:%S") + "\n")
            f.write("#\n")
            f.write("# This file contains the system prompts for different agent types.\n")
            f.write("# Edit these prompts to customize agent behavior.\n")
            f.write("#\n")
            f.write("# NOTE: After modifying this file, the changes take effect immediately.\n")
            f.write("#       Both web-ui and agent-service will reload prompts on next request.\n\n")
            yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return True
    except Exception as e:
        st.error(f"Error saving agent prompts: {e}")
        return False

# Initialize session state for language
if "language" not in st.session_state:
    st.session_state.language = "zh-TW"  # Default to Traditional Chinese

lang = st.session_state.language

st.set_page_config(
    page_title=get_text("page_title", lang),
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://agent-service:8000")
LITELLM_URL = os.getenv("LITELLM_URL", "http://litellm:4000")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://mcp-server:8000")

# Model context limits (conservative estimates to account for system prompt and tools)
MODEL_CONTEXT_LIMITS = {
    "qwen2.5": {
        "total_tokens": 32000,
        "safe_limit": 24000,
        "avg_tokens_per_message": 150
    },
    "qwen2.5-7b": {
        "total_tokens": 32000,
        "safe_limit": 24000,
        "avg_tokens_per_message": 150
    },
    "gpt-3.5-turbo": {
        "total_tokens": 16385,
        "safe_limit": 12000,
        "avg_tokens_per_message": 100
    },
    "gpt-4": {
        "total_tokens": 128000,
        "safe_limit": 96000,
        "avg_tokens_per_message": 150
    },
    "gpt-4o": {
        "total_tokens": 128000,
        "safe_limit": 96000,
        "avg_tokens_per_message": 150
    },
    "gpt-4o-mini": {
        "total_tokens": 128000,
        "safe_limit": 96000,
        "avg_tokens_per_message": 150
    },
    "claude-3-opus": {
        "total_tokens": 200000,
        "safe_limit": 150000,
        "avg_tokens_per_message": 200
    },
    "claude-3-sonnet": {
        "total_tokens": 200000,
        "safe_limit": 150000,
        "avg_tokens_per_message": 200
    },
    "claude-3-5-sonnet": {
        "total_tokens": 200000,
        "safe_limit": 150000,
        "avg_tokens_per_message": 200
    },
    "claude-3-haiku": {
        "total_tokens": 200000,
        "safe_limit": 150000,
        "avg_tokens_per_message": 200
    },
    "gemini-1.5-pro": {
        "total_tokens": 1000000,
        "safe_limit": 750000,
        "avg_tokens_per_message": 200
    },
    "gemini-1.5-flash": {
        "total_tokens": 1000000,
        "safe_limit": 750000,
        "avg_tokens_per_message": 150
    }
}

def estimate_tokens(text):
    """Rough estimate: ~4 characters per token"""
    return len(text) // 4

def truncate_conversation_history(history, model, max_messages=None):
    """Truncate conversation history to fit within model context limits"""
    if not history:
        return history

    limits = MODEL_CONTEXT_LIMITS.get(model, MODEL_CONTEXT_LIMITS["gpt-3.5-turbo"])

    # If max_messages specified, use that
    if max_messages:
        return history[-max_messages * 2:]  # Keep last N exchanges (user + assistant pairs)

    # Otherwise, estimate tokens and truncate
    estimated_tokens = sum(estimate_tokens(msg["content"]) for msg in history)

    if estimated_tokens <= limits["safe_limit"]:
        return history

    # Truncate from the beginning, keeping most recent messages
    # Always keep at least the last 4 messages (2 exchanges)
    min_messages = 4
    truncated = history[-min_messages:]

    # Add more messages if we have room
    for i in range(len(history) - min_messages - 1, -1, -1):
        msg = history[i]
        msg_tokens = estimate_tokens(msg["content"])
        current_tokens = sum(estimate_tokens(m["content"]) for m in truncated)

        if current_tokens + msg_tokens < limits["safe_limit"]:
            truncated.insert(0, msg)
        else:
            break

    return truncated

def get_context_usage_info(history, model):
    """Get context usage information"""
    if not history:
        return {"messages": 0, "estimated_tokens": 0, "percentage": 0}

    limits = MODEL_CONTEXT_LIMITS.get(model, MODEL_CONTEXT_LIMITS["gpt-3.5-turbo"])
    estimated_tokens = sum(estimate_tokens(msg["content"]) for msg in history)
    percentage = (estimated_tokens / limits["safe_limit"]) * 100

    return {
        "messages": len(history),
        "estimated_tokens": estimated_tokens,
        "safe_limit": limits["safe_limit"],
        "percentage": round(percentage, 1)
    }

# Custom CSS
st.markdown("""
<style>
    /* Main content area padding */
    .main > div {
        padding-top: 2rem !important;
    }

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 1rem !important;
    }

    /* Reduce sidebar padding aggressively */
    section[data-testid="stSidebar"] {
        padding-top: 0 !important;
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 0.3rem !important;
        padding-bottom: 0.3rem !important;
    }

    section[data-testid="stSidebar"] > div > div {
        padding-top: 0 !important;
    }

    /* Ensure first element in sidebar has no extra margin */
    section[data-testid="stSidebar"] .element-container:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }

    section[data-testid="stSidebar"] .element-container {
        margin-bottom: 0.3rem !important;
    }

    section[data-testid="stSidebar"] hr {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }

    section[data-testid="stSidebar"] .stSelectbox {
        margin-bottom: 0.3rem !important;
    }

    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        margin-bottom: 0.3rem !important;
    }

    section[data-testid="stSidebar"] .stAlert {
        padding: 0.5rem !important;
        margin-bottom: 0.3rem !important;
    }

    section[data-testid="stSidebar"] .stColumns {
        gap: 0.3rem !important;
    }

    /* Reduce header spacing */
    h1, h2, h3 {
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }

    /* Reduce caption spacing */
    .caption {
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
    }

    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 0.3rem;
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

# Sidebar
with st.sidebar:
    # Logo and Title at top of sidebar
    st.markdown("""
    <div style="text-align: center; margin: 0; padding: 0;">
        <div style="font-size: 2rem; line-height: 1; margin: 0;">🤖</div>
        <h3 style="margin: 0; padding: 0; color: #1f77b4; font-weight: 700; font-size: 1rem; line-height: 1;">AI Agents Platform</h3>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown(f"### {get_text('settings', lang)}")

    # Language selector
    selected_lang = st.selectbox(
        get_text("language", lang),
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x],
        index=list(LANGUAGES.keys()).index(st.session_state.language),
        key="lang_selector"
    )

    if selected_lang != st.session_state.language:
        st.session_state.language = selected_lang
        st.rerun()

    # Model options with display names
    # Load model options from litellm config
    import yaml

    def load_model_options():
        try:
            with open("/app/config/litellm-config.yaml", 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                model_options = {}
                if "model_list" in config:
                    for model in config["model_list"]:
                        # Only include models where visible is True (default to True if not specified)
                        is_visible = model.get("visible", True)
                        if not is_visible:
                            continue

                        model_name = model.get("model_name", "")
                        display_name = model.get("display_name", model_name)
                        if model_name and display_name:
                            model_options[display_name] = model_name
                return model_options
        except Exception as e:
            # Fallback to default if config can't be loaded
            return {
                "qwen2.5:7b (local - better for PDFs)": "qwen2.5-7b",
                "gpt-4o (OpenAI)": "gpt-4o"
            }

    model_options = load_model_options()

    model_display = st.selectbox(
        get_text("select_model", lang),
        options=list(model_options.keys()),
        help=get_text("model_help", lang)
    )

    model_choice = model_options[model_display]

    # Show model information
    st.markdown("---")
    st.markdown("### 📋 " + ("模型資訊" if lang == "zh-TW" else "Model Information"))

    # Get model info
    model_info = MODEL_CONTEXT_LIMITS.get(model_choice, {})

    # Display model details in a nice format
    col_info1, col_info2 = st.columns(2)

    with col_info1:
        # Model name and provider
        if model_choice.startswith("qwen"):
            st.info(f"**Provider:** Local (Ollama)\n\n**Status:** ✅ No API key needed")
        elif model_choice.startswith("gpt"):
            st.info(f"**Provider:** OpenAI\n\n**Status:** ⚠️ API key required")
        elif model_choice.startswith("claude"):
            st.info(f"**Provider:** Anthropic\n\n**Status:** ⚠️ API key required")
        elif model_choice.startswith("gemini"):
            st.info(f"**Provider:** Google\n\n**Status:** ⚠️ API key required")
        elif model_choice.startswith("llama"):
            st.info(f"**Provider:** Taiwan Gov (AFSPOD)\n\n**Status:** ✅ API key configured")

    with col_info2:
        # Context window info
        if model_info:
            st.info(f"**Context Window:** {model_info.get('total_tokens', 'N/A'):,} tokens\n\n**Safe Limit:** {model_info.get('safe_limit', 'N/A'):,} tokens")

    # Model capabilities
    vision_models = ["gpt-4o", "gpt-4o-mini", "claude-3-opus", "claude-3-5-sonnet", "claude-3-sonnet", "gemini-1.5-pro", "gemini-1.5-flash"]
    capabilities = []
    if model_choice in vision_models:
        capabilities.append("🖼️ Vision")
    if model_choice.startswith("qwen") or model_choice.startswith("claude"):
        capabilities.append("📄 PDF Analysis")
    if model_choice in ["gpt-4o", "gpt-4", "claude-3-opus", "claude-3-5-sonnet", "gemini-1.5-pro"]:
        capabilities.append("🧠 Advanced Reasoning")

    if capabilities:
        st.caption("**Capabilities:** " + " • ".join(capabilities))

    st.markdown("---")

    # Sampling parameters
    st.subheader("🎛️ " + ("採樣參數" if lang == "zh-TW" else "Sampling Parameters"))

    temperature = st.slider(
        get_text("temperature", lang),
        0.0, 1.0, 0.7,
        help=get_text("temperature_help", lang)
    )

    top_p = st.slider(
        "Top-P (nucleus sampling)",
        0.0, 1.0, 0.9,
        help="Controls diversity via nucleus sampling. Lower values make output more focused, higher values more diverse."
    )

    top_k = st.slider(
        "Top-K",
        0, 100, 40,
        help="Limits sampling to top K tokens. 0 means no limit. Lower values make output more focused."
    )

    st.divider()

    # Always show Context Information section
    st.subheader("💬 " + ("對話上下文" if lang == "zh-TW" else "Context Info"))

    # Show model context limits
    if model_choice in MODEL_CONTEXT_LIMITS:
        limits = MODEL_CONTEXT_LIMITS[model_choice]
        st.info(f"📊 **{model_choice}**\n\nMax Context: {limits['total_tokens']:,} tokens\nSafe Limit: {limits['safe_limit']:,} tokens")

    # Show context usage if there's conversation history
    if "conversation_history" in st.session_state and st.session_state.conversation_history:
        usage = get_context_usage_info(st.session_state.conversation_history, model_choice)

        # Color based on usage
        if usage["percentage"] < 50:
            color = "🟢"
        elif usage["percentage"] < 80:
            color = "🟡"
        else:
            color = "🔴"

        st.metric(
            label="Current Usage",
            value=f"{usage['percentage']}%",
            delta=f"{usage['messages']} messages"
        )
        st.caption(f"{color} {usage['estimated_tokens']:,} / {usage['safe_limit']:,} tokens")

        if usage["percentage"] > 80:
            st.warning("⚠️ " + ("接近上下文限制！" if lang == "zh-TW" else "Near context limit!"))
    else:
        st.caption("💭 " + ("開始對話後會顯示使用情況" if lang == "zh-TW" else "Start a conversation to see usage"))

    st.divider()

    # System Status
    st.header(get_text("system_status", lang))

    with st.spinner(get_text("checking_status", lang)):
        # Check Agent service
        try:
            resp = requests.get(f"{AGENT_SERVICE_URL}/health", timeout=3)
            if resp.ok:
                st.success(get_text("agent_service_ok", lang))
                health_data = resp.json()
                if "services" in health_data:
                    for service, status in health_data["services"].items():
                        if "connected" in str(status):
                            st.text(f"  └─ {service}: ✓")
                        else:
                            st.text(f"  └─ {service}: ✗")
            else:
                st.error(get_text("agent_service_error", lang))
        except Exception as e:
            st.error(get_text("agent_service_offline", lang))
            st.caption(f"{get_text('error', lang)}: {str(e)}")

    st.divider()

    # Quick Actions
    st.header(get_text("quick_actions", lang))
    if st.button(get_text("clear_chat", lang)):
        st.session_state.messages = []
        st.session_state.conversation_history = []  # Also clear conversation history
        st.rerun()

    if st.button(get_text("export_chat", lang)):
        if "messages" in st.session_state and st.session_state.messages:
            conversation = "\n\n".join([
                f"{msg['role'].upper()}: {msg['content']}"
                for msg in st.session_state.messages
            ])
            st.download_button(
                get_text("download_chat", lang),
                conversation,
                file_name="conversation.txt",
                mime="text/plain"
            )
        else:
            st.info(get_text("no_chat_history", lang))

# Main Content
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    get_text("tab_chat", lang),
    get_text("tab_agent", lang),
    get_text("tab_agents_catalog", lang),
    get_text("tab_models_config", lang),
    get_text("tab_monitor", lang),
    get_text("tab_rag", lang),
    "📚 Documentation",
    get_text("tab_about", lang)
])

with tab1:
    st.header(get_text("chat_header", lang))
    st.caption(get_text("chat_caption", lang))

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Initialize conversation history for multi-stage conversations
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []

    # Initialize uploaded files
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = []

    # File upload and web search options (Claude.ai style)
    with st.expander("📎 Attachments & Options", expanded=False):
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            uploaded_files = st.file_uploader(
                "Upload files (images, documents, etc.)",
                accept_multiple_files=True,
                type=['png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'md', 'csv', 'json', 'xml'],
                key="file_uploader"
            )

        with col2:
            web_search_enabled = st.checkbox(
                "🌐 Web Search",
                value=False,
                help="Enable web search for real-time information"
            )

        with col3:
            rag_search_enabled = st.checkbox(
                "📚 RAG Knowledge",
                value=False,
                help="Search knowledge base for relevant context"
            )

        # Document selection for RAG
        if rag_search_enabled:
            st.write("**Select documents to search:**")
            try:
                response = requests.get(f"{MCP_SERVER_URL}/rag/documents?limit=100", timeout=5)
                if response.status_code == 200:
                    docs_data = response.json()
                    documents = docs_data.get('documents', [])

                    if documents:
                        doc_options = {f"{doc['id']} - {doc['title']}": doc['id'] for doc in documents}
                        selected_docs = st.multiselect(
                            "Choose specific documents (optional - leave empty to search all)",
                            options=list(doc_options.keys()),
                            default=[],
                            key="rag_doc_selection"
                        )
                        # Store selected doc IDs in session state
                        if "selected_doc_ids" not in st.session_state:
                            st.session_state.selected_doc_ids = []
                        st.session_state.selected_doc_ids = [doc_options[doc] for doc in selected_docs]
                    else:
                        st.info("No documents available. Upload documents in the Knowledge Base tab.")
                else:
                    st.warning("Could not load documents list")
            except Exception as e:
                st.warning(f"Error loading documents: {str(e)}")

        # Display uploaded files
        if uploaded_files:
            st.write("**Attached files:**")
            for file in uploaded_files:
                file_size = len(file.getvalue()) / 1024  # KB
                st.caption(f"📄 {file.name} ({file_size:.1f} KB)")

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Show attached files if any
            if message.get("files"):
                with st.expander("📎 Attachments"):
                    for file_info in message["files"]:
                        st.caption(f"📄 {file_info['name']}")

            # Show conversation indicator if this was part of a multi-stage conversation
            if message.get("needs_more_info"):
                st.caption("💬 Waiting for more information...")

    # Chat input
    if prompt := st.chat_input(get_text("chat_input", lang)):
        # Process uploaded files
        file_contents = []
        file_info_list = []
        if uploaded_files:
            for file in uploaded_files:
                file_bytes = file.getvalue()
                file_name = file.name
                file_type = file.type

                # Handle different file types
                if file_type.startswith('image/'):
                    # Encode image as base64
                    base64_image = base64.b64encode(file_bytes).decode('utf-8')
                    file_contents.append({
                        "type": "image",
                        "name": file_name,
                        "data": base64_image,
                        "mime_type": file_type
                    })
                elif file_type == 'application/pdf':
                    # Extract PDF text content
                    try:
                        pdf_reader = PdfReader(BytesIO(file_bytes))
                        text_content = ""
                        for page in pdf_reader.pages:
                            text_content += page.extract_text() + "\n"
                        file_contents.append({
                            "type": "text",
                            "name": file_name,
                            "content": text_content,
                            "pages": len(pdf_reader.pages)
                        })
                    except Exception as e:
                        # If PDF extraction fails, provide error info
                        file_contents.append({
                            "type": "file",
                            "name": file_name,
                            "size": len(file_bytes),
                            "error": f"Failed to extract PDF: {str(e)}"
                        })
                elif file_type in ['text/plain', 'text/markdown', 'text/csv', 'application/json']:
                    # Extract text content
                    text_content = file_bytes.decode('utf-8')
                    file_contents.append({
                        "type": "text",
                        "name": file_name,
                        "content": text_content
                    })
                else:
                    # For other files, provide basic info
                    file_contents.append({
                        "type": "file",
                        "name": file_name,
                        "size": len(file_bytes)
                    })

                file_info_list.append({"name": file_name, "type": file_type})

        # Build enhanced prompt with file context
        enhanced_prompt = prompt
        has_images = False

        if file_contents:
            # Check if we have images
            has_images = any(fc["type"] == "image" for fc in file_contents)

            # Add text file contexts
            text_files = [fc for fc in file_contents if fc["type"] == "text"]
            if text_files:
                # Add explicit instruction for document analysis
                files_context = "\n\n===== IMPORTANT: DOCUMENT ANALYSIS REQUIRED =====\n"
                files_context += "User has uploaded document(s). Please analyze the content below and respond to the user's question based on this document.\n\n"

                for fc in text_files:
                    # For PDF files, include more content (up to 10000 chars for better understanding)
                    # For other text files, include full content or 5000 chars
                    if fc['name'].endswith('.pdf'):
                        max_chars = 10000
                        content_preview = fc['content'][:max_chars]
                        truncated = len(fc['content']) > max_chars
                        if truncated:
                            files_context += f"\n[DOCUMENT: {fc['name']} - {fc.get('pages', '?')} pages PDF - First {max_chars} characters shown]\n"
                            files_context += f"---BEGIN DOCUMENT CONTENT---\n{content_preview}\n---END DOCUMENT CONTENT (TRUNCATED)---\n"
                        else:
                            files_context += f"\n[DOCUMENT: {fc['name']} - {fc.get('pages', '?')} pages PDF - Complete Content]\n"
                            files_context += f"---BEGIN DOCUMENT CONTENT---\n{content_preview}\n---END DOCUMENT CONTENT---\n"
                    else:
                        max_chars = 5000
                        content_preview = fc['content'][:max_chars]
                        truncated = len(fc['content']) > max_chars
                        if truncated:
                            files_context += f"\n[DOCUMENT: {fc['name']} - First {max_chars} characters shown]\n"
                            files_context += f"---BEGIN DOCUMENT CONTENT---\n{content_preview}\n---END DOCUMENT CONTENT (TRUNCATED)---\n"
                        else:
                            files_context += f"\n[DOCUMENT: {fc['name']} - Complete Content]\n"
                            files_context += f"---BEGIN DOCUMENT CONTENT---\n{content_preview}\n---END DOCUMENT CONTENT---\n"

                files_context += "\n===== END OF DOCUMENT(S) =====\n\nUser's Question: "
                enhanced_prompt = files_context + prompt

            # For images, we'll add them separately to the API call
            vision_models = ["gpt-4o", "gpt-4o-mini", "claude-3-opus", "claude-3-5-sonnet", "claude-3-sonnet", "gemini-1.5-pro", "gemini-1.5-flash"]
            if has_images and model_choice not in vision_models:
                # Show error message with available vision models
                if lang == "zh-TW":
                    error_msg = """
                    ⚠️ **所選模型不支援圖像輸入**

                    您上傳了圖片，但當前選擇的模型 `{}` 無法處理圖像。

                    **請選擇以下支援視覺功能的模型之一：**
                    - gpt-4o (OpenAI)
                    - gpt-4o-mini (OpenAI)
                    - claude-3-5-sonnet (Anthropic)
                    - claude-3-opus (Anthropic)
                    - claude-3-sonnet (Anthropic)
                    - gemini-1.5-pro (Google)
                    - gemini-1.5-flash (Google)

                    請從左側欄更換模型後再試。
                    """.format(model_choice)
                else:
                    error_msg = """
                    ⚠️ **Selected model doesn't support vision**

                    You have uploaded image(s), but the current model `{}` cannot process images.

                    **Please select one of these vision-capable models:**
                    - gpt-4o (OpenAI)
                    - gpt-4o-mini (OpenAI)
                    - claude-3-5-sonnet (Anthropic)
                    - claude-3-opus (Anthropic)
                    - claude-3-sonnet (Anthropic)
                    - gemini-1.5-pro (Google)
                    - gemini-1.5-flash (Google)

                    Please change your model selection in the sidebar and try again.
                    """.format(model_choice)

                st.error(error_msg)
                st.stop()  # Prevent submission

        # RAG Knowledge Search
        rag_context = ""
        if rag_search_enabled:
            try:
                # Get selected doc IDs if any
                selected_doc_ids = st.session_state.get("selected_doc_ids", [])

                search_payload = {
                    "query": prompt,
                    "top_k": 3,
                    "similarity_threshold": 0.5
                }

                # Add doc_ids filter if specific documents are selected
                if selected_doc_ids:
                    search_payload["doc_ids"] = selected_doc_ids

                rag_response = requests.post(
                    f"{MCP_SERVER_URL}/rag/search",
                    json=search_payload,
                    timeout=10
                )

                if rag_response.status_code == 200:
                    rag_results = rag_response.json()
                    if rag_results.get('count', 0) > 0:
                        rag_context = "\n\n**[RAG Knowledge Context]**\n"
                        for result in rag_results['results']:
                            rag_context += f"\n- {result['title']} (similarity: {result['score']:.2f})\n"
                            rag_context += f"  {result['content'][:200]}...\n"

                        enhanced_prompt = f"{rag_context}\n\n**[User Question]**\n{enhanced_prompt}"
            except Exception as e:
                st.warning(f"RAG search failed: {str(e)}")

        if web_search_enabled:
            enhanced_prompt = f"[WEB_SEARCH_ENABLED] {enhanced_prompt}"

        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "files": file_info_list if file_info_list else None
        })

        with st.chat_message("user"):
            st.markdown(prompt)
            if file_info_list:
                with st.expander("📎 Attachments"):
                    for file_info in file_info_list:
                        st.caption(f"📄 {file_info['name']}")
            if rag_context:
                with st.expander("📚 RAG Knowledge Context"):
                    st.markdown(rag_context)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner(get_text("thinking", lang)):
                try:
                    start_time = time.time()

                    # Truncate conversation history to fit within context limits
                    truncated_history = truncate_conversation_history(
                        st.session_state.conversation_history,
                        model_choice
                    )

                    # Show truncation warning if needed
                    if len(truncated_history) < len(st.session_state.conversation_history):
                        removed = len(st.session_state.conversation_history) - len(truncated_history)
                        st.caption(f"ℹ️ {removed} " + ("條舊消息已移除以節省上下文空間" if lang == "zh-TW" else "old messages removed to save context"))

                    # Build request payload
                    request_payload = {
                        "task": enhanced_prompt,
                        "model": model_choice,
                        "conversation_history": truncated_history,
                        "temperature": temperature,
                        "top_p": top_p,
                        "top_k": top_k
                    }

                    # Add image data for vision models
                    if has_images and file_contents:
                        image_files = [fc for fc in file_contents if fc["type"] == "image"]
                        if image_files:
                            # Add images to context
                            request_payload["images"] = []
                            for img in image_files:
                                request_payload["images"].append({
                                    "name": img["name"],
                                    "data": img["data"],
                                    "mime_type": img["mime_type"]
                                })

                    # Use /agent/execute endpoint with conversation history support
                    # Longer timeout for PDF processing with qwen2.5:7b (180 seconds)
                    response = requests.post(
                        f"{AGENT_SERVICE_URL}/agent/execute",
                        json=request_payload,
                        timeout=180
                    )

                    elapsed_time = time.time() - start_time

                    if response.ok:
                        result = response.json()
                        answer = result["result"]
                        needs_more_info = result.get("needs_more_info", False)
                        conversation_active = result.get("metadata", {}).get("conversation_active", False)

                        # Display the response
                        st.markdown(answer)

                        # Show conversation status
                        if needs_more_info or conversation_active:
                            st.info("💬 " + ("請繼續提供資訊..." if lang == "zh-TW" else "Please provide more information..."))

                        # Show metadata
                        with st.expander(get_text("view_details", lang)):
                            metadata_display = {
                                get_text("model", lang): result.get("metadata", {}).get("model_used", model_choice),
                                get_text("response_time", lang): f"{elapsed_time:.2f}{get_text('seconds', lang)}",
                                "Tokens Used": result.get("metadata", {}).get("tokens_used", "N/A")
                            }

                            if needs_more_info:
                                metadata_display["Status"] = "Waiting for more info" if lang == "en" else "等待更多資訊"

                            st.json(metadata_display)

                            # Show execution steps if available
                            if result.get("steps"):
                                st.markdown("**Execution Steps:**")
                                for step in result["steps"]:
                                    st.text(f"• {step.get('step', 'Unknown')}: {step.get('status', 'unknown')}")

                        # Update conversation history for multi-stage conversations
                        if needs_more_info or conversation_active:
                            st.session_state.conversation_history.append({
                                "role": "user",
                                "content": prompt
                            })
                            st.session_state.conversation_history.append({
                                "role": "assistant",
                                "content": answer
                            })
                        else:
                            # Task completed, clear conversation history
                            st.session_state.conversation_history = []

                        # Add to display messages
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer,
                            "needs_more_info": needs_more_info
                        })
                    else:
                        error_msg = f"❌ {get_text('error', lang)}: {response.text}"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg
                        })
                        # Clear conversation history on error
                        st.session_state.conversation_history = []

                except requests.exceptions.Timeout:
                    error_msg = get_text("request_timeout", lang)
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
                    st.session_state.conversation_history = []
                except Exception as e:
                    error_msg = f"{get_text('request_failed', lang)}: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
                    st.session_state.conversation_history = []

with tab2:
    st.header(get_text("agent_header", lang))
    st.caption(get_text("agent_caption", lang))

    # Initialize selected_example in session state
    if "selected_example" not in st.session_state:
        st.session_state.selected_example = ""

    # Initialize agent tab conversation history
    if "agent_conversation_history" not in st.session_state:
        st.session_state.agent_conversation_history = []

    # Initialize agent conversation messages for display
    if "agent_messages" not in st.session_state:
        st.session_state.agent_messages = []

    # Initialize task input value
    if "task_input_value" not in st.session_state:
        st.session_state.task_input_value = ""

    # Show conversation history
    if st.session_state.agent_messages:
        st.subheader("💬 " + ("對話歷史" if lang == "zh-TW" else "Conversation History"))
        for msg in st.session_state.agent_messages:
            if msg["role"] == "user":
                st.info(f"**You:** {msg['content']}")
            else:
                st.success(f"**Agent:** {msg['content']}")

        st.divider()

    col1, col2 = st.columns([3, 1])

    with col1:
        # Use task_input_value to control the text_area
        if st.session_state.selected_example:
            st.session_state.task_input_value = st.session_state.selected_example
            st.session_state.selected_example = ""

        task = st.text_area(
            get_text("describe_task", lang),
            height=150,
            placeholder=get_text("task_placeholder", lang),
            value=st.session_state.task_input_value,
            key="task_input"
        )

    with col2:
        # Agent type mapping with icons and names
        agent_options = {
            "general": f"🤖 {get_text('agent_general', lang)}",
            "research": f"🔬 {get_text('agent_research', lang)}",
            "analysis": f"📊 {get_text('agent_analysis', lang)}",
            "contract_review": f"📋 {get_text('agent_contract_review', lang)}"
        }

        agent_type_display = st.selectbox(
            get_text("agent_type", lang),
            options=list(agent_options.values()),
            help=get_text("agent_type_help", lang)
        )

        # Reverse mapping to get the agent_type ID
        agent_type = [k for k, v in agent_options.items() if v == agent_type_display][0]

        # File upload for contracts and documents
        st.markdown("---")
        uploaded_file = st.file_uploader(
            "📎 " + get_text("upload_file", lang),
            type=['pdf', 'docx', 'txt'],
            help=get_text("upload_file_help", lang),
            key="agent_file_upload"
        )

        execute_button = st.button(get_text("execute_task", lang), use_container_width=True)

        # Add clear conversation button
        if st.session_state.agent_conversation_history:
            if st.button("🔄 " + ("重置對話" if lang == "zh-TW" else "Reset Conversation"), use_container_width=True):
                st.session_state.agent_conversation_history = []
                st.session_state.agent_messages = []
                st.rerun()

    # Initialize session state for file content
    if 'uploaded_file_content' not in st.session_state:
        st.session_state.uploaded_file_content = ""
    if 'uploaded_file_name' not in st.session_state:
        st.session_state.uploaded_file_name = ""

    # Process uploaded file if present
    if uploaded_file is not None:
        # Only process if it's a new file or different file
        if uploaded_file.name != st.session_state.uploaded_file_name:
            try:
                file_content = ""
                if uploaded_file.type == "application/pdf":
                    # Extract text from PDF
                    import PyPDF2
                    import io
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                    file_content = "\n\n".join([page.extract_text() for page in pdf_reader.pages])
                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    # Extract text from DOCX
                    import docx
                    import io
                    doc = docx.Document(io.BytesIO(uploaded_file.read()))
                    file_content = "\n\n".join([paragraph.text for paragraph in doc.paragraphs])
                elif uploaded_file.type == "text/plain":
                    # Extract text from TXT
                    file_content = uploaded_file.read().decode('utf-8')

                # Store in session state
                st.session_state.uploaded_file_content = file_content
                st.session_state.uploaded_file_name = uploaded_file.name

                if file_content:
                    st.success(f"✅ {get_text('file_loaded', lang)}: {uploaded_file.name} ({len(file_content)} {get_text('characters', lang)})")
                else:
                    st.warning(f"⚠️ 文件已上傳但未能提取內容: {uploaded_file.name}")
            except Exception as e:
                st.error(f"❌ {get_text('file_load_error', lang)}: {str(e)}")
                st.session_state.uploaded_file_content = ""
    elif st.session_state.uploaded_file_content:
        # File was uploaded before, show status
        st.info(f"📎 {get_text('file_loaded', lang)}: {st.session_state.uploaded_file_name} ({len(st.session_state.uploaded_file_content)} {get_text('characters', lang)})")

    # Get file content from session state
    file_content = st.session_state.uploaded_file_content

    if execute_button and (task or file_content):
        # Combine task description with file content
        if file_content and not task.strip():
            # If only file uploaded without task description, provide default instruction
            if agent_type == "contract_review":
                default_instruction = {
                    "zh-TW": "請審查以下契約內容，提供風險評估、條款分析和建議：",
                    "zh-CN": "请审查以下合同内容，提供风险评估、条款分析和建议：",
                    "en": "Please review the following contract, provide risk assessment, clause analysis and recommendations:",
                    "vi": "Vui lòng xem xét hợp đồng sau, cung cấp đánh giá rủi ro, phân tích điều khoản và khuyến nghị:"
                }
                combined_task = f"{default_instruction.get(lang, default_instruction['en'])}\n\n{file_content}"
            else:
                # For other agent types, just use the file content
                combined_task = f"{get_text('file_content', lang)}:\n\n{file_content}"
        elif file_content:
            # Both task and file content present
            combined_task = f"{task}\n\n{get_text('file_content', lang)}:\n\n{file_content}"
        else:
            # Only task, no file
            combined_task = task

        # Clear the task input after execution starts
        st.session_state.selected_example = ""
        st.session_state.task_input_value = ""

        with st.spinner(get_text("executing", lang)):
            try:
                start_time = time.time()

                response = requests.post(
                    f"{AGENT_SERVICE_URL}/agent/execute",
                    json={
                        "task": combined_task,
                        "agent_type": agent_type,
                        "model": model_choice,
                        "conversation_history": st.session_state.agent_conversation_history,
                        "temperature": temperature,
                        "top_p": top_p,
                        "top_k": top_k
                    },
                    timeout=180
                )

                elapsed_time = time.time() - start_time

                if response.ok:
                    result = response.json()
                    needs_more_info = result.get("needs_more_info", False)
                    conversation_active = result.get("metadata", {}).get("conversation_active", False)

                    # Add user message to conversation display
                    st.session_state.agent_messages.append({
                        "role": "user",
                        "content": task
                    })

                    # Add agent response to conversation display
                    st.session_state.agent_messages.append({
                        "role": "assistant",
                        "content": result["result"]
                    })

                    # Update conversation history if more info needed
                    if needs_more_info or conversation_active:
                        st.session_state.agent_conversation_history.append({
                            "role": "user",
                            "content": task
                        })
                        st.session_state.agent_conversation_history.append({
                            "role": "assistant",
                            "content": result["result"]
                        })

                        # Show that conversation is active
                        st.info("💬 " + ("請在上方文字框繼續提供資訊，然後點擊「執行任務」" if lang == "zh-TW" else "Please provide more information in the text box above and click 'Execute Task'"))
                    else:
                        # Task completed, clear conversation history
                        st.session_state.agent_conversation_history = []
                        st.success(get_text("task_complete", lang, time=f"{elapsed_time:.2f}"))

                    # Show result
                    st.subheader(get_text("execution_result", lang))
                    st.write(result["result"])

                    # Show execution steps
                    with st.expander(get_text("view_steps", lang), expanded=True):
                        for i, step in enumerate(result["steps"], 1):
                            # Map status to icon
                            status = step.get("status", "unknown")
                            if status == "success":
                                status_icon = "✅"
                            elif status == "failed":
                                status_icon = "❌"
                            elif status in ["detected", "executing"]:
                                status_icon = "🔍"
                            else:
                                status_icon = "ℹ️"

                            st.write(f"{status_icon} **{get_text('step', lang)} {i}: {step['step']}**")

                            # Display step details based on what's available
                            if "result" in step:
                                # Check if result is a dict (tool execution result)
                                if isinstance(step["result"], dict):
                                    st.json(step["result"])
                                else:
                                    st.caption(step["result"])
                            elif "tool" in step:
                                st.caption(f"🔧 Tool: **{step['tool']}**")
                                if "arguments" in step:
                                    # Show arguments inline with a toggle
                                    with st.container():
                                        st.caption("Arguments:")
                                        st.json(step["arguments"])
                            elif "error" in step:
                                st.error(f"❌ Error: {step['error']}")

                    # Show MCP Usage Information
                    mcp_usage = result.get("metadata", {}).get("mcp_usage", {})
                    if mcp_usage and any([mcp_usage.get("tools_used"), mcp_usage.get("resources_accessed")]):
                        with st.expander(get_text("mcp_usage", lang), expanded=False):
                            # Tools Used
                            if mcp_usage.get("tools_used"):
                                st.markdown(f"**{get_text('tools_used', lang)}** ({len(mcp_usage['tools_used'])})")
                                for idx, tool in enumerate(mcp_usage["tools_used"], 1):
                                    st.markdown(f"**{idx}. {tool['name']}**")
                                    with st.container():
                                        st.caption(f"📥 {get_text('arguments', lang)}:")
                                        st.json(tool.get("arguments", {}))
                                        if tool.get("result_summary"):
                                            st.caption(f"📤 {get_text('result', lang)}: {tool['result_summary']}")
                                st.divider()

                            # Resources Accessed
                            if mcp_usage.get("resources_accessed"):
                                st.markdown(f"**{get_text('resources_accessed', lang)}** ({len(mcp_usage['resources_accessed'])})")
                                for resource in mcp_usage["resources_accessed"]:
                                    if resource["type"] == "document":
                                        st.caption(f"📄 Document ID: {resource['id']}")
                                    elif resource["type"] == "search":
                                        st.caption(f"🔍 Search: {resource['query']}")
                                st.divider()

                            # Sampling Parameters
                            if mcp_usage.get("sampling_parameters"):
                                st.markdown(f"**{get_text('sampling_params', lang)}**")
                                params = mcp_usage["sampling_parameters"]
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Temperature", f"{params.get('temperature', 0.7):.2f}")
                                with col2:
                                    st.metric("Top-P", f"{params.get('top_p', 0.9):.2f}")
                                with col3:
                                    st.metric("Top-K", params.get('top_k', 40))
                                st.divider()

                            # System Prompt
                            if mcp_usage.get("system_prompt"):
                                st.markdown(f"**{get_text('system_prompt', lang)}**")
                                with st.container():
                                    st.text_area(
                                        label="",
                                        value=mcp_usage["system_prompt"],
                                        height=150,
                                        disabled=True,
                                        label_visibility="collapsed"
                                    )

                    # Show metadata
                    with st.expander(get_text("task_details", lang)):
                        metadata_display = result["metadata"].copy()
                        if needs_more_info:
                            metadata_display["conversation_status"] = "waiting_for_info"
                        # Remove mcp_usage from metadata display (shown above)
                        if "mcp_usage" in metadata_display:
                            del metadata_display["mcp_usage"]
                        st.json(metadata_display)

                    # Rerun to show updated conversation history
                    st.rerun()
                else:
                    st.error(f"{get_text('task_failed', lang)}: {response.text}")
                    # Clear conversation on error
                    st.session_state.agent_conversation_history = []

            except requests.exceptions.Timeout:
                st.error(get_text("task_timeout", lang))
                st.session_state.agent_conversation_history = []
            except Exception as e:
                st.error(f"{get_text('execution_failed', lang)}: {str(e)}")
                st.session_state.agent_conversation_history = []

    elif execute_button:
        st.warning(get_text("enter_task", lang))

    # Example tasks
    st.divider()

    col_header, col_button = st.columns([3, 1])
    with col_header:
        st.subheader(get_text("example_tasks", lang))
    with col_button:
        if st.button("🎲 " + get_text("generate_example", lang), use_container_width=True):
            # Define a pool of example tasks for different languages
            example_pool = {
                "zh-TW": [
                    "發送郵件給 team@example.com，主旨：每週會議，內容：提醒大家本週五下午3點開會",
                    "分析上個月的銷售數據並生成報告",
                    "搜索關於人工智能最新趨勢的文章",
                    "創建一個任務：完成Q1財務報表，截止日期：下週五",
                    "總結這份文件的主要內容",
                    "計算ROI：初始投資10萬，年收益3萬，期限5年",
                    "翻譯這段文字到英文：我們的產品在市場上表現優異",
                    "使用語義搜索找到與'機器學習'相關的文檔"
                ],
                "zh-CN": [
                    "发送邮件给 team@example.com，主题：每周会议，内容：提醒大家本周五下午3点开会",
                    "分析上个月的销售数据并生成报告",
                    "搜索关于人工智能最新趋势的文章",
                    "创建一个任务：完成Q1财务报表，截止日期：下周五",
                    "总结这份文件的主要内容",
                    "计算ROI：初始投资10万，年收益3万，期限5年",
                    "翻译这段文字到英文：我们的产品在市场上表现优异",
                    "使用语义搜索找到与'机器学习'相关的文档"
                ],
                "en": [
                    "Send email to team@example.com, subject: Weekly Meeting, body: Reminder for Friday 3pm meeting",
                    "Analyze last month's sales data and generate a report",
                    "Search for articles about the latest AI trends",
                    "Create a task: Complete Q1 financial report, deadline: next Friday",
                    "Summarize the main points of this document",
                    "Calculate ROI: Initial investment $100k, annual return $30k, period 5 years",
                    "Translate this text to Chinese: Our product performs exceptionally well in the market",
                    "Use semantic search to find documents related to 'machine learning'"
                ],
                "vi": [
                    "Gửi email đến team@example.com, chủ đề: Cuộc họp hàng tuần, nội dung: Nhắc nhở cuộc họp Thứ Sáu 3 giờ chiều",
                    "Phân tích dữ liệu bán hàng tháng trước và tạo báo cáo",
                    "Tìm kiếm bài viết về xu hướng AI mới nhất",
                    "Tạo nhiệm vụ: Hoàn thành báo cáo tài chính Q1, hạn chót: Thứ Sáu tuần sau",
                    "Tóm tắt các điểm chính của tài liệu này",
                    "Tính ROI: Đầu tư ban đầu $100k, lợi nhuận hàng năm $30k, thời hạn 5 năm",
                    "Dịch văn bản này sang tiếng Trung: Sản phẩm của chúng tôi hoạt động rất tốt trên thị trường",
                    "Sử dụng tìm kiếm ngữ nghĩa để tìm tài liệu liên quan đến 'machine learning'"
                ]
            }

            # Get pool for current language
            pool = example_pool.get(lang, example_pool["en"])
            # Pick a random example
            random_example = random.choice(pool)
            st.session_state.selected_example = random_example
            st.rerun()

    examples = [
        get_text("example_1", lang),
        get_text("example_2", lang),
        get_text("example_3", lang),
        get_text("example_4", lang)
    ]

    cols = st.columns(2)
    for i, example in enumerate(examples):
        with cols[i % 2]:
            if st.button(f"📋 {example}", key=f"example_{i}"):
                st.session_state.selected_example = example
                st.rerun()

with tab3:
    st.header(get_text("agents_catalog_header", lang))
    st.caption(get_text("agents_catalog_caption", lang))

    # Agent Types Section
    st.subheader(get_text("agent_types", lang))

    agent_configs = {
        "general": {
            "name": get_text("agent_general", lang),
            "icon": "🤖",
            "description": get_text("agent_general_desc", lang),
            "use_cases": get_text("agent_general_uses", lang),
            "prompt": """你是一個企業AI助手，可以直接回答問題或使用各種工具來幫助用戶完成任務。

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
- 用戶提供了所有信息 → 直接執行發送郵件"""
        },
        "research": {
            "name": get_text("agent_research", lang),
            "icon": "🔬",
            "description": get_text("agent_research_desc", lang),
            "use_cases": get_text("agent_research_uses", lang),
            "prompt": """你是一個專業的研究助手，擅長信息收集、分析和整理。

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

重點：深度、準確性、來源可靠性"""
        },
        "analysis": {
            "name": get_text("agent_analysis", lang),
            "icon": "📊",
            "description": get_text("agent_analysis_desc", lang),
            "use_cases": get_text("agent_analysis_uses", lang),
            "prompt": """你是一個數據分析專家，專注於數據處理、分析和可視化。

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
        },
        "contract_review": {
            "name": get_text("agent_contract_review", lang),
            "icon": "📋",
            "description": get_text("agent_contract_review_desc", lang),
            "use_cases": get_text("agent_contract_review_uses", lang),
            "prompt": """你是一個專業的契約審查助手，專注於契約分析、風險評估和合規檢查。

你的專長：
1. 使用 review_contract 工具進行全面的契約審查
2. 使用 analyze_clause 工具分析特定條款
3. 使用 compare_contracts 工具比較多份契約
4. 識別高風險條款和不公平條件
5. 評估契約合規性和完整性

工作流程：
1. 接收契約內容後，先判斷契約類型（employment/nda/service/lease/sales）
2. 使用 review_contract 工具進行完整分析
3. 識別關鍵風險點並計算風險評分（0-100）
4. 檢查缺失的必要條款
5. 提供具體的修改建議和優先級排序

風險評估標準：
- 0-24分：低風險 ✅ （可以接受）
- 25-49分：中等風險 ⚠️ （需要仔細審查）
- 50-74分：高風險 🔴 （建議協商修改）
- 75-100分：極高風險 🚨 （存在重大問題）

重點關注：
- 無限責任條款
- 永久性義務
- 放棄權利條款
- 單方面決定權
- 過於寬泛的競業禁止
- 自動續約條款
- 模糊不清的用語

輸出格式：
1. 契約摘要（類型、當事人、關鍵條款）
2. 風險評分及等級
3. 具體風險分析（按嚴重程度分類）
4. 缺失條款清單
5. 優先級排序的建議事項

重要提醒：
- 此工具提供初步分析，不能替代專業法律諮詢
- 對於高價值或複雜契約，建議諮詢專業律師
- 分析基於一般法律原則，不針對特定司法管轄區

請使用清晰、專業的語言，確保用戶能夠理解風險並採取行動。"""
        }
    }

    # Display agents in 2x2 grid layout
    agent_items = list(agent_configs.items())

    # First row: General and Research
    cols_row1 = st.columns(2)
    for idx, (agent_id, config) in enumerate(agent_items[:2]):
        with cols_row1[idx]:
            st.markdown(f"### {config['icon']} {config['name']}")
            st.caption(config['description'])
            st.markdown(f"**{get_text('use_cases', lang)}:**")
            st.markdown(config['use_cases'])

            with st.expander(get_text("view_system_prompt", lang)):
                st.text_area(
                    label="",
                    value=config['prompt'],
                    height=200,
                    disabled=True,
                    label_visibility="collapsed",
                    key=f"prompt_{agent_id}"
                )

    # Second row: Analysis and Contract Review
    cols_row2 = st.columns(2)
    for idx, (agent_id, config) in enumerate(agent_items[2:]):
        with cols_row2[idx]:
            st.markdown(f"### {config['icon']} {config['name']}")
            st.caption(config['description'])
            st.markdown(f"**{get_text('use_cases', lang)}:**")
            st.markdown(config['use_cases'])

            with st.expander(get_text("view_system_prompt", lang)):
                st.text_area(
                    label="",
                    value=config['prompt'],
                    height=200,
                    disabled=True,
                    label_visibility="collapsed",
                    key=f"prompt_{agent_id}"
                )

    st.divider()

    # Default Sampling Parameters
    st.subheader(get_text("default_sampling", lang))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Temperature", "0.7", help=get_text("default_temp_help", lang))
    with col2:
        st.metric("Top-P", "0.9", help=get_text("default_topp_help", lang))
    with col3:
        st.metric("Top-K", "40", help=get_text("default_topk_help", lang))

    st.info(get_text("sampling_info", lang))

    st.divider()

    # MCP Tools Section
    st.subheader(get_text("available_tools", lang))

    # Fetch tools from MCP server
    try:
        mcp_url = os.getenv("MCP_SERVER_URL", "http://mcp-server:8000")
        response = requests.get(f"{mcp_url}/tools/list", timeout=5)
        if response.ok:
            tools_data = response.json()
            tools = tools_data.get("tools", [])

            st.success(f"{get_text('tools_loaded', lang)}: {len(tools)} {get_text('tools', lang)}")

            # Group tools by category
            categorized_tools = {}
            for tool in tools:
                category = tool.get("category", "other")
                if category not in categorized_tools:
                    categorized_tools[category] = []
                categorized_tools[category].append(tool)

            # Display tools by category
            for category, category_tools in sorted(categorized_tools.items()):
                with st.expander(f"📂 {category.title()} ({len(category_tools)})"):
                    for tool in category_tools:
                        st.markdown(f"**{tool['name']}**")
                        st.caption(f"📝 {tool['description']}")
                        if tool.get("parameters"):
                            params_str = ", ".join([f"`{k}`: {v}" for k, v in tool["parameters"].items()])
                            st.caption(f"⚙️ {get_text('parameters', lang)}: {params_str}")
                        st.markdown("---")
        else:
            st.warning(get_text("tools_load_failed", lang))
            st.caption(f"Status: {response.status_code}")
    except Exception as e:
        st.error(f"{get_text('tools_load_error', lang)}: {str(e)}")

    st.divider()

    # Resources Section
    st.subheader(get_text("available_resources", lang))

    resource_types = {
        get_text("resource_documents", lang): {
            "icon": "📄",
            "description": get_text("resource_documents_desc", lang),
            "access": get_text("resource_documents_access", lang)
        },
        get_text("resource_knowledge_base", lang): {
            "icon": "📚",
            "description": get_text("resource_knowledge_desc", lang),
            "access": get_text("resource_knowledge_access", lang)
        },
        get_text("resource_web", lang): {
            "icon": "🌐",
            "description": get_text("resource_web_desc", lang),
            "access": get_text("resource_web_access", lang)
        },
        get_text("resource_databases", lang): {
            "icon": "🗄️",
            "description": get_text("resource_databases_desc", lang),
            "access": get_text("resource_databases_access", lang)
        }
    }

    for resource_name, resource_info in resource_types.items():
        with st.container():
            col_icon, col_content = st.columns([1, 9])
            with col_icon:
                st.markdown(f"<div style='font-size: 2rem; text-align: center;'>{resource_info['icon']}</div>", unsafe_allow_html=True)
            with col_content:
                st.markdown(f"**{resource_name}**")
                st.caption(resource_info['description'])
                st.caption(f"🔑 {get_text('access_via', lang)}: {resource_info['access']}")
            st.markdown("---")

with tab4:
    st.header(get_text("models_config_header", lang))
    st.caption(get_text("models_config_caption", lang))

    # Load litellm config
    import yaml
    import os

    config_path = "/app/config/litellm-config.yaml"

    def load_litellm_config():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            st.error(f"Error loading config: {str(e)}")
            return None

    def save_litellm_config(config_data):
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            return True
        except Exception as e:
            st.error(f"Error saving config: {str(e)}")
            return False

    # Load config
    litellm_config = load_litellm_config()

    if litellm_config:
        # Initialize session state for editing
        if 'editing_model' not in st.session_state:
            st.session_state.editing_model = None
        if 'adding_new_model' not in st.session_state:
            st.session_state.adding_new_model = False

        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button(get_text("add_new_model", lang), type="primary"):
                st.session_state.adding_new_model = True
                st.session_state.editing_model = None
                st.rerun()
        with col2:
            if st.button(get_text("reload_config", lang)):
                st.rerun()

        st.divider()

        # Add new model form
        if st.session_state.adding_new_model:
            with st.form("add_model_form"):
                st.subheader(get_text("add_new_model", lang))

                col1, col2 = st.columns(2)
                with col1:
                    new_model_name = st.text_input(get_text("model_name", lang), placeholder="gpt-4")
                    new_display_name = st.text_input(get_text("display_name", lang), placeholder="GPT-4 (OpenAI)")
                    new_model_provider = st.selectbox(
                        get_text("provider_type", lang),
                        ["openai", "anthropic", "ollama", "gemini", "custom"]
                    )
                    new_model_id = st.text_input(get_text("model_id", lang), placeholder="openai/gpt-4")

                with col2:
                    new_api_base = st.text_input(get_text("api_base", lang), placeholder="https://api.openai.com/v1")
                    new_api_key = st.text_input(
                        get_text("api_key", lang),
                        placeholder="os.environ/OPENAI_API_KEY or actual key",
                        type="password"
                    )
                    new_visible = st.checkbox(
                        get_text("visible_in_selection", lang),
                        value=True,
                        help=get_text("visible_help", lang)
                    )

                col_submit, col_cancel = st.columns([1, 5])
                with col_submit:
                    submitted = st.form_submit_button(get_text("save", lang), type="primary")
                with col_cancel:
                    cancelled = st.form_submit_button(get_text("cancel", lang))

                if submitted and new_model_name and new_model_id:
                    # Create new model entry
                    new_model = {
                        "model_name": new_model_name,
                        "visible": new_visible,
                        "litellm_params": {
                            "model": new_model_id
                        }
                    }

                    # Add display_name if provided
                    if new_display_name:
                        new_model["display_name"] = new_display_name

                    if new_api_base:
                        new_model["litellm_params"]["api_base"] = new_api_base
                    if new_api_key:
                        new_model["litellm_params"]["api_key"] = new_api_key

                    # Add to config
                    if "model_list" not in litellm_config:
                        litellm_config["model_list"] = []
                    litellm_config["model_list"].append(new_model)

                    if save_litellm_config(litellm_config):
                        st.success(get_text("model_added_success", lang))
                        st.session_state.adding_new_model = False
                        st.rerun()

                if cancelled:
                    st.session_state.adding_new_model = False
                    st.rerun()

        # Display models
        st.subheader(get_text("available_models", lang))

        if "model_list" in litellm_config:
            for idx, model in enumerate(litellm_config["model_list"]):
                model_name = model.get("model_name", "Unknown")
                display_name = model.get("display_name", model_name)
                litellm_params = model.get("litellm_params", {})
                model_id = litellm_params.get("model", "")
                api_base = litellm_params.get("api_base", "")
                api_key = litellm_params.get("api_key", "")

                # Determine provider
                provider = "Unknown"
                if "openai" in model_id.lower():
                    provider = "OpenAI"
                elif "anthropic" in model_id.lower() or "claude" in model_id.lower():
                    provider = "Anthropic"
                elif "ollama" in model_id.lower():
                    provider = "Ollama"
                elif "gemini" in model_id.lower():
                    provider = "Google"
                elif "llama" in model_name.lower():
                    provider = "Taiwan Gov"

                # Check if this model is being edited
                is_editing = st.session_state.editing_model == idx

                with st.expander(f"**{display_name}** ({model_name}) - {provider}", expanded=is_editing):
                    if is_editing:
                        # Edit mode
                        with st.form(f"edit_model_form_{idx}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                edit_model_name = st.text_input(
                                    get_text("model_name", lang),
                                    value=model_name,
                                    key=f"edit_name_{idx}"
                                )
                                edit_display_name = st.text_input(
                                    get_text("display_name", lang),
                                    value=display_name,
                                    key=f"edit_display_{idx}"
                                )
                                edit_model_id = st.text_input(
                                    get_text("model_id", lang),
                                    value=model_id,
                                    key=f"edit_id_{idx}"
                                )

                            with col2:
                                edit_api_base = st.text_input(
                                    get_text("api_base", lang),
                                    value=api_base,
                                    key=f"edit_base_{idx}"
                                )
                                # Mask API key display
                                display_key = api_key if len(api_key) < 20 else f"{api_key[:10]}...{api_key[-10:]}"
                                edit_api_key = st.text_input(
                                    get_text("api_key", lang),
                                    value=api_key,
                                    type="password",
                                    key=f"edit_key_{idx}"
                                )
                                edit_visible = st.checkbox(
                                    get_text("visible_in_selection", lang),
                                    value=model.get("visible", True),
                                    key=f"edit_visible_{idx}",
                                    help=get_text("visible_help", lang)
                                )

                            col_save, col_cancel, col_delete = st.columns([1, 1, 4])
                            with col_save:
                                save_clicked = st.form_submit_button(get_text("save", lang), type="primary")
                            with col_cancel:
                                cancel_clicked = st.form_submit_button(get_text("cancel", lang))
                            with col_delete:
                                delete_clicked = st.form_submit_button(get_text("delete", lang), type="secondary")

                            if save_clicked:
                                # Update model
                                litellm_config["model_list"][idx]["model_name"] = edit_model_name
                                litellm_config["model_list"][idx]["visible"] = edit_visible
                                if edit_display_name:
                                    litellm_config["model_list"][idx]["display_name"] = edit_display_name
                                litellm_config["model_list"][idx]["litellm_params"]["model"] = edit_model_id
                                if edit_api_base:
                                    litellm_config["model_list"][idx]["litellm_params"]["api_base"] = edit_api_base
                                else:
                                    litellm_config["model_list"][idx]["litellm_params"].pop("api_base", None)
                                if edit_api_key:
                                    litellm_config["model_list"][idx]["litellm_params"]["api_key"] = edit_api_key
                                else:
                                    litellm_config["model_list"][idx]["litellm_params"].pop("api_key", None)

                                if save_litellm_config(litellm_config):
                                    st.success(get_text("model_updated_success", lang))
                                    st.session_state.editing_model = None
                                    st.rerun()

                            if cancel_clicked:
                                st.session_state.editing_model = None
                                st.rerun()

                            if delete_clicked:
                                # Delete model
                                litellm_config["model_list"].pop(idx)
                                if save_litellm_config(litellm_config):
                                    st.success(get_text("model_deleted_success", lang))
                                    st.session_state.editing_model = None
                                    st.rerun()
                    else:
                        # View mode
                        col1, col2, col3 = st.columns([3, 3, 1])
                        with col1:
                            st.markdown(f"**{get_text('model_name', lang)}:** `{model_name}`")
                            st.markdown(f"**{get_text('model_id', lang)}:** `{model_id}`")
                            # Show visibility status
                            is_visible = model.get("visible", True)
                            visibility_icon = "✅" if is_visible else "❌"
                            visibility_text = get_text("visible", lang) if is_visible else get_text("hidden", lang)
                            st.markdown(f"**{get_text('visibility', lang)}:** {visibility_icon} {visibility_text}")
                        with col2:
                            st.markdown(f"**{get_text('provider', lang)}:** {provider}")
                            if api_base:
                                st.markdown(f"**{get_text('api_base', lang)}:** `{api_base}`")
                            if api_key:
                                masked_key = f"{api_key[:10]}..." if len(api_key) > 10 else "***"
                                st.markdown(f"**{get_text('api_key', lang)}:** `{masked_key}`")
                        with col3:
                            if st.button(get_text("edit", lang), key=f"edit_btn_{idx}"):
                                st.session_state.editing_model = idx
                                st.session_state.adding_new_model = False
                                st.rerun()

        # Config file info
        st.divider()
        st.info(f"{get_text('config_file_location', lang)}: `{config_path}`")

        # Raw config viewer
        with st.expander(get_text("view_raw_config", lang)):
            st.code(yaml.dump(litellm_config, default_flow_style=False, allow_unicode=True), language="yaml")

with tab5:
    st.header(get_text("monitor_header", lang))
    st.caption(get_text("monitor_caption", lang))

    col1, col2, col3 = st.columns(3)

    # Simulated metrics (should be fetched from Prometheus)
    with col1:
        st.metric(
            label=get_text("agent_service", lang),
            value=get_text("running", lang),
            delta=get_text("normal", lang)
        )

    with col2:
        st.metric(
            label=get_text("llm_service", lang),
            value=get_text("running", lang),
            delta=get_text("normal", lang)
        )

    with col3:
        st.metric(
            label=get_text("mcp_service", lang),
            value=get_text("running", lang),
            delta=get_text("normal", lang)
        )

    st.divider()

    # Monitoring links
    st.subheader(get_text("monitor_tools", lang))

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        **{get_text("grafana_dashboard", lang)}**
        - {get_text("grafana_url", lang)}: http://localhost:3000
        - {get_text("grafana_account", lang)}: admin
        - {get_text("grafana_password", lang)}: admin
        - {get_text("grafana_features", lang)}
        """)

    with col2:
        st.markdown(f"""
        **{get_text("prometheus", lang)}**
        - {get_text("grafana_url", lang)}: http://localhost:9090
        - {get_text("prometheus_features", lang)}
        """)

    st.info(get_text("monitor_tip", lang))

with tab6:
    st.header(get_text("rag_header", lang))
    st.caption(get_text("rag_caption", lang))

    # Create columns for layout
    col1, col2 = st.columns([1, 1])

    with col1:
        # Document Upload Section
        st.subheader(get_text("rag_upload_section", lang))

        uploaded_file = st.file_uploader(
            get_text("rag_upload_file", lang),
            type=['pdf', 'docx', 'txt'],
            help=get_text("rag_upload_help", lang)
        )

        doc_title = st.text_input(get_text("rag_doc_title", lang))
        doc_category = st.text_input(get_text("rag_doc_category", lang), value="General")
        doc_tags = st.text_input(get_text("rag_doc_tags", lang), placeholder="AI, Documentation, Enterprise")

        if st.button(get_text("rag_upload_button", lang)):
            if uploaded_file and doc_title:
                with st.spinner(get_text("rag_uploading", lang)):
                    try:
                        # Prepare file upload
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        data = {
                            "title": doc_title,
                            "category": doc_category,
                            "tags": doc_tags
                        }

                        # Upload to MCP server
                        response = requests.post(
                            f"{MCP_SERVER_URL}/rag/documents/upload",
                            files=files,
                            data=data,
                            timeout=30
                        )

                        if response.status_code == 200:
                            result = response.json()
                            st.success(get_text("rag_upload_success", lang).format(
                                doc_id=result.get('doc_id'),
                                chunks=result.get('chunks_count')
                            ))
                        else:
                            st.error(f"{get_text('rag_upload_error', lang)}: {response.text}")
                    except Exception as e:
                        st.error(f"{get_text('rag_upload_error', lang)}: {str(e)}")
            else:
                st.warning("Please provide both file and title!")

        st.divider()

        # Manual Text Input Section (for scanned PDFs or direct input)
        st.subheader("📝 " + ("直接輸入文本" if lang == "zh-TW" else "Direct Text Input"))
        st.caption("Alternative: Create document from text (useful for scanned PDFs)")

        with st.expander("Create document from text"):
            text_doc_title = st.text_input("Document Title", key="text_title")
            text_doc_content = st.text_area("Content", height=200, key="text_content",
                                           placeholder="Paste or type your document content here...")
            text_doc_category = st.text_input("Category", value="General", key="text_category")
            text_doc_tags = st.text_input("Tags (comma-separated)", key="text_tags")

            if st.button("Create from Text", key="create_text_doc"):
                if text_doc_title and text_doc_content:
                    with st.spinner("Creating document..."):
                        try:
                            response = requests.post(
                                f"{MCP_SERVER_URL}/rag/documents/text",
                                json={
                                    "title": text_doc_title,
                                    "content": text_doc_content,
                                    "category": text_doc_category,
                                    "tags": [t.strip() for t in text_doc_tags.split(",")] if text_doc_tags else []
                                },
                                timeout=30
                            )

                            if response.status_code == 200:
                                result = response.json()
                                st.success(f"✅ Document created! ID: {result.get('doc_id')}, Chunks: {result.get('chunks_count')}")
                            else:
                                st.error(f"❌ Error: {response.text}")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                else:
                    st.warning("Please provide both title and content!")

        st.divider()

        # Semantic Search Section
        st.subheader(get_text("rag_search_section", lang))

        search_query = st.text_input(
            get_text("rag_search_query", lang),
            placeholder=get_text("rag_search_placeholder", lang)
        )

        col_search1, col_search2 = st.columns(2)
        with col_search1:
            top_k = st.slider(get_text("rag_search_topk", lang), 1, 10, 5)
        with col_search2:
            threshold = st.slider(get_text("rag_search_threshold", lang), 0.0, 1.0, 0.5, 0.05)

        if st.button(get_text("rag_search_button", lang)):
            if search_query:
                with st.spinner(get_text("rag_searching", lang)):
                    try:
                        response = requests.post(
                            f"{MCP_SERVER_URL}/rag/search",
                            json={
                                "query": search_query,
                                "top_k": top_k,
                                "similarity_threshold": threshold
                            },
                            timeout=15
                        )

                        if response.status_code == 200:
                            results = response.json()

                            st.subheader(get_text("rag_search_results", lang))

                            if results.get('count', 0) > 0:
                                for i, result in enumerate(results['results'], 1):
                                    with st.expander(f"{i}. {result['title']} - {get_text('rag_result_score', lang)}: {result['score']:.3f}"):
                                        st.write(f"**{get_text('rag_doc_id', lang)}:** {result['doc_id']}")
                                        st.write(f"**{get_text('rag_result_content', lang)}:**")
                                        st.write(result['content'])
                            else:
                                st.info(get_text("rag_no_results", lang))
                        else:
                            st.error(f"Search failed: {response.text}")
                    except Exception as e:
                        st.error(f"Search error: {str(e)}")

    with col2:
        # Document List Section
        st.subheader(get_text("rag_docs_section", lang))

        try:
            response = requests.get(f"{MCP_SERVER_URL}/rag/documents?limit=10", timeout=5)

            if response.status_code == 200:
                docs_data = response.json()
                total = docs_data.get('total', 0)
                st.caption(get_text("rag_docs_total", lang).format(total=total))

                for doc in docs_data.get('documents', []):
                    with st.expander(f"📄 {doc['title']}"):
                        st.write(f"**{get_text('rag_doc_id', lang)}:** {doc['id']}")
                        st.write(f"**{get_text('rag_doc_category', lang)}:** {doc.get('category', 'N/A')}")
                        st.write(f"**{get_text('rag_doc_created', lang)}:** {doc.get('created_at', 'N/A')}")

                        if st.button(f"🗑️ {get_text('rag_doc_delete', lang)}", key=f"delete_{doc['id']}"):
                            try:
                                del_response = requests.delete(
                                    f"{MCP_SERVER_URL}/rag/documents/{doc['id']}",
                                    timeout=5
                                )
                                if del_response.status_code == 200:
                                    st.success("Document deleted!")
                                    st.rerun()
                                else:
                                    st.error(f"Delete failed: {del_response.text}")
                            except Exception as e:
                                st.error(f"Delete error: {str(e)}")
            else:
                st.error(f"Failed to load documents: {response.text}")
        except Exception as e:
            st.error(f"Error loading documents: {str(e)}")

        st.divider()

        # Stats Section
        st.subheader(get_text("rag_stats_section", lang))

        try:
            with st.spinner(get_text("rag_stats_loading", lang)):
                response = requests.get(f"{MCP_SERVER_URL}/rag/stats", timeout=5)

                if response.status_code == 200:
                    stats = response.json()

                    col_stat1, col_stat2 = st.columns(2)
                    with col_stat1:
                        st.metric(
                            get_text("rag_stats_total_docs", lang),
                            stats.get('documents', {}).get('total', 0)
                        )
                    with col_stat2:
                        st.metric(
                            get_text("rag_stats_total_vectors", lang),
                            stats.get('vectors', {}).get('points_count', 0)
                        )

                    st.caption(f"{get_text('rag_stats_collection', lang)}: {stats.get('vectors', {}).get('collection_name', 'N/A')}")
                else:
                    st.error(f"Failed to load stats: {response.text}")
        except Exception as e:
            st.error(f"Error loading stats: {str(e)}")

with tab7:
    st.header("📚 Project Documentation")
    st.caption("Complete documentation for the AI Platform")

    # Documentation navigation
    doc_sections = {
        "📖 Quick Start": "README.md",
        "🗄️ Database Schema": "DATABASE_SCHEMA.md",
        "🔧 Troubleshooting Guide": "TROUBLESHOOTING_GUIDE.md",
        "🧠 Context-Aware Agent": "CONTEXT_AWARE_AGENT_GUIDE.md",
        "📧 SMTP Configuration": "SMTP_CONFIGURATION_GUIDE.md",
        "📱 LINE Messaging Setup": "LINE_SETUP_GUIDE.md",
        "✅ Test Results": "TEST_RESULTS.md",
        "🚀 Deployment Guide": "DEPLOYMENT_GUIDE.md",
        "📝 Changelog": "CHANGELOG.md",
        "📊 Project Summary": "PROJECT_SUMMARY.md"
    }

    # Create columns for documentation cards
    cols = st.columns(2)

    for idx, (title, filename) in enumerate(doc_sections.items()):
        with cols[idx % 2]:
            with st.container():
                st.subheader(title)

                # Read documentation file
                doc_path = f"/app/{filename}"  # In Docker container
                try:
                    if os.path.exists(doc_path):
                        with open(doc_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Show preview
                        preview = content[:200] + "..." if len(content) > 200 else content
                        st.text(preview)

                        # View button
                        if st.button(f"📄 View {title}", key=f"view_{filename}"):
                            st.session_state['current_doc'] = filename
                            st.session_state['current_doc_title'] = title
                    else:
                        st.warning(f"Document not found: {filename}")
                except Exception as e:
                    st.error(f"Error loading {filename}: {str(e)}")

    st.divider()

    # Display selected document
    if 'current_doc' in st.session_state:
        doc_file = st.session_state['current_doc']
        doc_title = st.session_state.get('current_doc_title', doc_file)

        st.markdown(f"### 📖 {doc_title}")

        # Back button
        if st.button("⬅️ Back to Documentation List"):
            del st.session_state['current_doc']
            del st.session_state['current_doc_title']
            st.rerun()

        # Read and display full document
        doc_path = f"/app/{doc_file}"
        try:
            if os.path.exists(doc_path):
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Display markdown content
                st.markdown(content)

                # Download button
                st.download_button(
                    label=f"⬇️ Download {doc_file}",
                    data=content,
                    file_name=doc_file,
                    mime="text/markdown"
                )
            else:
                st.error(f"Document not found: {doc_file}")
        except Exception as e:
            st.error(f"Error reading document: {str(e)}")
    else:
        # Show quick links when no document is selected
        st.markdown("""
        ### Quick Links

        - **Getting Started**: View README.md for quickstart guide
        - **Troubleshooting**: TROUBLESHOOTING_GUIDE.md - Complete problem-solving guide
        - **Context-Aware Agent**: CONTEXT_AWARE_AGENT_GUIDE.md - Natural language understanding
        - **Email Setup**: SMTP_CONFIGURATION_GUIDE.md - Configure real email sending
        - **LINE Messaging**: LINE_SETUP_GUIDE.md - Smart group/personal messaging with auto-detection
        - **Database**: See DATABASE_SCHEMA.md for schema details
        - **Testing**: Check TEST_RESULTS.md for 100% test coverage
        - **Deployment**: Follow DEPLOYMENT_GUIDE.md for production setup
        - **Changes**: Review CHANGELOG.md for version history
        - **Overview**: Read PROJECT_SUMMARY.md for executive summary

        ### External Documentation

        - [LiteLLM Docs](https://docs.litellm.ai/)
        - [FastAPI Docs](https://fastapi.tiangolo.com/)
        - [Streamlit Docs](https://docs.streamlit.io/)
        - [Qdrant Docs](https://qdrant.tech/documentation/)
        - [PostgreSQL Docs](https://www.postgresql.org/docs/)
        """)

        # Tools reference
        st.divider()
        st.subheader("🛠️ Available Tools (28 Total)")

        tool_categories = {
            "Data Analysis & Processing (3)": [
                "analyze_data - Statistical analysis",
                "process_csv - CSV file processing",
                "generate_chart - Data visualization"
            ],
            "Search & Retrieval (3)": [
                "semantic_search - AI-driven search",
                "web_search - Web search integration",
                "find_similar_documents - Document similarity"
            ],
            "Content Generation (3)": [
                "summarize_document - Text summarization",
                "translate_text - Multi-language translation",
                "generate_report - Report generation"
            ],
            "Security & Compliance (3)": [
                "check_permissions - Access control",
                "audit_log - Audit logging",
                "scan_sensitive_data - PII detection"
            ],
            "Business Process (3)": [
                "create_task - Task management",
                "send_notification - Notifications",
                "schedule_meeting - Meeting scheduling"
            ],
            "System Integration (3)": [
                "call_api - External API calls",
                "execute_sql - SQL queries",
                "run_script - Script execution"
            ],
            "Communication (2)": [
                "send_email - Email sending",
                "create_slack_message - Slack integration"
            ],
            "File Management (3)": [
                "upload_file - File uploads",
                "download_file - File downloads",
                "list_files - File listing"
            ],
            "Calculation (2)": [
                "calculate_metrics - Business KPIs",
                "financial_calculator - ROI/NPV/IRR"
            ]
        }

        for category, tools in tool_categories.items():
            with st.expander(f"📂 {category}"):
                for tool in tools:
                    st.markdown(f"- `{tool}`")

with tab7:
    st.header(get_text("about_header", lang))

    st.markdown(f"""
    ### {get_text("about_title", lang)}

    {get_text("about_intro", lang)}

    #### {get_text("core_features", lang)}
    - 🔄 {get_text("feature_hybrid", lang)}
    - 🤖 {get_text("feature_agent", lang)}
    - 📊 {get_text("feature_monitor", lang)}
    - 🔒 {get_text("feature_security", lang)}

    #### {get_text("tech_stack", lang)}
    - {get_text("frontend", lang)}
    - {get_text("backend", lang)}
    - {get_text("llm_gateway", lang)}
    - {get_text("local_inference", lang)}
    - {get_text("database", lang)}
    - {get_text("monitoring", lang)}

    #### {get_text("supported_models", lang)}
    - {get_text("models_openai", lang)}
    - {get_text("models_anthropic", lang)}
    - {get_text("models_local", lang)}
    - {get_text("models_others", lang)}

    #### {get_text("usage_tips", lang)}
    1. {get_text("tip_1", lang)}
    2. {get_text("tip_2", lang)}
    3. {get_text("tip_3", lang)}

    #### {get_text("version_info", lang)}
    - {get_text("version", lang)}
    - {get_text("update_date", lang)}
    - {get_text("license", lang)}
    """)

    st.divider()

    st.markdown(f"""
    ### {get_text("tech_support", lang)}

    {get_text("support_intro", lang)}
    - {get_text("support_docs", lang)}
    - {get_text("support_troubleshoot", lang)}
    - {get_text("support_logs", lang)}
    """)
