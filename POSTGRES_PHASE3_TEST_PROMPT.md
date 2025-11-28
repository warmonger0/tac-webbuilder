# Task: Run PostgreSQL Migration Tests (Phase 3 Validation)

## Context
I'm working on the tac-webbuilder project. Phase 3 of the PostgreSQL migration is complete, which included creating comprehensive testing infrastructure. Now I need to validate that PostgreSQL integration works correctly before proceeding to Phase 4.

## Objective
Run the complete PostgreSQL test suite to validate:
1. Database connectivity and configuration
2. CRUD operations with PostgreSQL adapter
3. Performance comparison between SQLite and PostgreSQL
4. Full test suite compatibility with both databases
5. Document results for Phase 4 planning

## Background Information
- **Phase:** 3 (Testing & Validation) → 4 (Migration & Fixes)
- **Current State:** Testing infrastructure complete, PostgreSQL not yet started
- **Database:** PostgreSQL 15 (Alpine) via Docker Compose
- **Risk Level:** Low (read-only validation, no production impact)
- **Estimated Time:** 20-30 minutes (including Docker startup)

## What Was Built in Phase 3

### Test Scripts (app/server/)
1. **test_postgres_connection.py** - Connection validator
   - Tests database adapter initialization
   - Validates placeholder style (%s vs ?)
   - Checks PostgreSQL version and table count
   - Provides troubleshooting guidance

2. **test_db_operations.py** - CRUD operations tester
   - INSERT: Create test phase queue items
   - SELECT: Retrieve items by ID
   - UPDATE: Modify item status
   - DELETE: Remove items
   - Connection pooling (5 concurrent connections)
   - Database-agnostic query validation

3. **benchmark_db_performance.py** - Performance benchmark
   - Runs 100 operations of each type (INSERT, SELECT, UPDATE, DELETE)
   - Compares SQLite vs PostgreSQL side-by-side
   - Generates performance metrics table

### Configuration Files
- **.env.postgres.example** - PostgreSQL configuration template
- **POSTGRES_TEST_RESULTS.md** - Test results documentation template
- **docker-compose.yml** - PostgreSQL service definition (already existed)
- **migration/postgres_schema.sql** - Full schema (26 tables, 41 indexes)

### Automation
- **scripts/test_postgres_migration.sh** - Automated test runner
  - Checks Docker status
  - Starts PostgreSQL container
  - Runs all test scripts sequentially
  - Executes full pytest suite with both databases
  - Generates comparison report

## Infrastructure Details

### PostgreSQL Configuration
```yaml
# docker-compose.yml
postgres:
  image: postgres:15-alpine
  container_name: tac-webbuilder-postgres
  environment:
    POSTGRES_DB: tac_webbuilder
    POSTGRES_USER: tac_user
    POSTGRES_PASSWORD: tac_dev_password
  ports:
    - "5432:5432"
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./migration/postgres_schema.sql:/docker-entrypoint-initdb.d/init.sql
  healthcheck:
    test: ["CMD-HALT", "pg_isready", "-U", "tac_user", "-d", "tac_webbuilder"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### Environment Variables
```bash
# .env.postgres (create from .env.postgres.example)
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tac_webbuilder
DB_USER=tac_user
DB_PASSWORD=tac_dev_password
```

### Database Adapter
- **Location:** `app/server/database/db_adapter.py`
- **SQLite Placeholder:** `?`
- **PostgreSQL Placeholder:** `%s`
- **Lazy Initialization:** Adapter created on first use
- **Connection Pooling:** Supported for PostgreSQL

## Step-by-Step Instructions

### Step 1: Verify Prerequisites

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

# Check Docker is installed
docker --version
# Expected: Docker version 20.x or higher

# Check Docker Compose is available
docker-compose --version
# Expected: Docker Compose version 2.x or higher

# Verify test scripts exist
ls -la app/server/test_*.py app/server/benchmark_*.py
# Expected: 3 files listed

# Verify automation script exists
ls -la scripts/test_postgres_migration.sh
# Expected: File exists and is executable
```

