### Workflow 3.2: Create Background Tasks Tests
**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** Workflow 3.1

**Input Files:**
- `app/server/services/background_tasks.py`

**Output Files:**
- `app/server/tests/services/test_background_tasks.py` (new)

**Tasks:**
1. Write test for task startup
2. Write test for task shutdown
3. Write test for workflow watcher broadcasts
4. Write test for routes watcher broadcasts
5. Write test for history watcher broadcasts
6. Write test for error handling in watchers
7. Write test for cancellation handling

**Test Cases:**
- ✅ start_all() creates all tasks
- ✅ stop_all() cancels all tasks
- ✅ Workflow watcher broadcasts on changes
- ✅ Routes watcher broadcasts on changes
- ✅ History watcher broadcasts on changes
- ✅ Errors in watchers don't crash tasks
- ✅ Cancellation handled gracefully

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] Test coverage >80%
- [ ] Async behavior tested properly
- [ ] No task leaks in tests

**Verification Command:**
```bash
cd app/server && pytest tests/services/test_background_tasks.py -v --cov=services.background_tasks --cov-report=term-missing
```
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
