### Workflow 2.2: Create Workflow Service Tests
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** Workflow 2.1

**Input Files:**
- `app/server/services/workflow_service.py`

**Output Files:**
- `app/server/tests/services/test_workflow_service.py` (new)

**Tasks:**
1. Create fixtures for temporary workflow directories
2. Write test for empty directory
3. Write test for valid workflow directory
4. Write test for invalid workflow directory (no state file)
5. Write test for corrupted state file
6. Write test for workflow sorting (newest first)
7. Write test for history pagination

**Test Cases:**
- ✅ Empty directory returns empty list
- ✅ Valid workflow directory parsed correctly
- ✅ Invalid directories are skipped
- ✅ Corrupted JSON handled gracefully
- ✅ Workflows sorted by creation time
- ✅ History pagination works correctly

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] Test coverage >80%
- [ ] Edge cases covered (missing files, bad JSON, etc.)
- [ ] Temporary test data cleaned up properly

**Verification Command:**
```bash
cd app/server && pytest tests/services/test_workflow_service.py -v --cov=services.workflow_service --cov-report=term-missing
```
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
