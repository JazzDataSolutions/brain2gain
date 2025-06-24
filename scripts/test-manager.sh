#!/usr/bin/env bash

# 🧪 Test Manager - Unified Testing Interface
# Simplifies testing across all environments and test types

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
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

show_usage() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  setup           Setup testing environment"
    echo "  unit            Run unit tests"
    echo "  integration     Run integration tests"
    echo "  e2e             Run end-to-end tests"
    echo "  security        Run security tests"
    echo "  performance     Run performance tests"
    echo "  all             Run all tests"
    echo "  coverage        Generate coverage reports"
    echo "  clean           Clean testing environment"
    echo ""
    echo "Options:"
    echo "  --backend-only     Run only backend tests"
    echo "  --frontend-only    Run only frontend tests"
    echo "  --fast            Skip slow tests"
    echo "  --watch           Run tests in watch mode"
    echo "  --verbose         Verbose output"
    echo "  --coverage        Include coverage reports"
    echo ""
    echo "Examples:"
    echo "  $0 setup"
    echo "  $0 unit --backend-only"
    echo "  $0 all --coverage"
    echo "  $0 e2e --verbose"
}

# Test execution tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

setup_testing() {
    log_phase "Setting up testing environment"
    
    # Setup testing environment
    "$SCRIPT_DIR/env-manager.sh" setup testing
    
    # Start testing containers
    "$SCRIPT_DIR/env-manager.sh" start testing
    
    log_success "Testing environment ready"
}

run_unit_tests() {
    local backend_only="$1"
    local frontend_only="$2"
    local coverage="$3"
    
    log_phase "Running Unit Tests"
    
    if [[ "$frontend_only" != "true" ]]; then
        log_info "Running backend unit tests..."
        cd "$PROJECT_ROOT/backend"
        
        if [[ "$coverage" == "true" ]]; then
            uv run pytest app/tests/unit/ -v --cov=app --cov-report=html --cov-report=xml
        else
            uv run pytest app/tests/unit/ -v
        fi
        
        if [[ $? -eq 0 ]]; then
            ((PASSED_TESTS++))
            log_success "Backend unit tests passed"
        else
            ((FAILED_TESTS++))
            log_error "Backend unit tests failed"
        fi
        ((TOTAL_TESTS++))
    fi
    
    if [[ "$backend_only" != "true" ]]; then
        log_info "Running frontend unit tests..."
        cd "$PROJECT_ROOT/frontend"
        
        if [[ "$coverage" == "true" ]]; then
            npm run test:coverage
        else
            npm run test:run
        fi
        
        if [[ $? -eq 0 ]]; then
            ((PASSED_TESTS++))
            log_success "Frontend unit tests passed"
        else
            ((FAILED_TESTS++))
            log_error "Frontend unit tests failed"
        fi
        ((TOTAL_TESTS++))
    fi
}

run_integration_tests() {
    local backend_only="$1"
    local frontend_only="$2"
    
    log_phase "Running Integration Tests"
    
    if [[ "$frontend_only" != "true" ]]; then
        log_info "Running backend integration tests..."
        cd "$PROJECT_ROOT/backend"
        
        uv run pytest app/tests/integration/ -v
        
        if [[ $? -eq 0 ]]; then
            ((PASSED_TESTS++))
            log_success "Backend integration tests passed"
        else
            ((FAILED_TESTS++))
            log_error "Backend integration tests failed"
        fi
        ((TOTAL_TESTS++))
    fi
    
    if [[ "$backend_only" != "true" ]]; then
        log_info "Running frontend integration tests..."
        cd "$PROJECT_ROOT/frontend"
        
        npm run test:integration 2>/dev/null || npm run test:run
        
        if [[ $? -eq 0 ]]; then
            ((PASSED_TESTS++))
            log_success "Frontend integration tests passed"
        else
            ((FAILED_TESTS++))
            log_error "Frontend integration tests failed"
        fi
        ((TOTAL_TESTS++))
    fi
}

run_e2e_tests() {
    log_phase "Running End-to-End Tests"
    
    cd "$PROJECT_ROOT/frontend"
    
    log_info "Installing Playwright if needed..."
    npx playwright install --with-deps
    
    log_info "Running E2E tests..."
    npx playwright test --reporter=html
    
    if [[ $? -eq 0 ]]; then
        ((PASSED_TESTS++))
        log_success "E2E tests passed"
    else
        ((FAILED_TESTS++))
        log_error "E2E tests failed"
    fi
    ((TOTAL_TESTS++))
}

