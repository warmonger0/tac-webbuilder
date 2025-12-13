# Session 19 - Phase 2: State Management Clarity Implementation

## Context
I'm working on the tac-webbuilder project. The architectural consistency analysis identified a critical dual-state management problem where workflow state is tracked in both file system (JSON files) and database (PostgreSQL), creating divergence risks and race conditions. This phase establishes clear boundaries, validates state transitions, and documents contracts.

## Objectives
Implement 4 improvements to clarify state management, add validation, document phase contracts, and enable safe retries.

## Background Information
**Analysis Source**: Multi-agent architectural consistency review (Session 19)
**Priority Level**: HIGH - Data integrity and workflow reliability
**Estimated Time**: 27 hours total (can be split into 4 sub-tasks)
**Risk Level**: Medium-High - Changes affect core ADW workflow state management
**Dependencies**: Phase 1 must be complete

## Current State Management Problem

**Dual State Sources (INCONSISTENT):**
```
┌─────────────────────────────────────┐
│ File System State                   │
│ agents/<adw_id>/adw_state.json     │
│ - plan_file, branch_name            │
│ - worktree_path, ports              │
│ - baseline_errors, build_results    │
│ - Phase metadata                    │
└─────────────────────────────────────┘
              ↕ (can diverge)
┌─────────────────────────────────────┐
│ Database State                      │
│ phase_queue table                   │
│ - status (queued, ready, running)   │
│ - queue_id, phase_number            │
│ - adw_id, issue_number              │
│ - Phase coordination                │
└─────────────────────────────────────┘
```

**Issues:**
- Same data tracked in both places (e.g., adw_id, status)
- No atomic updates across both systems
- Phase transitions can partially fail
- Race conditions during concurrent operations
- No validation that required state exists before phase execution

---

## Phase 2 Tasks Overview

### Task 2.1: Define Single Source of Truth (6 hours)
**Files:**
- `adws/adw_modules/state.py` (ADWState class)
- `app/server/services/phase_queue_service.py`
- `app/server/repositories/phase_queue_repository.py`
- NEW: `docs/architecture/state-management.md`

**Current Problem:**
- `adw_state.json` tracks: adw_id, status, current_phase, plan_file, etc.
- `phase_queue` table tracks: adw_id, status, phase_number, queue_id, etc.
- OVERLAP causes confusion about which is authoritative

**Target Solution:**
- **Database**: Coordination state (phase status, queue position, dependencies)
- **Files**: Workflow metadata (plan paths, worktree paths, execution context)
- Clear boundary: "Does this affect other workflows?" → Database, "Is this workflow-specific context?" → File
- Document and enforce separation

---

### Task 2.2: Add State Validation Middleware (5 hours)
**Files:**
- NEW: `adws/adw_modules/state_validator.py`
- Modify: All 10 phase scripts (adw_plan_iso.py, adw_validate_iso.py, etc.)

**Current Problem:**
- Phases assume state fields exist without validation
- Missing fields cause cryptic errors mid-execution
- No pre-flight checks for required dependencies

**Target Solution:**
- Create `StateValidator` class with phase-specific validation
- Check required fields before phase execution
- Fail fast with clear error messages
- Validate file paths exist on filesystem

---

### Task 2.3: Document Phase Input/Output Contracts (4 hours)
**Files:**
- NEW: `docs/architecture/phase-contracts.md`
- Modify: Each phase script (add docstring contracts)

**Current Problem:**
- Implicit assumptions about what each phase needs
- No documentation of phase dependencies
- Hard to understand data flow through 10-phase workflow

**Target Solution:**
- Define explicit schema for each phase
- Document REQUIRES (input) and PRODUCES (output)
- Create dependency graph visualization
- Add contract validation to StateValidator

---

### Task 2.4: Implement Idempotent Phase Execution (12 hours)
**Files:**
- Modify: All 10 phase scripts
- NEW: `adws/adw_modules/idempotency.py`

**Current Problem:**
- Phases can't be safely re-run after failure
- Crash during phase leaves inconsistent state
- Manual recovery requires understanding internal state

**Target Solution:**
- Make each phase idempotent: same input → same output
- Check if phase already completed before re-executing
- Verify existing outputs are valid, regenerate if corrupted
- Enable automatic crash recovery and safe retries

---

## Multi-Part Implementation Approach

This phase should be implemented in **4 sequential parts**:

### Part 1: Document Phase Contracts (Foundation)
- Estimated: 4 hours
- Risk: Low (documentation only)
- Dependencies: None
- **Do First** - Provides clarity for Parts 2-4

### Part 2: Define Single Source of Truth
- Estimated: 6 hours
- Risk: Medium (architectural changes)
- Dependencies: Part 1 (needs contracts documented)
- **Do Second** - Establishes clear boundaries

### Part 3: Add State Validation Middleware
- Estimated: 5 hours
- Risk: Medium (affects all phase startups)
- Dependencies: Parts 1 & 2 (needs contracts and boundaries)
- **Do Third** - Enforces contracts

### Part 4: Implement Idempotent Phases
- Estimated: 12 hours (largest task)
- Risk: High (modifies all 10 phases)
- Dependencies: Parts 1, 2, 3 (needs validation framework)
- **Do Last** - Most complex, builds on everything

---

## PART 1: Document Phase Input/Output Contracts

### Step 1.1: Create Phase Contracts Documentation

**File:** `docs/architecture/phase-contracts.md` (NEW)

