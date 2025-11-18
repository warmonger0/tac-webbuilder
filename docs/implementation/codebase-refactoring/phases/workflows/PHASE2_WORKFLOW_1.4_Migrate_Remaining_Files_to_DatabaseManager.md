### Workflow 1.4: Migrate Remaining Files to DatabaseManager
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** Workflow 1.3

**Input Files:**
- `app/server/core/file_processor.py`
- `app/server/core/sql_processor.py`
- `app/server/core/insights.py`
- `app/server/core/adw_lock.py`
- `app/server/server.py`

**Output Files:**
- All above files (modified)

**Tasks:**
1. Migrate file_processor.py (search for `sqlite3.connect`)
2. Migrate sql_processor.py
3. Migrate insights.py
4. Migrate adw_lock.py
5. Migrate server.py (any direct database access)
6. Create single DatabaseManager instance to share
7. Test all modules

**Shared Instance Pattern:**
```python
# In core/database.py - add module-level instance
_default_db = None

def get_default_db() -> DatabaseManager:
    """Get or create the default DatabaseManager instance"""
    global _default_db
    if _default_db is None:
        _default_db = DatabaseManager()
    return _default_db

# In other modules:
from core.database import get_default_db

db = get_default_db()

# Use db.get_connection(), db.get_cursor(), etc.
```

**Files to Update:**
- `app/server/core/file_processor.py` - 2-3 connection points
- `app/server/core/sql_processor.py` - 4-5 connection points
- `app/server/core/insights.py` - 1-2 connection points
- `app/server/core/adw_lock.py` - 3-4 connection points
- `app/server/server.py` - 1-2 connection points

**Acceptance Criteria:**
- [ ] All files migrated to DatabaseManager
- [ ] Shared instance pattern used
- [ ] All tests pass for each module
- [ ] No sqlite3.connect() calls remain (except in DatabaseManager)
- [ ] Code duplication reduced by ~60 lines

**Verification Commands:**
```bash
# Search for remaining direct database connections
grep -r "sqlite3.connect" app/server/ --exclude-dir=tests

# Should only show app/server/core/database.py

# Run all tests
cd app/server && pytest tests/core/ -v
```

---
