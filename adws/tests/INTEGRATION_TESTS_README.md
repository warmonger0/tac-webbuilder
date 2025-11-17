# Integration Tests for External ADW Workflows

This directory contains comprehensive integration tests for the external tool ADW workflows (`adw_test_workflow.py`, `adw_build_workflow.py`, `adw_test_external.py`, `adw_build_external.py`).

## Overview

These integration tests validate the complete workflow execution chain:
- **ADW wrapper → Tool workflow → Result storage**
- **State loading and saving**
- **Subprocess chaining**
- **JSON input/output handling**
- **Error scenarios**
- **Data flow validation**

## Test Structure

### Test File: `test_external_workflows_integration.py`

The integration tests are organized into the following test classes:

1. **TestWorkflowScriptExecution**: Tests standalone workflow scripts
   - JSON input parameter handling
   - CLI argument parsing
   - Invalid input error handling
   - Output format validation

2. **TestExternalADWIntegration**: Tests external ADW wrappers
   - Complete workflow execution flow
   - State loading and result storage
   - Missing worktree handling
   - Missing state handling

3. **TestStatePersistence**: Tests state management
   - Load/save cycle validation
   - Data flow across workflow chain
   - State persistence across subprocesses

4. **TestErrorScenarios**: Tests error handling
   - Invalid state file handling
   - Workflow timeout handling
   - JSON parsing error handling
   - Missing required arguments

5. **TestDataFlow**: Tests data propagation
   - Input parameter propagation
   - Compact JSON output format
   - State persistence across subprocess chain

6. **TestExitCodes**: Tests exit code behavior
   - Successful test exit code (0)
   - Failed test exit code (1)
   - Error exit code (non-zero)

## Key Features

### Real Subprocess Execution
These tests use **real subprocess calls** (not mocked) to validate actual integration behavior:

```python
result = subprocess.run(
    cmd,
    cwd=temp_worktree,
    capture_output=True,
    text=True,
    timeout=60
)
```

### Temporary Directory Isolation
Tests use temporary directories for complete isolation:

```python
@pytest.fixture
def temp_worktree(tmp_path: Path, project_root: Path) -> Path:
    """Create a mock worktree structure for testing."""
    worktree_path = tmp_path / "test_worktree"
    # ... creates complete project structure
```

### Mock Worktree Structure
The `temp_worktree` fixture creates a realistic project structure:

```
test_worktree/
├── app/
│   ├── server/
│   │   ├── core/
│   │   ├── routers/
│   │   ├── tests/
│   │   │   ├── test_sample.py (passing tests)
│   │   │   └── test_failing.py (failing tests)
│   │   └── pytest.ini
│   └── client/
│       ├── src/
│       │   ├── sample.ts (valid TypeScript)
│       │   └── error.ts (TypeScript with errors)
│       ├── tsconfig.json
│       └── package.json
```

### ADW State Fixture
The `adw_state_fixture` creates a complete ADW state:

```python
@pytest.fixture
def adw_state_fixture(tmp_path: Path, temp_worktree: Path, project_root: Path):
    """Create a sample ADW state with worktree path configured."""
    # Creates state in agents/TEST1234/adw_state.json
    # Automatically cleans up after test
```

## Running the Tests

