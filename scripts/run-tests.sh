#!/usr/bin/env bash

# 🧪 Brain2Gain - Comprehensive Test Runner
# Uses the test environment and runs all tests according to testing_plan.yml

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_phase() { echo -e "${PURPLE}🚀 $1${NC}"; }

print_header() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}🧪 $1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

print_banner() {
    echo -e "${PURPLE}"
    echo "██████╗ ██████╗  █████╗ ██╗███╗   ██╗██████╗  ██████╗  █████╗ ██╗███╗   ██╗"
    echo "██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║╚════██╗██╔════╝ ██╔══██╗██║████╗  ██║"
    echo "██████╔╝██████╔╝███████║██║██╔██╗ ██║ █████╔╝██║  ███╗███████║██║██╔██╗ ██║"
    echo "██╔══██╗██╔══██╗██╔══██║██║██║╚██╗██║██╔═══╝ ██║   ██║██╔══██║██║██║╚██╗██║"
    echo "██████╔╝██║  ██║██║  ██║██║██║ ╚████║███████╗╚██████╔╝██║  ██║██║██║ ╚████║"
    echo "╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝"
    echo -e "${NC}"
    echo -e "${BLUE}                    🧪 COMPREHENSIVE TESTING SUITE 🧪${NC}"
    echo -e "${BLUE}                         Based on testing_plan.yml${NC}\n"
}

# Test execution tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Check if test environment is running
check_test_environment() {
    print_header "Checking Test Environment"
    
    log_info "Checking if test containers are running..."
    
    if ! docker ps --filter "name=brain2gain-postgres-test" --filter "status=running" | grep -q brain2gain-postgres-test; then
        log_warning "PostgreSQL test container not running"
        log_info "Starting test environment..."
        ./scripts/setup-test-env.sh
    else
        log_success "Test environment is running"
    fi
    
    # Load test environment variables
    if [[ -f ".env.test" ]]; then
        log_info "Loading test environment variables..."
        export $(grep -v '^#' .env.test | xargs)
        log_success "Environment variables loaded"
    else
        log_error "Test environment not found. Run ./scripts/setup-test-env.sh first"
        exit 1
    fi
}

# Backend testing
run_backend_tests() {
    log_phase "PHASE 1: Backend Testing"
    
    cd backend
    
    log_info "Installing backend dependencies..."
    uv sync --dev
    
    # Run database migrations
    log_info "Running database migrations..."
    uv run alembic upgrade head
    
    # Create test reports directory
    mkdir -p test-reports/{unit,integration,security,performance,coverage}
    
    print_header "Running Backend Unit Tests"
    
    log_info "Testing core modules..."
    if uv run pytest app/tests/unit/ -v --tb=short --cov=app --cov-report=html:test-reports/coverage/unit --junitxml=test-reports/unit/junit.xml; then
        log_success "Unit tests passed"
        ((PASSED_TESTS++))
    else
        log_error "Unit tests failed"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    
    print_header "Running Backend API Tests"
    
    log_info "Testing API routes..."
    if uv run pytest app/tests/api/ -v --tb=short --cov=app --cov-report=html:test-reports/coverage/api --junitxml=test-reports/integration/api-junit.xml; then
        log_success "API tests passed"
        ((PASSED_TESTS++))
    else
        log_error "API tests failed"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    
    print_header "Running Backend Security Tests"
    
    log_info "Testing security features..."
    if uv run pytest app/tests/security/ -v --tb=short --junitxml=test-reports/security/junit.xml; then
        log_success "Security tests passed"
        ((PASSED_TESTS++))
    else
        log_error "Security tests failed"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    
    print_header "Generating Backend Coverage Report"
    
    log_info "Generating comprehensive coverage report..."
    uv run pytest app/tests/ --cov=app --cov-report=html:test-reports/coverage/full --cov-report=term-missing --cov-fail-under=80 || log_warning "Coverage below 80%"
    
    cd ..
}

