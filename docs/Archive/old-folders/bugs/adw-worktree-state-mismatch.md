# Bug: ADW Worktree State Mismatch Causes Full SDLC Workflow Failures

## Severity
**HIGH** - Blocks users from running full SDLC workflow after standalone planning

## Status
**IDENTIFIED** - Root cause found, solutions proposed

## Description
When a user runs `adw_plan_iso.py` followed by `adw_sdlc_complete_iso.py` with the same ADW ID, the full SDLC workflow fails on Phase 1 (Plan) with a git worktree collision error, even though the workflow has worktree detection logic.

## Reproduction Steps

1. Run standalone planning:
   ```bash
   uv run adws/adw_plan_iso.py 135
   ```
   ✅ Creates worktree at `trees/19db0b8b/`
   ✅ Completes successfully
   ✅ Posts "Planning workflow complete" message to GitHub

2. Run full SDLC workflow:
   ```bash
   uv run adws/adw_sdlc_complete_iso.py 135 19db0b8b
   ```
   ❌ Fails with:
   ```
   Failed to create worktree: fatal: 'feature-issue-135-adw-19db0b8b-avg-cost-metric-history-panel'
   is already used by worktree at '/Users/Warmonger0/tac/tac-webbuilder/trees/19db0b8b'
   ```

## Root Cause Analysis

### The State File Location Problem

**Current behavior:**
- ADW state is stored at: `trees/<adw_id>/agents/<adw_id>/adw_state.json`
- When `adw_plan_iso.py` runs, it creates state inside the worktree
- When `adw_sdlc_complete_iso.py` runs with provided `adw_id`, it creates a **NEW state file** in the **same location** but with **empty fields**
- The worktree validation logic (`validate_worktree()`) checks `state.get("worktree_path")`
- The new state has `worktree_path: null`, so validation returns `False`
- The code tries to create the worktree, but git detects the branch is already checked out

**Evidence from logs:**
```
Created new ADW state for provided ID: 19db0b8b
State: {
  "adw_id": "19db0b8b",
  "worktree_path": null,  ← Empty!
  ...
}
```

### The Validation Logic Flow

**File:** `adws/adw_plan_iso.py:109-113`
```python
# Check if worktree already exists
valid, error = validate_worktree(adw_id, state)
if valid:
    logger.info(f"Using existing worktree for {adw_id}")
    worktree_path = state.get("worktree_path")
```

**File:** `adws/adw_modules/worktree_ops.py:75-104`
```python
def validate_worktree(adw_id: str, state: ADWState) -> Tuple[bool, Optional[str]]:
    # Check state has worktree_path
    worktree_path = state.get("worktree_path")
    if not worktree_path:
        return False, "No worktree_path in state"  ← Fails here for fresh state

    # Check directory exists
    if not os.path.exists(worktree_path):
        return False, f"Worktree directory not found: {worktree_path}"

    # Check git knows about it
    result = subprocess.run(["git", "worktree", "list"], capture_output=True, text=True)
    if worktree_path not in result.stdout:
        return False, "Worktree not registered with git"

    return True, None
```

**The problem:** Validation depends on state having `worktree_path`, but fresh state doesn't have it.

## Impact

- ❌ Users cannot run full SDLC workflow after standalone planning
- ❌ "Ghost issues" created without workflows
- ❌ PRs created and immediately closed
- ❌ Wasted GitHub Actions runs
- ❌ Confusion about workflow failure reasons

## Affected Workflows

- `adw_sdlc_complete_iso.py` - Cannot resume after `adw_plan_iso.py`
- `adw_sdlc_complete_zte_iso.py` - Same issue
- Any workflow that calls planning as Phase 1

## Proposed Solutions

### Solution 1: Shared State Location (RECOMMENDED)
**Move state outside the worktree to a shared location**

**Change:**
```python
# Current: state inside worktree
state_path = trees/<adw_id>/agents/<adw_id>/adw_state.json

# Proposed: state in shared location
state_path = agents/<adw_id>/adw_state.json
```

**Pros:**
- ✅ State persists across workflow runs
- ✅ No worktree dependency
- ✅ Single source of truth
- ✅ Minimal code changes

**Cons:**
- ⚠️ Requires migration of existing states
- ⚠️ Changes state path convention

### Solution 2: Enhanced Worktree Detection
**Add git-based detection as fallback when state is empty**