### Run All Integration Tests

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/adws
uv run pytest tests/test_external_workflows_integration.py -v
```

### Run Specific Test Class

```bash
uv run pytest tests/test_external_workflows_integration.py::TestWorkflowScriptExecution -v
```

### Run Specific Test

```bash
uv run pytest tests/test_external_workflows_integration.py::TestWorkflowScriptExecution::test_test_workflow_json_input -v
```

### Run with Coverage

```bash
uv run pytest tests/test_external_workflows_integration.py --cov=adws --cov-report=html
```

### Run Only Integration Tests (marked)

```bash
uv run pytest -m integration -v
```

### Skip Slow Tests

```bash
uv run pytest -m "not slow" -v
```

## Test Coverage Goals

These integration tests target **>80% code coverage** for:

- `/Users/Warmonger0/tac/tac-webbuilder/adws/adw_test_workflow.py`
- `/Users/Warmonger0/tac/tac-webbuilder/adws/adw_build_workflow.py`
- `/Users/Warmonger0/tac/tac-webbuilder/adws/adw_test_external.py`
- `/Users/Warmonger0/tac/tac-webbuilder/adws/adw_build_external.py`

## What Gets Tested

### Complete Workflow Flow
1. Create mock worktree with test files
2. Initialize ADW state with worktree path
3. Execute external ADW wrapper
4. Verify results stored in state
5. Validate exit codes
6. Cleanup automatically

### Error Scenarios
- Missing worktree path
- Invalid state files
- Tool workflow failures
- JSON parsing errors
- Timeout handling
- Missing required arguments

### Data Flow Validation
- Input parameters → Tool → Output
- State persistence across subprocess chain
- Compact JSON output format
- Exit code correctness

## Fixtures Reference

### Core Fixtures (from conftest.py)

- `project_root`: Path to tac-webbuilder directory
- `temp_worktree`: Mock worktree with complete project structure
- `adw_state_fixture`: ADW state with worktree configured (auto-cleanup)
- `sample_test_results`: Sample test results JSON
- `sample_build_results`: Sample build results JSON
- `cleanup_test_adw_states`: Helper to cleanup test ADW states

### Existing Fixtures (also available)

- `temp_directory`: Simple temporary directory
- `project_structure`: Minimal project structure
- `minimal_pytest_report`: Minimal pytest report
- `complex_pytest_report`: Complex pytest report
- `sample_test_failure`: Sample test failure object
- `sample_test_summary`: Sample test summary object
- `sample_coverage`: Sample coverage object

## Integration Test Patterns

### Pattern 1: Complete Workflow Test

```python
def test_complete_workflow(project_root, adw_state_fixture):
    """Test complete workflow execution."""
    external_script = project_root / "adws" / "adw_test_external.py"
    adw_id = adw_state_fixture.adw_id

    # Execute workflow
    cmd = ["uv", "run", str(external_script), "42", adw_id]
    result = subprocess.run(cmd, ...)

    # Verify results stored in state
    state = ADWState.load(adw_id)
    # Assert results...
```

### Pattern 2: Error Scenario Test

```python
def test_error_scenario(project_root):
    """Test error handling."""
    workflow_script = project_root / "adws" / "adw_test_workflow.py"

    # Trigger error condition
    cmd = ["uv", "run", str(workflow_script), "--json-input", "invalid"]
    result = subprocess.run(cmd, ...)

    # Verify error handling
    assert result.returncode != 0
    error_output = json.loads(result.stderr)
    assert error_output["success"] is False
```

### Pattern 3: State Persistence Test

```python
def test_state_persistence(project_root, adw_state_fixture):
    """Test state persists across subprocess calls."""
    # Get initial state
    initial_data = load_state(adw_state_fixture.adw_id)

    # Execute subprocess
    subprocess.run([...])

    # Verify state updated
    final_data = load_state(adw_state_fixture.adw_id)
    assert final_data contains results
```

## Cleanup

All tests automatically clean up after execution:

- Temporary worktree directories (via `tmp_path`)
- ADW state files (via `adw_state_fixture` cleanup)
- Log files (via `tmp_path`)

No manual cleanup required!

## Troubleshooting

### Tests Timeout

If tests timeout, increase the timeout value:

```python
result = subprocess.run(
    cmd,
    timeout=120  # Increase from 60 to 120 seconds
)
```

### State Files Not Cleaned Up

If state files persist after tests, ensure you're using the fixtures with cleanup:

```python
def test_something(adw_state_fixture):  # Use this fixture
    # It auto-cleans up
```

### Import Errors

Ensure you're running from the adws directory:

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/adws
uv run pytest tests/test_external_workflows_integration.py -v
```

## Next Steps

To extend these tests:

1. Add more error scenarios (network failures, permissions, etc.)
2. Add performance/benchmark tests
3. Add parallel execution tests
4. Add retry mechanism tests
5. Add logging validation tests

## Related Documentation

- Test Generator: `tests/TEST_GENERATOR_TESTS_README.md`
- Test Execution: `tests/TEST_EXECUTION_GUIDE.md`
- ADW Documentation: `../README.md`
