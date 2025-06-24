# 🧪 Brain2Gain - Comprehensive Testing Guide

This guide provides complete instructions for running the Brain2Gain testing suite, implemented according to the specifications in `testing_plan.yml`.

## 🚀 Quick Start

### Interactive Setup
```bash
./scripts/test-quick-setup.sh
```

This interactive script provides a menu-driven interface for all testing operations.

### Manual Execution
```bash
# Run all tests
./scripts/test-master.sh

# Quick tests (unit + integration)
./scripts/test-master.sh --fast

# Backend tests only
./scripts/test-master.sh --backend-only

# Frontend tests only
./scripts/test-master.sh --frontend-only
```

## 📋 Testing Architecture

### Test Categories

| Category | Location | Framework | Coverage Target |
|----------|----------|-----------|-----------------|
| **Backend Unit** | `backend/tests/unit/` | pytest | 95% |
| **Backend Integration** | `backend/tests/integration/` | pytest + fastapi.testclient | 90% |
| **Backend Security** | `backend/tests/security/` | pytest + security tools | 100% |
| **Backend Performance** | `backend/tests/performance/` | pytest + Artillery + k6 | - |
| **Frontend Unit** | `frontend/src/test/unit/` | Vitest + Testing Library | 90% |
| **Frontend Integration** | `frontend/src/test/integration/` | Vitest + MSW | 85% |
| **Frontend E2E** | `frontend/tests/` | Playwright | 100% critical paths |
| **Frontend Accessibility** | `frontend/tests/accessibility/` | Playwright + axe-core | WCAG AA |

### Test Scripts Overview

```
scripts/
├── test-master.sh              # 🎯 Master orchestration script
├── test-quick-setup.sh         # 🚀 Interactive setup and execution
backend/scripts/
├── test-comprehensive.sh       # 🐍 Complete backend testing
├── test-security.sh           # 🔒 Security validation
├── test-performance.sh        # ⚡ Performance and load testing
frontend/scripts/
├── test-comprehensive.sh      # ⚛️ Complete frontend testing
└── test-e2e-comprehensive.sh  # 🎭 E2E and accessibility testing
```

## 🔧 Setup Requirements

### System Dependencies
- **Python 3.11+** with `uv` package manager
- **Node.js 18+** with `npm`
- **Docker** (for integration tests)
- **PostgreSQL 17** (for database tests)
- **Redis 7** (for cache tests)

### Installation
```bash
# Install Python dependencies
cd backend
uv sync --dev

# Install Node.js dependencies
cd ../frontend
npm ci
npx playwright install --with-deps

# Make scripts executable
chmod +x scripts/*.sh
chmod +x backend/scripts/*.sh
chmod +x frontend/scripts/*.sh
```

## 📊 Test Execution

### Backend Testing

#### Unit Tests
```bash
cd backend
./scripts/test-comprehensive.sh --unit-only
```

Tests:
- **Models**: User, Product, Cart, Order, Transaction validation
- **Services**: Business logic, auth, cart, inventory, analytics
- **Repositories**: Database operations, queries, transactions

#### Integration Tests
```bash
cd backend
./scripts/test-comprehensive.sh --integration-only
```

Tests:
- **API Routes**: Authentication, products, cart, orders, analytics
- **Database**: Migrations, constraints, cascade operations
- **Cache**: Redis integration, session management
- **WebSocket**: Real-time notifications, concurrent connections

#### Security Tests
```bash
cd backend
./scripts/test-security.sh
```

Tests:
- **Authentication**: JWT validation, password security, rate limiting
- **API Security**: Input validation, CORS, XSS prevention, RBAC
- **Dependencies**: Vulnerability scanning with Safety, Bandit, Semgrep
- **Infrastructure**: Container security, secrets management

#### Performance Tests
```bash
cd backend
./scripts/test-performance.sh
```

Tests:
- **Load Testing**: Artillery.io with 100 concurrent users
- **Stress Testing**: k6 with progressive load scaling
- **Database Performance**: Query optimization validation
- **API Performance**: Response time validation (< 200ms)

### Frontend Testing

#### Unit Tests
```bash
cd frontend
./scripts/test-comprehensive.sh --unit-only
```

Tests:
- **UI Components**: Button, Card, Input, LoadingSpinner
- **Business Components**: ProductCard, CartItem, AnalyticsDashboard
- **Hooks**: useAuth, useCart, useNotifications
- **Stores**: Zustand cart store, auth context
- **Services**: API services, analytics, notifications

#### Integration Tests
```bash
cd frontend
npm run test -- src/test/integration/
```

