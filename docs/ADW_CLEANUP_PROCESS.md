# ADW Cleanup Process

## Overview

This document describes the process for cleaning up Autonomous Digital Worker (ADW) directories after GitHub issues are closed.

## Problem

The ADW Monitor (`/api/v1/adw-monitor` endpoint) scans the `/agents/` directory and displays **every** ADW state file it finds, regardless of whether the associated GitHub issue is open or closed. This causes closed issues to continue showing up in the UI, creating clutter and confusion.

## Root Cause

When an ADW workflow completes and the GitHub issue is closed, the agent directory (e.g., `/agents/adw-abc123/`) remains in the filesystem. The ADW monitor's `scan_adw_states()` function reads all directories in `/agents/` and displays them as active workflows.

## Solution: Manual Archiving

### Step 1: Identify Closed Issues in ADW Monitor

Check which workflows are showing in the ADW monitor:

```bash
curl -s http://localhost:8000/api/v1/adw-monitor | jq '.workflows[] | {adw_id, issue: .issue_number, status}'
```

### Step 2: Verify Issues are Closed on GitHub

For each issue number, check its status:

```bash
gh issue view <issue_number> --json state,title
```

### Step 3: Archive ADW Directories for Closed Issues

Move the ADW directories to the `_archived` subdirectory:

```bash
cd /path/to/tac-webbuilder/agents

# For a single ADW
mv <adw-id> _archived/

# For multiple ADWs
for adw_id in adw-abc123 adw-def456 xyz789; do
  [ -d "$adw_id" ] && mv "$adw_id" _archived/ && echo "Archived $adw_id"
done
```

### Step 4: Archive External ADW Directories

ADW workflows also create external agent directories for specific phases:

```bash
# Pattern: adw_<phase>_external_<adw-id>
# Examples: adw_build_external_abc123, adw_lint_external_abc123, adw_test_external_abc123

for pattern in adw_build_external adw_lint_external adw_test_external; do
  for adw_id in abc123 def456; do
    dir="${pattern}_${adw_id}"
    [ -d "$dir" ] && mv "$dir" _archived/ && echo "Archived $dir"
  done
done
```

### Step 5: Clean Up Database

Remove closed issues from the `phase_queue` table:

```python
from database.factory import get_database_adapter

adapter = get_database_adapter()
closed_issue_numbers = [111, 79, 83, ...]  # List of closed issues

with adapter.get_connection() as conn:
    cursor = conn.cursor()
    for issue_num in closed_issue_numbers:
        cursor.execute("DELETE FROM phase_queue WHERE issue_number = %s", (issue_num,))
    conn.commit()
```

### Step 6: Verify Cleanup

Wait for the ADW monitor cache to expire (5-6 seconds) and check:

```bash
curl -s http://localhost:8000/api/v1/adw-monitor | jq '{total: .summary.total, workflows: [.workflows[] | {adw_id, issue: .issue_number}]}'
```

## Automated Cleanup Script

### One-Time Bulk Cleanup

To clean up ALL closed issues at once:

```bash
#!/bin/bash
# cleanup_closed_adws.sh

cd /path/to/tac-webbuilder/agents

# Get all ADW IDs from monitor
adw_ids=$(curl -s http://localhost:8000/api/v1/adw-monitor | jq -r '.workflows[].adw_id')

for adw_id in $adw_ids; do
  # Extract issue number from monitor
  issue_num=$(curl -s http://localhost:8000/api/v1/adw-monitor | jq -r ".workflows[] | select(.adw_id == \"$adw_id\") | .issue_number")

  if [ -n "$issue_num" ] && [ "$issue_num" != "null" ]; then
    # Check if issue is closed
    issue_state=$(gh issue view $issue_num --json state --jq '.state' 2>/dev/null)

    if [ "$issue_state" = "CLOSED" ]; then
      echo "Archiving $adw_id for closed issue #$issue_num"
      [ -d "$adw_id" ] && mv "$adw_id" _archived/

      # Archive external directories
      for pattern in adw_build_external adw_lint_external adw_test_external; do
        ext_dir="${pattern}_${adw_id}"
        [ -d "$ext_dir" ] && mv "$ext_dir" _archived/
      done
    fi
  fi
done

echo "Cleanup complete!"
```

## UI Changes

### Removed "Current Workflow" Tab

The WorkflowDashboard component (Panel 2 - ADW's Panel) was updated to remove the "Current Workflow" tab:

**Before:**
- Tab 1: Workflow Catalog
- Tab 2: Current Workflow (showed active/completed workflows)

**After:**
- Only shows: Workflow Catalog (no tabs)

This change reduces clutter since the "Current Workflow" tab was showing closed issues.

**File:** `app/client/src/components/WorkflowDashboard.tsx`

## Testing

### Frontend Tests

Tests verify that the WorkflowDashboard:
- Only renders the AdwWorkflowCatalog component
- Does not show "Current Workflow" tab
- Does not render tab navigation
- Renders with correct structure

**File:** `app/client/src/components/__tests__/WorkflowDashboard.test.tsx`

**Run tests:**
```bash
cd app/client
npx vitest run WorkflowDashboard.test.tsx
```

**Expected output:**
```
✓ WorkflowDashboard > renders the workflow catalog
✓ WorkflowDashboard > does not show "Current Workflow" tab
✓ WorkflowDashboard > does not show "Workflow Catalog" tab
✓ WorkflowDashboard > does not render tab navigation
✓ WorkflowDashboard > renders with correct structure
✓ WorkflowDashboard > directly renders AdwWorkflowCatalog without state management

Test Files  1 passed (1)
Tests  6 passed (6)
```

### Backend Tests

ADW Monitor tests verify the scanning and aggregation functionality:

**Run tests:**
```bash
cd app/server
export DB_TYPE=sqlite && uv run pytest tests/core/test_adw_monitor.py -v
```

## Best Practices

1. **Archive regularly**: After closing GitHub issues, archive their ADW directories promptly
2. **Verify before archiving**: Always confirm the GitHub issue is closed before archiving
3. **Keep _archived clean**: Periodically clean out old archived directories (e.g., older than 30 days)
4. **Monitor disk space**: ADW directories can be large; monitor disk usage
5. **Database cleanup**: Always clean phase_queue when archiving ADWs

## Future Improvements

Potential automation options:

1. **Auto-archive on issue close**: GitHub webhook triggers archiving
2. **Scheduled cleanup**: Cron job runs daily to archive closed issues
3. **TTL-based cleanup**: Automatically archive workflows > 7 days old with closed issues
4. **UI indicator**: Show "archived" status for completed workflows

## Related Files

- **ADW Monitor Core**: `app/server/core/adw_monitor.py`
- **ADW Monitor Endpoint**: `app/server/routes/system_routes.py`
- **Frontend Component**: `app/client/src/components/WorkflowDashboard.tsx`
- **Frontend Tests**: `app/client/src/components/__tests__/WorkflowDashboard.test.tsx`
- **Phase Queue Service**: `app/server/services/phase_queue_service.py`

## Changelog

### 2025-12-02: Initial Documentation
- Documented manual archiving process
- Added bulk cleanup script
- Removed "Current Workflow" tab from UI
- Created frontend tests for WorkflowDashboard
- Archived 34 closed issue ADW directories
