# ADW Workflow Completion Guide

## Why Issues Don't Auto-Complete

### The Problem: Strict Quality Gates

The `adw_sdlc_complete_iso` workflow has **9 sequential phases**:
1. Plan → 2. Validate → 3. Build → 4. Lint → 5. **Test** → 6. Review → 7. Document → 8. **Ship** → 9. Cleanup

**If ANY phase fails, subsequent phases don't run.**

This means:
- ❌ Test failures prevent reaching the Ship phase
- ❌ No merge happens (even if GitHub CI passes)
- ❌ Issues remain open indefinitely
- ❌ PRs sit unmerged with green checks

### Example: Issue #76

**Status:**
- ✅ PR #77 created with all changes
- ✅ GitHub CI passes (4/4 checks green)
- ❌ Isolated test failed: `test_active_locks_retrieval`
- ❌ Workflow aborted at Phase 5 (Test)
- ❌ Never reached Phase 8 (Ship)
- ❌ PR not merged, issue not closed

**Root Cause:** Flaky test that passes in GitHub CI but fails in isolated worktree environment.

---

## How to Ensure Issues Finish Correctly

### 1. Proactive Monitoring

**Daily Health Check:**
```bash
./scripts/adw_health_check.sh
```

This detects:
- 🟢 Healthy workflows (merged & closed)
- 🟡 Stuck workflows (running >3 hours)
- 🔴 Failed workflows (aborted with errors)
- 🔴 **CI-pass/isolated-fail** scenarios

**Output Example:**
```
[STUCK]        Issue #76   | adw_sdlc_complete_iso     | Investigate logs
               └─ PR #77 (OPEN)
               └─ Age: 65h

[BLOCKED-CI-PASS] Issue #XX | adw_sdlc_complete_iso    | Review isolated test failure
```

### 2. Comprehensive Failure Recovery

**For Stuck Workflows:**
```bash
./scripts/adw_recovery.sh <issue-number>
```

This tool:
1. **Analyzes** the workflow state
2. **Detects** CI-pass vs isolated-fail scenarios
3. **Recommends** recovery actions

**Recovery Options:**

#### Option A: Force Ship (Recommended when CI passes)
```bash
./scripts/adw_recovery.sh 76 --force-ship
```

This:
- Bypasses failed isolated tests
- Runs Phase 8 (Ship) directly
- Merges PR via `gh pr merge --squash`
- Automatically closes linked issues
- Verifies commits landed on main

#### Option B: Manual Merge (Quick fix)
```bash
gh pr merge 77 --squash --delete-branch
gh issue close 76 --comment "Merged via PR #77"
```

Use when:
- Force ship fails
- Merge conflicts need manual resolution
- Immediate deployment needed

#### Option C: Fix & Rerun (Thorough)
```bash
# Investigate test failure
cat agents/<adw-id>/adw_test_iso/execution.log

# Fix the test or code
cd trees/<adw-id>
# ... make fixes ...

# Rerun from last phase
uv run adws/adw_test_iso.py <issue> <adw-id>
uv run adws/adw_ship_iso.py <issue> <adw-id>
```

### 3. Handling Merge Conflicts

If PR has conflicts (like #76's `github_issue_service.py`):

```bash
# Fetch latest main
git worktree add conflict-fix feature-issue-76-adw-e7341a50-drag-drop-md-upload
cd conflict-fix

# Merge main and resolve
git merge origin/main
# ... resolve conflicts in editor ...

git add .
git commit -m "Resolve merge conflicts with main"
git push

# Then force ship
cd ../
./scripts/adw_recovery.sh 76 --force-ship
```

### 4. State Management

**Mark workflows as failed (not stuck):**
```bash
# Update state to reflect reality
jq '.status = "failed"' agents/<adw-id>/adw_state.json > tmp.$$ && mv tmp.$$ agents/<adw-id>/adw_state.json
```

**Archive completed workflows:**
```bash
mv agents/<adw-id> agents/_archived/<adw-id>_issue-<num>_$(date +%Y%m%d)
```

---

## Systematic Process for Completion

### Weekly Workflow:

1. **Monday Morning:**
   ```bash
   ./scripts/adw_health_check.sh
   ```
   Review all stuck/failed workflows

2. **For Each Stuck Workflow:**
   ```bash
   ./scripts/adw_recovery.sh <issue>
   ```
   Follow recommended recovery action

3. **CI-Pass Scenarios:**
   ```bash
   ./scripts/adw_recovery.sh <issue> --force-ship
   ```
   Ship immediately if CI green

4. **Merge Conflicts:**
   - Resolve in worktree
   - Push resolution
   - Force ship

5. **Archive Completed:**
   ```bash
   mv agents/<adw-id> agents/_archived/
   ```

### Automation Opportunities:

Create a cron job:
```bash
# .github/workflows/adw-health.yml
name: ADW Health Check
on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday 9am
jobs:
  health:
    runs-on: ubuntu-latest
    steps:
      - run: ./scripts/adw_health_check.sh
      - if: failure()
        run: |
          # Post to Slack/Discord
          # Create GitHub issue for stuck workflows
```

---

## Specific Fix for Issue #76

**Immediate Action:**
```bash
# 1. Check conflict status
gh pr view 77

# 2. Resolve conflict in github_issue_service.py
git worktree add /tmp/fix-76 feature-issue-76-adw-e7341a50-drag-drop-md-upload
cd /tmp/fix-76
git merge origin/main
# Fix conflicts
git add . && git commit -m "Resolve merge conflicts"
git push
cd -

# 3. Force ship
./scripts/adw_recovery.sh 76 --force-ship

# 4. Archive
mv agents/e7341a50 agents/_archived/e7341a50_issue-76_$(date +%Y%m%d)
```

**Prevent Recurrence:**
1. Fix the flaky `test_active_locks_retrieval` test
2. Add test retry logic for order-dependent tests
3. Improve isolated test environment to match GitHub CI

---

## Key Takeaways

### Why Issues Don't Auto-Complete:
1. **Strict quality gates** - Any phase failure stops progression
2. **No Phase 8 Ship** - No merge, no closure
3. **State not updated** - Workflows show "running" forever

### How to Ensure Completion:
1. **Run health checks** - `./scripts/adw_health_check.sh`
2. **Recover stuck workflows** - `./scripts/adw_recovery.sh <issue> --force-ship`
3. **Handle merge conflicts** - Resolve in worktree before shipping
4. **Archive completed** - Clean up agents directory

### When to Use Each Tool:

| Scenario | Command | Why |
|----------|---------|-----|
| Find stuck workflows | `adw_health_check.sh` | Proactive monitoring |
| CI passes, tests fail | `adw_recovery.sh N --force-ship` | Bypass flaky tests |
| Need investigation | `adw_recovery.sh N` | Get analysis first |
| Quick manual fix | `gh pr merge N --squash` | Immediate merge |
| Clean up | `mv agents/X _archived/` | Free resources |

### Red Flags:
- 🚩 Workflows "running" >3 hours
- 🚩 Green PR checks but no merge
- 🚩 Open issue with closed/merged PR
- 🚩 Test failures on specific tests repeatedly

**Next Steps:**
1. Run health check now: `./scripts/adw_health_check.sh`
2. Fix issue #76: Follow steps above
3. Schedule weekly health checks
4. Fix flaky tests identified in recovery logs
