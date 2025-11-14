#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cleanup() {
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}
trap cleanup INT TERM

# Start backend
cd "$PROJECT_DIR"
./scripts/start_webbuilder.sh &
BACKEND_PID=$!
echo "⏳ Waiting for backend to initialize..."
sleep 3

# Wait for backend health check
echo "🔍 Checking backend health..."
for i in {1..10}; do
    if curl -s http://localhost:8002/api/health >/dev/null 2>&1; then
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
echo "   Backend:  http://localhost:8002"
echo "   Frontend: http://localhost:5174"
echo "   API Docs: http://localhost:8002/docs"
echo ""
echo "Press Ctrl+C to stop all services"

wait
