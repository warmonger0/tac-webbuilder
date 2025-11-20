# Phase 1: Tactical Fixes (Immediate)

**Timeline:** Days 1-2
**Goal:** Get Request 1.4 (Issue #54) running successfully end-to-end
**Priority:** P0 - Critical

---

## Overview

Phase 1 focuses on immediate bug fixes to restore basic ADW functionality and unblock Request 1.4 (Extract LLM Client Utilities). These are surgical fixes to critical issues identified in the investigation.

---

## 1.1 Database Cleanup

### Objective
Clean up 19 stale workflows stuck in "running" state to improve database accuracy and monitoring.

### Tasks

#### Task 1.1.1: Create Workflow Cleanup Script
**File:** `app/server/scripts/cleanup_stale_workflows.py`

**Implementation:**
```python
"""
Clean up stale workflows stuck in 'running' state.
Marks workflows older than 24 hours as 'abandoned'.
"""

import sqlite3
from datetime import datetime, timedelta

def cleanup_stale_workflows(db_path="db/database.db", hours_threshold=24):
    """Mark workflows running >24h as abandoned"""

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Calculate cutoff time
        cutoff = datetime.now() - timedelta(hours=hours_threshold)

        # Find stale workflows
        cursor.execute("""
            SELECT adw_id, issue_number, created_at
            FROM workflow_history
            WHERE status = 'running'
            AND created_at < ?
        """, (cutoff.isoformat(),))

        stale_workflows = cursor.fetchall()

        # Update status to abandoned
        for adw_id, issue_num, created_at in stale_workflows:
            cursor.execute("""
                UPDATE workflow_history
                SET status = 'abandoned',
                    error_message = 'Workflow stuck in running state - auto-cleaned',
                    end_time = ?
                WHERE adw_id = ?
            """, (datetime.now().isoformat(), adw_id))

            print(f"Marked {adw_id} (Issue #{issue_num}) as abandoned")

        conn.commit()
        return len(stale_workflows)
```

**Acceptance Criteria:**
- Script successfully marks 19 stale workflows as "abandoned"
- Database shows accurate workflow counts
- No active workflows incorrectly marked

---

#### Task 1.1.2: Clean Up Orphaned State Files
**Location:** `agents/*/adw_state.json`

**Implementation:**
```bash
#!/bin/bash
# cleanup_orphaned_states.sh

# Find state files older than 24 hours with no active worktree
for state_file in agents/*/adw_state.json; do
    if [ -f "$state_file" ]; then
        adw_id=$(basename $(dirname "$state_file"))
        worktree_path="trees/$adw_id"

        # If worktree doesn't exist and state file is old
        if [ ! -d "$worktree_path" ]; then
            age=$(find "$state_file" -mtime +1)
            if [ ! -z "$age" ]; then
                echo "Archiving orphaned state: $state_file"
                mkdir -p agents/_archived
                mv "$state_file" "agents/_archived/${adw_id}_state_$(date +%s).json"
            fi
        fi
    fi
done
```

**Acceptance Criteria:**
- Orphaned state files moved to `agents/_archived/`
- Active workflow state files preserved
- Archive directory created with proper permissions

---

## 1.2 Critical Bug Fixes

### Priority P0: Blocks Workflow Start

#### Bug Fix 1.2.1: Webhook Trigger for Issue #54
**Severity:** P0 - Critical
**Status:** Active Issue

**Investigation Steps:**
1. Check GitHub webhook configuration in repository settings
2. Review webhook service logs: `tail -f logs/webhook_service.log`
3. Check API quota: `gh api rate_limit`
4. Verify webhook URL accessibility

**Potential Fixes:**

**Option A: Webhook Misconfiguration**
```bash
# Check current webhook
gh api repos/:owner/:repo/hooks

# Verify webhook URL points to correct endpoint
# Expected: http://<server>/webhook/github
```

**Option B: API Quota Exhausted**
```python
# In trigger_webhook.py, add quota check before workflow start
from app.server.core.api_quota import check_quota_available

if not check_quota_available():
    post_github_comment(issue_number,
        "⚠️ Cannot start workflow - API quota low. Will retry when quota resets.")
    return
```

**Option C: Manual Trigger Workaround**
```bash
# If webhook broken, manually trigger workflow
cd /Users/Warmonger0/tac/tac-webbuilder
uv run adws/adw_sdlc_complete_iso.py 54
```

**Acceptance Criteria:**
- Issue #54 receives trigger comment
- Workflow 54 appears in `agents/` directory
- Webhook service logs show successful processing

---

#### Bug Fix 1.2.2: PR Creation JSON Serialization
**Severity:** P1 - High
**Location:** `adws/adw_modules/github.py`

**Problem:**
```python
# ERROR: Object of type datetime is not JSON serializable
```

**Fix:**
```python
# In adw_modules/github.py, add datetime serialization helper

import json
from datetime import datetime

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Update PR creation function
def create_pull_request(title, body, branch_name, base_branch="main"):
    """Create pull request with proper JSON serialization"""

    pr_data = {
        "title": title,
        "body": body,
        "head": branch_name,
        "base": base_branch,
        "created_at": datetime.now()  # Will be serialized correctly
    }

    # Use custom encoder
    json_data = json.dumps(pr_data, cls=DateTimeEncoder)

    # ... rest of function
```

**Acceptance Criteria:**
- PR creation succeeds without JSON errors
- Datetime fields properly serialized as ISO format
- All existing PR creation functionality preserved

---

#### Bug Fix 1.2.3: External Test Tool JSON Parsing
**Severity:** P1 - High
**Location:** `adws/adw_test_external.py`

**Problem:**
```
JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Root Cause:** External test tool not outputting valid JSON

**Fix:**
```python
# In adw_test_external.py, ensure JSON output

import json
import sys

def run_tests(test_path):
    """Run tests and return JSON results"""

    try:
        # Run tests
        result = subprocess.run(
            ["pytest", test_path, "--json-report"],
            capture_output=True,
            text=True
        )

        # Validate JSON before returning
        try:
            json_output = json.loads(result.stdout)
        except json.JSONDecodeError:
            # If stdout isn't JSON, create structured error
            json_output = {
                "success": False,
                "error": "Test output was not valid JSON",
                "raw_output": result.stdout,
                "stderr": result.stderr
            }

        # Always return valid JSON
        print(json.dumps(json_output))
        return json_output

    except Exception as e:
        # Even exceptions should return valid JSON
        error_output = {
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }
        print(json.dumps(error_output))
        return error_output
```

**Acceptance Criteria:**
- All test tool outputs are valid JSON
- Invalid JSON caught and wrapped in error structure
- Test results properly parsed by calling code

---

### Priority P1: Workflow Degradation

#### Bug Fix 1.2.4: Database State Sync After Completion
**Severity:** P1 - High
**Location:** `app/server/core/workflow_history.py`

**Problem:** Completed workflows not marked as "completed" in database

**Fix:**
```python
# In workflow_history.py, add sync call at workflow completion

def mark_workflow_completed(adw_id, status="completed"):
    """Mark workflow as completed with proper timestamps"""

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get workflow start time
        cursor.execute("""
            SELECT created_at FROM workflow_history
            WHERE adw_id = ?
        """, (adw_id,))

        row = cursor.fetchone()
        if not row:
            logger.error(f"Workflow {adw_id} not found in database")
            return False

        start_time = datetime.fromisoformat(row[0])
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds())

        # Update status
        cursor.execute("""
            UPDATE workflow_history
            SET status = ?,
                end_time = ?,
                duration_seconds = ?
            WHERE adw_id = ?
        """, (status, end_time.isoformat(), duration, adw_id))

        logger.info(f"Marked workflow {adw_id} as {status} (duration: {duration}s)")
        return True
