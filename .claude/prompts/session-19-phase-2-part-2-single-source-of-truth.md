# Task: Define Single Source of Truth for ADW State

## Context
I'm working on the tac-webbuilder project. Phase 2 of Session 19 addresses dual-state management issues. This is Part 2 of 4 - establishing clear boundaries between database and file-based state tracking.

## Objective
Eliminate dual-state management by defining clear rules for when to use database vs. files, removing duplicate state tracking, and documenting the Single Source of Truth (SSoT) architecture.

## Background Information
- **Files:** `adws/adw_state.json`, `app/server/repositories/phase_queue_repository.py`, all phase scripts
- **Current Problem:** State tracked in BOTH database (phase_queue table) and files (adw_state.json), causing divergence
- **Target Solution:** Clear SSoT rules - Database for coordination, Files for metadata
- **Risk Level:** Medium (architectural change, requires careful migration)
- **Estimated Time:** 6 hours
- **Prerequisite:** Issue #1 complete (phase contracts documented)

## Current Problem

### Duplicate State Tracking

**Database (`phase_queue` table):**
```sql
CREATE TABLE phase_queue (
    queue_id INTEGER PRIMARY KEY,
    issue_number INTEGER,
    status TEXT,              -- ⚠️ DUPLICATE
    current_phase TEXT,       -- ⚠️ DUPLICATE
    parent_issue INTEGER,
    assigned_to TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**File (`adw_state.json`):**
```json
{
  "adw_id": 5,
  "issue_number": 123,
  "status": "testing",       // ⚠️ DUPLICATE
  "current_phase": "test",   // ⚠️ DUPLICATE
  "worktree_path": "trees/adw-5",
  "ports": {"backend": 9104, "frontend": 9204},
  "started_at": "2025-12-10T10:00:00Z",
  "plan_path": "SDLC_PLAN.md"
}
```

**Problems:**
1. Two sources of truth for `status` and `current_phase`
2. Updates can diverge (DB updated but file not, or vice versa)
3. Race conditions when both are updated
4. Unclear which to trust when they disagree

## Target Solution

### Single Source of Truth Architecture

**Database = Coordination State** (shared across system)
- Workflow status (queued, running, completed, failed)
- Current phase (plan, build, test, etc.)
- Assignment (which ADW is handling this)
- Timing (created_at, updated_at)
- **Used by:** Dashboard, queue management, API endpoints

**Files = Execution Metadata** (local to worktree)
- Worktree path
- Port allocation
- File locations (SDLC_PLAN.md path, etc.)
- Phase-specific outputs
- **Used by:** Phase scripts, orchestrator

### Decision Tree

```
Need to know workflow status/phase? → Database
Need to know where files are? → adw_state.json
Need to coordinate across ADWs? → Database
Need metadata for current execution? → adw_state.json
Need to show in dashboard? → Database
Need to pass to next phase? → adw_state.json
```

## Step-by-Step Instructions

### Step 1: Analyze Current State Usage

```bash
cd adws/

# Find all places where status is read from database
grep -rn "status.*=" . | grep -v "__pycache__" | grep -i "queue"

# Find all places where status is read from adw_state.json
grep -rn "adw_state\[.*status" . | grep -v "__pycache__"

# Find all places where current_phase is used
grep -rn "current_phase" . | grep -v "__pycache__"

# Document conflicts and duplicates
```

### Step 2: Create SSoT Documentation

Create `docs/adw/state-management-ssot.md`:

```markdown
# ADW State Management - Single Source of Truth

## Architecture Principle

**Database** = Coordination State (shared, authoritative)
**Files** = Execution Metadata (local, supporting)

## Database Schema (Source of Truth for Coordination)

### `phase_queue` table
```sql
CREATE TABLE phase_queue (
    queue_id INTEGER PRIMARY KEY,
    issue_number INTEGER NOT NULL,
    status TEXT NOT NULL,           -- SSoT for workflow status
    current_phase TEXT NOT NULL,    -- SSoT for current phase
    parent_issue INTEGER,
    assigned_to TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
```

