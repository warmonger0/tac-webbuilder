# Performance Metrics & Validation Guide

**Purpose:** Measure and validate performance improvements from fixes
**Tools:** curl, time, browser DevTools, Python profiler
**Baseline:** Record metrics before fixes, then compare after

---

## Baseline Measurements (Before Fixes)

### Metric #1: Planned Features API Response Time

**Command:**
```bash
# Warm up cache first
curl -s http://localhost:8000/api/v1/planned-features > /dev/null

# Measure 3 times and average
for i in {1..3}; do
  time curl -s "http://localhost:8000/api/v1/planned-features?status=in_progress" > /dev/null
done
```

**Expected Baseline:** ~55 seconds
**Target After Fix #1:** < 1 second

**Record:**
- Baseline: _____ seconds
- After Fix: _____ seconds
- Improvement: _____x

---

### Metric #2: Frontend Load Time (Blank Screen Duration)

**Steps:**
1. Open DevTools (F12)
2. Go to Performance tab
3. Clear browser cache (Ctrl+Shift+Delete)
4. Hard refresh (Ctrl+Shift+R)
5. Navigate to Plans tab
6. Measure time until content appears (not skeleton)

**Expected Baseline:** 60+ seconds blank screen
**Target After Fix #2:** < 100ms to loading state, ~1s to content

**Record:**
- Time to loading state: _____ ms
- Time to content: _____ seconds
- Blank screen duration: _____ seconds (BEFORE FIX)

---

### Metric #3: Statistics Query Time

**Command:**
```bash
# Measure statistics endpoint
for i in {1..3}; do
  time curl -s "http://localhost:8000/api/v1/planned-features/stats" > /dev/null
done
```

**Expected Baseline:** ~5-10 seconds (5 database queries)
**Target After Fix #8:** < 1 second (cached)

**Record:**
- Baseline: _____ seconds
- After caching: _____ seconds

---

### Metric #4: Background Task CPU Usage

**Command:**
```bash
# Monitor CPU while background tasks run
top -p $(pgrep -f "uvicorn") -b -n 10

# Or watch CPU usage for 10 seconds
watch -n 1 'top -p $(pgrep -f uvicorn) | head -n 20'
```

**Expected Baseline:**
- CPU: ~5-10% (500ms ADW monitor polling)
- Threads: Multiple background tasks spinning

**Target After Fix #4:**
- CPU: ~1-2% (2s ADW monitor polling)
- 75% reduction

**Record:**
- Baseline CPU: _____%
- After optimization: _____%
- Reduction: _____x

---

### Metric #5: Database Query Analysis

**Command (SQLite):**
```bash
# Show query execution plan
sqlite3 db/workflow_history.db

sqlite> EXPLAIN QUERY PLAN
SELECT * FROM planned_features
WHERE status = 'in_progress'
ORDER BY priority, created_at DESC;

-- BEFORE (without indexes):
-- SCAN TABLE planned_features

-- AFTER (with indexes):
-- SEARCH TABLE planned_features USING idx_planned_features_status_priority_created
```

**For PostgreSQL:**
```bash
psql -U user -d dbname

# Show execution plan
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM planned_features
WHERE status = 'in_progress'
ORDER BY priority, created_at DESC;
```

**Record:**
- Before: SCAN TABLE (full scan)
- After: SEARCH ... USING idx_... (index scan)

---

## Post-Fix Measurements

### After Implementing Fix #1: Database Indexes

**Step 1: Verify indexes exist**

```bash
# SQLite
sqlite3 db/workflow_history.db ".indices planned_features"

# Output should show:
# idx_planned_features_status_priority_created
# idx_planned_features_type_created
# idx_planned_features_status
# idx_planned_features_session
# idx_planned_features_github_issue
```

**Step 2: Measure API response**

```bash
time curl -s "http://localhost:8000/api/v1/planned-features?status=in_progress" > /dev/null

# Expected: < 1 second
```

**Step 3: Check EXPLAIN QUERY PLAN**

