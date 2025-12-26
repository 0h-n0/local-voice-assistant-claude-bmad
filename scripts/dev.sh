#!/bin/bash
# ===========================================
# Development Environment Startup Script
# ===========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Starting Local Voice Assistant development servers..."
echo "=================================================="

# Check if frontend dependencies are installed
if [ -f "frontend/package.json" ]; then
    if [ ! -d "frontend/node_modules" ]; then
        echo "Installing frontend dependencies..."
        cd frontend && npm install && cd ..
    fi
else
    echo "Warning: frontend/package.json not found (run Story 1.3 first)"
fi

# Check if backend dependencies are installed
if [ -f "backend/pyproject.toml" ]; then
    if [ ! -d "backend/.venv" ]; then
        echo "Installing backend dependencies..."
        cd backend && uv sync && cd ..
    fi
else
    echo "Warning: backend/pyproject.toml not found (run Story 1.2 first)"
fi

# Copy config if not exists
if [ ! -f "config/config.yaml" ]; then
    echo "Creating config.yaml from example..."
    cp config/config.example.yaml config/config.yaml
fi

# Create data and logs directories if not exist
mkdir -p data logs

echo ""
echo "Starting servers..."
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""

# Run both servers using make
make dev
