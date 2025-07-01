#!/bin/bash
# Brain2Gain VPS Production Deployment Script
# Automated deployment to brain2gain.mx (5.183.9.128)
# Based on existing project infrastructure

set -e

# Configuration
VPS_HOST="5.183.9.128"
VPS_USER="root"
DOMAIN="brain2gain.mx"
PROJECT_NAME="brain2gain"
APP_DIR="/opt/brain2gain"

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

# Test SSH connection
test_ssh() {
    log "Testing SSH connection to VPS..."
    if ssh -o ConnectTimeout=10 $VPS_USER@$VPS_HOST "echo 'SSH connection successful'" &>/dev/null; then
        success "SSH connection established to $VPS_HOST"
    else
        error "Cannot connect to VPS. Please check your SSH configuration"
        echo "Try: ssh root@$VPS_HOST"
        exit 1
    fi
}

# Setup VPS environment
setup_vps() {
    log "Setting up VPS environment for Brain2Gain..."
    
    ssh $VPS_USER@$VPS_HOST << 'EOF'
        # Update system
        apt update && apt upgrade -y
        
        # Install essential packages
        apt install -y curl wget git unzip software-properties-common \
                      apt-transport-https ca-certificates gnupg lsb-release \
                      htop nginx certbot python3-certbot-nginx fail2ban ufw \
                      nano tree

        # Install Docker
        if ! command -v docker &> /dev/null; then
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
            apt update
            apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            
            # Configure Docker
            mkdir -p /etc/docker
            cat > /etc/docker/daemon.json << 'DOCKER_EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
DOCKER_EOF
            
            systemctl start docker
            systemctl enable docker
        fi
        
        # Create application directories
        mkdir -p /opt/brain2gain/{data/{postgres,redis},logs/{backend,frontend},backups,ssl,secrets}
        chmod 755 /opt/brain2gain
        
        # Configure UFW firewall
        ufw default deny incoming
        ufw default allow outgoing
        ufw allow ssh
        ufw allow 80
        ufw allow 443
        ufw allow 3001  # Grafana
        ufw allow 9090  # Prometheus
        ufw --force enable
        
        echo "VPS environment setup completed"
EOF
    
    success "VPS environment configured"
}

# Generate SSL certificates
setup_ssl() {
    log "Setting up SSL certificates for $DOMAIN..."
    
    ssh $VPS_USER@$VPS_HOST << EOF
        # Stop nginx temporarily
        systemctl stop nginx || true
        
        # Generate SSL certificates
        certbot certonly --standalone \
            -d $DOMAIN \
            -d www.$DOMAIN \
            -d api.$DOMAIN \
            -d admin.$DOMAIN \
            -d monitoring.$DOMAIN \
            --non-interactive \
            --agree-tos \
            --email admin@$DOMAIN \
            --no-eff-email
        
        # Set up auto-renewal
        echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
        
        # Copy certificates to app directory
        cp -r /etc/letsencrypt/live/$DOMAIN /opt/brain2gain/ssl/
        chmod -R 644 /opt/brain2gain/ssl/
        
        echo "SSL certificates configured"
EOF
    
    success "SSL certificates generated for $DOMAIN"
}

# Deploy application files
deploy_files() {
    log "Deploying Brain2Gain application files to VPS..."
    
    # Create deployment archive
    log "Creating deployment archive..."
    tar -czf brain2gain-deploy.tar.gz \
        --exclude='.git' \
        --exclude='node_modules' \
        --exclude='htmlcov' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.env*' \
        --exclude='monitoring-data' \
        --exclude='logs' \
        --exclude='test-results' \
        --exclude='blob-report' \
        .
    
    # Upload to VPS
    log "Uploading files to VPS..."
    scp brain2gain-deploy.tar.gz $VPS_USER@$VPS_HOST:/opt/brain2gain/
    
    # Extract on VPS
    ssh $VPS_USER@$VPS_HOST << 'EOF'
        cd /opt/brain2gain
        tar -xzf brain2gain-deploy.tar.gz
        rm brain2gain-deploy.tar.gz
        echo "Application files extracted"
EOF
    
    # Clean up local archive
    rm brain2gain-deploy.tar.gz
    
    success "Application files deployed"
}