```markdown
# ADW Phase Input/Output Contracts

This document defines the explicit data contracts for each phase in the 10-phase SDLC workflow.

## Contract Format

Each phase contract specifies:
- **Phase Name**: Human-readable name
- **Phase Number**: 1-10
- **Script**: File path to implementation
- **Requires**: Input state fields that MUST exist before execution
- **Produces**: Output state fields that WILL exist after successful execution
- **Optional**: Input fields that MAY be used if present
- **Side Effects**: External changes (git operations, file creation, API calls)

---

## Phase 1: PLAN

**Script**: `adws/adw_plan_iso.py`

**Requires**:
- `issue_number` (int) - GitHub issue to plan for
- Environment: GitHub API access, git repository

**Produces**:
- `adw_id` (str) - Unique workflow identifier (format: adw-{random})
- `plan_file` (str) - Absolute path to generated plan markdown file
- `branch_name` (str) - Git branch name created for this workflow
- `worktree_path` (str) - Absolute path to isolated worktree directory
- `issue_class` (str) - Classified issue type (/feature, /bug, /enhancement)
- `backend_port` (int) - Allocated backend service port (9100-9114)
- `frontend_port` (int) - Allocated frontend service port (9200-9214)
- `status` (str) - Workflow status (initially "running")
- `current_phase` (str) - Current phase name (initially "Plan")
- `workflow_template` (str) - Template name (e.g., "adw_sdlc_complete_iso")

**Optional**:
- None

**Side Effects**:
- Creates git worktree in `trees/<adw_id>/`
- Creates git branch `<branch_name>`
- Writes plan file to `specs/` directory in worktree
- Allocates ports in `agents/port_allocations.json`
- Creates `.ports.env` in worktree
- Creates state file `agents/<adw_id>/adw_state.json`

**Validation Rules**:
- `issue_number` must be valid GitHub issue
- `plan_file` path must exist after execution
- `worktree_path` must be valid directory
- `backend_port` and `frontend_port` must be available

---

## Phase 2: VALIDATE

**Script**: `adws/adw_validate_iso.py`

**Requires**:
- `adw_id` (str) - From Phase 1
- `worktree_path` (str) - From Phase 1
- `plan_file` (str) - From Phase 1
- Worktree must exist and be clean (no modifications)

**Produces**:
- `baseline_errors` (dict) - Pre-existing errors before changes
  - `frontend.type_errors` (int)
  - `frontend.build_errors` (int)
  - `frontend.error_details` (list)
  - `backend.errors` (int) (if applicable)
  - `worktree_base_commit` (str) - Git commit hash at validation
  - `validation_timestamp` (str) - ISO timestamp

**Optional**:
- None

**Side Effects**:
- Runs build commands in worktree (read-only, no modifications)
- Updates state file with baseline_errors

**Validation Rules**:
- `worktree_path` must exist
- `plan_file` must exist
- Worktree must be on correct branch
- **NEVER FAILS** - Always captures baseline, even if errors exist

---

## Phase 3: BUILD

**Script**: `adws/adw_build_iso.py`

**Requires**:
- `adw_id` (str) - From Phase 1
- `plan_file` (str) - From Phase 1
- `worktree_path` (str) - From Phase 1
- `baseline_errors` (dict) - From Phase 2
- `backend_port` (int) - From Phase 1
- `frontend_port` (int) - From Phase 1

**Produces**:
- `external_build_results` (dict) - Build results after implementation
  - `new_errors` (int) - Errors introduced by implementation
  - `build_status` (str) - "success" or "failure"
  - `error_diff` (dict) - Comparison to baseline
- Modified files in worktree (implementation changes)
- Git commits with implementation

**Optional**:
- `issue_class` (str) - May influence implementation approach

**Side Effects**:
- Modifies files in worktree (AI agent makes code changes)
- Creates git commits in worktree branch
- Runs build commands to verify changes
- Updates state file with build_results

**Validation Rules**:
- `baseline_errors` must exist (to enable differential checking)
- `plan_file` must be readable
- Worktree must be writable
- New errors should not exceed baseline (warn if they do)

---

## Phase 4: LINT

**Script**: `adws/adw_lint_iso.py`

**Requires**:
- `adw_id` (str)
- `worktree_path` (str)
- Modified files from Phase 3

**Produces**:
- `lint_results` (dict) - Linting results
  - `files_checked` (int)
  - `issues_found` (int)
  - `issues_by_severity` (dict)

**Optional**:
- Linting configuration files in worktree

**Side Effects**:
- Runs linters on changed files
- May auto-fix some issues (if configured)
- Updates state file with lint_results

**Validation Rules**:
- Worktree must have committed changes
- Linters must be available

---

## Phase 5: TEST

**Script**: `adws/adw_test_iso.py`

**Requires**:
- `adw_id` (str)
- `worktree_path` (str)
- `backend_port` (int)
- `frontend_port` (int)
- Linted code from Phase 4

**Produces**:
- `test_results` (dict) - Test execution results
  - `tests_run` (int)
  - `tests_passed` (int)
  - `tests_failed` (int)
  - `coverage_percent` (float)

**Optional**:
- None

**Side Effects**:
- Runs test suite in worktree
- May start temporary services on allocated ports
- Updates state file with test_results

**Validation Rules**:
- Ports must be available
- Test framework must be configured
- Tests should pass (or document failures)

---

## Phase 6: REVIEW

**Script**: `adws/adw_review_iso.py`

**Requires**:
- `adw_id` (str)
- `branch_name` (str) - From Phase 1
- `issue_number` (int) - From Phase 1
- Tested code from Phase 5

**Produces**:
- `pr_url` (str) - GitHub pull request URL
- `review_results` (dict) - Code review results
  - `review_status` (str) - "approved", "changes_requested", etc.
  - `comments_count` (int)

**Optional**:
- None

**Side Effects**:
- Creates GitHub pull request
- May add review comments via API
- Updates state file with review_results

**Validation Rules**:
- Branch must exist on remote
- GitHub API access required
- PR should be created successfully

---

## Phase 7: DOCUMENT

**Script**: `adws/adw_document_iso.py`

**Requires**:
- `adw_id` (str)
- `plan_file` (str) - From Phase 1
- `worktree_path` (str)
- Implementation from Phase 3

**Produces**:
- `doc_files_paths` (list[str]) - Paths to generated documentation
- Documentation files in worktree `docs/` directory

**Optional**:
- `issue_class` (str) - May influence doc style

**Side Effects**:
- Creates/updates markdown files in docs/
- Commits documentation to branch
- Updates state file with doc_files_paths

**Validation Rules**:
- **NON-CRITICAL** - Failure does not block workflow
- Documentation is best-effort

---

## Phase 8: SHIP

**Script**: `adws/adw_ship_iso.py`

**Requires**:
- `adw_id` (str)
- `pr_url` (str) - From Phase 6
- `branch_name` (str) - From Phase 1
- Reviewed code from Phase 6

**Produces**:
- `shipped_at` (str) - ISO timestamp of merge
- `merge_commit_sha` (str) - Git commit hash on main

**Optional**:
- None

**Side Effects**:
- **CRITICAL**: Merges PR to main branch (PRODUCTION DEPLOYMENT)
- Deletes worktree branch (after merge)
- Updates state file with shipped_at

**Validation Rules**:
- PR must exist and be approved
- No merge conflicts
- **POINT OF NO RETURN** - Cannot undo after merge

---

## Phase 9: CLEANUP

**Script**: `adws/cleanup_operations.py`

**Requires**:
- `adw_id` (str)
- `worktree_path` (str) - From Phase 1
- Shipped code from Phase 8

**Produces**:
- `cleanup_summary` (dict) - Cleanup results
  - `worktree_removed` (bool)
  - `ports_released` (bool)
  - `docs_organized` (bool)

**Optional**:
- `doc_files_paths` (list) - From Phase 7

**Side Effects**:
- Removes git worktree
- Releases allocated ports
- Organizes documentation files
- Updates state file with cleanup_summary

**Validation Rules**:
- **NEVER FAILS** - Best-effort cleanup
- Pure Python operations (no AI calls)

---

## Phase 10: VERIFY

**Script**: `adws/adw_verify_iso.py`

**Requires**:
- `adw_id` (str)
- `issue_number` (int) - From Phase 1
- `merge_commit_sha` (str) - From Phase 8
- Shipped code (already in production)

**Produces**:
- `verification_results` (dict) - Post-deployment checks
  - `health_checks_passed` (bool)
  - `functionality_verified` (bool)
  - `issues_found` (list)

**Optional**:
- None

**Side Effects**:
- Runs health checks on production
- May create follow-up GitHub issue if problems found
- Updates state file with verification_results

**Validation Rules**:
- **DOES NOT REVERT CODE** - Shipped is shipped
- Failure creates follow-up issue for manual review

---

## State Boundaries

### Database (Coordination State)
**Table**: `phase_queue`

**Fields**:
- `queue_id` (int, PK) - Unique queue entry
- `parent_issue` (int) - GitHub issue number
- `phase_number` (int) - Phase in sequence (1-10)
- `status` (str) - Current status (queued, ready, running, completed, failed, blocked)
- `adw_id` (str) - Associated workflow ID
- `issue_number` (int) - Phase-specific GitHub issue
- `depends_on_phase` (int) - Dependency tracking
- `phase_data` (jsonb) - Phase metadata
- Timestamps: created_at, ready_timestamp, started_timestamp

**Purpose**: Multi-phase coordination, dependency tracking, status transitions

### File System (Workflow Metadata)
**File**: `agents/<adw_id>/adw_state.json`

**Fields**: All phase-specific outputs (plan_file, baseline_errors, build_results, etc.)

**Purpose**: Execution context, phase outputs, workflow-specific data

---

## Dependency Graph

```
Phase 1 (Plan) → produces: adw_id, plan_file, worktree_path, ports
    ↓
