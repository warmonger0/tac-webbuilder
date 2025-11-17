# Test Execution Guide

Quick reference for running and debugging the ADW test suite.

## Quick Start

```bash
# Navigate to project root
cd /Users/Warmonger0/tac/tac-webbuilder

# Run all test_runner tests
pytest adws/tests/test_test_runner.py -v

# Run with coverage
pytest adws/tests/test_test_runner.py --cov=adws/adw_modules --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Common Commands

### Basic Execution

```bash
# Run all tests with verbose output
pytest adws/tests/test_test_runner.py -v

# Run all tests with minimal output
pytest adws/tests/test_test_runner.py -q

# Run all tests with very detailed output
pytest adws/tests/test_test_runner.py -vv

# Run tests and stop on first failure
pytest adws/tests/test_test_runner.py -x

# Run tests and stop after N failures
pytest adws/tests/test_test_runner.py --maxfail=3
```

### Coverage Reports

```bash
# Generate coverage report in terminal
pytest adws/tests/test_test_runner.py --cov=adws/adw_modules --cov-report=term-missing

# Generate HTML coverage report
pytest adws/tests/test_test_runner.py --cov=adws/adw_modules --cov-report=html

# Generate XML coverage report (for CI/CD)
pytest adws/tests/test_test_runner.py --cov=adws/adw_modules --cov-report=xml

# Fail if coverage below threshold
pytest adws/tests/test_test_runner.py --cov=adws/adw_modules --cov-fail-under=80
```

### Filtering Tests

```bash
# Run specific test class
pytest adws/tests/test_test_runner.py::TestRunPytestSuccess -v

# Run specific test method
pytest adws/tests/test_test_runner.py::TestRunPytestSuccess::test_run_pytest_success -v

# Run tests matching pattern
pytest adws/tests/test_test_runner.py -k "pytest and success" -v

# Run tests NOT matching pattern
pytest adws/tests/test_test_runner.py -k "not timeout" -v

# Run by marker
pytest adws/tests/ -m unit -v
pytest adws/tests/ -m "not slow" -v
```

### Debugging

```bash
# Show full tracebacks
pytest adws/tests/test_test_runner.py --tb=long

# Show local variables in tracebacks
pytest adws/tests/test_test_runner.py -l

# Drop into debugger on failures
pytest adws/tests/test_test_runner.py --pdb

# Drop into debugger on first failure
pytest adws/tests/test_test_runner.py -x --pdb

# Show print statements
pytest adws/tests/test_test_runner.py -s

# Show fixture names
pytest adws/tests/test_test_runner.py --fixtures
```

### Test Collection

```bash
# Collect tests without running
pytest adws/tests/test_test_runner.py --collect-only

# Collect and show test count
pytest adws/tests/test_test_runner.py --collect-only -q

# Collect with fixture usage
pytest adws/tests/test_test_runner.py --fixtures-per-test
```

## Running Specific Test Classes

### Initialization Tests
```bash
pytest adws/tests/test_test_runner.py::TestTestRunnerInit -v
```

### Pytest Success Tests
```bash
pytest adws/tests/test_test_runner.py::TestRunPytestSuccess -v
```

### Pytest Failure Tests
```bash
pytest adws/tests/test_test_runner.py::TestRunPytestFailures -v
```

### Vitest Success Tests
```bash
pytest adws/tests/test_test_runner.py::TestRunVitestSuccess -v
```

### Vitest Failure Tests
```bash
pytest adws/tests/test_test_runner.py::TestRunVitestFailures -v
```

### run_all() Tests
```bash
pytest adws/tests/test_test_runner.py::TestRunAll -v
```

### Serialization Tests
```bash
pytest adws/tests/test_test_runner.py::TestResultToDict -v
```

### Edge Cases Tests
```bash
pytest adws/tests/test_test_runner.py::TestEdgeCases -v
```

### Integration Tests
```bash
pytest adws/tests/test_test_runner.py::TestIntegration -v
```

### Command Construction Tests
```bash
pytest adws/tests/test_test_runner.py::TestCommandConstruction -v
```

## Test Group Execution

### All Success Scenarios
```bash
pytest adws/tests/test_test_runner.py -k "success" -v
```

### All Failure Scenarios
```bash
pytest adws/tests/test_test_runner.py -k "failure or fail or timeout or error" -v
```

### All Pytest Tests
```bash
pytest adws/tests/test_test_runner.py -k "pytest" -v
```

### All Vitest Tests
```bash
pytest adws/tests/test_test_runner.py -k "vitest" -v
```

### All Edge Case Tests
```bash
pytest adws/tests/test_test_runner.py::TestEdgeCases -v
```

## Combined Commands

### Full Validation
```bash
# Run all tests with coverage report and fail on low coverage
pytest adws/tests/test_test_runner.py \
  -v \
  --cov=adws/adw_modules \
  --cov-report=term-missing \
  --cov-report=html \
  --cov-fail-under=80

# View the HTML report
open htmlcov/index.html
```

### CI/CD Pipeline
```bash
# Strict testing: fail on first error, require 80% coverage, output XML
pytest adws/tests/test_test_runner.py \
  -v \
  -x \
  --cov=adws/adw_modules \
  --cov-report=xml \
  --cov-fail-under=80 \
  --junitxml=test-results.xml
```

### Quick Feedback
```bash
# Fast feedback: stop on first failure, show local variables, show prints
pytest adws/tests/test_test_runner.py \
  -x \
  -l \
  -s \
  --tb=short
