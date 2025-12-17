# ADW Workflow Validation Fixes - Session Summary

**Date:** 2025-12-16
**Session Goal:** Fix critical ADW workflow validation bugs preventing completion

---

## Issues Fixed

### 1. Missing psycopg2-binary Dependency (Commit 9d8ccd4 + d98da08)

**Problem:**
- StateValidator failed with `ModuleNotFoundError: No module named 'psycopg2'`
- Database queries required for validation couldn't execute

**Root Cause:**
- `adws/pyproject.toml` had psycopg2-binary dependency
- BUT ADW scripts use uv inline dependencies (`# /// script`)
- Inline scripts create isolated environments with ONLY listed dependencies
- psycopg2-binary was NOT in inline dependency lists

**Fix:**
```python
# Before (adw_sdlc_complete_iso.py, adw_plan_iso.py)
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

# After
# /// script
# dependencies = ["python-dotenv", "pydantic", "psycopg2-binary>=2.9.0"]
# ///
```

**Files Changed:**
- `adws/adw_sdlc_complete_iso.py` - Added psycopg2-binary to inline deps
- `adws/adw_plan_iso.py` - Added psycopg2-binary to inline deps

---

### 2. Non-existent Repository Method (Commits d98da08 + fb308bc)

**Problem:**
- Code called `PhaseQueueRepository.find_by_issue_number()`
- Method doesn't exist → AttributeError
- Validation failed with `'PhaseQueueRepository' object has no attribute 'find_by_issue_number'`

**Root Cause:**
- PhaseQueueRepository uses `feature_id` field to track issues
- Issue number stored as `feature_id` in ADW context
- Correct method is `get_all_by_feature_id(issue_number)`

**Fix:**
```python
# Before
workflow = repo.find_by_issue_number(issue_number)

# After
workflows = repo.get_all_by_feature_id(issue_number)
workflow = workflows[0] if workflows else None
```

**Files Changed:**
- `adws/utils/state_validator.py` - Fixed 2 instances (validate_inputs, validate_outputs)
- `adws/utils/idempotency.py` - Fixed 3 instances (get_or_create_state, get_worktree_path, ensure_database_state)

---

### 3. Database Records Required for Standalone Runs (Commit 02f7eac)

**Problem:**
- StateValidator REQUIRED database records from PhaseQueueRepository
- Standalone ADW tests (not launched by PhaseCoordinator) had no DB records
- Validation failed with "Workflow not found for issue X"

**Root Cause:**
- Design expects: PhaseCoordinator creates DB record → ADW executes → Validation checks DB
- Testing workflow: Run ADW directly → No DB record → Validation fails
- Database is SSoT (Single Source of Truth) for coordination
- But standalone testing shouldn't require full coordination infrastructure

**Fix:**
Added fallback to file-based validation when no database record exists:

```python
# If no database record exists
if not workflows:
    # Fall back to file-based validation
    warnings.append("No database record - using file-based validation (standalone mode)")
    workflow = None
    # Search agents directory for state files
    # Find worktree by matching issue_number in state files
```

**Files Changed:**
- `adws/utils/state_validator.py` - Added standalone mode support with file search fallback

---

### 4. None Workflow Crashes (Commit 52a545d)

**Problem:**
- After fixing #3, code tried to access `workflow.adw_id` when `workflow = None`
- Crashed with `'NoneType' object has no attribute 'adw_id'`

**Root Cause:**
- Validation methods assumed workflow object always exists
- Didn't handle None case introduced by standalone mode

**Fix:**
```python
# Before
if workflow.adw_id:
    # ...

# After
if workflow and workflow.adw_id:
    # ...
elif not workflow:
    # Standalone mode - validate using state instead
    if not state.get('adw_id'):
        errors.append("No adw_id in state")
```

**Files Changed:**
- `adws/utils/state_validator.py` - Added None checks in validate_inputs and _validate_plan_outputs

---

### 5. Worktree Backend Install Failure (Commit 8b11e2d)

**Problem:**
- Worktree setup failed with `error: package directory 'app' does not exist`
- Backend installation couldn't complete during plan phase
- Blocked workflow execution

**Root Cause:**
- `app/server/pyproject.toml` listed `packages = ["app", "core", "services", "utils"]`
- But inside `app/server/`, there is NO `app/` subdirectory
- Actual packages: core, services, utils, models, repositories, routes, database
- setuptools couldn't find the non-existent "app" package

**Fix:**
```toml
# Before
[tool.setuptools]
packages = ["app", "core", "services", "utils"]

# After
[tool.setuptools]
packages = ["core", "services", "utils", "models", "repositories", "routes", "database"]
```

**Files Changed:**
- `app/server/pyproject.toml` - Corrected package list

---

## Testing Results

### Before Fixes
- ❌ Plan phase validation: Failed with psycopg2 import error
- ❌ Database queries: Failed with missing method error
- ❌ Standalone ADW runs: Failed requiring database records
- ❌ Worktree setup: Failed with package directory error
- ❌ Retry loops: False validation failures triggered unnecessary retries

### After Fixes (Issues #214, #216)
- ✅ Plan phase validation: Psycopg2 imports successfully
- ✅ Database queries: Uses correct repository method
- ✅ Standalone ADW runs: Falls back to file-based validation
- ✅ Worktree setup: Backend installs successfully
- ✅ No retries: Plan phase validates correctly on first attempt
- ✅ PR creation: Issue #214 → PR #215, Issue #216 → PR #217
- ✅ Full workflow: Progressed through Plan → Validate → Build → Lint → Test phases

