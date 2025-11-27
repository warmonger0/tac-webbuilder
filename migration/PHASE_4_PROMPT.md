# Task: PostgreSQL Migration - Phase 4: Testing & Verification

## Context
I'm working on the tac-webbuilder project. Phase 3 is complete (data migrated to PostgreSQL). Now in **Phase 4 of 6** - comprehensive testing to ensure PostgreSQL works correctly before production deployment.

## Objective
Run full test suite, perform integration tests, load tests, and manual verification to ensure PostgreSQL is production-ready.

## Background Information
- **Phase 3 Status:** ✅ Complete - Data migrated successfully
- **Current State:** Application works with SQLite (proven) and PostgreSQL (needs testing)
- **Testing Scope:** Unit tests, integration tests, performance tests, manual QA
- **Risk Level:** Medium (testing phase - no production impact yet)
- **Estimated Time:** 4 hours

## Step-by-Step Instructions

### Step 1: Run Full Test Suite with Both Databases

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Test with SQLite (baseline - should pass)
DB_TYPE=sqlite pytest tests/ -v --tb=short

# Test with PostgreSQL (new - should also pass)
export DB_TYPE=postgresql
export POSTGRES_PASSWORD=changeme
pytest tests/ -v --tb=short
```

**Expected:** All tests pass with both databases

### Step 2: Run Integration Tests

```bash
# Run integration test suite
pytest tests/integration/ -v

# Specific integration tests
pytest tests/integration/test_workflow_history_integration.py -v
pytest tests/integration/test_api_contracts.py -v
pytest tests/integration/test_file_query_pipeline.py -v
```

**Expected:** All integration tests pass

### Step 3: Performance Comparison Tests

Create `migration/benchmark_databases.py`:

```python
"""
Database Performance Benchmark

Compares SQLite vs PostgreSQL performance.
"""

import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "app" / "server"))

import os
from database import get_database_adapter


def benchmark_query(adapter, query, params=None, iterations=100):
    """Run query multiple times and measure average time"""
    times = []

    for _ in range(iterations):
        start = time.time()
        with adapter.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            cursor.fetchall()
        times.append(time.time() - start)

    avg_time = sum(times) / len(times)
    return avg_time


def main():
    """Run benchmarks"""
    print("=" * 60)
    print("Database Performance Benchmark")
    print("=" * 60)

    queries = [
        ("Simple SELECT", "SELECT * FROM workflow_history LIMIT 100", None),
        ("COUNT query", "SELECT COUNT(*) FROM workflow_history", None),
        ("JOIN query", """
            SELECT wh.*, tc.tool_name
            FROM workflow_history wh
            LEFT JOIN tool_calls tc ON wh.workflow_id = tc.workflow_id
            LIMIT 100
        """, None),
        ("WHERE with INDEX", "SELECT * FROM workflow_history WHERE status = %s", ("completed",)),
    ]

    # Test SQLite
    print("\n📊 SQLite Performance:")
    os.environ["DB_TYPE"] = "sqlite"
    sqlite_adapter = get_database_adapter()

    sqlite_results = {}
    for name, query, params in queries:
        # Convert %s to ? for SQLite
        sqlite_query = query.replace("%s", "?")
        avg_time = benchmark_query(sqlite_adapter, sqlite_query, params)
        sqlite_results[name] = avg_time
        print(f"  {name}: {avg_time*1000:.2f}ms")

    # Test PostgreSQL
    print("\n📊 PostgreSQL Performance:")
    os.environ["DB_TYPE"] = "postgresql"
    os.environ["POSTGRES_PASSWORD"] = "changeme"
    postgres_adapter = get_database_adapter()

    postgres_results = {}
    for name, query, params in queries:
        avg_time = benchmark_query(postgres_adapter, query, params)
        postgres_results[name] = avg_time
        print(f"  {name}: {avg_time*1000:.2f}ms")

    # Comparison
    print("\n📈 Performance Comparison:")
    for name in sqlite_results:
        sqlite_time = sqlite_results[name]
        postgres_time = postgres_results[name]
        if postgres_time < sqlite_time:
            speedup = sqlite_time / postgres_time
            print(f"  {name}: PostgreSQL {speedup:.2f}x FASTER ✅")
        else:
            slowdown = postgres_time / sqlite_time
            print(f"  {name}: PostgreSQL {slowdown:.2f}x slower ⚠️")

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Run benchmark:

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/migration
python benchmark_databases.py
```

**Expected:** PostgreSQL should be similar or faster, especially for complex queries

### Step 4: Load Testing

```bash
# Install load testing tool if needed
pip install locust

# Create load test script
cat > migration/load_test.py << 'EOF'
from locust import HttpUser, task, between

class WebBuilderUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def get_workflows(self):
        self.client.get("/api/v1/workflows")

    @task
    def get_system_status(self):
        self.client.get("/api/v1/system-status")

    @task
    def get_queue(self):
        self.client.get("/api/v1/queue")
EOF