```

### Development Mode
```bash
# Full output, all details, drop into debugger on failure
pytest adws/tests/test_test_runner.py \
  -vv \
  -s \
  --tb=long \
  --pdb
```

## Performance Analysis

```bash
# Show slowest 10 tests
pytest adws/tests/test_test_runner.py --durations=10

# Show all test durations
pytest adws/tests/test_test_runner.py --durations=0

# Show fixtures used by each test
pytest adws/tests/test_test_runner.py --fixtures-per-test
```

## Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (using 4 CPUs)
pytest adws/tests/test_test_runner.py -n 4

# Run tests in parallel with output
pytest adws/tests/test_test_runner.py -n 4 -v
```

## Test Validation

```bash
# Validate test code (lint)
pylint adws/tests/test_test_runner.py

# Type checking
mypy adws/tests/test_test_runner.py

# Code formatting check
black --check adws/tests/test_test_runner.py

# Format code
black adws/tests/test_test_runner.py
```

## Troubleshooting

### Issue: Import Errors

**Symptom**: `ModuleNotFoundError: No module named 'adw_modules'`

**Solution**:
```bash
# Option 1: Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/adws"
pytest adws/tests/test_test_runner.py -v

# Option 2: Run from project root
cd /Users/Warmonger0/tac/tac-webbuilder
pytest adws/tests/test_test_runner.py -v
```

### Issue: Fixture Not Found

**Symptom**: `fixture 'fixture_name' not found`

**Solution**:
```bash
# Verify conftest.py is in tests directory
ls -la adws/tests/conftest.py

# Verify __init__.py exists
ls -la adws/tests/__init__.py
```

### Issue: Tests Fail with FileNotFoundError

**Symptom**: `FileNotFoundError: No such file or directory`

**Solution**:
```python
# Ensure tmp_path fixture is used
def test_something(tmp_path):
    # Create directories before creating files
    report_path = tmp_path / "app" / "server"
    report_path.mkdir(parents=True, exist_ok=True)
```

### Issue: Mocks Not Working

**Symptom**: Tests still try to run actual subprocess commands

**Solution**:
```python
# Use correct patch path
@patch("adws.adw_modules.test_runner.subprocess.run")
def test_something(mock_run):
    mock_run.return_value = Mock(stdout="", stderr="", returncode=0)
```

## Environment Setup

### Install Dependencies

```bash
# Install pytest and required plugins
pip install pytest pytest-cov pytest-mock

# Optional: Install performance tools
pip install pytest-xdist pytest-benchmark

# Optional: Install code quality tools
pip install pylint black mypy
```

### Verify Installation

```bash
# Check pytest version
pytest --version

# Check plugins
pytest --co | head -20

# List available fixtures
pytest --fixtures | head -50
```

## Continuous Integration

### GitHub Actions

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install pytest pytest-cov pytest-mock

      - name: Run tests
        run: |
          pytest adws/tests/test_test_runner.py \
            -v \
            --cov=adws/adw_modules \
            --cov-report=xml \
            --cov-fail-under=80

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

### Local Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

pytest adws/tests/test_test_runner.py \
  -x \
  --cov=adws/adw_modules \
  --cov-fail-under=80

if [ $? -ne 0 ]; then
  echo "Tests failed. Commit aborted."
  exit 1
fi
```

## Reference

### Test Class Coverage

| Class | Tests | Focus |
|-------|-------|-------|
| TestTestRunnerInit | 3 | Initialization |
| TestRunPytestSuccess | 7 | Success scenarios |
| TestRunPytestFailures | 7 | Failure handling |
| TestRunVitestSuccess | 5 | Vitest success |
| TestRunVitestFailures | 4 | Vitest failures |
| TestRunAll | 4 | Combined execution |
| TestResultToDict | 4 | Serialization |
| TestEdgeCases | 15+ | Edge cases |
| TestIntegration | 3 | End-to-end |
| TestCommandConstruction | 4 | Command building |

### Fixture Quick Reference

| Fixture | Source | Purpose |
|---------|--------|---------|
| `project_root` | conftest.py | Mock project directory |
| `test_runner` | conftest.py | TestRunner instance |
| `pytest_success_report` | test_test_runner.py | Successful test report |
| `pytest_failure_report` | test_test_runner.py | Failed test report |
| `vitest_success_report` | test_test_runner.py | Successful vitest report |
| `vitest_failure_report` | test_test_runner.py | Failed vitest report |
| `coverage_report` | test_test_runner.py | Coverage report |

## Tips & Tricks

### Run only recent tests
```bash
pytest adws/tests/test_test_runner.py --lf  # last failed
pytest adws/tests/test_test_runner.py --ff  # failed first
```

### Generate test report
```bash
pytest adws/tests/test_test_runner.py --html=report.html --self-contained-html
```

### Profile test execution
```bash
python -m cProfile -m pytest adws/tests/test_test_runner.py
```

### Check test quality
```bash
pytest adws/tests/test_test_runner.py --pycodestyle --pydocstyle
```

## Quick Links

- Test File: `/Users/Warmonger0/tac/tac-webbuilder/adws/tests/test_test_runner.py`
- Fixtures: `/Users/Warmonger0/tac/tac-webbuilder/adws/tests/conftest.py`
- Source: `/Users/Warmonger0/tac/tac-webbuilder/adws/adw_modules/test_runner.py`
- README: `/Users/Warmonger0/tac/tac-webbuilder/adws/tests/README.md`
