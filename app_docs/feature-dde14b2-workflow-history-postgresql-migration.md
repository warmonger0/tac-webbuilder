# Workflow History PostgreSQL Migration

**ADW ID:** dde14b2
**Date:** 2025-12-12
**Specification:** N/A (Technical debt cleanup from session summary)

## Overview

Migrated ADW workflow tracking from hardcoded SQLite paths to PostgreSQL-only architecture using the database adapter pattern. This eliminates split-brain database issues where some workflows wrote to SQLite files while backend services read from PostgreSQL, ensuring all workflow data resides in a centralized, production-grade database.

## What Was Built

- **Database adapter integration** in ADW review workflows
- **ToolRegistry refactoring** for PostgreSQL support
- **tool_calls table** auto-creation on initialization
- **Archived SQLite files** with proper cleanup

## Technical Implementation

### Files Modified

- `adws/adw_review_iso.py`: Refactored `validate_review_data_integrity` function to use database adapter instead of direct SQLite queries
- `adws/adw_modules/tool_registry.py`: Complete ToolRegistry class refactoring from SQLite to database adapter
- `db/workflow_history.db`: Archived as `workflow_history.db.sqlite-archive` (empty, 0 bytes)

### Key Changes

**adws/adw_review_iso.py** (validate_review_data_integrity function):
- **Before:** Direct `sqlite3.connect()` to hardcoded `workflow_history.db` path
- **After:** Dynamic database adapter import from worktree context with proper sys.path management
- **Impact:** Review workflow validation now works with PostgreSQL, maintaining compatibility with worktree isolation

**adws/adw_modules/tool_registry.py** (ToolRegistry class):
- **Removed:** Hardcoded `DB_PATH` constant pointing to SQLite file
- **Added:** Database adapter initialization with automatic table creation
- **Refactored methods:**
  - `__init__()` - Loads adapter, creates tool_calls table if missing
  - `_ensure_tables_exist()` - Database-agnostic table creation with PostgreSQL/SQLite syntax
  - `get_all_tools()` - Adapter-based queries with proper parameter placeholders (%s vs ?)
  - `register_tool()` - Database-agnostic INSERT with error handling
  - `update_tool_metrics()` - Dynamic SQL generation for PostgreSQL/SQLite
  - `_log_invocation()` - Adapter-based tool call logging

**Database tables** (PostgreSQL):
- `workflow_history` - 74 columns, already existed (created by schema.py)
- `adw_tools` - Tool registry definitions, already existed
- `tool_calls` - Tool invocation logging, created by ToolRegistry on first init

### Architecture Benefits

1. **True PostgreSQL-only architecture** - No file-based databases
2. **No split-brain** - All workflow data in centralized PostgreSQL
3. **Better observability** - Unified database for analytics and monitoring
4. **Database-agnostic code** - Works with both PostgreSQL and SQLite via adapter
5. **Eliminates file dependencies** - No hardcoded paths in ADW workflows

## How to Use

### For ADW Workflows

ADW workflows automatically use PostgreSQL through the database adapter:

```python
# adw_review_iso.py - validate_review_data_integrity
from database import get_database_adapter
adapter = get_database_adapter()
with adapter.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM workflow_history")
    # Works with PostgreSQL or SQLite based on DB_TYPE env var
```

### For Tool Registry

Tool registry initialization automatically handles PostgreSQL:

```python
from adw_modules.tool_registry import ToolRegistry

registry = ToolRegistry()  # Initializes with PostgreSQL adapter
tools = registry.get_all_tools()  # Queries PostgreSQL
```

## Configuration

**Environment variables** (required):
- `POSTGRES_HOST` - PostgreSQL host (default: localhost)
- `POSTGRES_PORT` - PostgreSQL port (default: 5432)
- `POSTGRES_DB` - Database name (default: tac_webbuilder)
- `POSTGRES_USER` - Database user
- `POSTGRES_PASSWORD` - Database password
- `DB_TYPE` - Must be set to "postgresql" for production

**Database adapter** (automatic):
- Located in `app/server/database/factory.py`
- Returns PostgreSQLAdapter when `DB_TYPE=postgresql`
- Handles connection pooling and query execution

## Testing

### Unit Testing

```bash
# Test database adapter initialization
cd app/server
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder \
POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql \
.venv/bin/python3 -c "from database import get_database_adapter; \
adapter = get_database_adapter(); print(f'✅ Adapter: {adapter.get_db_type()}')"
```

### Integration Testing

```bash
# Test ToolRegistry with PostgreSQL
cd app/server
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder \
POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql \
.venv/bin/python3 -c "
import sys; sys.path.insert(0, '../../adws/adw_modules')
from tool_registry import ToolRegistry
registry = ToolRegistry()
print(f'✅ Tools: {len(registry.get_all_tools())}')"
```

### E2E Workflow Testing

```bash
# Run ADW workflow to verify PostgreSQL integration
cd adws
uv run adw_sdlc_complete_iso.py <issue_number>
# Verify workflow_history records in PostgreSQL (not SQLite)
```

## Database State

After migration:

```sql
-- PostgreSQL tables (tac_webbuilder database)
workflow_history    -- 74 columns, workflow tracking
adw_tools          -- Tool registry definitions
tool_calls         -- Tool invocation logging

-- Archived SQLite files (no longer used)
db/workflow_history.db.sqlite-archive  -- 0 bytes, empty
```

## Migration Impact

**Changed files:**
- `adws/adw_modules/tool_registry.py`: +139 lines, -137 lines
- `adws/adw_review_iso.py`: +38 lines, -38 lines

**Database operations:**
- All workflow history queries → PostgreSQL
- All tool registry operations → PostgreSQL
- No more file-based SQLite dependencies

**Backward compatibility:**
- Database adapter supports both PostgreSQL and SQLite
- Set `DB_TYPE=sqlite` to fall back to SQLite (not recommended)

## Notes

### Why This Migration Was Needed

The previous architecture had a split-brain problem:
- Backend services (`app/server/`) read from PostgreSQL
- ADW workflows (`adws/`) wrote to SQLite files
- This caused data inconsistency and silent failures

### What Changed

- **Before:** `adws/adw_review_iso.py` queried `db/workflow_history.db` directly
- **Before:** `adws/adw_modules/tool_registry.py` used hardcoded `DB_PATH` to SQLite
- **After:** Both use `get_database_adapter()` to access PostgreSQL

### Future Considerations

1. **Integration test fixes** - 9 failing tests may be resolved by this migration
2. **E2E validation** - Run full ADW workflow to verify PostgreSQL tracking
3. **Observability** - All workflow data now queryable from centralized database
4. **Backup/restore** - PostgreSQL backup procedures should be documented

### Related Documentation

- Migration 010: Pattern predictions tracking (PostgreSQL)
- Database adapter factory: `app/server/database/factory.py`
- Workflow history schema: `app/server/core/workflow_history_utils/database/schema.py`
