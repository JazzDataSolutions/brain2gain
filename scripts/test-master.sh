#!/usr/bin/env bash

# 🧪 Brain2Gain - Master Test Execution Script
# Orchestrates all testing phases according to testing_plan.yml

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

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS_DIR="${PROJECT_ROOT}/test-reports"
BACKEND_DIR="${PROJECT_ROOT}/backend"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"

# Test execution tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Initialize test environment
initialize_test_environment() {
    print_header "Initializing Test Environment"
    
    log_info "Setting up master test reports directory..."
    mkdir -p "${REPORTS_DIR}"/{master,backend,frontend,integration,security,performance}
    
    log_info "Checking project structure..."
    if [[ ! -d "$BACKEND_DIR" ]]; then
        log_error "Backend directory not found: $BACKEND_DIR"
        exit 1
    fi
    
    if [[ ! -d "$FRONTEND_DIR" ]]; then
        log_error "Frontend directory not found: $FRONTEND_DIR"
        exit 1
    fi
    
    log_info "Creating test execution log..."
    echo "Brain2Gain Test Execution Log - $(date)" > "${REPORTS_DIR}/test-execution.log"
    
    log_success "Test environment initialized"
}

# Backend testing phase
run_backend_tests() {
    log_phase "PHASE 1: Backend Testing"
    
    cd "$BACKEND_DIR"
    
    log_info "Running comprehensive backend tests..."
    if ./scripts/test-comprehensive.sh "$@"; then
        log_success "Backend tests passed"
        ((PASSED_TESTS++))
    else
        log_error "Backend tests failed"
        ((FAILED_TESTS++))
        return 1
    fi
    
    log_info "Running security tests..."
    if ./scripts/test-security.sh; then
        log_success "Backend security tests passed"
        ((PASSED_TESTS++))
    else
        log_warning "Backend security tests failed"
        ((FAILED_TESTS++))
    fi
    
    log_info "Running performance tests..."
    if ./scripts/test-performance.sh; then
        log_success "Backend performance tests passed"
        ((PASSED_TESTS++))
    else
        log_warning "Backend performance tests failed"
        ((FAILED_TESTS++))
    fi
    
    cd "$PROJECT_ROOT"
}

# Frontend testing phase
run_frontend_tests() {
    log_phase "PHASE 2: Frontend Testing"
    
    cd "$FRONTEND_DIR"
    
    log_info "Running comprehensive frontend tests..."
    if ./scripts/test-comprehensive.sh "$@"; then
        log_success "Frontend tests passed"
        ((PASSED_TESTS++))
    else
        log_error "Frontend tests failed"
        ((FAILED_TESTS++))
        return 1
    fi
    
    log_info "Running E2E tests..."
    if ./scripts/test-e2e-comprehensive.sh "$@"; then
        log_success "Frontend E2E tests passed"
        ((PASSED_TESTS++))
    else
        log_warning "Frontend E2E tests failed"
        ((FAILED_TESTS++))
    fi
    
    cd "$PROJECT_ROOT"
}

# Integration testing phase
run_integration_tests() {
    log_phase "PHASE 3: Full Stack Integration Testing"
    
    log_info "Starting development environment..."
    make dev
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    log_info "Running full stack integration tests..."
    if make test-integration; then
        log_success "Integration tests passed"
        ((PASSED_TESTS++))
    else
        log_error "Integration tests failed"
        ((FAILED_TESTS++))
    fi
    
    log_info "Stopping development environment..."
    make stop
}

# Code quality checks
run_quality_checks() {
    log_phase "PHASE 4: Code Quality Checks"
    
    log_info "Running linting checks..."
    if make lint; then
        log_success "Linting passed"
        ((PASSED_TESTS++))
    else
        log_error "Linting failed"
        ((FAILED_TESTS++))
    fi
    
    log_info "Running type checking..."
    if make type-check; then
        log_success "Type checking passed"
        ((PASSED_TESTS++))
    else
        log_error "Type checking failed"
        ((FAILED_TESTS++))
    fi
}

