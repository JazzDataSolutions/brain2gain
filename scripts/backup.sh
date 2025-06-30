#!/bin/bash
# Database backup script for Brain2Gain production

set -e

# Configuration
POSTGRES_HOST=${POSTGRES_HOST:-postgres}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_DB=${POSTGRES_DB:-brain2gain_prod}
POSTGRES_USER=${POSTGRES_USER:-brain2gain_prod}
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/brain2gain_backup_${DATE}.sql"
KEEP_DAYS=${KEEP_DAYS:-7}

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

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Function to cleanup old backups
cleanup_old_backups() {
    log "Cleaning up backups older than ${KEEP_DAYS} days..."
    
    find "${BACKUP_DIR}" -name "brain2gain_backup_*.sql*" -mtime +${KEEP_DAYS} -delete
    
    success "Old backups cleaned up"
}

# Function to perform database backup
perform_backup() {
    log "Starting database backup..."
    
    # Set password from secret file
    export PGPASSWORD=$(cat /run/secrets/postgres_password)
    
    # Perform backup
    pg_dump \
        --host="${POSTGRES_HOST}" \
        --port="${POSTGRES_PORT}" \
        --username="${POSTGRES_USER}" \
        --dbname="${POSTGRES_DB}" \
        --verbose \
        --no-password \
        --format=custom \
        --compress=9 \
        --file="${BACKUP_FILE}.backup"
    
    # Also create a plain SQL backup for easier inspection
    pg_dump \
        --host="${POSTGRES_HOST}" \
        --port="${POSTGRES_PORT}" \
        --username="${POSTGRES_USER}" \
        --dbname="${POSTGRES_DB}" \
        --no-password \
        --format=plain \
        > "${BACKUP_FILE}"
    
    # Compress the plain SQL backup
    gzip "${BACKUP_FILE}"
    
    success "Database backup completed: ${BACKUP_FILE}.gz and ${BACKUP_FILE}.backup"
}

# Function to verify backup
verify_backup() {
    log "Verifying backup integrity..."
    
    # Check if backup files exist and are not empty
    if [[ -f "${BACKUP_FILE}.gz" && -s "${BACKUP_FILE}.gz" ]]; then
        success "Plain SQL backup verified: ${BACKUP_FILE}.gz"
    else
        error "Plain SQL backup verification failed"
        exit 1
    fi
    
    if [[ -f "${BACKUP_FILE}.backup" && -s "${BACKUP_FILE}.backup" ]]; then
        success "Custom format backup verified: ${BACKUP_FILE}.backup"
    else
        error "Custom format backup verification failed"
        exit 1
    fi
    
    # Test that compressed file can be read
    if gzip -t "${BACKUP_FILE}.gz"; then
        success "Backup compression integrity verified"
    else
        error "Backup compression integrity check failed"
        exit 1
    fi
}

# Function to log backup metadata
log_backup_metadata() {
    local metadata_file="${BACKUP_DIR}/backup_metadata.log"
    
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ),${DATE},${BACKUP_FILE}.gz,$(stat -c%s ${BACKUP_FILE}.gz),$(stat -c%s ${BACKUP_FILE}.backup)" >> "${metadata_file}"
    
    success "Backup metadata logged"
}

# Main backup function
main() {
    log "Starting Brain2Gain database backup process..."
    
    # Perform backup
    perform_backup
    
    # Verify backup
    verify_backup
    
    # Log metadata
    log_backup_metadata
    
    # Cleanup old backups
    cleanup_old_backups
    
    success "Backup process completed successfully"
}

# Error handling
handle_error() {
    error "Backup process failed"
    exit 1
}

# Set trap for error handling
trap handle_error ERR

# Execute main function
main "$@"