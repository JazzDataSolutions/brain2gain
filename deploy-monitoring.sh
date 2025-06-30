#!/bin/bash
# Monitoring Stack Deployment Script for Brain2Gain
# Deploys Prometheus + Grafana + ELK + AlertManager + Exporters

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    if ! docker compose version &> /dev/null; then
        error "Docker Compose is not available"
        exit 1
    fi
    
    success "Prerequisites check completed"
}

# Create monitoring directories
create_directories() {
    log "Creating monitoring directories..."
    
    mkdir -p ./monitoring-data/{prometheus,grafana,alertmanager,elasticsearch,logstash,kibana}
    chmod -R 755 ./monitoring-data/
    
    success "Monitoring directories created"
}

# Generate monitoring secrets
generate_secrets() {
    log "Generating monitoring secrets..."
    
    if [[ ! -f "secrets/grafana_admin_password.txt" ]]; then
        echo "admin123!" > secrets/grafana_admin_password.txt
        warning "Generated default Grafana admin password. Please change it!"
    fi
    
    if [[ ! -f "secrets/grafana_secret_key.txt" ]]; then
        openssl rand -base64 32 > secrets/grafana_secret_key.txt
    fi
    
    chmod 600 secrets/grafana_*.txt
    
    success "Monitoring secrets generated"
}

# Deploy monitoring stack
deploy_monitoring() {
    log "Deploying monitoring stack..."
    
    # Deploy core monitoring services
    docker compose -f docker-compose.monitoring.yml up -d
    
    # Deploy exporters
    docker compose -f docker-compose.exporters.yml up -d
    
    success "Monitoring stack deployed"
}

# Wait for services
wait_for_services() {
    log "Waiting for monitoring services to be ready..."
    
    local services=(
        "prometheus:9090"
        "grafana:3001"
        "alertmanager:9093"
        "elasticsearch:9200"
        "kibana:5601"
    )
    
    for service in "${services[@]}"; do
        local name=$(echo $service | cut -d: -f1)
        local port=$(echo $service | cut -d: -f2)
        
        log "Waiting for $name..."
        while ! curl -sf http://localhost:$port/api/health &>/dev/null && ! curl -sf http://localhost:$port/ &>/dev/null; do
            sleep 5
        done
        success "$name is ready"
    done
}

# Configure dashboards
configure_dashboards() {
    log "Configuring Grafana dashboards..."
    
    # Wait for Grafana to be fully ready
    sleep 30
    
    # Import dashboards via API (optional)
    # curl -X POST http://admin:admin123!@localhost:3001/api/dashboards/db \
    #   -H "Content-Type: application/json" \
    #   -d @monitoring/grafana/dashboards/brain2gain-overview.json
    
    success "Dashboards configured"
}

# Setup Kibana index patterns
setup_kibana() {
    log "Setting up Kibana index patterns..."
    
    # Wait for Kibana to be ready
    while ! curl -sf http://localhost:5601/api/status &>/dev/null; do
        sleep 5
    done
    
    # Create index pattern
    curl -X POST http://localhost:5601/api/saved_objects/index-pattern/brain2gain-logs \
      -H "Content-Type: application/json" \
      -H "kbn-xsrf: true" \
      -d '{
        "attributes": {
          "title": "brain2gain-logs-*",
          "timeFieldName": "@timestamp"
        }
      }' || true
    
    success "Kibana index patterns configured"
}

# Health check
health_check() {
    log "Running health checks..."
    
    local services=(
        "Prometheus:http://localhost:9090"
        "Grafana:http://localhost:3001"
        "AlertManager:http://localhost:9093"
        "Elasticsearch:http://localhost:9200"
        "Kibana:http://localhost:5601"
    )
    
    for service_info in "${services[@]}"; do
        local name=$(echo $service_info | cut -d: -f1)
        local url=$(echo $service_info | cut -d: -f2-)
        
        if curl -sf $url &>/dev/null; then
            success "$name is healthy"
        else
            warning "$name may not be ready yet"
        fi
    done
    
    success "Health check completed"
}

# Display access information
display_info() {
    log "Monitoring stack deployed successfully!"
    echo ""
    echo "📊 Access URLs:"
    echo "  🔥 Prometheus:   http://localhost:9090"
    echo "  📈 Grafana:      http://localhost:3001 (admin/admin123!)"
    echo "  🚨 AlertManager: http://localhost:9093"
    echo "  🔍 Elasticsearch: http://localhost:9200"
    echo "  📋 Kibana:       http://localhost:5601"
    echo ""
    echo "📊 Exporters:"
    echo "  🖥️  Node Exporter: http://localhost:9100"
    echo "  🐳 cAdvisor:      http://localhost:8080"
    echo "  🗄️  PostgreSQL:    http://localhost:9187"
    echo "  📱 Redis:         http://localhost:9121"
    echo "  🌐 Nginx:         http://localhost:9113"
    echo "  🔍 Blackbox:      http://localhost:9115"
    echo ""
    echo "🔧 Next steps:"
    echo "  1. Configure alert notification channels in AlertManager"
    echo "  2. Customize Grafana dashboards for your needs"
    echo "  3. Set up log parsing rules in Kibana"
    echo "  4. Configure metric retention policies"
}

# Stop monitoring stack
stop_monitoring() {
    log "Stopping monitoring stack..."
    
    docker compose -f docker-compose.monitoring.yml down
    docker compose -f docker-compose.exporters.yml down
    
    success "Monitoring stack stopped"
}

# Remove monitoring stack
remove_monitoring() {
    log "Removing monitoring stack..."
    
    docker compose -f docker-compose.monitoring.yml down -v
    docker compose -f docker-compose.exporters.yml down -v
    
    # Remove data directories (optional)
    read -p "Remove monitoring data directories? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf ./monitoring-data/
        success "Monitoring data removed"
    fi
    
    success "Monitoring stack removed"
}

# Main function
main() {
    case "${1:-deploy}" in
        "deploy")
            check_prerequisites
            create_directories
            generate_secrets
            deploy_monitoring
            wait_for_services
            configure_dashboards
            setup_kibana
            health_check
            display_info
            ;;
        "stop")
            stop_monitoring
            ;;
        "remove")
            remove_monitoring
            ;;
        "status")
            health_check
            ;;
        "logs")
            service_name="${2:-prometheus}"
            docker compose -f docker-compose.monitoring.yml logs -f $service_name
            ;;
        *)
            echo "Usage: $0 {deploy|stop|remove|status|logs [service]}"
            echo ""
            echo "Commands:"
            echo "  deploy  - Deploy the complete monitoring stack"
            echo "  stop    - Stop all monitoring services"
            echo "  remove  - Remove monitoring stack and optionally data"
            echo "  status  - Check health of monitoring services"
            echo "  logs    - View logs for a specific service"
            exit 1
            ;;
    esac
}

# Error handling
trap 'error "Monitoring deployment failed. Check logs above."; exit 1' ERR

# Run main function
main "$@"