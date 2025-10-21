#!/bin/bash
set -e

# AI Platform Production Deployment Script for RHEL 9.4 with NVIDIA GPU
# Target: Red Hat Enterprise Linux 9.4 (Plow) with 2x NVIDIA H100L 94GB
# Usage: sudo ./deploy-rhel-production.sh [start|stop|restart|status|verify]

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Project name
PROJECT_NAME="ai-platform-production"

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo -e "\n${MAGENTA}[====== $1 ======]${NC}\n"
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Detect OS
detect_os() {
    log_info "Detecting operating system..."

    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS_NAME=$NAME
        OS_VERSION=$VERSION_ID

        if [[ "$OS_NAME" == *"Red Hat"* ]] && [[ "$OS_VERSION" == "9.4" ]]; then
            log_success "Detected: $OS_NAME $OS_VERSION"
        else
            log_warning "This script is optimized for RHEL 9.4, detected: $OS_NAME $OS_VERSION"
            read -p "Continue anyway? (yes/no): " confirm
            [ "$confirm" != "yes" ] && exit 1
        fi
    else
        log_error "Cannot detect OS version"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log_section "Checking Prerequisites"

    local errors=0

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        log_info "Install with: sudo dnf install -y docker-ce docker-ce-cli containerd.io"
        errors=$((errors + 1))
    else
        log_success "Docker installed: $(docker --version)"
    fi

    # Check Docker Compose
    if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        errors=$((errors + 1))
    else
        log_success "Docker Compose installed: $(docker compose version 2>/dev/null || docker-compose --version)"
    fi

    # Check nvidia-smi
    if ! command -v nvidia-smi &> /dev/null; then
        log_error "NVIDIA drivers not installed"
        log_info "Install NVIDIA drivers before continuing"
        errors=$((errors + 1))
    else
        log_success "NVIDIA drivers installed"
        nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader
    fi

    # Check nvidia-container-toolkit
    if ! docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubi9 nvidia-smi &> /dev/null; then
        log_error "nvidia-container-toolkit not properly configured"
        log_info "Install with: sudo dnf install -y nvidia-container-toolkit"
        errors=$((errors + 1))
    else
        log_success "nvidia-container-toolkit configured"
    fi

    # Check GPU count
    gpu_count=$(nvidia-smi --query-gpu=count --format=csv,noheader | head -1)
    if [ "$gpu_count" -lt 2 ]; then
        log_warning "Expected 2 GPUs, found: $gpu_count"
    else
        log_success "Found $gpu_count GPUs"
    fi

    # Check available disk space (need at least 100GB)
    available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -lt 100 ]; then
        log_error "Insufficient disk space. Need 100GB, available: ${available_space}GB"
        errors=$((errors + 1))
    else
        log_success "Sufficient disk space: ${available_space}GB"
    fi

    # Check memory (need at least 32GB)
    total_mem=$(free -g | awk 'NR==2 {print $2}')
    if [ "$total_mem" -lt 32 ]; then
        log_warning "System memory is below 32GB, available: ${total_mem}GB"
    else
        log_success "Sufficient memory: ${total_mem}GB"
    fi

    if [ $errors -gt 0 ]; then
        log_error "Prerequisites check failed with $errors errors"
        exit 1
    fi

    log_success "All prerequisites met"
}

# Verify GPU configuration
verify_gpu() {
    log_section "Verifying GPU Configuration"

    # Check GPU details
    log_info "GPU Information:"
    nvidia-smi --query-gpu=index,name,driver_version,memory.total,compute_cap --format=table

    # Check CUDA version
    if command -v nvcc &> /dev/null; then
        log_info "CUDA Version: $(nvcc --version | grep release | awk '{print $5}' | cut -c2-)"
    fi

    # Test GPU in Docker
    log_info "Testing GPU access in Docker container..."
    if docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubi9 nvidia-smi &> /dev/null; then
        log_success "GPU accessible from Docker containers"
    else
        log_error "Cannot access GPU from Docker containers"
        exit 1
    fi
}

