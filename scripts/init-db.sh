#!/bin/bash

# Database Initialization Script for AI Platform
# This script initializes the PostgreSQL database with schema and sample data

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
POSTGRES_CONTAINER="ai-postgres"
POSTGRES_USER="${POSTGRES_USER:-admin}"
POSTGRES_DB="${POSTGRES_DB:-ai_platform}"
SCHEMA_FILE="./services/mcp-server/schema.sql"
SEED_FILE="./services/mcp-server/seed.sql"

# Helper functions
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

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    log_success "Docker is running"
}

# Check if PostgreSQL container is running
check_postgres() {
    if ! docker ps | grep -q $POSTGRES_CONTAINER; then
        log_error "PostgreSQL container ($POSTGRES_CONTAINER) is not running."
        log_info "Start it with: docker compose up -d postgres"
        exit 1
    fi
    log_success "PostgreSQL container is running"
}

# Wait for PostgreSQL to be ready
wait_for_postgres() {
    log_info "Waiting for PostgreSQL to be ready..."

    MAX_TRIES=30
    COUNT=0

    until docker compose exec -T postgres pg_isready -U $POSTGRES_USER > /dev/null 2>&1; do
        COUNT=$((COUNT+1))
        if [ $COUNT -gt $MAX_TRIES ]; then
            log_error "PostgreSQL did not become ready in time"
            exit 1
        fi
        echo -n "."
        sleep 1
    done

    echo ""
    log_success "PostgreSQL is ready"
}

# Check if database exists
check_database() {
    log_info "Checking if database '$POSTGRES_DB' exists..."

    DB_EXISTS=$(docker compose exec -T postgres psql -U $POSTGRES_USER -tAc "SELECT 1 FROM pg_database WHERE datname='$POSTGRES_DB'")

    if [ "$DB_EXISTS" = "1" ]; then
        log_success "Database '$POSTGRES_DB' exists"
        return 0
    else
        log_warning "Database '$POSTGRES_DB' does not exist"
        return 1
    fi
}

# Create database
create_database() {
    log_info "Creating database '$POSTGRES_DB'..."

    docker compose exec -T postgres psql -U $POSTGRES_USER -c "CREATE DATABASE $POSTGRES_DB;" 2>/dev/null || {
        log_warning "Database may already exist or could not be created"
    }

    log_success "Database creation completed"
}

# Create LiteLLM database
create_litellm_database() {
    log_info "Creating LiteLLM database..."

    docker compose exec -T postgres psql -U $POSTGRES_USER -c "CREATE DATABASE litellm;" 2>/dev/null || {
        log_info "LiteLLM database may already exist"
    }

    log_success "LiteLLM database checked/created"
}

# Apply schema
apply_schema() {
    log_info "Applying database schema..."

    if [ ! -f "$SCHEMA_FILE" ]; then
        log_error "Schema file not found: $SCHEMA_FILE"
        exit 1
    fi

    docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB < $SCHEMA_FILE

    if [ $? -eq 0 ]; then
        log_success "Schema applied successfully"
    else
        log_error "Failed to apply schema"
        exit 1
    fi
}

# Seed data
seed_data() {
    log_info "Seeding database with sample data..."

    if [ ! -f "$SEED_FILE" ]; then
        log_warning "Seed file not found: $SEED_FILE"
        log_info "Skipping data seeding"
        return 0
    fi

    docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB < $SEED_FILE

    if [ $? -eq 0 ]; then
        log_success "Data seeded successfully"
    else
        log_warning "Failed to seed data (this may be okay if data already exists)"
    fi
}

