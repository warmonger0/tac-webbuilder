# Multi-Phase Upload Feature - Session 3 Continuation Prompt

## Context: What Has Been Completed

You are continuing implementation of a multi-phase markdown file upload feature for the tac-webbuilder application. **Phases 1 and 2 are COMPLETE**.

### Feature Overview

When uploading multi-phase .md files via "Create New Request":
- Parse and separate phases automatically ✅ (Phase 1)
- Create parent/child GitHub issues ✅ (Phase 2)
- Queue phases with dependencies ✅ (Phase 2)
- Display queued phases in UI ⏳ (Phase 3 - NEXT)
- Execute phases sequentially ⏳ (Phase 3 - NEXT)
- Monitor execution progress ⏳ (Phase 3 - NEXT)

### Phase 1 Complete: Client-Side Phase Parsing & Preview ✅

**Commit:** d4a8f02 (merged to main, pushed to origin)

**Files Created:**
1. `app/client/src/utils/phaseParser.ts` (227 lines)
   - Flexible regex: `/^(#{1,6})\s+Phase\s*[:\-]?\s*(\d+|One|Two|...)?(?:[:\-]\s*)?(.*)$/im`
   - Word-to-number conversion (One→1, Two→2, etc.)
   - External doc extraction: `/(?:see|refer to|...)(?:\s+the)?\s+([...]+\.md)/gi`
   - Validation: Phase 1 required, no gaps, no duplicates, max 20 phases

2. `app/client/src/components/PhasePreview.tsx` (194 lines)
   - Modal with blue header, phase count
   - PhaseCard components: badges, titles, content preview, external docs
   - Validation warnings/errors display
   - Confirm/Cancel actions

3. `app/client/src/utils/__tests__/phaseParser.test.ts` (472 lines)
   - 29 tests covering parsing, validation, edge cases
   - ✅ ALL TESTS PASSING

**Files Modified:**
4. `app/client/src/components/RequestForm.tsx`
   - Phase detection on file upload (drag-and-drop + file picker)
   - PhasePreview integration
   - Multi-phase submission handler

### Phase 2 Complete: Backend Queue System ✅

**Commit:** d4a8f02 (merged to main, pushed to origin)

**Files Created:**
1. `app/server/services/phase_queue_service.py` (561 lines)
   - `PhaseQueueService` class: enqueue, dequeue, mark_complete, mark_failed, mark_blocked
   - `PhaseQueueItem` dataclass
   - SQLite persistence with dependency tracking
   - Sequential execution coordination

2. `app/server/routes/queue_routes.py` (159 lines)
   - `GET /api/queue` - List all queued phases
   - `GET /api/queue/{parent_issue}` - Get phases for parent
   - `POST /api/queue/enqueue` - Enqueue phase
   - `DELETE /api/queue/{queue_id}` - Remove phase

3. `app/server/tests/services/test_phase_queue_service.py` (283 lines)
   - 13 comprehensive tests for queue operations
   - Dependency tracking, completion, failure, blocking

4. `app/server/db/migrations/007_add_phase_queue.sql` (19 lines)
   - Created `phase_queue` table with status tracking
   - Indexes on status, parent_issue, issue_number

5. `app/server/db/migrations/008_update_workflow_history_phase_fields.sql` (12 lines)
   - Documents existing columns: phase_number, parent_workflow_id, is_multi_phase

**Files Modified:**
6. `app/server/core/data_models.py`
   - Added `Phase`, `ChildIssueInfo` models
   - Updated `SubmitRequestData` with `phases?: List[Phase]`
   - Updated `SubmitRequestResponse` with multi-phase fields

7. `app/server/services/github_issue_service.py`
   - Added `_handle_multi_phase_request()` method (145 lines)
   - Creates parent issue + child issues
   - Enqueues phases with dependencies
   - Links issues via references

8. `app/server/server.py`
   - Initialized `PhaseQueueService`
   - Registered queue routes
   - Injected into `GitHubIssueService`

9. `app/client/src/types/api.types.ts`
   - Added `Phase`, `ChildIssueInfo` interfaces
   - Updated request/response types

**Status:**
- ✅ Database migrations applied
- ✅ Backend imports verified
- ✅ TypeScript compilation clean
- ✅ 42 unit tests written (29 frontend + 13 backend)
- ✅ Git committed, merged to main, pushed to origin

---

## What Needs to Be Done Next: Phase 3 - Queue Display & Execution Coordinator

### Overview

Implement frontend queue display and backend execution coordination to enable sequential phase execution with real-time monitoring.

### Tasks Remaining

**Frontend (TypeScript/React):**

