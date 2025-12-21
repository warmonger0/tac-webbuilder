#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Source port configuration
if [ -f "$PROJECT_DIR/.ports.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.ports.env" | xargs)
else
    echo "❌ Error: .ports.env file not found"
    exit 1
fi

# Source database and other environment configuration (if exists)
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.env" | grep -v '^$' | xargs)
fi

cleanup() {
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}
trap cleanup INT TERM

# Kill any existing processes on our ports
echo "🧹 Cleaning up existing processes..."
pkill -9 -f "python.*server.py" 2>/dev/null || true
pkill -9 -f "bun.*dev" 2>/dev/null || true
pkill -9 -f "node.*vite" 2>/dev/null || true
lsof -ti:${BACKEND_PORT} | xargs kill -9 2>/dev/null || true
lsof -ti:${FRONTEND_PORT} | xargs kill -9 2>/dev/null || true
sleep 1

# Start backend
cd "$PROJECT_DIR"
cd "$PROJECT_DIR/app/server" && uv run python server.py &
BACKEND_PID=$!
echo "⏳ Waiting for backend to initialize..."
sleep 3

# Wait for backend health check
echo "🔍 Checking backend health..."
for i in {1..10}; do
    if curl -s http://localhost:${BACKEND_PORT}/api/v1/health >/dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ Backend failed to start"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# Start frontend
./scripts/start_client.sh &
FRONTEND_PID=$!

echo ""
echo "✅ Full stack is running:"
echo "   Backend:  http://localhost:${BACKEND_PORT}"
echo "   Frontend: http://localhost:${FRONTEND_PORT}"
echo "   API Docs: http://localhost:${BACKEND_PORT}/docs"
echo ""
echo "Press Ctrl+C to stop all services"

wait
