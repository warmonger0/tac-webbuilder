# Phase 2: Strategic Architectural Redesign

**Timeline:** Weeks 1-3
**Goal:** Achieve >80% workflow success rate with comprehensive reliability improvements
**Priority:** P1 - High (Long-term stability)

---

## Overview

Phase 2 addresses fundamental architectural gaps identified in the investigation. These changes transform ADW from a fragile prototype into a production-ready automation system.

---

## 2.1 State Management Redesign

### Objective
Replace fragile file-based state with robust, validated state management system.

### Current Problems
- File-based state with no validation
- No atomic updates (race conditions)
- No state versioning or migrations
- State corruption causes silent failures

---

### Component 2.1.1: Workflow State Machine

**File:** `adws/adw_modules/state_machine.py`

**Implementation:**
```python
"""
Formal workflow state machine with transitions and validations.
"""

from enum import Enum
from typing Optional, Dict, Any
from datetime import datetime

class WorkflowState(Enum):
    """Formal workflow states"""
    PENDING = "pending"
    PLANNING = "planning"
    BUILDING = "building"
    LINTING = "linting"
    TESTING = "testing"
    REVIEWING = "reviewing"
    DOCUMENTING = "documenting"
    SHIPPING = "shipping"
    CLEANING = "cleaning"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    ROLLED_BACK = "rolled_back"
    ABANDONED = "abandoned"

class StateTransition:
    """Valid state transitions"""

    TRANSITIONS = {
        WorkflowState.PENDING: [WorkflowState.PLANNING, WorkflowState.FAILED],
        WorkflowState.PLANNING: [WorkflowState.BUILDING, WorkflowState.FAILED],
        WorkflowState.BUILDING: [WorkflowState.LINTING, WorkflowState.FAILED],
        WorkflowState.LINTING: [WorkflowState.TESTING, WorkflowState.FAILED],
        WorkflowState.TESTING: [WorkflowState.REVIEWING, WorkflowState.FAILED],
        WorkflowState.REVIEWING: [WorkflowState.DOCUMENTING, WorkflowState.FAILED],
        WorkflowState.DOCUMENTING: [WorkflowState.SHIPPING, WorkflowState.FAILED],
        WorkflowState.SHIPPING: [WorkflowState.CLEANING, WorkflowState.FAILED],
        WorkflowState.CLEANING: [WorkflowState.COMPLETED, WorkflowState.FAILED],
        WorkflowState.FAILED: [WorkflowState.PLANNING, WorkflowState.ROLLED_BACK],  # Can retry
        WorkflowState.PAUSED: [WorkflowState.PLANNING],  # Resume from last phase
    }

    @classmethod
    def can_transition(cls, from_state: WorkflowState, to_state: WorkflowState) -> bool:
        """Check if transition is valid"""
        return to_state in cls.TRANSITIONS.get(from_state, [])

class WorkflowStateMachine:
    """Manages workflow state with validation"""

    def __init__(self, adw_id: str):
        self.adw_id = adw_id
        self.current_state = WorkflowState.PENDING
        self.retry_count = 0
        self.max_retries = 3
        self.state_history = []

    def transition(self, new_state: WorkflowState, metadata: Optional[Dict] = None):
        """Transition to new state with validation"""

        if not StateTransition.can_transition(self.current_state, new_state):
            raise ValueError(
                f"Invalid transition: {self.current_state.value} -> {new_state.value}"
            )

        # Record transition
        self.state_history.append({
            "from": self.current_state.value,
            "to": new_state.value,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })

        # Update state
        self.current_state = new_state

        # Reset retry count on success
        if new_state not in [WorkflowState.FAILED, WorkflowState.PAUSED]:
            self.retry_count = 0

    def can_retry(self) -> bool:
        """Check if workflow can be retried"""
        return (
            self.current_state == WorkflowState.FAILED and
            self.retry_count < self.max_retries
        )

    def mark_retry(self):
        """Mark a retry attempt"""
        if not self.can_retry():
            raise ValueError("Cannot retry - max retries exceeded")
        self.retry_count += 1
```

