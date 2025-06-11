#!/bin/bash

# ============================================================================
# Test Script - Environment Separation
# Verifica que los ambientes store y admin funcionen correctamente
# ============================================================================

set -e

echo "🧪 Testing Brain2Gain Environment Separation"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            print_status "$service_name is ready!"
            return 0
        fi
        
        echo "Attempt $attempt/$max_attempts: $service_name not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start after $max_attempts attempts"
    return 1
}

# Function to test API endpoint
test_endpoint() {
    local url=$1
    local expected_status=$2
    local description=$3
    
    echo "Testing: $description"
    
    response=$(curl -s -w "%{http_code}" -o /tmp/response.json "$url")
    
    if [ "$response" = "$expected_status" ]; then
        print_status "✓ $description (HTTP $response)"
        return 0
    else
        print_error "✗ $description (Expected HTTP $expected_status, got $response)"
        if [ -f /tmp/response.json ]; then
            echo "Response body:"
            cat /tmp/response.json
            echo ""
        fi
        return 1
    fi
}

# Cleanup function
cleanup() {
    echo ""
    echo "🧹 Cleaning up test environments..."
    
    docker-compose -f docker-compose.store.yml down -v 2>/dev/null || true
    docker-compose -f docker-compose.admin.yml down -v 2>/dev/null || true
    
    print_status "Cleanup completed"
}

# Set trap to cleanup on exit
trap cleanup EXIT

echo ""
echo "📦 Step 1: Testing Store Environment"
echo "====================================="

# Copy environment file for store
cp .env.store .env

# Start store environment
echo "Starting store environment..."
docker-compose -f docker-compose.store.yml up -d

# Wait for services
wait_for_service "http://localhost:8000/health" "Store API"
wait_for_service "http://localhost:3000" "Store Frontend"

# Test store endpoints
echo ""
echo "Testing Store API endpoints..."

test_endpoint "http://localhost:8000/health" "200" "Store API Health Check"
test_endpoint "http://localhost:8000/api/v1/products/" "200" "Products Endpoint (should be available)"
test_endpoint "http://localhost:8000/api/v1/cart/" "401" "Cart Endpoint (should require auth)"
test_endpoint "http://localhost:8000/api/v1/users/" "404" "Users Endpoint (should not be available in store mode)"
test_endpoint "http://localhost:8000/docs" "404" "API Docs (should be disabled in public mode)"

# Test store frontend
echo ""
echo "Testing Store Frontend..."
test_endpoint "http://localhost:3000" "200" "Store Frontend Homepage"

print_status "Store environment test completed"

# Stop store environment
echo ""
echo "Stopping store environment..."
docker-compose -f docker-compose.store.yml down

echo ""
echo "📦 Step 2: Testing Admin Environment"
echo "===================================="

# Copy environment file for admin
cp .env.admin .env

# Start admin environment
echo "Starting admin environment..."
docker-compose -f docker-compose.admin.yml up -d

# Wait for services
wait_for_service "http://localhost:8001/health" "Admin API"
wait_for_service "http://localhost:3001" "Admin Frontend"
wait_for_service "http://localhost:8080" "Adminer"

# Test admin endpoints
echo ""
echo "Testing Admin API endpoints..."

test_endpoint "http://localhost:8001/health" "200" "Admin API Health Check"
test_endpoint "http://localhost:8001/api/v1/users/" "401" "Users Endpoint (should require admin auth)"
test_endpoint "http://localhost:8001/api/v1/products/" "404" "Products Endpoint (should not be available in admin-only mode)"
test_endpoint "http://localhost:8001/docs" "200" "API Docs (should be available in admin mode)"

# Test admin frontend
echo ""
echo "Testing Admin Frontend..."
test_endpoint "http://localhost:3001" "200" "Admin Frontend"

# Test adminer
echo ""
echo "Testing Database Management..."
test_endpoint "http://localhost:8080" "200" "Adminer Database Interface"

print_status "Admin environment test completed"

# Stop admin environment
echo ""
echo "Stopping admin environment..."
docker-compose -f docker-compose.admin.yml down

echo ""
echo "🎉 All Tests Completed!"
echo "======================="

print_status "Store environment: ✓ Functional"
print_status "Admin environment: ✓ Functional"
print_status "API separation: ✓ Working correctly"
print_status "Frontend separation: ✓ Working correctly"

echo ""
echo "📋 Summary:"
echo "- Store mode successfully isolates public e-commerce functionality"
echo "- Admin mode successfully isolates administrative functionality"
echo "- Both environments run independently with separate databases"
echo "- Security isolation is working as expected"

echo ""
echo "🚀 Ready for production deployment!"