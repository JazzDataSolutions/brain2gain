# 🧪 Comprehensive Testing Guide - Brain2Gain

## 📋 Overview

This comprehensive guide covers all testing strategies for Brain2Gain, from Phase 1 optimizations through Phase 2 microservices architecture, including unit testing, integration, E2E, performance, security, and load testing.

### 🎯 Testing Objectives
- **Code Coverage**: >90% backend, >85% frontend
- **Quality**: 0 critical bugs in production
- **Performance**: <200ms API response time, <2s frontend load
- **Reliability**: 99.9% uptime, automated test suite in <10min
- **Security**: 0 critical/high vulnerabilities

### 📊 Current State vs Target

| Aspect | Current | Target | Gap |
|---------|---------|--------|-----|
| Backend Coverage | ~60% | >90% | +30% |
| Frontend Coverage | ~40% | >85% | +45% |
| Integration Tests | Basic | Complete | High |
| Performance Tests | 0 | Complete | Critical |
| Security Tests | Basic | Advanced | High |
| Load Tests | 0 | Implemented | Critical |

## 🏗️ Testing Architecture

### 🔹 Testing Pyramid
```
    🔺 E2E Tests (10%)
   🔸🔸 Integration Tests (30%)
  🔹🔹🔹 Unit Tests (60%)
```

### 🔹 Testing Strategy by Layer

#### **1. Unit Tests (60% - Solid Foundation)**
- **Backend**: Services, Repositories, Utils, Models
- **Frontend**: Components, Hooks, Utils, Stores
- **Goal**: Fast, isolated testing

#### **2. Integration Tests (30% - Contracts)**
- **Backend**: API endpoints, Database, Cache, External APIs
- **Frontend**: Feature flows, API integration
- **Goal**: Contract testing between systems

#### **3. E2E Tests (10% - User Journeys)**
- **Critical paths**: Login, Purchase flow, Admin operations
- **Cross-browser**: Chrome, Firefox, Safari
- **Goal**: Complete user experience testing

## 📋 Prerequisites

Before starting testing, ensure you have:

```bash
# Verify required versions
docker --version        # >= 20.0
docker-compose --version # >= 1.27
node --version          # >= 20.0
python --version        # >= 3.10
```

## 🚀 Environment Setup

### 1.1 Initial Configuration
```bash
cd /home/jazzzfm/Documents/Brain2Gain/brain2gain

# Verify .env file exists
ls -la .env

# If it doesn't exist, create from example
cp .env.example .env
```

### 1.2 Start Services
```bash
# Start PostgreSQL and Redis
docker-compose -f docker-compose.dev.yml up postgres redis -d

# Verify services are running
docker-compose -f docker-compose.dev.yml ps

# Check logs
docker-compose -f docker-compose.dev.yml logs postgres
docker-compose -f docker-compose.dev.yml logs redis
```

### 1.3 Verify Connectivity
```bash
# Test PostgreSQL connection
docker exec -it brain2gain-postgres-1 psql -U brain2gain_owner -d brain2gain_prod -c "SELECT version();"

# Test Redis connection
docker exec -it brain2gain-redis-1 redis-cli -a RedisPass2025 ping
```

## 🧪 Backend Testing

### Unit Tests
```bash
cd backend

# Install dependencies
uv sync
source .venv/bin/activate

# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/services/test_analytics_service.py -v
```

### Integration Tests
```bash
# Run integration tests
pytest tests/integration/ -v

# Run API route tests
pytest tests/api/routes/ -v

# Run database integration tests
pytest tests/integration/test_cache_integration.py -v
```

### Performance Tests
```bash
# Run performance tests
pytest tests/performance/ -v

# Run API performance tests
pytest tests/performance/test_api_performance.py -v
```

### Security Tests
```bash
# Run security tests
pytest tests/security/ -v

# Run authentication tests
pytest tests/security/test_authentication.py -v
```

## 🎨 Frontend Testing

### Unit Tests
```bash
cd frontend

# Install dependencies
npm install

# Run unit tests
npm run test

# Run with coverage
npm run test:coverage

# Run specific component tests
npm run test -- --testPathPattern=components/AnalyticsDashboard
```

### Integration Tests
```bash
# Run integration tests (using Vitest)
npm run test:integration

# Run specific integration test
npm run test -- tests/integration/cart-flow.test.tsx
```

### E2E Tests
```bash
# Install Playwright (if not installed)
npx playwright install

# Run E2E tests
npm run test:e2e

# Run specific E2E test
npx playwright test tests/login.spec.ts

# Run with UI mode
npx playwright test --ui

# Run in headed mode
npx playwright test --headed
```

## 🔧 Microservices Testing (Phase 2)

