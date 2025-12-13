# Task: Document ADW Phase Contracts and Dependencies

## Context
I'm working on the tac-webbuilder project. Phase 2 of Session 19 addresses dual-state management issues. This is Part 1 of 4 - establishing the foundation by documenting what each phase requires and produces.

## Objective
Create comprehensive documentation of phase input/output contracts for all 10 ADW SDLC phases, making dependencies explicit and enabling better validation.

## Background Information
- **Files:** All 10 phase scripts in `adws/` directory
- **Current Problem:** Phase dependencies are implicit, making validation difficult
- **Target Solution:** Explicit REQUIRES/PRODUCES contracts for each phase
- **Risk Level:** Low (documentation only, no code changes to logic)
- **Estimated Time:** 4 hours

## Current State

The 10 ADW phases are:
1. Plan (adw_planning.py) - Generates SDLC plan
2. Validate (adw_validate.py) - Validates plan feasibility
3. Build (adw_build.py) - Implements code changes
4. Lint (adw_lint.py) - Runs linters
5. Test (adw_test_iso.py) - Runs tests
6. Review (adw_review.py) - Code review
7. Document (adw_document.py) - Updates documentation
8. Ship (adw_ship.py) - Creates PR
9. Cleanup (adw_cleanup.py) - Removes worktree
10. Verify (adw_verify.py) - Post-merge validation

**Problem:**
- No explicit documentation of what each phase needs as input
- No explicit documentation of what each phase produces as output
- Dependencies are buried in code logic
- Hard to validate before execution starts

## Target Solution

Create structured documentation showing:

### 1. Phase Contract Documentation (`docs/adw/phase-contracts.md`)

For each phase, document:
```yaml
Phase: Plan
REQUIRES:
  - GitHub issue number
  - Valid GitHub token
  - Database connection
  - Issue metadata (title, body, labels)

PRODUCES:
  - SDLC_PLAN.md file
  - adw_state.json (initialized)
  - phase_queue record (status: planned)
  - Cost estimate

SIDE_EFFECTS:
  - Creates worktree directory
  - Updates database phase_queue table
  - Records observability event

ERROR_CONDITIONS:
  - Issue not found (404)
  - Invalid issue format
  - Database unavailable
  - Insufficient permissions
```

### 2. Dependency Graph (`docs/adw/phase-dependencies.md`)

Visual representation:
```
Plan
  ↓ (requires: SDLC_PLAN.md)
Validate
  ↓ (requires: validated plan, adw_state.json)
Build
  ↓ (requires: code changes, updated files)
Lint
  ↓ (requires: lint passing)
Test
  ↓ (requires: tests passing)
Review
  ↓ (requires: review comments)
Document
  ↓ (requires: docs updated)
Ship
  ↓ (requires: PR created)
Cleanup
  ↓ (requires: worktree removed)
Verify
```

### 3. Code Docstring Updates

Add contracts to each phase script:
```python
"""
Phase: Plan
Description: Generate comprehensive SDLC plan from GitHub issue

CONTRACT:
  REQUIRES:
    - issue_number: int (valid GitHub issue)
    - github_token: str (valid PAT with repo access)
    - db_connection: Available PostgreSQL connection

  PRODUCES:
    - SDLC_PLAN.md: Structured plan file
    - adw_state.json: Initial state tracking
    - phase_queue record: Database entry

  GUARANTEES:
    - If successful, SDLC_PLAN.md will exist and be valid markdown
    - adw_state.json will contain all required fields
    - Database record will be created with status='planned'

  ERROR_HANDLING:
    - Returns non-zero exit code on failure
    - Logs errors to observability system
    - Does not create partial outputs (atomic operation)
"""
```

## Step-by-Step Instructions

### Step 1: Analyze Current Phase Scripts

```bash
cd adws/

# List all phase scripts
ls -1 adw_*.py | grep -v "__pycache__"

# For each phase, identify:
# 1. Input parameters (argparse, function signatures)
# 2. File reads (open(), Path().read_text())
# 3. File writes (open('w'), Path().write_text())
# 4. Database reads (SELECT queries)
# 5. Database writes (INSERT/UPDATE queries)
# 6. External API calls (GitHub, OpenAI, Anthropic)
```

### Step 2: Extract Contracts from Code

For each phase script, create a contract document:

```bash
# Example: Analyze planning phase
grep -n "argparse\|open(\|cursor.execute\|github\|anthropic" adw_planning.py

# Document findings in structured format
# Repeat for all 10 phases
```

### Step 3: Create Phase Contracts Documentation

Create `docs/adw/phase-contracts.md`:

```markdown
# ADW Phase Contracts

## Overview
This document defines the input/output contracts for all 10 ADW SDLC phases.

## Contract Format
Each phase documents:
- **REQUIRES**: Inputs needed before phase can execute
- **PRODUCES**: Outputs guaranteed after successful execution
- **SIDE_EFFECTS**: External state changes (DB, files, API)
- **ERROR_CONDITIONS**: Known failure modes

---

## Phase 1: Plan

### REQUIRES
- **Input Parameters:**
  - `issue_number`: int - Valid GitHub issue number
  - `github_token`: str - PAT with repo:write access

- **Database State:**
  - PostgreSQL connection available
  - phase_queue table exists

- **External Services:**
  - GitHub API accessible
  - Anthropic API accessible (for plan generation)

### PRODUCES
- **Files Created:**
  - `trees/{adw_id}/SDLC_PLAN.md` - Structured plan (5-15 KB)
  - `trees/{adw_id}/adw_state.json` - Initial state tracking

- **Database Records:**
  - `phase_queue` record with status='planned'
  - `observability_events` record for plan creation

- **Return Values:**
  - Exit code 0 on success
  - JSON output with adw_id and worktree_path

### SIDE_EFFECTS
- Creates git worktree at `trees/{adw_id}/`
- Updates GitHub issue with plan comment
- Records cost in observability system

### ERROR_CONDITIONS
- Issue not found: Exit code 1, error message
- Invalid issue format: Exit code 2, validation details
- Database unavailable: Exit code 3, connection error
- API rate limit: Exit code 4, retry suggestion

---

## Phase 2: Validate
[... continue for all 10 phases ...]
```

### Step 4: Create Dependency Graph

Create `docs/adw/phase-dependencies.md`:

```markdown
# ADW Phase Dependencies

## Visual Dependency Graph

```
┌─────────────────────────────────────────────────┐
│ Phase 1: Plan                                   │
│ Produces: SDLC_PLAN.md, adw_state.json          │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ Phase 2: Validate                               │
│ Requires: SDLC_PLAN.md                          │
│ Produces: Validated plan, feasibility report    │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
[... continue for all phases ...]
```

## Dependency Matrix

| Phase    | Depends On           | Required Files          | Optional Files |
|----------|---------------------|-------------------------|----------------|
| Plan     | None                | -                       | -              |
| Validate | Plan                | SDLC_PLAN.md            | -              |
| Build    | Validate            | SDLC_PLAN.md, state     | -              |
| Lint     | Build               | Source files            | .eslintrc      |
| Test     | Build               | Source + test files     | pytest.ini     |
[... continue ...]
```

### Step 5: Add Contract Docstrings to Code

For each phase script in `adws/`, add comprehensive docstring:

```python
# Example: adws/adw_planning.py

"""
ADW Phase 1: Plan Generation

Generates comprehensive SDLC plan from GitHub issue using Claude.

CONTRACT:
  REQUIRES:
    - issue_number: Valid GitHub issue number
    - github_token: PAT with repo access
    - PostgreSQL database available
    - Anthropic API accessible

  PRODUCES:
    - SDLC_PLAN.md: Structured plan file (5-15 KB markdown)
    - adw_state.json: Initial state tracking JSON
    - phase_queue record: Database entry with status='planned'
    - observability_event: Plan generation event

  GUARANTEES:
    - Atomic operation: Either all outputs created or none
    - SDLC_PLAN.md validated before returning
    - Database and file state synchronized

  ERROR_HANDLING:
    - Exit code 0: Success
    - Exit code 1: Issue not found or invalid
    - Exit code 2: API failure (GitHub/Anthropic)
    - Exit code 3: Database unavailable
    - All errors logged to observability system

  SIDE_EFFECTS:
    - Creates git worktree at trees/{adw_id}/
    - Posts plan comment to GitHub issue
    - Updates observability database
    - Allocates unique ADW ID and ports

USAGE:
    python adw_planning.py <issue_number>

EXAMPLE:
    $ python adw_planning.py 123
    {
      "adw_id": 5,
      "worktree_path": "/path/to/trees/adw-5",
      "status": "planned"
    }
"""
```

Repeat for all 10 phase scripts.

### Step 6: Create Quick Reference Card

Create `docs/adw/phase-contracts-quick-ref.md`:

```markdown
# ADW Phase Contracts - Quick Reference

| Phase    | Key Input                | Key Output              | Can Skip If        |
|----------|--------------------------|-------------------------|-------------------|
| Plan     | Issue #                  | SDLC_PLAN.md            | Never             |
| Validate | SDLC_PLAN.md             | Validated plan          | Never             |
| Build    | Plan + issue             | Code changes            | Never             |
| Lint     | Source files             | Lint pass               | No linters found  |
| Test     | Source + tests           | Test pass               | No tests exist    |
| Review   | Code changes             | Review comments         | Never             |
| Document | Code changes             | Updated docs            | Docs unchanged    |
| Ship     | All above                | PR created              | Never             |
| Cleanup  | PR merged/closed         | Worktree removed        | Never             |
| Verify   | PR merged                | Verification report     | Optional          |

## Critical Dependencies

- **Cannot skip:** Plan, Validate, Build, Review, Ship, Cleanup
- **Can skip if N/A:** Lint (no config), Test (no tests), Document (no changes), Verify (optional)
- **Atomic operations:** Plan, Build, Ship (all-or-nothing)
- **Idempotent:** All phases should be safely re-runnable
```