### Step 2: Start Docker Desktop

```bash
# Check if Docker is running
docker ps
# If error: "Cannot connect to the Docker daemon"
# → Start Docker Desktop manually and wait for it to be ready

# Verify Docker is ready
docker ps
# Expected: Headers shown (even if no containers running)
```

### Step 3: Start PostgreSQL Container

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

# Start PostgreSQL in detached mode
docker-compose up -d postgres

# Expected output:
# [+] Running 2/2
#  ✔ Network tac-webbuilder_default      Created
#  ✔ Container tac-webbuilder-postgres   Started

# Wait for healthy status (may take 10-30 seconds)
docker-compose ps

# Expected output:
# NAME                      STATUS                    PORTS
# tac-webbuilder-postgres   Up (healthy)             0.0.0.0:5432->5432/tcp

# If status shows "Up (health: starting)", wait 10 seconds and check again
# If status shows "Unhealthy" or "Exited", see Troubleshooting section
```

### Step 4: Verify PostgreSQL Is Ready

```bash
# Check PostgreSQL logs
docker-compose logs postgres | tail -20

# Expected: Should see messages like:
# "database system is ready to accept connections"
# "PostgreSQL init process complete; ready for start up"

# Test direct connection
docker exec -it tac-webbuilder-postgres psql -U tac_user -d tac_webbuilder -c "SELECT version();"

# Expected: PostgreSQL version string
# PostgreSQL 15.x on x86_64-pc-linux-musl, compiled by gcc ...

# Check table count (schema should be loaded automatically)
docker exec -it tac-webbuilder-postgres psql -U tac_user -d tac_webbuilder -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"

# Expected: 26 tables
```

### Step 5: Create PostgreSQL Environment File

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

# Copy example file
cp .env.postgres.example app/server/.env.postgres

# Verify contents
cat app/server/.env.postgres

# Expected contents:
# DB_TYPE=postgresql
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=tac_webbuilder
# DB_USER=tac_user
# DB_PASSWORD=tac_dev_password
```

### Step 6: Run Connection Test

```bash
cd app/server

# Test PostgreSQL connection
uv run python test_postgres_connection.py

# Expected output:
# ========================================
# PostgreSQL Connection Test
# ========================================
#
# Testing database adapter initialization...
# ✅ Adapter type: postgresql
# ✅ Placeholder: %s
# ✅ NOW function: NOW()
#
# Testing PostgreSQL connection...
# ✅ PostgreSQL version: PostgreSQL 15.x on x86_64-pc-linux-musl...
# ✅ Tables in database: 26
#
# Running basic query test...
# ✅ Basic query successful
#
# ========================================
# ✅ PostgreSQL connection test PASSED!
# ========================================

# If any ❌ appears, see Troubleshooting section
```

### Step 7: Run CRUD Operations Test

```bash
cd app/server

# Test CRUD operations
uv run python test_db_operations.py

# Expected output:
# ========================================
# PostgreSQL CRUD Operations Test
# ========================================
#
# Using adapter: postgresql
# Placeholder style: %s
#
# Test 1: INSERT operation
# ✅ Insert successful: Created item with queue_id = [number]
#
# Test 2: SELECT operation
# ✅ Found item: test-postgres-001
#
# Test 3: UPDATE operation
# ✅ Update successful
# ✅ Update verified: status is now 'running'
#
# Test 4: DELETE operation
# ✅ Delete successful
# ✅ Delete verified: item no longer exists
#
# Test 5: Connection pooling (5 concurrent connections)
# ✅ Connection 1 successful
# ✅ Connection 2 successful
# ✅ Connection 3 successful
# ✅ Connection 4 successful
# ✅ Connection 5 successful
# ✅ Connection pooling test PASSED!
#
# Test 6: Database-agnostic queries
# ✅ Parameterized query test PASSED!
# ✅ Datetime function test PASSED!
#
# ========================================
# ✅ ALL TESTS PASSED!
# ========================================

# If any test fails, see Troubleshooting section
```

