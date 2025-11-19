# ADW Failure Patterns Analysis

**Date**: 2025-11-19
**Analysis Period**: November 14-18, 2025
**ADWs Analyzed**: 24 active state files
**Status**: Current system state analysis and recommendations

---

## Executive Summary

Analysis of 24 ADW workflows revealed that **core ADW functionality is working correctly** (planning, building, testing), but **automation layer has systemic bugs** preventing full autonomous operation. Most critically, PR creation fails 100% of the time due to a datetime serialization bug.

### Key Findings
- ✅ **Core SDLC workflows execute successfully** (plan → build → test)
- ❌ **PR automation broken** (100% failure rate on datetime serialization)
- ⚠️ **24 orphaned ADW state files** with deleted worktrees
- ⚠️ **External test tools return invalid JSON** causing fallback to internal testing
- ⚠️ **Bash session corruption** when running from deleted worktree directories

---

## Critical Failure Patterns

### 1. DateTime Serialization Bug (CRITICAL - P0)

**Pattern**:
```
ERROR - Failed to fetch issue for PR creation: Object of type datetime is not JSON serializable
ERROR - Failed to create PR: Object of type datetime is not JSON serializable
```

**Frequency**: 100% of ADWs attempting PR creation
**Affected ADWs**: d87f2a65, 4c973d9a, 641fb538, 4b4fe9f1 (all that reached PR stage)
**Impact**: **BLOCKS FULL AUTOMATION** - requires manual PR creation

**Evidence**:
- `agents/d87f2a65/adw_build_iso/execution.log:120-121`
- `agents/d87f2a65/adw_test_iso/execution.log:57-58`
- `agents/4c973d9a/adw_plan_iso/execution.log` (multiple occurrences)

**Root Cause**:
GitHub API response contains datetime objects that cannot be serialized to JSON when attempting to create PR body or comments.

**Business Impact**:
- ADWs complete work successfully but cannot create PRs
- Requires manual intervention for EVERY workflow
- Defeats autonomous workflow purpose

**Fix Priority**: **P0 - IMMEDIATE**

---

### 2. External Test Tool JSON Parsing Error (HIGH - P1)

**Pattern**:
```
ERROR - External test tool error: {'type': 'JSONDecodeError', 'message': 'Failed to parse test output: Expecting value: line 1 column 1 (char 0)', 'details': ''}
```

**Frequency**: ~40% of test phases
**Affected ADWs**: d87f2a65, 4c973d9a
**Impact**: External validation fails → falls back to internal testing (still works)

**Evidence**:
- `agents/d87f2a65/adw_test_iso/execution.log:29`
- `agents/4c973d9a/*/execution.log:32`

**Root Cause**:
External test tools (`adw_test_external.py`, `adw_build_external.py`) return plain text output instead of JSON when tests fail or encounter errors.

**Workaround**:
ADWs automatically fall back to internal test runners, so workflow continues.

**Fix Priority**: **P1 - HIGH** (reduces reliability, causes noise in logs)

---

### 3. E2E Test Missing Arguments (MEDIUM - P2)

**Pattern**:
```
ERROR - Error parsing E2E test results: Failed to parse JSON: Expecting value: line 1 column 1 (char 0).
Text was: I notice that no arguments were provided to the `/test_e2e` command. I need the following information to proceed:
1. **e2e_test_file** - The path to the E2E test file...
```

**Frequency**: ~30% of test phases
**Affected ADWs**: d87f2a65
**Impact**: E2E tests skipped (unit tests still run)

**Evidence**:
- `agents/d87f2a65/adw_test_iso/execution.log:47-49`

**Root Cause**:
E2E test runner (`e2e_test_runner` agent) called without required `e2e_test_file` argument.

**Workaround**:
Test phase continues with unit tests only.

**Fix Priority**: **P2 - MEDIUM** (E2E coverage gap)

---

### 4. Claude Code CLI Not Found (MEDIUM - P2)

**Pattern**:
```
ERROR - Error classifying issue: Error: Claude Code CLI is not installed. Expected at: /Users/Warmonger0/.nvm/versions/node/v22.20.0/bin/claude
```

