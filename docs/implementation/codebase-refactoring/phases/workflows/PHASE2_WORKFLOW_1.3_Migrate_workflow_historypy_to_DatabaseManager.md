### Workflow 1.3: Migrate workflow_history.py to DatabaseManager
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** Workflow 1.1, 1.2

**Input Files:**
- `app/server/core/workflow_history.py`
- `app/server/core/database.py`

**Output Files:**
- `app/server/core/workflow_history.py` (modified)

**Tasks:**
1. Add import for DatabaseManager
2. Replace all `sqlite3.connect()` calls with DatabaseManager
3. Update init_db() to use DatabaseManager
4. Update insert_workflow() to use DatabaseManager
5. Update update_workflow() to use DatabaseManager
6. Update get_workflow_by_id() to use DatabaseManager
7. Update get_workflow_history() to use DatabaseManager
8. Remove manual commit/rollback/close code
9. Test all workflow history operations

**Before/After Example:**
```python
# BEFORE:
def get_workflow_by_id(workflow_id: str):
    conn = sqlite3.connect("db/database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM workflow_history WHERE id = ?", (workflow_id,))
        result = cursor.fetchone()
        conn.commit()
        return result
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# AFTER:
from core.database import DatabaseManager

db = DatabaseManager()

def get_workflow_by_id(workflow_id: str):
    with db.get_cursor(sqlite3.Row) as cursor:
        cursor.execute("SELECT * FROM workflow_history WHERE id = ?", (workflow_id,))
        return cursor.fetchone()
```

**Acceptance Criteria:**
- [ ] All database calls use DatabaseManager
- [ ] No manual connection management code
- [ ] All existing tests still pass
- [ ] No regression in functionality
- [ ] Code is cleaner and shorter

**Verification Command:**
```bash
cd app/server && pytest tests/core/test_workflow_history.py -v
```
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
