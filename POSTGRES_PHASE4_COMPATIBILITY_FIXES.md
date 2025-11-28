# Task: PostgreSQL Migration - Phase 4.2 Compatibility Fixes

## Context
I'm working on the tac-webbuilder project. Phase 4.1 fixed critical schema issues (85 test failures). Phase 4.2 addresses PostgreSQL-specific compatibility issues: PRAGMA statements and column name case sensitivity.

## Objective
Fix the remaining PostgreSQL-specific compatibility issues:
1. Replace SQLite PRAGMA statements with PostgreSQL information_schema queries (1-2 test failures)
2. Fix column name case sensitivity issues (2 test failures)

After fixes, PostgreSQL should match or exceed SQLite test pass rate.

## Background Information
- **Phase:** 4.2 (Compatibility Fixes)
- **Previous Phase:** Phase 4.1 complete, ~648/766 tests passing with PostgreSQL
- **Test Results:** See `POSTGRES_TEST_RESULTS.md`
- **Risk Level:** Low (isolated changes to test code and queries)
- **Estimated Time:** 1-2 hours
- **Expected Improvement:** +3-4 test passes (648 → 651-652 passing tests)

## Test Results Summary

### After Phase 4.1
- **SQLite:** ~572/766 tests passed (74.7%)
- **PostgreSQL:** ~648/766 tests passed (84.6%)
- **Remaining Failures:** 3-4 PostgreSQL-specific issues

### Phase 4.2 Scope
1. **PRAGMA compatibility:** 1-2 failures
2. **Column case sensitivity:** 2 failures
3. **Total:** 3-4 failures to fix

## Issue #1: PRAGMA Statement Compatibility

### Problem
SQLite uses `PRAGMA` statements to query database metadata (table structure, indexes, etc.). PostgreSQL does not support PRAGMA and uses `information_schema` instead.

### Error Messages
```
psycopg2.errors.SyntaxError: syntax error at or near "PRAGMA"
```

### Affected Tests
- Tests that inspect table structure
- Tests that verify schema changes
- Estimated: 1-2 test failures

### Examples

#### SQLite PRAGMA Statements
```sql
-- Get table columns
PRAGMA table_info(table_name);

-- Get indexes
PRAGMA index_list(table_name);

-- Get foreign keys
PRAGMA foreign_key_list(table_name);

-- Get database list
PRAGMA database_list;
```

#### PostgreSQL Equivalents
```sql
-- Get table columns
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'table_name' AND table_schema = 'public'
ORDER BY ordinal_position;

-- Get indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'table_name' AND schemaname = 'public';

-- Get foreign keys
SELECT
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'table_name'
    AND tc.constraint_type = 'FOREIGN KEY';

-- Get database list
SELECT datname FROM pg_database
WHERE datistemplate = false;
```

### Fix Required
Replace PRAGMA statements with database-agnostic queries using the adapter pattern.

## Issue #2: Column Name Case Sensitivity

### Problem
PostgreSQL is case-sensitive for quoted column names and folds unquoted identifiers to lowercase. SQLite is case-insensitive.

### Error Messages
```
psycopg2.errors.UndefinedColumn: column "Id" does not exist
HINT: Perhaps you meant to reference the column "table.id"
```

### Affected Tests
- SQL injection tests (often use mixed case intentionally)
- Tests with inconsistent column name casing
- Estimated: 2 test failures

### Examples

#### Problem Code
```sql
-- SQLite: Works fine
SELECT Id, Name FROM users WHERE UserId = 1;

-- PostgreSQL: Fails!
-- Error: column "Id" does not exist
```

#### Solution
```sql
-- Use lowercase (preferred)
SELECT id, name FROM users WHERE userid = 1;

-- Or quote identifiers if mixed case is required
SELECT "Id", "Name" FROM users WHERE "UserId" = 1;
```

### Fix Required
Standardize column names to lowercase or use proper quoting.

---

## Step-by-Step Instructions

### Step 1: Find PRAGMA Statements

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Search for PRAGMA usage
grep -r "PRAGMA" tests/ --include="*.py" -n

# Expected output: List of files using PRAGMA
# Example:
# tests/integration/test_schema_validation.py:45:    cursor.execute("PRAGMA table_info(phase_queue)")

