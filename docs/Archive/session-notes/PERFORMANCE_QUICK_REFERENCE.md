# Performance Fix Quick Reference

**Status:** Ready to implement
**Total Effort:** ~20 hours
**Expected Improvement:** 100x+ faster on critical paths

---

## P0: Immediate Fixes (90 min)

### 1. Add Database Indexes - 30 min

**File:** Create `app/server/core/db/migrations/018_add_planned_features_indexes.sql`

```sql
-- Copy from main plan document
CREATE INDEX IF NOT EXISTS idx_planned_features_status_priority_created
  ON planned_features(status, priority, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_planned_features_type_created
  ON planned_features(item_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_planned_features_status
  ON planned_features(status);

CREATE INDEX IF NOT EXISTS idx_planned_features_session
  ON planned_features(session_number);

CREATE INDEX IF NOT EXISTS idx_planned_features_github_issue
  ON planned_features(github_issue_number);
```

**Update:** `app/server/services/planned_features_schema.py`

Add index loading in `init_planned_features_db()`:

```python
indexes_path = os.path.join(
    os.path.dirname(__file__),
    "..",
    "db",
    "migrations",
    "018_add_planned_features_indexes.sql"
)

if os.path.exists(indexes_path):
    with open(indexes_path, "r") as f:
        indexes_sql = f.read()
    with adapter.get_connection() as conn:
        cursor = conn.cursor()
        if db_type == "postgresql":
            cursor.execute(indexes_sql)
        else:
            cursor.executescript(indexes_sql)
        conn.commit()
```

**Impact:** 55s → 0.5s (100x faster)

---

### 2. Add Loading States - 30 min

**Update:** `app/client/src/components/PlansPanel.tsx`

Replace the render logic start with:

```typescript
const { data: features, isLoading: featuresLoading, error: featuresError } =
  useQuery({
    queryKey: ['plannedFeatures'],
    queryFn: plannedFeaturesClient.getAll,
    staleTime: 30000,
  });

const { data: stats, isLoading: statsLoading, error: statsError } =
  useQuery({
    queryKey: ['plannedFeaturesStats'],
    queryFn: plannedFeaturesClient.getStatistics,
    staleTime: 30000,
  });

// Show loading immediately
if (featuresLoading) {
  return (
    <div className="space-y-4">
      <div className="mb-6 grid grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg animate-pulse">
        {[1,2,3,4].map(i => <div key={i} className="h-16 bg-gray-200 rounded"></div>)}
      </div>
      <div className="space-y-3">
        {[1,2,3].map(i => <div key={i} className="h-12 bg-gray-200 rounded"></div>)}
      </div>
    </div>
  );
}

// Then render actual content...
```

**Same for:** `app/client/src/components/QualityPanel.tsx`

**Impact:** Blank screen → Instant loading state (UX perception)

---

### 3. Re-enable Background Sync - 5 min

**File:** `app/server/server.py` line 147

Change:
```python
# FROM:
workflow_service = WorkflowService(sync_cache_seconds=60, enable_background_sync=False)

# TO:
workflow_service = WorkflowService(sync_cache_seconds=60, enable_background_sync=True)
```

**Impact:** Prevents state drift, maintains data consistency

---

### 4. Optimize Polling Intervals - 10 min

**File:** `app/server/server.py` lines 176-184

Change:
```python
# FROM:
background_task_manager = BackgroundTaskManager(
    workflow_watch_interval=10.0,
    routes_watch_interval=10.0,
    history_watch_interval=10.0,
    adw_monitor_watch_interval=0.5,  # PROBLEM!
    queue_watch_interval=2.0,
)

# TO:
background_task_manager = BackgroundTaskManager(
    workflow_watch_interval=5.0,      # More responsive
    routes_watch_interval=30.0,       # Less critical
    history_watch_interval=10.0,      # Keep same
    adw_monitor_watch_interval=2.0,   # Was 0.5 (400x improvement!)
    queue_watch_interval=2.0,         # Keep same
)
```

**Impact:** 75% CPU reduction on background tasks

---

## P1: High Priority (2-3 hours)

### 5. Add HTTP Cache Headers - 30 min

**File:** `app/server/routes/planned_features_routes.py`

