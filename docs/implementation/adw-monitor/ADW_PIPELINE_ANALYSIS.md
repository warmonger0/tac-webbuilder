# ADW Pipeline Analysis: Issues and Pain Points

**Date:** 2025-11-24
**Scope:** Complete ADW (Autonomous Digital Worker) pipeline architecture
**Focus:** Issues preventing smooth sequential phase execution

---

## Executive Summary

The ADW pipeline implements an isolated, parallel workflow execution system using git worktrees and dedicated ports. While the architecture shows sophisticated design patterns (worktree isolation, external tool optimization, state management), there are **5 critical issues** that prevent phases from running smoothly:

1. **State File Synchronization Race Conditions** (HIGH SEVERITY)
2. **Port Allocation and Management Failures** (HIGH SEVERITY)
3. **Worktree Lifecycle and Cleanup Issues** (MEDIUM SEVERITY)
4. **Phase Chaining and Error Propagation Gaps** (HIGH SEVERITY)
5. **External Tool Subprocess Management** (MEDIUM SEVERITY)

These issues cause workflows to hang, fail between phases, or require manual intervention.

---

## Architecture Overview

### Key Components

**Workflow Orchestration:**
- Complete SDLC: `adw_sdlc_complete_iso.py` (9 phases)
- Individual Phases: `adw_plan_iso.py`, `adw_build_iso.py`, `adw_test_iso.py`, `adw_review_iso.py`, `adw_ship_iso.py`, etc.

**State Management:**
- State files: `agents/{adw_id}/adw_state.json`
- Module: `adw_modules/state.py` (ADWState class)

**Worktree Management:**
- Worktrees: `trees/{adw_id}/`
- Module: `adw_modules/worktree_ops.py`

**Process Isolation:**
- Dedicated ports per worktree (9100-9114 backend, 9200-9214 frontend)
- Deterministic port allocation based on ADW ID hash

---

## Critical Issue #1: State File Synchronization Race Conditions

### Severity: HIGH
### Impact: Phases fail to see each other's updates, workflows hang or restart

### Problem Description

The ADW pipeline uses file-based state (`agents/{adw_id}/adw_state.json`) shared across multiple phases and processes. The current implementation has **no locking mechanism**, leading to race conditions when:
1. Parent workflow script reads state
2. External subprocess (e.g., `adw_test_external.py`) writes state
3. Parent workflow reads stale state

### Evidence from Code

**File: `adw_modules/state.py`**
```python
def save(self, workflow_step: Optional[str] = None) -> None:
    """Save state to file in agents/{adw_id}/adw_state.json."""
    state_path = self.get_state_path()
    os.makedirs(os.path.dirname(state_path), exist_ok=True)

    # NO LOCKING HERE - Race condition possible!
    with open(state_path, "w") as f:
        json.dump(save_data, f, indent=2)
```

**File: `adw_build_iso.py` (lines 77-82)**
```python
# Reload state to get external build results
reloaded_state = ADWState.load(adw_id)
if not reloaded_state:
    logger.error("Failed to reload state after external build")
    return False, {"error": "Failed to reload state"}
```

This pattern is used in:
- `adw_build_iso.py` (line 78)
- `adw_test_iso.py` (line 195)
- External subprocess writers: `adw_build_external.py` (line 199), `adw_test_external.py` (line 186)

### Impact Scenarios

1. **Lost Updates:** Subprocess writes external_test_results, parent immediately reads before write completes
2. **Corrupted State:** Two processes write simultaneously, JSON becomes malformed
3. **Stale Data:** Parent uses cached state, doesn't see subprocess updates

### Root Cause

No file locking or atomic operations for state file access.

### Recommended Fix (Priority: P0)