**Acceptance Criteria:**
- State transitions validated before execution
- Invalid transitions raise exceptions
- State history tracked for debugging
- Retry logic built into state machine

---

### Component 2.1.2: Atomic State Persistence

**File:** `adws/adw_modules/atomic_state.py`

**Implementation:**
```python
"""
Atomic file operations for state persistence.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

class AtomicStateWriter:
    """Write state files atomically to prevent corruption"""

    @staticmethod
    def write(state_path: str, state_data: Dict[str, Any]):
        """
        Write state atomically using temp file + rename.
        This prevents corruption if process crashes during write.
        """

        state_path = Path(state_path)
        state_path.parent.mkdir(parents=True, exist_ok=True)

        # Create temp file in same directory
        temp_fd, temp_path = tempfile.mkstemp(
            dir=state_path.parent,
            prefix=".tmp_state_",
            suffix=".json"
        )

        try:
            # Write to temp file
            with os.fdopen(temp_fd, 'w') as f:
                json.dump(state_data, f, indent=2)

            # Atomic rename (POSIX guarantee)
            os.rename(temp_path, state_path)

        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise e

    @staticmethod
    def read(state_path: str) -> Dict[str, Any]:
        """Read state with validation"""

        if not os.path.exists(state_path):
            raise FileNotFoundError(f"State file not found: {state_path}")

        with open(state_path, 'r') as f:
            state_data = json.load(f)

        # Validate required fields
        required_fields = ["adw_id", "issue_number", "state_version"]
        missing = [f for f in required_fields if f not in state_data]

        if missing:
            raise ValueError(f"State missing required fields: {missing}")

        return state_data
```

**Acceptance Criteria:**
- State writes are atomic (no partial writes)
- Temp files cleaned up on error
- State reads validate required fields
- Crashes during write don't corrupt state

---

### Component 2.1.3: State Schema Versioning

**File:** `adws/adw_modules/state_schema.py`

**Implementation:**
```python
"""
State schema versioning and migrations.
"""

from typing import Dict, Any, Callable

class StateSchema:
    """Current state schema version"""

    CURRENT_VERSION = "2.0"

    @staticmethod
    def get_schema_v2() -> Dict[str, Any]:
        """Version 2.0 schema (with state machine)"""
        return {
            "state_version": "2.0",
            "adw_id": str,
            "issue_number": int,
            "current_state": str,  # WorkflowState enum value
            "retry_count": int,
            "state_history": list,
            "branch_name": str,
            "plan_file": str,
            "worktree_path": str,
            "backend_port": int,
            "frontend_port": int,
            "created_at": str,
            "updated_at": str,
        }

class StateMigration:
    """Migrate state files between versions"""

    MIGRATIONS: Dict[str, Callable] = {}

    @classmethod
    def register_migration(cls, from_version: str, to_version: str):
        """Decorator to register migration"""
        def decorator(func: Callable):
            cls.MIGRATIONS[f"{from_version}->{to_version}"] = func
            return func
        return decorator

    @classmethod
    def migrate(cls, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate state to current version"""

        current_version = state_data.get("state_version", "1.0")
        target_version = StateSchema.CURRENT_VERSION

        if current_version == target_version:
            return state_data  # Already current

        # Find migration path
        migration_key = f"{current_version}->{target_version}"
        migration_func = cls.MIGRATIONS.get(migration_key)

        if not migration_func:
            raise ValueError(
                f"No migration path from {current_version} to {target_version}"
            )

        # Apply migration
        migrated_data = migration_func(state_data)
        migrated_data["state_version"] = target_version

        return migrated_data

# Example migration
@StateMigration.register_migration("1.0", "2.0")
def migrate_v1_to_v2(state_data: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate from v1.0 (simple status) to v2.0 (state machine)"""

    # Map old status to new states
    status_mapping = {
        "running": "planning",  # Conservative default
        "completed": "completed",
        "failed": "failed",
    }

    old_status = state_data.get("status", "running")
    new_state = status_mapping.get(old_status, "planning")

    # Add new fields
    state_data["current_state"] = new_state
    state_data["retry_count"] = 0
    state_data["state_history"] = [{
        "from": "pending",
        "to": new_state,
        "timestamp": state_data.get("created_at", ""),
        "metadata": {"source": "v1_migration"}
    }]

    return state_data
```

