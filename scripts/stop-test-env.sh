#!/usr/bin/env bash

# 🧪 Brain2Gain - Stop Test Environment Script

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }

print_header() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}🧪 $1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

print_header "Brain2Gain Test Environment Cleanup"

log_info "Stopping test containers..."
docker stop brain2gain-postgres-test brain2gain-redis-test 2>/dev/null || true

log_info "Removing test containers..."
docker rm brain2gain-postgres-test brain2gain-redis-test 2>/dev/null || true

log_info "Removing test network..."
docker network rm brain2gain-test-network 2>/dev/null || true

log_info "Cleaning up environment files..."
rm -f .env.test

log_success "Test environment cleanup completed!"
echo -e "${GREEN}🎉 All test resources removed${NC}"