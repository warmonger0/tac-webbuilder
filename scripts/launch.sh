#!/bin/bash

# SINGLE SOURCE OF TRUTH: .ports.env
# All port configuration MUST be in .ports.env - no fallbacks allowed
if [ ! -f ".ports.env" ]; then
    echo "❌ ERROR: .ports.env not found!"
    echo "   Copy .ports.env.sample to .ports.env and configure your ports."
    exit 1
fi

source .ports.env

# Validate required variables are set
if [ -z "$BACKEND_PORT" ] || [ -z "$FRONTEND_PORT" ]; then
    echo "❌ ERROR: BACKEND_PORT and FRONTEND_PORT must be set in .ports.env"
    exit 1
fi

# Export for child processes (server.py, Vite, etc.)
export BACKEND_PORT
export FRONTEND_PORT
export VITE_BACKEND_URL

# Use configured ports
SERVER_PORT=$BACKEND_PORT
CLIENT_PORT=$FRONTEND_PORT
WEBHOOK_PORT=${PORT:-8001}

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Launching TAC WebBuilder...${NC}"

# Function to kill process on port
kill_port() {
    local port=$1
    local process_name=$2

    # Find ALL processes using the port (including parent/child processes)
    local pids=$(lsof -ti:$port 2>/dev/null)

    if [ ! -z "$pids" ]; then
        echo -e "${YELLOW}Found $process_name running on port $port (PIDs: $pids). Killing...${NC}"
        # Kill all processes at once
        echo "$pids" | xargs kill -9 2>/dev/null

        # Wait up to 5 seconds for port to be freed
        local attempts=0
        while [ $attempts -lt 5 ]; do
            if ! lsof -ti:$port >/dev/null 2>&1; then
                echo -e "${GREEN}✅ Port $port is now free${NC}"
                return 0
            fi
            sleep 1
            attempts=$((attempts + 1))
        done

        # Check one more time
        if lsof -ti:$port >/dev/null 2>&1; then
            echo -e "${RED}⚠️  Warning: Port $port may still be in use${NC}"
            return 1
        fi
    fi
}

# Function to wait for endpoint to be ready
wait_for_endpoint() {
    local url=$1
    local service_name=$2
    local max_attempts=${3:-30}  # Default 30 attempts
    local sleep_time=${4:-1}     # Default 1 second between attempts

    local attempt=1
    echo -n "⏳ Waiting for ${service_name} to be ready"

    while [ $attempt -le $max_attempts ]; do
        if curl -s -f -m 2 "$url" > /dev/null 2>&1; then
            echo ""
            echo -e "${GREEN}✅ ${service_name} is ready!${NC}"
            return 0
        fi

        echo -n "."
        sleep $sleep_time
        attempt=$((attempt + 1))
    done

    echo ""
    echo -e "${RED}❌ ${service_name} did not become ready after ${max_attempts} attempts${NC}"
    return 1
}

# Kill any existing processes on our ports
kill_port $SERVER_PORT "backend server"
kill_port $CLIENT_PORT "frontend server"
kill_port $WEBHOOK_PORT "webhook service"

# Get the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

# Check if .env exists in server directory
if [ ! -f "$PROJECT_ROOT/app/server/.env" ]; then
    echo -e "${RED}Warning: No .env file found in app/server/.${NC}"
    echo "Please:"
    echo "  1. cd app/server"
    echo "  2. cp .env.sample .env"
    echo "  3. Edit .env and add your API keys"
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n${BLUE}🛑 Shutting down services...${NC}"

    # Kill all child processes
    jobs -p | xargs -r kill 2>/dev/null

    # Wait for processes to terminate
    wait

    echo -e "${GREEN}✅ Services stopped successfully.${NC}"
    exit 0
}

# Trap EXIT, INT, and TERM signals
trap cleanup EXIT INT TERM

# Start backend
echo -e "${GREEN}Starting backend server...${NC}"
cd "$PROJECT_ROOT/app/server"
uv run python server.py &
BACKEND_PID=$!

# Wait for backend API to be ready (not just process started)
if ! wait_for_endpoint "http://localhost:$SERVER_PORT/api/v1/system-status" "Backend API" 30 1; then
    echo -e "${RED}❌ Backend API did not become ready!${NC}"
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}   Backend process crashed during startup${NC}"
    fi
    exit 1
fi

# Start webhook service
echo -e "${GREEN}Starting webhook service...${NC}"
cd "$PROJECT_ROOT/adws/adw_triggers"
uv run trigger_webhook.py &
WEBHOOK_PID=$!

# Wait for webhook endpoint to be ready
if ! wait_for_endpoint "http://localhost:$WEBHOOK_PORT/ping" "Webhook Service" 30 1; then
    echo -e "${RED}❌ Webhook service did not become ready!${NC}"
    if ! kill -0 $WEBHOOK_PID 2>/dev/null; then
        echo -e "${RED}   Webhook process crashed during startup${NC}"
    fi
    exit 1
fi

# Start frontend
echo -e "${GREEN}Starting frontend server...${NC}"
cd "$PROJECT_ROOT/app/client"
bun run dev &
FRONTEND_PID=$!

# Wait for frontend to be ready
if ! wait_for_endpoint "http://localhost:$CLIENT_PORT" "Frontend" 30 1; then
    echo -e "${RED}❌ Frontend did not become ready!${NC}"
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${RED}   Frontend process crashed during startup${NC}"
    fi
    exit 1
fi

echo ""
echo -e "${GREEN}✅ All services started!${NC}"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🏥 Running comprehensive health checks...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Run health checks
cd "$PROJECT_ROOT"
bash scripts/health_check.sh

HEALTH_EXIT=$?

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if [ $HEALTH_EXIT -eq 0 ]; then
    echo -e "${GREEN}✅ TAC WebBuilder is fully operational!${NC}"
else
    echo -e "${YELLOW}⚠️  TAC WebBuilder started but some health checks failed${NC}"
    echo -e "${YELLOW}   Review the health check output above for details${NC}"
fi
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}Service URLs:${NC}"
echo -e "${BLUE}  Frontend:       ${NC}http://localhost:$CLIENT_PORT"
echo -e "${BLUE}  Backend:        ${NC}http://localhost:$SERVER_PORT"
echo -e "${BLUE}  API Docs:       ${NC}http://localhost:$SERVER_PORT/docs"
echo -e "${BLUE}  Webhook:        ${NC}http://localhost:$WEBHOOK_PORT"
echo -e "${BLUE}  Webhook Health: ${NC}http://localhost:$WEBHOOK_PORT/health"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo -e "${BLUE}Tip: Run './scripts/health_check.sh' anytime to verify system health${NC}"
echo ""

# Wait for user to press Ctrl+C
wait