**Authoritative for:**
- ✅ Workflow status: queued, running, completed, failed, blocked
- ✅ Current phase: plan, validate, build, lint, test, review, document, ship, cleanup, verify
- ✅ Assignment: which ADW ID is handling this
- ✅ Timing: when workflow started, last updated, completed
- ✅ Coordination: parent/child relationships

**Not responsible for:**
- ❌ File locations (worktree path, plan path)
- ❌ Port allocations
- ❌ Phase-specific outputs
- ❌ Execution metadata

**Update Rules:**
- Update via `PhaseQueueRepository` only
- Always update `updated_at` timestamp
- Use transactions for multi-field updates
- Validate before update (valid status transitions)

## File Schema (Supporting Metadata for Execution)

### `adw_state.json`
```json
{
  "adw_id": 5,
  "issue_number": 123,
  "worktree_path": "trees/adw-5",
  "ports": {
    "backend": 9104,
    "frontend": 9204
  },
  "started_at": "2025-12-10T10:00:00Z",
  "plan_path": "SDLC_PLAN.md",
  "phase_outputs": {
    "plan": {"path": "SDLC_PLAN.md", "completed_at": "..."},
    "build": {"files_changed": 5, "completed_at": "..."}
  }
}
```

**Authoritative for:**
- ✅ Worktree location
- ✅ Port allocations (backend, frontend)
- ✅ File paths (plan, outputs)
- ✅ Phase-specific metadata
- ✅ Execution environment details

**Not responsible for:**
- ❌ Workflow status (use database)
- ❌ Current phase (use database)
- ❌ Coordination across ADWs

**Update Rules:**
- Update via helper functions in each phase
- Atomic writes (write to temp, then rename)
- No status or current_phase fields

## State Access Patterns

### Reading State

**From Dashboard/API:**
```python
# ✅ CORRECT: Read coordination state from database
from repositories.phase_queue_repository import PhaseQueueRepository

repo = PhaseQueueRepository()
workflow = repo.find_by_issue_number(123)
status = workflow.status          # SSoT
current_phase = workflow.current_phase  # SSoT
```

**From Phase Script:**
```python
# ✅ CORRECT: Read execution metadata from file
import json

with open('adw_state.json') as f:
    state = json.load(f)
worktree_path = state['worktree_path']  # SSoT
plan_path = state['plan_path']          # SSoT

# ✅ CORRECT: Read coordination state from database
workflow = repo.find_by_issue_number(state['issue_number'])
current_phase = workflow.current_phase  # SSoT
```

### Updating State

**After Phase Completes:**
```python
# ✅ CORRECT: Update coordination state in database
repo.update_phase(
    issue_number=123,
    current_phase='test',
    status='running'
)

# ✅ CORRECT: Update execution metadata in file
with open('adw_state.json', 'r+') as f:
    state = json.load(f)
    state['phase_outputs']['build'] = {
        'files_changed': 5,
        'completed_at': datetime.now().isoformat()
    }
    f.seek(0)
    json.dump(state, f, indent=2)
    f.truncate()
```

**❌ WRONG: Duplicate state in both:**
```python
# DON'T DO THIS
repo.update_phase(issue_number=123, status='running')
state['status'] = 'running'  # ❌ Duplicate!
```

## Migration Plan

### Remove Duplicate Fields

**From `adw_state.json`:**
```json
{
  "adw_id": 5,
  "issue_number": 123,
  "status": "running",       // ❌ REMOVE - use database
  "current_phase": "test",   // ❌ REMOVE - use database
  "worktree_path": "...",    // ✅ KEEP
  "ports": {...}             // ✅ KEEP
}
```

**After migration:**
```json
{
  "adw_id": 5,
  "issue_number": 123,
  "worktree_path": "trees/adw-5",
  "ports": {"backend": 9104, "frontend": 9204},
  "started_at": "2025-12-10T10:00:00Z",
  "plan_path": "SDLC_PLAN.md",
  "phase_outputs": {}
}
```

