# ADW Workflow Robustness System

**Last Updated:** 2025-11-25
**Status:** Production Ready
**Version:** 1.0

---

## Executive Summary

The ADW Workflow Robustness System is a comprehensive suite of preventive and corrective mechanisms that ensure reliable, predictable workflow execution. This system addresses the "little things" that caused workflow failures: uncommitted changes, test failures, orphaned PRs, and unclosed issues.

### Key Components

1. **Pre-flight Check System** - Prevents bad launches
2. **Automatic Cleanup System** - Cleans up failed workflows
3. **Automatic Issue Closing** - Closes issues on success

### Impact

**Before Robustness System:**
- Workflows failed due to uncommitted changes
- Failed workflows left orphaned PRs open
- Successful workflows required manual issue closing
- Test failures from main branch blocked workflows
- Manual cleanup required for every failure

**After Robustness System:**
- Pre-flight checks block launches with uncommitted changes
- Failed workflows automatically close PRs
- Successful workflows automatically close issues
- Pre-flight checks detect test failures early
- Zero manual intervention for standard failures

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Workflow Lifecycle                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. PRE-LAUNCH                                              │
│     ├─ Pre-flight Checks (BLOCKING)                        │
│     │   ├─ Git State Check ✓                               │
│     │   ├─ Port Availability ✓                             │
│     │   ├─ Test Status ✓                                   │
│     │   ├─ Disk Space ✓                                    │
│     │   └─ Python Environment ✓                            │
│     └─ Workflow Launch (if all checks pass)                │
│                                                              │
│  2. EXECUTION                                               │
│     ├─ Plan Phase                                          │
│     ├─ Validate Phase (baseline errors)                    │
│     ├─ Build Phase                                         │
│     ├─ Lint Phase                                          │
│     ├─ Test Phase                                          │
│     ├─ Review Phase                                        │
│     ├─ Document Phase                                      │
│     └─ Ship Phase                                          │
│                                                              │
│  3. FAILURE HANDLING (at any phase)                        │
│     ├─ Detect Failure                                      │
│     ├─ Find Associated PR                                  │
│     ├─ Close PR with Failure Comment                       │
│     ├─ Post Failure Summary to Issue                       │
│     └─ Mark Workflow as Failed                             │
│                                                              │
│  4. SUCCESS HANDLING (after Ship)                          │
│     ├─ Verify PR Merged                                    │
│     ├─ Verify Commits on Main                              │
│     ├─ Close Issue with Success Comment                    │
│     └─ Post Success Summary                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Component 1: Pre-flight Check System

### Purpose

Prevent workflow launches that are guaranteed to fail by checking system health before starting expensive operations.

### Location

- **Core Logic:** `app/server/core/preflight_checks.py`
- **API Endpoint:** `app/server/routes/system_routes.py` → `/api/preflight-checks`
- **UI Component:** `app/client/src/components/PreflightCheckPanel.tsx`
- **Webhook Integration:** `adws/adw_triggers/trigger_webhook.py`

### Checks Performed

#### 1. Git State Check (BLOCKING)

**Purpose:** Prevent worktree pollution from uncommitted changes

**What it checks:**
- Working directory is clean (no uncommitted changes)
- No untracked files that could propagate to worktree
- Current branch is main

**Why it's blocking:**
```
Problem: Main has uncommitted changes
  ↓
Workflow creates worktree from main's current state
  ↓
Uncommitted changes propagate to worktree
  ↓
Build/Test phase sees "new" changes that aren't yours
  ↓
False positive failures
```

**Implementation:**
```python
# adws/adw_triggers/trigger_webhook.py
git_check_result = check_git_status()
if not git_check_result["is_clean"]:
    comment = f"""❌ Cannot launch ADW workflow

**Pre-flight Check Failed: Git State**
Main branch has uncommitted changes:
{git_check_result["status"]}

**Required Actions:**
1. Commit or stash changes on main
2. Ensure working directory is clean
3. Retry workflow launch
"""
    make_issue_comment(issue_number, comment)
    return  # BLOCK WORKFLOW LAUNCH
```

