# ADW Workflow Enhancement Implementation Plan

**Status:** In Progress
**Created:** 2025-11-17
**Target Completion:** TBD

---

## Executive Summary

This plan implements three critical missing workflows in the ADW system:

1. **Stepwise Refinement** - Analyzes issues to determine if breakdown is needed
2. **Complete SDLC** - Full workflow chain with ALL phases including lint
3. **Complete ZTE** - Zero Touch Execution with ALL phases including lint

### Goals

- ✅ Enable intelligent issue breakdown before processing
- ✅ Provide complete SDLC workflow with proper phase ordering
- ✅ Fix missing lint phase in ZTE workflow
- ✅ Maintain external workflow optimization (70-95% token reduction)
- ✅ Respect existing ADW architecture patterns
- ✅ Update all documentation and references
- ✅ Archive obsolete workflows
- ✅ Provide regression testing

---

## Current State Analysis

### Existing Workflow Categories

#### ✅ **Entry Point Workflows** (Create Worktrees)
- `adw_plan_iso.py` - Standard planning
- `adw_plan_iso_optimized.py` - Inverted context flow planning (77% cost reduction)
- `adw_patch_iso.py` - Quick patch workflow
- `adw_lightweight_iso.py` - Cost-optimized simple changes

#### ✅ **Phase Workflows** (Require Worktree)
- `adw_build_iso.py` - Implementation (has external: `adw_build_external.py`)
- `adw_lint_iso.py` - Linting (has external: `adw_lint_external.py`)
- `adw_test_iso.py` - Testing (has external: `adw_test_external.py`)
- `adw_review_iso.py` - Review (NO external)
- `adw_document_iso.py` - Documentation (NO external)
- `adw_ship_iso.py` - Ship/merge (pure Python, no AI)
- `adw_cleanup_iso.py` - Cleanup (pure Python, no AI)

#### ⚠️ **Incomplete Orchestrators**
- `adw_sdlc_iso.py` - Plan → Build → **Lint** → Test → Review → Document (missing Ship/Cleanup)
- `adw_sdlc_zte_iso.py` - Plan → Build → Test → Review → Document → Ship → Cleanup (missing **Lint**)

#### ✅ **Partial Orchestrators** (Legacy/Special Purpose)
- `adw_plan_build_iso.py` - Plan + Build only
- `adw_plan_build_test_iso.py` - Plan + Build + Test
- `adw_plan_build_test_review_iso.py` - Plan + Build + Test + Review
- `adw_plan_build_review_iso.py` - Plan + Build + Review (skip tests)
- `adw_plan_build_document_iso.py` - Plan + Build + Document

#### ✅ **Support Workflows**
- `adw_build_workflow.py` - External build execution
- `adw_lint_workflow.py` - External lint execution
- `adw_test_workflow.py` - External test execution
- `adw_test_gen_workflow.py` - Test generation

### Missing Workflows

#### ❌ **Critical Missing**
1. **Stepwise Refinement** - No workflow exists to analyze if issue should be broken down
2. **Complete SDLC** - No workflow has all 8 phases (Plan → Build → Lint → Test → Review → Doc → Ship → Cleanup)
3. **Complete ZTE with Lint** - ZTE missing lint phase

#### ❌ **External Optimization Gaps**
- No external workflow for Review (currently inline only)
- No external workflow for Document (currently inline only)

---

## Implementation Plan

### Phase 1: Create Core Workflows ✅

#### 1.1 Create `adw_stepwise_iso.py`

**Purpose:** Analyze issue complexity and decide if breakdown into sub-issues is beneficial.

**Workflow:**
1. Fetch issue from GitHub
2. Generate unique ADW ID
3. Single AI call: Analyze issue for complexity/decomposition
4. Output decision:
   - **ATOMIC**: Issue is already atomic, proceed with normal workflow
   - **DECOMPOSE**: Issue should be broken down
     - Generate sub-issue specifications (title, body, acceptance criteria)
     - Create sub-issues via GitHub API
     - Link sub-issues to parent
     - Post summary comment with breakdown rationale
5. Save state with decision and sub-issue numbers
6. Exit with appropriate status code

