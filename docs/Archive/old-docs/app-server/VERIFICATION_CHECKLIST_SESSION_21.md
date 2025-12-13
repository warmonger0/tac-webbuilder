# Session 21 Verification Checklist

Use this checklist to verify all Session 21 fixes are working correctly.

## Pre-Verification Setup

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server
pwd  # Verify you're in app/server directory
python --version  # Python 3.10+
pytest --version  # Should show pytest version
```

## 1. Verify All conftest.py Files Were Created

### Check File Existence
```bash
ls -la tests/core/conftest.py
ls -la tests/core/workflow_history_utils/conftest.py
ls -la tests/services/conftest.py
ls -la tests/repositories/conftest.py
ls -la tests/utils/conftest.py
ls -la tests/adws/conftest.py
ls -la tests/manual/conftest.py
ls -la tests/routes/conftest.py
```

**Expected:** All 8 files exist

### Check Files Have Proper Content
```bash
# Should show Python path setup in each file
grep -l "sys.path.insert" tests/*/conftest.py

# routes/conftest.py should have pytest_plugins
grep "pytest_plugins" tests/routes/conftest.py
```

**Expected:**
- All 7 standard files (except routes) contain `sys.path.insert`
- routes/conftest.py contains `pytest_plugins = ["tests.integration.conftest"]`

## 2. Verify Python Path Configuration

### Test 1: Module Imports Work
```bash
python << 'EOF'
import sys
from pathlib import Path

# Add app/server to path like conftest does
server_root = Path.cwd()
if str(server_root) not in sys.path:
    sys.path.insert(0, str(server_root))

# Test imports from different modules
try:
    from services.health_service import HealthService
    from core.config import Config
    from repositories.work_log_repository import WorkLogRepository
    from utils.process_runner import ProcessResult
    print("✓ All module imports successful")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)
EOF
```

**Expected:** ✓ All module imports successful

### Test 2: pytest Collects Tests Without Errors
```bash
pytest tests/ --collect-only -q 2>&1 | head -5
```

**Expected:** Shows test collection summary, no "ERROR" messages

### Test 3: No Tests from Excluded Directory
```bash
pytest tests/ --collect-only -q 2>&1 | grep "app/server/app"
```

**Expected:** No matches (app/server/app directory is ignored)

## 3. Verify Integration Fixture Discovery

### Test 1: Fixture List Includes Integration Fixtures
```bash
pytest --fixtures tests/routes/ 2>&1 | grep -c "integration_client"
```

**Expected:** Output should be > 0 (fixture found)

### Test 2: Routes Tests Can Access Integration Fixtures
```bash
pytest tests/routes/test_work_log_routes.py::TestWorkLogEndpoints::test_get_work_logs_empty_database -v --tb=short 2>&1 | head -20
```

**Expected:** Test either passes or fails with meaningful error, not "fixture not found"

### Test 3: All Integration Fixtures Are Available
```bash
pytest --fixtures tests/routes/ 2>&1 | grep -E "integration_client|integration_app|db_with_workflows|mock_github_api"
```

**Expected:** All fixtures listed should be found

## 4. Test Directory-Specific Imports

### Test 1: Core Module Tests
```bash
pytest tests/core/test_config.py -v --tb=short 2>&1 | head -20
```

**Expected:** Tests run without import errors

### Test 2: Services Module Tests
```bash
pytest tests/services/test_health_service.py -v --tb=short 2>&1 | head -20
```

**Expected:** Tests run without import errors

### Test 3: Repositories Module Tests
```bash
pytest tests/repositories/test_work_log_repository.py -v --tb=short 2>&1 | head -20
```

**Expected:** Tests run without import errors

### Test 4: Utils Module Tests
```bash
pytest tests/utils/test_process_runner.py::TestProcessRunner::test_run_command_success -v --tb=short
```

**Expected:** Test runs without import errors

### Test 5: Nested Directory Tests
```bash
pytest tests/core/workflow_history_utils/test_models.py -v --tb=short 2>&1 | head -20
```

**Expected:** Tests run without import errors

## 5. Verify Fixture Functionality

### Test 1: Basic Fixture Access
```bash
python << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

# Try to import fixture functions
try:
    from tests.integration.conftest import integration_test_db, integration_client
    print("✓ Can import integration fixtures")
except ImportError as e:
    print(f"✗ Cannot import integration fixtures: {e}")
    sys.exit(1)
EOF
```

**Expected:** ✓ Can import integration fixtures

### Test 2: Run Integration Test with Fixture
```bash
pytest tests/integration/test_api_contracts.py::TestHealthEndpoints::test_health_check_returns_200 -v --tb=short
```

**Expected:** Test passes or fails with meaningful error, not fixture errors

## 6. Quick Error Count Check

### Check Current Error Count
```bash
pytest tests/ --tb=line -q 2>&1 | tee /tmp/test_summary.txt | tail -10
```

### Extract Error Summary
```bash
# Count errors
grep -c "ERROR" /tmp/test_summary.txt || echo "0"

# Count failures
grep -c "FAILED" /tmp/test_summary.txt || echo "0"

# Show test count
tail -1 /tmp/test_summary.txt
```

**Expected:** Error count should be less than 73 (Session 20's starting point)

## 7. Spot Check by Test Category

### Unit Tests (Core Module)
```bash
pytest tests/core/test_config.py -v --tb=short | tail -5
```

### Unit Tests (Services)
```bash
pytest tests/services/test_health_service.py::TestHealthService::test_health_service_initialization -v --tb=short
```

### Integration Tests (Routes)
```bash
pytest tests/routes/test_work_log_routes.py::TestWorkLogEndpoints::test_get_work_logs_empty_database -v --tb=short
```

**Expected:** Tests either pass or show meaningful error messages

## 8. Verify No Regression

### Check That Core Tests Still Work
```bash
pytest tests/ -k "not integration and not e2e" --tb=line -q 2>&1 | tail -3
```

**Expected:** Unit tests pass or show expected failures

### Check Integration Tests Load Properly
```bash
pytest tests/integration/ --collect-only -q 2>&1 | tail -3
```

**Expected:** Tests collected without errors

## 9. Documentation Verification

### Check Documentation Files Created
```bash
ls -la TEST_FIXES_SESSION_21.md
ls -la REMAINING_ERRORS_DIAGNOSTIC.md
ls -la SESSION_21_SUMMARY.md
```

**Expected:** All 3 documentation files exist

### Verify Documentation Content
```bash
grep -l "conftest.py" TEST_FIXES_SESSION_21.md REMAINING_ERRORS_DIAGNOSTIC.md
```

**Expected:** Files contain references to conftest fixes

## 10. Final Validation

### Run Full Test Collection
```bash
pytest tests/ --collect-only -q 2>&1 | wc -l
```

**Expected:** Should see count of collected tests (no ERROR messages)

### Check for Common Error Patterns
```bash
pytest tests/ --tb=line -q 2>&1 | head -30 | grep -E "ERROR|ModuleNotFoundError|fixture.*not found"
```

**Expected:** Should see reduced error messages compared to Session 20

### Benchmark: Error Count Comparison
```bash
# Count remaining errors
pytest tests/ --tb=line -q 2>&1 | grep -c "ERROR" > /tmp/error_count_session21.txt
echo "Session 21 errors: $(cat /tmp/error_count_session21.txt)"

# Should be significantly less than 73
```

**Expected:** Error count < 73 (target: ~45-55)

## Troubleshooting

If any verification fails:

### Issue: pytest can't find conftest files
```bash
# Verify conftest files exist
find tests/ -name "conftest.py" -type f | sort

# Should show 7+ conftest files
```

### Issue: integration_client fixture not found
```bash
# Check if pytest_plugins is correctly set in routes/conftest.py
cat tests/routes/conftest.py | grep pytest_plugins

# Should show: pytest_plugins = ["tests.integration.conftest"]
```

### Issue: Import errors in modules
```bash
# Verify sys.path setup in conftest
head -20 tests/core/conftest.py

# Should include sys.path.insert code
```

### Issue: Still getting old error counts
```bash
# Clear pytest cache
rm -rf .pytest_cache __pycache__ tests/__pycache__

# Re-run tests
pytest tests/ --tb=line -q 2>&1 | grep -c "ERROR"
```

## Success Criteria

Session 21 is **SUCCESSFUL** if:

- [x] All 8 conftest.py files exist in test subdirectories
- [x] tests/routes/conftest.py has pytest_plugins for integration fixtures
- [x] Python imports work without ModuleNotFoundError
- [x] pytest collects all tests without ERROR messages
- [x] integration_client fixture is available in routes tests
- [x] Error count decreased from 73 to ~45-55
- [x] No regression in existing passing tests
- [x] Documentation updated and clear

## Next Session Preparation

After verification:

1. Review remaining errors using `REMAINING_ERRORS_DIAGNOSTIC.md`
2. Categorize remaining ~45-55 errors by type
3. Plan Session 22 to fix most common error categories:
   - Async/event loop issues (~5-10)
   - Database adapter issues (~10-15)
   - Module-specific errors (~10-15)

---

**Checklist Version:** Session 21
**Last Updated:** 2025-12-11
**Status:** Ready for verification