#### 2. Port Availability Check

**Purpose:** Ensure backend/frontend ports are free for worktree services

**What it checks:**
- Ports 9100-9114 (backend) availability
- Ports 9200-9214 (frontend) availability
- Identifies which ports are in use

**Non-blocking:** Warns if no ports available but doesn't block launch

#### 3. Test Status Check

**Purpose:** Warn about test failures before launching workflow

**What it checks:**
- Backend test status (pytest)
- Frontend test status (vitest)
- Overall pass rate

**Non-blocking:** Warns but doesn't block (tests might be expected to fail)

#### 4. Disk Space Check

**Purpose:** Ensure sufficient space for worktree creation

**What it checks:**
- Available disk space
- Threshold: 1GB minimum

**Non-blocking:** Warns if low on space

#### 5. Python Environment Check

**Purpose:** Verify Python environment is correctly configured

**What it checks:**
- Python version compatibility
- Required packages installed (uv, pytest, etc.)

**Non-blocking:** Warns about missing dependencies

### UI Integration

The `PreflightCheckPanel` component displays real-time health status:

```typescript
// app/client/src/components/PreflightCheckPanel.tsx
interface PreflightCheck {
  name: string;
  status: 'pass' | 'warn' | 'fail';
  message: string;
  blocking: boolean;
}

// UI shows:
// ✅ Git State: Clean (blocking)
// ⚠️  Ports: 2 of 15 in use (non-blocking)
// ✅ Tests: 98% passing (non-blocking)
// ✅ Disk Space: 45GB free (non-blocking)
// ✅ Python Env: All packages installed (non-blocking)
```

### Configuration

Located in `app/server/core/preflight_checks.py`:

```python
# Configurable thresholds
MIN_DISK_SPACE_GB = 1.0
TEST_PASS_RATE_THRESHOLD = 0.8  # 80%
MAX_PORT_RETRIES = 3
```

---

## Component 2: Automatic Cleanup System

### Purpose

Automatically clean up resources when workflows fail, preventing orphaned PRs and providing clear failure feedback.

### Location

- **Core Module:** `adws/adw_modules/failure_cleanup.py`
- **Integration:** `adws/adw_sdlc_complete_iso.py` (all failure points)

### When Cleanup Triggers

Cleanup automatically triggers on failure in these phases:

1. **Plan Phase** - Planning fails (rare)
2. **Build Phase** - TypeScript/Python build errors
3. **Lint Phase** - Code style violations
4. **Test Phase** - Test failures
5. **Review Phase** - Review validation fails
6. **Document Phase** - Documentation generation fails

**Note:** Ship phase failures do NOT close PRs (code might be fine, just needs manual merge)

### Cleanup Operations

#### 1. Find and Close Associated PR

```python
# adws/adw_modules/failure_cleanup.py
def cleanup_failed_workflow(
    adw_id: str,
    issue_number: str,
    branch_name: Optional[str],
    phase_name: str,
    error_details: str,
    logger: logging.Logger
) -> None:
    """Clean up resources after workflow failure."""

    # Find PR for branch
    pr_number = find_pr_for_branch(branch_name, repo_path, logger)

    if pr_number:
        # Close with detailed comment
        close_pr_with_failure_comment(
            pr_number=pr_number,
            phase_name=phase_name,
            error_details=error_details,
            logger=logger
        )
```

#### 2. Post Failure Summary to Issue

```python
failure_summary = f"""🚨 **Workflow Failure Report**

**Workflow ID**: `{adw_id}`
**Failed Phase**: {phase_name}
**PR**: #{pr_number} (automatically closed)
**Status**: Workflow aborted and cleaned up

**Error Summary:**
```
{error_details[:500]}
```

**Automatic Actions Taken:**
✅ Associated PR closed
✅ Workflow marked as failed
✅ Resources cleaned up

**To Retry:**
Fix the errors above and launch a new workflow.
"""

make_issue_comment(issue_number, failure_summary)
```

