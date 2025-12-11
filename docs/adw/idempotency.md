# ADW Phase Idempotency

**Part 4 of 4 - Session 19 Phase 2: State Management Clarity**

## Definition

A phase is **idempotent** if running it multiple times with the same inputs produces the same result and has the same side effects as running it once.

**Mathematically**: `f(f(x)) = f(x)` for all inputs x

## Why Idempotency Matters

Idempotency enables:

1. **Automatic Crash Recovery** - Restart a workflow after system crash without manual cleanup
2. **Safe Retries** - Retry failed operations without worrying about duplicates
3. **Deterministic Execution** - Same inputs always produce same outputs
4. **Partial Completion Handling** - Resume from where a phase left off
5. **Developer Confidence** - Re-run phases during debugging without side effects

## Requirements

All 10 ADW phases must be idempotent to enable automatic recovery. Each phase must:

1. **Check completion** before starting (using StateValidator from Part 3)
2. **Skip work** if already complete with valid outputs
3. **Handle partial state** gracefully (resume or cleanup)
4. **Validate outputs** after execution
5. **Update state atomically** (Single Source of Truth from Part 2)

## Idempotency Pattern

This is the canonical pattern all phases must follow:

```python
from utils.state_validator import StateValidator
from adw_modules.state import ADWState
import logging

def idempotent_phase(issue_number: int, adw_id: str, logger: logging.Logger):
    """Template for idempotent phase implementation."""

    # 1. Check if already complete
    if is_complete(issue_number, logger):
        logger.info(f"✓ Phase already complete, skipping")
        return True

    # 2. Resume from partial state (if applicable)
    if has_partial_outputs(issue_number, adw_id):
        logger.info("Resuming from partial completion")
        cleanup_partial_outputs(issue_number, adw_id)  # Or resume if resumable

    # 3. Execute phase logic
    try:
        execute_phase_logic(issue_number, adw_id, logger)
    except Exception as e:
        logger.error(f"Phase execution failed: {e}")
        raise

    # 4. Validate completion
    if not is_complete(issue_number, logger):
        raise ValueError("Phase incomplete after execution")

    logger.info("✓ Phase complete")
    return True

def is_complete(issue_number: int, logger: logging.Logger) -> bool:
    """Check if phase outputs exist and are valid."""
    try:
        # Use StateValidator from Part 3
        validator = StateValidator(phase='phase_name')
        result = validator.validate_outputs(issue_number)

        if not result.is_valid:
            logger.debug(f"Phase incomplete: {result.errors}")
            return False

        logger.debug("Phase outputs valid")
        return True

    except Exception as e:
        logger.debug(f"Validation failed: {e}")
        return False
```

## Phase-Specific Idempotency Patterns

### 1. Plan Phase

**Completion Check**: SDLC_PLAN.md exists and valid

**Partial State**: Worktree exists but plan missing

**Idempotency Strategy**:
- If plan exists and valid → **skip** (fastest path)
- If worktree exists but plan missing/invalid → **regenerate plan** in existing worktree
- If neither exist → **create both**

**Critical Files**:
- `SDLC_PLAN.md` or `specs/issue-{N}.md`
- `adw_state.json`
- Worktree branch

**Example**:
```python
def is_plan_complete(issue_number: int, logger) -> bool:
    validator = StateValidator(phase='plan')
    result = validator.validate_outputs(issue_number)

    if not result.is_valid:
        return False

    # Additional check: plan file size and content
    state = ADWState.load_by_issue(issue_number)
    plan_file = state.get('plan_file')

    if not plan_file or not Path(plan_file).exists():
        return False

    if Path(plan_file).stat().st_size < 100:
        logger.warning(f"Plan file suspiciously small: {plan_file}")
        return False

    content = Path(plan_file).read_text()
    required_sections = ['## Objective', '## Implementation', '## Testing']

    for section in required_sections:
        if section not in content:
            logger.warning(f"Plan missing section: {section}")
            return False

    return True
```

### 2. Validate Phase

**Completion Check**: Baseline errors recorded

**Partial State**: Worktree exists but no baseline

**Idempotency Strategy**:
- If baseline exists → **skip**
- If worktree exists but no baseline → **run validation**, record baseline
- Validation is fast, so re-running is acceptable

**Critical Outputs**:
- `baseline_errors` in state
- Validation report

### 3. Build Phase

**Completion Check**: Code changes committed, build results recorded

**Partial State**: Uncommitted changes in worktree

**Idempotency Strategy**:
- If changes committed and build passed → **skip**
- If changes exist but uncommitted → **cleanup**, re-build (safer than resume)
- If no changes → **execute build**