Phase 2 (Validate) → requires: worktree_path, plan_file
                   → produces: baseline_errors
    ↓
Phase 3 (Build) → requires: plan_file, baseline_errors, ports
                → produces: external_build_results, modified files
    ↓
Phase 4 (Lint) → requires: worktree_path, modified files
               → produces: lint_results
    ↓
Phase 5 (Test) → requires: worktree_path, ports
               → produces: test_results
    ↓
Phase 6 (Review) → requires: branch_name, issue_number
                 → produces: pr_url, review_results
    ↓
Phase 7 (Document) → requires: plan_file, worktree_path
                   → produces: doc_files_paths
    ↓
Phase 8 (Ship) → requires: pr_url, branch_name
               → produces: shipped_at, merge_commit_sha
    ↓
Phase 9 (Cleanup) → requires: worktree_path
                  → produces: cleanup_summary
    ↓
Phase 10 (Verify) → requires: merge_commit_sha, issue_number
                  → produces: verification_results
```

---

## Validation Checklist Template

Use this for each phase:

```python
def validate_phase_X_inputs(state: dict) -> None:
    """Validate inputs for Phase X before execution.

    Raises:
        ValueError: If required fields missing or invalid
    """
    # Check required fields exist
    required = ['field1', 'field2', 'field3']
    missing = [f for f in required if f not in state or state[f] is None]
    if missing:
        raise ValueError(f"Phase X missing required inputs: {missing}")

    # Validate field types
    assert isinstance(state['adw_id'], str), "adw_id must be string"

    # Validate file paths exist
    if 'plan_file' in required:
        plan_file = state['plan_file']
        if not os.path.exists(plan_file):
            raise ValueError(f"Plan file not found: {plan_file}")

    # Phase-specific validation
    # ...
```
```

### Step 1.2: Add Contract Docstrings to Phase Scripts

For each phase script, add comprehensive docstring at top:

**Example:** `adws/adw_plan_iso.py`

```python
"""
Phase 1: PLAN - Generate implementation plan and setup worktree

CONTRACT:
    Requires:
        - issue_number (int): GitHub issue to plan for
        - Environment: GitHub API access, git repository

    Produces:
        - adw_id (str): Unique workflow identifier
        - plan_file (str): Path to generated plan markdown
        - branch_name (str): Git branch for this workflow
        - worktree_path (str): Isolated worktree directory
        - issue_class (str): Classified issue type
        - backend_port (int): Allocated backend port (9100-9114)
        - frontend_port (int): Allocated frontend port (9200-9214)
        - status (str): Workflow status
        - current_phase (str): Current phase name
        - workflow_template (str): Template name

    Side Effects:
        - Creates git worktree in trees/<adw_id>/
        - Creates git branch
        - Writes plan file to specs/
        - Allocates ports in agents/port_allocations.json
        - Creates .ports.env in worktree
        - Creates state file agents/<adw_id>/adw_state.json

    Validation:
        - issue_number must be valid GitHub issue
        - plan_file path must exist after execution
        - worktree_path must be valid directory
        - Ports must be available
"""
```

Repeat for all 10 phase scripts.

### Step 1.3: Commit Documentation

```bash
git add docs/architecture/phase-contracts.md
git add adws/adw_plan_iso.py  # (and all other phase scripts with updated docstrings)

git commit -m "$(cat <<'EOF'
docs: Document explicit phase input/output contracts

Comprehensive documentation of data flow through 10-phase SDLC workflow.

Created:
- docs/architecture/phase-contracts.md
  - Defines REQUIRES and PRODUCES for each phase
  - Documents side effects and validation rules
  - Shows dependency graph
  - Establishes state boundaries (DB vs files)

Updated:
- All 10 phase scripts with contract docstrings
- Clear expectations for phase inputs and outputs

Benefits:
- Developers understand phase dependencies
- Validation can be automated
- State divergence issues identifiable
- Foundation for idempotent execution

Session 19 - Phase 2, Part 1/4

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## PART 2: Define Single Source of Truth

### Step 2.1: Create State Management Architecture Doc

**File:** `docs/architecture/state-management.md` (NEW)

```markdown
# State Management Architecture

## Principle: Separation of Concerns

The tac-webbuilder system uses a **dual-state architecture** with clear boundaries:

1. **Database (PostgreSQL)** - Coordination State
2. **File System (JSON)** - Workflow Metadata

---

## Database: Coordination State

**Purpose**: Multi-workflow coordination, phase transitions, dependency tracking

**Table**: `phase_queue`

**Authoritative For**:
- Phase status (queued, ready, running, completed, failed, blocked)
- Queue position and dependencies
- Cross-workflow coordination
- Phase triggers and transitions

**When to Use Database**:
- Does this affect OTHER workflows? → Database
- Is this about phase SEQUENCING? → Database
- Is this coordination STATE? → Database

