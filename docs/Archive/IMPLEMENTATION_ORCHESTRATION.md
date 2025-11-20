# Codebase Refactoring - Implementation Orchestration Guide

**Status:** Ready to Execute
**Created:** 2025-11-17
**Total Duration:** 15-20 days
**Total Workflows:** 67 atomic units

## Overview

This document provides the master orchestration plan for executing all 5 phases of the codebase refactoring. It serves as the central navigation point for understanding workflow dependencies, optimal execution order, and progress tracking.

---

## Quick Reference

| Phase | Workflows | Duration | Dependencies | Document |
|-------|-----------|----------|--------------|----------|
| **Phase 1** | 25 | 4-5 days | None | [PHASE_1_DETAILED.md](./phases/PHASE_1_DETAILED.md) |
| **Phase 2** | 12 | 2-3 days | None | [PHASE_2_DETAILED.md](./phases/PHASE_2_DETAILED.md) |
| **Phase 3** | 15 | 4-5 days | Phase 2 | [PHASE_3_DETAILED.md](./phases/PHASE_3_DETAILED.md) |
| **Phase 4** | 16 | 3-4 days | Phase 2 | [PHASE_4_DETAILED.md](./phases/PHASE_4_DETAILED.md) |
| **Phase 5** | 5 | 1-2 days | Phases 1, 3 | [PHASE_5_DETAILED.md](./phases/PHASE_5_DETAILED.md) |
| **Total** | **67** | **15-20 days** | - | - |

---

## Document Structure

### Core Documents
- **[REFACTORING_ANALYSIS.md](./REFACTORING_ANALYSIS.md)** - Comprehensive analysis of all code quality issues
- **[REFACTORING_PLAN.md](./REFACTORING_PLAN.md)** - High-level strategy and phase overview
- **This Document** - Orchestration, dependencies, and execution guidance

### Phase Detailed Plans
- **[phases/PHASE_1_DETAILED.md](./phases/PHASE_1_DETAILED.md)** - Extract Server Services (25 workflows)
- **[phases/PHASE_2_DETAILED.md](./phases/PHASE_2_DETAILED.md)** - Create Helper Utilities (12 workflows)
- **[phases/PHASE_3_DETAILED.md](./phases/PHASE_3_DETAILED.md)** - Split Large Core Modules (15 workflows)
- **[phases/PHASE_4_DETAILED.md](./phases/PHASE_4_DETAILED.md)** - Frontend Component Refactoring (16 workflows)
- **[phases/PHASE_5_DETAILED.md](./phases/PHASE_5_DETAILED.md)** - Fix Import Structure (5 workflows)

---

## Dependency Graph

```
LEGEND:
→ : Sequential dependency (must complete before)
|| : Can run in parallel

Phase 1: Extract Server Services (25 workflows)
├── 1.1: WebSocket Manager (3 workflows)
│   └── 1.1.1 → 1.1.2 → 1.1.3
│
├── 1.2: Workflow Service (4 workflows)
│   └── 1.2.1 → 1.2.2 → 1.2.3 → 1.2.4
│
├── 1.3: Background Tasks (4 workflows)
│   └── 1.3.1 → 1.3.2 → 1.3.3 → 1.3.4
│   └── Depends: 1.1.1, 1.2.1
│
├── 1.4: Health Service (6 workflows)
│   └── 1.4.1 → 1.4.2 → 1.4.5 → 1.4.6
│       └── 1.4.3 ↗
│       └── 1.4.4 ↗
│
├── 1.5: Service Controller (4 workflows)
│   └── 1.5.1 → 1.5.2 → 1.5.3 → 1.5.4
│
└── 1.6: Integration & Migration (4 workflows)
    └── All above → 1.6.1 → 1.6.2 → 1.6.3 → 1.6.4

Phase 2: Create Helper Utilities (12 workflows)
├── 2.1: DatabaseManager (4 workflows)
│   └── 2.1.1 → 2.1.2 → 2.1.3 → 2.1.4
│
├── 2.2: LLMClient (3 workflows)
│   └── 2.2.1 → 2.2.2 → 2.2.3
│
├── 2.3: ProcessRunner (3 workflows)
│   └── 2.3.1 → 2.3.2 → 2.3.3
│
└── 2.4: Frontend Formatters (2 workflows)
    └── 2.4.1 → 2.4.2

Phase 3: Split Large Core Modules (15 workflows)
├── Depends: Phase 2 (DatabaseManager)
│
├── 3A: workflow_history.py split (8 workflows)
│   └── 3A.1 → 3A.2 → 3A.3 → 3A.4 → 3A.5 → 3A.6 → 3A.7 → 3A.8
│
└── 3B: workflow_analytics.py split (7 workflows)
    └── 3B.1 → 3B.2 → 3B.3 → 3B.4 → 3B.5 → 3B.6 → 3B.7

Phase 4: Frontend Component Refactoring (16 workflows)
├── Depends: Phase 2.4 (Frontend Formatters)
│
├── 4.1: WorkflowHistoryCard split (12 workflows)
│   └── 4.1.1 → 4.1.2 → 4.1.3 → 4.1.4 → ... → 4.1.12
│
└── 4.2: WebSocket hooks (4 workflows)
    └── 4.2.1 → 4.2.2 → 4.2.3 → 4.2.4

Phase 5: Fix Import Structure (5 workflows)
├── Depends: Phases 1, 3
└── 5.1 → 5.2 → 5.3 → 5.4 → 5.5
```

