#!/bin/bash
# Temporary script to disable rate limiting in all backend files

echo "Disabling rate limiting imports and decorators..."

# Find all files with rate limiting imports and comment them
find /root/brain2gain/backend/app -name "*.py" -exec sed -i 's/from app\.middlewares\.advanced_rate_limiting import/# from app.middlewares.advanced_rate_limiting import # Temporary/g' {} \;

# Comment all apply_endpoint_limits decorators
find /root/brain2gain/backend/app -name "*.py" -exec sed -i 's/@apply_endpoint_limits/# @apply_endpoint_limits # Temporary/g' {} \;

echo "Rate limiting disabled temporarily."