**Example Fields**:
```sql
queue_id INT PRIMARY KEY
parent_issue INT
phase_number INT
status VARCHAR  -- ← AUTHORITATIVE
adw_id VARCHAR
depends_on_phase INT
```

---

## File System: Workflow Metadata

**Purpose**: Execution context, phase outputs, workflow-specific data

**File**: `agents/<adw_id>/adw_state.json`

**Authoritative For**:
- Plan file paths
- Worktree paths
- Port allocations (specific to this workflow)
- Phase outputs (baseline_errors, build_results, etc.)
- Execution metadata

**When to Use Files**:
- Is this workflow-SPECIFIC context? → File
- Is this EXECUTION metadata? → File
- Does this affect ONLY this workflow? → File

**Example Fields**:
```json
{
  "adw_id": "adw-abc123",  // ← AUTHORITATIVE (workflow identity)
  "plan_file": "/path/to/plan.md",  // ← AUTHORITATIVE (execution context)
  "worktree_path": "/path/to/worktree",  // ← AUTHORITATIVE
  "baseline_errors": {...},  // ← AUTHORITATIVE (phase output)
  "status": "running"  // ← DUPLICATE (database is authoritative)
}
```

---

## Overlap Fields (MUST BE ELIMINATED)

**Current Duplicates**:

| Field | Database | File | Authoritative Source | Action |
|-------|----------|------|---------------------|--------|
| adw_id | ✓ | ✓ | **File** (workflow identity) | Keep in DB as FK only |
| status | ✓ | ✓ | **Database** (coordination) | Remove from file |
| current_phase | ✗ | ✓ | **Database** (via phase_number) | Remove from file |
| issue_number | ✓ | ✓ | **Database** (via parent_issue) | Keep in file for context only |

---

## State Update Patterns

### Pattern 1: Phase Transition (Database Update)

```python
# CORRECT: Update database for status transitions
phase_queue_service.update_status(queue_id, "completed")

# WRONG: Don't update status in file
# state.update(status="completed")  # ← Remove this
```

### Pattern 2: Phase Output (File Update)

```python
# CORRECT: Store phase outputs in file
state.update(baseline_errors=baseline)
state.save("validation_complete")

# WRONG: Don't store large outputs in database
# phase_queue_service.update_data(queue_id, baseline_errors=baseline)
```

### Pattern 3: Read Coordination State

```python
# CORRECT: Read status from database
phase = phase_queue_repository.find_by_id(queue_id)
if phase.status == "ready":
    # Execute phase

# WRONG: Don't read status from file
# if state.get("status") == "ready":  # ← Stale!
```

### Pattern 4: Read Execution Context

```python
# CORRECT: Read execution metadata from file
state = ADWState.load(adw_id)
plan_file = state.get("plan_file")

# WRONG: Don't store plan paths in database
# phase = phase_queue_repository.find_by_id(queue_id)
# plan_file = phase.phase_data.get("plan_file")  # ← Not coordination data
```

---

## Migration Plan

### Step 1: Identify Overlaps

Audit both state sources:
```bash
# Database fields
psql -c "\d phase_queue"

# File fields
cat agents/*/adw_state.json | jq 'keys'

# Find overlaps
comm -12 <(db_fields) <(file_fields)
```

### Step 2: Choose Authoritative Source

For each overlap, ask:
1. Does this affect other workflows? → Database
2. Is this workflow-specific? → File
3. Is this coordination vs execution? → Database vs File

### Step 3: Remove Duplicates

**Remove from ADWState (file)**:
- `status` field (use database)
- `current_phase` field (use database phase_number)

**Remove from phase_queue (database)**:
- Large phase outputs (keep in file only)
- Execution paths (worktree_path, plan_file)

### Step 4: Update Access Patterns

```python
# Before (inconsistent)
state = ADWState.load(adw_id)
if state.get("status") == "completed":  # ← Stale
    ...

# After (consistent)
phase = phase_queue_repository.find_by_adw_id(adw_id)
if phase.status == "completed":  # ← Authoritative
    ...
```

---

## Enforcement

### Rule 1: No Status in Files

**Before**:
```python
state.update(status="completed")  # ← WRONG
```

**After**:
```python
# Files don't track status anymore
# Use database only
```

### Rule 2: No Large Data in Database

**Before**:
```python
phase_queue_service.update_data(
    queue_id,
    baseline_errors=large_dict  # ← WRONG (too large for DB)
)
```

**After**:
```python
# Store in file
state.update(baseline_errors=large_dict)
state.save("validation_complete")
```

### Rule 3: Single Update Per Boundary

**Before** (inconsistent):
```python
# Update both (can diverge if one fails)
phase_queue_service.update_status(queue_id, "completed")
state.update(status="completed")  # ← WRONG (duplicate)
```

**After** (consistent):
```python
# Update database only for status
phase_queue_service.update_status(queue_id, "completed")

# Update file only for outputs
state.update(build_results=results)
state.save("build_complete")
```

---

## Benefits

✅ **Clarity**: One source of truth per field
✅ **Consistency**: No divergence between DB and files
✅ **Performance**: Database for queries, files for large data
✅ **Reliability**: Atomic updates within each boundary
✅ **Scalability**: Database transactions, file writes independent

---

## Decision Tree

```
Need to update state?
    ↓
Does this affect other workflows?
    ↓ YES                  ↓ NO
    Database          Is this large data (>1KB)?
                          ↓ YES        ↓ NO
                          File      Either (prefer file)
```
```

### Step 2.2: Modify ADWState Class to Remove Duplicates

**File:** `adws/adw_modules/state.py`

**Find status/current_phase tracking** and remove:

```python
# BEFORE (incorrect - tracks status in file)
class ADWState:
    def __init__(self, adw_id: str):
        self.data = {
            "adw_id": adw_id,
            "status": "initializing",  # ← REMOVE
            "current_phase": None,  # ← REMOVE
        }

    def update_status(self, status: str):  # ← REMOVE THIS METHOD
        """Update workflow status."""
        self.data["status"] = status
        self.save("status_update")

# AFTER (correct - no status tracking)
class ADWState:
    def __init__(self, adw_id: str):
        self.data = {
            "adw_id": adw_id,
            # Status removed - use database instead
        }

    # update_status method removed
```

### Step 2.3: Update Phase Scripts to Use Database for Status

**Example:** `adws/adw_plan_iso.py`

```python
# BEFORE (writes status to file)
state.update(status="running", current_phase="Plan")
state.save("phase_started")

