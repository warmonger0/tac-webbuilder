# Multi-Phase Upload Feature - Session 4 Continuation Prompt

## Context: What Has Been Completed

You are continuing implementation of a multi-phase markdown file upload feature for the tac-webbuilder application. **Phases 1, 2, and 3 are COMPLETE**.

### Feature Overview

When uploading multi-phase .md files via "Create New Request":
- Parse and separate phases automatically ✅ (Phase 1)
- Create parent/child GitHub issues ✅ (Phase 2)
- Queue phases with dependencies ✅ (Phase 2)
- Display queued phases in UI ✅ (Phase 3)
- Execute phases sequentially ✅ (Phase 3)
- Monitor execution progress ✅ (Phase 3)
- Test and document feature ⏳ (Phase 4 - NEXT)

### Phase 1 Complete: Client-Side Phase Parsing & Preview ✅

**Commit:** e85581c (merged to main, pushed to origin)

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

### Phase 3 Complete: Queue Display & Execution Coordinator ✅

**Commit:** b1f7754 (pushed to origin/main)

**Files Created:**
1. `app/client/src/components/PhaseQueueCard.tsx` (245 lines)
   - PhaseQueueCard component with color-coded status indicators
   - PhaseQueueList component for scrollable phase display
   - Click to open GitHub issue
   - Dependency chain display
   - External docs and error message display

2. `app/server/services/phase_coordinator.py` (282 lines)
   - Background polling service (10 second interval)
   - Monitors workflow_history for completions
   - Marks phases complete/failed
   - Triggers next phase automatically
   - Broadcasts WebSocket events

**Files Modified:**
3. `app/client/src/components/ZteHopperQueueCard.tsx` (137 lines)
   - Auto-refresh queue data every 10 seconds
   - Tab navigation (In Progress / Completed)
   - Loading and error states
   - Renders PhaseQueueList with filtered phases

4. `app/client/src/api/client.ts` (40 lines added)
   - `getQueueAll()` - Fetch all phases
   - `getQueueByParent(parentIssue)` - Fetch phases for parent
   - `dequeuePhase(queueId)` - Cancel phase
   - PhaseQueueItem and QueueListResponse types

5. `app/server/server.py` (14 lines added)
   - Initialized PhaseCoordinator service
   - Registered in FastAPI lifespan startup/shutdown

**Status:**
- ✅ Database migrations applied
- ✅ Backend imports verified
- ✅ TypeScript compilation clean
- ✅ 42 unit tests written (29 frontend + 13 backend)
- ✅ Queue display rendering correctly
- ✅ PhaseCoordinator polling background task working
- ✅ Git committed, pushed to origin/main

---

## What Needs to Be Done Next: Phase 4 - Testing & Documentation

### Overview

Complete the multi-phase upload feature by adding comprehensive testing, GitHub comment notifications, and user documentation.

### Tasks Remaining

**1. Integration Tests (Frontend)**

Create `app/client/src/__tests__/integration/multi-phase-flow.test.tsx`:
- Test multi-phase file upload flow
- Verify PhasePreview modal displays correct phase count
- Verify preview shows all phases with correct titles
- Test phase submission and API response
- Test queue display updates after submission
- Test error handling for invalid phase formats

**Test Structure:**
```typescript
describe('Multi-Phase Upload Flow', () => {
  it('should detect phases in uploaded markdown file')
  it('should show PhasePreview modal with 3 phases')
  it('should validate phase structure correctly')
  it('should submit multi-phase request successfully')
  it('should update queue display after submission')
  it('should handle invalid phase format with error')
});
```

**2. E2E Tests (Backend)**

Create `app/server/tests/e2e/test_multi_phase_execution.py`:
- Test 3-phase sequential execution
- Test Phase 1 completion triggers Phase 2
- Test Phase 2 completion triggers Phase 3
- Test failure scenario: Phase 1 fails → Phase 2+3 blocked
- Test workflow_history updates correctly
- Test WebSocket events broadcast correctly

**Test Structure:**
```python
class TestMultiPhaseExecution:
    def test_sequential_execution_success():
        # Create 3-phase parent issue
        # Verify Phase 1 status='ready'
        # Mark Phase 1 complete
        # Verify Phase 2 status='ready'
        # Mark Phase 2 complete
        # Verify Phase 3 status='ready'

    def test_failure_blocks_dependents():
        # Create 3-phase parent issue
        # Mark Phase 1 failed
        # Verify Phase 2 status='blocked'
        # Verify Phase 3 status='blocked'

    def test_phase_coordinator_polling():
        # Add workflow to workflow_history
        # Wait for polling cycle
        # Verify PhaseCoordinator detects completion
        # Verify next phase marked ready
```

**3. Component Tests (Frontend)**

