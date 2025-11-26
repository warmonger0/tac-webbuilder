# Next Chat: Queue Validation & Cleanup

## Objective
Fix current queue state and validate deterministic ordering implementation.

---

## Current Queue State

Based on earlier inspection:

```
Parent #0:   Phase 1-5 ✅ All completed
Parent #78:  Phase 2 🔄 Running (adw-09a062c2)
             Phase 3 ⏸️ Queued (waiting on Phase 2)
Parent #97:  Phase 2 ⏸️ Queued
Parent #107: Phase 1 🔄 Running (issue #108)
```

---

## Validation Tasks

### 1. Verify Database Migration Applied
```bash
sqlite3 app/server/db/database.db "
SELECT
  name,
  sql
FROM sqlite_master
WHERE type='table' AND name='phase_queue';
"
```

**Expected:** Should see `priority`, `queue_position`, `ready_timestamp`, `started_timestamp` fields.

**Status:** ✅ Already applied

---

### 2. Check Current Queue with Priority Data
```bash
sqlite3 app/server/db/database.db "
SELECT
  parent_issue,
  phase_number,
  status,
  priority,
  queue_position,
  ready_timestamp,
  created_at
FROM phase_queue
WHERE status IN ('ready', 'queued', 'running')
ORDER BY priority ASC, queue_position ASC, parent_issue ASC;
"
```

**Expected:** All phases should have:
- `priority = 50` (default)
- `queue_position` set (not NULL)
- `ready_timestamp` for ready phases

---

### 3. Validate HopperSorter Works
```python
cd app/server
uv run python -c "
from services.hopper_sorter import HopperSorter

sorter = HopperSorter(db_path='db/database.db')

# Get next Phase 1 to start
next_phase = sorter.get_next_phase_1()

if next_phase:
    print(f'Next Phase 1: parent #{next_phase.parent_issue}')
    print(f'  Priority: {next_phase.priority}')
    print(f'  Queue position: {next_phase.queue_position}')
else:
    print('No ready Phase 1s in hopper')

# Get stats
stats = sorter.get_priority_stats()
print(f'Total Phase 1s: {stats[\"total_phase_1s\"]}')
print(f'Ready Phase 1s: {stats[\"ready_phase_1s\"]}')
"
```

**Expected:**
- Should run without errors
- Should return deterministic next phase

---

### 4. Test Webhook Integration
```bash
# Simulate workflow completion
curl -X POST http://localhost:8000/api/workflow-complete \
  -H "Content-Type: application/json" \
  -d '{
    "adw_id": "test-webhook",
    "status": "completed",
    "queue_id": "test-queue-id",
    "phase_number": 3,
    "parent_issue": 999,
    "trigger_next": true
  }'
```

**Expected:**
- Webhook should respond successfully
- Should log "Checking hopper for other ready Phase 1s..."
- Should use HopperSorter to find next phase

---

### 5. Run Tests
```bash
cd app/server
uv run pytest tests/services/test_hopper_sorter.py -v
```

**Expected:** All 10 tests pass

---

## Cleanup Tasks

### Task 1: Fix Queue Positions for Existing Phases

**Issue:** Existing phases might have NULL `queue_position` if they were created before migration.

**Fix:**
```bash
sqlite3 app/server/db/database.db "
UPDATE phase_queue
SET queue_position = ROWID
WHERE queue_position IS NULL;

SELECT 'Updated' as status, COUNT(*) as count
FROM phase_queue
WHERE queue_position IS NOT NULL;
"
```

---

### Task 2: Set Ready Timestamps

**Issue:** Phases that are currently 'ready' might not have `ready_timestamp`.

**Fix:**
```bash
sqlite3 app/server/db/database.db "
UPDATE phase_queue
SET ready_timestamp = created_at
WHERE status = 'ready' AND ready_timestamp IS NULL;

SELECT 'Updated' as status, COUNT(*) as count
FROM phase_queue
WHERE status = 'ready' AND ready_timestamp IS NOT NULL;
"
```

---

### Task 3: Verify Parent #78 Phase 2 is Running

**Check:**
```bash
curl -s http://localhost:8000/api/adw-monitor | python3 -m json.tool | grep -A 20 "adw-09a062c2"
```

**Expected:** Should show workflow running or completed.

**If stuck/failed:**
```bash
# Reset to ready and let sorter pick it up
sqlite3 app/server/db/database.db "
UPDATE phase_queue
SET status = 'ready', error_message = NULL, ready_timestamp = datetime('now')
WHERE parent_issue = 78 AND phase_number = 2;
"
```

---

### Task 4: Check for Orphaned Phases

**Issue:** Phases that are stuck in 'running' but workflow is dead.

**Find them:**
```bash
sqlite3 app/server/db/database.db "
SELECT
  p.parent_issue,
  p.phase_number,
  p.status,
  p.adw_id,
  p.started_timestamp
FROM phase_queue p
WHERE status = 'running'
  AND started_timestamp < datetime('now', '-1 hour');
"
```

