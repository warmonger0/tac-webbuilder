# Patch: Migrate server.py to Database Connection Utility

## Metadata
adw_id: `7dc3d593`
review_change_request: `Migrate app/server/server.py to use the centralized database connection utility created in Request 1.1. Replace all 4 manual sqlite3.connect() calls with the db_connection utility at lines 596, 664, 1801, and 1836.`

## Issue Summary
**Original Spec:** Issue #50 - Request 1.2: Migrate server.py to Database Connection Utility
**Issue:** server.py contains 4 manual sqlite3.connect() calls that duplicate connection handling logic, violating DRY principles. These manual connections lack proper transaction management, retry logic, and row factory configuration.
**Solution:** Replace all 4 manual database connections with the centralized `get_connection()` utility from `app/server/utils/db_connection.py`. This will eliminate duplicate code, add automatic commit/rollback, retry logic for SQLITE_BUSY errors, and enable dict-like row access.

## Files to Modify
- `app/server/server.py` (4 locations: lines 596, 664, 1801, 1836)

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add import for db_connection utility
- Add `from app.server.utils.db_connection import get_connection` to imports section (after line 15, near other imports from core/)
- Place after existing core module imports to maintain consistency

### Step 2: Replace manual connection in health_check function (line 596)
- Replace lines 596-600:
  ```python
  conn = sqlite3.connect("db/database.db")
  cursor = conn.cursor()
  cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
  tables = cursor.fetchall()
  conn.close()
  ```
- With:
  ```python
  with get_connection() as conn:
      cursor = conn.cursor()
      cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
      tables = cursor.fetchall()
  ```
- Note: No manual commit/close needed, handled by context manager

### Step 3: Replace manual connection in get_system_status function (line 664)
- Replace lines 664-668:
  ```python
  conn = sqlite3.connect("db/database.db")
  cursor = conn.cursor()
  cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
  tables = cursor.fetchall()
  conn.close()
  ```
- With:
  ```python
  with get_connection() as conn:
      cursor = conn.cursor()
      cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
      tables = cursor.fetchall()
  ```

### Step 4: Replace manual connection in delete_table function (line 1801)
- Replace lines 1801-1816:
  ```python
  conn = sqlite3.connect("db/database.db")

  # Check if table exists using secure method
  if not check_table_exists(conn, table_name):
      conn.close()
      raise HTTPException(404, f"Table '{table_name}' not found")

  # Drop the table using safe query execution with DDL permission
  execute_query_safely(
      conn,
      "DROP TABLE IF EXISTS {table}",
      identifier_params={'table': table_name},
      allow_ddl=True
  )
  conn.commit()
  conn.close()
  ```
- With:
  ```python
  with get_connection() as conn:
      # Check if table exists using secure method
      if not check_table_exists(conn, table_name):
          raise HTTPException(404, f"Table '{table_name}' not found")

      # Drop the table using safe query execution with DDL permission
      execute_query_safely(
          conn,
          "DROP TABLE IF EXISTS {table}",
          identifier_params={'table': table_name},
          allow_ddl=True
      )
  ```
- Note: Commit automatically handled by context manager, no need for manual close

### Step 5: Replace manual connection in export_table function (line 1836)
- Replace lines 1836-1845:
  ```python
  # Connect to database
  conn = sqlite3.connect("db/database.db")

  # Check if table exists
  if not check_table_exists(conn, request.table_name):
      conn.close()
      raise HTTPException(404, f"Table '{request.table_name}' not found")

  # Generate CSV
  csv_data = generate_csv_from_table(conn, request.table_name)
  conn.close()
  ```
- With:
  ```python
  # Connect to database
  with get_connection() as conn:
      # Check if table exists
      if not check_table_exists(conn, request.table_name):
          raise HTTPException(404, f"Table '{request.table_name}' not found")

      # Generate CSV
      csv_data = generate_csv_from_table(conn, request.table_name)
  ```

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. **Python Syntax Check**
   ```bash
   cd app/server && uv run python -m py_compile server.py
   ```

2. **Backend Code Quality Check**
   ```bash
   cd app/server && uv run ruff check .
   ```

3. **All Backend Tests**
   ```bash
   cd app/server && uv run pytest tests/ -v --tb=short
   ```

4. **Verify health check endpoint works**
   ```bash
   curl http://localhost:8000/api/health
   ```

5. **Verify system status endpoint works**
   ```bash
   curl http://localhost:8000/api/system-status
   ```

## Patch Scope
**Lines of code to change:** ~30 lines (4 connection patterns simplified)
**Risk level:** Low (direct replacement of equivalent functionality with better error handling)
**Testing required:** Run full backend test suite to ensure database operations (health checks, table deletion, table export) work correctly with context manager