### Step 8: Run Performance Benchmark

```bash
cd app/server

# Run performance comparison
uv run python benchmark_db_performance.py

# Expected output:
# ========================================
# Database Performance Benchmark
# ========================================
#
# Benchmarking SQLite...
# INSERT: 100 operations...
# SELECT: 100 operations...
# UPDATE: 100 operations...
# DELETE: 100 operations...
#
# Benchmarking PostgreSQL...
# INSERT: 100 operations...
# SELECT: 100 operations...
# UPDATE: 100 operations...
# DELETE: 100 operations...
#
# ========================================
# Performance Comparison (100 operations each)
# ========================================
#
# Operation       SQLite        PostgreSQL    Winner
# -----------------------------------------------------
# INSERT          X.XXXs        X.XXXs        [SQLite/PostgreSQL/Tie]
# SELECT          X.XXXs        X.XXXs        [SQLite/PostgreSQL/Tie]
# UPDATE          X.XXXs        X.XXXs        [SQLite/PostgreSQL/Tie]
# DELETE          X.XXXs        X.XXXs        [SQLite/PostgreSQL/Tie]
#
# Note: Times may vary based on system load
# SQLite: In-memory database, optimized for single process
# PostgreSQL: Client-server, optimized for concurrency

# Document these results in POSTGRES_TEST_RESULTS.md
```

### Step 9: Run Full Test Suite with Both Databases

```bash
cd app/server

# Test with SQLite (current production database)
export DB_TYPE=sqlite
uv run pytest tests/ -v --tb=short

# Count results
# Expected: X tests passed

# Test with PostgreSQL
export DB_TYPE=postgresql
uv run pytest tests/ -v --tb=short

# Count results
# Expected: Similar number of tests passed
# Some tests may fail due to PostgreSQL-specific issues (document these)

# Compare test results
# - Which tests pass with both?
# - Which tests fail with PostgreSQL only?
# - Are failures due to:
#   - Schema differences?
#   - Query syntax issues?
#   - Adapter implementation gaps?
```

### Step 10: Run Automated Test Script (Alternative to Steps 6-9)

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

# Make script executable (if not already)
chmod +x scripts/test_postgres_migration.sh

# Run full automated test suite
./scripts/test_postgres_migration.sh

# This script will:
# 1. Check Docker is running
# 2. Start PostgreSQL if needed
# 3. Run connection test
# 4. Run CRUD operations test
# 5. Run performance benchmark
# 6. Run pytest with SQLite
# 7. Run pytest with PostgreSQL
# 8. Generate comparison report

# Expected: Script completes successfully
# Review output for any failures
```

### Step 11: Document Test Results

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

# Open results template
cat POSTGRES_TEST_RESULTS.md

# Update with actual results:
# 1. Connection test results
# 2. CRUD operations results
# 3. Performance benchmark numbers
# 4. pytest results (pass/fail counts)
# 5. List of failing tests (if any)
# 6. Performance comparison analysis

# Save updated results
# This will be used for Phase 4 planning
```

### Step 12: Review Results and Plan Phase 4

Based on test results, categorize issues:

**Category A: Schema Issues**
- Missing tables or columns
- Incorrect data types
- Missing indexes

**Category B: Query Syntax Issues**
- SQLite-specific syntax (e.g., `datetime('now')`)
- Placeholder mismatches (? vs %s)
- Function differences (SUBSTR vs SUBSTRING)

**Category C: Adapter Implementation Gaps**
- Connection pooling issues
- Transaction handling differences
- Error handling inconsistencies

**Category D: Performance Issues**
- Slow queries needing optimization
- Missing indexes
- N+1 query patterns

Create Phase 4 task list based on categories above.

## Success Criteria

- ✅ Docker Desktop running
- ✅ PostgreSQL container started and healthy
- ✅ Schema loaded (26 tables confirmed)
- ✅ Connection test passes
- ✅ CRUD operations test passes
- ✅ Performance benchmark completes
- ✅ Full pytest suite run with both databases
- ✅ Results documented in POSTGRES_TEST_RESULTS.md
- ✅ Phase 4 issues identified and categorized