---

## Optimal Execution Strategies

### Strategy 1: Sequential (1 Developer)

**Total Duration:** 18-23 days

```
Week 1:
  Day 1-2: Phase 1.1, 1.2 (WebSocket + Workflow Service)
  Day 3-4: Phase 1.3, 1.4 (Background Tasks + Health Service)
  Day 5:   Phase 1.5, 1.6 (Service Controller + Integration)

Week 2:
  Day 1-2: Phase 2 (All utilities in sequence)
  Day 3-5: Phase 3A (workflow_history split)

Week 3:
  Day 1-2: Phase 3B (workflow_analytics split)
  Day 3-5: Phase 4 (Frontend refactoring)

Week 4:
  Day 1-2: Phase 5 (Import structure)
  Day 3:   Final integration testing and documentation
```

### Strategy 2: Parallel (2 Developers)

**Total Duration:** 12-15 days

```
Week 1:
  Dev A: Phase 1 (4-5 days)
  Dev B: Phase 2 (2-3 days) → Phase 4.2 (WebSocket hooks, 2 days)

Week 2:
  Dev A: Phase 3A (workflow_history split, 4 days)
  Dev B: Phase 3B (workflow_analytics split, 3 days) → Phase 4.1 (start)

Week 3:
  Dev A: Phase 4.1 (continue WorkflowHistoryCard split)
  Dev B: Phase 4.1 (continue WorkflowHistoryCard split)

Week 3-4:
  Both: Phase 5 (Import structure, 1-2 days) + Final integration
```

### Strategy 3: Parallel (3 Developers)

**Total Duration:** 10-12 days

```
Week 1:
  Dev A: Phase 1.1, 1.2, 1.3 (WebSocket, Workflow, Background)
  Dev B: Phase 1.4, 1.5 (Health, Service Controller)
  Dev C: Phase 2 (All utilities)

Week 1.5-2:
  Dev A: Phase 1.6 (Integration) → Phase 3A (workflow_history)
  Dev B: Phase 4.2 (WebSocket hooks) → Phase 3B (workflow_analytics)
  Dev C: Phase 4.1 (WorkflowHistoryCard split)

Week 2:
  All Devs: Continue Phase 3 and Phase 4 in parallel

Week 2.5:
  All Devs: Phase 5 + Final integration testing
```

---

## Progress Tracking

### Overall Progress

- [ ] **Phase 1** - Extract Server Services (0/25 workflows)
- [ ] **Phase 2** - Create Helper Utilities (0/12 workflows)
- [ ] **Phase 3** - Split Large Core Modules (0/15 workflows)
- [ ] **Phase 4** - Frontend Component Refactoring (0/16 workflows)
- [ ] **Phase 5** - Fix Import Structure (0/5 workflows)

**Total Progress:** 0/67 workflows completed (0%)

### Current Metrics