# Verify schema
verify_schema() {
    log_info "Verifying database schema..."

    TABLES=$(docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';")
    TABLES=$(echo $TABLES | tr -d ' ')

    log_info "Found $TABLES tables"

    # Check for required tables
    REQUIRED_TABLES=("users" "documents" "tasks" "audit_logs")

    for table in "${REQUIRED_TABLES[@]}"; do
        EXISTS=$(docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -t -c "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '$table');")
        EXISTS=$(echo $EXISTS | tr -d ' ')

        if [ "$EXISTS" = "t" ]; then
            log_success "Table '$table' exists"
        else
            log_error "Table '$table' not found"
            exit 1
        fi
    done
}

# Show table statistics
show_statistics() {
    log_info "Database statistics:"

    docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "
        SELECT
            'users' as table_name,
            COUNT(*) as row_count
        FROM users
        UNION ALL
        SELECT 'documents', COUNT(*) FROM documents
        UNION ALL
        SELECT 'tasks', COUNT(*) FROM tasks
        UNION ALL
        SELECT 'audit_logs', COUNT(*) FROM audit_logs;
    "
}

# Backup database
backup_database() {
    log_info "Creating database backup..."

    BACKUP_DIR="./backups"
    mkdir -p $BACKUP_DIR

    BACKUP_FILE="$BACKUP_DIR/ai_platform_backup_$(date +%Y%m%d_%H%M%S).sql"

    docker compose exec -T postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB > $BACKUP_FILE

    if [ $? -eq 0 ]; then
        log_success "Backup created: $BACKUP_FILE"
    else
        log_error "Backup failed"
        exit 1
    fi
}

# Restore database
restore_database() {
    if [ -z "$1" ]; then
        log_error "Please provide backup file path"
        echo "Usage: $0 restore <backup-file>"
        exit 1
    fi

    BACKUP_FILE="$1"

    if [ ! -f "$BACKUP_FILE" ]; then
        log_error "Backup file not found: $BACKUP_FILE"
        exit 1
    fi

    log_info "Restoring database from: $BACKUP_FILE"
    log_warning "This will overwrite existing data!"

    read -p "Are you sure you want to continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "Restore cancelled"
        exit 0
    fi

    docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB < $BACKUP_FILE

    if [ $? -eq 0 ]; then
        log_success "Database restored successfully"
    else
        log_error "Restore failed"
        exit 1
    fi
}

# Reset database (drop and recreate)
reset_database() {
    log_warning "This will DROP and RECREATE the database, losing all data!"

    read -p "Are you sure you want to continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "Reset cancelled"
        exit 0
    fi

    log_info "Dropping database..."
    docker compose exec -T postgres psql -U $POSTGRES_USER -c "DROP DATABASE IF EXISTS $POSTGRES_DB;"

    log_info "Creating fresh database..."
    create_database
    create_litellm_database
    apply_schema
    seed_data
    verify_schema
    show_statistics

    log_success "Database reset completed"
}

# Main function
main() {
    case "${1:-init}" in
        init)
            log_info "=== Database Initialization ==="
            check_docker
            check_postgres
            wait_for_postgres

            if ! check_database; then
                create_database
            fi

            create_litellm_database
            apply_schema
            seed_data
            verify_schema
            show_statistics

            log_success "=== Database initialization completed ==="
            ;;

        reset)
            log_info "=== Database Reset ==="
            check_docker
            check_postgres
            wait_for_postgres
            reset_database
            ;;

        backup)
            log_info "=== Database Backup ==="
            check_docker
            check_postgres
            backup_database
            ;;

        restore)
            log_info "=== Database Restore ==="
            check_docker
            check_postgres
            wait_for_postgres
            restore_database "$2"
            ;;

        verify)
            log_info "=== Database Verification ==="
            check_docker
            check_postgres
            verify_schema
            show_statistics
            ;;

        stats)
            log_info "=== Database Statistics ==="
            check_docker
            check_postgres
            show_statistics
            ;;

        *)
            echo "Usage: $0 {init|reset|backup|restore|verify|stats}"
            echo ""
            echo "Commands:"
            echo "  init      - Initialize database with schema and sample data (default)"
            echo "  reset     - Drop and recreate database (WARNING: destroys all data)"
            echo "  backup    - Create database backup"
            echo "  restore   - Restore database from backup file"
            echo "  verify    - Verify database schema"
            echo "  stats     - Show database statistics"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
