# AI Platform - Enterprise AI Agent System

A comprehensive enterprise-grade AI platform with multi-model support, intelligent agents, and powerful tool integration. Built with microservices architecture using Docker Compose, FastAPI, and modern AI capabilities.

[![Test Status](https://img.shields.io/badge/tests-29%2F29%20passing-success)](./TEST_RESULTS.md)
[![Database](https://img.shields.io/badge/database-PostgreSQL-blue)](./DATABASE_SCHEMA.md)
[![License](https://img.shields.io/badge/license-MIT-green)]()

## 🚀 Features

### Core Capabilities
- **28 Intelligent Tools** across 9 categories (data analysis, search, content generation, security, etc.)
- **Multi-Model Support** - OpenAI GPT, Anthropic Claude, Local Qwen2.5
- **Enterprise Security** - Authentication, audit logging, sensitive data scanning
- **Full-Text Search** - PostgreSQL-powered document search with JSONB metadata
- **Real-time Monitoring** - Prometheus metrics + Grafana dashboards
- **Scalable Architecture** - Docker-based microservices with Redis caching

### Tool Categories
1. **Data Analysis & Processing** (3 tools) - Statistical analysis, CSV processing, chart generation
2. **Search & Retrieval** (3 tools) - Semantic search, web search, document similarity
3. **Content Generation** (3 tools) - Reports, summaries, translations
4. **Security & Compliance** (3 tools) - Permission checks, audit logs, PII scanning
5. **Business Process** (3 tools) - Task management, notifications, meeting scheduling
6. **System Integration** (3 tools) - API calls, SQL execution, script running
7. **Communication** (2 tools) - Email, Slack integration
8. **File Management** (3 tools) - Upload, download, file organization
9. **Calculation** (2 tools) - Business metrics, financial calculations (ROI, NPV, IRR)

## 📋 Prerequisites

- **Docker** (≥ 20.10) & **Docker Compose** (≥ 2.0)
- **Python 3.12+** (for local development)
- **8GB RAM** minimum (16GB recommended)
- **10GB disk space**

## 🔧 Quick Start

### 1. Clone and Configure

```bash
git clone <repository-url>
cd ai_platform

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### 2. Deploy the Platform

**Option A: Automated Deployment (Recommended)**
```bash
# For macOS/Linux
./deploy.sh

# For macOS with Ollama
./deploy-macos.sh
```

**Option B: Manual Deployment**
```bash
# Start all services
docker compose up -d

# Initialize database
docker compose exec -T postgres psql -U admin -d ai_platform < services/mcp-server/schema.sql
docker compose exec -T postgres psql -U admin -d ai_platform < services/mcp-server/seed.sql

# Check service health
docker compose ps
```

### 3. Access the Platform

| Service | URL | Credentials |
|---------|-----|-------------|
| **Web UI** | http://localhost:8501 | - |
| **Agent Service** | http://localhost:8000 | - |
| **MCP Server** | http://localhost:8001 | - |
| **LiteLLM Proxy** | http://localhost:4000 | API Key: `sk-1234` |
| **Grafana** | http://localhost:3000 | admin / admin |
| **Prometheus** | http://localhost:9090 | - |
| **Qdrant** | http://localhost:6333 | - |

### 4. Verify Installation

```bash
# Run comprehensive tests
python3 test_tools.py

# Check service health
curl http://localhost:8001/health

# View available tools
curl http://localhost:8001/tools/list | python3 -m json.tool
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Web UI (Streamlit)                  │
│                     http://localhost:8501                   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Agent Service (FastAPI)                  │
│              Orchestrates AI tasks and workflows            │
│                     http://localhost:8000                   │
└──────┬──────────────────────────────────────────────┬───────┘
       │                                              │
┌──────▼──────────────────┐              ┌───────────▼─────────┐
│  MCP Server (FastAPI)   │              │  LiteLLM Proxy      │
│  28 Tools & Resources   │              │  Multi-Model Router │
│  http://localhost:8001  │              │  http://localhost:4000│
└──┬──────────┬──────────┬┘              └─────────┬───────────┘
   │          │          │                         │
   │          │          │                         │
┌──▼──┐  ┌───▼────┐  ┌──▼──────┐          ┌──────▼──────┐
│ PG  │  │ Redis  │  │ Qdrant  │          │   Ollama    │
│ SQL │  │ Cache  │  │ Vector  │          │ Local LLMs  │
└─────┘  └────────┘  └─────────┘          └─────────────┘
```

### Services

| Service | Purpose | Port |
|---------|---------|------|
| **web-ui** | Streamlit frontend with multi-language support | 8501 |
| **agent-service** | Task orchestration and LLM integration | 8000 |
| **mcp-server** | Tool execution and resource management | 8001 |
| **litellm** | Multi-model LLM proxy and router | 4000 |
| **postgres** | Primary database (users, documents, tasks, audit) | 5432 |
| **redis** | Caching and session management | 6379 |
| **qdrant** | Vector database for semantic search | 6333 |
| **ollama** | Local LLM inference (Qwen2.5) | 11434 |
| **prometheus** | Metrics collection and monitoring | 9090 |
| **grafana** | Metrics visualization and dashboards | 3000 |

## 📊 Database Schema

The platform uses PostgreSQL with a comprehensive schema:

### Tables
- **users** (5 sample users) - User accounts and roles
- **documents** (10 sample documents) - Knowledge base with full-text search
- **tasks** (5 sample tasks) - Task management system
- **audit_logs** (10 sample logs) - Complete audit trail

### Key Features
- Full-text search with GIN indexes
- JSONB metadata for flexible properties
- Array-based tagging system
- Automatic timestamp triggers
- IP tracking for security

📖 [View Complete Database Documentation](./DATABASE_SCHEMA.md)

## 🔐 Environment Configuration

### Required Variables

```bash
# API Keys (add your own)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Database Configuration
POSTGRES_USER=admin
POSTGRES_PASSWORD=password
POSTGRES_DB=ai_platform

# Redis Configuration
REDIS_PASSWORD=password

# LiteLLM Configuration
LITELLM_API_KEY=sk-1234
LITELLM_MASTER_KEY=sk-master-1234

# Service URLs (default Docker network)
AGENT_SERVICE_URL=http://agent-service:8000
MCP_SERVER_URL=http://mcp-server:8001
LITELLM_URL=http://litellm:4000
```

📖 [View Complete Environment Template](./.env.example)

## 🛠️ Development

### Project Structure

```
ai_platform/
├── services/
│   ├── web-ui/              # Streamlit frontend
│   │   ├── app.py
│   │   ├── i18n.py          # Multi-language support
│   │   └── requirements.txt
│   ├── agent-service/       # Agent orchestration
│   │   ├── main.py
│   │   └── requirements.txt
│   └── mcp-server/          # Tool server
│       ├── main.py          # 28 tool implementations
│       ├── schema.sql       # Database schema
│       ├── seed.sql         # Sample data
│       └── requirements.txt
├── config/
│   ├── grafana/            # Grafana dashboards
│   ├── litellm/            # LiteLLM config
│   └── prometheus/         # Prometheus config
├── scripts/
│   └── init-db.sh          # Database initialization
├── docker-compose.yml       # Service orchestration
├── test_tools.py           # Comprehensive test suite
└── README.md               # This file
```

### Running Tests

```bash
# Install test dependencies
pip3 install requests

# Run all tests
python3 test_tools.py

# Test specific endpoint
curl -X POST http://localhost:8001/tools/analyze_data \
  -H 'Content-Type: application/json' \
  -d '{
    "data_source": "sales_data",
    "analysis_type": "descriptive",
    "options": {}
  }'
```

### Adding New Tools

1. Add Pydantic model in `services/mcp-server/main.py`:
```python
class YourToolRequest(BaseModel):
    param1: str
    param2: int
```

2. Implement endpoint:
```python
@app.post("/tools/your_tool")
async def your_tool(request: YourToolRequest):
    # Implementation
    return {"result": "data"}
```

3. Register in tools list (line ~231)
4. Add test in `test_tools.py`
5. Update documentation

## 📈 Monitoring

### Grafana Dashboards

Access Grafana at http://localhost:3000 (admin/admin)

**Available Dashboards:**
- Service Health & Uptime
- API Request Rates & Latency
- Database Performance
- Redis Cache Hit Rates
- LLM Token Usage & Costs

### Prometheus Metrics

Access Prometheus at http://localhost:9090

**Key Metrics:**
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency
- `db_query_duration_seconds` - Database query time
- `llm_tokens_used_total` - LLM token consumption

## 🚀 Deployment Scripts

### deploy.sh
Main deployment script for Linux/macOS
```bash
./deploy.sh              # Full deployment
./deploy.sh --rebuild    # Rebuild containers
./deploy.sh --clean      # Clean deployment
```

### deploy-macos.sh
macOS-specific deployment with Ollama support
```bash
./deploy-macos.sh        # Deploy with local Ollama
```

### maintenance_toolkit.sh
System maintenance and management
```bash
./maintenance_toolkit.sh  # Interactive menu
```

### Database Management

```bash
# Initialize/reset database
./scripts/init-db.sh

# Backup database
docker compose exec postgres pg_dump -U admin ai_platform > backup.sql

# Restore database
docker compose exec -T postgres psql -U admin -d ai_platform < backup.sql
```

## 🧪 Testing

### Test Results
- **Total Tools:** 28
- **Test Coverage:** 29/29 tests (100%)
- **Status:** ✅ All tests passing

📖 [View Detailed Test Results](./TEST_RESULTS.md)

### Running Tests

```bash
# Run all tests
python3 test_tools.py

# Expected output:
# Total Tests: 29
# Passed: 29 ✅
# Failed: 0 ❌
# Success Rate: 100.0%
```

## 🔒 Security

### Authentication
- API key authentication for LiteLLM
- Bearer token support for all endpoints
- Rate limiting (100 req/min per user)

### Audit Logging
- All API calls logged to `audit_logs` table
- IP address and user agent tracking
- Timestamp and action details

### Data Protection
- PII scanning tool for sensitive data detection
- SQL injection prevention (parameterized queries)
- CORS configuration for web security

## 🤖 Agent Tool Calling (NEW!)

### Natural Language Tool Execution

The agent can now automatically execute tools based on natural language commands! Simply describe what you want, and the agent will detect your intent and call the appropriate tool.

#### Supported Actions

**Email Sending:**
```bash
# Chinese
curl -X POST http://localhost:8002/agent/execute \
  -H 'Content-Type: application/json' \
  -d '{"task":"發送郵件給 john@example.com，主旨是測試郵件","model":"qwen2.5"}'

# English
curl -X POST http://localhost:8002/agent/execute \
  -H 'Content-Type: application/json' \
  -d '{"task":"send email to john@example.com with subject Test","model":"qwen2.5"}'

# Result: ✅ Email sent! ID: EMAIL-20251016083041
```

**Task Creation:**
```bash
curl -X POST http://localhost:8002/agent/execute \
  -H 'Content-Type: application/json' \
  -d '{"task":"創建任務：完成報告","model":"qwen2.5"}'

# Result: ✅ Task created! ID: TASK-20251016083111
```

**Knowledge Search:**
```bash
curl -X POST http://localhost:8002/agent/execute \
  -H 'Content-Type: application/json' \
  -d '{"task":"搜尋關於AI的文檔","model":"qwen2.5"}'

# Result: ✅ Search complete! Found X results
```

#### From Web UI (Easiest!)

1. Open http://localhost:8501
2. Click the **"🤖 Agent"** tab
3. Select model: **qwen2.5** (local, no API key needed)
4. Type natural command:
   - "發送郵件給 team@company.com 主旨是會議提醒"
   - "create task: Update documentation"
   - "search for product specifications"
5. Click **"Execute Task"**
6. See results with execution steps!

#### How It Works

**Two Modes:**
1. **Function Calling** (GPT-3.5/4, Claude-3): LLM automatically calls tools
2. **Fallback Mode** (Qwen2.5, local models): Keyword detection

**Supported Models:**
- ✅ **qwen2.5** - Local, works offline, no API key (RECOMMENDED for testing)
- ✅ **gpt-3.5-turbo** - Function calling support (requires API key)
- ✅ **gpt-4** - Advanced function calling (requires API key)
- ✅ **claude-3-sonnet** - Claude function calling (requires API key)

📖 [View Complete Agent Tool Integration Guide](./AGENT_TOOL_INTEGRATION_COMPLETE.md)

## 📝 API Examples

### Chat with AI
```bash
curl -X POST http://localhost:8002/agent/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "Analyze our Q3 sales performance",
    "model": "qwen2.5",
    "temperature": 0.7
  }'
```

### Execute Agent Task (Simple)
```bash
curl -X POST http://localhost:8002/agent/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "task": "Generate a financial report for Q3",
    "agent_type": "general",
    "model": "qwen2.5"
  }'
```

### Search Documents
```bash
curl -X POST http://localhost:8001/tools/search \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "API documentation",
    "collection": "documents",
    "limit": 5
  }'
```

### Calculate ROI
```bash
curl -X POST http://localhost:8001/tools/financial_calculator \
  -H 'Content-Type: application/json' \
  -d '{
    "operation": "roi",
    "values": {"gain": 15000, "cost": 10000}
  }'
```

## 🐛 Troubleshooting

### Service Won't Start
```bash
# Check logs
docker compose logs -f [service-name]

# Restart service
docker compose restart [service-name]

# Rebuild service
docker compose up -d --build [service-name]
```

### Database Connection Issues
```bash
# Check PostgreSQL status
docker compose exec postgres psql -U admin -d ai_platform -c "SELECT 1"

# Reinitialize database
docker compose exec -T postgres psql -U admin -d ai_platform < services/mcp-server/schema.sql
```

### Port Already in Use
```bash
# Find process using port
lsof -i :8501  # or any port

# Kill process
kill -9 [PID]
```

### Ollama/Local Model Issues
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Pull Qwen2.5 model
ollama pull qwen2.5:latest
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [README.md](./README.md) | This file - project overview |
| [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) | Complete database documentation |
| [TEST_RESULTS.md](./TEST_RESULTS.md) | Comprehensive test report |
| [.env.example](./.env.example) | Environment configuration template |

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and test (`python3 test_tools.py`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **LiteLLM** - Multi-model LLM proxy
- **FastAPI** - Modern Python web framework
- **Streamlit** - Interactive web applications
- **Qdrant** - Vector database
- **Ollama** - Local LLM inference

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation:** See docs/ directory
- **Email:** support@example.com

---

**Version:** 2.1.0 - Agent Tool Calling
**Last Updated:** 2025-10-16
**Status:** ✅ Production Ready
**Test Coverage:** 100% (29/29 tests passing)
**New Feature:** 🤖 Natural language tool execution!
