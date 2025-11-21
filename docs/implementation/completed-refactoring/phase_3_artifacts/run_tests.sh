#!/bin/bash

# Run the ProcessRunner unit tests
echo "Running ProcessRunner unit tests..."
echo "===================================="
echo ""

cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Run tests with verbose output
uv run pytest tests/utils/test_process_runner.py -v --tb=short

echo ""
echo "Test execution completed!"
