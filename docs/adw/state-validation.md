# ADW State Validation Middleware

**Version:** 1.0
**Last Updated:** 2025-12-10
**Part:** Session 19 Phase 2 Part 3 - State Validation
**Related:** `docs/adw/phase-contracts.md`, `docs/adw/state-management-ssot.md`

---

## Overview

State validation middleware validates phase inputs BEFORE execution (fail fast) and outputs AFTER execution (ensure completeness). This prevents wasteful mid-execution failures and ensures phases produce all required outputs.

### Problems Solved

**Before Validation:**
```python
def run_test_phase(issue_number):
    # ... expensive setup (30 seconds) ...

    # FAILURE: Test files don't exist (should have been validated up front!)
    test_files = glob.glob('tests/**/*.py')
    if not test_files:
        raise ValueError("No test files found")  # ❌ Too late!
```

**After Validation:**
```python
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

---

## Architecture

### StateValidator Class

**Location:** `adws/utils/state_validator.py`

**Key Components:**
- `ValidationResult` - Dataclass containing validation status, errors, and warnings
- `StateValidator` - Main validator class with phase-specific validation methods
- `PHASE_CONTRACTS` - Contract definitions from `docs/adw/phase-contracts.md`

### Validation Flow

```
Phase Script
    ↓
1. Create validator for phase
    ↓
2. Validate inputs (from database + state file)
    ↓
3. If invalid → Fail fast with clear errors
    ↓
4. If valid → Execute phase logic
    ↓
5. Validate outputs (from database + state file)
    ↓
6. If invalid → Fail with completeness errors
    ↓
7. If valid → Return success
```

---

## Usage

### Basic Usage

```python
from adws.utils.state_validator import StateValidator

def run_phase(issue_number: int):
    """Run a phase with validation."""

    # 1. Create validator for this phase
    validator = StateValidator(phase='test')

    # 2. Validate inputs BEFORE execution
    input_validation = validator.validate_inputs(issue_number)

    if not input_validation.is_valid:
        logger.error(f"Test phase input validation failed: {input_validation.errors}")
        raise ValueError(f"Invalid inputs for test phase: {', '.join(input_validation.errors)}")

    if input_validation.warnings:
        for warning in input_validation.warnings:
            logger.warning(f"Test phase input warning: {warning}")

    logger.info("✓ Test phase inputs validated")

    # 3. Execute phase
    try:
        # ... existing test execution logic ...
        pass
    except Exception as e:
        logger.error(f"Test phase execution failed: {e}")
        raise

    # 4. Validate outputs AFTER execution
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

### ValidationResult API

```python
# Create validation result
result = ValidationResult(
    is_valid=True,
    errors=[],
    warnings=["Non-critical issue"]
)

# Check validity (bool conversion)
if result:  # Same as: if result.is_valid
    print("Valid!")

# Access errors and warnings
for error in result.errors:
    logger.error(error)

for warning in result.warnings:
    logger.warning(warning)
```

---

## Validation Rules by Phase

### Phase 1: Plan

**Inputs:**
- ✅ `GITHUB_TOKEN` environment variable must be set
- ✅ GitHub issue must exist (verified by database query)
- ✅ Database connection must be available

**Outputs:**
- ✅ `worktree_path` must be set in state
- ✅ Worktree directory must exist
- ✅ Plan file must exist at `plan_file` path
- ✅ Plan file must be > 100 bytes (non-trivial)
- ✅ `adw_state.json` must exist in worktree
- ✅ Database `adw_id` field must be set

**Example:**
```python
validator = StateValidator(phase='plan')

# Before creating plan
validation = validator.validate_inputs(issue_number=123)
# Checks: GitHub token, database connection

# After creating plan
validation = validator.validate_outputs(issue_number=123)
# Checks: worktree exists, plan file exists and non-empty
```

### Phase 2: Validate

