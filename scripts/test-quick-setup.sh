#!/usr/bin/env bash

# 🚀 Brain2Gain - Quick Testing Setup and Execution Guide
# One-stop script for setting up and running the comprehensive testing suite

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

print_banner() {
    echo -e "${PURPLE}"
    echo "🧪 BRAIN2GAIN TESTING SUITE QUICK SETUP 🧪"
    echo "=========================================="
    echo -e "${NC}"
}

print_menu() {
    echo -e "${BLUE}Choose an option:${NC}"
    echo "1. 🛠️  Setup testing environment"
    echo "2. 🧪 Run quick tests (unit + integration)"
    echo "3. 🏃 Run full test suite"
    echo "4. 🎭 Run E2E tests only"
    echo "5. 🔒 Run security tests"
    echo "6. ⚡ Run performance tests"
    echo "7. 📊 Generate test reports"
    echo "8. 🔍 Check test status"
    echo "9. 🧹 Clean test artifacts"
    echo "0. ❓ Show help"
    echo "q. 🚪 Quit"
    echo ""
}

setup_environment() {
    log_info "Setting up Brain2Gain testing environment..."
    
    # Check dependencies
    log_info "Checking dependencies..."
    
    # Check Python and uv
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    if ! command -v uv &> /dev/null; then
        log_info "Installing uv..."
        pip install uv
    fi
    
    # Check Node.js and npm
    if ! command -v node &> /dev/null; then
        log_error "Node.js is required but not installed"
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        log_error "npm is required but not installed"
        exit 1
    fi
    
    # Setup backend environment
    log_info "Setting up backend environment..."
    cd backend
    uv sync --dev
    
    # Setup frontend environment
    log_info "Setting up frontend environment..."
    cd ../frontend
    npm ci
    npx playwright install --with-deps
    
    # Create test directories
    log_info "Creating test directories..."
    cd ..
    mkdir -p test-reports/{master,backend,frontend,integration,security,performance}
    
    # Make scripts executable
    log_info "Making test scripts executable..."
    chmod +x scripts/test-master.sh
    chmod +x backend/scripts/test-comprehensive.sh
    chmod +x backend/scripts/test-security.sh
    chmod +x backend/scripts/test-performance.sh
    chmod +x frontend/scripts/test-comprehensive.sh
    chmod +x frontend/scripts/test-e2e-comprehensive.sh
    
    log_success "Testing environment setup complete!"
    log_info "You can now run tests using the options in this menu"
}

run_quick_tests() {
    log_info "Running quick tests (unit + integration)..."
    ./scripts/test-master.sh --fast
}

run_full_tests() {
    log_info "Running full test suite..."
    ./scripts/test-master.sh
}

run_e2e_tests() {
    log_info "Running E2E tests only..."
    cd frontend
    ./scripts/test-e2e-comprehensive.sh
    cd ..
}

run_security_tests() {
    log_info "Running security tests..."
    cd backend
    ./scripts/test-security.sh
    cd ..
}

run_performance_tests() {
    log_info "Running performance tests..."
    cd backend
    ./scripts/test-performance.sh
    cd ..
}

generate_reports() {
    log_info "Generating comprehensive test reports..."
    ./scripts/test-master.sh --ci
    
    log_success "Reports generated!"
    log_info "Check the following locations:"
    log_info "  📊 Master report: test-reports/master-test-report.md"
    log_info "  🐍 Backend: backend/test-reports/"
    log_info "  ⚛️  Frontend: frontend/test-reports/"
    log_info "  🎭 E2E: frontend/e2e-reports/"
}

check_status() {
    log_info "Checking test environment status..."
    
    echo -e "\n${BLUE}Environment Status:${NC}"
    
    # Check if scripts exist
    if [[ -f "scripts/test-master.sh" ]]; then
        echo "✅ Master test script: Available"
    else
        echo "❌ Master test script: Missing"
    fi
    
    if [[ -f "backend/scripts/test-comprehensive.sh" ]]; then
        echo "✅ Backend test scripts: Available"
    else
        echo "❌ Backend test scripts: Missing"
    fi
    
    if [[ -f "frontend/scripts/test-comprehensive.sh" ]]; then
        echo "✅ Frontend test scripts: Available"
    else
        echo "❌ Frontend test scripts: Missing"
    fi
    
    # Check dependencies
    echo -e "\n${BLUE}Dependencies:${NC}"
    
    if command -v python3 &> /dev/null; then
        echo "✅ Python: $(python3 --version)"
    else
        echo "❌ Python: Not installed"
    fi
    
    if command -v uv &> /dev/null; then
        echo "✅ uv: $(uv --version)"
    else
        echo "❌ uv: Not installed"
    fi
    
    if command -v node &> /dev/null; then
        echo "✅ Node.js: $(node --version)"
    else
        echo "❌ Node.js: Not installed"
    fi
    
    if command -v npm &> /dev/null; then
        echo "✅ npm: $(npm --version)"
    else
        echo "❌ npm: Not installed"
    fi
    
    # Check test directories
    echo -e "\n${BLUE}Test Directories:${NC}"
    
    if [[ -d "test-reports" ]]; then
        echo "✅ Test reports directory: Exists"
    else
        echo "❌ Test reports directory: Missing"
    fi
    
    if [[ -d "backend/tests" ]]; then
        echo "✅ Backend tests: Directory exists"
    else
        echo "❌ Backend tests: Directory missing"
    fi
    
    if [[ -d "frontend/tests" ]]; then
        echo "✅ Frontend tests: Directory exists"
    else
        echo "❌ Frontend tests: Directory missing"
    fi
}