## Files Expected to Change

**Created:**
- `app/server/.env.postgres` (from .env.postgres.example)
- `POSTGRES_TEST_RESULTS.md` (updated with actual results)

**No Changes Expected:**
- All test scripts already created in Phase 3
- All infrastructure already in place

## Performance Expectations

### Connection Test
- **Duration:** < 1 second
- **Operations:** 3-5 simple queries
- **Success Rate:** 100%

### CRUD Operations Test
- **Duration:** < 5 seconds
- **Operations:** ~15 database operations
- **Success Rate:** 100%

### Performance Benchmark
- **Duration:** 10-30 seconds
- **Operations:** 400 total (100 × 4 operation types × 2 databases)
- **Expected Results:**
  - SQLite: Faster for single operations (in-memory)
  - PostgreSQL: More consistent under load
  - Difference: Usually within 2-5x range

### Full Test Suite
- **Duration:** 1-5 minutes (depending on test count)
- **SQLite Success Rate:** ~100% (baseline)
- **PostgreSQL Success Rate:** TBD (may have failures to fix in Phase 4)

## Troubleshooting

### Docker Won't Start
```bash
# Check if Docker Desktop is installed
docker --version

# If not installed:
# → Install Docker Desktop from docker.com

# If installed but not running:
# → Open Docker Desktop application
# → Wait for "Docker Desktop is running" status
```

### PostgreSQL Container Won't Start
```bash
# Check if port 5432 is already in use
lsof -ti:5432

# If port is in use:
# Option 1: Kill existing process
lsof -ti:5432 | xargs kill -9

# Option 2: Change port in docker-compose.yml
# ports:
#   - "5433:5432"  # Use 5433 instead
# Then update DB_PORT in .env.postgres

# Clean slate restart
docker-compose down -v
docker-compose up -d postgres

# Check logs for errors
docker-compose logs postgres
```

### PostgreSQL Shows "Unhealthy" Status
```bash
# Check detailed health check logs
docker-compose logs postgres | grep health

# Common causes:
# 1. Database not fully initialized (wait 30 seconds)
# 2. Wrong credentials in healthcheck
# 3. Port conflict

# Verify you can connect manually
docker exec -it tac-webbuilder-postgres psql -U tac_user -d tac_webbuilder

# If manual connection works but healthcheck fails:
# → Edit docker-compose.yml healthcheck configuration
```

### Schema Not Loaded (Table Count = 0)
```bash
# Check if init.sql was executed
docker-compose logs postgres | grep init

# If not executed:
# 1. Schema only loads on FIRST container creation
# 2. If container already exists, need to reload manually

# Manual schema load:
docker exec -i tac-webbuilder-postgres psql -U tac_user -d tac_webbuilder < migration/postgres_schema.sql

# Verify tables created
docker exec -it tac-webbuilder-postgres psql -U tac_user -d tac_webbuilder -c "\dt"

# Expected: 26 tables listed
```

### Connection Test Fails
```bash
# Error: "could not connect to server"
# → Check PostgreSQL is running: docker-compose ps
# → Check port 5432 is accessible: lsof -ti:5432

# Error: "password authentication failed"
# → Verify credentials in .env.postgres match docker-compose.yml
# → Check DB_PASSWORD=tac_dev_password

# Error: "database does not exist"
# → Verify DB_NAME=tac_webbuilder
# → Check database was created: docker exec -it tac-webbuilder-postgres psql -U tac_user -l

# Error: "psycopg2 module not found"
# → Install dependency: cd app/server && uv add psycopg2-binary
```