**Inverted Context Flow:**
- Single comprehensive AI call with full issue context
- Deterministic GitHub API calls to create sub-issues (zero AI)
- Minimal validation call for structured output

**Cost:** ~$0.30-0.50 per analysis

**Files to create:**
- `adws/adw_stepwise_iso.py` - Main workflow
- `.claude/commands/stepwise_analysis.md` - Slash command template

#### 1.2 Create `adw_sdlc_complete_iso.py`

**Purpose:** Complete SDLC workflow with ALL phases in correct order.

**Workflow:**
```
Plan → Build → Lint → Test → Review → Document → Ship → Cleanup
```

**Phase Details:**
1. **Plan** - `adw_plan_iso.py` (or optimized variant)
2. **Build** - `adw_build_iso.py` (defaults to external)
3. **Lint** - `adw_lint_iso.py` (defaults to external)
4. **Test** - `adw_test_iso.py` (defaults to external, skip E2E)
5. **Review** - `adw_review_iso.py` (with auto-resolution)
6. **Document** - `adw_document_iso.py`
7. **Ship** - `adw_ship_iso.py` (approve & merge PR)
8. **Cleanup** - Pure Python cleanup (no LLM)

**Flags:**
- `--skip-e2e` - Skip E2E tests
- `--skip-resolution` - Skip auto-resolution of review issues
- `--no-external` - Disable external workflows (higher token usage)
- `--use-optimized-plan` - Use inverted context flow planner

**Error Handling:**
- Stop on failure at any phase
- Post detailed error to GitHub issue
- Preserve state for manual intervention

**Files to create:**
- `adws/adw_sdlc_complete_iso.py` - Complete SDLC orchestrator

#### 1.3 Create `adw_sdlc_complete_zte_iso.py`

**Purpose:** Zero Touch Execution with ALL phases including lint.

**Workflow:**
```
Plan → Build → Lint → Test → Review → Document → Ship → Cleanup
```

**Key Differences from Standard:**
- Automatically ships to production if all phases pass
- Cleanup runs automatically after ship
- More aggressive error handling (fail fast)
- Posts ZTE status updates at each phase

**Warning Messages:**
- Clear warnings about auto-merge
- GitHub comment with ZTE initiation notice
- Abort messages if any phase fails

**Files to create:**
- `adws/adw_sdlc_complete_zte_iso.py` - Complete ZTE orchestrator

---

### Phase 2: Documentation Updates 📝

#### 2.1 Update `adws/README.md`

**Changes:**
- Add stepwise refinement workflow section
- Update SDLC workflow documentation to note incomplete vs complete
- Add complete SDLC workflows to quick start
- Update workflow decision tree
- Add deprecation notices for incomplete workflows

#### 2.2 Update `.claude/commands/references/adw_workflows.md`

**Changes:**
- Add stepwise refinement section
- Add complete SDLC orchestrators section
- Update workflow comparison table
- Add cost/token comparisons
- Document when to use each workflow variant

#### 2.3 Update `.claude/commands/quick_start/adw.md`

**Changes:**
- Add stepwise refinement to quick workflow selection
- Update complete workflows section
- Add recommended workflow decision tree

#### 2.4 Create Architecture Documentation

**New Files:**
- `docs/planned_features/workflow-enhancements/stepwise-refinement-architecture.md`
- `docs/planned_features/workflow-enhancements/complete-sdlc-architecture.md`
- `docs/planned_features/workflow-enhancements/workflow-comparison.md`

---

### Phase 3: Cleanup & Archival 🗂️

#### 3.1 Identify Obsolete Workflows

**Candidates for Deprecation:**
After complete workflows exist, these partial chains become redundant:
- `adw_plan_build_iso.py` → Use `adw_sdlc_complete_iso.py` instead
- `adw_plan_build_test_iso.py` → Use `adw_sdlc_complete_iso.py` instead
- `adw_plan_build_test_review_iso.py` → Use `adw_sdlc_complete_iso.py` instead
- `adw_plan_build_review_iso.py` → Use `adw_sdlc_complete_iso.py` instead
- `adw_plan_build_document_iso.py` → Use `adw_sdlc_complete_iso.py` instead

