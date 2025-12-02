#!/bin/bash
# cleanup_closed_adws.sh
#
# Automatically archives ADW directories for closed GitHub issues.
# This prevents closed issues from cluttering the ADW monitor UI.
#
# Usage:
#   ./scripts/cleanup_closed_adws.sh
#
# Requirements:
#   - gh CLI (GitHub CLI)
#   - jq (JSON processor)
#   - Running backend server on localhost:8000

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
AGENTS_DIR="$PROJECT_ROOT/agents"
ARCHIVED_DIR="$AGENTS_DIR/_archived"

echo "🧹 ADW Cleanup Script"
echo "=================="
echo ""

# Check dependencies
if ! command -v gh &> /dev/null; then
    echo "❌ Error: 'gh' CLI is not installed"
    echo "   Install: brew install gh"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "❌ Error: 'jq' is not installed"
    echo "   Install: brew install jq"
    exit 1
fi

# Check backend is running
if ! curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠️  Warning: Backend server not responding at localhost:8000"
    echo "   Make sure the server is running before continuing"
    exit 1
fi

# Create _archived directory if it doesn't exist
mkdir -p "$ARCHIVED_DIR"

cd "$AGENTS_DIR"

echo "📊 Fetching active workflows from ADW monitor..."
workflows=$(curl -s http://localhost:8000/api/v1/adw-monitor | jq -r '.workflows')
workflow_count=$(echo "$workflows" | jq 'length')

echo "Found $workflow_count workflows in ADW monitor"
echo ""

if [ "$workflow_count" -eq 0 ]; then
    echo "✅ No workflows to clean up"
    exit 0
fi

archived_count=0

# Get all workflow data at once for efficiency
echo "$workflows" | jq -c '.[]' | while read -r workflow; do
    adw_id=$(echo "$workflow" | jq -r '.adw_id')
    issue_num=$(echo "$workflow" | jq -r '.issue_number')

    if [ -z "$issue_num" ] || [ "$issue_num" = "null" ]; then
        echo "⏭️  Skipping $adw_id (no issue number)"
        continue
    fi

    # Check if issue is closed on GitHub
    echo -n "Checking issue #$issue_num (ADW: $adw_id)... "
    issue_state=$(gh issue view "$issue_num" --json state --jq '.state' 2>/dev/null)

    if [ $? -ne 0 ]; then
        echo "❌ Error fetching issue"
        continue
    fi

    if [ "$issue_state" = "CLOSED" ]; then
        echo "CLOSED - archiving"

        # Archive main ADW directory
        if [ -d "$adw_id" ]; then
            mv "$adw_id" "$ARCHIVED_DIR/" && echo "  ✓ Archived $adw_id"
        fi

        # Archive external directories (build, lint, test)
        for pattern in adw_build_external adw_lint_external adw_test_external; do
            ext_dir="${pattern}_${adw_id}"
            if [ -d "$ext_dir" ]; then
                mv "$ext_dir" "$ARCHIVED_DIR/" && echo "  ✓ Archived $ext_dir"
            fi
        done

        ((archived_count++))
    else
        echo "OPEN - keeping"
    fi
done

echo ""
echo "=================="
echo "✅ Cleanup complete!"
echo "   Archived $archived_count closed workflow(s)"
echo ""
echo "💡 Tip: Clear browser cache and refresh to see updated ADW monitor"
