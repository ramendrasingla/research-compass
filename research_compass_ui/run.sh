#!/bin/bash

# Research Compass UI - Development Runner
# This script starts both the backend and frontend in development mode

set -e

echo "🧭 Research Compass UI"
echo "======================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Creating .env from .env.example..."
    cp .env.example .env
    echo "   Please edit .env and add your API keys"
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
    echo "⚠️  Warning: research_compass_core not found!"
    echo "   Please install it first:"
    echo "   cd ../research_compass_core && pip install -e ."
    exit 1
fi

# Check if backend dependencies are installed
if ! python -c "import pydantic_settings" 2>/dev/null; then
    echo "📦 Installing backend dependencies..."
    cd backend
    pip install -e .
    cd ..
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
    exit
}

trap cleanup EXIT INT TERM

# Start backend in background
echo "🔧 Starting backend..."
cd backend && python -m app.main &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 2

# Start frontend in background
echo "🎨 Starting frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!

# Wait for both processes
wait
