#!/bin/bash
# ADW Recovery Script
# Handles stuck workflows and CI-pass/isolated-test-fail scenarios

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <adw-id|issue-number> [--force-ship]"
    echo ""
    echo "Options:"
    echo "  --force-ship    Force ship even if tests failed (use when CI passes)"
    echo ""
    echo "Examples:"
    echo "  $0 e7341a50                  # Analyze and suggest recovery"
    echo "  $0 76 --force-ship           # Force ship issue #76's PR"
    exit 1
fi

TARGET="$1"
FORCE_SHIP=false

if [ "${2:-}" = "--force-ship" ]; then
    FORCE_SHIP=true
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔧 ADW Recovery Tool${NC}"
echo "===================="
echo ""

# Find ADW state file
STATE_FILE=""
if [ -f "agents/$TARGET/adw_state.json" ]; then
    STATE_FILE="agents/$TARGET/adw_state.json"
else
    # Search by issue number
    STATE_FILE=$(find agents -name "adw_state.json" -not -path "*/_archived/*" -exec sh -c "jq -e '.issue_number == \"$TARGET\"' {} >/dev/null 2>&1 && echo {}" \; | head -1)
fi

if [ -z "$STATE_FILE" ] || [ ! -f "$STATE_FILE" ]; then
    echo -e "${RED}✗ Could not find ADW state for: $TARGET${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found state: $STATE_FILE${NC}"
echo ""

# Extract state
ADW_ID=$(jq -r '.adw_id' "$STATE_FILE")
ISSUE=$(jq -r '.issue_number' "$STATE_FILE")
STATUS=$(jq -r '.status' "$STATE_FILE")
BRANCH=$(jq -r '.branch_name' "$STATE_FILE")
WORKFLOW=$(jq -r '.workflow_template' "$STATE_FILE")

echo "ADW ID:    $ADW_ID"
echo "Issue:     #$ISSUE"
echo "Status:    $STATUS"
echo "Branch:    $BRANCH"
echo "Workflow:  $WORKFLOW"
echo ""

# Check if PR exists
PR_NUMBER=$(gh pr list --head "$BRANCH" --json number --jq '.[0].number' 2>/dev/null || echo "")

if [ -z "$PR_NUMBER" ]; then
    echo -e "${RED}✗ No PR found for branch: $BRANCH${NC}"
    echo ""
    echo "Recovery options:"
    echo "  1. Restart workflow from beginning"
    echo "  2. Archive this ADW (if duplicate or abandoned)"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Found PR: #$PR_NUMBER${NC}"
echo ""

# Get PR details
PR_STATE=$(gh pr view "$PR_NUMBER" --json state --jq '.state')
PR_MERGEABLE=$(gh pr view "$PR_NUMBER" --json mergeable --jq '.mergeable')
PR_CHECKS=$(gh pr view "$PR_NUMBER" --json statusCheckRollup --jq '.statusCheckRollup')
PR_CHECKS_PASS=$(echo "$PR_CHECKS" | jq '[.[] | select(.conclusion == "SUCCESS" or .conclusion == "NEUTRAL")] | length')
PR_CHECKS_TOTAL=$(echo "$PR_CHECKS" | jq 'length')

echo "PR State:       $PR_STATE"
echo "Mergeable:      $PR_MERGEABLE"
echo "CI Checks:      $PR_CHECKS_PASS/$PR_CHECKS_TOTAL passing"
echo ""

# Analyze scenario
if [ "$PR_STATE" = "MERGED" ]; then
    echo -e "${GREEN}✓ PR already merged!${NC}"
    echo ""
    echo "Recovery action: Archive this ADW"
    echo "  mv agents/$ADW_ID agents/_archived/${ADW_ID}_issue-${ISSUE}_$(date +%Y%m%d_%H%M%S)"
    exit 0
fi

if [ "$PR_STATE" = "CLOSED" ]; then
    echo -e "${YELLOW}⚠ PR is closed but not merged${NC}"
    echo ""
    echo "This workflow was manually closed. Archive ADW:"
    echo "  mv agents/$ADW_ID agents/_archived/"
    exit 0
fi

# Check for CI-pass / isolated-test-fail scenario
if [ "$PR_CHECKS_TOTAL" -gt 0 ] && [ "$PR_CHECKS_PASS" -eq "$PR_CHECKS_TOTAL" ]; then
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}⚠ DETECTED: CI passes but workflow stuck${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "This suggests isolated testing failed while GitHub CI passed."
    echo ""

    # Check test logs
    TEST_LOG="agents/$ADW_ID/adw_test_iso/execution.log"
    if [ -f "$TEST_LOG" ]; then
        echo "Last 10 lines of test log:"
        echo "---"
        tail -10 "$TEST_LOG"
        echo "---"
        echo ""
    fi

    if [ "$FORCE_SHIP" = true ]; then
        echo -e "${BLUE}🚢 Force shipping PR #$PR_NUMBER...${NC}"
        echo ""

        # Use the ship workflow
        echo "Running: uv run adws/adw_ship_iso.py $ISSUE $ADW_ID"
        if uv run adws/adw_ship_iso.py "$ISSUE" "$ADW_ID"; then
            echo ""
            echo -e "${GREEN}✓ Successfully shipped!${NC}"
            echo ""
            echo "Next steps:"
            echo "  1. Verify issue #$ISSUE is closed"
            echo "  2. Archive ADW: mv agents/$ADW_ID agents/_archived/"
        else
            echo ""
            echo -e "${RED}✗ Ship failed. Manual merge may be required.${NC}"
            echo ""
            echo "Manual merge:"
            echo "  gh pr merge $PR_NUMBER --squash --delete-branch"
            exit 1
        fi
    else
        echo "Recovery options:"
        echo ""
        echo -e "  ${GREEN}1. Force ship (recommended if CI passes):${NC}"
        echo "     $0 $ADW_ID --force-ship"
        echo ""
        echo -e "  ${YELLOW}2. Investigate test failure:${NC}"
        echo "     cat agents/$ADW_ID/adw_test_iso/execution.log"
        echo "     cd agents/$ADW_ID && pytest <failing-test>"
        echo ""
        echo -e "  ${YELLOW}3. Manual merge:${NC}"
        echo "     gh pr merge $PR_NUMBER --squash --delete-branch"
        echo ""
    fi
else
    echo -e "${RED}✗ PR has failing CI checks${NC}"
    echo ""
    echo "Cannot auto-recover. Please:"
    echo "  1. Review CI failures"
    echo "  2. Fix issues in branch: $BRANCH"
    echo "  3. Re-run workflow from last phase"
fi
