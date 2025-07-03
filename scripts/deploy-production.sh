#!/bin/bash

# =====================================================================
# Brain2Gain Production Deployment Script
# =====================================================================
# Complete deployment with SSL, reverse proxy, and monitoring
# Usage: ./deploy-production.sh [setup|deploy|ssl|monitoring|all]
# =====================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="${DOMAIN:-brain2gain.mx}"
EMAIL="${EMAIL:-admin@brain2gain.mx}"
PROJECT_NAME="brain2gain"

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
    fi
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
    fi
    
    # Check if docker compose is available
    if ! docker compose version &> /dev/null; then
        error "Docker Compose is not available. Please install Docker Compose."
    fi
    
    # Check if domain resolves to this server
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "unknown")
    log "Server IP: $SERVER_IP"
    
    success "Prerequisites check completed"
}

# Setup system dependencies
setup_system() {
    log "Setting up system dependencies..."
    
    # Update system
    apt-get update -y
    apt-get upgrade -y
    
    # Install required packages
    apt-get install -y curl wget gnupg lsb-release ufw fail2ban
    
    # Configure firewall
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 9090/tcp  # Prometheus
    ufw allow 3001/tcp  # Grafana
    ufw --force enable
    
    success "System setup completed"
}

# Setup SSL certificates
setup_ssl() {
    log "Setting up SSL certificates..."
    
    # Create SSL directory
    mkdir -p ./nginx/ssl/$DOMAIN
    
    # Check if certificates already exist
    if [[ -f "./nginx/ssl/$DOMAIN/fullchain.pem" ]]; then
        warning "SSL certificates already exist for $DOMAIN"
        return 0
    fi
    
    log "Obtaining SSL certificates for $DOMAIN..."
    
    # Start nginx temporarily for certificate validation
    docker compose -f docker-compose.ssl.yml up nginx -d
    sleep 10
    
    # Obtain certificates
    docker compose -f docker-compose.ssl.yml run --rm certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        --domains $DOMAIN,www.$DOMAIN,api.$DOMAIN \
        --verbose
    
    if [[ $? -eq 0 ]]; then
        success "SSL certificates obtained successfully"
    else
        error "Failed to obtain SSL certificates"
    fi
    
    # Stop temporary nginx
    docker compose -f docker-compose.ssl.yml down
}

# Deploy main application
deploy_app() {
    log "Deploying Brain2Gain application..."
    
    # Create necessary directories
    mkdir -p logs/{backend,frontend,nginx}
    
    # Generate secrets if they don't exist
    if [[ ! -f "./secrets/postgres_password.txt" ]]; then
        log "Generating secure credentials..."
        ./scripts/generate-secrets.sh
    fi
    
    # Deploy production stack
    log "Starting production services..."
    docker compose -f docker-compose.prod.yml --env-file .env.production up -d
    
    # Wait for services to be ready
    log "Waiting for services to start..."
    sleep 30
    
    # Check service health
    check_service_health
    
    success "Application deployed successfully"
}

# Deploy SSL and reverse proxy
deploy_ssl() {
    log "Deploying SSL and reverse proxy..."
    
    # Ensure SSL certificates exist
    if [[ ! -f "./nginx/ssl/$DOMAIN/fullchain.pem" ]]; then
        setup_ssl
    fi
    
    # Deploy nginx reverse proxy
    docker compose -f docker-compose.prod.yml -f docker-compose.ssl.yml --env-file .env.production up -d
    
    # Start certbot for automatic renewal
    docker compose -f docker-compose.ssl.yml --profile ssl up -d
    
    success "SSL and reverse proxy deployed"
}

# Deploy monitoring stack
deploy_monitoring() {
    log "Deploying monitoring stack..."
    
    # Ensure Grafana secrets exist
    if [[ ! -f "./secrets/grafana_admin_password.txt" ]]; then
        openssl rand -base64 32 > ./secrets/grafana_admin_password.txt
        log "Generated Grafana admin password"
    fi
    
    if [[ ! -f "./secrets/grafana_secret_key.txt" ]]; then
        openssl rand -base64 32 > ./secrets/grafana_secret_key.txt
        log "Generated Grafana secret key"
    fi
    
    # Deploy monitoring services
    docker compose -f docker-compose.monitoring.yml up -d
    
    # Wait for services to start
    log "Waiting for monitoring services to start..."
    sleep 60
    
    # Check monitoring health
    check_monitoring_health
    
    success "Monitoring stack deployed successfully"
}

