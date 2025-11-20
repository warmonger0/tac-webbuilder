# Quick Start: Running GitHub Issue Flow E2E Tests

## Prerequisites

Ensure you're in the server directory:
```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server
```

## Basic Test Execution

### Run All GitHub Issue Flow Tests
```bash
pytest tests/e2e/test_github_issue_flow.py -v
```

### Run with Detailed Output
```bash
pytest tests/e2e/test_github_issue_flow.py -v -s
```

## Run Specific Test Categories

### Core User Journey Tests (TC-001 to TC-005)
```bash
pytest tests/e2e/test_github_issue_flow.py::TestCompleteGitHubIssueFlow -v
```

### Edge Case Tests
```bash
pytest tests/e2e/test_github_issue_flow.py::TestGitHubIssueFlowEdgeCases -v
```

### Data Persistence Tests
```bash
pytest tests/e2e/test_github_issue_flow.py::TestGitHubIssueFlowDataPersistence -v
```

### Performance Tests (Marked as @slow)
```bash
pytest tests/e2e/test_github_issue_flow.py::TestGitHubIssueFlowPerformance -v
```

## Run Individual Test Cases

### TC-001: Happy Path
```bash
pytest tests/e2e/test_github_issue_flow.py::TestCompleteGitHubIssueFlow::test_complete_nl_request_to_issue_creation -v
```

### TC-002: Invalid Input Handling
```bash
pytest tests/e2e/test_github_issue_flow.py::TestCompleteGitHubIssueFlow::test_invalid_nl_input_handling -v
```

### TC-003: Preview Not Found
```bash
pytest tests/e2e/test_github_issue_flow.py::TestCompleteGitHubIssueFlow::test_preview_not_found -v
```

### TC-004: Duplicate Confirmation
```bash
pytest tests/e2e/test_github_issue_flow.py::TestCompleteGitHubIssueFlow::test_duplicate_confirmation_handling -v
```

### TC-005: Cost Estimate Accuracy
```bash
pytest tests/e2e/test_github_issue_flow.py::TestCompleteGitHubIssueFlow::test_cost_estimate_accuracy -v
```

## Advanced Options

### Run with Coverage Report
```bash
pytest tests/e2e/test_github_issue_flow.py --cov=services.github_issue_service --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html
```

### Run with Markers

#### Only E2E tests (exclude slow)
```bash
pytest tests/e2e/test_github_issue_flow.py -m "e2e and not slow"
```

#### Only slow tests
```bash
pytest tests/e2e/test_github_issue_flow.py -m "slow"
```

### Run with Parallel Execution (if pytest-xdist installed)
```bash
pytest tests/e2e/test_github_issue_flow.py -n auto
```

### Stop on First Failure
```bash
pytest tests/e2e/test_github_issue_flow.py -x
```

### Run in Quiet Mode (Less Output)
```bash
pytest tests/e2e/test_github_issue_flow.py -q
```

## Debugging

### Run with PDB on Failure
```bash
pytest tests/e2e/test_github_issue_flow.py --pdb
```

### Show Local Variables on Failure
```bash
pytest tests/e2e/test_github_issue_flow.py -l
```

### Increase Verbosity for Debugging
```bash
pytest tests/e2e/test_github_issue_flow.py -vv
```

### Show Print Statements
```bash
pytest tests/e2e/test_github_issue_flow.py -v -s
```

## Test Output Examples

### Successful Test Run
```
tests/e2e/test_github_issue_flow.py::TestCompleteGitHubIssueFlow::test_complete_nl_request_to_issue_creation PASSED [20%]
tests/e2e/test_github_issue_flow.py::TestCompleteGitHubIssueFlow::test_invalid_nl_input_handling PASSED [40%]
tests/e2e/test_github_issue_flow.py::TestCompleteGitHubIssueFlow::test_preview_not_found PASSED [60%]
tests/e2e/test_github_issue_flow.py::TestCompleteGitHubIssueFlow::test_duplicate_confirmation_handling PASSED [80%]
tests/e2e/test_github_issue_flow.py::TestCompleteGitHubIssueFlow::test_cost_estimate_accuracy PASSED [100%]

============================= 5 passed in 2.34s =============================
```

