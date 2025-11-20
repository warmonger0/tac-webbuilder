#!/bin/bash
# Script to archive workflow history records for specific issues
# Usage: ./scripts/archive_workflows.sh <issue_number> [issue_number2 ...]
#
# This script:
# 1. Copies workflow_history records to workflow_history_archive
# 2. Removes them from the active workflow_history table
# 3. Prevents archived issues from appearing in the history panel

set -e

DB_PATH="app/server/db/workflow_history.db"

if [ $# -eq 0 ]; then
    echo "Usage: $0 <issue_number> [issue_number2 ...]"
    echo "Example: $0 999 6 13"
    exit 1
fi

# Build comma-separated list of issue numbers
ISSUES=$(IFS=,; echo "$*")

echo "Archiving workflow records for issues: $ISSUES"

# Check if archive table exists
sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_history_archive';" | grep -q "workflow_history_archive" || {
    echo "Error: Archive table does not exist. Please run the initial archive setup first."
    exit 1
}

# Count records to be archived
RECORD_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM workflow_history WHERE issue_number IN ($ISSUES);")

if [ "$RECORD_COUNT" -eq 0 ]; then
    echo "No records found for issues: $ISSUES"
    exit 0
fi

echo "Found $RECORD_COUNT records to archive"

# Archive the records
sqlite3 "$DB_PATH" "
INSERT INTO workflow_history_archive (
    original_id, adw_id, issue_number, nl_input, github_url, workflow_template,
    model_used, status, start_time, end_time, duration_seconds, error_message,
    phase_count, current_phase, success_rate, retry_count, worktree_path,
    backend_port, frontend_port, concurrent_workflows, input_tokens, output_tokens,
    cached_tokens, cache_hit_tokens, cache_miss_tokens, total_tokens,
    cache_efficiency_percent, estimated_cost_total, actual_cost_total,
    estimated_cost_per_step, actual_cost_per_step, cost_per_token,
    structured_input, cost_breakdown, token_breakdown, worktree_reused,
    steps_completed, steps_total, created_at, updated_at, archive_reason
)
SELECT
    id, adw_id, issue_number, nl_input, github_url, workflow_template,
    model_used, status, start_time, end_time, duration_seconds, error_message,
    phase_count, current_phase, success_rate, retry_count, worktree_path,
    backend_port, frontend_port, concurrent_workflows, input_tokens, output_tokens,
    cached_tokens, cache_hit_tokens, cache_miss_tokens, total_tokens,
    cache_efficiency_percent, estimated_cost_total, actual_cost_total,
    estimated_cost_per_step, actual_cost_per_step, cost_per_token,
    structured_input, cost_breakdown, token_breakdown, worktree_reused,
    steps_completed, steps_total, created_at, updated_at,
    'Archived via script on ' || datetime('now')
FROM workflow_history
WHERE issue_number IN ($ISSUES);
"

# Delete from active table
sqlite3 "$DB_PATH" "DELETE FROM workflow_history WHERE issue_number IN ($ISSUES);"

# Verify
ARCHIVED=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM workflow_history_archive WHERE issue_number IN ($ISSUES);")
REMAINING=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM workflow_history WHERE issue_number IN ($ISSUES);")

echo "✓ Archived $ARCHIVED records"
echo "✓ Remaining in active table: $REMAINING"
echo "✓ Issues $ISSUES will no longer appear in the history panel"
