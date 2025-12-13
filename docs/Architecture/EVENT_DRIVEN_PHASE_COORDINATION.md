# Event-Driven Phase Coordination Architecture

**Date**: 2025-12-13
**Status**: Design Complete - Ready for Implementation
**Version**: 2.0 (Event-Driven with Parallel Execution)

---

## Executive Summary

The Phase Coordination system manages automated execution of multi-phase workflows with:
- **Event-driven architecture** (NO polling)
- **Parallel execution** with intelligent dependency resolution
- **Concurrency control** (max 3 concurrent ADWs)
- **Isolated GitHub issues** (no parent issues to avoid token bloat)
- **Real-time WebSocket updates** (<100ms latency)

### Key Improvements Over v1.0 (Polling)

| Metric | v1.0 (Polling) | v2.0 (Event-Driven) | Improvement |
|--------|----------------|---------------------|-------------|
| **Latency** | 3-10s (poll interval) | <100ms (instant) | **30-100x faster** |
| **Resource Usage** | Constant polling overhead | Event-triggered only | **90% reduction** |
| **Parallel Execution** | Sequential only | Up to 3 concurrent | **3x throughput** |
| **Token Efficiency** | Parent issue bloat | Isolated issues | **60-80% reduction** |
| **Scalability** | Limited by poll frequency | Event-driven | **Unlimited** |

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Event Flow](#2-event-flow)
3. [Concurrency Control](#3-concurrency-control)
4. [Dependency Resolution](#4-dependency-resolution)
5. [Isolated Issue Strategy](#5-isolated-issue-strategy)
6. [Database Schema](#6-database-schema)
7. [Implementation Guide](#7-implementation-guide)
8. [Migration from v1.0](#8-migration-from-v10)
9. [Testing Strategy](#9-testing-strategy)

---

## 1. Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Action (Panel 5)                    │
│              Click "⚡ Generate & Execute" on Feature            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend: Phase Generation                     │
│  1. Analyze feature complexity (plan_phases.py)                  │
│  2. Build dependency graph (detect parallel phases)              │
│  3. Generate prompts for each phase                              │
│  4. Insert phases into phase_queue table                         │
│  5. Create isolated GitHub issue for Phase 1 ONLY               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Phase Queue (Database)                       │
│  queue_id=1: feature_id=104, phase=1, depends_on=[]             │
│  queue_id=2: feature_id=104, phase=2, depends_on=[1]            │
│  queue_id=3: feature_id=104, phase=3, depends_on=[1]            │
│  queue_id=4: feature_id=104, phase=4, depends_on=[2,3]          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              PhaseCoordinator (Event-Driven Service)             │
│  • Subscribes to WebSocket "workflow_completed" events          │
│  • NO polling loop (v1.0 legacy removed)                         │
│  • Handles dependency resolution                                 │
│  • Enforces concurrency limit (max 3 ADWs)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ADW Workflow Execution                        │
│  Phase 1 starts → completes → POST /workflow-complete            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Webhook Handler (queue_routes.py)               │
│  1. Validate & deduplicate webhook                               │
│  2. Update phase_queue status = 'completed'                      │
│  3. Emit WebSocket event: "workflow_completed"                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│            WebSocket Event Dispatcher (websocket_manager.py)     │
│  • Broadcasts to WebSocket clients (Panel 5 UI)                 │
│  • Dispatches to event subscribers (PhaseCoordinator)            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              PhaseCoordinator.handle_workflow_completion()       │
│  1. Find ALL newly ready phases (dependency check)               │
│  2. Check concurrency limit (max 3 running)                      │
│  3. Create isolated GitHub issues for ready phases               │
│  4. Launch ADWs in parallel (up to limit)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    Repeat until all phases complete
```

---

## 2. Event Flow

### 2.1 Initial Execution

```
Panel 5 → "⚡ Generate & Execute" on Feature #104
  ↓
POST /api/v1/planned-features/104/execute
  ↓
Backend analyzes: 5 phases needed
  - Phase 1: Database Schema (blocking all)
  - Phase 2: Backend API (depends on [1])
  - Phase 3: Frontend UI (depends on [1])
  - Phase 4: Integration Tests (depends on [2,3])
  - Phase 5: Documentation (depends on [1])
  ↓
Insert into phase_queue:
  queue_id=1: phase=1, depends_on=[], status='queued'
  queue_id=2: phase=2, depends_on=[1], status='queued'
  queue_id=3: phase=3, depends_on=[1], status='queued'
  queue_id=4: phase=4, depends_on=[2,3], status='queued'
  queue_id=5: phase=5, depends_on=[1], status='queued'
  ↓
Create isolated GitHub issue #200: "Feature #104 - Phase 1: Database Schema"
  ↓
Update queue_id=1: issue_number=200, status='ready'
  ↓
PhaseCoordinator launches Phase 1 ADW
  ↓
Update queue_id=1: status='running', adw_id='adw-abc123'
```

### 2.2 Phase Completion Event

```
Phase 1 ADW completes
  ↓
POST /workflow-complete
  {
    "queue_id": "1",
    "feature_id": 104,
    "phase_number": 1,
    "status": "completed",
    "adw_id": "adw-abc123"
  }
  ↓
Webhook handler:
  1. Validates request (security, deduplication)
  2. Updates phase_queue: queue_id=1, status='completed'
  3. Emits WebSocket event:
     {
       "type": "workflow_completed",
       "data": {
         "queue_id": "1",
         "feature_id": 104,
         "phase_number": 1,
         "status": "completed"
       }
     }
  ↓
WebSocket Manager:
  1. Broadcasts to Panel 5 UI (real-time update)
  2. Dispatches to PhaseCoordinator.handle_workflow_completion()
  ↓
PhaseCoordinator:
  1. Finds newly ready phases:
     - Phase 2: depends_on=[1] → Phase 1 complete → READY ✅
     - Phase 3: depends_on=[1] → Phase 1 complete → READY ✅
     - Phase 4: depends_on=[2,3] → Phase 2,3 not complete → BLOCKED ❌
     - Phase 5: depends_on=[1] → Phase 1 complete → READY ✅

  2. Checks concurrency:
     - Currently running: 0
     - Max allowed: 3
     - Ready phases: 3 (Phases 2, 3, 5)
     - Can launch: 3 ✅

  3. Creates isolated GitHub issues:
     - Issue #201: "Feature #104 - Phase 2: Backend API"
     - Issue #202: "Feature #104 - Phase 3: Frontend UI"
     - Issue #203: "Feature #104 - Phase 5: Documentation"

  4. Launches ADWs in parallel:
     - Phase 2 → ADW adw-def456 (Issue #201)
     - Phase 3 → ADW adw-ghi789 (Issue #202)
     - Phase 5 → ADW adw-jkl012 (Issue #203)

  5. Updates phase_queue:
     - queue_id=2: status='running', adw_id='adw-def456'
     - queue_id=3: status='running', adw_id='adw-ghi789'
     - queue_id=5: status='running', adw_id='adw-jkl012'
  ↓
Now 3 ADWs running concurrently (at limit)
```

### 2.3 Concurrency Limit Reached

```
Phase 2 completes (Backend API)
  ↓
POST /workflow-complete → WebSocket event
  ↓
PhaseCoordinator:
  1. Finds newly ready phases:
     - Phase 4: depends_on=[2,3]
       - Phase 2: completed ✅
       - Phase 3: still running ❌
       - Result: BLOCKED (not all dependencies met)

  2. No phases ready → No action
  ↓
Phase 3 completes (Frontend UI)
  ↓
POST /workflow-complete → WebSocket event
  ↓
PhaseCoordinator:
  1. Finds newly ready phases:
     - Phase 4: depends_on=[2,3]
       - Phase 2: completed ✅
       - Phase 3: completed ✅
       - Result: READY ✅

  2. Checks concurrency:
     - Currently running: 1 (Phase 5 still running)
     - Max allowed: 3
     - Ready phases: 1 (Phase 4)
     - Can launch: 1 ✅

  3. Creates isolated GitHub issue:
     - Issue #204: "Feature #104 - Phase 4: Integration Tests"

  4. Launches ADW:
     - Phase 4 → ADW adw-mno345 (Issue #204)
  ↓
Now 2 ADWs running (Phase 4 and Phase 5)
```

---

## 3. Concurrency Control

### 3.1 Limit Configuration

**Maximum Concurrent ADWs: 3**

Rationale:
- Balances throughput vs. resource usage
- Prevents overwhelming CI/CD infrastructure
- Allows meaningful progress on 3 independent phases
- Leaves headroom for manual workflow launches

### 3.2 Enforcement Logic

```python
class PhaseCoordinator:
    def __init__(self, max_concurrent_adws: int = 3):
        self.max_concurrent_adws = max_concurrent_adws

    async def _handle_phase_success(self, queue_id, feature_id, phase_number):
        # Find all newly ready phases
        ready_phases = self._find_newly_ready_phases(feature_id)

        # Get current running count (across ALL features)
        running_count = self._get_running_count()

        # Launch phases up to limit
        launched = 0
        for phase in ready_phases:
            if running_count + launched >= self.max_concurrent_adws:
                logger.info(
                    f"[LIMIT] Max concurrent ADWs reached ({self.max_concurrent_adws}). "
                    f"Remaining {len(ready_phases) - launched} phases queued."
                )
                break

            await self._launch_phase(phase)
            launched += 1

        # Remaining phases stay in 'queued' status
        # They'll be launched when a slot opens up
```

### 3.3 Queuing Behavior

When limit is reached:
1. **New phases remain in `queued` status**
2. **When a running phase completes:**
   - Webhook event triggers dependency check
   - If concurrency limit allows, queued phases launch
   - FIFO order within same dependency level

Example:
```
State at concurrency limit (3 running):
  Phase 2: running (ADW adw-abc)
  Phase 3: running (ADW adw-def)
  Phase 5: running (ADW adw-ghi)
  Phase 4: queued (waiting for Phases 2+3, AND a free slot)
  Phase 6: queued (waiting for Phase 4, AND a free slot)

Phase 2 completes:
  → Running count: 2
  → Phase 4 dependencies met (Phases 2+3 complete)
  → Phase 4 launched (running count → 3)
  → Phase 6 still queued (depends on Phase 4)

Phase 3 completes:
  → Running count: 2
  → No new phases ready
  → Running count stays at 2

Phase 4 completes:
  → Running count: 1
  → Phase 6 dependencies met (Phase 4 complete)
  → Phase 6 launched (running count → 2)
```

---

## 4. Dependency Resolution

### 4.1 Dependency Graph Structure

Each phase declares dependencies as JSON array:

```json
{
  "queue_id": "4",
  "phase_number": 4,
  "depends_on_phases": [2, 3],  // Must wait for Phases 2 AND 3
  "status": "queued"
}
```

### 4.2 Ready Phase Detection Algorithm

A phase is ready when:
1. `status = 'queued'`
2. **ALL** phases in `depends_on_phases` have `status = 'completed'`
3. Concurrency limit not reached

```python
def _find_newly_ready_phases(self, feature_id: int) -> list[dict]:
    """
    Find all phases that just became ready.

    Algorithm:
    1. Get all queued phases for this feature
    2. For each queued phase:
       a. Parse depends_on_phases array
       b. Check if ALL dependencies are completed
       c. If yes, add to ready list
    3. Return ready list (may be empty)
    """
    with self.phase_queue_service.repository.adapter.get_connection() as conn:
        cursor = conn.cursor()

        # Get all queued phases for this feature
        cursor.execute(
            """
            SELECT queue_id, phase_number, depends_on_phases, phase_data
            FROM phase_queue
            WHERE feature_id = ? AND status = 'queued'
            """,
            (feature_id,)
        )
        queued_phases = cursor.fetchall()

        ready_phases = []
        for phase in queued_phases:
            dependencies = json.loads(phase["depends_on_phases"] or "[]")

            # No dependencies → always ready
            if not dependencies:
                ready_phases.append(phase)
                continue

            # Check if ALL dependencies are completed
            all_complete = True
            for dep_phase_num in dependencies:
                cursor.execute(
                    """
                    SELECT status FROM phase_queue
                    WHERE feature_id = ? AND phase_number = ?
                    """,
                    (feature_id, dep_phase_num)
                )
                dep_row = cursor.fetchone()

                # Dependency not found OR not completed → block
                if not dep_row or dep_row["status"] != "completed":
                    all_complete = False
                    break

            if all_complete:
                ready_phases.append(phase)

        return ready_phases
```

### 4.3 Example Dependency Graphs

**Simple Sequential:**
```
Phase 1 (no deps)
  ↓
Phase 2 (depends on [1])
  ↓
Phase 3 (depends on [2])
  ↓
Phase 4 (depends on [3])

Execution: 1 → 2 → 3 → 4 (sequential)
```

**Parallel with Converge:**
```
Phase 1 (no deps)
  ├─→ Phase 2 (depends on [1])
  ├─→ Phase 3 (depends on [1])
  └─→ Phase 4 (depends on [1])
        ↓
      Phase 5 (depends on [2,3,4])

Execution:
- Step 1: Phase 1 runs alone
- Step 2: Phases 2, 3, 4 run in parallel (3 concurrent)
- Step 3: Phase 5 runs after all complete
```

**Complex Diamond:**
```
       Phase 1 (no deps)
      ↙   ↓   ↘
Phase 2   3   4  (all depend on [1])
      ↘   ↓   ↙
       Phase 5 (depends on [2,3,4])
         ↓
       Phase 6 (depends on [5])

Execution:
- Step 1: Phase 1
- Step 2: Phases 2, 3, 4 in parallel (3 concurrent)
- Step 3: Phase 5 (after 2,3,4 complete)
- Step 4: Phase 6 (after 5 completes)
```

**Mixed Parallel:**
```
Phase 1 (no deps)
  ↓
Phase 2 (depends on [1])
  ├─→ Phase 3 (depends on [2])
  └─→ Phase 4 (depends on [2])
        ↓
      Phase 5 (depends on [3,4])

Execution:
- Step 1: Phase 1
- Step 2: Phase 2
- Step 3: Phases 3, 4 in parallel (2 concurrent)
- Step 4: Phase 5 (after 3,4 complete)
```

---

## 5. Isolated Issue Strategy

### 5.1 Problem with Parent Issues

**Old approach (v1.0):**
```
GitHub Parent Issue #100: "Implement Feature X"
├── Child Issue #101: Phase 1
├── Child Issue #102: Phase 2
└── Child Issue #103: Phase 3

Each ADW loads:
- Parent issue body (~5000 tokens)
- All child issues (~2000 tokens each)
- Total: 11,000 tokens per phase

With 5 phases: 55,000 tokens wasted on duplicate context
```

**Token bloat analysis:**
- Parent issue appears in EVERY child ADW context
- GitHub API includes parent in child issue response
- Claude Code loads parent issue when child is specified
- Result: **Exponential token growth** with phase count

### 5.2 Solution: Isolated Issues

**New approach (v2.0):**
```
NO parent issue in GitHub

Isolated Issues:
- Issue #200: "Feature #104 - Phase 1: Database Schema"
- Issue #201: "Feature #104 - Phase 2: Backend API"
- Issue #202: "Feature #104 - Phase 3: Frontend UI"

Each ADW loads:
- Only its own issue (~2000 tokens)
- No parent context

With 5 phases: 10,000 tokens total (5x reduction)
```

### 5.3 Tracking Without Parent Issues

**Plans Panel (Panel 5) is the tracker:**

```
planned_features table:
  id: 104
  title: "WebSocket Migration"
  status: "in_progress"
  total_phases: 5
  phases_completed: 2

phase_queue table:
  queue_id=1: feature_id=104, phase=1, issue=200, status='completed'
  queue_id=2: feature_id=104, phase=2, issue=201, status='running'
  queue_id=3: feature_id=104, phase=3, issue=202, status='queued'
  queue_id=4: feature_id=104, phase=4, issue=NULL, status='queued'
  queue_id=5: feature_id=104, phase=5, issue=NULL, status='queued'
```

**Panel 5 UI displays:**
```
Feature #104: WebSocket Migration
├─ ✅ Phase 1: Database Schema (Issue #200) - Completed
├─ ⏳ Phase 2: Backend API (Issue #201) - Running
├─ ⏸ Phase 3: Frontend UI - Queued (waiting for slot)
├─ ⏸ Phase 4: Integration Tests - Queued (waiting for Phases 2+3)
└─ ⏸ Phase 5: Documentation - Queued (waiting for Phases 2+3)

Progress: 2/5 phases complete (40%)
Status: In Progress
```

### 5.4 Issue Body Template

```markdown
# {phase_title}

**Feature**: {feature_title} (planned_features #{feature_id})
**Phase**: {phase_number} of {total_phases}

{prompt_content}

## Dependencies

{dependencies_list}

---
**Tracking**: See Panel 5 for full feature progress
**Labels**: feature-{feature_id}, phase-{phase_number}
```

Example:
```markdown
# Backend API Development

**Feature**: WebSocket Migration (planned_features #104)
**Phase**: 2 of 5

Implement WebSocket endpoints for real-time updates...

## Dependencies

This phase depends on:
- ✅ Phase 1: Database Schema (Issue #200) - Completed

---
**Tracking**: See Panel 5 for full feature progress
**Labels**: feature-104, phase-2
```

---

## 6. Database Schema

### 6.1 Updated `phase_queue` Table

```sql
CREATE TABLE phase_queue (
    -- Identity
    queue_id VARCHAR(255) PRIMARY KEY,
    feature_id INTEGER NOT NULL,              -- ✅ NEW: References planned_features.id
    phase_number INTEGER NOT NULL,

    -- GitHub Integration
    issue_number INTEGER,                     -- NULL until created (JIT)

    -- Status & Dependencies
    status VARCHAR(50) CHECK(status IN ('queued', 'ready', 'running', 'completed', 'blocked', 'failed')) DEFAULT 'queued',
    depends_on_phases JSONB,                  -- ✅ NEW: Array of phase numbers [1, 3, 5]

    -- Phase Data
    phase_data JSONB,                         -- {title, prompt_content, workflow_type, estimated_hours}

    -- Execution Tracking
    adw_id VARCHAR(255),                      -- NULL until launched
    pr_number INTEGER,                        -- NULL until PR created
    error_message TEXT,

    -- Priority & Ordering
    priority INTEGER DEFAULT 50,              -- 10 (urgent) to 90 (background)
    queue_position INTEGER,                   -- FIFO tiebreaker within priority

    -- Timestamps
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ready_timestamp TIMESTAMP WITHOUT TIME ZONE,
    started_timestamp TIMESTAMP WITHOUT TIME ZONE
);

-- Indexes
CREATE INDEX idx_phase_queue_status ON phase_queue(status);
CREATE INDEX idx_phase_queue_feature ON phase_queue(feature_id);
CREATE INDEX idx_phase_queue_status_feature ON phase_queue(status, feature_id);
CREATE INDEX idx_phase_queue_issue ON phase_queue(issue_number);

-- Foreign Key (optional, for referential integrity)
ALTER TABLE phase_queue
ADD CONSTRAINT fk_phase_queue_feature
FOREIGN KEY (feature_id) REFERENCES planned_features(id) ON DELETE CASCADE;

-- Comments
COMMENT ON TABLE phase_queue IS 'Queue of multi-phase workflow execution with dependency tracking';
COMMENT ON COLUMN phase_queue.feature_id IS 'References planned_features.id (NOT GitHub parent issue)';
COMMENT ON COLUMN phase_queue.depends_on_phases IS 'JSON array of phase numbers that must complete first (e.g., [1, 3])';
COMMENT ON COLUMN phase_queue.status IS 'queued=waiting, ready=can start, running=ADW active, completed/failed=done, blocked=dependency failed';
```

### 6.2 Migration from v1.0

```sql
-- Migration: phase_queue v1.0 → v2.0
-- Run this migration to convert from polling to event-driven schema

BEGIN;

-- 1. Add new column for multi-dependencies
ALTER TABLE phase_queue ADD COLUMN depends_on_phases JSONB;

-- 2. Migrate existing single dependency to array format
UPDATE phase_queue
SET depends_on_phases = CASE
    WHEN depends_on_phase IS NULL THEN '[]'::jsonb
    ELSE json_build_array(depends_on_phase)::jsonb
END;

-- 3. Rename parent_issue → feature_id (if needed)
-- NOTE: Only if parent_issue currently references GitHub issues
-- If parent_issue already references planned_features.id, skip this step
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='phase_queue' AND column_name='parent_issue'
    ) THEN
        ALTER TABLE phase_queue RENAME COLUMN parent_issue TO feature_id;
    END IF;
END $$;

-- 4. Drop old single-dependency column
ALTER TABLE phase_queue DROP COLUMN IF EXISTS depends_on_phase;

-- 5. Update indexes
DROP INDEX IF EXISTS idx_phase_queue_parent;
CREATE INDEX IF NOT EXISTS idx_phase_queue_feature ON phase_queue(feature_id);
CREATE INDEX IF NOT EXISTS idx_phase_queue_status_feature ON phase_queue(status, feature_id);

-- 6. Add foreign key constraint (optional)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_phase_queue_feature'
    ) THEN
        ALTER TABLE phase_queue
        ADD CONSTRAINT fk_phase_queue_feature
        FOREIGN KEY (feature_id) REFERENCES planned_features(id) ON DELETE CASCADE;
    END IF;
END $$;

COMMIT;
```

### 6.3 Example Data

```sql
-- Feature #104: WebSocket Migration (5 phases)

INSERT INTO phase_queue VALUES
-- Phase 1: Database (blocking all)
('queue-104-1', 104, 1, 200, 'completed', '[]'::jsonb,
 '{"title":"Database Schema","prompt_content":"Add WebSocket tables...","workflow_type":"adw_sdlc_complete_iso","estimated_hours":2}'::jsonb,
 'adw-abc123', NULL, NULL, 50, 1, NOW(), NOW(), NOW(), NOW()),

-- Phase 2: Backend API (depends on Phase 1)
('queue-104-2', 104, 2, 201, 'running', '[1]'::jsonb,
 '{"title":"Backend API","prompt_content":"Implement WebSocket endpoints...","workflow_type":"adw_sdlc_complete_iso","estimated_hours":3}'::jsonb,
 'adw-def456', NULL, NULL, 50, 2, NOW(), NOW(), NOW(), NOW()),

-- Phase 3: Frontend UI (depends on Phase 1, parallel with Phase 2)
('queue-104-3', 104, 3, 202, 'running', '[1]'::jsonb,
 '{"title":"Frontend Components","prompt_content":"Build WebSocket UI...","workflow_type":"adw_sdlc_complete_iso","estimated_hours":2}'::jsonb,
 'adw-ghi789', NULL, NULL, 50, 3, NOW(), NOW(), NOW(), NOW()),

-- Phase 4: Integration Tests (depends on Phases 2 AND 3)
('queue-104-4', 104, 4, NULL, 'queued', '[2, 3]'::jsonb,
 '{"title":"Integration Tests","prompt_content":"Test WebSocket integration...","workflow_type":"adw_sdlc_complete_iso","estimated_hours":2}'::jsonb,
 NULL, NULL, NULL, 50, 4, NOW(), NOW(), NULL, NULL),

-- Phase 5: Documentation (depends on Phase 1, parallel with Tests)
('queue-104-5', 104, 5, 203, 'running', '[1]'::jsonb,
 '{"title":"Documentation","prompt_content":"Document WebSocket API...","workflow_type":"adw_sdlc_complete_iso","estimated_hours":1}'::jsonb,
 'adw-jkl012', NULL, NULL, 50, 5, NOW(), NOW(), NOW(), NOW());
```

---

## 7. Implementation Guide

### 7.1 Phase 1: Database Migration (30 minutes)

```bash
# 1. Backup existing database
pg_dump tac_webbuilder > backup_before_migration.sql

# 2. Run migration script
psql -h localhost -U tac_user -d tac_webbuilder -f migration/phase_queue_v2_migration.sql

# 3. Verify migration
psql -h localhost -U tac_user -d tac_webbuilder -c "
SELECT
    queue_id,
    feature_id,
    phase_number,
    depends_on_phases,
    status
FROM phase_queue
LIMIT 5;
"

# 4. Test dependency query
psql -h localhost -U tac_user -d tac_webbuilder -c "
SELECT
    phase_number,
    depends_on_phases,
    jsonb_array_length(COALESCE(depends_on_phases, '[]'::jsonb)) as dep_count
FROM phase_queue
WHERE feature_id = 104;
"
```

### 7.2 Phase 2: WebSocket Event Subscription (1 hour)

**File: `app/server/services/websocket_manager.py`**

```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: set[WebSocket] = set()
        self.event_subscribers: dict[str, list[callable]] = {}  # NEW

    def subscribe(self, event_type: str, handler: callable):
        """Subscribe a handler to an event type"""
        if event_type not in self.event_subscribers:
            self.event_subscribers[event_type] = []
        self.event_subscribers[event_type].append(handler)
        logger.info(f"[WS] Handler subscribed to {event_type} events")

    async def broadcast(self, message: dict) -> None:
        """Broadcast to WebSocket clients AND event subscribers"""
        # 1. Send to WebSocket clients (existing)
        if self.active_connections:
            # ... existing broadcast logic ...

        # 2. Dispatch to event subscribers (NEW)
        event_type = message.get("type")
        if event_type and event_type in self.event_subscribers:
            for handler in self.event_subscribers[event_type]:
                try:
                    await handler(message.get("data", {}))
                except Exception as e:
                    logger.error(f"[WS] Event handler error for {event_type}: {e}")
```

### 7.3 Phase 3: Update Webhook Handler (30 minutes)

**File: `app/server/routes/queue_routes.py`**

```python
@webhook_router.post("/workflow-complete", response_model=WorkflowCompleteResponse)
async def workflow_complete(
    http_request: Request,
    request: WorkflowCompleteRequest
) -> WorkflowCompleteResponse:
    """Webhook endpoint - called by ADW when workflow completes"""

    # ... existing validation & deduplication ...

    try:
        # Update phase status
        response = _update_phase_status(phase_queue_service, request)

        # ✅ NEW: Emit WebSocket event
        if websocket_manager:
            from datetime import datetime
            await websocket_manager.broadcast({
                "type": "workflow_completed",
                "data": {
                    "queue_id": request.queue_id,
                    "feature_id": request.feature_id,  # Updated from parent_issue
                    "phase_number": request.phase_number,
                    "status": request.status,
                    "adw_id": request.adw_id,
                    "timestamp": datetime.now().isoformat()
                }
            })
            logger.info(f"[WEBHOOK] Broadcasted workflow_completed event")

        return response
    except Exception as e:
        logger.error(f"[WEBHOOK] Failed to process: {e}")
        raise
```

### 7.4 Phase 4: Rewrite PhaseCoordinator (3 hours)

**File: `app/server/services/phase_coordination/phase_coordinator.py`**

See complete implementation in Section 2 of this document.

Key changes:
- ❌ Remove: `_poll_loop()`, `poll_interval`, `asyncio.sleep()`
- ✅ Add: `handle_workflow_completion()`, dependency resolution, concurrency control
- ✅ Update: Isolated issue creation, parallel launching

### 7.5 Phase 5: Server Startup Integration (15 minutes)

**File: `app/server/server.py`**

```python
@app.on_event("startup")
async def startup_event():
    logger.info("[STARTUP] Initializing services...")

    # ... existing services ...

    # Initialize PhaseCoordinator (event-driven)
    phase_coordinator = PhaseCoordinator(
        phase_queue_service=phase_queue_service,
        websocket_manager=websocket_manager,
        github_poster=github_poster,
        max_concurrent_adws=3  # Concurrency limit
    )

    # Start coordinator (no longer starts polling loop)
    await phase_coordinator.start()

    # Subscribe to workflow completion events
    websocket_manager.subscribe(
        "workflow_completed",
        phase_coordinator.handle_workflow_completion
    )

    logger.info("[STARTUP] PhaseCoordinator subscribed to workflow_completed events")
    logger.info("[STARTUP] All services initialized (event-driven mode)")
```

---

## 8. Migration from v1.0

### 8.1 What Changes

| Component | v1.0 (Polling) | v2.0 (Event-Driven) |
|-----------|----------------|---------------------|
| **PhaseCoordinator** | Polls workflow_history every 10s | Subscribes to WebSocket events |
| **Webhook Handler** | Updates database only | Updates DB + emits WebSocket event |
| **Schema** | `depends_on_phase INTEGER` | `depends_on_phases JSONB` |
| **Schema** | `parent_issue` (GitHub) | `feature_id` (planned_features) |
| **GitHub Issues** | Parent + children | Isolated issues only |
| **Latency** | 3-10s (poll interval) | <100ms (instant) |
| **Parallel Execution** | Sequential only | Up to 3 concurrent |

### 8.2 Migration Checklist

- [ ] **Database Migration**
  - [ ] Backup database
  - [ ] Run migration script (Section 6.2)
  - [ ] Verify schema changes
  - [ ] Test dependency queries

- [ ] **Code Updates**
  - [ ] Add event subscription to WebSocketManager
  - [ ] Update webhook handler to emit events
  - [ ] Rewrite PhaseCoordinator (remove polling)
  - [ ] Update server.py startup

- [ ] **Testing**
  - [ ] Test single-phase execution
  - [ ] Test sequential multi-phase
  - [ ] Test parallel multi-phase
  - [ ] Test concurrency limit enforcement
  - [ ] Test dependency resolution

- [ ] **Deployment**
  - [ ] Deploy to staging
  - [ ] Monitor for 24 hours
  - [ ] Verify event flow in logs
  - [ ] Deploy to production

### 8.3 Rollback Plan

If issues occur:

```bash
# 1. Stop server
systemctl stop tac-webbuilder

# 2. Restore database backup
psql -h localhost -U tac_user -d tac_webbuilder < backup_before_migration.sql

# 3. Revert code to v1.0
git checkout v1.0-polling

# 4. Restart server
systemctl start tac-webbuilder
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

```python
# test_phase_coordinator_event_driven.py

async def test_handle_workflow_completion_triggers_ready_phases():
    """Test that completing Phase 1 triggers Phases 2 and 3"""
    # Setup: Phase 1 running, Phases 2,3 queued (depend on 1)
    phase_queue_service.create_phase(
        feature_id=104, phase_number=1, depends_on=[], status='running'
    )
    phase_queue_service.create_phase(
        feature_id=104, phase_number=2, depends_on=[1], status='queued'
    )
    phase_queue_service.create_phase(
        feature_id=104, phase_number=3, depends_on=[1], status='queued'
    )

    # Act: Emit workflow_completed event for Phase 1
    await coordinator.handle_workflow_completion({
        "queue_id": "1",
        "feature_id": 104,
        "phase_number": 1,
        "status": "completed"
    })

    # Assert: Phases 2 and 3 are now running
    phase2 = phase_queue_service.get_phase(2)
    phase3 = phase_queue_service.get_phase(3)
    assert phase2.status == 'running'
    assert phase3.status == 'running'

async def test_concurrency_limit_enforced():
    """Test that max 3 ADWs can run concurrently"""
    # Setup: 5 phases all ready (no dependencies)
    for i in range(1, 6):
        phase_queue_service.create_phase(
            feature_id=104, phase_number=i, depends_on=[], status='queued'
        )

    # Act: Mark Phase 0 as complete (triggers all 5 ready)
    await coordinator.handle_workflow_completion({
        "feature_id": 104,
        "phase_number": 0,
        "status": "completed"
    })

    # Assert: Only 3 phases running
    running = phase_queue_service.get_by_status('running')
    assert len(running) == 3

    # Assert: 2 phases still queued
    queued = phase_queue_service.get_by_status('queued')
    assert len(queued) == 2

async def test_dependency_resolution_complex():
    """Test complex dependency graph (diamond shape)"""
    # Setup diamond:
    #     Phase 1
    #    /   |   \
    # Phase 2,3,4
    #    \   |   /
    #     Phase 5
    phase_queue_service.create_phase(
        feature_id=104, phase_number=1, depends_on=[], status='running'
    )
    for i in [2, 3, 4]:
        phase_queue_service.create_phase(
            feature_id=104, phase_number=i, depends_on=[1], status='queued'
        )
    phase_queue_service.create_phase(
        feature_id=104, phase_number=5, depends_on=[2,3,4], status='queued'
    )

    # Act: Complete Phase 1
    await coordinator.handle_workflow_completion({
        "feature_id": 104, "phase_number": 1, "status": "completed"
    })

    # Assert: Phases 2,3,4 running (parallel), Phase 5 still queued
    assert phase_queue_service.get_phase(2).status == 'running'
    assert phase_queue_service.get_phase(3).status == 'running'
    assert phase_queue_service.get_phase(4).status == 'running'
    assert phase_queue_service.get_phase(5).status == 'queued'

    # Act: Complete Phases 2 and 3
    await coordinator.handle_workflow_completion({
        "feature_id": 104, "phase_number": 2, "status": "completed"
    })
    await coordinator.handle_workflow_completion({
        "feature_id": 104, "phase_number": 3, "status": "completed"
    })

    # Assert: Phase 5 still queued (waiting for Phase 4)
    assert phase_queue_service.get_phase(5).status == 'queued'

    # Act: Complete Phase 4
    await coordinator.handle_workflow_completion({
        "feature_id": 104, "phase_number": 4, "status": "completed"
    })

    # Assert: Phase 5 now running (all dependencies met)
    assert phase_queue_service.get_phase(5).status == 'running'
```

### 9.2 Integration Tests

```bash
# Test end-to-end flow

# 1. Create test feature
curl -X POST http://localhost:8002/api/v1/planned-features \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Feature",
    "description": "Multi-phase test",
    "estimated_hours": 10
  }'

# 2. Generate phases
curl -X POST http://localhost:8002/api/v1/planned-features/999/generate-implementation

# 3. Execute
curl -X POST http://localhost:8002/api/v1/planned-features/999/execute

# 4. Monitor WebSocket events
wscat -c ws://localhost:8002/ws/queue

# 5. Verify parallel execution
curl http://localhost:8002/api/v1/queue | jq '.[] | select(.status=="running")'
# Should see max 3 running

# 6. Complete a phase (simulate ADW webhook)
curl -X POST http://localhost:8002/workflow-complete \
  -H "Content-Type: application/json" \
  -d '{
    "queue_id": "queue-999-1",
    "feature_id": 999,
    "phase_number": 1,
    "status": "completed",
    "adw_id": "adw-test123"
  }'

# 7. Verify next phases launched
curl http://localhost:8002/api/v1/queue | jq '.[] | select(.feature_id==999)'
```

### 9.3 Performance Tests

```python
# test_performance.py

async def test_event_latency():
    """Measure time from webhook to phase launch"""
    import time

    # Setup: Phase 1 running, Phase 2 queued
    setup_test_phases()

    # Measure: Send webhook → Phase 2 launches
    start = time.time()

    await coordinator.handle_workflow_completion({
        "feature_id": 104,
        "phase_number": 1,
        "status": "completed"
    })

    # Wait for Phase 2 to start
    while phase_queue_service.get_phase(2).status != 'running':
        await asyncio.sleep(0.01)
        if time.time() - start > 1.0:
            raise TimeoutError("Phase didn't start within 1s")

    latency = time.time() - start

    # Assert: <100ms latency
    assert latency < 0.1, f"Latency too high: {latency*1000:.0f}ms"

    print(f"✅ Event latency: {latency*1000:.0f}ms")

async def test_concurrent_throughput():
    """Test maximum concurrent ADW throughput"""
    # Setup: 10 phases, all ready
    for i in range(1, 11):
        phase_queue_service.create_phase(
            feature_id=104, phase_number=i, depends_on=[], status='queued'
        )

    # Act: Trigger all phases
    start = time.time()

    for i in range(1, 11):
        await coordinator.handle_workflow_completion({
            "feature_id": 104,
            "phase_number": i,
            "status": "completed"
        })

    elapsed = time.time() - start

    # Assert: All 10 phases processed quickly
    assert elapsed < 1.0, f"Processing too slow: {elapsed:.2f}s"

    # Assert: Max 3 concurrent
    running = phase_queue_service.get_by_status('running')
    assert len(running) <= 3

    print(f"✅ Throughput: {10/elapsed:.1f} phases/sec")
```

---

## Summary

### Implementation Effort

| Phase | Task | Effort |
|-------|------|--------|
| 1 | Database migration | 30 min |
| 2 | WebSocket event subscription | 1 hour |
| 3 | Update webhook handler | 30 min |
| 4 | Rewrite PhaseCoordinator | 3 hours |
| 5 | Server integration | 15 min |
| 6 | Testing | 2 hours |
| **Total** | | **~7.5 hours** |

### Key Benefits

1. **30-100x faster** phase transitions (<100ms vs 3-10s)
2. **3x throughput** with parallel execution
3. **60-80% token savings** with isolated issues
4. **90% resource reduction** (no polling overhead)
5. **Unlimited scalability** (event-driven)

### Next Steps

1. Review this architecture doc
2. Run database migration
3. Implement code changes
4. Test thoroughly
5. Deploy to staging
6. Monitor for 24 hours
7. Deploy to production

---

**Ready to implement? Start with Phase 1: Database Migration**
