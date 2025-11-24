# ADW Failure Analysis & Complete Fix Protocol

**Date:** 2025-11-24
**Context:** Issues #78, #79, #83 - ADW Monitor multi-phase workflow
**Impact:** 3 empty PRs created, Phase 2 incomplete, no actual code implementation

---

## Executive Summary

Three ADW workflows (3af4a34d, 446dab5f, 2cfe5aa9) were triggered for Issue #83 (Phase 2: Frontend Component). All workflows:
- Used `adw_plan_iso` (planning-only workflow)
- Created empty PRs with only spec documents
- Failed to implement actual code
- Resulted in wasted resources and confusion

**Root Cause:** Systemic issues in ADW workflow selection, validation, and phase handoff.

---

## Detailed Failure Analysis

### 1. Timeline of Events

| Time | Event | ADW ID | Action |
|------|-------|---------|---------|
| 10:42:19 | ADW started | 12ad9dbd | Planning for Phase 1 validation |
| 10:44:01 | ADW started | 446dab5f | Planning for Phase 2 frontend |
| 10:44:XX | ADW started | 3af4a34d | Planning for Phase 2 frontend |
| ~10:45 | PRs created | All 3 | Empty PRs with only config changes |
| ~10:47 | Issue still open | #83 | No actual implementation |

### 2. Root Causes

#### A. Wrong Workflow Type Used

**Problem:** All ADWs used `adw_plan_iso` (planning-only workflow)

```python
# adw_plan_iso.py workflow steps:
# 1. Fetch GitHub issue
# 2. Classify issue type
# 3. Create feature branch
# 4. Generate implementation plan  ← Stops here!
# 5. Commit plan
# 6. Push and create PR

# Missing steps (in adw_sdlc_complete_iso):
# 7. Build (implement code)
# 8. Lint (check code quality)
# 9. Test (run tests)
# 10. Review (validate implementation)
# 11. Document (add docs)
# 12. Ship (merge PR)
# 13. Cleanup (remove worktree)
```

**Evidence:**
```json
// agents/446dab5f/adw_state.json
{
  "all_adws": ["adw_plan_iso"],  // ← Only planning workflow
  "status": "running",
  "workflow_template": "adw_plan_iso"
}
```

**Impact:**
- PRs contained only plan documents
- No TypeScript components written
- No API client functions created
- No integration with existing code

#### B. No Code Implementation Validation

**Problem:** PRs created without verifying actual code changes

**Current Flow:**
```bash
adw_plan_iso.py
  ↓
Create branch
  ↓
Write plan to specs/
  ↓
git add specs/
  ↓
git commit
  ↓
gh pr create  ← No validation of actual implementation
```

**Missing Validation:**
```bash
# Should check:
1. Are there code files (*.ts, *.tsx, *.py) changed?
2. Are there only documentation files?
3. Does git diff show actual implementation?
4. Do tests exist for new code?
5. Does build/typecheck pass?
```

#### C. Concurrent ADW Conflicts

**Problem:** Multiple ADWs triggered for same issue

**Evidence:**
```bash
# All working on Issue #83 simultaneously:
agents/3af4a34d/  # ADW 1
agents/446dab5f/  # ADW 2
agents/12ad9dbd/  # ADW 3 (different issue but related)
```

**Issues:**
- Racing to create same PR
- Conflicting branches
- Wasted compute resources
- Confusion about which ADW is "official"

**Missing Protection:**
- No mutex/lock on issue numbers
- No check for existing ADWs on same issue
- No coordination between ADWs

#### D. No Phase Handoff Mechanism

**Problem:** Planning phase doesn't automatically trigger implementation

**Current Behavior:**
```
Phase 2 Issue Created (#83)
  ↓
ADW triggered with adw_plan_iso
  ↓
Plan created
  ↓
PR opened
  ↓
❌ STOPS - No implementation phase
```

**Expected Behavior:**
```
Phase 2 Issue Created (#83)
  ↓
ADW triggered with adw_sdlc_complete_iso
  ↓
Plan created
  ↓
✅ Auto-transition to Build phase
  ↓
Code implemented
  ↓
Tests run
  ↓
PR merged
  ↓
Phase 3 auto-triggered
```