#### 3. Mark Workflow as Failed

Updates workflow state to reflect failure status.

### Integration Pattern

Every workflow phase integrates cleanup:

```python
# adws/adw_sdlc_complete_iso.py

# Build Phase
try:
    success, error = execute_adw_phase("build", adw_id, issue_number, state, logger)
    if not success:
        from adw_modules.failure_cleanup import cleanup_failed_workflow
        cleanup_failed_workflow(
            adw_id=adw_id,
            issue_number=issue_number,
            branch_name=state.get("branch_name"),
            phase_name="Build",
            error_details=error,
            logger=logger
        )
        sys.exit(1)
except Exception as e:
    # Also cleanup on exceptions
    cleanup_failed_workflow(...)
    raise
```

### Error Handling

Cleanup is **best-effort**:
- Errors during cleanup are logged but don't block
- Partial cleanup is better than no cleanup
- Never throws exceptions that would mask original failure

```python
try:
    cleanup_failed_workflow(...)
except Exception as e:
    logger.warning(f"Cleanup failed (non-critical): {e}")
    # Continue - don't mask original error
```

---

## Component 3: Automatic Issue Closing

### Purpose

Automatically close issues when workflows successfully ship to main, completing the workflow lifecycle without manual intervention.

### Location

- **Core Logic:** `adws/adw_ship_iso.py` (lines 472-518)

### When It Triggers

Issue closing triggers after successful PR merge verification in the Ship phase:

1. ✅ PR found for branch
2. ✅ PR merged via GitHub API
3. ✅ Merge commits verified on main (phantom merge detection)
4. ✅ **Issue closed with success comment** ← NEW

### Implementation

```python
# adws/adw_ship_iso.py (after successful merge)

logger.info(f"Closing issue #{issue_number}...")
try:
    success_comment = f"""🎉 **Successfully Shipped!**

✅ PR merged to main via GitHub API
✅ Branch `{branch_name}` deployed to production
✅ All validation checks passed

**Ship Summary:**
- Validated all state fields
- Found and merged PR successfully
- Verified commits landed on main
- Code is now in production

**Issue Status:** Automatically closing as resolved.

🤖 Generated with [Claude Code](https://claude.com/claude-code)"""

    result = subprocess.run(
        ["gh", "issue", "close", issue_number, "--comment", success_comment],
        capture_output=True,
        text=True,
        check=False
    )

    if result.returncode == 0:
        logger.info(f"✅ Closed issue #{issue_number}")
    else:
        # Graceful degradation
        logger.warning(f"Failed to close issue: {result.stderr}")
        make_issue_comment(
            issue_number,
            "⚠️ Could not automatically close issue. "
            "Please close manually - ship was successful!"
        )
```

### Error Handling

Issue closing is **best-effort**:
- Ship workflow doesn't fail if issue closing fails
- Posts manual reminder if auto-close fails
- Logs warnings but continues to success state

**Philosophy:** Better to have a successful ship with open issue than to fail ship because of GitHub API issues.

### Success Message

After issue closing, an additional success message is posted for context:

```python
make_issue_comment(
    issue_number,
    format_issue_message(adw_id, AGENT_SHIPPER,
        "🎉 **Successfully shipped!**\n\n"
        "✅ Validated all state fields\n"
        "✅ Found and merged PR via GitHub API\n"
        "✅ Branch `{branch_name}` merged to main\n\n"
        "🚢 Code has been deployed to production!")
)
```

---

## Complete Workflow Lifecycle Example

### Scenario: Implementing Issue #42 (Add Dark Mode Toggle)

#### Stage 1: Pre-Launch

