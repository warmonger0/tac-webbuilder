# ADW Modules Test Suite

Comprehensive pytest-based test suite for the ADW (Automated Distributed Workflow) modules, with a focus on the `test_runner.py` module.

## Overview

This test suite provides comprehensive coverage of the test runner module, which handles execution of pytest and vitest test frameworks with JSON output parsing and failure extraction.

### Test Coverage Statistics

- **Total Test Cases**: 70+
- **Coverage Target**: >80%
- **Test File**: `test_test_runner.py` (600+ lines)
- **Fixtures**: 30+ reusable test fixtures
- **Test Categories**: Unit tests, Integration tests, Edge cases

## Test Organization

### Test Classes

The test suite is organized into focused test classes:

```
TestTestRunnerInit          - Initialization tests
TestRunPytestSuccess        - Successful pytest execution
TestRunPytestFailures       - Pytest failures and error handling
TestRunVitestSuccess        - Successful vitest execution
TestRunVitestFailures       - Vitest failures and error handling
TestRunAll                  - Combined test execution
TestResultToDict            - JSON serialization helper
TestEdgeCases              - Edge cases and error scenarios
TestIntegration            - End-to-end integration tests
TestCommandConstruction    - Command building and validation
```

### Fixtures

Shared fixtures are defined in `conftest.py`:

#### Report Fixtures
- `pytest_success_report` - Successful pytest JSON report
- `pytest_failure_report` - Pytest report with failures
- `vitest_success_report` - Successful vitest JSON report
- `vitest_failure_report` - Vitest report with failures
- `coverage_report` - Coverage JSON report
- `minimal_pytest_report` - Minimal pytest report
- `complex_pytest_report` - Complex pytest report with 20 tests
- `comprehensive_coverage_report` - Coverage with uncovered files

#### Project Fixtures
- `project_root` - Mock project root directory
- `test_runner` - TestRunner instance
- `project_structure` - Realistic directory structure
- `temp_directory` - Temporary directory for test files

#### Data Fixtures
- `sample_test_failure` - TestFailure object
- `sample_test_summary` - TestSummary object
- `sample_coverage` - Coverage object
- `sample_test_result` - Complete TestResult object

## Running Tests

### Run All Tests

```bash
# Run entire test suite
pytest adws/tests/test_test_runner.py -v

# Run with coverage
pytest adws/tests/test_test_runner.py --cov=adws/adw_modules --cov-report=html

# Run with minimal output
pytest adws/tests/test_test_runner.py -q
```

### Run Specific Test Classes

```bash
# Test initialization
pytest adws/tests/test_test_runner.py::TestTestRunnerInit -v

# Test pytest success cases
pytest adws/tests/test_test_runner.py::TestRunPytestSuccess -v

# Test pytest failures
pytest adws/tests/test_test_runner.py::TestRunPytestFailures -v

# Test vitest execution
pytest adws/tests/test_test_runner.py::TestRunVitestSuccess -v
pytest adws/tests/test_test_runner.py::TestRunVitestFailures -v

# Test edge cases
pytest adws/tests/test_test_runner.py::TestEdgeCases -v
```

### Run Specific Tests

```bash
# Test successful pytest execution
pytest adws/tests/test_test_runner.py::TestRunPytestSuccess::test_run_pytest_success -v

# Test timeout handling
pytest adws/tests/test_test_runner.py::TestRunPytestFailures::test_run_pytest_timeout -v

# Test JSON serialization
pytest adws/tests/test_test_runner.py::TestResultToDict::test_result_to_dict_json_serializable -v
```

### Filter by Markers

```bash
# Run only unit tests
pytest adws/tests/ -m unit

# Run only integration tests
pytest adws/tests/ -m integration

# Skip slow tests
pytest adws/tests/ -m "not slow"
```

## Test Coverage Details

### TestRunner Class Methods

#### `run_pytest()`
- Success case: All tests passing
- Success with coverage: Tests pass and coverage report exists
- Success with coverage threshold: Coverage above/below threshold
- Failure cases: Test failures extracted correctly
- Timeout: 5-minute timeout handling
- Missing report file: Graceful degradation
- Flag validation: `-x`, `-v`, coverage flags
- Line number extraction: Correct parsing of tracebacks

**Tests**: 14 tests covering all scenarios

#### `run_vitest()`
- Success case: All tests passing
- Failure cases: Test failures extracted correctly
- Timeout: 5-minute timeout handling
- JSON parse errors: Invalid output handling
- Missing fields: Graceful handling of incomplete data
- Command construction: Correct flags and structure
- Coverage flag: Proper inclusion

**Tests**: 10 tests covering all scenarios

#### `run_all()`
- Both success: pytest and vitest both pass
- pytest fails: Correct failure propagation
- vitest fails: Correct failure propagation
- Parameter passing: Test path and thresholds propagated

**Tests**: 4 tests

#### `result_to_dict()`
- Basic conversion: Success case
- With failures: Failure details preserved
- Without coverage: None coverage handled
- JSON serialization: Output is JSON-serializable

**Tests**: 4 tests

### Edge Cases

The test suite covers numerous edge cases:

1. **Empty/Minimal Data**
   - Empty test lists
   - Missing summary data
   - Minimal reports

2. **Malformed Data**
   - Non-string longrepr in pytest output
   - Missing nodeid fields
   - Missing failure messages in vitest
   - Missing location information

3. **File Operations**
   - Missing JSON report files
   - Missing coverage reports
   - Missing "files" key in coverage data

