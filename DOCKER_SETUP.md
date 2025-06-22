# 🐳 Docker Setup Guide for Brain2Gain

This guide explains how to use the organized Docker Compose configurations for different environments.

## 📁 Docker Compose Files Structure

```
├── docker-compose.base.yml      # Shared infrastructure services
├── docker-compose.yml           # Production configuration
├── docker-compose.dev.yml       # Team development environment
├── docker-compose.local.yml     # Local development environment
├── docker-compose.testing.yml   # Testing environment with test runners
└── docker-compose.ci.yml        # CI/CD optimized configuration
```

## 🚀 Quick Start Commands

### Local Development (Recommended for individual developers)
```bash
# Start local development environment
docker-compose -f docker-compose.local.yml up -d

# View logs
docker-compose -f docker-compose.local.yml logs -f

# Stop services
docker-compose -f docker-compose.local.yml down
```

### Team Development Environment
```bash
# Start team development environment
docker-compose -f docker-compose.dev.yml up -d

# Include development tools (mailcatcher, adminer)
docker-compose -f docker-compose.dev.yml --profile tools up -d
```

### Testing Environment
```bash
# Start testing infrastructure
docker-compose -f docker-compose.testing.yml up -d

# Run backend tests
docker-compose -f docker-compose.testing.yml --profile testing run pytest-runner

# Run E2E tests
docker-compose -f docker-compose.testing.yml --profile testing run playwright-runner
```

### Production Environment
```bash
# Start production services
docker-compose up -d

# Include reverse proxy
docker-compose --profile nginx up -d

# Include monitoring stack
docker-compose --profile monitoring up -d
```

## 🔧 Environment Configuration

### 1. Copy Environment Files

```bash
# For local development
cp .env.example .env.local

# For production
cp .env.example .env.production
```

### 2. Configure Environment Variables

Edit your environment files with appropriate values:

#### Critical Production Variables
```bash
# Security
SECRET_KEY=your-super-secure-secret-key-here
DOMAIN=your-domain.com

# Database
POSTGRES_PASSWORD=secure-postgres-password
REDIS_PASSWORD=secure-redis-password

# Payment Gateways
STRIPE_SECRET_KEY=sk_live_your_stripe_key
PAYPAL_CLIENT_SECRET=your_paypal_secret

# Email
SMTP_PASSWORD=your-email-password
```

## 📊 Service Profiles

### Core Services (Always Running)
- **postgres**: PostgreSQL database
- **redis**: Redis cache and session store
- **backend**: FastAPI application
- **frontend**: React application

### Optional Profiles

#### `tools` - Development Tools
- **adminer**: Database administration UI (port 8080)
- **mailcatcher**: Email testing tool (port 1080)

#### `nginx` - Production Reverse Proxy
- **nginx**: Reverse proxy with SSL termination

#### `monitoring` - Observability Stack
- **prometheus**: Metrics collection (port 9090)
- **grafana**: Metrics visualization (port 3001)

#### `testing` - Test Runners
- **pytest-runner**: Backend test execution
- **playwright-runner**: E2E test execution

## 🌍 Environment Differences

| Feature | Local | Development | Testing | Production |
|---------|-------|-------------|---------|------------|
| Hot Reload | ✅ | ✅ | ❌ | ❌ |
| Debug Mode | ✅ | ✅ | ❌ | ❌ |
| Email | MailCatcher | MailCatcher | Mock | SMTP |
| Database | Local Volume | Shared Volume | Memory | Persistent |
| SSL | ❌ | ❌ | ❌ | ✅ |
| Monitoring | ❌ | ❌ | ❌ | ✅ |

## 📡 Port Mappings

### Local Development
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Database**: localhost:5432
- **Redis**: localhost:6379
- **MailCatcher**: http://localhost:1080
- **Adminer**: http://localhost:8080

### Production
- **Frontend**: http://localhost:80 or https://localhost:443
- **Backend API**: http://localhost:8000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001

## 🔄 Common Operations

### Database Operations
```bash
# Reset local database
docker-compose -f docker-compose.local.yml down -v
docker-compose -f docker-compose.local.yml up -d postgres

# Run migrations
docker-compose -f docker-compose.local.yml exec backend alembic upgrade head

# Create migration
docker-compose -f docker-compose.local.yml exec backend alembic revision --autogenerate -m "description"
```

### Development Workflow
```bash
# Install dependencies and start development
docker-compose -f docker-compose.local.yml up -d

# View backend logs
docker-compose -f docker-compose.local.yml logs -f backend

# Restart specific service
docker-compose -f docker-compose.local.yml restart backend

# Execute commands in running container
docker-compose -f docker-compose.local.yml exec backend pytest
docker-compose -f docker-compose.local.yml exec frontend npm run test
```

### Production Deployment
```bash
# Build and deploy with specific tag
export TAG=v1.2.3
docker-compose build
docker-compose up -d

# View production logs
docker-compose logs -f --tail=100

# Health check
docker-compose ps
```

## 🐛 Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check what's using a port
sudo lsof -i :5432

# Use different ports
export POSTGRES_PORT=5433
docker-compose -f docker-compose.local.yml up -d
```

#### Permission Issues
```bash
# Fix volume permissions
sudo chown -R $USER:$USER ./volumes
```

#### Database Connection Issues
```bash
# Reset database
docker-compose -f docker-compose.local.yml down -v postgres
docker volume rm brain2gain_postgres_local_data
docker-compose -f docker-compose.local.yml up -d postgres
```

#### Memory Issues
```bash
# Increase Docker memory limit (Docker Desktop)
# Settings > Resources > Memory > 4GB+

# Clean up Docker resources
docker system prune -a --volumes
```

### Logs and Debugging

```bash
# View all logs
docker-compose -f docker-compose.local.yml logs

# Follow specific service logs
docker-compose -f docker-compose.local.yml logs -f backend

# Debug container issues
docker-compose -f docker-compose.local.yml exec backend bash
```

## 🔐 Security Considerations

### Development
- Use `.env.local` for local development
- Never commit real credentials to version control
- Use test API keys for payment gateways

### Production
- Use strong, unique passwords for all services
- Enable SSL/TLS termination
- Configure proper CORS origins
- Use production API keys
- Enable monitoring and alerting
- Regular security updates

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [Redis Docker Image](https://hub.docker.com/_/redis)

## 🤝 Contributing

When adding new services or modifying configurations:

1. Update the appropriate `docker-compose.*.yml` file
2. Document any new environment variables in `.env.example`
3. Update this README with new instructions
4. Test across all environments before committing