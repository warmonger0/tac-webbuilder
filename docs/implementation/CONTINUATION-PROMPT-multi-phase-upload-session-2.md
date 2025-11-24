# Multi-Phase Upload Feature - Session 2 Continuation Prompt

## Context: What Has Been Completed

You are continuing implementation of a multi-phase markdown file upload feature for the tac-webbuilder application. Phase 1 (client-side parsing and preview) is **COMPLETE**.

### Feature Overview

When uploading multi-phase .md files via "Create New Request":
- Parse and separate phases automatically
- Queue phases in order (lowest number first) to hopper
- Display as stacked cards: current phase at bottom, queued phases above
- Each phase references full original document + external docs mentioned
- Execute sequentially (Phase N → Phase N+1 only after successful completion)

### Phase 1 Complete: Client-Side Phase Parsing & Preview ✅

**Files Created:**

1. **`app/client/src/utils/phaseParser.ts`** (237 lines)
   - Flexible regex pattern: `/^(#{1,6})\s+Phase\s*[:\-]?\s*(\d+|One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten)?(?:[:\-]\s*)?(.*)$/im`
   - Supports: `## Phase 1: Title`, `# Phase One - Title`, `### Phase: Setup`, `## Phase 2`
   - Word-to-number conversion (One→1, Two→2, etc.)
   - External doc extraction: `/(?:see|refer to|reference|referenced in|mentioned in|from)(?:\s+the)?\s+([a-zA-Z0-9_\-\/\.]+\.md)/gi`
   - Validation: checks for Phase 1, sequence gaps, duplicates, empty content
   - Line tracking for content extraction

2. **`app/client/src/components/PhasePreview.tsx`** (172 lines)
   - Modal dialog with blue header showing phase count
   - Individual PhaseCard components with:
     - Numbered badges (1, 2, 3...)
     - Title and content preview (200 chars)
     - External document references as blue code tags
     - Execution order badges ("Executes first", "After Phase N")
   - Warning/error display (yellow for warnings, red for errors)
   - Confirm/Cancel actions

3. **`app/client/src/utils/__tests__/phaseParser.test.ts`** (29 tests, all passing ✅)
   - Single-phase detection
   - Multi-phase parsing with flexible patterns
   - Content extraction and line tracking
   - External document reference extraction
   - Validation (missing Phase 1, gaps, duplicates, empty phases)
   - Word-to-number conversion
   - Edge cases (empty files, special chars, long content)

**Files Modified:**

4. **`app/client/src/components/RequestForm.tsx`**
   - Added imports: `PhasePreview`, `parsePhases`, `validatePhases`, `PhaseParseResult`
   - New state: `phasePreview`, `showPhasePreview`
   - Enhanced `useDragAndDrop` callback to detect multi-phase content
   - Enhanced `handleFileInputChange` to detect multi-phase for single-file uploads
   - New handlers: `handlePhasePreviewConfirm`, `handlePhasePreviewCancel`
   - Rendered `<PhasePreview>` modal when `showPhasePreview` is true
   - Removed unused `RejectedFileInfo` import (TypeScript fix)

5. **`app/client/src/hooks/useDragAndDrop.ts`**
   - Removed unused `RejectedFileInfo` import (TypeScript fix)

**Status:**
- ✅ TypeScript compilation: PASS
- ✅ Unit tests (29 tests): ALL PASS
- ✅ Phase preview UI: INTEGRATED
- ✅ Drag-and-drop detection: WORKING
- ✅ File picker detection: WORKING

---

## What Needs to Be Done Next: Phase 2 - Backend Queue System

### Overview

Implement server-side queue management to handle multi-phase issue creation and sequential execution gating.

### Tasks Remaining

**Backend Infrastructure (Python):**

1. **Create PhaseQueue Service** (`app/server/services/phase_queue_service.py`)
   - `PhaseQueue` class with operations:
     - `enqueue(parent_issue, phase_number, phase_data, depends_on)`
     - `dequeue()` - remove from queue
     - `get_next_ready()` - find phases whose dependencies are met
     - `mark_phase_complete(phase_id)` - mark done, check for dependent phases
     - `mark_phase_blocked(phase_id, reason)` - block if parent fails
   - SQLite persistence to `app/server/db/phase_queue.db`
   - Recovery logic (reload queue on server restart)