**Acceptance Criteria:**
- Schema version tracked in state files
- Migrations registered and discoverable
- Old state files automatically migrated on read
- Migration failures clearly reported

---

## 2.2 Error Recovery & Rollback Mechanism

### Objective
Add comprehensive error handling and rollback capabilities to prevent orphaned resources.

---

### Component 2.2.1: Error Classification System

**File:** `adws/adw_modules/error_handler.py`

**Implementation:**
```python
"""
Error classification and retry strategy.
"""

from enum import Enum
from typing import Optional, Dict, Any
import traceback

class ErrorCategory(Enum):
    """Error categories for appropriate handling"""
    TRANSIENT = "transient"  # Retry immediately
    RATE_LIMIT = "rate_limit"  # Retry with backoff
    CONFIGURATION = "configuration"  # Don't retry, needs manual fix
    RESOURCE = "resource"  # Needs cleanup, then retry
    FATAL = "fatal"  # Don't retry, fail workflow

class WorkflowError(Exception):
    """Base class for workflow errors"""

    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        phase: str,
        recoverable: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.phase = phase
        self.recoverable = recoverable
        self.metadata = metadata or {}
        self.traceback = traceback.format_exc()

class ErrorClassifier:
    """Classify errors to determine handling strategy"""

    @staticmethod
    def classify(exception: Exception, phase: str) -> WorkflowError:
        """Classify exception and return WorkflowError"""

        error_message = str(exception)

        # API rate limiting
        if "rate limit" in error_message.lower():
            return WorkflowError(
                message=error_message,
                category=ErrorCategory.RATE_LIMIT,
                phase=phase,
                recoverable=True,
                metadata={"retry_delay": 60}
            )

        # Resource conflicts (ports, disk space)
        if any(x in error_message.lower() for x in ["port", "disk", "space"]):
            return WorkflowError(
                message=error_message,
                category=ErrorCategory.RESOURCE,
                phase=phase,
                recoverable=True,
                metadata={"requires_cleanup": True}
            )

        # Configuration errors
        if any(x in error_message.lower() for x in ["config", "not found", "missing"]):
            return WorkflowError(
                message=error_message,
                category=ErrorCategory.CONFIGURATION,
                phase=phase,
                recoverable=False,
                metadata={"requires_manual_intervention": True}
            )

        # Network/API transient errors
        if any(x in error_message.lower() for x in ["timeout", "connection", "network"]):
            return WorkflowError(
                message=error_message,
                category=ErrorCategory.TRANSIENT,
                phase=phase,
                recoverable=True,
                metadata={"retry_delay": 5}
            )

        # Default to fatal
        return WorkflowError(
            message=error_message,
            category=ErrorCategory.FATAL,
            phase=phase,
            recoverable=False
        )
```

**Acceptance Criteria:**
- All exceptions classified by category
- Retry strategy determined by category
- Error metadata captured for debugging
- Traceback preserved for analysis

---

### Component 2.2.2: Rollback Mechanism

**File:** `adws/adw_modules/rollback.py`