# Generate master test report
generate_master_report() {
    print_header "Generating Master Test Report"
    
    local total_tests=$((PASSED_TESTS + FAILED_TESTS + SKIPPED_TESTS))
    local success_rate=0
    
    if [[ $total_tests -gt 0 ]]; then
        success_rate=$(( (PASSED_TESTS * 100) / total_tests ))
    fi
    
    cat > "${REPORTS_DIR}/master-test-report.md" << EOF
# Brain2Gain - Master Test Report

Generated on: $(date)

## Executive Summary

- **Total Test Suites**: $total_tests
- **Passed**: $PASSED_TESTS ✅
- **Failed**: $FAILED_TESTS ❌
- **Skipped**: $SKIPPED_TESTS ⏭️
- **Success Rate**: $success_rate%

## Test Phases Executed

### Phase 1: Backend Testing
- **Comprehensive Backend Tests**: Unit, Integration, API endpoints
- **Security Testing**: Authentication, authorization, input validation
- **Performance Testing**: Load testing, database performance
- **Reports**: [Backend Reports](backend/)

### Phase 2: Frontend Testing  
- **Unit Tests**: Components, hooks, services, stores
- **Integration Tests**: API integration, page flows
- **E2E Tests**: Critical user journeys, accessibility
- **Performance Tests**: Lighthouse audits, bundle analysis
- **Reports**: [Frontend Reports](frontend/)

### Phase 3: Full Stack Integration
- **End-to-End Integration**: Complete application flows
- **Cross-Service Communication**: API interactions
- **Database Integration**: Data consistency across services
- **Reports**: [Integration Reports](integration/)

### Phase 4: Code Quality
- **Linting**: Code style and quality standards
- **Type Checking**: TypeScript and Python type safety
- **Security Scanning**: Dependency vulnerabilities
- **Reports**: [Quality Reports](quality/)

## Test Coverage

### Backend Coverage
- **Target**: 90% overall coverage
- **Models**: 95% target
- **Services**: 90% target  
- **Repositories**: 95% target

### Frontend Coverage
- **Target**: 85% overall coverage
- **Components**: 90% target
- **Hooks**: 85% target
- **Services**: 85% target

## Performance Metrics

### Backend Performance
- **API Response Time**: < 200ms (95th percentile)
- **Database Queries**: < 100ms average
- **Load Testing**: 100 concurrent users

### Frontend Performance
- **Lighthouse Performance**: > 90
- **Bundle Size**: < 1MB gzipped
- **Page Load**: < 2 seconds

## Security Validation

### Authentication Security
- JWT validation and tampering resistance
- Password security and hashing
- Session management
- Rate limiting

### API Security
- Input validation and SQL injection prevention
- CORS configuration
- Data sanitization and XSS prevention
- Role-based access control

## Quality Gates Status

$(if [[ $success_rate -ge 90 ]]; then echo "✅ **PASSED**: All quality gates met"; else echo "❌ **FAILED**: Quality gates not met"; fi)

- Code Coverage: $(if [[ $success_rate -ge 85 ]]; then echo "✅ PASSED"; else echo "❌ FAILED"; fi)
- Security Scan: $(if [[ $FAILED_TESTS -eq 0 ]]; then echo "✅ PASSED"; else echo "⚠️ REVIEW NEEDED"; fi)
- Performance: $(if [[ $success_rate -ge 90 ]]; then echo "✅ PASSED"; else echo "❌ FAILED"; fi)
- E2E Tests: $(if [[ $success_rate -ge 95 ]]; then echo "✅ PASSED"; else echo "❌ FAILED"; fi)

## Next Steps

$(if [[ $FAILED_TESTS -gt 0 ]]; then
    echo "### Issues to Address"
    echo "1. Review failed test cases and fix underlying issues"
    echo "2. Ensure all security vulnerabilities are addressed"
    echo "3. Optimize performance bottlenecks identified"
    echo "4. Re-run tests to validate fixes"
else
    echo "### Deployment Ready"
    echo "✅ All tests passed - ready for deployment"
    echo "✅ Quality gates met - code quality validated"
    echo "✅ Security checks passed - no critical vulnerabilities"
    echo "✅ Performance targets achieved - ready for production"
fi)

## Detailed Reports

- **Backend**: [Backend Test Report](backend/test-reports/)
- **Frontend**: [Frontend Test Report](frontend/test-reports/)
- **E2E**: [E2E Test Report](frontend/e2e-reports/)
- **Security**: [Security Report](backend/security-reports/)
- **Performance**: [Performance Report](backend/performance-reports/)

---

*Generated by Brain2Gain Test Automation Suite*
*Based on testing_plan.yml specifications*
EOF

    log_success "Master test report generated: ${REPORTS_DIR}/master-test-report.md"
}