| Metric | Baseline | Current | Target | Progress |
|--------|----------|---------|--------|----------|
| Largest file | 2,091 lines | 2,091 lines | <400 lines | 0% |
| Files >500 lines | 13 files | 13 files | 0 files | 0% |
| Functions >100 lines | 14 functions | 14 functions | 0 functions | 0% |
| Code duplication | ~500 lines | ~500 lines | ~50 lines | 0% |
| Test coverage | ~60% | ~60% | >80% | 0% |

---

## Execution Guidelines

### Before Starting Any Phase

1. **Read the detailed phase plan** (phases/PHASE_X_DETAILED.md)
2. **Check dependencies** - Ensure prerequisite phases/workflows are complete
3. **Create feature branch** - Use naming convention: `refactor/phaseX-description`
4. **Review current state** - Verify baseline files haven't changed significantly
5. **Set up tracking** - Create GitHub issues or project board items

### During Workflow Execution

1. **Work on ONE workflow at a time** - Each workflow is atomic
2. **Follow the tasks sequentially** - They're ordered for a reason
3. **Run verification commands** - After each major step
4. **Write tests BEFORE or ALONGSIDE code** - Test-driven refactoring
5. **Commit frequently** - After each logical sub-task
6. **Update progress tracking** - Check off completed workflows

### After Completing Each Workflow

1. **Run all verification commands** - Listed in workflow acceptance criteria
2. **Run full test suite** - Ensure no regressions
3. **Check acceptance criteria** - All items must be checked
4. **Commit with descriptive message** - Reference workflow number
5. **Update progress in this document** - Check off completed workflow
6. **Review code** - Self-review before moving to next workflow

### After Completing Each Phase

1. **Run integration tests** - Full test suite for the phase
2. **Run performance benchmarks** - Compare with baseline
3. **Update metrics table** - Document progress toward targets
4. **Merge feature branch** - To main via pull request
5. **Update documentation** - Phase completion notes
6. **Take a break** - Refactoring is mentally taxing!

---

## Git Workflow

### Branch Strategy

```bash
# Create phase branch from main
git checkout main
git pull origin main
git checkout -b refactor/phase1-server-services

# Work on individual workflows
git add <modified-files>
git commit -m "refactor(phase1): Complete workflow 1.1.1 - Create WebSocket Manager module

- Created app/server/services/websocket_manager.py
- Implemented ConnectionManager class
- Added logging and error handling
- All methods have type hints and docstrings

Workflow: PHASE_1_DETAILED.md#workflow-1.1
"

# Continue for each workflow...

# After phase completion
git push origin refactor/phase1-server-services

# Create pull request with phase summary
```

### Commit Message Convention

```
refactor(phaseX): <workflow-number> - <workflow-description>

- Task 1 completed
- Task 2 completed
- Task N completed

Workflow: PHASE_X_DETAILED.md#workflow-<number>
Tests: <test-command-output>
Verification: <verification-results>
```

### Rollback Strategy

If a workflow causes issues:

```bash
# Rollback to before workflow started
git log --oneline  # Find commit hash before workflow
git revert <commit-hash>

# Or reset if not pushed
git reset --hard <commit-hash>

# Document the issue
# Fix the issue
# Re-attempt the workflow
```

---

## Testing Strategy

### Test Levels

1. **Unit Tests** - Test individual functions/classes
   - Run after: Each workflow
   - Coverage target: >80% for new code
   - Tools: pytest (backend), vitest (frontend)

2. **Integration Tests** - Test module interactions
   - Run after: Each phase
   - Coverage target: All major workflows
   - Tools: pytest, React Testing Library

3. **End-to-End Tests** - Test complete user flows
   - Run after: Each phase, before merge
   - Coverage target: Critical paths
   - Tools: Manual testing, E2E framework

4. **Performance Tests** - Ensure no regressions
   - Run after: Each phase
   - Metrics: API response time, memory usage
   - Tools: pytest-benchmark, Chrome DevTools

### Test Execution Schedule

