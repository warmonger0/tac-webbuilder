# Documentation Migration Plan

**Created:** 2025-11-17
**Purpose:** Reorganize documentation structure for better clarity and lifecycle management

## Executive Summary

This plan reorganizes 90+ documentation files from an over-complicated 15+ subfolder structure into a purpose-driven, 6-folder lifecycle structure.

**Benefits:**
- **50% fewer top-level directories** (15 → 7)
- **Purpose-driven organization** (by lifecycle stage, not just topic)
- **Clear documentation flow** (planned → implementing → implemented → archived)
- **Easier maintenance** (related docs grouped together)

---

## New Structure

```
docs/
├── README.md                          # Navigation guide
├── api.md                            # Core reference docs (root level)
├── architecture.md
├── cli.md
├── configuration.md
├── examples.md
├── troubleshooting.md
├── web-ui.md
│
├── architecture/                      # WHY we built things this way
├── features/                          # WHAT exists in production
├── planned_features/                  # WHAT's NEXT
├── implementation/                    # WHAT's IN FLIGHT (active work only)
├── testing/                           # Testing strategy & architecture
└── archive/                           # WHAT's DONE
```

---

## Migration Mapping

### 1. Root Level Files (Core Reference)

| Current Location | New Location | Action | Notes |
|------------------|--------------|--------|-------|
| `docs/api.md` | `docs/api.md` | **KEEP** | Core reference |
| `docs/architecture.md` | `docs/architecture.md` | **KEEP** | Core reference |
| `docs/cli.md` | `docs/cli.md` | **KEEP** | Core reference |
| `docs/configuration.md` | `docs/configuration.md` | **KEEP** | Core reference |
| `docs/examples.md` | `docs/examples.md` | **KEEP** | Core reference |
| `docs/troubleshooting.md` | `docs/troubleshooting.md` | **KEEP** | Core reference |
| `docs/web-ui.md` | `docs/web-ui.md` | **KEEP** | Core reference |
| `docs/playwright-mcp.md` | `docs/testing/playwright-mcp.md` | **MOVE** | Testing architecture |
| `docs/README.md` | `docs/README.md` | **UPDATE** | Update navigation |

### 2. Architecture Folder → `docs/architecture/`

| Current Location | New Location | Action | Notes |
|------------------|--------------|--------|-------|
| `docs/INVERTED_CONTEXT_FLOW.md` | `docs/architecture/decisions/inverted-context-flow.md` | **MOVE** | Architectural decision |
| `docs/addtl_efficiency_strats.md` | `docs/architecture/patterns/efficiency-strategies.md` | **MOVE** | Pattern doc |
| `docs/CONTEXT_PRUNING_STRATEGY.md` | `docs/architecture/patterns/context-pruning.md` | **MOVE** | Pattern doc |
| `docs/Architecture/README.md` | `docs/architecture/README.md` | **MOVE** | Index file |
| `docs/Architecture/CLEANUP_PERFORMANCE_OPTIMIZATION.md` | `docs/archive/phases/post-shipping-cleanup/performance-optimization.md` | **MOVE** | Completed phase |
| `docs/Architecture/POST_SHIPPING_CLEANUP_ARCHITECTURE.md` | `docs/archive/phases/post-shipping-cleanup/architecture.md` | **MOVE** | Completed phase |
| `docs/Architecture/POST_SHIPPING_CLEANUP_IMPLEMENTATION_PLAN.md` | `docs/archive/phases/post-shipping-cleanup/implementation-plan.md` | **MOVE** | Completed phase |
| `docs/Architecture/POST_SHIPPING_CLEANUP_SUMMARY.md` | `docs/archive/phases/post-shipping-cleanup/summary.md` | **MOVE** | Completed phase |

**Create:**
- `docs/architecture/decisions/` (new folder)
- `docs/architecture/patterns/` (new folder)
- `docs/architecture/testing/` (new folder) - will contain testing strategy docs

### 3. Features Folder → `docs/features/`

