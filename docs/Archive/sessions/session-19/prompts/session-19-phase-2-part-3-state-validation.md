# Task: Add State Validation Middleware for ADW Phases

## Context
I'm working on the tac-webbuilder project. Phase 2 of Session 19 addresses dual-state management issues. This is Part 3 of 4 - adding validation middleware to fail fast when phase inputs are invalid.

## Objective
Create a StateValidator class that validates phase inputs BEFORE execution (fail fast) and outputs AFTER execution (ensure completeness), using the phase contracts from Issue #1 and SSoT rules from Issue #2.

## Background Information
- **Files:** Create `adws/utils/state_validator.py`, update all phase scripts
- **Current Problem:** Phases fail mid-execution when inputs invalid, wasting time and creating inconsistent state
- **Target Solution:** Validate inputs before phase starts, validate outputs before marking complete
- **Risk Level:** Low-Medium (new code, doesn't change existing logic)
- **Estimated Time:** 5 hours
- **Prerequisites:** Issues #1 (contracts) and #2 (SSoT) complete

## Current Problem

Phases fail mid-execution:
```python
# Phase starts executing
def run_test_phase(issue_number):
    # ... expensive setup (30 seconds) ...

    # FAILURE: Test files don't exist (should have been validated up front!)
    test_files = glob.glob('tests/**/*.py')
    if not test_files:
        raise ValueError("No test files found")  # ❌ Too late!
```

**Problems:**
1. Waste time on setup before discovering invalid input
2. Partial state changes (some files created, then fail)
3. Unclear error messages (generic exceptions)
4. No consistent validation across phases

## Target Solution

Validate BEFORE execution:
```python
# Phase validates first
def run_test_phase(issue_number):
    # Validate inputs (< 1 second)
    validator = StateValidator(phase='test')
    validation = validator.validate_inputs(issue_number)
    if not validation.is_valid:
        raise ValueError(f"Invalid inputs: {validation.errors}")  # ✅ Fail fast!

    # Now safe to execute (inputs guaranteed valid)
    # ... test execution ...

    # Validate outputs before returning
    validation = validator.validate_outputs(issue_number)
    if not validation.is_valid:
        raise ValueError(f"Incomplete outputs: {validation.errors}")
```

## Step-by-Step Instructions

### Step 1: Create StateValidator Class

Create `adws/utils/state_validator.py`:

```python
"""
State validation middleware for ADW phases.

Validates phase inputs BEFORE execution (fail fast) and outputs AFTER
execution (ensure completeness) using contracts from docs/adw/phase-contracts.md
and SSoT rules from docs/adw/state-management-ssot.md.

Usage:
    validator = StateValidator(phase='test')

    # Before phase execution
    result = validator.validate_inputs(issue_number)
    if not result.is_valid:
        raise ValueError(f"Invalid inputs: {result.errors}")

    # After phase execution
    result = validator.validate_outputs(issue_number)
    if not result.is_valid:
        raise ValueError(f"Incomplete outputs: {result.errors}")
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import json

@dataclass
class ValidationResult:
    """Result of state validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]

    def __bool__(self):
        return self.is_valid

class StateValidator:
    """Validates ADW phase inputs and outputs."""

    # Phase contracts (from docs/adw/phase-contracts.md)
    PHASE_CONTRACTS = {
        'plan': {
            'requires': ['github_issue', 'github_token', 'database_connection'],
            'produces': ['SDLC_PLAN.md', 'adw_state.json', 'phase_queue_record']
        },
        'validate': {
            'requires': ['SDLC_PLAN.md', 'adw_state.json', 'phase_queue_record'],
            'produces': ['validated_plan', 'feasibility_check']
        },
        'build': {
            'requires': ['SDLC_PLAN.md', 'worktree', 'adw_state.json'],
            'produces': ['code_changes', 'modified_files']
        },
        'lint': {
            'requires': ['source_files', 'worktree'],
            'produces': ['lint_pass_or_fail', 'lint_report']
        },
        'test': {
            'requires': ['source_files', 'test_files', 'worktree'],
            'produces': ['test_pass_or_fail', 'test_report']
        },
        'review': {
            'requires': ['code_changes', 'worktree'],
            'produces': ['review_comments', 'review_status']
        },
        'document': {
            'requires': ['code_changes', 'worktree'],
            'produces': ['updated_docs', 'documentation_changes']
        },
        'ship': {
            'requires': ['all_phases_passed', 'worktree', 'clean_tests'],
            'produces': ['pull_request', 'pr_url']
        },
        'cleanup': {
            'requires': ['pr_created_or_closed', 'worktree_path'],
            'produces': ['worktree_removed', 'cleanup_complete']
        },
        'verify': {
            'requires': ['pr_merged', 'issue_number'],
            'produces': ['verification_report', 'verification_status']
        }
    }

    def __init__(self, phase: str):
        """Initialize validator for specific phase.

        Args:
            phase: Phase name (plan, validate, build, etc.)
        """
        if phase not in self.PHASE_CONTRACTS:
            raise ValueError(f"Unknown phase: {phase}")
        self.phase = phase
        self.contract = self.PHASE_CONTRACTS[phase]

    def validate_inputs(self, issue_number: int) -> ValidationResult:
        """Validate phase inputs before execution.

        Args:
            issue_number: GitHub issue number

        Returns:
            ValidationResult with is_valid and any errors/warnings
        """
        errors = []
        warnings = []

        # Get workflow state from database (SSoT for coordination)
        from app.server.repositories.phase_queue_repository import PhaseQueueRepository
        repo = PhaseQueueRepository()
        workflow = repo.find_by_issue_number(issue_number)

        if not workflow:
            errors.append(f"Workflow not found for issue {issue_number}")
            return ValidationResult(False, errors, warnings)

        # Get execution metadata from file (SSoT for metadata)
        worktree_path = self._get_worktree_path(workflow.queue_id)
        if worktree_path:
            state_file = Path(worktree_path) / 'adw_state.json'
            if state_file.exists():
                with open(state_file) as f:
                    state = json.load(f)
            else:
                state = {}
        else:
            state = {}

        # Validate phase-specific requirements
        validation_method = getattr(self, f'_validate_{self.phase}_inputs', None)
        if validation_method:
            phase_errors = validation_method(workflow, state)
            errors.extend(phase_errors)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def validate_outputs(self, issue_number: int) -> ValidationResult:
        """Validate phase outputs after execution.

        Args:
            issue_number: GitHub issue number

        Returns:
            ValidationResult with is_valid and any errors/warnings
        """
        errors = []
        warnings = []

        # Get workflow state
        from app.server.repositories.phase_queue_repository import PhaseQueueRepository
        repo = PhaseQueueRepository()
        workflow = repo.find_by_issue_number(issue_number)

        if not workflow:
            errors.append(f"Workflow not found for issue {issue_number}")
            return ValidationResult(False, errors, warnings)

        # Get execution metadata
        worktree_path = self._get_worktree_path(workflow.queue_id)
        if worktree_path:
            state_file = Path(worktree_path) / 'adw_state.json'
            if state_file.exists():
                with open(state_file) as f:
                    state = json.load(f)
            else:
                state = {}
        else:
            state = {}

        # Validate phase-specific outputs
        validation_method = getattr(self, f'_validate_{self.phase}_outputs', None)
        if validation_method:
            phase_errors = validation_method(workflow, state, worktree_path)
            errors.extend(phase_errors)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    # Phase-specific input validators

    def _validate_plan_inputs(self, workflow, state) -> List[str]:
        """Validate plan phase inputs."""
        errors = []
        # GitHub issue must exist (checked by repository)
        # GitHub token must be valid (checked by GitHub API)
        # Database connection verified by workflow existence
        return errors

    def _validate_test_inputs(self, workflow, state) -> List[str]:
        """Validate test phase inputs."""
        errors = []

        # Must have worktree
        worktree_path = state.get('worktree_path')
        if not worktree_path:
            errors.append("No worktree_path in state")
            return errors

        worktree = Path(worktree_path)
        if not worktree.exists():
            errors.append(f"Worktree not found: {worktree_path}")

        # Must have test files
        test_files = list(worktree.glob('tests/**/*.py'))
        if not test_files:
            errors.append("No test files found in tests/ directory")

        return errors

    # Add more phase-specific validators...

    # Phase-specific output validators

    def _validate_plan_outputs(self, workflow, state, worktree_path) -> List[str]:
        """Validate plan phase outputs."""
        errors = []

        if not worktree_path:
            errors.append("Plan phase must set worktree_path")
            return errors

        # Must have SDLC_PLAN.md
        plan_path = Path(worktree_path) / 'SDLC_PLAN.md'
        if not plan_path.exists():
            errors.append("SDLC_PLAN.md not created")
        elif plan_path.stat().st_size < 100:
            errors.append("SDLC_PLAN.md is suspiciously small (< 100 bytes)")

        # Must have adw_state.json
        state_file = Path(worktree_path) / 'adw_state.json'
        if not state_file.exists():
            errors.append("adw_state.json not created")

        # Database must be updated
        if workflow.status != 'planned':
            errors.append(f"Workflow status should be 'planned', got '{workflow.status}'")
        if workflow.current_phase != 'plan':
            errors.append(f"Current phase should be 'plan', got '{workflow.current_phase}'")

        return errors

    def _validate_test_outputs(self, workflow, state, worktree_path) -> List[str]:
        """Validate test phase outputs."""
        errors = []

        # Must have test results recorded somewhere
        # (Implementation depends on how test results are stored)

        return errors

    # Add more phase-specific output validators...

    def _get_worktree_path(self, queue_id: int) -> Optional[str]:
        """Get worktree path for ADW."""
        # Calculate from queue_id (adw_id logic)
        adw_id = queue_id  # Simplified
        worktree_path = Path(f"trees/adw-{adw_id}")
        if worktree_path.exists():
            return str(worktree_path)
        return None
```

### Step 2: Add Unit Tests for Validator

Create `app/server/tests/utils/test_state_validator.py`:

```python
"""Tests for state validator."""

import pytest
from adws.utils.state_validator import StateValidator, ValidationResult

def test_validation_result_bool():
    """ValidationResult should be truthy when valid."""
    valid = ValidationResult(is_valid=True, errors=[], warnings=[])
    invalid = ValidationResult(is_valid=False, errors=['Error'], warnings=[])

    assert bool(valid) is True
    assert bool(invalid) is False

def test_unknown_phase():
    """Should raise error for unknown phase."""
    with pytest.raises(ValueError, match="Unknown phase"):
        StateValidator(phase='invalid_phase')

def test_plan_phase_validator():
    """Test plan phase validation."""
    validator = StateValidator(phase='plan')

    # TODO: Add mocked database and test validation
    # This is a placeholder - implement with proper mocks

def test_test_phase_inputs():
    """Test phase should validate test files exist."""
    validator = StateValidator(phase='test')

    # TODO: Add mocked state and test validation
```

### Step 3: Integrate Validators into Phase Scripts

Update each phase script to use validation:

**Example: `adws/adw_test_iso.py`**

```python
from utils.state_validator import StateValidator

def run_test_phase(issue_number: int):
    """Run test phase with validation."""

    # Validate inputs BEFORE execution
    validator = StateValidator(phase='test')
    input_validation = validator.validate_inputs(issue_number)

    if not input_validation.is_valid:
        logger.error(f"Test phase input validation failed: {input_validation.errors}")
        raise ValueError(f"Invalid inputs for test phase: {', '.join(input_validation.errors)}")

    if input_validation.warnings:
        for warning in input_validation.warnings:
            logger.warning(f"Test phase input warning: {warning}")

    logger.info("✓ Test phase inputs validated")

    # Execute phase
    try:
        # ... existing test execution logic ...
        pass
    except Exception as e:
        logger.error(f"Test phase execution failed: {e}")
        raise

    # Validate outputs AFTER execution
    output_validation = validator.validate_outputs(issue_number)

    if not output_validation.is_valid:
        logger.error(f"Test phase output validation failed: {output_validation.errors}")
        raise ValueError(f"Incomplete outputs from test phase: {', '.join(output_validation.errors)}")

    if output_validation.warnings:
        for warning in output_validation.warnings:
            logger.warning(f"Test phase output warning: {warning}")

    logger.info("✓ Test phase outputs validated")

    return True
```

**Repeat for all 10 phase scripts.**

### Step 4: Add Validation to Orchestrator

Update `adws/adw_sdlc_complete_iso.py` to use validation:

```python
from utils.state_validator import StateValidator

def run_phase(phase_name: str, issue_number: int):
    """Run a single phase with validation."""

    logger.info(f"Starting phase: {phase_name}")

    # Pre-execution validation
    validator = StateValidator(phase=phase_name)
    input_validation = validator.validate_inputs(issue_number)

    if not input_validation.is_valid:
        logger.error(f"{phase_name} inputs invalid: {input_validation.errors}")
        return False

    logger.info(f"✓ {phase_name} inputs validated")

    # Execute phase
    success = execute_phase(phase_name, issue_number)

    if not success:
        logger.error(f"{phase_name} execution failed")
        return False

    # Post-execution validation
    output_validation = validator.validate_outputs(issue_number)

    if not output_validation.is_valid:
        logger.error(f"{phase_name} outputs invalid: {output_validation.errors}")
        return False

    logger.info(f"✓ {phase_name} outputs validated")

    return True
```

### Step 5: Test Validation

```bash
cd adws/

# Test validation with mock data
python3 << 'EOF'
from utils.state_validator import StateValidator

# Test each phase validator
for phase in ['plan', 'validate', 'build', 'lint', 'test', 'review', 'document', 'ship', 'cleanup', 'verify']:
    validator = StateValidator(phase=phase)
    print(f"✓ {phase} validator created")

print("\n✓ All phase validators initialized successfully")
EOF

# Run unit tests
cd app/server
uv run pytest tests/utils/test_state_validator.py -v

# Test with actual workflow (if available)
cd adws/
# Run a test phase and verify validation occurs
```

### Step 6: Document Validation

Add validation documentation to `docs/adw/state-validation.md`:

```markdown
# ADW State Validation

## Overview

State validation middleware validates phase inputs BEFORE execution (fail fast) and outputs AFTER execution (ensure completeness).

## Usage

```python
from utils.state_validator import StateValidator

validator = StateValidator(phase='test')

# Before phase execution
result = validator.validate_inputs(issue_number)
if not result.is_valid:
    raise ValueError(f"Invalid inputs: {result.errors}")

# After phase execution
result = validator.validate_outputs(issue_number)
if not result.is_valid:
    raise ValueError(f"Incomplete outputs: {result.errors}")
```

## Validation Rules

### Plan Phase
**Inputs:**
- GitHub issue must exist
- GitHub token must be valid
- Database connection available

**Outputs:**
- SDLC_PLAN.md created and non-empty
- adw_state.json created
- Database status='planned', current_phase='plan'

### Test Phase
**Inputs:**
- Worktree exists
- Test files exist in tests/ directory
- Source files exist

**Outputs:**
- Test results recorded
- Database updated with test status

[... continue for all phases ...]

## Benefits

✅ **Fail Fast:** Invalid inputs detected before expensive execution
✅ **Clear Errors:** Specific validation errors instead of generic exceptions
✅ **Consistency:** Same validation logic across all phases
✅ **Completeness:** Ensure phases produced all required outputs

## Error Handling

Invalid inputs:
```
ValueError: Invalid inputs for test phase: No test files found in tests/ directory
```

Incomplete outputs:
```
ValueError: Incomplete outputs from plan phase: SDLC_PLAN.md not created
```
```

### Step 7: Commit Changes

```bash
git add adws/utils/state_validator.py
git add app/server/tests/utils/test_state_validator.py
git add adws/*.py  # Updated phase scripts
git add adws/adw_sdlc_complete_iso.py  # Updated orchestrator
git add docs/adw/state-validation.md
git commit -m "feat: Add state validation middleware for ADW phases

Part 3 of 4 for Session 19 Phase 2 (State Management Clarity)

Created StateValidator class that validates:
- Inputs BEFORE phase execution (fail fast)
- Outputs AFTER phase execution (ensure completeness)

Benefits:
- Fail fast on invalid inputs (save time)
- Clear, specific error messages
- Consistent validation across all phases
- Foundation for idempotent phases (Part 4)

Changes:
1. Created StateValidator class with phase-specific validation
2. Added unit tests for validator
3. Integrated into all 10 phase scripts
4. Updated orchestrator to use validation
5. Documented validation rules

Files Added:
- adws/utils/state_validator.py (validator class)
- app/server/tests/utils/test_state_validator.py (tests)
- docs/adw/state-validation.md (documentation)

Files Modified:
- All 10 phase scripts (integrated validation)
- adws/adw_sdlc_complete_iso.py (orchestrator)

Next: Part 4 - Implement Idempotent Phases (12 hours)"
```

## Success Criteria

- ✅ StateValidator class created with phase-specific validation
- ✅ Unit tests for validation logic
- ✅ All 10 phase scripts integrated with validation
- ✅ Orchestrator uses validation
- ✅ Documentation complete
- ✅ Tests pass
- ✅ Changes committed

## Files Expected to Change

**Created:**
- `adws/utils/state_validator.py` (~300-400 lines)
- `app/server/tests/utils/test_state_validator.py` (~200 lines)
- `docs/adw/state-validation.md` (~2 KB)

**Modified:**
- All 10 phase scripts in `adws/` (validation integration)
- `adws/adw_sdlc_complete_iso.py` (orchestrator)

## Deliverables for Summary

When complete, return to coordination chat with:
```
**Issue #3 Complete: Add State Validation Middleware**

**Validator Created:**
- StateValidator class with phase-specific validation
- Input validation (before execution)
- Output validation (after execution)

**Integration:**
- All 10 phase scripts now validate inputs/outputs
- Orchestrator uses validation
- Unit tests created

**Validation Rules:**
- [N] input validations across all phases
- [N] output validations across all phases

**Time Spent:** [actual hours]

**Key Insights:**
- [Common validation failures found]
- [Phases with most complex validation]
- [Recommendations for Part 4]

**Ready for:** Part 4 - Implement Idempotent Phases (final part)
```

## Troubleshooting

**If validation too strict:**
- Add warnings instead of errors for non-critical issues
- Document validation as optional vs. required

**If validation too slow:**
- Cache results where possible
- Only validate when state changes
- Skip expensive checks in development mode

**If tests fail:**
- Use mocks for database/filesystem in unit tests
- Test validation logic separately from phase logic
- Add integration tests for end-to-end validation

---

**Ready to copy into Issue #3!**