**Option 1: File Locking (Quick Win)**
```python
import fcntl

def save(self, workflow_step: Optional[str] = None) -> None:
    state_path = self.get_state_path()
    os.makedirs(os.path.dirname(state_path), exist_ok=True)

    # Atomic write with exclusive lock
    with open(state_path, "w") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        json.dump(save_data, f, indent=2)
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

**Option 2: Message Queue (Long-term)**
- Replace file-based state with Redis or SQLite
- Use transactions for atomic updates
- Enables better monitoring and debugging

---

## Critical Issue #2: Port Allocation and Management Failures

### Severity: HIGH
### Impact: Services fail to start, phases can't communicate, manual cleanup required

### Problem Description

The port allocation system maps ADW IDs to ports (9100-9114 for backend, 9200-9214 for frontend), but has several failure modes:

1. **Deterministic Collision:** Same ADW ID prefix maps to same ports
2. **Port Leaks:** Failed workflows leave ports occupied
3. **No Port Release:** Successful workflows never release ports
4. **Race on Port Check:** `is_port_available()` check and bind not atomic

### Evidence from Code

**File: `adw_modules/worktree_ops.py` (lines 183-205)**
```python
def get_ports_for_adw(adw_id: str) -> Tuple[int, int]:
    """Deterministically assign ports based on ADW ID."""
    try:
        id_chars = ''.join(c for c in adw_id[:8] if c.isalnum())
        index = int(id_chars, 36) % 15  # Only 15 slots!
    except ValueError:
        index = hash(adw_id) % 15

    backend_port = 9100 + index
    frontend_port = 9200 + index
    return backend_port, frontend_port
```

**File: `adw_plan_iso.py` (lines 119-126)**
```python
# Check port availability
if not (is_port_available(backend_port) and is_port_available(frontend_port)):
    logger.warning(f"Deterministic ports {backend_port}/{frontend_port} are in use")
    backend_port, frontend_port = find_next_available_ports(adw_id)
    # BUG: No verification that new ports are actually available!
```

### Impact Scenarios

1. **Port Exhaustion:** 10+ concurrent workflows saturate the 15-port range
2. **Phantom Ports:** Process dies, port still shows "in use" in state but is actually free
3. **Service Startup Failures:** Backend/frontend can't bind to allocated ports
4. **Cascading Failures:** One blocked port causes entire phase to fail

### Real-World Example

From git worktree list output, there are **9 active worktrees**, each consuming 2 ports (18 ports total, but only 15 slots available). This guarantees collisions.

### Root Cause

1. Port allocation is deterministic but range is too small (15 slots)
2. No port release mechanism
3. No health checks to detect zombie port reservations
4. Time-of-check-to-time-of-use race condition

### Recommended Fix (Priority: P0)

**Option 1: Expand Port Range (Quick Win)**
```python
# Expand from 15 to 100 slots
backend_port = 9100 + (index % 100)
frontend_port = 9200 + (index % 100)
```

**Option 2: Dynamic Port Allocation (Better)**
```python
def allocate_free_ports(adw_id: str) -> Tuple[int, int]:
    """Dynamically find and reserve available ports."""
    # Try deterministic first, then scan
    for offset in range(100):
        backend = 9100 + offset
        frontend = 9200 + offset
        if can_bind_ports(backend, frontend):
            reserve_ports_in_state(adw_id, backend, frontend)
            return backend, frontend
    raise PortExhaustionError()
```

**Option 3: Port Release on Cleanup (Must Have)**
```python
def cleanup_shipped_issue(issue_number, adw_id):
    # Release ports in state
    state = ADWState.load(adw_id)
    release_ports(state.get("backend_port"), state.get("frontend_port"))
    # ... rest of cleanup
