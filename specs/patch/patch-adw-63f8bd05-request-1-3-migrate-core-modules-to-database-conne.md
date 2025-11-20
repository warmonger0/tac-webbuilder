# Patch: Migrate Core Modules to Database Connection Utility

## Metadata
adw_id: `63f8bd05`
review_change_request: `Migrate insights.py and sql_processor.py to use the centralized database connection utility created in Request 1.1`

## Issue Summary
**Original Spec:** specs/issue-52-migrate-core-modules-to-database-connection-utility.md
**Issue:** Two core modules (insights.py and sql_processor.py) have manual sqlite3.connect() calls that need to be replaced with the centralized database connection utility
**Solution:** Replace all 3 manual database connections with the get_connection() context manager from utils.db_connection

## Files to Modify
Use these files to implement the patch:

1. `app/server/core/insights.py` - Replace sqlite3.connect() on line 16
2. `app/server/core/sql_processor.py` - Replace sqlite3.connect() on lines 16 and 64

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update insights.py to use db_connection utility
- Add import statement: `from utils.db_connection import get_connection`
- Replace the manual connection pattern on line 16:
  - Replace: `conn = sqlite3.connect("db/database.db")`
  - With: Use `get_connection()` context manager to wrap database operations
- Remove manual `conn.close()` call on line 118 (no longer needed with context manager)
- Ensure all cursor operations remain inside the context manager scope

### Step 2: Update sql_processor.py to use db_connection utility (first occurrence)
- Add import statement: `from utils.db_connection import get_connection`
- Update `execute_sql_safely()` function (lines 7-57):
  - Replace manual connection on line 16: `conn = sqlite3.connect("db/database.db")`
  - Wrap database operations with `get_connection()` context manager
  - Remove manual `conn.close()` call on line 38
  - Preserve row_factory setting (already handled by get_connection)

### Step 3: Update sql_processor.py to use db_connection utility (second occurrence)
- Update `get_database_schema()` function (lines 59-115):
  - Replace manual connection on line 64: `conn = sqlite3.connect("db/database.db")`
  - Wrap database operations with `get_connection()` context manager
  - Remove manual `conn.close()` call on line 110

### Step 4: Verify imports and remove unused sqlite3 imports if appropriate
- Keep `sqlite3` import in both files (still needed for sqlite3.Row type and cursor operations)
- Ensure proper import order (stdlib imports before local imports)

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. **Python Syntax Check**
   ```bash
   cd app/server && uv run python -m py_compile core/insights.py core/sql_processor.py
   ```
   - Purpose: Verify no syntax errors were introduced

2. **Backend Code Quality Check**
   ```bash
   cd app/server && uv run ruff check core/insights.py core/sql_processor.py
   ```
   - Purpose: Ensure code quality standards are met

3. **All Backend Tests**
   ```bash
   cd app/server && uv run pytest tests/ -v --tb=short
   ```
   - Purpose: Verify all existing tests pass with no functional changes

## Patch Scope
**Lines of code to change:** ~15 lines (3 connection replacements, 3 close removals, 2 imports)
**Risk level:** Low - Using established pattern, no functional changes
**Testing required:** All backend tests must pass, no new tests needed