Tests:
- **Page Flows**: Navigation, routing, state management
- **API Integration**: Real backend communication
- **Cart Operations**: Add/remove items, persistence
- **Authentication**: Login/logout with token management

#### E2E Tests
```bash
cd frontend
./scripts/test-e2e-comprehensive.sh
```

Tests:
- **Critical User Journeys**:
  - Guest purchase flow
  - Registered user flow
  - Admin operations
- **Accessibility**: WCAG AA compliance, keyboard navigation
- **Cross-browser**: Chromium, Firefox, WebKit
- **Performance**: Page load, interaction responsiveness

### Full Stack Testing

#### Complete Test Suite
```bash
./scripts/test-master.sh
```

Executes:
1. **Phase 1**: Backend comprehensive testing
2. **Phase 2**: Frontend comprehensive testing
3. **Phase 3**: Full stack integration testing
4. **Phase 4**: Code quality and security validation

#### CI Mode
```bash
./scripts/test-master.sh --ci
```

Optimized for CI/CD pipelines with:
- Parallel test execution
- Artifact collection
- Quality gate validation
- Comprehensive reporting

## 📈 Coverage Reports

### Backend Coverage
```bash
cd backend
uv run pytest --cov=app --cov-report=html
# Open: htmlcov/index.html
```

### Frontend Coverage
```bash
cd frontend
npm run test:coverage
# Open: coverage/index.html
```

### Combined Coverage
Coverage reports are automatically generated and combined in:
- `test-reports/master-test-report.md`
- Individual service reports in respective directories

## 🔍 Quality Gates

### Minimum Requirements
- ✅ **Backend Coverage**: 90% overall
- ✅ **Frontend Coverage**: 85% overall
- ✅ **Security Scan**: No high/critical vulnerabilities
- ✅ **Performance**: API response < 200ms (95th percentile)
- ✅ **E2E Tests**: All critical user journeys pass
- ✅ **Accessibility**: WCAG AA compliance

### Quality Gate Validation
```bash
# Check all quality gates
./scripts/test-master.sh

# Quick quality check
make lint && make type-check
```

## 🤖 CI/CD Integration

### GitHub Actions
Automated testing pipeline: `.github/workflows/comprehensive-testing.yml`

**Triggers**:
- Push to `main`/`develop`
- Pull requests
- Daily scheduled runs (2 AM UTC)
- Manual trigger with `[perf]` in commit message

**Pipeline Stages**:
1. **Quality Gates** (2 min) - Linting, type checking
2. **Backend Tests** (15 min) - Unit, integration, security
3. **Frontend Tests** (15 min) - Unit, integration, build
4. **E2E Tests** (30 min) - Critical journeys, accessibility
5. **Security Scan** (10 min) - Dependency and code scanning
6. **Performance Tests** (20 min) - Load testing, Lighthouse
7. **Report Generation** (5 min) - Comprehensive results

### Quality Gate Enforcement
- **Coverage thresholds** must be met
- **Security scans** must pass
- **Performance benchmarks** must be achieved
- **E2E tests** must validate critical paths

## 📋 Test Reports

### Report Locations
```
test-reports/
├── master-test-report.md       # 📊 Executive summary
├── backend/                    # 🐍 Backend results
│   ├── coverage/              # Coverage reports
│   ├── security-reports/      # Security scan results
│   └── performance-reports/   # Performance test results
├── frontend/                  # ⚛️ Frontend results
│   ├── coverage/             # Coverage reports
│   └── e2e-reports/          # E2E test results
└── integration/              # 🔗 Integration test results
```

### Report Generation
```bash
# Generate all reports
./scripts/test-master.sh

# Generate specific reports
cd backend && ./scripts/test-security.sh      # Security report
cd frontend && ./scripts/test-e2e-comprehensive.sh  # E2E report
```

## 🐛 Debugging and Troubleshooting

### Common Issues

#### Backend Tests Failing
```bash
# Check database connection
docker-compose -f docker-compose.dev.yml up postgres redis

# Run specific test
cd backend
uv run pytest tests/api/routes/test_login.py::test_login -v

# Check dependencies
uv sync --dev
```

#### Frontend Tests Failing
```bash
# Check Node.js version
node --version  # Should be 18+

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Run specific test
npm run test -- src/components/ProductCard.test.tsx
```

#### E2E Tests Failing
```bash
# Reinstall Playwright browsers
npx playwright install --with-deps

# Run with UI
npx playwright test --headed

# Debug specific test
npx playwright test tests/login.spec.ts --debug
```