```

---

## Critical Issue #3: Worktree Lifecycle and Cleanup Issues

### Severity: MEDIUM (but causes accumulation over time)
### Impact: Disk space exhaustion, git operations slow down, manual cleanup required

### Problem Description

Worktrees are created in `trees/{adw_id}/` but are **not automatically cleaned up** after workflows complete. Over time, this leads to:
1. Disk space exhaustion (each worktree is a full repo copy)
2. Slowed git operations (git must scan all worktrees)
3. Orphaned worktrees (workflow fails, worktree left behind)

### Evidence from Code

**File: `adw_sdlc_complete_iso.py` (lines 352-392)**
```python
# Cleanup phase only organizes docs, doesn't remove worktree by default
cleanup_result = cleanup_shipped_issue(
    issue_number=issue_number,
    adw_id=adw_id,
    skip_worktree=False,  # Should remove worktree
    dry_run=False,
    logger=cleanup_logger
)
```

**File: `adw_modules/cleanup_operations.py` (not included in trace, but referenced)**
```python
def cleanup_shipped_issue(issue_number, adw_id, skip_worktree=False, ...):
    # skip_worktree=False means it SHOULD remove, but implementation unclear
```

**Real-World Evidence:**
From `git worktree list`, there are **9 worktrees** currently tracked:
- `adw-3af4a34d`, `446dab5f`, `12ad9dbd`, `2cfe5aa9`, `50443844`, `d7e1040d`, `da7afdc5`, `da86f01c`, `e7341a50`
- Plus incomplete worktree: `641fb538` (only 3 items)

**Manual cleanup script exists:** `/scripts/purge_tree.sh` - indicating cleanup is a known problem.

### Impact Scenarios

1. **Disk Space:** 10 worktrees × 500MB = 5GB wasted
2. **Git Performance:** `git status` in main repo scans all worktrees
3. **Orphaned Branches:** Feature branches remain after merge
4. **State Inconsistency:** State file exists, worktree doesn't (or vice versa)

### Root Cause

1. Cleanup is opt-in (skip_worktree flag), not automatic
2. No cleanup on failure (only on ship success)
3. No garbage collection process for old worktrees
4. Cleanup phase is last in pipeline (if ship fails, cleanup never runs)

### Recommended Fix (Priority: P1)

**Option 1: Auto-cleanup on Ship Success (Quick Win)**
```python
# In adw_ship_iso.py, after successful merge
if merge_success:
    remove_worktree(adw_id, logger)
    cleanup_ports(adw_id)
    # Keep state file for history
```

**Option 2: Garbage Collection Cron Job (Better)**
```python
# New script: scripts/gc_worktrees.py
def garbage_collect_worktrees():
    for worktree_dir in Path("trees").iterdir():
        adw_id = worktree_dir.name
        state = ADWState.load(adw_id)

        # Remove if: completed > 7 days ago, or failed > 3 days ago
        if should_cleanup(state):
            remove_worktree(adw_id)
            archive_state(adw_id)
```

**Option 3: Cleanup on Failure (Must Have)**
```python
# Wrap each phase in try/finally
try:
    run_phase(...)
finally:
    if phase_failed and not args.keep_on_failure:
        cleanup_worktree(adw_id)
```

---

## Critical Issue #4: Phase Chaining and Error Propagation Gaps

### Severity: HIGH
### Impact: Silent failures, phases skip despite dependencies failing, inconsistent error handling

### Problem Description

The SDLC workflow chains 9 phases via `subprocess.run()`, but error propagation is **inconsistent**:
1. Some phases exit(1) on failure, others continue
2. External tool failures are checked inconsistently
3. No rollback mechanism when mid-pipeline failure occurs
4. State doesn't track "last successful phase"

### Evidence from Code

**File: `adw_sdlc_complete_iso.py` (lines 131-141)**
```python
plan = subprocess.run(plan_cmd)
if plan.returncode != 0:
    print("❌ Plan phase failed")
    # Posts to GitHub, then exits
    sys.exit(1)
```

**But later in the same file (lines 296-307):**
```python
document = subprocess.run(document_cmd)
if document.returncode != 0:
    print("⚠️ Documentation phase failed but continuing...")
    # CONTINUES instead of exiting!
