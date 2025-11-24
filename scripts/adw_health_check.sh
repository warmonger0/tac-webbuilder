#!/bin/bash
# ADW Workflow Health Check
# Detects incomplete, failed, or stale workflows and provides actionable next steps

set -euo pipefail

echo "🏥 ADW Workflow Health Check"
echo "=============================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Find all non-archived ADW states
STATES=$(find agents -name "adw_state.json" -not -path "*/\\_archived/*")

HEALTHY=0
STUCK=0
FAILED=0
MISSING_PR=0

echo "Analyzing workflows..."
echo ""

for state_file in $STATES; do
    adw_id=$(jq -r '.adw_id // "unknown"' "$state_file")
    issue=$(jq -r '.issue_number // "unknown"' "$state_file")
    status=$(jq -r '.status // "unknown"' "$state_file")
    workflow=$(jq -r '.workflow_template // "unknown"' "$state_file")
    branch=$(jq -r '.branch_name // ""' "$state_file")
    start_time=$(jq -r '.start_time // ""' "$state_file")

    # Skip if no issue number
    if [ "$issue" = "unknown" ] || [ "$issue" = "null" ]; then
        continue
    fi

    # Calculate age if start time exists
    age_hours=""
    if [ -n "$start_time" ] && [ "$start_time" != "null" ]; then
        start_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${start_time%.*}" "+%s" 2>/dev/null || echo "0")
        now_epoch=$(date "+%s")
        age_seconds=$((now_epoch - start_epoch))
        age_hours=$((age_seconds / 3600))
    fi

    # Check issue status
    issue_state=$(gh issue view "$issue" --json state --jq '.state' 2>/dev/null || echo "UNKNOWN")

    # Check if PR exists
    pr_exists="NO"
    pr_number=""
    pr_merged=""
    if [ -n "$branch" ] && [ "$branch" != "null" ]; then
        pr_number=$(gh pr list --head "$branch" --json number --jq '.[0].number' 2>/dev/null || echo "")
        if [ -n "$pr_number" ]; then
            pr_exists="YES"
            pr_state=$(gh pr view "$pr_number" --json state --jq '.state' 2>/dev/null || echo "UNKNOWN")
            pr_merged=$(gh pr view "$pr_number" --json mergedAt --jq '.mergedAt' 2>/dev/null || echo "")
        fi
    fi

    # Determine health status
    health_status="UNKNOWN"
    action="None"

    if [ "$issue_state" = "CLOSED" ] && [ -n "$pr_merged" ]; then
        health_status="HEALTHY"
        action="Archive this workflow"
        ((HEALTHY++))
    elif [ "$status" = "running" ] && [ -n "$age_hours" ] && [ "$age_hours" -gt 3 ]; then
        health_status="STUCK"
        action="Investigate logs at agents/$adw_id/"
        ((STUCK++))
    elif [ "$status" = "running" ] && [ "$pr_exists" = "YES" ] && [ "$pr_state" = "OPEN" ]; then
        # Check if PR has passing CI
        pr_checks=$(gh pr view "$pr_number" --json statusCheckRollup --jq '.statusCheckRollup | length' 2>/dev/null || echo "0")
        pr_checks_pass=$(gh pr view "$pr_number" --json statusCheckRollup --jq '.statusCheckRollup | map(select(.conclusion == "SUCCESS" or .conclusion == "NEUTRAL")) | length' 2>/dev/null || echo "0")

        if [ "$pr_checks" -gt 0 ] && [ "$pr_checks" -eq "$pr_checks_pass" ]; then
            health_status="BLOCKED-CI-PASS"
            action="Review isolated test failure, consider manual merge"
            ((FAILED++))
        else
            health_status="STUCK"
            action="Check PR #$pr_number for CI failures"
            ((STUCK++))
        fi
    elif [ "$status" = "failed" ]; then
        health_status="FAILED"
        action="Review failure logs"
        ((FAILED++))
    elif [ "$status" = "running" ] && [ "$pr_exists" = "NO" ]; then
        health_status="NO-PR"
        action="Workflow may have failed early"
        ((MISSING_PR++))
    fi

    # Color code output
    case "$health_status" in
        "HEALTHY")
            color="$GREEN"
            ;;
        "STUCK"|"NO-PR")
            color="$YELLOW"
            ;;
        "FAILED"|"BLOCKED-CI-PASS")
            color="$RED"
            ;;
        *)
            color="$NC"
            ;;
    esac

    # Print status
    printf "${color}%-15s${NC} Issue #%-4s | %-25s | %s\n" \
        "[$health_status]" \
        "$issue" \
        "${workflow:0:25}" \
        "$action"

    if [ -n "$pr_number" ]; then
        echo "                  └─ PR #$pr_number (${pr_state:-UNKNOWN})"
    fi

    if [ -n "$age_hours" ]; then
        echo "                  └─ Age: ${age_hours}h"
    fi

    echo ""
done

# Summary
echo "=============================="
echo "Summary:"
echo "  ${GREEN}✓ Healthy:${NC}    $HEALTHY"
echo "  ${YELLOW}⚠ Stuck:${NC}      $STUCK"
echo "  ${RED}✗ Failed:${NC}     $FAILED"
echo "  ${YELLOW}○ No PR:${NC}      $MISSING_PR"
echo ""

# Recommendations
if [ $((STUCK + FAILED + MISSING_PR)) -gt 0 ]; then
    echo "🔧 Recommended Actions:"
    echo ""

    if [ $FAILED -gt 0 ]; then
        echo "1. ${RED}Failed Workflows:${NC}"
        echo "   Run: scripts/adw_recovery.sh <adw-id>"
        echo ""
    fi

    if [ $STUCK -gt 0 ]; then
        echo "2. ${YELLOW}Stuck Workflows:${NC}"
        echo "   Check logs: cat agents/<adw-id>/*/execution.log"
        echo "   Kill if needed: scripts/kill_adw.sh <adw-id>"
        echo ""
    fi

    if [ $MISSING_PR -gt 0 ]; then
        echo "3. ${YELLOW}No PR Workflows:${NC}"
        echo "   These likely failed during planning/build"
        echo "   Archive with: mv agents/<adw-id> agents/_archived/"
        echo ""
    fi

    exit 1
else
    echo "✅ All workflows healthy!"
    exit 0
fi