# AFTER (no status in file - database handles it)
# Status is managed by phase_queue table
# File only tracks execution metadata
state.save("phase_started")
```

### Step 2.4: Add Helper Methods for Clear Access

**File:** `adws/adw_modules/state.py`

Add comment block:

```python
class ADWState:
    """
    Workflow Execution Metadata (File-based State)

    BOUNDARY RULE:
    - This class manages EXECUTION CONTEXT only
    - Status/coordination managed by phase_queue table (database)
    - Do NOT track: status, current_phase, phase_number
    - DO track: plan paths, worktree paths, phase outputs

    See: docs/architecture/state-management.md
    """
```

### Step 2.5: Test State Separation

```bash
cd app/server

# Verify no status in state files
cat agents/*/adw_state.json | jq '.status'
# Should return: null or missing

# Verify status in database
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme PGPASSWORD=changeme psql -h localhost -U tac_user -d tac_webbuilder -c "SELECT adw_id, status FROM phase_queue LIMIT 5;"
# Should return: adw_id and status columns
```

### Step 2.6: Commit Changes

```bash
git add docs/architecture/state-management.md
git add adws/adw_modules/state.py
git add adws/adw_plan_iso.py  # (and other phases with status removal)

git commit -m "$(cat <<'EOF'
refactor: Define single source of truth for state management

Established clear boundaries between database and file system state.

Architecture Changes:
- Database: Coordination state (status, phase_number, dependencies)
- Files: Execution metadata (paths, outputs, context)
- Removed duplicate status tracking from ADWState

Documentation:
- Created docs/architecture/state-management.md
- Defines when to use database vs files
- Documents migration plan and enforcement rules
- Provides decision tree for state updates

Code Changes:
- Removed status field from ADWState class
- Removed current_phase field from ADWState
- Updated phase scripts to not write status to files
- Added boundary comments to ADWState class

Benefits:
- Single source of truth for each field
- No divergence between database and files
- Clear ownership of state data
- Foundation for atomic updates

Session 19 - Phase 2, Part 2/4

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## PART 3: Add State Validation Middleware

### Step 3.1: Create State Validator Module

**File:** `adws/adw_modules/state_validator.py` (NEW)

```python
"""
State validation middleware for ADW phases.

Validates that required state fields exist and are valid before phase execution.
Uses contracts defined in docs/architecture/phase-contracts.md
"""
import os
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class StateValidationError(Exception):
    """Raised when state validation fails."""
    pass


# Phase Contracts: Define required fields for each phase
PHASE_CONTRACTS = {
    "Plan": {
        "requires": ["issue_number"],
        "produces": [
            "adw_id", "plan_file", "branch_name", "worktree_path",
            "issue_class", "backend_port", "frontend_port",
            "workflow_template"
        ],
        "file_paths": [],  # No file paths required before Plan
    },
    "Validate": {
        "requires": ["adw_id", "worktree_path", "plan_file"],
        "produces": ["baseline_errors"],
        "file_paths": ["worktree_path", "plan_file"],
    },
    "Build": {
        "requires": [
            "adw_id", "plan_file", "worktree_path", "baseline_errors",
            "backend_port", "frontend_port"
        ],
        "produces": ["external_build_results"],
        "file_paths": ["worktree_path", "plan_file"],
    },
    "Lint": {
        "requires": ["adw_id", "worktree_path"],
        "produces": ["lint_results"],
        "file_paths": ["worktree_path"],
    },
    "Test": {
        "requires": ["adw_id", "worktree_path", "backend_port", "frontend_port"],
        "produces": ["test_results"],
        "file_paths": ["worktree_path"],
    },
    "Review": {
        "requires": ["adw_id", "branch_name", "issue_number"],
        "produces": ["pr_url", "review_results"],
        "file_paths": [],
    },
    "Document": {
        "requires": ["adw_id", "plan_file", "worktree_path"],
        "produces": ["doc_files_paths"],
        "file_paths": ["plan_file", "worktree_path"],
    },
    "Ship": {
        "requires": ["adw_id", "pr_url", "branch_name"],
        "produces": ["shipped_at", "merge_commit_sha"],
        "file_paths": [],
    },
    "Cleanup": {
        "requires": ["adw_id", "worktree_path"],
        "produces": ["cleanup_summary"],
        "file_paths": ["worktree_path"],
    },
    "Verify": {
        "requires": ["adw_id", "issue_number", "merge_commit_sha"],
        "produces": ["verification_results"],
        "file_paths": [],
    },
}


class StateValidator:
    """Validates workflow state before phase execution."""

    def __init__(self, phase_name: str):
        """
        Initialize validator for specific phase.

        Args:
            phase_name: Name of phase to validate (e.g., "Plan", "Build")

        Raises:
            ValueError: If phase_name not recognized
        """
        if phase_name not in PHASE_CONTRACTS:
            raise ValueError(
                f"Unknown phase: {phase_name}. "
                f"Valid phases: {list(PHASE_CONTRACTS.keys())}"
            )

        self.phase_name = phase_name
        self.contract = PHASE_CONTRACTS[phase_name]

    def validate(self, state: Dict[str, Any]) -> None:
        """
        Validate state has all required fields for this phase.

        Args:
            state: State dictionary (from ADWState.data)

        Raises:
            StateValidationError: If validation fails
        """
        errors = []

        # Check required fields exist
        missing_fields = self._check_required_fields(state)
        if missing_fields:
            errors.append(f"Missing required fields: {missing_fields}")

        # Validate field types
        type_errors = self._check_field_types(state)
        if type_errors:
            errors.extend(type_errors)

        # Validate file paths exist
        path_errors = self._check_file_paths(state)
        if path_errors:
            errors.extend(path_errors)

        # Raise if any errors
        if errors:
            error_msg = f"State validation failed for phase '{self.phase_name}':\n"
            error_msg += "\n".join(f"  - {err}" for err in errors)
            raise StateValidationError(error_msg)

        logger.info(f"[STATE_VALIDATOR] Phase '{self.phase_name}' validation passed")

    def _check_required_fields(self, state: Dict[str, Any]) -> List[str]:
        """Check that all required fields exist in state."""
        required = self.contract["requires"]
        missing = []

        for field in required:
            if field not in state or state[field] is None:
                missing.append(field)

        return missing

    def _check_field_types(self, state: Dict[str, Any]) -> List[str]:
        """Validate types of known fields."""
        errors = []

        # Type validations
        type_checks = {
            "adw_id": str,
            "issue_number": int,
            "plan_file": str,
            "worktree_path": str,
            "branch_name": str,
            "backend_port": int,
            "frontend_port": int,
            "baseline_errors": dict,
            "external_build_results": dict,
        }

        for field, expected_type in type_checks.items():
            if field in state and state[field] is not None:
                if not isinstance(state[field], expected_type):
                    errors.append(
                        f"Field '{field}' has wrong type: "
                        f"expected {expected_type.__name__}, "
                        f"got {type(state[field]).__name__}"
                    )

        return errors

    def _check_file_paths(self, state: Dict[str, Any]) -> List[str]:
        """Validate that file/directory paths exist."""
        errors = []

        for field in self.contract["file_paths"]:
            if field not in state:
                continue

            path = state[field]
            if not os.path.exists(path):
                errors.append(f"Path does not exist: {field}={path}")

        return errors

    def validate_outputs(self, state: Dict[str, Any]) -> None:
        """
        Validate that phase produced required outputs.

        Args:
            state: State dictionary after phase execution

        Raises:
            StateValidationError: If required outputs missing
        """
        produces = self.contract["produces"]
        missing = []

        for field in produces:
            if field not in state or state[field] is None:
                missing.append(field)

        if missing:
            raise StateValidationError(
                f"Phase '{self.phase_name}' did not produce required outputs: {missing}"
            )

        logger.info(f"[STATE_VALIDATOR] Phase '{self.phase_name}' outputs validated")


def validate_phase_inputs(phase_name: str, state: Dict[str, Any]) -> None:
    """
    Convenience function to validate state before phase execution.

    Args:
        phase_name: Name of phase (e.g., "Build")
        state: State dictionary from ADWState.data

    Raises:
        StateValidationError: If validation fails

    Example:
        >>> from adw_modules.state import ADWState
        >>> from adw_modules.state_validator import validate_phase_inputs
        >>>
        >>> state = ADWState.load(adw_id)
        >>> validate_phase_inputs("Build", state.data)
        >>> # Phase execution here
    """
    validator = StateValidator(phase_name)
    validator.validate(state)


def validate_phase_outputs(phase_name: str, state: Dict[str, Any]) -> None:
    """
    Convenience function to validate state after phase execution.

    Args:
        phase_name: Name of phase
        state: State dictionary after phase execution

    Raises:
        StateValidationError: If required outputs missing
    """
    validator = StateValidator(phase_name)
    validator.validate_outputs(state)
```

### Step 3.2: Add Validation to Phase Scripts

**Pattern to add to EVERY phase script:**

```python
# Add import at top
from adw_modules.state_validator import validate_phase_inputs, validate_phase_outputs, StateValidationError

# At start of main execution (after loading state)
def main():
    # ... existing setup ...

    state = ADWState.load(adw_id)

    # VALIDATE INPUTS BEFORE EXECUTION
    try:
        validate_phase_inputs("Build", state.data)  # Change phase name
    except StateValidationError as e:
        logger.error(f"[BUILD] State validation failed: {e}")
        sys.exit(1)

    # ... existing phase logic ...

    # After phase completes successfully
    state.update(external_build_results=results)  # Phase-specific output
    state.save("build_complete")

    # VALIDATE OUTPUTS AFTER EXECUTION
    try:
        validate_phase_outputs("Build", state.data)  # Change phase name
    except StateValidationError as e:
        logger.error(f"[BUILD] Output validation failed: {e}")
        sys.exit(1)
```

**Apply to all 10 phases:**
- adw_plan_iso.py
- adw_validate_iso.py
- adw_build_iso.py
- adw_lint_iso.py
- adw_test_iso.py
- adw_review_iso.py
- adw_document_iso.py
- adw_ship_iso.py
- cleanup_operations.py
- adw_verify_iso.py

### Step 3.3: Test Validation

Create test file: `adws/tests/test_state_validator.py`

```python
import pytest
from adw_modules.state_validator import StateValidator, StateValidationError, PHASE_CONTRACTS


def test_validate_plan_inputs():
    """Test Plan phase validation."""
    validator = StateValidator("Plan")

    # Valid state
    state = {"issue_number": 123}
    validator.validate(state)  # Should not raise

    # Missing issue_number
    with pytest.raises(StateValidationError, match="Missing required fields"):
        validator.validate({})


def test_validate_build_inputs():
    """Test Build phase validation."""
    validator = StateValidator("Build")

    # Valid state
    state = {
        "adw_id": "adw-test123",
        "plan_file": "/tmp/plan.md",  # Won't exist, will fail path check
        "worktree_path": "/tmp/worktree",
        "baseline_errors": {},
        "backend_port": 9100,
        "frontend_port": 9200,
    }

    # Will fail due to missing files (expected in test)
    with pytest.raises(StateValidationError, match="Path does not exist"):
        validator.validate(state)


def test_phase_contracts_complete():
    """Verify all 10 phases have contracts."""
    expected_phases = [
        "Plan", "Validate", "Build", "Lint", "Test",
        "Review", "Document", "Ship", "Cleanup", "Verify"
    ]

    for phase in expected_phases:
        assert phase in PHASE_CONTRACTS, f"Missing contract for {phase}"
        assert "requires" in PHASE_CONTRACTS[phase]
        assert "produces" in PHASE_CONTRACTS[phase]
```

Run tests:
```bash
cd adws
pytest tests/test_state_validator.py -v
```

### Step 3.4: Commit Validation Middleware

```bash
git add adws/adw_modules/state_validator.py
git add adws/tests/test_state_validator.py
git add adws/adw_plan_iso.py  # (and all other phases with validation added)

git commit -m "$(cat <<'EOF'
feat: Add state validation middleware for phases

Centralized validation ensures required state exists before phase execution.

Created:
- adws/adw_modules/state_validator.py
  - StateValidator class with phase-specific validation
  - PHASE_CONTRACTS defining required/produced fields
  - File path existence validation
  - Type checking for known fields

- adws/tests/test_state_validator.py
  - Unit tests for all validation logic

Updated:
- All 10 phase scripts with input/output validation
- Validates before execution (fail fast)
- Validates after execution (ensures outputs created)

Benefits:
- Fail fast with clear error messages
- Prevents cryptic mid-phase failures
- Documents dependencies in code
- Foundation for idempotent execution

Error Examples:
- "Missing required fields: ['plan_file', 'baseline_errors']"
- "Path does not exist: worktree_path=/invalid/path"
- "Field 'backend_port' has wrong type: expected int, got str"

Session 19 - Phase 2, Part 3/4

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## PART 4: Implement Idempotent Phase Execution

This is the largest and most complex part (12 hours estimated).

### Step 4.1: Create Idempotency Module

**File:** `adws/adw_modules/idempotency.py` (NEW)

```python
"""
Idempotency utilities for ADW phases.

Makes phases safely re-runnable: same input → same output
Enables crash recovery and safe retries.
"""
import os
import hashlib
import json
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class IdempotencyChecker:
    """Checks if phase has already been completed and outputs are valid."""

    def __init__(self, adw_id: str, phase_name: str):
        """
        Initialize idempotency checker.

        Args:
            adw_id: Workflow ID
            phase_name: Name of phase to check
        """
        self.adw_id = adw_id
        self.phase_name = phase_name

    def is_completed(
        self,
        state: Dict[str, Any],
        required_outputs: list[str]
    ) -> bool:
        """
        Check if phase has already completed successfully.

        Args:
            state: Current state dictionary
            required_outputs: List of fields this phase should produce

        Returns:
            True if all outputs exist and are valid, False otherwise
        """
        # Check all required outputs exist
        for output in required_outputs:
            if output not in state or state[output] is None:
                logger.info(
                    f"[IDEMPOTENCY] Phase '{self.phase_name}' not completed: "
                    f"missing output '{output}'"
                )
                return False

        logger.info(
            f"[IDEMPOTENCY] Phase '{self.phase_name}' already completed with valid outputs"
        )
        return True

    def validate_file_output(
        self,
        file_path: Optional[str],
        min_size_bytes: int = 0
    ) -> bool:
        """
        Validate that file output exists and is valid.

        Args:
            file_path: Path to file that should exist
            min_size_bytes: Minimum expected file size (0 for any size)

        Returns:
            True if file exists and meets criteria, False otherwise
        """
        if not file_path:
            return False

        if not os.path.exists(file_path):
            logger.warning(
                f"[IDEMPOTENCY] Output file missing: {file_path}"
            )
            return False

        file_size = os.path.getsize(file_path)
        if file_size < min_size_bytes:
            logger.warning(
                f"[IDEMPOTENCY] Output file too small: {file_path} "
                f"({file_size} < {min_size_bytes} bytes)"
            )
            return False

        logger.info(
            f"[IDEMPOTENCY] Output file valid: {file_path} ({file_size} bytes)"
        )
        return True

    def compute_input_hash(self, inputs: Dict[str, Any]) -> str:
        """
        Compute deterministic hash of phase inputs.

        Args:
            inputs: Dictionary of input values

        Returns:
            SHA256 hash of inputs (first 16 chars)
        """
        # Sort keys for determinism
        sorted_inputs = json.dumps(inputs, sort_keys=True)
        hash_obj = hashlib.sha256(sorted_inputs.encode())
        return hash_obj.hexdigest()[:16]


def make_phase_idempotent(
    phase_name: str,
    adw_id: str,
    state: Dict[str, Any],
    required_outputs: list[str],
    execution_func: Callable[[], Dict[str, Any]],
    file_outputs: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """
    Wrapper to make phase execution idempotent.

    Args:
        phase_name: Name of phase
        adw_id: Workflow ID
        state: Current state dictionary
        required_outputs: Fields this phase should produce
        execution_func: Function to execute phase (returns outputs dict)
        file_outputs: Optional dict of {output_field: min_file_size}

    Returns:
        Phase outputs (either from existing state or new execution)

    Example:
        >>> def execute_build():
        ...     # ... build logic ...
        ...     return {"external_build_results": {...}}
        >>>
        >>> outputs = make_phase_idempotent(
        ...     phase_name="Build",
        ...     adw_id=adw_id,
        ...     state=state.data,
        ...     required_outputs=["external_build_results"],
        ...     execution_func=execute_build
        ... )
    """
    checker = IdempotencyChecker(adw_id, phase_name)

    # Check if already completed
    if checker.is_completed(state, required_outputs):
        # Validate file outputs if specified
        if file_outputs:
            all_valid = True
            for output_field, min_size in file_outputs.items():
                file_path = state.get(output_field)
                if not checker.validate_file_output(file_path, min_size):
                    all_valid = False
                    break

            if not all_valid:
                logger.info(
                    f"[IDEMPOTENCY] Phase '{phase_name}' outputs invalid, re-executing"
                )
                # Fall through to re-execute
            else:
                # All valid, return existing outputs
                logger.info(
                    f"[IDEMPOTENCY] Phase '{phase_name}' skipped (already completed)"
                )
                return {field: state[field] for field in required_outputs}

        else:
            # No file validation needed, return existing outputs
            logger.info(
                f"[IDEMPOTENCY] Phase '{phase_name}' skipped (already completed)"
            )
            return {field: state[field] for field in required_outputs}

    # Not completed or invalid outputs, execute phase
    logger.info(f"[IDEMPOTENCY] Executing phase '{phase_name}'")
    return execution_func()


# Idempotent wrappers for specific phases

def idempotent_plan(
    issue_number: int,
    adw_id: str,
    state: Dict[str, Any],
    plan_func: Callable[[], Dict[str, Any]]
) -> Dict[str, Any]:
    """Idempotent wrapper for Plan phase."""
    return make_phase_idempotent(
        phase_name="Plan",
        adw_id=adw_id,
        state=state,
        required_outputs=[
            "adw_id", "plan_file", "branch_name", "worktree_path",
            "backend_port", "frontend_port"
        ],
        execution_func=plan_func,
        file_outputs={"plan_file": 100}  # Plan file should be >100 bytes
    )


def idempotent_validate(
    adw_id: str,
    state: Dict[str, Any],
    validate_func: Callable[[], Dict[str, Any]]
) -> Dict[str, Any]:
    """Idempotent wrapper for Validate phase."""
    return make_phase_idempotent(
        phase_name="Validate",
        adw_id=adw_id,
        state=state,
        required_outputs=["baseline_errors"],
        execution_func=validate_func
    )


def idempotent_build(
    adw_id: str,
    state: Dict[str, Any],
    build_func: Callable[[], Dict[str, Any]]
) -> Dict[str, Any]:
    """Idempotent wrapper for Build phase."""
    return make_phase_idempotent(
        phase_name="Build",
        adw_id=adw_id,
        state=state,
        required_outputs=["external_build_results"],
        execution_func=build_func
    )


# Add similar wrappers for other phases...
```

### Step 4.2: Refactor Phase Scripts for Idempotency

**Example:** `adws/adw_build_iso.py`

**Before (not idempotent):**
```python
def main():
    state = ADWState.load(adw_id)
    validate_phase_inputs("Build", state.data)

    # Execute build logic
    results = execute_build_logic(state)

    state.update(external_build_results=results)
    state.save("build_complete")

    validate_phase_outputs("Build", state.data)
```

**After (idempotent):**
```python
from adw_modules.idempotency import idempotent_build

def main():
    state = ADWState.load(adw_id)
    validate_phase_inputs("Build", state.data)

    # Define execution function
    def execute():
        results = execute_build_logic(state)
        return {"external_build_results": results}

    # Execute with idempotency check
    outputs = idempotent_build(adw_id, state.data, execute)

    # Update state with outputs (may be from cache or new execution)
    state.update(**outputs)
    state.save("build_complete")

    validate_phase_outputs("Build", state.data)
```

### Step 4.3: Apply to All Phases

**Phases to update:**
1. adw_plan_iso.py → idempotent_plan
2. adw_validate_iso.py → idempotent_validate
3. adw_build_iso.py → idempotent_build
4. adw_lint_iso.py → idempotent_lint
5. adw_test_iso.py → idempotent_test
6. adw_review_iso.py → idempotent_review
7. adw_document_iso.py → idempotent_document
8. adw_ship_iso.py → idempotent_ship
9. cleanup_operations.py → idempotent_cleanup
10. adw_verify_iso.py → idempotent_verify

### Step 4.4: Test Idempotency

**Manual test:**
```bash
# Run phase once
uv run adw_build_iso.py 123 adw-test123

# Run again (should skip execution)
uv run adw_build_iso.py 123 adw-test123
# Expected log: "[IDEMPOTENCY] Phase 'Build' skipped (already completed)"

# Corrupt output
rm agents/adw-test123/adw_state.json

# Run again (should re-execute)
uv run adw_build_iso.py 123 adw-test123
# Expected log: "[IDEMPOTENCY] Executing phase 'Build'"
```

### Step 4.5: Commit Idempotency Implementation

```bash
git add adws/adw_modules/idempotency.py
git add adws/adw_plan_iso.py  # (and all other phases)

git commit -m "$(cat <<'EOF'
feat: Implement idempotent phase execution

Make all 10 phases safely re-runnable with automatic output validation.

Created:
- adws/adw_modules/idempotency.py
  - IdempotencyChecker class
  - make_phase_idempotent wrapper
  - Phase-specific idempotent functions
  - File output validation
  - Input hash computation

Updated:
- All 10 phase scripts with idempotency wrappers
- Phases check if already completed before execution
- Validates existing outputs, re-executes if invalid
- Enables crash recovery without manual intervention

How It Works:
1. Check if phase already completed (required outputs exist)
2. Validate file outputs if applicable (size, existence)
3. If valid: Skip execution, return cached outputs
4. If invalid/missing: Execute phase, produce new outputs

Benefits:
- Safe retries after crashes
- Automatic recovery from failures
- Prevents duplicate work
- Deterministic execution (same input → same output)
- Graceful handling of corrupted outputs

Example:
- First run: Executes phase, produces outputs
- Second run: Skips execution, uses cached outputs
- After corruption: Detects invalid outputs, re-executes

Session 19 - Phase 2, Part 4/4

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## Success Criteria - Phase 2 Complete

After completing all 4 parts, verify:

### Part 1: Phase Contracts Documentation
- ✅ docs/architecture/phase-contracts.md created
- ✅ All 10 phases documented with REQUIRES and PRODUCES
- ✅ Dependency graph visualized
- ✅ Contract docstrings added to all phase scripts

### Part 2: Single Source of Truth
- ✅ docs/architecture/state-management.md created
- ✅ Boundaries defined (database vs files)
- ✅ Status/current_phase removed from ADWState
- ✅ No duplicate state tracking
- ✅ Clear decision tree for state updates

### Part 3: State Validation Middleware
- ✅ adws/adw_modules/state_validator.py created
- ✅ PHASE_CONTRACTS defined for all 10 phases
- ✅ Input validation added to all phases
- ✅ Output validation added to all phases
- ✅ Tests passing for validation logic

### Part 4: Idempotent Phases
- ✅ adws/adw_modules/idempotency.py created
- ✅ All 10 phases refactored with idempotency wrappers
- ✅ File output validation implemented
- ✅ Phases skip execution if already completed
- ✅ Manual test confirms idempotency works

### Overall Phase 2 Verification

```bash
# Verify documentation exists
ls -la docs/architecture/phase-contracts.md
ls -la docs/architecture/state-management.md

# Verify no status in state files
grep -r '"status"' agents/*/adw_state.json || echo "No status in state files ✓"