# Configure firewall
configure_firewall() {
    log_section "Configuring Firewall"

    if command -v firewall-cmd &> /dev/null; then
        log_info "Configuring firewalld..."

        # Check if firewalld is running
        if systemctl is-active --quiet firewalld; then
            # Add ports
            firewall-cmd --permanent --add-port=8501/tcp  # Web UI
            firewall-cmd --permanent --add-port=8000/tcp  # Agent Service
            firewall-cmd --permanent --add-port=8001/tcp  # MCP Server
            firewall-cmd --permanent --add-port=4000/tcp  # LiteLLM
            firewall-cmd --permanent --add-port=3000/tcp  # Grafana
            firewall-cmd --permanent --add-port=9090/tcp  # Prometheus
            firewall-cmd --reload

            log_success "Firewall configured"
        else
            log_warning "firewalld is not running"
        fi
    else
        log_info "firewalld not found, skipping firewall configuration"
    fi
}

# Configure SELinux
configure_selinux() {
    log_section "Configuring SELinux"

    if command -v getenforce &> /dev/null; then
        selinux_status=$(getenforce)
        log_info "SELinux status: $selinux_status"

        if [ "$selinux_status" = "Enforcing" ]; then
            log_info "Setting SELinux booleans for Docker..."
            setsebool -P container_manage_cgroup on || log_warning "Failed to set container_manage_cgroup"

            # Set proper context for volumes
            chcon -Rt svirt_sandbox_file_t ./data || log_warning "Failed to set SELinux context for data directory"

            log_success "SELinux configured for containers"
        fi
    fi
}

# Generate production .env file
generate_production_env() {
    if [ -f .env ]; then
        log_warning ".env file already exists, skipping generation"
        return
    fi

    log_section "Generating Production Environment Configuration"

    # Generate secure passwords
    POSTGRES_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    REDIS_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    RABBITMQ_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    GRAFANA_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    LITELLM_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)

    # Prompt for API keys
    read -p "Enter OpenAI API Key (or press Enter to skip): " OPENAI_KEY
    read -p "Enter Anthropic API Key (or press Enter to skip): " ANTHROPIC_KEY
    read -p "Enter SMTP server (or press Enter to skip): " SMTP_SERVER_INPUT

    cat > .env << EOF
# Production Environment Configuration for RHEL 9.4
# Generated on: $(date)
# WARNING: Keep this file secure and never commit to version control

# ====================
# API Keys
# ====================
OPENAI_API_KEY=${OPENAI_KEY:-sk-your-openai-api-key}
ANTHROPIC_API_KEY=${ANTHROPIC_KEY:-sk-ant-your-anthropic-api-key}

# ====================
# Database Configuration
# ====================
POSTGRES_USER=ai_admin
POSTGRES_PASSWORD=${POSTGRES_PASS}
POSTGRES_DB=ai_platform_prod

# ====================
# Redis Configuration
# ====================
REDIS_PASSWORD=${REDIS_PASS}

# ====================
# RabbitMQ Configuration
# ====================
RABBITMQ_DEFAULT_USER=ai_admin
RABBITMQ_DEFAULT_PASS=${RABBITMQ_PASS}

# ====================
# Application Settings
# ====================
ENVIRONMENT=production
LOG_LEVEL=info
MAX_CONCURRENT_REQUESTS=100
DEBUG=false

# ====================
# GPU Configuration
# ====================
ENABLE_GPU=true
GPU_MEMORY_UTILIZATION=0.9
NVIDIA_VISIBLE_DEVICES=0,1
CUDA_VISIBLE_DEVICES=0,1

# ====================
# Security
# ====================
LITELLM_MASTER_KEY=${LITELLM_KEY}
GRAFANA_ADMIN_PASSWORD=${GRAFANA_PASS}

# ====================
# SMTP Configuration (Optional)
# ====================
SMTP_SERVER=${SMTP_SERVER_INPUT:-}
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=noreply@ai-platform.local
SMTP_ENABLED=${SMTP_SERVER_INPUT:+true}

# ====================
# Monitoring
# ====================
GRAFANA_ROOT_URL=http://localhost:3000
PROMETHEUS_RETENTION=30d

# ====================
# Performance Tuning
# ====================
POSTGRES_SHARED_BUFFERS=2GB
POSTGRES_EFFECTIVE_CACHE_SIZE=6GB
REDIS_MAXMEMORY=3gb
EOF

    # Secure the .env file
    chmod 600 .env
    chown root:root .env

    log_success ".env file created with secure passwords"
    log_warning "Passwords saved to .env - keep this file secure!"

    # Save passwords to separate file for admin reference
    cat > .env.passwords << EOF
