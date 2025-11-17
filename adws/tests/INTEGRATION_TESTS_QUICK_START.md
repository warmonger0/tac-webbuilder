# Integration Tests Quick Start Guide

## Quick Start (TL;DR)

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/adws

# Make test runner executable
chmod +x tests/run_integration_tests.sh

# Run all integration tests
./tests/run_integration_tests.sh

# Run with coverage
./tests/run_integration_tests.sh --coverage

# Open coverage report
open htmlcov/index.html
```

## What Was Created

### 1. Integration Test File (22 tests)
**File**: `tests/test_external_workflows_integration.py`

Tests complete workflow execution for:
- `adw_test_workflow.py` - Test execution workflow
- `adw_build_workflow.py` - Build/typecheck workflow
- `adw_test_external.py` - External test runner ADW
- `adw_build_external.py` - External build runner ADW

### 2. Test Fixtures
**File**: `tests/conftest.py` (updated)

New fixtures:
- `project_root` - Project root path
- `temp_worktree` - Mock worktree with complete structure
- `adw_state_fixture` - ADW state (auto-cleanup)
- `sample_test_results` - Sample test results
- `sample_build_results` - Sample build results

### 3. Test Runner Script
**File**: `tests/run_integration_tests.sh`

Features:
- Run all or specific tests
- Coverage reporting
- Skip slow tests
- Colored output

### 4. Documentation
- `INTEGRATION_TESTS_README.md` - Comprehensive guide
- `INTEGRATION_TESTS_IMPLEMENTATION_SUMMARY.md` - Implementation details
- `INTEGRATION_TESTS_QUICK_START.md` - This file

## Test Structure

### 6 Test Classes, 22 Tests Total

```
TestWorkflowScriptExecution (6 tests)
├── test_test_workflow_json_input
├── test_test_workflow_cli_args
├── test_test_workflow_invalid_json
├── test_build_workflow_json_input
├── test_build_workflow_cli_args
└── test_build_workflow_invalid_json

TestExternalADWIntegration (4 tests)
├── test_test_external_complete_flow
├── test_test_external_missing_worktree
├── test_build_external_complete_flow
└── test_build_external_missing_state

TestStatePersistence (2 tests)
├── test_state_load_save_cycle
└── test_state_data_flow_across_chain

TestErrorScenarios (4 tests)
├── test_invalid_state_file
├── test_workflow_timeout_handling
├── test_json_parsing_error_handling
└── test_missing_required_args

TestDataFlow (3 tests)
├── test_input_parameters_propagation
├── test_compact_json_output_format
└── test_state_persistence_across_subprocess_chain

TestExitCodes (3 tests)
├── test_successful_test_exit_code
├── test_failed_test_exit_code
└── test_error_exit_code
```

## Running Tests

### Method 1: Using Test Runner Script (Recommended)

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/adws

# Make executable (first time only)
chmod +x tests/run_integration_tests.sh

# Run all tests
./tests/run_integration_tests.sh

# Run with coverage
./tests/run_integration_tests.sh --coverage

# Run specific test class
./tests/run_integration_tests.sh --test TestWorkflowScriptExecution

# Skip slow tests
./tests/run_integration_tests.sh --skip-slow

# Get help
./tests/run_integration_tests.sh --help
```

### Method 2: Using pytest Directly

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/adws

# Run all integration tests
uv run pytest tests/test_external_workflows_integration.py -v

# Run with coverage
uv run pytest tests/test_external_workflows_integration.py -v \
  --cov=. --cov-report=html --cov-report=term-missing

# Run specific test class
uv run pytest tests/test_external_workflows_integration.py::TestWorkflowScriptExecution -v

# Run specific test
uv run pytest tests/test_external_workflows_integration.py::TestWorkflowScriptExecution::test_test_workflow_json_input -v

# Run only integration tests (marked)
uv run pytest -m integration -v

# Skip slow tests
uv run pytest -m "not slow" -v
```

## What Gets Tested

### Complete Workflow Flow
1. ✅ Create mock worktree with test files
2. ✅ Initialize ADW state with worktree path
3. ✅ Execute external ADW wrapper
4. ✅ Verify results stored in state
5. ✅ Validate exit codes
6. ✅ Automatic cleanup

### Error Scenarios
- ✅ Missing worktree path
- ✅ Invalid state files
- ✅ Tool workflow failures
- ✅ JSON parsing errors
- ✅ Timeout handling
- ✅ Missing required arguments

### Data Flow
- ✅ Input parameters → Tool → Output
- ✅ State persistence across subprocess chain
- ✅ Compact JSON output format
- ✅ Exit code correctness

## Key Features

### 1. Real Subprocess Execution
Tests use **real subprocess calls** (not mocked):
```python
result = subprocess.run(cmd, cwd=temp_worktree, ...)
```

### 2. Temporary Directory Isolation
All tests use temporary directories:
```python
@pytest.fixture
def temp_worktree(tmp_path: Path) -> Path:
    """Create mock worktree in tmp_path"""
