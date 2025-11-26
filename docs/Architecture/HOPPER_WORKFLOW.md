# Hopper Workflow - Multi-Phase Issue Orchestration

## Overview

The **Hopper Workflow** is a queue-based system for orchestrating multi-phase development workflows where phases are pre-divided from an uploaded specification document. Each phase becomes a separate GitHub issue that executes sequentially, with automatic triggering of the next phase upon completion.

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                     HOPPER WORKFLOW                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌─────────────┐  │
│  │  Phase Queue │───▶│  Hopper      │───▶│   GitHub    │  │
│  │  (Database)  │    │  Sorter      │    │   Issues    │  │
│  └──────────────┘    └──────────────┘    └─────────────┘  │
│         │                    │                    │        │
│         │                    │                    │        │
│         ▼                    ▼                    ▼        │
│  ┌──────────────┐    ┌──────────────┐    ┌─────────────┐  │
│  │  Dependency  │    │   ADW        │    │  Background │  │
│  │  Tracker     │    │  Workflows   │    │  Poller     │  │
│  └──────────────┘    └──────────────┘    └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Data Model

**Phase Queue Item:**
```python
{
    "queue_id": str,           # Unique identifier
    "parent_issue": int,       # 0 for hopper workflows
    "phase_number": int,       # 1, 2, 3, 4...
    "issue_number": int | None,# GitHub issue (created JIT)
    "status": str,             # pending/ready/running/completed/failed
    "depends_on_phase": int,   # Previous phase number
    "phase_data": dict,        # Phase content from .md
    "priority": int,           # 10-90 (lower = higher priority)
    "queue_position": int,     # FIFO tiebreaker
    "adw_id": str | None       # Active workflow ID
}
```

## Workflow States

```
                 ┌──────────┐
                 │ pending  │  Initial state
                 └─────┬────┘
                       │
          ┌────────────▼──────────────┐
          │  dependency satisfied?    │
          └───────┬──────────┬────────┘
                 Yes        No
                  │          │
            ┌─────▼────┐     │
            │  ready   │◀────┘ (waits for dependency)
            └─────┬────┘
                  │
       ┌──────────▼──────────────┐
       │  issue created + ADW    │
       │  workflow launched      │
       └──────────┬──────────────┘
                  │
            ┌─────▼─────┐
            │  running  │  ADW executing
            └─────┬─────┘
                  │
        ┌─────────▼─────────┐
        │   completed?      │
        └────┬─────────┬────┘
            Yes       No
             │         │
    ┌────────▼───┐ ┌──▼──────┐
    │ completed  │ │ failed  │
    └────────────┘ └─────────┘
```

## Complete Workflow Flow

### 1. Initialization (From .md Upload)

```python
# User uploads multi-phase spec
POST /api/submit-request
{
    "phases": [
        {"number": 1, "title": "...", "content": "..."},
        {"number": 2, "title": "...", "content": "..."},
        {"number": 3, "title": "...", "content": "..."},
        {"number": 4, "title": "...", "content": "..."}
    ]
}

# Backend response:
MultiPhaseIssueHandler.handle_multi_phase_request()
  ├─ Create Phase 1 GitHub issue (#114)
  ├─ Enqueue Phase 1 (status="ready", issue_number=114)
  ├─ Enqueue Phase 2 (status="pending", depends_on_phase=1)
  ├─ Enqueue Phase 3 (status="pending", depends_on_phase=2)
  └─ Enqueue Phase 4 (status="pending", depends_on_phase=3)
```

### 2. Phase Execution

```
Background Poller (every ~10s):
  PhaseCoordinator._poll_loop()
    │
    ├─ _create_missing_issues()
    │    └─ For each ready phase without issue_number:
    │         └─ Create GitHub issue with workflow trigger
    │
    ├─ _auto_start_ready_phases()
    │    └─ For each ready phase with issue_number:
    │         └─ Launch ADW workflow (adw_sdlc_complete_iso)
    │
    └─ _check_workflow_completions()
         └─ Monitor running ADWs for completion
```

### 3. Phase Completion Hook

**Critical Flow:** When an ADW workflow completes:

