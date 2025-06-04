# ============================================================================
# Multi-stage Dockerfile for Brain2Gain Frontend
# Optimized for production with security and performance
# ============================================================================

# =============
# Builder Stage
# =============
FROM node:20-alpine AS builder

# Metadata
LABEL stage=builder

# Install dependencies for building
RUN apk add --no-cache \
    git \
    python3 \
    make \
    g++

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S frontend -u 1001

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with clean cache
RUN npm ci --only=production --silent && \
    npm cache clean --force

# Copy source code
COPY . .

# Build arguments
ARG VITE_API_URL
ARG NODE_ENV=production
ENV VITE_API_URL=${VITE_API_URL}
ENV NODE_ENV=${NODE_ENV}

# Change ownership and switch to non-root user
RUN chown -R frontend:nodejs /app
USER frontend

# Build application
RUN npm run build

# =============
# Runtime Stage
# =============
FROM nginx:1.25-alpine AS runtime

# Metadata
LABEL maintainer="Brain2Gain Team" \
      version="1.0.0" \
      description="Brain2Gain Frontend"

# Install security updates
RUN apk upgrade --no-cache

# Create non-root user for nginx
RUN addgroup -g 1001 -S nginx-app && \
    adduser -S frontend -u 1001 -G nginx-app

# Copy built application
COPY --from=builder --chown=frontend:nginx-app /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY --chown=frontend:nginx-app ./nginx.conf /etc/nginx/conf.d/default.conf
COPY --chown=frontend:nginx-app ./nginx-backend-not-found.conf /etc/nginx/extra-conf.d/backend-not-found.conf

# Create necessary directories
RUN mkdir -p /var/cache/nginx /var/log/nginx /etc/nginx/extra-conf.d && \
    chown -R frontend:nginx-app /var/cache/nginx /var/log/nginx /etc/nginx/extra-conf.d && \
    chmod -R 755 /var/cache/nginx /var/log/nginx

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Expose port
EXPOSE 80

# Switch to non-root user
USER frontend

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
