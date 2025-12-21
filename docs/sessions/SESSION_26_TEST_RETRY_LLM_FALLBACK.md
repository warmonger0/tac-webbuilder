# Session 26 - Test Phase LLM Fallback Fix

**Date:** December 21, 2025
**Issues:** #254, #255
**Key Change:** Fixed test phase retry to trigger LLM-based fixes when external resolution fails

---

## Problem Statement

ADW workflows were experiencing infinite retry loops when tests failed, leading to workflow aborts:

### Symptoms (GitHub Issues #254/255)
1. Test phase would retry 3 times but fail each time
2. Loop detector would trigger: "Agent `checker` has posted 8 times in last 15 comments"
3. Workflow would abort without fixing the underlying test failures
4. Comment pattern showed retries without actual progress toward resolution

### Root Cause Analysis

The test phase had **two separate retry mechanisms** that weren't properly coordinated:

1. **External Test Resolution Loop** (`run_external_tests_with_resolution()`):
   - Runs external tests via subprocess
   - Has internal retry logic (MAX_TEST_RETRY_ATTEMPTS = 3)
   - Can fix infrastructure failures (JSON parse errors, subprocess crashes)
   - **But**: When tests simply failed (not infrastructure errors), it would NOT trigger LLM fixes

2. **Orchestrator Retry** (`adw_sdlc_complete_iso.py` → `run_phase_with_retry()`):
   - Retries entire test phase on failure
   - **But**: Just re-runs the same command - doesn't add new resolution logic
   - Results in same test failures repeating

### The Gap

In `adw_test_iso.py` lines 1372-1426, the fallback to LLM-based resolution only triggered on **infrastructure errors**:

```python
# OLD CODE (BROKEN)
if not success and "error" in external_results:
    # Only falls back to LLM on infrastructure failures
    # Missing: Fallback when tests simply fail!
```

When external resolution exhausted its retries but tests still failed, the code would:
- Report failures to GitHub
- Exit with failure code
- Orchestrator would retry the whole phase
- Same external resolution would fail again
- Loop detector would abort

**The missing piece:** Never triggered LLM-based test fixing (`run_tests_with_resolution()`) when external resolution couldn't fix test failures.

---

## Solution

### Code Changes

**File:** `adws/adw_test_iso.py` (lines 1371-1426)

Changed the logic to trigger LLM fallback on **ANY** test failure, not just infrastructure errors:

```python
# NEW CODE (FIXED)
if not success:  # ANY failure triggers check
    if "error" in external_results:
        # Infrastructure failure - fallback to inline mode
        logger.warning("External test tools failed after retries, using inline execution as fallback")
    else:
        # Test failures after external resolution - need LLM-based fixes
        logger.warning(f"External resolution could not fix {failed_count_ext} test failures, falling back to LLM-based fixes")

    # Use inline mode with full LLM-based resolution
    test_results, passed_count, failed_count, test_response = run_tests_with_resolution(
        adw_id, issue_number, logger, worktree_path
    )
```

### What Changed

**Before:**
1. External tests run → fail
2. External resolution attempts (3 tries) → still fail
3. Report failures to GitHub
4. Exit with error code
5. Orchestrator retries → same cycle repeats
6. Loop detector aborts

**After:**
1. External tests run → fail
2. External resolution attempts (3 tries) → still fail
3. **Automatically fall back to LLM-based test fixing**
4. LLM analyzes failures and fixes underlying code issues
5. Re-runs tests to verify fixes
6. Either succeeds or exits with genuine unfixable failures

---

## Technical Details

### Test Resolution Flow

The test phase now has **cascading resolution strategies**:

1. **Layer 1 - External Tool Resolution** (fast, context-efficient):
   - `run_external_tests_with_resolution()` in `adw_test_iso.py:632`
   - Runs tests via external subprocess (`adw_test_external.py`)
   - Attempts resolution via same external process (3 retries)
   - ~90% context savings vs inline execution

2. **Layer 2 - LLM-Based Resolution** (comprehensive, higher context):
   - `run_tests_with_resolution()` in `adw_test_iso.py:754`
   - Uses `/resolve_failed_test` command to fix code issues
   - Verification-based loop control (re-runs tests after each fix)
   - Circuit breaker: stops if no progress detected
   - Handles complex test failures requiring code changes

