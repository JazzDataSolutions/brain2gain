#!/bin/bash
# Production startup script for Brain2Gain Backend

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Wait for database to be ready
wait_for_db() {
    log "Waiting for database to be ready..."
    
    while ! pg_isready -h "${POSTGRES_SERVER}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"; do
        log "Database is not ready. Waiting 2 seconds..."
        sleep 2
    done
    
    success "Database is ready"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    # Run Alembic migrations
    alembic upgrade head
    
    success "Database migrations completed"
}

# Initialize application data
init_data() {
    log "Initializing application data..."
    
    # Run initial data setup if needed
    python -m app.initial_data
    
    success "Application data initialized"
}

# Start the application
start_app() {
    log "Starting Brain2Gain Backend API..."
    
    # Calculate workers based on CPU cores
    WORKERS_PER_CORE=${WORKERS_PER_CORE:-2}
    MAX_WORKERS=${MAX_WORKERS:-8}
    WEB_CONCURRENCY=${WEB_CONCURRENCY:-4}
    
    # Calculate number of workers
    WORKERS=$(python -c "
import multiprocessing
cores = multiprocessing.cpu_count()
workers = min(max(cores * ${WORKERS_PER_CORE}, 1), ${MAX_WORKERS})
print(workers)
")
    
    log "Starting with ${WORKERS} workers"
    
    # Start Uvicorn with production settings
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers ${WORKERS} \
        --worker-class uvicorn.workers.UvicornWorker \
        --access-log \
        --log-level info \
        --timeout-keep-alive 65 \
        --limit-concurrency 1000 \
        --limit-max-requests 10000 \
        --backlog 2048
}

# Main execution
main() {
    log "Starting Brain2Gain Backend in production mode..."
    
    # Wait for dependencies
    wait_for_db
    
    # Run migrations
    run_migrations
    
    # Initialize data
    init_data
    
    # Start application
    start_app
}

# Error handling
handle_error() {
    error "An error occurred during startup. Exiting..."
    exit 1
}

# Set trap for error handling
trap handle_error ERR

# Execute main function
main "$@"