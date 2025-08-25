#!/bin/bash

# Update docker-compose.yaml with Docker image SHA256 digests
# Usage: ./update_compose_digests.sh [--fetch-digests|--use-env]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICES_DIR="$SCRIPT_DIR/../services"
COMPOSE_FILE="$SERVICES_DIR/docker-compose.yaml"

NAMESPACE="zyg5467"
REGISTRY="docker.io"

SERVICES=(
    "account"
    "terminal" 
    "master-data"
    "cart"
    "report"
    "journal"
    "stock"
)

echo "=== Docker Compose Digest Updater ==="

# Check if docker-compose.yaml exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "Error: docker-compose.yaml not found at $COMPOSE_FILE"
    exit 1
fi

# Function to get digest from DockerHub
get_digest_from_registry() {
    local service="$1"
    local image_name="$NAMESPACE/pos-$service"
    
    echo "Fetching digest for $image_name:latest..."
    
    # Use docker manifest inspect to get the digest
    local digest
    if command -v docker &> /dev/null; then
        digest=$(docker manifest inspect "$REGISTRY/$image_name:latest" 2>/dev/null | jq -r '.digest' || echo "")
    fi
    
    if [ -z "$digest" ] || [ "$digest" = "null" ]; then
        echo "Warning: Could not fetch digest for $image_name"
        return 1
    fi
    
    echo "$digest"
}

# Function to update compose file with digest
update_compose_with_digest() {
    local service="$1"
    local digest="$2"
    
    if [ -z "$digest" ]; then
        echo "Warning: Empty digest for service $service, skipping..."
        return 1
    fi
    
    echo "Updating $service with digest: $digest"
    
    # Use sed to replace the image line (Linux/macOS compatible)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i .bak "s|image: $NAMESPACE/pos-$service:latest|image: $NAMESPACE/pos-$service@$digest|g" "$COMPOSE_FILE"
        sed -i .bak "s|image: $NAMESPACE/pos-$service@sha256:[a-f0-9]*|image: $NAMESPACE/pos-$service@$digest|g" "$COMPOSE_FILE"
    else
        # Linux
        sed -i.bak "s|image: $NAMESPACE/pos-$service:latest|image: $NAMESPACE/pos-$service@$digest|g" "$COMPOSE_FILE"
        sed -i.bak "s|image: $NAMESPACE/pos-$service@sha256:[a-f0-9]*|image: $NAMESPACE/pos-$service@$digest|g" "$COMPOSE_FILE"
    fi
}

# Function to revert to latest tags
revert_to_latest() {
    echo "Reverting all images to :latest tags..."
    for service in "${SERVICES[@]}"; do
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i .bak "s|image: $NAMESPACE/pos-$service@sha256:[a-f0-9]*|image: $NAMESPACE/pos-$service:latest|g" "$COMPOSE_FILE"
        else
            # Linux
            sed -i.bak "s|image: $NAMESPACE/pos-$service@sha256:[a-f0-9]*|image: $NAMESPACE/pos-$service:latest|g" "$COMPOSE_FILE"
        fi
    done
    echo "Reverted to :latest tags"
}

# Parse command line arguments
FETCH_DIGESTS=false
USE_ENV=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --fetch-digests)
            FETCH_DIGESTS=true
            shift
            ;;
        --use-env)
            USE_ENV=true
            shift
            ;;
        --revert-to-latest)
            revert_to_latest
            exit 0
            ;;
        --help|-h)
            echo "Usage: $0 [--fetch-digests|--use-env|--revert-to-latest]"
            echo ""
            echo "Options:"
            echo "  --fetch-digests    Fetch latest digests from DockerHub"
            echo "  --use-env          Use digests from environment variables"
            echo "  --revert-to-latest Revert all images to :latest tags"
            echo ""
            echo "Environment variables (used with --use-env):"
            echo "  ACCOUNT_DIGEST, TERMINAL_DIGEST, MASTER_DATA_DIGEST,"
            echo "  CART_DIGEST, REPORT_DIGEST, JOURNAL_DIGEST, STOCK_DIGEST"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Create backup
cp "$COMPOSE_FILE" "$COMPOSE_FILE.backup.$(date +%Y%m%d_%H%M%S)"

if [ "$USE_ENV" = true ]; then
    echo "Using digests from environment variables..."
    
    # Use environment variables for digests
    declare -A ENV_DIGESTS=(
        ["account"]="$ACCOUNT_DIGEST"
        ["terminal"]="$TERMINAL_DIGEST"
        ["master-data"]="$MASTER_DATA_DIGEST"
        ["cart"]="$CART_DIGEST"
        ["report"]="$REPORT_DIGEST"
        ["journal"]="$JOURNAL_DIGEST"
        ["stock"]="$STOCK_DIGEST"
    )
    
    for service in "${SERVICES[@]}"; do
        local digest="${ENV_DIGESTS[$service]}"
        if [ -n "$digest" ]; then
            update_compose_with_digest "$service" "$digest"
        else
            echo "Warning: No digest found in environment for service: $service"
        fi
    done
    
elif [ "$FETCH_DIGESTS" = true ]; then
    echo "Fetching digests from DockerHub..."
    
    # Fetch digests from registry
    for service in "${SERVICES[@]}"; do
        digest=$(get_digest_from_registry "$service")
        if [ $? -eq 0 ] && [ -n "$digest" ]; then
            update_compose_with_digest "$service" "$digest"
        fi
    done
    
else
    echo "Error: Please specify either --fetch-digests or --use-env"
    echo "Use --help for usage information"
    exit 1
fi

# Remove backup file if everything worked
rm -f "$COMPOSE_FILE.bak"

echo ""
echo "✅ docker-compose.yaml updated successfully!"
echo "Backup created: $COMPOSE_FILE.backup.*"
echo ""
echo "To verify changes, run:"
echo "  grep 'image:.*@sha256:' $COMPOSE_FILE"