#!/bin/bash

# ============================================================================
# Kong API Gateway Setup Script for Brain2Gain
# Phase 1: API Gateway Configuration
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
KONG_ADMIN_URL=${KONG_ADMIN_URL:-"http://localhost:8081"}
KONG_CONFIG_FILE="kong.yml"

echo -e "${BLUE}🚀 Setting up Kong API Gateway for Brain2Gain${NC}"
echo "=============================================="

# Function to check if Kong is running
check_kong_health() {
    echo -e "${YELLOW}⏳ Checking Kong health...${NC}"
    
    for i in {1..30}; do
        if curl -f -s "$KONG_ADMIN_URL/status" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Kong is healthy!${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
    done
    
    echo -e "${RED}❌ Kong health check failed after 60 seconds${NC}"
    return 1
}

# Function to apply Kong configuration
apply_kong_config() {
    echo -e "${YELLOW}⏳ Applying Kong configuration...${NC}"
    
    if [ ! -f "$KONG_CONFIG_FILE" ]; then
        echo -e "${RED}❌ Kong configuration file not found: $KONG_CONFIG_FILE${NC}"
        exit 1
    fi
    
    # Apply declarative configuration
    if curl -X POST "$KONG_ADMIN_URL/config" \
        -F "config=@$KONG_CONFIG_FILE" \
        -H "Content-Type: multipart/form-data"; then
        echo -e "${GREEN}✅ Kong configuration applied successfully!${NC}"
    else
        echo -e "${RED}❌ Failed to apply Kong configuration${NC}"
        exit 1
    fi
}

# Function to create API keys for consumers
create_api_keys() {
    echo -e "${YELLOW}⏳ Creating API keys for consumers...${NC}"
    
    # ERP Frontend API Key
    ERP_API_KEY=${ERP_API_KEY:-$(openssl rand -hex 32)}
    curl -X POST "$KONG_ADMIN_URL/consumers/erp-frontend/key-auth" \
        -d "key=$ERP_API_KEY" > /dev/null 2>&1
    
    # Mobile App API Key
    MOBILE_API_KEY=${MOBILE_API_KEY:-$(openssl rand -hex 32)}
    curl -X POST "$KONG_ADMIN_URL/consumers/mobile-app/key-auth" \
        -d "key=$MOBILE_API_KEY" > /dev/null 2>&1
    
    echo -e "${GREEN}✅ API keys created successfully!${NC}"
    echo -e "${BLUE}📋 API Keys:${NC}"
    echo -e "   ERP API Key: ${ERP_API_KEY}"
    echo -e "   Mobile API Key: ${MOBILE_API_KEY}"
}

# Function to configure JWT secrets
configure_jwt() {
    echo -e "${YELLOW}⏳ Configuring JWT secrets...${NC}"
    
    # Store Frontend JWT Secret
    JWT_SECRET_STORE=${JWT_SECRET_STORE:-$(openssl rand -base64 32)}
    curl -X POST "$KONG_ADMIN_URL/consumers/store-frontend/jwt" \
        -d "key=store-frontend-key" \
        -d "secret=$JWT_SECRET_STORE" > /dev/null 2>&1
    
    # ERP Frontend JWT Secret
    JWT_SECRET_ERP=${JWT_SECRET_ERP:-$(openssl rand -base64 32)}
    curl -X POST "$KONG_ADMIN_URL/consumers/erp-frontend/jwt" \
        -d "key=erp-frontend-key" \
        -d "secret=$JWT_SECRET_ERP" > /dev/null 2>&1
    
    echo -e "${GREEN}✅ JWT secrets configured successfully!${NC}"
}

# Function to verify Kong setup
verify_setup() {
    echo -e "${YELLOW}⏳ Verifying Kong setup...${NC}"
    
    # Check services
    echo -e "${BLUE}📋 Services:${NC}"
    curl -s "$KONG_ADMIN_URL/services" | jq -r '.data[] | "   - \(.name): \(.host):\(.port)"' 2>/dev/null || {
        echo "   Could not retrieve services (jq not available)"
        curl -s "$KONG_ADMIN_URL/services" | grep -o '"name":"[^"]*"' | sed 's/"name":"//g; s/"//g; s/^/   - /'
    }
    
    # Check routes
    echo -e "${BLUE}📋 Routes:${NC}"
    curl -s "$KONG_ADMIN_URL/routes" | jq -r '.data[] | "   - \(.name): \(.paths[])"' 2>/dev/null || {
        echo "   Could not retrieve routes (jq not available)"
        curl -s "$KONG_ADMIN_URL/routes" | grep -o '"name":"[^"]*"' | sed 's/"name":"//g; s/"//g; s/^/   - /'
    }
    
    # Check consumers
    echo -e "${BLUE}📋 Consumers:${NC}"
    curl -s "$KONG_ADMIN_URL/consumers" | jq -r '.data[] | "   - \(.username)"' 2>/dev/null || {
        echo "   Could not retrieve consumers (jq not available)"
        curl -s "$KONG_ADMIN_URL/consumers" | grep -o '"username":"[^"]*"' | sed 's/"username":"//g; s/"//g; s/^/   - /'
    }
    
    echo -e "${GREEN}✅ Kong setup verification completed!${NC}"
}

# Function to show Kong dashboard info
show_dashboard_info() {
    echo -e "${BLUE}📊 Kong Dashboard Information:${NC}"
    echo "=============================================="
    echo -e "Admin API: ${KONG_ADMIN_URL}"
    echo -e "Proxy: http://localhost:8080"
    echo -e "Manager UI: http://localhost:8002 (if enabled)"
    echo ""
    echo -e "${YELLOW}🔗 Useful Kong Admin API endpoints:${NC}"
    echo "   Services: GET $KONG_ADMIN_URL/services"
    echo "   Routes: GET $KONG_ADMIN_URL/routes"
    echo "   Consumers: GET $KONG_ADMIN_URL/consumers"
    echo "   Plugins: GET $KONG_ADMIN_URL/plugins"
    echo "   Status: GET $KONG_ADMIN_URL/status"
}

# Function to create environment file with secrets
create_env_file() {
    echo -e "${YELLOW}⏳ Creating environment file with secrets...${NC}"
    
    cat > .env.kong << EOF
# Kong API Gateway Secrets
# Generated on $(date)

ERP_API_KEY=${ERP_API_KEY:-$(openssl rand -hex 32)}
MOBILE_API_KEY=${MOBILE_API_KEY:-$(openssl rand -hex 32)}
JWT_SECRET_STORE=${JWT_SECRET_STORE:-$(openssl rand -base64 32)}
JWT_SECRET_ERP=${JWT_SECRET_ERP:-$(openssl rand -base64 32)}

# Kong URLs
KONG_ADMIN_URL=${KONG_ADMIN_URL}
KONG_PROXY_URL=http://localhost:8080
EOF
    
    echo -e "${GREEN}✅ Environment file created: .env.kong${NC}"
    echo -e "${YELLOW}⚠️  Remember to add these secrets to your production environment!${NC}"
}

# Main execution
main() {
    echo -e "${BLUE}Starting Kong setup process...${NC}"
    
    # Check if Kong is running
    if ! check_kong_health; then
        echo -e "${RED}❌ Kong is not running. Please start Kong first.${NC}"
        echo -e "${YELLOW}💡 Run: docker-compose up kong-migrations kong-db kong${NC}"
        exit 1
    fi
    
    # Apply configuration
    apply_kong_config
    
    # Wait a moment for configuration to be applied
    sleep 2
    
    # Configure authentication
    create_api_keys
    configure_jwt
    
    # Verify setup
    verify_setup
    
    # Create environment file
    create_env_file
    
    # Show dashboard info
    show_dashboard_info
    
    echo ""
    echo -e "${GREEN}🎉 Kong API Gateway setup completed successfully!${NC}"
    echo -e "${YELLOW}📝 Next steps:${NC}"
    echo "   1. Update your frontend applications to use the API Gateway"
    echo "   2. Configure microservices to register with Kong"
    echo "   3. Test API endpoints through the gateway"
    echo "   4. Set up monitoring and logging"
}

# Execute main function
main "$@"