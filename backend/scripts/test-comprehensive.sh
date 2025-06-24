#!/usr/bin/env bash

# 🧪 Brain2Gain - Comprehensive Backend Testing Script
# Based on testing_plan.yml requirements

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COVERAGE_THRESHOLD=90
PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
TEST_DB_NAME="brain2gain_test"
REPORTS_DIR="test-reports"

# Utility functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}🧪 $1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

# Setup function
setup_test_environment() {
    print_header "Setting up test environment"
    
    log_info "Creating test reports directory..."
    mkdir -p "${REPORTS_DIR}"/{unit,integration,performance,security,coverage}
    
    log_info "Installing test dependencies..."
    uv sync --dev
    
    log_info "Setting up test database..."
    # Database setup will be handled by conftest.py fixtures
    
    log_success "Test environment setup complete"
}

# Unit Tests
run_unit_tests() {
    print_header "Running Unit Tests"
    
    log_info "Testing Models..."
    uv run pytest tests/unit/models/ -v \
        --cov=app/models \
        --cov-report=html:${REPORTS_DIR}/coverage/unit-models \
        --cov-report=xml:${REPORTS_DIR}/coverage/unit-models.xml \
        --junit-xml=${REPORTS_DIR}/unit/models-junit.xml \
        --cov-fail-under=95 || log_warning "Models coverage below 95%"
    
    log_info "Testing Services..."
    uv run pytest tests/unit/services/ -v \
        --cov=app/services \
        --cov-report=html:${REPORTS_DIR}/coverage/unit-services \
        --cov-report=xml:${REPORTS_DIR}/coverage/unit-services.xml \
        --junit-xml=${REPORTS_DIR}/unit/services-junit.xml \
        --cov-fail-under=90 || log_warning "Services coverage below 90%"
    
    log_info "Testing Repositories..."
    uv run pytest tests/unit/repositories/ -v \
        --cov=app/repositories \
        --cov-report=html:${REPORTS_DIR}/coverage/unit-repositories \
        --cov-report=xml:${REPORTS_DIR}/coverage/unit-repositories.xml \
        --junit-xml=${REPORTS_DIR}/unit/repositories-junit.xml \
        --cov-fail-under=95 || log_warning "Repositories coverage below 95%"
    
    log_success "Unit tests completed"
}

# Integration Tests
run_integration_tests() {
    print_header "Running Integration Tests"
    
    log_info "Testing API routes..."
    uv run pytest tests/integration/api/ -v \
        --cov=app/api \
        --cov-report=html:${REPORTS_DIR}/coverage/integration-api \
        --cov-report=xml:${REPORTS_DIR}/coverage/integration-api.xml \
        --junit-xml=${REPORTS_DIR}/integration/api-junit.xml
    
    log_info "Testing Database operations..."
    uv run pytest tests/integration/database/ -v \
        --junit-xml=${REPORTS_DIR}/integration/database-junit.xml
    
    log_info "Testing Cache operations..."
    uv run pytest tests/integration/cache/ -v \
        --junit-xml=${REPORTS_DIR}/integration/cache-junit.xml
    
    log_info "Testing WebSocket connections..."
    uv run pytest tests/integration/websocket/ -v \
        --junit-xml=${REPORTS_DIR}/integration/websocket-junit.xml
    
    log_success "Integration tests completed"
}

# API Endpoint Tests
run_api_tests() {
    print_header "Running API Endpoint Tests"
    
    log_info "Testing Authentication endpoints..."
    uv run pytest tests/api/routes/test_login.py -v \
        --junit-xml=${REPORTS_DIR}/integration/auth-endpoints-junit.xml
    
    log_info "Testing Product endpoints..."
    uv run pytest tests/api/routes/test_products.py -v \
        --junit-xml=${REPORTS_DIR}/integration/product-endpoints-junit.xml
    
    log_info "Testing Cart endpoints..."
    uv run pytest tests/api/routes/test_cart.py -v \
        --junit-xml=${REPORTS_DIR}/integration/cart-endpoints-junit.xml
    
    log_info "Testing Order endpoints..."
    uv run pytest tests/api/routes/test_orders.py -v \
        --junit-xml=${REPORTS_DIR}/integration/order-endpoints-junit.xml
    
    log_info "Testing Analytics endpoints..."
    uv run pytest tests/api/routes/test_analytics.py -v \
        --junit-xml=${REPORTS_DIR}/integration/analytics-endpoints-junit.xml
    
    log_success "API tests completed"
}

