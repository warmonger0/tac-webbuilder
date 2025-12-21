#!/bin/bash

# start_full_clean.sh - Reliable full-stack startup script
# Starts all three services: ADW webhook (8001), Backend API (8002), Frontend (5173)
# DOES NOT use --reload flag to avoid PostgreSQL PoolError

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧹 Starting clean full-stack startup...${NC}"

# Step 1: Kill all existing processes
echo -e "${YELLOW}Killing all existing processes...${NC}"
pkill -9 python3 2>/dev/null || true
pkill -9 node 2>/dev/null || true
pkill -9 bun 2>/dev/null || true

# Step 2: Wait for ports to clear
echo -e "${YELLOW}Waiting for ports to clear...${NC}"
sleep 3

# Clear specific ports if still in use
lsof -ti:8001 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti:8002 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti:5173 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 1

echo -e "${GREEN}✓ All processes killed and ports cleared${NC}"

# Get project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

# Source port configuration
if [ -f "$PROJECT_ROOT/.ports.env" ]; then
    source "$PROJECT_ROOT/.ports.env"
fi

# Port configuration with fallbacks
WEBHOOK_PORT=${WEBHOOK_PORT:-8001}
BACKEND_PORT=${BACKEND_PORT:-8002}
FRONTEND_PORT=${FRONTEND_PORT:-5173}

# PostgreSQL configuration
POSTGRES_HOST=${POSTGRES_HOST:-localhost}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_DB=${POSTGRES_DB:-tac_webbuilder}
POSTGRES_USER=${POSTGRES_USER:-tac_user}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-changeme}

# Function to cleanup on exit
cleanup() {
    echo -e "\n${BLUE}🛑 Shutting down services...${NC}"
    kill $WEBHOOK_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null
    wait $WEBHOOK_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✓ Services stopped${NC}"
    exit 0
}
trap cleanup INT TERM

# Step 3: Start ADW webhook service
echo -e "${GREEN}📡 Starting ADW webhook service on port $WEBHOOK_PORT...${NC}"
cd "$PROJECT_ROOT/adws/adw_triggers"
PORT=$WEBHOOK_PORT \
POSTGRES_HOST=$POSTGRES_HOST \
POSTGRES_PORT=$POSTGRES_PORT \
POSTGRES_DB=$POSTGRES_DB \
POSTGRES_USER=$POSTGRES_USER \
POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
DB_TYPE=postgresql \
uv run trigger_webhook.py > /tmp/tac_webhook.log 2>&1 &
WEBHOOK_PID=$!

# Step 3.5: Wait for webhook service to be ready
echo -e "${YELLOW}⏳ Waiting for webhook service to initialize...${NC}"
for i in {1..20}; do
    if curl -s http://localhost:$WEBHOOK_PORT/webhook-status >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Webhook service is ready at http://localhost:$WEBHOOK_PORT${NC}"
        break
    fi
    if [ $i -eq 20 ]; then
        echo -e "${YELLOW}⚠️  Webhook service may still be starting...${NC}"
    fi
    sleep 1
done

# Step 4: Start backend WITHOUT --reload flag
echo -e "${GREEN}🚀 Starting backend on port $BACKEND_PORT...${NC}"
cd "$PROJECT_ROOT/app/server"

# CRITICAL: Do NOT use --reload flag to avoid PostgreSQL PoolError
BACKEND_PORT=$BACKEND_PORT \
FRONTEND_PORT=$FRONTEND_PORT \
POSTGRES_HOST=$POSTGRES_HOST \
POSTGRES_PORT=$POSTGRES_PORT \
POSTGRES_DB=$POSTGRES_DB \
POSTGRES_USER=$POSTGRES_USER \
POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
DB_TYPE=postgresql \
uv run python server.py --host 0.0.0.0 --port $BACKEND_PORT > /tmp/tac_backend.log 2>&1 &
BACKEND_PID=$!

# Step 5: Wait for backend to be ready
echo -e "${YELLOW}⏳ Waiting for backend to initialize...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:$BACKEND_PORT/api/v1/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is ready at http://localhost:$BACKEND_PORT${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Backend failed to start after 30 seconds${NC}"
        echo -e "${YELLOW}Check logs: tail -f /tmp/tac_backend.log${NC}"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# Step 6: Start frontend
echo -e "${GREEN}🎨 Starting frontend on port $FRONTEND_PORT...${NC}"
cd "$PROJECT_ROOT/app/client"
VITE_BACKEND_URL=http://localhost:$BACKEND_PORT bun run dev > /tmp/tac_frontend.log 2>&1 &
FRONTEND_PID=$!

# Step 7: Wait for frontend to be ready
echo -e "${YELLOW}⏳ Waiting for frontend to initialize...${NC}"
sleep 5
for i in {1..20}; do
    if curl -s http://localhost:$FRONTEND_PORT >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend is ready at http://localhost:$FRONTEND_PORT${NC}"
        break
    fi
    if [ $i -eq 20 ]; then
        echo -e "${YELLOW}⚠️  Frontend may still be starting...${NC}"
    fi
    sleep 1
done

# Success message
echo ""
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Full stack is running successfully!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Webhook:   http://localhost:$WEBHOOK_PORT${NC}"
echo -e "${BLUE}Backend:   http://localhost:$BACKEND_PORT${NC}"
echo -e "${BLUE}Frontend:  http://localhost:$FRONTEND_PORT${NC}"
echo -e "${BLUE}API Docs:  http://localhost:$BACKEND_PORT/docs${NC}"
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}📋 Logs:${NC}"
echo -e "  Webhook:  tail -f /tmp/tac_webhook.log"
echo -e "  Backend:  tail -f /tmp/tac_backend.log"
echo -e "  Frontend: tail -f /tmp/tac_frontend.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for user to press Ctrl+C
wait