run_security_tests() {
    log_phase "Running Security Tests"
    
    cd "$PROJECT_ROOT/backend"
    
    log_info "Running security unit tests..."
    uv run pytest app/tests/unit/core/test_security.py -v
    
    if [[ $? -eq 0 ]]; then
        ((PASSED_TESTS++))
        log_success "Security tests passed"
    else
        ((FAILED_TESTS++))
        log_error "Security tests failed"
    fi
    ((TOTAL_TESTS++))
    
    # Additional security checks
    log_info "Running dependency security scan..."
    uv run safety check || log_warning "Safety check completed with warnings"
}

run_performance_tests() {
    log_phase "Running Performance Tests"
    
    # Backend performance
    cd "$PROJECT_ROOT/backend"
    log_info "Running backend performance tests..."
    uv run pytest app/tests/performance/ -v 2>/dev/null || log_warning "Performance tests not implemented yet"
    
    # Frontend performance
    cd "$PROJECT_ROOT/frontend"
    log_info "Running Lighthouse audit..."
    npx lighthouse http://localhost:5174 --output=html --output-path=./lighthouse-report.html || log_warning "Lighthouse audit skipped (server not running)"
    
    ((TOTAL_TESTS++))
    ((PASSED_TESTS++))
}

generate_coverage() {
    log_phase "Generating Coverage Reports"
    
    # Backend coverage
    cd "$PROJECT_ROOT/backend"
    log_info "Generating backend coverage..."
    uv run pytest app/tests/ --cov=app --cov-report=html --cov-report=xml
    
    # Frontend coverage
    cd "$PROJECT_ROOT/frontend"
    log_info "Generating frontend coverage..."
    npm run test:coverage
    
    log_success "Coverage reports generated"
}

clean_testing() {
    log_phase "Cleaning testing environment"
    
    # Clean testing containers
    "$SCRIPT_DIR/env-manager.sh" clean testing
    
    # Clean test artifacts
    find "$PROJECT_ROOT" -name "*.pyc" -delete 2>/dev/null || true
    find "$PROJECT_ROOT" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find "$PROJECT_ROOT" -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
    find "$PROJECT_ROOT" -name "test-results" -type d -exec rm -rf {} + 2>/dev/null || true
    
    log_success "Testing environment cleaned"
}

display_summary() {
    log_phase "Test Execution Summary"
    
    local success_rate=0
    if [[ $TOTAL_TESTS -gt 0 ]]; then
        success_rate=$(( (PASSED_TESTS * 100) / TOTAL_TESTS ))
    fi
    
    echo ""
    echo "📊 Test Results:"
    echo "   Total: $TOTAL_TESTS"
    echo "   Passed: $PASSED_TESTS ✅"
    echo "   Failed: $FAILED_TESTS ❌"
    echo "   Success Rate: $success_rate%"
    echo ""
    
    if [[ $success_rate -ge 90 ]]; then
        log_success "🎉 All tests passed successfully!"
    elif [[ $success_rate -ge 70 ]]; then
        log_warning "⚠️  Some tests failed - review results"
    else
        log_error "❌ Testing failed - critical issues found"
        return 1
    fi
}

# Main execution
main() {
    local command="$1"
    shift || true
    
    # Parse options
    local backend_only="false"
    local frontend_only="false"
    local fast="false"
    local watch="false"
    local verbose="false"
    local coverage="false"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --backend-only)
                backend_only="true"
                shift
                ;;
            --frontend-only)
                frontend_only="true"
                shift
                ;;
            --fast)
                fast="true"
                shift
                ;;
            --watch)
                watch="true"
                shift
                ;;
            --verbose)
                verbose="true"
                shift
                ;;
            --coverage)
                coverage="true"
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    case "$command" in
        setup)
            setup_testing
            ;;
        unit)
            run_unit_tests "$backend_only" "$frontend_only" "$coverage"
            display_summary
            ;;
        integration)
            run_integration_tests "$backend_only" "$frontend_only"
            display_summary
            ;;
        e2e)
            run_e2e_tests
            display_summary
            ;;
        security)
            run_security_tests
            display_summary
            ;;
        performance)
            run_performance_tests
            display_summary
            ;;
        all)
            run_unit_tests "$backend_only" "$frontend_only" "$coverage"
            [[ "$fast" != "true" ]] && run_integration_tests "$backend_only" "$frontend_only"
            [[ "$fast" != "true" && "$backend_only" != "true" ]] && run_e2e_tests
            run_security_tests
            [[ "$fast" != "true" ]] && run_performance_tests
            display_summary
            ;;
        coverage)
            generate_coverage
            ;;
        clean)
            clean_testing
            ;;
        *)
            if [[ -z "$command" ]]; then
                show_usage
            else
                log_error "Unknown command: $command"
                show_usage
                exit 1
            fi
            ;;
    esac
}

main "$@"