# Count occurrences
grep -r "PRAGMA" tests/ --include="*.py" | wc -l
```

### Step 2: Create Database-Agnostic Helper Functions

Create a utility module for database metadata queries:

```bash
cd app/server

# Create utilities module
mkdir -p utils
touch utils/__init__.py
touch utils/db_metadata.py
```

Edit `utils/db_metadata.py`:

```python
"""Database metadata utilities - works with both SQLite and PostgreSQL."""

from typing import List, Dict, Any
from app.server.database.db_adapter import db_adapter


def get_table_columns(table_name: str) -> List[Dict[str, Any]]:
    """
    Get column information for a table.

    Works with both SQLite and PostgreSQL.

    Args:
        table_name: Name of the table

    Returns:
        List of dicts with column info: name, type, nullable, default
    """
    conn = db_adapter.get_connection()
    cursor = conn.cursor()

    if db_adapter.db_type == "sqlite":
        # SQLite: Use PRAGMA
        cursor.execute(f"PRAGMA table_info({table_name})")
        rows = cursor.fetchall()

        # Convert to standardized format
        # SQLite PRAGMA returns: (cid, name, type, notnull, dflt_value, pk)
        columns = []
        for row in rows:
            columns.append({
                "name": row[1],
                "type": row[2],
                "nullable": not row[3],  # notnull=1 means NOT NULL
                "default": row[4],
                "primary_key": row[5]
            })

    else:  # PostgreSQL
        # PostgreSQL: Use information_schema
        cursor.execute("""
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position
        """, (table_name,))

        rows = cursor.fetchall()

        # Convert to standardized format
        columns = []
        for row in rows:
            columns.append({
                "name": row[0] if isinstance(row, tuple) else row["column_name"],
                "type": row[1] if isinstance(row, tuple) else row["data_type"],
                "nullable": (row[2] if isinstance(row, tuple) else row["is_nullable"]) == "YES",
                "default": row[3] if isinstance(row, tuple) else row["column_default"],
                "primary_key": False  # Would need separate query
            })

    conn.close()
    return columns