# Run load test
cd migration
DB_TYPE=postgresql locust -f load_test.py --headless -u 10 -r 2 -t 1m --host http://localhost:8000
```

**Expected:** No errors, reasonable response times

### Step 5: Manual QA Testing

Start application with PostgreSQL:

```bash
export DB_TYPE=postgresql
export POSTGRES_PASSWORD=changeme
./scripts/webbuilder start
```

**Manual Test Checklist:**

1. **Home Page** (http://localhost:5173)
   - [ ] Page loads without errors
   - [ ] No console errors

2. **Create New Request**
   - [ ] Can enter description
   - [ ] Can set project path
   - [ ] Auto-post checkbox works
   - [ ] Generate Issue button works
   - [ ] Preview displays correctly

3. **Workflow History**
   - [ ] Shows all migrated workflows
   - [ ] Filters work (status, date)
   - [ ] Details load correctly
   - [ ] Pagination works

4. **Phase Queue**
   - [ ] Shows queued phases
   - [ ] Phase status updates
   - [ ] Can create multi-phase workflows

5. **System Status**
   - [ ] All services show status
   - [ ] Health checks pass
   - [ ] Database shows "PostgreSQL"

6. **ADW Monitor**
   - [ ] Shows active ADWs
   - [ ] Real-time updates work

### Step 6: Data Integrity Checks

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U tac_user -d tac_webbuilder

# Run integrity checks
-- Check for NULL values where they shouldn't be
SELECT COUNT(*) FROM workflow_history WHERE adw_id IS NULL;
-- Should be 0

-- Check foreign key integrity
SELECT COUNT(*) FROM tool_calls tc
LEFT JOIN workflow_history wh ON tc.workflow_id = wh.workflow_id
WHERE wh.workflow_id IS NULL;
-- Should be 0

-- Check date ranges are valid
SELECT COUNT(*) FROM workflow_history
WHERE start_time > end_time AND end_time IS NOT NULL;
-- Should be 0

-- Check JSONB fields are valid
SELECT COUNT(*) FROM workflow_history
WHERE structured_input IS NOT NULL
AND NOT (structured_input::text ~ '^\{.*\}$');
-- Should be 0
```

### Step 7: Concurrent Access Test

```bash
# Run multiple test sessions simultaneously
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Terminal 1
DB_TYPE=postgresql pytest tests/ &

# Terminal 2
DB_TYPE=postgresql pytest tests/ &

# Terminal 3
DB_TYPE=postgresql pytest tests/ &

# Wait for all to complete
wait

# All should pass without deadlocks
```

### Step 8: Rollback Test

Verify we can rollback to SQLite if needed:

```bash
# Stop application
./scripts/webbuilder stop

# Switch to SQLite
export DB_TYPE=sqlite
unset POSTGRES_PASSWORD

# Start application
./scripts/webbuilder start

# Verify it works
curl http://localhost:8000/api/v1/system-status

# Stop again
./scripts/webbuilder stop
```

**Expected:** SQLite still works (rollback path verified)

### Step 9: Document Test Results

Create `migration/TEST_RESULTS.md`:

```markdown
# PostgreSQL Migration - Test Results

## Date: [YYYY-MM-DD]
## Phase: 4 - Testing & Verification

### Unit Tests
- SQLite: ✅ XXX/XXX passing
- PostgreSQL: ✅ XXX/XXX passing

### Integration Tests
- ✅ All integration tests passing

### Performance Tests
- Simple SELECT: PostgreSQL X.XXx faster
- Complex JOIN: PostgreSQL X.XXx faster
- Writes: Similar performance

### Load Tests
- Concurrent users: 10
- Duration: 1 minute
- Requests: XXX
- Failures: 0 ✅
- Avg response time: XXms

### Manual QA
- ✅ All features working
- ✅ No console errors
- ✅ Data displays correctly
- ✅ Real-time updates work

### Data Integrity
- ✅ No NULL violations
- ✅ Foreign keys valid
- ✅ Date ranges valid
- ✅ JSON fields valid

### Rollback Test
- ✅ Can switch back to SQLite successfully

## Conclusion
PostgreSQL is **PRODUCTION READY** ✅
```

### Step 10: Commit Test Results

```bash
git add migration/
git commit -m "$(cat <<'EOF'
test: Comprehensive PostgreSQL testing complete (Phase 4)

All tests pass with PostgreSQL - production ready.

Phase 4 Complete (4 hours):
✅ Full test suite passing (both databases)
✅ Integration tests passing
✅ Performance tests: PostgreSQL comparable/faster
✅ Load tests: No errors, good response times
✅ Manual QA: All features working
✅ Data integrity: All checks passing
✅ Concurrent access: No deadlocks
✅ Rollback tested: Can revert to SQLite

Test Results:
- Unit tests: XXX/XXX passing (100%)
- Integration tests: XX/XX passing (100%)
- Load test: 10 users, XXX requests, 0 failures
- Performance: Similar or better than SQLite

Files Created:
+ migration/benchmark_databases.py
+ migration/load_test.py
+ migration/TEST_RESULTS.md

PostgreSQL Status: PRODUCTION READY ✅

Next: Phase 5 - Deployment (2 hours)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Success Criteria

- ✅ Full test suite passing with PostgreSQL
- ✅ Integration tests passing
- ✅ Performance acceptable (similar or better than SQLite)
- ✅ Load tests successful (no errors)
- ✅ Manual QA complete (all features work)
- ✅ Data integrity validated
- ✅ Rollback path verified
- ✅ Test results documented
- ✅ Changes committed

## Troubleshooting

**If tests fail with "connection pool exhausted":**
```bash
# Increase pool size in .env
POSTGRES_POOL_MAX=20
```

**If performance is slow:**
```sql
-- Check for missing indexes
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public';

-- Run VACUUM ANALYZE
VACUUM ANALYZE;
```

**If deadlocks occur:**
```sql
-- Check for lock conflicts
SELECT * FROM pg_locks WHERE NOT granted;
```

## Next Steps

After completing Phase 4, report:
- "Phase 4 complete - All tests passing ✅"
- PostgreSQL is production ready
- Performance comparison results

**Next Task:** Phase 5 - Deployment (2 hours)

---

**Ready to copy into a new chat!** 🚀
