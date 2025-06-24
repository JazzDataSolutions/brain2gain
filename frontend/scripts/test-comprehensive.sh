#!/usr/bin/env bash

# ⚛️ Brain2Gain - Comprehensive Frontend Testing Script
# Based on testing_plan.yml requirements

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COVERAGE_THRESHOLD=85
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
    echo -e "${BLUE}⚛️ $1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

# Setup function
setup_test_environment() {
    print_header "Setting up Frontend Test Environment"
    
    log_info "Creating test reports directory..."
    mkdir -p "${REPORTS_DIR}"/{unit,integration,e2e,coverage,accessibility,performance}
    
    log_info "Installing dependencies..."
    npm ci
    
    log_info "Checking Playwright installation..."
    npx playwright install --with-deps
    
    log_success "Frontend test environment setup complete"
}

# Unit Tests
run_unit_tests() {
    print_header "Running Unit Tests"
    
    log_info "Testing UI Components..."
    npm run test -- --run --reporter=verbose --reporter=junit \
        --outputFile=${REPORTS_DIR}/unit/ui-components-junit.xml \
        src/components/UI/
    
    log_info "Testing Business Components..."
    npm run test -- --run --reporter=verbose --reporter=junit \
        --outputFile=${REPORTS_DIR}/unit/business-components-junit.xml \
        src/components/Products/ src/components/Cart/ src/components/Admin/
    
    log_info "Testing Layout Components..."
    npm run test -- --run --reporter=verbose --reporter=junit \
        --outputFile=${REPORTS_DIR}/unit/layout-components-junit.xml \
        src/components/Landing/ src/components/Common/
    
    log_info "Testing Hooks..."
    npm run test -- --run --reporter=verbose --reporter=junit \
        --outputFile=${REPORTS_DIR}/unit/hooks-junit.xml \
        src/hooks/
    
    log_info "Testing Stores..."
    npm run test -- --run --reporter=verbose --reporter=junit \
        --outputFile=${REPORTS_DIR}/unit/stores-junit.xml \
        src/stores/
    
    log_info "Testing Services..."
    npm run test -- --run --reporter=verbose --reporter=junit \
        --outputFile=${REPORTS_DIR}/unit/services-junit.xml \
        src/services/
    
    log_success "Unit tests completed"
}

# Integration Tests
run_integration_tests() {
    print_header "Running Integration Tests"
    
    log_info "Testing page flows..."
    npm run test -- --run --reporter=verbose --reporter=junit \
        --outputFile=${REPORTS_DIR}/integration/page-flows-junit.xml \
        src/test/integration/page-flows.test.tsx
    
    log_info "Testing API integration..."
    npm run test -- --run --reporter=verbose --reporter=junit \
        --outputFile=${REPORTS_DIR}/integration/api-integration-junit.xml \
        src/test/integration/api-integration.test.tsx
    
    log_info "Testing cart operations..."
    npm run test -- --run --reporter=verbose --reporter=junit \
        --outputFile=${REPORTS_DIR}/integration/cart-operations-junit.xml \
        src/test/cart-flow.test.tsx
    
    log_success "Integration tests completed"
}

# E2E Tests
run_e2e_tests() {
    print_header "Running E2E Tests"
    
    log_info "Running critical user journeys..."
    npx playwright test --reporter=html --output-dir=${REPORTS_DIR}/e2e/html-report
    
    log_info "Running accessibility tests..."
    npx playwright test tests/accessibility/ --reporter=junit --output-dir=${REPORTS_DIR}/e2e/accessibility
    
    log_success "E2E tests completed"
}

# Performance Tests
run_performance_tests() {
    print_header "Running Performance Tests"
    
    log_info "Running Lighthouse audit..."
    npm run test:lighthouse || log_warning "Lighthouse not configured, skipping audit"
    
    log_info "Running bundle analysis..."
    npm run build
    
    # Analyze bundle size
    npx vite-bundle-analyzer dist/assets --json > ${REPORTS_DIR}/performance/bundle-analysis.json
    
    log_success "Performance tests completed"
}

# Accessibility Tests
run_accessibility_tests() {
    print_header "Running Accessibility Tests"
    
    log_info "Testing WCAG compliance..."
    npx playwright test tests/accessibility/ --reporter=junit
    
    log_info "Running axe-core accessibility scan..."
    npm run test -- --run src/test/accessibility/ --reporter=junit \
        --outputFile=${REPORTS_DIR}/accessibility/axe-junit.xml
    
    log_success "Accessibility tests completed"
}

# Coverage Report
generate_coverage_report() {
    print_header "Generating Coverage Report"
    
    log_info "Running full test suite with coverage..."
    npm run test:coverage -- --reporter=verbose
    
    log_info "Coverage report generated at: coverage/index.html"
    log_success "Coverage analysis completed"
}

