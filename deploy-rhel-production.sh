#!/bin/bash

###############################################################################
# AI Platform - RHEL Production Deployment Script
# Red Hat Enterprise Linux 9.4 with 2x NVIDIA H100 GPUs
#
# This script automates the deployment of the AI Platform in a production
# environment with GPU acceleration support.
#
# Prerequisites:
# - RHEL 9.4 with kernel 5.14+
# - 2x NVIDIA H100 GPUs
# - NVIDIA Driver 535+ installed
# - CUDA Toolkit 12.0+ installed
# - Docker 24.0+ and Docker Compose 2.20+
# - nvidia-container-toolkit installed
#
# Usage:
#   sudo ./deploy-rhel-production.sh [command]
#
# Commands:
#   check       - Check system prerequisites
#   install     - Install required dependencies
#   deploy      - Deploy the AI Platform
#   start       - Start all services
#   stop        - Stop all services
#   restart     - Restart all services
#   status      - Check service status
#   logs        - View service logs
#   backup      - Create database backup
#   update      - Update services to latest version
#   cleanup     - Clean up old containers and images
#
###############################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.production.yml"
ENV_FILE="${SCRIPT_DIR}/.env"
ENV_EXAMPLE="${SCRIPT_DIR}/.env.production.example"
LOG_FILE="${SCRIPT_DIR}/deployment.log"

# System requirements
MIN_MEMORY_GB=32
MIN_DISK_GB=100
MIN_CPUS=8
REQUIRED_GPU_COUNT=2

###############################################################################
# Utility Functions
###############################################################################

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "${LOG_FILE}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $*" | tee -a "${LOG_FILE}"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $*" | tee -a "${LOG_FILE}"
}

log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $*" | tee -a "${LOG_FILE}"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

###############################################################################
# System Checks
###############################################################################

check_os() {
    log "Checking operating system..."

    if [[ ! -f /etc/redhat-release ]]; then
        log_error "This script is designed for Red Hat Enterprise Linux"
        exit 1
    fi

    OS_VERSION=$(cat /etc/redhat-release)
    log "Operating System: ${OS_VERSION}"

    if [[ ! "$OS_VERSION" =~ "Red Hat Enterprise Linux release 9" ]]; then
        log_warn "This script is optimized for RHEL 9.4. Your version may not be fully supported."
    fi
}

check_resources() {
    log "Checking system resources..."

    # Check CPU cores
    CPU_CORES=$(nproc)
    log_info "CPU Cores: ${CPU_CORES}"
    if [[ ${CPU_CORES} -lt ${MIN_CPUS} ]]; then
        log_error "Insufficient CPU cores. Required: ${MIN_CPUS}, Available: ${CPU_CORES}"
        exit 1
    fi

    # Check memory
    TOTAL_MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
    log_info "Total Memory: ${TOTAL_MEMORY_GB}GB"
    if [[ ${TOTAL_MEMORY_GB} -lt ${MIN_MEMORY_GB} ]]; then
        log_error "Insufficient memory. Required: ${MIN_MEMORY_GB}GB, Available: ${TOTAL_MEMORY_GB}GB"
        exit 1
    fi

    # Check disk space
    AVAILABLE_DISK_GB=$(df -BG "${SCRIPT_DIR}" | awk 'NR==2 {print $4}' | sed 's/G//')
    log_info "Available Disk Space: ${AVAILABLE_DISK_GB}GB"
    if [[ ${AVAILABLE_DISK_GB} -lt ${MIN_DISK_GB} ]]; then
        log_error "Insufficient disk space. Required: ${MIN_DISK_GB}GB, Available: ${AVAILABLE_DISK_GB}GB"
        exit 1
    fi
}

check_nvidia_driver() {
    log "Checking NVIDIA GPU drivers..."

    if ! command -v nvidia-smi &> /dev/null; then
        log_error "nvidia-smi not found. Please install NVIDIA drivers."
        log_error "Installation: sudo dnf install -y nvidia-driver nvidia-settings"
        exit 1
    fi

    DRIVER_VERSION=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -n 1)
    log "NVIDIA Driver Version: ${DRIVER_VERSION}"

    # Check GPU count
    GPU_COUNT=$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l)
    log_info "Detected GPUs: ${GPU_COUNT}"

    if [[ ${GPU_COUNT} -lt ${REQUIRED_GPU_COUNT} ]]; then
        log_error "Insufficient GPUs. Required: ${REQUIRED_GPU_COUNT}, Detected: ${GPU_COUNT}"
        exit 1
    fi

    # Display GPU information
    log "GPU Information:"
    nvidia-smi --query-gpu=index,name,memory.total,memory.free --format=csv,noheader | while read line; do
        log_info "  GPU ${line}"
    done
}

