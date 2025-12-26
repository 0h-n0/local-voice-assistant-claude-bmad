#!/bin/bash
# ===========================================
# Initial Setup Script
# ===========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Setting up Local Voice Assistant..."
echo "===================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
required_version="3.12"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Warning: Python 3.12+ is recommended. Found: Python $python_version"
fi

# Check Node.js version
echo "Checking Node.js version..."
if command -v node &> /dev/null; then
    node_version=$(node --version | grep -oP '\d+' | head -1)
    if [ "$node_version" -lt 20 ]; then
        echo "Warning: Node.js 20+ is recommended. Found: Node $(node --version)"
    else
        echo "Node.js $(node --version) - OK"
    fi
else
    echo "Error: Node.js is not installed. Please install Node.js 20 LTS."
    exit 1
fi

# Check uv
echo "Checking uv..."
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed."
    echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
else
    echo "uv $(uv --version) - OK"
fi

echo ""
echo "Creating directories..."
mkdir -p data logs

echo ""
echo "Setting up configuration..."
if [ ! -f "config/config.yaml" ]; then
    cp config/config.example.yaml config/config.yaml
    echo "Created config/config.yaml from example"
else
    echo "config/config.yaml already exists"
fi

echo ""
echo "Installing backend dependencies..."
if [ -f "backend/pyproject.toml" ]; then
    cd backend
    uv sync
    cd ..
else
    echo "Skipping backend: pyproject.toml not found (run Story 1.2 first)"
fi

echo ""
echo "Installing frontend dependencies..."
if [ -f "frontend/package.json" ]; then
    cd frontend
    npm install
    cd ..
else
    echo "Skipping frontend: package.json not found (run Story 1.3 first)"
fi

echo ""
echo "Making scripts executable..."
chmod +x scripts/*.sh

echo ""
echo "===================================="
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit config/config.yaml with your settings"
echo "  2. Run 'make dev' to start development servers"
echo "  3. Open http://localhost:3000 in your browser"
echo ""
