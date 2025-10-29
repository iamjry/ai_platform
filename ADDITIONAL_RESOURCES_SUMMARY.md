# AI Platform - Additional Resources Summary
## Systemd Auto-Start, Grafana Dashboards, and Load Testing

**Created:** 2025-10-29  
**Package Version:** 2.0.0

---

## Overview

This document summarizes the additional production resources created for the AI Platform deployment:

1. **Systemd Service Files** - Automatic startup and management
2. **Grafana Dashboard Templates** - Production monitoring
3. **Load Testing Scripts** - Performance validation

---

## 1. Systemd Service Files

### Purpose

Enable automatic startup of the AI Platform on boot and provide systemd-based service management.

### Files Created

| File | Purpose | Location |
|------|---------|----------|
| `ai-platform.service` | Main service unit | `/etc/systemd/system/` |
| `ai-platform-backup.service` | Backup service | `/etc/systemd/system/` |
| `ai-platform-backup.timer` | Backup scheduler (daily 2 AM) | `/etc/systemd/system/` |
| `ai-platform-healthcheck.service` | Health monitoring | `/etc/systemd/system/` |
| `ai-platform-healthcheck.timer` | Health check scheduler (every 5 min) | `/etc/systemd/system/` |
| `install-systemd.sh` | Installation script | `systemd/` |

### Installation

```bash
# Navigate to systemd directory
cd /opt/ai_platform/systemd

# Run installation script
sudo ./install-systemd.sh

# Verify installation
systemctl status ai-platform
```

### Key Features

#### Main Service (`ai-platform.service`)

- ✅ **Auto-start on boot**: Platform starts automatically
- ✅ **Dependency management**: Requires Docker service
- ✅ **GPU verification**: Checks NVIDIA GPUs before starting
- ✅ **Ordered startup**: Services start in correct sequence
- ✅ **Restart policy**: Automatic restart on failure
- ✅ **Security**: ProtectSystem and ProtectHome enabled

#### Backup Service (`ai-platform-backup.timer`)

- ✅ **Scheduled backups**: Daily at 2:00 AM
- ✅ **Automatic cleanup**: Removes backups older than 30 days
- ✅ **Randomized delay**: Prevents load spikes
- ✅ **Boot backup**: Runs if missed during downtime

#### Health Check Service (`ai-platform-healthcheck.timer`)

- ✅ **Periodic checks**: Every 5 minutes
- ✅ **Auto-restart**: Restarts platform if services unhealthy
- ✅ **Service validation**: Checks MCP, Agent Service, and LiteLLM

### Usage Commands

```bash
# Start the platform
sudo systemctl start ai-platform

# Stop the platform
sudo systemctl stop ai-platform

# Restart the platform
sudo systemctl restart ai-platform

# Check status
sudo systemctl status ai-platform

# View logs
sudo journalctl -u ai-platform -f

# Enable auto-start (default after installation)
sudo systemctl enable ai-platform

# Disable auto-start
sudo systemctl disable ai-platform

# Manual backup
sudo systemctl start ai-platform-backup

# Check backup status
sudo systemctl status ai-platform-backup

# View health check logs
sudo journalctl -u ai-platform-healthcheck -f
```

### Benefits

1. **Reliability**: Platform survives server reboots
2. **Automation**: No manual startup required
3. **Monitoring**: Built-in health checks
4. **Backup**: Automated daily backups with retention
5. **Logging**: Centralized systemd journal logs

---

## 2. Grafana Dashboard Templates

### Purpose

Provide pre-configured Grafana dashboards for comprehensive monitoring of the AI Platform.

### Files Created

| File | Purpose | Panels |
|------|---------|--------|
| `ai-platform-overview.json` | System overview | 5 panels |
| `gpu-monitoring.json` | GPU monitoring (H100) | 6 panels |
| `dashboard-provisioning.yaml` | Auto-import config | - |
| `datasources/prometheus.yaml` | Prometheus datasource | - |

### Dashboard Details

#### System Overview Dashboard

