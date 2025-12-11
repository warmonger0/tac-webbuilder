# Test Error Diagnostic Guide - Session 21

## Problem Summary

Still have approximately 73 test errors after Session 20's fixture setup fixes.

## Session 21 Fixes Applied

### 1. Added Missing conftest.py Files (10 new files)
- `tests/core/conftest.py`
- `tests/services/conftest.py`
- `tests/repositories/conftest.py`
- `tests/utils/conftest.py`
- `tests/adws/conftest.py`
- `tests/manual/conftest.py`
- `tests/core/workflow_history_utils/conftest.py`
- `tests/routes/conftest.py` (with integration fixture loading)

**Expected to fix:** ~15-25 import and fixture discovery errors

### 2. Integration Fixture Loading
- Added `pytest_plugins = ["tests.integration.conftest"]` to `tests/routes/conftest.py`
- Makes `integration_client`, `integration_app`, `db_with_workflows`, and other integration fixtures available to routes tests

**Expected to fix:** ~3-5 fixture not found errors

## Estimated Errors Fixed

From 73 errors → approximately **48-55 remaining errors**

## Error Categorization & Investigation Guide

### Category 1: Module Not Found / Import Errors (~10-15 remaining)

**Location:** tests that import non-existent modules

**To identify:**
```bash
pytest tests/ --tb=short 2>&1 | grep "ModuleNotFoundError\|ImportError" | head -20
```

**Common causes:**
- Module names changed but imports not updated
- Wrong import path (e.g., `from foo.bar` when it should be `from baz.bar`)
- Module doesn't exist yet

**Fix strategy:**
- Check if module exists
- Verify import path matches actual module structure
- Look for module aliases or re-exports

### Category 2: Fixture Not Found Errors (~5-10 remaining)

**Location:** Tests requesting fixtures that don't exist

**To identify:**
```bash
pytest tests/ --tb=short 2>&1 | grep "fixture.*not found" | head -20
```

**Common causes:**
- Fixture defined in wrong conftest (wrong scope level)
- Fixture misspelled
- Fixture in integration conftest but test not in integration directory
- Fixture depends on another fixture that doesn't exist

**Fix strategy:**
- Search for fixture definition
- Check if it's in scope for that test
- Look for typos in fixture names
- Check fixture dependencies

### Category 3: Async/Event Loop Issues (~5-10 remaining)

**Location:** Tests marked with `@pytest.mark.asyncio`

**To identify:**
```bash
pytest tests/ -k "asyncio" --tb=short 2>&1 | head -30
```

**Common causes:**
- Event loop not properly configured
- Mixing async and sync fixtures
- Task cleanup issues
- pytest-asyncio not installed or misconfigured

**Fix strategy:**
- Ensure `asyncio_mode = auto` in pytest.ini (DONE)
- Check event_loop fixture is available
- Verify async fixtures in conftest.py
- Look for proper await syntax

### Category 4: Database/Adapter Issues (~10-15 remaining)

**Location:** Tests that use database fixtures

**To identify:**
```bash
pytest tests/ --tb=short 2>&1 | grep -E "adapter|database|connection" | head -20
```

**Common causes:**
- Database adapter not initialized
- Monkeypatch of DB_PATH not working
- Database table doesn't exist
- SQLite file locking

**Fix strategy:**
- Verify adapter initialization in fixtures
- Check monkeypatch is applied correctly
- Ensure schema creation before using tables
- Look for fixture cleanup issues

### Category 5: Test Logic Errors (~8-15 remaining)

**Location:** Tests that fail during execution, not setup

**To identify:**
```bash
pytest tests/ --tb=short 2>&1 | grep -E "AssertionError|FAILED" | head -20
```

**Common causes:**
- API endpoints not implemented
- Test expectations don't match actual behavior
- Mock responses not set up correctly
- Data validation logic changed

**Fix strategy:**
- Review test expectations
- Check if endpoints exist
- Verify mock setup matches usage
- Compare test code with implementation

### Category 6: External Service Mocking Issues (~5-10 remaining)

**Location:** Tests that mock GitHub, OpenAI, Anthropic APIs

**To identify:**
```bash
pytest tests/ -k "github\|openai\|anthropic" --tb=short 2>&1 | head -30
```

**Common causes:**
- Mock not patching correct module path
- Mock response structure doesn't match actual API
- Mock not properly configured in fixture
- Patch target path incorrect

**Fix strategy:**
- Verify patch target path
- Check mock response structure matches actual API response
- Look for Mock vs MagicMock usage
- Verify async vs sync mock setup

### Category 7: Missing Dependencies (~3-5 remaining)

**Location:** Tests that require specific packages

**To identify:**
```bash
pytest tests/ --tb=short 2>&1 | grep "No module named\|ImportError" | grep -v "tests\." | head -10
```

**Common causes:**
- Package not installed
- Package version incompatible
- Optional dependencies not available

**Fix strategy:**
- Check if package is installed
- Verify package version compatibility
- Consider skip decorators for optional dependencies

## Quick Diagnostic Commands

### Run with detailed error output:
```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server
pytest tests/ -v --tb=long 2>&1 | head -100
```

### Count errors by type:
```bash
pytest tests/ --tb=line -q 2>&1 | \
  tee /tmp/pytest_output.txt | \
  grep -E "ERROR|error|Error" | \
  wc -l
```

### Show first 20 errors:
```bash
pytest tests/ --tb=short -q 2>&1 | grep -E "^ERROR|^tests/" | head -20
```

### Test specific directory:
```bash
# Test core module
pytest tests/core/ -v --tb=short 2>&1 | head -50

# Test services
pytest tests/services/ -v --tb=short 2>&1 | head -50

# Test integration
pytest tests/integration/ -v --tb=short 2>&1 | head -50
```

### Check fixture availability:
```bash
pytest --fixtures 2>&1 | grep -A 2 "integration_client\|integration_app\|db_with_workflows"
```

## Next Steps

1. **Run pytest with Session 21 fixes applied**
   ```bash
   pytest tests/ --tb=line -q 2>&1 | wc -l
   ```
   Should show reduced error count

2. **Categorize remaining errors**
   Run diagnostic commands above to group errors by type

3. **Fix by category**
   Start with most common categories:
   - Module/import errors
   - Fixture errors
   - Database errors

4. **Validate fixes**
   - Run tests for each fixed category
   - Monitor error count trend
   - Commit working fixes

## Files To Review If Issues Persist

- `/Users/Warmonger0/tac/tac-webbuilder/app/server/database/factory.py` - Database adapter initialization
- `/Users/Warmonger0/tac/tac-webbuilder/app/server/tests/conftest.py` - Main test configuration
- `/Users/Warmonger0/tac/tac-webbuilder/app/server/tests/integration/conftest.py` - Integration fixtures
- `/Users/Warmonger0/tac/tac-webbuilder/app/server/pytest.ini` - Pytest configuration

---

**Session 21 Summary:** Added 10 conftest.py files to ensure proper Python path and fixture availability in all test subdirectories. Expected to reduce errors by 15-25, leaving ~48-55 errors to investigate and fix by category.
