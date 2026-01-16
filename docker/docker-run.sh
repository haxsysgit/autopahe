#!/bin/bash

# AutoPahe Docker Run Script
# This script helps build and run the AutoPahe Docker container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}AutoPahe Docker Script${NC}"
echo "========================"

# Create data directories if they don't exist
mkdir -p data json_data collection

# Create Downloads directory if it doesn't exist
mkdir -p ~/Downloads/autopahe

# Function to sanitize and join arguments
sanitize_args() {
    local args=""
    for arg in "$@"; do
        # Don't add extra quotes, just pass as-is with proper escaping
        if [[ "$arg" =~ [[:space:]] ]]; then
            args="$args \"$arg\""
        else
            args="$args $arg"
        fi
    done
    echo "$args" | sed 's/^ *//'
}

# Function to build the Docker image
build_image() {
    echo -e "${YELLOW}Building Docker image...${NC}"
    docker build -t autopahe:latest .
    echo -e "${GREEN}✅ Image built successfully!${NC}"
}

# Function to run the container
run_container() {
    shift 1  # Skip the 'run' argument
    
    # Build the command string properly
    local cmd=""
    for arg in "$@"; do
        if [[ -z "$cmd" ]]; then
            cmd="$arg"
        else
            cmd="$cmd $arg"
        fi
    done
    
    if [ -z "$cmd" ]; then
        cmd="--help"
    fi
    
    echo -e "${YELLOW}Running AutoPahe with command: $cmd${NC}"
    
    # Pass arguments as an array to preserve quotes
    docker run -it --rm \
        -v "$(pwd)/data:/app/data" \
        -v "$(pwd)/json_data:/app/json_data" \
        -v "$(pwd)/collection:/app/collection" \
        -v "$HOME/Downloads/autopahe:/app/downloads" \
        -e AUTOPAHE_DOWNLOAD_DIR=/app/downloads \
        autopahe:latest \
        "$@"
}

# Function to run with docker-compose
run_compose() {
    shift 1  # Skip the 'compose' argument
    
    # Build the command string properly
    local cmd=""
    for arg in "$@"; do
        if [[ -z "$cmd" ]]; then
            cmd="$arg"
        else
            cmd="$cmd $arg"
        fi
    done
    
    if [ -z "$cmd" ]; then
        cmd="--help"
    fi
    
    echo -e "${YELLOW}Running with docker-compose...${NC}"
    
    # Pass arguments as an array to preserve quotes
    docker-compose run --rm autopahe "$@"
}

# Function to open shell
open_shell() {
    echo -e "${YELLOW}Opening shell in container...${NC}"
    docker run -it --rm \
        -v "$(pwd)/data:/app/data" \
        -v "$(pwd)/json_data:/app/json_data" \
        -v "$(pwd)/collection:/app/collection" \
        -v "$HOME/Downloads/autopahe:/app/downloads" \
        -e AUTOPAHE_DOWNLOAD_DIR=/app/downloads \
        --entrypoint /bin/bash \
        autopahe:latest
}

# Function to clean up
clean_up() {
    echo -e "${YELLOW}Cleaning up Docker resources...${NC}"
    docker container prune -f
    docker image prune -f
    echo -e "${GREEN}✅ Cleanup completed!${NC}"
}

# Main script logic
case "$1" in
    "build")
        build_image
        ;;
    "run")
        build_image
        run_container "$@"
        ;;
    "compose")
        run_compose "$@"
        ;;
    "shell")
        open_shell
        ;;
    "clean")
        clean_up
        ;;
    *)
        echo "Usage: $0 {build|run|compose|shell|clean} [command]"
        echo ""
        echo "Commands:"
        echo "  build          - Build the Docker image"
        echo "  run [cmd]      - Build and run with docker run"
        echo "  compose [cmd]  - Run with docker-compose"
        echo "  shell          - Open a bash shell in the container"
        echo "  clean          - Clean up Docker resources"
        echo ""
        echo "Examples:"
        echo "  $0 run --help"
        echo "  $0 run search one piece"
        echo "  $0 run -s one piece -i 0 -d 1"
        echo "  $0 compose download -u <anime-url>"
        echo ""
        echo "Note: No need to escape quotes, just pass arguments normally!"
        exit 1
        ;;
esac