Create `app/client/src/components/__tests__/PhaseQueueCard.test.tsx`:
- Test PhaseQueueCard renders correctly for each status
- Test color-coded badges display correctly
- Test dependency chain display
- Test external docs display
- Test error message display
- Test click to open GitHub issue
- Test PhaseQueueList sorting by phase number

**4. GitHub Comment Notifications (Backend)**

Update `app/server/services/phase_coordinator.py`:
- Uncomment TODO sections (lines 150, 175)
- Implement `_post_github_comment()` method
- Post comment on parent issue when phase completes/fails
- Include phase number, status, execution time
- Link to child issue

**Comment Format:**
```markdown
## Phase 2 Completed ✅

**Issue:** #456
**Status:** Completed
**Duration:** 3m 24s

Phase 2 has completed successfully. Moving to Phase 3.

[View Phase 2 Details](https://github.com/owner/repo/issues/456)
```

**Implementation:**
```python
async def _post_github_comment(self, parent_issue: int, phase_number: int, status: str, error_msg: str = None):
    # Get GitHub API client
    # Format comment based on status (completed/failed)
    # Post comment to parent issue
    # Log result
```

**5. PhaseCoordinator Tests (Backend)**

Create `app/server/tests/services/test_phase_coordinator.py`:
- Test polling loop starts/stops correctly
- Test workflow completion detection
- Test phase completion triggers next phase
- Test phase failure blocks dependents
- Test WebSocket event broadcasting
- Test error handling in polling loop
- Test concurrent phase monitoring

**6. WebSocket Integration Tests**

Create `app/server/tests/integration/test_queue_websocket.py`:
- Test queue_update event broadcasting
- Test frontend receives updates
- Test multiple clients receive same event
- Test event format matches specification

**7. API Documentation Updates**

Update `app/server/server.py` (FastAPI OpenAPI):
- Add `/api/queue` endpoint documentation
- Add multi-phase submission examples
- Document PhaseQueueItem schema
- Add error response examples

**8. User Guide Documentation**

Create `docs/user-guide/MULTI-PHASE-UPLOADS.md`:
- How to create multi-phase markdown files
- Phase header format examples
- External doc reference syntax
- Queue monitoring guide
- Troubleshooting common issues
- Examples of valid/invalid formats

**Example Structure:**
```markdown
# Multi-Phase Uploads User Guide

## Creating Multi-Phase Markdown Files

### Phase Header Formats
Valid formats:
- `# Phase 1: Setup Database`
- `## Phase: Two - Create API`
- `### Phase Three: Add Tests`

### External Document References
- `See the architecture.md for details`
- `Refer to docs/design.md`

### Example Multi-Phase File
(Include full example)

## Monitoring Execution
- How to view queue
- Understanding status colors
- Checking phase dependencies

## Troubleshooting
- Phase not detected
- Phase stays in "queued" status
- Handling failed phases
```

---

## Current Working Directory

```
/Users/Warmonger0/tac/tac-webbuilder
```

**Important Files:**
- Phase parser: `app/client/src/utils/phaseParser.ts`
- Phase preview: `app/client/src/components/PhasePreview.tsx`
- Phase queue card: `app/client/src/components/PhaseQueueCard.tsx`
- Queue service: `app/server/services/phase_queue_service.py`
- Phase coordinator: `app/server/services/phase_coordinator.py`
- Queue routes: `app/server/routes/queue_routes.py`

---

## Testing Commands

```bash
# Backend unit tests
cd /Users/Warmonger0/tac/tac-webbuilder
uv run python -m pytest app/server/tests/services/test_phase_queue_service.py -v

# Backend integration tests (NEW in Phase 4)
uv run python -m pytest app/server/tests/integration/ -v

# Backend E2E tests (NEW in Phase 4)
uv run python -m pytest app/server/tests/e2e/test_multi_phase_execution.py -v

# Frontend unit tests
cd /Users/Warmonger0/tac/tac-webbuilder/app/client
bun run test src/utils/__tests__/phaseParser.test.ts --run

# Frontend component tests (NEW in Phase 4)
bun run test src/components/__tests__/PhaseQueueCard.test.tsx --run

# Frontend integration tests (NEW in Phase 4)
bun run test src/__tests__/integration/multi-phase-flow.test.tsx --run

# All tests
bun run test --run

# TypeScript compilation
bun run typecheck

