# Refactoring Phase Implementation Plans

This directory contains detailed, atomic workflow-level implementation plans for all 5 phases of the codebase refactoring.

## Quick Navigation

| Phase | File | Workflows | Duration | Status |
|-------|------|-----------|----------|--------|
| **Phase 1** | [PHASE_1_DETAILED.md](./PHASE_1_DETAILED.md) | 25 | 4-5 days | Not Started |
| **Phase 2** | [PHASE_2_DETAILED.md](./PHASE_2_DETAILED.md) | 12 | 2-3 days | Not Started |
| **Phase 3** | [PHASE_3_DETAILED.md](./PHASE_3_DETAILED.md) | 15 | 4-5 days | Not Started |
| **Phase 4** | [PHASE_4_DETAILED.md](./PHASE_4_DETAILED.md) | 16 | 3-4 days | Not Started |
| **Phase 5** | [PHASE_5_DETAILED.md](./PHASE_5_DETAILED.md) | 5 | 1-2 days | Not Started |

**Total:** 67 atomic workflows, 15-20 days

## Document Structure

Each phase detailed plan follows the same proven structure:

### 1. Overview
- Phase goals and success criteria
- Duration and priority
- Risk assessment

### 2. Hierarchical Decomposition
- Level 1: Major components
- Level 2: Atomic workflow units (1-3 hours each)

### 3. Detailed Workflows
Each workflow includes:
- **Estimated time** - Realistic time estimate
- **Complexity** - Low/Medium/High
- **Dependencies** - Prerequisites
- **Input/Output files** - Exact file paths
- **Tasks** - 6-10 specific steps
- **Code examples** - Before/after code
- **Acceptance criteria** - Checkboxes
- **Verification commands** - Actual bash commands

### 4. Summary Statistics
- Total workflows and time
- Dependency graph
- Optimal execution order
- Parallelization opportunities

## Phase Summaries

### Phase 1: Extract Server Services
**Goal:** Split `server.py` (2,091 lines) into focused service modules

**Components:**
1. WebSocket Manager (3 workflows)
2. Workflow Service (4 workflows)
3. Background Tasks (4 workflows)
4. Health Service (6 workflows)
5. Service Controller (4 workflows)
6. Integration & Migration (4 workflows)

**Target:** Reduce server.py to <300 lines

### Phase 2: Create Helper Utilities
**Goal:** Eliminate ~30% code duplication by creating reusable utilities

**Components:**
1. DatabaseManager (4 workflows) - ~60 lines saved
2. LLMClient (3 workflows) - ~90 lines saved
3. ProcessRunner (3 workflows) - ~120 lines saved
4. Frontend Formatters (2 workflows) - ~50 lines saved

**Target:** Reduce duplication from ~500 to ~50 lines

### Phase 3: Split Large Core Modules
**Goal:** Split two largest core modules into focused packages

**Part A - workflow_history.py (8 workflows):**
- 1,311 lines → 8 modules of 150-220 lines each
- Modules: database, scanner, enrichment, analytics, similarity, resync, sync

**Part B - workflow_analytics.py (7 workflows):**
- 904 lines → 9 modules of 80-180 lines each
- Modules: base scorer, 4 scorers, similarity, anomalies, recommendations

**Target:** All modules <400 lines

### Phase 4: Frontend Component Refactoring
**Goal:** Modularize oversized React components

**Part A - WorkflowHistoryCard (12 workflows):**
- 793 lines → 9 section components of 30-102 lines each
- Main component reduced to <200 lines

**Part B - WebSocket Hooks (4 workflows):**
- 3 duplicate hooks (275 lines) → 1 generic hook + 3 wrappers (~80 lines total)
- 71% reduction in code

**Target:** WorkflowHistoryCard <200 lines, 70% hook reduction

### Phase 5: Fix Import Structure
**Goal:** Eliminate path manipulation, establish proper dependency hierarchy

**Components:**
1. Create shared package (1 workflow)
2. Move shared types (1 workflow)
3. Update server imports (1 workflow)
4. Update ADW imports (1 workflow)
5. Validation and cleanup (1 workflow)

**Target:** Zero path manipulation, clean dependency hierarchy

## Execution Guidelines

### Before Starting
1. Read [REFACTORING_ANALYSIS.md](../REFACTORING_ANALYSIS.md) - Understand the problems
2. Read [REFACTORING_PLAN.md](../REFACTORING_PLAN.md) - Understand the strategy
3. Read [IMPLEMENTATION_ORCHESTRATION.md](../IMPLEMENTATION_ORCHESTRATION.md) - Understand execution
4. Review phase dependencies in orchestration doc

### During Execution
1. **Work on ONE workflow at a time**
2. **Follow tasks sequentially** within each workflow
3. **Run verification commands** after each major step
4. **Write tests before or alongside code**
5. **Commit after each workflow**
6. **Update progress tracking**

### Workflow Format
Each workflow is structured to be:
- **Atomic** - Completable in one sitting (1-3 hours)
- **Self-contained** - All information needed is in the workflow
- **Verifiable** - Clear acceptance criteria and tests
- **Reversible** - Can be rolled back if needed

## Dependencies Between Phases