1. **PhaseQueueCard Component** (`app/client/src/components/PhaseQueueCard.tsx`)
   - Display individual phase in queue
   - Show: phase number, title, status badge, parent issue link, execution order
   - Color-coded status:
     - Gray: queued (waiting for dependency)
     - Blue: ready (can execute now)
     - Yellow: running (currently executing)
     - Green: completed (done successfully)
     - Red: failed (execution failed)
     - Orange: blocked (dependency failed)
   - Click to view GitHub issue
   - Show dependency chain ("After Phase N")

2. **Update ZteHopperQueueCard** (`app/client/src/components/ZteHopperQueueCard.tsx`)
   - Replace "Queue Empty" placeholder
   - Fetch queue data: `GET /api/queue`
   - Render stacked cards (bottom = current/ready, above = queued)
   - WebSocket subscription for real-time updates
   - Show phase count and parent issue
   - Visual dependency indicators
   - Refresh on queue changes

3. **Queue API Client Functions** (`app/client/src/api/client.ts`)
   - `getQueueAll()` - Fetch all phases
   - `getQueueByParent(parentIssue)` - Fetch phases for parent
   - `dequeuePhase(queueId)` - Cancel phase

**Backend (Python):**

4. **PhaseCoordinator Service** (`app/server/services/phase_coordinator.py`)
   - Background task: poll workflow completions every 10 seconds
   - Monitor `workflow_history` for completed/failed workflows
   - On workflow completion:
     - Find corresponding phase in `phase_queue` by `issue_number`
     - If success: `mark_phase_complete(queue_id)` → trigger next phase
     - If failure: `mark_phase_failed(queue_id)` → block dependents
   - On phase transition:
     - Broadcast WebSocket event to frontend
     - Post GitHub comment on parent issue with progress

5. **Integrate PhaseCoordinator** (`app/server/server.py`)
   - Initialize `PhaseCoordinator` service
   - Register with `BackgroundTaskManager`
   - Start polling on app startup

6. **Update Webhook Trigger** (`adws/adw_triggers/trigger_webhook.py`)
   - Before starting ADW workflow:
     - Query `phase_queue` for this `issue_number`
     - Check if `status == 'ready'`
     - If not ready: skip execution, return early
   - After workflow completion:
     - Notify `PhaseCoordinator` via HTTP callback
     - Or: rely on polling (simpler, no callback needed)

7. **WebSocket Events** (`app/server/routes/websocket_routes.py`)
   - Add `queue_update` event type
   - Broadcast on phase status changes
   - Payload: `{type: 'queue_update', queue_id, status, parent_issue}`

---

## Phase 4 - Testing & Documentation

**Integration Tests:**

8. **Multi-Phase Flow Test** (`app/client/src/__tests__/integration/multi-phase-flow.test.ts`)
   - Upload 3-phase markdown
   - Verify preview shows 3 phases
   - Submit and verify issues created
   - Verify queue populated

**E2E Tests:**

9. **Phase Execution Test** (`tests/e2e/test_multi_phase_execution.py`)
   - Create 3-phase parent issue
   - Mock webhook triggers
   - Verify Phase 1 executes
   - Verify Phase 2 waits for Phase 1
   - Verify Phase 3 waits for Phase 2
   - Test failure: Phase 1 fails → Phase 2+3 blocked

**Documentation:**

10. **API Documentation**
    - Update OpenAPI/Swagger specs
    - Document queue endpoints
    - Add multi-phase submission examples

11. **User Guide**
    - How to create multi-phase markdown
    - Phase header format examples
    - External doc reference syntax
    - Queue monitoring guide

---

## Current Working Directory

```
/Users/Warmonger0/tac/tac-webbuilder
```

**Important Files:**
- Phase parser: `app/client/src/utils/phaseParser.ts`
- Phase preview: `app/client/src/components/PhasePreview.tsx`
- Queue service: `app/server/services/phase_queue_service.py`
- Queue routes: `app/server/routes/queue_routes.py`
- GitHub service: `app/server/services/github_issue_service.py`

---

## Database Schema

### phase_queue Table (Already Created)
```sql
CREATE TABLE phase_queue (
  queue_id TEXT PRIMARY KEY,
  parent_issue INTEGER NOT NULL,
  phase_number INTEGER NOT NULL,
  issue_number INTEGER,  -- Filled after GitHub issue created
  status TEXT CHECK(status IN ('queued', 'ready', 'running', 'completed', 'blocked', 'failed')),
  depends_on_phase INTEGER,
  phase_data TEXT,  -- JSON: {title, content, externalDocs}
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  error_message TEXT
);

CREATE INDEX idx_phase_queue_status ON phase_queue(status);
CREATE INDEX idx_phase_queue_parent ON phase_queue(parent_issue);
CREATE INDEX idx_phase_queue_issue ON phase_queue(issue_number);
```

