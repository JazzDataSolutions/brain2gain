#!/usr/bin/env bash

# 🔒 Brain2Gain - Security Testing Script
# Comprehensive security testing based on testing_plan.yml

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
    echo -e "${BLUE}🔒 $1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

# Security Test Suite
run_authentication_security_tests() {
    print_header "Authentication Security Tests"
    
    log_info "Testing JWT validation and tampering resistance..."
    uv run pytest tests/security/test_jwt_security.py -v
    
    log_info "Testing password security and hashing..."
    uv run pytest tests/security/test_password_security.py -v
    
    log_info "Testing session management..."
    uv run pytest tests/security/test_session_security.py -v
    
    log_info "Testing rate limiting and brute force protection..."
    uv run pytest tests/security/test_rate_limiting.py -v
    
    log_success "Authentication security tests completed"
}

run_api_security_tests() {
    print_header "API Security Tests"
    
    log_info "Testing input validation and SQL injection prevention..."
    uv run pytest tests/security/test_input_validation.py -v
    
    log_info "Testing CORS configuration..."
    uv run pytest tests/security/test_cors.py -v
    
    log_info "Testing data sanitization and XSS prevention..."
    uv run pytest tests/security/test_xss_prevention.py -v
    
    log_info "Testing authorization and role-based access control..."
    uv run pytest tests/security/test_rbac.py -v
    
    log_success "API security tests completed"
}

run_dependency_scan() {
    print_header "Dependency Security Scan"
    
    log_info "Installing security tools..."
    uv add --dev safety bandit semgrep
    
    log_info "Scanning for vulnerable dependencies..."
    uv run safety check --json --output security-reports/safety-report.json || log_warning "Some vulnerabilities found"
    
    log_info "Running static security analysis with Bandit..."
    uv run bandit -r app/ -f json -o security-reports/bandit-report.json || log_warning "Security issues found"
    
    log_info "Running Semgrep security scan..."
    uv run semgrep --config=auto app/ --json --output=security-reports/semgrep-report.json || log_warning "Security patterns found"
    
    log_success "Dependency scan completed"
}

run_infrastructure_security_tests() {
    print_header "Infrastructure Security Tests"
    
    log_info "Testing Docker container security..."
    # Check if Docker is available
    if command -v docker &> /dev/null; then
        log_info "Running Docker security scan..."
        docker run --rm -v "$(pwd)":/app aquasec/trivy filesystem /app --format json --output /app/security-reports/trivy-report.json || log_warning "Container vulnerabilities found"
    else
        log_warning "Docker not available, skipping container security scan"
    fi
    
    log_info "Testing secrets management..."
    uv run pytest tests/security/test_secrets_management.py -v
    
    log_success "Infrastructure security tests completed"
}

# Generate security report
generate_security_report() {
    print_header "Generating Security Report"
    
    mkdir -p security-reports
    
    cat > security-reports/security-summary.md << EOF
# Brain2Gain Security Test Report

Generated on: $(date)

## Test Results Summary

### Authentication Security
- JWT validation and tampering resistance
- Password security and hashing
- Session management
- Rate limiting and brute force protection

### API Security  
- Input validation and SQL injection prevention
- CORS configuration
- Data sanitization and XSS prevention
- Authorization and role-based access control

### Dependency Security
- Vulnerable package detection
- Static security analysis
- Security pattern detection

### Infrastructure Security
- Container security scanning
- Secrets management validation

## Recommendations

1. Regularly update dependencies to patch security vulnerabilities
2. Implement proper input validation on all endpoints
3. Use secure session management practices
4. Regular security testing in CI/CD pipeline
5. Monitor for security alerts and respond promptly

## Files Scanned
- Application code: \`app/\`
- Dependencies: \`pyproject.toml\`, \`uv.lock\`
- Docker configuration: \`Dockerfile\`

EOF

    log_success "Security report generated: security-reports/security-summary.md"
}

main() {
    print_header "Brain2Gain Security Testing Suite"
    
    mkdir -p security-reports
    
    run_authentication_security_tests
    run_api_security_tests  
    run_dependency_scan
    run_infrastructure_security_tests
    generate_security_report
    
    log_success "Security testing completed! Check security-reports/ for detailed results."
}

main "$@"