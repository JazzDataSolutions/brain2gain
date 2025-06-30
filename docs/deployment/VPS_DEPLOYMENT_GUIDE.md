# 🚀 Brain2Gain VPS Deployment Guide

Complete guide for deploying Brain2Gain e-commerce platform to a Virtual Private Server (VPS) with production-ready infrastructure.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [VPS Requirements](#vps-requirements)
3. [Initial Server Setup](#initial-server-setup)
4. [Docker Installation](#docker-installation)
5. [Domain and SSL Setup](#domain-and-ssl-setup)
6. [Environment Configuration](#environment-configuration)
7. [Database Setup](#database-setup)
8. [Application Deployment](#application-deployment)
9. [Monitoring Stack Deployment](#monitoring-stack-deployment)
10. [Load Balancer Configuration](#load-balancer-configuration)
11. [Backup Setup](#backup-setup)
12. [Security Hardening](#security-hardening)
13. [Post-Deployment Verification](#post-deployment-verification)
14. [Maintenance](#maintenance)
15. [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

### Required Knowledge
- Basic Linux command line
- Docker and Docker Compose
- Domain management (DNS)
- SSL certificate setup

### Local Requirements
- Git installed
- SSH client
- Domain name (recommended)

## 🖥️ VPS Requirements

### Minimum Specifications
```yaml
Production Environment:
  CPU: 4 vCPUs
  RAM: 8GB
  Storage: 100GB SSD
  Bandwidth: 1TB/month
  OS: Ubuntu 22.04 LTS

Development/Staging:
  CPU: 2 vCPUs  
  RAM: 4GB
  Storage: 50GB SSD
  Bandwidth: 500GB/month
  OS: Ubuntu 22.04 LTS
```

### Recommended VPS Providers
- **DigitalOcean**: Droplets ($40-80/month)
- **Linode**: Shared/Dedicated instances ($30-60/month)
- **Vultr**: High Performance instances ($24-48/month)
- **Hetzner**: CX31-CX41 instances (€8-16/month)
- **AWS EC2**: t3.medium/large instances ($24-48/month)

## ⚙️ Initial Server Setup

### 1. Connect to Your VPS

```bash
# Connect via SSH (replace with your VPS IP)
ssh root@YOUR_VPS_IP

# Or if using SSH key
ssh -i ~/.ssh/your_key root@YOUR_VPS_IP
```

### 2. Update System

```bash
# Update package list and upgrade system
apt update && apt upgrade -y

# Install essential packages
apt install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release
```

### 3. Create Application User

```bash
# Create dedicated user for the application
adduser brain2gain
usermod -aG sudo brain2gain

# Switch to application user
su - brain2gain
```

### 4. Configure SSH Keys (Optional but Recommended)

```bash
# On your local machine, copy SSH key to server
ssh-copy-id brain2gain@YOUR_VPS_IP

# Or manually copy your public key
mkdir -p ~/.ssh
echo "your-public-key-here" >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

## 🐳 Docker Installation

### 1. Install Docker

```bash
# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker brain2gain

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Verify installation
docker --version
docker compose version
```

### 2. Configure Docker

```bash
# Create Docker daemon configuration
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
EOF

# Restart Docker
sudo systemctl restart docker
```

## 🌐 Domain and SSL Setup

### 1. Domain Configuration

Point your domain to your VPS IP:

```bash
# DNS Records needed:
A     @               YOUR_VPS_IP
A     www             YOUR_VPS_IP
A     api             YOUR_VPS_IP
A     admin           YOUR_VPS_IP
A     monitoring      YOUR_VPS_IP

# Optional subdomains:
A     grafana         YOUR_VPS_IP
A     prometheus      YOUR_VPS_IP
A     kibana          YOUR_VPS_IP
```

### 2. Install Certbot for SSL

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Generate SSL certificates (replace with your domain)
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com

# Set up auto-renewal
sudo crontab -e
# Add this line:
0 12 * * * /usr/bin/certbot renew --quiet
```

## 🔧 Environment Configuration

### 1. Clone Repository

```bash
# Clone the Brain2Gain repository
git clone https://github.com/YourUsername/brain2gain.git
cd brain2gain
```

### 2. Create Environment Files

```bash
# Create production environment file
cp .env.example .env.production

# Edit production environment
nano .env.production
```

### 3. Production Environment Variables

```bash
# .env.production
ENVIRONMENT=production

# Database Configuration
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=brain2gain_prod
POSTGRES_USER=brain2gain_prod
POSTGRES_PASSWORD=your_secure_password_here

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password_here

# Application Settings
SECRET_KEY=your_super_secure_secret_key_here
API_V1_STR=/api/v1
PROJECT_NAME="Brain2Gain Production"
BACKEND_CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]

# Security
HASH_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Configuration
SMTP_TLS=True
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# File Upload
MAX_FILE_SIZE=10485760
UPLOAD_FOLDER=uploads

# Monitoring
PROMETHEUS_ENABLED=true
METRICS_ENABLED=true

# Domain Configuration
DOMAIN=yourdomain.com
```

### 4. Create Secrets

```bash
# Create secrets directory
mkdir -p secrets

# Generate secure passwords
openssl rand -base64 32 > secrets/postgres_password.txt
openssl rand -base64 32 > secrets/redis_password.txt
openssl rand -base64 32 > secrets/secret_key.txt
openssl rand -base64 32 > secrets/grafana_admin_password.txt
openssl rand -base64 32 > secrets/grafana_secret_key.txt

# Set proper permissions
chmod 600 secrets/*.txt
```

## 🗄️ Database Setup

### 1. Deploy Database Services

```bash
# Start PostgreSQL and Redis
docker compose -f docker-compose.yml up -d postgres redis

# Wait for services to be ready
docker compose ps

# Check logs
docker compose logs postgres
docker compose logs redis
```

### 2. Initialize Database

```bash
# Run database migrations
docker compose exec backend alembic upgrade head

# Create initial admin user (optional)
docker compose exec backend python -c "
from app.core.init_db import init_db
init_db()
"
```

## 🚀 Application Deployment

### 1. Build and Deploy Application

```bash
# Build all services
docker compose build

# Deploy complete stack
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify deployment
docker compose ps
```

### 2. Production Docker Compose Override

Create `docker-compose.prod.yml`:

```yaml
# docker-compose.prod.yml
services:
  backend:
    restart: unless-stopped
    environment:
      - ENVIRONMENT=production
    env_file:
      - .env.production
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'

  frontend:
    restart: unless-stopped
    environment:
      - NODE_ENV=production
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.25'

  postgres:
    restart: unless-stopped
    command: >
      postgres
      -c max_connections=100
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c maintenance_work_mem=64MB
      -c checkpoint_completion_target=0.9
      -c wal_buffers=16MB
      -c default_statistics_target=100
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

  redis:
    restart: unless-stopped
    command: >
      redis-server
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --appendonly yes
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.25'
```

## 📊 Monitoring Stack Deployment

### 1. Deploy Monitoring Services

```bash
# Deploy core monitoring
docker compose -f docker-compose.monitoring.yml up -d prometheus grafana alertmanager

# Deploy system exporters
docker compose -f docker-compose.monitoring.yml up -d node-exporter cadvisor

# Wait for services and then deploy ELK stack
sleep 30
docker compose -f docker-compose.monitoring.yml up -d elasticsearch
sleep 60
docker compose -f docker-compose.monitoring.yml up -d logstash kibana filebeat
```

### 2. Configure Monitoring Access

```bash
# Get Grafana admin password
cat secrets/grafana_admin_password.txt

# Access monitoring services:
# Grafana: https://yourdomain.com:3001 (admin/password)
# Prometheus: https://yourdomain.com:9090
# AlertManager: https://yourdomain.com:9093
# Kibana: https://yourdomain.com:5601
```

## ⚖️ Load Balancer Configuration

### 1. Install and Configure Nginx

```bash
# Install Nginx
sudo apt install -y nginx

# Create site configuration
sudo nano /etc/nginx/sites-available/brain2gain
```

### 2. Nginx Configuration

```nginx
# /etc/nginx/sites-available/brain2gain
upstream backend_servers {
    server localhost:8000 max_fails=3 fail_timeout=30s;
}

upstream frontend_servers {
    server localhost:5173 max_fails=3 fail_timeout=30s;
}

upstream grafana_servers {
    server localhost:3001 max_fails=3 fail_timeout=30s;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# Main application
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
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
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://backend_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # API specific settings
        client_max_body_size 50M;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
}

# Monitoring subdomain
server {
    listen 443 ssl http2;
    server_name monitoring.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Basic auth for monitoring (optional)
    # auth_basic "Monitoring Access";
    # auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://grafana_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Enable Site

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/brain2gain /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## 💾 Backup Setup

### 1. Database Backup Script

```bash
# Create backup directory
sudo mkdir -p /opt/backups/brain2gain
sudo chown brain2gain:brain2gain /opt/backups/brain2gain

# Create backup script
nano /home/brain2gain/backup.sh
```

```bash
#!/bin/bash
# backup.sh

set -e

BACKUP_DIR="/opt/backups/brain2gain"
DATE=$(date +%Y%m%d_%H%M%S)
POSTGRES_CONTAINER="brain2gain-postgres-1"
REDIS_CONTAINER="brain2gain-redis-1"

echo "Starting backup at $(date)"

# PostgreSQL backup
echo "Backing up PostgreSQL..."
docker exec $POSTGRES_CONTAINER pg_dump -U brain2gain_prod brain2gain_prod | gzip > "$BACKUP_DIR/postgres_$DATE.sql.gz"

# Redis backup
echo "Backing up Redis..."
docker exec $REDIS_CONTAINER redis-cli --rdb /tmp/dump.rdb
docker cp $REDIS_CONTAINER:/tmp/dump.rdb "$BACKUP_DIR/redis_$DATE.rdb"

# Application data backup
echo "Backing up application data..."
tar -czf "$BACKUP_DIR/app_data_$DATE.tar.gz" -C /home/brain2gain/brain2gain uploads logs

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed at $(date)"
```

### 2. Schedule Backups

```bash
# Make script executable
chmod +x /home/brain2gain/backup.sh

# Add to crontab
crontab -e
# Add this line for daily backups at 2 AM:
0 2 * * * /home/brain2gain/backup.sh >> /var/log/brain2gain_backup.log 2>&1
```

## 🔒 Security Hardening

### 1. Firewall Configuration

```bash
# Install and configure UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443

# Optional: Allow monitoring access
sudo ufw allow 3001  # Grafana
sudo ufw allow 9090  # Prometheus
sudo ufw allow 9093  # AlertManager

# Enable firewall
sudo ufw enable
```

### 2. Fail2Ban Setup

```bash
# Install Fail2Ban
sudo apt install -y fail2ban

# Configure Fail2Ban
sudo nano /etc/fail2ban/jail.local
```

```ini
# /etc/fail2ban/jail.local
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
```

```bash
# Start and enable Fail2Ban
sudo systemctl start fail2ban
sudo systemctl enable fail2ban
```

### 3. System Security

```bash
# Disable root login via SSH
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
# Set: PasswordAuthentication no (if using SSH keys)

# Restart SSH
sudo systemctl restart ssh

# Install security updates automatically
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

## ✅ Post-Deployment Verification

### 1. Health Checks

```bash
# Check all services
docker compose ps

# Test application endpoints
curl -I https://yourdomain.com
curl -I https://yourdomain.com/api/v1/health

# Check monitoring
curl -I https://yourdomain.com:3001
curl -I https://yourdomain.com:9090/-/healthy
```

### 2. Performance Testing

```bash
# Install Apache Bench for testing
sudo apt install -y apache2-utils

# Test application performance
ab -n 100 -c 10 https://yourdomain.com/
ab -n 100 -c 10 https://yourdomain.com/api/v1/health
```

### 3. Monitoring Verification

1. **Grafana Dashboard**: Access https://yourdomain.com:3001
   - Login with admin credentials
   - Verify dashboards are working
   - Check data sources connection

2. **Prometheus Targets**: Access https://yourdomain.com:9090/targets
   - Verify all targets are UP
   - Check metrics collection

3. **AlertManager**: Access https://yourdomain.com:9093
   - Verify configuration is loaded
   - Test alert routes

## 🔧 Maintenance

### Daily Tasks
- Monitor application logs: `docker compose logs -f`
- Check system resources: `htop`, `df -h`
- Review security logs: `sudo journalctl -f`

### Weekly Tasks
- Update system packages: `sudo apt update && sudo apt upgrade`
- Review backup integrity
- Check SSL certificate status: `certbot certificates`

### Monthly Tasks
- Review and rotate logs
- Update Docker images: `docker compose pull && docker compose up -d`
- Security audit and vulnerability scan

## 🚨 Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check service logs
docker compose logs service_name

# Check system resources
docker stats
df -h
free -h
```

#### 2. Database Connection Issues
```bash
# Check PostgreSQL logs
docker compose logs postgres

# Test connection
docker compose exec backend python -c "from app.db.database import engine; print(engine.execute('SELECT 1').scalar())"
```

#### 3. SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificates
sudo certbot renew --dry-run
```

#### 4. High Resource Usage
```bash
# Check container resource usage
docker stats

# Check system resources
htop
iotop
```

### Emergency Procedures

#### 1. Service Recovery
```bash
# Stop all services
docker compose down

# Check for corrupted containers
docker system prune -f

# Restart services
docker compose up -d
```

#### 2. Database Recovery
```bash
# Restore from backup
gunzip < /opt/backups/brain2gain/postgres_YYYYMMDD_HHMMSS.sql.gz | docker exec -i postgres psql -U brain2gain_prod brain2gain_prod
```

#### 3. Rollback Deployment
```bash
# Pull previous version
git checkout previous_stable_tag

# Rebuild and deploy
docker compose build
docker compose up -d
```

## 📞 Support and Monitoring

### Log Locations
- Application: `docker compose logs`
- Nginx: `/var/log/nginx/`
- System: `/var/log/syslog`
- Backup: `/var/log/brain2gain_backup.log`

### Key Metrics to Monitor
- CPU usage: < 80%
- Memory usage: < 85%
- Disk usage: < 80%
- Response time: < 2 seconds
- Error rate: < 1%

### Alerting Contacts
- **Critical Issues**: Operations team
- **Application Issues**: Development team
- **Infrastructure Issues**: DevOps team

---

## 🎉 Deployment Complete!

Your Brain2Gain e-commerce platform is now deployed and running in production. The platform includes:

- ✅ **High-availability application stack**
- ✅ **Comprehensive monitoring and alerting**
- ✅ **Automated backups and recovery**
- ✅ **SSL encryption and security hardening**
- ✅ **Load balancing and performance optimization**

For ongoing support and updates, refer to the main project documentation and monitoring dashboards.

**🚀 Welcome to production with Brain2Gain!**