```bash
sqlite3 db/workflow_history.db "EXPLAIN QUERY PLAN SELECT * FROM planned_features WHERE status = 'in_progress' ORDER BY priority, created_at DESC;"

# Output should show SEARCH (not SCAN)
```

**Validation:**
- [ ] All 5 indexes exist
- [ ] Query uses index (SEARCH in EXPLAIN)
- [ ] API responds in < 1 second
- [ ] 100x speedup from baseline

---

### After Implementing Fix #2: Loading States

**Step 1: Clear browser cache**

```bash
# Chrome: Ctrl+Shift+Delete (or Cmd+Shift+Delete on Mac)
# Clear "All time"
```

**Step 2: Test loading state**

```bash
# Open DevTools Performance tab
# Hard refresh (Ctrl+Shift+R)
# Go to Plans tab
# Measure:
# - Time to first paint (skeleton appears)
# - Time to first content (data appears)
```

**Expected:**
- First paint: < 100ms (skeleton)
- First content: ~1-2s (API response)

**Validation:**
- [ ] Skeleton appears immediately (not blank)
- [ ] Smooth fade-in with `animate-pulse`
- [ ] Content appears after ~1s
- [ ] No more 60s blank screen

---

### After Implementing Fix #3: Background Sync

**Step 1: Check logs**

```bash
# Run server with debug logging
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --log-level info

# Check for sync messages:
# [WORKFLOW_SERVICE] Background sync triggered
# [WORKFLOW_SERVICE] Background sync: N workflows updated
```

**Step 2: Verify sync runs**

```bash
# Wait 60+ seconds and check logs
# Should see sync running every 60 seconds (or less frequently if no changes)
```

**Validation:**
- [ ] Background sync enabled
- [ ] Logs show sync running
- [ ] No errors in sync output
- [ ] Database state consistent

---

### After Implementing Fix #4: Polling Intervals

**Step 1: Verify intervals**

```bash
# Check code
grep -A 8 "BackgroundTaskManager(" app/server/server.py

# Should show:
# workflow_watch_interval=5.0
# routes_watch_interval=30.0
# history_watch_interval=10.0
# adw_monitor_watch_interval=2.0  <-- CRITICAL (was 0.5)
# queue_watch_interval=2.0
```

**Step 2: Monitor CPU impact**

```bash
# Start server
python -m uvicorn server:app &

# Check CPU usage for 30 seconds
top -p $(pgrep -f uvicorn) -b -n 30 | grep -E "CPU|COMMAND"
```

**Expected CPU reduction:**
- Before: ~5-10% from 0.5s polling
- After: ~1-2% from 2s polling

**Validation:**
- [ ] Intervals configured correctly
- [ ] CPU usage reduced by 75%
- [ ] No WebSocket errors in logs
- [ ] UI still responsive

---

## Comprehensive Performance Test

### Full Test Suite

```bash
#!/bin/bash
# performance_test.sh

echo "=== Performance Metrics Test ==="
echo "Date: $(date)"
echo ""

# Test 1: API Response Time
echo "Test 1: Planned Features API Response Time"
echo "Running 3 iterations..."
for i in {1..3}; do
  echo -n "Iteration $i: "
  time curl -s "http://localhost:8000/api/v1/planned-features" > /dev/null
done
echo ""

# Test 2: Database Query Plan
echo "Test 2: Query Execution Plan (should use index)"
sqlite3 db/workflow_history.db "EXPLAIN QUERY PLAN SELECT * FROM planned_features WHERE status = 'in_progress';"
echo ""

# Test 3: Index Verification
echo "Test 3: Indexes Created"
sqlite3 db/workflow_history.db ".indices planned_features"
echo ""

# Test 4: CPU Baseline
echo "Test 4: CPU Usage (30 second sample)"
echo "Top 5 CPU-using processes:"
top -b -n 1 | head -10
echo ""

# Test 5: Background Task Status
echo "Test 5: Background Tasks (from logs)"
tail -20 server.log | grep -i "background\|sync"
echo ""

echo "=== Test Complete ==="
```

**Run:**
```bash
chmod +x performance_test.sh
./performance_test.sh
```

---

## Before/After Comparison Template

### Summary Table

