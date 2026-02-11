#!/bin/bash
# ==============================================
# Swine Monitor - macOS Build Script
# ==============================================
# Usage: ./scripts/build_mac.sh (from project root)
#    or: cd scripts && ./build_mac.sh
# ==============================================

set -e  # Exit on error

# Determine project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "========================================"
echo "  Swine Monitor - macOS Build Script"
echo "========================================"
echo "Project root: $PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if build.spec exists
if [ ! -f "scripts/build.spec" ]; then
    echo -e "${RED}Error: scripts/build.spec not found.${NC}"
    exit 1
fi

# Check Python version
echo -e "\n${YELLOW}[1/6] Checking Python...${NC}"
python3 --version

# Activate virtual environment if exists
if [ -d ".venv" ]; then
    echo -e "${GREEN}Activating virtual environment...${NC}"
    source .venv/bin/activate
else
    echo -e "${YELLOW}No .venv found. Using system Python.${NC}"
fi

# Install/upgrade PyInstaller
echo -e "\n${YELLOW}[2/6] Installing PyInstaller...${NC}"
pip install --upgrade pyinstaller

# Clean previous builds
echo -e "\n${YELLOW}[3/6] Cleaning previous builds...${NC}"
rm -rf dist/SwineMonitor
rm -rf build/

# Create required directories if they don't exist
echo -e "\n${YELLOW}[4/6] Preparing directories...${NC}"
mkdir -p models
mkdir -p data/images

# Run PyInstaller with --noconfirm to skip prompts
echo -e "\n${YELLOW}[5/6] Building application...${NC}"
echo "This may take several minutes..."
pyinstaller scripts/build.spec --clean --noconfirm

# Check if build was successful
if [ -d "dist/SwineMonitor" ]; then
    echo -e "\n${GREEN}========================================"
    echo "  Build completed successfully!"
    echo "========================================${NC}"
    
    # Copy required files to dist folder
    echo -e "\n${YELLOW}[6/6] Copying configuration files...${NC}"
    
    # Copy config template
    if [ -f "config.yaml.template" ]; then
        cp config.yaml.template dist/SwineMonitor/config.yaml
        echo "  - config.yaml copied"
    fi
    
    # Copy .env template
    if [ -f ".env.template" ]; then
        cp .env.template dist/SwineMonitor/.env
        echo "  - .env copied"
    fi
    
    # Create data directories in dist
    mkdir -p dist/SwineMonitor/data/images
    echo "  - data/images/ directory created"
    
    # Create models directory in dist
    mkdir -p dist/SwineMonitor/models
    echo "  - models/ directory created"
    
    # Create logs directory in dist
    mkdir -p dist/SwineMonitor/logs
    echo "  - logs/ directory created"
    
    # Copy model file if exists
    if [ -f "models/yolo11s.pt" ]; then
        cp models/yolo11s.pt dist/SwineMonitor/models/
        echo "  - YOLO model copied"
    else
        echo -e "${YELLOW}  - Warning: No YOLO model found in models/${NC}"
    fi

    if [ -f "models/yolo_best.pt" ]; then
        cp models/yolo_best.pt dist/SwineMonitor/models/
        echo "  - YOLO model copied"
    else
        echo -e "${YELLOW}  - Warning: No YOLO model found in models/${NC}"
    fi
    
    echo -e "\n${GREEN}Build output: dist/SwineMonitor/${NC}"
    echo -e "To run the application: ${GREEN}./dist/SwineMonitor/SwineMonitor${NC}"
    
    # Show directory size
    echo -e "\n${YELLOW}Build size:${NC}"
    du -sh dist/SwineMonitor
else
    echo -e "\n${RED}========================================"
    echo "  Build failed!"
    echo "========================================${NC}"
    echo "Check the error messages above."
    exit 1
fi
