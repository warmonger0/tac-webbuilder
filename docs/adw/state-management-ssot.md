# ADW State Management - Single Source of Truth

**Version:** 1.0
**Last Updated:** 2025-12-10
**Related:** Session 19 Phase 2 Part 2 - Dual-State Management Clarity

---

## Architecture Principle

**Database** = Coordination State (shared, authoritative)
**Files** = Execution Metadata (local, supporting)

**Problem Eliminated:** Dual-state management where `status` and `current_phase` were tracked in BOTH database (`phase_queue` table) AND files (`adw_state.json`), causing divergence, race conditions, and unclear authority.

**Solution:** Clear Single Source of Truth (SSoT) boundaries with explicit ownership rules.

---

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
    adw_id TEXT,                    -- ADW identifier
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    priority INTEGER DEFAULT 50,
    queue_position INTEGER,
    phase_number INTEGER,
    depends_on_phase INTEGER,
    phase_data TEXT,
    ready_timestamp TIMESTAMP,
    started_timestamp TIMESTAMP,
    error_message TEXT
);
```

### Authoritative For

✅ **Workflow status:** `queued`, `running`, `completed`, `failed`, `blocked`
✅ **Current phase:** `plan`, `validate`, `build`, `lint`, `test`, `review`, `document`, `ship`, `cleanup`, `verify`
✅ **Assignment:** Which ADW ID is handling this workflow
✅ **Timing:** When workflow started, last updated, completed
✅ **Coordination:** Parent/child relationships, dependencies
✅ **Error tracking:** Error messages from failed phases

### Not Responsible For

❌ **File locations** (worktree path, plan path)
❌ **Port allocations** (backend, frontend)
❌ **Phase-specific outputs** (test results, lint results)
❌ **Execution metadata** (branch name, model set, cost estimates)

### Update Rules

- **Repository only:** Update via `PhaseQueueRepository` class methods
- **Always update timestamp:** Set `updated_at` on every change
- **Use transactions:** For multi-field updates
- **Validate transitions:** Ensure valid status state transitions
- **WebSocket broadcast:** Notify dashboard of coordination state changes

---

## File Schema (Supporting Metadata for Execution)

### `agents/{adw_id}/adw_state.json`

```json
{
  "adw_id": "77c90e61",
  "issue_number": "170",
  "worktree_path": "/Users/user/tac/tac-webbuilder/trees/77c90e61",
  "branch_name": "feature/add-user-auth",
  "plan_file": "trees/77c90e61/specs/issue-170-adw-77c90e61-sdlc_planner-user-auth.md",
  "issue_class": "/feature",
  "backend_port": 9107,
  "frontend_port": 9207,
  "model_set": "base",
  "all_adws": ["adw_plan_iso", "adw_build_iso"],
  "estimated_cost_total": 0.45,
  "estimated_cost_breakdown": {
    "plan": 0.15,
    "build": 0.20,
    "test": 0.10
  },
  "workflow_template": "adw_sdlc_complete_iso",
  "model_used": "sonnet",
  "start_time": "2025-12-10T10:33:03.064774",
  "nl_input": "Add user authentication",
  "github_url": "https://github.com/user/repo/issues/170",
  "baseline_errors": {
    "frontend": {
      "type_errors": 0,
      "build_errors": 0
    }
  },
  "external_build_results": {
    "success": true,
    "summary": {"total_errors": 0}
  }
}
```

### Authoritative For

✅ **Worktree location:** Absolute path to isolated worktree
✅ **Port allocations:** Backend (9100-9114), Frontend (9200-9214)
✅ **File paths:** Plan file, spec files, output locations
✅ **Phase-specific metadata:** Test results, build results, lint results
✅ **Execution environment:** Branch name, model set, cost estimates
✅ **Workflow context:** Template used, natural language input, GitHub URL

### Not Responsible For

❌ **Workflow status** (use database `phase_queue.status`)
❌ **Current phase** (use database `phase_queue.current_phase`)
❌ **Coordination across ADWs** (use database)
❌ **Dashboard display** (use database)

### Update Rules

- **Helper functions:** Update via state management utilities
- **Atomic writes:** Write to temp file, then rename
- **Schema validation:** No `status` or `current_phase` fields allowed
- **Preserve extra fields:** Allow phase-specific outputs not in core schema

---

## State Access Patterns

### Reading State

#### From Dashboard/API (Coordination State)

```python
# ✅ CORRECT: Read coordination state from database
from app.server.repositories.phase_queue_repository import PhaseQueueRepository