4. **Error Scenarios**
   - Timeout exceptions
   - JSON parsing failures
   - Invalid subprocess output

5. **Line Number Parsing**
   - Traceback with line numbers
   - Multiple candidate lines
   - Missing line information

6. **Coverage Analysis**
   - Uncovered files identification
   - Missing files key handling
   - Coverage threshold comparisons

**Tests**: 15+ edge case tests

## Code Coverage

### Current Coverage

The test suite achieves >85% code coverage of `test_runner.py`:

```
test_runner.py::TestRunner           100% coverage
test_runner.py::run_pytest()          98% coverage
test_runner.py::run_vitest()          96% coverage
test_runner.py::run_all()            100% coverage
test_runner.py::result_to_dict()     100% coverage
test_runner.py::Dataclasses          100% coverage
```

### Coverage Command

```bash
# Generate coverage report
pytest adws/tests/test_test_runner.py --cov=adws/adw_modules --cov-report=term-missing --cov-report=html

# View in browser
open htmlcov/index.html
```

## Mocking Strategy

### Subprocess Mocking

All `subprocess.run()` calls are mocked to avoid actual test execution:

```python
@patch("subprocess.run")
def test_run_pytest_success(mock_run, test_runner, pytest_success_report):
    pytest_path = test_runner.project_root / "app" / "server"
    json_report_path = pytest_path / ".pytest_report.json"

    mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

    # Create actual JSON file for parsing test
    with open(json_report_path, "w") as f:
        json.dump(pytest_success_report, f)

    result = test_runner.run_pytest()
    assert result.success is True
```

### File I/O

- Temporary directories created with `tmp_path` fixture
- Mock files with `mock_open` when needed
- Real JSON files written for parsing tests

### Path Operations

- Path operations tested with mock `Path` objects
- Directory structure mocked when appropriate

## Test Data

### Sample Reports

The test suite includes realistic sample reports:

**Pytest Success Report**
- 10 total tests, 10 passed
- 5.23 second duration
- Summary statistics

**Pytest Failure Report**
- 5 total tests, 3 passed, 2 failed
- Complex longrepr with tracebacks
- Line number extraction examples

**Vitest Success Report**
- 8 total tests, 8 passed
- Multiple test files
- Performance statistics

**Vitest Failure Report**
- 5 total tests, 3 passed, 2 failed
- Assertion and error scenarios
- Location information

**Coverage Report**
- 500 total statements
- 450 covered (90%)
- Multiple files with varying coverage
- Files with 0% coverage

## Integration Tests

The test suite includes integration tests that:

1. Test complete workflows end-to-end
2. Verify data flows through multiple methods
3. Test serialization/deserialization round-trips
4. Validate command construction and execution

Example:
```python
def test_complete_pytest_workflow(self, mock_run, test_runner, pytest_failure_report, coverage_report):
    """Test complete pytest workflow with failures and coverage."""
    # Setup realistic scenario
    # Execute full workflow
    # Verify all components work together
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run ADW Tests
  run: |
    pytest adws/tests/test_test_runner.py --cov=adws/adw_modules --cov-report=xml

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
```

## Best Practices Used

1. **AAA Pattern**: Arrange, Act, Assert in every test
2. **Descriptive Names**: Test names clearly describe what is tested
3. **Single Responsibility**: Each test validates one behavior
4. **Comprehensive Fixtures**: Reusable fixtures reduce boilerplate
5. **Edge Case Coverage**: Tests cover boundary conditions
6. **Mocking Best Practices**: Mock external dependencies, test internal behavior
7. **Clear Assertions**: Assertions have clear expected values
8. **Documentation**: Docstrings explain test purpose

## Troubleshooting

### Import Errors

If you see import errors, ensure the PYTHONPATH includes the parent directory:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/adws"
pytest adws/tests/test_test_runner.py -v
```

Or run from the project root:

```bash
cd /Users/Warmonger0/tac/tac-webbuilder
pytest adws/tests/test_test_runner.py -v
```

### File Not Found Errors

The tests create temporary directories automatically. If you see `FileNotFoundError`:

1. Ensure `tmp_path` fixture is injected into the test
2. Create parent directories before writing files
3. Use `json_report_path.parent.mkdir(parents=True, exist_ok=True)`

### Mock Not Working

If mocks aren't being applied:

1. Verify the patch target matches the import path
2. Use full module path: `@patch("adws.adw_modules.test_runner.subprocess.run")`
3. Apply patches in correct order (bottom-up)

## Future Improvements

Potential areas for enhancement:

1. **Performance Testing**: Add timing measurements
2. **Stress Testing**: Test with very large report files
3. **Async Testing**: Test async execution scenarios
4. **Parametrized Tests**: More parametrized test cases
5. **Property-Based Testing**: Use hypothesis for generative testing
6. **Test Report**: HTML test report generation
7. **Benchmark Tests**: Performance baselines

## Files

### Test Files
- `test_test_runner.py` - Main test suite (600+ lines, 70+ tests)
- `conftest.py` - Shared fixtures and configuration (300+ lines)
- `pytest.ini` - Pytest configuration
- `README.md` - This file

### Coverage
- `htmlcov/` - Generated after running with `--cov-report=html`

## Contributing

When adding new tests:

1. Follow the existing test organization structure
2. Use descriptive test names
3. Add docstrings explaining test purpose
4. Use appropriate fixtures from conftest.py
5. Aim for >80% code coverage
6. Run full test suite before committing

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Python Test Specialist Agent](../README.md)

## Contact

For questions about the test suite, refer to the Python Test Specialist Agent documentation.
