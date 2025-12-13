# Task: PostgreSQL Migration - Phase 4.1 Critical Fixes

## Context
I'm working on the tac-webbuilder project. Phase 3 testing identified 85 critical test failures that must be fixed before PostgreSQL can be used in production. These failures fall into three categories: missing schema columns, test isolation issues, and missing tables.

## Objective
Fix the 3 critical issues blocking PostgreSQL migration:
1. Add missing `queue_position` column to phase_queue table (38 test failures)
2. Fix test isolation to prevent UNIQUE constraint violations (40+ test failures)
3. Ensure `adw_locks` table exists in test database (7 test failures)

After fixes, verify tests pass with both SQLite and PostgreSQL.

## Background Information
- **Phase:** 4.1 (Critical Fixes)
- **Previous Phase:** Phase 3 testing complete, 563/766 tests passing with PostgreSQL
- **Test Results:** See `POSTGRES_TEST_RESULTS.md`
- **Risk Level:** Medium (schema changes, test infrastructure changes)
- **Estimated Time:** 2-3 hours
- **Expected Improvement:** +85 test passes (563 → 648 passing tests)

## Test Results Summary from Phase 3

### Current State
- **SQLite:** 572/766 tests passed (74.7%)
- **PostgreSQL:** 563/766 tests passed (73.5%)
- **Gap:** 9 fewer tests passing with PostgreSQL

### Critical Failures (Phase 4.1 Scope)
1. **Missing queue_position column:** 38 failures
2. **Test isolation issues:** 40+ failures
3. **Missing adw_locks table:** 7 failures
4. **Total:** 85 failures to fix

## Issue #1: Missing queue_position Column

### Problem
The `phase_queue` table is missing a `queue_position` column that is referenced in code but not defined in the schema.

### Error Messages
```
sqlite3.OperationalError: no such column: queue_position
```

### Affected Tests
- `tests/services/test_phase_coordinator.py` - Multiple tests
- `tests/services/test_phase_queue_service.py` - Multiple tests
- **Total:** 38 test failures

### Root Cause
The schema evolution added `queue_position` column usage in the application code, but the column was never added to either the SQLite or PostgreSQL schemas.

### Fix Required
Add `queue_position` column to both database schemas.

## Issue #2: Test Isolation - UNIQUE Constraint Violations

### Problem
Tests are not properly isolated, causing UNIQUE constraint violations when tests run in sequence. Previous test data is not being cleaned up properly.

### Error Messages
```
sqlite3.IntegrityError: UNIQUE constraint failed: workflow_history.adw_id
psycopg2.errors.UniqueViolation: duplicate key value violates unique constraint "workflow_history_adw_id_key"
```

### Affected Tests
- `tests/test_workflow_history.py` - Multiple tests
- `tests/integration/test_database_operations.py` - Multiple tests
- `tests/integration/test_workflow_history_integration.py` - Multiple tests
- **Total:** 40+ test failures

### Root Cause
Test fixtures in `conftest.py` are not properly cleaning up the `workflow_history` table between tests, causing UNIQUE constraint violations on the `adw_id` column.

### Fix Required
Improve test fixtures to ensure clean database state between tests.

## Issue #3: Missing adw_locks Table

### Problem
Tests expect an `adw_locks` table to exist, but it's not being created in the test database setup.

### Error Messages
```
sqlite3.OperationalError: no such table: adw_locks
```

### Affected Tests
- `tests/integration/test_database_operations.py` - Lock-related tests
- **Total:** 7 test failures

### Root Cause
The `adw_locks` table schema exists in production schemas but is not being initialized in the test database setup.

### Fix Required
Ensure `adw_locks` table is created during test database initialization.

---

## Step-by-Step Instructions

### Step 1: Verify Current Test Results

Before making changes, establish baseline:

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Run tests with SQLite (baseline)
export DB_TYPE=sqlite
uv run pytest tests/ -v --tb=short | tee /tmp/phase4_sqlite_before.txt

# Count failures
grep -E "FAILED|PASSED|ERROR" /tmp/phase4_sqlite_before.txt | tail -1

# Expected: 572 passed, 80 failed, 14 skipped, 100 errors