### Update All Phase Scripts

For each phase script (10 total):
1. Remove writes to `status` and `current_phase` in adw_state.json
2. Keep database updates via repository
3. Add execution metadata to phase_outputs
4. Test that coordination still works

## Decision Tree

```
┌─────────────────────────────────────────┐
│ Need to access state?                   │
└────────────┬────────────────────────────┘
             │
             ▼
    ┌────────────────────┐
    │ What information?  │
    └────────┬───────────┘
             │
             ├─→ Workflow status/phase ──→ Database (phase_queue)
             ├─→ File locations/paths ───→ adw_state.json
             ├─→ Port allocations ────────→ adw_state.json
             ├─→ Dashboard display ───────→ Database
             ├─→ Phase coordination ──────→ Database
             └─→ Execution metadata ──────→ adw_state.json
```

## Validation Rules

**Before Reading State:**
1. Identify what you need (status vs. metadata)
2. Use decision tree to choose source
3. Read from SSoT only

**Before Writing State:**
1. Identify what changed (coordination vs. execution)
2. Use decision tree to choose destination
3. Write to SSoT only
4. Never duplicate writes

**On State Divergence:**
1. Database is authoritative for coordination
2. Log warning about divergence
3. Fix by syncing from database → file (if needed)
4. Investigate why divergence occurred
```

### Step 3: Update State Schema

Edit `adws/adw_state_schema.json` (or create if doesn't exist):

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ADW State File Schema",
  "description": "Execution metadata for ADW workflows (NOT coordination state)",
  "type": "object",
  "required": ["adw_id", "issue_number", "worktree_path", "ports"],
  "properties": {
    "adw_id": {
      "type": "integer",
      "description": "Unique ADW identifier"
    },
    "issue_number": {
      "type": "integer",
      "description": "GitHub issue number"
    },
    "worktree_path": {
      "type": "string",
      "description": "Absolute path to worktree directory"
    },
    "ports": {
      "type": "object",
      "required": ["backend", "frontend"],
      "properties": {
        "backend": {"type": "integer", "minimum": 9100, "maximum": 9114},
        "frontend": {"type": "integer", "minimum": 9200, "maximum": 9214}
      }
    },
    "started_at": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp when workflow started"
    },
    "plan_path": {
      "type": "string",
      "description": "Relative path to SDLC plan file"
    },
    "phase_outputs": {
      "type": "object",
      "description": "Phase-specific execution metadata",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "completed_at": {"type": "string", "format": "date-time"},
          "duration_seconds": {"type": "number"},
          "outputs": {"type": "object"}
        }
      }
    }
  },
  "additionalProperties": false,
  "not": {
    "anyOf": [
      {"required": ["status"]},
      {"required": ["current_phase"]}
    ]
  }
}
```

**Key points:**
- Explicitly excludes `status` and `current_phase`
- Documents SSoT purpose in description
- Defines required vs. optional fields

### Step 4: Remove Duplicate State from Files

```bash
cd adws/

# Create backup first
cp adw_state.json adw_state.json.backup 2>/dev/null || true

# Find all state files
find trees/ -name "adw_state.json" 2>/dev/null

# For each state file, remove status and current_phase
# (Manual or script - be careful!)
python3 << 'EOF'
import json
import glob
from pathlib import Path

state_files = glob.glob('trees/*/adw_state.json')
for file_path in state_files:
    try:
        with open(file_path, 'r') as f:
            state = json.load(f)

        # Remove duplicate fields
        removed = []
        if 'status' in state:
            del state['status']
            removed.append('status')
        if 'current_phase' in state:
            del state['current_phase']
            removed.append('current_phase')

        if removed:
            with open(file_path, 'w') as f:
                json.dump(state, f, indent=2)
            print(f"✓ {file_path}: Removed {removed}")
        else:
            print(f"  {file_path}: Already clean")
    except Exception as e:
        print(f"✗ {file_path}: Error - {e}")
EOF
```