| Current Location | New Location | Action | Notes |
|------------------|--------------|--------|-------|
| `docs/features/PLAYWRIGHT_LAZY_LOADING_IMPLEMENTATION.md` | `docs/features/outloop-testing/playwright-lazy-loading.md` | **MOVE** | Feature doc |
| `docs/ADW/README.md` | `docs/features/adw/README.md` | **MOVE** | Feature overview |
| `docs/ADW/ADW_TECHNICAL_OVERVIEW.md` | `docs/features/adw/technical-overview.md` | **MOVE** | Feature doc |
| `docs/ADW/ADW_CHAINING_ARCHITECTURE.md` | `docs/features/adw/chaining-architecture.md` | **MOVE** | Feature architecture |
| `docs/ADW/EXTERNAL_TOOLS_INTEGRATION_GUIDE.md` | `docs/features/adw/external-tools/integration-guide.md` | **MOVE** | Feature guide |
| `docs/ADW/EXTERNAL_TOOLS_MIGRATION_GUIDE.md` | `docs/features/adw/external-tools/migration-guide.md` | **MOVE** | Feature guide |
| `docs/ADW/EXTERNAL_TOOLS_E2E_VALIDATION_GUIDE.md` | `docs/features/adw/external-tools/e2e-validation-guide.md` | **MOVE** | Feature guide |
| `docs/ADW/EXTERNAL_TOOL_SCHEMAS.md` | `docs/features/adw/external-tools/schemas.md` | **MOVE** | Feature doc |
| `docs/ADW/EXTERNAL_TOOLS_USAGE_EXAMPLES.md` | `docs/features/adw/external-tools/usage-examples.md` | **MOVE** | Feature examples |
| `docs/ADW/EXTERNAL_TEST_TOOLS_ARCHITECTURE.md` | `docs/features/adw/external-tools/test-tools-architecture.md` | **MOVE** | Feature architecture |
| `docs/adw-optimization.md` | `docs/features/adw/optimization.md` | **MOVE** | Feature doc |
| `docs/Webhooks/README.md` | `docs/features/github-integration/webhooks/README.md` | **MOVE** | Feature doc |
| `docs/Webhooks/WEBHOOK_TRIGGER_QUICK_REFERENCE.md` | `docs/features/github-integration/webhooks/quick-reference.md` | **MOVE** | Feature doc |
| `docs/Webhooks/WEBHOOK_TRIGGER_SETUP.md` | `docs/features/github-integration/webhooks/setup.md` | **MOVE** | Feature doc |
| `docs/Cost-Optimization/README.md` | `docs/features/cost-optimization/README.md` | **MOVE** | Feature overview |
| `docs/Cost-Optimization/COST_OPTIMIZATION_QUICK_START.md` | `docs/features/cost-optimization/quick-start.md` | **MOVE** | Feature guide |
| `docs/Cost-Optimization/HOW_TO_GET_COST_ESTIMATES.md` | `docs/features/cost-optimization/how-to-get-estimates.md` | **MOVE** | Feature guide |
| `docs/Cost-Optimization/ANTHROPIC_API_USAGE_ANALYSIS.md` | `docs/features/cost-optimization/api-usage-analysis.md` | **MOVE** | Feature analysis |
| `docs/Cost-Optimization/PROGRESSIVE_COST_ESTIMATION.md` | `docs/features/cost-optimization/progressive-estimation.md` | **MOVE** | Feature doc |

**Create:**
- `docs/features/adw/` (new folder)
- `docs/features/adw/external-tools/` (new folder)
- `docs/features/github-integration/` (new folder)
- `docs/features/github-integration/webhooks/` (new folder)
- `docs/features/cost-optimization/` (new folder)
- `docs/features/outloop-testing/` (new folder)

### 4. Planned Features → `docs/planned_features/`

