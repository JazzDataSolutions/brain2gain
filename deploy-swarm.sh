#!/bin/bash
# Production Deployment Script - Docker Swarm
# Brain2Gain Full Stack Application

set -e

# Configuration
STACK_NAME="brain2gain"
COMPOSE_FILE="docker-compose.prod.yml"
SWARM_FILE="docker-swarm.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
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
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Swarm
    if ! docker info --format '{{.Swarm.LocalNodeState}}' | grep -q "active"; then
        warning "Docker Swarm not initialized. Initializing..."
        docker swarm init
    fi
    
    # Check required files
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        error "Production compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    # Check secrets directory
    if [[ ! -d "secrets" ]]; then
        error "Secrets directory not found. Please create secrets first."
        exit 1
    fi
    
    success "Prerequisites check completed"
}

# Create production directories
create_directories() {
    log "Creating production directories..."
    
    sudo mkdir -p /opt/brain2gain/{data/{postgres,redis},logs/{backend,frontend},backups,ssl}
    sudo chown -R $(whoami):$(whoami) /opt/brain2gain/
    
    success "Production directories created"
}

# Build production images
build_images() {
    log "Building production images..."
    
    # Build backend
    log "Building backend image..."
    docker build -f backend/Dockerfile.prod -t brain2gain/backend:latest ./backend/
    
    # Build frontend  
    log "Building frontend image..."
    docker build -f frontend/Dockerfile.prod -t brain2gain/frontend:latest ./frontend/
    
    success "Production images built successfully"
}

# Deploy to swarm
deploy_stack() {
    log "Deploying stack to Docker Swarm..."
    
    # Deploy the stack
    docker stack deploy -c $SWARM_FILE $STACK_NAME
    
    success "Stack deployed successfully"
}

# Wait for services to be ready
wait_for_services() {
    log "Waiting for services to be ready..."
    
    # Wait for database
    log "Waiting for PostgreSQL..."
    while ! docker exec $(docker ps -q -f name=${STACK_NAME}_postgres) pg_isready -U brain2gain_prod -d brain2gain_prod &>/dev/null; do
        sleep 2
    done
    
    # Wait for Redis
    log "Waiting for Redis..."
    while ! docker exec $(docker ps -q -f name=${STACK_NAME}_redis) redis-cli -a "$(cat secrets/redis_password.txt)" ping | grep -q PONG &>/dev/null; do
        sleep 2
    done
    
    # Wait for backend
    log "Waiting for Backend API..."
    while ! curl -sf http://localhost:8000/api/v1/utils/health-check/ &>/dev/null; do
        sleep 5
    done
    
    # Wait for frontend
    log "Waiting for Frontend..."
    while ! curl -sf http://localhost/health &>/dev/null; do
        sleep 3
    done
    
    success "All services are ready"
}

# Health check
health_check() {
    log "Running health checks..."
    
    # Check all services
    docker stack services $STACK_NAME
    
    # Detailed service status
    for service in postgres redis backend frontend loadbalancer; do
        replicas=$(docker service ls --filter name=${STACK_NAME}_${service} --format "{{.Replicas}}")
        if [[ "$replicas" == *"/"* ]]; then
            running=$(echo $replicas | cut -d'/' -f1)
            desired=$(echo $replicas | cut -d'/' -f2)
            if [[ "$running" == "$desired" ]]; then
                success "Service ${service}: ${replicas}"
            else
                warning "Service ${service}: ${replicas} (not all replicas running)"
            fi
        fi
    done
    
    success "Health check completed"
}

# Rollback function
rollback() {
    log "Rolling back deployment..."
    docker stack rm $STACK_NAME
    warning "Stack rolled back. Previous version restored."
}

# Main deployment function
main() {
    log "Starting Brain2Gain production deployment..."
    
    case "${1:-deploy}" in
        "deploy")
            check_prerequisites
            create_directories
            build_images
            deploy_stack
            wait_for_services
            health_check
            success "🚀 Brain2Gain deployed successfully!"
            ;;
        "rollback")
            rollback
            ;;
        "status")
            health_check
            ;;
        "logs")
            service_name="${2:-backend}"
            docker service logs -f ${STACK_NAME}_${service_name}
            ;;
        "scale")
            service_name="$2"
            replicas="$3"
            if [[ -z "$service_name" || -z "$replicas" ]]; then
                error "Usage: $0 scale <service_name> <replicas>"
                exit 1
            fi
            docker service scale ${STACK_NAME}_${service_name}=${replicas}
            ;;
        *)
            echo "Usage: $0 {deploy|rollback|status|logs [service]|scale <service> <replicas>}"
            exit 1
            ;;
    esac
}

# Trap for cleanup on error
trap 'error "Deployment failed. Check logs above."; exit 1' ERR

# Run main function
main "$@"