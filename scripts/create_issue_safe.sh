#!/bin/bash
set -e

# Safe issue creation with automatic workflow trigger
# Usage: ./scripts/create_issue_safe.sh --title "title" --body-file file.md

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🔍 Issue Creation with Auto-Trigger"
echo "===================================="
echo ""

# Parse body file to extract workflow command
BODY_FILE=""
for ((i=1; i<=$#; i++)); do
    if [[ "${!i}" == "--body-file" ]]; then
        j=$((i+1))
        BODY_FILE="${!j}"
        break
    fi
done

# Extract workflow command from body file if provided
WORKFLOW_CMD=""
if [ -n "$BODY_FILE" ] && [ -f "$BODY_FILE" ]; then
    # Look for adw_* workflow command in the file
    WORKFLOW_CMD=$(grep -i "adw_.*iso" "$BODY_FILE" | grep -o "adw_[a-z_]*_iso" | head -1)

    if [ -n "$WORKFLOW_CMD" ]; then
        echo -e "${BLUE}🔍 Detected workflow: ${WORKFLOW_CMD}${NC}"
    fi
fi

# Create the issue
echo "📝 Creating GitHub issue..."
echo ""

# Capture issue creation output
ISSUE_OUTPUT=$(gh issue create "$@" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ Failed to create issue${NC}"
    echo "$ISSUE_OUTPUT"
    exit $EXIT_CODE
fi

# Display issue creation result
echo "$ISSUE_OUTPUT"

# Extract issue number from URL
ISSUE_URL=$(echo "$ISSUE_OUTPUT" | grep -o "https://github.com/[^/]*/[^/]*/issues/[0-9]*" | head -1)
ISSUE_NUMBER=$(echo "$ISSUE_URL" | grep -o "[0-9]*$")

if [ -z "$ISSUE_NUMBER" ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Could not extract issue number from output${NC}"
    echo "Issue created but workflow not triggered automatically"
    exit 0
fi

echo ""
echo -e "${GREEN}✅ Issue #${ISSUE_NUMBER} created successfully!${NC}"

# Auto-trigger workflow if detected
if [ -n "$WORKFLOW_CMD" ]; then
    echo ""
    echo -e "${BLUE}🚀 Auto-triggering workflow: ${WORKFLOW_CMD}${NC}"
    echo ""

    # Run workflow in background
    uv run "adws/${WORKFLOW_CMD}.py" "$ISSUE_NUMBER" &
    WORKFLOW_PID=$!

    echo -e "${GREEN}✅ Workflow started (PID: ${WORKFLOW_PID})${NC}"
    echo ""
    echo "📊 Monitor progress:"
    echo "   - Issue comments: gh issue view ${ISSUE_NUMBER}"
    echo "   - Issue URL: ${ISSUE_URL}"
else
    echo ""
    echo -e "${YELLOW}ℹ️  No ADW workflow detected in issue body${NC}"
    echo "   To trigger manually: uv run adws/adw_sdlc_zte_iso.py ${ISSUE_NUMBER}"
fi

exit 0
