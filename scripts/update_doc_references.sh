#!/bin/bash

# Update Documentation References Script
# Updates all references to moved documentation files
# Created: 2025-11-17

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

UPDATED=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Update Documentation References${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Safety check - must be run from project root
if [ ! -d "docs" ] || [ ! -d "adws" ]; then
    echo -e "${RED}Error: Must be run from project root directory${NC}"
    exit 1
fi

# Function to update references in a file
update_file() {
    local file="$1"
    local old_pattern="$2"
    local new_pattern="$3"

    if [ -f "$file" ]; then
        if grep -q "$old_pattern" "$file" 2>/dev/null; then
            # Use different sed syntax for macOS vs Linux
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s|$old_pattern|$new_pattern|g" "$file"
            else
                sed -i "s|$old_pattern|$new_pattern|g" "$file"
            fi
            echo -e "${GREEN}✓ Updated: $file${NC}"
            echo -e "  ${old_pattern} → ${new_pattern}"
            ((UPDATED++))
        fi
    fi
}

echo -e "${YELLOW}Updating references in documentation files...${NC}"
echo ""

# 1. Update ADW Chaining Architecture references
echo -e "${BLUE}[1/10] Updating ADW Chaining Architecture references...${NC}"
update_file "docs/features/adw/external-tools/usage-examples.md" "docs/ADW_CHAINING_ARCHITECTURE.md" "docs/features/adw/chaining-architecture.md"
update_file "docs/features/adw/external-tools/migration-guide.md" "docs/ADW_CHAINING_ARCHITECTURE.md" "docs/features/adw/chaining-architecture.md"
update_file "docs/features/adw/external-tools/integration-guide.md" "docs/ADW_CHAINING_ARCHITECTURE.md" "docs/features/adw/chaining-architecture.md"
update_file "docs/features/adw/external-tools/e2e-validation-guide.md" "docs/ADW_CHAINING_ARCHITECTURE.md" "docs/features/adw/chaining-architecture.md"
update_file "adws/README.md" "docs/ADW_CHAINING_ARCHITECTURE.md" "docs/features/adw/chaining-architecture.md"

# 2. Update ADW Technical Overview references
echo -e "${BLUE}[2/10] Updating ADW Technical Overview references...${NC}"
update_file "docs/archive/issues/CONTEXT_HANDOFF_ISSUE_11.md" "docs/ADW_TECHNICAL_OVERVIEW.md" "docs/features/adw/technical-overview.md"
update_file "docs/features/outloop-testing/playwright-lazy-loading.md" "docs/ADW_TECHNICAL_OVERVIEW.md" "docs/features/adw/technical-overview.md"

# 3. Update ADW Optimization references
echo -e "${BLUE}[3/10] Updating ADW Optimization references...${NC}"
update_file "docs/features/cost-optimization/how-to-get-estimates.md" "docs/ADW_OPTIMIZATION_ANALYSIS.md" "docs/features/adw/optimization.md"

# 4. Update Implementation Plan references
echo -e "${BLUE}[4/10] Updating Implementation Plan references...${NC}"
update_file "docs/implementation/README.md" "../OUT_LOOP_CODING_IMPLEMENTATION_PLAN.md" "../planned_features/pattern-learning/implementation-plan.md"
update_file "docs/planned_features/pattern-learning/observability-summary.md" "docs/OUT_LOOP_CODING_IMPLEMENTATION_PLAN.md" "docs/planned_features/pattern-learning/implementation-plan.md"

# 5. Update PHASE file references in implementation/README.md
echo -e "${BLUE}[5/10] Updating PHASE file references...${NC}"
update_file "docs/implementation/README.md" "PHASE_1_PATTERN_DETECTION.md" "pattern-signatures/phase-1-detection.md"
update_file "docs/implementation/README.md" "PHASE_2_CONTEXT_EFFICIENCY.md" "pattern-signatures/phase-2-context-efficiency.md"
update_file "docs/implementation/README.md" "PHASE_3_TOOL_ROUTING.md" "pattern-signatures/phase-3-tool-routing.md"
update_file "docs/implementation/README.md" "PHASE_4_AUTO_DISCOVERY.md" "pattern-signatures/phase-4-auto-discovery.md"
update_file "docs/implementation/README.md" "PHASE_5_QUOTA_MANAGEMENT.md" "pattern-signatures/phase-5-quota-management.md"
update_file "docs/implementation/README.md" "PHASES_3_4_5_SUMMARY.md" "pattern-signatures/phases-3-4-5-summary.md"

# 6. Update internal PHASE references in implementation plan
echo -e "${BLUE}[6/10] Updating internal PHASE references in implementation plan...${NC}"
update_file "docs/planned_features/pattern-learning/implementation-plan.md" "docs/implementation/PHASE_1_PATTERN_DETECTION.md" "docs/implementation/pattern-signatures/phase-1-detection.md"
update_file "docs/planned_features/pattern-learning/implementation-plan.md" "docs/implementation/PHASE_2" "docs/implementation/pattern-signatures/phase-2"
update_file "docs/planned_features/pattern-learning/implementation-plan.md" "docs/implementation/PHASE_3" "docs/implementation/pattern-signatures/phase-3"
update_file "docs/planned_features/pattern-learning/implementation-plan.md" "docs/implementation/PHASE_4" "docs/implementation/pattern-signatures/phase-4"
update_file "docs/planned_features/pattern-learning/implementation-plan.md" "docs/implementation/PHASE_5" "docs/implementation/pattern-signatures/phase-5"

# 7. Update references in PHASE_3_OVERVIEW
echo -e "${BLUE}[7/10] Updating references in phase-3-overview...${NC}"
update_file "docs/implementation/pattern-signatures/phase-3-overview.md" "docs/implementation/PHASE_3A_PATTERN_MATCHING.md" "docs/implementation/pattern-signatures/phase-3a-pattern-matching.md"
update_file "docs/implementation/pattern-signatures/phase-3-overview.md" "docs/implementation/PHASE_3B_TOOL_REGISTRATION.md" "docs/implementation/pattern-signatures/phase-3b-tool-registration.md"
update_file "docs/implementation/pattern-signatures/phase-3-overview.md" "docs/implementation/PHASE_3C_ADW_INTEGRATION.md" "docs/implementation/pattern-signatures/phase-3c-adw-integration.md"
update_file "docs/implementation/pattern-signatures/phase-3-overview.md" "docs/implementation/" "docs/implementation/pattern-signatures/"

# 8. Update Cost-Optimization README references
echo -e "${BLUE}[8/10] Updating Cost-Optimization README references...${NC}"
update_file "docs/features/cost-optimization/README.md" "../ADW/" "../features/adw/"
update_file "docs/features/cost-optimization/README.md" "../Architecture/" "../architecture/"
update_file "docs/features/cost-optimization/README.md" "../Analysis/" "../archive/analysis/"

# 9. Update conditional_docs.md references
echo -e "${BLUE}[9/10] Updating conditional_docs.md references...${NC}"
update_file ".claude/commands/conditional_docs.md" "docs/playwright-mcp.md" "docs/testing/playwright-mcp.md"

# 10. Update quick_start/docs.md references
echo -e "${BLUE}[10/10] Updating quick_start/docs.md references...${NC}"
if [ -f ".claude/commands/quick_start/docs.md" ]; then
    # This file needs manual review as it describes the structure
    echo -e "${YELLOW}⚠ Manual review needed: .claude/commands/quick_start/docs.md${NC}"
    echo -e "  This file describes the docs structure and should be manually updated"
fi

echo ""
echo -e "${GREEN}Reference updates complete!${NC}"
echo -e "${YELLOW}Files updated: $UPDATED${NC}"
echo ""
echo -e "${YELLOW}Manual review recommended for:${NC}"
echo -e "  - .claude/commands/quick_start/docs.md (structure description)"
echo -e "  - docs/README.md (may need navigation updates)"
echo -e "  - Any custom scripts that reference old paths"
echo ""