def get_table_indexes(table_name: str) -> List[Dict[str, Any]]:
    """
    Get index information for a table.

    Works with both SQLite and PostgreSQL.

    Args:
        table_name: Name of the table

    Returns:
        List of dicts with index info: name, columns, unique
    """
    conn = db_adapter.get_connection()
    cursor = conn.cursor()

    if db_adapter.db_type == "sqlite":
        # SQLite: Use PRAGMA
        cursor.execute(f"PRAGMA index_list({table_name})")
        rows = cursor.fetchall()

        # Returns: (seq, name, unique, origin, partial)
        indexes = []
        for row in rows:
            indexes.append({
                "name": row[1],
                "unique": bool(row[2]),
                "definition": None  # Not available in PRAGMA
            })

    else:  # PostgreSQL
        # PostgreSQL: Use pg_indexes
        cursor.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = %s AND schemaname = 'public'
        """, (table_name,))

        rows = cursor.fetchall()

        indexes = []
        for row in rows:
            indexes.append({
                "name": row[0] if isinstance(row, tuple) else row["indexname"],
                "unique": "UNIQUE" in (row[1] if isinstance(row, tuple) else row["indexdef"]),
                "definition": row[1] if isinstance(row, tuple) else row["indexdef"]
            })

    conn.close()
    return indexes


def table_exists(table_name: str) -> bool:
    """
    Check if a table exists.

    Works with both SQLite and PostgreSQL.

    Args:
        table_name: Name of the table

    Returns:
        True if table exists, False otherwise
    """
    conn = db_adapter.get_connection()
    cursor = conn.cursor()

    if db_adapter.db_type == "sqlite":
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
        """, (table_name,))
    else:  # PostgreSQL
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = %s
        """, (table_name,))

    result = cursor.fetchone()
    conn.close()

    return result is not None


def get_column_names(table_name: str) -> List[str]:
    """
    Get list of column names for a table.

    Args:
        table_name: Name of the table

    Returns:
        List of column names
    """
    columns = get_table_columns(table_name)
    return [col["name"] for col in columns]
```

### Step 3: Replace PRAGMA Statements in Tests

For each test file using PRAGMA, replace with utility functions:

#### Example Fix

**Before:**
```python
# tests/integration/test_schema_validation.py

def test_phase_queue_schema():
    """Test that phase_queue table has expected columns."""
    conn = get_connection()
    cursor = conn.cursor()

    # Get table info
    cursor.execute("PRAGMA table_info(phase_queue)")  # ❌ SQLite-specific
    columns = cursor.fetchall()

    # Verify columns
    column_names = [col[1] for col in columns]
    assert "queue_id" in column_names
    assert "issue_number" in column_names
    assert "queue_position" in column_names

    conn.close()
```

**After:**
```python
# tests/integration/test_schema_validation.py

from app.server.utils.db_metadata import get_column_names

def test_phase_queue_schema():
    """Test that phase_queue table has expected columns."""
    # Get column names (works with both SQLite and PostgreSQL)
    column_names = get_column_names("phase_queue")  # ✅ Database-agnostic

    # Verify columns
    assert "queue_id" in column_names
    assert "issue_number" in column_names
    assert "queue_position" in column_names
```

### Step 4: Find and Fix Case Sensitivity Issues

```bash
cd app/server

# Find SQL queries with mixed case column names
grep -r "SELECT.*[A-Z]" tests/ --include="*.py" | grep -i "FROM\|WHERE" | head -20

# Look for patterns like:
# SELECT Id, Name
# WHERE UserId =
# etc.
```

#### Strategy 1: Standardize to Lowercase

**Before:**
```python
def test_injection():
    cursor.execute("SELECT Id FROM users WHERE UserId = %s", (user_id,))
```

**After:**
```python
def test_injection():
    cursor.execute("SELECT id FROM users WHERE userid = %s", (user_id,))
```

#### Strategy 2: Use Proper Quoting (if mixed case is required)

**Before:**
```python
# Fails in PostgreSQL
cursor.execute('SELECT Id, Name FROM users')
```

**After:**
```python
# Works in PostgreSQL (but verbose)
cursor.execute('SELECT "Id", "Name" FROM users')
```

#### Strategy 3: Create Column Name Constants

```python
# tests/conftest.py or tests/constants.py

# Define column names as constants (all lowercase)
COLUMN_ID = "id"
COLUMN_USER_ID = "userid"
COLUMN_NAME = "name"

# Use in tests
def test_something():
    cursor.execute(f"SELECT {COLUMN_ID}, {COLUMN_NAME} FROM users")
```

### Step 5: Find Specific Failing Tests

Run tests to identify which ones are failing:

```bash
cd app/server
export DB_TYPE=postgresql
export POSTGRES_HOST=127.0.0.1
export POSTGRES_PORT=5432
export POSTGRES_DB=tac_webbuilder
export POSTGRES_USER=tac_user
export POSTGRES_PASSWORD=changeme

# Run tests and filter for PRAGMA errors
uv run pytest tests/ -v 2>&1 | grep -A 5 "PRAGMA\|syntax error"

# Run tests and filter for case sensitivity errors
uv run pytest tests/ -v 2>&1 | grep -A 5 "column.*does not exist\|Perhaps you meant"

# Save failing test names
uv run pytest tests/ -v --tb=short 2>&1 | grep "FAILED" | tee /tmp/phase42_failures.txt
```

### Step 6: Fix Identified Tests

For each failing test:

1. Open the test file
2. Locate the PRAGMA or case-sensitive SQL
3. Replace with database-agnostic code
4. Run the test to verify fix

```bash
# Fix one test at a time
uv run pytest tests/path/to/test_file.py::test_name -v

# Example:
uv run pytest tests/integration/test_schema_validation.py::test_phase_queue_schema -v
```

### Step 7: Add Utility Functions to conftest.py

Make utilities easily accessible in tests:

```python
# tests/conftest.py

import pytest
from app.server.utils.db_metadata import (
    get_table_columns,
    get_column_names,
    get_table_indexes,
    table_exists
)

# Export for use in tests
@pytest.fixture
def db_metadata():
    """Fixture providing database metadata utilities."""
    return {
        "get_columns": get_table_columns,
        "get_column_names": get_column_names,
        "get_indexes": get_table_indexes,
        "table_exists": table_exists,
    }
```

Then use in tests:

```python
def test_something(db_metadata):
    """Test using metadata utilities."""
    columns = db_metadata["get_column_names"]("phase_queue")
    assert "queue_id" in columns
```

### Step 8: Run Full Test Suite

```bash
cd app/server

# Test with SQLite (verify no regression)
export DB_TYPE=sqlite
uv run pytest tests/ -v --tb=short | tee /tmp/phase42_sqlite.txt

# Test with PostgreSQL (verify fixes)
export DB_TYPE=postgresql
export POSTGRES_HOST=127.0.0.1
export POSTGRES_PORT=5432
export POSTGRES_DB=tac_webbuilder
export POSTGRES_USER=tac_user
export POSTGRES_PASSWORD=changeme

uv run pytest tests/ -v --tb=short | tee /tmp/phase42_postgres.txt

# Compare results
echo "SQLite: $(grep -E 'passed' /tmp/phase42_sqlite.txt | tail -1)"
echo "PostgreSQL: $(grep -E 'passed' /tmp/phase42_postgres.txt | tail -1)"

# Expected:
# SQLite: ~572 passed (no regression)
# PostgreSQL: ~651-652 passed (+3-4 from Phase 4.1)
```

### Step 9: Update Documentation

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

# Update test results
cat >> POSTGRES_TEST_RESULTS.md <<EOF

---

## Phase 4.2 Results ($(date +%Y-%m-%d))

### Fixes Applied

1. ✅ **PRAGMA Statement Compatibility**
   - Created database-agnostic metadata utilities
   - Replaced PRAGMA with information_schema queries
   - Files Modified: utils/db_metadata.py, test files
   - Tests Fixed: [count]

2. ✅ **Column Name Case Sensitivity**
   - Standardized column names to lowercase
   - Fixed SQL injection tests
   - Tests Fixed: [count]

### Test Results After Phase 4.2

**SQLite:**
- After 4.1: ~572/766 passed (74.7%)
- After 4.2: [fill in] passed ([fill in]%)
- Change: [no regression expected]

**PostgreSQL:**
- After 4.1: ~648/766 passed (84.6%)
- After 4.2: [fill in] passed ([fill in]%)
- Change: +[fill in] tests

### Success Metrics
- PRAGMA errors: [before] → 0
- Case sensitivity errors: [before] → 0
- PostgreSQL vs SQLite gap: [fill in]

EOF
```

### Step 10: Commit Changes

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

git status

# Expected changes:
# - app/server/utils/db_metadata.py (new file)
# - app/server/utils/__init__.py (new file)
# - Test files with PRAGMA or case issues (modified)
# - tests/conftest.py (if added utilities fixture)
# - POSTGRES_TEST_RESULTS.md (updated)

git add app/server/utils/
git add tests/
git add POSTGRES_TEST_RESULTS.md

git commit -m "$(cat <<'EOF'
fix: PostgreSQL migration Phase 4.2 - Database compatibility fixes

Fixed PostgreSQL-specific compatibility issues:

Issue #1: PRAGMA Statement Compatibility ([count] failures fixed)
- Created database-agnostic metadata utilities in utils/db_metadata.py
- Implemented get_table_columns(), get_column_names(), get_table_indexes()
- Works seamlessly with both SQLite (PRAGMA) and PostgreSQL (information_schema)
- Replaced PRAGMA statements in test files with utility functions

Issue #2: Column Name Case Sensitivity ([count] failures fixed)
- Standardized column names to lowercase throughout tests
- Fixed SQL injection tests to use PostgreSQL-compatible syntax
- PostgreSQL is case-sensitive for quoted identifiers
- Ensured consistent column naming across both databases

Utilities Added:
- utils/db_metadata.py - Database-agnostic metadata queries
  - get_table_columns(table_name) - Get column information
  - get_column_names(table_name) - Get list of column names
  - get_table_indexes(table_name) - Get index information
  - table_exists(table_name) - Check if table exists

Test Results:
- PostgreSQL: ~648 → [new count] passing tests (+[increase])
- SQLite: ~572 passing (no regression)
- PRAGMA errors: [before] → 0
- Case sensitivity errors: [before] → 0

Files Modified:
- app/server/utils/db_metadata.py - New metadata utilities
- tests/[affected files] - Replaced PRAGMA, fixed case sensitivity
- POSTGRES_TEST_RESULTS.md - Phase 4.2 results

Next: Phase 4.3 - Regression testing and validation

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

git push
```

---

## Success Criteria

- ✅ No PRAGMA syntax errors in PostgreSQL tests
- ✅ No column case sensitivity errors in PostgreSQL tests
- ✅ Database metadata utilities created and tested
- ✅ PostgreSQL tests: +3-4 passing (~648 → ~652)
- ✅ SQLite tests: No regression (~572 passing)
- ✅ All Phase 4.2 specific tests pass
- ✅ Changes committed with descriptive message
- ✅ Documentation updated

## Files Expected to Change

**New Files:**
- `app/server/utils/db_metadata.py` - Metadata utilities
- `app/server/utils/__init__.py` - Module init

**Modified:**
- Test files using PRAGMA statements
- Test files with case-sensitive column names
- `tests/conftest.py` - Utilities fixture (optional)
- `POSTGRES_TEST_RESULTS.md` - Phase 4.2 results

**No Changes Expected:**
- Production code (these are test-only fixes)
- Database schemas
- Repository implementations

## Troubleshooting

### PRAGMA Errors Persist

**Error: "syntax error at or near 'PRAGMA'"**
```bash
# Find remaining PRAGMA usage
cd app/server
grep -r "PRAGMA" tests/ --include="*.py" -n

# Should return empty (all replaced)
# If any found, replace with utility functions
```

**Utility functions not working:**
```bash
# Test utilities directly
cd app/server
python3 <<EOF
from utils.db_metadata import get_column_names
print(get_column_names("phase_queue"))
EOF

# Should print list of column names
# If error, check db_adapter import and connection
```

### Case Sensitivity Errors Persist

**Error: column "Id" does not exist**
```bash
# Find mixed-case column references
cd app/server
grep -r 'SELECT.*[A-Z]' tests/ --include="*.py" | grep -v "FROM\|WHERE" | head -20

# Look for SQL with mixed case
# Should be standardized to lowercase
```

**Not sure if issue is case sensitivity:**
```bash
# Test directly in PostgreSQL
docker exec -it tac-webbuilder-postgres psql -U tac_user -d tac_webbuilder <<EOF
-- This fails:
SELECT Id FROM phase_queue;

-- This works:
SELECT id FROM phase_queue;

-- This also works:
SELECT "Id" FROM phase_queue;
EOF
```

### Tests Pass Individually But Fail Together

**Intermittent failures:**
- May be test isolation issue from Phase 4.1
- Check cleanup fixtures are running
- Try: `pytest --forked` or `pytest -x` (stop on first failure)

### Performance Issues

**Tests slower after adding utilities:**
- Utilities create new connections
- Consider connection pooling or caching
- Profile with: `pytest --durations=10`

---

## Expected Improvements

### Before Phase 4.2
```
PostgreSQL: ~648/766 passed (84.6%)
SQLite: ~572/766 passed (74.7%)
```

### After Phase 4.2
```
PostgreSQL: ~652/766 passed (85.1%)
SQLite: ~572/766 passed (74.7%)
PostgreSQL ahead: +80 tests
```

### Remaining Issues
```
Pre-existing database init errors: 100 (affects both DBs equally)
Other failures: ~14 (unknown causes, need investigation)
```

---

## Next Steps

After completing Phase 4.2:

1. **Verify Success**
   - Run full test suite with both databases
   - Confirm +3-4 tests passing with PostgreSQL
   - No regression in SQLite tests

2. **Phase 4.3: Regression Testing**
   - Run performance benchmarks again
   - Verify no new failures introduced
   - Test edge cases
   - Document final Phase 4 results

3. **Phase 5: Production Readiness**
   - Use POSTGRES_PHASE5_PRODUCTION_READY.md (to be created)
   - Production configuration
   - Deployment procedures
   - Monitoring setup

4. **Report Back**
```
✅ Phase 4.2 Complete - Compatibility Fixes Applied

Fixes:
- ✅ PRAGMA statements replaced with information_schema
- ✅ Column case sensitivity standardized

Results:
- PostgreSQL: [before] → [after] tests passing (+[increase])
- SQLite: [count] tests passing (no regression)
- PRAGMA errors: 0
- Case sensitivity errors: 0

Utilities Created:
- db_metadata.py with 4 utility functions

Ready for: Phase 4.3 - Regression Testing
```

---

**Ready to copy into a new context!**

This prompt will fix the remaining PostgreSQL compatibility issues, bringing test pass rate from ~84.6% to ~85%+.
