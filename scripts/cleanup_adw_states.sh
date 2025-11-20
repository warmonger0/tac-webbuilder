#!/bin/bash
# Cleanup orphaned ADW state files for deleted worktrees
#
# This script identifies ADW directories that reference non-existent worktrees
# and archives them to agents/_archived/ for historical reference.
#
# Usage:
#   ./scripts/cleanup_adw_states.sh [--dry-run] [--force]
#
# Options:
#   --dry-run    Show what would be archived without making changes
#   --force      Skip confirmation prompt

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
AGENTS_DIR="$PROJECT_ROOT/agents"
TREES_DIR="$PROJECT_ROOT/trees"
ARCHIVE_DIR="$PROJECT_ROOT/agents/_archived"

# Parse arguments
DRY_RUN=false
FORCE=false

for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            ;;
        --force)
            FORCE=true
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Usage: $0 [--dry-run] [--force]"
            exit 1
            ;;
    esac
done

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 ADW State Cleanup Utility${NC}"
echo ""

# Create archive directory if needed (unless dry-run)
if [ "$DRY_RUN" = false ]; then
    mkdir -p "$ARCHIVE_DIR"
fi

echo "📁 Checking: $AGENTS_DIR"
echo "🗄️  Archive:  $ARCHIVE_DIR"
echo ""

# Check if agents directory exists
if [ ! -d "$AGENTS_DIR" ]; then
    echo -e "${RED}❌ Error: Agents directory not found: $AGENTS_DIR${NC}"
    exit 1
fi

# Count ADW states
orphaned_count=0
active_count=0
orphaned_adws=()

echo -e "${BLUE}Scanning ADW state files...${NC}"
echo ""

for adw_dir in "$AGENTS_DIR"/*/ ; do
    # Skip if not a directory
    [ -d "$adw_dir" ] || continue

    adw_id=$(basename "$adw_dir")

    # Skip special directories
    if [[ "$adw_id" == "_archived" ]] || [[ "$adw_id" == "--resume" ]]; then
        continue
    fi

    state_file="$adw_dir/adw_state.json"

    if [[ -f "$state_file" ]]; then
        # Extract worktree_path from JSON
        worktree_path=$(grep -o '"worktree_path": "[^"]*"' "$state_file" 2>/dev/null | cut -d'"' -f4 || echo "")

        # Check if worktree_path is null or empty
        if [[ -z "$worktree_path" || "$worktree_path" == "null" ]]; then
            echo -e "⚠️  ${YELLOW}$adw_id${NC}: No worktree path in state (skipping)"
            continue
        fi

        # Check if worktree exists
        if [[ ! -d "$worktree_path" ]]; then
            # Get issue number for display
            issue_number=$(grep -o '"issue_number": "[^"]*"' "$state_file" 2>/dev/null | cut -d'"' -f4 || echo "unknown")

            echo -e "📦 ${YELLOW}$adw_id${NC} (issue #$issue_number): Worktree MISSING"
            echo "   Path: $worktree_path"

            # Calculate size
            size=$(du -sh "$adw_dir" 2>/dev/null | cut -f1)
            echo "   Size: $size"

            orphaned_adws+=("$adw_id:$issue_number")
            ((orphaned_count++))
        else
            echo -e "✅ ${GREEN}$adw_id${NC}: Active (worktree exists)"
            ((active_count++))
        fi
    else
        echo -e "⚠️  ${YELLOW}$adw_id${NC}: No state file (skipping)"
    fi
done

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 Summary:${NC}"
echo -e "   Active ADWs:   ${GREEN}$active_count${NC}"
echo -e "   Orphaned ADWs: ${YELLOW}$orphaned_count${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# If no orphaned ADWs, exit
if [ $orphaned_count -eq 0 ]; then
    echo -e "${GREEN}✨ No orphaned ADW states found. Nothing to clean up!${NC}"
    exit 0
fi

# Dry-run mode
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}🔍 DRY-RUN MODE - No changes will be made${NC}"
    echo ""
    echo "Would archive the following ADWs:"
    for adw_info in "${orphaned_adws[@]}"; do
        adw_id=$(echo "$adw_info" | cut -d':' -f1)
        issue_number=$(echo "$adw_info" | cut -d':' -f2)
        echo "  - $adw_id (issue #$issue_number)"
    done
    echo ""
    echo "Run without --dry-run to perform cleanup."
    exit 0
fi

# Confirmation prompt (unless --force)
if [ "$FORCE" = false ]; then
    echo -e "${YELLOW}⚠️  This will archive $orphaned_count ADW state directories.${NC}"
    echo ""
    echo "Orphaned ADWs to be archived:"
    for adw_info in "${orphaned_adws[@]}"; do
        adw_id=$(echo "$adw_info" | cut -d':' -f1)
        issue_number=$(echo "$adw_info" | cut -d':' -f2)
        echo "  - $adw_id (issue #$issue_number)"
    done
    echo ""
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ Cancelled by user${NC}"
        exit 1
    fi
fi

# Perform archival
echo ""
echo -e "${BLUE}📦 Archiving orphaned ADW states...${NC}"
echo ""

archived_count=0
failed_count=0

for adw_info in "${orphaned_adws[@]}"; do
    adw_id=$(echo "$adw_info" | cut -d':' -f1)
    issue_number=$(echo "$adw_info" | cut -d':' -f2)

    adw_dir="$AGENTS_DIR/$adw_id"
    timestamp=$(date +%Y%m%d_%H%M%S)
    archive_path="$ARCHIVE_DIR/${adw_id}_issue-${issue_number}_${timestamp}"

    echo -n "📦 Archiving $adw_id... "

    if mv "$adw_dir" "$archive_path" 2>/dev/null; then
        echo -e "${GREEN}✓${NC}"
        ((archived_count++))
    else
        echo -e "${RED}✗ (failed)${NC}"
        ((failed_count++))
    fi
done

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}✅ Cleanup Complete!${NC}"
echo ""
echo -e "   Archived:    ${GREEN}$archived_count${NC} ADWs"
if [ $failed_count -gt 0 ]; then
    echo -e "   Failed:      ${RED}$failed_count${NC} ADWs"
fi
echo -e "   Location:    $ARCHIVE_DIR"
echo ""

# Show disk space saved
if [ $archived_count -gt 0 ]; then
    archive_size=$(du -sh "$ARCHIVE_DIR" 2>/dev/null | cut -f1)
    echo -e "   Total size:  $archive_size"
    echo ""
fi

# Suggest next steps
if [ $archived_count -gt 0 ]; then
    echo -e "${BLUE}💡 Next Steps:${NC}"
    echo "   1. Review archived ADWs: ls -la $ARCHIVE_DIR"
    echo "   2. Delete archive if not needed: rm -rf $ARCHIVE_DIR"
    echo "   3. Commit changes: git add agents/ && git commit -m 'chore: Archive orphaned ADW states'"
    echo ""
fi

echo -e "${GREEN}🎉 Done!${NC}"