| When | What to Test | Command |
|------|-------------|---------|
| After each workflow | Unit tests for changed code | `pytest <specific-test-file>` |
| After each day | All unit tests | `pytest tests/` |
| After each phase | Integration tests | `pytest tests/integration/` |
| Before merge | Full test suite | `pytest` |
| Before merge | Frontend tests | `npm run test` |
| Before merge | E2E tests | Manual or automated E2E |

---

## Quality Gates

### Workflow Completion Criteria

A workflow is considered complete when:

- [ ] All tasks in the workflow are finished
- [ ] All acceptance criteria are checked off
- [ ] All verification commands pass
- [ ] Unit tests written and passing (>80% coverage)
- [ ] Code reviewed (self-review minimum)
- [ ] Committed with descriptive message
- [ ] No regressions in existing tests
- [ ] Documentation updated if needed

### Phase Completion Criteria

A phase is considered complete when:

- [ ] All workflows in the phase are complete
- [ ] Integration tests passing
- [ ] Performance benchmarks acceptable (no >10% regression)
- [ ] Metrics updated in this document
- [ ] Phase-specific documentation complete
- [ ] Pull request created and reviewed
- [ ] Merged to main branch

### Overall Completion Criteria

The refactoring is complete when:

- [ ] All 5 phases complete (67/67 workflows)
- [ ] All target metrics achieved:
  - [ ] Largest file <400 lines
  - [ ] Zero files >500 lines
  - [ ] Zero functions >100 lines
  - [ ] Code duplication <100 lines (80% reduction)
  - [ ] Test coverage >80%
- [ ] No performance regressions
- [ ] All documentation updated
- [ ] Team trained on new architecture
- [ ] Lessons learned documented

---

## Risk Management

### High-Risk Workflows

The following workflows have higher risk and require extra caution:

| Workflow | Risk | Mitigation |
|----------|------|------------|
| 1.6.2 | Medium | Extensive testing of server.py after code removal |
| 3A.8 | Medium | Comprehensive integration tests for workflow_history |
| 3B.7 | Medium | Validate all scoring algorithms unchanged |
| 4.1.11 | Medium | Visual regression testing for UI changes |
| 5.5 | Medium | Validate no circular dependencies introduced |

### Rollback Procedures

If a phase causes critical issues:

1. **Immediate Actions:**
   - Stop all development on the phase
   - Document the issue in detail
   - Assess impact on production/staging

2. **Rollback Decision:**
   - Minor issues: Fix forward
   - Major issues: Rollback the phase

3. **Rollback Execution:**
   ```bash
   # Revert the merge commit
   git revert -m 1 <merge-commit-hash>
   git push origin main

   # Or reset if not deployed
   git reset --hard <commit-before-merge>
   git push --force origin main  # ONLY if not deployed!
   ```

4. **Post-Rollback:**
   - Analyze root cause
   - Update phase plan to prevent recurrence
   - Re-execute phase with fixes

---

## Communication Plan

### Daily Updates (if team >1 developer)

**Format:** Quick standup or Slack update

- What workflow(s) completed yesterday
- What workflow working on today
- Any blockers or issues

### Weekly Updates

**Format:** Written summary

- Workflows completed this week
- Current phase progress
- Updated metrics
- Issues encountered and resolved
- Plan for next week

### Phase Completion Report

**Format:** Detailed document

- Phase summary
- All workflows completed
- Metrics achieved
- Lessons learned
- Recommendations for next phase

---

## Troubleshooting Guide

### Common Issues

#### Issue: Tests failing after migration

**Solution:**
1. Check imports - ensure all modules can be found
2. Check for missing fixtures or test data
3. Check for changed function signatures
4. Run tests in isolation to identify specific failures

#### Issue: Import errors after refactoring

**Solution:**
1. Check `__init__.py` files exist in all packages
2. Check import paths are correct
3. Check for circular dependencies
4. Use absolute imports instead of relative

#### Issue: Performance degradation

**Solution:**
1. Run benchmarks to identify bottleneck
2. Profile the slow code path
3. Check for N+1 query problems
4. Check for missing caching
5. Consider reverting and redesigning

#### Issue: Merge conflicts

**Solution:**
1. Keep feature branches short-lived
2. Merge main into feature branch frequently
3. Coordinate with other developers
4. Use smaller, more focused workflows

---

