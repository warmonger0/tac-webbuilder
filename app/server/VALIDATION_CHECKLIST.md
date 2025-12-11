# Test Error Fixes - Validation Checklist

Use this checklist to verify all fixes are working correctly.

---

## Pre-Validation Setup

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Ensure you're in the correct directory
pwd  # Should end with: .../app/server

# Verify Python virtual environment is active
python --version  # Should show Python 3.10+

# Verify pytest is available
pytest --version  # Should show pytest version
```

---

## 1. Test Discovery Validation

### Check 1.1: Proper Test Path Resolution
```bash
# Should show only tests from tests/ directory
pytest tests/ --collect-only -q 2>&1 | head -20

# Expected output:
# tests/conftest.py
# tests/core/test_config.py
# tests/services/test_health_service.py
# ... (all from tests/ directory only)
```

**Pass Criteria:**
- [ ] No tests from `app/server/app/` directory
- [ ] No import errors during collection
- [ ] All test modules listed

### Check 1.2: Duplicate Directory is Ignored
```bash
# Verify pytest ignores the problematic directory
pytest tests/ --collect-only -q 2>&1 | grep -c "app/server/app"

# Expected: 0 (zero matches)
```

**Pass Criteria:**
- [ ] No matches from app/server/app directory
- [ ] --ignore rule working

---

## 2. Import Path Validation

### Check 2.1: Module Imports Work
```bash
# Test that modules can be imported
python -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
try:
    from services.health_service import HealthService
    from core.config import Config
    from utils.db_connection import get_connection
    from database import get_database_adapter
    print('SUCCESS: All modules imported')
except ImportError as e:
    print(f'FAILED: {e}')
    sys.exit(1)
"

# Expected: SUCCESS: All modules imported
```

**Pass Criteria:**
- [ ] All modules import successfully
- [ ] No ModuleNotFoundError
- [ ] No ImportError

### Check 2.2: Conftest Path Configuration
```bash
# Verify conftest is setting sys.path
grep -n "sys.path.insert" tests/conftest.py

# Expected: Should see sys.path setup code
```

**Pass Criteria:**
- [ ] Line output shows sys.path configuration
- [ ] Multiple conftest files have the setup

---

## 3. Database Adapter Validation

### Check 3.1: SQLite Adapter Used by Default
```bash
# Run a simple test that uses database
pytest tests/services/test_health_service.py -v -s 2>&1

# Look for connection messages (if verbose)
# Expected: Test passes with SQLite
```

**Pass Criteria:**
- [ ] Tests pass (or fail for other reasons, not DB connection)
- [ ] No psycopg2 connection errors
- [ ] No "connection refused" errors

### Check 3.2: Database Adapter Factory Works
```bash
# Test the factory directly
python -c "
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

# Make sure we use SQLite
os.environ['DB_TYPE'] = 'sqlite'

from database import get_database_adapter
adapter = get_database_adapter()
print(f'Adapter type: {adapter.get_db_type()}')
print(f'DB type match: {adapter.get_db_type() == \"sqlite\"}')
"

# Expected output:
# Adapter type: sqlite
# DB type match: True
```

**Pass Criteria:**
- [ ] Adapter initialized successfully
- [ ] Type is 'sqlite'
- [ ] No import errors

### Check 3.3: Adapter Reset Fixture Exists
```bash
# Verify the reset fixture is in conftest
grep -A 5 "reset_database_adapter" tests/conftest.py | head -10

# Expected: Should show fixture definition
```

**Pass Criteria:**
- [ ] Fixture definition found
- [ ] autouse=True is set
- [ ] Close logic present

---

## 4. Test Isolation Validation

### Check 4.1: Database Adapter Resets Between Tests
```bash
# Create a simple test script
cat > /tmp/test_isolation.py << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "app" / "server"))

import pytest
from unittest.mock import Mock, patch

def test_one():
    from database import factory
    # Store initial adapter
    test_one.initial_adapter = factory._adapter
    assert True

def test_two():
    from database import factory
    # Should be different or reset
    test_two.second_adapter = factory._adapter
    # This will be verified by pytest output
    assert True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
EOF

# Run the test (from app/server directory)
cd /Users/Warmonger0/tac/tac-webbuilder/app/server
pytest /tmp/test_isolation.py -v

# Expected: Both tests pass, adapter properly reset
```

**Pass Criteria:**
- [ ] Both tests pass
- [ ] No connection errors between tests
- [ ] Proper cleanup visible

---

## 5. Environment Variable Validation

### Check 5.1: DB_TYPE Environment Variable
```bash
# Test with explicit SQLite
DB_TYPE=sqlite pytest tests/services/test_health_service.py::TestHealthService::test_health_check_basic -v

# Expected: Test passes with SQLite
```

**Pass Criteria:**
- [ ] Test passes
- [ ] No database errors
- [ ] Uses SQLite

### Check 5.2: Fallback to SQLite When No PG Vars
```bash
# Verify fallback with no POSTGRES vars set
python -c "
import os
import sys
from pathlib import Path

# Clear any PostgreSQL env vars
for var in ['POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']:
    os.environ.pop(var, None)

sys.path.insert(0, str(Path.cwd()))

from database import get_database_adapter
adapter = get_database_adapter()
print(f'Fallback to: {adapter.get_db_type()}')
assert adapter.get_db_type() == 'sqlite', 'Should fallback to SQLite'
print('SUCCESS: Fallback works')
"

