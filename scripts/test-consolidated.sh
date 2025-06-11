#!/usr/bin/env bash

# ============================================================================
# Consolidated Test Script for Brain2Gain
# Unifies all testing operations: backend, frontend, and environments
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${ENVIRONMENT:-"dev"}
CLEANUP=${CLEANUP:-"true"}
VERBOSE=${VERBOSE:-"false"}
TEST_TYPE=${TEST_TYPE:-"all"}

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Help function
show_help() {
    cat << EOF
Brain2Gain Consolidated Test Script

Usage: $0 [OPTIONS]

OPTIONS:
    -h, --help              Show this help message
    -e, --environment       Environment (dev|ci|local) [default: dev]
    -t, --type              Test type (backend|frontend|e2e|env|all) [default: all]
    -c, --cleanup           Clean up after tests (true|false) [default: true]
    -v, --verbose           Verbose output [default: false]

EXAMPLES:
    $0                              # Run all tests in dev mode
    $0 -t backend                   # Run only backend tests
    $0 -e ci -t frontend            # Run frontend tests in CI mode
    $0 -t env --no-cleanup          # Test environments without cleanup
    $0 -v -t e2e                    # Run E2E tests with verbose output

TEST TYPES:
    backend     Backend unit and integration tests
    frontend    Frontend unit tests with Vitest
    e2e         End-to-end tests with Playwright
    env         Environment separation tests
    all         All of the above
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -t|--type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -c|--cleanup)
            CLEANUP="$2"
            shift 2
            ;;
        --no-cleanup)
            CLEANUP="false"
            shift
            ;;
        -v|--verbose)
            VERBOSE="true"
            set -x
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Set Docker Compose file based on environment
COMPOSE_FILE="docker-compose.yml"
case $ENVIRONMENT in
    "dev")
        COMPOSE_FILE="docker-compose.dev.yml"
        ;;
    "ci")
        COMPOSE_FILE="docker-compose.ci.yml"
        ;;
    "local")
        COMPOSE_FILE="docker-compose.yml"
        ;;
esac

print_info "Starting Brain2Gain tests..."
print_info "Environment: $ENVIRONMENT"
print_info "Test type: $TEST_TYPE"
print_info "Compose file: $COMPOSE_FILE"

# Cleanup function
cleanup() {
    if [[ "$CLEANUP" == "true" ]]; then
        print_info "Cleaning up test environment..."
        
        # Clean up main environment
        docker-compose -f "$COMPOSE_FILE" down -v --remove-orphans 2>/dev/null || true
        
        # Clean up separated environments if they exist
        docker-compose -f docker-compose.store.yml down -v --remove-orphans 2>/dev/null || true
        docker-compose -f docker-compose.admin.yml down -v --remove-orphans 2>/dev/null || true
        
        # Remove __pycache__ files on Linux
        if [ $(uname -s) = "Linux" ]; then
            print_info "Removing Python cache files..."
            sudo find . -type d -name __pycache__ -exec rm -r {} \+ 2>/dev/null || true
        fi
        
        print_success "Cleanup completed"
    fi
}

# Set trap to cleanup on exit
trap cleanup EXIT

# Backend tests function
run_backend_tests() {
    print_info "Running backend tests..."
    
    docker-compose -f "$COMPOSE_FILE" build backend
    docker-compose -f "$COMPOSE_FILE" up -d postgres redis
    
    # Wait for services to be ready
    sleep 10
    
    docker-compose -f "$COMPOSE_FILE" exec -T backend bash scripts/tests-start.sh
    
    print_success "Backend tests completed"
}

# Frontend tests function
run_frontend_tests() {
    print_info "Running frontend tests..."
    
    cd frontend
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        print_info "Installing frontend dependencies..."
        npm ci
    fi
    
    # Run unit tests
    npm run test
    
    cd ..
    
    print_success "Frontend tests completed"
}

# E2E tests function
run_e2e_tests() {
    print_info "Running E2E tests..."
    
    # Start full environment
    docker-compose -f "$COMPOSE_FILE" build
    docker-compose -f "$COMPOSE_FILE" up -d
    
    # Wait for services to be ready
    print_info "Waiting for services to be ready..."
    sleep 30
    
    cd frontend
    
    # Install Playwright if needed
    if [ ! -d "node_modules/@playwright" ]; then
        print_info "Installing Playwright..."
        npx playwright install
    fi
    
    # Run E2E tests
    npm run test:e2e
    
    cd ..
    
    print_success "E2E tests completed"
}

# Environment separation tests function
run_env_tests() {
    print_info "Running environment separation tests..."
    
    # Check if the environment test script exists
    if [ ! -f "scripts/test-environments.sh" ]; then
        print_error "Environment test script not found"
        return 1
    fi
    
    # Make sure it's executable
    chmod +x scripts/test-environments.sh
    
    # Run environment tests
    ./scripts/test-environments.sh
    
    print_success "Environment tests completed"
}

# Main execution logic
case $TEST_TYPE in
    "backend")
        run_backend_tests
        ;;
    "frontend")
        run_frontend_tests
        ;;
    "e2e")
        run_e2e_tests
        ;;
    "env")
        run_env_tests
        ;;
    "all")
        print_info "Running all tests..."
        run_backend_tests
        run_frontend_tests
        run_e2e_tests
        run_env_tests
        print_success "All tests completed successfully!"
        ;;
    *)
        print_error "Unknown test type: $TEST_TYPE"
        echo "Valid types: backend, frontend, e2e, env, all"
        exit 1
        ;;
esac

print_success "Test execution completed successfully!"