clean_artifacts() {
    log_info "Cleaning test artifacts..."
    
    # Remove test reports
    if [[ -d "test-reports" ]]; then
        rm -rf test-reports/*
        log_info "Cleaned test reports"
    fi
    
    # Remove backend test artifacts
    if [[ -d "backend" ]]; then
        cd backend
        rm -rf htmlcov* coverage*.xml junit*.xml .coverage .pytest_cache
        rm -rf security-reports performance-reports
        cd ..
        log_info "Cleaned backend test artifacts"
    fi
    
    # Remove frontend test artifacts
    if [[ -d "frontend" ]]; then
        cd frontend
        rm -rf coverage test-results playwright-report e2e-reports
        cd ..
        log_info "Cleaned frontend test artifacts"
    fi
    
    log_success "Test artifacts cleaned!"
}

show_help() {
    echo -e "${BLUE}Brain2Gain Testing Suite Help${NC}"
    echo ""
    echo "This testing suite implements the comprehensive testing plan from testing_plan.yml:"
    echo ""
    echo -e "${YELLOW}Available Test Types:${NC}"
    echo "🧪 Unit Tests - Fast, isolated component testing"
    echo "🔗 Integration Tests - API and database integration"
    echo "🎭 E2E Tests - Critical user journey validation"
    echo "🔒 Security Tests - Vulnerability and security scanning"
    echo "⚡ Performance Tests - Load testing and performance validation"
    echo ""
    echo -e "${YELLOW}Test Scripts:${NC}"
    echo "📁 scripts/test-master.sh - Master orchestration script"
    echo "📁 backend/scripts/test-comprehensive.sh - Backend testing"
    echo "📁 backend/scripts/test-security.sh - Security validation"
    echo "📁 backend/scripts/test-performance.sh - Performance testing"
    echo "📁 frontend/scripts/test-comprehensive.sh - Frontend testing"
    echo "📁 frontend/scripts/test-e2e-comprehensive.sh - E2E testing"
    echo ""
    echo -e "${YELLOW}Manual Execution:${NC}"
    echo "# Run all tests:"
    echo "./scripts/test-master.sh"
    echo ""
    echo "# Run quick tests:"
    echo "./scripts/test-master.sh --fast"
    echo ""
    echo "# Run backend only:"
    echo "./scripts/test-master.sh --backend-only"
    echo ""
    echo "# Run frontend only:"
    echo "./scripts/test-master.sh --frontend-only"
    echo ""
    echo -e "${YELLOW}Coverage Targets:${NC}"
    echo "Backend: 90% overall coverage"
    echo "Frontend: 85% overall coverage"
    echo ""
    echo -e "${YELLOW}Quality Gates:${NC}"
    echo "✅ Code coverage thresholds met"
    echo "✅ All security tests pass"
    echo "✅ Performance benchmarks achieved"
    echo "✅ E2E critical journeys validated"
    echo ""
    echo -e "${YELLOW}CI/CD Integration:${NC}"
    echo "GitHub Actions workflow: .github/workflows/comprehensive-testing.yml"
    echo ""
}

main() {
    print_banner
    
    while true; do
        print_menu
        read -p "Enter your choice: " choice
        
        case $choice in
            1)
                setup_environment
                ;;
            2)
                run_quick_tests
                ;;
            3)
                run_full_tests
                ;;
            4)
                run_e2e_tests
                ;;
            5)
                run_security_tests
                ;;
            6)
                run_performance_tests
                ;;
            7)
                generate_reports
                ;;
            8)
                check_status
                ;;
            9)
                clean_artifacts
                ;;
            0)
                show_help
                ;;
            q|Q)
                log_info "Goodbye! 👋"
                exit 0
                ;;
            *)
                log_error "Invalid option. Please try again."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
        clear
        print_banner
    done
}

main "$@"