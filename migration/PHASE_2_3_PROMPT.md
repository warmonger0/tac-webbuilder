# Task: PostgreSQL Migration - Phase 2.3: Convert Datetime Functions

## Context
I'm working on the tac-webbuilder project. We're migrating from SQLite to PostgreSQL. Phase 2.2 is complete (all placeholders converted). Now in **Phase 2.3 of 6** - converting datetime functions to be database-agnostic.

## Objective
Convert all `datetime('now')` and `CURRENT_TIMESTAMP` calls to use `adapter.now_function()`, enabling the same queries to work with both SQLite and PostgreSQL.

## Background Information
- **Phase 2.2 Status:** ✅ Complete - All placeholders converted
- **Current Pattern:** Hardcoded `datetime('now')` (SQLite-only)
- **Target Pattern:** Dynamic `adapter.now_function()`
- **Total Occurrences:** ~40 datetime function calls
- **Risk Level:** Low (simple string replacement)
- **Estimated Time:** 1 hour

## Step-by-Step Instructions

### Step 1: Find All Datetime Functions

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Find datetime('now')
grep -rn "datetime('now')" . --include="*.py"

# Find CURRENT_TIMESTAMP
grep -rn "CURRENT_TIMESTAMP" . --include="*.py"

# Count total
grep -rn "datetime('now')\|CURRENT_TIMESTAMP" . --include="*.py" | wc -l
```

**Expected:** ~40 occurrences

### Step 2: Add Helper to query_helpers.py

Update `utils/query_helpers.py`:

```python
def get_now_function() -> str:
    """
    Get the current database's NOW() function.

    Returns:
        "datetime('now')" for SQLite, "NOW()" for PostgreSQL
    """
    return get_database_adapter().now_function()
```

### Step 3: Convert Simple NOW() Usage

**Pattern 1: In DEFAULT clauses (schema-level - ignore for now)**
```sql
-- These are in schema files, not Python code
created_at TEXT DEFAULT CURRENT_TIMESTAMP  -- SQLite schema
created_at TIMESTAMP DEFAULT NOW()  -- PostgreSQL schema
```

**Pattern 2: In INSERT statements (Python code - update these)**

```python
# Before
cursor.execute("""
    INSERT INTO table (id, created_at)
    VALUES (?, datetime('now'))
""", (id_val,))

# After
from utils.query_helpers import get_placeholder, get_now_function
ph = get_placeholder()
now = get_now_function()
cursor.execute(f"""
    INSERT INTO table (id, created_at)
    VALUES ({ph}, {now})
""", (id_val,))
```

**Pattern 3: In UPDATE statements**

```python
# Before
cursor.execute("""
    UPDATE table
    SET updated_at = datetime('now')
    WHERE id = ?
""", (id_val,))

# After
from utils.query_helpers import get_placeholder, get_now_function
ph = get_placeholder()
now = get_now_function()
cursor.execute(f"""
    UPDATE table
    SET updated_at = {now}
    WHERE id = {ph}
""", (id_val,))
```

### Step 4: Update Repository Files

Find and update all datetime usage:

```bash
# Find in repositories
grep -rn "datetime('now')" repositories/

# Example files to update
# - repositories/workflow_history_repository.py
# - repositories/phase_queue_repository.py
# - repositories/tool_calls_repository.py
```

**Example:**

```python
# Before
def create_workflow(self, data):
    cursor.execute("""
        INSERT INTO workflow_history (adw_id, status, created_at, updated_at)
        VALUES (?, ?, datetime('now'), datetime('now'))
    """, (data['adw_id'], data['status']))

# After
def create_workflow(self, data):
    from utils.query_helpers import build_placeholders, get_now_function
    ph_list = build_placeholders(2)
    now = get_now_function()
    cursor.execute(f"""
        INSERT INTO workflow_history (adw_id, status, created_at, updated_at)
        VALUES ({ph_list}, {now}, {now})
    """, (data['adw_id'], data['status']))
```

### Step 5: Handle Trigger Updates

SQLite triggers use `datetime('now')`, PostgreSQL triggers use `NOW()`.

**SQLite trigger (in sqlite schema):**
```sql
CREATE TRIGGER trigger_update_pattern_timestamp
AFTER UPDATE ON operation_patterns
FOR EACH ROW
BEGIN
    UPDATE operation_patterns
    SET updated_at = datetime('now')
    WHERE id = NEW.id;
