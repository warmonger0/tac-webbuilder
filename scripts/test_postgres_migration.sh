#!/bin/bash
# PostgreSQL Migration Test Script
# Tests both SQLite and PostgreSQL database adapters

set -e  # Exit on error

PROJECT_ROOT="/Users/Warmonger0/tac/tac-webbuilder"
SERVER_DIR="$PROJECT_ROOT/app/server"

echo "======================================================================"
echo "PostgreSQL Migration - Phase 3 Testing"
echo "======================================================================"
echo ""

# Check if Docker is running
if ! docker ps >/dev/null 2>&1; then
    echo "⚠️  Docker is not running!"
    echo "   Please start Docker Desktop and run this script again."
    echo ""
    echo "   You can still test SQLite by running:"
    echo "   cd app/server && uv run pytest tests/ -v"
    exit 1
fi

# Check if PostgreSQL is running
if ! docker ps | grep -q tac-webbuilder-postgres; then
    echo "⚠️  PostgreSQL container is not running"
    echo "   Starting PostgreSQL..."
    cd "$PROJECT_ROOT"
    docker-compose up -d postgres

    echo "   Waiting for PostgreSQL to be healthy..."
    sleep 5

    # Wait for health check
    for i in {1..30}; do
        if docker ps | grep tac-webbuilder-postgres | grep -q "healthy"; then
            echo "   ✅ PostgreSQL is healthy"
            break
        fi
        echo "   Waiting... ($i/30)"
        sleep 1
    done
fi

echo ""
echo "======================================================================"
echo "Step 1: Test PostgreSQL Connection"
echo "======================================================================"
cd "$SERVER_DIR"
uv run python test_postgres_connection.py

echo ""
echo "======================================================================"
echo "Step 2: Test Database Operations"
echo "======================================================================"
uv run python test_db_operations.py

echo ""
echo "======================================================================"
echo "Step 3: Run Performance Benchmark"
echo "======================================================================"
uv run python benchmark_db_performance.py

echo ""
echo "======================================================================"
echo "Step 4: Run Test Suite - SQLite (Baseline)"
echo "======================================================================"
export DB_TYPE=sqlite
uv run pytest tests/ -v --tb=short -x

echo ""
echo "======================================================================"
echo "Step 5: Run Test Suite - PostgreSQL"
echo "======================================================================"
export DB_TYPE=postgresql
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=tac_webbuilder
export POSTGRES_USER=tac_user
export POSTGRES_PASSWORD=changeme

uv run pytest tests/ -v --tb=short 2>&1 | tee postgres_test_results.txt

echo ""
echo "======================================================================"
echo "✅ Testing Complete!"
echo "======================================================================"
echo ""
echo "Results saved to: app/server/postgres_test_results.txt"
echo "Review and update: POSTGRES_TEST_RESULTS.md"
echo ""