| Metric | Before | After | Unit | Improvement |
|--------|--------|-------|------|-------------|
| Planned Features API | 55 | < 1 | seconds | 100x faster |
| Frontend Load | 60+ | < 0.5 | seconds | Instant |
| Stats Query | 5-10 | < 1 | seconds | 5-10x faster |
| Background CPU | 5-10 | 1-2 | % | 75% reduction |
| Database Queries | Full scans | Index scans | - | Indexed |
| ADW Monitor Polling | 2000/s | 0.5/s | polls/sec | 4000x reduction |

### Detailed Results

**Fix #1: Database Indexes**
- Status: [✓] Complete / [ ] Pending
- Metrics:
  - API response: _____ → _____ seconds (___x)
  - Index count: _____ indexes created
  - Query plan: Now uses index ✓
- Date completed: _______

**Fix #2: Loading States**
- Status: [✓] Complete / [ ] Pending
- Metrics:
  - Time to skeleton: < 100ms ✓
  - Time to content: _____ seconds
  - User feedback: ________________
- Date completed: _______

**Fix #3: Background Sync**
- Status: [✓] Complete / [ ] Pending
- Metrics:
  - Sync enabled: ✓
  - Sync frequency: Every _____ seconds
  - Error count: _____
- Date completed: _______

**Fix #4: Polling Optimization**
- Status: [✓] Complete / [ ] Pending
- Metrics:
  - ADW monitor interval: 0.5s → _____ s
  - CPU reduction: _____%
  - Backend responsiveness: Unchanged ✓
- Date completed: _______

---

## Load Testing (Advanced)

### Simple Load Test with Apache Bench

```bash
# Install if needed
brew install httpd  # macOS
# or: apt-get install apache2-utils  # Linux

# Test with 100 requests, 10 concurrent
ab -n 100 -c 10 http://localhost:8000/api/v1/planned-features

# Output shows:
# - Requests per second
# - Mean response time
# - Min/Max response times
# - Failed requests
```

**Expected Results:**
- Requests per second: > 10 (before fixes might be < 1)
- Mean response time: < 100ms (with indexes)
- Failed requests: 0

### Load Test with k6 (More Advanced)

```bash
# Install: https://k6.io/docs/getting-started/installation/

# Create load-test.js
cat > load-test.js << 'EOF'
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: 20 },  // Ramp-up
    { duration: '1m', target: 100 },  // Stay at 100 users
    { duration: '30s', target: 0 },   // Ramp-down
  ],
};

export default function () {
  let res = http.get('http://localhost:8000/api/v1/planned-features');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 1s': (r) => r.timings.duration < 1000,
  });
  sleep(1);
}
EOF

# Run test
k6 run load-test.js
```

---

## Monitoring Dashboard (Optional)

### Real-time Metrics Script

```bash
#!/bin/bash
# monitor_performance.sh

while true; do
  clear
  echo "=== TAC-WebBuilder Performance Monitor ==="
  echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
  echo ""

  echo "1. API Response Time:"
  time_ms=$(curl -w "%{time_total}\n" -o /dev/null -s http://localhost:8000/api/v1/planned-features | awk '{print int($1*1000)}')
  echo "   Planned Features: ${time_ms}ms"
  echo ""

  echo "2. Backend CPU Usage:"
  top -p $(pgrep -f "uvicorn") -b -n 1 | grep uvicorn | awk '{print "   " $3 "%"}'
  echo ""

  echo "3. Active Connections:"
  netstat -an | grep ESTABLISHED | wc -l
  echo ""

  echo "4. Database Status:"
  sqlite3 db/workflow_history.db "SELECT COUNT(*) FROM planned_features;" | awk '{print "   Total features: " $1}'
  echo ""

  echo "Press Ctrl+C to stop"
  sleep 10
done
```

**Run:**
```bash
chmod +x monitor_performance.sh
./monitor_performance.sh
```

---

## Regression Testing

After each fix, ensure no regressions:

```bash
# Run full test suite
cd app/server
pytest -v --tb=short

# Check:
# - All tests pass
# - No new warnings
# - Database integrity intact
# - WebSocket connections stable
```