**Change in `validate_worktree()`:**
```python
def validate_worktree(adw_id: str, state: ADWState) -> Tuple[bool, Optional[str]]:
    # Check state first (existing logic)
    worktree_path = state.get("worktree_path")

    if not worktree_path:
        # FALLBACK: Check git worktree list
        expected_path = get_worktree_path(adw_id)
        result = subprocess.run(["git", "worktree", "list"], capture_output=True, text=True)

        if expected_path in result.stdout and os.path.exists(expected_path):
            # Worktree exists in git but not in state - recover it
            return True, None

        return False, "No worktree_path in state and not found in git"

    # Rest of existing validation logic...
```

**Pros:**
- ✅ Backward compatible
- ✅ No state migration needed
- ✅ Recovers from state mismatches

**Cons:**
- ⚠️ More complex logic
- ⚠️ Relies on git command parsing
- ⚠️ Doesn't fix underlying state issue

### Solution 3: State Passing via CLI Flag
**Add `--resume` or `--reuse-worktree` flag**

**Usage:**
```bash
# First run creates state
uv run adws/adw_plan_iso.py 135

# Second run reuses state
uv run adws/adw_sdlc_complete_iso.py 135 19db0b8b --resume
```

**Implementation:**
```python
if "--resume" in sys.argv:
    # Load existing state from worktree
    existing_state_path = f"trees/{adw_id}/agents/{adw_id}/adw_state.json"
    if os.path.exists(existing_state_path):
        state = ADWState.load_from_file(existing_state_path, logger)
else:
    # Create fresh state
    state = ADWState.load(adw_id, logger)
```

**Pros:**
- ✅ Explicit user control
- ✅ No breaking changes
- ✅ Works with current state location

**Cons:**
- ⚠️ Requires user to remember flag
- ⚠️ Not automatic
- ⚠️ Extra CLI complexity

### Solution 4: Smart State Resolution
**Auto-detect and merge states from multiple locations**

**Logic:**
```python
def load_state_smart(adw_id: str, logger):
    # Check shared location first
    shared_state = load_from("agents/<adw_id>/adw_state.json")

    # Check worktree location
    worktree_state = load_from("trees/<adw_id>/agents/<adw_id>/adw_state.json")

    # Merge (worktree takes precedence for worktree-specific fields)
    return merge_states(shared_state, worktree_state)
```

**Pros:**
- ✅ Backward compatible
- ✅ Auto-recovery
- ✅ No user action needed

**Cons:**
- ⚠️ Complex merge logic
- ⚠️ Potential for state conflicts
- ⚠️ Hard to debug

## Recommended Fix

**Implement Solution 1 (Shared State) + Solution 2 (Enhanced Detection)**

1. **Immediate fix:** Add git-based fallback detection (Solution 2)
   - Allows workflows to complete now
   - No breaking changes

2. **Long-term fix:** Move state to shared location (Solution 1)
   - Prevents future issues
   - Cleaner architecture

## Implementation Plan

### Phase 1: Quick Fix (30 minutes)
1. Update `validate_worktree()` with git-based fallback
2. Test with Issue #135
3. Commit and deploy

### Phase 2: Long-term Fix (2 hours)
1. Create state migration script
2. Update state path convention
3. Update all ADW scripts to use shared location
4. Test full workflow chain
5. Document new state location

## Test Cases

### Test 1: Fresh Workflow
```bash
uv run adws/adw_sdlc_complete_iso.py 136
# Expected: ✅ Completes all 9 phases
```

### Test 2: Resume After Planning
```bash
uv run adws/adw_plan_iso.py 137
uv run adws/adw_sdlc_complete_iso.py 137 <adw-id>
# Expected: ✅ Detects existing worktree, continues from Validate phase
```

### Test 3: State Recovery
```bash
# Manually delete state file
rm agents/<adw-id>/adw_state.json
uv run adws/adw_sdlc_complete_iso.py 138 <adw-id>
# Expected: ✅ Detects worktree from git, recovers state
```

## Related Files

- `adws/adw_sdlc_complete_iso.py` - Main workflow orchestrator
- `adws/adw_plan_iso.py` - Planning phase
- `adws/adw_modules/worktree_ops.py` - Worktree management
- `adws/adw_modules/state.py` - State management

## Timeline

- **Discovered:** 2025-12-02 (Session with Issue #135)
- **Root Cause Identified:** 2025-12-02
- **Quick Fix Target:** 2025-12-03
- **Long-term Fix Target:** 2025-12-05

## Notes

- This bug explains why users see "Planning workflow complete" message but then full SDLC fails
- The worktree detection logic EXISTS but fails due to state location issue
- Observability system successfully logged this failure (Panel 10 working as intended)
