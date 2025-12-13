# Task: Implement Idempotent ADW Phases

## Context
I'm working on the tac-webbuilder project. Phase 2 of Session 19 addresses dual-state management issues. This is Part 4 of 4 (FINAL) - making all phases safely re-runnable to enable automatic crash recovery.

## Objective
Make all 10 ADW phases idempotent (safely re-runnable): check if already completed, skip if valid outputs exist, re-execute if outputs corrupted. Enables automatic recovery from crashes.

## Background Information
- **Files:** All 10 phase scripts in `adws/`
- **Current Problem:** Re-running a phase after crash causes duplicates or errors
- **Target Solution:** Phases check existing state, skip if complete, resume if partial
- **Risk Level:** Medium-High (changes core phase logic, extensive testing needed)
- **Estimated Time:** 12 hours
- **Prerequisites:** Issues #1 (contracts), #2 (SSoT), #3 (validation) complete

## Current Problem

Phases are NOT idempotent:
```python
def plan_phase(issue_number):
    # Always creates new plan, even if one exists
    worktree = create_worktree()  # ❌ Fails if already exists
    plan = generate_plan()
    save_plan(plan)
    return True
```

**If phase crashes and restarts:**
- Tries to create worktree again → error
- Generates new plan → overwrites partial work
- Inconsistent state

## Target Solution

Phases are idempotent:
```python
def plan_phase(issue_number):
    # Check if already completed
    if is_plan_complete(issue_number):
        logger.info("Plan already complete, skipping")
        return True

    # Check if partially complete
    if worktree_exists():
        logger.info("Resuming from existing worktree")
        worktree = get_existing_worktree()
    else:
        worktree = create_worktree()

    # Generate plan if not exists or corrupted
    if not plan_exists() or not is_plan_valid():
        plan = generate_plan()
        save_plan(plan)

    # Validate completion
    if not is_plan_complete(issue_number):
        raise ValueError("Plan incomplete after execution")

    return True
```

**Benefits:**
- ✅ Can re-run after crash → automatic recovery
- ✅ Skip work if already done → faster retries
- ✅ Deterministic → same input = same output
- ✅ No duplicate side effects

## Step-by-Step Instructions

### Step 1: Define Idempotency Contract

Create `docs/adw/idempotency.md`:

```markdown
# ADW Phase Idempotency

## Definition

A phase is **idempotent** if running it multiple times with the same inputs produces the same result and has the same side effects as running it once.

## Requirements

All ADW phases must be idempotent to enable:
- Automatic crash recovery
- Safe retries after failures
- Resumption from partial completion

## Idempotency Pattern

```python
def idempotent_phase(issue_number):
    """Template for idempotent phase implementation."""

    # 1. Check if already complete
    if is_complete(issue_number):
        logger.info("Phase already complete, skipping")
        return True

    # 2. Resume from partial state (if applicable)
    if has_partial_outputs():
        logger.info("Resuming from partial completion")
        cleanup_partial_outputs()  # Or resume if resumable

    # 3. Execute phase
    execute()

    # 4. Validate completion
    if not is_complete(issue_number):
        raise ValueError("Phase incomplete after execution")

    return True

def is_complete(issue_number):
    """Check if phase outputs exist and are valid."""
    # Use StateValidator from Part 3
    validator = StateValidator(phase=self.phase_name)
    result = validator.validate_outputs(issue_number)
    return result.is_valid
```

## Phase-Specific Patterns

### Plan Phase
- **Check:** SDLC_PLAN.md exists and valid
- **Resume:** If worktree exists but plan missing → regenerate plan
- **Skip:** If plan exists and valid → skip

### Build Phase
- **Check:** Code changes committed to worktree branch
- **Resume:** If partial changes → reset to clean state, rebuild
- **Skip:** If all changes applied and committed → skip

### Test Phase
- **Check:** Tests passed (recorded in database or test report)
- **Resume:** Always re-run tests (fast, deterministic)
- **Skip:** If tests passed and code unchanged → skip

### Ship Phase
- **Check:** PR created (URL in database)
- **Resume:** If PR draft → update, if no PR → create
- **Skip:** If PR exists and ready → skip

[... continue for all phases ...]
```