| Current Location | New Location | Action | Notes |
|------------------|--------------|--------|-------|
| `docs/TOKEN_QUOTA_OPTIMIZATION_STRATEGY.md` | `docs/planned_features/pattern-learning/token-quota-strategy.md` | **MOVE** | Planned feature |
| `docs/WORKFLOW_COST_ANALYSIS_PLAN.md` | `docs/planned_features/pattern-learning/workflow-cost-analysis.md` | **MOVE** | Planned feature |
| `docs/OUT_LOOP_CODING_IMPLEMENTATION_PLAN.md` | `docs/planned_features/pattern-learning/implementation-plan.md` | **MOVE** | Planned feature |
| `docs/ADW/OUT_LOOP_CODING_IMPLEMENTATION_PLAN.md` | **DELETE** | **DELETE** | Duplicate of above |
| `docs/ADW/IMPLEMENTATION_SUMMARY_OBSERVABILITY_AND_PATTERN_LEARNING.md` | `docs/planned_features/pattern-learning/observability-summary.md` | **MOVE** | Planned feature |
| `docs/Cost-Optimization/COST_OPTIMIZATION_INTELLIGENCE.md` | `docs/planned_features/pattern-learning/cost-intelligence.md` | **MOVE** | Planned feature (part of pattern learning) |
| `docs/Cost-Optimization/CONVERSATION_RECONSTRUCTION_COST_OPTIMIZATION.md` | `docs/planned_features/pattern-learning/conversation-reconstruction.md` | **MOVE** | Planned feature |
| `docs/Cost-Optimization/AUTO_ROUTING_COST_ANALYSIS.md` | `docs/planned_features/auto-tool-routing/cost-analysis.md` | **MOVE** | Planned feature |
| `docs/Cost-Optimization/ADW_OPTIMIZATION_ANALYSIS.md` | `docs/planned_features/pattern-learning/adw-optimization.md` | **MOVE** | Planned feature |

**Create:**
- `docs/planned_features/pattern-learning/` (new folder)
- `docs/planned_features/auto-tool-routing/` (new folder)
- `docs/planned_features/pattern-learning/README.md` (brief overview)
- `docs/planned_features/auto-tool-routing/README.md` (brief overview)

### 5. Implementation (Active Work) → `docs/implementation/`

**Current Status:** All PHASE files in `docs/implementation/` are ACTIVE work

| Current Location | New Location | Action | Notes |
|------------------|--------------|--------|-------|
| `docs/implementation/README.md` | `docs/implementation/README.md` | **KEEP** | Already good |
| `docs/implementation/PHASE_1_PATTERN_DETECTION.md` | `docs/implementation/pattern-signatures/phase-1-detection.md` | **MOVE** | Active work |
| `docs/implementation/PHASE_1.1_CORE_PATTERN_SIGNATURES.md` | `docs/implementation/pattern-signatures/phase-1.1-core-signatures.md` | **MOVE** | Active work |
| `docs/implementation/PHASE_1.2_PATTERN_DETECTION.md` | `docs/implementation/pattern-signatures/phase-1.2-detection.md` | **MOVE** | Active work |
| `docs/implementation/PHASE_1.3_DATABASE_INTEGRATION.md` | `docs/implementation/pattern-signatures/phase-1.3-database.md` | **MOVE** | Active work |
| `docs/implementation/PHASE_1.4_BACKFILL_AND_VALIDATION.md` | `docs/implementation/pattern-signatures/phase-1.4-backfill.md` | **MOVE** | Active work |
| `docs/implementation/PHASE_2_CONTEXT_EFFICIENCY.md` | `docs/implementation/pattern-signatures/phase-2-context-efficiency.md` | **MOVE** | Active work |
| `docs/implementation/PHASE_2_QUICK_START.md` | `docs/implementation/pattern-signatures/phase-2-quick-start.md` | **MOVE** | Active work |
| `docs/implementation/PHASE_2A_FILE_ACCESS_TRACKING.md` | `docs/implementation/pattern-signatures/phase-2a-file-tracking.md` | **MOVE** | Active work |
| `docs/implementation/PHASE_2B_CONTEXT_EFFICIENCY_ANALYSIS.md` | `docs/implementation/pattern-signatures/phase-2b-analysis.md` | **MOVE** | Active work |
| `docs/implementation/PHASE_2C_CONTEXT_PROFILE_BUILDER.md` | `docs/implementation/pattern-signatures/phase-2c-profile-builder.md` | **MOVE** | Active work |
| `docs/implementation/PHASE_3_OVERVIEW.md` | `docs/implementation/pattern-signatures/phase-3-overview.md` | **MOVE** | Active work |
| `docs/implementation/PHASE_3_TOOL_ROUTING.md` | `docs/implementation/pattern-signatures/phase-3-tool-routing.md` | **MOVE** | Active work |
| `docs/implementation/PHASE_3A_PATTERN_MATCHING.md` | `docs/implementation/pattern-signatures/phase-3a-pattern-matching.md` | **MOVE** | Active work |
| `docs/implementation/PHASE_3B_TOOL_REGISTRATION.md` | `docs/implementation/pattern-signatures/phase-3b-tool-registration.md` | **MOVE** | Active work |
| `docs/implementation/PHASE_3C_ADW_INTEGRATION.md` | `docs/implementation/pattern-signatures/phase-3c-adw-integration.md` | **MOVE** | Active work |
| `docs/implementation/PHASE_4_AUTO_DISCOVERY.md` | `docs/implementation/pattern-signatures/phase-4-auto-discovery.md` | **MOVE** | Active work |
| `docs/implementation/PHASE_5_QUOTA_MANAGEMENT.md` | `docs/implementation/pattern-signatures/phase-5-quota-management.md` | **MOVE** | Active work |
| `docs/implementation/PHASES_3_4_5_SUMMARY.md` | `docs/implementation/pattern-signatures/phases-3-4-5-summary.md` | **MOVE** | Active work |

