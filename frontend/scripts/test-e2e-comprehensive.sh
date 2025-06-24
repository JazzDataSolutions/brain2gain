#!/usr/bin/env bash

# 🎭 Brain2Gain - Comprehensive E2E Testing Script
# Critical user journeys and accessibility testing

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
    echo -e "${BLUE}🎭 $1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

setup_e2e_environment() {
    print_header "Setting up E2E Test Environment"
    
    log_info "Installing Playwright browsers..."
    npx playwright install --with-deps
    
    log_info "Creating E2E test reports directory..."
    mkdir -p e2e-reports/{critical-journeys,accessibility,performance,cross-browser}
    
    log_success "E2E environment setup complete"
}

run_critical_user_journeys() {
    print_header "Running Critical User Journeys"
    
    log_info "Testing guest purchase flow..."
    npx playwright test tests/e2e/guest-purchase-flow.spec.ts \
        --reporter=html --output-dir=e2e-reports/critical-journeys/guest-purchase
    
    log_info "Testing registered user flow..."
    npx playwright test tests/e2e/registered-user-flow.spec.ts \
        --reporter=html --output-dir=e2e-reports/critical-journeys/registered-user
    
    log_info "Testing admin operations..."
    npx playwright test tests/e2e/admin-operations.spec.ts \
        --reporter=html --output-dir=e2e-reports/critical-journeys/admin-operations
    
    log_success "Critical user journeys completed"
}

run_accessibility_tests() {
    print_header "Running Accessibility Tests"
    
    log_info "Testing keyboard navigation..."
    npx playwright test tests/accessibility/keyboard-navigation.spec.ts \
        --reporter=html --output-dir=e2e-reports/accessibility/keyboard
    
    log_info "Testing screen reader compatibility..."
    npx playwright test tests/accessibility/screen-reader.spec.ts \
        --reporter=html --output-dir=e2e-reports/accessibility/screen-reader
    
    log_info "Testing color contrast..."
    npx playwright test tests/accessibility/color-contrast.spec.ts \
        --reporter=html --output-dir=e2e-reports/accessibility/color-contrast
    
    log_info "Testing responsive design..."
    npx playwright test tests/accessibility/responsive-design.spec.ts \
        --reporter=html --output-dir=e2e-reports/accessibility/responsive
    
    log_success "Accessibility tests completed"
}

run_cross_browser_tests() {
    print_header "Running Cross-Browser Tests"
    
    log_info "Testing on Chromium..."
    npx playwright test --project=chromium \
        --reporter=html --output-dir=e2e-reports/cross-browser/chromium
    
    log_info "Testing on Firefox..."
    npx playwright test --project=firefox \
        --reporter=html --output-dir=e2e-reports/cross-browser/firefox
    
    log_info "Testing on WebKit..."
    npx playwright test --project=webkit \
        --reporter=html --output-dir=e2e-reports/cross-browser/webkit
    
    log_success "Cross-browser tests completed"
}

run_performance_e2e_tests() {
    print_header "Running Performance E2E Tests"
    
    log_info "Testing page load performance..."
    npx playwright test tests/performance/page-load-performance.spec.ts \
        --reporter=html --output-dir=e2e-reports/performance/page-load
    
    log_info "Testing interaction performance..."
    npx playwright test tests/performance/interaction-performance.spec.ts \
        --reporter=html --output-dir=e2e-reports/performance/interactions
    
    log_success "Performance E2E tests completed"
}

generate_e2e_report() {
    print_header "Generating E2E Test Report"
    
    cat > e2e-reports/e2e-summary.md << EOF
# Brain2Gain E2E Test Report

Generated on: $(date)

## Critical User Journeys

### Guest Purchase Flow
- Visit landing page
- Browse product catalog with filters and search
- Add products to cart
- Proceed to checkout as guest
- Fill shipping and payment information
- Complete purchase flow
- **Status**: [View Report](critical-journeys/guest-purchase/index.html)

### Registered User Flow  
- User registration with email verification
- Login and browse products
- Add items to cart with quantity modifications
- Complete purchase as registered user
- View order history and details
- **Status**: [View Report](critical-journeys/registered-user/index.html)

### Admin Operations
- Admin login with proper authentication
- Product management (CRUD operations)
- Order management and status updates
- Analytics dashboard functionality
- User management capabilities
- **Status**: [View Report](critical-journeys/admin-operations/index.html)

## Accessibility Testing

### Keyboard Navigation
- Tab navigation through all interactive elements
- Enter/Space activation of buttons and links
- Arrow key navigation in lists and menus
- Escape key functionality for modals
- **Status**: [View Report](accessibility/keyboard/index.html)

### Screen Reader Compatibility
- ARIA labels and roles properly implemented
- Semantic HTML structure
- Alternative text for images
- Form labels and descriptions
- **Status**: [View Report](accessibility/screen-reader/index.html)

### Color Contrast
- WCAG AA compliance for all text
- Sufficient contrast ratios
- Color-blind friendly design
- **Status**: [View Report](accessibility/color-contrast/index.html)

### Responsive Design
- Mobile device compatibility (320px+)
- Tablet layout optimization
- Desktop full functionality
- Touch-friendly interaction areas
- **Status**: [View Report](accessibility/responsive/index.html)

## Cross-Browser Testing

### Browser Support
- **Chromium**: [Results](cross-browser/chromium/index.html)
- **Firefox**: [Results](cross-browser/firefox/index.html)  
- **WebKit**: [Results](cross-browser/webkit/index.html)

## Performance Testing

### Page Load Performance
- First Contentful Paint < 1.5s
- Largest Contentful Paint < 2.5s
- Time to Interactive < 3s
- **Status**: [View Report](performance/page-load/index.html)

### Interaction Performance
- Button click responsiveness
- Form submission performance
- Page navigation speed
- **Status**: [View Report](performance/interactions/index.html)

## Test Environment
- **Frontend URL**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Test Data**: Isolated test database
- **Browsers**: Chromium, Firefox, WebKit

## Quality Gates
- ✅ All critical user journeys must pass
- ✅ WCAG AA accessibility compliance  
- ✅ Cross-browser compatibility
- ✅ Performance thresholds met
- ✅ No console errors during flows

EOF

    log_success "E2E report generated: e2e-reports/e2e-summary.md"
}

main() {
    print_header "Brain2Gain E2E Testing Suite"
    
    # Parse arguments
    local run_journeys=true
    local run_accessibility=true
    local run_cross_browser=true
    local run_performance=true
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --journeys-only)
                run_accessibility=false
                run_cross_browser=false
                run_performance=false
                shift
                ;;
            --accessibility-only)
                run_journeys=false
                run_cross_browser=false
                run_performance=false
                shift
                ;;
            --no-cross-browser)
                run_cross_browser=false
                shift
                ;;
            --fast)
                run_cross_browser=false
                run_performance=false
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --journeys-only      Run only critical user journeys"
                echo "  --accessibility-only Run only accessibility tests"
                echo "  --no-cross-browser  Skip cross-browser testing"
                echo "  --fast              Skip time-consuming tests"
                echo "  -h, --help          Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    setup_e2e_environment
    
    [[ "$run_journeys" == true ]] && run_critical_user_journeys
    [[ "$run_accessibility" == true ]] && run_accessibility_tests
    [[ "$run_cross_browser" == true ]] && run_cross_browser_tests
    [[ "$run_performance" == true ]] && run_performance_e2e_tests
    
    generate_e2e_report
    
    log_success "E2E testing completed! Check e2e-reports/ for detailed results."
    log_info "Main report: e2e-reports/e2e-summary.md"
}

main "$@"