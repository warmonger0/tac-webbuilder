# ADW Workflow Failure Scenarios - Comprehensive Test Plan

**Date**: 2025-11-21
**Context**: Post-Issue #66 implementation - testing all workflows for failure resilience
**Related**: `docs/ISSUE_66_COMPREHENSIVE_IMPLEMENTATION_PLAN.md`

---

## Executive Summary

This document identifies potential failure scenarios for ALL ADW workflows and provides a systematic testing strategy. The goal is to prevent the types of failures encountered in Issue #66 and Issue #64 from recurring across any workflow type.

---

## Workflow Inventory

### Recommended Production Workflows
1. **`adw_sdlc_complete_iso.py`** - Complete SDLC (9 phases with Validate)
2. **`adw_sdlc_complete_zte_iso.py`** - Complete ZTE with auto-merge (9 phases)
3. **`adw_lightweight_iso.py`** - Cost-optimized for simple changes
4. **`adw_patch_iso.py`** - Targeted fixes (requires "adw_patch" keyword)
5. **`adw_stepwise_iso.py`** - Issue decomposition analyzer

### Deprecated Workflows (Still in Use)
6. **`adw_sdlc_iso.py`** ⚠️ Missing lint, validate, ship phases
7. **`adw_sdlc_zte_iso.py`** ⚠️ Missing lint, validate phases

### Partial Workflows
8. **`adw_plan_build_iso.py`** - Plan + Build only
9. **`adw_plan_build_test_iso.py`** - Plan + Build + Test
10. **`adw_plan_build_test_review_iso.py`** - Plan + Build + Test + Review
11. **`adw_plan_build_review_iso.py`** - Plan + Build + Review (skip tests)
12. **`adw_plan_build_document_iso.py`** - Plan + Build + Document

---

## Failure Scenario Categories

### Category 1: Code Quality Issues

#### FS-1.1: Inherited Errors from Main Branch
**Scenario**: Main branch has TypeScript/lint errors, worktree inherits them
**Affected Workflows**: ALL workflows with Build phase
**Issue #66 Status**: ✅ FIXED with Validate phase
**Expected Behavior**:
- Validate phase detects baseline errors
- Build phase uses differential detection
- Only NEW errors cause failure

**Test Cases**:
```bash
# TC-1.1.1: Clean main → Clean worktree (should pass)
# TC-1.1.2: Dirty main → Dirty worktree, no new errors (should pass)
# TC-1.1.3: Dirty main → Dirty worktree, new errors (should fail)
# TC-1.1.4: Dirty main → Cleaner worktree (should pass + celebrate)
```

**Testing Priority**: 🔴 CRITICAL

#### FS-1.2: New TypeScript Errors Introduced
**Scenario**: Implementation introduces new TypeScript compilation errors
**Affected Workflows**: ALL workflows with Build phase
**Expected Behavior**:
- Build phase catches errors
- Differential detection identifies them as NEW
- Build phase fails with clear message
- Lists specific errors with file:line:column

**Test Cases**:
```bash
# TC-1.2.1: Single new error in modified file
# TC-1.2.2: Multiple errors across files
# TC-1.2.3: Import/export type errors
# TC-1.2.4: Type guard failures
```

**Testing Priority**: 🔴 CRITICAL

#### FS-1.3: Lint Rule Violations
**Scenario**: Code violates ESLint/Ruff rules
**Affected Workflows**: Complete workflows with Lint phase
**Expected Behavior**:
- Lint phase catches violations
- Provides actionable fix suggestions
- Auto-fix attempts (if enabled)

**Test Cases**:
```bash
# TC-1.3.1: Frontend ESLint violations
# TC-1.3.2: Backend Ruff violations
# TC-1.3.3: Mixed frontend + backend violations
```

**Testing Priority**: 🟡 HIGH

#### FS-1.4: Test Failures
**Scenario**: Unit/integration/E2E tests fail
**Affected Workflows**: ALL workflows with Test phase
**Expected Behavior**:
- Test phase detects failures
- Auto-resolution attempts (if enabled)
- Detailed failure logs provided

**Test Cases**:
```bash
# TC-1.4.1: Frontend unit test failure
# TC-1.4.2: Backend pytest failure
# TC-1.4.3: Integration test failure
# TC-1.4.4: E2E test failure (if not skipped)
```

**Testing Priority**: 🔴 CRITICAL

---

### Category 2: Environment & Infrastructure

#### FS-2.1: Port Conflicts
**Scenario**: Multiple ADWs allocated same ports, or ports already in use
**Affected Workflows**: ALL workflows creating worktrees
**Expected Behavior**:
- Port allocation algorithm provides deterministic ports
- Fallback to next available ports if occupied
- .ports.env correctly configured

