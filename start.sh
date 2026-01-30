#!/bin/bash

echo ""
echo "========================================"
echo "  CaptionFoundry - Starting Desktop App"
echo "========================================"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "[ERROR] Virtual environment not found"
    echo "Please run ./install.sh first"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "[ERROR] Node.js dependencies not installed"
    echo "Please run ./install.sh first"
    exit 1
fi

# Check if config exists
if [ ! -f "config/settings.yaml" ]; then
    echo "[WARNING] Configuration file not found"
    echo "Copying template..."
    cp "config/settings.yaml.template" "config/settings.yaml"
fi

echo "[INFO] Starting CaptionFoundry..."
echo ""

# Start the Electron app (which will spawn the Python backend)
npm start