# AI Platform Production Passwords
# Generated on: $(date)
# KEEP THIS FILE SECURE AND IN A SAFE LOCATION

PostgreSQL Password: ${POSTGRES_PASS}
Redis Password: ${REDIS_PASS}
RabbitMQ Password: ${RABBITMQ_PASS}
Grafana Admin Password: ${GRAFANA_PASS}
LiteLLM Master Key: ${LITELLM_KEY}
EOF

    chmod 600 .env.passwords
    log_info "Passwords also saved to .env.passwords for your reference"
}

# Setup directories
setup_directories() {
    log_section "Setting Up Directory Structure"

    mkdir -p data/{postgres,redis,rabbitmq,qdrant,prometheus,grafana,models}
    mkdir -p logs/{mcp-server,agent-service,web-ui,litellm}
    mkdir -p backups/{database,config}
    mkdir -p config/ssl

    # Set proper permissions
    chmod -R 755 data logs backups config

    log_success "Directory structure created"
}

# Pull and build images
build_services() {
    log_section "Building Docker Images"

    # Pull base images
    log_info "Pulling base images..."
    docker compose pull postgres redis qdrant rabbitmq prometheus grafana

    # Build custom services
    log_info "Building application services..."
    docker compose build --no-cache mcp-server agent-service web-ui

    log_success "Docker images ready"
}

# Start services with GPU
start_services() {
    log_section "Starting Services with GPU Support"

    # Start infrastructure layer
    log_info "Starting infrastructure services..."
    docker compose up -d postgres redis qdrant rabbitmq

    log_info "Waiting for infrastructure to be ready..."
    sleep 15

    # Initialize database
    log_info "Initializing database..."
    ./scripts/init-db.sh init || log_warning "Database initialization may need manual retry"

    # Start LLM services with GPU
    log_info "Starting LLM services with GPU acceleration..."
    docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d ollama litellm

    log_info "Waiting for LLM services..."
    sleep 20

    # Pull Ollama models optimized for H100L
    log_info "Pulling optimized Ollama models for H100L..."
    docker exec ai-ollama ollama pull llama3.1:70b || log_warning "Model download failed, can retry later"
    docker exec ai-ollama ollama pull qwen2.5:32b || log_warning "Model download failed, can retry later"

    # Start application services
    log_info "Starting application services..."
    docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d mcp-server agent-service web-ui

    # Start monitoring
    log_info "Starting monitoring services..."
    docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d prometheus grafana

    log_success "All services started"
}

# Wait for services to be healthy
wait_for_health() {
    log_section "Waiting for Services to Become Healthy"

    local max_attempts=60
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        attempt=$((attempt + 1))

        local healthy=0
        local total=6

        # Check each service
        curl -sf http://localhost:6333/health | grep -q "ok" && healthy=$((healthy + 1))
        curl -sf http://localhost:4000/health/readiness && healthy=$((healthy + 1))
        curl -sf http://localhost:8001/health && healthy=$((healthy + 1))
        curl -sf http://localhost:8000/health && healthy=$((healthy + 1))
        curl -sf http://localhost:8501 &> /dev/null && healthy=$((healthy + 1))
        curl -sf http://localhost:9090/-/healthy && healthy=$((healthy + 1))

        if [ $healthy -eq $total ]; then
            log_success "All services are healthy"
            return 0
        fi

        echo -n "."
        sleep 5
    done

    log_warning "Some services may not be fully healthy after ${max_attempts} attempts"
}

