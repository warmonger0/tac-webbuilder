#!/bin/bash
# Post-Session Hook - Auto-archive after completion
# Called when a session is marked complete in the database
#
# Usage:
#   ./scripts/post_session_hook.sh <session_number>
#
# Example:
#   ./scripts/post_session_hook.sh 7

set -e

SESSION_NUMBER=$1

if [ -z "$SESSION_NUMBER" ]; then
    echo "Usage: $0 <session_number>"
    echo ""
    echo "Example:"
    echo "  $0 7     # Archive Session 7 files"
    exit 1
fi

# Get project root (directory containing this script's parent)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "Post-Session Hook: Session $SESSION_NUMBER"
echo "=========================================="
echo ""

# Check if archiving script exists
if [ ! -f "scripts/archive_sessions.py" ]; then
    echo "❌ Error: scripts/archive_sessions.py not found"
    exit 1
fi

# Archive session files
echo "📦 Archiving session files..."
python3 scripts/archive_sessions.py --session "$SESSION_NUMBER" --archive

if [ $? -eq 0 ]; then
    echo "✅ Session files archived successfully"
else
    echo "❌ Error archiving session files"
    exit 1
fi

echo ""

# Update archive index
echo "📝 Updating archive index..."
python3 scripts/archive_sessions.py --update-index

if [ $? -eq 0 ]; then
    echo "✅ Archive index updated"
else
    echo "❌ Error updating archive index"
    exit 1
fi

echo ""

# Optional: Commit changes to git
if [ -d ".git" ]; then
    echo "🔍 Checking for git changes..."

    # Check if there are changes to commit
    if [ -n "$(git status --porcelain archives/)" ]; then
        echo "📝 Committing archive changes..."

        git add archives/

        git commit -m "Archive Session $SESSION_NUMBER documentation

Automatically archived by post-session hook:
- Session documents moved to archives/
- Archive index updated

Session: $SESSION_NUMBER
Date: $(date '+%Y-%m-%d %H:%M:%S')" || true

        echo "✅ Changes committed to git"
    else
        echo "ℹ️  No changes to commit"
    fi
fi

echo ""
echo "=========================================="
echo "✅ Session $SESSION_NUMBER archived successfully"
echo "=========================================="