```
Phase 1: Server Services
  ├─ No dependencies (can start immediately)
  └─ Required by: Phase 5

Phase 2: Helper Utilities
  ├─ No dependencies (can start immediately)
  ├─ Required by: Phase 3, Phase 4
  └─ Can run in parallel with Phase 1

Phase 3: Core Modules
  ├─ Depends on: Phase 2 (DatabaseManager)
  └─ Required by: Phase 5

Phase 4: Frontend
  ├─ Depends on: Phase 2 (Frontend Formatters)
  └─ Can run in parallel with Phase 3

Phase 5: Import Structure
  ├─ Depends on: Phases 1, 3
  └─ Final cleanup phase
```

## Optimal Execution Order

### With 1 Developer (Sequential)
```
Week 1: Phase 1
Week 2: Phase 2 + start Phase 3
Week 3: Complete Phase 3 + Phase 4
Week 4: Complete Phase 4 + Phase 5
```

### With 2 Developers (Parallel)
```
Week 1:
  Dev A: Phase 1
  Dev B: Phase 2 + WebSocket hooks

Week 2:
  Dev A: Phase 3A (workflow_history)
  Dev B: Phase 3B (workflow_analytics) + start Phase 4

Week 3:
  Both: Phase 4 + Phase 5
```

### With 3 Developers (Maximum Parallelization)
```
Week 1:
  Dev A: Phase 1 (server services)
  Dev B: Phase 1 (server services)
  Dev C: Phase 2 (utilities)

Week 2:
  Dev A: Phase 3A (workflow_history)
  Dev B: Phase 3B (workflow_analytics)
  Dev C: Phase 4 (frontend)

Week 2.5:
  All: Phase 5 + integration testing
```

## Progress Tracking

Update this table as you complete workflows:

### Phase 1: Extract Server Services
- [ ] 1.1: WebSocket Manager (0/3 workflows)
- [ ] 1.2: Workflow Service (0/4 workflows)
- [ ] 1.3: Background Tasks (0/4 workflows)
- [ ] 1.4: Health Service (0/6 workflows)
- [ ] 1.5: Service Controller (0/4 workflows)
- [ ] 1.6: Integration & Migration (0/4 workflows)

**Phase 1 Progress:** 0/25 workflows (0%)

### Phase 2: Create Helper Utilities
- [ ] 2.1: DatabaseManager (0/4 workflows)
- [ ] 2.2: LLMClient (0/3 workflows)
- [ ] 2.3: ProcessRunner (0/3 workflows)
- [ ] 2.4: Frontend Formatters (0/2 workflows)

**Phase 2 Progress:** 0/12 workflows (0%)

### Phase 3: Split Large Core Modules
- [ ] 3A: workflow_history.py (0/8 workflows)
- [ ] 3B: workflow_analytics.py (0/7 workflows)

**Phase 3 Progress:** 0/15 workflows (0%)

### Phase 4: Frontend Component Refactoring
- [ ] 4.1: WorkflowHistoryCard (0/12 workflows)
- [ ] 4.2: WebSocket Hooks (0/4 workflows)

**Phase 4 Progress:** 0/16 workflows (0%)

### Phase 5: Fix Import Structure
- [ ] 5.1-5.5: All workflows (0/5 workflows)

**Phase 5 Progress:** 0/5 workflows (0%)

---

**Overall Progress:** 0/67 workflows completed (0%)

## How to Use These Plans

### For Implementation
1. **Start with the phase document** that matches your current work
2. **Read the workflow description** for context
3. **Execute tasks sequentially** - they're ordered for success
4. **Run verification commands** - verify each step works
5. **Check acceptance criteria** - all must pass
6. **Commit and move to next workflow**

### For Review
1. **Check the workflow description** to understand intent
2. **Review code against tasks** - ensure all completed
3. **Run verification commands** - tests must pass
4. **Check acceptance criteria** - all should be checked
5. **Approve or request changes**

### For Estimation
1. **Count workflows** in the phase
2. **Sum estimated times** (conservative)
3. **Add 20% buffer** for unexpected issues
4. **Consider parallelization** if multiple developers

## Tips for Success

### Do
✅ Read the entire workflow before starting
✅ Run tests frequently (after each task)
✅ Commit after completing each workflow
✅ Update progress tracking regularly
✅ Ask questions when unclear
✅ Take breaks between phases

### Don't
❌ Skip verification commands
❌ Work on multiple workflows simultaneously
❌ Batch commits across multiple workflows
❌ Skip writing tests
❌ Ignore failing acceptance criteria
❌ Rush through workflows

## Getting Help

### Troubleshooting
1. Check the **Troubleshooting** section in [IMPLEMENTATION_ORCHESTRATION.md](../IMPLEMENTATION_ORCHESTRATION.md)
2. Review the **Common Issues** guide
3. Check workflow **Acceptance Criteria** - what's failing?
4. Consult the original **REFACTORING_ANALYSIS.md** for context

### Questions
1. Re-read the workflow description
2. Check related workflows for context
3. Review the phase overview
4. Ask the team or tech lead

## Document Maintenance

### After Completing a Workflow
- Update progress checkboxes above
- Note any deviations from the plan
- Document lessons learned

### After Completing a Phase
- Update status in the table above
- Create phase completion report
- Update [IMPLEMENTATION_ORCHESTRATION.md](../IMPLEMENTATION_ORCHESTRATION.md)

---

**Last Updated:** 2025-11-17
**Status:** Ready for execution
**Total Estimated Effort:** 95-130 hours (15-20 days)