**Implementation:**
```python
"""
Rollback mechanism for failed workflows.
"""

import os
import subprocess
import shutil
from typing import Optional
from adws.adw_modules.state import ADWState
from adws.adw_modules.github import close_pull_request, post_github_comment

class WorkflowRollback:
    """Rollback workflow to clean state"""

    def __init__(self, adw_id: str, logger):
        self.adw_id = adw_id
        self.logger = logger
        self.state = ADWState.load(adw_id, logger)

    def rollback(self, reason: str):
        """Perform complete rollback"""

        self.logger.info(f"Starting rollback for {self.adw_id}: {reason}")

        # Track what was rolled back
        rollback_actions = []

        # 1. Close PR if created
        if self.state.get("pr_number"):
            try:
                self._close_pr(reason)
                rollback_actions.append("PR closed")
            except Exception as e:
                self.logger.error(f"Failed to close PR: {e}")

        # 2. Delete branch if created
        if self.state.get("branch_name"):
            try:
                self._delete_branch()
                rollback_actions.append("Branch deleted")
            except Exception as e:
                self.logger.error(f"Failed to delete branch: {e}")

        # 3. Remove worktree if exists
        if self.state.get("worktree_path"):
            try:
                self._remove_worktree()
                rollback_actions.append("Worktree removed")
            except Exception as e:
                self.logger.error(f"Failed to remove worktree: {e}")

        # 4. Free allocated ports
        if self.state.get("backend_port") or self.state.get("frontend_port"):
            try:
                self._free_ports()
                rollback_actions.append("Ports freed")
            except Exception as e:
                self.logger.error(f"Failed to free ports: {e}")

        # 5. Clean up external process directories
        try:
            self._cleanup_external_processes()
            rollback_actions.append("External processes cleaned")
        except Exception as e:
            self.logger.error(f"Failed to cleanup external processes: {e}")

        # 6. Post GitHub comment about rollback
        if self.state.get("issue_number"):
            self._post_rollback_comment(reason, rollback_actions)

        # 7. Update database state
        self._update_database_state(reason)

        self.logger.info(f"Rollback complete: {', '.join(rollback_actions)}")

    def _close_pr(self, reason: str):
        """Close pull request with explanation"""
        pr_number = self.state.get("pr_number")
        close_pull_request(
            pr_number=pr_number,
            comment=f"Closing PR due to workflow rollback: {reason}"
        )

    def _delete_branch(self):
        """Delete the workflow branch"""
        branch_name = self.state.get("branch_name")

        # Delete local branch
        subprocess.run(
            ["git", "branch", "-D", branch_name],
            capture_output=True,
            check=False  # Don't fail if branch doesn't exist
        )

        # Delete remote branch
        subprocess.run(
            ["git", "push", "origin", "--delete", branch_name],
            capture_output=True,
            check=False
        )

    def _remove_worktree(self):
        """Remove git worktree"""
        worktree_path = self.state.get("worktree_path")

        if os.path.exists(worktree_path):
            # Remove worktree
            subprocess.run(
                ["git", "worktree", "remove", worktree_path, "--force"],
                capture_output=True,
                check=False
            )

            # Prune worktree references
            subprocess.run(
                ["git", "worktree", "prune"],
                capture_output=True
            )

    def _free_ports(self):
        """Kill processes on allocated ports"""
        backend_port = self.state.get("backend_port")
        frontend_port = self.state.get("frontend_port")

        for port in [backend_port, frontend_port]:
            if port:
                subprocess.run(
                    ["lsof", "-ti", f":{port}"],
                    capture_output=True,
                    text=True
                ).stdout.strip()

                if pids:
                    subprocess.run(
                        ["kill", "-9"] + pids.split('\n'),
                        capture_output=True,
                        check=False
                    )

    def _cleanup_external_processes(self):
        """Remove external process directories"""
        external_dirs = [
            f"adw_test_external_{self.adw_id}",
            f"adw_build_external_{self.adw_id}"
        ]

        for dir_name in external_dirs:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)

    def _post_rollback_comment(self, reason: str, actions: list):
        """Post GitHub comment about rollback"""
        issue_number = self.state.get("issue_number")

        comment = f"""
## Workflow Rolled Back

**Reason:** {reason}

**Actions Taken:**
{chr(10).join(f'- {action}' for action in actions)}

The workflow has been safely rolled back. Please review the error and retry if appropriate.
"""

        post_github_comment(issue_number, comment)

    def _update_database_state(self, reason: str):
        """Update database to reflect rollback"""
        from app.server.core.workflow_history import mark_workflow_rolled_back

        mark_workflow_rolled_back(
            adw_id=self.adw_id,
            error_message=reason
        )
```