**Inputs:**
- ✅ Worktree must exist at `worktree_path`
- ✅ Plan file must exist at `plan_file`
- ✅ `adw_state.json` must exist in worktree

**Outputs:**
- ✅ `baseline_errors` must be recorded in state

**Example:**
```python
validator = StateValidator(phase='validate')

# Before validation
validation = validator.validate_inputs(issue_number=123)
# Checks: worktree exists, plan file exists

# After validation
validation = validator.validate_outputs(issue_number=123)
# Checks: baseline_errors recorded
```

### Phase 3: Build

**Inputs:**
- ✅ Worktree must exist
- ✅ Plan file must exist
- ✅ `branch_name` must be set in state

**Outputs:**
- ✅ `external_build_results` must be recorded in state

**Example:**
```python
validator = StateValidator(phase='build')

# Before build
validation = validator.validate_inputs(issue_number=123)
# Checks: worktree, plan file, branch name

# After build
validation = validator.validate_outputs(issue_number=123)
# Checks: build results recorded
```

### Phase 4: Lint

**Inputs:**
- ✅ Worktree must exist
- ✅ Source files must exist (backend: `app/server/**/*.py` OR frontend: `app/client/src/**/*.{ts,tsx,js,jsx}`)

**Outputs:**
- ✅ `external_lint_results` must be recorded in state

**Example:**
```python
validator = StateValidator(phase='lint')

# Before lint
validation = validator.validate_inputs(issue_number=123)
# Checks: worktree exists, source files exist

# After lint
validation = validator.validate_outputs(issue_number=123)
# Checks: lint results recorded
```

### Phase 5: Test

**Inputs:**
- ✅ Worktree must exist
- ✅ Test files must exist (backend: `app/server/tests/**/*.py` OR frontend: `app/client/src/__tests__/**/*.{test.ts,test.tsx,spec.ts,spec.tsx}`)

**Outputs:**
- ✅ `external_test_results` must be recorded in state

**Example:**
```python
validator = StateValidator(phase='test')

# Before test
validation = validator.validate_inputs(issue_number=123)
# Checks: worktree exists, test files exist

# After test
validation = validator.validate_outputs(issue_number=123)
# Checks: test results recorded
```

### Phase 6: Review

**Inputs:**
- ✅ Worktree must exist
- ✅ Plan file must exist (for spec comparison)
- ✅ `backend_port` must be set
- ✅ `frontend_port` must be set

**Outputs:**
- ⚠️ Review results recorded (may be in GitHub comments instead of state)

**Example:**
```python
validator = StateValidator(phase='review')

# Before review
validation = validator.validate_inputs(issue_number=123)
# Checks: worktree, plan file, ports

# After review
validation = validator.validate_outputs(issue_number=123)
# Less strict - review might post to GitHub
```

### Phase 7: Document

**Inputs:**
- ✅ Worktree must exist
- ✅ Plan file must exist

**Outputs:**
- ⚠️ Documentation files in `app_docs/` (if changes exist)

**Example:**
```python
validator = StateValidator(phase='document')

# Before document
validation = validator.validate_inputs(issue_number=123)
# Checks: worktree, plan file

# After document
validation = validator.validate_outputs(issue_number=123)
# Checks for docs if changes were made
```

### Phase 8: Ship

**Inputs:**
- ✅ All required state fields must be populated:
  - `adw_id`
  - `branch_name`
  - `plan_file`
  - `issue_class`
  - `worktree_path`
  - `backend_port`
  - `frontend_port`
- ✅ Worktree must exist

**Outputs:**
- ✅ `ship_timestamp` must be recorded

**Example:**
```python
validator = StateValidator(phase='ship')

# Before ship
validation = validator.validate_inputs(issue_number=123)
# Checks: ALL required state fields present

# After ship
validation = validator.validate_outputs(issue_number=123)
# Checks: ship timestamp recorded
```

### Phase 9: Cleanup

