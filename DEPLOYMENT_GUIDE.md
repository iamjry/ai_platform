# AI Platform - Complete Deployment Guide

## Table of Contents

- [Overview](#overview)
- [System Requirements](#system-requirements)
- [Quick Start](#quick-start)
- [Detailed Deployment](#detailed-deployment)
- [Database Setup](#database-setup)
- [Configuration](#configuration)
- [Testing](#testing)
- [Maintenance](#maintenance)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)

## Overview

This guide provides complete instructions for deploying the AI Platform, an enterprise-grade multi-model AI system with 28 intelligent tools, full-text search, and comprehensive monitoring.

### Architecture Components

- **Web UI** - Streamlit-based frontend (Port 8501)
- **Agent Service** - Task orchestration (Port 8000)
- **MCP Server** - Tool execution (Port 8001)
- **LiteLLM** - Multi-model LLM proxy (Port 4000)
- **PostgreSQL** - Primary database (Port 5433)
- **Redis** - Caching layer (Port 6380)
- **Qdrant** - Vector database (Port 6333)
- **Ollama** - Local LLM inference (Port 11434)
- **Prometheus** - Metrics collection (Port 9090)
- **Grafana** - Monitoring dashboards (Port 3000)

## System Requirements

### Development Environment (macOS)
- **CPU**: 4+ cores (Apple Silicon M1/M2 or Intel)
- **RAM**: 8 GB minimum, 16 GB recommended
- **Disk**: 10 GB free space
- **OS**: macOS 12.0 (Monterey) or later
- **Docker Desktop**: 4.20+ for Mac
- **Docker Compose**: 2.0+ (included with Docker Desktop)

### Production Environment (Red Hat Enterprise Linux 9.4)
- **CPU**: 8+ cores
- **RAM**: 32 GB minimum, 64 GB recommended
- **Disk**: 100 GB SSD (NVMe preferred)
- **OS**: Red Hat Enterprise Linux 9.4 (Plow) x86_64
- **GPU**: 2x NVIDIA H100L 94GB
  - NVIDIA Driver: 535+
  - CUDA Toolkit: 12.0+
  - nvidia-container-toolkit installed
- **Docker**: 24.0+
- **Docker Compose**: 2.20+
- **Network**: 1 Gbps+ for model downloads

### Minimum Requirements (Testing/Development)
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disk**: 10 GB free space
- **OS**: Linux, macOS, or Windows with WSL2
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### GPU Requirements (Production)
- **NVIDIA GPU**: H100, A100, or V100 series
- **VRAM**: 40GB+ per GPU
- **CUDA Compute Capability**: 8.0+
- **Driver**: 535+ (for CUDA 12.x support)
- **Container Runtime**: nvidia-container-toolkit

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd ai_platform
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
nano .env
```

**Required Variables:**
```bash
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-ant-your-key
```

### 3. Deploy

```bash
# For macOS Development
./deploy-macos.sh

# For Linux Development
./deploy.sh

# For RHEL Production with GPU
./deploy-rhel-production.sh
```

### 4. Verify

```bash
# Check service health
docker compose ps

# Run tests
python3 test_tools.py

# Access Web UI
open http://localhost:8501
```

## Detailed Deployment

### Step 1: Preparation

#### Check Prerequisites

```bash
# Check Docker
docker --version
docker compose version

# Check disk space
df -h .

# Check memory
free -h  # Linux
vm_stat  # macOS
```

#### Clone and Navigate

```bash
git clone <repository-url>
cd ai_platform
```

### Step 2: Environment Configuration

#### Create .env File

```bash
cp .env.example .env
```

#### Edit Configuration

```bash
nano .env
```

**Essential Variables:**

```bash
# API Keys
OPENAI_API_KEY=sk-proj-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Database (auto-generated secure passwords recommended)
POSTGRES_USER=admin
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
POSTGRES_DB=ai_platform

# Redis
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# RabbitMQ
RABBITMQ_DEFAULT_USER=admin
RABBITMQ_DEFAULT_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
```

### Step 3: Build Services

#### Option A: Using Deployment Script

```bash
./deploy.sh start
```

This will:
- Check prerequisites
- Create directory structure
- Build Docker images
- Start all services
- Initialize database
- Run health checks

#### Option B: Manual Deployment

```bash
# Build images
docker compose build

# Start infrastructure
docker compose up -d postgres redis qdrant rabbitmq

# Wait for infrastructure
sleep 15

# Initialize database
./scripts/init-db.sh init

# Start LLM services
docker compose up -d ollama litellm

# Wait for LLM services
sleep 15

# Start application services
docker compose up -d mcp-server agent-service web-ui

# Start monitoring
docker compose up -d prometheus grafana
```

### Step 4: Database Initialization

The database is automatically initialized by the deployment script, but you can manually initialize:

```bash
# Initialize with schema and sample data
./scripts/init-db.sh init

# Verify tables
./scripts/init-db.sh verify

# View statistics
./scripts/init-db.sh stats
```

### Step 5: Verification

#### Check Service Health

```bash
# View all services
docker compose ps

# Check specific service logs
docker compose logs -f mcp-server

# Check health endpoints
curl http://localhost:8001/health
curl http://localhost:8000/health
curl http://localhost:4000/health/readiness
```

#### Run Test Suite

```bash
# Install dependencies
pip3 install requests

# Run all tests
python3 test_tools.py

# Expected output: 29/29 tests passing (100%)
```

## Database Setup

### Automatic Initialization

The deployment script automatically runs database initialization. To manually control:

```bash
# Initialize fresh database
./scripts/init-db.sh init

# Reset database (WARNING: destroys all data)
./scripts/init-db.sh reset

# Create backup
./scripts/init-db.sh backup

# Restore from backup
./scripts/init-db.sh restore /path/to/backup.sql
```

### Manual Database Setup

```bash
# Connect to PostgreSQL
docker compose exec postgres psql -U admin -d ai_platform

# Run schema manually
docker compose exec -T postgres psql -U admin -d ai_platform < services/mcp-server/schema.sql

# Load sample data
docker compose exec -T postgres psql -U admin -d ai_platform < services/mcp-server/seed.sql
```

### Database Schema

The platform includes 4 main tables:

1. **users** - User accounts and authentication
2. **documents** - Knowledge base with full-text search
3. **tasks** - Task management system
4. **audit_logs** - Security audit trail

📖 See [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) for complete documentation.

## Configuration

### Environment Variables

#### API Keys

```bash
# OpenAI (GPT models)
OPENAI_API_KEY=sk-proj-your-key

# Anthropic (Claude models)
ANTHROPIC_API_KEY=sk-ant-your-key
```

#### Database

```bash
POSTGRES_USER=admin
POSTGRES_PASSWORD=secure-password
POSTGRES_DB=ai_platform
```

#### Redis

```bash
REDIS_PASSWORD=secure-redis-password
```

#### Application Settings

```bash
ENVIRONMENT=development  # development, staging, production
LOG_LEVEL=info          # debug, info, warning, error
MAX_CONCURRENT_REQUESTS=100
```

### Service Configuration

#### LiteLLM (config/litellm-config.yaml)

```yaml
model_list:
  - model_name: gpt-3.5-turbo
    litellm_params:
      model: gpt-3.5-turbo
      api_key: ${OPENAI_API_KEY}

  - model_name: claude-3-sonnet
    litellm_params:
      model: claude-3-sonnet-20240229
      api_key: ${ANTHROPIC_API_KEY}

  - model_name: qwen2.5
    litellm_params:
      model: ollama/qwen2.5
      api_base: http://ollama:11434
```

#### Prometheus (config/prometheus.yml)

```yaml
scrape_configs:
  - job_name: 'mcp-server'
    static_configs:
      - targets: ['mcp-server:8000']

  - job_name: 'agent-service'
    static_configs:
      - targets: ['agent-service:8000']
```

## Testing

### Automated Tests

```bash
# Run full test suite
python3 test_tools.py

# Test specific component
curl -X POST http://localhost:8001/tools/analyze_data \
  -H 'Content-Type: application/json' \
  -d '{
    "data_source": "sales_data",
    "analysis_type": "descriptive",
    "options": {}
  }'
```

### Manual Testing

#### Test Web UI
```bash
open http://localhost:8501
```

#### Test Chat API
```bash
curl -X POST http://localhost:8000/agent/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "Hello, how can you help me?",
    "model": "qwen2.5",
    "temperature": 0.7
  }'
```

#### Test Tool Execution
```bash
curl -X POST http://localhost:8001/tools/financial_calculator \
  -H 'Content-Type: application/json' \
  -d '{
    "operation": "roi",
    "values": {"gain": 15000, "cost": 10000}
  }'
```

### Load Testing

```bash
# Install Apache Bench
apt-get install apache2-utils  # Ubuntu/Debian
brew install httpd              # macOS

# Run load test
ab -n 1000 -c 10 http://localhost:8001/health
```

## Maintenance

### Daily Operations

#### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f mcp-server

# Last 100 lines
docker compose logs --tail=100 agent-service
```

#### Monitor Resources

```bash
# Real-time stats
docker stats

# Service status
docker compose ps
```

#### Backup Database

```bash
# Automatic backup with script
./scripts/init-db.sh backup

# Manual backup
docker compose exec postgres pg_dump -U admin ai_platform > backup_$(date +%Y%m%d).sql

# Backup with compression
docker compose exec postgres pg_dump -U admin ai_platform | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Weekly Maintenance

#### Update Docker Images

```bash
# Pull latest images
docker compose pull

# Rebuild services
docker compose up -d --build
```

#### Clean Up

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes (CAUTION: may delete data)
docker volume prune

# Full cleanup
docker system prune -a --volumes
```

#### Database Maintenance

```bash
# Vacuum database
docker compose exec postgres psql -U admin -d ai_platform -c "VACUUM ANALYZE;"

# Check database size
docker compose exec postgres psql -U admin -d ai_platform -c "
SELECT pg_size_pretty(pg_database_size('ai_platform')) as size;
"
```

### Monitoring

#### Grafana Dashboards

Access: http://localhost:3000 (admin/admin)

**Key Metrics to Monitor:**
- Request rate and latency
- Error rate
- Database query performance
- Redis cache hit rate
- LLM token usage and costs
- System resources (CPU, memory, disk)

#### Prometheus Queries

Access: http://localhost:9090

**Useful Queries:**
```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Average latency
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

## Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Find process using port
lsof -i :8501  # or any port

# Kill process
kill -9 [PID]

# Or change port in docker-compose.yml
ports:
  - "8502:8501"  # Change 8501 to 8502
```

#### Service Won't Start

```bash
# Check logs
docker compose logs [service-name]

# Restart service
docker compose restart [service-name]

# Force rebuild
docker compose up -d --build --force-recreate [service-name]
```

#### Database Connection Errors

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Check connection
docker compose exec postgres psql -U admin -d ai_platform -c "SELECT 1"

# Reinitialize database
./scripts/init-db.sh reset
```

#### Out of Memory

```bash
# Check memory usage
docker stats

# Increase Docker memory limit (Docker Desktop)
# Settings → Resources → Memory → Increase limit

# Stop non-essential services
docker compose stop grafana prometheus
```

#### Ollama Model Issues

```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Pull model manually
docker compose exec ollama ollama pull qwen2.5:latest

# List available models
docker compose exec ollama ollama list
```

### Debug Mode

#### Enable Debug Logging

Edit `.env`:
```bash
LOG_LEVEL=debug
DEBUG=true
```

Restart services:
```bash
docker compose restart
```

#### Access Container Shell

```bash
# Access MCP server container
docker compose exec mcp-server /bin/bash

# Access PostgreSQL
docker compose exec postgres psql -U admin -d ai_platform

# Access Redis
docker compose exec redis redis-cli -a $REDIS_PASSWORD
```

## Production Deployment

### Platform-Specific Deployment

#### macOS Development Deployment

```bash
# Use the macOS-specific deployment script
./deploy-macos.sh

# This script:
# - Detects macOS-specific Docker configuration
# - Uses Docker Desktop for Mac
# - Optimizes for local development
# - Skips GPU configuration (uses CPU)
```

#### RHEL 9.4 Production Deployment

```bash
# Automated production deployment for RHEL with GPU support
sudo ./deploy-rhel-production.sh

# This script:
# - Verifies NVIDIA GPU drivers and CUDA
# - Configures nvidia-container-toolkit
# - Enables GPU acceleration for Ollama and LiteLLM
# - Sets production-grade resource limits
# - Configures security hardening
# - Sets up automated backups
```

**Prerequisites for RHEL Production:**

1. **Install NVIDIA Drivers and CUDA:**
   ```bash
   # Install NVIDIA driver
   sudo dnf install -y nvidia-driver nvidia-settings

   # Verify driver
   nvidia-smi

   # Install CUDA Toolkit
   sudo dnf config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/rhel9/x86_64/cuda-rhel9.repo
   sudo dnf install -y cuda-toolkit-12-2
   ```

2. **Install Docker and nvidia-container-toolkit:**
   ```bash
   # Install Docker
   sudo dnf install -y docker-ce docker-ce-cli containerd.io

   # Install nvidia-container-toolkit
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.repo | \
     sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo

   sudo dnf install -y nvidia-container-toolkit
   sudo nvidia-ctk runtime configure --runtime=docker
   sudo systemctl restart docker

   # Verify GPU in Docker
   docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubi9 nvidia-smi
   ```

3. **Configure Firewall:**
   ```bash
   # Allow required ports
   sudo firewall-cmd --permanent --add-port=8501/tcp  # Web UI
   sudo firewall-cmd --permanent --add-port=8000/tcp  # Agent Service
   sudo firewall-cmd --permanent --add-port=8001/tcp  # MCP Server
   sudo firewall-cmd --permanent --add-port=4000/tcp  # LiteLLM
   sudo firewall-cmd --permanent --add-port=3000/tcp  # Grafana
   sudo firewall-cmd --permanent --add-port=9090/tcp  # Prometheus
   sudo firewall-cmd --reload
   ```

### Pre-Production Checklist

- [ ] Change all default passwords
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure HTTPS/SSL with reverse proxy
- [ ] Set up automated backups (daily)
- [ ] Configure log rotation
- [ ] Set up monitoring alerts (Grafana/PagerDuty)
- [ ] Review and set resource limits
- [ ] Enable rate limiting
- [ ] Configure CORS properly
- [ ] Set up reverse proxy (nginx/HAProxy)
- [ ] Verify GPU drivers and CUDA (production)
- [ ] Configure SELinux policies (RHEL)
- [ ] Set up firewall rules
- [ ] Enable audit logging
- [ ] Test disaster recovery procedures

### Security Hardening

```bash
# Generate secure passwords
openssl rand -base64 32

# Use Docker secrets (docker-compose-prod.yml)
secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt

# Enable firewall
ufw enable
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
```

### High Availability Setup

```yaml
# docker-compose-ha.yml
services:
  postgres:
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure

  mcp-server:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### Backup Strategy

#### Automated Backups

```bash
# Add to crontab
0 2 * * * /path/to/scripts/init-db.sh backup

# Backup to S3 (if configured)
0 3 * * * aws s3 cp /path/to/backup.sql s3://your-bucket/backups/
```

#### Disaster Recovery

1. Keep offsite backups
2. Test restore procedures regularly
3. Document recovery steps
4. Maintain backup retention policy (30 days)

### Performance Tuning

#### PostgreSQL

```sql
-- Increase shared_buffers
ALTER SYSTEM SET shared_buffers = '2GB';
ALTER SYSTEM SET effective_cache_size = '6GB';
ALTER SYSTEM SET maintenance_work_mem = '512MB';
```

#### Redis

```bash
# Increase max memory
docker compose exec redis redis-cli CONFIG SET maxmemory 2gb
docker compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Monitoring in Production

- Set up email/Slack alerts in Grafana
- Configure PagerDuty for critical alerts
- Monitor:
  - Service uptime (target: 99.9%)
  - Response time (target: < 500ms p95)
  - Error rate (target: < 1%)
  - Database size and growth rate
  - API usage and costs

---

## Support

- **Documentation**: See README.md and other docs
- **Issues**: GitHub Issues
- **Email**: support@example.com

## License

MIT License - see LICENSE file

---

**Version:** 2.0.0
**Last Updated:** 2025-10-16
**Status:** Production Ready