# Frontend testing
run_frontend_tests() {
    log_phase "PHASE 2: Frontend Testing"
    
    cd frontend
    
    log_info "Installing frontend dependencies..."
    npm ci
    
    # Create test reports directory
    mkdir -p test-reports/{unit,integration,e2e,coverage}
    
    print_header "Running Frontend Unit Tests"
    
    log_info "Testing components and services..."
    if npm run test:run; then
        log_success "Frontend unit tests passed"
        ((PASSED_TESTS++))
    else
        log_error "Frontend unit tests failed"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    
    print_header "Running Frontend Coverage"
    
    log_info "Generating frontend coverage..."
    npm run test:coverage || log_warning "Coverage generation issues"
    
    cd ..
}

# E2E testing (if requested)
run_e2e_tests() {
    log_phase "PHASE 3: End-to-End Testing"
    
    cd frontend
    
    log_info "Installing Playwright..."
    npx playwright install --with-deps
    
    print_header "Running E2E Tests"
    
    # Check if backend is accessible
    log_info "Checking backend accessibility..."
    if curl -f -s "http://localhost:8000/health" > /dev/null 2>&1; then
        log_success "Backend is accessible"
    else
        log_warning "Backend not accessible, starting test backend..."
        # Here we could start a test backend instance
    fi
    
    log_info "Running Playwright E2E tests..."
    if npx playwright test --reporter=html --output-dir=test-reports/e2e; then
        log_success "E2E tests passed"
        ((PASSED_TESTS++))
    else
        log_error "E2E tests failed"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    
    cd ..
}

# Code quality checks
run_quality_checks() {
    log_phase "PHASE 4: Code Quality Checks"
    
    print_header "Backend Code Quality"
    
    cd backend
    log_info "Running backend linting..."
    if uv run ruff check app/ && uv run ruff format app/ --check; then
        log_success "Backend linting passed"
        ((PASSED_TESTS++))
    else
        log_error "Backend linting failed"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    
    log_info "Running type checking..."
    if uv run mypy app/; then
        log_success "Type checking passed"
        ((PASSED_TESTS++))
    else
        log_error "Type checking failed"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    cd ..
    
    print_header "Frontend Code Quality"
    
    cd frontend
    log_info "Running frontend linting..."
    if npm run lint; then
        log_success "Frontend linting passed"
        ((PASSED_TESTS++))
    else
        log_error "Frontend linting failed"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    
    log_info "Running TypeScript compilation..."
    if npm run build; then
        log_success "TypeScript compilation passed"
        ((PASSED_TESTS++))
    else
        log_error "TypeScript compilation failed"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    cd ..
}

# Generate comprehensive report
generate_test_report() {
    print_header "Generating Test Report"
    
    local total_tests=$TOTAL_TESTS
    local success_rate=0
    
    if [[ $total_tests -gt 0 ]]; then
        success_rate=$(( (PASSED_TESTS * 100) / total_tests ))
    fi
    
    cat > test-reports/comprehensive-report.md << EOF
# Brain2Gain - Comprehensive Test Report

Generated on: $(date)

## Executive Summary

- **Total Test Suites**: $total_tests
- **Passed**: $PASSED_TESTS ✅
- **Failed**: $FAILED_TESTS ❌
- **Success Rate**: $success_rate%

## Test Phases Executed

### Phase 1: Backend Testing
- **Unit Tests**: Core functionality, models, services
- **API Tests**: Route handlers and integration
- **Security Tests**: Authentication and authorization
- **Coverage**: Generated in backend/test-reports/coverage/

### Phase 2: Frontend Testing  
- **Unit Tests**: Components, hooks, services
- **Coverage**: Generated in frontend/coverage/

### Phase 3: Code Quality
- **Backend**: Ruff linting, MyPy type checking
- **Frontend**: Biome linting, TypeScript compilation

## Coverage Targets (from testing_plan.yml)
- **Backend**: 90% overall target
- **Frontend**: 85% overall target

## Quality Gates Status

$(if [[ $success_rate -ge 90 ]]; then echo "✅ **PASSED**: All quality gates met"; else echo "❌ **FAILED**: Quality gates not met"; fi)

## Detailed Reports

- **Backend Coverage**: backend/test-reports/coverage/full/index.html
- **Frontend Coverage**: frontend/coverage/index.html
- **Test Results**: backend/test-reports/ and frontend/test-reports/

## Next Steps

$(if [[ $FAILED_TESTS -gt 0 ]]; then
    echo "### Issues to Address"
    echo "1. Review failed test cases and fix underlying issues"
    echo "2. Ensure all quality standards are met"
    echo "3. Re-run tests to validate fixes"
else
    echo "### Ready for Deployment"
    echo "✅ All tests passed - code quality validated"
    echo "✅ Quality gates met - ready for next phase"
fi)

---

*Generated by Brain2Gain Test Automation Suite*
*Based on testing_plan.yml specifications*
EOF

    log_success "Comprehensive test report generated: test-reports/comprehensive-report.md"
}