check_cuda() {
    log "Checking CUDA installation..."

    if ! command -v nvcc &> /dev/null; then
        log_error "CUDA not found. Please install CUDA Toolkit 12.0+"
        log_error "Installation guide: https://developer.nvidia.com/cuda-downloads"
        exit 1
    fi

    CUDA_VERSION=$(nvcc --version | grep "release" | sed -n 's/.*release \([0-9\.]*\).*/\1/p')
    log "CUDA Version: ${CUDA_VERSION}"
}

check_docker() {
    log "Checking Docker installation..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Run './deploy-rhel-production.sh install' first"
        exit 1
    fi

    DOCKER_VERSION=$(docker --version | sed -n 's/Docker version \([^,]*\).*/\1/p')
    log "Docker Version: ${DOCKER_VERSION}"

    if ! docker ps &> /dev/null; then
        log_error "Docker daemon is not running"
        systemctl start docker
        sleep 5
    fi
}

check_docker_compose() {
    log "Checking Docker Compose installation..."

    if ! command -v docker compose version &> /dev/null; then
        log_error "Docker Compose not found. Run './deploy-rhel-production.sh install' first"
        exit 1
    fi

    COMPOSE_VERSION=$(docker compose version | sed -n 's/Docker Compose version \(v[0-9\.]*\).*/\1/p')
    log "Docker Compose Version: ${COMPOSE_VERSION}"
}

check_nvidia_docker() {
    log "Checking nvidia-container-toolkit..."

    if ! docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubi9 nvidia-smi &> /dev/null; then
        log_error "nvidia-container-toolkit not working properly"
        log_error "Run './deploy-rhel-production.sh install' to install it"
        exit 1
    fi

    log "nvidia-container-toolkit is working correctly"
}

check_firewall() {
    log "Checking firewall configuration..."

    if systemctl is-active --quiet firewalld; then
        log_info "Firewalld is active"

        # Check required ports
        REQUIRED_PORTS=(80 443 8501 8000 8001 4000 3000 9090)
        for port in "${REQUIRED_PORTS[@]}"; do
            if ! firewall-cmd --list-ports | grep -q "${port}/tcp"; then
                log_warn "Port ${port}/tcp is not open in firewall"
            fi
        done
    else
        log_warn "Firewalld is not active"
    fi
}

check_selinux() {
    log "Checking SELinux status..."

    SELINUX_STATUS=$(getenforce)
    log_info "SELinux Status: ${SELINUX_STATUS}"

    if [[ "${SELINUX_STATUS}" == "Enforcing" ]]; then
        log_warn "SELinux is in enforcing mode. You may need to configure policies for Docker."
    fi
}

###############################################################################
# Installation Functions
###############################################################################

install_docker() {
    log "Installing Docker..."

    # Add Docker repository
    dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo

    # Install Docker
    dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin

    # Start and enable Docker
    systemctl start docker
    systemctl enable docker

    log "Docker installed successfully"
}

install_docker_compose() {
    log "Installing Docker Compose..."

    # Docker Compose is included in docker-compose-plugin
    dnf install -y docker-compose-plugin

    log "Docker Compose installed successfully"
}

install_nvidia_container_toolkit() {
    log "Installing nvidia-container-toolkit..."

    # Add NVIDIA repository
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
    curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.repo | \
        tee /etc/yum.repos.d/nvidia-container-toolkit.repo

    # Install nvidia-container-toolkit
    dnf install -y nvidia-container-toolkit

    # Configure Docker to use NVIDIA runtime
    nvidia-ctk runtime configure --runtime=docker

    # Restart Docker
    systemctl restart docker

    # Test GPU access
    if docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubi9 nvidia-smi; then
        log "nvidia-container-toolkit installed and configured successfully"
    else
        log_error "Failed to verify nvidia-container-toolkit installation"
        exit 1
    fi
}