**Keep (still useful):**
- `adw_sdlc_iso.py` - Has lint phase, useful for non-ship workflows
- `adw_sdlc_zte_iso.py` - Mark as deprecated, redirect to complete version
- Individual phase workflows - Needed for manual intervention
- `adw_patch_iso.py` - Special purpose, keep
- `adw_lightweight_iso.py` - Cost-optimized, keep

#### 3.2 Archive Strategy

**Create Archive Directory:**
```
adws/archived/
  ├── partial-chains/
  │   ├── adw_plan_build_iso.py
  │   ├── adw_plan_build_test_iso.py
  │   ├── adw_plan_build_test_review_iso.py
  │   ├── adw_plan_build_review_iso.py
  │   └── adw_plan_build_document_iso.py
  └── README.md  # Explains why archived and what to use instead
```

**Migration Path:**
1. Add deprecation warnings to files (Phase 3.1)
2. Update all documentation to point to new workflows (Phase 2)
3. Wait 1 release cycle for user migration
4. Move to archive (Phase 3.2)

---

### Phase 4: Testing & Validation ✅

#### 4.1 Create Regression Test Plan

**Test Matrix:**

| Workflow | Test Case | Expected Outcome | Status |
|----------|-----------|------------------|--------|
| `adw_stepwise_iso.py` | Simple issue (atomic) | ATOMIC decision, no sub-issues | ⏳ |
| `adw_stepwise_iso.py` | Complex feature | DECOMPOSE decision, 2-4 sub-issues | ⏳ |
| `adw_sdlc_complete_iso.py` | Bug fix | All 8 phases pass | ⏳ |
| `adw_sdlc_complete_iso.py` | Feature | All 8 phases pass, ship succeeds | ⏳ |
| `adw_sdlc_complete_zte_iso.py` | Simple feature | Auto-merge to main | ⏳ |
| `adw_sdlc_complete_zte_iso.py` | Failing test | Abort before ship | ⏳ |

#### 4.2 Integration Tests

**Test Scenarios:**
1. Stepwise → Complete SDLC (use sub-issue from decomposition)
2. Complete SDLC with external tools (default)
3. Complete SDLC with inline execution (`--no-external`)
4. Complete ZTE with all flags
5. Error recovery at each phase

#### 4.3 Reference Validation

**Automated Checks:**
```bash
# Check for broken links in documentation
grep -r "adw_.*\.py" docs/ .claude/ | \
  while read line; do
    file=$(echo "$line" | grep -o "adw_[a-z_]*\.py")
    if [ ! -f "adws/$file" ]; then
      echo "Broken reference: $line"
    fi
  done
```

---

### Phase 5: Future Enhancements 🚀

#### 5.1 External Workflows for Review/Document

**Motivation:** Review and Document phases still use inline execution.

**Proposed:**
- `adw_review_external.py` + `adw_review_workflow.py`
  - Screenshot capture (deterministic)
  - Diff generation (deterministic)
  - Structured comparison (minimal AI call)

- `adw_document_external.py` + `adw_document_workflow.py`
  - Code extraction (deterministic)
  - Screenshot collection (deterministic)
  - Template filling (minimal AI call)

**Expected Savings:** 60-80% token reduction

#### 5.2 Parallel Phase Execution

**Motivation:** Some phases can run in parallel.

