---
description: Nuclear reset - completely obliterate a failed workflow and restart fresh
---

# Workflow Nuclear Reset (Development Only)

**⚠️ WARNING: This command is DESTRUCTIVE and should only be used in development!**

Completely resets a failed workflow by:
1. Deleting GitHub issue and PRs
2. Clearing queue/hopper entries
3. Removing git worktrees and branches
4. Cleaning database entries
5. Removing ADW state directories
6. Restarting all services
7. Running preflight checks

## Usage

`/nuke <issue_number> [--keep-remote-branch]`

Example:
- `/nuke 123` - Nuclear reset for issue #123
- `/nuke 123 --keep-remote-branch` - Reset but don't delete remote branch

## Execution Steps

### Step 1: Rate Limit Check (Logic Gate)
**CRITICAL:** Before any GitHub operations, check rate limits:
```bash
curl -s -H "Authorization: Bearer $(gh auth token)" \
  https://api.github.com/rate_limit | jq '.resources.core'
```

If remaining < 100, ABORT and warn user about rate limit exhaustion.

### Step 2: Gather Workflow Metadata
```bash
# Read backend port
BACKEND_PORT=$(grep BACKEND_PORT .ports.env | cut -d '=' -f2 || echo "8002")

# Get queue items for this issue
QUEUE_DATA=$(curl -s "http://localhost:${BACKEND_PORT}/api/v1/queue" | jq ".phases[] | select(.issue_number == <issue_number>)")

# Extract metadata
QUEUE_IDS=$(echo "$QUEUE_DATA" | jq -r '.queue_id')
ADW_IDS=$(echo "$QUEUE_DATA" | jq -r '.adw_id // empty')
PR_NUMBERS=$(echo "$QUEUE_DATA" | jq -r '.pr_number // empty')

# Also check for PRs via GitHub API
GH_PRS=$(gh pr list --json number,title --search "<issue_number> in:title" | jq -r '.[].number')
PR_NUMBERS="$PR_NUMBERS $GH_PRS"
```

### Step 3: Delete GitHub Issue and PRs
```bash
echo "🗑️  Deleting GitHub artifacts..."

# Close/delete PRs (close is safer than delete)
for pr in $PR_NUMBERS; do
  [ -z "$pr" ] && continue
  echo "  Closing PR #$pr"
  gh pr close $pr --delete-branch || true
done

# Close the issue (with confirmation that it's a failed workflow)
echo "  Closing issue #<issue_number>"
gh issue close <issue_number> --comment "♻️ Workflow reset - restarting from scratch"
```

### Step 4: Clear Queue/Hopper
```bash
echo "🧹 Clearing queue entries..."

for queue_id in $QUEUE_IDS; do
  [ -z "$queue_id" ] && continue
  echo "  Removing queue entry: $queue_id"
  curl -s -X DELETE "http://localhost:${BACKEND_PORT}/api/v1/queue/${queue_id}"
done
```

### Step 5: Clean Git Artifacts
```bash
echo "🌲 Cleaning git worktrees and branches..."

# Clean worktrees for each ADW ID
for adw_id in $ADW_IDS; do
  [ -z "$adw_id" ] && continue
  echo "  Purging worktree for $adw_id"

  if [ "$1" == "--keep-remote-branch" ]; then
    ./scripts/purge_tree.sh "$adw_id" --keep-branch
  else
    ./scripts/purge_tree.sh "$adw_id"
  fi
done

# Clean up any stale worktrees
git worktree prune

# Also check for branches matching the issue number
ISSUE_BRANCHES=$(git branch -a | grep -i "issue-<issue_number>\|#<issue_number>" | sed 's/^[*+ ]*//' | grep -v "remotes/")
if [ ! -z "$ISSUE_BRANCHES" ]; then
  echo "  Found branches for issue #<issue_number>:"
  echo "$ISSUE_BRANCHES" | sed 's/^/    /'

  for branch in $ISSUE_BRANCHES; do
    # Switch off the branch if we're on it
    CURRENT_BRANCH=$(git branch --show-current)
    [ "$CURRENT_BRANCH" == "$branch" ] && git checkout main

    # Delete local branch
    git branch -D "$branch" 2>/dev/null || true
  done
fi
```

