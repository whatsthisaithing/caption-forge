#!/bin/bash

echo ""
echo "========================================"
echo "  CaptionFoundry - Installation"
echo "========================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 is not installed"
    echo "Please install Python 3.10+ from https://python.org"
    exit 1
fi

PYVER=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "[OK] Python $PYVER detected"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js is not installed"
    echo "Please install Node.js 18+ from https://nodejs.org"
    exit 1
fi

NODEVER=$(node --version 2>&1)
echo "[OK] Node.js $NODEVER detected"

# Check if venv exists
if [ -d "venv" ]; then
    echo "[INFO] Virtual environment already exists"
    read -p "Do you want to recreate it? (y/N): " RECREATE
    if [ "$RECREATE" = "y" ] || [ "$RECREATE" = "Y" ]; then
        echo "[INFO] Removing existing venv..."
        rm -rf venv
    fi
fi

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo ""
    echo "[INFO] Creating Python virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment"
        exit 1
    fi
    echo "[OK] Virtual environment created"
fi

# Activate venv and install dependencies
echo ""
echo "[INFO] Installing Python dependencies..."
source venv/bin/activate

pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install Python dependencies"
    exit 1
fi
echo "[OK] Python dependencies installed"

# Install Node.js dependencies (Electron)
echo ""
echo "[INFO] Installing Node.js dependencies (Electron)..."
npm install
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install Node.js dependencies"
    exit 1
fi
echo "[OK] Node.js dependencies installed"

# Create config from template if not exists
if [ ! -f "config/settings.yaml" ]; then
    echo ""
    echo "[INFO] Creating default configuration..."
    cp "config/settings.yaml.template" "config/settings.yaml"
    echo "[OK] Configuration file created at config/settings.yaml"
fi

# Create data directories
echo ""
echo "[INFO] Creating data directories..."
mkdir -p data/thumbnails
mkdir -p data/exports
mkdir -p data/logs
echo "[OK] Data directories created"

echo ""
echo "========================================"
echo "  Installation Complete!"
echo "========================================"
echo ""
echo "To start CaptionFoundry, run: ./start.sh"
echo ""
echo "Configuration: config/settings.yaml"
echo "Database: data/captionforge.db (created on first run)"
echo ""