```bash
# User triggers workflow
cd adws/
uv run adw_sdlc_complete_iso.py 42

# Pre-flight checks run
✅ Git State: Clean
✅ Ports: Available (9100, 9200)
✅ Tests: 98% passing
✅ Disk Space: 45GB free
✅ Python Env: Ready

# Workflow launches
```

#### Stage 2: Execution

```
Plan Phase    → Creates implementation plan
Validate Phase → Detects baseline errors (0 found)
Build Phase   → Implements dark mode toggle
Lint Phase    → Checks code style (pass)
Test Phase    → Runs tests (pass)
Review Phase  → Validates implementation (pass)
Doc Phase     → Generates documentation (pass)
Ship Phase    → Merges PR #123 (pass)
```

#### Stage 3: Success Handling

```python
# Ship phase completes
✅ PR #123 merged to main
✅ Commits verified on main
✅ Issue #42 closed automatically

# GitHub issue shows:
🎉 **Successfully Shipped!**
✅ PR merged to main via GitHub API
✅ Branch feature-issue-42-dark-mode-toggle deployed to production
✅ All validation checks passed
**Issue Status:** Automatically closing as resolved.
```

### Scenario: Failure at Build Phase

```bash
# Build phase fails with TypeScript errors
❌ Build Phase Failed

# Automatic cleanup triggers:
1. Finds PR #124 for branch feature-issue-42-dark-mode
2. Closes PR with comment:
   "❌ Workflow Failed - Closing PR
   This PR is being automatically closed because the workflow
   failed during the Build phase.

   Error Details:
   TypeScript error in DarkModeToggle.tsx:15..."

3. Posts failure summary to issue #42:
   "🚨 Workflow Failure Report
   Workflow ID: a1b2c3d4
   Failed Phase: Build
   PR: #124 (automatically closed)..."

4. Marks workflow as failed
```

---

## Configuration & Customization

### Pre-flight Check Configuration

```python
# app/server/core/preflight_checks.py

# Adjust thresholds
MIN_DISK_SPACE_GB = 1.0  # Minimum free space
TEST_PASS_RATE_THRESHOLD = 0.8  # 80% tests passing

# Enable/disable specific checks
ENABLE_GIT_CHECK = True  # Always recommended
ENABLE_PORT_CHECK = True
ENABLE_TEST_CHECK = True
ENABLE_DISK_CHECK = True
ENABLE_PYTHON_CHECK = True
```

### Cleanup Configuration

```python
# adws/adw_modules/failure_cleanup.py

# Control cleanup behavior
AUTO_CLOSE_PRS = True  # Disable for testing
TRUNCATE_ERROR_DETAILS = 500  # Max chars in error message
COMMENT_TEMPLATE = "..."  # Customize PR close comment
```

### Issue Closing Configuration

```python
# adws/adw_ship_iso.py

# Control issue closing
AUTO_CLOSE_ISSUES = True  # Disable for testing
SUCCESS_COMMENT_TEMPLATE = "..."  # Customize success message
```

---

## Monitoring & Observability

### Key Metrics

Track these metrics to monitor robustness system health:

1. **Pre-flight Check Metrics**
   - Check pass rate by type
   - Blocked workflows (git state failures)
   - Average check execution time

2. **Cleanup Metrics**
   - Failed workflows cleaned up
   - PRs automatically closed
   - Cleanup success rate

3. **Issue Closing Metrics**
   - Issues automatically closed
   - Issue close success rate
   - Manual close fallback rate

### Logging

All components log extensively:

```python
# Pre-flight checks
logger.info("✅ Git state check passed")
logger.warning("⚠️ Port 9100 in use, trying 9101")
logger.error("❌ Git state check BLOCKED workflow launch")

# Cleanup
logger.info("Starting failure cleanup for adw_id")
logger.info("✅ Closed PR #123 with failure comment")
logger.warning("Failed to close PR during cleanup")

# Issue closing
logger.info("Closing issue #42...")
logger.info("✅ Closed issue #42 with success comment")
logger.warning("Failed to close issue: network timeout")
```

