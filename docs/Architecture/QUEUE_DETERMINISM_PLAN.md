# Queue Determinism & Robustness Plan

## Executive Summary

**Problem:** The phase queue has non-deterministic execution ordering due to:
1. Race conditions when multiple phases become ready simultaneously
2. Ambiguous prioritization strategy (FIFO vs priority-based)
3. Implicit ordering that depends on database query results
4. No explicit queue position or priority field

**Solution:** Implement explicit priority-based queue with deterministic ordering.

---

## Root Cause Analysis

### Current Architecture

```
PhaseCoordinator (polls every 10s)
  ↓
_auto_start_ready_phases()
  ↓
get_all_queued() → repository.find_all()
  ↓
ORDER BY parent_issue ASC, phase_number ASC
  ↓
Filter: status='ready' AND issue_number IS NOT NULL
  ↓
for phase in ready_phases_to_start:  # Start in list order
    launch_workflow(phase)
```

### Race Conditions

**Scenario 1: Simultaneous Ready States**
```
T0: Parent #78 Phase 2 completes → Phase 3 becomes ready
T0: Parent #107 Phase 1 is created as ready
T1: PhaseCoordinator polls
    → Both #78-P3 and #107-P1 are ready
    → ORDER BY parent_issue ASC: #78 before #107
    → Expected: #78-P3 runs first
    → Actual: Depends on race conditions!
```

**Scenario 2: Polling Window**
```
T0: Parent #0 Phase 2 is running
T5: Parent #107 Phase 1 becomes ready
T8: Parent #0 Phase 2 completes, Phase 3 becomes ready
T10: PhaseCoordinator polls
     → Sees #0-P3 (newer) and #107-P1 (older)
     → ORDER BY parent_issue: #0 before #107
     → #0-P3 might run first even though #107-P1 was ready earlier
```

### Non-Determinism Sources

1. **No explicit priority field** - relies on implicit ORDER BY
2. **No queue position tracking** - can't tell "who was first"
3. **Simultaneous transitions** - multiple phases → ready at once
4. **Polling delays** - 10-second window creates timing dependencies
5. **No locking mechanism** - two workers could theoretically start same phase

---

## Design Principles for Deterministic Queue

### 1. **Explicit Priority System**
- Every phase gets a numeric priority on enqueue
- Lower number = higher priority
- Priority determines execution order, not database query ordering

### 2. **FIFO Within Priority Levels**
- Phases with same priority execute in creation timestamp order
- Prevents newer phases from jumping ahead unfairly

### 3. **Atomic State Transitions**
- Use database transactions for state changes
- Prevent race conditions between status checks and updates

### 4. **Single-Threaded Executor**
- Only one coordinator instance processes queue
- Prevents duplicate workflow launches

