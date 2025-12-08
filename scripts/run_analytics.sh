#!/bin/bash
# =============================================================================
# Analytics Runner - Automatically sets PostgreSQL environment variables
# =============================================================================
# This script sources the correct PostgreSQL credentials from .env and runs
# analytics scripts with the proper environment configuration.
#
# Usage:
#   ./scripts/run_analytics.sh analyze_daily_patterns.py --report
#   ./scripts/run_analytics.sh analyze_errors.py --days 7
#   ./scripts/run_analytics.sh analyze_costs.py --report
# =============================================================================

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if .env exists
ENV_FILE="$PROJECT_ROOT/app/server/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Error: .env file not found at $ENV_FILE${NC}"
    echo "Please create .env file with PostgreSQL credentials"
    exit 1
fi

# Source environment variables from .env
echo -e "${BLUE}Loading PostgreSQL credentials from .env...${NC}"
export $(grep -v '^#' "$ENV_FILE" | grep -E '^POSTGRES_' | xargs)

# Verify required environment variables are set
REQUIRED_VARS=("POSTGRES_HOST" "POSTGRES_PORT" "POSTGRES_DB" "POSTGRES_USER" "POSTGRES_PASSWORD")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo -e "${RED}❌ Error: Missing required environment variables:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    echo ""
    echo "Please add these variables to $ENV_FILE"
    exit 1
fi

echo -e "${GREEN}✅ PostgreSQL configuration loaded:${NC}"
echo "   Host: $POSTGRES_HOST:$POSTGRES_PORT"
echo "   Database: $POSTGRES_DB"
echo "   User: $POSTGRES_USER"
echo ""

# Check if script name was provided
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}Usage: $0 <script_name.py> [args...]${NC}"
    echo ""
    echo "Available analytics scripts:"
    echo "  - analyze_daily_patterns.py --report"
    echo "  - analyze_errors.py --report"
    echo "  - analyze_costs.py --report"
    echo "  - analyze_latency.py --report"
    echo "  - analyze_deterministic_patterns.py --report"
    echo ""
    echo "Example:"
    echo "  $0 analyze_daily_patterns.py --report"
    exit 1
fi

SCRIPT_NAME="$1"
shift  # Remove script name from arguments

# Build full script path
if [[ "$SCRIPT_NAME" == /* ]]; then
    # Absolute path provided
    SCRIPT_PATH="$SCRIPT_NAME"
else
    # Relative path - look in scripts directory
    SCRIPT_PATH="$PROJECT_ROOT/scripts/$SCRIPT_NAME"
fi

# Check if script exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo -e "${RED}❌ Error: Script not found at $SCRIPT_PATH${NC}"
    exit 1
fi

# Run the script with remaining arguments
echo -e "${BLUE}Running: $(basename "$SCRIPT_PATH") $@${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cd "$PROJECT_ROOT/app/server"
.venv/bin/python3 "$SCRIPT_PATH" "$@"

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}✅ Script completed successfully${NC}"
else
    echo -e "${RED}❌ Script failed with exit code $exit_code${NC}"
fi

exit $exit_code
