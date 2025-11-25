# Incident Report: ADW Workflow Stall After Planning Phase

**Date:** 2025-11-25
**Issue:** #91
**ADW ID:** ccc93560
**Severity:** High - Workflow silently stalls without user notification

---

## Summary

ADW workflow for issue #91 completed planning phase successfully but stalled instead of continuing through the full SDLC (build, test, review, ship, cleanup). The workflow appeared "stuck" with no activity for nearly 2 hours, requiring manual investigation and intervention.

## Timeline

| Time | Event |
|------|-------|
| 00:21 | Workflow started with `adw_plan_iso.py` |
| 00:26 | Planning completed, PR #95 created successfully |
| 00:26 | **Workflow stopped** - No further activity |
| 02:12 | User noticed workflow stall (1h 46m later) |
| 02:18 | Manual resume attempted with `adw_sdlc_complete_iso.py` |
| 02:21 | Build phase failed due to branch name mismatch |

## Root Causes

### Primary Cause: Workflow Template Mismatch

**Problem:** User selected `adw_plan_iso.py` which is designed to ONLY create a plan and PR, not execute the full SDLC.

**Evidence:**
```python
# adw_plan_iso.py workflow completes at line 281:
logger.info("Isolated planning phase completed successfully")
sys.exit(0)  # Exits after PR creation
```

**Why It Happened:**
- `adw_plan_iso.py` is for planning only (phases: plan → PR creation)
- `adw_sdlc_complete_iso.py` is for full SDLC (phases: plan → validate → build → lint → test → review → doc → ship → cleanup)
- No visual/UX indicator to show which workflow template was selected
- Workflow state shows `"status": "running"` even after completion

### Secondary Cause: Branch Name Inconsistency on Resume

**Problem:** When resuming with `adw_sdlc_complete_iso.py`, the issue was reclassified differently, causing a branch name mismatch.

**Evidence:**
```
Original classification: /feature
Branch created: feature-issue-91-adw-ccc93560-verify-pattern-collection

Resume classification: /chore
Expected branch: chore-issue-91-adw-ccc93560-verify-pattern-collection
Error: pathspec 'chore-issue-91-adw-ccc93560-verify-pattern-collection' did not match any file(s) known to git
```

**Why It Happened:**
- Issue classifier agent (`issue_classifier`) is non-deterministic
- First run classified as `/feature`
- Second run (resume) classified as `/chore`
- Branch name derives from classification
- Worktree already exists with `feature-*` branch
- Build phase tries to checkout non-existent `chore-*` branch

### Tertiary Cause: State File Never Marked "Completed"

**Problem:** The ADW state file shows `"status": "running"` indefinitely after workflow exits.

**Evidence:**
```json
{
  "status": "running",
  "workflow_template": "adw_plan_iso",
  "start_time": "2025-11-25T00:21:50.254958"
  // No end_time, no status update
}
```

**Why It Happened:**
- `adw_plan_iso.py` exits with `sys.exit(0)` without updating state to "completed"
- State file never gets `end_time` timestamp
- Monitor API interprets >10min inactivity as "paused" but state still says "running"

## Impact

1. **User Confusion:** Workflow appeared stuck with no clear indication it had finished
2. **Wasted Time:** 1h 46m before issue was noticed
3. **Silent Failure:** No notification that planning-only workflow completed
4. **Manual Intervention Required:** User had to diagnose and manually resume
5. **Resume Failure:** Branch name mismatch caused build phase to fail on resume

## What Worked Well

1. ✅ ADW Monitor API correctly detected PR #95 for issue #91
2. ✅ Frontend UI now shows `#91 → PR #95` relationship clearly
3. ✅ Worktree isolation prevented conflicts
4. ✅ Planning phase executed successfully
5. ✅ PR was created correctly

## Fixes Required

### Fix 1: Update Workflow Exit Status ⚠️ CRITICAL
**Priority:** P0
**File:** `adws/adw_plan_iso.py`

```python
# Before exit, update state to completed
state.update(
    status="completed",
    end_time=datetime.now().isoformat()
)
state.save("adw_plan_iso")
logger.info("✅ Planning workflow completed")
```

### Fix 2: Make Issue Classification Deterministic ⚠️ CRITICAL
**Priority:** P0
**File:** `adw_modules/workflow_ops.py`

**Option A: Cache classification in state**
```python
def classify_issue(issue, adw_id, logger):
    state = ADWState.load(adw_id, logger)

    # Return cached classification if exists
    if state.get("issue_class"):
        logger.info(f"Using cached classification: {state.get('issue_class')}")
        return state.get("issue_class"), None

    # Otherwise classify and cache
    classification, error = _classify_issue_with_ai(issue, adw_id, logger)
    if not error:
        state.update(issue_class=classification)
        state.save("classify_issue")
    return classification, error
```

**Option B: Derive from existing branch**
```python
def get_branch_name_from_worktree(worktree_path, logger):
    """Get current branch name from worktree instead of regenerating"""
    result = subprocess.run(
        ["git", "-C", worktree_path, "branch", "--show-current"],
        capture_output=True,
        text=True,
        timeout=5
    )
    if result.returncode == 0:
        return result.stdout.strip(), None
    return None, "Failed to get branch name"
```

### Fix 3: Workflow Template Indicator in UI
**Priority:** P1
**File:** `app/client/src/components/AdwMonitorCard.tsx`

Add workflow template badge:
```tsx
<span className="px-2 py-0.5 bg-blue-500/20 text-blue-300 text-xs rounded-md font-medium">
  {currentWorkflow.workflow_template}
</span>
```

