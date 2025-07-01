#!/bin/bash
# Generate secure credentials for Brain2Gain

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log "Generating secure credentials for Brain2Gain..."

mkdir -p secrets

# Generate cryptographically secure passwords
log "Generating PostgreSQL password..."
openssl rand -base64 32 > secrets/postgres_password.txt

log "Generating Redis password..."
openssl rand -base64 32 > secrets/redis_password.txt

log "Generating application secret key..."
openssl rand -base64 64 > secrets/secret_key.txt

log "Generating JWT secret..."
openssl rand -base64 32 > secrets/jwt_secret.txt

log "Generating SMTP password..."
openssl rand -base64 16 > secrets/smtp_password.txt

log "Generating superuser password..."
openssl rand -base64 32 > secrets/superuser_password.txt

log "Generating Grafana admin password..."
openssl rand -base64 32 > secrets/grafana_admin_password.txt

log "Generating Grafana secret key..."
openssl rand -base64 32 > secrets/grafana_secret_key.txt

# Set proper permissions
chmod 600 secrets/*.txt

success "All secrets generated successfully"
echo ""
echo "📋 Generated credentials:"
echo "   - PostgreSQL password: $(head -c 16 secrets/postgres_password.txt)..."
echo "   - Redis password: $(head -c 16 secrets/redis_password.txt)..."
echo "   - Grafana admin password: $(head -c 16 secrets/grafana_admin_password.txt)..."
echo ""
echo "🔒 All credentials are stored securely in secrets/ directory"