# E2E Test: Pattern Predictions in Queue

## User Story
**As a** developer using the multi-phase workflow system
**I want** to see predicted patterns for each queued phase
**So that** I understand what types of operations each phase will perform and can verify pattern accuracy

## Test Objective
Validate that pattern predictions flow correctly from request submission through the queue system and are displayed in the ZTE Hopper Queue Card UI.

## Prerequisites
- Backend server running on port 8002
- Frontend server running on port 5173
- Pattern prediction system operational (Phase 1 complete)
- Multi-phase queue system operational
- Clean database state (or known test data)

## Test Steps

### Step 1: Submit Multi-Phase Request with Pattern Keywords
1. Navigate to frontend: http://localhost:5173
2. Enter natural language input with pattern-triggering keywords:
   ```
   Phase 1: Run backend tests with pytest
   Phase 2: Build and validate TypeScript types
   Phase 3: Deploy to staging environment
   ```
3. Enable multi-phase mode (if required by UI)
4. Click "Submit" button
5. Wait for request processing to complete

**Expected Result:**
- Request submitted successfully
- Pattern prediction triggered for input
- Predicted patterns include: "test:pytest:backend", "build:typecheck", "deploy:staging"
- Request ID returned

**Screenshot:** `test-pattern-queue-1-submit.png`

### Step 2: Navigate to ZTE Hopper Queue Card
1. Click on "ZTE Hopper" or "Queue" tab in the UI
2. Verify queue card is visible
3. Verify phases are displayed in the queue

**Expected Result:**
- Queue card displays all 3 phases
- Each phase shows correct status (Phase 1: ready, Phase 2-3: queued)
- Phase titles visible

**Screenshot:** `test-pattern-queue-2-navigate.png`

### Step 3: Expand Phase 1 to View Pattern Badges
1. Click expand button (▼) on Phase 1 card
2. Wait for expanded section to appear
3. Look for "Patterns:" section

**Expected Result:**
- Phase 1 expands to show details
- "Patterns:" label visible
- Pattern badges displayed: "test:pytest:backend"
- Badges styled with emerald theme (emerald-500/20 background, emerald-300 text)
- Pattern badges have border and rounded corners

**Screenshot:** `test-pattern-queue-3-expand-phase1.png`

### Step 4: Verify Pattern Display for Other Phases
1. Collapse Phase 1 (click ▲ button)
2. Expand Phase 2 (click ▼ button)
3. Verify pattern badges for Phase 2
4. Collapse Phase 2
5. Expand Phase 3
6. Verify pattern badges for Phase 3

**Expected Result:**
- Phase 2 shows "build:typecheck" pattern badge
- Phase 3 shows "deploy:staging" pattern badge
- All pattern badges consistently styled
- Patterns section only appears when patterns exist

**Screenshot:** `test-pattern-queue-4-other-phases.png`

### Step 5: Test Phase Without Patterns
1. Submit another multi-phase request without pattern keywords:
   ```
   Phase 1: Update documentation
   Phase 2: Review changes
   ```
2. Navigate to queue
3. Expand phases

**Expected Result:**
- Phases display correctly
- NO "Patterns:" section visible (conditional rendering works)
- No empty pattern sections or visual clutter

**Screenshot:** `test-pattern-queue-5-no-patterns.png`

### Step 6: Verify Pattern Persistence Through State Transitions
1. Execute Phase 1 of first request (with patterns)
2. Wait for Phase 1 to complete
3. Verify Phase 2 becomes ready
4. Expand Phase 2
5. Verify patterns still displayed

**Expected Result:**
- Phase 1 status changes: ready → running → completed
- Phase 2 status changes: queued → ready
- Pattern badges persist through status changes
- Patterns correctly displayed in Phase 2 after it becomes ready

**Screenshot:** `test-pattern-queue-6-persistence.png`

### Step 7: Test Pattern Display with Many Patterns
1. Submit request with input that triggers multiple patterns:
   ```
   Run all tests (unit, integration, e2e), build frontend and backend, deploy to staging and production
   ```
2. Navigate to queue
3. Expand phase
4. Verify pattern badge wrapping

**Expected Result:**
- Multiple pattern badges displayed (5+ patterns)
- Badges wrap correctly (flex-wrap works)
- UI remains readable
- No overflow or layout breaking

**Screenshot:** `test-pattern-queue-7-many-patterns.png`

### Step 8: Verify Long Pattern Names
1. Manually test or observe if any patterns have long names
2. Verify badges handle long text gracefully

**Expected Result:**
- Long pattern names don't break layout
- Text wraps or truncates appropriately
- Badges remain visually consistent

**Screenshot:** `test-pattern-queue-8-long-patterns.png` (if applicable)

## Success Criteria
- ✅ Pattern predictions triggered on multi-phase request submission
- ✅ Pattern badges displayed in PhaseQueueCard expanded view
- ✅ Pattern badges styled consistently (emerald theme, border, rounded)
- ✅ "Patterns:" section only appears when patterns exist
- ✅ Patterns persist through queue state transitions (ready → running → completed)
- ✅ Multiple patterns display correctly with proper wrapping
- ✅ Phases without patterns show no pattern section (no clutter)
- ✅ Pattern display works for all phases (1, 2, 3, ...)
- ✅ UI remains readable with many patterns (5+)
- ✅ Long pattern names handled gracefully

## Cleanup
1. Clear test data from queue (if needed)
2. Reset database to clean state (optional)
3. Archive screenshots

## Notes
- Pattern prediction accuracy is not tested here (covered in Phase 1 tests)
- This test focuses on UI display and data flow through queue system
- Pattern badges should match design system (emerald/teal theme)
- Pattern metadata (confidence, reasoning) not displayed in UI (by design)

## Related Tests
- `.claude/commands/e2e/test_basic_query.md` - Example E2E test structure
- Phase 1 pattern prediction tests - Pattern accuracy validation
- Queue integration tests - Queue state management

## Troubleshooting
**Issue:** Patterns not appearing in queue
**Solution:** Check backend logs for pattern prediction errors, verify github_issue_service passes patterns to multi_phase_handler

**Issue:** Pattern section always empty
**Solution:** Verify phase_data.predicted_patterns exists in database, check PhaseQueueCard component props

**Issue:** UI breaks with many patterns
**Solution:** Verify flex-wrap works, check for CSS conflicts, ensure container width appropriate

**Issue:** Patterns disappear after status change
**Solution:** Verify patterns stored in phase_data (not separate field), check database persistence
