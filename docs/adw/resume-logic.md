# ADW Workflow Resume Logic

## Overview

ADW (Automated Development Workflow) workflows support resuming from where they left off using persistent state files. This prevents duplicate work and allows workflows to be interrupted and resumed gracefully.

## State Management

### State File Location
Each ADW workflow stores its state in:
```
agents/{adw_id}/adw_state.json
```

### Core State Fields (ADWStateData)
```python
{
  "adw_id": str,                    # Unique workflow identifier
  "issue_number": str,              # GitHub issue number
  "branch_name": str,               # Git branch for this workflow
  "plan_file": str,                 # Path to implementation plan
  "issue_class": str,               # /chore, /bug, /feature, /patch
  "worktree_path": str,             # Path to isolated git worktree
  "backend_port": int,              # Allocated backend port
  "frontend_port": int,             # Allocated frontend port
  "model_set": str,                 # "base" or "heavy"
  "all_adws": List[str]             # List of completed workflow steps
}
```

### Extended State Fields
State files can contain additional fields beyond core fields:
- `external_build_results`: Results from build validation
- `external_lint_results`: Results from lint checks
- `external_test_results`: Results from test execution
- `estimated_cost_total`: Cost estimates
- `estimated_cost_breakdown`: Detailed cost breakdown

**Note:** The state persistence layer automatically preserves ALL fields, not just core fields.

## Resume Detection

### How Workflows Detect Resume State

1. **State File Check**: Workflow checks if `agents/{adw_id}/adw_state.json` exists
2. **Validation**: Validates core fields using `ADWStateData` Pydantic model
3. **Full Data Load**: Loads complete JSON (including extra fields) into `state.data`
4. **Progress Tracking**: Checks `all_adws` array to see which phases completed

### State Loading Pattern
```python
# Correct pattern (as of latest fix)
state = ADWState.load(adw_id, logger)
if not state:
    # No existing state - fresh start
    state = ADWState(adw_id)
    state.update(
        issue_number=issue_number,
        branch_name=branch_name,
        # ... other fields
    )
else:
    # State exists - resume mode
    logger.info("🔍 Found existing state - resuming workflow")
    completed_phases = state.get("all_adws", [])
```

## Workflow Phase Tracking

### The `all_adws` Array

Each workflow phase appends its identifier to the `all_adws` array:

```python
state.append_adw_id("adw_plan_iso")      # Phase 1: Planning
state.append_adw_id("adw_build_iso")     # Phase 2: Build
state.append_adw_id("adw_lint_iso")      # Phase 3: Lint
state.append_adw_id("adw_test_iso")      # Phase 4: Test
state.append_adw_id("adw_review_iso")    # Phase 5: Review (optional)
state.append_adw_id("adw_document_iso")  # Phase 6: Document (optional)
state.append_adw_id("adw_ship_iso")      # Phase 7: Ship
state.append_adw_id("adw_cleanup_iso")   # Phase 8: Cleanup
```

### Resume Logic Example

```python
completed_phases = state.get("all_adws", [])

# Check if planning already done
if "adw_plan_iso" not in completed_phases:
    run_planning_phase()
    state.append_adw_id("adw_plan_iso")
    state.save(workflow_step="plan")
else:
    logger.info("⏭️ Skipping planning - already completed")

# Check if build already done
if "adw_build_iso" not in completed_phases:
    run_build_phase()
    state.append_adw_id("adw_build_iso")
    state.save(workflow_step="build")
else:
    logger.info("⏭️ Skipping build - already completed")

# ... continue for remaining phases
```

## ZTE (Zero Touch Execution) Workflows

### Current Limitation

**Problem:** The `adw_sdlc_complete_zte_iso.py` workflow does NOT support resume. It always starts from Phase 1 (planning), even if state exists.

**Impact:** If a ZTE workflow is interrupted:
- Running it again will duplicate all work
- No resume detection or skipping of completed phases

### Workaround: Manual Phase Execution

If a ZTE workflow is interrupted, resume manually by running individual phases:

```bash
# Check completed phases
cat agents/{adw_id}/adw_state.json | jq '.all_adws'

# Example output:
# ["adw_plan_iso", "adw_build_iso", "adw_lint_iso"]

# Resume from test phase (if build/lint completed)
uv run adws/adw_test_iso.py {issue_number} {adw_id}

# Then run remaining phases
uv run adws/adw_review_iso.py {issue_number} {adw_id}  # Optional
uv run adws/adw_ship_iso.py {issue_number} {adw_id}
uv run adws/adw_cleanup_iso.py {issue_number} {adw_id}
```

### Recommended Enhancement