```
adw_sdlc_complete_iso.py (Phase N)
  │
  ├─ Phase 8: Ship
  │    └─ Merge PR via GitHub API
  │
  └─ Phase 9: Cleanup
       └─ POST /api/issue/{N}/complete
            │
            └─ issue_completion_routes.py
                 │
                 ├─ Query: WHERE issue_number = {N}  ← CRITICAL FIX
                 │   (NOT parent_issue, hopper uses parent_issue=0)
                 │
                 ├─ Call: phase_queue_service.mark_phase_complete(queue_id)
                 │   │
                 │   └─ dependency_tracker.trigger_next_phase()
                 │        ├─ Mark Phase N as "completed"
                 │        └─ Mark Phase N+1 as "ready"
                 │
                 └─ Close GitHub issue #{N}
```

### 4. Next Phase Trigger

```
Background Poller (next iteration):
  │
  ├─ _create_missing_issues()
  │    └─ Finds Phase N+1 (status="ready", issue_number=NULL)
  │    └─ Creates GitHub issue #{N+1}
  │    └─ Updates phase_queue: issue_number={N+1}
  │
  └─ _auto_start_ready_phases()
       └─ Finds Phase N+1 (status="ready", issue_number={N+1})
       └─ Launches ADW workflow for issue #{N+1}
```

## Critical Bugs Fixed (2025-11-25)

### Bug #1: Wrong Query Field
**File:** `app/server/routes/issue_completion_routes.py:71-83`

**Before:**
```python
WHERE parent_issue = ?  # WRONG for hopper (parent_issue=0)
```

**After:**
```python
WHERE issue_number = ?  # CORRECT - finds hopper phases
```

**Impact:** Hopper workflows never triggered next phase because queue entry wasn't found.

### Bug #2: Bypassed Dependency Tracker
**File:** `app/server/routes/issue_completion_routes.py:89-101`

**Before:**
```python
# Direct DB update - no next phase trigger
cursor.execute("UPDATE phase_queue SET status='completed' WHERE queue_id=?")
```

**After:**
```python
# Uses service layer - triggers next phase
next_phase_triggered = phase_queue_service.mark_phase_complete(queue_id)
```

**Impact:** Next phases stayed in "pending" state instead of becoming "ready".

### Bug #3: Missing Request Body
**File:** `adws/adw_modules/success_operations.py:38-41`

**Before:**
```python
requests.post(f"{BACKEND_URL}/api/issue/{issue_number}/complete")
# No JSON body - FastAPI requires it
```

**After:**
```python
requests.post(
    f"{BACKEND_URL}/api/issue/{issue_number}/complete",
    json={"issue_number": int(issue_number)}
)
```

**Impact:** 422 error "Field required" prevented completion hook from running.

### Bug #4: Context Manager Misuse
**File:** `app/server/routes/issue_completion_routes.py:62-87`

**Before:**
```python
db_conn = get_connection()
cursor = db_conn.cursor()  # Error: context manager has no .cursor()
```

**After:**
```python
with get_connection() as db_conn:
    cursor = db_conn.cursor()  # Correct
```

**Impact:** Runtime error prevented endpoint from executing.

## Database Schema

### phase_queue Table

```sql
CREATE TABLE phase_queue (
    queue_id TEXT PRIMARY KEY,
    parent_issue INTEGER NOT NULL,     -- 0 for hopper workflows
    phase_number INTEGER NOT NULL,
    issue_number INTEGER,              -- Created just-in-time
    status TEXT NOT NULL,              -- pending/ready/running/completed/failed
    depends_on_phase INTEGER,
    phase_data TEXT,                   -- JSON blob
    priority INTEGER DEFAULT 50,       -- 10 (urgent) to 90 (background)
    queue_position INTEGER,            -- FIFO tiebreaker
    ready_timestamp TEXT,
    started_timestamp TEXT,
    adw_id TEXT,
    created_at TEXT,
    updated_at TEXT,
    error_message TEXT
);
```

### Key Indexes

```sql
CREATE INDEX idx_phase_queue_priority
  ON phase_queue(priority, queue_position);

CREATE INDEX idx_phase_queue_status_issue
  ON phase_queue(status, issue_number);
```

## Priority System

The **HopperSorter** provides deterministic ordering:

```python
class HopperSorter:
    PRIORITY_URGENT = 10
    PRIORITY_HIGH = 20
    PRIORITY_NORMAL = 50  # Default
    PRIORITY_LOW = 70
    PRIORITY_BACKGROUND = 90
```

**Selection Order:**
1. Priority (lower number = higher urgency)
2. Queue position (FIFO within same priority)
3. Parent issue (tiebreaker)

## API Endpoints

