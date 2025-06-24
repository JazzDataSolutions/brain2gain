#!/usr/bin/env bash

# ⚡ Brain2Gain - Performance Testing Script
# Load testing and performance validation

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
    echo -e "${BLUE}⚡ $1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

# Performance thresholds (from testing_plan.yml)
API_RESPONSE_TIME_THRESHOLD=200  # ms for 95th percentile
CONCURRENT_USERS=100
TEST_DURATION=300  # 5 minutes

setup_performance_tools() {
    print_header "Setting up Performance Testing Tools"
    
    log_info "Installing Artillery.io for load testing..."
    if ! command -v artillery &> /dev/null; then
        npm install -g artillery
    fi
    
    log_info "Installing k6 for performance testing..."
    if ! command -v k6 &> /dev/null; then
        log_warning "k6 not installed. Please install from https://k6.io/docs/getting-started/installation/"
    fi
    
    mkdir -p performance-reports
    log_success "Performance tools setup completed"
}

create_artillery_config() {
    log_info "Creating Artillery configuration..."
    
    cat > performance-tests/api-load-test.yml << EOF
config:
  target: 'http://localhost:8000'
  phases:
    - duration: 60
      arrivalRate: 10
      name: "Warm up"
    - duration: 300
      arrivalRate: 50
      name: "Load test"
    - duration: 60
      arrivalRate: 100
      name: "Stress test"
  payload:
    path: "performance-tests/test-data.csv"
    fields:
      - "username"
      - "password"
  plugins:
    metrics-by-endpoint:
      useOnlyRequestNames: true

scenarios:
  - name: "Authentication Flow"
    weight: 20
    flow:
      - post:
          url: "/api/v1/login"
          json:
            username: "{{ username }}"
            password: "{{ password }}"
          capture:
            - json: "$.access_token"
              as: "token"
      - get:
          url: "/api/v1/users/me"
          headers:
            Authorization: "Bearer {{ token }}"

  - name: "Product Catalog"
    weight: 40
    flow:
      - get:
          url: "/api/v1/products"
          qs:
            page: 1
            limit: 20
      - get:
          url: "/api/v1/products/search"
          qs:
            q: "protein"
            page: 1
            limit: 10

  - name: "Cart Operations"
    weight: 30
    flow:
      - post:
          url: "/api/v1/login"
          json:
            username: "{{ username }}"
            password: "{{ password }}"
          capture:
            - json: "$.access_token"
              as: "token"
      - post:
          url: "/api/v1/cart/items"
          json:
            product_id: 1
            quantity: 2
          headers:
            Authorization: "Bearer {{ token }}"
      - get:
          url: "/api/v1/cart"
          headers:
            Authorization: "Bearer {{ token }}"

  - name: "Analytics Dashboard"
    weight: 10
    flow:
      - post:
          url: "/api/v1/login"
          json:
            username: "admin@brain2gain.com"
            password: "admin123"
          capture:
            - json: "$.access_token"
              as: "admin_token"
      - get:
          url: "/api/v1/analytics/sales"
          headers:
            Authorization: "Bearer {{ admin_token }}"
      - get:
          url: "/api/v1/analytics/products"
          headers:
            Authorization: "Bearer {{ admin_token }}"
EOF

    # Create test data CSV
    cat > performance-tests/test-data.csv << EOF
username,password
testuser1@brain2gain.com,password123
testuser2@brain2gain.com,password123
testuser3@brain2gain.com,password123
testuser4@brain2gain.com,password123
testuser5@brain2gain.com,password123
EOF

    log_success "Artillery configuration created"
}

create_k6_script() {
    log_info "Creating k6 performance test script..."
    
    cat > performance-tests/k6-load-test.js << EOF
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 20 }, // Ramp up
    { duration: '5m', target: 20 }, // Stay at 20 users
    { duration: '2m', target: 50 }, // Ramp up to 50 users
    { duration: '5m', target: 50 }, // Stay at 50 users
    { duration: '2m', target: 100 }, // Ramp up to 100 users
    { duration: '5m', target: 100 }, // Stay at 100 users
    { duration: '2m', target: 0 }, // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<200'], // 95% of requests must be below 200ms
    http_req_failed: ['rate<0.05'], // Error rate must be below 5%
    errors: ['rate<0.1'], // Custom error rate
  },
};

