#!/bin/bash

# Validation Script for Documentation Migration
# Checks for broken references and validates new structure
# Created: 2025-11-17

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Documentation Migration Validation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Safety check - must be run from project root
if [ ! -d "docs" ] || [ ! -f "package.json" ]; then
    echo -e "${RED}Error: Must be run from project root directory${NC}"
    exit 1
fi

echo -e "${BLUE}[1/6] Checking for old folder references...${NC}"
echo ""

# Check for references to old paths
OLD_PATHS=(
    "docs/ADW/"
    "docs/Cost-Optimization/"
    "docs/Architecture/"
    "docs/Testing/"
    "docs/Webhooks/"
    "docs/Analysis/"
    "docs/Archive/"
    "docs/Archived Issues/"
    "docs/Implementation Plans/"
    "docs/implementation/PHASE_"
)

for old_path in "${OLD_PATHS[@]}"; do
    # Search in docs and .claude directories
    results=$(grep -r "$old_path" docs/ .claude/ adws/README.md 2>/dev/null || true)

    if [ ! -z "$results" ]; then
        echo -e "${RED}✗ Found references to old path: $old_path${NC}"
        echo "$results" | head -n 5
        if [ $(echo "$results" | wc -l) -gt 5 ]; then
            echo -e "${YELLOW}  ... and $(( $(echo "$results" | wc -l) - 5 )) more${NC}"
        fi
        echo ""
        ((ERRORS++))
    else
        echo -e "${GREEN}✓ No references to: $old_path${NC}"
    fi
done

echo ""
echo -e "${BLUE}[2/6] Verifying new directory structure...${NC}"
echo ""

# Check for expected directories
EXPECTED_DIRS=(
    "docs/architecture"
    "docs/architecture/decisions"
    "docs/architecture/patterns"
    "docs/features"
    "docs/features/adw"
    "docs/features/cost-optimization"
    "docs/planned_features"
    "docs/planned_features/pattern-learning"
    "docs/implementation"
    "docs/implementation/pattern-signatures"
    "docs/testing"
    "docs/archive"
    "docs/archive/issues"
    "docs/archive/phases"
)

for dir in "${EXPECTED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓ Directory exists: $dir${NC}"
    else
        echo -e "${RED}✗ Missing directory: $dir${NC}"
        ((ERRORS++))
    fi
done

echo ""
echo -e "${BLUE}[3/6] Checking for old directories (should be removed)...${NC}"
echo ""

# Check that old directories are gone
OLD_DIRS=(
    "docs/ADW"
    "docs/Cost-Optimization"
    "docs/Architecture"
    "docs/Testing"
    "docs/Webhooks"
    "docs/Analysis"
    "docs/Archive"
    "docs/Archived Issues"
    "docs/Implementation Plans"
    "docs/logs"
)

for dir in "${OLD_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${RED}✗ Old directory still exists: $dir${NC}"
        ((WARNINGS++))
    else
        echo -e "${GREEN}✓ Removed: $dir${NC}"
    fi
done

echo ""
echo -e "${BLUE}[4/6] Verifying file counts...${NC}"
echo ""

# Count markdown files
total_md_files=$(find docs -type f -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
echo -e "Total markdown files in docs/: ${YELLOW}$total_md_files${NC}"

if [ "$total_md_files" -lt 70 ]; then
    echo -e "${RED}✗ Warning: Expected ~90+ files, found only $total_md_files${NC}"
    ((WARNINGS++))
else
    echo -e "${GREEN}✓ File count looks reasonable${NC}"
fi

echo ""
echo -e "${BLUE}[5/6] Checking for broken markdown links...${NC}"
echo ""

# Simple check for markdown links to docs/ that might be broken
broken_links=0
for file in $(find docs -type f -name "*.md"); do
    # Look for markdown links like [text](docs/...)
    links=$(grep -o '\](docs/[^)]*\.md)' "$file" 2>/dev/null || true)

    if [ ! -z "$links" ]; then
        while IFS= read -r link; do
            # Extract the path (remove ]( and ))
            path=$(echo "$link" | sed 's/^](//' | sed 's/)$//')

            # Check if file exists (relative to the file's directory)
            file_dir=$(dirname "$file")
            if [ ! -f "$file_dir/$path" ]; then
                echo -e "${YELLOW}⚠ Potentially broken link in $file:${NC}"
                echo -e "  Link: $link"
                ((broken_links++))
            fi
        done <<< "$links"
    fi
done

if [ "$broken_links" -eq 0 ]; then
    echo -e "${GREEN}✓ No obviously broken markdown links found${NC}"
else
    echo -e "${YELLOW}⚠ Found $broken_links potentially broken links (manual review recommended)${NC}"
    ((WARNINGS++))
fi

echo ""
echo -e "${BLUE}[6/6] Checking directory depth and structure...${NC}"
echo ""

# Show tree structure (if tree command is available)
if command -v tree &> /dev/null; then
    echo -e "${YELLOW}Documentation structure (2 levels deep):${NC}"
    tree docs -L 2 -d --dirsfirst
else
    echo -e "${YELLOW}Tree command not available. Using find instead:${NC}"
    find docs -type d | head -n 30
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Validation Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ "$ERRORS" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
    echo -e "${GREEN}✓ Migration validation passed!${NC}"
    echo -e "${GREEN}  No errors or warnings found${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo -e "  1. Review the structure: ${BLUE}tree docs/ -L 2${NC}"
    echo -e "  2. Test loading docs in Claude Code"
    echo -e "  3. Commit changes: ${BLUE}git add docs/ && git commit -m 'docs: Reorganize documentation structure'${NC}"
    exit 0
elif [ "$ERRORS" -eq 0 ]; then
    echo -e "${YELLOW}⚠ Migration completed with warnings${NC}"
    echo -e "${YELLOW}  Errors: $ERRORS${NC}"
    echo -e "${YELLOW}  Warnings: $WARNINGS${NC}"
    echo ""
    echo -e "${YELLOW}Please review warnings above before committing${NC}"
    exit 0
else
    echo -e "${RED}✗ Migration validation failed${NC}"
    echo -e "${RED}  Errors: $ERRORS${NC}"
    echo -e "${YELLOW}  Warnings: $WARNINGS${NC}"
    echo ""
    echo -e "${RED}Please fix errors before proceeding${NC}"
    echo -e "${YELLOW}To rollback: ${BLUE}rm -rf docs/ && mv docs_backup/ docs/${NC}"
    exit 1
fi