### Complete Issue
```http
POST /api/issue/{issue_number}/complete
Content-Type: application/json

{
    "issue_number": 114,
    "phase_number": 1,       // Optional
    "commit_sha": "abc123",  // Optional
    "close_message": "..."   // Optional
}
```

**Response:**
```json
{
    "success": true,
    "queue_updated": true,
    "issue_closed": true,
    "message": "Phase 1 completed, next phase triggered"
}
```

### Queue Status
```http
GET /api/queue
```

**Response:**
```json
{
    "queue_paused": false,
    "phases": [
        {
            "queue_id": "uuid",
            "parent_issue": 0,
            "phase_number": 1,
            "issue_number": 114,
            "status": "completed"
        },
        {
            "queue_id": "uuid",
            "parent_issue": 0,
            "phase_number": 2,
            "issue_number": 115,
            "status": "running"
        }
    ]
}
```

## Configuration

### Environment Variables
```bash
BACKEND_URL=http://localhost:8000
GITHUB_TOKEN=ghp_...
```

### Queue Config (Database)
```sql
INSERT INTO queue_config (config_key, config_value) VALUES
('queue_paused', 'false'),
('max_parallel_parents', '5');
```

## Monitoring

### Check Queue Status
```bash
cd app/server
uv run python -c "
from services.hopper_sorter import HopperSorter
sorter = HopperSorter()
stats = sorter.get_priority_stats()
print(stats)
"
```

### View Background Poller Logs
```bash
tail -f app/server/logs/server.log | grep PhaseCoordinator
```

## Example Workflow

**Scenario:** 4-phase pattern recognition feature

```
Initial State:
├─ Phase 1: "Complete Submission-Time Pattern Detection" (#114, ready)
├─ Phase 2: "Integrate with Queue System" (pending)
├─ Phase 3: "Validate Predictions" (pending)
└─ Phase 4: "Observability Dashboard" (pending)

Execution Timeline:
T+0min:  Phase 1 issue created, ADW launched
T+45min: Phase 1 completes, PR merged
T+45min: Cleanup calls /api/issue/114/complete
T+45min: Phase 2 marked ready
T+45min: Background poller creates Phase 2 issue (#115)
T+46min: Phase 2 ADW launches automatically
T+90min: Phase 2 completes, triggers Phase 3
...and so on
```

## Troubleshooting

### Phase Not Triggering
**Symptom:** Next phase stays "pending" after previous completes

**Debug:**
```sql
-- Check if phase was marked complete
SELECT * FROM phase_queue WHERE issue_number = 114;

-- Check if next phase became ready
SELECT * FROM phase_queue
WHERE parent_issue = 0 AND phase_number = 2;
```

**Fix:** Ensure `/api/issue/{N}/complete` was called with correct JSON body.

### Issue Not Created
**Symptom:** Phase is "ready" but has no issue_number

**Debug:**
```bash
# Check background poller logs
tail -f app/server/logs/server.log | grep AUTO-CREATE
```

**Fix:** Restart backend to restart background poller.

### Workflow Not Auto-Starting
**Symptom:** Issue created but ADW not launched

**Debug:**
```sql
-- Check queue is not paused
SELECT config_value FROM queue_config WHERE config_key = 'queue_paused';
```

**Fix:** Un-pause queue via `/api/queue/pause` endpoint.

## Testing

### Manual Phase Trigger Test
```bash
# Create Phase 1 issue and enqueue phases 2-4
curl -X POST http://localhost:8000/api/submit-request \
  -H "Content-Type: application/json" \
  -d @multi_phase_spec.json

# Complete Phase 1 (triggers Phase 2)
curl -X POST http://localhost:8000/api/issue/114/complete \
  -H "Content-Type: application/json" \
  -d '{"issue_number": 114}'

# Verify Phase 2 became ready
curl http://localhost:8000/api/queue | jq '.phases[] | select(.phase_number == 2)'
```

## References

- Phase Queue Service: `app/server/services/phase_queue_service.py`
- Hopper Sorter: `app/server/services/hopper_sorter.py`
- Dependency Tracker: `app/server/services/phase_dependency_tracker.py`
- Phase Coordinator: `app/server/services/phase_coordination/phase_coordinator.py`
- Multi-Phase Handler: `app/server/services/multi_phase_issue_handler.py`
- Issue Completion Routes: `app/server/routes/issue_completion_routes.py`
- Ship Workflow: `adws/adw_ship_iso.py`
- Success Operations: `adws/adw_modules/success_operations.py`