#### E. Multi-Phase Workflow Issues

**Problem:** Multi-phase workflow spawns multiple concurrent ADWs

**Code Location:** `app/server/services/multi_phase_issue_handler.py`

**Current Behavior:**
1. User submits multi-phase request
2. Backend creates parent issue (#78)
3. Backend creates phase issues (#79, #83, etc.)
4. **Each phase triggers separate ADW workflow**
5. No coordination between phase ADWs

**Issues:**
- Phase 1 and Phase 2 ADWs start simultaneously
- No dependency enforcement (Phase 2 should wait for Phase 1)
- No shared context between phases

---

## Complete Fix Protocol

### Stage 1: Pre-Implementation Analysis ✅

**Checklist:**
- [x] Identify all failed ADWs
- [x] Analyze failure patterns
- [x] Document root causes
- [x] Review ADW workflow types
- [x] Examine phase queue system
- [x] Check for systemic issues

### Stage 2: Immediate Fixes (Critical Path)

#### Fix 2A: Enforce Correct Workflow Type

**File:** `app/server/services/phase_queue_service.py` (or wherever ADW execution is triggered)

**Current (Wrong):**
```python
# Somewhere in the code that triggers ADWs:
subprocess.run(["uv", "run", "adws/adw_plan_iso.py", str(issue_number)])
```

**Fixed:**
```python
# Use complete SDLC workflow for implementation phases
def execute_phase(queue_id: str) -> dict:
    """Execute a phase from the queue."""
    phase = self.repository.get_phase(queue_id)

    # Determine workflow type based on phase content
    workflow_type = determine_workflow_type(phase)

    if workflow_type == "implementation":
        # Use complete SDLC workflow
        cmd = ["uv", "run", "adws/adw_sdlc_complete_iso.py", str(phase.issue_number)]
    elif workflow_type == "validation":
        # Use planning workflow for validation only
        cmd = ["uv", "run", "adws/adw_plan_iso.py", str(phase.issue_number)]
    else:
        raise ValueError(f"Unknown workflow type: {workflow_type}")

    # Execute workflow
    result = subprocess.run(cmd, capture_output=True, text=True)
    return {"success": result.returncode == 0, "output": result.stdout}

def determine_workflow_type(phase: PhaseQueueItem) -> str:
    """Determine if phase needs implementation or validation."""
    title_lower = phase.phase_data.get("title", "").lower()
    content_lower = phase.phase_data.get("content", "").lower()

    # Check for validation indicators
    validation_keywords = ["validate", "verify", "check", "confirm", "review existing"]
    if any(kw in title_lower or kw in content_lower for kw in validation_keywords):
        return "validation"

    # Default to implementation for all other phases
    return "implementation"
```

**Test Plan:**
```bash
# Test 1: Implementation phase should use adw_sdlc_complete_iso
pytest -xvs app/server/tests/services/test_phase_queue_service.py::test_execute_implementation_phase

# Test 2: Validation phase should use adw_plan_iso
pytest -xvs app/server/tests/services/test_phase_queue_service.py::test_execute_validation_phase
```

#### Fix 2B: Add ADW Mutex/Lock System

**File:** `app/server/services/adw_coordination_service.py` (new file)

```python
"""
ADW Coordination Service - Prevents concurrent ADWs on same issue.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from utils.db_connection import get_connection

logger = logging.getLogger(__name__)


class ADWCoordinationService:
    """Ensures only one ADW works on an issue at a time."""

    def __init__(self, db_path: str = "db/database.db"):
        self.db_path = db_path
        self._ensure_locks_table()

    def _ensure_locks_table(self):
        """Create adw_locks table if it doesn't exist."""
        with get_connection(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS adw_locks (
                    issue_number INTEGER PRIMARY KEY,
                    adw_id TEXT NOT NULL,
                    locked_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    status TEXT NOT NULL
                )
            """)
            conn.commit()

    def acquire_lock(self, issue_number: int, adw_id: str, timeout_minutes: int = 120) -> bool:
        """
        Acquire exclusive lock on issue for ADW.

        Returns:
            True if lock acquired, False if issue already locked
        """
        now = datetime.now()
        expires_at = now + timedelta(minutes=timeout_minutes)

        with get_connection(self.db_path) as conn:
            # Check for existing lock
            existing = conn.execute(
                "SELECT adw_id, expires_at FROM adw_locks WHERE issue_number = ?",
                (issue_number,)
            ).fetchone()

            if existing:
                existing_adw_id, expires_at_str = existing
                expires_at_dt = datetime.fromisoformat(expires_at_str)

                # Check if lock expired
                if expires_at_dt > now:
                    logger.warning(
                        f"Issue #{issue_number} already locked by ADW {existing_adw_id} "
                        f"(expires: {expires_at_str})"
                    )
                    return False

                # Lock expired, take it over
                logger.info(f"Taking over expired lock on issue #{issue_number}")
                conn.execute(
                    "DELETE FROM adw_locks WHERE issue_number = ?",
                    (issue_number,)
                )

            # Acquire new lock
            conn.execute(
                """INSERT INTO adw_locks
                   (issue_number, adw_id, locked_at, expires_at, status)
                   VALUES (?, ?, ?, ?, ?)""",
                (issue_number, adw_id, now.isoformat(), expires_at.isoformat(), "active")
            )
            conn.commit()

        logger.info(
            f"ADW {adw_id} acquired lock on issue #{issue_number} "
            f"(expires: {expires_at.isoformat()})"
        )
        return True

    def release_lock(self, issue_number: int, adw_id: str):
        """Release lock on issue."""
        with get_connection(self.db_path) as conn:
            conn.execute(
                "DELETE FROM adw_locks WHERE issue_number = ? AND adw_id = ?",
                (issue_number, adw_id)
            )
            conn.commit()
        logger.info(f"ADW {adw_id} released lock on issue #{issue_number}")

    def is_locked(self, issue_number: int) -> tuple[bool, Optional[str]]:
        """
        Check if issue is locked.

        Returns:
            (is_locked, adw_id_holding_lock)
        """
        now = datetime.now()
        with get_connection(self.db_path) as conn:
            result = conn.execute(
                "SELECT adw_id, expires_at FROM adw_locks WHERE issue_number = ?",
                (issue_number,)
            ).fetchone()

            if not result:
                return False, None

            adw_id, expires_at_str = result
            expires_at = datetime.fromisoformat(expires_at_str)

            if expires_at < now:
                # Lock expired
                return False, None

            return True, adw_id
```

**Integration:**
```python
# In adw_modules/workflow_ops.py
from app.server.services.adw_coordination_service import ADWCoordinationService

def ensure_adw_id(issue_number: str, adw_id: Optional[str] = None, logger=None) -> str:
    """Ensure ADW ID exists and acquire lock."""
    # ... existing code ...

    # NEW: Acquire lock before proceeding
    coordinator = ADWCoordinationService()
    if not coordinator.acquire_lock(int(issue_number), adw_id):
        locked_by = coordinator.is_locked(int(issue_number))[1]
        raise RuntimeError(
            f"Issue #{issue_number} is already being processed by ADW {locked_by}. "
            f"Wait for that workflow to complete or use --force to override."
        )

    return adw_id
```

**Test Plan:**
```bash
# Test 1: Single ADW acquires lock
pytest -xvs app/server/tests/services/test_adw_coordination.py::test_acquire_lock

# Test 2: Second ADW blocked
pytest -xvs app/server/tests/services/test_adw_coordination.py::test_concurrent_adw_blocked

# Test 3: Expired lock can be taken over
pytest -xvs app/server/tests/services/test_adw_coordination.py::test_expired_lock_takeover
```

#### Fix 2C: Add Pre-PR Validation

**File:** `adws/adw_modules/pr_validator.py` (new file)

```python
"""
PR Validator - Ensures PRs contain actual implementation before creation.
"""
import subprocess
import logging
from pathlib import Path
from typing import Tuple, List

logger = logging.getLogger(__name__)


class PRValidator:
    """Validates that PR contains actual code changes."""

    def __init__(self, worktree_path: str):
        self.worktree_path = Path(worktree_path)

    def validate_changes(self) -> Tuple[bool, str, List[str]]:
        """
        Validate that branch contains actual code implementation.

        Returns:
            (is_valid, message, issues)
        """
        issues = []

        # Get list of changed files
        result = subprocess.run(
            ["git", "diff", "--name-only", "main...HEAD"],
            cwd=self.worktree_path,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return False, "Failed to get git diff", ["Git diff command failed"]

        changed_files = [f.strip() for f in result.stdout.split("\n") if f.strip()]

        if not changed_files:
            issues.append("No files changed")
            return False, "No changes detected", issues

        # Categorize files
        code_files = []
        test_files = []
        doc_files = []
        config_files = []
        spec_files = []

        for file in changed_files:
            if file.startswith("specs/"):
                spec_files.append(file)
            elif file.endswith((".ts", ".tsx", ".py", ".js", ".jsx")):
                if "test" in file or "__tests__" in file:
                    test_files.append(file)
                else:
                    code_files.append(file)
            elif file.endswith((".md", ".txt", ".rst")):
                doc_files.append(file)
            elif file.endswith((".json", ".yaml", ".yml", ".toml", ".ini")):
                config_files.append(file)

        # Validation rules
        if spec_files and not code_files:
            issues.append("Only spec files changed - no actual implementation")

        if not code_files and not test_files:
            issues.append("No code or test files changed")

        if code_files and not test_files:
            logger.warning("Code files changed but no tests added")

        # Check if only trivial config changes
        if config_files and not code_files and len(changed_files) <= 2:
            issues.append("Only trivial config changes - no implementation")

        # Validation result
        if issues:
            message = "PR validation failed: " + "; ".join(issues)
            return False, message, issues

        # Success
        message = f"PR validation passed: {len(code_files)} code files, {len(test_files)} test files"
        logger.info(message)
        return True, message, []

    def should_create_pr(self) -> Tuple[bool, str]:
        """
        Determine if PR should be created based on changes.

        Returns:
            (should_create, reason)
        """
        is_valid, message, issues = self.validate_changes()

        if not is_valid:
            return False, f"Skipping PR creation: {message}"

        return True, message
```

**Integration in `adw_modules/git_ops.py`:**
```python
from adw_modules.pr_validator import PRValidator

def finalize_git_operations(state: ADWState, logger):
    """Finalize git operations and create PR."""
    # ... existing code ...

    # NEW: Validate changes before creating PR
    validator = PRValidator(state.get("worktree_path"))
    should_create, reason = validator.should_create_pr()

    if not should_create:
        logger.warning(f"PR creation skipped: {reason}")
        # Add comment to issue instead
        make_issue_comment(
            state.get("issue_number"),
            f"## 🛑 PR Creation Skipped\n\n{reason}\n\n"
            f"This workflow completed the planning phase but did not implement code. "
            f"To proceed with implementation, trigger a full SDLC workflow."
        )
        return {"pr_created": False, "reason": reason}

    # Proceed with PR creation
    logger.info(f"PR validation passed: {reason}")
    # ... existing PR creation code ...
```

**Test Plan:**
```bash
# Test 1: Reject PR with only spec files
pytest -xvs app/server/tests/adw/test_pr_validator.py::test_reject_spec_only

# Test 2: Accept PR with code and tests
pytest -xvs app/server/tests/adw/test_pr_validator.py::test_accept_code_and_tests

# Test 3: Warn on code without tests
pytest -xvs app/server/tests/adw/test_pr_validator.py::test_warn_no_tests
```

### Stage 3: Integration Testing

#### Test 3A: End-to-End Multi-Phase Workflow

**Test Script:** `tests/e2e/test_complete_multi_phase.py`

```python
"""
E2E test for complete multi-phase workflow with fixes.
"""
import pytest
import subprocess
import time
from services.adw_coordination_service import ADWCoordinationService
from services.phase_queue_service import PhaseQueueService


def test_multi_phase_workflow_with_proper_coordination():
    """Test that multi-phase workflow executes correctly with all fixes."""

    # Setup
    queue_service = PhaseQueueService()
    coordinator = ADWCoordinationService()

    # Step 1: Create multi-phase request
    parent_issue = 999  # Test issue

    # Enqueue Phase 1
    phase1_id = queue_service.enqueue(
        parent_issue=parent_issue,
        phase_number=1,
        phase_data={
            "title": "Phase 1: Backend API",
            "content": "Implement /api/test endpoint"
        },
        depends_on_phase=None
    )

    # Enqueue Phase 2 (depends on Phase 1)
    phase2_id = queue_service.enqueue(
        parent_issue=parent_issue,
        phase_number=2,
        phase_data={
            "title": "Phase 2: Frontend Component",
            "content": "Create TestComponent.tsx"
        },
        depends_on_phase=1
    )

    # Step 2: Execute Phase 1
    result1 = queue_service.execute_phase(phase1_id)
    assert result1["success"], "Phase 1 execution failed"

    # Verify lock was acquired
    is_locked, adw_id = coordinator.is_locked(parent_issue)
    assert is_locked, "Phase 1 should have acquired lock"

    # Step 3: Try to execute Phase 2 before Phase 1 completes (should be blocked)
    phase2 = queue_service.get_phase(phase2_id)
    assert phase2.status == "queued", "Phase 2 should still be queued"

    # Step 4: Mark Phase 1 complete
    queue_service.mark_completed(phase1_id, issue_number=1001, pr_number=501)

    # Wait for Phase 2 to become ready
    time.sleep(1)
    phase2 = queue_service.get_phase(phase2_id)
    assert phase2.status == "ready", "Phase 2 should be ready after Phase 1 completes"

    # Step 5: Execute Phase 2
    result2 = queue_service.execute_phase(phase2_id)
    assert result2["success"], "Phase 2 execution failed"

    # Step 6: Verify both phases created valid PRs
    # (This would check GitHub API for actual PRs with code changes)

    print("✅ Multi-phase workflow test passed")


def test_concurrent_adw_prevention():
    """Test that concurrent ADWs on same issue are prevented."""

    coordinator = ADWCoordinationService()
    issue_number = 998

    # ADW 1 acquires lock
    success1 = coordinator.acquire_lock(issue_number, "adw-test-1")
    assert success1, "First ADW should acquire lock"

    # ADW 2 tries to acquire same lock (should fail)
    success2 = coordinator.acquire_lock(issue_number, "adw-test-2")
    assert not success2, "Second ADW should be blocked"

    # ADW 1 releases lock
    coordinator.release_lock(issue_number, "adw-test-1")

    # ADW 2 can now acquire lock
    success3 = coordinator.acquire_lock(issue_number, "adw-test-2")
    assert success3, "ADW 2 should acquire lock after release"

    print("✅ Concurrent ADW prevention test passed")


def test_pr_validation_prevents_empty_prs():
    """Test that PR validation prevents empty/spec-only PRs."""

    from adw_modules.pr_validator import PRValidator

    # Test case 1: Only spec files (should reject)
    # (Would set up a test worktree with only spec changes)

    # Test case 2: Code + tests (should accept)
    # (Would set up a test worktree with code and test files)

    # Test case 3: Code without tests (should warn but accept)
    # (Would set up a test worktree with code but no tests)

    print("✅ PR validation test passed")
```

**Run Tests:**
```bash
# Run all E2E tests
pytest -xvs tests/e2e/test_complete_multi_phase.py

# Run specific test
pytest -xvs tests/e2e/test_complete_multi_phase.py::test_multi_phase_workflow_with_proper_coordination
```

### Stage 4: Regression Testing

**Test Scenarios:**

1. **Single-Phase Workflow**
   ```bash
   # Should still work with single issue
   uv run adws/adw_sdlc_complete_iso.py 100
   ```

2. **Multi-Phase Workflow**
   ```bash
   # Phase 2 should wait for Phase 1
   # No concurrent ADWs on same issue
   # Proper workflow type selection
   ```

3. **Concurrent Issues**
   ```bash
   # Different issues should execute in parallel
   uv run adws/adw_sdlc_complete_iso.py 101 &
   uv run adws/adw_sdlc_complete_iso.py 102 &
   ```

4. **Lock Expiration**
   ```bash
   # Lock should expire after timeout
   # New ADW can take over
   ```

**Regression Test Script:**
```bash
#!/bin/bash
# tests/regression/test_adw_workflows.sh

echo "Running ADW workflow regression tests..."

# Test 1: Single-phase workflow
echo "Test 1: Single-phase workflow"
uv run adws/adw_sdlc_complete_iso.py 997 --skip-e2e
if [ $? -eq 0 ]; then
  echo "✅ Single-phase workflow passed"
else
  echo "❌ Single-phase workflow failed"
  exit 1
fi

# Test 2: Multi-phase workflow
echo "Test 2: Multi-phase workflow"
pytest -xvs tests/e2e/test_complete_multi_phase.py::test_multi_phase_workflow_with_proper_coordination
if [ $? -eq 0 ]; then
  echo "✅ Multi-phase workflow passed"
else
  echo "❌ Multi-phase workflow failed"
  exit 1
fi

# Test 3: Concurrent ADW prevention
echo "Test 3: Concurrent ADW prevention"
pytest -xvs tests/e2e/test_complete_multi_phase.py::test_concurrent_adw_prevention
if [ $? -eq 0 ]; then
  echo "✅ Concurrent ADW prevention passed"
else
  echo "❌ Concurrent ADW prevention failed"
  exit 1
fi

echo "All regression tests passed!"
```

### Stage 5: Deployment & Monitoring

#### 5A: Deployment Checklist

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All E2E tests pass
- [ ] Regression tests pass
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Migration scripts ready (for adw_locks table)
- [ ] Rollback plan prepared

#### 5B: Migration Script

**File:** `app/server/db/migrations/009_add_adw_locks.sql`

```sql
-- Migration: Add ADW locks table for coordination
-- Date: 2025-11-24
-- Purpose: Prevent concurrent ADWs on same issue

CREATE TABLE IF NOT EXISTS adw_locks (
    issue_number INTEGER PRIMARY KEY,
    adw_id TEXT NOT NULL,
    locked_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('active', 'expired', 'released'))
);

CREATE INDEX IF NOT EXISTS idx_adw_locks_expires_at ON adw_locks(expires_at);
CREATE INDEX IF NOT EXISTS idx_adw_locks_adw_id ON adw_locks(adw_id);

-- Add comment
INSERT INTO migration_history (version, description, applied_at)
VALUES (9, 'Add ADW locks table for coordination', datetime('now'));
```

#### 5C: Monitoring Dashboard

**Metrics to Track:**
- ADW lock acquisition success rate
- Average lock hold time
- Lock timeouts/expirations
- PR validation pass/fail rate
- Empty PR prevention count
- Phase handoff success rate

**File:** `app/server/routes/monitoring_routes.py`

```python
@router.get("/api/adw-metrics")
async def get_adw_metrics():
    """Get ADW coordination metrics."""
    with get_connection() as conn:
        # Lock metrics
        total_locks = conn.execute(
            "SELECT COUNT(*) FROM adw_locks"
        ).fetchone()[0]

        active_locks = conn.execute(
            "SELECT COUNT(*) FROM adw_locks WHERE expires_at > datetime('now')"
        ).fetchone()[0]

        # PR validation metrics (would need new table to track)
        # ...

        return {
            "locks": {
                "total": total_locks,
                "active": active_locks,
                "expired": total_locks - active_locks
            },
            # ... other metrics
        }
```

### Stage 6: Documentation & Training

#### 6A: Update ADW Documentation

**File:** `docs/ADW_WORKFLOWS.md`

```markdown
# ADW Workflow Selection Guide

## When to Use Each Workflow

### adw_plan_iso.py
**Use for:** Validation, planning, research
**Output:** Implementation plan only
**Duration:** 1-2 minutes
**Cost:** $0.05-0.15

**Examples:**
- Validate that feature is already implemented
- Research approach before implementation
- Generate RFC/design document

### adw_sdlc_complete_iso.py
**Use for:** Full feature implementation
**Output:** Working code + tests + docs + merged PR
**Duration:** 10-20 minutes
**Cost:** $1.50-$5.00

**Examples:**
- Implement new feature
- Fix bugs
- Add new components

## Multi-Phase Workflows

**Automatic Coordination:**
- Only one ADW per issue at a time
- Phase 2 waits for Phase 1 to complete
- Locks expire after 2 hours
- Empty PRs automatically prevented

**Phase Dependencies:**
```
Phase 1 (Backend) → Phase 2 (Frontend) → Phase 3 (E2E Tests)
```
```

#### 6B: Update README

Add section on multi-phase workflows and ADW coordination.

---

## Implementation Checklist

### Critical Path (Must Complete)

- [ ] **Fix 2A:** Enforce correct workflow type in phase execution
- [ ] **Fix 2B:** Implement ADW coordination/locking system
- [ ] **Fix 2C:** Add PR validation before creation
- [ ] **Test 3A:** E2E multi-phase workflow test
- [ ] **Migration:** Create adw_locks table
- [ ] **Deploy:** Roll out fixes to production

### High Priority (Should Complete)

- [ ] Add monitoring for ADW metrics
- [ ] Update documentation
- [ ] Add alerting for lock timeouts
- [ ] Implement lock cleanup job (remove expired locks)

### Medium Priority (Nice to Have)

- [ ] Dashboard for visualizing ADW activity
- [ ] Slack/Discord notifications for ADW events
- [ ] Cost tracking per ADW workflow
- [ ] ADW workflow analytics

---

## Success Criteria

### Immediate (Post-Deployment)

- [ ] No empty PRs created in next 7 days
- [ ] No concurrent ADWs on same issue
- [ ] All phase dependencies respected
- [ ] PR validation catches 100% of planning-only PRs

### Long-Term (30 Days)

- [ ] 95%+ ADW success rate
- [ ] <5% lock contention rate
- [ ] Zero manual intervention needed for phase coordination
- [ ] Average ADW completion time within expected range

---

## Rollback Plan

If critical issues arise:

1. **Disable ADW locking:**
   ```python
   # In ADWCoordinationService
   ENABLE_LOCKING = False  # Emergency disable
   ```

2. **Revert to manual phase execution:**
   ```bash
   # Manually trigger ADWs instead of automatic
   uv run adws/adw_sdlc_complete_iso.py <issue-number>
   ```

3. **Fall back to single-ADW mode:**
   ```python
   # Disable parallel ADW execution
   MAX_CONCURRENT_ADWS = 1
   ```

---

## Contact & Escalation

**Issues:** Open GitHub issue with label `adw-coordination`
**Urgent:** Disable automatic ADW execution in settings
**Data Loss:** ADW state files backed up in `agents/_archived/`

---

## Appendix: Common Issues & Solutions

### Issue: Lock Not Released

**Symptom:** ADW stuck, lock not released
**Solution:**
```bash
# Manually release lock
sqlite3 app/server/db/database.db "DELETE FROM adw_locks WHERE issue_number = X"
```

### Issue: Wrong Workflow Type Selected

**Symptom:** Planning workflow used for implementation
**Solution:**
```python
# Check determination logic in determine_workflow_type()
# Add more keywords to validation_keywords list
```

### Issue: PR Created Despite Validation Failure

**Symptom:** Empty PR created
**Solution:**
```python
# Check PRValidator logic
# Ensure finalize_git_operations() respects validation result
```

---

**Document Version:** 1.0
**Last Updated:** 2025-11-24
**Next Review:** 2025-12-01
