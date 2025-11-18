### Workflow 1.2: Create DatabaseManager Tests
**Estimated Time:** 2 hours
**Complexity:** Low
**Dependencies:** Workflow 1.1

**Input Files:**
- `app/server/core/database.py`

**Output Files:**
- `app/server/tests/core/__init__.py` (new if doesn't exist)
- `app/server/tests/core/test_database.py` (new)

**Tasks:**
1. Create fixtures for temporary database
2. Write test for get_connection() commit
3. Write test for get_connection() rollback
4. Write test for get_cursor()
5. Write test for execute_query()
6. Write test for execute_update()
7. Write test for row factory
8. Write test for directory creation

**Test Cases:**
- ✅ Connection commits on success
- ✅ Connection rolls back on error
- ✅ Cursor context manager works
- ✅ execute_query() returns results
- ✅ execute_update() returns rowcount
- ✅ Row factory converts rows to dict-like
- ✅ Database directory created if missing
- ✅ Duplicate key error handled with rollback

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] Test coverage >90%
- [ ] Temporary test databases cleaned up
- [ ] Edge cases covered

**Verification Command:**
```bash
cd app/server && pytest tests/core/test_database.py -v --cov=core.database --cov-report=term-missing
```
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
