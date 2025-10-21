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
        ["qwen2.5", "gpt-3.5-turbo", "gpt-4", "claude-3-sonnet"],
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
    - OpenAI GPT系列 (需要API金鑰)
    - Anthropic Claude系列 (需要API金鑰)
    - 本地Qwen2.5模型 (通過Ollama運行)
    - 其他開源模型

    #### 使用建議
    1. 首次使用建議選擇 qwen2.5 快速測試 (本地模型,無需API金鑰)
    2. 複雜任務可選擇 gpt-4 或 claude-3-opus (需要有效的API金鑰)
    3. 注重隱私建議使用本地 qwen2.5 模型
    
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
