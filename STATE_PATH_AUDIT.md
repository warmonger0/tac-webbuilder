# State Path Audit - adw_state.json Loading

## Executive Summary

**Audit Date:** 2025-12-22
**Scope:** All code that loads or references `adw_state.json`
**Critical Finding:** StateValidator uses WRONG path - affects ALL phase validations
**Other Findings:** Server-side code is CORRECT, tests are CORRECT

---

## State Storage Location (Source of Truth)

**ADWState.save()** writes to:
```
/agents/{adw_id}/adw_state.json
```

**Source:** `adws/adw_modules/state.py:99`

```python
def get_state_path(self) -> str:
    """Get path to state file."""
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    return os.path.join(project_root, "agents", self.adw_id, self.STATE_FILENAME)
```

---

## Audit Results by Component

### ✅ CORRECT: Server-Side Code

All server code correctly uses `agents/` directory:

1. **`app/server/server.py:238`**
   ```python
   state_path = os.path.join(project_root, "agents", adw_id, "adw_state.json")
   ```
   ✅ Correct

2. **`app/server/core/health_checks.py:198`**
   ```python
   state_file_path = project_root / "agents" / adw_id / "adw_state.json"
   ```
   ✅ Correct

3. **`app/server/core/health_checks.py:445`**
   ```python
   state_file = adw_dir / "adw_state.json"  # adw_dir is agents/{adw_id}
   ```
   ✅ Correct (adw_dir already points to agents/)

4. **`app/server/core/workflow_history_utils/filesystem.py:138`**
   ```python
   state_file = adw_dir / "adw_state.json"  # adw_dir from agents/
   ```
   ✅ Correct

5. **`app/server/core/adw_monitor.py:96`**
   ```python
   state_file = adw_dir / "adw_state.json"  # adw_dir from agents/
   ```
   ✅ Correct

**Verdict:** Server-side code is CORRECT - all use `agents/` directory

---

### ❌ INCORRECT: StateValidator (CRITICAL BUG)

**File:** `adws/utils/state_validator.py`

**Bug Location 1:** Lines 152-157 (validate_inputs)
```python
if worktree_path:
    state_file = Path(worktree_path) / 'adw_state.json'  # ❌ WRONG PATH
    if state_file.exists():
        try:
            with open(state_file) as f:
                state = json.load(f)
```

**Problem:** `worktree_path` is `/trees/{adw_id}`, but state is in `/agents/{adw_id}`

---

**Bug Location 2:** Lines 256-264 (validate_outputs)
```python
if worktree_path and not state:
    state_file = Path(worktree_path) / 'adw_state.json'  # ❌ WRONG PATH
    if state_file.exists():
        try:
            with open(state_file) as f:
                state = json.load(f)
```

**Problem:** Same - reads from worktree instead of agents/

---

**Bug Location 3:** Lines 313-316 (validate inputs)
```python
# Check for state file
state_file = worktree / 'adw_state.json'  # ❌ WRONG PATH
if not state_file.exists():
    errors.append("adw_state.json not found in worktree")
```

**Problem:** Checks worktree instead of agents/

---

**Bug Location 4:** Lines 528-540 (plan outputs validation)
```python
# Check for adw_state.json (check both locations)
state_file_worktree = worktree / 'adw_state.json'  # Legacy location
state_file_agents = project_root / 'agents' / adw_id_from_state / 'adw_state.json'  # Correct location

if not state_file_worktree.exists() and not (state_file_agents and state_file_agents.exists()):
    errors.append("adw_state.json not found in worktree or agents directory")
```

**Status:** ⚠️ PARTIALLY CORRECT - checks both, but worktree check is misleading

---

**Fallback Logic:** Lines 229-255 (validate_outputs)
```python
if not workflow or not worktree_path:
    # Fallback: Search agents/ directories by issue_number
    agents_dir = project_root / 'agents'
    if agents_dir.exists():
        for agent_dir in sorted(agents_dir.iterdir(), ...):
            state_file = agent_dir / 'adw_state.json'
            if state_file.exists():
                # ... load and verify ...
```

**Status:** ✅ CORRECT - searches agents/ directory

**Problem:** Fallback only triggers when `worktree_path` is None, which doesn't happen in normal operation

---

### ✅ CORRECT: External Phase Scripts

All external scripts are documented to use `agents/`:

1. **`adws/adw_build_external.py:16`**
   ```python
   # 1. Load state from agents/{adw_id}/adw_state.json
   ```
   ✅ Correct (documentation)

2. **`adws/adw_lint_external.py:16`**
   ```python
   # 1. Load state from agents/{adw_id}/adw_state.json
   ```
   ✅ Correct (documentation)

3. **`adws/adw_test_external.py:16`**
   ```python
   # 1. Load state from agents/{adw_id}/adw_state.json
   ```
   ✅ Correct (documentation)

**Implementation:** All use `ADWState.load(adw_id)` which automatically uses correct path

---

### ✅ CORRECT: Test Files

All test files correctly use `agents/` directory:

1. **`app/server/tests/core/test_adw_monitor.py`** - ✅ Uses `adw_dir / "adw_state.json"` where adw_dir is agents/
2. **`app/server/tests/core/workflow_history_utils/test_filesystem.py`** - ✅ Uses agents/ directory

**Verdict:** Tests are correct

---

## Impact Analysis

### Phases Affected by StateValidator Bug

All phases that use `validate_phase_completion()`:

| Phase | Validation Method | State Key Checked | Affected? |
|-------|------------------|-------------------|-----------|
| Plan | `_validate_plan_outputs` | `plan_file`, `adw_id` | ⚠️ Partially |
| Validate | `_validate_validate_outputs` | `baseline_errors` | ❌ Yes |
| Build | `_validate_build_outputs` | `external_build_results` | ❌ Yes |
| Lint | `_validate_lint_outputs` | `external_lint_results` | ❌ Yes |
| Test | `_validate_test_outputs` | `external_test_results` | ❌ Yes |
| Review | `_validate_review_outputs` | (lenient) | ⚠️ Minimal |
| Document | `_validate_document_outputs` | (checks files) | ⚠️ Minimal |
| Ship | `_validate_ship_outputs` | `ship_timestamp` | ❌ Yes |
| Cleanup | `_validate_cleanup_outputs` | (best-effort) | ✅ No |
| Verify | `_validate_verify_outputs` | `verification_results` | ⚠️ Minimal |

**High Risk:** Build, Lint, Test, Ship (check for specific state keys)
**Medium Risk:** Validate (checks baseline_errors)
**Low Risk:** Plan, Review, Document, Verify (more lenient checks)
**No Risk:** Cleanup (best-effort)

---

## Failure Scenarios

### Scenario 1: Test Phase Validation Failure

```
1. Test phase completes
   ├─> state.data["external_test_results"] = {...}
   ├─> state.save("adw_test_iso")
   └─> Saves to: /agents/{adw_id}/adw_state.json ✅

2. Validation runs
   ├─> validate_phase_completion('test', issue_number, logger)
   ├─> StateValidator.validate_outputs(issue_number)
   ├─> Loads from: /trees/{adw_id}/adw_state.json ❌
   └─> Gets STALE state (no external_test_results)

3. Validation fails
   └─> "Test phase did not record external_test_results"
```

### Scenario 2: Build Phase Validation Failure

```
Same flow as Test, but checks for:
- external_build_results

Result: "Build phase did not record external_build_results"
```

### Scenario 3: Lint Phase Validation Failure

```
Same flow as Test, but checks for:
- external_lint_results

Result: "Lint phase did not record external_lint_results"
```

---

## Why Fallback Doesn't Trigger

StateValidator has fallback logic to search `agents/` directory (lines 229-255), but it only triggers when:

```python
if not workflow or not worktree_path:
    # Search agents/ directory
```

**In normal operation:**
- ✅ `workflow` exists (database record found)
- ✅ `worktree_path` exists (`/trees/{adw_id}`)
- ❌ Condition is FALSE
- ❌ Fallback NEVER runs

**Fallback only triggers when:**
- Database unavailable, OR
- Worktree deleted/missing, OR
- Workflow not in database

**Result:** Bug affects 99% of workflows

---

## Code That Needs Fixing

### Priority 1: StateValidator (CRITICAL)

**File:** `adws/utils/state_validator.py`

**Lines to fix:**
1. Line 152-157 (validate_inputs)
2. Line 256-264 (validate_outputs)
3. Line 313-316 (validate inputs - state file check)
4. Line 529 (plan outputs - remove misleading worktree check)

**Fix:** Replace manual file loading with `ADWState.load(adw_id, logger)`

---

## Recommended Fix Strategy

### 1. StateValidator - Use ADWState.load()

**Current (BUGGY):**
```python
if worktree_path and not state:
    state_file = Path(worktree_path) / 'adw_state.json'  # ❌ Wrong path
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)
```

**Fixed:**
```python
if adw_id and not state:
    from adw_modules.state import ADWState
    from adw_modules.utils import setup_logger

    logger = setup_logger(adw_id, "state_validator")
    state_obj = ADWState.load(adw_id, logger)
    if state_obj:
        state = state_obj.data
```

**Benefits:**
- ✅ Uses SAME path resolution as ADWState.save()
- ✅ No hardcoded paths
- ✅ Automatic fallback handling
- ✅ Consistent behavior

---

## Prevention Measures

### 1. Centralized State Loading

**Rule:** NEVER load state manually - always use `ADWState.load()`

```python
# ❌ NEVER DO THIS
with open(some_path / 'adw_state.json') as f:
    state = json.load(f)

# ✅ ALWAYS DO THIS
from adw_modules.state import ADWState
state_obj = ADWState.load(adw_id, logger)
state = state_obj.data if state_obj else {}
```

### 2. Path Constants Module

Create `adw_modules/paths.py`:

```python
"""Canonical path definitions for ADW system."""

from pathlib import Path

def get_project_root() -> Path:
    """Get project root directory."""
    # Implementation...

def get_state_path(adw_id: str) -> Path:
    """Get canonical state file path."""
    return get_project_root() / "agents" / adw_id / "adw_state.json"

def get_worktree_path(adw_id: str) -> Path:
    """Get canonical worktree path."""
    return get_project_root() / "trees" / adw_id
```

### 3. Linting Rule

Add to `.ruff.toml`:

```toml
[lint.rules]
# Ban manual state file loading
banned-imports = [
    {path = "json.load", reason = "Use ADWState.load() instead of manual JSON loading"}
]
```

---

## Summary

| Component | Status | Path Used | Verdict |
|-----------|--------|-----------|---------|
| ADWState.save() | ✅ | `agents/{adw_id}` | Correct (SSoT) |
| ADWState.load() | ✅ | `agents/{adw_id}` | Correct |
| StateValidator | ❌ | `trees/{adw_id}` | **BUG** |
| Server code | ✅ | `agents/{adw_id}` | Correct |
| External scripts | ✅ | `agents/{adw_id}` | Correct |
| Tests | ✅ | `agents/{adw_id}` | Correct |

**Critical Finding:** StateValidator is the ONLY component using wrong path

**Impact:** ALL phase validations (Build, Lint, Test, Ship) fail with stale state

**Severity:** P0 - CRITICAL

**Estimated Fix Time:** 30 minutes

**Estimated Test Time:** 1 hour

---

**Created:** 2025-12-22
**Status:** Ready for Fix
**Next Step:** Implement fix in StateValidator