repo = PhaseQueueRepository()
workflow = repo.find_by_issue_number(170)

# These are authoritative from database
status = workflow.status              # SSoT
current_phase = workflow.current_phase  # SSoT
adw_id = workflow.adw_id               # SSoT
created_at = workflow.created_at       # SSoT
```

#### From Phase Script (Execution Metadata)

```python
# ✅ CORRECT: Read execution metadata from file
from adw_modules.state import ADWState

state = ADWState.load(adw_id="77c90e61")

# These are authoritative from file
worktree_path = state.get('worktree_path')  # SSoT
plan_file = state.get('plan_file')          # SSoT
backend_port = state.get('backend_port')    # SSoT
branch_name = state.get('branch_name')      # SSoT

# For coordination state, query database
repo = PhaseQueueRepository()
workflow = repo.find_by_issue_number(state.get('issue_number'))
current_phase = workflow.current_phase  # SSoT from database
```

#### Hybrid Access (Both Sources)

```python
# When you need both coordination and execution data
from adw_modules.state import ADWState
from app.server.repositories.phase_queue_repository import PhaseQueueRepository

# Load execution metadata
state = ADWState.load(adw_id="77c90e61")
worktree_path = state.get('worktree_path')
backend_port = state.get('backend_port')

# Load coordination state
repo = PhaseQueueRepository()
workflow = repo.find_by_issue_number(state.get('issue_number'))
current_phase = workflow.current_phase
status = workflow.status
```

---

### Updating State

#### After Phase Completes (Coordination State)

```python
# ✅ CORRECT: Update coordination state in database only
from app.server.repositories.phase_queue_repository import PhaseQueueRepository

repo = PhaseQueueRepository()
repo.update_status(
    queue_id=workflow.queue_id,
    status='running',
    adw_id='77c90e61'
)

# Broadcast to WebSocket clients for real-time dashboard updates
from adw_modules.workflow_ops import broadcast_phase_update
broadcast_phase_update(
    adw_id='77c90e61',
    current_phase='test',
    status='running'
)
```

#### After Phase Produces Metadata (Execution State)

```python
# ✅ CORRECT: Update execution metadata in file only
from adw_modules.state import ADWState

state = ADWState.load(adw_id="77c90e61")
state.update(
    external_build_results={
        'success': True,
        'summary': {'total_errors': 0},
        'errors': []
    }
)
state.save(workflow_step="Build Phase")
```

#### ❌ WRONG: Duplicate State

```python
# ❌ DON'T DO THIS - Duplicating state in both locations
repo.update_status(queue_id=workflow.queue_id, status='running')
state.update(status='running')  # ❌ Duplicate!
state.save()
```

---

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
             ├─→ Workflow status/phase ────────────────→ Database (phase_queue.status, phase_queue.current_phase)
             ├─→ Assignment (which ADW) ────────────────→ Database (phase_queue.adw_id)
             ├─→ Timing (created/updated/completed) ────→ Database (phase_queue.*_at)
             ├─→ Error messages ───────────────────────→ Database (phase_queue.error_message)
             ├─→ Dashboard display ────────────────────→ Database (via API endpoints)
             ├─→ Phase coordination ───────────────────→ Database (depends_on_phase, phase_number)
             │
             ├─→ File locations/paths ─────────────────→ File (worktree_path, plan_file)
             ├─→ Port allocations ─────────────────────→ File (backend_port, frontend_port)
             ├─→ Execution metadata ───────────────────→ File (branch_name, model_set)
             ├─→ Phase outputs ────────────────────────→ File (external_build_results, baseline_errors)
             └─→ Cost estimates ───────────────────────→ File (estimated_cost_total, estimated_cost_breakdown)
```

---

## Validation Rules

### Before Reading State

1. **Identify what you need:** Status vs. metadata
2. **Use decision tree:** Choose source based on data type
3. **Read from SSoT only:** Never read duplicate data from both
4. **Handle missing gracefully:** File may not exist yet, database may have NULL

### Before Writing State

