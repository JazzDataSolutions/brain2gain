#!/usr/bin/env bash

# 🧪 Brain2Gain - Test Environment Setup Script
# Sets up minimal testing infrastructure

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

print_header() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}🧪 $1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

# Configuration
POSTGRES_DB="brain2gain_test"
POSTGRES_USER="brain2gain_test"
POSTGRES_PASSWORD="TestPassword123!"
REDIS_PASSWORD="TestRedisPass123!"

print_header "Brain2Gain Test Environment Setup"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed or not running"
    exit 1
fi

# Create network if it doesn't exist
log_info "Creating test network..."
docker network create brain2gain-test-network 2>/dev/null || log_info "Network already exists"

# Start PostgreSQL for testing
print_header "Starting Test Database"
log_info "Starting PostgreSQL test container..."

docker run -d \
    --name brain2gain-postgres-test \
    --network brain2gain-test-network \
    -e POSTGRES_DB=${POSTGRES_DB} \
    -e POSTGRES_USER=${POSTGRES_USER} \
    -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
    -p 5434:5432 \
    postgres:17-alpine

# Wait for PostgreSQL to be ready
log_info "Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if docker exec brain2gain-postgres-test pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB} &>/dev/null; then
        log_success "PostgreSQL is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        log_error "PostgreSQL failed to start"
        exit 1
    fi
    sleep 1
done

# Start Redis for testing
print_header "Starting Test Cache"
log_info "Starting Redis test container..."

docker run -d \
    --name brain2gain-redis-test \
    --network brain2gain-test-network \
    -e REDIS_PASSWORD=${REDIS_PASSWORD} \
    -p 6380:6379 \
    redis:7-alpine \
    redis-server --requirepass ${REDIS_PASSWORD}

# Wait for Redis to be ready
log_info "Waiting for Redis to be ready..."
sleep 2
if docker exec brain2gain-redis-test redis-cli -a ${REDIS_PASSWORD} ping &>/dev/null; then
    log_success "Redis is ready!"
else
    log_warning "Redis may not be fully ready, but continuing..."
fi

# Create environment file for testing
print_header "Creating Test Environment Configuration"

cat > .env.test << EOF
# Brain2Gain Test Environment Configuration
ENVIRONMENT=testing
DEBUG=false
LOG_LEVEL=WARNING

# Database Configuration
POSTGRES_SERVER=localhost
POSTGRES_PORT=5434
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5434/${POSTGRES_DB}

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6380
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_URL=redis://:${REDIS_PASSWORD}@localhost:6380

# Security
SECRET_KEY=test-secret-key-for-testing-only
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Email (disabled for testing)
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_TLS=false
EMAILS_FROM_EMAIL=test@brain2gain.test

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:5173", "http://localhost:5174"]

# First superuser
FIRST_SUPERUSER=admin@brain2gain.test
FIRST_SUPERUSER_PASSWORD=admin123
EMAIL_TEST_USER=test@brain2gain.test
EOF

log_success "Test environment configuration created: .env.test"

# Display connection information
print_header "Test Environment Information"
echo -e "${GREEN}✅ Test environment is ready!${NC}"
echo ""
echo -e "${BLUE}Database Connection:${NC}"
echo "  Host: localhost"
echo "  Port: 5434"
echo "  Database: ${POSTGRES_DB}"
echo "  User: ${POSTGRES_USER}"
echo "  Password: ${POSTGRES_PASSWORD}"
echo ""
echo -e "${BLUE}Redis Connection:${NC}"
echo "  Host: localhost"
echo "  Port: 6380"
echo "  Password: ${REDIS_PASSWORD}"
echo ""
echo -e "${BLUE}Environment file: .env.test${NC}"
echo ""
echo -e "${YELLOW}To run tests:${NC}"
echo "  cd backend && source .env.test && uv run pytest app/tests/ -v"
echo ""
echo -e "${YELLOW}To stop test environment:${NC}"
echo "  ./scripts/stop-test-env.sh"

# Test the connection
print_header "Testing Connections"

log_info "Testing PostgreSQL connection..."
if docker exec brain2gain-postgres-test psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT 1;" &>/dev/null; then
    log_success "PostgreSQL connection successful"
else
    log_error "PostgreSQL connection failed"
fi

log_info "Testing Redis connection..."
if docker exec brain2gain-redis-test redis-cli -a ${REDIS_PASSWORD} ping &>/dev/null; then
    log_success "Redis connection successful"
else
    log_error "Redis connection failed"
fi

echo ""
log_success "Test environment setup completed successfully!"
echo -e "${GREEN}🎉 Ready to run tests!${NC}"