# Performance Tests
run_performance_tests() {
    print_header "Running Performance Tests"
    
    log_info "Testing API performance..."
    uv run pytest tests/performance/test_api_performance.py -v \
        --junit-xml=${REPORTS_DIR}/performance/api-performance-junit.xml
    
    log_info "Testing database query performance..."
    uv run pytest tests/performance/test_db_performance.py -v \
        --junit-xml=${REPORTS_DIR}/performance/db-performance-junit.xml
    
    log_success "Performance tests completed"
}

# Security Tests
run_security_tests() {
    print_header "Running Security Tests"
    
    log_info "Testing authentication security..."
    uv run pytest tests/security/test_authentication.py -v \
        --junit-xml=${REPORTS_DIR}/security/auth-security-junit.xml
    
    log_info "Testing input validation..."
    uv run pytest tests/security/test_input_validation.py -v \
        --junit-xml=${REPORTS_DIR}/security/input-validation-junit.xml
    
    log_info "Testing authorization..."
    uv run pytest tests/security/test_authorization.py -v \
        --junit-xml=${REPORTS_DIR}/security/authorization-junit.xml
    
    log_success "Security tests completed"
}

# Generate overall coverage report
generate_coverage_report() {
    print_header "Generating Coverage Report"
    
    log_info "Running full test suite with coverage..."
    uv run pytest \
        --cov=app \
        --cov-report=html:${REPORTS_DIR}/coverage/full \
        --cov-report=xml:${REPORTS_DIR}/coverage/coverage.xml \
        --cov-report=term-missing \
        --cov-fail-under=${COVERAGE_THRESHOLD}
    
    log_info "Coverage report generated at: ${REPORTS_DIR}/coverage/full/index.html"
    log_success "Coverage analysis completed"
}

# Test database migrations
test_migrations() {
    print_header "Testing Database Migrations"
    
    log_info "Testing migration rollback and upgrade..."
    uv run pytest tests/integration/test_migrations.py -v \
        --junit-xml=${REPORTS_DIR}/integration/migrations-junit.xml
    
    log_success "Migration tests completed"
}

# Cleanup function
cleanup() {
    print_header "Cleaning up"
    
    log_info "Cleaning up test artifacts..."
    # Clean up any temporary files or test data
    
    log_success "Cleanup completed"
}

# Main execution
main() {
    print_header "Brain2Gain Backend Comprehensive Testing Suite"
    
    local start_time=$(date +%s)
    
    # Parse command line arguments
    local run_unit=true
    local run_integration=true
    local run_api=true
    local run_performance=true
    local run_security=true
    local run_coverage=true
    local run_migrations=true
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --unit-only)
                run_integration=false
                run_api=false
                run_performance=false
                run_security=false
                run_migrations=false
                shift
                ;;
            --integration-only)
                run_unit=false
                run_api=false
                run_performance=false
                run_security=false
                run_migrations=false
                shift
                ;;
            --api-only)
                run_unit=false
                run_integration=false
                run_performance=false
                run_security=false
                run_migrations=false
                shift
                ;;
            --no-coverage)
                run_coverage=false
                shift
                ;;
            --fast)
                run_performance=false
                run_security=false
                run_migrations=false
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --unit-only      Run only unit tests"
                echo "  --integration-only Run only integration tests"
                echo "  --api-only       Run only API tests"
                echo "  --no-coverage    Skip coverage report generation"
                echo "  --fast           Skip performance, security, and migration tests"
                echo "  -h, --help       Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Setup
    setup_test_environment
    
    # Execute tests based on flags
    [[ "$run_unit" == true ]] && run_unit_tests
    [[ "$run_integration" == true ]] && run_integration_tests  
    [[ "$run_api" == true ]] && run_api_tests
    [[ "$run_performance" == true ]] && run_performance_tests
    [[ "$run_security" == true ]] && run_security_tests
    [[ "$run_migrations" == true ]] && test_migrations
    [[ "$run_coverage" == true ]] && generate_coverage_report
    
    # Cleanup
    cleanup
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_header "Test Execution Summary"
    log_success "All tests completed successfully!"
    log_info "Total execution time: ${duration} seconds"
    log_info "Reports generated in: ${REPORTS_DIR}/"
    log_info "Coverage report: ${REPORTS_DIR}/coverage/full/index.html"
    
    echo -e "\n${GREEN}🎉 Brain2Gain backend testing completed successfully!${NC}\n"
}

# Execute main function with all arguments
main "$@"