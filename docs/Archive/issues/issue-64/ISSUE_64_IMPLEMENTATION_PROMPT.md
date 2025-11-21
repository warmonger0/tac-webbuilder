# Implementation Prompt for Issue #64 Quality Gate Fixes

Copy this entire prompt into a new Claude Code chat to begin fixing the ADW quality gate failures:

---

## Context

I need to fix critical bugs in the ADW (Autonomous Digital Worker) workflow quality gates that were discovered during analysis of issue #64. Three quality gates (Test, Review, Ship) failed silently, allowing broken code to be marked as "successful" and an issue to be falsely closed.

## Background Reading

Please read these three analysis documents first:
1. `docs/ISSUE_64_ADW_FAILURE_ANALYSIS.md` - Complete technical breakdown
2. `docs/ISSUE_64_ACTION_PLAN.md` - Fix implementation guide
3. `docs/ISSUE_64_COMPLETE_FAILURE_SUMMARY.md` - Executive summary

**Key findings:**
- Test phase: External tool crashed with JSONDecodeError but reported "All tests passed"
- Review phase: Screenshot showed 0 workflows but accepted as success (DB had 453 records)
- Ship phase: GitHub API said "MERGED" but commits never landed on main
- Original bug still exists in production

## Implementation Scope

I want to fix the THREE critical quality gate failures in priority order:

### Phase 1: Fix Test Phase Error Handling (P0 - Critical)
**File**: `adws/adw_test_iso.py`

**Problem**: When external test tool fails with JSON parsing error, phase catches exception but continues as success.

**Evidence**:
```
agents/af4246c1/adw_test_iso/execution.log:
Line 35: External tests completed: ❌ Failures detected
Line 36: ERROR - External test tool error: JSONDecodeError
Line 45: All tests passed successfully  ← FALSE!
```

**Required Fix**:
- Properly propagate external tool failures
- Return failure when JSON parsing fails
- Return failure when external tool exits non-zero
- Only return success if tests actually ran AND passed

### Phase 2: Fix Ship Phase Merge Verification (P0 - Critical)
**File**: `adws/adw_ship_iso.py`

**Problem**: Trusts GitHub API response without verifying commits actually landed on target branch.

**Evidence**:
```bash
# GitHub says merged
$ gh pr view 65 --json state
{"state": "MERGED"}

# But file doesn't exist on main
$ ls app/server/db/migrations/005_*
ls: No such file or directory

# Commit only on feature branch
$ git branch --contains 82ed38a
  bug-issue-64-adw-af4246c1-fix-workflow-history-column
```

**Required Fix**:
- After GitHub API merge call, verify commits landed
- Check if merge commit exists on target branch
- Verify expected files exist on target branch
- Fail ship phase if verification fails

### Phase 3: Fix Review Phase Data Validation (P1 - High)
**File**: `adws/adw_review_iso.py`

**Problem**: Accepts screenshot showing empty state without verifying if data should exist.

**Evidence**:
- Screenshot: `.playwright-mcp/01_workflow_history_page_loading_successfully.png`
- Shows: "No workflow history found" (0 total workflows)
- Reality: Database had 453 workflow records
- Backend logs full of: "table workflow_history has no column named hour_of_day"

**Required Fix**:
- When screenshot shows empty state, cross-reference with database
- Check backend logs for errors during screenshot capture
- Test API endpoint directly to verify it returns data
- Only accept empty state if legitimately empty (DB also empty, no errors in logs)

## Implementation Approach

For each phase, I want you to:

1. **Read the existing code** to understand current implementation
2. **Identify the exact bug** (show me the problematic code)
3. **Design the fix** (explain your approach before coding)
4. **Implement the fix** with proper error handling
5. **Add tests** to verify the fix prevents recurrence
6. **Document the change** in code comments

## Success Criteria

Each fix should ensure:

- ✅ Failures are detected and propagated correctly
- ✅ False positives are eliminated
- ✅ Clear error messages explain what went wrong
- ✅ GitHub comments alert user to actual failures
- ✅ Workflow stops at first real failure (fail-fast)
- ✅ Tests verify the fix works

## Important Constraints

- **Don't break existing functionality** - only fix the error handling
- **Maintain backward compatibility** - existing successful workflows should still work
- **Add logging** - make failures visible and debuggable
- **Test thoroughly** - these are critical quality gates

## Start With Phase 1

Let's begin with the Test Phase fix (`adws/adw_test_iso.py`) since it's the first quality gate that failed.

Please:
1. Read `adws/adw_test_iso.py` and `adws/adw_test_external.py`
2. Show me the current error handling code
3. Explain what's wrong with it
4. Propose a fix
5. Implement the fix with tests

After we complete Phase 1, we'll move to Phase 2 (Ship), then Phase 3 (Review).

---

## Additional Context

**Project**: tac-webbuilder (Natural language web development assistant)
**Tech Stack**: Python, FastAPI, React, SQLite
**ADW System**: Automated development workflows in isolated git worktrees
**Testing**: pytest for Python, vitest for frontend

**Related Files**:
- Test phase: `adws/adw_test_iso.py`, `adws/adw_test_external.py`
- Ship phase: `adws/adw_ship_iso.py`
- Review phase: `adws/adw_review_iso.py`
- Workflow orchestrator: `adws/adw_sdlc_complete_iso.py`

Let me know when you're ready to start with Phase 1!
