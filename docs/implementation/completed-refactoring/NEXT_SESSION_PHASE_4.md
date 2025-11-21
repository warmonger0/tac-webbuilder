# Next Session: Start Phase 4 Refactoring

**Status:** Phase 3 ✅ COMPLETE | Phase 4 🟡 READY TO START
**Last Session:** Phase 3.3 completed (ProcessRunner utility)
**Next Action:** Begin Phase 4.1 - Extract foundation modules

---

## Quick Start Prompt for Next Session

Copy this prompt to Claude Code to continue:

```
Continue Phase 4 refactoring from where we left off.
Begin work following the ADW workflow: Plan → Build → Test → Review → Document → Ship → Cleanup

Current status:
- Phase 3 is 100% complete (ProcessRunner utility shipped)
- Phase 4 plan is ready: Split workflow_history.py (1,427 lines → 8 focused modules)
- Target: Reduce main file from 1,427 to ~50 lines

Start with Phase 4.1 (Foundation - Low Risk, 3-4 hours):
1. Create core/workflow_history/ directory
2. Extract models.py (type definitions, enums, constants)
3. Extract metrics.py (calculate_phase_metrics, categorize_error, estimate_complexity)
4. Extract github_client.py (fetch_github_issue_state)
5. Write unit tests for each module
6. Update imports in workflow_history.py

Read these files first:
- docs/refactoring/PHASE_4_WORKFLOW_HISTORY_SPLIT_PLAN.md (full plan)
- docs/refactoring/NEXT_SESSION_PHASE_4.md (this file)
- app/server/core/workflow_history.py (source to refactor)

Follow ADW workflow phases:
✅ Plan - Already done (see PHASE_4_WORKFLOW_HISTORY_SPLIT_PLAN.md)
⏳ Build - Create modules, move functions
⏳ Lint - Run syntax checks
⏳ Test - Write unit tests, run test suite
⏳ Review - Self-review changes
⏳ Document - Update completion log
⏳ Ship - Commit and push
⏳ Cleanup - Archive artifacts

Use TodoWrite to track progress through all workflow phases.
Leverage sub-agents for complex tasks (testing, review).
Be efficient with context and token use.
```

---

## What Was Completed Last Session

### Phase 3.3: ProcessRunner Utility ✅
- Created `utils/process_runner.py` (211 lines)
- Created comprehensive test suite (1,105 lines, 47 tests)
- Refactored 17 subprocess calls across 5 files
- Removed unused subprocess imports
- ~120 lines of duplication eliminated
- All tests passing (47/47)
- Committed: `6625604`
- Pushed to main branch

### Phase 3 Complete Summary ✅
- **Phase 3.1:** Database connection consolidation (~27 lines eliminated)
- **Phase 3.2:** LLMClient utility (~153 lines eliminated)
- **Phase 3.3:** ProcessRunner utility (~120 lines eliminated)
- **Total:** ~300 lines eliminated, +2,064 lines of quality code added
- **Documentation:** PHASE_3_COMPLETE_LOG.md created

---

## Phase 4 Overview

**Goal:** Split `core/workflow_history.py` (1,427 lines) into 8 focused modules

**Target Structure:**
```
workflow_history/
├── __init__.py (50 lines) ............... Public API facade
├── models.py (80 lines) ................. Type definitions
├── database.py (400 lines) .............. CRUD operations
├── filesystem.py (150 lines) ............ Agent directory scanning
├── github_client.py (50 lines) .......... GitHub API wrapper
├── metrics.py (120 lines) ............... Metric calculations
├── enrichment.py (200 lines) ............ Data enrichment
└── sync_manager.py (350 lines) .......... Sync orchestration
```

**Estimated Effort:** 27-36 hours (3.5-4.5 days)

---

## Phase 4.1: Foundation Modules (START HERE)

**Status:** 🟡 READY TO START
**Risk Level:** Low
**Estimated Time:** 3-4 hours

### What to Extract

#### 1. `models.py` (~80 lines)
**Extract from workflow_history.py:**
- Type definitions specific to workflow history
- Constants (if any)
- Enums for workflow status
- Dataclasses for filters/queries

**New code to add:**
```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class WorkflowStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class WorkflowFilter:
    issue_number: Optional[int] = None
    status: Optional[WorkflowStatus] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
```

---

#### 2. `metrics.py` (~120 lines)
**Extract these functions:**
- `calculate_phase_metrics()` (lines 59-127)
- `categorize_error()` (lines ~800-850)
- `estimate_complexity()` (lines ~850-870)

**Dependencies:**
- `core.data_models.CostData`
- `datetime`, `logging`

---

#### 3. `github_client.py` (~50 lines)
**Extract this function:**
- `fetch_github_issue_state()` (lines 35-56)

**Dependencies:**
- `utils.process_runner.ProcessRunner`
- `logging`

---

### Steps for Phase 4.1

1. **Create directory structure**
   ```bash
   cd /Users/Warmonger0/tac/tac-webbuilder/app/server
   mkdir -p core/workflow_history
   touch core/workflow_history/__init__.py
   ```

2. **Create models.py**
   - Define WorkflowStatus enum
   - Define WorkflowFilter dataclass
   - Add module docstring

