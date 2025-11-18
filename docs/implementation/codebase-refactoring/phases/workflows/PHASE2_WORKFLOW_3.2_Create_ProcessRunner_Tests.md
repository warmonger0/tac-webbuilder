### Workflow 3.2: Create ProcessRunner Tests
**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** Workflow 3.1

**Input Files:**
- `app/server/core/process_utils.py`

**Output Files:**
- `app/server/tests/core/test_process_utils.py` (new)

**Tasks:**
1. Write test for successful command
2. Write test for failed command
3. Write test for timeout
4. Write test for background process
5. Write test for retry logic
6. Write test for kill_process()
7. Write test for error handling

**Test Cases:**
- ✅ Successful command returns success=True
- ✅ Failed command returns success=False
- ✅ Timeout sets timed_out=True
- ✅ Background process starts with PID
- ✅ Retry succeeds after transient failure
- ✅ Retry gives up after max attempts
- ✅ kill_process() terminates gracefully
- ✅ kill_process() force kills if needed

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] Test coverage >85%
- [ ] All execution paths tested
- [ ] Cleanup of test processes

**Verification Command:**
```bash
cd app/server && pytest tests/core/test_process_utils.py -v --cov=core.process_utils --cov-report=term-missing
```
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