### Step 6: Clean Database Entries
```bash
echo "🗄️  Cleaning database entries..."

# PostgreSQL connection
PGPASSWORD=${POSTGRES_PASSWORD:-changeme}
PGHOST=${POSTGRES_HOST:-localhost}
PGPORT=${POSTGRES_PORT:-5432}
PGDATABASE=${POSTGRES_DB:-tac_webbuilder}
PGUSER=${POSTGRES_USER:-tac_user}

# Find psql (may not be in PATH on macOS)
PSQL_CMD=$(which psql 2>/dev/null || echo "/opt/homebrew/bin/psql")
if [ ! -f "$PSQL_CMD" ]; then
  PSQL_CMD="/opt/homebrew/Cellar/postgresql@16/16.10/bin/psql"
fi

# Clean workflow_history
for adw_id in $ADW_IDS; do
  [ -z "$adw_id" ] && continue
  echo "  Removing workflow_history for $adw_id"
  PGPASSWORD=$PGPASSWORD "$PSQL_CMD" -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE \
    -c "DELETE FROM workflow_history WHERE adw_id = '$adw_id';" 2>/dev/null || true
done

# Clean task_logs
echo "  Removing task_logs for issue #<issue_number>"
PGPASSWORD=$PGPASSWORD "$PSQL_CMD" -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE \
  -c "DELETE FROM task_logs WHERE issue_number = <issue_number>;" 2>/dev/null || true

# Clean work_log
echo "  Removing work_log for issue #<issue_number>"
PGPASSWORD=$PGPASSWORD "$PSQL_CMD" -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE \
  -c "DELETE FROM work_log WHERE issue_number = <issue_number>;" 2>/dev/null || true

# Clean user_prompts
echo "  Removing user_prompts for issue #<issue_number>"
PGPASSWORD=$PGPASSWORD "$PSQL_CMD" -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE \
  -c "DELETE FROM user_prompts WHERE github_issue_number = <issue_number>;" 2>/dev/null || true

# Clean planned_features
echo "  Removing planned_features for issue #<issue_number>"
PGPASSWORD=$PGPASSWORD "$PSQL_CMD" -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE \
  -c "DELETE FROM planned_features WHERE github_issue_number = <issue_number>;" 2>/dev/null || true

# Clean adw_locks
echo "  Removing adw_locks for issue #<issue_number>"
PGPASSWORD=$PGPASSWORD "$PSQL_CMD" -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE \
  -c "DELETE FROM adw_locks WHERE issue_number = <issue_number>;" 2>/dev/null || true

# Clean webhook_events
for adw_id in $ADW_IDS; do
  [ -z "$adw_id" ] && continue
  echo "  Removing webhook_events for $adw_id"
  PGPASSWORD=$PGPASSWORD "$PSQL_CMD" -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE \
    -c "DELETE FROM webhook_events WHERE adw_id = '$adw_id';" 2>/dev/null || true
done

# Clean hook_events (tool tracking)
for adw_id in $ADW_IDS; do
  [ -z "$adw_id" ] && continue
  echo "  Removing hook_events for $adw_id"
  PGPASSWORD=$PGPASSWORD "$PSQL_CMD" -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE \
    -c "DELETE FROM hook_events WHERE metadata->>'adw_id' = '$adw_id';" 2>/dev/null || true
done

# Clean tool_calls (linked via workflow_id from workflow_history)
for adw_id in $ADW_IDS; do
  [ -z "$adw_id" ] && continue
  echo "  Removing tool_calls for $adw_id"
  # First get workflow_id from workflow_history
  WORKFLOW_ID=$(PGPASSWORD=$PGPASSWORD "$PSQL_CMD" -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE \
    -t -c "SELECT workflow_id FROM workflow_history WHERE adw_id = '$adw_id';" 2>/dev/null | xargs)

  if [ ! -z "$WORKFLOW_ID" ]; then
    PGPASSWORD=$PGPASSWORD "$PSQL_CMD" -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE \
      -c "DELETE FROM tool_calls WHERE workflow_id = '$WORKFLOW_ID';" 2>/dev/null || true
  fi
done
```

### Step 7: Clean ADW State Directories
```bash
echo "📁 Removing ADW state directories..."

for adw_id in $ADW_IDS; do
  [ -z "$adw_id" ] && continue
  ADW_DIR="agents/$adw_id"

  if [ -d "$ADW_DIR" ]; then
    echo "  Removing $ADW_DIR"
    rm -rf "$ADW_DIR"
  fi
done
```