**Inputs:**
- ⚠️ Worktree path (best-effort, not required)

**Outputs:**
- ⚠️ No strict validation (cleanup is best-effort)

**Example:**
```python
validator = StateValidator(phase='cleanup')

# Before cleanup
validation = validator.validate_inputs(issue_number=123)
# Minimal validation - cleanup is best-effort

# After cleanup
validation = validator.validate_outputs(issue_number=123)
# No strict requirements
```

### Phase 10: Verify

**Inputs:**
- ✅ `backend_port` must be set (for smoke tests)
- ✅ `frontend_port` must be set (for smoke tests)

**Outputs:**
- ⚠️ Verification results (may be in GitHub issue comments)

**Example:**
```python
validator = StateValidator(phase='verify')

# Before verify
validation = validator.validate_inputs(issue_number=123)
# Checks: ports for smoke tests

# After verify
validation = validator.validate_outputs(issue_number=123)
# Minimal validation - results posted to GitHub
```

---

## Integration Examples

### Example 1: Test Phase (`adws/adw_test_iso.py`)

```python
import logging
from adws.utils.state_validator import StateValidator

logger = logging.getLogger(__name__)

def run_test_phase(issue_number: int) -> bool:
    """Run test phase with validation."""

    # Validate inputs BEFORE execution
    validator = StateValidator(phase='test')
    input_validation = validator.validate_inputs(issue_number)

    if not input_validation.is_valid:
        logger.error(f"Test phase input validation failed:")
        for error in input_validation.errors:
            logger.error(f"  - {error}")
        raise ValueError(f"Invalid inputs for test phase: {', '.join(input_validation.errors)}")

    if input_validation.warnings:
        for warning in input_validation.warnings:
            logger.warning(f"Test phase input warning: {warning}")

    logger.info("✓ Test phase inputs validated")

    # Execute test phase
    try:
        # ... existing test execution logic ...
        # Run pytest, vitest, etc.
        success = True  # Placeholder
    except Exception as e:
        logger.error(f"Test phase execution failed: {e}")
        raise

    # Validate outputs AFTER execution
    output_validation = validator.validate_outputs(issue_number)

    if not output_validation.is_valid:
        logger.error(f"Test phase output validation failed:")
        for error in output_validation.errors:
            logger.error(f"  - {error}")
        raise ValueError(f"Incomplete outputs from test phase: {', '.join(output_validation.errors)}")

    if output_validation.warnings:
        for warning in output_validation.warnings:
            logger.warning(f"Test phase output warning: {warning}")

    logger.info("✓ Test phase outputs validated")

    return success
```

### Example 2: Plan Phase (`adws/adw_plan_iso.py`)

```python
from adws.utils.state_validator import StateValidator

def run_plan_phase(issue_number: int) -> bool:
    """Run plan phase with validation."""

    # Validate inputs
    validator = StateValidator(phase='plan')
    input_validation = validator.validate_inputs(issue_number)

    if not input_validation:  # Uses __bool__
        raise ValueError(f"Invalid inputs for plan phase: {', '.join(input_validation.errors)}")

    logger.info("✓ Plan phase inputs validated")

    # Execute plan
    # ... create worktree, generate plan, etc. ...

    # Validate outputs
    output_validation = validator.validate_outputs(issue_number)

    if not output_validation:
        raise ValueError(f"Incomplete outputs from plan phase: {', '.join(output_validation.errors)}")

    logger.info("✓ Plan phase outputs validated")

    return True
```

### Example 3: Orchestrator (`adws/adw_sdlc_complete_iso.py`)

```python
from adws.utils.state_validator import StateValidator

def run_phase(phase_name: str, issue_number: int) -> bool:
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


def run_full_sdlc(issue_number: int):
    """Run full SDLC with validation."""
    phases = ['plan', 'validate', 'build', 'lint', 'test',
             'review', 'document', 'ship', 'cleanup', 'verify']

    for phase in phases:
        if not run_phase(phase, issue_number):
            logger.error(f"SDLC failed at {phase} phase")
            return False

    logger.info("✓ SDLC completed successfully")
    return True
```