2. **Database Schema** (`app/server/db/migrations/` or direct SQL)
   ```sql
   CREATE TABLE IF NOT EXISTS phase_queue (
     queue_id TEXT PRIMARY KEY,
     parent_issue INTEGER NOT NULL,
     phase_number INTEGER NOT NULL,
     issue_number INTEGER,  -- NULL until GitHub issue created
     status TEXT CHECK(status IN ('queued', 'ready', 'running', 'completed', 'blocked', 'failed')) DEFAULT 'queued',
     depends_on_phase INTEGER,  -- Phase number that must complete first
     phase_data TEXT,  -- JSON: {title, content, externalDocs}
     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
     error_message TEXT
   );

   CREATE INDEX idx_phase_queue_status ON phase_queue(status);
   CREATE INDEX idx_phase_queue_parent ON phase_queue(parent_issue);
   ```

3. **Update `workflow_history` table**
   ```sql
   ALTER TABLE workflow_history ADD COLUMN phase_number INTEGER;
   ALTER TABLE workflow_history ADD COLUMN parent_workflow_id TEXT;
   ALTER TABLE workflow_history ADD COLUMN is_multi_phase BOOLEAN DEFAULT 0;
   ```

4. **Queue API Routes** (`app/server/routes/queue_routes.py`)
   ```python
   GET  /api/queue              # List all queued phases
   GET  /api/queue/{parent_issue}  # Get phases for specific parent
   POST /api/queue/enqueue      # Add phase to queue
   DELETE /api/queue/{queue_id} # Cancel queued phase
   ```

5. **Extend GitHub Issue Service** (`app/server/services/github_issue_service.py`)
   - Modify `submit_nl_request()` to accept optional `phases: List[Phase]` parameter
   - If phases provided:
     - Create parent GitHub issue with full content + label "multi-phase"
     - For each phase: create child issue with phase content + label "phase-N"
     - Link child issues to parent via issue body or comments
     - Store phase metadata in `structured_input` JSON field
     - Enqueue all phases (Phase 1 as 'ready', others as 'queued')
   - Return `{parent_issue_number, child_issues: [{phase_number, issue_number, queue_id}]}`

6. **Update API Types** (`app/client/src/types/api.types.ts`)
   ```typescript
   interface Phase {
     number: number;
     title: string;
     content: string;
     externalDocs?: string[];
   }

   interface SubmitRequestData {
     nl_input: string;
     project_path?: string;
     auto_post: boolean;
     phases?: Phase[];  // NEW: multi-phase data
   }

   interface SubmitRequestResponse {
     request_id: string;
     is_multi_phase?: boolean;  // NEW
     parent_issue_number?: number;  // NEW
     child_issues?: Array<{  // NEW
       phase_number: number;
       issue_number: number;
       queue_id: string;
     }>;
   }
   ```

7. **API Client Updates** (`app/client/src/api/client.ts`)
   - Update `submitRequest()` to send `phases` array when multi-phase

8. **RequestForm Phase Submission** (`app/client/src/components/RequestForm.tsx`)
   - In `handlePhasePreviewConfirm()`:
     - Convert `phasePreview.phases` to `Phase[]` array
     - Call `submitRequest()` with `phases` parameter
     - Handle multi-phase response (show all created issues)

---

## Phase 3 - Queue Display & Execution Coordinator

**Frontend (TypeScript/React):**

9. **PhaseQueueCard Component** (`app/client/src/components/PhaseQueueCard.tsx`)
   - Display individual phase in queue
   - Show: phase number, title, status badge, parent issue link
   - Color-coded status: gray (queued), blue (ready), yellow (running), green (completed), red (blocked/failed)

10. **Update ZteHopperQueueCard** (`app/client/src/components/ZteHopperQueueCard.tsx`)
    - Replace "Queue Empty" placeholder
    - Fetch queue data: `GET /api/queue`
    - Render stacked cards (bottom = running, above = queued)
    - WebSocket subscription for real-time updates
    - Show dependencies visually