# Run tests with PostgreSQL (before fixes)
export DB_TYPE=postgresql
export POSTGRES_HOST=127.0.0.1
export POSTGRES_PORT=5432
export POSTGRES_DB=tac_webbuilder
export POSTGRES_USER=tac_user
export POSTGRES_PASSWORD=changeme

uv run pytest tests/ -v --tb=short | tee /tmp/phase4_postgres_before.txt

# Count failures
grep -E "FAILED|PASSED|ERROR" /tmp/phase4_postgres_before.txt | tail -1

# Expected: 563 passed, 89 failed, 14 skipped, 100 errors
```

### Step 2: Fix Issue #1 - Add queue_position Column

#### Step 2a: Check Current Schema

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

# Check PostgreSQL schema
grep -A 20 "CREATE TABLE phase_queue" migration/postgres_schema.sql

# Check if queue_position exists
grep "queue_position" migration/postgres_schema.sql

# Expected: No matches (column doesn't exist)
```

#### Step 2b: Find Column Usage in Code

```bash
# Find where queue_position is used
cd app/server
grep -r "queue_position" --include="*.py" | grep -v test | head -20

# This will show you:
# - Which files use queue_position
# - How it's being used (INSERT, SELECT, UPDATE)
# - What data type it should be
```

#### Step 2c: Add Column to PostgreSQL Schema

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

# Edit PostgreSQL schema
# Find the CREATE TABLE phase_queue statement
# Add the queue_position column
```

Edit `migration/postgres_schema.sql`:

```sql
CREATE TABLE phase_queue (
    queue_id SERIAL PRIMARY KEY,
    issue_number INTEGER NOT NULL,
    parent_issue INTEGER,
    phase_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    dependencies TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    queue_position INTEGER,  -- ADD THIS LINE
    UNIQUE(issue_number)
);
```

#### Step 2d: Update SQLite Schema (if exists)

```bash
# Check if there's a SQLite schema file
find . -name "*sqlite*.sql" -o -name "*schema*.sql" | grep -v postgres | grep -v node_modules

# If SQLite schema file exists, add queue_position there too
# Otherwise, SQLite schema is created dynamically by repositories
```

#### Step 2e: Add Column to Existing Database

```bash
# Add to PostgreSQL (if database already exists)
docker exec -i tac-webbuilder-postgres psql -U tac_user -d tac_webbuilder <<EOF
ALTER TABLE phase_queue ADD COLUMN IF NOT EXISTS queue_position INTEGER;
EOF

# Verify column added
docker exec -it tac-webbuilder-postgres psql -U tac_user -d tac_webbuilder -c "\d phase_queue"

# Expected: queue_position column listed
```

For SQLite (test database):
```bash
cd app/server