**Fix:**
```bash
# If any found, reset to ready
sqlite3 app/server/db/database.db "
UPDATE phase_queue
SET status = 'ready',
    adw_id = NULL,
    error_message = 'Reset: workflow was stale (>1 hour old)',
    ready_timestamp = datetime('now')
WHERE status = 'running'
  AND started_timestamp < datetime('now', '-1 hour');
"
```

---

## Retry Failed Phases

### Parent #78 Phase 2 (if failed)

**Check status:**
```bash
curl -s http://localhost:8000/api/queue/78 | python3 -m json.tool | jq '.phases[] | select(.phase_number == 2)'
```

**If failed, reset:**
```bash
sqlite3 app/server/db/database.db "
UPDATE phase_queue
SET status = 'ready',
    error_message = NULL,
    adw_id = NULL,
    ready_timestamp = datetime('now')
WHERE parent_issue = 78 AND phase_number = 2;
"
```

**Trigger manually:**
```bash
# Get queue_id
QUEUE_ID=$(curl -s http://localhost:8000/api/queue/78 | python3 -m json.tool | jq -r '.phases[] | select(.phase_number == 2) | .queue_id')

# Execute
curl -X POST "http://localhost:8000/api/queue/${QUEUE_ID}/execute"
```

---

## End-to-End Test

### Scenario: Submit New Multi-Phase Request

1. **Submit request with priority:**
```bash
curl -X POST http://localhost:8000/api/submit-request \
  -H "Content-Type: application/json" \
  -d '{
    "nl_input": "Test deterministic queue ordering",
    "phases": [
      {"number": 1, "title": "Phase 1", "content": "First phase"},
      {"number": 2, "title": "Phase 2", "content": "Second phase"}
    ],
    "priority": 10
  }'
```

2. **Check hopper:**
```python
cd app/server
uv run python -c "
from services.hopper_sorter import HopperSorter

sorter = HopperSorter(db_path='db/database.db')
next_phase = sorter.get_next_phase_1()

if next_phase:
    print(f'Next: Parent #{next_phase.parent_issue}, Priority: {next_phase.priority}')
else:
    print('Hopper empty')
"
```

3. **Verify priority ordering:**
- New request (priority=10) should be ahead of existing (priority=50)

---

## Success Criteria

✅ All existing phases have `priority`, `queue_position`, and timestamps
✅ HopperSorter returns deterministic results
✅ Webhook uses sorter for cross-parent ordering
✅ Tests pass
✅ No orphaned or stuck phases
✅ New phases get auto-assigned priority and position
✅ Queue executes in priority → FIFO → parent_issue order

---

## Rollback Plan (If Needed)

If something breaks:

1. **Revert webhook changes:**
```bash
git checkout HEAD -- app/server/routes/queue_routes.py
```

2. **Remove sorter dependency:**
```bash
# Webhook will fall back to old behavior (no cross-parent ordering)
```

3. **Database stays intact:**
- New fields are optional
- Old code still works (ignores new fields)

---

## Next Session Commands

```bash
# 1. Validate migration
sqlite3 app/server/db/database.db ".schema phase_queue" | grep -E "priority|queue_position"

# 2. Check current queue
sqlite3 app/server/db/database.db "
SELECT parent_issue, phase_number, status, priority, queue_position
FROM phase_queue
WHERE status IN ('ready', 'queued', 'running')
ORDER BY priority, queue_position;
"

# 3. Test sorter
cd app/server && uv run python -c "
from services.hopper_sorter import HopperSorter
sorter = HopperSorter()
print('Next:', sorter.get_next_phase_1())
print('Stats:', sorter.get_priority_stats())
"

# 4. Run tests
cd app/server && uv run pytest tests/services/test_hopper_sorter.py -v

# 5. Clean up orphans
sqlite3 app/server/db/database.db "
UPDATE phase_queue SET queue_position = ROWID WHERE queue_position IS NULL;
UPDATE phase_queue SET ready_timestamp = created_at WHERE status = 'ready' AND ready_timestamp IS NULL;
"

# 6. Check for stale workflows
sqlite3 app/server/db/database.db "
SELECT parent_issue, phase_number, adw_id, started_timestamp
FROM phase_queue
WHERE status = 'running' AND started_timestamp < datetime('now', '-1 hour');
"
```

---

## Summary

**What we built:** Deterministic queue with priority-based, FIFO ordering.

**What needs validation:**
1. Migration applied correctly
2. Existing phases populated with defaults
3. HopperSorter works end-to-end
4. Webhook integration functional
5. No stuck/orphaned phases

**What to retry:**
- Any failed phases (reset to 'ready')
- Stale running phases (>1 hour old)

**Expected outcome:** Queue executes in strict priority → FIFO → parent_issue order, no race conditions, fully deterministic!
