#!/usr/bin/env bash

# ============================================================================
# Consolidated Build Script for Brain2Gain
# Handles building for different environments and modes
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
MODE=${MODE:-"full"}
ENVIRONMENT=${ENVIRONMENT:-"production"}
TAG=${TAG:-"latest"}
PUSH=${PUSH:-"false"}
PLATFORM=${PLATFORM:-"linux/amd64"}

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Help function
show_help() {
    cat << EOF
Brain2Gain Consolidated Build Script

Usage: $0 [OPTIONS]

OPTIONS:
    -h, --help              Show this help message
    -m, --mode              Build mode (store|admin|full) [default: full]
    -e, --environment       Environment (development|production) [default: production]
    -t, --tag               Docker image tag [default: latest]
    -p, --push              Push images after build [default: false]
    --platform              Target platform [default: linux/amd64]

EXAMPLES:
    $0                              # Build full application
    $0 -m store -t v1.0.0          # Build store mode with version tag
    $0 -m admin -p                 # Build admin mode and push
    $0 -e development              # Build for development
    $0 --platform linux/arm64      # Build for ARM64

BUILD MODES:
    store       Build only store/e-commerce components
    admin       Build only admin/ERP components  
    full        Build complete application (default)
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -m|--mode)
            MODE="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -p|--push)
            PUSH="true"
            shift
            ;;
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate mode
case $MODE in
    "store"|"admin"|"full")
        ;;
    *)
        print_error "Invalid mode: $MODE"
        echo "Valid modes: store, admin, full"
        exit 1
        ;;
esac

print_info "Starting Brain2Gain build..."
print_info "Mode: $MODE"
print_info "Environment: $ENVIRONMENT"
print_info "Tag: $TAG"
print_info "Platform: $PLATFORM"

# Set image names based on mode
BACKEND_IMAGE="brain2gain-backend"
FRONTEND_IMAGE="brain2gain-frontend"

if [[ "$MODE" != "full" ]]; then
    BACKEND_IMAGE="brain2gain-${MODE}-backend"
    FRONTEND_IMAGE="brain2gain-${MODE}-frontend"
fi

# Set Docker Compose file based on mode
COMPOSE_FILE="docker-compose.yml"
case $MODE in
    "store")
        COMPOSE_FILE="docker-compose.store.yml"
        ;;
    "admin")
        COMPOSE_FILE="docker-compose.admin.yml"
        ;;
esac

# Function to build images
build_images() {
    print_info "Building images for $MODE mode..."
    
    # Set build arguments based on mode and environment
    BACKEND_BUILD_ARGS=""
    FRONTEND_BUILD_ARGS=""
    
    case $MODE in
        "store")
            BACKEND_BUILD_ARGS="--build-arg APP_MODE=store --build-arg API_MODE=public"
            FRONTEND_BUILD_ARGS="--build-arg VITE_APP_MODE=store --build-arg VITE_API_URL=http://localhost:8000"
            ;;
        "admin")
            BACKEND_BUILD_ARGS="--build-arg APP_MODE=admin --build-arg API_MODE=admin"
            FRONTEND_BUILD_ARGS="--build-arg VITE_APP_MODE=admin --build-arg VITE_API_URL=http://localhost:8001"
            ;;
        "full")
            BACKEND_BUILD_ARGS="--build-arg APP_MODE=production --build-arg API_MODE=full"
            FRONTEND_BUILD_ARGS="--build-arg VITE_APP_MODE=full"
            ;;
    esac
    
    # Build backend
    print_info "Building backend image: $BACKEND_IMAGE:$TAG"
    docker build \
        --platform "$PLATFORM" \
        --tag "$BACKEND_IMAGE:$TAG" \
        $BACKEND_BUILD_ARGS \
        ./backend
    
    # Build frontend
    print_info "Building frontend image: $FRONTEND_IMAGE:$TAG"
    docker build \
        --platform "$PLATFORM" \
        --tag "$FRONTEND_IMAGE:$TAG" \
        $FRONTEND_BUILD_ARGS \
        ./frontend
    
    print_success "Images built successfully"
}

# Function to push images
push_images() {
    if [[ "$PUSH" == "true" ]]; then
        print_info "Pushing images to registry..."
        
        docker push "$BACKEND_IMAGE:$TAG"
        docker push "$FRONTEND_IMAGE:$TAG"
        
        print_success "Images pushed successfully"
    fi
}

# Function to build with Docker Compose
build_with_compose() {
    print_info "Building with Docker Compose: $COMPOSE_FILE"
    
    # Set environment variables for Docker Compose
    export TAG
    export FRONTEND_ENV="$ENVIRONMENT"
    export DOCKER_IMAGE_BACKEND="$BACKEND_IMAGE"
    export DOCKER_IMAGE_FRONTEND="$FRONTEND_IMAGE"
    
    docker-compose -f "$COMPOSE_FILE" build
    
    print_success "Docker Compose build completed"
}

# Main execution
case $MODE in
    "store"|"admin")
        # For separated environments, build individual images
        build_images
        push_images
        ;;
    "full")
        # For full mode, use Docker Compose
        build_with_compose
        push_images
        ;;
esac

print_success "Build completed successfully!"

# Show built images
print_info "Built images:"
docker images | grep -E "(brain2gain|$BACKEND_IMAGE|$FRONTEND_IMAGE)" | head -10