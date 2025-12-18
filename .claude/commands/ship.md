---
description: Complete shipping workflow - docs, commits, push, merge, cleanup, and health checks
---

# Ship - Complete Release Workflow

Executes the complete workflow to ship changes:
1. Update documentation to capture session work
2. Commit all changes with proper messages
3. Push to origin
4. Merge to main branch
5. Prune outdated worktrees
6. Verify all preflight health checks pass

## Usage

`/ship [session_summary]`

**Examples:**
- `/ship` - Interactive mode (asks about session work)
- `/ship Added WebSocket support to Panel 8` - Quick ship with summary

## Workflow Steps

### Step 1: Update Documentation

Follow the `/updatedocs` workflow:

1. **Analyze session work:**
   ```bash
   git log -5 --oneline --no-decorate
   git status
   git diff --stat main
   ```

2. **Determine what documentation needs updating:**
   - Feature docs (app_docs/)
   - Quick start guides (.claude/commands/quick_start/)
   - Reference docs (.claude/commands/references/)
   - Prime command (.claude/commands/prime.md) - only for significant changes
   - Conditional docs (.claude/commands/conditional_docs.md)

3. **Update relevant documentation files** using Edit tool

4. **Report documentation updates** to user

**Note:** If user provided a session summary, use it to guide documentation updates. Otherwise, analyze git history and ask clarifying questions with AskUserQuestion tool.

### Step 2: Commit All Changes

**CRITICAL:** Follow commit message rules from CLAUDE.md:
- ❌ Never include "🤖 Generated with [Claude Code]"
- ❌ Never include "Co-Authored-By: Claude"
- ❌ No AI generation references

1. **Stage all changes:**
   ```bash
   git add .
   ```

2. **Review what will be committed:**
   ```bash
   git status
   git diff --cached --stat
   ```

3. **Create professional commit message:**
   - Format: `<type>: <description>`
   - Types: feat, fix, docs, refactor, perf, test, chore
   - Focus on technical changes only
   - Be concise but descriptive

4. **Commit changes:**
   ```bash
   git commit -m "$(cat <<'EOF'
   <type>: <description>

   <optional body explaining changes>
   EOF
   )"
   ```

**Example commit messages:**
```
docs: Update documentation for WebSocket migration

Updated quick start and reference docs to reflect
completion of WebSocket real-time updates in 5/6 panels.
```

```
feat: Add phase queue repository optimization

Replaced N+1 query patterns with direct database queries
using new find_by_id() method. 100x faster for large queues.
```

### Step 3: Push to Origin

1. **Verify current branch:**
   ```bash
   git branch --show-current
   ```

2. **Push to origin:**
   ```bash
   git push origin $(git branch --show-current)
   ```

3. **Handle errors:**
   - If push rejected: `git pull --rebase origin $(git branch --show-current)`
   - If conflicts: Stop workflow and report to user
   - If upstream not set: `git push -u origin $(git branch --show-current)`

### Step 4: Merge to Main

**Only proceed if:**
- Current branch is NOT main
- All commits are pushed
- No conflicts exist

1. **Switch to main:**
   ```bash
   git checkout main
   ```

2. **Pull latest changes:**
   ```bash
   git pull origin main
   ```

3. **Merge feature branch:**
   ```bash
   BRANCH_NAME=$(git branch --show-current)
   git checkout main
   git merge $BRANCH_NAME --no-ff -m "Merge $BRANCH_NAME"
   ```

4. **Push merged main:**
   ```bash
   git push origin main
   ```

5. **Return to original branch (or stay on main):**
   ```bash
   # Ask user if they want to stay on main or return to branch
   ```

**If already on main:**
- Skip merge step
- Just ensure main is pushed to origin

### Step 5: Prune Outdated Worktrees

1. **List all worktrees:**
   ```bash
   git worktree list
   ```

2. **Identify stale worktrees:**
   - Worktrees for completed issues
   - Worktrees with no recent activity
   - Broken/inaccessible worktrees

3. **Prune broken references:**
   ```bash
   git worktree prune --verbose
   ```

4. **Remove stale worktrees:**
   ```bash
   # For each stale worktree in trees/ directory
   for tree in trees/*/; do
     if [ -d "$tree" ]; then
       # Check if worktree is still active
       ADW_ID=$(basename "$tree")
       # Remove if directory exists but not in git worktree list
       git worktree remove "$tree" 2>/dev/null || rm -rf "$tree"
     fi
   done
   ```