### Step 2: Implement Idempotent Plan Phase

Update `adws/adw_planning.py`:

```python
from utils.state_validator import StateValidator
from pathlib import Path
import json

def plan_phase_idempotent(issue_number: int):
    """Idempotent plan phase - safely re-runnable."""

    logger.info(f"Starting plan phase for issue {issue_number}")

    # 1. Check if already complete
    if is_plan_complete(issue_number):
        logger.info("✓ Plan phase already complete, skipping")
        return True

    # 2. Get or create worktree
    worktree_path = get_or_create_worktree(issue_number)

    # 3. Generate plan if missing or invalid
    plan_path = Path(worktree_path) / 'SDLC_PLAN.md'
    if plan_path.exists() and is_plan_valid(plan_path):
        logger.info(f"✓ Existing plan is valid: {plan_path}")
    else:
        if plan_path.exists():
            logger.warning(f"Existing plan invalid, regenerating: {plan_path}")
        else:
            logger.info(f"No plan found, generating: {plan_path}")

        generate_plan(issue_number, worktree_path)

    # 4. Ensure database state is correct
    ensure_database_state(issue_number, status='planned', current_phase='plan')

    # 5. Validate completion
    if not is_plan_complete(issue_number):
        raise ValueError("Plan phase incomplete after execution")

    logger.info("✓ Plan phase complete")
    return True

def is_plan_complete(issue_number: int) -> bool:
    """Check if plan phase is complete and valid."""
    try:
        validator = StateValidator(phase='plan')
        result = validator.validate_outputs(issue_number)
        return result.is_valid
    except Exception as e:
        logger.debug(f"Plan validation failed: {e}")
        return False

def is_plan_valid(plan_path: Path) -> bool:
    """Check if SDLC_PLAN.md is valid."""
    if not plan_path.exists():
        return False

    # Check file size
    if plan_path.stat().st_size < 100:
        logger.warning("Plan file too small")
        return False

    # Check for required sections
    content = plan_path.read_text()
    required_sections = ['## Objective', '## Implementation', '## Testing']
    for section in required_sections:
        if section not in content:
            logger.warning(f"Plan missing section: {section}")
            return False

    return True

def get_or_create_worktree(issue_number: int) -> str:
    """Get existing worktree or create new one."""
    from app.server.repositories.phase_queue_repository import PhaseQueueRepository

    repo = PhaseQueueRepository()
    workflow = repo.find_by_issue_number(issue_number)

    if workflow:
        # Check if worktree already exists
        worktree_path = f"trees/adw-{workflow.queue_id}"
        if Path(worktree_path).exists():
            logger.info(f"Using existing worktree: {worktree_path}")
            return worktree_path

    # Create new worktree
    logger.info(f"Creating new worktree for issue {issue_number}")
    return create_worktree(issue_number)

def ensure_database_state(issue_number: int, status: str, current_phase: str):
    """Ensure database has correct state."""
    from app.server.repositories.phase_queue_repository import PhaseQueueRepository

    repo = PhaseQueueRepository()
    workflow = repo.find_by_issue_number(issue_number)

    if not workflow:
        logger.error(f"Workflow not found for issue {issue_number}")
        raise ValueError(f"Workflow not found for issue {issue_number}")

    # Update if incorrect
    if workflow.status != status or workflow.current_phase != current_phase:
        logger.info(f"Updating database state: status={status}, current_phase={current_phase}")
        repo.update_phase(
            issue_number=issue_number,
            status=status,
            current_phase=current_phase
        )
```

### Step 3: Implement Idempotent Test Phase

Update `adws/adw_test_iso.py`:

```python
from utils.state_validator import StateValidator

def test_phase_idempotent(issue_number: int):
    """Idempotent test phase - safely re-runnable."""

    logger.info(f"Starting test phase for issue {issue_number}")

    # 1. Check if already complete
    if is_test_complete(issue_number):
        logger.info("✓ Test phase already complete, skipping")
        return True

    # 2. Get worktree
    worktree_path = get_worktree_path(issue_number)
    if not worktree_path or not Path(worktree_path).exists():
        raise ValueError(f"Worktree not found for issue {issue_number}")

    # 3. Run tests (always re-run - tests are fast and deterministic)
    logger.info(f"Running tests in {worktree_path}")
    test_result = run_tests(worktree_path)

    # 4. Record results
    record_test_results(issue_number, test_result)

    # 5. Update database
    status = 'tested' if test_result['passed'] else 'failed'
    ensure_database_state(issue_number, status=status, current_phase='test')

    # 6. Validate completion
    if not is_test_complete(issue_number):
        raise ValueError("Test phase incomplete after execution")

    logger.info(f"✓ Test phase complete: {'PASSED' if test_result['passed'] else 'FAILED'}")
    return test_result['passed']

def is_test_complete(issue_number: int) -> bool:
    """Check if test phase is complete and passed."""
    try:
        validator = StateValidator(phase='test')
        result = validator.validate_outputs(issue_number)
        if not result.is_valid:
            return False

        # Check test results
        test_results = get_test_results(issue_number)
        return test_results and test_results.get('passed', False)
    except Exception as e:
        logger.debug(f"Test validation failed: {e}")
        return False

def get_test_results(issue_number: int) -> dict:
    """Get recorded test results."""
    # Implementation depends on how results are stored
    # Could be in database, file, or both
    pass

def record_test_results(issue_number: int, test_result: dict):
    """Record test results for idempotency checking."""
    # Store in database or file for future idempotency checks
    pass
```

### Step 4: Implement Idempotent Ship Phase

Update `adws/adw_ship.py`:

```python
from utils.state_validator import StateValidator

def ship_phase_idempotent(issue_number: int):
    """Idempotent ship phase - safely re-runnable."""

    logger.info(f"Starting ship phase for issue {issue_number}")

    # 1. Check if already complete
    if is_ship_complete(issue_number):
        logger.info("✓ Ship phase already complete, skipping")
        return True

    # 2. Check if PR already exists
    existing_pr = get_existing_pr(issue_number)
    if existing_pr:
        logger.info(f"PR already exists: {existing_pr['url']}")
        # Validate PR is ready
        if is_pr_ready(existing_pr):
            logger.info("✓ Existing PR is ready")
            return True
        else:
            logger.info("Updating existing PR")
            update_pr(existing_pr, issue_number)
    else:
        logger.info("Creating new PR")
        create_pr(issue_number)

    # 3. Ensure database state
    ensure_database_state(issue_number, status='shipped', current_phase='ship')

    # 4. Validate completion
    if not is_ship_complete(issue_number):
        raise ValueError("Ship phase incomplete after execution")

    logger.info("✓ Ship phase complete")
    return True

def is_ship_complete(issue_number: int) -> bool:
    """Check if ship phase is complete."""
    try:
        validator = StateValidator(phase='ship')
        result = validator.validate_outputs(issue_number)
        if not result.is_valid:
            return False

        # Check PR exists
        pr = get_existing_pr(issue_number)
        return pr is not None and is_pr_ready(pr)
    except Exception as e:
        logger.debug(f"Ship validation failed: {e}")
        return False

def get_existing_pr(issue_number: int):
    """Get existing PR for issue if exists."""
    import subprocess

    result = subprocess.run(
        ['gh', 'pr', 'list', '--search', f'issue:{issue_number}', '--json', 'url,number,title,state'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0 and result.stdout.strip():
        prs = json.loads(result.stdout)
        if prs:
            return prs[0]  # Return first matching PR

    return None

def is_pr_ready(pr: dict) -> bool:
    """Check if PR is ready (not draft, has description, etc.)."""
    # Implementation depends on PR requirements
    return pr.get('state') == 'OPEN'
```

### Step 5: Update Remaining Phases

Repeat idempotency pattern for:
- ✅ Plan (done in Step 2)
- Validate
- Build
- Lint
- ✅ Test (done in Step 3)
- Review
- Document
- ✅ Ship (done in Step 4)
- Cleanup
- Verify