# Verify validation module works
cd adws && pytest tests/test_state_validator.py -v

# Test idempotency manually
uv run adw_plan_iso.py 123  # First run
uv run adw_plan_iso.py 123  # Second run (should skip)
```

---

## Files Modified Summary

**Created (4 new files):**
- `docs/architecture/phase-contracts.md` - Phase input/output documentation
- `docs/architecture/state-management.md` - State boundaries documentation
- `adws/adw_modules/state_validator.py` - Validation middleware
- `adws/adw_modules/idempotency.py` - Idempotency utilities

**Modified (13 files):**
- `adws/adw_modules/state.py` - Removed status tracking
- All 10 phase scripts - Added validation + idempotency
- `adws/tests/test_state_validator.py` - Validation tests

---

## Return Summary Template

After completing Phase 2, return to Session 19 main chat with this summary:

```
# Session 19 - Phase 2 Implementation Summary

## Completed Tasks

**Part 1: Phase Contracts Documentation (4 hours)**
- ✅ Created docs/architecture/phase-contracts.md
- ✅ Documented all 10 phases with REQUIRES/PRODUCES
- ✅ Added dependency graph visualization
- ✅ Updated phase scripts with contract docstrings

**Part 2: Single Source of Truth (6 hours)**
- ✅ Created docs/architecture/state-management.md
- ✅ Defined clear boundaries (DB for coordination, files for metadata)
- ✅ Removed duplicate status tracking from ADWState
- ✅ Established decision tree for state updates

