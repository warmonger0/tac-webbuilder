# Phase 5 Refactoring Plan - database.py

**Date:** 2025-01-24
**Status:** 🟡 Planned (Schema module extracted, remaining modules pending)
**Target File:** database.py (666 lines)
**Estimated New Modules:** 5
**Estimated Line Count:** 666 → ~740 lines (+11% for structure)

---

## Summary

Phase 5 targets `database.py` (666 lines) - a monolithic database module containing all CRUD operations, schema management, and analytics queries. This module will be refactored into a clean package structure following the repository pattern.

---

## Current Structure Analysis

**database.py (666 lines)**
```python
# Functions:
1. init_db() - Lines 21-135 (115 lines) - Schema initialization
2. insert_workflow_history() - Lines 137-247 (110 lines) - INSERT operation
3. update_workflow_history_by_issue() - Lines 247-295 (48 lines) - UPDATE by issue
4. update_workflow_history() - Lines 295-368 (73 lines) - UPDATE by adw_id
5. get_workflow_by_adw_id() - Lines 368-409 (41 lines) - SELECT single
6. get_workflow_history() - Lines 409-553 (144 lines) - SELECT with filters
7. get_history_analytics() - Lines 553-666 (113 lines) - Analytics queries
```

---

## Proposed Modular Structure

```
core/workflow_history_utils/
├── database.py (original - to be replaced)
└── database/
    ├── __init__.py (~50 lines) - Backward compatibility exports
    ├── schema.py (~130 lines) - ✅ COMPLETED - Schema & migrations
    ├── mutations.py (~180 lines) - Insert & update operations
    ├── queries.py (~190 lines) - Read operations & filtering
    └── analytics.py (~130 lines) - Analytics queries

Total: ~680 lines (+14 lines, +2% overhead)
```

---

## Module Breakdown

### 1. schema.py (130 lines) - ✅ COMPLETED

**Responsibility:** Database schema initialization and migrations

**Functions:**
- `init_db()` - Create tables, indexes, handle migrations

**Features:**
- CREATE TABLE with all fields
- CREATE INDEX for performance
- Schema migrations (e.g., gh_issue_state column)
- Path management for DB_PATH

**Status:** ✅ Extracted and ready

---

### 2. mutations.py (180 lines) - 🟡 PENDING

**Responsibility:** All write operations (INSERT, UPDATE)

**Functions:**
- `insert_workflow_history(adw_id, issue_number, ...)` - Insert new workflow
- `update_workflow_history_by_issue(issue_number, ...)` - Update by issue number
- `update_workflow_history(adw_id, ...)` - Update by adw_id with **kwargs

**Features:**
- JSON serialization for structured fields
- Bulk update support
- Transaction handling
- Error logging

**Imports:** `schema.DB_PATH`, `get_db_connection`, `json`, `logging`

---

### 3. queries.py (190 lines) - 🟡 PENDING

**Responsibility:** All read operations and filtering

**Functions:**
- `get_workflow_by_adw_id(adw_id)` - Fetch single workflow
- `get_workflow_history(filters, limit, offset, order_by, order_dir)` - Fetch with filters

**Features:**
- Dynamic WHERE clause building
- Pagination support (limit, offset)
- Sorting (order_by, order_dir)
- Filter support (status, model, template, date range)
- JSON deserialization for structured fields
- Row count for pagination

**Imports:** `schema.DB_PATH`, `get_db_connection`, `json`, `logging`

---

### 4. analytics.py (130 lines) - 🟡 PENDING

**Responsibility:** Analytics and aggregate queries

**Functions:**
- `get_history_analytics()` - Comprehensive analytics summary

**Features:**
- Total workflow counts
- Status breakdowns (completed, failed, etc.)
- Success rate calculation
- Average duration/cost/tokens
- Grouping by model and template
- Cache efficiency metrics

**Imports:** `schema.DB_PATH`, `get_db_connection`, `logging`

---

### 5. __init__.py (50 lines) - 🟡 PENDING

**Responsibility:** Backward compatibility exports