```

**Integration Point:**
```python
# In adw_ship_iso.py, call after successful PR merge
from app.server.core.workflow_history import mark_workflow_completed

if pr_merged:
    mark_workflow_completed(adw_id, status="completed")
```

**Acceptance Criteria:**
- Completed workflows marked as "completed" in database
- `end_time` and `duration_seconds` properly populated
- Status sync happens automatically at ship phase

---

#### Bug Fix 1.2.5: Add Error Messages to Database
**Severity:** P2 - Medium
**Location:** All `adw_*_iso.py` files

**Problem:** `error_message` field always empty, making debugging difficult

**Fix:**
```python
# Add helper function to log errors to database

def log_workflow_error(adw_id, phase, error_message):
    """Log error to database for debugging"""

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE workflow_history
            SET status = 'failed',
                error_message = ?,
                end_time = ?
            WHERE adw_id = ?
        """, (f"[{phase}] {error_message}",
              datetime.now().isoformat(),
              adw_id))

# Use in all phases before sys.exit(1)
try:
    # ... phase logic
except Exception as e:
    log_workflow_error(adw_id, "build", str(e))
    sys.exit(1)
```

**Acceptance Criteria:**
- Failed workflows have meaningful error messages
- Error messages include phase name
- Errors visible in database queries

---

## 1.3 Validation Testing

### Test 1.3.1: Create Synthetic Test Workflow
**Objective:** Validate fixes with simple, controlled workflow

**Test Workflow Specification:**
```markdown
# Test Issue: Simple README Update

**Workflow:** lightweight (Haiku model)

Add a new line to README.md with the current date.

TASK:
1. Read README.md
2. Append line: "Last tested: [current date]"
3. Commit change
4. Create PR

ACCEPTANCE CRITERIA:
- README.md updated
- Commit created
- PR opened
- All phases succeed
```

**Execution:**
```bash
# Create test issue
gh issue create --title "Test: Simple README Update" \
  --body "$(cat test_workflow_spec.md)" \
  --label "adw-enabled"

# Monitor execution
tail -f agents/*/adw.log
```

**Success Criteria:**
- All 8 phases complete
- PR created successfully
- No JSON errors
- Database shows "completed" status

---

### Test 1.3.2: Execute Request 1.4
**Objective:** Validate fixes with real production workflow

**Trigger Methods:**

**Option A: Via Webhook (if fixed)**
```bash
# Webhook should auto-trigger on issue #54
# Just verify it starts
gh issue view 54 --comments
```

**Option B: Manual Trigger (if webhook still broken)**
```bash
cd /Users/Warmonger0/tac/tac-webbuilder
uv run adws/adw_sdlc_complete_iso.py 54
```

**Monitoring:**
```bash
# Watch workflow progress
watch -n 5 'gh issue view 54 --comments | tail -20'

# Check database status
sqlite3 db/database.db "SELECT adw_id, status, error_message FROM workflow_history WHERE issue_number = 54"

# Monitor logs
tail -f agents/*/adw.log
```

**Success Criteria:**
- Request 1.4 completes all 8 phases
- PR created for LLM client utilities
- Tests pass
- PR merges successfully
- Worktree cleaned up
- Database shows "completed"

---

## Rollback Plan

If Phase 1 fixes cause regressions:

1. **Revert Database Changes:**
```sql
-- Restore "abandoned" workflows to "running" if needed
UPDATE workflow_history
SET status = 'running', error_message = NULL
WHERE status = 'abandoned' AND end_time > '2025-11-19';
```

2. **Restore State Files:**
```bash
# Move archived states back
mv agents/_archived/*_state_*.json agents/
```

3. **Git Revert:**
```bash
# Revert bug fix commits
git revert <commit-hash>
```

---

## Success Metrics

### Phase 1 Complete When:
- [ ] 19 stale workflows marked as "abandoned" in database
- [ ] Webhook triggering for new issues (Issue #54 has comments)
- [ ] PR creation works without JSON errors
- [ ] External test tools return valid JSON
- [ ] Database state syncs after workflow completion
- [ ] Synthetic test workflow completes successfully
- [ ] Request 1.4 completes end-to-end
- [ ] PR for Request 1.4 merged
- [ ] No orphaned worktrees
- [ ] All error messages logged to database

### Timeline
- **Day 1 Morning:** Database cleanup + bug fixes
- **Day 1 Afternoon:** Synthetic test workflow
- **Day 2 Morning:** Request 1.4 execution
- **Day 2 Afternoon:** Validation and documentation

---

## Next Steps

After Phase 1 completion, proceed to Phase 2: Strategic Redesign for long-term reliability improvements.
