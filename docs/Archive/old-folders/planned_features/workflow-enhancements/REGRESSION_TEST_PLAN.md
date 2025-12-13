# ADW Workflow Enhancements - Regression Test Plan

**Status:** Ready for Execution
**Created:** 2025-11-17
**Version:** 1.0

---

## Executive Summary

This test plan validates the new ADW workflow enhancements while ensuring no regressions in existing functionality.

### Scope

**New Features:**
- ✅ Stepwise refinement analysis (`adw_stepwise_iso.py`)
- ✅ Complete SDLC workflow (`adw_sdlc_complete_iso.py`)
- ✅ Complete ZTE workflow (`adw_sdlc_complete_zte_iso.py`)

**Regression Coverage:**
- All existing workflows remain functional
- State management compatibility
- GitHub API integrations
- External workflow tools
- Documentation accuracy

---

## Test Environment Setup

### Prerequisites

```bash
# 1. Verify environment variables
echo "GITHUB_REPO_URL: ${GITHUB_REPO_URL}"
echo "ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:0:10}..."
echo "CLAUDE_CODE_PATH: ${CLAUDE_CODE_PATH}"

# 2. Verify tools installed
gh --version
claude --version
uv --version
git --version

# 3. Authenticate
gh auth status

# 4. Clean up any existing test worktrees
git worktree list
# Remove any test worktrees: git worktree remove trees/{adw_id}
```

### Test Repository Setup

```bash
# Create a test branch for regression testing
git checkout -b regression-test-workflow-enhancements

# Ensure we're on a clean state
git status
```

---

## Test Categories

### Category 1: New Workflow Functionality ✨

#### Test 1.1: Stepwise Refinement - ATOMIC Decision

**Objective:** Verify stepwise analysis correctly identifies atomic issues

**Test Steps:**
1. Create simple test issue:
   ```bash
   gh issue create \
     --title "Fix: Update copyright year in footer" \
     --body "Simple one-line change to update footer copyright from 2024 to 2025"
   ```
2. Run stepwise analysis:
   ```bash
   cd adws/
   uv run adw_stepwise_iso.py <issue-number>
   ```

**Expected Results:**
- ✅ Exit code: 0 (ATOMIC decision)
- ✅ GitHub comment shows "Decision: ATOMIC"
- ✅ No sub-issues created
- ✅ Recommendation to use `adw_sdlc_complete_iso` or `adw_lightweight_iso`
- ✅ State file created with decision data

**Validation:**
```bash
# Check state file
cat agents/{adw_id}/adw_state.json | jq '.stepwise_decision'
# Should output: "ATOMIC"

# Check exit code
echo $?
# Should output: 0
```

---

#### Test 1.2: Stepwise Refinement - DECOMPOSE Decision

**Objective:** Verify stepwise analysis correctly decomposes complex issues

**Test Steps:**
1. Create complex test issue:
   ```bash
   gh issue create \
     --title "Feature: Add user authentication system" \
     --body "Implement complete user authentication including:
     - Database schema for users
     - Registration API endpoints
     - Login/logout functionality
     - JWT token management
     - Frontend login/registration forms
     - Password reset flow
     - Email verification"
   ```
2. Run stepwise analysis:
   ```bash
   cd adws/
   uv run adw_stepwise_iso.py <issue-number>
   ```

**Expected Results:**
- ✅ Exit code: 10 (DECOMPOSE decision)
- ✅ GitHub comment shows "Decision: DECOMPOSE"
- ✅ 2-5 sub-issues created
- ✅ Sub-issues linked to parent issue
- ✅ Dependencies correctly specified
- ✅ State file contains sub-issue numbers

**Validation:**
```bash
# Check sub-issues created
gh issue list --label sub-issue

# Check parent issue has reference
gh issue view <parent-issue-number>

# Check state file
cat agents/{adw_id}/adw_state.json | jq '.sub_issue_numbers'

# Check exit code
echo $?
# Should output: 10
```

---

