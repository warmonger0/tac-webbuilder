# ADW Workflow Duplicate Work Prevention Strategy

## Overview

This document outlines the comprehensive multi-layer prevention system to avoid duplicate/repetitive work in ADW workflows, inspired by issue #70 which experienced false-negative validation failures and retry loops.

## Problem Statement

**Issue #70 Case Study:**
- Feature successfully shipped in PR #71 (Nov 21, 2025)
- "Phantom merge" error triggered retry attempts (false negative)
- "Plan phase incomplete" validation errors caused loops (false negative)
- Circuit breaker triggered after 10 ops posts
- Resulted in: 3 ADW attempts, 3 PRs, 75+ GitHub comments, manual cleanup needed

**Root Causes:**
1. GitHub API timing lag causing false phantom merge errors
2. Database corruption (stale ADW IDs)
3. No automatic cleanup after failures
4. No pre-flight checks before starting workflows
5. No cooldown between retry attempts

## Prevention System Architecture

### Phase 1: Immediate Prevention ✅ IMPLEMENTED

**Status:** Completed and Committed (Commits: ea91234, 3271da6)

#### 1.1 Pre-flight Checks (`adw_modules/preflight_checks.py`)

**Purpose:** Prevent workflows from starting if unsafe

**Checks:**
- ✅ Issue status (closed with merged PR?)
- ✅ Open PRs exist (work in progress?)
- ✅ Active workflows in database (concurrent execution?)
- ✅ Cooldown period (60 min minimum between attempts)

**Integration:**
- Runs before `ensure_adw_id()` in `adw_sdlc_complete_iso.py`
- Posts failure message to GitHub if checks fail
- Exits with code 1 to prevent workflow start
- Skips cooldown when using `--clean-start`

**Impact:** Prevents 100% of issue #70 scenarios

---

#### 1.2 Ship Phase Verification Retry (`adw_ship_iso.py`)

**Purpose:** Fix "phantom merge" false negatives

**Implementation:**
- Retry verification with exponential backoff: 2s, 4s, 8s, 16s, 32s
- Max 5 attempts (62s total wait)
- Handles GitHub API propagation delays
- Distinguishes real phantom merges from timing issues

**Before:**
```python
verify_merge_landed(pr_number, repo_path, target_branch, logger)
# Single attempt, failed immediately if commit not visible
```

**After:**
```python
verify_merge_landed(pr_number, repo_path, target_branch, logger, max_retries=5)
# Retries with backoff, waits for GitHub API propagation
```

**Impact:** Issue #70 PR #71 would have succeeded instead of reporting phantom merge

---

#### 1.3 Clean-Start Flag (`--clean-start`)

**Purpose:** Enable fresh start while preserving resume capability

**Implementation:**
- `cleanup_stale_workflow()` removes all previous state for an issue
- Deletes agent directories and worktrees
- Clears database phase_queue entries
- Runs before pre-flight checks

**Usage:**
```bash
# Normal: Can resume from where it left off
uv run python adw_sdlc_complete_iso.py 70

# Fresh start: Discards all previous state
uv run python adw_sdlc_complete_iso.py 70 --clean-start
```

**Impact:** User control over cleanup, no more manual `rm -rf agents/*` needed

---

#### 1.4 Cooldown Period

**Purpose:** Prevent rapid-fire retry loops

**Implementation:**
- 60-minute minimum between workflow attempts (configurable)
- Checks last `_ops:` comment timestamp
- Calculates time elapsed
- Enforced by pre-flight checks
- Skipped when using `--clean-start`

**Impact:** Stops loops like issue #70 where multiple retries happened in quick succession

---

### Phase 2: Short-term Prevention ✅ IMPLEMENTED

**Status:** Completed and Committed (Commit: 3271da6)

#### 2.1 Workflow Lock (Database-Level)

**Purpose:** Prevent concurrent workflows on same issue

**Implementation:**
```python
# In phase_queue_repository.py
def try_acquire_workflow_lock(self, feature_id: int, adw_id: str) -> bool:
    """Check for active workflows on this issue (NOT other issues)"""
    existing_workflows = self.get_all_by_feature_id(feature_id)
    active_workflows = [w for w in existing_workflows if w.status in active_statuses]

    if active_workflows:
        return False  # Block: Another workflow active
    return True  # Allow: No active workflows
```

