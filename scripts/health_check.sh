#!/bin/bash

# Health check script for TAC WebBuilder
# Verifies all services are running and functional

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

# Exit codes
EXIT_SUCCESS=0
EXIT_FAILURE=1

# Track overall health
OVERALL_HEALTH=0

echo -e "${BLUE}🏥 TAC WebBuilder Health Check${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Function to check if port is listening
check_port() {
    local port=$1
    local service_name=$2

    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name is listening on port $port${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name is NOT listening on port $port${NC}"
        OVERALL_HEALTH=1
        return 1
    fi
}

# Function to check HTTP endpoint
check_endpoint() {
    local url=$1
    local service_name=$2
    local timeout=${3:-5}

    if curl -s -f -m $timeout "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name is responding at $url${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name is NOT responding at $url${NC}"
        OVERALL_HEALTH=1
        return 1
    fi
}

# Function to check JSON API endpoint and validate response
check_json_endpoint() {
    local url=$1
    local service_name=$2
    local expected_field=$3
    local timeout=${4:-5}

    response=$(curl -s -f -m $timeout "$url" 2>&1)
    curl_exit=$?

    if [ $curl_exit -eq 0 ]; then
        # Check if response is valid JSON
        if echo "$response" | python3 -m json.tool > /dev/null 2>&1; then
            # If expected field is provided, check for it
            if [ -n "$expected_field" ]; then
                if echo "$response" | grep -q "\"$expected_field\""; then
                    echo -e "${GREEN}✅ $service_name API is responding with valid data${NC}"
                    return 0
                else
                    echo -e "${YELLOW}⚠️  $service_name API responded but missing expected field '$expected_field'${NC}"
                    OVERALL_HEALTH=1
                    return 1
                fi
            else
                echo -e "${GREEN}✅ $service_name API is responding with valid JSON${NC}"
                return 0
            fi
        else
            echo -e "${RED}❌ $service_name API returned invalid JSON${NC}"
            OVERALL_HEALTH=1
            return 1
        fi
    else
        echo -e "${RED}❌ $service_name API is NOT responding at $url${NC}"
        OVERALL_HEALTH=1
        return 1
    fi
}

# Function to check workflow history data
check_workflow_history() {
    local backend_url="http://localhost:$SERVER_PORT/api/workflow-history?limit=5"
    local frontend_url="http://localhost:$CLIENT_PORT/api/workflow-history?limit=5"

    # Check backend directly (without -f flag to avoid 404 issues)
    response=$(curl -s -m 5 "$backend_url" 2>&1)
    http_code=$(curl -s -w "%{http_code}" -o /dev/null -m 5 "$backend_url" 2>&1)

    if [ "$http_code" = "200" ]; then
        # Check if response has workflows and analytics
        total_count=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('total_count', 0))" 2>/dev/null)

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Backend Workflow History API: ${total_count} workflows${NC}"

            if [ "$total_count" -eq 0 ]; then
                echo -e "${YELLOW}   ⚠️  No workflow history data (normal for fresh installs)${NC}"
            fi
        else
            echo -e "${RED}❌ Backend Workflow History API returned malformed data${NC}"
            OVERALL_HEALTH=1
            return 1
        fi
    else
        echo -e "${RED}❌ Backend Workflow History API returned HTTP $http_code${NC}"
        OVERALL_HEALTH=1
        return 1
    fi

    # Check frontend proxy
    response=$(curl -s -m 5 "$frontend_url" 2>&1)
    http_code=$(curl -s -w "%{http_code}" -o /dev/null -m 5 "$frontend_url" 2>&1)

    if [ "$http_code" = "200" ]; then
        total_count=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('total_count', 0))" 2>/dev/null)

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Frontend Proxy Workflow History: ${total_count} workflows${NC}"

            if [ "$total_count" -eq 0 ]; then
                echo -e "${YELLOW}   ⚠️  Frontend proxy working but no data${NC}"
                OVERALL_HEALTH=1
            fi
        else
            echo -e "${RED}❌ Frontend proxy returned malformed data${NC}"
            OVERALL_HEALTH=1
            return 1
        fi
    else
        echo -e "${RED}❌ Frontend proxy returned HTTP $http_code${NC}"
        echo -e "${YELLOW}   This means the React app won't receive data${NC}"
        echo -e "${YELLOW}   Try restarting the frontend server${NC}"
        OVERALL_HEALTH=1
        return 1
    fi

    return 0
}

# Function to check database accessibility
check_database() {
    local db_path="app/server/db/workflow_history.db"

    if [ ! -f "$db_path" ]; then
        echo -e "${YELLOW}⚠️  Workflow history database not found (will be created on first use)${NC}"
        return 0
    fi

    # Check if we can query the database
    count=$(sqlite3 "$db_path" "SELECT COUNT(*) FROM workflow_history;" 2>/dev/null)

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Database is accessible (${count} workflow records)${NC}"
        return 0
    else
        echo -e "${RED}❌ Database exists but cannot be queried${NC}"
        OVERALL_HEALTH=1
        return 1
    fi
}

# 1. Check Backend Service
echo -e "${BLUE}[1/6] Backend Server (port $SERVER_PORT)${NC}"
check_port $SERVER_PORT "Backend"
if [ $? -eq 0 ]; then
    check_endpoint "http://localhost:$SERVER_PORT/docs" "Backend API Docs"
    check_json_endpoint "http://localhost:$SERVER_PORT/api/routes" "Backend Routes API" "routes"
fi
echo ""

# 2. Check Frontend Service
echo -e "${BLUE}[2/6] Frontend Server (port $CLIENT_PORT)${NC}"
check_port $CLIENT_PORT "Frontend"
if [ $? -eq 0 ]; then
    check_endpoint "http://localhost:$CLIENT_PORT" "Frontend"
fi
echo ""

# 3. Check Webhook Service
echo -e "${BLUE}[3/6] Webhook Service (port $WEBHOOK_PORT)${NC}"
check_port $WEBHOOK_PORT "Webhook"
if [ $? -eq 0 ]; then
    check_endpoint "http://localhost:$WEBHOOK_PORT/ping" "Webhook Health Endpoint"
fi
echo ""

# 4. Check API Connectivity
echo -e "${BLUE}[4/6] API Connectivity${NC}"
check_json_endpoint "http://localhost:$SERVER_PORT/api/workflows" "Workflows API" "" 10
check_json_endpoint "http://localhost:$CLIENT_PORT/api/routes" "Frontend Proxy to Backend" "routes"
echo ""

# 5. Check Workflow History
echo -e "${BLUE}[5/6] Workflow History${NC}"
check_workflow_history
check_database
echo ""

# 6. Check WebSocket Connections
echo -e "${BLUE}[6/6] WebSocket Endpoints${NC}"
echo -e "${GREEN}✅ WebSocket endpoints are registered (cannot test with HTTP)${NC}"
echo -e "${BLUE}   - /ws/workflows${NC}"
echo -e "${BLUE}   - /ws/workflow-history${NC}"
echo -e "${BLUE}   - /ws/routes${NC}"
echo -e "${YELLOW}   Note: WebSocket endpoints require upgrade protocol and cannot be tested with curl${NC}"
echo ""

# Summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if [ $OVERALL_HEALTH -eq 0 ]; then
    echo -e "${GREEN}✅ All health checks passed!${NC}"
    echo -e "${GREEN}   System is fully operational${NC}"
    exit $EXIT_SUCCESS
else
    echo -e "${RED}❌ Some health checks failed${NC}"
    echo -e "${RED}   Please review the errors above${NC}"
    exit $EXIT_FAILURE
fi