### 5. **Idempotency**
- Safe to poll multiple times
- Safe to restart coordinator mid-execution
- ADW workflows can be re-run safely (they're already idempotent)

---

## Proposed Solution: Priority-Based Queue

### Schema Changes

```sql
-- Add priority and queue_position fields
ALTER TABLE phase_queue ADD COLUMN priority INTEGER DEFAULT 50;
ALTER TABLE phase_queue ADD COLUMN queue_position INTEGER;
ALTER TABLE phase_queue ADD COLUMN ready_timestamp TEXT;  -- When phase became ready
ALTER TABLE phase_queue ADD COLUMN started_timestamp TEXT;  -- When workflow launched

-- Index for efficient priority-based queries
CREATE INDEX idx_phase_queue_priority ON phase_queue(priority, ready_timestamp);
CREATE INDEX idx_phase_queue_position ON phase_queue(queue_position);
```

### Priority Levels

```python
PRIORITY_LEVELS = {
    "urgent": 10,      # Critical fixes, blockers
    "high": 20,        # User-facing features, important bugs
    "normal": 50,      # Default priority
    "low": 70,         # Nice-to-have, refactoring
    "background": 90   # Documentation, cleanup
}
```

### Deterministic Ordering Query

```sql
-- Get next phase to execute
SELECT *
FROM phase_queue
WHERE status = 'ready'
  AND issue_number IS NOT NULL
ORDER BY
  priority ASC,           -- Lower priority number = higher urgency
  ready_timestamp ASC,    -- FIFO within same priority
  parent_issue ASC,       -- Tiebreaker: older parent issues first
  phase_number ASC        -- Tiebreaker: earlier phases first
LIMIT 1;
```

### Auto-Start Logic (Revised)

```python
async def _auto_start_ready_phases(self):
    """
    Start EXACTLY ONE ready phase per poll cycle.

    Prevents race conditions by processing phases one at a time.
    """
    try:
        # Get THE NEXT phase (singular) using priority ordering
        next_phase = self.phase_queue_service.get_next_ready_phase()

        if not next_phase:
            return  # No ready phases

        # Atomically transition ready → running
        success = self.phase_queue_service.try_claim_phase(next_phase.queue_id)

        if not success:
            # Another worker claimed it, or status changed
            logger.warning(f"Failed to claim phase {next_phase.queue_id}")
            return

        # Launch workflow
        await self._launch_workflow(next_phase)

    except Exception as e:
        logger.error(f"Failed to auto-start phase: {e}")
```

### Atomic Claim Operation

```python
def try_claim_phase(self, queue_id: str) -> bool:
    """
    Atomically transition phase from 'ready' to 'running'.

    Returns True if successful, False if phase was already claimed.
    """
    with get_connection(self.db_path) as conn:
        cursor = conn.execute(
            """
            UPDATE phase_queue
            SET status = 'running',
                started_timestamp = datetime('now'),
                updated_at = datetime('now')
            WHERE queue_id = ?
              AND status = 'ready'  -- Only claim if still ready
            """,
            (queue_id,)
        )

        rows_affected = cursor.rowcount
        conn.commit()

        return rows_affected == 1  # True only if we changed the status
```

---

## Implementation Plan

### Phase 1: Add Priority Fields (No Behavior Change)
**Effort:** 1-2 hours
**Risk:** Low

1. Add database migration for new fields:
   - `priority INTEGER DEFAULT 50`
   - `ready_timestamp TEXT`
   - `started_timestamp TEXT`

2. Update `enqueue()` to set default priority

3. Update `update_status()` to set `ready_timestamp` when transitioning to 'ready'

4. Add indexes for performance

**Acceptance Criteria:**
- All new phases get priority=50 by default
- Existing behavior unchanged
- Database migration runs successfully

---

### Phase 2: Implement Deterministic Ordering
**Effort:** 2-3 hours
**Risk:** Medium

1. Update `repository.find_ready_phases()`:
   ```python
   def find_next_ready_phase(self) -> Optional[PhaseQueueItem]:
       """Get THE NEXT phase to execute (deterministic ordering)"""
       cursor = conn.execute("""
           SELECT * FROM phase_queue
           WHERE status = 'ready' AND issue_number IS NOT NULL
           ORDER BY priority ASC, ready_timestamp ASC,
                    parent_issue ASC, phase_number ASC
           LIMIT 1
       """)
   ```

2. Update `PhaseCoordinator._auto_start_ready_phases()`:
   - Change from processing ALL ready phases to ONE phase per poll
   - Use `get_next_ready_phase()` instead of `get_all_queued()`

3. Add logging for queue position tracking

**Acceptance Criteria:**
- Only one workflow launches per 10-second poll cycle
- Phases execute in strict priority → timestamp → parent_issue order
- Logs clearly show: "Starting phase X (priority=Y, position=Z)"

---

### Phase 3: Atomic Claim Mechanism
**Effort:** 2 hours
**Risk:** Low

1. Implement `try_claim_phase()` with atomic UPDATE

2. Update auto-start logic to use claim mechanism

3. Add retry logic if claim fails (next poll cycle will try again)

**Acceptance Criteria:**
- No duplicate workflow launches (verified by checking for duplicate ADW IDs)
- Status transitions are atomic
- Safe to run multiple coordinator instances (future-proofing)

---

### Phase 4: Priority API & UI
**Effort:** 3-4 hours
**Risk:** Low

1. Add API endpoint: `PATCH /api/queue/{queue_id}/priority`

2. Update `RequestForm` to allow priority selection:
   ```typescript
   <select name="priority">
     <option value="normal">Normal Priority</option>
     <option value="high">High Priority</option>
     <option value="urgent">Urgent (Jump Queue)</option>
   </select>
   ```

3. Update `ZteHopperQueueCard` to show priority badges

4. Add queue position indicator (e.g., "Position #3 in queue")

**Acceptance Criteria:**
- Users can set priority when submitting requests
- Queue UI shows priority and position
- High-priority phases jump ahead of lower-priority ones

---

### Phase 5: Advanced Features (Optional)
**Effort:** 4-6 hours
**Risk:** Low

1. **Priority bumping:** Auto-increase priority for phases waiting > 1 hour

2. **Rate limiting:** Max N concurrent workflows (prevent system overload)

3. **Resource-aware scheduling:** Check available ports before starting

4. **Queue analytics:** Track average wait time per priority level

5. **Manual queue reordering:** Drag-and-drop in UI

---

## Testing Strategy

### Unit Tests

```python
def test_deterministic_ordering():
    """Verify phases execute in priority → timestamp order"""
    # Create phases in random order
    enqueue(parent=100, phase=1, priority=50, timestamp="T1")
    enqueue(parent=200, phase=1, priority=20, timestamp="T2")  # Higher priority
    enqueue(parent=300, phase=1, priority=50, timestamp="T0")  # Same priority, earlier

    # Get next ready phase
    next_phase = get_next_ready_phase()

    # Should be parent=200 (priority=20, highest)
    assert next_phase.parent_issue == 200

def test_atomic_claim():
    """Verify only one worker can claim a phase"""
    phase_id = enqueue(parent=1, phase=1)

    # Simulate two workers claiming simultaneously
    worker1_success = try_claim_phase(phase_id)
    worker2_success = try_claim_phase(phase_id)

    # Only one should succeed
    assert worker1_success != worker2_success
    assert worker1_success or worker2_success  # At least one succeeded

def test_fifo_within_priority():
    """Verify FIFO ordering within same priority"""
    enqueue(parent=1, phase=1, priority=50, timestamp="T2")
    enqueue(parent=2, phase=1, priority=50, timestamp="T1")  # Earlier
    enqueue(parent=3, phase=1, priority=50, timestamp="T3")

    # Should execute in T1 → T2 → T3 order
    assert get_next_ready_phase().parent_issue == 2
    claim_phase(2)
    assert get_next_ready_phase().parent_issue == 1
```

### Integration Tests

```python
async def test_no_duplicate_launches():
    """Verify coordinator doesn't launch same phase twice"""
    enqueue_phase(parent=1, phase=1)

    # Run coordinator for 30 seconds
    coordinator = PhaseCoordinator(poll_interval=5)
    await coordinator.start()
    await asyncio.sleep(30)
    await coordinator.stop()

    # Check only ONE workflow was launched
    workflows = get_workflows_for_issue(1)
    assert len(workflows) == 1

async def test_priority_ordering():
    """E2E test: high-priority phases execute first"""
    enqueue(parent=1, phase=1, priority=50)  # Normal
    enqueue(parent=2, phase=1, priority=10)  # Urgent
    enqueue(parent=3, phase=1, priority=70)  # Low

    # Wait for coordinator to process
    await wait_for_all_complete()

    # Check execution order
    workflows = get_all_workflows()
    start_times = sorted(workflows, key=lambda w: w.start_time)

    assert start_times[0].issue_number == 2  # Urgent first
    assert start_times[1].issue_number == 1  # Normal second
    assert start_times[2].issue_number == 3  # Low last
```

---

## Migration Strategy

### Backwards Compatibility

1. **Default priority:** All existing phases get `priority=50` (normal)

2. **Gradual rollout:** Phase 1-3 don't change user-facing behavior

3. **Feature flag:** Enable priority selection in UI only when ready

### Rollback Plan

1. Keep old `find_ready_phases()` method as `find_ready_phases_legacy()`

2. Add config flag: `USE_PRIORITY_QUEUE = True/False`

3. If issues arise, flip flag to revert to old behavior

### Database Migration

```sql
-- migrations/007_add_queue_priority.sql

BEGIN TRANSACTION;

-- Add new columns
ALTER TABLE phase_queue ADD COLUMN priority INTEGER DEFAULT 50;
ALTER TABLE phase_queue ADD COLUMN ready_timestamp TEXT;
ALTER TABLE phase_queue ADD COLUMN started_timestamp TEXT;

-- Populate ready_timestamp for existing ready phases
UPDATE phase_queue
SET ready_timestamp = updated_at
WHERE status = 'ready' AND ready_timestamp IS NULL;

-- Create indexes
CREATE INDEX idx_phase_queue_priority
  ON phase_queue(priority, ready_timestamp);

COMMIT;
```

---

## Success Metrics

### Determinism
- ✅ 100% reproducible execution order given same queue state
- ✅ No race conditions in concurrent scenarios
- ✅ Phases execute in documented priority → FIFO order

### Performance
- ⏱️ Queue query time: <10ms (with indexes)
- ⏱️ Claim operation: <5ms (atomic UPDATE)
- ⏱️ No degradation for large queues (100+ phases)

### Reliability
- 🛡️ Zero duplicate workflow launches
- 🛡️ Safe to restart coordinator mid-execution
- 🛡️ No orphaned phases stuck in "ready" state

### User Experience
- 📊 Queue position visible in UI
- 🎯 High-priority phases complete faster
- 📈 Average wait time < 2 minutes for normal priority

---

## Rollout Timeline

**Week 1:**
- Day 1-2: Phase 1 (Add priority fields)
- Day 3-4: Phase 2 (Deterministic ordering)
- Day 5: Phase 3 (Atomic claim)

**Week 2:**
- Day 1-3: Phase 4 (Priority API & UI)
- Day 4-5: Testing & validation

**Week 3 (Optional):**
- Advanced features based on user feedback

---

## Open Questions

1. **Should priority be mutable?**
   - Pro: Allows bumping urgent issues to front
   - Con: Could create fairness issues
   - **Recommendation:** Allow PATCH /api/queue/{id}/priority but log all changes

2. **Max concurrent workflows?**
   - Current: Unlimited (limited by ports: 15 max)
   - **Recommendation:** Default limit = 5, configurable

3. **Priority inheritance?**
   - If Phase 1 is urgent, are Phase 2-N also urgent?
   - **Recommendation:** Yes, inherit priority from parent issue

4. **Queue pausing granularity?**
   - Current: Global pause (all phases)
   - Future: Per-priority pause? Per-parent pause?
   - **Recommendation:** Start with global, add granularity if needed

---

## Conclusion

The current queue has **implicit, non-deterministic ordering** that creates confusion and unpredictability. By implementing an **explicit priority-based queue with atomic operations**, we achieve:

1. ✅ **Deterministic execution order**
2. ✅ **No race conditions**
3. ✅ **Fair FIFO within priority levels**
4. ✅ **User control over priority**
5. ✅ **Bulletproof reliability**

**Next step:** Review this plan and proceed with Phase 1 implementation.