### workflow_history Columns (Already Added)
- `phase_number INTEGER`
- `parent_workflow_id TEXT`
- `is_multi_phase BOOLEAN`

---

## How to Continue

**Start with Phase 3 - Queue Display & Execution Coordinator:**

```
I'm continuing the multi-phase upload feature implementation. Phases 1 and 2 are complete and merged to main.

Please proceed with Phase 3: Queue Display & Execution Coordinator. Start by creating:

1. PhaseQueueCard component for displaying individual phases
2. Update ZteHopperQueueCard to fetch and display queued phases
3. Create PhaseCoordinator service for background execution monitoring
4. Add WebSocket events for real-time queue updates

Follow the specifications in docs/implementation/CONTINUATION-PROMPT-multi-phase-upload-session-3.md.
```

---

## Key Design Decisions (Already Made)

1. **Phase Detection:** Flexible headers (any `## Phase`, `# Phase One`, `### Phase:`)
2. **Issue Strategy:** Separate GitHub issues (parent + children)
3. **Execution Model:** Queue phases, execute sequentially when dependencies met
4. **Status Tracking:** queued → ready → running → completed/failed/blocked
5. **External Docs:** Pass file paths to ADW (read from project_path)
6. **Failure Handling:** Failed phase blocks all subsequent phases
7. **Auto-Post:** Multi-phase requests skip preview/confirm (already confirmed in PhasePreview)

---

## Testing Commands

```bash
# Backend tests
cd /Users/Warmonger0/tac/tac-webbuilder
uv run python -m pytest app/server/tests/services/test_phase_queue_service.py -v

# Frontend tests
cd /Users/Warmonger0/tac/tac-webbuilder/app/client
bun run test src/utils/__tests__/phaseParser.test.ts --run

# TypeScript compilation
cd /Users/Warmonger0/tac/tac-webbuilder/app/client
bun run typecheck

# Backend imports
cd /Users/Warmonger0/tac/tac-webbuilder/app/server
uv run python -c "from services.phase_queue_service import PhaseQueueService; ..."
```

---

## Current Git Status

**Branch:** main
**Latest Commit:** d4a8f02 (feat: Implement multi-phase upload feature (Phases 1 & 2))
**Pushed to Origin:** ✅ Yes

**Next Branch Recommendation:**
```bash
git checkout -b feature/multi-phase-upload-phase3
```

---

## Expected Phase 3 Deliverables

**Frontend:**
- PhaseQueueCard.tsx (NEW)
- ZteHopperQueueCard.tsx (MODIFIED)
- API client queue functions (MODIFIED)

**Backend:**
- PhaseCoordinator service (NEW)
- WebSocket queue events (MODIFIED)
- Background task registration (MODIFIED)

**Tests:**
- PhaseCoordinator tests (NEW)
- WebSocket integration tests (NEW)
- Queue display component tests (NEW)

**Expected LOC:** ~800-1000 lines total

---

## Hints for Implementation

### PhaseQueueCard Component Structure
```typescript
interface PhaseQueueCardProps {
  queueItem: {
    queue_id: string;
    parent_issue: number;
    phase_number: number;
    issue_number?: number;
    status: 'queued' | 'ready' | 'running' | 'completed' | 'blocked' | 'failed';
    phase_data: {
      title: string;
      content: string;
      externalDocs?: string[];
    };
  };
}
```

### PhaseCoordinator Polling Logic
```python
async def poll_workflow_completions():
    while True:
        # 1. Get phases with status='running'
        # 2. Check workflow_history for completion
        # 3. If completed: mark_phase_complete()
        # 4. If failed: mark_phase_failed()
        # 5. Broadcast WebSocket event
        await asyncio.sleep(10)
```

### WebSocket Event Format
```json
{
  "type": "queue_update",
  "queue_id": "abc-123",
  "parent_issue": 456,
  "phase_number": 2,
  "status": "ready",
  "timestamp": "2025-11-24T12:34:56Z"
}
```

---

## Success Criteria for Phase 3

- [ ] Queue visible in ZteHopperQueueCard UI
- [ ] Phase status updates in real-time
- [ ] PhaseCoordinator detects workflow completions
- [ ] Phase N completion triggers Phase N+1
- [ ] Failed phases block dependents
- [ ] WebSocket events broadcast correctly
- [ ] GitHub comments posted on phase transitions
- [ ] Manual testing: 3-phase execution works end-to-end

---

**Ready to start Phase 3!** All infrastructure is in place, now we need the UI and execution coordinator.