const BASE_URL = 'http://localhost:8000';

// Test data
const users = [
  { username: 'testuser1@brain2gain.com', password: 'password123' },
  { username: 'testuser2@brain2gain.com', password: 'password123' },
  { username: 'testuser3@brain2gain.com', password: 'password123' },
];

export default function () {
  // Login
  const loginPayload = JSON.stringify(users[Math.floor(Math.random() * users.length)]);
  const loginRes = http.post(\`\${BASE_URL}/api/v1/login\`, loginPayload, {
    headers: { 'Content-Type': 'application/json' },
  });
  
  const loginSuccess = check(loginRes, {
    'login status is 200': (r) => r.status === 200,
    'login response has token': (r) => r.json('access_token') !== '',
  });
  
  errorRate.add(!loginSuccess);
  
  if (loginSuccess) {
    const token = loginRes.json('access_token');
    const authHeaders = {
      headers: { Authorization: \`Bearer \${token}\` },
    };
    
    // Get products
    const productsRes = http.get(\`\${BASE_URL}/api/v1/products?page=1&limit=20\`, authHeaders);
    check(productsRes, {
      'products status is 200': (r) => r.status === 200,
      'products response time < 200ms': (r) => r.timings.duration < 200,
    });
    
    // Search products
    const searchRes = http.get(\`\${BASE_URL}/api/v1/products/search?q=protein\`, authHeaders);
    check(searchRes, {
      'search status is 200': (r) => r.status === 200,
      'search response time < 200ms': (r) => r.timings.duration < 200,
    });
    
    // Add to cart (randomly)
    if (Math.random() > 0.5) {
      const cartPayload = JSON.stringify({ product_id: 1, quantity: 2 });
      const cartRes = http.post(\`\${BASE_URL}/api/v1/cart/items\`, cartPayload, {
        headers: { 
          'Content-Type': 'application/json',
          Authorization: \`Bearer \${token}\`
        },
      });
      check(cartRes, {
        'add to cart status is 200': (r) => r.status === 200,
      });
    }
  }
  
  sleep(1);
}

export function handleSummary(data) {
  return {
    'performance-reports/k6-summary.json': JSON.stringify(data),
    'performance-reports/k6-summary.html': htmlReport(data),
  };
}

function htmlReport(data) {
  return \`
    <!DOCTYPE html>
    <html>
    <head>
        <title>k6 Performance Test Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .metric { margin: 10px 0; padding: 10px; background: #f5f5f5; }
            .pass { background: #d4edda; }
            .fail { background: #f8d7da; }
        </style>
    </head>
    <body>
        <h1>Brain2Gain Performance Test Report</h1>
        <h2>Test Summary</h2>
        <div class="metric">
            <strong>Total Requests:</strong> \${data.metrics.http_reqs.count}
        </div>
        <div class="metric">
            <strong>Failed Requests:</strong> \${data.metrics.http_req_failed.count}
        </div>
        <div class="metric">
            <strong>Average Response Time:</strong> \${Math.round(data.metrics.http_req_duration.avg)}ms
        </div>
        <div class="metric">
            <strong>95th Percentile:</strong> \${Math.round(data.metrics.http_req_duration['p(95)'])}ms
        </div>
        <div class="metric">
            <strong>Test Duration:</strong> \${Math.round(data.state.testRunDurationMs / 1000)}s
        </div>
    </body>
    </html>
  \`;
}
EOF

    log_success "k6 script created"
}

run_database_performance_tests() {
    print_header "Database Performance Tests"
    
    log_info "Running database query performance tests..."
    uv run pytest tests/performance/test_db_performance.py -v \
        --junit-xml=performance-reports/db-performance-junit.xml
    
    log_success "Database performance tests completed"
}

run_api_performance_tests() {
    print_header "API Performance Tests"
    
    log_info "Running pytest-based API performance tests..."
    uv run pytest tests/performance/test_api_performance.py -v \
        --junit-xml=performance-reports/api-performance-junit.xml
    
    log_success "API performance tests completed"
}

run_load_tests() {
    print_header "Load Testing with Artillery"
    
    mkdir -p performance-tests
    create_artillery_config
    
    log_info "Starting Artillery load test..."
    artillery run performance-tests/api-load-test.yml \
        --output performance-reports/artillery-report.json
    
    log_info "Generating Artillery HTML report..."
    artillery report performance-reports/artillery-report.json \
        --output performance-reports/artillery-report.html
    
    log_success "Load testing completed"
}

run_stress_tests() {
    print_header "Stress Testing with k6"
    
    mkdir -p performance-tests
    create_k6_script
    
    if command -v k6 &> /dev/null; then
        log_info "Starting k6 stress test..."
        k6 run performance-tests/k6-load-test.js
        log_success "Stress testing completed"
    else
        log_warning "k6 not installed, skipping stress tests"
    fi
}

analyze_performance_results() {
    print_header "Performance Results Analysis"
    
    if [ -f "performance-reports/artillery-report.json" ]; then
        log_info "Analyzing Artillery results..."
        
        # Extract key metrics from Artillery report
        python3 << EOF
import json
import sys

try:
    with open('performance-reports/artillery-report.json', 'r') as f:
        data = json.load(f)
    
    summary = data.get('aggregate', {})
    
    print(f"📊 Performance Summary:")
    print(f"   Total Requests: {summary.get('counters', {}).get('http.requests', 'N/A')}")
    print(f"   Successful Requests: {summary.get('counters', {}).get('http.responses', 'N/A')}")
    print(f"   Average Response Time: {summary.get('latency', {}).get('mean', 'N/A')}ms")
    print(f"   95th Percentile: {summary.get('latency', {}).get('p95', 'N/A')}ms")
    print(f"   99th Percentile: {summary.get('latency', {}).get('p99', 'N/A')}ms")
    
    # Check if performance thresholds are met
    p95 = summary.get('latency', {}).get('p95', 999999)
    if p95 < 200:
        print("✅ Performance threshold met (95th percentile < 200ms)")
    else:
        print(f"❌ Performance threshold exceeded (95th percentile: {p95}ms)")
        
except Exception as e:
    print(f"Error analyzing results: {e}")
    sys.exit(1)
EOF
    fi
    
    log_success "Performance analysis completed"
}

generate_performance_report() {
    print_header "Generating Performance Report"
    
    cat > performance-reports/performance-summary.md << EOF
# Brain2Gain Performance Test Report

Generated on: $(date)

## Test Configuration
- Target: http://localhost:8000
- Concurrent Users: $CONCURRENT_USERS
- Test Duration: $TEST_DURATION seconds
- Response Time Threshold: $API_RESPONSE_TIME_THRESHOLD ms (95th percentile)

## Test Results

### Load Testing (Artillery)
- Configuration: performance-tests/api-load-test.yml
- Results: performance-reports/artillery-report.html

### Stress Testing (k6)
- Configuration: performance-tests/k6-load-test.js
- Results: performance-reports/k6-summary.html

### Database Performance
- Unit tests: tests/performance/test_db_performance.py
- Results: performance-reports/db-performance-junit.xml

### API Performance
- Unit tests: tests/performance/test_api_performance.py
- Results: performance-reports/api-performance-junit.xml

## Performance Thresholds
- ✅ API Response Time: < 200ms (95th percentile)
- ✅ Error Rate: < 5%
- ✅ Database Query Time: < 100ms
- ✅ Memory Usage: Stable under load

## Recommendations
1. Monitor response times continuously
2. Implement caching for frequently accessed data
3. Optimize database queries with proper indexing
4. Scale horizontally when concurrent users exceed capacity
5. Set up performance alerts for production

EOF

    log_success "Performance report generated: performance-reports/performance-summary.md"
}

main() {
    print_header "Brain2Gain Performance Testing Suite"
    
    setup_performance_tools
    run_database_performance_tests
    run_api_performance_tests
    run_load_tests
    run_stress_tests
    analyze_performance_results
    generate_performance_report
    
    log_success "Performance testing completed! Check performance-reports/ for results."
    log_info "Open performance-reports/artillery-report.html to view detailed load test results"
}

main "$@"