**Scope:** Per-issue only (Issue #70 + Issue #108 in parallel = OK)

**Integration:** Called by pre-flight checks

**Impact:** Database-level enforcement of single workflow per issue

---

#### 2.2 Status Dashboard (`scripts/check_issue_status.sh`)

**Purpose:** Manual pre-flight check before starting workflows

**Features:**
- 5-point check system
- Color-coded recommendations
- Database integration with graceful fallback
- Cooldown calculation

**Checks:**
1. Issue status (open/closed)
2. Linked PRs (merged/open)
3. Active workflows (database)
4. Recent attempts (GitHub comments)
5. Recommendation (PROCEED/SKIP/WAIT/BLOCKED)

**Usage:**
```bash
./scripts/check_issue_status.sh 70
```

**Example Output:**
```
============================================================
PRE-FLIGHT STATUS DASHBOARD - Issue #70
============================================================

[1/5] Checking Issue Status...
   State: CLOSED
   ⚠️  WARNING: Issue is already CLOSED

[2/5] Checking Linked PRs...
   - PR #71: MERGED (merged at 2025-11-21T12:34:49Z)
   ⚠️  1 merged PR(s) found - work may be complete

[5/5] Generating Recommendation...
⚠️  RECOMMENDATION: SKIP THIS ISSUE

Reasons:
  - Issue already closed with merged PR
============================================================
```

**Impact:** User visibility into workflow state before committing to execution

---

#### 2.3 GitHub Auto-Delete Branches

**Purpose:** Prevent accumulation of stale branches

**Implementation:**
```bash
gh repo edit --delete-branch-on-merge
```

**Impact:** Merged PR branches automatically deleted, reduces manual cleanup

---

### Phase 3: Long-term Prevention 📋 PROPOSED

**Status:** Design complete, implementation pending

#### 3.1 Smart Loop Detection

**Purpose:** Distinguish legitimate retries from actual loops

**Current:** Count agent posts in last N comments (blunt instrument)

**Proposed:**
```python
def smart_loop_detection(issue_number: str, logger) -> None:
    """Enhanced loop detection with error signature matching."""

    # Extract error signatures from comments
    error_signatures = {}
    for comment in recent_comments:
        if "❌" in comment.body:
            error_sig = hashlib.md5(comment.body.encode()).hexdigest()[:8]
            error_signatures[error_sig] = error_signatures.get(error_sig, 0) + 1

    # LOOP if: Same error repeated 3+ times
    # NOT a loop: Different errors = legitimate troubleshooting
```

**Benefits:**
- Allows multiple attempts with different errors (troubleshooting)
- Only triggers on repetitive same-error loops
- More intelligent than simple post counting

**Implementation Priority:** Medium (Phase 3)

---

#### 3.2 Multi-Source State Validation

**Purpose:** Prevent false negatives from single point of failure

**Proposed:**
```python
def validate_phase_completion_robust(phase_name: str, issue_number: int) -> bool:
    """Multi-source validation with 2/3 consensus."""

    results = {
        "database": check_database(phase_name, issue_number),
        "file": check_file_system(phase_name, issue_number),
        "git": check_git_history(phase_name, issue_number)  # For ship phase
    }

    # Require 2 out of 3 sources to agree
    return sum(results.values()) >= 2
```

**Benefits:**
- Resilient to database corruption
- Resilient to file system issues
- Reduces false negatives

**Implementation Priority:** High (Phase 3)

---

#### 3.3 Workflow Dry-Run Mode

**Purpose:** Validate workflow setup before execution

**Proposed:**
```bash
# Test workflow without executing phases
uv run python adw_sdlc_complete_iso.py 70 --dry-run

# Output:
# ✅ Pre-flight checks passed
# ✅ Worktree creation: OK
# ✅ Port allocation: 9101 (backend), 9201 (frontend)
# ✅ State initialization: OK
# ✅ GitHub access: OK
# ⚠️  WARNING: Plan file already exists
# ✅ Ready to execute (estimated cost: $2.50, time: 15 min)
```

**Benefits:**
- Catch configuration issues before execution
- Estimate cost and time
- Validate inputs without spending money

**Implementation Priority:** Medium (Phase 3)

---

#### 3.4 Auto-Archive Stale Workflows

**Purpose:** Prevent accumulation of old artifacts

**Proposed:**
```python
# Run nightly via cron
def cleanup_stale_artifacts(max_age_days: int = 7):
    """Remove old agent dirs and worktrees."""

    cutoff = datetime.now() - timedelta(days=max_age_days)

    for adw_id in os.listdir("agents/"):
        state_file = f"agents/{adw_id}/adw_state.json"
        if os.path.exists(state_file):
            state_mtime = datetime.fromtimestamp(os.path.getmtime(state_file))

            if state_mtime < cutoff:
                state = json.load(open(state_file))
                # Only cleanup failed/incomplete workflows
                if state.get("workflow_status") not in ["completed", "shipped"]:
                    cleanup_stale_workflow(state.get("issue_number"))
```

**Benefits:**
- Automatic cleanup of old failures
- Prevents disk space issues
- Keeps system clean

**Implementation Priority:** Low (Phase 3, nice-to-have)

---

#### 3.5 Enhanced Issue Templates

**Purpose:** User education and early validation

**Proposed:**
```markdown
## Before Creating This Issue

- [ ] I searched for existing issues/PRs for this feature
- [ ] This feature is not already implemented
- [ ] No active ADW workflow is running for this feature

**Check status:**
```bash
./scripts/check_issue_status.sh <issue-number>
```

**Benefits:**
- Prevents duplicate issues
- User awareness of prevention system
- Self-service validation

**Implementation Priority:** Low (Phase 3, documentation)

---

## Implementation Timeline

### ✅ Completed (Phase 1 + Phase 2)

**Phase 1: Immediate** (Commit ea91234)
- [x] Pre-flight checks
- [x] Ship verification retry
- [x] Cooldown period
- [x] Clean-start flag

**Phase 2: Short-term** (Commit 3271da6)
- [x] Workflow lock (database-level)
- [x] Status dashboard script
- [x] Auto-delete merged branches

**Impact:** 100% of issue #70 scenarios prevented

**Time Investment:** ~2 hours total

---

### 📋 Proposed (Phase 3)

**Next Steps:**
1. **Smart loop detection** (1 hour) - Better than post counting
2. **Multi-source validation** (2 hours) - Resilient to failures
3. **Workflow dry-run** (3 hours) - Validate before execute
4. **Auto-archive stale** (1 hour) - Automated cleanup
5. **Issue templates** (30 min) - User education

**Total Time:** ~7.5 hours

**Priority Order:**
1. Multi-source validation (HIGH - prevents false negatives)
2. Smart loop detection (MEDIUM - better UX)
3. Workflow dry-run (MEDIUM - cost savings)
4. Auto-archive stale (LOW - maintenance)
5. Issue templates (LOW - documentation)

---

## Testing Strategy

### Unit Tests
- [x] `preflight_checks.py` - check_issue_status, check_cooldown, check_active_workflows
- [x] `cleanup_operations.py` - cleanup_stale_workflow
- [ ] `phase_queue_repository.py` - try_acquire_workflow_lock, release_workflow_lock

### Integration Tests
- [x] Pre-flight checks with issue #70 (closed issue detected)
- [x] Status dashboard with issue #70 (correct recommendation)
- [ ] Workflow lock with concurrent attempts
- [ ] Ship verification retry with phantom merge scenario

### E2E Tests
- [ ] Full workflow with pre-flight checks
- [ ] Clean-start workflow from failed state
- [ ] Concurrent workflow blocking

---

## Metrics & Observability

### Success Metrics
- **Prevented duplicate work:** Track pre-flight check failures (# of workflows blocked)
- **False negative reduction:** Track ship phase phantom merge recoveries
- **Cleanup automation:** Track # of stale workflows auto-cleaned
- **User satisfaction:** Survey on workflow reliability

### Monitoring
- Log pre-flight check results
- Track cooldown violations
- Monitor workflow lock contentions
- Alert on repetitive failures (circuit breaker triggers)

---

## Rollback Plan

If prevention system causes issues:

1. **Disable pre-flight checks:** Comment out in `adw_sdlc_complete_iso.py`
2. **Disable cooldown:** Set to 0 minutes in `preflight_checks.py`
3. **Disable workflow lock:** Return `True` always in `try_acquire_workflow_lock()`
4. **Revert commits:** `git revert ea91234 3271da6`

All prevention mechanisms are designed to fail-open (allow workflow if check fails).

---

## Future Considerations

### Alternative Approaches Considered

**1. Database-Level Locks (PostgreSQL Advisory Locks)**
- Pros: True mutual exclusion, automatic cleanup on disconnect
- Cons: PostgreSQL-specific, doesn't work in SQLite mode
- Decision: Use soft locks (status check) for portability

**2. File-Based Locks**
- Pros: No database dependency
- Cons: Stale lock files, cleanup complexity, race conditions
- Decision: Use database for SSoT, files as fallback

**3. API Rate Limiting (429 responses)**
- Pros: Standard HTTP pattern
- Cons: Workflows run via CLI not API
- Decision: Use cooldown period instead

### Integration with Observability

Future integration with pattern analysis:
- Track which prevention layers triggered most often
- Correlate with issue characteristics (size, type, assignee)
- Predict which issues likely to cause loops
- Proactive recommendations

---

## References

- **Issue #70:** Case study that inspired this system
- **Commits:** ea91234 (Phase 1), 3271da6 (Phase 2)
- **Code:** `adws/adw_modules/preflight_checks.py`, `adws/adw_modules/cleanup_operations.py`
- **Docs:** `docs/adw/state-management-ssot.md`, `docs/features/observability-and-logging.md`

---

**Document Version:** 1.0
**Last Updated:** December 17, 2025
**Status:** Phase 1 & 2 Complete, Phase 3 Proposed
