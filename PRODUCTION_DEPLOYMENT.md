# AI Platform - Production Deployment Guide
## Red Hat Enterprise Linux 9.4 with 2x NVIDIA H100 GPUs

**Version:** 2.0.0  
**Target Environment:** RHEL 9.4 with GPU Acceleration  
**Last Updated:** 2025-10-29

---

## Table of Contents

1. [Overview](#overview)
2. [Hardware Requirements](#hardware-requirements)
3. [Software Prerequisites](#software-prerequisites)
4. [Pre-Deployment Checklist](#pre-deployment-checklist)
5. [Quick Start](#quick-start)
6. [Detailed Installation](#detailed-installation)
7. [Configuration](#configuration)
8. [Deployment](#deployment)
9. [Post-Deployment](#post-deployment)
10. [Security Hardening](#security-hardening)
11. [Monitoring & Maintenance](#monitoring--maintenance)
12. [Troubleshooting](#troubleshooting)
13. [Backup & Recovery](#backup--recovery)

---

## Overview

This guide provides comprehensive instructions for deploying the AI Platform in a production environment on Red Hat Enterprise Linux 9.4 with NVIDIA H100 GPU acceleration.

### Architecture Highlights

- **GPU-Accelerated LLM Inference**: Utilizing 2x NVIDIA H100 GPUs for maximum throughput
- **High Availability**: Multiple replicas of critical services
- **Scalable**: Designed to handle 200+ concurrent requests
- **Secure**: Production-grade security hardening
- **Observable**: Comprehensive monitoring with Prometheus & Grafana

### Services

| Service | Port | Replicas | GPU | Purpose |
|---------|------|----------|-----|---------|
| Web UI | 8501 | 2 | No | User interface |
| Agent Service | 8002 | 3 | No | Task orchestration |
| MCP Server | 8001 | 3 | No | Tool execution |
| LiteLLM | 4000 | 1 | No | LLM proxy |
| Ollama | 11434 | 1 | Yes (2x H100) | Local LLM inference |
| PostgreSQL | 5433 | 1 | No | Primary database |
| Redis | 6380 | 1 | No | Caching layer |
| Qdrant | 6333 | 1 | No | Vector database |
| RabbitMQ | 5672 | 1 | No | Message queue |
| Prometheus | 9090 | 1 | No | Metrics collection |
| Grafana | 3000 | 1 | No | Monitoring dashboard |
| NGINX | 80/443 | 1 | No | Reverse proxy |

---

## Hardware Requirements

### Minimum Configuration

| Component | Requirement |
|-----------|-------------|
| **CPU** | 8 cores (Intel Xeon or AMD EPYC) |
| **RAM** | 32 GB DDR4/DDR5 |
| **Storage** | 100 GB NVMe SSD |
| **GPU** | 2x NVIDIA H100 94GB |
| **Network** | 1 Gbps Ethernet |

### Recommended Configuration

| Component | Recommendation |
|-----------|---------------|
| **CPU** | 16+ cores @ 2.5GHz+ |
| **RAM** | 64-128 GB ECC Memory |
| **Storage** | 500 GB NVMe SSD (RAID 10) |
| **GPU** | 2x NVIDIA H100 PCIe 94GB |
| **Network** | 10 Gbps Ethernet |

### GPU Specifications (NVIDIA H100)

- **Architecture**: Hopper
- **Memory**: 94 GB HBM3
- **Memory Bandwidth**: 3.35 TB/s
- **FP16 Performance**: 1,979 TFLOPS
- **TDP**: 350W per GPU
- **CUDA Compute Capability**: 9.0

---

## Software Prerequisites

### Operating System

- **OS**: Red Hat Enterprise Linux 9.4 (Plow)
- **Kernel**: 5.14.0-427+ 
- **Architecture**: x86_64

### NVIDIA Software Stack

| Software | Version | Purpose |
|----------|---------|---------|
| NVIDIA Driver | 535.183.01+ | GPU driver |
| CUDA Toolkit | 12.2.0+ | CUDA libraries |
| nvidia-container-toolkit | 1.14.0+ | Docker GPU support |

### Container Runtime

| Software | Version | Purpose |
|----------|---------|---------|
| Docker Engine | 24.0.0+ | Container runtime |
| Docker Compose | 2.20.0+ | Multi-container orchestration |

---

## Pre-Deployment Checklist

Before deploying, ensure all prerequisites are met:

### System Checks

- [ ] RHEL 9.4 installed and updated
- [ ] System has minimum 8 CPU cores
- [ ] System has minimum 32 GB RAM
- [ ] System has minimum 100 GB free disk space
- [ ] Network connectivity (1 Gbps+)

### GPU Checks

- [ ] 2x NVIDIA H100 GPUs physically installed
- [ ] NVIDIA driver 535+ installed
- [ ] CUDA Toolkit 12.2+ installed
- [ ] `nvidia-smi` command works
- [ ] Both GPUs detected and healthy

### Software Checks

- [ ] Docker Engine 24+ installed
- [ ] Docker Compose 2.20+ installed
- [ ] nvidia-container-toolkit installed
- [ ] Docker can access GPUs
- [ ] SELinux configured (if applicable)
- [ ] Firewall configured for required ports

### Security Checks

- [ ] Strong passwords generated for all services
- [ ] SSL certificates obtained (Let's Encrypt recommended)
- [ ] API keys for OpenAI, Anthropic, etc. ready
- [ ] Backup strategy planned
- [ ] Disaster recovery tested

---

## Quick Start

For experienced administrators, here's the TL;DR:

```bash
# 1. Clone repository
git clone <repository-url> && cd ai_platform

# 2. Check prerequisites
sudo ./deploy-rhel-production.sh check

# 3. Install dependencies (if needed)
sudo ./deploy-rhel-production.sh install

# 4. Configure environment
cp .env.production.example .env
vi .env  # Edit with your credentials

# 5. Deploy
sudo ./deploy-rhel-production.sh deploy

# 6. Verify
sudo ./deploy-rhel-production.sh status
```

---

## Detailed Installation

### Step 1: Install NVIDIA Driver

```bash
# Enable NVIDIA repository
sudo dnf config-manager --add-repo \
    https://developer.download.nvidia.com/compute/cuda/repos/rhel9/x86_64/cuda-rhel9.repo

# Install driver
sudo dnf install -y nvidia-driver-latest nvidia-settings

# Reboot to load driver
sudo reboot

# Verify installation
nvidia-smi

# Expected output:
# +---------------------------------------------------------------------------------------+
# | NVIDIA-SMI 535.183.01   Driver Version: 535.183.01   CUDA Version: 12.2             |
# |-----------------------------------------+----------------------+----------------------+
# | GPU  Name                 Persistence-M | Bus-Id        Disp.A | Volatile Uncorr. ECC |
# | Fan  Temp   Perf          Pwr:Usage/Cap |         Memory-Usage | GPU-Util  Compute M. |
# |=========================================+======================+======================|
# |   0  NVIDIA H100 PCIe               Off | 00000000:17:00.0 Off |                    0 |
# | N/A   30C    P0              55W / 350W |      0MiB / 94514MiB |      0%      Default |
# +-----------------------------------------+----------------------+----------------------+
# |   1  NVIDIA H100 PCIe               Off | 00000000:65:00.0 Off |                    0 |
# | N/A   31C    P0              57W / 350W |      0MiB / 94514MiB |      0%      Default |
# +-----------------------------------------+----------------------+----------------------+
```

### Step 2: Install CUDA Toolkit

```bash
# Install CUDA Toolkit
sudo dnf install -y cuda-toolkit-12-2

# Add CUDA to PATH
echo 'export PATH=/usr/local/cuda-12.2/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.2/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# Verify CUDA
nvcc --version

# Expected output:
# nvcc: NVIDIA (R) Cuda compiler driver
# Copyright (c) 2005-2023 NVIDIA Corporation
# Built on Tue_Aug_15_22:02:13_PDT_2023
# Cuda compilation tools, release 12.2, V12.2.140
```

### Step 3: Install Docker

```bash
# Add Docker repository
sudo dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo

# Install Docker
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Verify Docker
docker --version
docker compose version

# Add current user to docker group (optional)
sudo usermod -aG docker $USER
newgrp docker
```

### Step 4: Install nvidia-container-toolkit

```bash
# Add NVIDIA container toolkit repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.repo | \
    sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo

# Install nvidia-container-toolkit
sudo dnf install -y nvidia-container-toolkit

# Configure Docker runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Test GPU access in Docker
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubi9 nvidia-smi

# Should display same nvidia-smi output as before
```

### Step 5: Configure Firewall

```bash
# Allow required ports
sudo firewall-cmd --permanent --add-port=80/tcp        # HTTP
sudo firewall-cmd --permanent --add-port=443/tcp       # HTTPS
sudo firewall-cmd --permanent --add-port=8501/tcp      # Web UI
sudo firewall-cmd --permanent --add-port=8000/tcp      # Agent Service
sudo firewall-cmd --permanent --add-port=8001/tcp      # MCP Server
sudo firewall-cmd --permanent --add-port=4000/tcp      # LiteLLM
sudo firewall-cmd --permanent --add-port=3000/tcp      # Grafana
sudo firewall-cmd --permanent --add-port=9090/tcp      # Prometheus

# Reload firewall
sudo firewall-cmd --reload

# Verify ports
sudo firewall-cmd --list-ports
```

---

## Configuration

### Step 1: Configure Environment Variables

```bash
# Copy production environment template
cp .env.production.example .env

# Edit with your credentials
vi .env
```

**Critical Variables to Configure:**

```bash
# API Keys (REQUIRED)
OPENAI_API_KEY=sk-proj-your-production-key
ANTHROPIC_API_KEY=sk-ant-your-production-key
GEMINI_API_KEY=your-gemini-key

# Database Credentials (Generate secure passwords!)
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
RABBITMQ_DEFAULT_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
LITELLM_MASTER_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# GPU Configuration (REQUIRED for H100)
ENABLE_GPU=true
CUDA_VISIBLE_DEVICES=0,1

# Production Settings
ENVIRONMENT=production
LOG_LEVEL=info
MAX_CONCURRENT_REQUESTS=200
```

### Step 2: Configure SSL Certificates

For production, SSL/TLS is required. Use Let's Encrypt for free certificates:

```bash
# Install certbot
sudo dnf install -y certbot

# Obtain certificates (replace your-domain.com)
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Copy certificates to NGINX config directory
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem \
    /path/to/your/ai_platform/config/nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem \
    /path/to/your/ai_platform/config/nginx/ssl/

# Update NGINX configuration
vi config/nginx/nginx.conf
# Uncomment SSL lines and update server_name
```

### Step 3: Verify Configuration

```bash
# Check all prerequisites
sudo ./deploy-rhel-production.sh check

# Expected output:
# ✓ Operating System: RHEL 9.4
# ✓ CPU Cores: 16
# ✓ Total Memory: 64GB
# ✓ Available Disk: 500GB
# ✓ NVIDIA Driver: 535.183.01
# ✓ Detected GPUs: 2
# ✓ CUDA Version: 12.2
# ✓ Docker Version: 24.0.7
# ✓ Docker Compose Version: v2.23.0
# ✓ nvidia-container-toolkit working
```

---

## Deployment

### Automated Deployment (Recommended)

```bash
# Full deployment with one command
sudo ./deploy-rhel-production.sh deploy
```

This script will:
1. ✅ Check all prerequisites
2. ✅ Prepare environment
3. ✅ Pull Docker images
4. ✅ Build custom services
5. ✅ Start services in correct order
6. ✅ Run health checks

### Manual Deployment (Advanced)

If you prefer manual control:

```bash
# 1. Pull images
docker compose -f docker-compose.production.yml pull

# 2. Build services
docker compose -f docker-compose.production.yml build --no-cache

# 3. Start infrastructure
docker compose -f docker-compose.production.yml up -d postgres redis qdrant rabbitmq
sleep 15

# 4. Start LLM services
docker compose -f docker-compose.production.yml up -d ollama litellm
sleep 20

# 5. Start application services
docker compose -f docker-compose.production.yml up -d mcp-server agent-service web-ui
sleep 15

# 6. Start monitoring
docker compose -f docker-compose.production.yml up -d prometheus grafana nginx
```

### Verify Deployment

```bash
# Check service status
docker compose -f docker-compose.production.yml ps

# Should show all services as "Up" and "healthy"

# Check GPU usage
nvidia-smi

# Should show Ollama process using GPUs

# Test health endpoints
curl http://localhost:8001/health  # MCP Server
curl http://localhost:8002/health  # Agent Service  
curl http://localhost:4000/health/readiness  # LiteLLM
curl http://localhost:9090/-/healthy  # Prometheus
```

---

## Post-Deployment

### 1. Initial Access

```bash
# Web UI
http://your-domain.com or https://your-domain.com

# Grafana Dashboard
https://your-domain.com/grafana
Username: admin
Password: (from GRAFANA_ADMIN_PASSWORD in .env)

# Prometheus
http://your-domain.com:9090
```

### 2. Load Ollama Models

```bash
# Pull recommended models for H100
docker compose -f docker-compose.production.yml exec ollama ollama pull llama2:70b
docker compose -f docker-compose.production.yml exec ollama ollama pull codellama:34b
docker compose -f docker-compose.production.yml exec ollama ollama pull qwen2.5:72b

# List loaded models
docker compose -f docker-compose.production.yml exec ollama ollama list
```

### 3. Configure Automated Backups

```bash
# Create backup script in cron
sudo crontab -e

# Add daily backup at 2 AM
0 2 * * * /path/to/ai_platform/deploy-rhel-production.sh backup

# Add weekly cleanup at 3 AM Sunday
0 3 * * 0 docker system prune -af
```

### 4. Set Up Monitoring Alerts

Configure alerts in Grafana:
- High memory usage (>80%)
- High GPU temperature (>85°C)
- High error rate (>5%)
- Service downtime
- Disk space low (<20% free)

---

## Security Hardening

### 1. Change Default Credentials

```bash
# PostgreSQL
docker compose -f docker-compose.production.yml exec postgres \
    psql -U admin -d ai_platform -c "ALTER USER admin WITH PASSWORD 'new-secure-password';"

# Grafana (via UI)
# Login → Profile → Change Password
```

### 2. Configure SELinux (if enabled)

```bash
# Check SELinux status
getenforce

# If Enforcing, configure policies
sudo setsebool -P container_manage_cgroup on
sudo setsebool -P virt_sandbox_use_all_caps on
```

### 3. Limit External Access

```bash
# Bind services to localhost only (already configured in docker-compose.production.yml)
# Services are only accessible through NGINX reverse proxy

# Verify
ss -tlnp | grep -E '(8001|8002|4000)'
# Should show 127.0.0.1 not 0.0.0.0
```

### 4. Enable Audit Logging

```bash
# Audit logging is enabled by default in production
# View audit logs
docker compose -f docker-compose.production.yml logs -f mcp-server | grep AUDIT
```

---

## Monitoring & Maintenance

### Daily Operations

```bash
# View logs
sudo ./deploy-rhel-production.sh logs

# Check status
sudo ./deploy-rhel-production.sh status

# Monitor GPU usage
watch -n 1 nvidia-smi

# Monitor Docker stats
docker stats
```

### Weekly Maintenance

```bash
# Update services
sudo ./deploy-rhel-production.sh update

# Clean up unused resources
sudo ./deploy-rhel-production.sh cleanup

# Verify backups
ls -lh backups/
```

### Monthly Review

- Review monitoring dashboards
- Analyze error logs
- Check disk usage growth
- Review API usage costs
- Update documentation
- Test disaster recovery

---

## Troubleshooting

### GPU Not Detected

```bash
# Check if GPUs are visible
nvidia-smi

# Check if Docker can access GPUs
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubi9 nvidia-smi

# Check Ollama GPU usage
docker compose -f docker-compose.production.yml logs ollama | grep CUDA
```

### Service Won't Start

```bash
# Check logs for specific service
docker compose -f docker-compose.production.yml logs [service-name]

# Restart service
docker compose -f docker-compose.production.yml restart [service-name]

# Force recreate
docker compose -f docker-compose.production.yml up -d --force-recreate [service-name]
```

### High Memory Usage

```bash
# Check memory usage
free -h
docker stats

# Restart heavy services
docker compose -f docker-compose.production.yml restart litellm ollama
```

### SSL Certificate Issues

```bash
# Renew Let's Encrypt certificates
sudo certbot renew

# Reload NGINX
docker compose -f docker-compose.production.yml restart nginx
```

---

## Backup & Recovery

### Automated Backup

Backups are configured to run daily at 2 AM via cron:

```bash
# Manual backup
sudo ./deploy-rhel-production.sh backup

# Backup location
ls -lh backups/
# Example: backup_20251029_140530.sql.gz
```

### Restore from Backup

```bash
# Stop services
docker compose -f docker-compose.production.yml stop

# Restore database
gunzip -c backups/backup_YYYYMMDD_HHMMSS.sql.gz | \
    docker compose -f docker-compose.production.yml exec -T postgres \
    psql -U admin ai_platform

# Start services
docker compose -f docker-compose.production.yml start
```

### Disaster Recovery

1. **Backup critical data:**
   - Database backups (PostgreSQL)
   - Vector embeddings (Qdrant)
   - Configuration files (.env, nginx.conf)
   - SSL certificates

2. **Document configuration:**
   - API keys and credentials
   - Domain names and DNS settings
   - Firewall rules
   - Custom configurations

3. **Test restore procedure monthly**

---

## Support & Resources

- **Documentation**: See README.md and other guides
- **Issues**: GitHub Issues
- **NVIDIA Documentation**: https://docs.nvidia.com/
- **Docker Documentation**: https://docs.docker.com/

---

**Deployment Complete!** 🎉

Your AI Platform is now running in production with GPU acceleration.

Access your platform at: **https://your-domain.com**