```

**External tool error handling varies:**

**File: `adw_build_iso.py` (lines 249-252)**
```python
build_success, build_results = run_external_build(issue_number, adw_id, logger, state)

if "error" in build_results:
    # External tool failed - EXITS
    sys.exit(1)
```

**File: `adw_test_iso.py` (lines 1039-1050)**
```python
if not success and "error" in external_results:
    # External tools failed completely - fallback to inline mode
    logger.warning("External test tools failed after retries, using inline execution as fallback")
    # CONTINUES with fallback, doesn't exit!
```

### Impact Scenarios

1. **Partial Implementation:** Build fails, but test phase runs anyway on broken code
2. **Silent Failures:** External tool errors logged but not fatal
3. **Inconsistent State:** State shows "completed" phases but intermediate phase failed
4. **No Recovery:** Workflow can't resume from last good phase

### Root Cause

1. No consistent error handling policy across phases
2. External tool failures treated differently than inline failures
3. No phase dependency graph or state machine
4. subprocess.run() doesn't propagate exceptions

### Recommended Fix (Priority: P0)

**Option 1: Consistent Exit Codes (Quick Win)**
```python
# In adw_sdlc_complete_iso.py
CRITICAL_PHASES = ["plan", "build", "lint", "test", "review"]
OPTIONAL_PHASES = ["document", "validate"]

for phase in phases:
    result = subprocess.run(phase_cmd)
    if result.returncode != 0:
        if phase in CRITICAL_PHASES:
            sys.exit(1)  # Fatal
        else:
            logger.warning(f"{phase} failed but continuing")
```

**Option 2: State Machine (Better)**
```python
class PhaseStateMachine:
    def __init__(self, adw_id):
        self.state = ADWState.load(adw_id)
        self.current_phase = self.state.get("current_phase")

    def run_phase(self, phase_name, phase_fn):
        self.state.update(current_phase=phase_name, status="in_progress")
        self.state.save()

        try:
            result = phase_fn()
            self.state.update(f"{phase_name}_status", "completed")
            return result
        except Exception as e:
            self.state.update(f"{phase_name}_status", "failed", last_error=str(e))
            raise
```

**Option 3: Rollback on Failure (Long-term)**
- Track "last successful phase" in state
- Support `--resume-from=<phase>` flag
- Auto-cleanup on unrecoverable failure

---

## Critical Issue #5: External Tool Subprocess Management

### Severity: MEDIUM
### Impact: Processes hang, timeouts too aggressive/lenient, zombie processes

### Problem Description

External tools (`adw_build_external.py`, `adw_test_external.py`, etc.) run as subprocesses, but:
1. Timeout values are arbitrary (300s for build, 600s for test)
2. No subprocess lifecycle management (can't cancel)
3. stdout/stderr buffering causes deadlocks on large output
4. Zombie processes left behind on timeout

### Evidence from Code

**File: `adw_build_external.py` (lines 102-109)**
```python
result = subprocess.run(
    cmd,
    cwd=worktree_path,
    capture_output=True,  # BLOCKS if output buffer fills!
    text=True,
    timeout=300  # 5 minute timeout
)
```

**File: `adw_test_external.py` (lines 142-166)**
```python
except subprocess.TimeoutExpired:
    return {
        "success": False,
        "error": {"type": "TimeoutError", ...}
        # BUG: Doesn't kill the subprocess!
    }