**Regression checklist:**
- [ ] Planned features tests pass
- [ ] Queue tests pass
- [ ] Background task tests pass
- [ ] WebSocket tests pass
- [ ] No performance degradation

---

## Performance Validation Checklist

- [ ] Baseline metrics recorded (before any fixes)
- [ ] Fix #1 (indexes) implemented and validated
  - [ ] Indexes created
  - [ ] API < 1 second
  - [ ] 100x speedup verified
- [ ] Fix #2 (loading states) implemented and validated
  - [ ] Loading skeleton appears immediately
  - [ ] Content loads after API returns
  - [ ] No blank screen
- [ ] Fix #3 (background sync) implemented and validated
  - [ ] Sync enabled
  - [ ] Logs show sync running
  - [ ] No database errors
- [ ] Fix #4 (polling intervals) implemented and validated
  - [ ] Intervals configured correctly
  - [ ] CPU usage reduced
  - [ ] WebSocket responsive
- [ ] Full test suite passes
- [ ] No regressions detected
- [ ] Performance improvements documented

---

## Success Criteria

**All metrics must improve:**

| Metric | Before | After | Status |
|--------|--------|-------|--------|
| API response time | 55s | < 1s | [ ] Pass |
| Frontend load perceived | 60s blank | < 0.5s skeleton | [ ] Pass |
| Background CPU | 5-10% | 1-2% | [ ] Pass |
| Index count | 0 | 5 | [ ] Pass |
| All tests | TBD | Pass | [ ] Pass |

---

## Troubleshooting

### API Still Slow (> 5 seconds)

**Check:**
1. Indexes exist: `sqlite3 db/workflow_history.db ".indices"`
2. Indexes being used: `EXPLAIN QUERY PLAN SELECT ...`
3. Caching headers set: Check response headers in DevTools

**If still slow:**
- [ ] Drop and recreate indexes
- [ ] Check database file size and corruption
- [ ] Profile with SQLite EXPLAIN ANALYZE

### Frontend Still Loading Slow

**Check:**
1. Network latency: DevTools Network tab
2. Backend API response: `time curl ...`
3. Bundle size: `npm run build` and check dist/

**If still slow:**
- [ ] Increase backend concurrency
- [ ] Check for other blocking requests
- [ ] Enable HTTP caching

### CPU Still High

**Check:**
1. Polling intervals: `grep watch_interval server.py`
2. Background tasks: `ps aux | grep uvicorn`
3. Database locks: `lsof | grep workflow_history.db`

---

## Final Validation

Run this command to validate all fixes:

```bash
#!/bin/bash
# final_validation.sh

echo "=== Final Performance Validation ==="

# Check 1: Indexes
echo "1. Checking indexes..."
INDEX_COUNT=$(sqlite3 db/workflow_history.db ".indices planned_features" | wc -l)
if [ $INDEX_COUNT -ge 5 ]; then echo "✓ Indexes created ($INDEX_COUNT)"; else echo "✗ Missing indexes"; fi

# Check 2: API Performance
echo "2. Checking API response time..."
RESPONSE_TIME=$(curl -w "%{time_total}\n" -o /dev/null -s http://localhost:8000/api/v1/planned-features)
if (( $(echo "$RESPONSE_TIME < 2" | bc -l) )); then echo "✓ API fast ($RESPONSE_TIME s)"; else echo "✗ API slow ($RESPONSE_TIME s)"; fi

# Check 3: Background Sync
echo "3. Checking background sync..."
if grep -q "enable_background_sync=True" app/server/server.py; then echo "✓ Sync enabled"; else echo "✗ Sync disabled"; fi

# Check 4: Polling Intervals
echo "4. Checking polling intervals..."
if grep -q "adw_monitor_watch_interval=2.0" app/server/server.py; then echo "✓ Intervals optimized"; else echo "✗ Intervals not optimized"; fi

# Check 5: Tests
echo "5. Running tests..."
pytest -q --tb=no
if [ $? -eq 0 ]; then echo "✓ All tests pass"; else echo "✗ Tests failing"; fi

echo ""
echo "=== Validation Complete ==="
```