# Generate production environment
generate_env() {
    log "Generating production environment configuration..."
    
    ssh $VPS_USER@$VPS_HOST << EOF
        cd /opt/brain2gain
        
        # Generate secure passwords
        POSTGRES_PASSWORD=\$(openssl rand -base64 32)
        REDIS_PASSWORD=\$(openssl rand -base64 32)
        SECRET_KEY=\$(openssl rand -base64 32)
        JWT_SECRET=\$(openssl rand -base64 32)
        GRAFANA_PASSWORD=\$(openssl rand -base64 16)
        
        # Store secrets
        echo "\$POSTGRES_PASSWORD" > secrets/postgres_password.txt
        echo "\$REDIS_PASSWORD" > secrets/redis_password.txt
        echo "\$SECRET_KEY" > secrets/secret_key.txt
        echo "\$JWT_SECRET" > secrets/jwt_secret.txt
        echo "\$GRAFANA_PASSWORD" > secrets/grafana_admin_password.txt
        echo "\$SECRET_KEY" > secrets/grafana_secret_key.txt
        chmod 600 secrets/*.txt
        
        # Create production environment file
        cat > .env.production << ENV_EOF
# Brain2Gain Production Environment Configuration
ENVIRONMENT=production

# Database Configuration
POSTGRES_SERVER=postgres
POSTGRES_PORT=5432
POSTGRES_DB=brain2gain_prod
POSTGRES_USER=brain2gain_prod
POSTGRES_PASSWORD=\$POSTGRES_PASSWORD

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=\$REDIS_PASSWORD

# Application Settings
SECRET_KEY=\$SECRET_KEY
JWT_SECRET=\$JWT_SECRET
API_V1_STR=/api/v1
PROJECT_NAME="Brain2Gain Production"
BACKEND_CORS_ORIGINS=["https://$DOMAIN","https://www.$DOMAIN","https://api.$DOMAIN"]
FRONTEND_HOST=https://$DOMAIN

# Security
HASH_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Configuration (Update with your SMTP settings)
SMTP_TLS=True
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=admin@$DOMAIN
SMTP_PASSWORD=your-smtp-password

# Domain Configuration
DOMAIN=$DOMAIN

# Monitoring
PROMETHEUS_ENABLED=true
METRICS_ENABLED=true
ENV_EOF
        
        chmod 600 .env.production
        echo "Production environment configured"
EOF
    
    success "Production environment generated"
}

# Configure Nginx
configure_nginx() {
    log "Configuring Nginx reverse proxy for Brain2Gain..."
    
    ssh $VPS_USER@$VPS_HOST << EOF
        # Create Nginx configuration
        cat > /etc/nginx/sites-available/brain2gain << 'NGINX_EOF'
upstream backend_servers {
    server localhost:8000 max_fails=3 fail_timeout=30s;
}

upstream frontend_servers {
    server localhost:3000 max_fails=3 fail_timeout=30s;
}

upstream grafana_servers {
    server localhost:3001 max_fails=3 fail_timeout=30s;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN api.$DOMAIN admin.$DOMAIN monitoring.$DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

# Main application
server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Frontend
    location / {
        proxy_pass http://frontend_servers;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://backend_servers;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        client_max_body_size 50M;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
}

# API subdomain
server {
    listen 443 ssl http2;
    server_name api.$DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    location / {
        proxy_pass http://backend_servers;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

# Monitoring subdomain
server {
    listen 443 ssl http2;
    server_name monitoring.$DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    location / {
        proxy_pass http://grafana_servers;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
NGINX_EOF
        
        # Enable site
        ln -sf /etc/nginx/sites-available/brain2gain /etc/nginx/sites-enabled/
        rm -f /etc/nginx/sites-enabled/default
        
        # Test configuration
        nginx -t
        
        echo "Nginx configured"
EOF
    
    success "Nginx reverse proxy configured"
}

# Update docker-compose files for production
update_docker_configs() {
    log "Updating Docker configurations for production..."
    
    ssh $VPS_USER@$VPS_HOST << EOF
        cd /opt/brain2gain
        
        # Update docker-compose.prod.yml with correct domain
        sed -i "s/brain2gain\.com/$DOMAIN/g" docker-compose.prod.yml
        
        # Update CORS origins in backend environment
        sed -i "s/brain2gain\.com/$DOMAIN/g" .env.production
        
        echo "Docker configurations updated for $DOMAIN"
EOF
    
    success "Docker configurations updated"
}

# Deploy application stack
deploy_stack() {
    log "Deploying Brain2Gain application stack..."
    
    ssh $VPS_USER@$VPS_HOST << 'EOF'
        cd /opt/brain2gain
        
        # Deploy database services first
        log() { echo "[$(date +'%H:%M:%S')] $1"; }
        
        log "Starting PostgreSQL and Redis..."
        docker compose -f docker-compose.prod.yml up -d postgres redis
        
        # Wait for database to be ready
        log "Waiting for database services..."
        sleep 30
        
        # Check database health
        while ! docker exec brain2gain-postgres-prod pg_isready -U brain2gain_prod -d brain2gain_prod &>/dev/null; do
            log "Waiting for PostgreSQL..."
            sleep 5
        done
        
        # Check Redis health
        while ! docker exec brain2gain-redis-prod redis-cli ping | grep -q PONG &>/dev/null; do
            log "Waiting for Redis..."
            sleep 5
        done
        
        log "Database services ready. Deploying application..."
        
        # Deploy application services
        docker compose -f docker-compose.prod.yml up -d backend frontend
        
        # Wait for services to be ready
        log "Waiting for application services..."
        sleep 60
        
        # Run database migrations
        log "Running database migrations..."
        docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head
        
        log "Application stack deployed successfully"
EOF
    
    success "Application stack deployed"
}

# Deploy monitoring stack
deploy_monitoring() {
    log "Deploying monitoring stack..."
    
    ssh $VPS_USER@$VPS_HOST << 'EOF'
        cd /opt/brain2gain
        
        # Create monitoring data directories
        mkdir -p monitoring-data/{prometheus,grafana,alertmanager,elasticsearch,logstash,kibana}
        
        # Deploy monitoring services
        echo "Starting core monitoring services..."
        docker compose -f docker-compose.monitoring.yml up -d prometheus grafana alertmanager
        
        # Wait for core services
        sleep 30
        
        # Deploy ELK stack
        echo "Starting ELK stack..."
        docker compose -f docker-compose.monitoring.yml up -d elasticsearch
        sleep 60
        docker compose -f docker-compose.monitoring.yml up -d logstash kibana
        
        # Deploy exporters
        echo "Starting exporters..."
        docker compose -f docker-compose.exporters.yml up -d
        
        echo "Monitoring stack deployed"
EOF
    
    success "Monitoring stack deployed"
}

# Start Nginx
start_nginx() {
    log "Starting Nginx..."
    
    ssh $VPS_USER@$VPS_HOST << 'EOF'
        systemctl start nginx
        systemctl enable nginx
        echo "Nginx started and enabled"
EOF
    
    success "Nginx started"
}

# Setup backup cron
setup_backup() {
    log "Setting up automated backups..."
    
    ssh $VPS_USER@$VPS_HOST << 'EOF'
        # Create backup script
        cat > /opt/brain2gain/backup.sh << 'BACKUP_EOF'
#!/bin/bash
set -e

BACKUP_DIR="/opt/brain2gain/backups"
DATE=$(date +%Y%m%d_%H%M%S)

echo "Starting Brain2Gain backup at $(date)"

# PostgreSQL backup
echo "Backing up PostgreSQL..."
docker exec brain2gain-postgres-prod pg_dump -U brain2gain_prod brain2gain_prod | gzip > "$BACKUP_DIR/postgres_$DATE.sql.gz"

# Redis backup
echo "Backing up Redis..."
docker exec brain2gain-redis-prod redis-cli --rdb /tmp/dump.rdb
docker cp brain2gain-redis-prod:/tmp/dump.rdb "$BACKUP_DIR/redis_$DATE.rdb"

# Application data backup
echo "Backing up application data..."
tar -czf "$BACKUP_DIR/app_data_$DATE.tar.gz" -C /opt/brain2gain logs uploads

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Brain2Gain backup completed at $(date)"
BACKUP_EOF
        
        chmod +x /opt/brain2gain/backup.sh
        
        # Add to crontab
        echo "0 2 * * * /opt/brain2gain/backup.sh >> /var/log/brain2gain_backup.log 2>&1" | crontab -
        
        echo "Backup cron job configured for daily 2 AM"
EOF
    
    success "Automated backups configured"
}

# Health check
health_check() {
    log "Running deployment health checks..."
    
    ssh $VPS_USER@$VPS_HOST << 'EOF'
        echo "=== Brain2Gain Health Check ==="
        echo "=== Docker Services Status ==="
        docker compose -f /opt/brain2gain/docker-compose.prod.yml ps
        
        echo -e "\n=== Service Health Checks ==="
        # Backend API
        if curl -sf http://localhost:8000/api/v1/utils/health-check/ &>/dev/null; then
            echo "✅ Backend API: Healthy"
        else
            echo "❌ Backend API: Not responding"
        fi
        
        # Frontend
        if curl -sf http://localhost:3000/ &>/dev/null; then
            echo "✅ Frontend: Healthy"
        else
            echo "❌ Frontend: Not responding"
        fi
        
        # Database
        if docker exec brain2gain-postgres-prod pg_isready -U brain2gain_prod &>/dev/null; then
            echo "✅ PostgreSQL: Healthy"
        else
            echo "❌ PostgreSQL: Not ready"
        fi
        
        # Redis
        if docker exec brain2gain-redis-prod redis-cli ping | grep -q PONG &>/dev/null; then
            echo "✅ Redis: Healthy"
        else
            echo "❌ Redis: Not responding"
        fi
        
        echo -e "\n=== Nginx Status ==="
        systemctl status nginx --no-pager -l
        
        echo -e "\n=== SSL Certificate Status ==="
        certbot certificates
        
        echo -e "\n=== Disk Usage ==="
        df -h
        
        echo -e "\n=== Memory Usage ==="
        free -h
EOF
    
    success "Health check completed"
}

# Display access information
display_info() {
    log "🚀 Brain2Gain deployment completed successfully!"
    echo ""
    echo "🌐 Access URLs:"
    echo "  📱 Main Site:     https://$DOMAIN"
    echo "  🔧 API:           https://api.$DOMAIN"
    echo "  👤 Admin:         https://$DOMAIN/admin"
    echo "  📊 Monitoring:    https://monitoring.$DOMAIN"
    echo ""
    echo "📊 Monitoring Services:"
    echo "  📈 Grafana:       https://monitoring.$DOMAIN (admin/[generated])"
    echo "  🔥 Prometheus:    https://$DOMAIN:9090"
    echo "  🚨 AlertManager:  https://$DOMAIN:9093"
    echo "  📋 Kibana:        https://$DOMAIN:5601"
    echo ""
    echo "🔧 SSH Access:"
    echo "  ssh $VPS_USER@$VPS_HOST"
    echo ""
    echo "📝 Important Files on VPS:"
    echo "  Application:      /opt/brain2gain/"
    echo "  Logs:            /opt/brain2gain/logs/"
    echo "  Backups:         /opt/brain2gain/backups/"
    echo "  SSL Certs:       /opt/brain2gain/ssl/"
    echo "  Secrets:         /opt/brain2gain/secrets/"
    echo ""
    echo "🔑 Next Steps:"
    echo "  1. Update SMTP settings in .env.production"
    echo "  2. Configure monitoring alerts"
    echo "  3. Test backup and restore procedures"
    echo "  4. Set up monitoring notification channels"
    echo "  5. Configure domain DNS records:"
    echo "     A    @               $VPS_HOST"
    echo "     A    www             $VPS_HOST"
    echo "     A    api             $VPS_HOST"
    echo "     A    admin           $VPS_HOST"
    echo "     A    monitoring      $VPS_HOST"
    echo ""
    success "Brain2Gain is ready for production use!"
}

# Rollback function
rollback() {
    log "Rolling back Brain2Gain deployment..."
    
    ssh $VPS_USER@$VPS_HOST << 'EOF'
        cd /opt/brain2gain
        docker compose -f docker-compose.prod.yml down
        docker compose -f docker-compose.monitoring.yml down
        docker compose -f docker-compose.exporters.yml down
        systemctl stop nginx
EOF
    
    warning "Deployment rolled back"
}

# Show logs
show_logs() {
    local service=${1:-all}
    
    ssh $VPS_USER@$VPS_HOST << EOF
        cd /opt/brain2gain
        if [ "$service" = "all" ]; then
            echo "=== Backend Logs ==="
            docker compose -f docker-compose.prod.yml logs --tail=50 backend
            echo -e "\n=== Frontend Logs ==="
            docker compose -f docker-compose.prod.yml logs --tail=50 frontend
        else
            docker compose -f docker-compose.prod.yml logs --tail=100 -f $service
        fi
EOF
}

# Main deployment function
main() {
    case "${1:-deploy}" in
        "setup")
            test_ssh
            setup_vps
            success "VPS setup completed. Run './deploy-vps-brain2gain.sh deploy' to deploy the application."
            ;;
        "deploy")
            test_ssh
            deploy_files
            generate_env
            update_docker_configs
            setup_ssl
            configure_nginx
            deploy_stack
            deploy_monitoring
            setup_backup
            start_nginx
            sleep 30
            health_check
            display_info
            ;;
        "monitoring")
            test_ssh
            deploy_monitoring
            success "Monitoring stack deployed"
            ;;
        "status")
            test_ssh
            health_check
            ;;
        "logs")
            test_ssh
            show_logs $2
            ;;
        "rollback")
            test_ssh
            rollback
            ;;
        *)
            echo "Brain2Gain VPS Deployment Script"
            echo "Usage: $0 {setup|deploy|monitoring|status|logs [service]|rollback}"
            echo ""
            echo "Commands:"
            echo "  setup      - Initial VPS setup (Docker, SSL, Nginx)"
            echo "  deploy     - Full deployment of Brain2Gain application"
            echo "  monitoring - Deploy only monitoring stack"
            echo "  status     - Check deployment health"
            echo "  logs       - Show service logs (default: all)"
            echo "  rollback   - Rollback deployment"
            echo ""
            echo "Examples:"
            echo "  $0 setup                    # Initial VPS setup"
            echo "  $0 deploy                   # Full deployment"
            echo "  $0 logs backend             # Show backend logs"
            echo "  $0 status                   # Health check"
            exit 1
            ;;
    esac
}

# Error handling
trap 'error "Deployment failed. Check logs above."; exit 1' ERR

# Run main function
main "$@"