# Display test summary
display_summary() {
    print_header "Test Execution Summary"
    
    local total_tests=$((PASSED_TESTS + FAILED_TESTS + SKIPPED_TESTS))
    local success_rate=0
    
    if [[ $total_tests -gt 0 ]]; then
        success_rate=$(( (PASSED_TESTS * 100) / total_tests ))
    fi
    
    echo -e "📊 ${BLUE}Test Results Summary${NC}"
    echo -e "   Total Suites: $total_tests"
    echo -e "   ${GREEN}Passed: $PASSED_TESTS${NC}"
    echo -e "   ${RED}Failed: $FAILED_TESTS${NC}"
    echo -e "   ${YELLOW}Skipped: $SKIPPED_TESTS${NC}"
    echo -e "   Success Rate: $success_rate%"
    echo ""
    
    if [[ $success_rate -ge 90 ]]; then
        echo -e "${GREEN}🎉 TESTING COMPLETED SUCCESSFULLY!${NC}"
        echo -e "${GREEN}✅ Quality gates met - ready for deployment${NC}"
    elif [[ $success_rate -ge 75 ]]; then
        echo -e "${YELLOW}⚠️  TESTING COMPLETED WITH WARNINGS${NC}"
        echo -e "${YELLOW}🔍 Review failed tests before deployment${NC}"
    else
        echo -e "${RED}❌ TESTING FAILED${NC}"
        echo -e "${RED}🚨 Critical issues must be addressed${NC}"
    fi
    
    echo -e "\n📋 Reports available in: ${REPORTS_DIR}/"
    echo -e "📊 Master report: ${REPORTS_DIR}/master-test-report.md"
}

# Main execution function
main() {
    print_banner
    
    local start_time=$(date +%s)
    
    # Parse command line arguments
    local run_backend=true
    local run_frontend=true
    local run_integration=true
    local run_quality=true
    local skip_e2e=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --backend-only)
                run_frontend=false
                run_integration=false
                run_quality=false
                shift
                ;;
            --frontend-only)
                run_backend=false
                run_integration=false
                run_quality=false
                shift
                ;;
            --no-integration)
                run_integration=false
                shift
                ;;
            --no-e2e)
                skip_e2e=true
                shift
                ;;
            --fast)
                run_integration=false
                skip_e2e=true
                shift
                ;;
            --ci)
                # CI mode - all tests but optimized
                skip_e2e=false
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --backend-only     Run only backend tests"
                echo "  --frontend-only    Run only frontend tests"
                echo "  --no-integration   Skip integration tests"
                echo "  --no-e2e          Skip E2E tests"
                echo "  --fast            Run only unit and integration tests"
                echo "  --ci              CI mode - all tests optimized"
                echo "  -h, --help        Show this help message"
                echo ""
                echo "Examples:"
                echo "  $0                    # Run all tests"
                echo "  $0 --fast            # Quick test run"
                echo "  $0 --backend-only     # Backend tests only"
                echo "  $0 --ci               # CI pipeline mode"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Initialize
    initialize_test_environment
    
    # Execute test phases
    if [[ "$run_backend" == true ]]; then
        if [[ "$skip_e2e" == true ]]; then
            run_backend_tests --fast
        else
            run_backend_tests
        fi
    fi
    
    if [[ "$run_frontend" == true ]]; then
        if [[ "$skip_e2e" == true ]]; then
            run_frontend_tests --no-e2e
        else
            run_frontend_tests
        fi
    fi
    
    if [[ "$run_integration" == true ]]; then
        run_integration_tests
    fi
    
    if [[ "$run_quality" == true ]]; then
        run_quality_checks
    fi
    
    # Generate reports
    generate_master_report
    
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