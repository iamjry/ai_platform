# AI Platform - Load Testing Guide

Comprehensive load testing suite for the AI Platform.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Test Scripts](#test-scripts)
- [Running Tests](#running-tests)
- [Interpreting Results](#interpreting-results)
- [Best Practices](#best-practices)

---

## Overview

This directory contains load testing scripts to validate the AI Platform's performance under various load conditions.

### Available Test Scripts

| Script | Tool | Purpose |
|--------|------|---------|
| `test-api-endpoints.sh` | Apache Bench | Quick API endpoint testing |
| `locustfile.py` | Locust | Comprehensive load testing with UI |

---

## Prerequisites

### Install Testing Tools

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Apache Bench (for test-api-endpoints.sh)
# Ubuntu/Debian:
sudo apt-get install apache2-utils

# macOS:
brew install httpd

# RHEL/CentOS:
sudo dnf install httpd-tools
```

### Verify Installation

```bash
# Check Apache Bench
ab -V

# Check Locust
locust --version

# Check jq (optional, for JSON parsing)
jq --version
```

---

## Test Scripts

### 1. Apache Bench Tests (`test-api-endpoints.sh`)

**Purpose:** Quick validation of API endpoints

**Features:**
- Tests 6 core API endpoints
- Concurrent user simulation
- Response time analysis
- Success rate metrics

**Usage:**

```bash
# Basic usage
./test-api-endpoints.sh

# Custom configuration
BASE_URL=http://production.example.com:8001 \
CONCURRENT_USERS=50 \
TOTAL_REQUESTS=5000 \
./test-api-endpoints.sh
```

**Configuration Options:**

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `http://localhost:8001` | API base URL |
| `CONCURRENT_USERS` | `10` | Number of concurrent users |
| `TOTAL_REQUESTS` | `1000` | Total requests to send |
| `TEST_DURATION` | `60` | Test duration in seconds |

### 2. Locust Tests (`locustfile.py`)

**Purpose:** Comprehensive load testing with Web UI

**Features:**
- Multiple user classes (AI Tools, LLM, Mixed)
- Realistic workload simulation
- Real-time metrics dashboard
- Custom load shapes (ramp-up/ramp-down)
- Detailed response time analysis

**Usage:**

```bash
# Start with Web UI (recommended for initial testing)
locust -f locustfile.py --host=http://localhost:8001

# Access Web UI at: http://localhost:8089

# Headless mode (for CI/CD)
locust -f locustfile.py \
       --host=http://localhost:8001 \
       --users 100 \
       --spawn-rate 10 \
       --run-time 10m \
       --headless

# Export results to CSV
locust -f locustfile.py \
       --host=http://localhost:8001 \
       --users 200 \
       --spawn-rate 20 \
       --run-time 5m \
       --headless \
       --csv=results/loadtest
```

**User Classes:**

- `AIToolUser`: Simulates tool usage (search, query, analyze)
- `LLMUser`: Simulates LLM chat completions
- `MixedWorkloadUser`: Realistic mixed workload

**Load Shapes:**

- `StepLoadShape`: Gradual ramp-up (10 → 50 → 100 → 200 users)

---

## Running Tests

### Pre-Test Checklist

- [ ] AI Platform is deployed and running
- [ ] All services are healthy (`docker compose ps`)
- [ ] Database is populated with test data
- [ ] GPU is functioning (if testing LLM endpoints)
- [ ] Monitoring is enabled (Grafana)

### Test Scenarios

#### 1. Smoke Test (Quick Validation)

```bash
# Test with low load
BASE_URL=http://localhost:8001 \
CONCURRENT_USERS=5 \
TOTAL_REQUESTS=100 \
./test-api-endpoints.sh
```

**Expected:**
- All endpoints return 200 OK
- Response time < 500ms
- Error rate < 1%

#### 2. Load Test (Normal Traffic)

```bash
# Simulate normal production traffic
locust -f locustfile.py \
       --host=http://localhost:8001 \
       --users 50 \
       --spawn-rate 5 \
       --run-time 10m \
       --headless
```

**Expected:**
- Response time p95 < 1s
- Error rate < 2%
- System resources < 70%

#### 3. Stress Test (Peak Traffic)

```bash
# Simulate peak traffic
locust -f locustfile.py \
       --host=http://localhost:8001 \
       --users 200 \
       --spawn-rate 20 \
       --run-time 15m \
       --headless
```

**Expected:**
- Response time p95 < 2s
- Error rate < 5%
- System resources < 85%
- No service crashes

#### 4. Spike Test (Sudden Traffic Surge)

```bash
# Rapid ramp-up to test elasticity
locust -f locustfile.py \
       --host=http://localhost:8001 \
       --users 300 \
       --spawn-rate 50 \
       --run-time 5m \
       --headless
```

**Expected:**
- System remains stable
- No cascading failures
- Graceful degradation if needed

#### 5. Soak Test (Endurance)

```bash
# Long-running test to detect memory leaks
locust -f locustfile.py \
       --host=http://localhost:8001 \
       --users 50 \
       --spawn-rate 5 \
       --run-time 2h \
       --headless
```

**Expected:**
- Memory usage stable over time
- No gradual performance degradation
- No service crashes

---

## Interpreting Results

### Key Metrics

#### Response Time

- **p50 (median)**: 50% of requests complete in this time
- **p95**: 95% of requests complete in this time
- **p99**: 99% of requests complete in this time

**Targets:**
- p50 < 200ms ✅ Excellent
- p95 < 500ms ✅ Good
- p99 < 1s ✅ Acceptable
- p99 > 2s ⚠️ Investigate

#### Error Rate

**Formula:** `(Failed Requests / Total Requests) * 100`

**Targets:**
- < 0.1% ✅ Excellent
- < 1% ✅ Good
- < 5% ⚠️ Investigate
- > 5% ❌ Critical

#### Throughput

**Metric:** Requests per second (RPS)

**Expected (with 2x H100 GPUs):**
- API endpoints: 500-1000 RPS
- LLM completions: 10-50 RPS (depends on model)
- Search operations: 200-500 RPS

### Sample Results Analysis

```
Total Requests: 10,000
Successful: 9,950
Failed: 50
Error Rate: 0.5% ✅

Response Times:
- p50: 180ms ✅
- p95: 450ms ✅
- p99: 850ms ✅
- Max: 2.1s

Throughput:
- Average: 833 RPS ✅
- Peak: 1,100 RPS

Status: PASS
```

---

## Best Practices

### Before Testing

1. **Baseline Performance**
   - Run tests on a clean system
   - Document baseline metrics
   - Compare future tests against baseline

2. **Environment Consistency**
   - Use same hardware configuration
   - Same software versions
   - Consistent network conditions

3. **Test Data Preparation**
   - Populate database with realistic data
   - Use varied test queries
   - Ensure data diversity

### During Testing

1. **Monitor System Resources**
   - CPU utilization
   - Memory usage
   - GPU utilization & temperature
   - Disk I/O
   - Network bandwidth

2. **Watch for Issues**
   - Memory leaks
   - Connection pool exhaustion
   - Database deadlocks
   - Rate limiting triggers

3. **Document Observations**
   - Note any anomalies
   - Record error patterns
   - Capture system metrics

### After Testing

1. **Analyze Results**
   - Compare against targets
   - Identify bottlenecks
   - Prioritize optimization

2. **Generate Reports**
   - Summary metrics
   - Graphs and charts
   - Recommendations

3. **Archive Results**
   - Save for historical comparison
   - Tag with version number
   - Include system configuration

---

## Troubleshooting

### High Error Rate

**Possible Causes:**
- Service timeout
- Connection pool exhaustion
- Rate limiting

**Solutions:**
- Increase timeout values
- Scale service replicas
- Adjust rate limits

### High Response Time

**Possible Causes:**
- CPU bottleneck
- Database slow queries
- Network latency

**Solutions:**
- Scale horizontally
- Optimize database queries
- Add caching layer

### GPU Not Utilized

**Possible Causes:**
- Model not using GPU
- GPU memory full
- Driver issues

**Solutions:**
- Check CUDA_VISIBLE_DEVICES
- Monitor GPU memory
- Restart Ollama service

---

## Advanced Testing

### Custom Scenarios

Create custom test scenarios by modifying `locustfile.py`:

```python
class CustomUser(HttpUser):
    @task
    def custom_workflow(self):
        # Search
        self.client.post("/tools/search_knowledge_base", ...)

        # Analyze results
        self.client.post("/tools/analyze_data", ...)

        # Create report
        self.client.post("/tools/generate_report", ...)
```

### Distributed Testing

For very high load, distribute across multiple machines:

```bash
# Master node
locust -f locustfile.py --master --host=http://production.com

# Worker nodes (on separate machines)
locust -f locustfile.py --worker --master-host=<master-ip>
```

---

## CI/CD Integration

### Example GitHub Actions Workflow

```yaml
name: Load Test

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Install dependencies
        run: pip install -r load-tests/requirements.txt

      - name: Run load test
        run: |
          cd load-tests
          locust -f locustfile.py \
                 --host=${{ secrets.API_HOST }} \
                 --users 100 \
                 --spawn-rate 10 \
                 --run-time 5m \
                 --headless \
                 --csv=results/loadtest

      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: load-test-results
          path: load-tests/results/
```

---

## Support

For issues or questions:
- Check TROUBLESHOOTING_GUIDE.md
- Review Grafana dashboards
- Examine service logs

---

**Happy Testing!** 🚀
