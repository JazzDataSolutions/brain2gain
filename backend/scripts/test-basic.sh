#!/usr/bin/env bash

# 🧪 Brain2Gain - Basic Testing Script
# Run tests that don't require database connectivity

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
    echo -e "${BLUE}🧪 $1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

print_header "Brain2Gain Basic Testing"

# Check if we're in the backend directory
if [[ ! -f "pyproject.toml" ]]; then
    log_error "Must be run from backend directory"
    exit 1
fi

log_info "Current directory: $(pwd)"
log_info "Python version: $(uv run python --version)"
log_info "Pytest version: $(uv run pytest --version)"

# Test Python imports without database
print_header "Testing Python Module Imports"

log_info "Testing core module imports..."
uv run python -c "
try:
    from app.core.security import create_access_token, get_password_hash, verify_password, decode_access_token
    from app.core.config import settings
    print('✅ Core modules import successfully')
except Exception as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

log_info "Testing model imports..."
uv run python -c "
try:
    from app.models import User, Product, Order, Payment
    print('✅ Model imports successful')
except Exception as e:
    print(f'❌ Model import error: {e}')
    exit(1)
"

log_info "Testing service imports..."
uv run python -c "
try:
    from app.services.auth_service import AuthService
    from app.services.product_service import ProductService
    from app.services.cart_service import CartService
    print('✅ Service imports successful')
except Exception as e:
    print(f'❌ Service import error: {e}')
    exit(1)
"

# Test configuration
print_header "Testing Configuration"

log_info "Testing environment configuration..."
uv run python -c "
from app.core.config import settings
print(f'Environment: {settings.ENVIRONMENT}')
print(f'Project name: {settings.PROJECT_NAME}')
print('✅ Configuration loaded successfully')
"

# Test simple security functions
print_header "Testing Security Functions"

log_info "Testing password hashing and verification..."
uv run python -c "
from app.core.security import get_password_hash, verify_password
password = 'test_password_123'
hashed = get_password_hash(password)
if verify_password(password, hashed):
    print('✅ Password hashing/verification works')
else:
    print('❌ Password verification failed')
    exit(1)
"

log_info "Testing JWT token creation and validation..."
uv run python -c "
from datetime import timedelta
from app.core.security import create_access_token, decode_access_token

# Create token
token = create_access_token('test_user', timedelta(minutes=15))
print(f'Token created: {token[:20]}...')

# Decode token
payload = decode_access_token(token)
if payload and payload.get('sub') == 'test_user':
    print('✅ JWT token creation/validation works')
else:
    print('❌ JWT token validation failed')
    exit(1)
"

# Test without database
print_header "Running Tests Without Database"

log_info "Running pure unit tests (no database required)..."

# Try to find and run specific unit tests that don't need DB
if [[ -f "app/tests/unit/core/test_security.py" ]]; then
    log_info "Running security unit tests..."
    uv run pytest app/tests/unit/core/test_security.py -v
else
    log_warning "No security unit tests found"
fi

# Test simple linting
print_header "Code Quality Checks"

log_info "Running basic syntax checks..."
uv run python -m py_compile app/core/security.py
uv run python -m py_compile app/models.py
uv run python -m py_compile app/main.py

log_success "Basic syntax checks passed"

# Summary
print_header "Basic Testing Summary"

log_success "All basic tests completed successfully!"
log_info "✅ Module imports working"
log_info "✅ Configuration loading"
log_info "✅ Security functions working"
log_info "✅ Basic syntax validation"

log_warning "Note: Database-dependent tests skipped"
log_info "To run full tests, ensure PostgreSQL is available and configured"

echo -e "\n${GREEN}🎉 Basic testing validation completed!${NC}\n"