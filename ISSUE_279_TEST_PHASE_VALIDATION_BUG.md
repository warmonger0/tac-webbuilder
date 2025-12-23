# Issue #279: Test Phase Validation Failure - CRITICAL BUG

## Executive Summary

**Bug:** Test phase validation fails even when tests complete successfully
**Root Cause:** StateValidator reads state from WRONG location (`trees/` instead of `agents/`)
**Impact:** BLOCKS workflow progression, requires manual intervention
**Severity:** CRITICAL - Affects ALL test phases in ALL workflows
**Status:** 🔴 UNFIXED (distinct from original #279 external results bug which IS fixed)

---

## The Bug

### Symptoms

```
❌ Test phase validation failed: Test phase incomplete after execution
❌ Test phase did not record external_test_results
```

This error occurs EVEN WHEN:
- ✅ Tests actually ran successfully
- ✅ `state.save("adw_test_iso")` was called
- ✅ `external_test_results` WAS saved to state
- ✅ State file exists in `agents/{adw_id}/adw_state.json`

### Root Cause Analysis

**STATE PATH MISMATCH:**

1. **ADWState.save()** writes to:
   ```
   /agents/{adw_id}/adw_state.json
   ```
   Source: `adws/adw_modules/state.py:99`

2. **StateValidator.validate_outputs()** reads from:
   ```
   /trees/{adw_id}/adw_state.json  ❌ WRONG PATH
   ```
   Source: `adws/utils/state_validator.py:258`

**Flow:**

```
Step 1: Test Phase Completes
├─> state.data["external_test_results"] = {...}
├─> state.save("adw_test_iso")
└─> Writes to: /agents/{adw_id}/adw_state.json ✅

Step 2: Validation Called
├─> validate_phase_completion('test', issue_number, logger)
├─> StateValidator.validate_outputs(issue_number)
├─> Reads from: /trees/{adw_id}/adw_state.json ❌ WRONG
└─> Finds old/stale state WITHOUT external_test_results

Step 3: Validation Fails
├─> test_results = state.get('external_test_results')
├─> if not test_results:
├─>     errors.append("Test phase did not record external_test_results")
└─> raise ValueError("Test phase incomplete after execution")
```

---

## The Code

### Bug Location 1: StateValidator Loading Stale State

**File:** `adws/utils/state_validator.py:256-264`

```python
if worktree_path and not state:
    state_file = Path(worktree_path) / 'adw_state.json'  # ❌ BUG: Wrong path
    if state_file.exists():
        try:
            with open(state_file) as f:
                state = json.load(f)
        except Exception as e:
            warnings.append(f"Failed to load state file: {str(e)}")
```

**Problem:** `worktree_path` is `/trees/{adw_id}`, but state is saved to `/agents/{adw_id}`

### Bug Location 2: Validation Check

**File:** `adws/utils/state_validator.py:585-594`

```python
def _validate_test_outputs(self, workflow: Any, state: dict, worktree_path: Optional[str]) -> List[str]:
    """Validate test phase outputs."""
    errors = []

    # Should have test results
    test_results = state.get('external_test_results')
    if not test_results:
        errors.append("Test phase did not record external_test_results")  # ❌ Fails due to stale state

    return errors
```

**Problem:** `state` is loaded from wrong path, so `external_test_results` is missing

---

## Why This Wasn't Caught Earlier

### The Fallback Logic

StateValidator DOES have fallback logic at lines 229-255:

```python
if not workflow or not worktree_path:
    # Fallback: Search agents/ directories by issue_number
    agents_dir = project_root / 'agents'
    if agents_dir.exists():
        for agent_dir in sorted(agents_dir.iterdir(), ...):
            state_file = agent_dir / 'adw_state.json'
            if state_file.exists():
                # ... load and check issue_number ...
```

**BUT:** This fallback only triggers when:
- `workflow` is None (no database record), OR
- `worktree_path` is None (worktree not found)

**In normal operation:**
- ✅ `workflow` exists (database record found)
- ✅ `worktree_path` exists (`/trees/{adw_id}`)
- ❌ Fallback NEVER runs
- ❌ Wrong path used

---

## Impact Analysis

### Affected Workflows

**ALL workflows with Test phase:**
- `adw_sdlc_complete_iso`
- `adw_sdlc_complete_zte_iso`
- `adw_sdlc_iso`
- `adw_plan_build_test_iso`
- `adw_plan_build_test_review_iso`
- `adw_test_iso` (standalone)
- `adw_lightweight_iso`

### Failure Symptoms

```
1. Test phase runs successfully
   └─> Tests pass/fail correctly
   └─> Results saved to state

2. Validation fails immediately after
   └─> "Test phase incomplete after execution"
   └─> Workflow BLOCKED

3. Manual intervention required
   └─> Developer must debug state files
   └─> Must manually verify tests passed
   └─> Must skip validation or fix state
```

### Cascading Effects

```
Test validation fails
  ↓
Workflow exits with error
  ↓
Auto-continuation blocked (if enabled)
  ↓
Review phase never runs
  ↓
Ship phase never runs
  ↓
Manual recovery required
```

---

## The Fix

### Option 1: Fix StateValidator Path (RECOMMENDED)

**File:** `adws/utils/state_validator.py:256-264`

```python
# BEFORE (BUGGY)
if worktree_path and not state:
    state_file = Path(worktree_path) / 'adw_state.json'  # ❌ Wrong path
    if state_file.exists():
        ...

# AFTER (FIXED)
if worktree_path and not state:
    # CRITICAL FIX: Load state from agents/ directory, NOT trees/ directory
    # ADWState saves to agents/{adw_id}/adw_state.json (see state.py:99)
    if adw_id:
        project_root = Path(worktree_path).parent.parent  # trees/{adw_id} -> project_root
        state_file = project_root / 'agents' / adw_id / 'adw_state.json'

        if state_file.exists():
            try:
                with open(state_file) as f:
                    state = json.load(f)
            except Exception as e:
                warnings.append(f"Failed to load state file: {str(e)}")
        else:
            # Fallback: Try worktree path (legacy support)
            state_file_worktree = Path(worktree_path) / 'adw_state.json'
            if state_file_worktree.exists():
                try:
                    with open(state_file_worktree) as f:
                        state = json.load(f)
                except Exception as e:
                    warnings.append(f"Failed to load state file: {str(e)}")
```

### Option 2: Use ADWState.load() (BETTER)

```python
# Replace raw file loading with ADWState.load()
if adw_id and not state:
    from adw_modules.state import ADWState
    loaded_state = ADWState.load(adw_id, logger)
    if loaded_state:
        state = loaded_state.data
```

This is better because:
- Uses the SAME loading logic as ADWState
- Automatically handles path resolution
- No path hardcoding
- Consistent behavior

---

## Regression Test

**File:** `adws/tests/test_phase_validation_state_loading.py` (NEW)

```python
"""
Regression test for Issue #279: Test phase validation reads stale state.

Ensures StateValidator loads state from correct location (agents/ not trees/).
"""

import tempfile
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_modules.state import ADWState
from adw_modules.utils import setup_logger
from utils.state_validator import StateValidator


def test_state_validator_loads_from_correct_path():
    """Test that StateValidator reads from agents/ directory, not trees/."""

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        adw_id = "test-validation-123"
        issue_number = 999

        # Setup directories
        agents_dir = project_root / "agents" / adw_id
        trees_dir = project_root / "trees" / adw_id
        agents_dir.mkdir(parents=True)
        trees_dir.mkdir(parents=True)

        # Save CORRECT state to agents/ (where ADWState.save() puts it)
        correct_state = {
            "adw_id": adw_id,
            "issue_number": issue_number,
            "worktree_path": str(trees_dir),
            "external_test_results": {
                "success": True,
                "summary": {"total": 10, "passed": 10, "failed": 0},
                "failures": []
            }
        }

        agents_state_file = agents_dir / "adw_state.json"
        with open(agents_state_file, 'w') as f:
            json.dump(correct_state, f)

        # Save STALE state to trees/ (old/wrong location)
        stale_state = {
            "adw_id": adw_id,
            "issue_number": issue_number,
            "worktree_path": str(trees_dir),
            # NO external_test_results (stale)
        }

        trees_state_file = trees_dir / "adw_state.json"
        with open(trees_state_file, 'w') as f:
            json.dump(stale_state, f)

        # Temporarily change working directory for ADWState resolution
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(project_root)

            # Create validator and validate
            validator = StateValidator(phase='test')
            result = validator.validate_outputs(issue_number)

            # CRITICAL: Validation should PASS because correct state is in agents/
            assert result.is_valid, f"Validation should pass. Errors: {result.errors}"

            # If this fails, StateValidator is reading from trees/ (stale state)
            # instead of agents/ (correct state)

            print("✅ StateValidator correctly reads from agents/ directory")

        finally:
            os.chdir(old_cwd)


def test_state_validator_falls_back_to_trees_if_agents_missing():
    """Test that StateValidator falls back to trees/ if agents/ doesn't exist."""

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        adw_id = "test-fallback-456"
        issue_number = 998

        # Only create trees/ directory (no agents/)
        trees_dir = project_root / "trees" / adw_id
        trees_dir.mkdir(parents=True)

        # Save state to trees/ only
        state_data = {
            "adw_id": adw_id,
            "issue_number": issue_number,
            "worktree_path": str(trees_dir),
            "external_test_results": {
                "success": True,
                "summary": {"total": 5, "passed": 5, "failed": 0}
            }
        }

        trees_state_file = trees_dir / "adw_state.json"
        with open(trees_state_file, 'w') as f:
            json.dump(state_data, f)

        # Validate - should fall back to trees/
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(project_root)

            validator = StateValidator(phase='test')
            result = validator.validate_outputs(issue_number)

            # Should still pass (fallback works)
            assert result.is_valid, f"Fallback validation should pass. Errors: {result.errors}"

            print("✅ StateValidator correctly falls back to trees/ when agents/ missing")

        finally:
            os.chdir(old_cwd)


if __name__ == "__main__":
    print("Running state validator path regression tests...\n")

    try:
        test_state_validator_loads_from_correct_path()
        test_state_validator_falls_back_to_trees_if_agents_missing()

        print("\n✅ All tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
```

---

## Recommended Actions

### Immediate (This Hour)

1. **Fix StateValidator path** in `adws/utils/state_validator.py:256-264`
2. **Use ADWState.load()** instead of raw file loading
3. **Create regression test** to prevent recurrence

### Short-Term (Today)

1. **Test the fix** with real workflow
2. **Verify all phases** (Build, Lint, Test) validate correctly
3. **Check Build/Lint phases** - they likely have same bug!

### Long-Term (This Week)

1. **Audit all state loading** for path mismatches
2. **Centralize state loading** - use ADWState.load() everywhere
3. **Document state paths** in architecture docs

---

## Prevention Strategy

### 1. Centralize State Loading

**Rule:** NEVER load state manually - always use `ADWState.load()`

```python
# ❌ NEVER DO THIS
with open(worktree_path / 'adw_state.json') as f:
    state = json.load(f)

# ✅ ALWAYS DO THIS
from adw_modules.state import ADWState
state_obj = ADWState.load(adw_id, logger)
state = state_obj.data if state_obj else {}
```

### 2. Path Constants

Define state paths in ONE place:

```python
# adw_modules/constants.py
def get_state_path(adw_id: str) -> Path:
    """Get canonical state file path."""
    project_root = get_project_root()
    return project_root / "agents" / adw_id / "adw_state.json"
```

### 3. Validation Tests

Add tests that verify:
- State saved to correct path
- State loaded from correct path
- Fallback logic works
- No stale state used

---

## Related Bugs

### 1. Build Phase Validation (Likely Same Bug)

**File:** `adws/utils/state_validator.py:563-572`

```python
def _validate_build_outputs(self, workflow: Any, state: dict, worktree_path: Optional[str]) -> List[str]:
    """Validate build phase outputs."""
    errors = []

    # Should have build results
    build_results = state.get('external_build_results')
    if not build_results:
        errors.append("Build phase did not record external_build_results")  # ❌ Likely fails too!

    return errors
```

**Risk:** Same path mismatch bug

### 2. Lint Phase Validation (Likely Same Bug)

**File:** `adws/utils/state_validator.py:574-583`

```python
def _validate_lint_outputs(self, workflow: Any, state: dict, worktree_path: Optional[str]) -> List[str]:
    """Validate lint phase outputs."""
    errors = []

    # Should have lint results
    lint_results = state.get('external_lint_results')
    if not lint_results:
        errors.append("Lint phase did not record external_lint_results")  # ❌ Likely fails too!

    return errors
```

**Risk:** Same path mismatch bug

---

## Summary

**What:** StateValidator reads state from `/trees/{adw_id}/` instead of `/agents/{adw_id}/`
**Why:** Hard-coded path assumes state is in worktree, but ADWState saves to agents/
**Impact:** All Test/Build/Lint phase validations fail with "phase incomplete"
**Fix:** Use `ADWState.load(adw_id)` instead of manual file loading
**Severity:** CRITICAL - Blocks all workflows

**Status:** 🔴 UNFIXED (separate from original Issue #279 external results bug)

---

**Created:** 2025-12-22
**Last Updated:** 2025-12-22
**Priority:** P0 - CRITICAL
**Assignee:** TBD
**Estimated Fix Time:** 30 minutes
**Estimated Test Time:** 1 hour
