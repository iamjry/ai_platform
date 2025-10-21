# AI Platform - Complete Replication & Improvement Guide

**Version:** 2.1.0
**Last Updated:** 2025-10-17
**Purpose:** Comprehensive guide to duplicate and enhance this AI Platform in a new environment

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Summary](#architecture-summary)
3. [Prerequisites](#prerequisites)
4. [Step-by-Step Replication](#step-by-step-replication)
5. [Configuration Details](#configuration-details)
6. [Improvement Opportunities](#improvement-opportunities)
7. [Customization Guide](#customization-guide)
8. [Production Deployment](#production-deployment)
9. [Troubleshooting](#troubleshooting)

---

## 📊 Project Overview

### What Is This Project?

An **enterprise-grade AI agent platform** featuring:
- **28 intelligent tools** across 14 categories
- **Multi-stage conversational AI** with context memory management
- **Multi-model LLM support** (GPT-4, Claude, local Qwen)
- **Microservices architecture** with Docker Compose
- **Full monitoring stack** (Prometheus + Grafana)
- **Production-ready** with GPU support for RHEL 9.4

### Key Capabilities

✅ **Conversational AI**: Agents can ask follow-up questions to gather missing information
✅ **Tool Execution**: 28 tools for data analysis, search, email, tasks, security, etc.
✅ **Multi-Platform**: Runs on macOS (dev) and RHEL 9.4 (production with GPU)
✅ **Context Management**: Intelligent context window handling per model
✅ **Web UI**: Streamlit-based interface with real-time status
✅ **API Access**: RESTful APIs for all functionality

### Technology Stack

**Backend:**
- FastAPI (Python 3.11+)
- PostgreSQL 16 (database)
- Redis 7.2 (caching)
- Qdrant 1.9.0 (vector database)
- RabbitMQ 3.12 (message queue)

**AI/ML:**
- LiteLLM (multi-model proxy)
- Ollama (local LLM inference)
- OpenAI GPT models
- Anthropic Claude models

**Frontend:**
- Streamlit (Web UI)
- Python-based interactive interface

**Infrastructure:**
- Docker + Docker Compose
- Prometheus (metrics)
- Grafana (dashboards)
- NVIDIA GPU support (H100L)

---

## 🏗️ Architecture Summary

### Microservices Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Web UI (8501)                        │
│                   Streamlit Frontend Interface               │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                   Agent Service (8002)                       │
│            Task Orchestration & Conversation Management      │
└────────────┬────────────────────────────────┬────────────────┘
             │                                 │
             ├─────────────────┐              │
             │                 │              │
┌────────────┴────────┐  ┌────┴───────────┐ │
│  MCP Server (8001)  │  │ LiteLLM (4000) │ │
│   28 Tools          │  │  Multi-Model   │ │
│   Execution         │  │  LLM Proxy     │ │
└──┬──────────────────┘  └────┬───────────┘ │
   │                          │             │
   │                          │             │
┌──┴───────┐  ┌──────┐  ┌────┴──────┐  ┌──┴────────┐
│PostgreSQL│  │Qdrant│  │  Ollama   │  │ RabbitMQ  │
│  (5433)  │  │(6333)│  │  (11434)  │  │  (5672)   │
└──────────┘  └──────┘  └───────────┘  └───────────┘
                             │
                        ┌────┴────┐
                        │  Redis  │
                        │ (6380)  │
                        └─────────┘
```

### Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| Web UI | 8501 | User interface |
| Agent Service | 8002 | Task orchestration |
| MCP Server | 8001 | Tool execution |
| LiteLLM | 4000 | LLM proxy |
| PostgreSQL | 5433 | Primary database |
| Redis | 6380 | Cache |
| Qdrant | 6333/6334 | Vector DB |
| Ollama | 11434 | Local LLM |
| RabbitMQ | 5672/15672 | Message queue |
| Prometheus | 9090 | Metrics |
| Grafana | 3000 | Dashboards |

---

## ✅ Prerequisites

### Development Environment (macOS)

```bash
# Required Software
- macOS 12.0+ (Monterey or later)
- Docker Desktop 4.20+ for Mac
- 8GB+ RAM (16GB recommended)
- 20GB+ free disk space

# Install Docker Desktop
https://www.docker.com/products/docker-desktop/

# Verify Installation
docker --version
docker compose version
```

### Production Environment (RHEL 9.4)

```bash
# System Requirements
- Red Hat Enterprise Linux 9.4 (Plow) x86_64
- 2x NVIDIA H100L 94GB GPUs (or similar)
- 32GB+ RAM (64GB recommended)
- 100GB+ SSD storage
- NVIDIA Driver 535+
- CUDA Toolkit 12.0+

# Install Docker
sudo dnf install -y docker-ce docker-ce-cli containerd.io

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.repo | \
  sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo
sudo dnf install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### API Keys (Required)

You'll need API keys for external LLM providers:

- **OpenAI API Key**: https://platform.openai.com/api-keys
- **Anthropic API Key**: https://console.anthropic.com/settings/keys

*(Optional: Local models work without API keys)*

---

## 🚀 Step-by-Step Replication

### Step 1: Clone/Copy Project Structure

```bash
# Create new project directory
mkdir -p /path/to/new/ai_platform
cd /path/to/new/ai_platform

# Copy entire project structure
# (Or download/clone from repository)
```

### Required Directory Structure

```
ai_platform/
├── services/
│   ├── agent-service/
│   │   ├── Dockerfile
│   │   ├── main.py                    # 600+ lines
│   │   └── requirements.txt
│   ├── mcp-server/
│   │   ├── Dockerfile
│   │   ├── main.py                    # 1,069 lines - 28 tools
│   │   ├── schema.sql                 # Database schema
│   │   ├── seed.sql                   # Sample data
│   │   └── requirements.txt
│   └── web-ui/
│       ├── Dockerfile
│       ├── app.py                     # 670+ lines
│       ├── i18n.py                    # Internationalization
│       └── requirements.txt
├── config/
│   ├── litellm-config.yaml
│   ├── prometheus.yml
│   └── grafana/
│       ├── dashboards/
│       └── datasources/
├── scripts/
│   └── init-db.sh                     # 400+ lines
├── docker-compose.yml                 # Base configuration
├── docker-compose.gpu.yml             # GPU configuration
├── deploy.sh                          # Development deployment
├── deploy-macos.sh                    # macOS deployment
├── deploy-rhel-production.sh          # Production deployment
├── .env.example                       # Environment template
└── documentation/
    ├── README.md
    ├── DEPLOYMENT_GUIDE.md
    ├── MULTI_STAGE_CONVERSATION_GUIDE.md
    ├── TOOLS_REFERENCE.md
    └── ... (other docs)
```

### Step 2: Set Up Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env  # or vim, code, etc.
```

**Minimum Required Configuration:**

```bash
# API Keys
OPENAI_API_KEY=sk-proj-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Database (auto-generate secure passwords)
POSTGRES_USER=admin
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
POSTGRES_DB=ai_platform

# Redis
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# RabbitMQ
RABBITMQ_DEFAULT_USER=admin
RABBITMQ_DEFAULT_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Environment
ENVIRONMENT=development  # or production
LOG_LEVEL=info
```

### Step 3: Deploy the Platform

**For macOS Development:**

```bash
chmod +x deploy-macos.sh
./deploy-macos.sh
```

**For Linux Development:**

```bash
chmod +x deploy.sh
./deploy.sh
```

**For RHEL Production with GPU:**

```bash
chmod +x deploy-rhel-production.sh
sudo ./deploy-rhel-production.sh
```

### Step 4: Initialize Database

```bash
# Run database initialization
chmod +x scripts/init-db.sh
./scripts/init-db.sh init

# Verify initialization
./scripts/init-db.sh verify
```

### Step 5: Verify Deployment

```bash
# Check all services are running
docker compose ps

# Should show 11 services as "healthy" or "running":
# - postgres
# - redis
# - qdrant
# - rabbitmq
# - ollama
# - litellm
# - mcp-server
# - agent-service
# - web-ui
# - prometheus
# - grafana

# Test health endpoints
curl http://localhost:8001/health  # MCP Server
curl http://localhost:8002/health  # Agent Service
curl http://localhost:4000/health  # LiteLLM
```

### Step 6: Access the Platform

```bash
# Open Web UI
open http://localhost:8501

# Or for remote server
open http://your-server-ip:8501
```

---

## ⚙️ Configuration Details

### LiteLLM Configuration

**File:** `config/litellm-config.yaml`

```yaml
model_list:
  # OpenAI Models
  - model_name: gpt-4
    litellm_params:
      model: openai/gpt-4
      api_key: os.environ/OPENAI_API_KEY

  - model_name: gpt-3.5-turbo
    litellm_params:
      model: openai/gpt-3.5-turbo
      api_key: os.environ/OPENAI_API_KEY

  # Anthropic Models
  - model_name: claude-3-opus
    litellm_params:
      model: claude-3-opus-20240229
      api_key: os.environ/ANTHROPIC_API_KEY

  - model_name: claude-3-sonnet
    litellm_params:
      model: claude-3-5-sonnet-20240620
      api_key: os.environ/ANTHROPIC_API_KEY

  # Local Ollama Models
  - model_name: qwen2.5
    litellm_params:
      model: ollama/qwen2.5:0.5b
      api_base: http://ollama:11434

litellm_settings:
  drop_params: true
  set_verbose: true
  cache: true
  cache_params:
    type: redis
    host: redis
    port: 6379
    password: os.environ/REDIS_PASSWORD

general_settings:
  master_key: sk-1234
  database_url: os.environ/DATABASE_URL
  ui_access_mode: admin
  store_model_in_db: true
```

### Docker Compose Configuration

**Base File:** `docker-compose.yml`

Key sections:
- Network configuration
- Volume mounts
- Service dependencies
- Health checks
- Port mappings

**GPU File:** `docker-compose.gpu.yml`

Additional GPU-specific config:
- NVIDIA device allocation
- Resource limits
- Production tuning

### Database Schema

**File:** `services/mcp-server/schema.sql`

Tables:
- `users` - User accounts with roles
- `documents` - Knowledge base with full-text search
- `tasks` - Task management
- `audit_logs` - Security audit trail

---

## 💡 Improvement Opportunities

### 1. Add More Tools

**Location:** `services/mcp-server/main.py`

**How to Add a New Tool:**

```python
@app.post("/tools/your_new_tool")
async def your_new_tool(request: YourToolRequest):
    """
    Your tool description
    """
    try:
        # Your tool logic here
        result = {
            "status": "success",
            "data": {}
        }
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add to tools list
@app.get("/tools/list")
async def list_tools():
    tools = {
        "tools": [
            # ... existing tools ...
            {
                "name": "your_new_tool",
                "description": "Tool description",
                "category": "integration",
                "parameters": {
                    "param1": "string",
                    "param2": "integer"
                }
            }
        ]
    }
    return tools
```

**Suggested New Tools:**
- Jira integration
- GitHub operations
- Google Calendar integration
- Stripe payment processing
- Twilio SMS sending
- AWS S3 operations
- Document OCR
- Image generation (DALL-E, Stable Diffusion)
- Code execution sandbox
- Web scraping

### 2. Enhanced Authentication

**Current State:** Basic setup, no JWT

**Improvements:**

```python
# Add JWT authentication
# File: services/agent-service/auth.py

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# Use in endpoints
@app.post("/agent/execute")
async def execute_agent(request: AgentRequest, user=Depends(verify_token)):
    # user contains decoded token data
    pass
```

**Add Features:**
- User registration and login
- Role-based access control (RBAC)
- API key management
- OAuth2 integration (Google, GitHub)
- Session management
- Rate limiting per user

### 3. Advanced Vector Search

**Current State:** Basic Qdrant integration

**Improvements:**

```python
# Enhanced embeddings
from sentence_transformers import SentenceTransformer

# Use better embedding models
model = SentenceTransformer('all-MiniLM-L6-v2')  # or 'all-mpnet-base-v2'

# Add semantic caching
# Cache expensive LLM calls based on semantic similarity

# Multi-vector search
# Search across documents, code, images simultaneously

# Hybrid search
# Combine vector search with keyword search
```

**New Features:**
- Document chunking strategies
- Multi-modal embeddings (text + images)
- Semantic caching for LLM responses
- Retrieval-Augmented Generation (RAG) pipelines
- Collection management UI

### 4. Real-Time Features

**Add WebSocket Support:**

```python
# services/agent-service/main.py
from fastapi import WebSocket

@app.websocket("/ws/agent")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        # Stream agent responses in real-time
        async for chunk in agent_stream(data):
            await websocket.send_text(chunk)
```

**Use Cases:**
- Streaming LLM responses
- Real-time collaboration
- Live system monitoring
- Chat notifications
- Progress updates for long-running tasks

### 5. Advanced Monitoring

**Current:** Basic Prometheus + Grafana

**Add:**

```yaml
# docker-compose.monitoring.yml

services:
  # Distributed tracing
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # UI
      - "6831:6831/udp"  # Jaeger agent

  # Log aggregation
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"

  # APM
  elastic-apm:
    image: docker.elastic.co/apm/apm-server:8.0.0
```

**Metrics to Add:**
- LLM token usage per user
- Tool execution success rates
- Response time percentiles (p50, p95, p99)
- Error rate by endpoint
- Cost tracking (API usage)
- User activity patterns

### 6. Multi-Tenancy

**Add Organization Support:**

```python
# Database schema addition
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    api_key VARCHAR(255) UNIQUE,
    tier VARCHAR(50),  -- free, pro, enterprise
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE users ADD COLUMN organization_id INTEGER REFERENCES organizations(id);

# Middleware for tenant isolation
@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    # Extract org from API key
    api_key = request.headers.get("X-API-Key")
    org = get_organization_by_api_key(api_key)
    request.state.organization = org
    response = await call_next(request)
    return response
```

### 7. Enhanced Web UI

**Current:** Streamlit-based

**Improvements:**

```python
# Add features to services/web-ui/app.py

# 1. Conversation Export
def export_conversation(messages, format='json'):
    if format == 'json':
        return json.dumps(messages, indent=2)
    elif format == 'markdown':
        return "\n\n".join([f"**{m['role']}:** {m['content']}" for m in messages])
    elif format == 'pdf':
        # Generate PDF
        pass

# 2. Tool Usage Analytics
def show_tool_analytics():
    # Query tool usage from database
    # Display charts and statistics
    pass

# 3. Prompt Templates
def load_prompt_templates():
    templates = {
        "Email Draft": "Draft an email to {recipient} about {topic}...",
        "Data Analysis": "Analyze the following data and provide insights...",
        # ...
    }
    return templates

# 4. Conversation Branching
# Allow users to branch conversations and explore alternatives

# 5. Cost Calculator
def calculate_cost(tokens_used, model):
    rates = {
        "gpt-4": 0.03 / 1000,
        "claude-3-opus": 0.015 / 1000,
        # ...
    }
    return tokens_used * rates.get(model, 0)
```

### 8. CI/CD Pipeline

**Add GitHub Actions:**

```yaml
# .github/workflows/deploy.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          docker compose -f docker-compose.test.yml up --abort-on-container-exit

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build images
        run: docker compose build

      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker compose push

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.PROD_HOST }}
          username: ${{ secrets.PROD_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/ai_platform
            git pull
            docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
```

### 9. Plugin System

**Allow Custom Tools:**

```python
# services/mcp-server/plugin_loader.py

import importlib
import os
from pathlib import Path

class PluginLoader:
    def __init__(self, plugin_dir="plugins"):
        self.plugin_dir = Path(plugin_dir)
        self.plugins = {}

    def load_plugins(self):
        """Load all plugins from plugin directory"""
        for file in self.plugin_dir.glob("*.py"):
            if file.name.startswith("_"):
                continue

            module_name = file.stem
            spec = importlib.util.spec_from_file_location(module_name, file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Register plugin tools
            if hasattr(module, "register_tool"):
                tool = module.register_tool()
                self.plugins[tool["name"]] = tool

    def get_plugin(self, name):
        return self.plugins.get(name)

# Plugin example: plugins/custom_tool.py
def register_tool():
    return {
        "name": "my_custom_tool",
        "description": "Custom tool description",
        "handler": handle_tool,
        "schema": {...}
    }

def handle_tool(params):
    # Tool logic
    return {"result": "success"}
```

### 10. Enhanced Security

**Add Security Features:**

```python
# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/agent/execute")
@limiter.limit("10/minute")
async def execute_agent(request: Request, agent_request: AgentRequest):
    pass

# Input sanitization
from bleach import clean

def sanitize_input(text):
    return clean(text, tags=[], strip=True)

# SQL injection prevention (already using parameterized queries)
# XSS prevention
# CSRF protection
# API key rotation
# Audit logging
```

---

## 🎨 Customization Guide

### Change Branding

**1. Update Web UI:**

```python
# services/web-ui/app.py

# Change title
st.set_page_config(
    page_title="Your Company AI Platform",
    page_icon="🏢",
    layout="wide"
)

# Update header
st.markdown('<p class="main-header">Your Company AI Assistant</p>')

# Add logo
st.sidebar.image("logo.png", width=200)
```

**2. Update Colors:**

```python
# Custom CSS
st.markdown("""
<style>
    .main-header {
        color: #YOUR_COLOR;
    }
    /* Add more custom styles */
</style>
""", unsafe_allow_html=True)
```

### Add New Languages

**File:** `services/web-ui/i18n.py`

```python
LANGUAGES = {
    "en": "English",
    "zh-TW": "繁體中文",
    "zh-CN": "简体中文",  # Add Simplified Chinese
    "ja": "日本語",        # Add Japanese
    "es": "Español",       # Add Spanish
    "fr": "Français",      # Add French
}

TRANSLATIONS = {
    "en": {
        "page_title": "AI Platform",
        # ... all translations
    },
    "es": {
        "page_title": "Plataforma de IA",
        # ... Spanish translations
    }
}
```

### Customize Models

**Add More Models:**

```yaml
# config/litellm-config.yaml

model_list:
  # Add Google PaLM
  - model_name: palm-2
    litellm_params:
      model: palm/chat-bison-001
      api_key: os.environ/GOOGLE_API_KEY

  # Add Azure OpenAI
  - model_name: gpt-4-azure
    litellm_params:
      model: azure/gpt-4
      api_key: os.environ/AZURE_API_KEY
      api_base: https://your-resource.openai.azure.com/

  # Add Custom Ollama Models
  - model_name: mistral
    litellm_params:
      model: ollama/mistral:latest
      api_base: http://ollama:11434
```

---

## 🚀 Production Deployment

### Pre-Production Checklist

- [ ] Change all default passwords in `.env`
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure HTTPS/SSL (use reverse proxy)
- [ ] Set up automated backups (configured in RHEL script)
- [ ] Configure log rotation
- [ ] Set up monitoring alerts (Grafana)
- [ ] Review and set resource limits
- [ ] Enable rate limiting
- [ ] Configure CORS properly
- [ ] Set up reverse proxy (nginx/HAProxy)
- [ ] Verify GPU drivers (RHEL)
- [ ] Configure firewall rules
- [ ] Test disaster recovery
- [ ] Load testing
- [ ] Security audit

### Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/ai-platform

upstream web_ui {
    server localhost:8501;
}

upstream agent_service {
    server localhost:8002;
}

upstream mcp_server {
    server localhost:8001;
}

server {
    listen 80;
    server_name your-domain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Web UI
    location / {
        proxy_pass http://web_ui;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # API endpoints
    location /api/ {
        proxy_pass http://agent_service/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /tools/ {
        proxy_pass http://mcp_server/tools/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### SSL Certificate

```bash
# Install certbot
sudo dnf install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Backup Strategy

```bash
# Automated backups (already configured in RHEL script)
# /usr/local/bin/ai-platform-backup.sh runs daily at 2 AM

# Manual backup
./scripts/init-db.sh backup

# Backup to S3 (optional)
#!/bin/bash
BACKUP_FILE="/opt/ai_platform/backups/database/backup_$(date +%Y%m%d).sql.gz"
aws s3 cp $BACKUP_FILE s3://your-bucket/backups/

# Retention: Keep 30 days
find /opt/ai_platform/backups/database/ -name "backup_*.sql.gz" -mtime +30 -delete
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
# Find process
lsof -i :8501

# Kill process
kill -9 [PID]

# Or change port in docker-compose.yml
```

#### 2. GPU Not Detected

```bash
# Verify GPU
nvidia-smi

# Check Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubi9 nvidia-smi

# Reconfigure
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

#### 3. Service Won't Start

```bash
# Check logs
docker compose logs [service-name]

# Restart service
docker compose restart [service-name]

# Force rebuild
docker compose up -d --build --force-recreate [service-name]
```

#### 4. Database Connection Errors

```bash
# Check PostgreSQL
docker compose ps postgres

# Reinitialize
./scripts/init-db.sh reset
./scripts/init-db.sh init
```

#### 5. Out of Memory

```bash
# Check usage
docker stats

# Increase Docker memory (Docker Desktop)
# Settings → Resources → Memory

# Stop non-essential services
docker compose stop grafana prometheus
```

### Debug Mode

```bash
# Enable debug logging
# Edit .env
LOG_LEVEL=debug
DEBUG=true

# Restart services
docker compose restart
```

---

## 📚 Additional Resources

### Documentation Files

All documentation is in the project root:

- `README.md` - Overview and quick start
- `DEPLOYMENT_GUIDE.md` - Complete deployment instructions
- `DATABASE_SCHEMA.md` - Database documentation
- `MULTI_STAGE_CONVERSATION_GUIDE.md` - Conversation feature guide
- `TOOLS_REFERENCE.md` - All 28 tools documented
- `TEST_RESULTS.md` - Test coverage report
- `CHANGELOG.md` - Version history
- `PROJECT_SUMMARY.md` - Executive summary
- `TROUBLESHOOTING_GUIDE.md` - Problem solving

### External References

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Prometheus Documentation](https://prometheus.io/docs/)

---

## 🎯 Quick Start Command Summary

```bash
# Clone/Copy Project
cp -r /source/ai_platform /destination/ai_platform
cd /destination/ai_platform

# Configure
cp .env.example .env
# Edit .env with your settings

# Deploy (choose one)
./deploy-macos.sh              # macOS development
./deploy.sh                    # Linux development
sudo ./deploy-rhel-production.sh  # RHEL production

# Initialize Database
./scripts/init-db.sh init

# Verify
docker compose ps
curl http://localhost:8001/health
curl http://localhost:8002/health

# Access
open http://localhost:8501

# Monitor
open http://localhost:3000  # Grafana (admin/admin)
open http://localhost:9090  # Prometheus
```

---

## ✅ Success Criteria

Your replication is successful when:

- ✅ All 11 services are running (docker compose ps)
- ✅ Health endpoints respond (curl tests pass)
- ✅ Web UI is accessible at port 8501
- ✅ Can execute test: `python3 test_tools.py` (29/29 pass)
- ✅ Can send chat message and get response
- ✅ Can execute agent task (e.g., "send email")
- ✅ Multi-stage conversation works
- ✅ Context usage shows in sidebar
- ✅ Grafana dashboards load
- ✅ Database contains sample data

---

## 📝 Notes

- **Security**: Change all default passwords before production
- **Backup**: Set up automated backups immediately
- **Monitoring**: Configure alerts in Grafana
- **Scaling**: Use docker-compose.gpu.yml for production
- **Costs**: Monitor API usage to control costs
- **Updates**: Keep Docker images and dependencies updated

---

**Project Version:** 2.1.0
**Last Updated:** 2025-10-17
**Status:** ✅ Production Ready
**Maintained By:** AI Development Team

For questions or issues, refer to the documentation files or create an issue in the project repository.