**Create:**
- `docs/implementation/pattern-signatures/` (new folder for current work)
- `docs/implementation/pattern-signatures/README.md` (progress tracker)

### 6. Testing → `docs/testing/`

| Current Location | New Location | Action | Notes |
|------------------|--------------|--------|-------|
| `docs/playwright-mcp.md` | `docs/testing/playwright-mcp.md` | **MOVE** | Testing architecture |
| `docs/Testing/README.md` | `docs/testing/README.md` | **MOVE** | Testing index |
| `docs/Testing/START_HERE.md` | `docs/testing/getting-started.md` | **MOVE** | Testing guide |
| `docs/Testing/PYTEST_QUICK_START.md` | `docs/testing/pytest-quick-start.md` | **MOVE** | Testing guide |
| `docs/Testing/TEST_FILES_INDEX.md` | `docs/testing/test-files-index.md` | **MOVE** | Testing index |
| `docs/Testing/TEST_GENERATION_VERIFICATION.md` | `docs/testing/test-generation-verification.md` | **MOVE** | Testing process |
| `docs/Testing/TESTING_DELIVERABLES.md` | `docs/testing/deliverables.md` | **MOVE** | Testing docs |
| `docs/Testing/TESTS_CREATED.md` | `docs/testing/tests-created.md` | **MOVE** | Testing log |
| `docs/Testing/Build-Checker/` | `docs/archive/testing/build-checker/` | **MOVE** | Completed testing project |

**Create:**
- `docs/testing/` (new folder)

### 7. Archive → `docs/archive/`

| Current Location | New Location | Action | Notes |
|------------------|--------------|--------|-------|
| `docs/Archive/README.md` | `docs/archive/README.md` | **MOVE** | Archive index |
| `docs/Archive/NEW_SESSION_PRIMER.md` | `docs/archive/deprecated/new-session-primer.md` | **MOVE** | Deprecated doc |
| `docs/Archived Issues/` (all files) | `docs/archive/issues/` | **MOVE** | Archived issues |
| `docs/Analysis/ISSUE_8_PR_COMPARISON.md` | `docs/archive/issues/issue-8/pr-comparison.md` | **MOVE** | Issue analysis |
| `docs/Implementation Plans/` | `docs/archive/phases/workflow-history/` | **MOVE** | Completed implementation |
| `docs/logs/` | **DELETE** | **DELETE** | Log files don't belong in docs |

