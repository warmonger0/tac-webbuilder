# Session 19 Phase 2: State Management Clarity - Implementation Plan

## Overview

This plan breaks Session 19 Phase 2 into **4 sequential GitHub issues**, addressing the dual-state management problem where workflow state is tracked in BOTH file system (adw_state.json) and database (phase_queue table).

## Total Estimated Time: 27 hours

## Execution Strategy

- **Parallelization:** ❌ Must be sequential (each builds on previous)
- **Approach:** 4 separate GitHub issues, executed one at a time
- **Deliverable:** Each issue returns a summary to coordination chat for tracking

## The 4 Issues

### Issue #1: Document Phase Contracts (4 hours)

**File:** `.claude/prompts/session-19-phase-2-part-1-phase-contracts.md`

**Dependencies:** None (Foundation)
**Can start:** Immediately

**What it does:**
- Creates comprehensive phase input/output documentation
- Defines REQUIRES and PRODUCES for all 10 phases
- Visualizes dependency graph
- Adds contract docstrings to phase scripts

**Key deliverables:**
- `docs/adw/phase-contracts.md` (complete contracts)
- `docs/adw/phase-dependencies.md` (dependency graph)
- `docs/adw/phase-contracts-quick-ref.md` (quick reference)
- Updated docstrings in all 10 phase scripts

**Why it matters:**
Foundation for validation (Issue #3) and clear understanding of phase relationships.

---

### Issue #2: Define Single Source of Truth (6 hours)

**File:** `.claude/prompts/session-19-phase-2-part-2-single-source-of-truth.md`

**Dependencies:** Issue #1 (needs phase contracts)
**Can start:** After Issue #1 complete

**What it does:**
- Establishes clear boundaries: Database for coordination, Files for metadata
- Removes duplicate state tracking (status, current_phase)
- Documents when to use database vs files
- Provides decision tree for state updates

**Key deliverables:**
- `docs/adw/state-management-ssot.md` (SSoT architecture)
- `adws/adw_state_schema.json` (JSON schema)
- Cleaned `adw_state.json` files (removed duplicates)
- Updated all 10 phase scripts (SSoT compliance)

**Why it matters:**
Eliminates state divergence and race conditions by having one authoritative source for each piece of state.

---

### Issue #3: Add State Validation Middleware (5 hours)

**File:** `.claude/prompts/session-19-phase-2-part-3-state-validation.md`

**Dependencies:** Issues #1, #2 (needs contracts + SSoT)
**Can start:** After Issue #2 complete

**What it does:**
- Creates StateValidator class with phase-specific validation
- Validates inputs before execution (fail fast)
- Validates outputs after execution (ensure completeness)
- Unit tests for validation logic

**Key deliverables:**
- `adws/utils/state_validator.py` (validator class)
- `app/server/tests/utils/test_state_validator.py` (tests)
- `docs/adw/state-validation.md` (documentation)
- All 10 phase scripts integrated with validation

**Why it matters:**
Fail fast on invalid inputs, preventing wasted time and ensuring phases produce complete outputs.

---

### Issue #4: Implement Idempotent Phases (12 hours)

**File:** `.claude/prompts/session-19-phase-2-part-4-idempotent-phases.md`

**Dependencies:** Issues #1, #2, #3 (needs contracts + SSoT + validation)
**Can start:** After Issue #3 complete

**What it does:**
- Makes all 10 phases safely re-runnable
- Checks if already completed, skips if valid
- Validates file outputs, re-executes if corrupted
- Enables automatic crash recovery

**Key deliverables:**
- All 10 phase scripts (idempotent implementation)
- `adws/adw_sdlc_complete_iso.py` (retry logic)
- `app/server/tests/adws/test_idempotency.py` (tests)
- `docs/adw/idempotency.md` (documentation)

**Why it matters:**
Enables automatic crash recovery and safe retries - critical for reliability.

---

## How to Use These Prompts

### For Each Issue:

1. **Create GitHub Issue** with title from above
2. **Copy prompt file** content into new Claude Code chat
3. **Let agent execute** the complete task
4. **Collect summary** when agent completes
5. **Post summary** back to this coordination chat
6. **Move to next issue** in sequence

### Example Workflow:

```bash
# Issue #1
# 1. Create GitHub issue: "Document Phase Contracts"
# 2. Open new Claude Code chat
# 3. Paste content from: .claude/prompts/session-19-phase-2-part-1-phase-contracts.md
# 4. Let agent work
# 5. Agent returns summary when done
# 6. Post summary to coordination chat

# Issue #2
# Repeat same process with part-2 file
# And so on...
```

## Expected Summary Format

Each issue should return:

```
**Issue #N Complete: [Title]**

**Work Completed:**
- [Key deliverable 1]
- [Key deliverable 2]
- ...

**Time Spent:** [actual hours]

**Key Insights:**
- [Finding 1]
- [Finding 2]

**Ready for:** [Next issue title]
```

## Benefits of This Approach

✅ **Single Source of Truth** - No more state divergence
✅ **Fail Fast** - Clear errors before phase execution starts
✅ **Crash Recovery** - Automatic retry after failures
✅ **Deterministic** - Same input → same output
✅ **Clear Contracts** - Explicit dependencies documented

## Risk Management

- Each part delivers independent value
- Can pause/assess between parts
- Medium-High risk only on Part 4 (changes core logic)
- Parts 1-3 are low-medium risk

## Progress Tracking

- [ ] Issue #1: Document Phase Contracts (4h)
- [ ] Issue #2: Define Single Source of Truth (6h)
- [ ] Issue #3: Add State Validation Middleware (5h)
- [ ] Issue #4: Implement Idempotent Phases (12h)

**Total:** 0/27 hours complete

---

## Files Created

1. `.claude/prompts/session-19-phase-2-part-1-phase-contracts.md`
2. `.claude/prompts/session-19-phase-2-part-2-single-source-of-truth.md`
3. `.claude/prompts/session-19-phase-2-part-3-state-validation.md`
4. `.claude/prompts/session-19-phase-2-part-4-idempotent-phases.md`
5. `.claude/prompts/session-19-phase-2-SUMMARY.md` (this file)

All prompts are ready to copy into new chat contexts!