configure_firewall() {
    log "Configuring firewall..."

    if systemctl is-active --quiet firewalld; then
        firewall-cmd --permanent --add-port=80/tcp
        firewall-cmd --permanent --add-port=443/tcp
        firewall-cmd --permanent --add-port=8501/tcp
        firewall-cmd --permanent --add-port=8000/tcp
        firewall-cmd --permanent --add-port=8001/tcp
        firewall-cmd --permanent --add-port=4000/tcp
        firewall-cmd --permanent --add-port=3000/tcp
        firewall-cmd --permanent --add-port=9090/tcp
        firewall-cmd --reload

        log "Firewall configured successfully"
    else
        log_warn "Firewalld is not running, skipping firewall configuration"
    fi
}

###############################################################################
# Deployment Functions
###############################################################################

prepare_environment() {
    log "Preparing environment..."

    # Create .env file if it doesn't exist
    if [[ ! -f "${ENV_FILE}" ]]; then
        if [[ -f "${ENV_EXAMPLE}" ]]; then
            log "Creating .env file from template..."
            cp "${ENV_EXAMPLE}" "${ENV_FILE}"
            log_warn "Please edit ${ENV_FILE} with your production credentials"
            log_warn "Required changes:"
            log_warn "  1. Set all API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)"
            log_warn "  2. Replace all 'CHANGE_ME_TO_SECURE_PASSWORD_*' with strong passwords"
            log_warn "  3. Configure SSL certificate paths"
            log_warn "  4. Update domain names and email addresses"
            echo ""
            read -p "Press Enter when you have configured .env file..."
        else
            log_error ".env.production.example not found"
            exit 1
        fi
    fi

    # Create necessary directories
    mkdir -p "${SCRIPT_DIR}/config/nginx/ssl"
    mkdir -p "${SCRIPT_DIR}/config/grafana/dashboards"
    mkdir -p "${SCRIPT_DIR}/config/grafana/datasources"
    mkdir -p "${SCRIPT_DIR}/backups"
    mkdir -p "${SCRIPT_DIR}/logs"

    # Set permissions
    chmod 600 "${ENV_FILE}"

    log "Environment prepared successfully"
}

pull_images() {
    log "Pulling Docker images..."
    docker compose -f "${COMPOSE_FILE}" pull
    log "Images pulled successfully"
}

build_services() {
    log "Building custom services..."
    docker compose -f "${COMPOSE_FILE}" build --no-cache
    log "Services built successfully"
}

start_services() {
    log "Starting services..."

    # Start infrastructure services first
    log_info "Starting infrastructure services..."
    docker compose -f "${COMPOSE_FILE}" up -d postgres redis qdrant rabbitmq
    sleep 15

    # Start LLM services
    log_info "Starting LLM services..."
    docker compose -f "${COMPOSE_FILE}" up -d ollama litellm
    sleep 20

    # Start application services
    log_info "Starting application services..."
    docker compose -f "${COMPOSE_FILE}" up -d mcp-server agent-service web-ui
    sleep 15

    # Start monitoring services
    log_info "Starting monitoring services..."
    docker compose -f "${COMPOSE_FILE}" up -d prometheus grafana
    sleep 10

    # Start reverse proxy
    log_info "Starting reverse proxy..."
    docker compose -f "${COMPOSE_FILE}" up -d nginx

    log "All services started successfully"
}

check_services() {
    log "Checking service health..."

    sleep 30  # Wait for services to stabilize

    # Check service status
    docker compose -f "${COMPOSE_FILE}" ps

    # Check health endpoints
    HEALTH_CHECKS=(
        "http://localhost:8001/health|MCP Server"
        "http://localhost:8002/health|Agent Service"
        "http://localhost:4000/health/readiness|LiteLLM"
        "http://localhost:9090/-/healthy|Prometheus"
    )

    for check in "${HEALTH_CHECKS[@]}"; do
        IFS='|' read -r url name <<< "$check"
        if curl -sf "${url}" > /dev/null 2>&1; then
            log "${name}: ${GREEN}✓ Healthy${NC}"
        else
            log_error "${name}: ${RED}✗ Unhealthy${NC}"
        fi
    done
}

###############################################################################
# Main Commands
###############################################################################

cmd_check() {
    log "=== Checking System Prerequisites ==="
    check_os
    check_resources
    check_nvidia_driver
    check_cuda
    check_docker || log_warn "Docker not installed"
    check_docker_compose || log_warn "Docker Compose not installed"
    check_nvidia_docker || log_warn "nvidia-container-toolkit not installed"
    check_firewall
    check_selinux
    log "=== Prerequisite Check Complete ==="
}