**Backend (Python):**

11. **PhaseCoordinator Service** (`app/server/services/phase_coordinator.py`)
    - Background task: poll workflow completions every 10 seconds
    - When Phase N completes successfully:
      - `phase_queue.mark_phase_complete(queue_id)`
      - Find Phase N+1 in queue
      - If found: mark as 'ready', trigger webhook for Phase N+1 issue
    - When Phase N fails:
      - `phase_queue.mark_phase_blocked(dependent_phase_ids)`
      - Post GitHub comment on parent issue: "Phase N failed, Phase N+1 blocked"

12. **Update Webhook Trigger** (`adws/adw_triggers/trigger_webhook.py`)
    - Before starting ADW workflow:
      - Check if issue is part of multi-phase queue
      - Query `phase_queue` for this issue_number
      - If status != 'ready': skip execution, return early
    - After workflow completion:
      - Notify PhaseCoordinator of completion

---

## Phase 4 - Testing & Documentation

13. **Integration Tests** (`app/client/src/__tests__/integration/multi-phase-flow.test.ts`)
    - Upload 3-phase markdown
    - Verify preview shows 3 phases
    - Submit and verify 3 GitHub issues created
    - Verify queue populated with correct dependencies

14. **E2E Test** (`tests/e2e/test_multi_phase_execution.py`)
    - Create 3-phase parent issue
    - Mock webhook triggers
    - Verify Phase 1 executes
    - Verify Phase 2 only starts after Phase 1 completes
    - Verify Phase 3 only starts after Phase 2 completes
    - Test failure scenario: Phase 1 fails → Phase 2 and 3 blocked

15. **API Documentation**
    - Update OpenAPI/Swagger specs
    - Add examples for multi-phase submission
    - Document queue endpoints

---

## Key Design Decisions Already Made

1. **Phase Detection:** Flexible headers (any `## Phase`, `# Phase`, `### Phase:`)
2. **Issue Strategy:** Separate GitHub issues (one per phase)
3. **Execution Model:** Queue in hopper, execute when prior phase completes
4. **Document References:** Pass file paths to ADW (no separate file storage)
5. **External Docs:** Reference by path (ADW reads from project_path)

---

## Current Working Directory

```
/Users/Warmonger0/tac/tac-webbuilder/app/client
```

**Important Files:**
- Phase parser: `src/utils/phaseParser.ts`
- Phase preview: `src/components/PhasePreview.tsx`
- Request form: `src/components/RequestForm.tsx`
- Tests: `src/utils/__tests__/phaseParser.test.ts`

---

## How to Continue

**Start with Phase 2 - Backend Queue System:**

```
I'm continuing the multi-phase upload feature implementation. Phase 1 (client-side parsing and preview) is complete with all tests passing.

Please proceed with Phase 2: Backend Queue System. Start by creating:

1. PhaseQueue service class in app/server/services/phase_queue_service.py
2. Database schema for phase_queue table
3. Queue API routes in app/server/routes/queue_routes.py

Follow the specifications in docs/implementation/CONTINUATION-PROMPT-multi-phase-upload-session-2.md.
```

---

## Testing Commands

```bash
# Frontend tests
cd /Users/Warmonger0/tac/tac-webbuilder/app/client
bun run typecheck
bun run test src/utils/__tests__/phaseParser.test.ts
bun run test src/components/__tests__/RequestForm.test.tsx

# Backend tests (when implemented)
cd /Users/Warmonger0/tac/tac-webbuilder
uv run pytest app/server/tests/test_phase_queue_service.py -v
```

---

## Current Git Status

Branch: `pr-77-review`

**New Files:**
- `app/client/src/utils/phaseParser.ts`
- `app/client/src/components/PhasePreview.tsx`
- `app/client/src/utils/__tests__/phaseParser.test.ts`

**Modified Files:**
- `app/client/src/components/RequestForm.tsx`
- `app/client/src/hooks/useDragAndDrop.ts`

Consider creating a new branch for backend work:
```bash
git checkout -b feature/multi-phase-upload-backend
```