### CRUD Operations Test Fails
```bash
# Error: "syntax error at or near..."
# → Likely placeholder issue (? vs %s)
# → Check adapter is using correct placeholder: print(db_adapter.placeholder)

# Error: "relation does not exist"
# → Table not created, reload schema (see "Schema Not Loaded" above)

# Error: "column does not exist"
# → Schema mismatch between SQLite and PostgreSQL
# → Compare schemas:
#   - SQLite: .schema phase_queue
#   - PostgreSQL: \d phase_queue

# Error on concurrent connections:
# → PostgreSQL connection limit reached
# → Check max_connections:
#   docker exec -it tac-webbuilder-postgres psql -U tac_user -d tac_webbuilder -c "SHOW max_connections;"
```

### Performance Benchmark Issues
```bash
# Error: Benchmark hangs
# → Likely connection pool exhaustion
# → Check active connections:
#   docker exec -it tac-webbuilder-postgres psql -U tac_user -d tac_webbuilder -c "SELECT COUNT(*) FROM pg_stat_activity;"

# Error: PostgreSQL much slower than SQLite (>10x)
# → Expected for small operations (network overhead)
# → PostgreSQL optimized for concurrency, not single operations
# → Real-world workloads may show different results

# Error: Benchmark fails partway through
# → Cleanup previous test data
# → Check disk space: df -h
```

### Pytest Failures with PostgreSQL
```bash
# Many tests fail with "fixture not found"
# → Tests may need PostgreSQL-specific fixtures
# → Review conftest.py for database setup

# Tests fail with "database is locked"
# → This is SQLite error, not PostgreSQL
# → Make sure DB_TYPE=postgresql is set

# Tests fail with timeout
# → PostgreSQL may be slower for test setup
# → Increase timeout in pytest.ini or test decorators

# Tests fail with "violates foreign key constraint"
# → PostgreSQL enforces FK constraints by default
# → SQLite may not enforce them
# → Need to fix test data order or disable constraints temporarily
```

## Next Steps After Testing

### If All Tests Pass ✅
Congratulations! Your PostgreSQL migration is ready for Phase 4.

**Phase 4 Tasks:**
1. Update production configuration to support both databases
2. Add database selection to startup scripts
3. Create migration documentation
4. Set up CI/CD for both databases
5. Plan production cutover strategy

**Create Phase 4 prompt with actual test results**

### If Some Tests Fail ❌
Don't worry - this is expected! Use test failures to guide Phase 4.

**Categorize failures:**
1. **Critical:** Core functionality broken (CRUD, connections)
   - Fix immediately before proceeding
2. **High:** Major features broken (workflows, GitHub integration)
   - Fix in Phase 4 priority 1
3. **Medium:** Edge cases or specific features
   - Fix in Phase 4 priority 2
4. **Low:** Performance or optimization issues
   - Fix in Phase 4 priority 3

**Document in POSTGRES_TEST_RESULTS.md:**
```markdown
## Test Failures

### Critical Issues (Fix Immediately)
- [ ] Issue 1: Description
  - Test: test_name
  - Error: error message
  - Location: file:line
  - Fix plan: ...

### High Priority (Phase 4.1)
- [ ] Issue 2: ...

### Medium Priority (Phase 4.2)
- [ ] Issue 3: ...

### Low Priority (Phase 4.3)
- [ ] Issue 4: ...
```

**Create Phase 4 prompt prioritizing critical fixes**

## Reporting Back

After completing this task, report:

```
✅ Phase 3 Testing Complete - PostgreSQL Validation Results

Connection Test: [PASSED/FAILED]
CRUD Operations: [PASSED/FAILED]
Performance Benchmark: [COMPLETED]
Full Test Suite (SQLite): [X/Y tests passed]
Full Test Suite (PostgreSQL): [X/Y tests passed]

Issues Found:
- Critical: [count]
- High: [count]
- Medium: [count]
- Low: [count]

Performance Comparison:
- SQLite: [summary]
- PostgreSQL: [summary]
- Winner: [analysis]

Next: [Phase 4 - Immediate fixes / Phase 4 - Full migration / Issue #X]

Results documented in: POSTGRES_TEST_RESULTS.md
```

---

**Ready to copy into a new context!**

This is the validation gate before Phase 4. Run these tests to understand what needs to be fixed in the migration.
