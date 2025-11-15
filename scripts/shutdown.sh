#!/bin/bash

# Source port configuration if exists
[ -f ".ports.env" ] && source .ports.env

# Port configuration with fallbacks
SERVER_PORT=${BACKEND_PORT:-8000}
CLIENT_PORT=${FRONTEND_PORT:-5173}
WEBHOOK_PORT=${PORT:-8001}

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Shutting down TAC WebBuilder...${NC}"
echo ""

# Function to kill process on port
kill_port() {
    local port=$1
    local process_name=$2

    # Find process using the port
    local pid=$(lsof -ti:$port 2>/dev/null)

    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}Stopping $process_name on port $port (PID: $pid)...${NC}"
        kill -15 $pid 2>/dev/null

        # Wait up to 5 seconds for graceful shutdown
        for i in {1..5}; do
            if ! kill -0 $pid 2>/dev/null; then
                echo -e "${GREEN}✅ $process_name stopped gracefully${NC}"
                return 0
            fi
            sleep 1
        done

        # Force kill if still running
        if kill -0 $pid 2>/dev/null; then
            echo -e "${YELLOW}Force stopping $process_name...${NC}"
            kill -9 $pid 2>/dev/null
            sleep 1
            echo -e "${GREEN}✅ $process_name stopped${NC}"
        fi
    else
        echo -e "${BLUE}ℹ️  $process_name not running on port $port${NC}"
    fi
}

# Shutdown services in reverse order (frontend, webhook, backend)
kill_port $CLIENT_PORT "Frontend server"
kill_port $WEBHOOK_PORT "Webhook service"
kill_port $SERVER_PORT "Backend server"

echo ""
echo -e "${BLUE}Verifying clean shutdown...${NC}"

# Verify all ports are free
PORTS_CLEAR=0

for port in $CLIENT_PORT $WEBHOOK_PORT $SERVER_PORT; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ Port $port is still in use${NC}"
        PORTS_CLEAR=1
    fi
done

# Check for any stray processes
STRAY_PROCESSES=$(ps aux | grep -E "(server\.py|trigger_webhook\.py|vite|bun.*dev)" | grep -v grep | wc -l)

if [ $STRAY_PROCESSES -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Found $STRAY_PROCESSES potentially stray process(es):${NC}"
    ps aux | grep -E "(server\.py|trigger_webhook\.py|vite|bun.*dev)" | grep -v grep | head -5
    echo ""
    echo -e "${YELLOW}Tip: You may need to manually kill these processes${NC}"
    PORTS_CLEAR=1
fi

echo ""
if [ $PORTS_CLEAR -eq 0 ]; then
    echo -e "${GREEN}✅ All services stopped cleanly${NC}"
    echo -e "${GREEN}   All ports are free and no stray processes detected${NC}"
else
    echo -e "${YELLOW}⚠️  Shutdown completed but some cleanup may be needed${NC}"
    echo -e "${YELLOW}   Run this script again or manually check for stray processes${NC}"
fi
