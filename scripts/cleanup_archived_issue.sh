#!/bin/bash
#
# Cleanup documentation for a specific archived issue
#
# This script manually runs the cleanup workflow for a completed issue.
# It moves specs and related docs to the archived issues folder.
#
# Usage:
#   ./scripts/cleanup_archived_issue.sh <issue-number> <adw-id>
#
# Example:
#   ./scripts/cleanup_archived_issue.sh 33 88405eb3
#

set -e

# Check arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <issue-number> <adw-id>"
    echo ""
    echo "Example: $0 33 88405eb3"
    exit 1
fi

ISSUE_NUMBER=$1
ADW_ID=$2

echo "=========================================="
echo "Cleanup Archived Issue Documentation"
echo "=========================================="
echo ""
echo "Issue Number: $ISSUE_NUMBER"
echo "ADW ID: $ADW_ID"
echo ""

# Confirm
read -p "Continue with cleanup? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted"
    exit 0
fi

# Run cleanup workflow
cd "$(dirname "$0")/.."
uv run adws/adw_cleanup_iso.py "$ISSUE_NUMBER" "$ADW_ID"

echo ""
echo "=========================================="
echo "Cleanup completed"
echo "=========================================="