Each phase should:
1. Check if complete → skip if yes
2. Check partial state → resume or cleanup
3. Execute phase logic
4. Validate completion
5. Update database state

### Step 6: Add Idempotency Tests

Create `app/server/tests/adws/test_idempotency.py`:

```python
"""Tests for ADW phase idempotency."""

import pytest
from adws.adw_planning import plan_phase_idempotent, is_plan_complete
from adws.adw_test_iso import test_phase_idempotent, is_test_complete

def test_plan_phase_idempotent(mock_db, mock_worktree):
    """Plan phase should be idempotent."""
    issue_number = 123

    # First run - should create plan
    result1 = plan_phase_idempotent(issue_number)
    assert result1 is True
    assert is_plan_complete(issue_number)

    # Second run - should skip (already complete)
    result2 = plan_phase_idempotent(issue_number)
    assert result2 is True
    assert is_plan_complete(issue_number)

    # Should have created plan exactly once
    # (verify no duplicates or overwrites)

def test_plan_phase_resume_from_partial(mock_db, mock_worktree):
    """Plan phase should resume from partial state."""
    issue_number = 123

    # Create worktree but no plan
    create_worktree_without_plan(issue_number)

    # Run plan phase - should generate plan in existing worktree
    result = plan_phase_idempotent(issue_number)
    assert result is True
    assert is_plan_complete(issue_number)

    # Worktree should not be recreated
    assert worktree_was_not_recreated()

def test_test_phase_idempotent(mock_db, mock_worktree):
    """Test phase should be idempotent."""
    issue_number = 123

    # Setup: plan and build phases complete
    setup_phases_up_to_test(issue_number)

    # First run - should run tests
    result1 = test_phase_idempotent(issue_number)
    assert result1 is True
    assert is_test_complete(issue_number)

    # Second run - should skip (already complete)
    result2 = test_phase_idempotent(issue_number)
    assert result2 is True
    assert is_test_complete(issue_number)

# Add more idempotency tests for each phase...
```

### Step 7: Update Orchestrator for Idempotency

Update `adws/adw_sdlc_complete_iso.py`:

```python
def run_sdlc_with_idempotency(issue_number: int):
    """Run SDLC workflow with idempotent phases."""

    phases = [
        'plan', 'validate', 'build', 'lint', 'test',
        'review', 'document', 'ship', 'cleanup', 'verify'
    ]

    for phase_name in phases:
        logger.info(f"\n{'='*60}")
        logger.info(f"Phase: {phase_name}")
        logger.info(f"{'='*60}")

        try:
            # Each phase is idempotent - safe to retry
            success = run_phase_idempotent(phase_name, issue_number)

            if not success:
                logger.error(f"Phase {phase_name} failed")
                return False

            logger.info(f"✓ Phase {phase_name} complete")

        except Exception as e:
            logger.error(f"Phase {phase_name} crashed: {e}")
            logger.info(f"Retrying {phase_name} (idempotent)...")

            # Retry is safe because phases are idempotent
            try:
                success = run_phase_idempotent(phase_name, issue_number)
                if success:
                    logger.info(f"✓ Phase {phase_name} recovered")
                else:
                    logger.error(f"Phase {phase_name} failed after retry")
                    return False
            except Exception as retry_error:
                logger.error(f"Phase {phase_name} failed after retry: {retry_error}")
                return False

    logger.info("\n✓ SDLC workflow complete")
    return True
```

### Step 8: Test Idempotency End-to-End

```bash
cd adws/

# Test 1: Run workflow twice, should skip on second run
python3 adw_sdlc_complete_iso.py 123
python3 adw_sdlc_complete_iso.py 123  # Should skip all phases

# Test 2: Simulate crash and recovery
python3 << 'EOF'
# Start workflow
import subprocess
import time
import signal

proc = subprocess.Popen(['python3', 'adw_sdlc_complete_iso.py', '124'])
time.sleep(30)  # Let it run for 30 seconds
proc.send_signal(signal.SIGTERM)  # Simulate crash

# Resume workflow
subprocess.run(['python3', 'adw_sdlc_complete_iso.py', '124'])
# Should resume from where it left off
EOF

# Test 3: Run idempotency tests
cd app/server
uv run pytest tests/adws/test_idempotency.py -v
```

