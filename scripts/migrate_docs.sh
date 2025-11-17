#!/bin/bash

# Documentation Migration Script
# Reorganizes docs/ structure from 15+ folders to 7 purpose-driven folders
# Created: 2025-11-17

# Don't exit on error - continue to completion
set +e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
CREATED=0
MOVED=0
DELETED=0
UPDATED=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Documentation Migration Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Safety check - must be run from project root
if [ ! -d "docs" ] || [ ! -d "adws" ]; then
    echo -e "${RED}Error: Must be run from project root directory${NC}"
    exit 1
fi

# Create backup
echo -e "${YELLOW}Creating backup...${NC}"
if [ -d "docs_backup" ]; then
    rm -rf docs_backup
fi
cp -r docs/ docs_backup/
echo -e "${GREEN}✓ Backup created at docs_backup/${NC}"
echo ""

# Function to create directory if it doesn't exist
create_dir() {
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        echo -e "${GREEN}✓ Created: $1${NC}"
        ((CREATED++))
    fi
}

# Function to move file
move_file() {
    local src="$1"
    local dest="$2"

    if [ -f "$src" ]; then
        # Create destination directory if needed
        local dest_dir=$(dirname "$dest")
        create_dir "$dest_dir"

        # Move file
        mv "$src" "$dest"
        echo -e "${GREEN}✓ Moved: $src → $dest${NC}"
        ((MOVED++))
    else
        echo -e "${YELLOW}⚠ Not found: $src${NC}"
    fi
}

# Function to delete file
delete_file() {
    local file="$1"

    if [ -f "$file" ]; then
        rm "$file"
        echo -e "${RED}✓ Deleted: $file${NC}"
        ((DELETED++))
    fi
}

