#!/bin/bash
# Quick commands for Build State Persistence Regression Tests
# See BUILD_STATE_PERSISTENCE_QUICK_START.md for details

# Navigate to project root
cd "$(dirname "$(dirname "$(dirname "$0")")")"

# ============================================================================
# Essential Commands
# ============================================================================

echo "=== Build State Persistence Tests - Quick Commands ==="
echo ""
echo "1. Run all tests (fastest check):"
echo "   pytest adws/tests/test_build_state_persistence.py -v"
echo ""

echo "2. Run with coverage report:"
echo "   pytest adws/tests/test_build_state_persistence.py --cov=adw_modules.state -v"
echo ""

echo "3. Run specific test class (e.g., save tests):"
echo "   pytest adws/tests/test_build_state_persistence.py::TestBuildStateDataSave -v"
echo ""

echo "4. Run specific test method:"
echo "   pytest adws/tests/test_build_state_persistence.py::TestBuildStateDataSave::test_save_successful_build_results -v"
echo ""

# ============================================================================
# Common Scenarios
# ============================================================================

echo "=== Common Scenarios ==="
echo ""

echo "Scenario 1: Test that successful builds save correctly"
echo "  pytest adws/tests/test_build_state_persistence.py::TestBuildStateDataSave::test_save_successful_build_results -v"
echo ""

echo "Scenario 2: Test that build results survive state reload"
echo "  pytest adws/tests/test_build_state_persistence.py::TestStatePersistenceAcrossReload::test_build_results_survive_reload_cycle -v"
echo ""

echo "Scenario 3: Test backward compatibility with legacy state files"
echo "  pytest adws/tests/test_build_state_persistence.py::TestBackwardCompatibility -v"
echo ""

echo "Scenario 4: Test all schema validation"
echo "  pytest adws/tests/test_build_state_persistence.py::TestBuildResultsSchemaValidation -v"
echo ""

# ============================================================================
# Detailed Analysis
# ============================================================================

echo "=== Detailed Analysis ==="
echo ""

echo "Show coverage with detailed line-by-line output:"
echo "  pytest adws/tests/test_build_state_persistence.py --cov=adw_modules.state --cov-report=term-missing -v"
echo ""

echo "Generate HTML coverage report:"
echo "  pytest adws/tests/test_build_state_persistence.py --cov=adw_modules.state --cov-report=html:htmlcov && open htmlcov/index.html"
echo ""

echo "Show slowest tests (requires pytest plugin):"
echo "  pytest adws/tests/test_build_state_persistence.py --durations=10"
echo ""

echo "Stop on first failure (useful for debugging):"
echo "  pytest adws/tests/test_build_state_persistence.py -x -v"
echo ""

# ============================================================================
# CI/CD Integration
# ============================================================================

echo "=== CI/CD Integration ==="
echo ""

echo "Full CI/CD test (like pipeline would run):"
echo "  pytest adws/tests/test_build_state_persistence.py \\"
echo "    --cov=adw_modules.state \\"
echo "    --cov-fail-under=85 \\"
echo "    --tb=short \\"
echo "    -v \\"
echo "    --junit-xml=test_results.xml"
echo ""

# ============================================================================
# Function to run tests
# ============================================================================

if [ "$1" == "run" ]; then
    echo "Running all tests..."
    pytest adws/tests/test_build_state_persistence.py -v
elif [ "$1" == "coverage" ]; then
    echo "Running tests with coverage..."
    pytest adws/tests/test_build_state_persistence.py --cov=adw_modules.state --cov-report=term-missing -v
elif [ "$1" == "quick" ]; then
    echo "Running quick sanity check..."
    pytest adws/tests/test_build_state_persistence.py::TestBuildStateDataSave -v
elif [ "$1" == "save-tests" ]; then
    echo "Running save/load tests..."
    pytest adws/tests/test_build_state_persistence.py::TestBuildStateDataSave -v
    pytest adws/tests/test_build_state_persistence.py::TestBuildStateDataLoad -v
elif [ "$1" == "persistence" ]; then
    echo "Running persistence tests..."
    pytest adws/tests/test_build_state_persistence.py::TestStatePersistenceAcrossReload -v
elif [ "$1" == "compat" ]; then
    echo "Running backward compatibility tests..."
    pytest adws/tests/test_build_state_persistence.py::TestBackwardCompatibility -v
elif [ "$1" == "html" ]; then
    echo "Generating HTML coverage report..."
    pytest adws/tests/test_build_state_persistence.py \
        --cov=adw_modules.state \
        --cov-report=html:htmlcov
    open htmlcov/index.html
elif [ "$1" == "help" ] || [ -z "$1" ]; then
    echo "Usage: bash QUICK_COMMANDS.sh [command]"
    echo ""
    echo "Commands:"
    echo "  run       - Run all tests"
    echo "  coverage  - Run tests with coverage report"
    echo "  quick     - Quick sanity check (TestBuildStateDataSave only)"
    echo "  save-tests - Run save/load tests"
    echo "  persistence - Run persistence tests"
    echo "  compat    - Run backward compatibility tests"
    echo "  html      - Generate HTML coverage report"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  bash QUICK_COMMANDS.sh run"
    echo "  bash QUICK_COMMANDS.sh coverage"
    echo "  bash QUICK_COMMANDS.sh html"
else
    echo "Unknown command: $1"
    echo "Try: bash QUICK_COMMANDS.sh help"
fi
