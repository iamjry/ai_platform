# Command History Log

This file tracks all commands executed during the development and maintenance of the AI Agents Platform.

## Session: 2025-10-21 - Initial Setup and Version Control

### Task: Fix qwen2.5:7b Timeout and Add Model Parameters

#### Build and Restart Services
```bash
# Rebuild web-ui and agent-service containers with new features
docker-compose up -d --build web-ui agent-service
```

#### Check Service Status
```bash
# Verify all services are healthy
docker-compose ps
```

### Task: Initialize Git Version Control

#### Check Git Status
```bash
# Check if repository is already initialized
git status
# Result: fatal: not a git repository (or any of the parent directories): .git
```

#### Initialize Git Repository
```bash
# Initialize git repository and configure user
git init
git config user.name "AI Platform Team"
git config user.email "your-email@gmail.com"
# Result: Initialized empty Git repository in /path/to/your/ai_platform/.git/
```

#### Stage All Files
```bash
# Add all files to staging area
git add .
```

#### Check Staged Files
```bash
# Verify what files are staged for commit
git status
# Result: 47 files staged for initial commit
```

#### Create Initial Commit
```bash
# Create comprehensive initial commit
git commit -m "$(cat <<'EOF'
Initial commit: AI Agents Platform v1.0.0

🎉 Complete enterprise AI platform with multi-model support

## Features
- 🔄 Multi-Model LLM Support (OpenAI, Anthropic, Google, Local)
- 🤖 Intelligent Agent System with 28 tools
- 📄 PDF & Document Analysis
- 🖼️ Vision Model Support (GPT-4o, Claude-3, Gemini)
- 💬 Multi-Stage Conversational AI
- 🌐 Web Search Integration
- 📊 Real-time Monitoring (Prometheus + Grafana)
- 🔒 Enterprise Security & Audit Logging

## Architecture
- Agent Service: FastAPI-based orchestration layer
- MCP Server: 28 production-ready tools (email, search, data analysis)
- Web UI: Streamlit interface with i18n support
- LiteLLM: Unified API gateway for all LLM providers
- Ollama: Local model inference (qwen2.5:0.5b, qwen2.5:7b)
- PostgreSQL: Persistent storage
- Redis: Caching layer
- RabbitMQ: Message queue
- Qdrant: Vector database for semantic search

## Services Included
- agent-service: AI agent orchestration
- mcp-server: Tool execution server
- web-ui: User interface
- litellm: LLM proxy gateway
- ollama: Local model server
- postgres: Database
- redis: Cache
- rabbitmq: Message broker
- qdrant: Vector store
- prometheus: Metrics collection
- grafana: Visualization

## Documentation
- Complete deployment guides (macOS, RHEL, Docker)
- Troubleshooting guide
- Context-aware agent guide
- SMTP configuration guide
- Multi-stage conversation guide
- Database schema documentation
- Test results (100% tool coverage)
- Project replication guide

## Technical Highlights
- Docker-based microservices architecture
- Health checks and auto-restart
- Comprehensive error handling
- Bilingual support (English/Chinese)
- Model information display
- Advanced sampling parameters (temperature, top-p, top-k)
- PDF text extraction with PyPDF2
- 180-second timeout for large document processing
- Context-aware conversation management

## Version
v1.0.0 - Initial Release
Date: 2025-10-21
EOF
)"
# Result: [main (root-commit) 0c7af4d] Initial commit: AI Agents Platform v1.0.0
```

#### Create Version Tag
```bash
# Create annotated version tag v1.0.0
git tag -a v1.0.0 -m "$(cat <<'EOF'
Release v1.0.0 - AI Agents Platform

Major Features:
- Multi-model LLM support (OpenAI, Anthropic, Google, Local)
- 28 production-ready tools
- PDF & document analysis
- Vision model support
- Multi-stage conversational AI
- Real-time monitoring with Prometheus & Grafana
- Enterprise security & audit logging

Services: 11 microservices running in Docker
Documentation: Complete deployment, troubleshooting, and user guides
Testing: 100% tool coverage

Release Date: 2025-10-21
EOF
)"
```

#### Verify Commit and Tag
```bash
# View commit history and tags
git log --oneline
git tag -l -n9
# Result:
# 0c7af4d Initial commit: AI Agents Platform v1.0.0
# v1.0.0 Release v1.0.0 - AI Agents Platform
```

#### Add Documentation Files
```bash
# Commit VERSION file and Git workflow guide
git add VERSION GIT_WORKFLOW.md
git commit -m "docs: add VERSION file and Git workflow guide

- Added VERSION file to track current version (1.0.0)
- Added comprehensive GIT_WORKFLOW.md with:
  - Semantic versioning strategy
  - Common Git commands
  - Branch management strategy
  - Commit message conventions
  - Version tagging procedures
  - Emergency recovery procedures
  - Best practices for version control"
# Result: [main 901b1af] docs: add VERSION file and Git workflow guide
```