#### Test 1.3: Complete SDLC - All 8 Phases

**Objective:** Verify complete SDLC executes all phases in correct order

**Test Steps:**
1. Create feature test issue:
   ```bash
   gh issue create \
     --title "Feature: Add dark mode toggle" \
     --body "Add a dark mode toggle to the settings page"
   ```
2. Run complete SDLC:
   ```bash
   cd adws/
   uv run adw_sdlc_complete_iso.py <issue-number> --skip-e2e --use-optimized-plan
   ```

**Expected Results:**
- ✅ Phase 1: Plan completes successfully
- ✅ Phase 2: Build completes successfully
- ✅ Phase 3: Lint passes ✨ (NEW)
- ✅ Phase 4: Tests pass
- ✅ Phase 5: Review passes
- ✅ Phase 6: Documentation generated
- ✅ Phase 7: PR approved and merged ✨ (NEW)
- ✅ Phase 8: Cleanup completes ✨ (NEW)
- ✅ Exit code: 0
- ✅ PR merged to main
- ✅ Worktree removed

**Validation:**
```bash
# Check all phases in state
cat agents/{adw_id}/adw_state.json | jq '.adw_ids'
# Should include: plan, build, lint, test, review, document

# Check PR merged
gh pr list --state merged | grep <branch-name>

# Check worktree cleaned up
git worktree list | grep <adw_id>
# Should return nothing

# Check main branch updated
git log main --oneline -5
```

---

#### Test 1.4: Complete ZTE - Auto-Merge

**Objective:** Verify ZTE completes all phases and auto-merges

**Test Steps:**
1. Create simple feature issue:
   ```bash
   gh issue create \
     --title "Chore: Add loading spinner to button" \
     --body "Add loading state with spinner to submit button"
   ```
2. Run complete ZTE:
   ```bash
   cd adws/
   uv run adw_sdlc_complete_zte_iso.py <issue-number> --skip-e2e --use-optimized-plan
   ```

**Expected Results:**
- ✅ All 8 phases complete automatically
- ✅ Lint phase prevents broken code ✨
- ✅ PR auto-merged to main
- ✅ GitHub comments show ZTE progress
- ✅ Warning messages about auto-merge
- ✅ Cleanup runs automatically
- ✅ Exit code: 0

**Validation:**
```bash
# Check auto-merge happened
gh pr list --state merged | grep <branch-name>

# Check GitHub comments mention ZTE
gh issue view <issue-number> | grep "Zero Touch Execution"

# Check timing (should be < 5 minutes for simple feature)
```

---

### Category 2: Regression Testing - Existing Workflows

#### Test 2.1: Individual Phase Workflows Still Work

**Test Steps:**
```bash
# Test each individual phase workflow
uv run adw_plan_iso.py <issue-1>
uv run adw_build_iso.py <issue-1> <adw-id>
uv run adw_lint_iso.py <issue-1> <adw-id>
uv run adw_test_iso.py <issue-1> <adw-id> --skip-e2e
uv run adw_review_iso.py <issue-1> <adw-id>
uv run adw_document_iso.py <issue-1> <adw-id>
uv run adw_ship_iso.py <issue-1> <adw-id>
uv run adw_cleanup_iso.py <issue-1> <adw-id>
```

**Expected Results:**
- ✅ All phases execute without errors
- ✅ State management works correctly
- ✅ No new errors introduced

---

#### Test 2.2: Deprecated Workflows Show Warnings

**Test Steps:**
```bash
# Test deprecated workflows
uv run adw_sdlc_iso.py <issue-number>
uv run adw_sdlc_zte_iso.py <issue-number>
uv run adw_plan_build_iso.py <issue-number>
uv run adw_plan_build_test_iso.py <issue-number>
```

**Expected Results:**
- ✅ Deprecation warnings printed to console
- ✅ Warnings mention replacement workflows
- ✅ Workflows still function correctly
- ✅ GitHub comments mention deprecation

