# Task: Cleanup Phase 1 - Fix Pre-existing Test Failures

## Context
I'm working on the tac-webbuilder project. The PostgreSQL migration is complete and successful. Now we're cleaning up pre-existing test failures that affect both SQLite and PostgreSQL equally.

## Objective
Fix ~146 pre-existing test failures to improve test pass rate from 81% to 85-90%:
1. Fix database initialization errors (100 errors - highest impact)
2. Fix SQL injection test failures (10-15 failures)
3. Investigate and categorize remaining test failures (30-40 failures)

## Background Information
- **Phase:** Cleanup Phase 1 (Test Fixes)
- **Current State:** 620/766 (81.0%) SQLite, 611/766 (79.8%) PostgreSQL
- **Target State:** 650-680/766 (85-89%) for both databases
- **Risk Level:** Low-Medium (fixing tests, not production code)
- **Estimated Time:** 4-6 hours
- **Expected Improvement:** +30-60 tests passing

## Current Test Status

### Overall Results
- **Total Tests:** 766
- **SQLite Passing:** 620 (81.0%)
- **PostgreSQL Passing:** 611 (79.8%)
- **Failures to Fix:** ~146 tests

### Failure Breakdown
1. **Database Initialization Errors:** 100 errors (13% of all tests) - Priority 1
2. **SQL Injection Tests:** ~10-15 failures (1-2% of tests) - Priority 2
3. **Miscellaneous Failures:** ~30-40 failures (4-5% of tests) - Priority 3

---

## Issue #1: Database Initialization Errors (100 errors)

### Problem
Tests in `core/workflow_history_utils/test_database.py` have initialization issues that cause 100 test errors affecting both databases equally.

### Error Patterns
Need to identify specific errors by running:
```bash
cd app/server
uv run pytest core/workflow_history_utils/test_database.py -v --tb=short
```

Common initialization errors:
- Database not initialized before tests
- Missing tables or schema
- Fixture configuration issues
- Import errors
- Connection errors

### Impact
- **Tests Affected:** 100 errors (13% of entire test suite)
- **Severity:** Critical - largest single source of test failures
- **Databases:** Both SQLite and PostgreSQL affected equally

### Investigation Required
1. Why are these tests failing?
2. What is the expected vs actual behavior?
3. Are these tests actually needed?
4. Can they be fixed or should they be removed?

---

## Issue #2: SQL Injection Test Failures (10-15 failures)

### Problem
SQL injection tests reference non-existent `core/sql_processor.py` module.

### Error Pattern
```python
ModuleNotFoundError: No module named 'core.sql_processor'
# or
ImportError: cannot import name 'validate_sql' from 'core.sql_processor'
```

### Root Cause
Tests were written for a `sql_processor` module that either:
- Never existed
- Was deleted during refactoring
- Was moved to a different location

### Impact
- **Tests Affected:** ~10-15 failures (1-2% of test suite)
- **Severity:** Medium - tests are non-functional
- **Databases:** Both affected equally