5. **Report pruned worktrees:**
   ```
   Worktrees Cleaned:
   ✅ Pruned 3 broken references
   ✅ Removed 2 stale worktrees: trees/adw-abc123/, trees/adw-def456/
   ✅ Current worktrees: 1 active
   ```

**Safety checks:**
- Never remove worktree if it has uncommitted changes
- Warn user before removing active worktrees
- Skip removal if worktree is locked

### Step 6: Run Preflight Health Checks

Execute all health checks to verify system is operational:

1. **Run script-based health check:**
   ```bash
   ./scripts/health_check.sh
   ```

2. **Run API preflight checks:**
   ```bash
   curl -s http://localhost:8002/api/v1/preflight-checks | jq
   ```

3. **Verify all checks pass:**
   - Database connection ✓
   - GitHub authentication ✓
   - Environment variables ✓
   - Required tools installed ✓
   - Port availability ✓
   - File permissions ✓
   - Observability system ✓
   - Hook events recording ✓
   - Pattern analysis system ✓

4. **Report results:**
   ```
   Preflight Checks:
   ✅ All 9 checks passed

   System Status:
   ✅ Backend: Running on port 8002
   ✅ Database: PostgreSQL connected
   ✅ GitHub: Authenticated
   ✅ Observability: Recording events
   ```

**If any checks fail:**
- Report which checks failed
- Suggest remediation steps
- Ask user if they want to proceed anyway or fix issues first

### Step 7: Final Report

Provide comprehensive summary of all actions:

```
🚀 Ship Complete

📝 Documentation Updated:
   ✅ app_docs/feature-168-loop-prevention.md (created)
   ✅ .claude/commands/quick_start/adw.md (updated)
   ✅ .claude/commands/references/adw_workflows.md (updated)
   ✅ .claude/commands/prime.md (updated - Session 19 milestone)

💾 Commits:
   ✅ feat: Add dual-layer loop prevention to ADW workflows
   ✅ docs: Document loop prevention system (Issue #168)
   Total: 2 commits

🔄 Git Operations:
   ✅ Pushed to origin/feature-168-loop-prevention
   ✅ Merged to main
   ✅ Pushed main to origin

🧹 Cleanup:
   ✅ Pruned 3 broken worktree references
   ✅ Removed 2 stale worktrees (adw-abc123, adw-def456)
   ✅ Active worktrees: 1

✅ Health Checks:
   ✅ All 9 preflight checks passed
   ✅ System operational

Ready for next task!
```

## Error Handling

### Documentation Update Fails
- Report which files couldn't be updated
- Continue with commits if changes are staged
- Note documentation gaps in final report

### Commit Fails
- Show git error message
- Common issues:
  - No changes to commit (skip to push)
  - Pre-commit hook failures (show output)
  - Commit message validation errors

### Push Fails
- Show error (rejected, no upstream, network)
- Suggest fix (pull, set upstream, check network)
- Ask if user wants to continue without push

### Merge Conflicts
- **STOP workflow immediately**
- Report conflict details
- Suggest manual resolution
- Do NOT attempt automatic conflict resolution

### Worktree Removal Fails
- Report which worktrees couldn't be removed
- Suggest manual cleanup if necessary
- Continue to health checks

### Health Checks Fail
- Report which checks failed
- Provide detailed failure reasons
- Suggest fixes based on failure type
- Ask user if they want to:
  - Fix issues now
  - Continue anyway (if non-critical)
  - Abort and investigate

## Safety Guidelines

1. **Never force push** unless explicitly requested by user
2. **Never delete uncommitted changes**
3. **Always ask before merging** if conflicts might exist
4. **Preserve user data** - never remove worktrees with uncommitted work
5. **Report all actions** - transparency is critical
6. **Fail safely** - if uncertain, ask user before proceeding

## When to Use This Command

**Use `/ship` when:**
- ✅ Completing a feature or issue
- ✅ End of coding session
- ✅ Ready to deploy changes
- ✅ Want to ensure everything is clean and working

**Don't use `/ship` when:**
- ❌ Work in progress (not ready to commit)
- ❌ Experimenting with changes
- ❌ In middle of debugging
- ❌ Waiting for test results

## Related Commands

- `/updatedocs` - Just update documentation (no commits/push)
- `/done <issue>` - Mark issue complete and close on GitHub
- `/commit` - Just commit changes (no push/merge)
- `/preflight` - Just run health checks (no commits)

## Notes

- This command automates the complete shipping workflow
- Each step can fail independently - workflow stops on critical errors
- Non-critical errors are reported but workflow continues
- Always asks for confirmation before destructive operations
- Follows commit message rules from CLAUDE.md (no AI attribution)