3. **Create metrics.py**
   - Copy `calculate_phase_metrics()` from workflow_history.py
   - Copy `categorize_error()` from workflow_history.py
   - Copy `estimate_complexity()` from workflow_history.py
   - Update imports
   - Add module docstring

4. **Create github_client.py**
   - Copy `fetch_github_issue_state()` from workflow_history.py
   - Update imports
   - Add module docstring

5. **Write tests**
   ```bash
   mkdir -p tests/core/workflow_history
   touch tests/core/workflow_history/__init__.py
   touch tests/core/workflow_history/test_models.py
   touch tests/core/workflow_history/test_metrics.py
   touch tests/core/workflow_history/test_github_client.py
   ```

6. **Update workflow_history.py**
   - Remove extracted functions
   - Add imports from new modules
   - Verify imports work

7. **Run tests**
   ```bash
   uv run pytest tests/core/workflow_history/ -v
   uv run pytest tests/ -k workflow_history -v
   ```

8. **Commit Phase 4.1**
   ```bash
   git add core/workflow_history/ tests/core/workflow_history/
   git add core/workflow_history.py
   git commit -m "refactor: Phase 4.1 - Extract foundation modules (models, metrics, github_client)"
   ```

---

## Key Files to Read First

1. **Full Plan:** `docs/refactoring/PHASE_4_WORKFLOW_HISTORY_SPLIT_PLAN.md`
   - Complete architecture
   - All 6 phases detailed
   - Risk assessment

2. **Source File:** `app/server/core/workflow_history.py`
   - 1,427 lines to refactor
   - Read to understand structure

3. **Progress Tracker:** `docs/refactoring/REFACTORING_PROGRESS.md`
   - Current status: 65% overall progress
   - Phase 3 marked complete

---

## Important Reminders

### ADW Workflow Phases
1. ✅ **Plan** - Already done (see PHASE_4_WORKFLOW_HISTORY_SPLIT_PLAN.md)
2. ⏳ **Build** - Create modules, move functions (YOU ARE HERE)
3. ⏳ **Lint** - Run syntax checks
4. ⏳ **Test** - Write unit tests, run test suite
5. ⏳ **Review** - Self-review changes
6. ⏳ **Document** - Update completion log
7. ⏳ **Ship** - Commit and push
8. ⏳ **Cleanup** - Archive artifacts

### Use Sub-Agents
- **Plan agent:** For design decisions (if needed)
- **Test specialist:** For writing comprehensive tests
- **General-purpose:** For complex refactoring tasks
- **Review agent:** For self-review

### Track Progress
Use `TodoWrite` to track all 8 ADW workflow phases and sub-tasks.

### Be Efficient
- Use sub-agents for parallel work
- Read only what's needed
- Commit after each phase
- Test incrementally

---

## Success Criteria for Phase 4.1

✅ Three new modules created (models.py, metrics.py, github_client.py)
✅ Functions moved from workflow_history.py
✅ All imports updated and working
✅ Unit tests written for each module
✅ All existing tests still pass
✅ Zero regressions introduced
✅ Code committed to feature branch

---

## Estimated Timeline

| Phase | Time | Status |
|-------|------|--------|
| 4.1 Foundation | 3-4h | 🟡 START HERE |
| 4.2 Filesystem | 2-3h | ⏳ Next |
| 4.3 Database | 4-5h | ⏳ Pending |
| 4.4 Enrichment | 5-6h | ⏳ Pending |
| 4.5 Sync Manager | 6-8h | ⏳ Pending |
| 4.6 Public API | 2-3h | ⏳ Pending |
| **Total** | **27-36h** | **3.5-4.5 days** |

---

## Quick Commands

```bash
# Navigate to project
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Check current status
git status
wc -l core/workflow_history.py

# View recent commits
git log --oneline -5

# Create module directory
mkdir -p core/workflow_history

# Run baseline tests
uv run pytest tests/ -v --tb=short

# Run workflow_history tests
uv run pytest tests/ -k workflow_history -v

# Verify imports after refactor
uv run python3 -c "from core.workflow_history import metrics, models, github_client; print('✓ All imports work')"
```

---

## Context from Last Session

**Working Directory:** `/Users/Warmonger0/tac/tac-webbuilder/app/server`

**Recent Commits:**
- `6625604` - Phase 3.3 (ProcessRunner utility)
- `76d255c` - Phase 3.1 & 3.2 (Database & LLM utilities)
- `365ffab` - GitHubIssueService extraction

**Current Branch:** `main`

**Uncommitted Changes:**
- Some ADW module changes (not Phase 4 related)
- Client component changes (not Phase 4 related)
- Cost estimates updates (not Phase 4 related)

**Test Status:**
- 360+ tests passing
- Phase 3 tests: 47/47 passing
- Pre-existing failures in test_llm_processor.py (integration tests)

---

## Documentation to Update

After completing Phase 4.1:
1. Create `docs/refactoring/PHASE_4_PARTIAL_LOG.md`
2. Update `docs/refactoring/REFACTORING_PROGRESS.md`
3. Document any issues in ADW workflow log

After completing all of Phase 4:
1. Create `docs/refactoring/PHASE_4_COMPLETE_LOG.md`
2. Update cumulative metrics
3. Prepare for Phase 5 (workflow_analytics.py split)

---

**Ready to start Phase 4.1!**

Use the prompt at the top of this file to begin your next session.