#### Repository Summary
```bash
# Display comprehensive repository information
echo "=== Git Repository Summary ==="
echo ""
echo "📍 Repository Location:"
pwd
echo ""
echo "📊 Commit History:"
git log --oneline
echo ""
echo "🏷️  Version Tags:"
git tag -l
echo ""
echo "📝 Current Version:"
cat VERSION
echo ""
echo "📁 Tracked Files:"
git ls-files | wc -l
echo "files tracked"
echo ""
echo "🔒 .gitignore Protection:"
echo "- .env files ✓"
echo "- Docker volumes ✓"
echo "- Python cache ✓"
echo "- Logs ✓"
echo ""
echo "👤 Git Configuration:"
git config user.name
git config user.email
```

---

## Common Docker Commands

### Service Management
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart <service-name>

# View logs
docker-compose logs -f <service-name>

# Rebuild and restart
docker-compose up -d --build <service-name>
```

### Monitoring
```bash
# Check service status
docker-compose ps

# View resource usage
docker stats

# Check logs for specific service
docker-compose logs agent-service
docker-compose logs web-ui
docker-compose logs litellm
```

### Maintenance
```bash
# Remove all stopped containers
docker-compose down --remove-orphans

# Remove volumes (CAUTION: deletes data)
docker-compose down -v

# Prune unused images
docker image prune -a

# Clean up everything (CAUTION)
docker system prune -a --volumes
```

---

## Common Git Commands Reference

### Daily Workflow
```bash
# Check status
git status

# Stage changes
git add .
git add <specific-file>

# Commit
git commit -m "type: description"

# View history
git log --oneline
git log --graph --oneline --all
```

### Version Management
```bash
# Create new version
echo "1.1.0" > VERSION
git add VERSION
git commit -m "chore: bump version to 1.1.0"
git tag -a v1.1.0 -m "Release notes..."

# List tags
git tag -l

# Show tag details
git show v1.0.0
```

### Branch Management
```bash
# Create and switch to branch
git checkout -b feature/new-feature

# Switch branches
git checkout main

# Merge branch
git merge feature/new-feature

# Delete branch
git branch -d feature/new-feature

# List branches
git branch -a
```

### Remote Operations (when configured)
```bash
# Add remote
git remote add origin <repository-url>

# Push to remote
git push -u origin main
git push --tags

# Pull from remote
git pull origin main

# View remotes
git remote -v
```

---

## Project-Specific Commands

### Development
```bash
# Access web UI
open http://localhost:8501

# Check LiteLLM health
curl http://localhost:4000/health/readiness

# Check agent service
curl http://localhost:8002/health

# View Grafana dashboard
open http://localhost:3000
```

### Testing
```bash
# Run tool tests
python test_tools.py

# Test specific service
docker-compose exec agent-service python -m pytest

# Check service health
curl http://localhost:8002/health
curl http://localhost:8001/health
```

### Database
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U aiplatform -d aiplatform

# View database logs
docker-compose logs postgres

# Backup database
docker-compose exec postgres pg_dump -U aiplatform aiplatform > backup.sql

# Restore database
docker-compose exec -T postgres psql -U aiplatform aiplatform < backup.sql
```

### Ollama Model Management
```bash
# Pull new model
docker-compose exec ollama ollama pull qwen2.5:7b

# List models
docker-compose exec ollama ollama list

# Remove model
docker-compose exec ollama ollama rm <model-name>
```

---

## Troubleshooting Commands

### Debug Services
```bash
# View all logs
docker-compose logs

# Follow logs for specific service
docker-compose logs -f web-ui

# Inspect container
docker inspect ai-web-ui

# Execute command in container
docker-compose exec web-ui sh
```

### Network Issues
```bash
# Check network
docker network ls
docker network inspect ai-platform

# Test connectivity between services
docker-compose exec web-ui ping agent-service
```

### Resource Issues
```bash
# Check disk usage
docker system df

# Check volume usage
docker volume ls
du -sh postgres_data/ redis_data/ qdrant_data/

# Monitor resources
docker stats
```

---

## Maintenance Schedule Commands

### Daily
```bash
# Check service health
docker-compose ps

# View recent logs
docker-compose logs --tail=100
```

### Weekly
```bash
# Clean up unused images
docker image prune

# Check disk space
df -h
docker system df
```

### Monthly
```bash
# Full system cleanup (careful!)
docker system prune -a

# Backup database
docker-compose exec postgres pg_dump -U aiplatform aiplatform > backup_$(date +%Y%m%d).sql

# Review logs
docker-compose logs --since 24h > logs_$(date +%Y%m%d).txt
```

---

## Notes

- All commands are run from the project root directory: `/path/to/your/ai_platform`
- Git user configured as: your-email@gmail.com
- Current version: v1.0.0
- Services run on macOS (ARM64 architecture)

## Command Log Format

Each command entry should include:
- **Date**: When the command was run
- **Context**: What task/feature was being worked on
- **Command**: The actual command executed
- **Result**: Brief description of outcome (optional)

---

## Future Commands

This section will be updated with new commands as they are executed during development and maintenance.

### Template for Adding New Commands
```
### Task: [Description]
Date: YYYY-MM-DD

#### [Step Description]
\`\`\`bash
# Command with comments
<actual-command>
# Result: [outcome]
\`\`\`
```