# Create a migration script
cat > migrate_add_queue_position.py <<'EOF'
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "test_database.db")
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if column exists
    cursor.execute("PRAGMA table_info(phase_queue)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'queue_position' not in columns:
        cursor.execute("ALTER TABLE phase_queue ADD COLUMN queue_position INTEGER")
        conn.commit()
        print("✅ Added queue_position column to SQLite")
    else:
        print("✅ queue_position column already exists")

    conn.close()
else:
    print("⚠️ Test database doesn't exist yet (will be created on first test run)")
EOF

uv run python migrate_add_queue_position.py
```

#### Step 2f: Update Repository to Include queue_position

```bash
# Find the PhaseQueueRepository
find app/server -name "*phase_queue*.py" -type f | grep -i repository

# Expected: app/server/repositories/phase_queue_repository.py
```

Check if the repository's CREATE TABLE statement includes queue_position:

```bash
grep -A 30 "CREATE TABLE.*phase_queue" app/server/repositories/phase_queue_repository.py
```

If the repository creates the schema dynamically, update it to include `queue_position`:

```python
# In phase_queue_repository.py, find the CREATE TABLE statement
CREATE TABLE IF NOT EXISTS phase_queue (
    queue_id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_number INTEGER NOT NULL UNIQUE,
    parent_issue INTEGER,
    phase_name TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    dependencies TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    queue_position INTEGER  -- ADD THIS LINE
)
```

### Step 3: Fix Issue #2 - Test Isolation

#### Step 3a: Identify Test Fixtures

```bash
cd app/server

# Find conftest.py files
find tests/ -name "conftest.py"

# Expected multiple conftest.py files:
# - tests/conftest.py (root)
# - tests/integration/conftest.py
# - tests/services/conftest.py
# etc.
```

#### Step 3b: Review Current Fixtures

```bash
# Check workflow_history related fixtures
grep -A 10 "workflow_history" tests/conftest.py tests/*/conftest.py
```

Look for:
- Database setup fixtures
- Cleanup/teardown logic
- Transaction management

#### Step 3c: Add Proper Cleanup

Edit relevant `conftest.py` files to add cleanup:

```python
# In tests/conftest.py or tests/integration/conftest.py

import pytest
from app.server.database.db_adapter import db_adapter

@pytest.fixture(autouse=True)
def clean_workflow_history():
    """Clean workflow_history table before each test."""
    yield  # Test runs here

    # Cleanup after test
    try:
        with db_adapter.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM workflow_history")
            conn.commit()
    except Exception as e:
        print(f"Warning: Could not clean workflow_history: {e}")


@pytest.fixture(autouse=True)
def clean_database():
    """Clean all test data between tests."""
    yield  # Test runs here

    # Cleanup after test
    try:
        with db_adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Clean tables in correct order (respect foreign keys)
            tables_to_clean = [
                'workflow_history',
                'phase_queue',
                'adw_metadata',
                # Add other tables as needed
            ]

            for table in tables_to_clean:
                try:
                    cursor.execute(f"DELETE FROM {table}")
                except Exception as e:
                    # Table might not exist in all test scenarios
                    pass

            conn.commit()
    except Exception as e:
        print(f"Warning: Could not clean database: {e}")
```

**Alternative: Use Transactions for Isolation**

Better approach - use database transactions:

```python
@pytest.fixture(autouse=True)
def db_transaction():
    """Wrap each test in a transaction that gets rolled back."""
    conn = db_adapter.get_connection()

    # Start transaction
    yield conn

    # Rollback after test (don't commit)
    try:
        conn.rollback()
    except:
        pass
    finally:
        conn.close()
```

#### Step 3d: Fix Specific Test Files

Check the failing test files for hardcoded adw_id values:

```bash
# Find tests using hardcoded adw_id
grep -n "adw_id.*=.*[0-9]" tests/test_workflow_history.py tests/integration/test_workflow_history_integration.py

# Look for patterns like:
# adw_id=1
# adw_id=123
# etc.
```

Change hardcoded values to unique values or use auto-generated UUIDs:

```python
# Before (causes conflicts):
def test_something():
    item = WorkflowHistory(adw_id=1, ...)  # Always uses 1!

# After (unique values):
import uuid

def test_something():
    item = WorkflowHistory(adw_id=str(uuid.uuid4()), ...)

# Or use a counter:
_test_counter = 0

def test_something():
    global _test_counter
    _test_counter += 1
    item = WorkflowHistory(adw_id=f"test_{_test_counter}", ...)
```

### Step 4: Fix Issue #3 - Missing adw_locks Table

#### Step 4a: Check if Table Exists in Schema

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

# Check PostgreSQL schema
grep -i "adw_locks" migration/postgres_schema.sql

# Check for any SQL files with the schema
find . -name "*.sql" -type f -exec grep -l "adw_locks" {} \;
```

#### Step 4b: Find Table Definition

If table exists in schema:
```bash
# Get the full CREATE TABLE statement
grep -A 15 "CREATE TABLE.*adw_locks" migration/postgres_schema.sql
```

If table doesn't exist in schema, find it in the codebase:
```bash
# Find where adw_locks is created
cd app/server
grep -r "CREATE TABLE.*adw_locks" --include="*.py"

# Expected: repository or migration file
```

#### Step 4c: Add to Test Database Setup

Find the test database initialization:

```bash
# Find test setup files
find app/server/tests -name "conftest.py" -exec grep -l "CREATE TABLE" {} \;
find app/server/tests -name "*.py" -exec grep -l "test_database" {} \;
```

Add adw_locks table creation to test setup. Example:

```python
# In tests/conftest.py

@pytest.fixture(scope="session")
def setup_test_database():
    """Create test database schema."""
    conn = db_adapter.get_connection()
    cursor = conn.cursor()

    # Create adw_locks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS adw_locks (
            lock_id INTEGER PRIMARY KEY AUTOINCREMENT,
            adw_id TEXT NOT NULL UNIQUE,
            lock_type TEXT NOT NULL,
            locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            locked_by TEXT,
            status TEXT DEFAULT 'active'
        )
    """)

    # Create other tables...

    conn.commit()
    conn.close()
```

#### Step 4d: Verify Table in PostgreSQL

```bash
# Add to PostgreSQL schema if missing
docker exec -i tac-webbuilder-postgres psql -U tac_user -d tac_webbuilder <<EOF
CREATE TABLE IF NOT EXISTS adw_locks (
    lock_id SERIAL PRIMARY KEY,
    adw_id TEXT NOT NULL UNIQUE,
    lock_type VARCHAR(50) NOT NULL,
    locked_at TIMESTAMP DEFAULT NOW(),
    locked_by VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active'
);
EOF

# Verify table exists
docker exec -it tac-webbuilder-postgres psql -U tac_user -d tac_webbuilder -c "\dt adw_locks"

# Expected: Table listed
```

### Step 5: Run Tests to Verify Fixes

#### Step 5a: Test with SQLite

```bash
cd app/server
export DB_TYPE=sqlite

# Run full test suite
uv run pytest tests/ -v --tb=short | tee /tmp/phase4_sqlite_after.txt

# Count results
grep -E "passed|failed|error" /tmp/phase4_sqlite_after.txt | tail -1

# Expected: Should still have ~572 passed (no regression)
```

#### Step 5b: Test with PostgreSQL

```bash
export DB_TYPE=postgresql
export POSTGRES_HOST=127.0.0.1
export POSTGRES_PORT=5432
export POSTGRES_DB=tac_webbuilder
export POSTGRES_USER=tac_user
export POSTGRES_PASSWORD=changeme

# Run full test suite
uv run pytest tests/ -v --tb=short | tee /tmp/phase4_postgres_after.txt

# Count results
grep -E "passed|failed|error" /tmp/phase4_postgres_after.txt | tail -1

# Expected: ~648 passed (563 + 85 fixes)
# Actual may vary slightly
```

#### Step 5c: Compare Results

```bash
# Create comparison report
cat > /tmp/phase4_comparison.txt <<EOF
Phase 4.1 Test Results Comparison

SQLite:
Before: $(grep -E "passed" /tmp/phase4_sqlite_before.txt | tail -1)
After:  $(grep -E "passed" /tmp/phase4_sqlite_after.txt | tail -1)

PostgreSQL:
Before: $(grep -E "passed" /tmp/phase4_postgres_before.txt | tail -1)
After:  $(grep -E "passed" /tmp/phase4_postgres_after.txt | tail -1)

Target: +85 tests passing with PostgreSQL
EOF

cat /tmp/phase4_comparison.txt
```

### Step 6: Run Specific Test Groups

Test each fix individually to verify:

#### Test queue_position Fix (Issue #1)

```bash
cd app/server
export DB_TYPE=postgresql

# Run phase queue tests
uv run pytest tests/services/test_phase_coordinator.py -v
uv run pytest tests/services/test_phase_queue_service.py -v

# Expected: All tests pass (were 38 failures)
```

#### Test Isolation Fix (Issue #2)

```bash
# Run workflow history tests
uv run pytest tests/test_workflow_history.py -v
uv run pytest tests/integration/test_workflow_history_integration.py -v
uv run pytest tests/integration/test_database_operations.py -v

# Expected: No more UNIQUE constraint failures
```

#### Test adw_locks Fix (Issue #3)

```bash
# Run lock-related tests
uv run pytest tests/integration/test_database_operations.py -k "lock" -v

# Expected: All lock tests pass (were 7 failures)
```

### Step 7: Update Documentation

Update `POSTGRES_TEST_RESULTS.md` with Phase 4.1 results:

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

# Add Phase 4.1 section to test results
cat >> POSTGRES_TEST_RESULTS.md <<EOF

---

## Phase 4.1 Results ($(date +%Y-%m-%d))

### Fixes Applied

1. ✅ **Added queue_position Column**
   - Location: phase_queue table
   - Files Modified: migration/postgres_schema.sql, repositories/phase_queue_repository.py
   - Tests Fixed: 38

2. ✅ **Improved Test Isolation**
   - Location: tests/conftest.py, test files
   - Approach: [Transaction rollback / DELETE cleanup / UUID generation]
   - Tests Fixed: 40+

3. ✅ **Added adw_locks Table**
   - Location: Test database initialization
   - Files Modified: tests/conftest.py, migration/postgres_schema.sql
   - Tests Fixed: 7

### Test Results After Phase 4.1

**SQLite:**
- Before: 572/766 passed (74.7%)
- After: [fill in] passed ([fill in]%)
- Change: [fill in]

**PostgreSQL:**
- Before: 563/766 passed (73.5%)
- After: [fill in] passed ([fill in]%)
- Change: +[fill in] tests

### Remaining Issues
- Phase 4.2: PRAGMA compatibility (1-2 failures)
- Phase 4.2: Column case sensitivity (2 failures)
- Pre-existing: Database initialization errors (100 errors)

EOF
```

### Step 8: Commit Changes

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

# Check what changed
git status

# Expected changes:
# - migration/postgres_schema.sql (queue_position column, adw_locks table)
# - app/server/repositories/phase_queue_repository.py (queue_position)
# - app/server/tests/conftest.py (test isolation fixtures)
# - Possibly: test files (UUID generation for adw_id)
# - POSTGRES_TEST_RESULTS.md (updated with Phase 4.1 results)

# Stage changes
git add migration/postgres_schema.sql
git add app/server/repositories/phase_queue_repository.py
git add app/server/tests/conftest.py
git add POSTGRES_TEST_RESULTS.md
# Add any other modified files

# Commit
git commit -m "$(cat <<'EOF'
fix: PostgreSQL migration Phase 4.1 - Critical schema and test fixes

Fixed 85 critical test failures blocking PostgreSQL migration:

Issue #1: Missing queue_position Column (38 failures fixed)
- Added queue_position INTEGER column to phase_queue table
- Updated PostgreSQL schema: migration/postgres_schema.sql
- Updated repository: repositories/phase_queue_repository.py
- Applied migration to existing PostgreSQL database

Issue #2: Test Isolation - UNIQUE Constraints (40+ failures fixed)
- Added database cleanup fixtures in tests/conftest.py
- [Transaction rollback / DELETE cleanup / UUID generation approach]
- Prevents UNIQUE constraint violations on workflow_history.adw_id
- Ensures clean database state between tests

Issue #3: Missing adw_locks Table (7 failures fixed)
- Added adw_locks table to PostgreSQL schema
- Added table creation to test database setup
- Enables lock acquisition and management tests

Test Results:
- PostgreSQL: 563 → [new count] passing tests (+[increase])
- SQLite: No regression (still ~572 passing)
- Target: 85 additional tests passing

Files Modified:
- migration/postgres_schema.sql - Added queue_position, adw_locks
- app/server/repositories/phase_queue_repository.py - queue_position support
- app/server/tests/conftest.py - Test isolation fixtures
- POSTGRES_TEST_RESULTS.md - Phase 4.1 results

Next: Phase 4.2 - PostgreSQL compatibility fixes (PRAGMA, case sensitivity)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# Push to remote
git push
```

---

## Success Criteria

- ✅ queue_position column added to phase_queue table (both DBs)
- ✅ Test isolation improved (no more UNIQUE constraint failures)
- ✅ adw_locks table exists in both production and test databases
- ✅ PostgreSQL tests: +85 passing (563 → ~648)
- ✅ SQLite tests: No regression (still ~572 passing)
- ✅ All Phase 4.1 specific tests pass
- ✅ Changes committed with descriptive message
- ✅ Documentation updated

## Files Expected to Change

**Modified:**
- `migration/postgres_schema.sql` - Added queue_position, adw_locks
- `app/server/repositories/phase_queue_repository.py` - queue_position support
- `app/server/tests/conftest.py` - Test isolation fixtures
- `POSTGRES_TEST_RESULTS.md` - Phase 4.1 results
- Possibly: Individual test files if using UUID approach

**No Changes Expected:**
- Core application code (these are schema/test fixes)
- Other repositories (unless they use queue_position)

## Troubleshooting

### queue_position Column Issues

**Error: "no such column: queue_position" persists**
```bash
# Verify column was added to PostgreSQL
docker exec -it tac-webbuilder-postgres psql -U tac_user -d tac_webbuilder -c "\d phase_queue"

# Should see queue_position in the list

# If missing, add manually:
docker exec -i tac-webbuilder-postgres psql -U tac_user -d tac_webbuilder <<EOF
ALTER TABLE phase_queue ADD COLUMN queue_position INTEGER;
EOF

# For SQLite test database, delete and recreate:
rm app/server/test_database.db
# Tests will recreate it with new schema
```

**Error: Column exists but tests still fail**
- Check repository CREATE TABLE statement includes queue_position
- Verify INSERT/UPDATE queries include queue_position
- Check for typos: queue_position vs queuePosition vs queue-position

### Test Isolation Issues

**Error: UNIQUE constraint failures still occur**
```bash
# Verify fixtures are being used
cd app/server
grep -A 5 "autouse=True" tests/conftest.py

# Should see clean_database or similar fixture with autouse=True

# If missing, fixtures may not be running
# Check pytest is finding conftest.py:
uv run pytest --fixtures | grep -i clean

# Run single test to debug:
uv run pytest tests/test_workflow_history.py::test_name -v -s
```

**Fixtures not running:**
- Ensure `autouse=True` is set
- Check fixture scope (function, class, module, session)
- Verify conftest.py is in correct location

**Transactions not rolling back:**
- Check database adapter supports transactions
- Verify COMMIT is not being called in fixtures
- May need explicit BEGIN/ROLLBACK

### adw_locks Table Issues

**Error: "no such table: adw_locks" persists**
```bash
# Check if table exists in PostgreSQL
docker exec -it tac-webbuilder-postgres psql -U tac_user -d tac_webbuilder -c "\dt adw_locks"

# If missing, create it:
docker exec -i tac-webbuilder-postgres psql -U tac_user -d tac_webbuilder <<EOF
CREATE TABLE adw_locks (
    lock_id SERIAL PRIMARY KEY,
    adw_id TEXT NOT NULL UNIQUE,
    lock_type VARCHAR(50) NOT NULL,
    locked_at TIMESTAMP DEFAULT NOW(),
    locked_by VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active'
);
EOF

# For SQLite, check test setup creates the table
grep -A 10 "CREATE TABLE.*adw_locks" tests/conftest.py
```

### General Test Issues

**Tests pass individually but fail when run together:**
- Test isolation issue - cleanup not working
- Try running with `--forked` flag: `pytest --forked`
- Or use separate database per test

**Different failures between SQLite and PostgreSQL:**
- Check data type compatibility
- Verify placeholder usage (? vs %s)
- Check for database-specific SQL

**Performance degraded after fixes:**
- Transaction overhead may slow tests
- Consider using in-memory database for tests
- Optimize cleanup queries

---

## Expected Improvements

### Before Phase 4.1
```
PostgreSQL: 563/766 passed (73.5%)
SQLite: 572/766 passed (74.7%)
Gap: -9 tests
```

### After Phase 4.1
```
PostgreSQL: ~648/766 passed (84.6%)
SQLite: ~572/766 passed (74.7%)
Gap: +76 tests (PostgreSQL ahead!)
```

### Remaining Issues for Phase 4.2
```
PRAGMA compatibility: 1-2 failures
Column case sensitivity: 2 failures
Total remaining: 3-4 failures (vs 89 before)
```

---

## Next Steps

After completing Phase 4.1:

1. **Verify Success**
   - Run full test suite with both databases
   - Compare before/after results
   - Confirm +85 tests passing

2. **Document Results**
   - Update POSTGRES_TEST_RESULTS.md
   - Update POSTGRES_MIGRATION_TRACKER.md
   - Note any unexpected issues

3. **Proceed to Phase 4.2**
   - Use POSTGRES_PHASE4_COMPATIBILITY_FIXES.md
   - Fix remaining 3-4 PostgreSQL-specific failures
   - PRAGMA → information_schema
   - Column case sensitivity

4. **Report Back**
```
✅ Phase 4.1 Complete - Critical Fixes Applied

Fixes:
- ✅ queue_position column added
- ✅ Test isolation improved
- ✅ adw_locks table added

Results:
- PostgreSQL: [before] → [after] tests passing (+[increase])
- SQLite: [count] tests passing (no regression)

Issues Encountered:
- [list any problems and solutions]

Ready for: Phase 4.2 - PostgreSQL Compatibility Fixes
```

---

**Ready to copy into a new context!**

This prompt will fix the 3 critical issues blocking PostgreSQL migration, improving test pass rate from 73.5% to ~85%.
