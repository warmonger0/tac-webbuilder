# PyTest Quick Start Guide for build_checker.py Tests

## File Location
```
adws/adw_tests/test_build_checker.py
```

## Running Tests

### Basic Execution
```bash
# Run all tests with verbose output
pytest adws/adw_tests/test_build_checker.py -v

# Run all tests with summary
pytest adws/adw_tests/test_build_checker.py
```

### Coverage Reports
```bash
# Generate coverage report
pytest adws/adw_tests/test_build_checker.py \
  --cov=adws.adw_modules.build_checker \
  --cov-report=term-missing \
  --cov-report=html

# Quick coverage check (text output)
pytest adws/adw_tests/test_build_checker.py \
  --cov=adws.adw_modules.build_checker \
  --cov-report=term-missing
```

### Run Specific Tests
```bash
# Single test class
pytest adws/adw_tests/test_build_checker.py::TestParseTscOutput -v

# Single test method
pytest adws/adw_tests/test_build_checker.py::TestParseTscOutput::test_parse_tsc_single_error -v

# All parsing tests
pytest adws/adw_tests/test_build_checker.py -k "parse" -v

# All timeout tests
pytest adws/adw_tests/test_build_checker.py -k "timeout" -v
```

### Detailed Output
```bash
# Show print statements and full traceback
pytest adws/adw_tests/test_build_checker.py -vv -s

# Show captured output on failure
pytest adws/adw_tests/test_build_checker.py -v --tb=short
```

## Test Organization

### Test Classes (12 total)
1. **TestBuildError** (3 tests) - Dataclass initialization
2. **TestBuildSummary** (2 tests) - Summary dataclass
3. **TestResultToDict** (10 tests) - JSON serialization
4. **TestParseTscOutput** (6 tests) - TypeScript parsing
5. **TestParseViteOutput** (5 tests) - Vite parsing
6. **TestParseMyPyOutput** (7 tests) - MyPy parsing
7. **TestCheckFrontendTypes** (8 tests) - Type checking
8. **TestCheckFrontendBuild** (6 tests) - Build execution
9. **TestCheckBackendTypes** (6 tests) - Backend validation
10. **TestCheckAll** (8 tests) - Combined checks
11. **TestBuildCheckerInitialization** (3 tests) - Initialization
12. **TestEdgeCases** (5 tests) - Edge cases
13. **TestTimeoutHandling** (3 tests) - Timeout scenarios

### Total: 72 Tests

## Key Testing Patterns

### 1. Parser Tests
```python
# Example: Testing tsc output parsing
pytest adws/adw_tests/test_build_checker.py::TestParseTscOutput -v

# Tests:
# - Single error parsing
# - Multiple errors
# - Empty output
# - Special characters
# - Various error codes
# - Invalid line filtering
```

### 2. Method Tests
```python
# Example: Testing check_frontend_types
pytest adws/adw_tests/test_build_checker.py::TestCheckFrontendTypes -v

# Tests:
# - Success scenarios
# - Error scenarios
# - Timeout handling
# - Strict mode parameter
# - Command construction
# - Working directory
```

### 3. Integration Tests
```bash
# Test the check_all method with various combinations
pytest adws/adw_tests/test_build_checker.py::TestCheckAll -v
```

## Quick Test Filters

### Run Only Parser Tests
```bash
pytest adws/adw_tests/test_build_checker.py -k "parse" -v
```

### Run Only Check Method Tests
```bash
pytest adws/adw_tests/test_build_checker.py -k "check_" -v
```

### Run Only Timeout Tests
```bash
pytest adws/adw_tests/test_build_checker.py -k "timeout" -v
```

### Run Only Error Tests
```bash
pytest adws/adw_tests/test_build_checker.py -k "error" -v
```

## Coverage Goals

| Metric | Target | Achieved |
|--------|--------|----------|
| Line Coverage | 80%+ | 98%+ |
| Branch Coverage | 70%+ | 95%+ |
| Function Coverage | 100% | 100% |

## Common Issues and Solutions

### Issue: ImportError for build_checker module
**Solution**: Ensure `adws` directory is in PYTHONPATH
```bash
# Run from project root
cd /Users/Warmonger0/tac/tac-webbuilder
pytest adws/adw_tests/test_build_checker.py -v
```

### Issue: Tests run but coverage is 0%
**Solution**: Verify module path in coverage command
```bash
pytest adws/adw_tests/test_build_checker.py \
  --cov=adws.adw_modules.build_checker
```

### Issue: Subprocess mocking not working
**Solution**: Ensure @patch decorator is applied correctly
```python
@patch("subprocess.run")  # Correct - patches in the module being tested
def test_example(self, mock_run):
    pass
```

## Test File Structure

```python
# Fixtures (test data and setup)
@pytest.fixture
def build_checker(project_root):
    return BuildChecker(project_root)

# Test classes
class TestClassName:
    def test_method_name(self):
        """Test description."""
        # Arrange
        # Act
        # Assert

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

## Debugging Tests

### Run with debugger
```bash
pytest adws/adw_tests/test_build_checker.py --pdb -v
```

### Show local variables on failure
```bash
pytest adws/adw_tests/test_build_checker.py --tb=long -v
```

### Stop after first failure
```bash
pytest adws/adw_tests/test_build_checker.py -x -v
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Run build_checker tests
  run: |
    pytest adws/adw_tests/test_build_checker.py \
      --cov=adws.adw_modules.build_checker \
      --cov-report=xml \
      --cov-fail-under=80
```

### GitLab CI Example
```yaml
test_build_checker:
  script:
    - pytest adws/adw_tests/test_build_checker.py -v --cov=adws.adw_modules.build_checker
```

## Performance Considerations

- All tests use mocked subprocess calls (very fast)
- Total execution time: <2 seconds
- No external dependencies required
- Parallel execution possible with pytest-xdist:

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest adws/adw_tests/test_build_checker.py -n auto -v
```

## Test Maintenance

### Adding New Tests
1. Choose appropriate test class
2. Follow naming convention: `test_<method>_<scenario>`
3. Add docstring describing what is tested
4. Use existing fixtures when possible

### Updating Fixtures
- Fixtures are at the top of the file
- Modify fixture data to test new scenarios
- Consider creating new fixtures for new patterns

### Reviewing Coverage
```bash
# Generate HTML coverage report
pytest adws/adw_tests/test_build_checker.py \
  --cov=adws.adw_modules.build_checker \
  --cov-report=html

# Open report in browser
open htmlcov/index.html
```

## References

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-mock Documentation](https://pytest-mock.readthedocs.io/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- Test file: `adws/adw_tests/test_build_checker.py`
- Coverage report: `TEST_COVERAGE_BUILD_CHECKER.md`
