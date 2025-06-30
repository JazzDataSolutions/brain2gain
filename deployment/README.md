# Brain2Gain Production Deployment Guide

## Overview

This guide covers the production deployment of Brain2Gain using Docker Swarm for container orchestration.

## Architecture

```
                     ┌─────────────────┐
                     │   Load Balancer │
                     │    (HAProxy)    │
                     └─────────┬───────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼───────┐   ┌────▼────┐   ┌──────▼──────┐
    │   Frontend      │   │   API   │   │ WebSocket   │
    │   (Nginx)       │   │ Backend │   │  Backend    │
    │   React App     │   │FastAPI  │   │  FastAPI    │
    └─────────────────┘   └─────────┘   └─────────────┘
                               │
                    ┌──────────┼──────────┐
                    │          │          │
            ┌───────▼──┐   ┌───▼────┐  ┌─▼─────────┐
            │PostgreSQL│   │ Redis  │  │  Backup   │
            │    DB    │   │ Cache  │  │ Service   │
            └──────────┘   └────────┘  └───────────┘
```

## Prerequisites

- Docker Engine 20.10+
- Docker Swarm initialized
- Domain name configured (brain2gain.com)
- SSL certificates
- Minimum 4GB RAM, 2 CPU cores

## Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd brain2gain
   ```

2. **Configure secrets**:
   ```bash
   # Create production secrets
   ./scripts/setup-secrets.sh
   ```

3. **Deploy to production**:
   ```bash
   ./deploy-swarm.sh deploy
   ```

4. **Check deployment status**:
   ```bash
   ./deploy-swarm.sh status
   ```

## Deployment Files

### Core Configuration Files

- `docker-swarm.yml` - Docker Swarm stack configuration
- `docker-compose.prod.yml` - Production Docker Compose file
- `deploy-swarm.sh` - Deployment script

### Service Configurations

- `backend/Dockerfile.prod` - Production backend image
- `frontend/Dockerfile.prod` - Production frontend image
- `haproxy/haproxy.swarm.cfg` - Load balancer configuration
- `nginx/nginx.prod.conf` - Frontend server configuration

### Scripts

- `backend/scripts/start-prod.sh` - Backend startup script
- `scripts/backup.sh` - Database backup script

## Services

### Load Balancer (HAProxy)
- **Replicas**: 2
- **Ports**: 80, 443, 8404 (stats)
- **Features**: SSL termination, rate limiting, health checks

### Frontend (Nginx + React)
- **Replicas**: 2
- **Port**: 80
- **Features**: Static file serving, API proxy, gzip compression

### Backend (FastAPI)
- **Replicas**: 3
- **Port**: 8000
- **Features**: Auto-scaling, health checks, graceful shutdown

### Database (PostgreSQL 17)
- **Replicas**: 1
- **Port**: 5432
- **Features**: Persistent storage, automated backups

### Cache (Redis 7.2)
- **Replicas**: 1
- **Port**: 6379
- **Features**: Persistent storage, memory optimization

### Backup Service
- **Replicas**: 1
- **Schedule**: Every 6 hours
- **Features**: Automated DB backups, retention policy

## Configuration

### Environment Variables

```bash
# Backend
ENVIRONMENT=production
POSTGRES_SERVER=postgres
REDIS_HOST=redis
FRONTEND_HOST=https://brain2gain.com

# Frontend
NODE_ENV=production
VITE_API_URL=https://api.brain2gain.com
```

### Resource Limits

| Service | CPU Limit | Memory Limit | CPU Request | Memory Request |
|---------|-----------|--------------|-------------|----------------|
| Backend | 1.0       | 1GB          | 0.5         | 512MB          |
| Frontend| 0.5       | 512MB        | 0.25        | 256MB          |
| PostgreSQL| 1.0     | 2GB          | 0.5         | 1GB            |
| Redis   | 0.5       | 512MB        | 0.25        | 256MB          |
| HAProxy | 0.5       | 256MB        | 0.1         | 128MB          |

## Monitoring

### Health Checks

All services include comprehensive health checks:

- **Database**: `pg_isready` command
- **Redis**: `redis-cli ping` command  
- **Backend**: HTTP health check endpoint
- **Frontend**: Nginx status check
- **Load Balancer**: HAProxy stats endpoint

### Logging

Centralized logging to `/opt/brain2gain/logs/`:

- Backend API logs
- Frontend access logs
- Database logs
- Load balancer logs

### Metrics

HAProxy statistics available at: `http://<server>:8404/stats`