**Critical Outputs**:
- Git commits in worktree branch
- `external_build_results` in state
- Modified files list

**Note**: Build phase is NOT resumable - always start from clean state

### 4. Lint Phase

**Completion Check**: Lint passed and recorded

**Partial State**: N/A (lint is stateless)

**Idempotency Strategy**:
- If lint already passed → **skip** (if code unchanged)
- Otherwise → **re-run lint** (fast and deterministic)

**Critical Outputs**:
- `external_lint_results` in state
- Lint report

**Note**: Lint is fast (~30s), so re-running is acceptable even if previously passed

### 5. Test Phase

**Completion Check**: Tests passed and recorded

**Partial State**: N/A (tests are stateless)

**Idempotency Strategy**:
- If tests passed and code unchanged → **skip**
- Otherwise → **re-run tests** (deterministic)
- Test failures are valid completion states

**Critical Outputs**:
- `external_test_results` in state
- Test report
- Coverage data (if applicable)

**Note**: Tests can take longer, but must be re-run if code changes

### 6. Review Phase

**Completion Check**: Review comments posted, review status recorded

**Partial State**: Partial review comments

**Idempotency Strategy**:
- If review complete and posted → **skip**
- If partial review → **continue from last comment** (resumable)
- If no review → **start fresh**

**Critical Outputs**:
- Review comments on GitHub issue
- `review_status` in state
- Review summary

### 7. Document Phase

**Completion Check**: Documentation files created in `app_docs/`

**Partial State**: Some docs created but incomplete

**Idempotency Strategy**:
- If all docs exist and valid → **skip**
- If partial docs → **cleanup**, regenerate (safer than resume)
- If no docs → **generate**

**Critical Outputs**:
- Documentation files in `app_docs/`
- Documentation summary in state

### 8. Ship Phase

**Completion Check**: Pull request created and ready

**Partial State**: Draft PR exists

**Idempotency Strategy**:
- If PR exists and ready → **skip**
- If PR exists but draft/incomplete → **update PR**
- If no PR → **create PR**

**Critical Outputs**:
- GitHub Pull Request (URL recorded in state)
- `ship_timestamp` in state

**Note**: PR creation is naturally idempotent - GitHub prevents duplicate PRs

**Example**:
```python
def is_ship_complete(issue_number: int, logger) -> bool:
    validator = StateValidator(phase='ship')
    result = validator.validate_outputs(issue_number)

    if not result.is_valid:
        return False

    # Check if PR exists and is ready
    pr = get_existing_pr(issue_number)
    return pr is not None and pr['state'] == 'OPEN'

def get_existing_pr(issue_number: int):
    """Get existing PR for issue if exists."""
    import subprocess
    import json

    result = subprocess.run(
        ['gh', 'pr', 'list', '--search', f'issue:{issue_number}',
         '--json', 'url,number,title,state,isDraft'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0 and result.stdout.strip():
        prs = json.loads(result.stdout)
        if prs:
            return prs[0]  # Return first matching PR

    return None
```

### 9. Cleanup Phase

**Completion Check**: Worktree removed

**Partial State**: Partial cleanup (some files removed)

**Idempotency Strategy**:
- If worktree already removed → **skip**
- If worktree exists → **remove** (idempotent operation)

**Critical Outputs**:
- Worktree removed from filesystem
- Cleanup completion recorded

**Note**: Cleanup is best-effort and naturally idempotent

### 10. Verify Phase

**Completion Check**: Verification tests passed

**Partial State**: N/A (verification is stateless)

**Idempotency Strategy**:
- If verification already passed → **skip**
- Otherwise → **re-run verification** (smoke tests are fast)

**Critical Outputs**:
- `verification_results` in state
- Verification report

## Implementation Checklist

For each phase, ensure:

- [ ] Completion check implemented using StateValidator
- [ ] Partial state detection and handling
- [ ] Execute logic only if not complete
- [ ] Output validation after execution
- [ ] State updates are atomic (Single Source of Truth)
- [ ] Logging at each decision point
- [ ] Error handling and cleanup
- [ ] Tests for idempotency (run twice, verify same result)

## Testing Idempotency

### Unit Tests

```python
def test_phase_idempotent(mock_db, mock_worktree):
    """Phase should be idempotent - running twice produces same result."""
    issue_number = 123

    # First run - should execute
    result1 = phase_function(issue_number)
    assert result1 is True
    assert is_complete(issue_number)

    # Capture state after first run
    state1 = capture_phase_state(issue_number)

    # Second run - should skip (already complete)
    result2 = phase_function(issue_number)
    assert result2 is True
    assert is_complete(issue_number)

    # State should be identical
    state2 = capture_phase_state(issue_number)
    assert state1 == state2

    # No duplicate side effects (check GitHub API calls, commits, etc.)
    assert_no_duplicate_side_effects()
```