**Panels:**
1. **Request Rate** - Real-time API request rate
2. **Error Rate** - Percentage of failed requests
3. **Response Time (p95 & p99)** - Latency percentiles
4. **CPU Usage** - System CPU utilization
5. **Memory Usage** - System memory utilization

**Refresh:** 30 seconds  
**Time Range:** Last 6 hours  
**UID:** `ai-platform-overview`

#### GPU Monitoring Dashboard

**Panels:**
1. **GPU 0 Utilization** - First H100 GPU usage
2. **GPU 1 Utilization** - Second H100 GPU usage
3. **GPU 0 Temperature** - Thermal monitoring
4. **GPU 1 Temperature** - Thermal monitoring
5. **GPU Memory Usage** - VRAM utilization timeline
6. **GPU Power Consumption** - Power draw monitoring

**Refresh:** 10 seconds  
**Time Range:** Last 1 hour  
**UID:** `ai-platform-gpu`

**Alert Thresholds:**
- GPU Utilization: 70% (yellow), 80% (orange), 90% (red)
- Temperature: 75°C (yellow), 85°C (orange), 90°C (red)
- Memory: 70% (yellow), 85% (red)

### Installation

The dashboards are automatically loaded when the platform starts via Grafana provisioning.

**Manual Import:**
1. Access Grafana: `http://localhost:3000`
2. Login: admin/admin (change after first login)
3. Navigate to: Dashboards → Import
4. Upload JSON files from `config/grafana/dashboards/`

### Access

```bash
# Grafana URL
http://localhost:3000
# or
https://your-domain.com/grafana

# Default credentials
Username: admin
Password: (from GRAFANA_ADMIN_PASSWORD in .env)
```

### Dashboard Features

- ✅ **Auto-refresh**: Configurable refresh intervals
- ✅ **Time range selection**: From 5 minutes to 90 days
- ✅ **Interactive**: Click to zoom, hover for details
- ✅ **Alerts**: Visual thresholds for critical metrics
- ✅ **Export**: Download as PNG or share link
- ✅ **Custom queries**: Modify Prometheus queries

### Monitoring Best Practices

1. **Set up alerts** for critical thresholds
2. **Review dashboards daily** during initial deployment
3. **Compare metrics** against baseline
4. **Document anomalies** and resolutions
5. **Archive screenshots** for reporting

---

## 3. Load Testing Scripts

### Purpose

Comprehensive load testing suite to validate platform performance under various conditions.

### Files Created

| File | Tool | Purpose |
|------|------|---------|
| `test-api-endpoints.sh` | Apache Bench | Quick API testing |
| `locustfile.py` | Locust | Comprehensive load testing |
| `requirements.txt` | pip | Python dependencies |
| `README.md` | - | Complete testing guide |

### Test Scripts Overview

#### Apache Bench Script (`test-api-endpoints.sh`)

**Features:**
- ✅ Tests 6 core API endpoints
- ✅ Concurrent user simulation
- ✅ Response time analysis
- ✅ Success rate metrics
- ✅ Automatic result reports

**Endpoints Tested:**
1. Health Check (`/health`)
2. Search Knowledge Base (`/tools/search_knowledge_base`)
3. Semantic Search (`/tools/semantic_search`)
4. Web Search (`/tools/web_search`)
5. Get Document (`/tools/get_document`)
6. Query Database (`/tools/query_database`)

**Usage:**

```bash
cd load-tests

# Basic test (10 users, 1000 requests)
./test-api-endpoints.sh

# Custom configuration
BASE_URL=http://production.example.com:8001 \
CONCURRENT_USERS=50 \
TOTAL_REQUESTS=5000 \
./test-api-endpoints.sh
```

**Output:**
- Results saved to `results_YYYYMMDD_HHMMSS/`
- Summary report in `SUMMARY.txt`
- CSV files for each endpoint
- TSV files for graphing

#### Locust Script (`locustfile.py`)