### Solutions
**Option 1: Remove Tests** (if feature doesn't exist)
- Delete SQL injection tests
- Remove references to sql_processor

**Option 2: Implement Missing Module** (if feature is needed)
- Create `core/sql_processor.py`
- Implement SQL validation logic
- Ensure tests pass

**Option 3: Update Tests** (if module was moved)
- Find where sql_processor logic now lives
- Update imports in tests
- Verify tests pass

---

## Issue #3: Miscellaneous Test Failures (30-40 failures)

### Problem
Various test failures not related to database initialization or SQL injection.

### Investigation Required
Run full test suite and categorize failures:
```bash
cd app/server
uv run pytest tests/ -v --tb=short 2>&1 | tee /tmp/test_failures.txt
grep "FAILED" /tmp/test_failures.txt > /tmp/failed_tests.txt
```

### Categorization Strategy
Group failures by:
1. **Import errors** - Missing modules or circular imports
2. **Assertion failures** - Logic errors in tests or code
3. **Setup/teardown errors** - Fixture issues
4. **Timeout errors** - Tests running too long
5. **Flaky tests** - Intermittent failures

### Priority
- Fix quick wins first (import errors, obvious bugs)
- Document harder issues for later phases
- Skip flaky tests temporarily

---

## Step-by-Step Instructions

### Step 1: Establish Baseline

Run full test suite and capture results:

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Run with SQLite
export DB_TYPE=sqlite
uv run pytest tests/ -v --tb=short 2>&1 | tee /tmp/cleanup_phase1_sqlite_before.txt

# Count results
echo "SQLite Before:"
grep -E "passed|failed|error" /tmp/cleanup_phase1_sqlite_before.txt | tail -1

# Run with PostgreSQL
export DB_TYPE=postgresql
export POSTGRES_HOST=127.0.0.1
export POSTGRES_PORT=5432
export POSTGRES_DB=tac_webbuilder
export POSTGRES_USER=tac_user
export POSTGRES_PASSWORD=changeme

uv run pytest tests/ -v --tb=short 2>&1 | tee /tmp/cleanup_phase1_postgres_before.txt

# Count results
echo "PostgreSQL Before:"
grep -E "passed|failed|error" /tmp/cleanup_phase1_postgres_before.txt | tail -1

# Expected:
# SQLite: 620 passed, 80 failed, 14 skipped, 100 errors
# PostgreSQL: 611 passed, 89 failed, 14 skipped, 100 errors
```

### Step 2: Investigate Database Initialization Errors

#### Step 2a: Run Problematic Tests

```bash
cd app/server

# Run the problematic test file
uv run pytest core/workflow_history_utils/test_database.py -v --tb=short 2>&1 | tee /tmp/db_init_errors.txt

# Analyze errors
cat /tmp/db_init_errors.txt | grep -A 10 "ERROR\|FAILED"

# Look for patterns:
# - Import errors
# - Missing fixtures
# - Database connection issues
# - Schema problems
```

#### Step 2b: Check File Structure

```bash
# Verify file exists
ls -la core/workflow_history_utils/test_database.py

# Check imports
head -30 core/workflow_history_utils/test_database.py

# Look for issues:
# - Circular imports
# - Missing dependencies
# - Incorrect paths
```

#### Step 2c: Determine Fix Strategy

Based on errors found, choose approach:

**If tests are outdated/broken:**
```bash
# Option 1: Skip these tests temporarily
# Add pytest.mark.skip to problematic tests

# Option 2: Remove if no longer needed
git rm core/workflow_history_utils/test_database.py
```

**If tests need fixing:**
```bash
# Fix imports, fixtures, or database setup
# See Step 2d for common fixes
```

#### Step 2d: Common Fixes

**Fix 1: Missing Fixtures**
```python
# In core/workflow_history_utils/conftest.py or test file

import pytest
from app.server.database.db_adapter import db_adapter

@pytest.fixture(scope="function")
def test_db():
    """Initialize test database."""
    # Setup
    conn = db_adapter.get_connection()
    cursor = conn.cursor()

    # Create tables if needed
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY,
            data TEXT
        )
    """)
    conn.commit()

    yield conn

    # Teardown
    cursor.execute("DROP TABLE IF EXISTS test_table")
    conn.commit()
    conn.close()
```

**Fix 2: Import Errors**
```python
# Before (broken):
from core.some_module import SomeClass

# After (fixed):
from app.server.some_module import SomeClass
# or
import sys
sys.path.insert(0, '/path/to/core')
from some_module import SomeClass
```

**Fix 3: Database Connection**
```python
# Ensure DB_TYPE is set for tests
import os
os.environ.setdefault('DB_TYPE', 'sqlite')

from app.server.database.db_adapter import db_adapter
```

### Step 3: Fix SQL Injection Test Failures

#### Step 3a: Locate SQL Injection Tests

```bash
cd app/server

# Find tests importing sql_processor
grep -r "sql_processor" tests/ --include="*.py" -n

# Expected output: List of test files
# Example: tests/security/test_sql_injection.py:5:from core.sql_processor import validate_sql
```

#### Step 3b: Check If Module Exists

```bash
# Search for sql_processor in codebase
find . -name "*sql_processor*" -type f

# Search for SQL validation logic
grep -r "validate_sql\|sanitize_sql\|sql.*injection" app/server/ --include="*.py"

# If found: Module was moved, update imports
# If not found: Module never existed or was deleted
```

#### Step 3c: Choose Fix Strategy

**Option 1: Remove Tests (If feature doesn't exist)**
```bash
# If sql_processor was never implemented:
cd app/server

# Remove SQL injection test files
git rm tests/security/test_sql_injection.py
# Or skip them
# Add @pytest.mark.skip to the tests
```

**Option 2: Implement Module (If feature is needed)**
```python
# Create app/server/core/sql_processor.py

def validate_sql(query: str) -> bool:
    """
    Validate SQL query for injection attacks.

    Args:
        query: SQL query string to validate

    Returns:
        True if safe, False if potentially malicious
    """
    dangerous_patterns = [
        r"';.*--",  # Comment-based injection
        r"UNION.*SELECT",  # UNION-based injection
        r"DROP\s+TABLE",  # Table dropping
        r"DELETE\s+FROM.*WHERE\s+1=1",  # Mass deletion
    ]

    import re
    query_upper = query.upper()

    for pattern in dangerous_patterns:
        if re.search(pattern, query_upper, re.IGNORECASE):
            return False

    return True

def sanitize_sql(value: str) -> str:
    """
    Sanitize SQL input value.

    Args:
        value: Input value to sanitize

    Returns:
        Sanitized value
    """
    # Use parameterized queries instead!
    # This is just for legacy code
    return value.replace("'", "''")
```

**Option 3: Update Imports (If module was moved)**
```python
# If validation logic exists elsewhere, update imports
# Before:
from core.sql_processor import validate_sql

# After (if moved to database module):
from app.server.database.security import validate_sql
```

### Step 4: Investigate Miscellaneous Failures

#### Step 4a: Extract Failed Test Names

```bash
cd app/server

# Get list of failed tests
grep "FAILED" /tmp/cleanup_phase1_sqlite_before.txt | cut -d' ' -f1 | cut -d':' -f3 > /tmp/failed_test_names.txt

# Count failures
wc -l /tmp/failed_test_names.txt

# Group by test file
cat /tmp/failed_test_names.txt | cut -d':' -f1 | sort | uniq -c | sort -rn

# This shows which test files have most failures
```

#### Step 4b: Categorize by Error Type

```bash
# Find import errors
grep -B5 "ImportError\|ModuleNotFoundError" /tmp/cleanup_phase1_sqlite_before.txt | grep "FAILED" | wc -l

# Find assertion errors
grep -B5 "AssertionError" /tmp/cleanup_phase1_sqlite_before.txt | grep "FAILED" | wc -l

# Find timeout errors
grep -B5 "Timeout" /tmp/cleanup_phase1_sqlite_before.txt | grep "FAILED" | wc -l

# Find setup/teardown errors
grep -B5 "fixture\|setup\|teardown" /tmp/cleanup_phase1_sqlite_before.txt | grep "FAILED" | wc -l
```

#### Step 4c: Fix by Category

**Import Errors:**
```bash
# For each import error, fix the import
# Common fixes:
# - Update path: core.module → app.server.module
# - Add missing dependency: pip install package
# - Fix circular import: reorganize imports
```

**Assertion Errors:**
```python
# Review test logic
# Options:
# 1. Fix the code if test is correct
# 2. Fix the test if expectations are wrong
# 3. Skip test if it's outdated

# Example fix:
# Before:
assert result == "expected_value"

# After (if expectations changed):
assert result == "new_expected_value"

# Or skip if test is outdated:
@pytest.mark.skip(reason="Test outdated - needs rewrite")
def test_something():
    ...
```

**Fixture Errors:**
```python
# Ensure fixtures are properly defined
# Check conftest.py files
# Verify fixture scope and dependencies

# Example fix:
@pytest.fixture(scope="function")  # or "module", "session"
def my_fixture():
    # setup
    yield value
    # teardown
```

### Step 5: Run Tests After Fixes

```bash
cd app/server

# Run with SQLite
export DB_TYPE=sqlite
uv run pytest tests/ -v --tb=short 2>&1 | tee /tmp/cleanup_phase1_sqlite_after.txt

echo "SQLite After:"
grep -E "passed|failed|error" /tmp/cleanup_phase1_sqlite_after.txt | tail -1

# Run with PostgreSQL
export DB_TYPE=postgresql
export POSTGRES_HOST=127.0.0.1
export POSTGRES_PORT=5432
export POSTGRES_DB=tac_webbuilder
export POSTGRES_USER=tac_user
export POSTGRES_PASSWORD=changeme

uv run pytest tests/ -v --tb=short 2>&1 | tee /tmp/cleanup_phase1_postgres_after.txt

echo "PostgreSQL After:"
grep -E "passed|failed|error" /tmp/cleanup_phase1_postgres_after.txt | tail -1

# Compare before/after
echo "=== Improvement Summary ==="
echo "SQLite:"
echo "  Before: 620 passed"
echo "  After:  $(grep -E 'passed' /tmp/cleanup_phase1_sqlite_after.txt | tail -1 | grep -oP '\d+ passed' | cut -d' ' -f1)"
echo ""
echo "PostgreSQL:"
echo "  Before: 611 passed"
echo "  After:  $(grep -E 'passed' /tmp/cleanup_phase1_postgres_after.txt | tail -1 | grep -oP '\d+ passed' | cut -d' ' -f1)"
```

### Step 6: Document Results

Update `POSTGRES_TEST_RESULTS.md` with Phase 1 cleanup results:

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

cat >> POSTGRES_TEST_RESULTS.md <<EOF

---

## Cleanup Phase 1 Results ($(date +%Y-%m-%d))

### Fixes Applied

1. **Database Initialization Errors** ([Fixed/Skipped/Removed])
   - Location: core/workflow_history_utils/test_database.py
   - Tests Affected: 100 errors → [new count] errors
   - Solution: [describe fix]
   - Files Modified: [list files]

2. **SQL Injection Test Failures** ([Fixed/Skipped/Removed])
   - Root Cause: Missing core/sql_processor.py
   - Tests Affected: [count] failures → [new count] failures
   - Solution: [describe fix]
   - Files Modified: [list files]

3. **Miscellaneous Test Failures** ([count] fixed)
   - Import errors: [count] fixed
   - Assertion errors: [count] fixed
   - Fixture errors: [count] fixed
   - Other: [count] fixed

### Test Results After Cleanup Phase 1

**SQLite:**
- Before: 620/766 passed (81.0%)
- After: [fill in]/766 passed ([fill in]%)
- Change: +[fill in] tests

**PostgreSQL:**
- Before: 611/766 passed (79.8%)
- After: [fill in]/766 passed ([fill in]%)
- Change: +[fill in] tests

### Success Metrics
- Database init errors: 100 → [new count]
- SQL injection failures: ~15 → [new count]
- Misc failures: ~40 → [new count]
- Total improvement: +[fill in] tests passing

### Remaining Issues
- [List remaining high-priority failures]
- [Note any issues deferred to Phase 2]

EOF
```

### Step 7: Commit Changes

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

git status

# Stage changes
git add -u  # Add all modified files
git add .  # Add any new files (if created sql_processor, etc.)

# Commit
git commit -m "$(cat <<'EOF'
fix: Cleanup Phase 1 - Fix pre-existing test failures

Fixed ~[count] pre-existing test failures to improve test quality.

Issue #1: Database Initialization Errors ([count] fixed/skipped)
- Location: core/workflow_history_utils/test_database.py
- Solution: [describe]
- Tests: 100 errors → [new count]

Issue #2: SQL Injection Test Failures ([count] fixed/removed)
- Root Cause: Missing core/sql_processor.py
- Solution: [describe]
- Tests: ~15 failures → [new count]

Issue #3: Miscellaneous Test Failures ([count] fixed)
- Import errors: [count] fixed
- Assertion errors: [count] fixed
- Fixture errors: [count] fixed

Test Results:
- SQLite: 620 → [new count] passing (+[improvement])
- PostgreSQL: 611 → [new count] passing (+[improvement])

Target: 85-89% pass rate (650-680/766 tests)
Current: [fill in]% pass rate ([count]/766 tests)

Files Modified:
- [list modified files]

Next: Cleanup Phase 2 - Code quality improvements

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

git push
```

---

## Success Criteria

- [ ] Database initialization errors: 100 → < 10
- [ ] SQL injection test failures: ~15 → 0
- [ ] Miscellaneous failures investigated and categorized
- [ ] Total test pass rate: 85-89% (650-680/766) for both databases
- [ ] All fixes documented in POSTGRES_TEST_RESULTS.md
- [ ] Changes committed and pushed

## Expected Improvements

### Before Cleanup Phase 1
```
SQLite: 620/766 passed (81.0%)
PostgreSQL: 611/766 passed (79.8%)
Total failures: ~146
```

### After Cleanup Phase 1 (Target)
```
SQLite: 650-680/766 passed (85-89%)
PostgreSQL: 650-680/766 passed (85-89%)
Total failures: ~86-116 (improvement of 30-60 tests)
```

### Remaining for Phase 2+
```
~86-116 failures to address in future phases
Many may be edge cases or acceptable failures
Target final state: 720-750/766 (94-98%)
```

---

## Troubleshooting

### Database Initialization Errors Won't Fix

**Issue:** Tests still fail after attempted fixes

**Solutions:**
1. **Skip the tests temporarily:**
   ```python
   import pytest

   @pytest.mark.skip(reason="Database init issues - deferred to Phase 2")
   class TestDatabase:
       ...
   ```

2. **Check test dependencies:**
   ```bash
   # Ensure all dependencies installed
   cd app/server
   uv sync

   # Check for missing test fixtures
   find tests/ -name "conftest.py" -exec cat {} \;
   ```

3. **Isolate the problem:**
   ```bash
   # Run just one test to debug
   uv run pytest core/workflow_history_utils/test_database.py::test_specific_test -vvs
   ```

### SQL Injection Tests Are Critical

**Issue:** Can't remove SQL injection tests - they're actually needed

**Solution:** Implement sql_processor module

```bash
# Create the module
mkdir -p app/server/core
touch app/server/core/__init__.py

# Add implementation (see Step 3c Option 2)
cat > app/server/core/sql_processor.py <<'EOF'
# Implementation here
EOF

# Update tests to import correctly
# Fix any test assertions to match new implementation
```

### Too Many Miscellaneous Failures

**Issue:** 40+ misc failures is overwhelming

**Strategy:** Prioritize and batch

```bash
# Focus on quick wins first
# 1. Fix all import errors (usually easy)
# 2. Fix obvious assertion bugs
# 3. Skip flaky tests
# 4. Document harder issues for Phase 2

# Create issues for deferred work
# Track remaining failures in CLEANUP_OPTIMIZATION_TRACKER.md
```

---

## Next Steps

After completing Phase 1:

1. **Update Documentation**
   - POSTGRES_TEST_RESULTS.md with actual results
   - CLEANUP_OPTIMIZATION_TRACKER.md with Phase 1 completion
   - Note any issues deferred to Phase 2

2. **Review Results**
   - Did we hit 85-89% pass rate target?
   - What were the biggest wins?
   - What issues remain?

3. **Proceed to Phase 2**
   - Use CLEANUP_PHASE2_CODE_QUALITY.md (to be created)
   - Focus on code cleanup and quality
   - Target remaining test failures caused by code quality issues

4. **Report Back**
```
✅ Cleanup Phase 1 Complete - Test Failures Fixed

Results:
- SQLite: [before] → [after] tests (+[improvement])
- PostgreSQL: [before] → [after] tests (+[improvement])

Fixes:
- Database init errors: 100 → [new count]
- SQL injection tests: ~15 → [new count]
- Misc failures: ~40 → [new count]

Test pass rate: [percentage]% (target was 85-89%)

Issues deferred to Phase 2: [count]

Ready for: Cleanup Phase 2 - Code Quality
```

---

**Ready to copy into a new context!**

This prompt will fix ~30-60 test failures, improving test pass rate from 81% to 85-89%.
