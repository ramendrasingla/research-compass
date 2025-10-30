#!/bin/bash

# Kill any processes running on ports 8000 and 3000

echo "🧹 Cleaning up server processes..."

# Function to kill processes on a port
kill_port() {
    local port=$1
    local name=$2

    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "   Found processes on port $port ($name):"
        lsof -Pi :$port -sTCP:LISTEN | tail -n +2 | awk '{print "     - PID " $2 ": " $1}'

        # Get all PIDs
        local pids=$(lsof -t -i:$port)

        # Try graceful shutdown first (SIGTERM)
        echo "   Sending SIGTERM..."
        echo "$pids" | xargs kill 2>/dev/null || true
        sleep 1

        # Check if still running and force kill if needed (SIGKILL)
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo "   Processes still running, sending SIGKILL..."
            echo "$pids" | xargs kill -9 2>/dev/null || true
            sleep 1
        fi

        # Final check
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo "   ⚠️  Warning: Some processes still running on port $port"
            lsof -Pi :$port -sTCP:LISTEN
        else
            echo "   ✓ Port $port cleared"
        fi
    else
        echo "   ✓ No process running on port $port"
    fi
}

# Kill backend (port 8000)
kill_port 8000 "backend"

# Kill frontend (port 3000)
kill_port 3000 "frontend"

echo ""
echo "✓ Cleanup complete!"
echo ""

# Show final status
echo "Port status:"
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "  ❌ Port 8000: STILL IN USE"
else
    echo "  ✓ Port 8000: free"
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "  ❌ Port 3000: STILL IN USE"
else
    echo "  ✓ Port 3000: free"
fi
