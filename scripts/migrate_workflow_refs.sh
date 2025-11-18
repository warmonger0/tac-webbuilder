#!/bin/bash
# Migrate workflow references from deprecated to complete versions
# This script safely updates all workflow references in your codebase

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}ADW Workflow Reference Migration${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to create backup
create_backup() {
    local file=$1
    cp "$file" "$file.migration-backup-$(date +%Y%m%d-%H%M%S)"
}

# Function to migrate a single file
migrate_file() {
    local file=$1
    local changes=0

    # Create backup
    create_backup "$file"

    # Migrate adw_sdlc_iso.py → adw_sdlc_complete_iso.py
    if grep -q "adw_sdlc_iso\.py" "$file"; then
        sed -i '' 's/adw_sdlc_iso\.py/adw_sdlc_complete_iso.py/g' "$file"
        ((changes++))
        echo -e "  ${GREEN}✓${NC} adw_sdlc_iso.py → adw_sdlc_complete_iso.py"
    fi

    # Migrate adw_sdlc_zte_iso.py → adw_sdlc_complete_zte_iso.py
    if grep -q "adw_sdlc_zte_iso\.py" "$file"; then
        sed -i '' 's/adw_sdlc_zte_iso\.py/adw_sdlc_complete_zte_iso.py/g' "$file"
        ((changes++))
        echo -e "  ${GREEN}✓${NC} adw_sdlc_zte_iso.py → adw_sdlc_complete_zte_iso.py"
    fi

    # Migrate partial chains → complete
    local partial_chains=(
        "adw_plan_build_iso"
        "adw_plan_build_test_iso"
        "adw_plan_build_test_review_iso"
        "adw_plan_build_review_iso"
        "adw_plan_build_document_iso"
    )

    for chain in "${partial_chains[@]}"; do
        if grep -q "${chain}\.py" "$file"; then
            sed -i '' "s/${chain}\.py/adw_sdlc_complete_iso.py/g" "$file"
            ((changes++))
            echo -e "  ${GREEN}✓${NC} ${chain}.py → adw_sdlc_complete_iso.py"
        fi
    done

    return $changes
}

# Find all shell scripts
echo -e "${YELLOW}Scanning for workflow references...${NC}"
echo ""

files_found=0
files_changed=0

# Search in scripts directory
if [ -d "$PROJECT_ROOT/scripts" ]; then
    while IFS= read -r file; do
        ((files_found++))
        echo -e "${BLUE}Checking:${NC} $file"

        if migrate_file "$file"; then
            ((files_changed++))
        else
            echo -e "  ${YELLOW}↦${NC} No deprecated references found"
        fi
        echo ""
    done < <(find "$PROJECT_ROOT/scripts" -name "*.sh" -type f)
fi

# Search in GitHub workflows
if [ -d "$PROJECT_ROOT/.github/workflows" ]; then
    while IFS= read -r file; do
        ((files_found++))
        echo -e "${BLUE}Checking:${NC} $file"

        if migrate_file "$file"; then
            ((files_changed++))
        else
            echo -e "  ${YELLOW}↦${NC} No deprecated references found"
        fi
        echo ""
    done < <(find "$PROJECT_ROOT/.github/workflows" -name "*.yml" -o -name "*.yaml" -type f 2>/dev/null || true)
fi

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Migration Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Files scanned: ${files_found}"
echo -e "Files changed: ${GREEN}${files_changed}${NC}"
echo ""

if [ $files_changed -gt 0 ]; then
    echo -e "${GREEN}✓ Migration complete!${NC}"
    echo ""
    echo -e "${YELLOW}Backup files created with .migration-backup-* suffix${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Review changes: git diff"
    echo "2. Test migrated scripts"
    echo "3. Commit changes: git add -A && git commit -m 'chore: migrate to complete ADW workflows'"
    echo "4. Remove backup files: find . -name '*.migration-backup-*' -delete"
else
    echo -e "${GREEN}✓ No deprecated workflow references found${NC}"
fi

echo ""
