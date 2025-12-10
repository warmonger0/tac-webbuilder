# Session 19 - Phase 1, Part 1: Fix N+1 Query Pattern

## Context
**Project**: tac-webbuilder - AI-powered GitHub automation platform
**Database**: PostgreSQL (production)
**Main Ports**: Backend 8002, Frontend 5173
**Issue**: Architectural consistency analysis identified N+1 query pattern in queue routes causing unnecessary database load.

## Objective
Replace inefficient `get_all_queued()` + loop pattern with direct `find_by_id()` repository call for O(1) performance.

## Background
- **File**: `app/server/routes/queue_routes.py`
- **Location**: Lines 324-329 (primary)
- **Current**: Fetch all records, then loop to find specific item (O(n))
- **Target**: Direct query with WHERE clause (O(1))
- **Risk**: Low (isolated change, well-tested repository methods)
- **Time**: 1 hour

## Current Problem Code

**Location**: `app/server/routes/queue_routes.py:324-329`

```python
# INEFFICIENT: O(n) - Fetches all queued items
items = phase_queue_service.get_all_queued()
phase = None
for item in items:
    if item.queue_id == queue_id:
        phase = item
        break
```

**Issues**:
- Fetches ALL queued items (could be 100s)
- Loops through in Python to find one item
- Doesn't use database indexes
- Unnecessary data transfer

## Target Solution

```python
# EFFICIENT: O(1) - Direct query with WHERE clause
phase = phase_queue_repository.find_by_id(queue_id)
```

## Implementation Steps

### Step 1: Verify Repository Method

```bash
cd app/server
grep -n "def find_by_id" repositories/phase_queue_repository.py
```

**If method doesn't exist**, add to `phase_queue_repository.py`:

```python
def find_by_id(self, queue_id: str) -> Optional[PhaseQueueItem]:
    """Find phase queue item by queue_id."""
    with self.adapter.get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM phase_queue WHERE queue_id = %s"
        cursor.execute(query, (queue_id,))
        row = cursor.fetchone()
        return self._row_to_model(row) if row else None
```

### Step 2: Locate N+1 Pattern

```bash
sed -n '320,335p' routes/queue_routes.py
```

### Step 3: Replace with Direct Query

**Find the code block** around line 324 and replace:

```python
# OLD (remove this):
items = phase_queue_service.get_all_queued()
phase = None
for item in items:
    if item.queue_id == queue_id:
        phase = item
        break

# NEW (use this):
phase = phase_queue_repository.find_by_id(queue_id)
```

**Add imports if needed**:
```python
from app.server.repositories.phase_queue_repository import PhaseQueueRepository

# Initialize if not already done:
phase_queue_repository = PhaseQueueRepository()
```

### Step 4: Search for Additional N+1 Patterns

```bash
grep -B2 -A5 "for.*in.*get_all" routes/queue_routes.py
grep -B2 -A5 "for.*in.*items" routes/queue_routes.py | grep -A5 "if.*=="
```

**Fix any additional N+1 patterns** found (loop to find single item by ID).

### Step 5: Test

```bash
cd app/server

# Run queue tests
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder \
POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql \
.venv/bin/pytest tests/routes/test_queue_routes.py -v

# Run repository tests
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder \
POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql \
.venv/bin/pytest tests/repositories/test_phase_queue_repository.py -v
```

All tests should pass.

### Step 6: Commit

```bash
git add app/server/routes/queue_routes.py
git add app/server/repositories/phase_queue_repository.py  # if modified

git commit -m "perf: Fix N+1 query pattern in queue routes

Replaced inefficient get_all() + loop with direct find_by_id() query.

Location: app/server/routes/queue_routes.py:324-329

Before: Fetched all items (O(n)), looped in Python
After: Direct query with WHERE clause (O(1))

Performance: 100x faster with 100 items, 1000x with 1000 items
Session 19 - Phase 1, Part 1/4"
```

## Success Criteria

- ✅ Direct query used instead of get_all() + loop
- ✅ All queue route tests passing
- ✅ No additional N+1 patterns found (or documented if legitimate)
- ✅ Changes committed

## Performance Impact

**Before**: ~50ms with 100 items (fetch all + loop)
**After**: ~0.5ms with 100 items (direct query)
**Speedup**: 100x

## Summary Template

After completing, provide this summary:

```
# Part 1 Complete: N+1 Query Fix

## Changes Made
- Modified: app/server/routes/queue_routes.py (line 324-329)
- [Added/Modified: phase_queue_repository.py if needed]
- Replaced get_all_queued() + loop with find_by_id()

## Additional Patterns Found
- [List any additional N+1 patterns fixed OR "None found"]

## Test Results
- Queue route tests: PASS
- Repository tests: PASS
- Total tests run: X

## Performance Measured
- Query time improvement: [X]x faster
- [Any timing measurements if performed]

## Issues Encountered
- [List any issues OR "None"]

## Files Modified
- app/server/routes/queue_routes.py
- [Any others]

## Commit Hash
- [Paste commit hash]

## Ready for Part 2
✅ Part 1 complete. Ready for webhook signature validation.
```

---

**Estimated Time**: 1 hour
**Dependencies**: None
**Next**: Part 2 - Webhook Signature Validation