# Coverage report
bun run test --coverage
```

---

## Current Git Status

**Branch:** main
**Latest Commit:** b1f7754 (feat: Implement Phase 3 - Queue Display & Execution Coordinator)
**Pushed to Origin:** ✅ Yes

**Working Branch Recommendation:**
```bash
git checkout -b feature/multi-phase-upload-phase4
```

---

## Expected Phase 4 Deliverables

**Frontend Tests:**
- multi-phase-flow.test.tsx (NEW) - ~150 lines
- PhaseQueueCard.test.tsx (NEW) - ~200 lines

**Backend Tests:**
- test_multi_phase_execution.py (NEW) - ~300 lines
- test_phase_coordinator.py (NEW) - ~250 lines
- test_queue_websocket.py (NEW) - ~150 lines

**GitHub Integration:**
- phase_coordinator.py (MODIFIED) - Add comment posting (~50 lines)

**Documentation:**
- MULTI-PHASE-UPLOADS.md (NEW) - ~400 lines
- API documentation updates (MODIFIED) - ~50 lines

**Expected Total LOC:** ~1,550 lines

---

## Success Criteria for Phase 4

- [ ] All integration tests passing
- [ ] E2E test for 3-phase execution passing
- [ ] Component tests for PhaseQueueCard passing
- [ ] PhaseCoordinator tests passing
- [ ] WebSocket integration tests passing
- [ ] GitHub comments posted on phase transitions
- [ ] User guide documentation complete
- [ ] API documentation updated
- [ ] Manual testing: Full flow works end-to-end
- [ ] Code coverage >80% for new code

---

## Priority Order for Implementation

**High Priority (Must Have):**
1. E2E test for sequential execution
2. PhaseCoordinator tests
3. GitHub comment notifications
4. User guide documentation

**Medium Priority (Should Have):**
5. Frontend integration tests
6. Component tests for PhaseQueueCard
7. WebSocket integration tests
8. API documentation updates

**Low Priority (Nice to Have):**
9. Coverage optimization
10. Performance testing
11. Error scenario edge cases

---

## How to Continue

**Start with Phase 4 - Testing & Documentation:**

```
I'm continuing the multi-phase upload feature implementation. Phases 1, 2, and 3 are complete and pushed to origin/main.

Please proceed with Phase 4: Testing & Documentation. Start by creating:

1. E2E test for 3-phase sequential execution
2. PhaseCoordinator unit tests
3. GitHub comment notification implementation
4. User guide documentation

Follow the specifications in docs/implementation/CONTINUATION-PROMPT-multi-phase-upload-session-4.md.
```

---

## Key Design Decisions (Reminder)

1. **Phase Detection:** Flexible headers (any `## Phase`, `# Phase One`, `### Phase:`)
2. **Issue Strategy:** Separate GitHub issues (parent + children)
3. **Execution Model:** Queue phases, execute sequentially when dependencies met
4. **Status Tracking:** queued → ready → running → completed/failed/blocked
5. **External Docs:** Pass file paths to ADW (read from project_path)
6. **Failure Handling:** Failed phase blocks all subsequent phases
7. **Auto-Post:** Multi-phase requests skip preview/confirm (already confirmed in PhasePreview)
8. **Polling Interval:** 10 seconds (both frontend and backend)
9. **GitHub Comments:** Post to parent issue on phase transitions

---

## Test File Templates

### Frontend Integration Test Template
```typescript
// app/client/src/__tests__/integration/multi-phase-flow.test.tsx
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RequestForm } from '../../components/RequestForm';

describe('Multi-Phase Upload Flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should detect phases in uploaded markdown file', async () => {
    // Test implementation
  });
});
```

### Backend E2E Test Template
```python
# app/server/tests/e2e/test_multi_phase_execution.py
import pytest
from services.phase_queue_service import PhaseQueueService
from services.phase_coordinator import PhaseCoordinator

@pytest.mark.asyncio
class TestMultiPhaseExecution:
    async def test_sequential_execution_success(self):
        # Test implementation
        pass
```

---

## WebSocket Event Format (Reminder)

```json
{
  "type": "queue_update",
  "queue_id": "abc-123",
  "status": "completed",
  "parent_issue": 456,
  "timestamp": "2025-11-24T12:34:56Z"
}
```

---

## GitHub Comment Format (To Implement)

**On Completion:**
```markdown
## Phase {N} Completed ✅

**Issue:** #{issue_number}
**Status:** Completed
**Duration:** {duration}

Phase {N} has completed successfully. Moving to Phase {N+1}.

[View Phase {N} Details](https://github.com/{owner}/{repo}/issues/{issue_number})
```

**On Failure:**
```markdown
## Phase {N} Failed ❌

**Issue:** #{issue_number}
**Status:** Failed
**Error:** {error_message}

Phase {N} has failed. Subsequent phases have been blocked.

[View Phase {N} Details](https://github.com/{owner}/{repo}/issues/{issue_number})
```

---

## Known Issues & Edge Cases to Test

1. **Empty phase content** - How to handle?
2. **Very long phase titles** - Truncation?
3. **Missing external docs** - Graceful handling?
4. **Concurrent phase updates** - Race conditions?
5. **Webhook timing issues** - Polling frequency adequate?
6. **Database connection failures** - Retry logic?
7. **GitHub API rate limits** - Backoff strategy?

---

**Ready to start Phase 4!** Focus on testing, GitHub integration, and documentation.