# Check service health
check_service_health() {
    log "Checking service health..."
    
    local services=("postgres" "redis" "backend" "frontend")
    local healthy=0
    
    for service in "${services[@]}"; do
        if docker compose -f docker-compose.prod.yml ps --filter "name=brain2gain-${service}" --format "table {{.Health}}" | grep -q "healthy"; then
            success "$service is healthy"
            ((healthy++))
        else
            warning "$service is not healthy"
        fi
    done
    
    if [[ $healthy -eq ${#services[@]} ]]; then
        success "All services are healthy"
    else
        warning "Some services are not healthy. Check logs with: docker compose logs"
    fi
}

# Check monitoring health
check_monitoring_health() {
    log "Checking monitoring services health..."
    
    local services=("prometheus" "grafana" "elasticsearch")
    local healthy=0
    
    for service in "${services[@]}"; do
        if docker compose -f docker-compose.monitoring.yml ps --filter "name=brain2gain-${service}" --format "table {{.Health}}" | grep -q "healthy"; then
            success "$service is healthy"
            ((healthy++))
        else
            warning "$service is not healthy"
        fi
    done
    
    if [[ $healthy -eq ${#services[@]} ]]; then
        success "All monitoring services are healthy"
    else
        warning "Some monitoring services are not healthy"
    fi
}

# Show deployment status
show_status() {
    log "Deployment Status"
    echo "=================="
    
    # Main services
    echo -e "\n${BLUE}Main Services:${NC}"
    docker compose -f docker-compose.prod.yml ps
    
    # SSL and Nginx
    echo -e "\n${BLUE}SSL & Reverse Proxy:${NC}"
    docker compose -f docker-compose.ssl.yml ps
    
    # Monitoring
    echo -e "\n${BLUE}Monitoring Services:${NC}"
    docker compose -f docker-compose.monitoring.yml ps
    
    # URLs
    echo -e "\n${BLUE}Access URLs:${NC}"
    echo "🌐 Main Site: https://$DOMAIN"
    echo "🔧 API: https://api.$DOMAIN"
    echo "📊 Grafana: http://$DOMAIN:3001"
    echo "🔥 Prometheus: http://$DOMAIN:9090"
    echo "📋 Kibana: http://$DOMAIN:5601"
    
    # Credentials
    echo -e "\n${BLUE}Credentials:${NC}"
    if [[ -f "./secrets/grafana_admin_password.txt" ]]; then
        echo "📊 Grafana Admin: admin / $(cat ./secrets/grafana_admin_password.txt)"
    fi
}

# Generate secrets script
create_secrets_script() {
    cat > ./scripts/generate-secrets.sh << 'EOF'
#!/bin/bash
# Generate secure credentials for Brain2Gain

mkdir -p secrets

# Generate cryptographically secure passwords
openssl rand -base64 32 > secrets/postgres_password.txt
openssl rand -base64 32 > secrets/redis_password.txt
openssl rand -base64 64 > secrets/secret_key.txt
openssl rand -base64 32 > secrets/jwt_secret.txt
openssl rand -base64 16 > secrets/smtp_password.txt
openssl rand -base64 32 > secrets/superuser_password.txt
openssl rand -base64 32 > secrets/grafana_admin_password.txt
openssl rand -base64 32 > secrets/grafana_secret_key.txt

echo "✅ All secrets generated successfully"
EOF
    chmod +x ./scripts/generate-secrets.sh
}

# Main deployment function
main() {
    local action="${1:-all}"
    
    log "Starting Brain2Gain Production Deployment"
    log "Action: $action"
    log "Domain: $DOMAIN"
    
    case $action in
        "setup")
            check_root
            check_prerequisites
            setup_system
            create_secrets_script
            ;;
        "deploy")
            check_prerequisites
            deploy_app
            ;;
        "ssl")
            check_prerequisites
            setup_ssl
            deploy_ssl
            ;;
        "monitoring")
            check_prerequisites
            deploy_monitoring
            ;;
        "all")
            check_root
            check_prerequisites
            setup_system
            create_secrets_script
            setup_ssl
            deploy_app
            deploy_ssl
            deploy_monitoring
            show_status
            ;;
        "status")
            show_status
            ;;
        *)
            echo "Usage: $0 [setup|deploy|ssl|monitoring|all|status]"
            echo ""
            echo "Commands:"
            echo "  setup      - Setup system dependencies and firewall"
            echo "  deploy     - Deploy main application services"
            echo "  ssl        - Setup SSL certificates and reverse proxy"
            echo "  monitoring - Deploy monitoring stack"
            echo "  all        - Full deployment (recommended)"
            echo "  status     - Show deployment status"
            exit 1
            ;;
    esac
    
    success "Deployment completed successfully!"
}

# Execute main function with all arguments
main "$@"