3. **Layer 3 - Orchestrator Retry** (last resort):
   - `run_phase_with_retry()` in `adw_sdlc_complete_iso.py:154`
   - Only triggers if phase crashes (not for test failures)
   - Leverages idempotency for safe retries

### Verification-Based Loop Control

The LLM resolution layer includes Issue #168's verification system:

```python
# From adw_test_iso.py:826-871
if resolved > 0:
    # Re-run tests to VERIFY fixes actually work
    verify_response = run_tests(adw_id, logger, worktree_path)
    verify_results, verify_passed, verify_failed = parse_test_results(...)

    # Check for ACTUAL progress (not just agent claims)
    if verify_failed >= previous_failed_count:
        # No progress - break to prevent infinite loop
        make_issue_comment("⚠️ No Progress Detected")
        break
```

This prevents false success loops where agents claim to fix tests but verification shows no improvement.

---

## Impact

### Before This Fix
- Workflows with test failures would hit retry loops
- Loop detector would abort after 8 repetitive agent posts
- Manual intervention required to fix and restart
- Wasted API quota on ineffective retries

### After This Fix
- Test failures automatically escalate to LLM-based fixes
- Higher success rate for complex test issues
- Loop detector should rarely trigger (progress is made)
- Workflows complete or fail with clear unfixable reasons

### Trade-offs
- **Context usage**: LLM fallback uses more tokens than external tools
- **Latency**: LLM resolution is slower than external subprocess
- **Success rate**: Much higher - can fix code issues, not just re-run tests

---

## Related Work

### Session 19 - ADW Loop Prevention (Issue #168)
- Implemented verification-based loop control
- Added circuit breaker for repetitive agent patterns
- Set MAX_TEST_RETRY_ATTEMPTS = 3, MAX_SAME_AGENT_REPEATS = 8

**This session builds on that work** by ensuring the retry attempts actually make progress via LLM fixes.

### Future Improvements

1. **Adaptive Strategy Selection**: Start with external tools, escalate to LLM only if needed (already implemented!)
2. **Cost Attribution**: Track which resolution strategy fixed which tests
3. **Pattern Learning**: Identify test types that always need LLM vs. external resolution
4. **Smart Retry**: Skip external resolution if pattern analysis shows it won't work

---

## Testing

### Manual Verification
- Observe issues #254/255 behavior after this fix
- Check if loop detector triggers less frequently
- Monitor test phase completion rates

### Expected Outcomes
- Test phase should complete successfully or fail with clear reasons
- GitHub comments should show LLM fallback happening
- Loop detector should not abort (progress being made)

---

## Files Changed

1. **adws/adw_test_iso.py** (lines 1371-1426)
   - Changed fallback logic to trigger on ANY test failure
   - Added clear messaging for LLM fallback
   - Simplified success path (external tests passed)

---

## Documentation Updates

- **This file**: `docs/sessions/SESSION_26_TEST_RETRY_LLM_FALLBACK.md`
- **Recent work**: Will update `.claude/commands/references/recent_work.md`
- **ADW primer**: May need update in `.claude/commands/quick_start/adw.md`

---

## Commit Message

```
fix: Trigger LLM-based test fixing when external resolution fails

Resolves issue #254/255 where test phase retries would loop without progress.

Previously, LLM-based test fixing only triggered on infrastructure errors
(JSON parse, subprocess crash). When tests simply failed after external
resolution attempts, the workflow would retry the same external resolution,
leading to loop detector aborts.

Now, ANY test failure triggers automatic fallback to LLM-based resolution:
1. External tests run and attempt resolution (fast, 90% context savings)
2. If tests still fail, automatically invoke run_tests_with_resolution()
3. LLM analyzes failures and fixes underlying code issues
4. Verification-based loop control ensures actual progress

This ensures orchestrator retries are effective (new resolution strategy
runs) and reduces loop detector false positives (progress is being made).

Changes:
- adws/adw_test_iso.py: Updated fallback logic (lines 1371-1426)

Related: Session 19 (Issue #168 - loop prevention), Session 26 docs
```

---

## Key Takeaway

**Test resolution requires escalation, not just retry.**

Retrying the same strategy (external resolution) won't fix code issues. The fix ensures that when "outflow work" (external tools) can't solve the problem, it automatically kicks back into the LLM to fix the underlying code - which is what test resolution should do.
