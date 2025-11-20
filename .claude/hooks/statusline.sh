#!/bin/bash
# Custom status line script for Claude Code
# Tracks git branch and uncommitted changes in real-time

# Get current directory from environment or use pwd
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Change to project directory
cd "$PROJECT_DIR" 2>/dev/null || exit 0

# Check if we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "cc-cli | Sonnet 4.5 | Not a git repo"
    exit 0
fi

# Get current branch
BRANCH=$(git branch --show-current 2>/dev/null || echo "detached")

# Get diff stats for unstaged + staged changes
DIFF_STATS=$(git diff HEAD --shortstat 2>/dev/null)

# Parse insertions and deletions
INSERTIONS=0
DELETIONS=0

if [[ -n "$DIFF_STATS" ]]; then
    # Extract insertions
    if [[ "$DIFF_STATS" =~ ([0-9]+)\ insertion ]]; then
        INSERTIONS="${BASH_REMATCH[1]}"
    fi

    # Extract deletions
    if [[ "$DIFF_STATS" =~ ([0-9]+)\ deletion ]]; then
        DELETIONS="${BASH_REMATCH[1]}"
    fi
fi

# Format output with dynamic uncommitted status
if [[ $INSERTIONS -eq 0 && $DELETIONS -eq 0 ]]; then
    UNCOMMITTED_STATUS="uncommitted:none"
else
    UNCOMMITTED_STATUS="uncommitted:+${INSERTIONS}|-${DELETIONS}"
fi

echo "cc-cli | Sonnet 4.5 | cwd:.../tac/tac-webbuilder | ${BRANCH} | ${UNCOMMITTED_STATUS}"