**Example Warning:**
```
======================================================================
WARNING: DEPRECATION NOTICE
======================================================================
This workflow is incomplete (missing Lint, Ship, Cleanup phases)
Please use: adw_sdlc_complete_iso.py
Continuing execution...
======================================================================
```

---

#### Test 2.3: External Workflows Still Function

**Test Steps:**
```bash
# Test external tool workflows
uv run adw_build_iso.py <issue-number> <adw-id>  # Should use external by default
uv run adw_lint_iso.py <issue-number> <adw-id>   # Should use external by default
uv run adw_test_iso.py <issue-number> <adw-id>   # Should use external by default

# Test with --no-external flag
uv run adw_build_iso.py <issue-number> <adw-id> --no-external
```

**Expected Results:**
- ✅ External tools used by default
- ✅ Token usage significantly lower (70-95% reduction)
- ✅ --no-external flag works (higher token usage)
- ✅ Build/lint/test results consistent

---

### Category 3: State Management & Compatibility

#### Test 3.1: State Files Compatible Across Workflows

**Test Steps:**
1. Run stepwise → complete SDLC chain
2. Verify state persists correctly

```bash
# Run stepwise (creates state)
uv run adw_stepwise_iso.py <issue-number>

# Check state
cat agents/{adw_id}/adw_state.json

# Run complete SDLC (should use same state)
uv run adw_sdlc_complete_iso.py <issue-number> <adw-id>

# Verify state updated
cat agents/{adw_id}/adw_state.json | jq '.adw_ids'
```

**Expected Results:**
- ✅ State file created by stepwise
- ✅ Complete SDLC reads and updates state
- ✅ No state conflicts
- ✅ All workflow IDs tracked

---

#### Test 3.2: Worktree Isolation

**Test Steps:**
1. Run multiple workflows in parallel
```bash
# Terminal 1
uv run adw_sdlc_complete_iso.py 101 &

# Terminal 2
uv run adw_sdlc_complete_iso.py 102 &

# Terminal 3
uv run adw_sdlc_complete_iso.py 103 &
```

**Expected Results:**
- ✅ Each gets unique ADW ID
- ✅ Each gets unique worktree
- ✅ Each gets unique ports
- ✅ No interference between workflows
- ✅ All complete successfully

---

### Category 4: Documentation Validation

#### Test 4.1: All References Valid

**Test Steps:**
```bash
# Check for broken workflow references
cd /Users/Warmonger0/tac/tac-webbuilder

# Search for workflow references in docs
grep -r "adw_.*\.py" docs/ .claude/ | \
  grep -v "Binary" | \
  while read line; do
    # Extract filename
    file=$(echo "$line" | grep -oE "adw_[a-z_]+\.py")
    if [ -n "$file" ] && [ ! -f "adws/$file" ]; then
      echo "BROKEN REFERENCE: $line"
    fi
  done
```

**Expected Results:**
- ✅ No broken references to workflow files
- ✅ All mentioned workflows exist
- ✅ Deprecated workflows clearly marked

---

#### Test 4.2: Documentation Consistency

**Test Steps:**
1. Verify new workflows documented in all locations:
   - `adws/README.md`
   - `.claude/commands/references/adw_workflows.md`
   - `.claude/commands/quick_start/adw.md`

2. Check deprecation notices consistent

**Expected Results:**
- ✅ New workflows in all documentation
- ✅ Flags documented consistently
- ✅ Examples use recommended workflows
- ✅ Deprecation warnings consistent

---

### Category 5: Error Handling & Edge Cases

#### Test 5.1: Lint Failure Stops Workflow

**Test Steps:**
1. Create intentionally broken code
2. Run complete SDLC
3. Verify lint phase catches and stops