```

### 3. Automatic Cleanup
All fixtures clean up automatically:
- Temporary worktree directories
- ADW state files
- Log files

### 4. Mock Worktree Structure
Complete project structure:
```
test_worktree/
├── app/server/tests/test_sample.py (passing)
├── app/server/tests/test_failing.py (failing)
├── app/client/src/sample.ts (valid)
└── app/client/src/error.ts (with errors)
```

## Coverage Goals

**Target**: >80% code coverage

**Target Files**:
- `adw_test_workflow.py`
- `adw_build_workflow.py`
- `adw_test_external.py`
- `adw_build_external.py`

## Viewing Coverage Report

```bash
# After running with --coverage
cd /Users/Warmonger0/tac/tac-webbuilder/adws

# Open HTML coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

The coverage report shows:
- Line-by-line coverage
- Uncovered lines highlighted
- Branch coverage
- Summary statistics

## Common Commands

```bash
# Run all tests with coverage
./tests/run_integration_tests.sh --coverage

# Run only workflow script tests
uv run pytest tests/test_external_workflows_integration.py::TestWorkflowScriptExecution -v

# Run only external ADW tests
uv run pytest tests/test_external_workflows_integration.py::TestExternalADWIntegration -v

# Run only error scenario tests
uv run pytest tests/test_external_workflows_integration.py::TestErrorScenarios -v

# Run with verbose output and stop on first failure
uv run pytest tests/test_external_workflows_integration.py -v -x

# Run and show local variables on failure
uv run pytest tests/test_external_workflows_integration.py -v -l

# Run and show print statements
uv run pytest tests/test_external_workflows_integration.py -v -s
```

## Expected Output

### Success
```
========================================
External Workflow Integration Tests
========================================

Running command:
uv run pytest tests/test_external_workflows_integration.py -v

tests/test_external_workflows_integration.py::TestWorkflowScriptExecution::test_test_workflow_json_input PASSED
tests/test_external_workflows_integration.py::TestWorkflowScriptExecution::test_test_workflow_cli_args PASSED
...
tests/test_external_workflows_integration.py::TestExitCodes::test_error_exit_code PASSED

========================================
All tests passed!
========================================
```

### With Coverage
```
Coverage report generated:
  HTML: file:///Users/Warmonger0/tac/tac-webbuilder/adws/htmlcov/index.html

Open coverage report:
  open htmlcov/index.html
```

## Troubleshooting

### Tests Take Too Long
Skip slow tests:
```bash
./tests/run_integration_tests.sh --skip-slow
```

### Import Errors
Ensure you're in the correct directory:
```bash
cd /Users/Warmonger0/tac/tac-webbuilder/adws
```

### State Files Not Cleaned Up
Use the fixtures with automatic cleanup:
```python
def test_something(adw_state_fixture):  # This auto-cleans
    # Test code
```

### Permission Denied
Make script executable:
```bash
chmod +x tests/run_integration_tests.sh
```

## Next Steps

1. **Run the tests**:
   ```bash
   ./tests/run_integration_tests.sh --coverage
   ```

2. **Check coverage**:
   ```bash
   open htmlcov/index.html
   ```

3. **Add more tests** (if coverage <80%):
   - Add tests for uncovered code paths
   - Add edge case tests
   - Add performance tests

4. **Integrate into CI/CD**:
   ```yaml
   # .github/workflows/test.yml
   - name: Run integration tests
     run: |
       cd adws
       ./tests/run_integration_tests.sh --coverage
   ```

## Files Reference

```
adws/tests/
├── test_external_workflows_integration.py  # Main test file (22 tests)
├── conftest.py                            # Test fixtures (updated)
├── run_integration_tests.sh               # Test runner script
├── .coveragerc                           # Coverage configuration
├── INTEGRATION_TESTS_README.md           # Comprehensive guide
├── INTEGRATION_TESTS_IMPLEMENTATION_SUMMARY.md  # Implementation details
└── INTEGRATION_TESTS_QUICK_START.md      # This file
```

## Success Checklist

- ✅ 22 comprehensive integration tests created
- ✅ 6 test classes covering all scenarios
- ✅ Real subprocess execution (no mocks)
- ✅ Automatic cleanup of temp files
- ✅ Mock worktree with complete structure
- ✅ ADW state fixtures with cleanup
- ✅ Test runner script with coverage
- ✅ Coverage configuration
- ✅ Comprehensive documentation
- ✅ >80% code coverage goal

## Get Help

```bash
# Test runner help
./tests/run_integration_tests.sh --help

# Pytest help
uv run pytest --help

# Read comprehensive guide
cat tests/INTEGRATION_TESTS_README.md

# Read implementation details
cat tests/INTEGRATION_TESTS_IMPLEMENTATION_SUMMARY.md
```

---

**Ready to Test!** 🚀

Start with:
```bash
cd /Users/Warmonger0/tac/tac-webbuilder/adws
chmod +x tests/run_integration_tests.sh
./tests/run_integration_tests.sh --coverage
```
