# Quick Start Guide

Get the test suite up and running in 5 minutes.

## 1. Install Dependencies (1 minute)

```bash
# Navigate to project
cd /Users/Warmonger0/tac/tac-webbuilder

# Install pytest and plugins
pip install pytest pytest-mock pytest-cov
```

## 2. Run Tests (2 minutes)

```bash
# From project root, run all tests
pytest adws/tests/test_test_runner.py -v

# You should see:
# ====== 53 passed in X.XXs ======
```

## 3. Generate Coverage Report (1 minute)

```bash
# Generate HTML coverage report
pytest adws/tests/test_test_runner.py \
  --cov=adws/adw_modules \
  --cov-report=html

# View the report
open htmlcov/index.html
```

## 4. Explore Documentation (1 minute)

- **README.md** - Full guide with test organization
- **TEST_EXECUTION_GUIDE.md** - Examples and troubleshooting
- **TEST_SUMMARY.md** - Statistics and coverage breakdown
- **VERIFICATION_CHECKLIST.md** - Verify everything works

## Common Commands

### Run Specific Tests
```bash
# Run one test class
pytest adws/tests/test_test_runner.py::TestRunPytestSuccess -v

# Run one test
pytest adws/tests/test_test_runner.py::TestRunPytestSuccess::test_run_pytest_success -v

# Run tests matching pattern
pytest adws/tests/test_test_runner.py -k "success" -v
```

### Debugging
```bash
# Show more detail
pytest adws/tests/test_test_runner.py -vv

# Stop on first failure
pytest adws/tests/test_test_runner.py -x

# Drop into debugger on failure
pytest adws/tests/test_test_runner.py --pdb
```

### Coverage
```bash
# Terminal coverage report
pytest adws/tests/test_test_runner.py --cov=adws/adw_modules --cov-report=term-missing

# Fail if coverage below threshold
pytest adws/tests/test_test_runner.py --cov=adws/adw_modules --cov-fail-under=80
```

## Files Overview

| File | Purpose |
|------|---------|
| `test_test_runner.py` | 53 test methods (main test suite) |
| `conftest.py` | 30+ shared fixtures and configuration |
| `pytest.ini` | Pytest configuration |
| `README.md` | Comprehensive documentation |
| `TEST_EXECUTION_GUIDE.md` | How to run tests with examples |
| `TEST_SUMMARY.md` | Statistics and breakdown |
| `VERIFICATION_CHECKLIST.md` | Verify setup is correct |
| `QUICK_START.md` | This file |

## Test Coverage

### Test Classes (10 total)
- TestTestRunnerInit (3 tests)
- TestRunPytestSuccess (7 tests)
- TestRunPytestFailures (7 tests)
- TestRunVitestSuccess (5 tests)
- TestRunVitestFailures (4 tests)
- TestRunAll (4 tests)
- TestResultToDict (4 tests)
- TestEdgeCases (15+ tests)
- TestIntegration (3 tests)
- TestCommandConstruction (4 tests)

### Target Coverage
- All TestRunner methods: 98%+
- All helper functions: 100%
- All dataclasses: 100%
- **Overall target**: >80%

## Troubleshooting

### Import Error
```bash
# Make sure you're in the project root
cd /Users/Warmonger0/tac/tac-webbuilder
pytest adws/tests/test_test_runner.py -v
```

### Pytest Not Found
```bash
# Install pytest
pip install pytest pytest-mock
```

### Tests Fail to Collect
```bash
# Verify files exist
ls -la adws/tests/

# Should see:
# test_test_runner.py
# conftest.py
# pytest.ini
# __init__.py
```

## Next Steps

1. **Run the tests**: `pytest adws/tests/test_test_runner.py -v`
2. **Check coverage**: `pytest adws/tests/test_test_runner.py --cov=adws/adw_modules --cov-report=html`
3. **Read documentation**: Start with `README.md`
4. **Add to CI/CD**: See `TEST_EXECUTION_GUIDE.md` for examples

## Full Suite Validation

One command to verify everything:

```bash
cd /Users/Warmonger0/tac/tac-webbuilder && \
pytest adws/tests/test_test_runner.py -v --cov=adws/adw_modules --cov-fail-under=80
```

Expected output:
```
====== 53 passed in X.XXs ======
---------- coverage: X.XX% ----------
```

## Support

- **Full Documentation**: See `README.md`
- **Execution Examples**: See `TEST_EXECUTION_GUIDE.md`
- **Statistics**: See `TEST_SUMMARY.md`
- **Verification**: See `VERIFICATION_CHECKLIST.md`

## Key Facts

- **53 tests** covering all functionality
- **>80% code coverage** of target module
- **30+ fixtures** for reusability
- **Complete documentation** included
- **Zero external dependencies** beyond pytest family
- **Fast execution** (~10 seconds full suite)

---

That's it! You're ready to start testing.