**Acceptance Criteria:**
- All resources cleaned up on rollback
- PRs closed with explanation
- Branches deleted (local and remote)
- Ports freed
- Worktrees removed
- Database updated
- GitHub comment posted

---

### Component 2.2.3: Retry Logic with Exponential Backoff

**File:** `adws/adw_modules/retry_handler.py`

**Implementation:**
```python
"""
Retry logic with exponential backoff.
"""

import time
from typing import Callable, Any
from adws.adw_modules.error_handler import WorkflowError, ErrorCategory

class RetryStrategy:
    """Retry strategy with exponential backoff"""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    def execute_with_retry(
        self,
        func: Callable,
        phase: str,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with retry logic"""

        attempt = 0
        last_error = None

        while attempt < self.max_retries:
            try:
                return func(*args, **kwargs)

            except Exception as e:
                # Classify error
                workflow_error = ErrorClassifier.classify(e, phase)
                last_error = workflow_error

                # Check if recoverable
                if not workflow_error.recoverable:
                    raise workflow_error

                # Determine delay
                delay = self._calculate_delay(
                    attempt,
                    workflow_error.category
                )

                attempt += 1

                if attempt < self.max_retries:
                    logger.warning(
                        f"Attempt {attempt} failed ({workflow_error.category.value}). "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Max retries ({self.max_retries}) exceeded")
                    raise workflow_error

        # Should never reach here, but just in case
        raise last_error

    def _calculate_delay(self, attempt: int, category: ErrorCategory) -> float:
        """Calculate delay based on attempt and error category"""

        if category == ErrorCategory.RATE_LIMIT:
            # Longer delays for rate limiting
            return min(self.base_delay * (3 ** attempt), 300)  # Max 5 minutes

        elif category == ErrorCategory.TRANSIENT:
            # Shorter delays for transient errors
            return self.base_delay * (2 ** attempt)  # Exponential

        elif category == ErrorCategory.RESOURCE:
            # Medium delays for resource conflicts
            return self.base_delay * (2 ** attempt) * 2

        else:
            # Default exponential backoff
            return self.base_delay * (2 ** attempt)
```

**Acceptance Criteria:**
- Automatic retry for recoverable errors
- Exponential backoff prevents API hammering
- Different strategies for different error types
- Max retries enforced
- Non-recoverable errors fail immediately

---

## 2.3 Concurrency & Resource Management

### Component 2.3.1: Fix Lock Bypass Vulnerability

**File:** `adws/adw_triggers/trigger_webhook.py`

**Fix:**
```python
# Lines 293-318 - Fix lock bypass for continuing workflows

def handle_webhook_trigger(issue_number: int, provided_adw_id: Optional[str] = None):
    """Handle webhook trigger with proper locking"""

    if not provided_adw_id:
        # NEW workflow - create lock
        adw_id = make_adw_id()
        lock_acquired = acquire_lock(issue_number, adw_id)

        if not lock_acquired:
            post_github_comment(
                issue_number,
                "⚠️ Another workflow is already running for this issue"
            )
            return
    else:
        # CONTINUING workflow - verify lock ownership
        adw_id = provided_adw_id

        # FIX: Check that this ADW owns the lock
        if not verify_lock_ownership(issue_number, adw_id):
            post_github_comment(
                issue_number,
                f"⚠️ Workflow {adw_id} does not own the lock for this issue"
            )
            return

    # Proceed with workflow
    try:
        start_workflow(issue_number, adw_id)
    finally:
        # Release lock when done
        release_lock(issue_number, adw_id)

def verify_lock_ownership(issue_number: int, adw_id: str) -> bool:
    """Verify that ADW owns the lock for this issue"""

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT adw_id FROM adw_locks
            WHERE issue_number = ? AND adw_id = ?
        """, (issue_number, adw_id))

        return cursor.fetchone() is not None
```

**Acceptance Criteria:**
- Continuing workflows verify lock ownership
- Cannot bypass locks
- Race conditions prevented
- Locks released on workflow completion