Show completion status for planning-only workflows:
```tsx
{currentWorkflow.workflow_template === 'adw_plan_iso' && currentWorkflow.status === 'completed' && (
  <div className="text-yellow-400 text-sm">
    ⚠️ Planning only - requires full SDLC to continue
  </div>
)}
```

### Fix 4: Automatic Workflow Chain Detection
**Priority:** P1
**File:** `adws/adw_plan_iso.py`

Add prompt at workflow end:
```python
if os.getenv("INTERACTIVE_MODE", "false").lower() == "true":
    response = input("\n✅ Planning complete. Continue with full SDLC? (y/N): ")
    if response.lower() == 'y':
        logger.info("Chaining to full SDLC workflow")
        subprocess.run([
            "uv", "run",
            os.path.join(os.path.dirname(__file__), "adw_sdlc_complete_iso.py"),
            issue_number, adw_id
        ])
```

### Fix 5: State Validation Check
**Priority:** P2
**File:** `adw_modules/state.py`

Add state consistency checker:
```python
def validate_state_consistency(self, phase: str, logger):
    """Validate state consistency before phase execution"""
    errors = []

    # Check branch name matches classification
    if self.get("branch_name") and self.get("issue_class"):
        expected_prefix = self.get("issue_class").strip("/")
        if not self.get("branch_name").startswith(expected_prefix):
            errors.append(
                f"Branch '{self.get('branch_name')}' doesn't match "
                f"classification '{self.get('issue_class')}'"
            )

    # Check worktree branch exists
    if self.get("worktree_path"):
        result = subprocess.run(
            ["git", "-C", self.get("worktree_path"), "branch", "--list", self.get("branch_name")],
            capture_output=True,
            text=True
        )
        if not result.stdout.strip():
            errors.append(f"Branch '{self.get('branch_name')}' not found in worktree")

    if errors:
        logger.error(f"State validation errors in {phase}: {errors}")
        return False, errors

    return True, []
```

## Prevention Measures

### Automated Tests

**Test 1: Workflow Completion Status** (`tests/adw/test_workflow_completion.py`)
```python
def test_workflow_updates_status_on_completion():
    """Verify workflows mark state as completed when done"""
    # Run planning workflow
    result = subprocess.run([
        "uv", "run", "adws/adw_plan_iso.py", "test-issue", "test-adw"
    ], capture_output=True)

    # Load state
    state = ADWState.load("test-adw")

    # Assert completion status
    assert state.get("status") == "completed"
    assert state.get("end_time") is not None
    assert state.get("end_time") > state.get("start_time")
```

**Test 2: Classification Determinism** (`tests/adw/test_classification_consistency.py`)
```python
def test_classification_is_deterministic():
    """Verify issue classification doesn't change between runs"""
    issue = fetch_issue("91", "warmonger0/tac-webbuilder")

    # Classify twice
    class1, _ = classify_issue(issue, "test-adw-1", logger)
    class2, _ = classify_issue(issue, "test-adw-1", logger)  # Same ADW ID

    # Should return cached value
    assert class1 == class2
```

**Test 3: Branch Name Consistency** (`tests/adw/test_branch_name_consistency.py`)
```python
def test_branch_name_matches_classification():
    """Verify branch name prefix matches issue classification"""
    state = ADWState.load("test-adw")

    classification = state.get("issue_class", "").strip("/")
    branch_name = state.get("branch_name", "")

    assert branch_name.startswith(classification), \
        f"Branch '{branch_name}' doesn't start with '{classification}'"
```

## Monitoring Improvements

### Health Check Enhancements

Add to `app/server/core/adw_monitor.py`:

```python
def detect_stalled_workflows() -> list[dict]:
    """Detect workflows that may be stalled"""
    states = scan_adw_states()
    stalled = []

    for state in states:
        # Planning-only workflow completed but user may expect full SDLC
        if (state.get("workflow_template") == "adw_plan_iso"
            and state.get("status") == "completed"
            and not state.get("chained_to_full_sdlc")):
            stalled.append({
                "adw_id": state["adw_id"],
                "issue_number": state["issue_number"],
                "reason": "Planning completed, requires full SDLC for implementation",
                "action": f"Run: uv run adws/adw_sdlc_complete_iso.py {state['issue_number']} {state['adw_id']}"
            })

    return stalled
```

## Lessons Learned

1. **Workflow Templates Need Clear Names:** `adw_plan_iso.py` vs `adw_sdlc_complete_iso.py` aren't intuitive
2. **Exit Status is Critical:** All workflows must update state before exiting
3. **Determinism Matters:** Non-deterministic classification causes cascading failures
4. **State Validation:** Check state consistency before each phase
5. **User Visibility:** Need clear UI indicators for workflow template and status

## Action Items

- [ ] Implement Fix 1: Update workflow exit status (P0)
- [ ] Implement Fix 2: Make classification deterministic (P0)
- [ ] Implement Fix 3: Add workflow template indicator to UI (P1)
- [ ] Implement Fix 4: Add workflow chain prompt (P1)
- [ ] Implement Fix 5: Add state validation check (P2)
- [ ] Add automated tests for workflow completion
- [ ] Add automated tests for classification consistency
- [ ] Add automated tests for branch name consistency
- [ ] Update ADW monitor to detect stalled planning-only workflows
- [ ] Document workflow template differences in user guide

---

**Report Author:** Claude (with assistance from user diagnosis)
**Last Updated:** 2025-11-25
**Status:** Fixes Pending Implementation