**Part 3: State Validation Middleware (5 hours)**
- ✅ Created adws/adw_modules/state_validator.py
- ✅ Defined PHASE_CONTRACTS for all 10 phases
- ✅ Added input/output validation to all phases
- ✅ Unit tests passing

**Part 4: Idempotent Phases (12 hours)**
- ✅ Created adws/adw_modules/idempotency.py
- ✅ Refactored all 10 phases with idempotency wrappers
- ✅ File output validation implemented
- ✅ Crash recovery enabled
- ✅ Manual tests confirm safe re-execution

## Issues Encountered
[List any issues and how they were resolved]

## Test Results
- Validation tests: PASS
- Idempotency tests: PASS (manual verification)
- All phases: Safe to re-run

## Architecture Impact
- State divergence risk: ELIMINATED
- Clear separation: Database vs Files
- Fail-fast validation: Prevents cryptic errors
- Crash recovery: ENABLED (automatic)

## Files Modified
- Created: 4 new files (docs + modules)
- Modified: 13 existing files (state.py + 10 phases + tests)
- Total commits: 4 (one per part)

## Ready for Phase 3
Phase 2 complete and meets expectations. State management is now clear, validated, and resilient. Ready to proceed with Phase 3: Code Quality & Consistency.
```

---

**End of Phase 2 Implementation Guide**