---

### Component 2.3.2: Resource Quota Management

**File:** `adws/adw_modules/resource_manager.py`

**Implementation:**
```python
"""
Resource quota management (disk, memory, API costs).
"""

import shutil
import psutil
from typing import Optional, Dict

class ResourceQuota:
    """Resource quota enforcement"""

    # Default quotas
    MAX_WORKTREES = 15
    MAX_DISK_PER_WORKTREE_GB = 5
    MAX_API_COST_PER_WORKFLOW = 10.0
    MIN_FREE_DISK_GB = 10

    @classmethod
    def check_disk_space(cls) -> bool:
        """Check if enough disk space available"""

        usage = shutil.disk_usage("/")
        free_gb = usage.free / (1024 ** 3)

        return free_gb >= cls.MIN_FREE_DISK_GB

    @classmethod
    def check_worktree_count(cls) -> bool:
        """Check if under worktree limit"""

        import os
        trees_dir = "trees"

        if not os.path.exists(trees_dir):
            return True

        worktree_count = len([
            d for d in os.listdir(trees_dir)
            if os.path.isdir(os.path.join(trees_dir, d))
        ])

        return worktree_count < cls.MAX_WORKTREES

    @classmethod
    def check_api_budget(cls, estimated_cost: float) -> bool:
        """Check if workflow within API budget"""

        return estimated_cost <= cls.MAX_API_COST_PER_WORKFLOW

    @classmethod
    def enforce_quotas(cls, estimated_cost: Optional[float] = None) -> Dict[str, bool]:
        """Enforce all resource quotas"""

        checks = {
            "disk_space": cls.check_disk_space(),
            "worktree_count": cls.check_worktree_count(),
        }

        if estimated_cost is not None:
            checks["api_budget"] = cls.check_api_budget(estimated_cost)

        return checks
```

**Acceptance Criteria:**
- Disk space checked before workflow start
- Worktree limit enforced
- API budget validated
- Clear error messages when quotas exceeded

---

## 2.4 Observability & Monitoring

### Component 2.4.1: Structured Logging

**File:** `adws/adw_modules/structured_logger.py`

**Implementation:**
```python
"""
Structured logging for ADW workflows.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

class StructuredLogger:
    """JSON-formatted structured logging"""

    def __init__(self, adw_id: str, phase: str):
        self.adw_id = adw_id
        self.phase = phase
        self.logger = logging.getLogger(f"adw.{adw_id}.{phase}")

    def log(
        self,
        level: str,
        message: str,
        **kwargs
    ):
        """Log structured message"""

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "adw_id": self.adw_id,
            "phase": self.phase,
            "level": level,
            "message": message,
            **kwargs
        }

        # Log as JSON
        log_line = json.dumps(log_entry)

        if level == "ERROR":
            self.logger.error(log_line)
        elif level == "WARNING":
            self.logger.warning(log_line)
        elif level == "INFO":
            self.logger.info(log_line)
        else:
            self.logger.debug(log_line)

    def info(self, message: str, **kwargs):
        self.log("INFO", message, **kwargs)

    def error(self, message: str, **kwargs):
        self.log("ERROR", message, **kwargs)

    def warning(self, message: str, **kwargs):
        self.log("WARNING", message, **kwargs)
```

---

## Success Metrics

### Phase 2 Complete When:
- [ ] State machine implemented and tested
- [ ] Rollback mechanism works for all phases
- [ ] Retry logic handles transient failures
- [ ] Lock bypass vulnerability fixed
- [ ] Resource quotas enforced
- [ ] Structured logging operational
- [ ] >80% workflow success rate achieved
- [ ] All 22 NL_REQUESTS.md workflows complete
- [ ] Zero orphaned resources
- [ ] Full observability dashboard

---

## Timeline

**Week 1:** State management + error recovery
**Week 2:** Concurrency + resource management
**Week 3:** Observability + testing + validation

For detailed week-by-week breakdown, see `implementation_roadmap.md`.