### Step 9: Document Idempotency

Update `docs/adw/idempotency.md` with implementation details and examples.

### Step 10: Commit Changes

```bash
git add adws/*.py  # All updated phase scripts
git add adws/adw_sdlc_complete_iso.py
git add app/server/tests/adws/test_idempotency.py
git add docs/adw/idempotency.md
git commit -m "feat: Implement idempotent ADW phases

Part 4 of 4 for Session 19 Phase 2 (State Management Clarity) - FINAL

Made all 10 ADW phases idempotent (safely re-runnable):
- Check if already complete → skip if yes
- Resume from partial state → cleanup or continue
- Execute phase logic
- Validate completion
- Update state

Benefits:
- ✅ Automatic crash recovery
- ✅ Safe retries after failures
- ✅ Skip completed work (faster)
- ✅ Deterministic execution

Changes:
1. Implemented idempotency for all 10 phases
2. Added completion checks using StateValidator (Part 3)
3. Updated orchestrator to retry on crash
4. Added idempotency tests
5. Documented idempotency patterns

Files Modified:
- All 10 phase scripts (idempotent implementation)
- adws/adw_sdlc_complete_iso.py (retry logic)

Files Added:
- app/server/tests/adws/test_idempotency.py
- docs/adw/idempotency.md

Session 19 Phase 2 COMPLETE:
✅ Part 1: Phase contracts documented
✅ Part 2: Single Source of Truth defined
✅ Part 3: State validation middleware
✅ Part 4: Idempotent phases

Next: Session 19 Phase 3 (if any)"
```

## Success Criteria

- ✅ All 10 phases are idempotent (safely re-runnable)
- ✅ Phases skip if already complete (validated)
- ✅ Phases resume from partial state when possible
- ✅ Orchestrator retries on crash (automatic recovery)
- ✅ Idempotency tests pass
- ✅ Documentation complete
- ✅ End-to-end testing confirms recovery works

## Files Expected to Change

**Modified:**
- All 10 phase scripts in `adws/` (idempotent implementation, ~100-200 lines each)
- `adws/adw_sdlc_complete_iso.py` (retry logic)

**Created:**
- `app/server/tests/adws/test_idempotency.py` (~300-500 lines)
- `docs/adw/idempotency.md` (~3-5 KB)

## Deliverables for Summary

When complete, return to coordination chat with:
```
**Issue #4 Complete: Implement Idempotent Phases (FINAL)**

**All 10 Phases Now Idempotent:**
- Plan, Validate, Build, Lint, Test, Review, Document, Ship, Cleanup, Verify

**Idempotency Features:**
- Completion checks using StateValidator (Part 3)
- Partial state resumption where applicable
- Automatic retry on crash
- Skip completed work

**Testing:**
- [N] idempotency tests created
- End-to-end crash recovery tested
- All tests passing

**Time Spent:** [actual hours]

**Key Insights:**
- [Phases that were hardest to make idempotent]
- [Recovery scenarios tested]
- [Performance improvement from skipping completed work]

**Session 19 Phase 2 COMPLETE:**
✅ Part 1: Phase contracts (4 hours)
✅ Part 2: Single Source of Truth (6 hours)
✅ Part 3: State validation (5 hours)
✅ Part 4: Idempotent phases (12 hours)

Total: 27 hours

**Next Steps:** [What's next in Session 19 or move to Phase 3]
```

## Troubleshooting

**If phase difficult to make idempotent:**
- Identify external side effects (API calls, DB writes)
- Make side effects idempotent first (e.g., upsert instead of insert)
- Use completion checks to skip redundant work

**If partial state unclear:**
- Document what "partial" means for each phase
- Prefer cleanup over resume if complex
- Use validation to detect corruption

**If tests flaky:**
- Ensure test environment is clean between runs
- Mock external dependencies
- Test both "already complete" and "partial state" scenarios

---

**Ready to copy into Issue #4!**