1. **Identify what changed:** Coordination vs. execution
2. **Use decision tree:** Choose destination based on data type
3. **Write to SSoT only:** Never duplicate writes to both
4. **Update timestamp:** Always update `updated_at` in database
5. **Broadcast if coordination:** Notify WebSocket clients of phase/status changes

### On State Divergence

If you find `status` or `current_phase` in `adw_state.json`:

1. **Database is authoritative** for coordination state
2. **Log warning** about divergence
3. **Remove from file** (file should not have these fields)
4. **Investigate why** divergence occurred
5. **Fix the code** that wrote to both sources

---

## Migration Strategy

### Phase 1: Documentation (Current)

- ✅ Define SSoT architecture
- ✅ Create decision tree
- ✅ Document update rules

### Phase 2: Schema Enforcement

- Create JSON schema to reject forbidden fields
- Add validation in `ADWState.save()` to prevent `status`/`current_phase` writes
- Update `ADWStateData` model to remove duplicate fields

### Phase 3: Code Migration

- Remove `status` and `current_phase` from `adw_modules/state.py` core_fields
- Update all 10 phase scripts to use SSoT pattern
- Clean existing state files

### Phase 4: Testing

- Verify database queries work correctly
- Verify file reads work correctly
- Verify no state divergence occurs
- Verify WebSocket broadcasts work

---

## Examples from Codebase

### Example 1: Plan Phase (adw_plan_iso.py)

**Before (Dual State):**
```python
# ❌ Writing coordination state to file
state.update(
    status='planned',
    current_phase='plan',
    worktree_path='/path/to/worktree',
    backend_port=9100
)
state.save()

# Also updating database
repo.update_status(queue_id, status='planned')
```

**After (SSoT):**
```python
# ✅ Coordination to database
repo.update_status(
    queue_id=queue_id,
    status='planned',
    adw_id=adw_id
)

# ✅ Execution metadata to file
state.update(
    worktree_path='/path/to/worktree',
    backend_port=9100,
    plan_file='trees/adw-X/specs/...'
)
state.save(workflow_step="Plan Phase")

# ✅ Broadcast coordination update
broadcast_phase_update(
    adw_id=adw_id,
    current_phase='plan',
    status='planned'
)
```

### Example 2: Test Phase (adw_test_iso.py)

**Before (Dual State):**
```python
# ❌ Reading from file
state = ADWState.load(adw_id)
current_phase = state.get('current_phase')  # ❌ Wrong source

# ❌ Updating both
state.update(status='testing', current_phase='test')
repo.update_status(queue_id, status='testing')
```

**After (SSoT):**
```python
# ✅ Read coordination from database
repo = PhaseQueueRepository()
workflow = repo.find_by_issue_number(issue_number)
current_phase = workflow.current_phase  # ✅ SSoT

# ✅ Read execution metadata from file
state = ADWState.load(adw_id)
worktree_path = state.get('worktree_path')
backend_port = state.get('backend_port')

# ✅ Update coordination in database
repo.update_status(
    queue_id=workflow.queue_id,
    status='testing'
)

# ✅ Update execution metadata in file
state.update(
    external_test_results={
        'passed': 45,
        'failed': 2,
        'coverage': 78.5
    }
)
state.save(workflow_step="Test Phase")

# ✅ Broadcast coordination update
broadcast_phase_update(
    adw_id=adw_id,
    current_phase='test',
    status='testing'
)
```

### Example 3: Dashboard API (routes/workflow_routes.py)

**Before (Ambiguous):**
```python
# ❌ Unclear which source to trust
state = ADWState.load(adw_id)
workflow = repo.find_by_issue_number(issue_number)

# What if they disagree?
file_status = state.get('status')
db_status = workflow.status
```

**After (Clear SSoT):**
```python
# ✅ Always use database for coordination state
workflow = repo.find_by_issue_number(issue_number)

return {
    'status': workflow.status,              # SSoT
    'current_phase': workflow.current_phase,  # SSoT
    'created_at': workflow.created_at,       # SSoT

    # Load file only if needed for execution metadata
    # (usually not needed for dashboard - database has what we need)
}
```

---

## Benefits of SSoT Architecture

### 1. No State Divergence
- **Before:** Database says "running", file says "completed" → Which is correct?
- **After:** Database is authoritative for status → Always trust database