cmd_install() {
    check_root
    log "=== Installing Dependencies ==="

    install_docker
    install_docker_compose
    install_nvidia_container_toolkit
    configure_firewall

    log "=== Installation Complete ==="
    log "Run './deploy-rhel-production.sh check' to verify installation"
}

cmd_deploy() {
    check_root
    log "=== Deploying AI Platform (Production) ==="

    cmd_check
    prepare_environment
    pull_images
    build_services
    start_services
    check_services

    log "=== Deployment Complete ==="
    log ""
    log "Access the platform:"
    log "  Web UI: http://localhost:8501"
    log "  Grafana: http://localhost:3000 (admin/admin)"
    log "  Prometheus: http://localhost:9090"
    log ""
    log "Next steps:"
    log "  1. Configure SSL certificates for NGINX"
    log "  2. Set up automated backups (cron)"
    log "  3. Configure monitoring alerts"
    log "  4. Test disaster recovery procedures"
}

cmd_start() {
    check_root
    log "Starting services..."
    docker compose -f "${COMPOSE_FILE}" start
    log "Services started"
}

cmd_stop() {
    check_root
    log "Stopping services..."
    docker compose -f "${COMPOSE_FILE}" stop
    log "Services stopped"
}

cmd_restart() {
    check_root
    log "Restarting services..."
    docker compose -f "${COMPOSE_FILE}" restart
    log "Services restarted"
}

cmd_status() {
    log "Service Status:"
    docker compose -f "${COMPOSE_FILE}" ps
}

cmd_logs() {
    SERVICE="${2:-}"
    if [[ -z "${SERVICE}" ]]; then
        docker compose -f "${COMPOSE_FILE}" logs -f --tail=100
    else
        docker compose -f "${COMPOSE_FILE}" logs -f --tail=100 "${SERVICE}"
    fi
}

cmd_backup() {
    check_root
    log "Creating database backup..."

    BACKUP_DIR="${SCRIPT_DIR}/backups"
    BACKUP_FILE="${BACKUP_DIR}/backup_$(date +%Y%m%d_%H%M%S).sql"

    mkdir -p "${BACKUP_DIR}"

    docker compose -f "${COMPOSE_FILE}" exec -T postgres \
        pg_dump -U "${POSTGRES_USER:-admin}" "${POSTGRES_DB:-ai_platform}" > "${BACKUP_FILE}"

    gzip "${BACKUP_FILE}"
    log "Backup created: ${BACKUP_FILE}.gz"
}

cmd_update() {
    check_root
    log "Updating services..."

    pull_images
    build_services
    docker compose -f "${COMPOSE_FILE}" up -d --force-recreate

    log "Services updated successfully"
}

cmd_cleanup() {
    check_root
    log "Cleaning up Docker resources..."

    docker system prune -af --volumes

    log "Cleanup complete"
}

###############################################################################
# Main Script
###############################################################################

main() {
    COMMAND="${1:-help}"

    case "${COMMAND}" in
        check)
            cmd_check
            ;;
        install)
            cmd_install
            ;;
        deploy)
            cmd_deploy
            ;;
        start)
            cmd_start
            ;;
        stop)
            cmd_stop
            ;;
        restart)
            cmd_restart
            ;;
        status)
            cmd_status
            ;;
        logs)
            cmd_logs "$@"
            ;;
        backup)
            cmd_backup
            ;;
        update)
            cmd_update
            ;;
        cleanup)
            cmd_cleanup
            ;;
        help|*)
            echo "AI Platform - RHEL Production Deployment"
            echo ""
            echo "Usage: sudo $0 [command]"
            echo ""
            echo "Commands:"
            echo "  check       - Check system prerequisites"
            echo "  install     - Install required dependencies"
            echo "  deploy      - Deploy the AI Platform"
            echo "  start       - Start all services"
            echo "  stop        - Stop all services"
            echo "  restart     - Restart all services"
            echo "  status      - Check service status"
            echo "  logs [svc]  - View service logs"
            echo "  backup      - Create database backup"
            echo "  update      - Update services to latest version"
            echo "  cleanup     - Clean up old containers and images"
            echo "  help        - Show this help message"
            ;;
    esac
}

main "$@"