---

## Loop Detection Behavior Observed

**Circuit Breaker Settings:**
- Checks last 15 comments on issue
- Triggers if same agent posts 8+ times
- Threshold: Prevents infinite retry loops

**Why Loop Detection Triggered During Testing:**
Each failed workflow run posts ~10-15 comments:
1. Workflow start
2. Phase status updates
3. State displays
4. Classification, branch creation
5. Validation failures
6. 3 retry attempts (each posting comments)
7. Cleanup messages

**Result:** One failed run ≈ 10+ ops comments → Triggers circuit breaker on next attempt

**This is correct behavior** - prevents runaway workflows from spamming issues.

---

### 6. False Validation Failures Causing Retries (Commit fe03946)

**Problem:**
- Plan phase completed successfully (files created, branch pushed, PR created)
- Validation incorrectly reported "Plan phase incomplete after execution"
- Workflow retried unnecessarily, causing push failures and loop detection

**Root Cause:**
- Validation looked for `adw_state.json` in worktree: `trees/{adw_id}/adw_state.json`
- ADWState actually saves to agents directory: `agents/{adw_id}/adw_state.json`
- Validation couldn't find state file → false negative → triggered retries

**Fix:**
```python
# Check both locations for state file
state_file_worktree = worktree / 'adw_state.json'

# Primary location (where ADWState saves)
project_root = worktree.parent.parent
state_file_agents = project_root / 'agents' / adw_id / 'adw_state.json'

if not state_file_worktree.exists() and not (state_file_agents and state_file_agents.exists()):
    errors.append("adw_state.json not found")
```

**Files Changed:**
- `adws/utils/state_validator.py` - Check both locations, use portable paths

---

## Commits Pushed

All fixes pushed to main:

```
fe03946 fix: Check both agents/ and worktree locations for adw_state.json in validation
8b11e2d fix: Correct setuptools package list in app/server/pyproject.toml
52a545d fix: Handle None workflow in StateValidator phase validation methods
02f7eac fix: Make StateValidator work for standalone ADW runs without database records
fb308bc fix: Replace find_by_issue_number with get_all_by_feature_id in idempotency utils
d98da08 fix: Add psycopg2-binary to ADW inline dependencies and fix StateValidator repository method
9d8ccd4 fix: Add psycopg2-binary dependency to adws for database operations
```

---

## Files Modified Summary

### adws/ (ADW Workflow System)
- `adw_sdlc_complete_iso.py` - Added psycopg2-binary to inline deps
- `adw_plan_iso.py` - Added psycopg2-binary to inline deps
- `utils/state_validator.py` - Fixed repository method, added standalone mode, None checks
- `utils/idempotency.py` - Fixed repository method in 3 functions
- `pyproject.toml` - Already had psycopg2-binary (not the issue)

### app/server/ (Backend)
- `pyproject.toml` - Corrected setuptools package list

---

## Architecture Insights

### Database as Source of Truth (SSoT)

**Design Pattern:**
```
PhaseCoordinator (creates DB records)
    ↓
ADW Workflows (update DB status)
    ↓
StateValidator (checks DB for validation)
```

**Two Operating Modes:**

1. **Production Mode** (PhaseCoordinator orchestrated):
   - DB records exist
   - Full validation against database SSoT
   - Coordination state managed centrally

2. **Standalone Mode** (Direct ADW execution):
   - No DB records
   - Falls back to file-based validation
   - Uses state files in agents/ directory
   - Warnings logged, not errors

### Inline Script Dependencies

**Key Lesson:** uv inline scripts (`# /// script`) create isolated environments.

Dependencies must be declared inline, NOT just in pyproject.toml:
```python
#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "psycopg2-binary>=2.9.0"]
# ///
```

Even if `adws/pyproject.toml` has the dependency, inline scripts won't see it.

---

## Next Steps

### Recommended
1. ✅ Test on fresh issue (no retry history) - Validation fixes are working
2. ✅ Monitor auto-triggered workflows via PhaseCoordinator
3. Consider adding other ADW scripts' inline dependencies if they need DB access

### Future Improvements
1. Add integration test for standalone ADW mode
2. Document inline dependency pattern for new ADW scripts
3. Consider making worktree backend install optional for plan-only phases
4. Review loop detection threshold (currently 8/15 may be conservative)

---

## Key Takeaways

✅ **Root Cause:** Inline script dependencies were incomplete
✅ **Secondary Issue:** Wrong repository method called (5 locations)
✅ **Design Decision:** Standalone mode now supported via fallback validation
✅ **Pre-existing Bugs:** Fixed pyproject.toml package list & state file location check
✅ **Retry Prevention:** Validation now checks correct locations, no false failures

**All 6 critical validation bugs resolved and committed.**

### Bugs Fixed Summary

1. ✅ Missing psycopg2-binary in inline script dependencies
2. ✅ Non-existent find_by_issue_number() method (5 locations)
3. ✅ Database records required for standalone mode
4. ✅ None workflow attribute access crashes
5. ✅ Incorrect pyproject.toml package list
6. ✅ State file location mismatch causing false validation failures