### Dashboard Integration

Pre-flight checks integrate with the WorkflowDashboard:

```typescript
// app/client/src/components/WorkflowDashboard.tsx
<PreflightCheckPanel />
```

Shows real-time system health and blocks manual workflow launches if critical checks fail.

---

## Troubleshooting

### Pre-flight Checks

#### Problem: Git State Check Always Failing

**Symptom:** Workflows blocked with "uncommitted changes" error

**Diagnosis:**
```bash
git status
```

**Solution:**
```bash
# Commit changes
git add .
git commit -m "Your message"

# Or stash changes
git stash

# Or discard changes (careful!)
git reset --hard HEAD
```

#### Problem: Port Check Warns About Full Ports

**Symptom:** "All ports in use" warning

**Diagnosis:**
```bash
# Check what's using ports
lsof -i :9100-9114
lsof -i :9200-9214
```

**Solution:**
```bash
# Kill stale worktree processes
pkill -f "port 9100"

# Or use cleanup script
./scripts/cleanup_stale_worktrees.sh
```

### Cleanup System

#### Problem: PR Not Closed After Failure

**Symptom:** Failed workflow but PR still open

**Diagnosis:**
```bash
# Check cleanup logs
cat agents/<adw-id>/<phase>/raw_output.jsonl | grep cleanup
```

**Solution:**
```bash
# Manually close PR
gh pr close <pr-number> --comment "Manually closing after workflow failure"
```

#### Problem: Cleanup Logs Show "No PR Found"

**Symptom:** Cleanup runs but can't find PR

**Diagnosis:**
```bash
# Check if PR was created
gh pr list --head <branch-name>

# Check branch name in state
cat agents/<adw-id>/adw_state.json | jq .branch_name
```

**Solution:**
- PR might not have been created yet (early phase failure)
- This is expected behavior - no PR to clean up

### Issue Closing

#### Problem: Issue Not Closed After Ship

**Symptom:** Ship succeeds but issue remains open

**Diagnosis:**
```bash
# Check ship logs
cat agents/<adw-id>/ship/raw_output.jsonl | grep "Closing issue"
```

**Solution:**
```bash
# Manually close issue
gh issue close <issue-number> --comment "Manually closing after successful ship"
```

#### Problem: Ship Fails with "Could not close issue"

**Symptom:** Ship phase logs warning about issue closing

**Diagnosis:**
- GitHub API timeout
- Network connectivity issue
- Permissions issue (rare)

**Solution:**
- Check issue comments for manual close reminder
- Manually close issue if needed
- Ship is still successful (issue closing is best-effort)

---

## Testing

### Pre-flight Checks

```bash
# Test pre-flight checks endpoint
curl http://localhost:8000/api/preflight-checks

# Expected response:
{
  "checks": [
    {
      "name": "Git State",
      "status": "pass",
      "message": "Working directory is clean",
      "blocking": true
    },
    ...
  ]
}
```

### Cleanup System

```bash
# Simulate failure in test workflow
cd adws/
uv run adw_test_iso.py 999 test-adw-id

# Verify cleanup:
# 1. Check if PR was closed
gh pr list --head feature-issue-999-*

# 2. Check issue comments
gh issue view 999

# 3. Check cleanup logs
cat agents/test-adw-id/test/raw_output.jsonl | grep cleanup
```

### Issue Closing

```bash
# Test ship workflow with mock issue
cd adws/
uv run adw_ship_iso.py 998 test-adw-id

# Verify issue closed:
gh issue view 998

# Check logs:
cat agents/test-adw-id/ship/raw_output.jsonl | grep "Closing issue"
```

---

## Best Practices

### For Users

1. **Before Launching Workflows:**
   - Check pre-flight status in dashboard
   - Ensure main branch is clean
   - Commit or stash local changes

2. **After Workflow Failures:**
   - Read failure summary in issue comments
   - Check closed PR for error details
   - Fix issues before retrying