## Backup & Recovery

### Automated Backups

- **Frequency**: Every 6 hours
- **Retention**: 7 days
- **Location**: `/opt/brain2gain/backups/`
- **Format**: PostgreSQL custom format + compressed SQL

### Manual Backup

```bash
# Create immediate backup
docker exec brain2gain_backup /usr/local/bin/backup.sh
```

### Recovery

```bash
# Restore from backup
docker exec -i brain2gain_postgres pg_restore -U brain2gain_prod -d brain2gain_prod < backup.sql
```

## Scaling

### Horizontal Scaling

```bash
# Scale backend API
./deploy-swarm.sh scale backend 5

# Scale frontend
./deploy-swarm.sh scale frontend 3
```

### Vertical Scaling

Update resource limits in `docker-swarm.yml` and redeploy.

## Security

### Network Security

- **Overlay networks**: Isolated service communication
- **Firewall**: Only necessary ports exposed
- **Rate limiting**: HAProxy and Nginx rate limiting

### Application Security

- **Secrets management**: Docker Swarm secrets
- **HTTPS**: SSL/TLS encryption
- **Security headers**: HSTS, CSP, XSS protection
- **Non-root containers**: All services run as non-root

### Database Security

- **Encrypted connections**: SSL required
- **Strong passwords**: Secrets-based authentication
- **Network isolation**: Backend network only

## Troubleshooting

### Common Issues

1. **Service not starting**:
   ```bash
   docker service logs brain2gain_backend
   ```

2. **Database connection issues**:
   ```bash
   docker exec brain2gain_postgres pg_isready -U brain2gain_prod
   ```

3. **Memory issues**:
   ```bash
   docker stats
   ```

### Debug Commands

```bash
# View all services
docker stack services brain2gain

# Check service logs
./deploy-swarm.sh logs <service_name>

# Inspect service configuration
docker service inspect brain2gain_backend

# Access service shell
docker exec -it <container_id> /bin/bash
```

## Maintenance

### Updates

1. **Rolling updates**:
   ```bash
   # Update backend
   docker service update --image brain2gain/backend:v2.0 brain2gain_backend
   ```

2. **Blue-green deployment**:
   ```bash
   # Deploy new version
   ./deploy-swarm.sh deploy
   
   # Rollback if needed
   ./deploy-swarm.sh rollback
   ```

### Routine Maintenance

- **Weekly**: Review logs and metrics
- **Monthly**: Update base images
- **Quarterly**: Security audit and updates

## Performance Tuning

### Database Optimization

- **Connection pooling**: Configured in backend
- **Query optimization**: Index analysis
- **Memory settings**: PostgreSQL memory configuration

### Cache Optimization

- **Redis memory policy**: LRU eviction
- **Cache hit rate**: Monitor cache effectiveness
- **TTL settings**: Optimize cache expiration

### Load Balancer Tuning

- **Connection limits**: Adjust based on load
- **Health check intervals**: Balance responsiveness and load
- **Timeout settings**: Optimize for application behavior

## Compliance & Auditing

### Logging Compliance

- **Access logs**: All HTTP requests logged
- **Audit trails**: Database and application events
- **Log retention**: 90 days minimum

### Security Compliance

- **Regular updates**: Security patches applied
- **Vulnerability scanning**: Automated security scans
- **Access control**: Role-based permissions

## Support

For deployment issues or questions:

1. **Check logs**: Use debugging commands above
2. **Review configuration**: Verify environment variables and secrets
3. **Monitor resources**: Check CPU, memory, and disk usage
4. **Contact support**: Include relevant logs and error messages