### Step 5: Update Phase Scripts to Use SSoT

For each of the 10 phase scripts, update state access:

**Example: `adws/adw_planning.py`**

**Before (dual state):**
```python
# ❌ WRONG: Writing coordination state to file
state = {
    'adw_id': adw_id,
    'issue_number': issue_number,
    'status': 'planned',        # ❌ Duplicate
    'current_phase': 'plan',    # ❌ Duplicate
    'worktree_path': worktree_path,
    'ports': ports
}
with open('adw_state.json', 'w') as f:
    json.dump(state, f)

# Also update database
repo.update_phase(issue_number, status='planned', current_phase='plan')
```

**After (SSoT):**
```python
# ✅ CORRECT: Coordination to database, metadata to file
# Update database (SSoT for coordination)
repo.update_phase(
    issue_number=issue_number,
    status='planned',
    current_phase='plan'
)

# Update file (SSoT for execution metadata)
state = {
    'adw_id': adw_id,
    'issue_number': issue_number,
    'worktree_path': worktree_path,
    'ports': ports,
    'started_at': datetime.now().isoformat(),
    'plan_path': 'SDLC_PLAN.md',
    'phase_outputs': {}
}
with open('adw_state.json', 'w') as f:
    json.dump(state, f, indent=2)
```

**Repeat for all 10 phase scripts:**
1. adw_planning.py
2. adw_validate.py
3. adw_build.py
4. adw_lint.py
5. adw_test_iso.py
6. adw_review.py
7. adw_document.py
8. adw_ship.py
9. adw_cleanup.py
10. adw_verify.py

### Step 6: Update Helper Functions

If there are shared state management functions, update them:

```python
# Example: adws/utils/state_manager.py (if exists)

def update_workflow_status(issue_number: int, status: str, current_phase: str):
    """Update workflow coordination state.

    Uses database as SSoT for coordination state.
    Does NOT write to adw_state.json (that's for execution metadata).
    """
    from repositories.phase_queue_repository import PhaseQueueRepository

    repo = PhaseQueueRepository()
    repo.update_phase(
        issue_number=issue_number,
        status=status,
        current_phase=current_phase
    )

def update_execution_metadata(worktree_path: str, metadata: dict):
    """Update execution metadata in adw_state.json.

    Uses file as SSoT for execution metadata.
    Does NOT update status/current_phase (use update_workflow_status).
    """
    state_file = Path(worktree_path) / 'adw_state.json'

    with open(state_file, 'r+') as f:
        state = json.load(f)
        state.update(metadata)
        # Validate no forbidden fields
        if 'status' in metadata or 'current_phase' in metadata:
            raise ValueError("Use update_workflow_status for coordination state")
        f.seek(0)
        json.dump(state, f, indent=2)
        f.truncate()
```

### Step 7: Test SSoT Changes

```bash
# Test 1: Verify state file schema
cd adws/
python3 << 'EOF'
import json
import glob

state_files = glob.glob('trees/*/adw_state.json')
for file_path in state_files:
    with open(file_path) as f:
        state = json.load(f)

    # Check forbidden fields
    if 'status' in state:
        print(f"✗ {file_path}: Still has 'status' field")
    elif 'current_phase' in state:
        print(f"✗ {file_path}: Still has 'current_phase' field")
    else:
        print(f"✓ {file_path}: Clean")
EOF

# Test 2: Run a simple workflow to verify coordination still works
cd app/server
uv run python3 << 'EOF'
from repositories.phase_queue_repository import PhaseQueueRepository

repo = PhaseQueueRepository()

# Test update
repo.update_phase(
    issue_number=999,
    status='testing',
    current_phase='test'
)

# Test read
workflow = repo.find_by_issue_number(999)
assert workflow.status == 'testing', "Database update failed"
assert workflow.current_phase == 'test', "Database update failed"
print("✓ Database SSoT working")
EOF

# Test 3: Run phase tests
uv run pytest tests/ -k "phase" -v
```

