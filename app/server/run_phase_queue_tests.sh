#!/bin/bash

# Test runner for phase queue service tests
# Ensures proper PostgreSQL environment setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== Phase Queue Service Tests ==="
echo ""

# Check if PostgreSQL environment variables are set
if [ -z "$POSTGRES_HOST" ] || [ -z "$POSTGRES_PORT" ] || [ -z "$POSTGRES_DB" ]; then
    echo -e "${YELLOW}Setting PostgreSQL environment variables...${NC}"
    export POSTGRES_HOST=${POSTGRES_HOST:-localhost}
    export POSTGRES_PORT=${POSTGRES_PORT:-5432}
    export POSTGRES_DB=${POSTGRES_DB:-tac_webbuilder}
    export POSTGRES_USER=${POSTGRES_USER:-tac_user}
    export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-changeme}
    export DB_TYPE=postgresql
fi

echo "PostgreSQL Configuration:"
echo "  Host: $POSTGRES_HOST"
echo "  Port: $POSTGRES_PORT"
echo "  Database: $POSTGRES_DB"
echo "  User: $POSTGRES_USER"
echo "  Type: $DB_TYPE"
echo ""

# Run the specific failing tests
echo "Running phase queue service tests..."
echo ""

.venv/bin/pytest tests/services/test_phase_queue_service.py::test_invalid_status_raises_error -v --tb=short
TEST1=$?

.venv/bin/pytest tests/services/test_phase_queue_service.py::test_enqueue_with_predicted_patterns -v --tb=short
TEST2=$?

.venv/bin/pytest tests/services/test_phase_queue_service.py::test_enqueue_without_predicted_patterns -v --tb=short
TEST3=$?

.venv/bin/pytest tests/services/test_phase_queue_service.py::test_enqueue_with_empty_patterns_list -v --tb=short
TEST4=$?

echo ""
echo "=== Test Results Summary ==="
[ $TEST1 -eq 0 ] && echo -e "${GREEN}✓ test_invalid_status_raises_error${NC}" || echo -e "${RED}✗ test_invalid_status_raises_error${NC}"
[ $TEST2 -eq 0 ] && echo -e "${GREEN}✓ test_enqueue_with_predicted_patterns${NC}" || echo -e "${RED}✗ test_enqueue_with_predicted_patterns${NC}"
[ $TEST3 -eq 0 ] && echo -e "${GREEN}✓ test_enqueue_without_predicted_patterns${NC}" || echo -e "${RED}✗ test_enqueue_without_predicted_patterns${NC}"
[ $TEST4 -eq 0 ] && echo -e "${GREEN}✓ test_enqueue_with_empty_patterns_list${NC}" || echo -e "${RED}✗ test_enqueue_with_empty_patterns_list${NC}"

if [ $TEST1 -eq 0 ] && [ $TEST2 -eq 0 ] && [ $TEST3 -eq 0 ] && [ $TEST4 -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed${NC}"
    exit 1
fi