# Function to delete empty directories
cleanup_empty_dirs() {
    find docs -type d -empty -delete 2>/dev/null || true
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Phase 1: Handle Case-Sensitive Renames${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# On macOS, filesystem is case-insensitive, so we need to rename via temp
# Rename uppercase folders to temp names first
if [ -d "docs/Architecture" ]; then
    mv "docs/Architecture" "docs/Architecture_temp" 2>/dev/null || true
    echo -e "${YELLOW}Renamed Architecture to temp${NC}"
fi
if [ -d "docs/Testing" ]; then
    mv "docs/Testing" "docs/Testing_temp" 2>/dev/null || true
    echo -e "${YELLOW}Renamed Testing to temp${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Phase 2: Create New Directory Structure${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Create new directories
create_dir "docs/architecture"
create_dir "docs/architecture/decisions"
create_dir "docs/architecture/patterns"
create_dir "docs/architecture/testing"
create_dir "docs/architecture/guides"

create_dir "docs/features"
create_dir "docs/features/adw"
create_dir "docs/features/adw/external-tools"
create_dir "docs/features/github-integration/webhooks"
create_dir "docs/features/cost-optimization"
create_dir "docs/features/outloop-testing"

create_dir "docs/planned_features"
create_dir "docs/planned_features/pattern-learning"
create_dir "docs/planned_features/auto-tool-routing"

create_dir "docs/implementation/pattern-signatures"

create_dir "docs/testing"

create_dir "docs/archive"
create_dir "docs/archive/issues"
create_dir "docs/archive/phases"
create_dir "docs/archive/phases/post-shipping-cleanup"
create_dir "docs/archive/phases/workflow-history"
create_dir "docs/archive/deprecated"
create_dir "docs/archive/testing/build-checker"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Phase 3: Move Architecture Files${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

move_file "docs/INVERTED_CONTEXT_FLOW.md" "docs/architecture/decisions/inverted-context-flow.md"
move_file "docs/addtl_efficiency_strats.md" "docs/architecture/patterns/efficiency-strategies.md"
move_file "docs/CONTEXT_PRUNING_STRATEGY.md" "docs/architecture/patterns/context-pruning.md"
move_file "docs/Architecture_temp/README.md" "docs/architecture/README.md"
move_file "docs/Architecture_temp/CLEANUP_PERFORMANCE_OPTIMIZATION.md" "docs/archive/phases/post-shipping-cleanup/performance-optimization.md"
move_file "docs/Architecture_temp/POST_SHIPPING_CLEANUP_ARCHITECTURE.md" "docs/archive/phases/post-shipping-cleanup/architecture.md"
move_file "docs/Architecture_temp/POST_SHIPPING_CLEANUP_IMPLEMENTATION_PLAN.md" "docs/archive/phases/post-shipping-cleanup/implementation-plan.md"
move_file "docs/Architecture_temp/POST_SHIPPING_CLEANUP_SUMMARY.md" "docs/archive/phases/post-shipping-cleanup/summary.md"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Phase 4: Move Feature Files${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# ADW Features
move_file "docs/ADW/README.md" "docs/features/adw/README.md"
move_file "docs/ADW/ADW_TECHNICAL_OVERVIEW.md" "docs/features/adw/technical-overview.md"
move_file "docs/ADW/ADW_CHAINING_ARCHITECTURE.md" "docs/features/adw/chaining-architecture.md"
move_file "docs/ADW/EXTERNAL_TOOLS_INTEGRATION_GUIDE.md" "docs/features/adw/external-tools/integration-guide.md"
move_file "docs/ADW/EXTERNAL_TOOLS_MIGRATION_GUIDE.md" "docs/features/adw/external-tools/migration-guide.md"
move_file "docs/ADW/EXTERNAL_TOOLS_E2E_VALIDATION_GUIDE.md" "docs/features/adw/external-tools/e2e-validation-guide.md"
move_file "docs/ADW/EXTERNAL_TOOL_SCHEMAS.md" "docs/features/adw/external-tools/schemas.md"
move_file "docs/ADW/EXTERNAL_TOOLS_USAGE_EXAMPLES.md" "docs/features/adw/external-tools/usage-examples.md"
move_file "docs/ADW/EXTERNAL_TEST_TOOLS_ARCHITECTURE.md" "docs/features/adw/external-tools/test-tools-architecture.md"
move_file "docs/adw-optimization.md" "docs/features/adw/optimization.md"

# Webhooks
move_file "docs/Webhooks/README.md" "docs/features/github-integration/webhooks/README.md"
move_file "docs/Webhooks/WEBHOOK_TRIGGER_QUICK_REFERENCE.md" "docs/features/github-integration/webhooks/quick-reference.md"
move_file "docs/Webhooks/WEBHOOK_TRIGGER_SETUP.md" "docs/features/github-integration/webhooks/setup.md"

# Cost Optimization Features
move_file "docs/Cost-Optimization/README.md" "docs/features/cost-optimization/README.md"
move_file "docs/Cost-Optimization/COST_OPTIMIZATION_QUICK_START.md" "docs/features/cost-optimization/quick-start.md"
move_file "docs/Cost-Optimization/HOW_TO_GET_COST_ESTIMATES.md" "docs/features/cost-optimization/how-to-get-estimates.md"
move_file "docs/Cost-Optimization/ANTHROPIC_API_USAGE_ANALYSIS.md" "docs/features/cost-optimization/api-usage-analysis.md"
move_file "docs/Cost-Optimization/PROGRESSIVE_COST_ESTIMATION.md" "docs/features/cost-optimization/progressive-estimation.md"

# Other Features
move_file "docs/features/PLAYWRIGHT_LAZY_LOADING_IMPLEMENTATION.md" "docs/features/outloop-testing/playwright-lazy-loading.md"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Phase 5: Move Planned Features${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

move_file "docs/TOKEN_QUOTA_OPTIMIZATION_STRATEGY.md" "docs/planned_features/pattern-learning/token-quota-strategy.md"
move_file "docs/WORKFLOW_COST_ANALYSIS_PLAN.md" "docs/planned_features/pattern-learning/workflow-cost-analysis.md"
move_file "docs/OUT_LOOP_CODING_IMPLEMENTATION_PLAN.md" "docs/planned_features/pattern-learning/implementation-plan.md"
move_file "docs/ADW/IMPLEMENTATION_SUMMARY_OBSERVABILITY_AND_PATTERN_LEARNING.md" "docs/planned_features/pattern-learning/observability-summary.md"
move_file "docs/Cost-Optimization/COST_OPTIMIZATION_INTELLIGENCE.md" "docs/planned_features/pattern-learning/cost-intelligence.md"
move_file "docs/Cost-Optimization/CONVERSATION_RECONSTRUCTION_COST_OPTIMIZATION.md" "docs/planned_features/pattern-learning/conversation-reconstruction.md"
move_file "docs/Cost-Optimization/AUTO_ROUTING_COST_ANALYSIS.md" "docs/planned_features/auto-tool-routing/cost-analysis.md"
move_file "docs/Cost-Optimization/ADW_OPTIMIZATION_ANALYSIS.md" "docs/planned_features/pattern-learning/adw-optimization.md"

# Delete duplicate
delete_file "docs/ADW/OUT_LOOP_CODING_IMPLEMENTATION_PLAN.md"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Phase 6: Move Implementation Files${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

move_file "docs/implementation/PHASE_1_PATTERN_DETECTION.md" "docs/implementation/pattern-signatures/phase-1-detection.md"
move_file "docs/implementation/PHASE_1.1_CORE_PATTERN_SIGNATURES.md" "docs/implementation/pattern-signatures/phase-1.1-core-signatures.md"
move_file "docs/implementation/PHASE_1.2_PATTERN_DETECTION.md" "docs/implementation/pattern-signatures/phase-1.2-detection.md"
move_file "docs/implementation/PHASE_1.3_DATABASE_INTEGRATION.md" "docs/implementation/pattern-signatures/phase-1.3-database.md"
move_file "docs/implementation/PHASE_1.4_BACKFILL_AND_VALIDATION.md" "docs/implementation/pattern-signatures/phase-1.4-backfill.md"
move_file "docs/implementation/PHASE_2_CONTEXT_EFFICIENCY.md" "docs/implementation/pattern-signatures/phase-2-context-efficiency.md"
move_file "docs/implementation/PHASE_2_QUICK_START.md" "docs/implementation/pattern-signatures/phase-2-quick-start.md"
move_file "docs/implementation/PHASE_2A_FILE_ACCESS_TRACKING.md" "docs/implementation/pattern-signatures/phase-2a-file-tracking.md"
move_file "docs/implementation/PHASE_2B_CONTEXT_EFFICIENCY_ANALYSIS.md" "docs/implementation/pattern-signatures/phase-2b-analysis.md"
move_file "docs/implementation/PHASE_2C_CONTEXT_PROFILE_BUILDER.md" "docs/implementation/pattern-signatures/phase-2c-profile-builder.md"
move_file "docs/implementation/PHASE_3_OVERVIEW.md" "docs/implementation/pattern-signatures/phase-3-overview.md"
move_file "docs/implementation/PHASE_3_TOOL_ROUTING.md" "docs/implementation/pattern-signatures/phase-3-tool-routing.md"
move_file "docs/implementation/PHASE_3A_PATTERN_MATCHING.md" "docs/implementation/pattern-signatures/phase-3a-pattern-matching.md"
move_file "docs/implementation/PHASE_3B_TOOL_REGISTRATION.md" "docs/implementation/pattern-signatures/phase-3b-tool-registration.md"
move_file "docs/implementation/PHASE_3C_ADW_INTEGRATION.md" "docs/implementation/pattern-signatures/phase-3c-adw-integration.md"
move_file "docs/implementation/PHASE_4_AUTO_DISCOVERY.md" "docs/implementation/pattern-signatures/phase-4-auto-discovery.md"
move_file "docs/implementation/PHASE_5_QUOTA_MANAGEMENT.md" "docs/implementation/pattern-signatures/phase-5-quota-management.md"
move_file "docs/implementation/PHASES_3_4_5_SUMMARY.md" "docs/implementation/pattern-signatures/phases-3-4-5-summary.md"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Phase 7: Move Testing Files${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

move_file "docs/playwright-mcp.md" "docs/testing/playwright-mcp.md"
move_file "docs/Testing_temp/README.md" "docs/testing/README.md"
move_file "docs/Testing_temp/START_HERE.md" "docs/testing/getting-started.md"
move_file "docs/Testing_temp/PYTEST_QUICK_START.md" "docs/testing/pytest-quick-start.md"
move_file "docs/Testing_temp/TEST_FILES_INDEX.md" "docs/testing/test-files-index.md"
move_file "docs/Testing_temp/TEST_GENERATION_VERIFICATION.md" "docs/testing/test-generation-verification.md"
move_file "docs/Testing_temp/TESTING_DELIVERABLES.md" "docs/testing/deliverables.md"
move_file "docs/Testing_temp/TESTS_CREATED.md" "docs/testing/tests-created.md"

# Move Build-Checker to archive
if [ -d "docs/Testing_temp/Build-Checker" ]; then
    mv docs/Testing_temp/Build-Checker/* docs/archive/testing/build-checker/ 2>/dev/null || true
    echo -e "${GREEN}✓ Moved: docs/Testing_temp/Build-Checker → docs/archive/testing/build-checker${NC}"
    ((MOVED++))
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Phase 8: Move Archive Files${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

move_file "docs/Archive/README.md" "docs/archive/README.md"
move_file "docs/Archive/NEW_SESSION_PRIMER.md" "docs/archive/deprecated/new-session-primer.md"
move_file "docs/Analysis/ISSUE_8_PR_COMPARISON.md" "docs/archive/issues/issue-8/pr-comparison.md"

# Move all Archived Issues
if [ -d "docs/Archived Issues" ]; then
    for file in "docs/Archived Issues"/*.md; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            move_file "$file" "docs/archive/issues/$filename"
        fi
    done
fi

# Move Implementation Plans to archive
move_file "docs/Implementation Plans/PHASE_3_WORKFLOW_HISTORY_ENHANCEMENTS.md" "docs/archive/phases/workflow-history/phase-3-enhancements.md"
move_file "docs/Implementation Plans/README.md" "docs/archive/phases/workflow-history/README.md"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Phase 9: Delete Log Files & Cleanup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Delete log files (they don't belong in docs)
if [ -d "docs/logs" ]; then
    rm -rf "docs/logs"
    echo -e "${RED}✓ Deleted: docs/logs/ (doesn't belong in documentation)${NC}"
    ((DELETED++))
fi

# Delete Guides folder if empty or just has README
if [ -d "docs/Guides" ]; then
    if [ -z "$(ls -A docs/Guides)" ] || [ "$(ls docs/Guides)" = "README.md" ]; then
        rm -rf "docs/Guides"
        echo -e "${RED}✓ Deleted: docs/Guides/ (empty or minimal)${NC}"
        ((DELETED++))
    fi
fi

# Remove temp directories
if [ -d "docs/Architecture_temp" ]; then
    rmdir "docs/Architecture_temp" 2>/dev/null || true
    echo -e "${GREEN}✓ Removed temp: docs/Architecture_temp${NC}"
fi
if [ -d "docs/Testing_temp" ]; then
    rmdir "docs/Testing_temp" 2>/dev/null || true
    echo -e "${GREEN}✓ Removed temp: docs/Testing_temp${NC}"
fi

cleanup_empty_dirs
echo -e "${GREEN}✓ Removed all empty directories${NC}"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Phase 10: Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${GREEN}Migration Complete!${NC}"
echo ""
echo -e "${YELLOW}Statistics:${NC}"
echo -e "  Directories created: ${CREATED}"
echo -e "  Files moved: ${MOVED}"
echo -e "  Files deleted: ${DELETED}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "  1. Review migration with: ${BLUE}tree docs/ -L 2${NC}"
echo -e "  2. Update references with: ${BLUE}./scripts/update_doc_references.sh${NC}"
echo -e "  3. Validate changes with: ${BLUE}./scripts/validate_migration.sh${NC}"
echo -e "  4. If everything looks good: ${BLUE}git add docs/ && git commit -m 'docs: Reorganize documentation structure'${NC}"
echo -e "  5. If something went wrong: ${BLUE}rm -rf docs/ && mv docs_backup/ docs/${NC}"
echo ""
echo -e "${GREEN}Backup preserved at: docs_backup/${NC}"
echo ""