# Setup automated backups
setup_backups() {
    log_section "Setting Up Automated Backups"

    # Create backup script
    cat > /usr/local/bin/ai-platform-backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/ai_platform/backups/database"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.sql.gz"

mkdir -p ${BACKUP_DIR}

# Backup database
docker exec ai-postgres pg_dump -U ai_admin ai_platform_prod | gzip > ${BACKUP_FILE}

# Keep only last 30 days of backups
find ${BACKUP_DIR} -name "backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_FILE}"
EOF

    chmod +x /usr/local/bin/ai-platform-backup.sh

    # Add to crontab (daily at 2 AM)
    (crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/ai-platform-backup.sh >> /var/log/ai-platform-backup.log 2>&1") | crontab -

    log_success "Automated backups configured (daily at 2 AM)"
}

# Show status
show_status() {
    log_section "System Status"

    echo -e "${BLUE}Service Status:${NC}"
    docker compose ps

    echo -e "\n${BLUE}GPU Status:${NC}"
    nvidia-smi --query-gpu=index,name,utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu --format=table

    echo -e "\n${BLUE}Resource Usage:${NC}"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

    echo -e "\n${BLUE}Access URLs:${NC}"
    echo "  🌐 Web UI:        http://$(hostname -I | awk '{print $1}'):8501"
    echo "  📊 Grafana:       http://$(hostname -I | awk '{print $1}'):3000"
    echo "  📈 Prometheus:    http://$(hostname -I | awk '{print $1}'):9090"
    echo "  🐰 RabbitMQ:      http://$(hostname -I | awk '{print $1}'):15672"
    echo "  🔧 LiteLLM:       http://$(hostname -I | awk '{print $1}'):4000"

    echo -e "\n${BLUE}Credentials:${NC}"
    echo "  See .env.passwords file for all credentials"
}

# Run production tests
run_production_tests() {
    log_section "Running Production Tests"

    source .env

    local failed=0

    # Test GPU access
    echo -n "Testing GPU in Ollama container... "
    if docker exec ai-ollama nvidia-smi &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        failed=$((failed + 1))
    fi

    # Test services
    echo -n "Testing PostgreSQL... "
    docker exec ai-postgres pg_isready -U ai_admin &> /dev/null && echo -e "${GREEN}✓${NC}" || { echo -e "${RED}✗${NC}"; failed=$((failed + 1)); }

    echo -n "Testing Redis... "
    docker exec ai-redis redis-cli -a "$REDIS_PASSWORD" ping 2>/dev/null | grep -q PONG && echo -e "${GREEN}✓${NC}" || { echo -e "${RED}✗${NC}"; failed=$((failed + 1)); }

    echo -n "Testing Qdrant... "
    curl -sf http://localhost:6333/health | grep -q ok && echo -e "${GREEN}✓${NC}" || { echo -e "${RED}✗${NC}"; failed=$((failed + 1)); }

    echo -n "Testing LiteLLM... "
    curl -sf http://localhost:4000/health/readiness && echo -e "${GREEN}✓${NC}" || { echo -e "${RED}✗${NC}"; failed=$((failed + 1)); }

    echo -n "Testing MCP Server... "
    curl -sf http://localhost:8001/health && echo -e "${GREEN}✓${NC}" || { echo -e "${RED}✗${NC}"; failed=$((failed + 1)); }

    echo -n "Testing Agent Service... "
    curl -sf http://localhost:8000/health && echo -e "${GREEN}✓${NC}" || { echo -e "${RED}✗${NC}"; failed=$((failed + 1)); }

    if [ $failed -eq 0 ]; then
        log_success "All tests passed"
    else
        log_warning "$failed tests failed"
    fi
}

# Stop services
stop_services() {
    log_info "Stopping all services..."
    docker compose -f docker-compose.yml -f docker-compose.gpu.yml down
    log_success "Services stopped"
}

# Restart services
restart_services() {
    log_info "Restarting services..."
    docker compose -f docker-compose.yml -f docker-compose.gpu.yml restart
    log_success "Services restarted"
}

# Main function
main() {
    case "${1:-start}" in
        start)
            echo -e "${MAGENTA}"
            echo "╔════════════════════════════════════════════════════════╗"
            echo "║  AI Platform - Production Deployment for RHEL 9.4     ║"
            echo "║  Target: 2x NVIDIA H100L 94GB GPUs                    ║"
            echo "╚════════════════════════════════════════════════════════╝"
            echo -e "${NC}"

            check_root
            detect_os
            check_prerequisites
            verify_gpu
            configure_firewall
            configure_selinux
            generate_production_env
            setup_directories
            build_services
            start_services
            wait_for_health
            setup_backups
            run_production_tests
            show_status

            echo ""
            log_success "🎉 Production deployment complete!"
            log_info "Access the Web UI at: http://$(hostname -I | awk '{print $1}'):8501"
            log_warning "Review .env.passwords for all credentials"
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        verify)
            verify_gpu
            run_production_tests
            ;;
        *)
            echo "Usage: $0 {start|stop|restart|status|verify}"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
