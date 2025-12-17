#!/bin/bash
#
# check_issue_status.sh - Pre-flight status dashboard for ADW workflows
#
# Usage: ./scripts/check_issue_status.sh <issue-number>
#
# Displays comprehensive status information before starting a workflow:
# - Issue state (open/closed)
# - Linked PRs and their states
# - Active workflows in database
# - Recent workflow attempts
# - Recommendation (safe to proceed / skip / wait)
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if issue number provided
if [ -z "$1" ]; then
    echo "Usage: $0 <issue-number>"
    echo ""
    echo "Example: $0 70"
    exit 1
fi

ISSUE_NUMBER=$1

echo "============================================================"
echo "PRE-FLIGHT STATUS DASHBOARD - Issue #${ISSUE_NUMBER}"
echo "============================================================"
echo ""

# Check 1: Issue Status
echo -e "${BLUE}[1/5] Checking Issue Status...${NC}"
ISSUE_DATA=$(gh issue view "${ISSUE_NUMBER}" --json state,title,closedAt,url 2>/dev/null || echo "{}")

if [ "$ISSUE_DATA" = "{}" ]; then
    echo -e "${RED}❌ ERROR: Could not retrieve issue #${ISSUE_NUMBER}${NC}"
    echo "   Check that the issue exists and gh CLI is authenticated"
    exit 1
fi

ISSUE_STATE=$(echo "$ISSUE_DATA" | jq -r '.state')
ISSUE_TITLE=$(echo "$ISSUE_DATA" | jq -r '.title')
ISSUE_CLOSED_AT=$(echo "$ISSUE_DATA" | jq -r '.closedAt // "N/A"')

echo "   State: ${ISSUE_STATE}"
echo "   Title: ${ISSUE_TITLE}"
if [ "$ISSUE_CLOSED_AT" != "N/A" ]; then
    echo "   Closed At: ${ISSUE_CLOSED_AT}"
fi

if [ "$ISSUE_STATE" = "CLOSED" ]; then
    echo -e "${YELLOW}⚠️  WARNING: Issue is already CLOSED${NC}"
fi
echo ""

# Check 2: Linked PRs
echo -e "${BLUE}[2/5] Checking Linked PRs...${NC}"
PR_DATA=$(gh pr list --search "${ISSUE_NUMBER} in:title" --state all --json number,state,mergedAt,url --limit 10 2>/dev/null || echo "[]")
PR_COUNT=$(echo "$PR_DATA" | jq 'length')