3. **After Workflow Success:**
   - Verify issue is closed
   - Check closed PR for implementation details
   - Pull latest main to get changes

### For Developers

1. **Adding New Workflow Phases:**
   - Integrate cleanup at all failure points
   - Use best-effort error handling
   - Log all cleanup actions

2. **Modifying Pre-flight Checks:**
   - Document check purpose and thresholds
   - Make checks fast (<5s each)
   - Use warnings for non-critical checks

3. **Debugging Robustness Issues:**
   - Check logs in `agents/<adw-id>/`
   - Verify GitHub API responses
   - Test with mock workflows first

---

## Future Enhancements

### Planned Improvements

1. **Enhanced Pre-flight Checks:**
   - API quota check (prevent mid-execution failures)
   - Dependency conflict detection
   - Branch protection rule validation

2. **Smarter Cleanup:**
   - Partial PR cleanup (close but keep branch)
   - Automatic retry for transient failures
   - Resource usage cleanup (disk space, etc.)

3. **Better Issue Management:**
   - Automatic issue reopening if ship fails
   - Issue labels based on phase failures
   - Issue milestone tracking

4. **Monitoring Dashboard:**
   - Real-time robustness metrics
   - Failure trend analysis
   - Cost per failure analysis

### Ideas for Exploration

- Self-healing workflows (automatic retry with fixes)
- Predictive failure detection (ML-based)
- Multi-issue coordination (prevent conflicts)
- Rollback on failed ship (automatic revert)

---

## Related Documentation

- **ADW Workflow Best Practices:** `docs/ADW_WORKFLOW_BEST_PRACTICES.md`
- **ADW Failure Analysis:** `docs/ADW_FAILURE_ANALYSIS_AND_FIX_PROTOCOL.md`
- **ADW Completion Guide:** `docs/ADW_COMPLETION_GUIDE.md`
- **Pre-flight Checks Implementation:** `app/server/core/preflight_checks.py`
- **Cleanup Module:** `adws/adw_modules/failure_cleanup.py`
- **Ship Workflow:** `adws/adw_ship_iso.py`

---

## Changelog

### Version 1.0 (2025-11-25)

**Added:**
- Pre-flight check system (5 checks)
- Automatic PR cleanup on failure
- Automatic issue closing on success
- Comprehensive documentation

**Fixed:**
- Worktree pollution from uncommitted changes
- Orphaned PRs from failed workflows
- Manual issue closing requirement

**Status:** Production ready, all features tested

---

## Appendix: Code Locations

### Pre-flight Check System

| Component | Location |
|-----------|----------|
| Core checks | `app/server/core/preflight_checks.py` |
| API endpoint | `app/server/routes/system_routes.py` |
| UI component | `app/client/src/components/PreflightCheckPanel.tsx` |
| Webhook integration | `adws/adw_triggers/trigger_webhook.py` |
| Dashboard integration | `app/client/src/components/WorkflowDashboard.tsx` |

### Cleanup System

| Component | Location |
|-----------|----------|
| Core cleanup | `adws/adw_modules/failure_cleanup.py` |
| Find PR helper | `adws/adw_modules/failure_cleanup.py:18` |
| Close PR function | `adws/adw_modules/failure_cleanup.py:116` |
| Format summary | `adws/adw_modules/failure_cleanup.py:167` |
| Integration points | `adws/adw_sdlc_complete_iso.py` (all phases) |

### Issue Closing System

| Component | Location |
|-----------|----------|
| Core logic | `adws/adw_ship_iso.py:472-518` |
| Success comment template | `adws/adw_ship_iso.py:480-494` |
| Error handling | `adws/adw_ship_iso.py:500-514` |
| Docstring | `adws/adw_ship_iso.py:6-32` |

---

**Document Version:** 1.0
**Author:** TAC Webbuilder Team
**Maintained By:** Claude Code
**License:** MIT