**Features:**
- ✅ Web UI for real-time monitoring
- ✅ Multiple user classes (AI Tools, LLM, Mixed)
- ✅ Realistic workload simulation
- ✅ Step-based load ramping
- ✅ CSV export for analysis

**User Classes:**
1. **AIToolUser**: Simulates tool usage patterns
   - Knowledge base search (10x weight)
   - Semantic search (8x weight)
   - Document retrieval (6x weight)
   - Web search (3x weight)
   - Data analysis (2x weight)

2. **LLMUser**: Simulates LLM chat interactions
   - Chat completions with 30s timeout
   - Varied prompts
   - Temperature: 0.7

3. **MixedWorkloadUser**: Realistic mixed patterns

**Usage:**

```bash
# Install dependencies
pip install -r requirements.txt

# Start with Web UI (http://localhost:8089)
locust -f locustfile.py --host=http://localhost:8001

# Headless mode (for CI/CD)
locust -f locustfile.py \
       --host=http://localhost:8001 \
       --users 100 \
       --spawn-rate 10 \
       --run-time 10m \
       --headless

# Export to CSV
locust -f locustfile.py \
       --host=http://localhost:8001 \
       --users 200 \
       --spawn-rate 20 \
       --run-time 5m \
       --headless \
       --csv=results/loadtest
```

### Test Scenarios

#### 1. Smoke Test (Quick Validation)
```bash
# 5 users, 100 requests
CONCURRENT_USERS=5 TOTAL_REQUESTS=100 ./test-api-endpoints.sh
```
**Expected:** All pass, < 500ms response time

#### 2. Load Test (Normal Traffic)
```bash
# 50 users, 10 minutes
locust -f locustfile.py --host=http://localhost:8001 --users 50 --spawn-rate 5 --run-time 10m --headless
```
**Expected:** p95 < 1s, error rate < 2%

#### 3. Stress Test (Peak Traffic)
```bash
# 200 users, 15 minutes
locust -f locustfile.py --host=http://localhost:8001 --users 200 --spawn-rate 20 --run-time 15m --headless
```
**Expected:** p95 < 2s, error rate < 5%, no crashes

#### 4. Spike Test (Sudden Surge)
```bash
# 300 users, rapid ramp-up
locust -f locustfile.py --host=http://localhost:8001 --users 300 --spawn-rate 50 --run-time 5m --headless
```
**Expected:** System remains stable, graceful degradation

#### 5. Soak Test (Endurance)
```bash
# 50 users, 2 hours
locust -f locustfile.py --host=http://localhost:8001 --users 50 --spawn-rate 5 --run-time 2h --headless
```
**Expected:** No memory leaks, stable performance

### Performance Targets

| Metric | Target | Good | Acceptable | Critical |
|--------|--------|------|------------|----------|
| Response Time (p50) | < 200ms | < 200ms | < 500ms | > 1s |
| Response Time (p95) | < 500ms | < 500ms | < 1s | > 2s |
| Response Time (p99) | < 1s | < 1s | < 2s | > 5s |
| Error Rate | < 0.1% | < 1% | < 5% | > 5% |
| API Throughput | 500+ RPS | 500+ | 200+ | < 100 |
| LLM Throughput | 10+ RPS | 10+ | 5+ | < 5 |

### Expected Performance (2x H100 GPUs)

**API Endpoints:**
- Health checks: 1000+ RPS
- Knowledge base search: 500-800 RPS
- Semantic search: 200-400 RPS
- Web search: 50-100 RPS
- Database queries: 600-1000 RPS

**LLM Completions:**
- 7B model: 100+ tokens/sec, 10+ concurrent users
- 13B model: 70+ tokens/sec, 8+ concurrent users
- 34B model: 50+ tokens/sec, 5+ concurrent users
- 70B model: 30+ tokens/sec, 3+ concurrent users

---

## Installation Guide

### System Requirements

**Systemd Services:**
- RHEL 9.4 or compatible
- Root access
- Docker & Docker Compose installed
- AI Platform deployed at `/opt/ai_platform`