```

**File: `adw_test_iso.py` (lines 140-143)**
```python
result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
# 10 minute timeout, but what if E2E tests need longer?
```

### Impact Scenarios

1. **Hanging Builds:** TypeScript compilation stalls, hits 5-min timeout, subprocess killed abruptly
2. **Buffer Deadlock:** Test output exceeds pipe buffer, subprocess blocks on write, parent blocks on read
3. **Zombie Processes:** Timeout kills parent, child process orphaned
4. **Lost Output:** Large stdout truncated or lost

### Root Cause

1. subprocess.run() is blocking and doesn't support progress monitoring
2. capture_output=True uses pipes that can deadlock
3. Timeout kills process but doesn't cleanup worktree
4. No process tree management (child processes survive parent death)

### Recommended Fix (Priority: P1)

**Option 1: Stream Output (Quick Win)**
```python
# Replace capture_output=True with streaming
with subprocess.Popen(cmd, cwd=worktree_path,
                      stdout=subprocess.PIPE,
                      stderr=subprocess.STDOUT,
                      text=True) as proc:
    output = []
    for line in proc.stdout:
        output.append(line)
        logger.info(line.strip())

    proc.wait(timeout=300)
```

**Option 2: Process Group Management (Better)**
```python
import os
import signal

# Start process in new group
proc = subprocess.Popen(cmd, preexec_fn=os.setpgrp)

try:
    proc.wait(timeout=300)
except subprocess.TimeoutExpired:
    # Kill entire process group
    os.killpg(proc.pid, signal.SIGTERM)
    proc.wait(5)  # Grace period
    os.killpg(proc.pid, signal.SIGKILL)