---

## Benefits

### 1. Fail Fast
**Before:** Waste 30 seconds on setup before discovering missing test files
**After:** Fail in < 1 second with clear error message

### 2. Clear Error Messages
**Before:** `FileNotFoundError: [Errno 2] No such file or directory: 'tests/'`
**After:** `Invalid inputs for test phase: No test files found in tests/ directory`

### 3. Consistency
**Before:** Different error handling in each phase script
**After:** Consistent validation across all 10 phases

### 4. Completeness
**Before:** Phase completes but forgets to record results
**After:** Output validation catches missing results before phase returns

### 5. Foundation for Idempotence (Part 4)
Validation ensures phase can safely re-run by checking preconditions and postconditions.

---

## Error Handling

### Invalid Inputs

```python
ValueError: Invalid inputs for test phase: No worktree_path in state, Worktree not found: /path/to/trees/77c90e61
```

**What happened:** Test phase started without required inputs
**Why it's good:** Saved time by not running tests that would fail
**Fix:** Run Plan phase to create worktree

### Incomplete Outputs

```python
ValueError: Incomplete outputs from plan phase: SDLC_PLAN.md not created, adw_state.json not created
```

**What happened:** Plan phase completed but didn't create required files
**Why it's good:** Caught missing outputs before later phases depend on them
**Fix:** Debug plan phase to ensure it creates all required files

### Warnings (Non-Blocking)

```python
WARNING: Test phase input warning: Failed to load state file: Invalid JSON
```

**What happened:** State file exists but is malformed
**Why it's a warning:** Validation can continue with partial state
**Action:** Fix state file format, but phase can proceed

---

## Testing

### Unit Tests

**Location:** `app/server/tests/utils/test_state_validator.py`

**Coverage:**
- 20 unit tests covering:
  - ValidationResult behavior
  - StateValidator initialization
  - Plan phase validation
  - Test phase validation
  - Build phase validation
  - Ship phase validation
  - Worktree path resolution
  - Database error handling
  - Warning generation

**Run tests:**
```bash
cd app/server
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql uv run pytest tests/utils/test_state_validator.py -v
```

### Integration Tests

To test validation in actual workflows:

```bash
# Test Plan phase validation
cd adws
uv run python3 adw_plan_iso.py 123  # Should validate inputs/outputs

# Test Test phase validation (without test files)
# Should fail fast with validation error

# Test Ship phase validation (without complete state)
# Should fail with missing required fields error
```

---

## Implementation Checklist

To integrate validation into a phase script:

- [ ] Import StateValidator: `from adws.utils.state_validator import StateValidator`
- [ ] Create validator at start: `validator = StateValidator(phase='<phase_name>')`
- [ ] Validate inputs before execution: `input_validation = validator.validate_inputs(issue_number)`
- [ ] Check validation result: `if not input_validation.is_valid: raise ValueError(...)`
- [ ] Log warnings if present: `for warning in input_validation.warnings: logger.warning(warning)`
- [ ] Execute phase logic
- [ ] Validate outputs after execution: `output_validation = validator.validate_outputs(issue_number)`
- [ ] Check output validation: `if not output_validation.is_valid: raise ValueError(...)`
- [ ] Log success: `logger.info("✓ Phase outputs validated")`

---

## Next Steps

**Part 3 Complete:** State validation middleware implemented
**Next:** Part 4 - Implement Idempotent Phases

With validation in place, Part 4 can build on this foundation to make phases safely re-runnable by:
1. Checking if phase already completed (skip if outputs exist)
2. Resuming from partial progress (if inputs exist but outputs incomplete)
3. Cleaning up and restarting (if both inputs and outputs invalid)

---

**End of State Validation Documentation**