Add resume logic to ZTE workflows:

```python
# At start of adw_sdlc_complete_zte_iso.py
state = ADWState.load(adw_id, logger)
completed = state.get("all_adws", []) if state else []

# Skip completed phases
phases = [
    ("plan", adw_plan_iso, "adw_plan_iso"),
    ("build", adw_build_iso, "adw_build_iso"),
    ("lint", adw_lint_iso, "adw_lint_iso"),
    ("test", adw_test_iso, "adw_test_iso"),
    ("review", adw_review_iso, "adw_review_iso"),
    ("document", adw_document_iso, "adw_document_iso"),
    ("ship", adw_ship_iso, "adw_ship_iso"),
    ("cleanup", adw_cleanup_iso, "adw_cleanup_iso"),
]

for phase_name, phase_func, phase_id in phases:
    if phase_id not in completed:
        logger.info(f"▶️ Running {phase_name} phase")
        phase_func(issue_number, adw_id)
    else:
        logger.info(f"⏭️ Skipping {phase_name} - already completed")
```

## Individual Workflow Scripts

Individual phase scripts (`adw_plan_iso.py`, `adw_build_iso.py`, etc.) DO support resume:

1. **Load existing state** at startup
2. **Validate dependencies** (e.g., build requires plan to exist)
3. **Skip if already run** (check `all_adws` array)
4. **Execute phase** if not completed
5. **Update state** and append to `all_adws`

### Example: Build Phase Resume

```python
# adw_build_iso.py startup logic
state = ADWState.load(adw_id, logger)

if not state:
    logger.error("No state found - run planning first")
    sys.exit(1)

if "adw_build_iso" in state.get("all_adws", []):
    logger.info("Build already completed - skipping")
    sys.exit(0)

if "adw_plan_iso" not in state.get("all_adws", []):
    logger.error("Planning not complete - run adw_plan_iso.py first")
    sys.exit(1)

# Proceed with build...
```

## State Persistence Fixes (Nov 2025)

### Issues Fixed

1. **TypeError in state loading** - `state.load()` was called as instance method instead of classmethod
2. **Extra fields not persisted** - State save/load only preserved core ADWStateData fields
3. **External results lost** - Build/lint/test results were stored but not persisted

### Solution

- Modified `ADWState.save()` to preserve all fields in `self.data`, not just core fields
- Modified `ADWState.load()` to load complete JSON while still validating core fields
- Fixed all workflows to use `ADWState.load(adw_id)` classmethod pattern

## Best Practices

### 1. Always Check State Before Starting
```python
state = ADWState.load(adw_id, logger)
if state:
    logger.info("Resuming workflow from existing state")
else:
    logger.info("Starting fresh workflow")
    state = ADWState(adw_id)
```

### 2. Track Progress Granularly
```python
# Mark each sub-step
state.append_adw_id("adw_build_iso")
state.data["build_completed_at"] = datetime.now().isoformat()
state.save(workflow_step="build_complete")
```

### 3. Validate Dependencies
```python
if "adw_plan_iso" not in state.get("all_adws", []):
    raise ValueError("Cannot run build without planning")
```

### 4. Store Phase Results
```python
# External workflows can store results in state
state.data["external_build_results"] = {
    "success": True,
    "summary": { "total_errors": 0 }
}
state.save(workflow_step="build_external")
```

### 5. Clean State on Completion
```python
# Cleanup phase removes worktree and archives docs
# State file remains for audit trail
state.append_adw_id("adw_cleanup_iso")
state.save(workflow_step="cleanup_complete")
```

## Debugging Resume Issues

### Check Current State
```bash
cat agents/{adw_id}/adw_state.json | jq '.all_adws'
```

### Verify State Loading
```bash
uv run python3 -c "
import sys
sys.path.insert(0, 'adws')
from adw_modules.state import ADWState
state = ADWState.load('{adw_id}')
print(f'Loaded: {state is not None}')
if state:
    print(f'Completed: {state.get(\"all_adws\", [])}')
"
```

### Manual State Repair
```bash
# If state is corrupted, manually edit
cat agents/{adw_id}/adw_state.json | jq '.all_adws += ["adw_plan_iso"]' > temp.json
mv temp.json agents/{adw_id}/adw_state.json
```

## Future Enhancements

1. **Add resume support to ZTE workflows** - Detect and skip completed phases
2. **State versioning** - Track state schema version for backwards compatibility
3. **Phase rollback** - Remove phase from `all_adws` to re-run with fixes
4. **State snapshots** - Backup state before each phase for rollback
5. **Resume UI** - Web interface showing workflow progress and resume options