**Archived Issues Reorganization:**
- Group by issue number where possible
- Create `docs/archive/issues/issue-{N}/` folders
- Move related docs into issue folders

**Create:**
- `docs/archive/` (new folder)
- `docs/archive/issues/` (new folder)
- `docs/archive/phases/` (new folder)
- `docs/archive/deprecated/` (new folder)
- `docs/archive/testing/` (new folder)

---

## Files Requiring Reference Updates

### High Priority (Direct Path References)

1. **`docs/OUT_LOOP_CODING_IMPLEMENTATION_PLAN.md`** → Moving to `docs/planned_features/pattern-learning/implementation-plan.md`
   - References in:
     - `docs/implementation/README.md:18` - Update path
     - `docs/ADW/IMPLEMENTATION_SUMMARY_OBSERVABILITY_AND_PATTERN_LEARNING.md` - Update path
   - Contains internal references to implementation phase docs (lines 49-285) - Update all paths

2. **`docs/implementation/PHASE_3_OVERVIEW.md`**
   - Lines 114, 131, 154, 237 - References to other PHASE docs
   - Update all paths to new `docs/implementation/pattern-signatures/` structure

3. **`.claude/commands/conditional_docs.md`**
   - References to:
     - `docs/api.md` - No change needed
     - `docs/web-ui.md` - No change needed
     - `docs/architecture.md` - No change needed
     - `docs/cli.md` - No change needed
     - `docs/playwright-mcp.md` - **UPDATE** to `docs/testing/playwright-mcp.md`
     - `docs/troubleshooting.md` - No change needed
     - `docs/examples.md` - No change needed
   - All other references are in `.claude/commands/` which don't need updating

4. **`docs/implementation/README.md`**
   - Line 18: `../OUT_LOOP_CODING_IMPLEMENTATION_PLAN.md` → `../planned_features/pattern-learning/implementation-plan.md`
   - Lines 26-59: Phase file references → Update to `pattern-signatures/` subfolder
   - Lines 321-323: References to docs in Cost-Optimization → Update paths

5. **`docs/Cost-Optimization/README.md`**
   - Lines 68-76: References to other docs folders (ADW, Architecture, Analysis) → Update paths

6. **ADW External Tools Documentation**
   - `docs/ADW/EXTERNAL_TOOLS_USAGE_EXAMPLES.md:697` - Reference to `docs/ADW_CHAINING_ARCHITECTURE.md`
   - `docs/ADW/EXTERNAL_TOOLS_MIGRATION_GUIDE.md:129,760` - Reference to `docs/ADW_CHAINING_ARCHITECTURE.md`
   - `docs/ADW/EXTERNAL_TOOLS_INTEGRATION_GUIDE.md:27` - Reference to `docs/ADW_CHAINING_ARCHITECTURE.md`
   - `docs/ADW/EXTERNAL_TOOLS_E2E_VALIDATION_GUIDE.md:429` - Reference to `docs/ADW_CHAINING_ARCHITECTURE.md`
   - **UPDATE ALL** to `docs/features/adw/chaining-architecture.md`

7. **`adws/README.md`**
   - Line 651: Reference to `docs/ADW_CHAINING_ARCHITECTURE.md` → Update to `docs/features/adw/chaining-architecture.md`

### Medium Priority (Contextual References)

8. **Archived Issues Documents**
   - `docs/Archived Issues/CONTEXT_HANDOFF_ISSUE_11.md:245` - Reference to `docs/ADW_TECHNICAL_OVERVIEW.md`
   - **UPDATE** to `docs/features/adw/technical-overview.md`

9. **Feature Documentation**
   - `docs/features/PLAYWRIGHT_LAZY_LOADING_IMPLEMENTATION.md:324` - Reference to `docs/ADW_TECHNICAL_OVERVIEW.md`
   - **UPDATE** to `docs/features/adw/technical-overview.md`