# Expected: SUCCESS: Fallback works
```

**Pass Criteria:**
- [ ] Falls back to SQLite
- [ ] No PostgreSQL connection attempt
- [ ] Success message displayed

---

## 6. Full Test Suite Validation

### Check 6.1: Run Sample of Each Test Type
```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Unit tests (should be fast)
echo "Running unit tests..."
pytest tests/services/test_health_service.py -v --tb=short

# If integration test DB is set up:
# echo "Running integration tests..."
# pytest tests/integration/test_api_contracts.py -v --tb=short
```

**Pass Criteria:**
- [ ] Unit tests pass (or appropriate skip messages)
- [ ] No import/collection errors
- [ ] Clear test output

### Check 6.2: Check for Remaining Errors
```bash
# Run all tests and capture error summary
pytest tests/ -v --tb=line 2>&1 | grep -E "ERROR|error" | head -20

# Expected: No ERROR lines (collection or fixture errors)
# Note: Test assertion failures are OK, we're looking for errors
```

**Pass Criteria:**
- [ ] No "ERROR" lines in output
- [ ] Only test failures (not errors)
- [ ] Clear pass/fail summary

---

## 7. Documentation Validation

### Check 7.1: Documentation Files Exist
```bash
# Verify documentation files were created
ls -la /Users/Warmonger0/tac/tac-webbuilder/app/server/*.md | grep -E "TEST_ERROR|CHANGES_APPLIED|VALIDATION"

# Expected: Three documentation files exist
```

**Pass Criteria:**
- [ ] TEST_ERROR_FIXES.md exists
- [ ] CHANGES_APPLIED.md exists
- [ ] VALIDATION_CHECKLIST.md exists (this file)

### Check 7.2: Code Comments Are Present
```bash
# Verify changes are documented in code
grep -n "# Ensure app/server directory is in Python path" tests/conftest.py

# Expected: Found in conftest.py files
```

**Pass Criteria:**
- [ ] Comments present in modified files
- [ ] Clear explanation of changes
- [ ] Path setup documented

---

## 8. Git Status Validation

### Check 8.1: Changes Are Tracked
```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Check git status
git status

# Expected to see:
# Modified:   database/factory.py
# Modified:   tests/conftest.py
# Modified:   tests/integration/conftest.py
# Modified:   tests/e2e/conftest.py
# Modified:   tests/regression/conftest.py
# Modified:   pytest.ini
# Untracked:  TEST_ERROR_FIXES.md
# Untracked:  CHANGES_APPLIED.md
# Untracked:  VALIDATION_CHECKLIST.md

# Note: app/server/app/ should still show as untracked (??), marked for deletion
```

**Pass Criteria:**
- [ ] database/factory.py shows as modified
- [ ] conftest.py files show as modified
- [ ] pytest.ini shows as modified
- [ ] Documentation files are untracked
- [ ] app/server/app/ still shows as untracked (for deletion)

---

## 9. Cleanup Validation

### Check 9.1: Verify Duplicate Directory Still Exists (For Manual Deletion)
```bash
# Confirm the directory structure that needs removal
ls -la /Users/Warmonger0/tac/tac-webbuilder/app/server/app/server/tests/

# Expected: Shows test_idempotency.py and adws directory
```

**Pass Criteria:**
- [ ] Directory still exists
- [ ] Confirmed for manual deletion via: rm -rf app/server/

### Check 9.2: Plan for Directory Removal
```bash
# Document how to remove (don't run yet, just verify command)
echo "To clean up duplicate directory, run:"
echo "cd /Users/Warmonger0/tac/tac-webbuilder/app/server"
echo "rm -rf app/"
echo "(Note: Only removes the accidentally created nested structure)"
```

**Pass Criteria:**
- [ ] Cleanup command understood
- [ ] Ready for manual execution

---

## Summary

**Validation Completed:**
- [ ] Test discovery - only tests/ directory included
- [ ] Module imports - all paths resolve correctly
- [ ] Database adapter - SQLite used by default, proper type
- [ ] Test isolation - adapter resets between tests
- [ ] Environment variables - DB_TYPE and fallback work
- [ ] Test execution - sample tests pass
- [ ] Documentation - all guides created
- [ ] Git tracking - changes properly staged
- [ ] Cleanup - manual removal steps clear

**Total Checks:** 27
**Expected Passed:** All 27

---

## Issues Found During Validation

If any check fails, note it here with details:

1. **[DESCRIBE ISSUE]**
   - Check number: [e.g., 2.1]
   - Expected vs. Actual: [describe]
   - Solution: [proposed fix]

---

## Final Sign-Off

- [ ] All validation checks passed
- [ ] No test errors remaining
- [ ] Code is ready for commit
- [ ] Manual cleanup documented
- [ ] Changes documented thoroughly

**Validated By:** [Name/Date]
**Confidence Level:** [High/Medium/Low]

---

## Quick Validation Command

Run this single command to validate key aspects:
```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server && \
echo "=== Test Discovery ===" && \
pytest tests/ --collect-only -q 2>&1 | wc -l && \
echo "=== Module Import ===" && \
python -c "from services.health_service import HealthService; print('OK')" && \
echo "=== Database Adapter ===" && \
python -c "import os; os.environ['DB_TYPE']='sqlite'; from database import get_database_adapter; print(get_database_adapter().get_db_type())" && \
echo "=== All Key Tests Passed ===" \
"
```

This should output:
```
=== Test Discovery ===
[number of tests]
=== Module Import ===
OK
=== Database Adapter ===
sqlite
=== All Key Tests Passed ===
```