For each GET endpoint, add:

```python
from fastapi import Response
import json

response = Response(
    content=json.dumps([f.model_dump() for f in features]),
    media_type="application/json"
)
response.headers["Cache-Control"] = "public, max-age=30"
return response
```

Apply to:
- `GET /api/v1/planned-features`
- `GET /api/v1/planned-features/stats`
- `GET /api/v1/planned-features/recent-completions`

**Impact:** 80% reduction in API calls from frontend

---

### 6. Find & Fix N+1 Patterns - 1 hour

**Command:**
```bash
cd app/server
grep -rn "get_all().*for.*in" routes/ services/
```

Look for patterns like:

```python
# WRONG:
items = service.get_all()
for item in items:
    if item.id == search_id:
        result = item
        break

# RIGHT:
result = repository.find_by_id(search_id)
```

**Priority files:**
- `app/server/routes/queue_routes.py`
- `app/server/services/phase_queue_service.py`
- `app/server/routes/planned_features_routes.py`

**Impact:** Unknown without scanning, likely 10-50% improvement

---

### 7. Verify Pagination - 30 min

Check that all list endpoints have:

```python
limit: int = Query(100, ge=1, le=1000)
offset: int = Query(0, ge=0)
```

**Endpoints to check:**
- `GET /api/v1/workflow-history`
- `GET /api/v1/patterns`
- `GET /api/v1/work-logs`
- `GET /api/v1/planned-features`

---

## P2: Medium Priority (This week)

### 8. Cache Statistics - 1 hour

**File:** `app/server/services/planned_features_service.py`

Add to `__init__`:
```python
self._stats_cache = {}
self._stats_cache_time = 0
```

Update `get_statistics()`:
```python
def get_statistics(self) -> dict[str, Any]:
    current_time = time.time()
    if current_time - self._stats_cache_time < 300:  # 5 min cache
        return self._stats_cache

    # ... compute stats ...

    self._stats_cache = stats
    self._stats_cache_time = current_time
    return stats
```

**Impact:** 99% reduction in stats query frequency

---

## Testing

```bash
# After each change:
cd app/server
pytest tests/services/test_planned_features_service.py -v

# Frontend:
cd app/client
npm run build  # Check for errors

# Full test suite:
cd app/server
pytest -v

# Measure API response time:
time curl http://localhost:8000/api/v1/planned-features
# Should be < 1 second
```

---

## Verification Checklist

- [ ] Indexes created and exist in database
- [ ] Planned features API returns in < 1s
- [ ] Frontend shows loading state immediately
- [ ] Background sync enabled
- [ ] ADW monitor polling at 2s (not 0.5s)
- [ ] Cache headers set on GET endpoints
- [ ] No N+1 patterns in critical paths
- [ ] Pagination on all list endpoints
- [ ] Statistics cached (5 min)
- [ ] All tests pass
- [ ] Load test shows 10x+ improvement

---

## Expected Results

**Planned Features API:**
- Before: 55 seconds
- After: 0.5 seconds
- Improvement: 100x

**Frontend Load:**
- Before: 60+ seconds blank screen
- After: < 500ms loading state + 1s API calls
- Improvement: Perceived responsiveness

**Background Tasks:**
- Before: 500ms polling cycle
- After: 2-30s polling cycle
- Improvement: 75% CPU reduction

**Database Load:**
- Before: Full table scans, no indexes
- After: Index-based queries, cached results
- Improvement: 10-100x faster queries

---

## Timeline

**Session 1:** Issues #1-4 (P0 immediate fixes)
- Time: ~90 minutes
- Impact: Critical performance improvement

**Session 2:** Issues #5-7 (P1 high priority)
- Time: ~2-3 hours
- Impact: 80% API call reduction

**Session 3:** Issues #8-12 (P2-P3)
- Time: ~3-5 hours
- Impact: Long-term stability

---

## Critical Path

1. Add indexes ← **HIGHEST PRIORITY** (55s → 0.5s)
2. Add loading states ← **Improves UX immediately**
3. Optimize polling ← **Reduces CPU waste**
4. Re-enable sync ← **Prevents data corruption**

Do these 4 first (90 min total). They give maximum impact with minimum risk.

