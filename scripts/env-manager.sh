#!/usr/bin/env bash

# 🔧 Environment Manager - Simplified Environment Configuration
# Manages environment files and docker compose configurations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_DIR="$PROJECT_ROOT/config"
DOCKER_DIR="$PROJECT_ROOT/docker"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

setup_environment() {
    local env="$1"
    
    log_info "Setting up $env environment..."
    
    local env_file="$CONFIG_DIR/.env.$env"
    
    # Check if environment file exists
    if [[ ! -f "$env_file" ]]; then
        log_error "Environment file not found: $env_file"
        exit 1
    fi
    
    # Copy environment file to project root
    cp "$env_file" "$PROJECT_ROOT/.env"
    log_success "Environment file configured for $env"
    
    # Create directories if needed
    mkdir -p "$PROJECT_ROOT/database/backups"
    mkdir -p "$PROJECT_ROOT/logs"
    
    log_success "Environment $env setup completed"
}

# Main execution
main() {
    local command="$1"
    local environment="$2"
    
    case "$command" in
        setup)
            setup_environment "$environment"
            ;;
        *)
            log_error "Command not implemented yet: $command"
            exit 1
            ;;
    esac
}

main "$@"