**Opportunities:**
- Build + Lint (independent)
- Test + Review (if review doesn't block on tests)

**Complexity:** High - requires state synchronization

#### 5.3 Smart Workflow Routing

**Motivation:** Auto-select workflow based on issue characteristics.

**Proposed:**
- Enhance complexity analyzer to recommend workflow
- Auto-route simple issues to `adw_lightweight_iso.py`
- Auto-route complex issues to `adw_sdlc_complete_iso.py`
- Auto-decompose very complex issues with stepwise

#### 5.4 Incremental Inverted Context

**Motivation:** Apply inverted context to more phases.

**Candidates:**
- Document phase - Plan documentation structure, execute deterministically
- Review phase - Plan review criteria, execute checks deterministically

---

## Implementation Timeline

### Week 1: Core Workflows
- ✅ Day 1-2: Create stepwise refinement workflow
- ✅ Day 3-4: Create complete SDLC workflow
- ✅ Day 5: Create complete ZTE workflow

### Week 2: Documentation & Testing
- ✅ Day 1-2: Update all documentation
- ✅ Day 3-4: Create and execute regression tests
- ✅ Day 5: Validate references and fix broken links

### Week 3: Cleanup & Migration
- ✅ Day 1-2: Add deprecation warnings
- ✅ Day 3-4: Create archive structure
- ✅ Day 5: Final validation and release

---

## Success Criteria

### Must Have (Phase 1-4)
- ✅ Stepwise refinement workflow creates sub-issues correctly
- ✅ Complete SDLC executes all 8 phases in order
- ✅ Complete ZTE includes lint phase
- ✅ All workflows use external optimization by default
- ✅ All documentation updated with no broken references
- ✅ Regression tests pass 100%

### Should Have (Phase 5)
- ✅ External review/document workflows
- ✅ Smart workflow routing
- ✅ Parallel execution prototype

### Nice to Have
- ✅ Incremental inverted context for more phases
- ✅ Auto-healing for common failures
- ✅ Workflow telemetry and analytics

---

## Risk Mitigation

### Risk: Breaking Existing Workflows
**Mitigation:**
- Keep all existing workflows functional
- Add new workflows alongside existing ones
- Deprecation warnings before removal
- Comprehensive regression testing

### Risk: State Management Conflicts
**Mitigation:**
- All new workflows use existing `ADWState` pattern
- State fields are additive, not breaking
- State validation at each phase
- Clear error messages for state issues

### Risk: Documentation Drift
**Mitigation:**
- Update all docs in single PR
- Automated reference checking
- Version documentation with implementation
- Regular doc audits

---

## Appendix A: File Structure

```
adws/
├── adw_stepwise_iso.py              # NEW - Issue breakdown analysis
├── adw_sdlc_complete_iso.py         # NEW - Complete SDLC (8 phases)
├── adw_sdlc_complete_zte_iso.py     # NEW - Complete ZTE (8 phases)
├── adw_plan_iso.py                  # KEEP - Standard planning
├── adw_plan_iso_optimized.py        # KEEP - Inverted context planning
├── adw_patch_iso.py                 # KEEP - Quick patches
├── adw_lightweight_iso.py           # KEEP - Cost-optimized
├── adw_build_iso.py                 # KEEP - Implementation
├── adw_lint_iso.py                  # KEEP - Linting
├── adw_test_iso.py                  # KEEP - Testing
├── adw_review_iso.py                # KEEP - Review
├── adw_document_iso.py              # KEEP - Documentation
├── adw_ship_iso.py                  # KEEP - Ship/merge
├── adw_cleanup_iso.py               # KEEP - Cleanup
├── adw_sdlc_iso.py                  # DEPRECATE → use complete version
├── adw_sdlc_zte_iso.py              # DEPRECATE → use complete version
├── archived/                        # NEW - Archive directory
│   ├── partial-chains/
│   │   ├── adw_plan_build_iso.py          # DEPRECATED
│   │   ├── adw_plan_build_test_iso.py     # DEPRECATED
│   │   └── ...
│   └── README.md
└── README.md                        # UPDATE

docs/planned_features/workflow-enhancements/  # NEW
├── IMPLEMENTATION_PLAN.md           # This file
├── stepwise-refinement-architecture.md
├── complete-sdlc-architecture.md
├── workflow-comparison.md
└── future-enhancements.md

.claude/commands/
├── stepwise_analysis.md             # NEW - Stepwise slash command
├── references/
│   └── adw_workflows.md             # UPDATE
└── quick_start/
    └── adw.md                       # UPDATE
```

---

## Appendix B: Dependencies

### Python Packages (existing)
- `python-dotenv`
- `pydantic`
- `pyyaml`

### External Tools (existing)
- GitHub CLI (`gh`)
- Claude Code CLI (`claude`)
- UV package manager
- Git

### No New Dependencies Required ✅

---

**Document Version:** 1.0
**Last Updated:** 2025-11-17