### Step 8: Update Documentation

Add SSoT reference to phase contract docs (from Issue #1):

```bash
# Edit docs/adw/phase-contracts.md
# Add note to each phase about state management

# Example addition to Phase 1 contract:
```

**STATE MANAGEMENT:**
- **Database (SSoT for coordination):** Updates status='planned', current_phase='plan'
- **File (SSoT for metadata):** Creates adw_state.json with worktree_path, ports, plan_path
- **See:** docs/adw/state-management-ssot.md for complete rules

```

### Step 9: Commit Changes

```bash
git add docs/adw/state-management-ssot.md
git add adws/adw_state_schema.json
git add adws/*.py  # Updated phase scripts
git add trees/*/adw_state.json  # Cleaned state files
git commit -m "refactor: Establish Single Source of Truth for ADW state

Part 2 of 4 for Session 19 Phase 2 (State Management Clarity)

Eliminated dual-state management by defining clear SSoT rules:
- Database = Coordination state (status, current_phase)
- Files = Execution metadata (paths, ports, outputs)

Changes:
1. Created SSoT documentation with decision tree
2. Removed status/current_phase from adw_state.json
3. Updated all 10 phase scripts to use SSoT
4. Added JSON schema to enforce file structure
5. Updated helper functions

Benefits:
- No more state divergence
- Clear ownership (DB vs file)
- Easier to validate (single source per field)
- Foundation for state validation middleware (Part 3)

Files Modified:
- All 10 phase scripts (SSoT compliance)
- All active adw_state.json files (removed duplicates)

Files Added:
- docs/adw/state-management-ssot.md (architecture)
- adws/adw_state_schema.json (validation schema)

Next: Part 3 - Add State Validation Middleware (5 hours)"
```

## Success Criteria

- ✅ SSoT documentation created with clear rules
- ✅ Decision tree for state access defined
- ✅ All duplicate fields removed from adw_state.json
- ✅ All 10 phase scripts updated to use SSoT
- ✅ JSON schema enforces file structure
- ✅ Tests pass (coordination still works)
- ✅ Documentation updated
- ✅ Changes committed

## Files Expected to Change

**Created:**
- `docs/adw/state-management-ssot.md` (SSoT architecture, ~5 KB)
- `adws/adw_state_schema.json` (JSON schema, ~1 KB)

**Modified:**
- All 10 phase scripts in `adws/` (SSoT compliance)
- All `trees/*/adw_state.json` files (removed duplicates)
- `docs/adw/phase-contracts.md` (add SSoT references)

## Deliverables for Summary

When complete, return to coordination chat with:
```
**Issue #2 Complete: Define Single Source of Truth**

**SSoT Rules Established:**
- Database: Coordination state (status, current_phase, timing)
- Files: Execution metadata (paths, ports, outputs)

**Cleanup Performed:**
- Removed status/current_phase from [N] adw_state.json files
- Updated all 10 phase scripts to use SSoT
- Created JSON schema to prevent future duplicates

**Documentation:**
- SSoT architecture documented
- Decision tree for state access
- Migration guide for future changes

**Time Spent:** [actual hours]

**Key Insights:**
- [Number of state divergence issues found]
- [Patterns of incorrect state access]
- [Recommendations for Part 3]

**Ready for:** Part 3 - Add State Validation Middleware
```

## Troubleshooting

**If state divergence found during migration:**
- Database is authoritative for coordination
- Document the divergence
- Sync from database to file (not vice versa)

**If tests fail after removing duplicates:**
- Check if test reads from file instead of database
- Update test to use correct SSoT
- Add validation to test suite

**If phase script unclear which source to use:**
- Use decision tree
- Ask: "Is this coordination or execution?"
- When in doubt, prefer database for shared state

---

**Ready to copy into Issue #2!**