END;
```

**PostgreSQL trigger (already in postgres_schema.sql):**
```sql
CREATE OR REPLACE FUNCTION trigger_update_pattern_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

**No Python code changes needed for triggers** - they're schema-level.

### Step 6: Update DEFAULT Values (Pass Parameter Instead)

Best practice: Pass timestamp as a parameter rather than using SQL function:

```python
# Instead of relying on DEFAULT
from datetime import datetime

# Option 1: Python datetime (recommended)
now = datetime.now()
cursor.execute(f"""
    INSERT INTO table (id, created_at)
    VALUES ({ph}, {ph})
""", (id_val, now))

# Option 2: Database function
now_func = get_now_function()
cursor.execute(f"""
    INSERT INTO table (id, created_at)
    VALUES ({ph}, {now_func})
""", (id_val,))  # Note: No parameter for now_func
```

### Step 7: Run Tests After Each Update

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Test with SQLite
DB_TYPE=sqlite pytest tests/repositories/test_workflow_history_repository.py -v

# Test with PostgreSQL
DB_TYPE=postgresql pytest tests/repositories/test_workflow_history_repository.py -v
```

### Step 8: Verify No Hardcoded Datetime Remains

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Find remaining datetime('now') in Python files
grep -rn "datetime('now')" . --include="*.py" | grep -v ".sql"

# Should only find schema files (if any)
```

**Expected:** 0 occurrences in Python files

### Step 9: Run Full Test Suite

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Test both databases
DB_TYPE=sqlite pytest tests/ -v
DB_TYPE=postgresql pytest tests/ -v
```

**Expected:** All tests passing with both databases

### Step 10: Commit Changes

```bash
git add app/server/
git commit -m "$(cat <<'EOF'
refactor: Convert to database-agnostic datetime functions (Phase 2.3)

Replaced all hardcoded datetime('now') with dynamic functions.

Phase 2.3 Complete (1 hour):
✅ Converted ~40 datetime function calls
✅ Added get_now_function() helper
✅ All repositories updated
✅ All services updated
✅ Tests passing with both SQLite and PostgreSQL

Query Helper Addition:
- get_now_function() - Returns datetime('now') or NOW()

Migration Pattern:
OLD: INSERT INTO table (created_at) VALUES (datetime('now'))
NEW: now = get_now_function()
     INSERT INTO table (created_at) VALUES ({now})

Benefits:
- Same queries work with SQLite and PostgreSQL
- Consistent timestamp handling
- Database-agnostic datetime logic

Files Modified:
~ utils/query_helpers.py (added get_now_function)
~ repositories/*.py (5 files)
~ services/*.py (8 files)

Testing:
- SQLite: All tests passing ✅
- PostgreSQL: All tests passing ✅

Phase 2 Complete (6 hours total):
✅ 2.1: Updated get_connection() calls (79)
✅ 2.2: Converted placeholders (160)
✅ 2.3: Converted datetime functions (40)

Next: Phase 3 - Data Migration (2 hours)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Success Criteria

- ✅ All ~40 datetime calls converted
- ✅ get_now_function() helper created
- ✅ No hardcoded `datetime('now')` in Python
- ✅ All tests passing with SQLite
- ✅ All tests passing with PostgreSQL
- ✅ Phase 2 fully complete
- ✅ Changes committed

## Files Expected to Change

**Modified:**
- `utils/query_helpers.py` (add get_now_function)
- `repositories/*.py` (~5 files)
- `services/*.py` (~8 files)

## Troubleshooting

**If datetime import conflicts occur:**
```python
# Be explicit
from datetime import datetime as py_datetime  # Python datetime
now_func = get_now_function()  # SQL function
```

**If tests fail with timestamp comparison:**
```python
# PostgreSQL timestamps may have different precision
# Use date comparison or round to seconds
```

## Next Steps

After completing Phase 2.3, report:
- "Phase 2.3 complete - All datetime functions converted ✅"
- "Phase 2 COMPLETE - Code changes done ✅"
- Both databases tested successfully

**Next Task:** Phase 3 - Data Migration (SQLite → PostgreSQL, 2 hours)

---

**Ready to copy into a new chat!** 🚀