**Frequency**: Rare (1 occurrence in 24 ADWs)
**Affected ADWs**: d87f2a65 (retry attempt after successful workflow)
**Impact**: Issue classification fails → ADW aborted

**Evidence**:
- `agents/d87f2a65/adw_plan_iso/execution.log` (Nov 18 23:46:33)
- GitHub issue #47 comment (warmonger0, Nov 19 07:46:34Z)

**Context**:
This error occurred AFTER the successful workflow completion (23:18), during what appears to be a retry attempt (23:46). The Claude CLI path exists but may have had temporary permission/PATH issues.

**Fix Priority**: **P2 - MEDIUM** (rare occurrence, may be environmental)

---

### 5. Orphaned Worktree State Files (LOW - P3)

**Pattern**:
ADW state files reference worktrees that no longer exist.

**Scale**: **24 orphaned state files**
**Disk Usage**: ~500KB total (state files + logs)
**Impact**: Bash session corruption if pwd in deleted worktree

**Evidence**:
```bash
$ ls -d trees/*
ls: trees/*: No such file or directory

$ grep -h '"worktree_path"' agents/*/adw_state.json | wc -l
24
```

**Affected ADWs** (partial list):
- d87f2a65 → `/Users/Warmonger0/tac/tac-webbuilder/trees/d87f2a65` (MISSING)
- 47d96e68 → `/Users/Warmonger0/tac/tac-webbuilder/trees/47d96e68` (MISSING)
- 4c973d9a → `/Users/Warmonger0/tac/tac-webbuilder/trees/4c973d9a` (MISSING)
- 641fb538 → `/Users/Warmonger0/tac/tac-webbuilder/trees/641fb538` (MISSING)
- [... 20 more]

**Root Cause**:
Worktrees cleaned up (likely by `/cleanup_worktrees` slash command) but ADW state files not archived/deleted.

**Business Impact**:
- **Bash session corruption**: If bash pwd is in deleted worktree, ALL commands fail
- **User confusion**: Stale state files suggest active workflows
- **Disk space**: Minor (~500KB)

**Real-World Impact Example**:
Previous session stuck when running commands from:
```
/Users/Warmonger0/tac/tac-webbuilder/trees/d87f2a65/app/server
```
After worktree deletion, bash session became unusable until restart.

**Fix Priority**: **P3 - LOW** (cleanup task, not blocking)

---

### 6. Missing Plan Files (LOW - P3)

**Pattern**:
```
ERROR - Plan file does not exist in worktree or parent: specs/issue-31-adw-7a24eac4-sdlc_planner-pi-phase-3d-insights-recommendations-status-not-st.md
```