**Expected Results:**
- ✅ Build phase succeeds
- ✅ Lint phase fails
- ✅ Workflow stops at lint (doesn't continue to test)
- ✅ Clear error message
- ✅ No PR created

---

#### Test 5.2: Test Failure Stops ZTE

**Test Steps:**
1. Create code with failing tests
2. Run complete ZTE
3. Verify ZTE aborts before ship

**Expected Results:**
- ✅ Test phase fails
- ✅ ZTE aborts with clear message
- ✅ No auto-merge occurs
- ✅ GitHub comment explains abort reason

---

#### Test 5.3: Cleanup Handles Missing Worktree

**Test Steps:**
1. Manually delete worktree
2. Run cleanup
3. Verify graceful handling

**Expected Results:**
- ✅ Cleanup doesn't crash
- ✅ Warning logged
- ✅ Continues with other cleanup tasks
- ✅ Exit code indicates partial success

---

## Automated Test Suite

### Quick Smoke Test

```bash
#!/bin/bash
# smoke_test.sh - Quick validation of new workflows

set -e

echo "=== ADW Workflow Enhancement Smoke Test ==="

# Test 1: Stepwise with ATOMIC issue
echo "Test 1: Stepwise ATOMIC..."
ISSUE_1=$(gh issue create --title "Test: Simple fix" --body "One line change" | grep -oE '[0-9]+$')
uv run adws/adw_stepwise_iso.py $ISSUE_1
[ $? -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED"

# Test 2: Complete SDLC dry run (plan only)
echo "Test 2: Complete SDLC (plan phase)..."
ISSUE_2=$(gh issue create --title "Test: Feature" --body "Test feature" | grep -oE '[0-9]+$')
uv run adws/adw_plan_iso_optimized.py $ISSUE_2
[ $? -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED"

# Test 3: Deprecated workflow shows warning
echo "Test 3: Deprecated workflow warning..."
ISSUE_3=$(gh issue create --title "Test: Deprecated" --body "Test deprecated workflow" | grep -oE '[0-9]+$')
uv run adws/adw_sdlc_iso.py $ISSUE_3 2>&1 | grep -q "DEPRECATION WARNING"
[ $? -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED"

echo "=== Smoke Test Complete ==="
```

---

## Success Criteria

### Must Pass (Critical)
- ✅ All new workflows execute without errors
- ✅ Stepwise correctly identifies ATOMIC vs DECOMPOSE
- ✅ Complete SDLC includes all 8 phases
- ✅ Lint phase prevents broken code from reaching tests
- ✅ Complete ZTE auto-merges only when all phases pass
- ✅ All deprecated workflows show warnings
- ✅ No broken documentation references
- ✅ State management works across workflows

### Should Pass (Important)
- ✅ External tools provide 70-95% token reduction
- ✅ Optimized planner provides 77% cost reduction
- ✅ Parallel workflows don't interfere
- ✅ Error messages are clear and actionable
- ✅ Cleanup handles edge cases gracefully

### Nice to Have
- ✅ Performance benchmarks meet expectations
- ✅ Cost estimates accurate within 20%
- ✅ All examples in docs work as-is

---

## Test Execution Checklist

- [ ] Environment setup complete
- [ ] All Category 1 tests passed (New Functionality)
- [ ] All Category 2 tests passed (Regression)
- [ ] All Category 3 tests passed (State Management)
- [ ] All Category 4 tests passed (Documentation)
- [ ] All Category 5 tests passed (Error Handling)
- [ ] Smoke test script executed successfully
- [ ] All test issues cleaned up
- [ ] Test worktrees removed
- [ ] Results documented

---

## Test Results Log Template

```markdown
# Test Execution Results - [DATE]

## Environment
- Branch: regression-test-workflow-enhancements
- Commit: [hash]
- Tester: [name]

## Results Summary
- Total Tests: X
- Passed: X
- Failed: X
- Skipped: X

## Detailed Results

### Test 1.1: Stepwise ATOMIC
- Status: ✅ PASSED / ❌ FAILED
- Issue #: XXX
- Notes: ...

[Continue for each test...]

## Issues Found
1. [Description] - Severity: [High/Medium/Low]
2. ...

## Recommendations
- ...
```

---

**Document Version:** 1.0
**Last Updated:** 2025-11-17