if [ "$PR_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✅ No PRs found (clean slate)${NC}"
else
    echo "   Found ${PR_COUNT} PR(s):"
    echo "$PR_DATA" | jq -r '.[] | "   - PR #\(.number): \(.state)\(if .mergedAt then " (merged at \(.mergedAt))" else "" end)"'

    # Check for merged PRs
    MERGED_COUNT=$(echo "$PR_DATA" | jq '[.[] | select(.state == "MERGED")] | length')
    OPEN_COUNT=$(echo "$PR_DATA" | jq '[.[] | select(.state == "OPEN")] | length')

    if [ "$MERGED_COUNT" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  ${MERGED_COUNT} merged PR(s) found - work may be complete${NC}"
    fi

    if [ "$OPEN_COUNT" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  ${OPEN_COUNT} open PR(s) found - work may be in progress${NC}"
    fi
fi
echo ""

# Check 3: Active Workflows (Database)
echo -e "${BLUE}[3/5] Checking Active Workflows in Database...${NC}"
if [ -z "$POSTGRES_HOST" ]; then
    echo -e "${YELLOW}⚠️  PostgreSQL not configured - skipping database check${NC}"
    echo "   Set POSTGRES_* env vars to check database"
else
    # Try to query database
    DB_RESULT=$(cd app/server && env POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-changeme}" DB_TYPE=postgresql python3 << EOF 2>/dev/null || echo "ERROR"
import sys
sys.path.insert(0, '.')
from repositories.phase_queue_repository import PhaseQueueRepository

try:
    repo = PhaseQueueRepository()
    workflows = repo.get_all_by_feature_id(${ISSUE_NUMBER})

    active_statuses = ["running", "planned", "building", "linting", "testing", "reviewing", "documenting", "shipping"]
    active = [w for w in workflows if w.status in active_statuses]

    print(f"TOTAL:{len(workflows)}")
    print(f"ACTIVE:{len(active)}")

    if active:
        for w in active:
            print(f"WORKFLOW:{w.adw_id}|{w.phase_name}|{w.status}")
except Exception as e:
    print(f"ERROR:{e}")
EOF
)

    if echo "$DB_RESULT" | grep -q "^ERROR"; then
        echo -e "${YELLOW}⚠️  Could not query database${NC}"
        echo "   Database may not be running or credentials incorrect"
    else
        TOTAL=$(echo "$DB_RESULT" | grep "^TOTAL:" | cut -d: -f2)
        ACTIVE=$(echo "$DB_RESULT" | grep "^ACTIVE:" | cut -d: -f2)

        echo "   Total workflows in DB: ${TOTAL}"
        echo "   Active workflows: ${ACTIVE}"

        if [ "$ACTIVE" -gt 0 ]; then
            echo -e "${RED}❌ ACTIVE WORKFLOWS FOUND:${NC}"
            echo "$DB_RESULT" | grep "^WORKFLOW:" | while IFS='|' read -r _ adw_id phase status; do
                echo "      - ADW: ${adw_id}, Phase: ${phase}, Status: ${status}"
            done
        else
            echo -e "${GREEN}✅ No active workflows (database clear)${NC}"
        fi
    fi
fi
echo ""

# Check 4: Recent Workflow Attempts (GitHub Comments)
echo -e "${BLUE}[4/5] Checking Recent Workflow Attempts...${NC}"
RECENT_COMMENTS=$(gh api "repos/{owner}/{repo}/issues/${ISSUE_NUMBER}/comments" --jq '.[-15:]' 2>/dev/null || echo "[]")

OPS_COUNT=$(echo "$RECENT_COMMENTS" | jq '[.[] | select(.body | contains("_ops:"))] | length')
LAST_OPS_TIME=$(echo "$RECENT_COMMENTS" | jq -r '[.[] | select(.body | contains("_ops:"))] | .[-1].created_at // "N/A"')

echo "   ops comments in last 15: ${OPS_COUNT}"
if [ "$LAST_OPS_TIME" != "N/A" ]; then
    echo "   Last workflow attempt: ${LAST_OPS_TIME}"

    # Calculate time since last attempt
    if command -v python3 &> /dev/null; then
        TIME_DIFF=$(python3 << EOF
from datetime import datetime
last = datetime.fromisoformat("${LAST_OPS_TIME}".replace("Z", "+00:00"))
now = datetime.now(last.tzinfo)
diff = (now - last).total_seconds() / 60
print(f"{diff:.1f}")
EOF
)
        echo "   Time since last attempt: ${TIME_DIFF} minutes"

        # Check cooldown (60 minutes)
        if (( $(echo "$TIME_DIFF < 60" | bc -l) )); then
            REMAINING=$(echo "60 - $TIME_DIFF" | bc -l | xargs printf "%.1f")
            echo -e "${YELLOW}⚠️  Cooldown active: ${REMAINING} minutes remaining${NC}"
        fi
    fi
else
    echo -e "${GREEN}✅ No recent workflow attempts${NC}"
fi
echo ""

# Check 5: Recommendation
echo -e "${BLUE}[5/5] Generating Recommendation...${NC}"
echo ""

RECOMMENDATION="PROCEED"
REASONS=()

if [ "$ISSUE_STATE" = "CLOSED" ] && [ "$MERGED_COUNT" -gt 0 ]; then
    RECOMMENDATION="SKIP"
    REASONS+=("Issue already closed with merged PR")
fi

if [ "$OPEN_COUNT" -gt 0 ]; then
    RECOMMENDATION="WAIT"
    REASONS+=("Open PR exists - check if it needs work or should be closed")
fi

if [ "$ACTIVE" -gt 0 ] 2>/dev/null; then
    RECOMMENDATION="BLOCKED"
    REASONS+=("Active workflow already running for this issue")
fi

if [ "$OPS_COUNT" -ge 10 ]; then
    RECOMMENDATION="WAIT"
    REASONS+=("Too many recent attempts (possible loop)")
fi

echo "============================================================"
case "$RECOMMENDATION" in
    "PROCEED")
        echo -e "${GREEN}✅ RECOMMENDATION: SAFE TO PROCEED${NC}"
        echo ""
        echo "All checks passed. You can start a workflow for this issue."
        echo ""
        echo "Command:"
        echo "  cd adws && uv run python adw_sdlc_complete_iso.py ${ISSUE_NUMBER}"
        ;;
    "SKIP")
        echo -e "${RED}❌ RECOMMENDATION: SKIP THIS ISSUE${NC}"
        echo ""
        echo "Reasons:"
        for reason in "${REASONS[@]}"; do
            echo "  - ${reason}"
        done
        echo ""
        echo "This issue appears to be already complete. No workflow needed."
        ;;
    "WAIT")
        echo -e "${YELLOW}⚠️  RECOMMENDATION: WAIT OR INVESTIGATE${NC}"
        echo ""
        echo "Reasons:"
        for reason in "${REASONS[@]}"; do
            echo "  - ${reason}"
        done
        echo ""
        echo "Manual investigation recommended before starting workflow."
        ;;
    "BLOCKED")
        echo -e "${RED}🛑 RECOMMENDATION: BLOCKED${NC}"
        echo ""
        echo "Reasons:"
        for reason in "${REASONS[@]}"; do
            echo "  - ${reason}"
        done
        echo ""
        echo "Wait for active workflow to complete, or use --clean-start to override."
        ;;
esac
echo "============================================================"