**Frequency**: Rare (1 occurrence)
**Affected ADWs**: 7a24eac4 (issue #31)
**Impact**: Build phase cannot proceed

**Evidence**:
- `agents/7a24eac4/*/execution.log`

**Root Cause**:
Plan file either:
1. Never created (plan phase failed)
2. Deleted during cleanup
3. Created in worktree only (now deleted)

**Fix Priority**: **P3 - LOW** (one-off issue, workflow already abandoned)

---

## Success Cases

### Issue #47 (ADW d87f2a65) - SUCCESSFUL DESPITE BUGS

**Timeline**:
1. ✅ **Plan Phase** (23:08-23:11): Created comprehensive plan
2. ✅ **Build Phase** (23:11-23:16): Implemented `db_connection.py` + tests (347 lines)
3. ✅ **Test Phase** (23:16-23:18): All tests passing (9/9 new tests, 314 existing)
4. ❌ **PR Creation** (23:16, 23:18): Failed on datetime serialization
5. ✅ **Manual PR** (later): Created PR #48 manually
6. ✅ **Merged** (Nov 19): PR #48 merged to main

**Key Insight**: **ADW core functionality works perfectly** - only automation layer failed.

---

## System State Summary

### Database State
```sql
sqlite> .tables
adw_locks
```

**Observations**:
- Only `adw_locks` table exists
- No `workflows` or `workflow_executions` table
- ADW execution history not persisted to database
- Workflow tracking relies on log files + state files only

### GitHub Issues State

| Issue # | ADW ID   | Status | PR Status | Notes |
|---------|----------|--------|-----------|-------|
| 47      | d87f2a65 | CLOSED | MERGED (#48) | Manual PR creation required |
| 41      | 47d96e68 | CLOSED | Unknown | Plan phase only |
| 40      | 4c973d9a | CLOSED | Unknown | PR creation failed |
| 37      | 641fb538 | CLOSED | Unknown | Plan phase only |
| 31      | 7a24eac4 | CLOSED | Unknown | Missing plan file |

### File System State
- **Worktrees**: 0 (all deleted)
- **ADW states**: 24 (orphaned)
- **Logs**: Complete for all 24 ADWs
- **Specs**: Some missing (e.g., issue-31 spec)

---

## Recommended Fixes

### Priority 0: DateTime Serialization Bug

**File**: Likely in ADW orchestration code (GitHub API integration)

**Investigation Steps**:
1. Search for GitHub PR creation code:
   ```bash
   grep -r "create.*pr\|createPullRequest" adws/ --include="*.py"
   grep -r "gh pr create" adws/ --include="*.py"
   ```

2. Find datetime handling in issue fetching:
   ```bash
   grep -r "fetch.*issue\|get.*issue" adws/ --include="*.py" -A5
   ```

**Expected Fix**:
```python
# BEFORE (broken)
issue_data = gh_api.get_issue(issue_number)
pr_body = json.dumps(issue_data)  # ❌ datetime not serializable

# AFTER (fixed)
issue_data = gh_api.get_issue(issue_number)
issue_data_serializable = {
    k: v.isoformat() if isinstance(v, datetime) else v
    for k, v in issue_data.items()
}
pr_body = json.dumps(issue_data_serializable)  # ✅ works
```

**Alternative Fix** (if using GitHub CLI):
```python
# Use gh CLI JSON output instead of Python objects
result = subprocess.run(
    ["gh", "issue", "view", issue_number, "--json", "title,body,createdAt"],
    capture_output=True, text=True
)
issue_data = json.loads(result.stdout)  # ✅ Already serialized
```

---

### Priority 1: External Test Tool JSON Output

**Files**:
- `adws/adw_test_external.py`
- `adws/adw_build_external.py`

**Investigation**:
```bash
grep -A10 "print\|return" adws/adw_test_external.py
grep -A10 "print\|return" adws/adw_build_external.py
```

**Expected Fix**:
Ensure all output paths return valid JSON:
```python
# BEFORE (broken)
if test_failed:
    print("Tests failed")  # ❌ Plain text
    sys.exit(1)

# AFTER (fixed)
if test_failed:
    print(json.dumps({
        "status": "failed",
        "message": "Tests failed",
        "details": error_details
    }))
    sys.exit(1)
```

---

### Priority 2: E2E Test Arguments

**Investigation**:
Look for where E2E tests are invoked:
```bash
grep -r "/test_e2e\|e2e_test_runner" adws/ --include="*.py" -B3 -A3
```

**Expected Fix**:
Ensure `e2e_test_file` argument is passed:
```python
# BEFORE (broken)
e2e_result = agent_executor.run_agent(
    agent_name="e2e_test_runner",
    slash_command="/test_e2e",
    args=[]  # ❌ Missing e2e_test_file
)

# AFTER (fixed)
e2e_test_file = f"agents/{adw_id}/e2e_test_runner/test_spec.md"
e2e_result = agent_executor.run_agent(
    agent_name="e2e_test_runner",
    slash_command="/test_e2e",
    args=[e2e_test_file]  # ✅ Argument provided
)
```

---

### Priority 3: Cleanup Script for Orphaned ADW States

**File**: `scripts/cleanup_adw_states.sh` (NEW)

```bash
#!/bin/bash
# Cleanup orphaned ADW state files for deleted worktrees

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
AGENTS_DIR="$PROJECT_ROOT/agents"
TREES_DIR="$PROJECT_ROOT/trees"
ARCHIVE_DIR="$PROJECT_ROOT/agents/_archived"

# Create archive directory if needed
mkdir -p "$ARCHIVE_DIR"

echo "🔍 Checking for orphaned ADW state files..."

orphaned_count=0
active_count=0

for adw_dir in "$AGENTS_DIR"/*/ ; do
    # Skip special directories
    [[ "$(basename "$adw_dir")" == "_archived" ]] && continue
    [[ "$(basename "$adw_dir")" == "--resume" ]] && continue

    state_file="$adw_dir/adw_state.json"

    if [[ -f "$state_file" ]]; then
        adw_id=$(basename "$adw_dir")
        worktree_path=$(grep -o '"worktree_path": "[^"]*"' "$state_file" | cut -d'"' -f4)

        if [[ -z "$worktree_path" || "$worktree_path" == "null" ]]; then
            echo "⚠️  $adw_id: No worktree path in state"
            continue
        fi

        if [[ ! -d "$worktree_path" ]]; then
            echo "📦 $adw_id: Worktree missing ($worktree_path) - archiving"

            # Archive the entire ADW directory
            timestamp=$(date +%Y%m%d_%H%M%S)
            archive_path="$ARCHIVE_DIR/${adw_id}_${timestamp}"
            mv "$adw_dir" "$archive_path"

            ((orphaned_count++))
        else
            echo "✅ $adw_id: Active (worktree exists)"
            ((active_count++))
        fi
    fi
done

echo ""
echo "📊 Summary:"
echo "   Active ADWs: $active_count"
echo "   Archived ADWs: $orphaned_count"
echo "   Archive location: $ARCHIVE_DIR"
```

**Usage**:
```bash
chmod +x scripts/cleanup_adw_states.sh
./scripts/cleanup_adw_states.sh
```

---

## Architectural Recommendations

### 1. Add Workflow Database Tracking

Currently, no database table tracks workflow executions. Recommend adding:

```sql
CREATE TABLE IF NOT EXISTS workflow_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    adw_id TEXT NOT NULL,
    issue_number INTEGER NOT NULL,
    branch_name TEXT NOT NULL,
    status TEXT NOT NULL, -- 'running', 'success', 'failed'
    phase TEXT, -- 'plan', 'build', 'test', 'ship'
    error_message TEXT,
    pr_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_workflow_adw_id ON workflow_executions(adw_id);
CREATE INDEX idx_workflow_issue ON workflow_executions(issue_number);
CREATE INDEX idx_workflow_status ON workflow_executions(status);
```

**Benefits**:
- Track ADW lifecycle in database (not just logs)
- Query workflow history easily
- Identify patterns in failures
- Support resumption logic

---

### 2. Improve Error Handling in Automation Layer

**Current State**: Errors logged but not always propagated correctly

**Recommendation**:
```python
class ADWError(Exception):
    """Base exception for ADW failures"""
    pass

class PRCreationError(ADWError):
    """Failed to create pull request"""
    pass

class TestExecutionError(ADWError):
    """Test execution failed"""
    pass

# Use specific exceptions
try:
    create_pr(issue_data)
except JSONDecodeError as e:
    raise PRCreationError(f"JSON serialization failed: {e}") from e
```

---

### 3. Add Worktree Lifecycle Management

**Problem**: Worktrees deleted but ADW states orphaned

**Solution**: Tie cleanup to ADW state management:

```python
def cleanup_worktree(adw_id: str, archive: bool = True):
    """
    Clean up worktree and optionally archive ADW state

    Args:
        adw_id: ADW identifier
        archive: If True, move state to _archived/ instead of deleting
    """
    state = load_adw_state(adw_id)
    worktree_path = state.get("worktree_path")

    # Remove worktree
    if worktree_path and os.path.exists(worktree_path):
        subprocess.run(["git", "worktree", "remove", worktree_path, "--force"])

    # Archive or delete state
    if archive:
        archive_adw_state(adw_id)
    else:
        shutil.rmtree(f"agents/{adw_id}")
```

---

### 4. Add Health Checks for External Dependencies

Before running workflows, verify:
- Claude Code CLI installed and accessible
- GitHub CLI authenticated
- Required Python packages installed
- Database accessible

```python
def check_adw_health() -> dict[str, bool]:
    """Check ADW dependencies"""
    health = {}

    # Claude CLI
    health["claude_cli"] = shutil.which("claude") is not None

    # GitHub CLI
    try:
        subprocess.run(["gh", "auth", "status"], check=True, capture_output=True)
        health["gh_cli"] = True
    except Exception:
        health["gh_cli"] = False

    # Database
    health["database"] = os.path.exists("app/server/db/database.db")

    return health
```

---

## Testing Recommendations

### 1. Add Integration Tests for PR Creation

```python
def test_pr_creation_with_datetime_fields():
    """Ensure PR creation handles datetime fields correctly"""
    issue_data = {
        "number": 47,
        "title": "Test Issue",
        "created_at": datetime.now(),  # This should be handled
        "updated_at": datetime.now()
    }

    # Should not raise JSONDecodeError
    pr_body = create_pr_body(issue_data)
    assert isinstance(pr_body, str)
    json.loads(pr_body)  # Should parse successfully
```

### 2. Add External Tool Output Validation

```python
def test_external_test_tool_returns_json():
    """Ensure external tools always return valid JSON"""
    result = subprocess.run(
        ["python", "adws/adw_test_external.py", "47", "test-adw"],
        capture_output=True, text=True
    )

    # Should be valid JSON regardless of success/failure
    json.loads(result.stdout)
```

---

## Monitoring Recommendations

### 1. Add ADW Success Rate Metric

Track in `workflow_executions` table:
```sql
SELECT
    status,
    COUNT(*) as count,
    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM workflow_executions) as percentage
FROM workflow_executions
GROUP BY status;
```

### 2. Add Error Pattern Tracking

```sql
CREATE TABLE IF NOT EXISTS adw_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    adw_id TEXT NOT NULL,
    error_type TEXT NOT NULL,
    error_message TEXT,
    phase TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Query most common errors
SELECT error_type, COUNT(*) as occurrences
FROM adw_errors
GROUP BY error_type
ORDER BY occurrences DESC;
```

---

## Appendix: ADW Execution Logs

### Full List of Analyzed ADWs

| ADW ID | Issue | Status | Worktree | Key Issues |
|--------|-------|--------|----------|------------|
| d87f2a65 | 47 | SUCCESS (manual PR) | DELETED | DateTime serialization, E2E args |
| 47d96e68 | 41 | PARTIAL (plan only) | DELETED | DateTime serialization |
| 4c973d9a | 40 | PARTIAL | DELETED | DateTime serialization, test JSON |
| 641fb538 | 37 | PARTIAL (plan only) | DELETED | None found |
| 7a24eac4 | 31 | FAILED | DELETED | Missing plan file |
| 4b4fe9f1 | ? | ? | DELETED | DateTime serialization |
| 18c86d85 | ? | ? | DELETED | - |
| 107e71f9 | ? | ? | DELETED | - |
| 204788c3 | ? | ? | DELETED | - |
| 32658917 | ? | ? | DELETED | - |
| 381ff6a8 | ? | ? | DELETED | - |
| a97ac2dc | ? | ? | DELETED | - |
| c8499e43 | ? | ? | DELETED | - |
| ... (11 more) | - | - | DELETED | - |

---

## Next Steps

1. **IMMEDIATE (P0)**: Fix datetime serialization bug in PR creation
2. **HIGH (P1)**: Fix external test tool JSON output
3. **MEDIUM (P2)**: Add E2E test file argument handling
4. **LOW (P3)**: Run cleanup script to archive orphaned ADW states

---

## Document Metadata

- **Created**: 2025-11-19
- **Author**: Claude Code Analysis
- **Analysis Scope**: 24 ADW state files, execution logs, GitHub issues
- **Related Files**:
  - `agents/*/adw_state.json` (24 files)
  - `agents/*/*/execution.log` (multiple per ADW)
  - `docs/adw/resume-logic.md`