**Exports:**
```python
from .schema import init_db, DB_PATH
from .mutations import (
    insert_workflow_history,
    update_workflow_history_by_issue,
    update_workflow_history,
)
from .queries import (
    get_workflow_by_adw_id,
    get_workflow_history,
)
from .analytics import get_history_analytics

__all__ = [
    # Schema
    'init_db',
    'DB_PATH',
    # Mutations
    'insert_workflow_history',
    'update_workflow_history_by_issue',
    'update_workflow_history',
    # Queries
    'get_workflow_by_adw_id',
    'get_workflow_history',
    # Analytics
    'get_history_analytics',
]
```

---

## Benefits of Refactoring

### ✅ Maintainability
- Each module has single, clear responsibility
- Easier to locate specific database operations
- Reduced cognitive load (max file: 190 lines vs 666)

### ✅ Testability
- Each module can be tested in isolation
- Mock dependencies easily (schema, mutations separate from queries)
- Clear boundaries for unit vs integration tests

### ✅ Scalability
- Easy to add new query types to queries.py
- Easy to add new analytics to analytics.py
- Schema migrations centralized in schema.py

### ✅ Repository Pattern
- Clear separation: schema, writes, reads, analytics
- Foundation for future ORM or query builder integration
- Easy to swap implementations (e.g., PostgreSQL)

---

## Migration Strategy

### Phase 5A: Extract Modules (Current Phase)
1. ✅ Create `database/` directory
2. ✅ Extract `schema.py`
3. Extract `mutations.py`
4. Extract `queries.py`
5. Extract `analytics.py`
6. Create `__init__.py` with exports

### Phase 5B: Update Imports
1. Find all imports of `database.py` functions
2. Verify backward compatibility works
3. Run test suite

### Phase 5C: Verification & Documentation
1. Run all database tests
2. Run integration tests
3. Document completion
4. Commit changes

---

## Testing Requirements

**Must Pass:**
- All existing database tests (1,574 lines in test_database.py)
- Integration tests (test_database_operations.py)
- Workflow history tests

**Test Coverage:**
- Schema initialization
- Insert operations
- Update operations (by adw_id and issue_number)
- Query operations (single and filtered)
- Analytics queries
- JSON serialization/deserialization
- Pagination
- Error handling

---

## Backward Compatibility

**100% Backward Compatible** - All existing imports will work:

```python
# OLD (still works):
from core.workflow_history_utils.database import (
    init_db,
    insert_workflow_history,
    update_workflow_history,
    get_workflow_history,
    get_history_analytics,
)

# NEW (explicit, optional):
from core.workflow_history_utils.database.schema import init_db
from core.workflow_history_utils.database.mutations import insert_workflow_history
from core.workflow_history_utils.database.queries import get_workflow_history
from core.workflow_history_utils.database.analytics import get_history_analytics
```

---

## Implementation Status

| Module | Lines | Status | Notes |
|--------|-------|--------|-------|
| schema.py | 130 | ✅ Complete | Extracted, tested |
| mutations.py | 180 | 🟡 Pending | Needs extraction |
| queries.py | 190 | 🟡 Pending | Needs extraction |
| analytics.py | 130 | 🟡 Pending | Needs extraction |
| __init__.py | 50 | 🟡 Pending | Needs exports |

---

## Next Steps

1. **Complete extractions** - Extract remaining modules (mutations, queries, analytics)
2. **Create __init__.py** - Add backward compatibility exports
3. **Test integration** - Run full test suite (1,574 test lines)
4. **Document completion** - Create PHASE_5_COMPLETION.md
5. **Commit changes** - Single atomic commit with all changes

---

## Comparison with Previous Phases

| Phase | Target | Original Lines | New Modules | Reduction |
|-------|--------|----------------|-------------|-----------|
| Phase 3 | workflow_analytics.py | 865 | 10 | -92% main |
| Phase 4 | WorkflowHistoryCard.tsx | 818 | 11 | -79% main |
| **Phase 5** | **database.py** | **666** | **5** | **Est. -80% main** |

**Consistent pattern across all phases!**

---

## References

- Original file: `app/server/core/workflow_history_utils/database.py`
- Test file: `app/server/tests/core/workflow_history_utils/test_database.py` (1,574 lines)
- Integration tests: `app/server/tests/integration/test_database_operations.py`

---

**Status:** Schema extraction complete, remaining modules pending full implementation.
**Recommendation:** Complete Phase 5 extraction to maintain consistency with Phases 3-4.