### 2. Clear Ownership
- **Before:** Should I update database or file or both?
- **After:** Decision tree tells you exactly where to read/write

### 3. Easier Validation
- **Before:** Must validate consistency between two sources
- **After:** Single source per field → Validate once

### 4. Better Performance
- **Before:** Read from both sources, compare, resolve conflicts
- **After:** Read from correct source once

### 5. Simpler Code
- **Before:** Synchronization logic, conflict resolution, defensive checks
- **After:** Direct access to authoritative source

### 6. Foundation for Middleware
- **Before:** Difficult to add validation when state is duplicated
- **After:** Can add state validation middleware at single chokepoint (Part 3)

---

## Common Pitfalls

### Pitfall 1: Reading from Wrong Source

```python
# ❌ WRONG: Reading coordination state from file
state = ADWState.load(adw_id)
status = state.get('status')  # ❌ File is not SSoT for status

# ✅ CORRECT: Read from database
workflow = repo.find_by_issue_number(issue_number)
status = workflow.status  # ✅ Database is SSoT
```

### Pitfall 2: Updating Both Sources

```python
# ❌ WRONG: Updating coordination state in both places
repo.update_status(queue_id, status='completed')
state.update(status='completed')  # ❌ Duplicate write

# ✅ CORRECT: Update database only
repo.update_status(queue_id, status='completed')
# state.update() should only contain execution metadata
```

### Pitfall 3: Forgetting to Broadcast

```python
# ⚠️ INCOMPLETE: Updated database but no WebSocket broadcast
repo.update_status(queue_id, status='running')
# Dashboard won't update in real-time!

# ✅ CORRECT: Update + broadcast
repo.update_status(queue_id, status='running')
broadcast_phase_update(adw_id, current_phase='test', status='running')
```

### Pitfall 4: Assuming File Exists

```python
# ❌ WRONG: Assuming file always exists
state = ADWState.load(adw_id)
port = state.get('backend_port')  # May be None if Plan didn't run

# ✅ CORRECT: Handle missing gracefully
state = ADWState.load(adw_id)
if not state:
    raise ValueError(f"No state found for ADW {adw_id} - run Plan phase first")
port = state.get('backend_port')
if not port:
    raise ValueError("Backend port not allocated - run Plan phase first")
```

---

## Testing SSoT Compliance

### Test 1: No Forbidden Fields in Files

```bash
cd /Users/Warmonger0/tac/tac-webbuilder
python3 << 'EOF'
import json
import glob

state_files = glob.glob('agents/*/adw_state.json')
violations = []

for file_path in state_files:
    with open(file_path) as f:
        state = json.load(f)

    if 'status' in state:
        violations.append(f"{file_path}: Has 'status' field")
    if 'current_phase' in state:
        violations.append(f"{file_path}: Has 'current_phase' field")

if violations:
    print("❌ SSoT VIOLATIONS FOUND:")
    for v in violations:
        print(f"  {v}")
    exit(1)
else:
    print("✅ All state files SSoT compliant")
EOF
```

### Test 2: Database Contains Required Fields

```python
from app.server.repositories.phase_queue_repository import PhaseQueueRepository

repo = PhaseQueueRepository()
workflows = repo.find_all()

for workflow in workflows:
    assert workflow.status is not None, f"Workflow {workflow.queue_id} missing status"
    assert workflow.current_phase is not None, f"Workflow {workflow.queue_id} missing current_phase"

print("✅ All database records have required coordination fields")
```

### Test 3: State Access Uses Correct Source

```bash
# Check that code doesn't read status from file
cd adws/
grep -rn "state.get('status')" . --include="*.py"
# Should return: No matches (or only in migration scripts)

grep -rn "state.get('current_phase')" . --include="*.py"
# Should return: No matches (or only in migration scripts)
```

---

## Related Documentation

- **Phase Contracts:** `docs/adw/phase-contracts.md` - Defines what each phase produces
- **State Validation:** `docs/adw/state-validation-middleware.md` (Part 3) - Validates state transitions
- **Idempotent Phases:** `docs/adw/idempotent-phases.md` (Part 4) - Safe phase re-execution
- **Database Schema:** `app/server/database.py` - Complete schema definitions
- **Repository Pattern:** `app/server/repositories/phase_queue_repository.py` - Database access layer

---

**End of SSoT Documentation**