### Step 8: Restart Services
```bash
echo "🔄 Restarting all services..."

# Stop existing services
./scripts/stop_apps.sh

# Wait for ports to clear
sleep 3

# Start clean
./scripts/start_full_clean.sh &
START_PID=$!

# Wait for services to be ready (max 60 seconds)
echo "⏳ Waiting for services to start..."
for i in {1..60}; do
  if curl -s http://localhost:${BACKEND_PORT}/api/v1/health >/dev/null 2>&1; then
    echo "✅ Backend ready"
    break
  fi
  [ $i -eq 60 ] && echo "⚠️  Backend may still be starting..."
  sleep 1
done
```

### Step 9: Run Preflight Checks
```bash
echo "🔍 Running preflight checks..."

# Use the /preflight command
BACKEND_PORT=$(grep BACKEND_PORT .ports.env | cut -d '=' -f2 || echo "8002")
PREFLIGHT_RESULT=$(curl -s "http://localhost:${BACKEND_PORT}/api/v1/preflight-checks")

# Parse and display results
PASSED=$(echo "$PREFLIGHT_RESULT" | jq -r '.passed')
BLOCKING_FAILURES=$(echo "$PREFLIGHT_RESULT" | jq -r '.blocking_failures | length')

if [ "$PASSED" == "true" ]; then
  echo "✅ All preflight checks PASSED"
else
  echo "❌ Preflight checks FAILED ($BLOCKING_FAILURES blocking failures)"
  echo "$PREFLIGHT_RESULT" | jq -r '.blocking_failures[] | "  • \(.check): \(.error)\n    Fix: \(.fix)"'
  echo ""
  echo "⚠️  Fix the above issues before resubmitting workflow"
fi
```

### Step 10: Summary Report
```bash
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "♻️  Workflow Nuclear Reset Complete"
echo "═══════════════════════════════════════════════════════════"
echo "Issue: #<issue_number>"
echo ""
echo "GitHub Cleanup:"
echo "  • Queue entries removed: $(echo "$QUEUE_IDS" | wc -w)"
echo "  • PRs closed: $(echo "$PR_NUMBERS" | wc -w)"
echo "  • Issue #<issue_number> closed"
echo ""
echo "Database Cleanup (10 tables):"
echo "  • workflow_history (ADW execution records)"
echo "  • task_logs (phase completion logs)"
echo "  • work_log (work log entries)"
echo "  • user_prompts (user request capture)"
echo "  • planned_features (database planning)"
echo "  • adw_locks (workflow locks)"
echo "  • webhook_events (webhook deduplication)"
echo "  • hook_events (tool call tracking)"
echo "  • tool_calls (LLM tool invocations)"
echo "  • phase_queue (queue entries)"
echo ""
echo "Filesystem Cleanup:"
echo "  • ADW IDs cleaned: $(echo "$ADW_IDS" | wc -w)"
echo "  • Git worktrees removed: $(echo "$ADW_IDS" | wc -w)"
echo "  • ADW state directories removed"
echo ""
echo "System Status:"
echo "  • Services restarted: ✅"
echo "  • Preflight checks: $([[ "$PASSED" == "true" ]] && echo "✅ PASSED" || echo "❌ FAILED")"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Verify services are running at http://localhost:${FRONTEND_PORT}"
echo "  2. Re-submit the issue through Panel 1"
echo "  3. Monitor the new workflow in Panel 2"
echo ""
```

## Safety Checks

Before executing, confirm:
1. **Development environment only** - Check we're NOT on production
2. **Issue exists** - Verify issue number is valid
3. **User confirmation** - Ask "Are you sure you want to nuke issue #<issue_number>? (y/N)"
4. **Rate limit check** - Ensure sufficient GitHub API quota

## Error Handling

If any step fails:
- Log the error but continue with remaining cleanup
- Report all failures in the summary
- Suggest manual cleanup steps if needed

## Recovery

If the nuke fails partway through, you can:
1. Re-run the command (idempotent where possible)
2. Manually run individual cleanup scripts
3. Check logs: `/tmp/tac_backend.log`, `/tmp/tac_webhook.log`, `/tmp/tac_frontend.log`