# Display final summary
display_summary() {
    print_header "Test Execution Summary"
    
    local total_tests=$TOTAL_TESTS
    local success_rate=0
    
    if [[ $total_tests -gt 0 ]]; then
        success_rate=$(( (PASSED_TESTS * 100) / total_tests ))
    fi
    
    echo -e "📊 ${BLUE}Test Results Summary${NC}"
    echo -e "   Total Suites: $total_tests"
    echo -e "   ${GREEN}Passed: $PASSED_TESTS${NC}"
    echo -e "   ${RED}Failed: $FAILED_TESTS${NC}"
    echo -e "   Success Rate: $success_rate%"
    echo ""
    
    if [[ $success_rate -ge 90 ]]; then
        echo -e "${GREEN}🎉 TESTING COMPLETED SUCCESSFULLY!${NC}"
        echo -e "${GREEN}✅ Quality gates met - ready for deployment${NC}"
    elif [[ $success_rate -ge 70 ]]; then
        echo -e "${YELLOW}⚠️  TESTING COMPLETED WITH WARNINGS${NC}"
        echo -e "${YELLOW}🔍 Review failed tests before proceeding${NC}"
    else
        echo -e "${RED}❌ TESTING FAILED${NC}"
        echo -e "${RED}🚨 Critical issues must be addressed${NC}"
    fi
    
    echo -e "\n📋 Reports available in: test-reports/"
    echo -e "📊 Comprehensive report: test-reports/comprehensive-report.md"
}

# Main execution
main() {
    print_banner
    
    local start_time=$(date +%s)
    
    # Parse arguments
    local run_backend=true
    local run_frontend=true
    local run_e2e=false
    local run_quality=true
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --backend-only)
                run_frontend=false
                run_e2e=false
                shift
                ;;
            --frontend-only)
                run_backend=false
                run_e2e=false
                shift
                ;;
            --with-e2e)
                run_e2e=true
                shift
                ;;
            --no-quality)
                run_quality=false
                shift
                ;;
            --fast)
                run_e2e=false
                run_quality=false
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --backend-only     Run only backend tests"
                echo "  --frontend-only    Run only frontend tests"
                echo "  --with-e2e         Include E2E tests"
                echo "  --no-quality       Skip quality checks"
                echo "  --fast             Skip E2E and quality checks"
                echo "  -h, --help         Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Check and setup test environment
    check_test_environment
    
    # Create master reports directory
    mkdir -p test-reports
    
    # Execute test phases
    [[ "$run_backend" == true ]] && run_backend_tests
    [[ "$run_frontend" == true ]] && run_frontend_tests
    [[ "$run_e2e" == true ]] && run_e2e_tests
    [[ "$run_quality" == true ]] && run_quality_checks
    
    # Generate comprehensive report
    generate_test_report
    
    # Calculate execution time
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))
    
    # Display summary
    display_summary
    
    echo -e "\n⏱️  ${BLUE}Total execution time: ${minutes}m ${seconds}s${NC}"
    
    # Exit with appropriate code
    if [[ $FAILED_TESTS -gt 0 ]]; then
        exit 1
    else
        exit 0
    fi
}

# Execute main function with all arguments
main "$@"