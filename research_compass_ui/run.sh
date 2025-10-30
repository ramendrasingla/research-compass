#!/bin/bash

# Research Compass UI - Development Runner
# This script sets up a virtual environment, installs dependencies,
# and starts both the backend and frontend in development mode

set -e

echo "🧭 Research Compass UI"
echo "======================"
echo ""

# Get absolute path to project root (before any cd commands)
PROJECT_ROOT=$(pwd)

# Virtual environment setup
VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "🔨 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip in virtual environment
echo "📦 Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Creating .env from .env.example..."
    cp .env.example .env
    echo "   Please edit .env and add your API keys"
    deactivate
    exit 1
fi

# Check if frontend dependencies are installed
if [ ! -d frontend/node_modules ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Check if research_compass_core is installed
if ! python -c "import research_compass_core" 2>/dev/null; then
    echo "📦 Installing research_compass_core..."
    if [ -d ../research_compass_core ]; then
        cd ../research_compass_core
        pip install -e .
        cd ../research_compass_ui
        echo "✓ research_compass_core installed successfully"
    else
        echo "❌ Error: research_compass_core not found at ../research_compass_core"
        echo "   Please ensure the directory exists or install it manually"
        deactivate
        exit 1
    fi
fi

# Install backend dependencies
echo "📦 Checking backend dependencies..."
if ! python -c "import fastapi" 2>/dev/null; then
    echo "   Installing backend dependencies..."
    pip install fastapi "uvicorn[standard]" python-multipart python-dotenv pydantic pydantic-settings aiofiles
    echo "✓ Backend dependencies installed successfully"
else
    echo "✓ Backend dependencies already installed"
fi

# Verify all critical dependencies
echo "🔍 Verifying all dependencies..."
MISSING_DEPS=0

if ! python -c "import fastapi" 2>/dev/null; then
    echo "❌ fastapi not found"
    MISSING_DEPS=1
fi

if ! python -c "import uvicorn" 2>/dev/null; then
    echo "❌ uvicorn not found"
    MISSING_DEPS=1
fi

if ! python -c "import research_compass_core" 2>/dev/null; then
    echo "❌ research_compass_core not found"
    MISSING_DEPS=1
fi

if [ $MISSING_DEPS -eq 1 ]; then
    echo ""
    echo "❌ Some dependencies are missing. Trying to fix..."
    echo "   Installing missing dependencies..."
    pip install fastapi "uvicorn[standard]" python-multipart python-dotenv pydantic pydantic-settings aiofiles

    # Verify again
    if ! python -c "import fastapi" 2>/dev/null; then
        echo "❌ Installation failed. Please install manually:"
        echo "   source .venv/bin/activate"
        echo "   pip install fastapi uvicorn[standard] python-multipart python-dotenv pydantic pydantic-settings aiofiles"
        echo "   cd ../research_compass_core && pip install -e ."
        deactivate
        exit 1
    fi
fi

echo "✓ All dependencies verified"
echo ""

# Check if ports are already in use and kill them
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8000 is already in use!"
    echo "   Killing existing processes..."
    kill $(lsof -t -i:8000) 2>/dev/null || true
    sleep 1
    # Force kill if still running
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "   Force killing..."
        kill -9 $(lsof -t -i:8000) 2>/dev/null || true
        sleep 1
    fi
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 3000 is already in use!"
    echo "   Killing existing processes..."
    kill $(lsof -t -i:3000) 2>/dev/null || true
    sleep 1
    # Force kill if still running
    if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "   Force killing..."
        kill -9 $(lsof -t -i:3000) 2>/dev/null || true
        sleep 1
    fi
fi

echo "🚀 Starting development servers..."
echo ""
echo "Backend will run on: http://localhost:8000"
echo "Frontend will run on: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Function to kill all background processes on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $(jobs -p) 2>/dev/null
    echo "🔌 Deactivating virtual environment..."
    deactivate 2>/dev/null || true
    exit
}

trap cleanup EXIT INT TERM

# Start backend in background
echo "🔧 Starting backend..."
cd "$PROJECT_ROOT/backend"
python -m app.main &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 2

# Start frontend in background
echo "🎨 Starting frontend..."
cd "$PROJECT_ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

# Wait for both processes
wait