**Test Cases**:
```bash
# TC-2.1.1: Sequential ADWs (different ports)
# TC-2.1.2: Concurrent ADWs (deterministic allocation)
# TC-2.1.3: Port already occupied by external process
# TC-2.1.4: All 15 ports occupied (edge case)
```

**Testing Priority**: 🟡 HIGH

#### FS-2.2: Worktree Creation Failures
**Scenario**: Git worktree creation fails or becomes corrupted
**Affected Workflows**: ALL workflows creating worktrees
**Expected Behavior**:
- Clear error message if worktree creation fails
- Automatic cleanup of partial worktrees
- Graceful degradation

**Test Cases**:
```bash
# TC-2.2.1: Insufficient disk space
# TC-2.2.2: trees/ directory doesn't exist
# TC-2.2.3: Permission denied on trees/
# TC-2.2.4: Worktree path already exists
# TC-2.2.5: Git repository corrupted
```

**Testing Priority**: 🟡 HIGH

#### FS-2.3: Missing Environment Variables
**Scenario**: Required .env variables not configured
**Affected Workflows**: ALL workflows
**Expected Behavior**:
- Early validation checks for required vars
- Clear error messages indicating which vars missing
- Workflow exits gracefully

**Test Cases**:
```bash
# TC-2.3.1: Missing ANTHROPIC_API_KEY
# TC-2.3.2: Missing GITHUB_TOKEN
# TC-2.3.3: Missing OPENAI_API_KEY
# TC-2.3.4: .env file completely missing
```

**Testing Priority**: 🔴 CRITICAL

#### FS-2.4: Database Connectivity
**Scenario**: SQLite database locked or corrupted
**Affected Workflows**: Workflows that write to database (Ship, Document)
**Expected Behavior**:
- Retry logic for locked database
- Error recovery for corrupted database
- Clear error messages

**Test Cases**:
```bash
# TC-2.4.1: Database locked by another process
# TC-2.4.2: Database file corrupted
# TC-2.4.3: Database schema mismatch
# TC-2.4.4: Database file permissions issue
```

**Testing Priority**: 🟠 MEDIUM

---

### Category 3: GitHub Integration

