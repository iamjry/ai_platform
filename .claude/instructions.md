# Project: AI Platform - Claude Instructions

## Project Overview
Enterprise-grade AI platform with hybrid LLM support (cloud + local), agent framework, and comprehensive monitoring.

## Version Control Policy

### Always Use Git
- Check `git status` before starting work
- Commit logical units of work (features, fixes, refactors)
- Commit before risky changes (can revert if needed)
- Commit after tests pass
- Use clear, descriptive commit messages

### Commit Message Format
```
<type>: <description>

[optional body]

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

### When to Commit
- ✅ Feature complete
- ✅ Bug fixed and tested
- ✅ Before experimental changes
- ✅ After refactoring
- ✅ End of logical work unit
- ❌ Not for typos, single variable renames, or trivial changes

## Token Efficiency Guidelines

### Rule 1: Search First, Read Second
```bash
# Find files
glob "**/*.py" | grep "model"

# Find code
grep "def process_" -n

# Only then read specific sections
read file.py --offset 100 --limit 50
```

### Rule 2: Batch Operations
```python
# ✅ Good - one message, multiple operations
Read file1.py
Read file2.py
Edit file1.py (change A)
Edit file2.py (change B)
Bash: pytest tests/

# ❌ Bad - separate messages
Message 1: Read file1.py
Message 2: Edit file1.py
Message 3: Read file2.py
Message 4: Edit file2.py
```

### Rule 3: Reference, Don't Repeat
```python
# ✅ Good
"See the error in services/web-ui/app.py:245"

# ❌ Bad
"The error is in this code: [paste 50 lines]"
```

### Rule 4: Use Smart Tools
- `Grep` > `Read` + manual search
- `Edit` > `Write` for changes
- `Task` agent > manual multi-step execution
- `Glob` > `find` command
- Parallel tool calls when possible

### Rule 5: Minimize Context
- Read only what you need
- Use `head`/`tail` for previews
- Use `grep -C 5` for context
- Check file sizes: `ls -lh` before reading

### Rule 6: Organize and Reuse
- Create helper scripts for repeated tasks
- Build templates for similar operations
- Reference previous successful patterns
- Don't rewrite what works

## Project-Specific Notes

### Technology Stack
- Frontend: Streamlit (Python)
- Backend: FastAPI
- LLM Gateway: LiteLLM
- Local Inference: Ollama (qwen2.5)
- Databases: PostgreSQL, Redis, Qdrant
- Monitoring: Prometheus, Grafana
- Containerization: Docker Compose

### Key Directories
- `services/web-ui/` - Streamlit frontend
- `services/agent-service/` - FastAPI agent service
- `services/mcp-server/` - MCP tool server
- `config/` - Configuration files
- `scripts/` - Utility scripts

### Important Files
- `docker-compose.yml` - Service orchestration
- `.env` - Environment variables (NOT in git)
- `services/web-ui/app.py` - Main UI
- `services/web-ui/i18n.py` - Translations

### Testing
- Always test after changes
- Use `docker-compose logs <service>` to check errors
- Verify service health: `docker-compose ps`

### Common Tasks
```bash
# Rebuild specific service
docker-compose build web-ui
docker-compose up -d web-ui

# View logs
docker-compose logs --tail=50 web-ui

# Check health
docker-compose ps

# Git workflow
git status
git add <files>
git commit -m "description"
git log --oneline -5
```

## User Preferences
- 🔥 **High efficiency** - minimize token usage
- 🔥 **Version control** - commit logical units
- 🔥 **Best practices** - industry standards
- 🔥 **No waste** - search before reading, batch operations

---
*This file helps Claude remember project context and preferences across sessions*
