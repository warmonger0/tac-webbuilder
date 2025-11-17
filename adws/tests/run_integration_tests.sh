#!/bin/bash
# Integration Test Runner for External ADW Workflows
#
# This script runs the integration tests for external tool ADW workflows
# with proper environment setup and reporting.

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADWS_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$ADWS_DIR")"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}External Workflow Integration Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Change to adws directory
cd "$ADWS_DIR"

# Parse command-line arguments
COVERAGE=false
VERBOSE=false
SPECIFIC_TEST=""
MARKERS=""
SKIP_SLOW=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --test)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        -m|--markers)
            MARKERS="$2"
            shift 2
            ;;
        --skip-slow)
            SKIP_SLOW=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --coverage         Run with coverage reporting"
            echo "  -v, --verbose      Verbose output"
            echo "  --test <name>      Run specific test (e.g., TestWorkflowScriptExecution)"
            echo "  -m, --markers <m>  Run tests with specific markers (e.g., integration)"
            echo "  --skip-slow        Skip slow tests"
            echo "  -h, --help         Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Run all integration tests"
            echo "  $0 --coverage                         # Run with coverage"
            echo "  $0 --test TestWorkflowScriptExecution # Run specific test class"
            echo "  $0 -m integration                     # Run only integration tests"
            echo "  $0 --skip-slow                        # Skip slow tests"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Build pytest command
CMD="uv run pytest tests/test_external_workflows_integration.py"

# Add verbose flag
if [ "$VERBOSE" = true ]; then
    CMD="$CMD -v"
else
    CMD="$CMD -v"  # Always use verbose for better output
fi

# Add specific test
if [ -n "$SPECIFIC_TEST" ]; then
    CMD="$CMD::$SPECIFIC_TEST"
fi

# Add markers
if [ -n "$MARKERS" ]; then
    CMD="$CMD -m \"$MARKERS\""
elif [ "$SKIP_SLOW" = true ]; then
    CMD="$CMD -m \"not slow\""
fi

# Add coverage
if [ "$COVERAGE" = true ]; then
    echo -e "${YELLOW}Running with coverage...${NC}"
    CMD="$CMD --cov=. --cov-report=html --cov-report=term-missing"
    CMD="$CMD --cov-config=tests/.coveragerc"
fi

# Add output formatting
CMD="$CMD --tb=short"  # Short traceback format

echo -e "${BLUE}Running command:${NC}"
echo -e "${YELLOW}$CMD${NC}"
echo ""

# Run tests
eval $CMD
TEST_EXIT_CODE=$?

echo ""
echo -e "${BLUE}========================================${NC}"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"

    if [ "$COVERAGE" = true ]; then
        echo ""
        echo -e "${BLUE}Coverage report generated:${NC}"
        echo -e "${YELLOW}  HTML: file://$ADWS_DIR/htmlcov/index.html${NC}"
        echo ""
        echo -e "${BLUE}Open coverage report:${NC}"
        echo -e "${YELLOW}  open htmlcov/index.html${NC}"
    fi
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