## Success Metrics Dashboard

### Code Quality Metrics

Track these metrics after each phase:

```bash
# File size distribution
find app/server -name "*.py" -type f -exec wc -l {} + | sort -rn | head -20

# Function size analysis
# (Use custom script or tool)

# Code duplication
# (Use SonarQube or similar)

# Test coverage
pytest --cov=app.server --cov-report=term-missing
cd app/client && npm run test:coverage
```

### Performance Metrics

Baseline and track after each phase:

```bash
# API response times
ab -n 1000 -c 10 http://localhost:8000/api/workflows

# Memory usage
ps aux | grep "python.*server.py"

# WebSocket latency
# (Custom WebSocket client test)
```

---

## Reference Quick Links

### Documentation
- [Main README](../../../README.md) - Project overview
- [Architecture Docs](../../architecture/) - System architecture
- [Testing Docs](../../testing/) - Testing strategy

### Phase Details
- [Phase 1: Server Services](./phases/PHASE_1_DETAILED.md) - 25 workflows
- [Phase 2: Helper Utilities](./phases/PHASE_2_DETAILED.md) - 12 workflows
- [Phase 3: Core Modules](./phases/PHASE_3_DETAILED.md) - 15 workflows
- [Phase 4: Frontend](./phases/PHASE_4_DETAILED.md) - 16 workflows
- [Phase 5: Import Structure](./phases/PHASE_5_DETAILED.md) - 5 workflows

### Tools
- [pytest](https://docs.pytest.org/) - Python testing
- [vitest](https://vitest.dev/) - Frontend testing
- [React Testing Library](https://testing-library.com/react) - React testing
- [pytest-cov](https://pytest-cov.readthedocs.io/) - Coverage reporting

---

## Getting Started

### For First-Time Execution

1. **Read the analysis:**
   - Review [REFACTORING_ANALYSIS.md](./REFACTORING_ANALYSIS.md)
   - Understand the problems being solved

2. **Read the strategy:**
   - Review [REFACTORING_PLAN.md](./REFACTORING_PLAN.md)
   - Understand the overall approach

3. **Choose an execution strategy:**
   - Sequential (1 dev) vs Parallel (2-3 devs)
   - Select based on team size and availability

4. **Start with Phase 1:**
   - Read [PHASE_1_DETAILED.md](./phases/PHASE_1_DETAILED.md)
   - Create feature branch
   - Execute workflow 1.1.1

5. **Track progress:**
   - Update this document after each workflow
   - Update metrics after each phase
   - Document lessons learned

### For Resuming Execution

1. **Check progress:**
   - Review "Progress Tracking" section above
   - Identify next workflow to execute

2. **Verify state:**
   - Ensure previous workflows still passing
   - Check for any changes to baseline code

3. **Continue execution:**
   - Follow the detailed plan for next workflow
   - Update tracking as you go

---

## Appendix

### Workflow ID Reference

Quick reference for workflow naming:

- **1.X.Y** - Phase 1, Component X, Workflow Y
- **2.X.Y** - Phase 2, Component X, Workflow Y
- **3A.Y** - Phase 3, Part A (workflow_history), Workflow Y
- **3B.Y** - Phase 3, Part B (workflow_analytics), Workflow Y
- **4.X.Y** - Phase 4, Component X, Workflow Y
- **5.Y** - Phase 5, Workflow Y

### Estimated Effort by Developer Skill Level

| Developer Level | Time Multiplier | Total Duration |
|-----------------|-----------------|----------------|
| Senior (familiar with codebase) | 1.0x | 15-20 days |
| Mid-level (some familiarity) | 1.3x | 20-26 days |
| Junior (learning codebase) | 1.8x | 27-36 days |

### Contact and Support

For questions or issues during execution:
- Review the detailed phase plan first
- Check troubleshooting guide
- Consult with tech lead
- Document the issue for future reference

---

**Document Status:** Complete and Ready for Execution
**Last Updated:** 2025-11-17
**Maintained By:** Development Team
**Next Review:** After Phase 1 completion

---

## Document History

| Date | Change | Author |
|------|--------|--------|
| 2025-11-17 | Initial creation | Claude Code |
| - | - | - |