#### FS-3.1: GitHub API Rate Limiting
**Scenario**: GitHub API quota exceeded
**Affected Workflows**: ALL workflows
**Expected Behavior** (Post Issue #66):
- Pre-flight quota check in Validate phase
- Graceful degradation when quota low
- Clear error message with quota status

**Test Cases**:
```bash
# TC-3.1.1: Quota exhausted before workflow starts
# TC-3.1.2: Quota exhausted mid-workflow
# TC-3.1.3: Quota recovered after wait
```

**Testing Priority**: 🔴 CRITICAL

#### FS-3.2: Issue Not Found
**Scenario**: GitHub issue doesn't exist or is inaccessible
**Affected Workflows**: ALL workflows
**Expected Behavior**:
- Early validation of issue existence
- Clear error message
- Workflow exits gracefully

**Test Cases**:
```bash
# TC-3.2.1: Issue number doesn't exist
# TC-3.2.2: Issue exists but no permissions
# TC-3.2.3: Issue in wrong repository
```

**Testing Priority**: 🟡 HIGH

#### FS-3.3: PR Creation Failure
**Scenario**: Pull request creation fails
**Affected Workflows**: Workflows with Ship phase
**Expected Behavior**:
- Retry logic for transient failures
- Detailed error message
- Preserve work (don't lose commits)

**Test Cases**:
```bash
# TC-3.3.1: Branch already has open PR
# TC-3.3.2: Base branch doesn't exist
# TC-3.3.3: Network timeout during creation
# TC-3.3.4: GitHub API returns 500 error
```

**Testing Priority**: 🟡 HIGH

#### FS-3.4: Comment Posting Failure
**Scenario**: GitHub comment posting fails
**Affected Workflows**: ALL workflows (status updates)
**Expected Behavior**:
- Non-fatal error (workflow continues)
- Logged for debugging
- Retry with backoff

**Test Cases**:
```bash
# TC-3.4.1: Network timeout
# TC-3.4.2: Comment too large (>65536 chars)
# TC-3.4.3: GitHub API error
```

**Testing Priority**: 🟠 MEDIUM

#### FS-3.5: Phantom Merge (Issue #64)
**Scenario**: GitHub API reports merge success, but merge didn't happen
**Affected Workflows**: Workflows with Ship phase
**Issue #64 Status**: ✅ FIXED with post-merge verification
**Expected Behavior**:
- Ship phase verifies merge actually happened
- Checks commit is on target branch
- Verifies files exist on target branch
- Runs post-merge smoke tests

**Test Cases**:
```bash
# TC-3.5.1: API says merged, but commit not on main
# TC-3.5.2: API says merged, but files missing
# TC-3.5.3: API says merged, smoke tests fail
```

**Testing Priority**: 🔴 CRITICAL

---

### Category 4: State Management

#### FS-4.1: ADW State Corruption
**Scenario**: adw_state.json is corrupted or malformed
**Affected Workflows**: All dependent workflows (Build, Test, Review, etc.)
**Expected Behavior**:
- State validation on load
- Clear error message indicating corruption
- Recovery suggestions

**Test Cases**:
```bash
# TC-4.1.1: Invalid JSON syntax
# TC-4.1.2: Missing required fields
# TC-4.1.3: Type mismatches in fields
# TC-4.1.4: Empty state file
```

**Testing Priority**: 🟡 HIGH

#### FS-4.2: Phase Mismatch
**Scenario**: Running wrong phase for current workflow state
**Affected Workflows**: All dependent workflows
**Expected Behavior**:
- Phase validation checks prerequisites
- Clear error message indicating required phase
- Workflow exits gracefully

**Test Cases**:
```bash
# TC-4.2.1: Build before Plan
# TC-4.2.2: Test before Build
# TC-4.2.3: Ship before Review
```

**Testing Priority**: 🟠 MEDIUM

#### FS-4.3: Concurrent State Modifications
**Scenario**: Multiple processes modifying same ADW state (Issue #8)
**Affected Workflows**: ALL workflows in concurrent scenarios
**Issue #8 Status**: ✅ FIXED with adw_locks table
**Expected Behavior**:
- Mutex-style locking prevents concurrent access
- Clear error message if lock held
- Lock released on completion or failure

**Test Cases**:
```bash
# TC-4.3.1: Two workflows on same issue
# TC-4.3.2: Lock timeout scenario
# TC-4.3.3: Lock holder crashes (orphaned lock)
```

**Testing Priority**: 🔴 CRITICAL

---

### Category 5: Workflow-Specific Issues

#### FS-5.1: Lightweight Workflow Misrouted
**Scenario**: Complex issue routed to lightweight workflow
**Affected Workflows**: `adw_lightweight_iso.py`
**Expected Behavior**:
- Complexity analyzer catches mismatch
- Recommends appropriate workflow
- Fails early with clear message

**Test Cases**:
```bash
# TC-5.1.1: Multi-file change routed to lightweight
# TC-5.1.2: Database change routed to lightweight
# TC-5.1.3: Full-stack change routed to lightweight
```

**Testing Priority**: 🟠 MEDIUM

#### FS-5.2: Patch Workflow Missing Keyword
**Scenario**: `adw_patch_iso.py` called without "adw_patch" keyword
**Affected Workflows**: `adw_patch_iso.py`
**Expected Behavior**:
- Early validation for keyword presence
- Clear error message
- Workflow exits gracefully

**Test Cases**:
```bash
# TC-5.2.1: No comments with keyword
# TC-5.2.2: Issue body doesn't contain keyword
# TC-5.2.3: Keyword in wrong format
```

**Testing Priority**: 🟠 MEDIUM

#### FS-5.3: Stepwise Decomposition Failure
**Scenario**: `adw_stepwise_iso.py` can't determine if ATOMIC or DECOMPOSE
**Affected Workflows**: `adw_stepwise_iso.py`
**Expected Behavior**:
- Fallback to conservative estimate (DECOMPOSE)
- Clear explanation in comment
- Provides manual override option

**Test Cases**:
```bash
# TC-5.3.1: Ambiguous issue description
# TC-5.3.2: Issue with missing details
# TC-5.3.3: Edge case complexity score
```

**Testing Priority**: 🟠 MEDIUM

#### FS-5.4: ZTE Auto-Merge of Broken Code
**Scenario**: ZTE workflow auto-merges despite quality gate failures
**Affected Workflows**: `adw_sdlc_complete_zte_iso.py`
**Expected Behavior**:
- NEVER auto-merge if ANY phase fails
- NEVER auto-merge if tests fail
- NEVER auto-merge if lint fails
- NEVER auto-merge if build fails

**Test Cases**:
```bash
# TC-5.4.1: Build fails → NO merge
# TC-5.4.2: Lint fails → NO merge
# TC-5.4.3: Test fails → NO merge
# TC-5.4.4: Review fails → NO merge
# TC-5.4.5: All pass → YES merge
```

**Testing Priority**: 🔴 CRITICAL

---

### Category 6: Cost & Performance

#### FS-6.1: Runaway Token Usage
**Scenario**: Workflow consumes excessive tokens (>$50)
**Affected Workflows**: ALL workflows
**Expected Behavior**:
- Cost estimation before execution
- Token usage monitoring during execution
- Abort if exceeds reasonable threshold
- External tools enabled by default (70-95% reduction)

**Test Cases**:
```bash
# TC-6.1.1: Large codebase change
# TC-6.1.2: Complex nested issue
# TC-6.1.3: Iterative resolution loops
# TC-6.1.4: External tools disabled (--no-external)
```

**Testing Priority**: 🟡 HIGH

#### FS-6.2: Infinite Resolution Loops
**Scenario**: Auto-resolution retries indefinitely
**Affected Workflows**: Test and Review phases with auto-resolution
**Expected Behavior**:
- Maximum retry limit (3-5 attempts)
- Exponential backoff between retries
- Abort if no progress made

**Test Cases**:
```bash
# TC-6.2.1: Test fix doesn't resolve failure
# TC-6.2.2: Review fix creates new blockers
# TC-6.2.3: Circular dependency in fixes
```

**Testing Priority**: 🟡 HIGH

---

## Test Matrix

### Priority 1: CRITICAL (Must Test Before Production Use)

| ID | Scenario | Workflow Type | Test Method | Expected Outcome | Issue Reference |
|----|----------|---------------|-------------|------------------|-----------------|
| TC-1.1.2 | Dirty main, no new errors | Complete SDLC | Real workflow | Pass with baseline ignore | #66 |
| TC-1.1.3 | Dirty main, new errors | Complete SDLC | Real workflow | Fail on new errors only | #66 |
| TC-1.2.1 | New TypeScript error | Complete SDLC | Inject error | Fail with clear message | #66 |
| TC-1.4.1 | Frontend unit test fail | Complete SDLC | Failing test | Fail with auto-resolve | - |
| TC-2.3.1 | Missing API key | ALL | Remove .env var | Fail early with message | - |
| TC-3.1.1 | API quota exhausted | ALL | Mock quota | Fail with quota status | #66 |
| TC-3.5.1 | Phantom merge | Ship phase | Mock GitHub API | Detect and revert | #64 |
| TC-4.3.1 | Concurrent ADWs | ALL | Parallel execution | Lock prevents conflict | #8 |
| TC-5.4.1 | ZTE with build fail | Complete ZTE | Inject error | NO auto-merge | - |

### Priority 2: HIGH (Important for Stability)

| ID | Scenario | Workflow Type | Test Method | Expected Outcome | Issue Reference |
|----|----------|---------------|-------------|------------------|-----------------|
| TC-1.3.1 | ESLint violations | Complete SDLC | Bad code | Fail with suggestions | - |
| TC-2.1.2 | Concurrent port alloc | ALL | Parallel workflows | Unique ports | - |
| TC-2.2.1 | Disk space full | Plan phase | Mock disk error | Fail gracefully | - |
| TC-3.2.1 | Issue not found | ALL | Invalid issue # | Fail early | - |
| TC-3.3.1 | PR already exists | Ship phase | Duplicate PR | Fail with link | - |
| TC-4.1.1 | Corrupted state | Build/Test | Malformed JSON | Fail with recovery | - |
| TC-6.1.1 | Excessive tokens | ALL | Large change | Abort with estimate | - |

### Priority 3: MEDIUM (Nice to Have)

| ID | Scenario | Workflow Type | Test Method | Expected Outcome | Issue Reference |
|----|----------|---------------|-------------|------------------|-----------------|
| TC-2.4.1 | Database locked | Ship/Document | Lock DB | Retry with backoff | - |
| TC-3.4.1 | Comment post fail | ALL | Network issue | Log and continue | - |
| TC-4.2.1 | Build before Plan | Build phase | Out of order | Fail with message | - |
| TC-5.1.1 | Complex → Lightweight | Lightweight | Wrong routing | Fail with recommend | - |
| TC-5.2.1 | Missing patch keyword | Patch | No keyword | Fail early | - |
| TC-6.2.1 | Infinite fix loop | Test phase | Persistent failure | Abort after 3 tries | - |

---

## Testing Strategy

### Phase 1: Automated Unit Tests
Create pytest/vitest tests for individual failure scenarios:

```python
# Example: test_inherited_errors.py
def test_validate_phase_detects_baseline_errors(worktree_with_errors):
    """TC-1.1.2: Validate phase detects inherited errors"""
    result = run_validate_phase(worktree_with_errors)
    assert result.baseline_errors > 0
    assert result.status == "success"  # Validate never fails

def test_build_phase_ignores_baseline_errors(worktree_with_errors):
    """TC-1.1.2: Build phase ignores baseline errors"""
    validate_result = run_validate_phase(worktree_with_errors)
    build_result = run_build_phase(worktree_with_errors, no_new_changes=True)
    assert build_result.status == "success"
    assert build_result.new_errors == 0
```

### Phase 2: Integration Tests
Test complete workflow executions:

```bash
# Example: Integration test script
#!/bin/bash
set -e

echo "TC-1.1.2: Testing inherited errors scenario"

# Create test issue with TypeScript errors on main
create_test_issue "Test inherited errors" "simple fix"

# Run complete workflow
uv run adw_sdlc_complete_iso.py $ISSUE_NUM

# Verify workflow passed despite baseline errors
assert_workflow_success $ISSUE_NUM
```

### Phase 3: Manual Testing Checklist
For scenarios difficult to automate:

- [ ] TC-2.1.4: Manually occupy all 15 ports, verify fallback
- [ ] TC-3.1.2: Manually trigger mid-workflow quota exhaustion
- [ ] TC-3.5.1: Use GitHub API mock server for phantom merge
- [ ] TC-5.4.5: Run complete ZTE on passing PR, verify auto-merge

### Phase 4: Chaos Engineering
Randomly inject failures during workflow execution:

```python
# chaos_test.py
def chaos_test_complete_workflow():
    """Randomly inject failures to test resilience"""
    failures = [
        ("network_timeout", 0.1),
        ("disk_full", 0.05),
        ("api_rate_limit", 0.15),
        ("port_conflict", 0.1),
    ]

    for _ in range(10):
        inject_random_failure(failures)
        result = run_workflow_with_chaos()
        assert result.handled_gracefully
```

---

## Success Criteria

### Critical Scenarios (Must Pass)
- ✅ Inherited errors don't block valid work (TC-1.1.2)
- ✅ New errors are always caught (TC-1.2.1)
- ✅ API quota exhaustion handled gracefully (TC-3.1.1)
- ✅ Phantom merges detected and prevented (TC-3.5.1)
- ✅ Concurrent ADWs don't conflict (TC-4.3.1)
- ✅ ZTE never merges broken code (TC-5.4.1-5)

### High Priority Scenarios (Should Pass)
- ✅ Port conflicts resolved automatically (TC-2.1.2)
- ✅ Missing env vars fail early (TC-2.3.1)
- ✅ Invalid issues caught early (TC-3.2.1)
- ✅ Corrupted state handled gracefully (TC-4.1.1)

### Medium Priority Scenarios (Nice to Pass)
- ✅ Database locks handled with retry (TC-2.4.1)
- ✅ Comment failures are non-fatal (TC-3.4.1)
- ✅ Wrong workflow routing detected (TC-5.1.1)
- ✅ Infinite loops prevented (TC-6.2.1)

---

## Recommendations

### Immediate Actions
1. **Implement Critical Tests** (TC-1.1.2, TC-1.2.1, TC-3.5.1, TC-4.3.1, TC-5.4.1)
2. **Add P1.1 CI/CD Pipeline** from Issue #66 plan (currently NOT implemented)
3. **Regression Test Suite** for Issue #64 and #66 scenarios

### Short-term Improvements
1. **Chaos Engineering Suite** for resilience testing
2. **Integration Test Harness** for end-to-end workflows
3. **Cost Monitoring** for runaway token usage

### Long-term Enhancements
1. **Workflow Health Dashboard** showing failure rates by scenario
2. **Automated Recovery** for common failure patterns
3. **Predictive Failure Detection** using ML on workflow logs

---

## Appendix: Issue References

### Issue #66 (Build Check Failure)
- **Problem**: Inherited TypeScript errors from main branch
- **Solution**: New Validate phase + differential error detection
- **Status**: 7/8 complete (P1.1 CI/CD pending)
- **Related Scenarios**: TC-1.1.x, TC-1.2.x

### Issue #64 (Quality Gate Failures)
- **Problem**: Phantom merges, data integrity issues
- **Solution**: Post-merge verification, data validation in Review
- **Status**: Complete
- **Related Scenarios**: TC-3.5.x

### Issue #8 (Concurrent ADWs)
- **Problem**: Multiple ADWs working on same issue
- **Solution**: adw_locks table with mutex locking
- **Status**: Complete
- **Related Scenarios**: TC-4.3.x

---

**Document Status**: ✅ Ready for Test Implementation
**Next Action**: Implement Priority 1 tests from test matrix
**Owner**: tac-webbuilder QA team
**Review Date**: 2025-11-21