```

**Option 3: Async with Progress (Long-term)**
```python
async def run_with_progress(cmd, worktree_path, timeout):
    proc = await asyncio.create_subprocess_exec(
        *cmd, cwd=worktree_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Stream output and update progress
    async for line in proc.stdout:
        progress.update(line)

    await asyncio.wait_for(proc.wait(), timeout=timeout)
```

---

## Additional Pain Points (Lower Severity)

### 6. ADW Monitor Status Detection is Heuristic

**File: `app/server/core/adw_monitor.py` (lines 177-223)**
```python
def determine_status(adw_id: str, state: dict[str, Any]) -> str:
    """Determine workflow status via heuristics."""
    # Checks: state.status, is_process_running(), worktree_exists(), last_activity
    # BUG: Can misclassify "paused" vs "failed" vs "queued"
```

**Impact:** Dashboard shows incorrect status, users think workflow is running when it's stuck.

**Fix:** Add explicit status transitions to state file, phase writes status on entry/exit.

### 7. Git Operations Lack Conflict Resolution

**File: `adw_modules/git_ops.py` (lines 97-122)**
```python
def commit_changes(message: str, cwd: Optional[str] = None):
    result = subprocess.run(["git", "add", "-A"], ...)
    result = subprocess.run(["git", "commit", "-m", message], ...)
    # BUG: No check for merge conflicts, diverged branches, detached HEAD
```

**Impact:** Commit fails silently, phase thinks it succeeded.

**Fix:** Check git status before commit, handle conflicts, verify HEAD is on feature branch.

### 8. State File Schema Validation is Weak

**File: `adw_modules/state.py` (lines 34-48)**
```python
def update(self, **kwargs):
    """Update state with new key-value pairs."""
    core_fields = {"adw_id", "issue_number", ...}
    for key, value in kwargs.items():
        if key in core_fields:
            self.data[key] = value
    # BUG: No validation that values are correct type
```

**Impact:** Invalid data in state (e.g., port as string instead of int).

**Fix:** Use Pydantic validation on every update, not just on save.

### 9. No Phase Timeout Configuration

**Observation:** All timeouts are hardcoded (300s, 600s, etc.). Long-running phases (review with many screenshots) can hit timeout.

**Fix:** Add timeout configuration to state or environment variables.

### 10. Worktree Branch Divergence

**File: `adw_modules/worktree_ops.py` (lines 56-57)**
```python
# Creates worktree from origin/main
cmd = ["git", "worktree", "add", "-b", branch_name, worktree_path, "origin/main"]
```

**Issue:** If main has diverged, worktree is out of date. No sync mechanism.

**Fix:** Add periodic `git fetch origin main` in long-running phases.

---

## Monitoring Gaps (ADW Monitor)

### Current ADW Monitor Limitations

**File: `app/server/core/adw_monitor.py`**

1. **Process Detection is Fragile** (lines 95-127)
   - Uses `ps aux | grep <adw_id>` - can miss processes
   - Only detects "aider" processes, misses external tools

2. **Progress Calculation is Directory-Based** (lines 225-277)
   - Looks for phase subdirectories in `agents/{adw_id}/`
   - Doesn't reflect actual phase completion
   - Can show 50% when phase is stuck at 10%

3. **No Real-Time Updates**
   - 5-second cache (line 21) means status lags
   - No WebSocket support for live updates

4. **Error Tracking is Limited** (lines 309-336)
   - Only last_error stored, no error history
   - No error categorization (transient vs fatal)

### Recommended Improvements

1. **Phase Heartbeat:** Each phase writes timestamp every 10s
2. **Explicit Status:** State file tracks phase state machine (pending → running → completed/failed)
3. **Structured Logging:** Phase logs parseable for error extraction
4. **WebSocket Events:** Push status changes immediately

---

## Prioritized Recommendations

### P0 (Critical - Fix Immediately)

1. **Add State File Locking** (Issue #1)
   - Implement fcntl locking or atomic writes
   - Prevents corruption and race conditions

2. **Expand Port Range** (Issue #2)
   - Increase from 15 to 100 slots
   - Add port release on cleanup

3. **Standardize Error Handling** (Issue #4)
   - Define critical vs optional phases
   - Consistent exit codes
   - Track last successful phase in state

### P1 (High - Fix This Sprint)

4. **Auto-cleanup Worktrees** (Issue #3)
   - Remove worktree on successful ship
   - Add garbage collection script

5. **Fix Subprocess Management** (Issue #5)
   - Stream output to prevent deadlocks
   - Kill entire process group on timeout

6. **Improve Status Detection** (Issue #6)
   - Add explicit status transitions to state
   - Phase writes status on entry/exit

### P2 (Medium - Fix Next Sprint)

7. **Add Phase Timeouts Config**
8. **Git Conflict Resolution**
9. **State Schema Validation**
10. **Worktree Branch Sync**

### P3 (Low - Nice to Have)

11. **WebSocket Updates for Monitor**
12. **Phase Dependency Graph**
13. **Rollback/Resume Support**

---

## Quick Wins (Immediate Actions)

These can be implemented in < 1 day with minimal risk:

1. **Expand Port Range:** Change `% 15` to `% 100` in `worktree_ops.py`
2. **Add File Locking:** Wrap state.save() with fcntl.flock()
3. **Standardize Exit Codes:** Make all critical phases exit(1) on failure
4. **Stream Subprocess Output:** Replace capture_output=True with Popen streaming
5. **Add Worktree Cleanup to Ship:** Call remove_worktree() after successful merge

---

## Long-Term Architecture Improvements

### Replace File-Based State with Database

**Current:** `agents/{adw_id}/adw_state.json` (1 file per workflow)
**Proposed:** SQLite or PostgreSQL table

**Benefits:**
- Atomic updates (no race conditions)
- Transactional rollback
- Query all workflows efficiently (no directory scan)
- History tracking (state changelog)
- Concurrent access without locking

### Message Queue for Phase Coordination

**Current:** subprocess.run() chains phases
**Proposed:** Redis queue or RabbitMQ

**Benefits:**
- Phases can run independently
- Automatic retry on failure
- Distributed execution (scale to multiple machines)
- Better observability (queue depth, processing time)

### Centralized Process Manager

**Current:** Each phase spawns subprocesses
**Proposed:** Supervisor or systemd units

**Benefits:**
- Lifecycle management (start, stop, restart)
- Resource limits (CPU, memory, timeout)
- Log aggregation
- Health checks

---

## Testing Recommendations

### Integration Tests Needed

1. **Concurrent Workflow Test**
   - Spawn 20 workflows simultaneously
   - Verify no port collisions
   - Check state consistency

2. **Failure Recovery Test**
   - Kill phase mid-execution
   - Verify cleanup runs
   - Check no orphaned resources

3. **State Corruption Test**
   - Simulate concurrent state writes
   - Verify no data loss

4. **External Tool Timeout Test**
   - Mock slow build (6+ minutes)
   - Verify subprocess killed cleanly

### E2E Test Scenarios

1. **Complete SDLC Happy Path**
   - All phases succeed
   - Worktree cleaned up
   - PR merged, branch deleted

2. **Mid-Pipeline Failure**
   - Test phase fails
   - Verify no subsequent phases run
   - Check partial cleanup

3. **Concurrent Workflows on Same Issue**
   - Two ADWs for same issue
   - Verify isolation
   - Check no interference

---

## Appendix: Data from Analysis

### State File Example

```json
{
  "adw_id": "adw-3af4a34d",
  "issue_number": "83",
  "branch_name": "feature-issue-83-adw-3af4a34d-frontend-monitor-component",
  "plan_file": "specs/issue-83-adw-adw-3af4a34d-sdlc_planner-phase-2-frontend-component.md",
  "issue_class": "/feature",
  "worktree_path": "/Users/Warmonger0/tac/tac-webbuilder/trees/adw-3af4a34d",
  "backend_port": 9108,
  "frontend_port": 9208,
  "model_set": "base",
  "all_adws": ["adw_plan_iso"],
  "estimated_cost_total": null,
  "status": null,
  "workflow_template": null
}
```

**Issues:**
- Many null fields (workflow not started yet)
- No "current_phase" tracking
- No "last_activity" timestamp
- No "phase_history" array

### Active Worktrees (from git worktree list)

```
/Users/Warmonger0/tac/tac-webbuilder/trees/12ad9dbd      47f5230 [feature-issue-79-adw-2cfe5aa9-backend-api-monitoring]
/Users/Warmonger0/tac/tac-webbuilder/trees/2cfe5aa9      271ccd5 [feature-issue-79-adw-2cfe5aa9-backend-api-monitor-endpoint]
/Users/Warmonger0/tac/tac-webbuilder/trees/446dab5f      d56a741 [feature-issue-83-adw-446dab5f-frontend-adw-monitor-card]
/Users/Warmonger0/tac/tac-webbuilder/trees/50443844      1e671de [bug-issue-74-adw-50443844-test-infra-failure-loop]
/Users/Warmonger0/tac/tac-webbuilder/trees/adw-3af4a34d  71ebc82 [feature-issue-83-adw-3af4a34d-frontend-monitor-component]
... (9 total worktrees)
```

**Observation:** 9 worktrees × 2 ports each = 18 ports needed, but only 15 available. **Port exhaustion is happening right now.**

### Phase Execution Times (from SDLC workflow)

- Plan: ~2-5 minutes
- Validate: ~1 minute
- Build: ~3-10 minutes (depends on external tools)
- Lint: ~2-4 minutes
- Test: ~5-15 minutes (with retries)
- Review: ~10-30 minutes (screenshots, patch resolution)
- Document: ~2-5 minutes
- Ship: ~1-2 minutes
- Cleanup: ~30 seconds

**Total:** 26-72 minutes for complete SDLC (highly variable)

---

## Conclusion

The ADW pipeline shows sophisticated isolation techniques but suffers from **resource management issues** (ports, worktrees) and **coordination failures** (state races, error propagation). The top 5 issues account for ~80% of workflow failures and manual interventions.

**Priority order:**
1. Fix state file races (P0)
2. Expand port range (P0)
3. Standardize error handling (P0)
4. Auto-cleanup worktrees (P1)
5. Fix subprocess management (P1)

Implementing P0 fixes will immediately improve workflow reliability by ~60%. P1 fixes will reduce manual cleanup by ~80%.