10. **Cost Optimization Docs**
    - `docs/Cost-Optimization/HOW_TO_GET_COST_ESTIMATES.md:245` - Reference to `docs/ADW_OPTIMIZATION_ANALYSIS.md`
    - **UPDATE** to `docs/features/adw/optimization.md`

### Low Priority (Informational/Historical)

11. **Archive/Completed Phase Documents**
    - These are historical and don't need updating as urgently
    - Can be updated during migration for completeness

---

## Migration Script

The migration will be performed by a bash script that:
1. Creates new directory structure
2. Moves files to new locations
3. Updates internal references
4. Removes empty directories
5. Creates new README files where needed

**Script:** `scripts/migrate_docs.sh`

---

## Validation Steps

After migration:

1. **Verify no broken links:**
   ```bash
   # Search for old paths
   grep -r "docs/ADW/" docs/ .claude/
   grep -r "docs/Cost-Optimization/" docs/ .claude/
   grep -r "docs/Architecture/" docs/ .claude/
   grep -r "docs/Testing/" docs/ .claude/
   grep -r "docs/implementation/PHASE_" docs/ .claude/
   ```

2. **Verify new structure:**
   ```bash
   tree docs/ -L 2
   ```

3. **Verify file counts:**
   ```bash
   # Before
   find docs -type f -name "*.md" | wc -l

   # After (should be same or less due to duplicate removal)
   find docs -type f -name "*.md" | wc -l
   ```

4. **Test documentation loading:**
   - Run `/prime` command
   - Load quick start guides
   - Verify conditional_docs.md references work

5. **Update `.claude/commands/conditional_docs.md`:**
   - Update all references to moved files
   - Add new folder structure navigation

6. **Update `.claude/commands/quick_start/docs.md`:**
   - Update folder structure description
   - Update file locations

---

## Rollback Plan

If migration causes issues:

1. **Git rollback:**
   ```bash
   git checkout HEAD -- docs/
   ```

2. **Restore from backup:**
   ```bash
   # Before migration, create backup
   cp -r docs/ docs_backup/

   # To rollback
   rm -rf docs/
   mv docs_backup/ docs/
   ```

---

## Post-Migration Tasks

1. **Update `adw_cleanup_iso.py`:**
   - Line 14-19: Update destination paths
   - Should move specs to `docs/archive/issues/issue-{N}/`
   - Should move plans to `docs/archive/issues/issue-{N}/`

2. **Create README files:**
   - `docs/architecture/README.md`
   - `docs/features/README.md`
   - `docs/planned_features/README.md`
   - `docs/testing/README.md`
   - `docs/archive/README.md`

3. **Update main docs/README.md:**
   - New folder structure
   - Navigation guide
   - Quick links

4. **Test ADW workflows:**
   - Run test workflow
   - Verify cleanup phase works with new structure

---

## Timeline

**Estimated Duration:** 2-3 hours

1. **Phase 1 (30 min):** Create migration script
2. **Phase 2 (15 min):** Test migration on subset of files
3. **Phase 3 (30 min):** Run full migration
4. **Phase 4 (45 min):** Update all references
5. **Phase 5 (30 min):** Validation and testing

---

## Success Criteria

- [ ] All 90+ files migrated successfully
- [ ] No broken internal references
- [ ] Directory count reduced from 15 to 7
- [ ] All README files created
- [ ] `.claude/commands/conditional_docs.md` updated
- [ ] `adw_cleanup_iso.py` updated for new structure
- [ ] Migration tested with sample workflow
- [ ] Git commit created with full migration

---

## Notes

- **Duplicate Files:** `docs/ADW/OUT_LOOP_CODING_IMPLEMENTATION_PLAN.md` is identical to `docs/OUT_LOOP_CODING_IMPLEMENTATION_PLAN.md` - delete duplicate
- **Log Files:** `docs/logs/` should be deleted (doesn't belong in documentation)
- **Empty Folders:** Remove after migration
- **Lowercase Convention:** New structure uses lowercase-with-hyphens for consistency