### Step 7: Validate Documentation Completeness

```bash
# Check all 10 phases documented
grep -c "^## Phase" docs/adw/phase-contracts.md  # Should be 10

# Check all phases have required sections
for phase in Plan Validate Build Lint Test Review Document Ship Cleanup Verify; do
  echo "Checking $phase..."
  grep -A 20 "## Phase.*$phase" docs/adw/phase-contracts.md | \
    grep -E "REQUIRES|PRODUCES|SIDE_EFFECTS|ERROR_CONDITIONS" || \
    echo "  ⚠️  Missing sections for $phase"
done

# Verify all phase scripts have contract docstrings
for script in adws/adw_*.py; do
  echo "Checking $script..."
  head -50 "$script" | grep -q "CONTRACT:" || \
    echo "  ⚠️  Missing contract docstring in $script"
done
```

### Step 8: Test Documentation

```bash
# Generate dependency graph visualization (optional)
# If you have graphviz installed
cd docs/adw/
# Create a .dot file from dependency info and render
# (This is optional, manual graph is fine)

# Verify all documentation is valid markdown
cd docs/adw/
for doc in *.md; do
  echo "Validating $doc..."
  # Basic markdown validation
  grep -E "^#+ " "$doc" > /dev/null && echo "  ✓ Headers OK" || echo "  ✗ No headers"
done
```

### Step 9: Commit Changes

```bash
git add docs/adw/
git add adws/adw_*.py  # Updated docstrings
git commit -m "docs: Add comprehensive ADW phase contracts

Part 1 of 4 for Session 19 Phase 2 (State Management Clarity)

Created structured documentation for all 10 ADW phases:
- REQUIRES: Explicit input requirements
- PRODUCES: Guaranteed outputs
- SIDE_EFFECTS: External state changes
- ERROR_CONDITIONS: Known failure modes

Files Added:
- docs/adw/phase-contracts.md (complete contracts)
- docs/adw/phase-dependencies.md (dependency graph)
- docs/adw/phase-contracts-quick-ref.md (quick reference)

Files Modified:
- All 10 phase scripts in adws/ (added contract docstrings)

Benefits:
- Clear contracts enable pre-execution validation (Part 3)
- Explicit dependencies enable better error messages
- Foundation for idempotent phases (Part 4)
- Easier onboarding for new developers

Next: Part 2 - Define Single Source of Truth (6 hours)"
```

## Success Criteria

- ✅ All 10 phases have complete contract documentation
- ✅ Dependency graph shows clear phase relationships
- ✅ All phase scripts have contract docstrings
- ✅ Quick reference card created
- ✅ Documentation validated (complete, consistent)
- ✅ Changes committed with descriptive message

## Files Expected to Change

**Created:**
- `docs/adw/phase-contracts.md` (~3-5 KB, complete contracts)
- `docs/adw/phase-dependencies.md` (~2 KB, dependency graph)
- `docs/adw/phase-contracts-quick-ref.md` (~1 KB, quick ref)

**Modified:**
- `adws/adw_planning.py` (contract docstring)
- `adws/adw_validate.py` (contract docstring)
- `adws/adw_build.py` (contract docstring)
- `adws/adw_lint.py` (contract docstring)
- `adws/adw_test_iso.py` (contract docstring)
- `adws/adw_review.py` (contract docstring)
- `adws/adw_document.py` (contract docstring)
- `adws/adw_ship.py` (contract docstring)
- `adws/adw_cleanup.py` (contract docstring)
- `adws/adw_verify.py` (contract docstring)

## Deliverables for Summary

When complete, return to coordination chat with:
```
**Issue #1 Complete: Document Phase Contracts**

**Phases Documented:** 10/10
- Plan, Validate, Build, Lint, Test, Review, Document, Ship, Cleanup, Verify

**Documentation Created:**
- Phase contracts (full detail)
- Dependency graph (visual + matrix)
- Quick reference card

**Code Updated:**
- 10 phase scripts now have contract docstrings

**Time Spent:** [actual hours]

**Key Insights:**
- [Any surprising dependencies found]
- [Phases that were missing documentation]
- [Recommendations for Part 2]

**Ready for:** Part 2 - Define Single Source of Truth
```

## Troubleshooting

**If phase script is hard to analyze:**
- Focus on function signatures and file I/O first
- Check database queries second
- Document "Unknown" for unclear dependencies (mark for investigation)

**If dependency graph is complex:**
- Start with linear dependencies (Plan → Validate → Build → ...)
- Add optional branches separately
- Document conditional dependencies clearly

**If docstring is too long:**
- Keep core contract in docstring
- Link to full docs/adw/phase-contracts.md for details
- Focus on REQUIRES and PRODUCES in code

---

**Ready to copy into Issue #1!**
