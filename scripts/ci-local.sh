#!/bin/bash

# ============================================================================
# Local CI Pipeline Script
# Runs the same tests that will be executed in CI/CD
# ============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to cleanup on exit
cleanup() {
    print_step "Cleaning up CI environment..."
    docker-compose -f docker-compose.ci.yml down --volumes --remove-orphans
    docker system prune -f
}

# Trap cleanup function on script exit
trap cleanup EXIT

# Main execution
main() {
    echo "============================================================================"
    echo "                        Brain2Gain CI Pipeline"
    echo "============================================================================"
    echo ""

    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi

    # Check if required files exist
    if [[ ! -f "docker-compose.ci.yml" ]]; then
        print_error "docker-compose.ci.yml not found. Please run this script from the project root."
        exit 1
    fi

    print_step "Starting CI pipeline..."

    # Parse command line arguments
    RUN_E2E=false
    SKIP_CLEANUP=false
    VERBOSE=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --e2e)
                RUN_E2E=true
                shift
                ;;
            --skip-cleanup)
                SKIP_CLEANUP=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --e2e           Run E2E tests (takes longer)"
                echo "  --skip-cleanup  Don't cleanup containers after tests"
                echo "  --verbose       Show detailed output"
                echo "  --help          Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done

    # Cleanup any existing containers
    print_step "Cleaning up existing CI containers..."
    docker-compose -f docker-compose.ci.yml down --volumes --remove-orphans || true

    # Build and start services
    print_step "Building CI environment..."
    if [[ "$VERBOSE" == "true" ]]; then
        docker-compose -f docker-compose.ci.yml build --no-cache
    else
        docker-compose -f docker-compose.ci.yml build --no-cache >/dev/null 2>&1
    fi

    print_step "Starting database..."
    docker-compose -f docker-compose.ci.yml up -d postgres-ci

    # Wait for database to be ready
    print_step "Waiting for database to be ready..."
    for i in {1..30}; do
        if docker-compose -f docker-compose.ci.yml exec -T postgres-ci pg_isready -U brain2gain_test >/dev/null 2>&1; then
            print_success "Database is ready"
            break
        fi
        if [[ $i -eq 30 ]]; then
            print_error "Database failed to start after 30 seconds"
            exit 1
        fi
        sleep 1
    done

    # Run backend tests
    print_step "Running backend tests..."
    if [[ "$VERBOSE" == "true" ]]; then
        docker-compose -f docker-compose.ci.yml run --rm backend-ci
    else
        docker-compose -f docker-compose.ci.yml run --rm backend-ci >/dev/null 2>&1
    fi

    if [[ $? -eq 0 ]]; then
        print_success "Backend tests passed"
    else
        print_error "Backend tests failed"
        exit 1
    fi

    # Run frontend tests
    print_step "Running frontend tests..."
    if [[ "$VERBOSE" == "true" ]]; then
        docker-compose -f docker-compose.ci.yml run --rm frontend-ci
    else
        docker-compose -f docker-compose.ci.yml run --rm frontend-ci >/dev/null 2>&1
    fi

    if [[ $? -eq 0 ]]; then
        print_success "Frontend tests passed"
    else
        print_error "Frontend tests failed"
        exit 1
    fi

    # Run integration tests
    print_step "Running integration tests..."
    if [[ "$VERBOSE" == "true" ]]; then
        docker-compose -f docker-compose.ci.yml run --rm integration-tests
    else
        docker-compose -f docker-compose.ci.yml run --rm integration-tests >/dev/null 2>&1
    fi

    if [[ $? -eq 0 ]]; then
        print_success "Integration tests passed"
    else
        print_error "Integration tests failed"
        exit 1
    fi

    # Run E2E tests if requested
    if [[ "$RUN_E2E" == "true" ]]; then
        print_step "Running E2E tests..."
        
        # Start frontend service for E2E tests
        docker-compose -f docker-compose.ci.yml up -d frontend-ci
        
        if [[ "$VERBOSE" == "true" ]]; then
            docker-compose -f docker-compose.ci.yml --profile e2e run --rm e2e-tests
        else
            docker-compose -f docker-compose.ci.yml --profile e2e run --rm e2e-tests >/dev/null 2>&1
        fi

        if [[ $? -eq 0 ]]; then
            print_success "E2E tests passed"
        else
            print_error "E2E tests failed"
            exit 1
        fi
    fi

    # Generate coverage reports
    print_step "Generating coverage reports..."
    
    # Extract coverage reports from containers
    mkdir -p ./ci-reports/backend ./ci-reports/frontend
    
    # Backend coverage
    if docker-compose -f docker-compose.ci.yml ps backend-ci >/dev/null 2>&1; then
        docker cp $(docker-compose -f docker-compose.ci.yml ps -q backend-ci):/app/coverage/ ./ci-reports/backend/ 2>/dev/null || true
    fi
    
    # Frontend coverage
    if docker-compose -f docker-compose.ci.yml ps frontend-ci >/dev/null 2>&1; then
        docker cp $(docker-compose -f docker-compose.ci.yml ps -q frontend-ci):/app/coverage/ ./ci-reports/frontend/ 2>/dev/null || true
    fi

    print_success "Coverage reports generated in ./ci-reports/"

    # Cleanup if not skipped
    if [[ "$SKIP_CLEANUP" != "true" ]]; then
        print_step "Cleaning up CI environment..."
        docker-compose -f docker-compose.ci.yml down --volumes --remove-orphans
    else
        print_warning "Skipping cleanup. Run 'docker-compose -f docker-compose.ci.yml down --volumes' to cleanup manually."
    fi

    echo ""
    echo "============================================================================"
    print_success "🎉 All CI tests passed successfully!"
    echo "============================================================================"
    echo ""
    
    if [[ -d "./ci-reports" ]]; then
        echo "Coverage reports available in:"
        echo "  - Backend: ./ci-reports/backend/coverage/"
        echo "  - Frontend: ./ci-reports/frontend/coverage/"
        echo ""
    fi
}

# Run main function
main "$@"