### Failed Test Example
```
tests/e2e/test_github_issue_flow.py::TestCompleteGitHubIssueFlow::test_complete_nl_request_to_issue_creation FAILED [20%]

================================= FAILURES ==================================
________ TestCompleteGitHubIssueFlow.test_complete_nl_request_to_issue_creation ________

    def test_complete_nl_request_to_issue_creation(self, e2e_test_client, ...):
>       assert submit_response.status_code == 200
E       assert 500 == 200

tests/e2e/test_github_issue_flow.py:123: AssertionError
============================= 1 failed in 0.45s =============================
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: E2E Tests - GitHub Issue Flow

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd app/server
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      - name: Run GitHub Issue Flow E2E Tests
        run: |
          cd app/server
          pytest tests/e2e/test_github_issue_flow.py -v --cov=services.github_issue_service
```

## Troubleshooting

### Common Issues

#### Import Errors
**Problem**: `ModuleNotFoundError: No module named 'services'`

**Solution**: Ensure you're in the correct directory:
```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/e2e/test_github_issue_flow.py -v
```

#### Fixture Not Found
**Problem**: `fixture 'e2e_test_client' not found`

**Solution**: Ensure conftest.py files are present:
```bash
ls tests/conftest.py
ls tests/e2e/conftest.py
```

#### Mock Not Working
**Problem**: Tests failing due to real API calls

**Solution**: Verify mocks are properly patched. Check test fixtures are being used.

#### Database Errors
**Problem**: `sqlite3.OperationalError: no such table`

**Solution**: E2E tests should use `e2e_database` fixture which creates schema automatically.

## Performance Monitoring

### Run with Timing Information
```bash
pytest tests/e2e/test_github_issue_flow.py -v --durations=10
```

This shows the 10 slowest tests.

### Expected Timing
- Individual tests: 0.1-1 second
- Full suite: 2-10 seconds
- Slow tests: May take up to 5 seconds

## Test Maintenance

### After Updating API Endpoints

1. Run tests to identify failures:
```bash
pytest tests/e2e/test_github_issue_flow.py -v
```

2. Update test expectations to match new API contract

3. Verify all tests pass:
```bash
pytest tests/e2e/test_github_issue_flow.py -v
```

### After Updating Data Models

1. Check which tests fail:
```bash
pytest tests/e2e/test_github_issue_flow.py -v
```

2. Update assertions in tests to match new model structure

3. Verify cost estimate validations still correct

## Best Practices

### Before Committing Code

Run full E2E test suite:
```bash
pytest tests/e2e/test_github_issue_flow.py -v
```

Ensure all tests pass before pushing.

### When Adding New Features

1. Add new test cases to appropriate test class
2. Follow existing patterns and fixtures
3. Add `@pytest.mark.e2e` decorator
4. Document test scenario in docstring

### Regular Maintenance

Run tests regularly during development:
```bash
# Quick check
pytest tests/e2e/test_github_issue_flow.py -q

# Full validation
pytest tests/e2e/test_github_issue_flow.py -v --cov=services.github_issue_service
```

## Additional Resources

- **Full Test Documentation**: `TEST_GITHUB_ISSUE_FLOW_SUMMARY.md`
- **Test Infrastructure**: `../INFRASTRUCTURE_SUMMARY.md`
- **E2E Testing Guide**: `../README.md`

## Quick Reference Card

| Command | Purpose |
|---------|---------|
| `pytest tests/e2e/test_github_issue_flow.py -v` | Run all tests verbose |
| `pytest ... -m "e2e and not slow"` | Skip slow tests |
| `pytest ... --pdb` | Debug on failure |
| `pytest ... --cov=services.github_issue_service` | With coverage |
| `pytest ... -x` | Stop on first failure |
| `pytest ... -k test_complete` | Run tests matching pattern |
| `pytest ... --durations=10` | Show slowest tests |

## Questions?

Check test file for inline documentation:
```bash
cat tests/e2e/test_github_issue_flow.py
```

Each test includes detailed docstrings explaining the scenario and validations.
