#!/bin/bash
#
# Workflow Completion Hook
#
# Called by ADW workflows when they complete to notify tac-webbuilder
# and optionally trigger the next phase in the queue.
#
# Usage:
#   ./scripts/hooks/workflow_complete.sh <adw_id> <status> [options]
#
# Arguments:
#   adw_id: ADW workflow identifier (e.g., ccc93560)
#   status: Workflow status (completed|failed)
#
# Options:
#   --issue <number>: GitHub issue number
#   --queue-id <id>: Queue ID for this phase
#   --phase <number>: Phase number in multi-phase workflow
#   --parent <number>: Parent issue for multi-phase workflow
#   --trigger-next: Auto-trigger next phase if this one succeeds
#   --cost <amount>: Total workflow cost in USD
#   --duration <seconds>: Workflow duration in seconds
#
# Examples:
#   # Notify completion without auto-trigger
#   ./scripts/hooks/workflow_complete.sh ccc93560 completed --issue 91
#
#   # Notify completion and auto-trigger next phase
#   ./scripts/hooks/workflow_complete.sh ccc93560 completed \
#     --issue 91 \
#     --queue-id 08ee8cc1-9102-4e32-bf9d-95447fd8e215 \
#     --phase 1 \
#     --parent 0 \
#     --trigger-next \
#     --cost 2.50 \
#     --duration 1234

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
ADW_ID="${1:-}"
STATUS="${2:-}"
ISSUE_NUMBER=""
QUEUE_ID=""
PHASE_NUMBER=""
PARENT_ISSUE=""
TRIGGER_NEXT=false
COST=""
DURATION=""

# Validate required arguments
if [ -z "$ADW_ID" ] || [ -z "$STATUS" ]; then
    echo -e "${RED}Error: Missing required arguments${NC}"
    echo "Usage: $0 <adw_id> <status> [options]"
    exit 1
fi

# Validate status
if [[ ! "$STATUS" =~ ^(completed|failed)$ ]]; then
    echo -e "${RED}Error: Invalid status '$STATUS'. Must be 'completed' or 'failed'${NC}"
    exit 1
fi

# Parse optional arguments
shift 2
while [[ $# -gt 0 ]]; do
    case $1 in
        --issue)
            ISSUE_NUMBER="$2"
            shift 2
            ;;
        --queue-id)
            QUEUE_ID="$2"
            shift 2
            ;;
        --phase)
            PHASE_NUMBER="$2"
            shift 2
            ;;
        --parent)
            PARENT_ISSUE="$2"
            shift 2
            ;;
        --trigger-next)
            TRIGGER_NEXT=true
            shift
            ;;
        --cost)
            COST="$2"
            shift 2
            ;;
        --duration)
            DURATION="$2"
            shift 2
            ;;
        *)
            echo -e "${YELLOW}Warning: Unknown option: $1${NC}"
            shift
            ;;
    esac
done

# Build JSON payload
build_payload() {
    local payload='{'
    payload+="\"adw_id\":\"$ADW_ID\""
    payload+=",\"status\":\"$STATUS\""

    [ -n "$ISSUE_NUMBER" ] && payload+=",\"issue_number\":$ISSUE_NUMBER"
    [ -n "$QUEUE_ID" ] && payload+=",\"queue_id\":\"$QUEUE_ID\""
    [ -n "$PHASE_NUMBER" ] && payload+=",\"phase_number\":$PHASE_NUMBER"
    [ -n "$PARENT_ISSUE" ] && payload+=",\"parent_issue\":$PARENT_ISSUE"

    payload+=",\"trigger_next\":$TRIGGER_NEXT"

    # Add metadata
    payload+=",\"metadata\":{"
    local metadata_items=()
    [ -n "$DURATION" ] && metadata_items+=("\"duration_seconds\":$DURATION")
    [ -n "$COST" ] && metadata_items+=("\"cost\":$COST")

    # Join metadata items with commas
    if [ ${#metadata_items[@]} -gt 0 ]; then
        payload+=$(IFS=,; echo "${metadata_items[*]}")
    fi
    payload+='}'

    payload+='}'
    echo "$payload"
}

# Send notification
PAYLOAD=$(build_payload)

echo -e "${YELLOW}[Hook] Notifying tac-webbuilder of workflow completion${NC}"
echo "  ADW ID: $ADW_ID"
echo "  Status: $STATUS"
[ -n "$ISSUE_NUMBER" ] && echo "  Issue: #$ISSUE_NUMBER"
[ -n "$QUEUE_ID" ] && echo "  Queue ID: $QUEUE_ID"
[ -n "$PHASE_NUMBER" ] && echo "  Phase: $PHASE_NUMBER"
echo "  Trigger Next: $TRIGGER_NEXT"

# Send POST request
RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    "$BACKEND_URL/api/workflow-complete" \
    2>&1) || {
    echo -e "${RED}[Hook] Failed to send notification to $BACKEND_URL${NC}"
    exit 1
}

# Parse response (last line is status code)
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}[Hook] ✓ Notification sent successfully${NC}"

    # Parse response for next phase info
    if echo "$BODY" | grep -q "next_phase_triggered"; then
        NEXT_PHASE=$(echo "$BODY" | grep -o '"next_phase_number":[0-9]*' | cut -d':' -f2)
        [ -n "$NEXT_PHASE" ] && echo -e "${GREEN}[Hook] ✓ Next phase #$NEXT_PHASE triggered${NC}"
    fi

    exit 0
else
    echo -e "${RED}[Hook] ✗ Notification failed (HTTP $HTTP_CODE)${NC}"
    echo "$BODY"
    exit 1
fi