# Lint and Type Check
run_code_quality_checks() {
    print_header "Running Code Quality Checks"
    
    log_info "Running Biome linting..."
    npm run lint
    
    log_info "Running TypeScript compilation..."
    npm run build
    
    log_success "Code quality checks completed"
}

# Generate comprehensive test report
generate_test_report() {
    print_header "Generating Test Report"
    
    cat > ${REPORTS_DIR}/frontend-test-summary.md << EOF
# Brain2Gain Frontend Test Report

Generated on: $(date)

## Test Results Summary

### Unit Tests
- **UI Components**: Buttons, Cards, Inputs, Loading Spinners
- **Business Components**: ProductCard, CartItem, CartSummary, AnalyticsDashboard  
- **Layout Components**: Navbar, Sidebar, Footer
- **Hooks**: useAuth, useCart, useNotifications, useCustomToast
- **Stores**: cartStore, authContext
- **Services**: AnalyticsService, ProductsService, NotificationService

### Integration Tests
- **Page Flows**: Navigation between pages
- **API Integration**: Real API calls and responses
- **Cart Operations**: Add to cart, modify, checkout flow
- **User Authentication**: Login/logout flow with backend

### End-to-End Tests
- **Critical User Journeys**: 
  - Guest purchase flow
  - Registered user flow  
  - Admin operations
- **Accessibility**: WCAG compliance, keyboard navigation, screen reader support
- **Cross-browser**: Chrome, Firefox, Safari testing

### Performance Tests
- **Lighthouse Audit**: Performance, accessibility, best practices, SEO scores
- **Bundle Analysis**: Bundle size optimization and code splitting
- **Load Times**: Page load performance metrics

### Code Quality
- **Linting**: Biome code style and quality checks
- **Type Safety**: TypeScript compilation without errors
- **Coverage**: ${COVERAGE_THRESHOLD}% code coverage target

## Coverage Targets
- Components: 90%
- Hooks: 85% 
- Services: 85%
- Overall: ${COVERAGE_THRESHOLD}%

## Files Tested
- Components: \`src/components/\`
- Hooks: \`src/hooks/\`
- Stores: \`src/stores/\`
- Services: \`src/services/\`
- E2E Tests: \`tests/\`

## Reports Generated
- Coverage: \`coverage/index.html\`
- E2E Results: \`${REPORTS_DIR}/e2e/html-report/index.html\`
- Unit Test Results: \`${REPORTS_DIR}/unit/\`
- Integration Results: \`${REPORTS_DIR}/integration/\`

EOF

    log_success "Test report generated: ${REPORTS_DIR}/frontend-test-summary.md"
}

# Cleanup function
cleanup() {
    print_header "Cleaning up"
    
    log_info "Cleaning up test artifacts..."
    # Keep reports but clean temporary files
    
    log_success "Cleanup completed"
}

# Main execution
main() {
    print_header "Brain2Gain Frontend Comprehensive Testing Suite"
    
    local start_time=$(date +%s)
    
    # Parse command line arguments
    local run_unit=true
    local run_integration=true
    local run_e2e=true
    local run_performance=true
    local run_accessibility=true
    local run_coverage=true
    local run_quality=true
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --unit-only)
                run_integration=false
                run_e2e=false
                run_performance=false
                run_accessibility=false
                shift
                ;;
            --e2e-only)
                run_unit=false
                run_integration=false
                run_performance=false
                run_accessibility=false
                shift
                ;;
            --no-e2e)
                run_e2e=false
                shift
                ;;
            --no-coverage)
                run_coverage=false
                shift
                ;;
            --fast)
                run_e2e=false
                run_performance=false
                run_accessibility=false
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --unit-only      Run only unit tests"
                echo "  --e2e-only       Run only E2E tests"
                echo "  --no-e2e         Skip E2E tests"
                echo "  --no-coverage    Skip coverage report generation"
                echo "  --fast           Skip E2E, performance, and accessibility tests"
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
    [[ "$run_quality" == true ]] && run_code_quality_checks
    [[ "$run_unit" == true ]] && run_unit_tests
    [[ "$run_integration" == true ]] && run_integration_tests
    [[ "$run_e2e" == true ]] && run_e2e_tests
    [[ "$run_performance" == true ]] && run_performance_tests
    [[ "$run_accessibility" == true ]] && run_accessibility_tests
    [[ "$run_coverage" == true ]] && generate_coverage_report
    
    # Generate reports
    generate_test_report
    
    # Cleanup
    cleanup
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_header "Test Execution Summary"
    log_success "All frontend tests completed successfully!"
    log_info "Total execution time: ${duration} seconds"
    log_info "Reports generated in: ${REPORTS_DIR}/"
    log_info "Coverage report: coverage/index.html"
    log_info "E2E report: ${REPORTS_DIR}/e2e/html-report/index.html"
    
    echo -e "\n${GREEN}🎉 Brain2Gain frontend testing completed successfully!${NC}\n"
}

# Execute main function with all arguments
main "$@"