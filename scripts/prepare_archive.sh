#!/bin/bash
# Prepare deprecated workflows for archival
# This script moves deprecated workflows to archive directory

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ADW_DIR="$PROJECT_ROOT/adws"
ARCHIVE_DIR="$ADW_DIR/archived"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}ADW Deprecated Workflow Archival${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Safety check - confirm with user
echo -e "${YELLOW}⚠️  This will move deprecated workflows to archive directory.${NC}"
echo -e "${YELLOW}They will no longer be in the main adws/ directory.${NC}"
echo ""
echo -e "Workflows to archive:"
echo "  • adw_sdlc_iso.py"
echo "  • adw_sdlc_zte_iso.py"
echo "  • adw_plan_build_iso.py"
echo "  • adw_plan_build_test_iso.py"
echo "  • adw_plan_build_test_review_iso.py"
echo "  • adw_plan_build_review_iso.py"
echo "  • adw_plan_build_document_iso.py"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Archival cancelled."
    exit 0
fi

# Create archive directory structure
echo ""
echo -e "${BLUE}Creating archive structure...${NC}"

mkdir -p "$ARCHIVE_DIR/partial-chains"
mkdir -p "$ARCHIVE_DIR/incomplete-sdlc"

# Create archive README
cat > "$ARCHIVE_DIR/README.md" << 'EOF'
# Archived ADW Workflows

This directory contains deprecated ADW workflows that have been archived.

## Why Archived?

These workflows were deprecated in favor of complete workflow chains that include all phases:
- `adw_sdlc_complete_iso.py` - Complete SDLC with all 8 phases
- `adw_sdlc_complete_zte_iso.py` - Complete ZTE with all 8 phases

## Archived Workflows

### Incomplete SDLC Workflows

**adw_sdlc_iso.py**
- Missing: Ship, Cleanup phases
- Replacement: `adw_sdlc_complete_iso.py`
- Reason: Incomplete workflow, manual PR merge required

**adw_sdlc_zte_iso.py**
- Missing: Lint phase
- Replacement: `adw_sdlc_complete_zte_iso.py`
- Reason: Critical safety issue - can auto-merge broken code without lint validation

### Partial Chain Workflows

- `adw_plan_build_iso.py` - Only Plan + Build
- `adw_plan_build_test_iso.py` - Only Plan + Build + Test
- `adw_plan_build_test_review_iso.py` - Only Plan + Build + Test + Review
- `adw_plan_build_review_iso.py` - Only Plan + Build + Review
- `adw_plan_build_document_iso.py` - Only Plan + Build + Document

**Replacement:** All can use `adw_sdlc_complete_iso.py` with appropriate flags

## Migration Guide

See: `docs/planned_features/workflow-enhancements/MIGRATION_GUIDE.md`

## Restoration

If you need to restore these workflows:

```bash
# Copy back to main directory
cp archived/incomplete-sdlc/adw_sdlc_iso.py ../

# Or use directly from archive
uv run archived/incomplete-sdlc/adw_sdlc_iso.py <issue>
```

---

**Archived:** $(date +%Y-%m-%d)
**Status:** Deprecated but functional
EOF

echo -e "${GREEN}✓${NC} Created archive directory structure"
echo -e "${GREEN}✓${NC} Created README.md"

# Move incomplete SDLC workflows
echo ""
echo -e "${BLUE}Moving incomplete SDLC workflows...${NC}"

for workflow in "adw_sdlc_iso.py" "adw_sdlc_zte_iso.py"; do
    if [ -f "$ADW_DIR/$workflow" ]; then
        mv "$ADW_DIR/$workflow" "$ARCHIVE_DIR/incomplete-sdlc/"
        echo -e "${GREEN}✓${NC} Moved $workflow"
    else
        echo -e "${YELLOW}⚠${NC}  $workflow not found (may already be archived)"
    fi
done

# Move partial chain workflows
echo ""
echo -e "${BLUE}Moving partial chain workflows...${NC}"

partial_chains=(
    "adw_plan_build_iso.py"
    "adw_plan_build_test_iso.py"
    "adw_plan_build_test_review_iso.py"
    "adw_plan_build_review_iso.py"
    "adw_plan_build_document_iso.py"
)

for workflow in "${partial_chains[@]}"; do
    if [ -f "$ADW_DIR/$workflow" ]; then
        mv "$ADW_DIR/$workflow" "$ARCHIVE_DIR/partial-chains/"
        echo -e "${GREEN}✓${NC} Moved $workflow"
    else
        echo -e "${YELLOW}⚠${NC}  $workflow not found (may already be archived)"
    fi
done

# Create symlinks for backward compatibility (optional)
echo ""
read -p "Create symlinks for backward compatibility? (yes/no): " create_symlinks

if [ "$create_symlinks" == "yes" ]; then
    echo ""
    echo -e "${BLUE}Creating symlinks...${NC}"

    cd "$ADW_DIR"

    # SDLC workflows
    ln -sf "archived/incomplete-sdlc/adw_sdlc_iso.py" "adw_sdlc_iso.py"
    ln -sf "archived/incomplete-sdlc/adw_sdlc_zte_iso.py" "adw_sdlc_zte_iso.py"
    echo -e "${GREEN}✓${NC} Created symlinks for SDLC workflows"

    # Partial chains
    for workflow in "${partial_chains[@]}"; do
        ln -sf "archived/partial-chains/$workflow" "$workflow"
    done
    echo -e "${GREEN}✓${NC} Created symlinks for partial chains"

    cd - > /dev/null

    echo ""
    echo -e "${YELLOW}Note: Symlinks maintain backward compatibility${NC}"
    echo -e "${YELLOW}Old commands will still work but point to archived files${NC}"
fi

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Archival Complete${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Workflows archived to: $ARCHIVE_DIR"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. Update any remaining references to archived workflows"
echo "2. Commit changes:"
echo "   git add adws/archived/"
echo "   git commit -m 'chore: archive deprecated ADW workflows'"
echo "3. Review migration guide:"
echo "   docs/planned_features/workflow-enhancements/MIGRATION_GUIDE.md"
echo ""