### Integration Tests

```python
def test_crash_recovery(mock_db, mock_worktree):
    """Workflow should recover from crash mid-phase."""
    issue_number = 124

    # Start workflow
    workflow = start_workflow(issue_number)

    # Let it run for 30 seconds, then kill
    time.sleep(30)
    workflow.terminate()

    # Capture partial state
    partial_state = capture_workflow_state(issue_number)

    # Resume workflow
    workflow_resumed = start_workflow(issue_number)
    workflow_resumed.wait()

    # Should complete successfully
    assert workflow_resumed.returncode == 0

    # Final state should be valid
    assert is_workflow_complete(issue_number)
```

## Common Pitfalls

### ❌ Anti-Pattern: Assuming Clean State

```python
# BAD - Assumes no prior state
def plan_phase(issue_number):
    worktree = create_worktree()  # Fails if exists!
    plan = generate_plan()
    save_plan(plan)
```

### ✅ Good Pattern: Check and Resume

```python
# GOOD - Checks existing state
def plan_phase(issue_number):
    if is_complete(issue_number):
        return True

    worktree = get_or_create_worktree(issue_number)

    if plan_exists_and_valid():
        return True

    plan = generate_plan()
    save_plan(plan)
    return is_complete(issue_number)
```

### ❌ Anti-Pattern: Partial Completion Not Validated

```python
# BAD - Doesn't validate completion
def test_phase(issue_number):
    run_tests()
    return True  # Assumed success
```

### ✅ Good Pattern: Validate Completion

```python
# GOOD - Validates outputs
def test_phase(issue_number):
    if is_complete(issue_number):
        return True

    run_tests()

    if not is_complete(issue_number):
        raise ValueError("Tests incomplete")

    return True
```

### ❌ Anti-Pattern: Side Effects Without Idempotency

```python
# BAD - Creates duplicate GitHub comments
def ship_phase(issue_number):
    create_pr()
    post_comment("PR created!")  # Posts duplicate comment on retry!
```

### ✅ Good Pattern: Idempotent Side Effects

```python
# GOOD - Checks before creating side effects
def ship_phase(issue_number):
    if is_complete(issue_number):
        return True

    pr = get_existing_pr(issue_number)
    if not pr:
        pr = create_pr()
        post_comment(f"PR created: {pr['url']}")

    return True
```

## Observability

Log at each decision point for debugging:

```python
def idempotent_phase(issue_number):
    logger.info(f"Starting phase for issue {issue_number}")

    # Log completion check
    if is_complete(issue_number):
        logger.info("✓ Phase already complete, skipping")
        return True

    # Log partial state detection
    if has_partial_state():
        logger.info("⚠ Partial state detected, cleaning up")
        cleanup_partial_state()

    # Log execution
    logger.info("Executing phase logic")
    execute()

    # Log validation
    if not is_complete(issue_number):
        logger.error("✗ Phase incomplete after execution")
        raise ValueError("Phase incomplete")

    logger.info("✓ Phase complete")
    return True
```

## Benefits Summary

With idempotent phases, the ADW system gains:

1. **🔄 Automatic Recovery** - System can restart after crash without manual intervention
2. **⚡ Faster Retries** - Skip completed work, only re-execute what's needed
3. **🎯 Deterministic** - Same input always produces same output
4. **🛡️ Safer** - No duplicate side effects (GitHub comments, PRs, commits)
5. **🔍 Debuggable** - Can re-run phases during investigation without corruption
6. **🚀 Scalable** - Enables parallel execution of independent phases
7. **💪 Robust** - Handles partial failures gracefully

## See Also

- **Part 1**: [Phase Contracts](phase-contracts.md) - Input/output contracts for each phase
- **Part 2**: [State Management SSoT](state-management-ssot.md) - Single source of truth for state
- **Part 3**: [State Validation](state-validation.md) - Validation middleware using StateValidator

## Implementation Timeline

- **Part 1**: Phase contracts (4 hours) - ✅ Complete
- **Part 2**: Single Source of Truth (6 hours) - ✅ Complete
- **Part 3**: State validation (5 hours) - ✅ Complete
- **Part 4**: Idempotent phases (12 hours) - 🔄 In Progress

**Total**: 27 hours for complete state management clarity