### Test Debugging Commands
```bash
# Backend debug mode
cd backend
uv run pytest --pdb tests/failing_test.py

# Frontend debug mode
cd frontend
npm run test:ui  # Visual test runner

# E2E debug mode
cd frontend
npx playwright test --debug
```

## 📚 Test Writing Guidelines

### Backend Test Structure
```python
# tests/unit/services/test_product_service.py
import pytest
from app.services.product_service import ProductService

class TestProductService:
    """Test suite for ProductService"""
    
    @pytest.fixture
    def product_service(self, db_session):
        return ProductService(db_session)
    
    def test_create_product_success(self, product_service):
        """Test successful product creation"""
        # Arrange
        product_data = {"name": "Test Product", "price": 99.99}
        
        # Act
        product = product_service.create_product(product_data)
        
        # Assert
        assert product.name == "Test Product"
        assert product.price == 99.99
```

### Frontend Test Structure
```typescript
// src/test/unit/components/ProductCard.test.tsx
import { render, screen } from '@testing-library/react'
import { ProductCard } from '@/components/Products/ProductCard'

describe('ProductCard', () => {
  const mockProduct = {
    id: '1',
    name: 'Test Product',
    price: 99.99,
    image_url: '/test-image.jpg'
  }

  it('renders product information correctly', () => {
    render(<ProductCard product={mockProduct} />)
    
    expect(screen.getByText('Test Product')).toBeInTheDocument()
    expect(screen.getByText('$99.99')).toBeInTheDocument()
  })
})
```

### E2E Test Structure
```typescript
// tests/e2e/guest-purchase-flow.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Guest Purchase Flow', () => {
  test('complete guest checkout process', async ({ page }) => {
    // Navigate to product catalog
    await page.goto('/')
    await page.click('[data-testid="browse-products"]')
    
    // Add product to cart
    await page.click('[data-testid="product-card"]:first-child [data-testid="add-to-cart"]')
    
    // Proceed to checkout
    await page.click('[data-testid="cart-icon"]')
    await page.click('[data-testid="checkout-button"]')
    
    // Fill guest information
    await page.fill('[data-testid="guest-email"]', 'test@example.com')
    await page.fill('[data-testid="guest-name"]', 'John Doe')
    
    // Complete purchase
    await page.click('[data-testid="complete-order"]')
    
    // Verify success
    await expect(page.locator('[data-testid="order-success"]')).toBeVisible()
  })
})
```

## 🎯 Best Practices

### Test Organization
- **Group related tests** in describe blocks
- **Use descriptive test names** that explain the scenario
- **Follow AAA pattern**: Arrange, Act, Assert
- **Keep tests isolated** and independent

### Test Data Management
- **Use factories** for consistent test data
- **Avoid hard-coded values** where possible
- **Clean up after tests** to prevent state leakage
- **Use realistic but minimal** data sets

### Performance Considerations
- **Run fast tests first** for quick feedback
- **Parallelize test execution** where possible
- **Use test doubles** (mocks, stubs) appropriately
- **Monitor test execution times** and optimize slow tests

### Maintenance
- **Review and update tests** regularly
- **Remove obsolete tests** when features change
- **Refactor tests** when code structure changes
- **Document complex test scenarios**

## 🔧 Customization

### Adding New Tests

#### Backend Test
```bash
# Create new test file
touch backend/tests/unit/services/test_new_service.py

# Follow existing patterns
# Use fixtures from conftest.py
# Add to appropriate test script
```

#### Frontend Test
```bash
# Create new test file
touch frontend/src/test/unit/components/NewComponent.test.tsx

# Follow existing patterns
# Use test utilities from test-utils.tsx
# Import in test-comprehensive.sh
```

#### E2E Test
```bash
# Create new test file
touch frontend/tests/new-flow.spec.ts

# Follow Playwright patterns
# Use page object model
# Add to playwright.config.ts
```

### Modifying Test Scripts
Test scripts are modular and can be customized:

```bash
# Edit test-master.sh for orchestration changes
# Edit individual scripts for specific test modifications
# Update CI workflow for pipeline changes
```

## 📞 Support

### Getting Help
- **Documentation**: Check this guide and `testing_plan.yml`
- **Issues**: Create GitHub issues for bugs or feature requests
- **Scripts**: Use `./scripts/test-quick-setup.sh` for interactive help
- **Status**: Run `check_status` option in quick setup script

### Contributing
1. Follow existing test patterns
2. Maintain coverage thresholds
3. Update documentation for new features
4. Ensure all quality gates pass

---

**Ready to test?** Start with `./scripts/test-quick-setup.sh` for an interactive experience!