### Kong API Gateway Testing
```bash
# Test Kong setup
./scripts/test-kong-setup.sh

# Test API Gateway health
curl -f http://localhost:8081/status

# Test service routing
curl -X GET "http://localhost:8080/api/v1/products" \
  -H "Host: tienda.brain2gain.com"
```

### Service-Specific Testing
```bash
# Test Auth Service
curl -X POST "http://localhost:8080/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'

# Test Product Service
curl -X GET "http://localhost:8080/api/v1/products" \
  -H "Host: tienda.brain2gain.com"

# Test Order Service
curl -X POST "http://localhost:8080/api/v1/orders" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Event Sourcing Testing
```bash
# Test event store
curl -X GET "http://localhost:8000/api/v1/events/health" \
  -H "Authorization: Bearer ADMIN_TOKEN"

# Test event history
curl -X GET "http://localhost:8000/api/v1/events/product/{product_id}/history" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

## 📊 Analytics Testing

### Analytics Dashboard Testing
```bash
# Run analytics-specific tests
npm run test -- tests/analytics-dashboard.spec.ts

# Test analytics API endpoints
curl -X GET "http://localhost:8000/api/v1/analytics/dashboard" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### Real-time Analytics Testing
```bash
# Test WebSocket connections
wscat -c ws://localhost:8000/api/v1/ws/notifications
```

## 🔒 Security Testing

### Authentication Testing
```bash
# Test JWT token validation
pytest tests/security/test_authentication.py::test_jwt_validation -v

# Test unauthorized access
curl -X GET "http://localhost:8000/api/v1/admin/users" \
  -H "Authorization: Bearer invalid_token"
```

### API Security Testing
```bash
# Test rate limiting
for i in {1..20}; do
  curl -X GET "http://localhost:8080/api/v1/products" \
    -H "Host: tienda.brain2gain.com"
done
```

## 🚀 Performance Testing

### Load Testing with K6
```bash
# Install k6 (if not installed)
brew install k6  # macOS
# or
sudo apt install k6  # Ubuntu

# Run load tests
k6 run tests/performance/load-test.js

# Run stress tests
k6 run --vus 100 --duration 30s tests/performance/stress-test.js
```

### Database Performance Testing
```bash
# Test database performance
pytest tests/performance/test_api_performance.py::test_database_queries -v
```

## 📈 Continuous Integration

### GitHub Actions Integration
```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install uv
          uv sync
      - name: Run tests
        run: |
          cd backend
          source .venv/bin/activate
          pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run tests
        run: |
          cd frontend
          npm run test:coverage
      - name: Run E2E tests
        run: |
          cd frontend
          npx playwright install
          npm run test:e2e
```

## 🔍 Monitoring and Reporting

### Test Coverage Reports
```bash
# Backend coverage
cd backend
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Frontend coverage
cd frontend
npm run test:coverage
open coverage/index.html
```

### Performance Monitoring
```bash
# Generate performance reports
k6 run --out json=performance-results.json tests/performance/load-test.js

# Analyze results
k6 run --out influxdb=http://localhost:8086/k6 tests/performance/load-test.js
```

## 📝 Test Maintenance

### Regular Tasks
1. **Daily**: Run smoke tests on critical paths
2. **Weekly**: Full test suite execution
3. **Monthly**: Performance baseline updates
4. **Quarterly**: Security vulnerability scans

### Test Data Management
```bash
# Reset test database
alembic downgrade base
alembic upgrade head

# Seed test data
python backend/app/initial_data.py
```

## 🎯 Testing Checklist

### Before Deployment
- [ ] All unit tests pass (>90% coverage)
- [ ] Integration tests pass
- [ ] E2E tests pass on critical paths
- [ ] Performance tests meet SLA requirements
- [ ] Security tests pass
- [ ] Load tests confirm system capacity

### Post-Deployment
- [ ] Smoke tests in production
- [ ] Monitor error rates
- [ ] Verify performance metrics
- [ ] Check security logs

## 📚 Resources

### Tools and Frameworks
- **Backend**: pytest, pytest-cov, pytest-asyncio, factory-boy
- **Frontend**: Vitest, Testing Library, Playwright
- **Performance**: k6, Artillery
- **Security**: OWASP ZAP, bandit
- **API**: Postman, Insomnia, curl

### Documentation
- [Pytest Documentation](https://docs.pytest.org/)
- [Playwright Documentation](https://playwright.dev/)
- [Vitest Documentation](https://vitest.dev/)
- [K6 Documentation](https://k6.io/docs/)

This comprehensive guide ensures robust testing across all phases of the Brain2Gain project, from initial optimizations through microservices architecture implementation.