**Grafana Dashboards:**
- Grafana 8.0+
- Prometheus configured
- GPU exporters (for GPU dashboard)

**Load Testing:**
- Python 3.8+
- Apache Bench (`httpd-tools` package)
- Network access to AI Platform

### Quick Setup

```bash
# 1. Install systemd services
cd /opt/ai_platform/systemd
sudo ./install-systemd.sh

# 2. Verify Grafana dashboards (auto-loaded)
# Access: http://localhost:3000
# Check: Dashboards → Browse → AI Platform folder

# 3. Install load testing dependencies
cd /opt/ai_platform/load-tests
pip install -r requirements.txt

# 4. Run smoke test
./test-api-endpoints.sh
```

---

## Directory Structure

```
ai_platform/
├── systemd/
│   ├── ai-platform.service
│   ├── ai-platform-backup.service
│   ├── ai-platform-backup.timer
│   ├── ai-platform-healthcheck.service
│   ├── ai-platform-healthcheck.timer
│   └── install-systemd.sh
│
├── config/
│   └── grafana/
│       ├── dashboards/
│       │   ├── dashboard-provisioning.yaml
│       │   ├── ai-platform-overview.json
│       │   └── gpu-monitoring.json
│       └── datasources/
│           └── prometheus.yaml
│
└── load-tests/
    ├── test-api-endpoints.sh
    ├── locustfile.py
    ├── requirements.txt
    └── README.md
```

---

## Complete Package Summary

### All Files Created

**Production Deployment (6 files):**
- ✅ docker-compose.production.yml
- ✅ .env.production.example
- ✅ deploy-rhel-production.sh
- ✅ PRODUCTION_DEPLOYMENT.md
- ✅ DEPLOYMENT_PACKAGE_SUMMARY.md
- ✅ config/nginx/nginx.conf

**Systemd Services (6 files):**
- ✅ ai-platform.service
- ✅ ai-platform-backup.service & timer
- ✅ ai-platform-healthcheck.service & timer
- ✅ install-systemd.sh

**Grafana Dashboards (4 files):**
- ✅ ai-platform-overview.json
- ✅ gpu-monitoring.json
- ✅ dashboard-provisioning.yaml
- ✅ datasources/prometheus.yaml

**Load Testing (4 files):**
- ✅ test-api-endpoints.sh
- ✅ locustfile.py
- ✅ requirements.txt
- ✅ README.md

**Total:** 20 additional resource files

---

## Next Steps

1. **Install Systemd Services**
   ```bash
   cd systemd && sudo ./install-systemd.sh
   ```

2. **Configure Monitoring Alerts**
   - Access Grafana
   - Set up alert rules
   - Configure notification channels

3. **Run Load Tests**
   ```bash
   cd load-tests
   ./test-api-endpoints.sh  # Quick test
   locust -f locustfile.py  # Comprehensive test
   ```

4. **Verify Auto-Start**
   ```bash
   sudo reboot
   # After reboot
   systemctl status ai-platform
   ```

5. **Schedule Regular Testing**
   - Add load tests to CI/CD
   - Run weekly performance tests
   - Monitor and compare trends

---

## Support & Documentation

- **Systemd**: See `systemd/install-systemd.sh` output for commands
- **Grafana**: Access http://localhost:3000 and browse dashboards
- **Load Testing**: See `load-tests/README.md` for complete guide
- **Production Deployment**: See `PRODUCTION_DEPLOYMENT.md`

---

## Summary

All additional resources are now ready for production use:

| Resource | Status | Ready for |
|----------|--------|-----------|
| Systemd Services | ✅ Complete | Auto-start & Management |
| Grafana Dashboards | ✅ Complete | Monitoring & Alerts |
| Load Testing Scripts | ✅ Complete | Performance Validation |

**Total Package Size:** ~3 GB (including Docker images)  
**Setup Time:** ~15 minutes (for additional resources)  
**Status:** Production Ready ✅

---

**Version:** 2.0.0  
**Last Updated:** 2025-10-29  
**Created By:** AI Platform DevOps Team
