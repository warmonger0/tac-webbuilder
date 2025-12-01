# Cleanup & Performance Optimization - Phase Tracker

## Overview

**Project:** tac-webbuilder
**Goal:** Clean up technical debt and optimize performance post-PostgreSQL migration
**Strategy:** Phased approach - cleanup first, then optimization
**Status:** 🚀 **READY TO START**

### Quick Summary
- 🎯 **Current Test Pass Rate:** 81% SQLite, 79.8% PostgreSQL
- 🎯 **Target Test Pass Rate:** 95%+ for both databases
- 📊 **Pre-existing Issues:** ~146 test failures to investigate
- ⚡ **Performance:** Already good, can be optimized further

### Motivation
With the PostgreSQL migration complete, we have a solid foundation. Now we can:
1. **Clean up technical debt** accumulated over time
2. **Fix pre-existing test failures** not related to migration
3. **Optimize performance** using PostgreSQL-specific features
4. **Improve code quality** and maintainability

---

## Cleanup & Optimization Phases

### 📋 Phase 1: Test Cleanup (READY TO START)
**Goal:** Fix pre-existing test failures and improve test infrastructure
**Duration:** Estimated 4-6 hours
**Status:** Ready to start

**Issues to Fix:**
1. **SQL Injection Test Failures** (~10-15 failures)
   - Tests reference non-existent `core/sql_processor.py`
   - Need to either remove tests or implement missing code
   - Both databases affected equally

2. **Database Initialization Errors** (100 errors)
   - Location: `core/workflow_history_utils/test_database.py`
   - Tests have initialization issues
   - Need to investigate root cause

3. **Remaining Test Failures** (~30-40 failures)
   - Various test failures unrelated to migration
   - Need investigation and categorization

**Target Improvement:**
- Current: 620/766 (81.0%) SQLite, 611/766 (79.8%) PostgreSQL
- Target: 650-680/766 (85-89%) for both databases

**Prompt:** `CLEANUP_PHASE1_TEST_FIXES.md` (to be created)

---

### 🧹 Phase 2: Code Cleanup (PENDING)
**Goal:** Remove dead code, fix deprecations, improve code quality
**Duration:** Estimated 3-4 hours
**Status:** Pending Phase 1 completion

**Tasks:**
1. **Remove Dead Code**
   - Files referencing non-existent modules
   - Unused imports and functions
   - Deprecated patterns

2. **Dependency Cleanup**
   - Remove unused dependencies
   - Update outdated packages
   - Consolidate duplicate utilities

3. **Code Quality Improvements**
   - Fix linting issues
   - Standardize error handling
   - Improve type hints

4. **Documentation Updates**
   - Update outdated comments
   - Document complex logic
   - Add missing docstrings

**Target Metrics:**
- Zero dead code references
- All dependencies actively used
- 90%+ code quality score

**Prompt:** `CLEANUP_PHASE2_CODE_QUALITY.md` (to be created)

---

### ⚡ Phase 3: Query Performance Optimization (PENDING)
**Goal:** Optimize database queries for both SQLite and PostgreSQL
**Duration:** Estimated 4-6 hours
**Status:** Pending Phase 1-2 completion

**Tasks:**
1. **N+1 Query Detection and Fixes**
   - Scan codebase for N+1 patterns (mentioned in CLAUDE.md)
   - Replace `get_all()` + loop with direct queries
   - Use JOINs instead of multiple queries

2. **Index Optimization**
   - Analyze slow queries
   - Add missing indexes
   - Remove unused indexes
   - Optimize composite indexes

3. **Query Optimization**
   - Replace SELECT * with specific columns
   - Add query result caching where appropriate
   - Optimize complex queries with EXPLAIN ANALYZE

4. **Connection Pool Tuning**
   - Optimize pool size for workload
   - Add connection monitoring
   - Tune timeout settings

**Target Metrics:**
- Zero N+1 query patterns
- All queries under 50ms (P95)
- Database connection pool utilization < 80%

**Prompt:** `OPTIMIZATION_PHASE3_QUERIES.md` (to be created)

---

### 🚀 Phase 4: Application Performance (PENDING)
**Goal:** Optimize application-level performance
**Duration:** Estimated 3-4 hours
**Status:** Pending Phase 3 completion

**Tasks:**
1. **Caching Strategy**
   - Implement Redis/memory caching for hot data
   - Cache expensive computations
   - Add cache invalidation logic

2. **Async Operations**
   - Identify blocking operations
   - Convert to async where beneficial
   - Optimize background job processing

3. **Resource Optimization**
   - Optimize memory usage
   - Reduce CPU-intensive operations
   - Optimize file I/O

4. **API Response Times**
   - Target < 100ms for simple endpoints
   - Target < 500ms for complex operations
   - Add response time monitoring

**Target Metrics:**
- API response time P95 < 200ms
- Memory usage optimized
- Zero blocking operations in hot paths

**Prompt:** `OPTIMIZATION_PHASE4_APPLICATION.md` (to be created)

---

### 📊 Phase 5: Monitoring & Observability (PENDING)
**Goal:** Add comprehensive monitoring and performance tracking
**Duration:** Estimated 2-3 hours
**Status:** Pending Phase 4 completion

**Tasks:**
1. **Database Monitoring**
   - Query performance tracking
   - Connection pool monitoring
   - Slow query logging

2. **Application Metrics**
   - Request/response time tracking
   - Error rate monitoring
   - Resource usage tracking

3. **Alerting Setup**
   - Slow query alerts
   - High error rate alerts
   - Resource exhaustion alerts

4. **Performance Dashboards**
   - Real-time performance metrics
   - Historical trend analysis
   - Database health dashboard

**Deliverables:**
- Prometheus/Grafana setup (or similar)
- Comprehensive dashboards
- Alert configuration
- Performance baseline documentation

**Prompt:** `OPTIMIZATION_PHASE5_MONITORING.md` (to be created)

---

## Current Test Failure Breakdown

### From PostgreSQL Migration Testing

**Total Tests:** 766
**Passing (SQLite):** 620 (81.0%)
**Passing (PostgreSQL):** 611 (79.8%)
**Failing:** ~146 tests

### Categorization

#### Category 1: Database Initialization Errors (100 errors)
- **Location:** `core/workflow_history_utils/test_database.py`
- **Impact:** High (13% of all tests)
- **Priority:** P1 - Critical
- **Estimated Fix Time:** 2-3 hours

#### Category 2: SQL Injection Test Failures (10-15 failures)
- **Root Cause:** Missing `core/sql_processor.py`
- **Impact:** Medium (1-2% of tests)
- **Priority:** P2 - High
- **Estimated Fix Time:** 1-2 hours

#### Category 3: Other Test Failures (30-40 failures)
- **Status:** Need investigation
- **Impact:** Medium (4-5% of tests)
- **Priority:** P2 - High
- **Estimated Fix Time:** 2-3 hours

---

## Performance Baseline

### Current Performance (From Phase 3 Testing)

**Database Operations (100 operations each):**
| Operation | SQLite | PostgreSQL | Winner |
|-----------|--------|------------|--------|
| INSERT | 0.110s | 0.106s | PostgreSQL (4% faster) |
| SELECT | 0.060s | 0.062s | SQLite (marginal) |
| UPDATE | 0.118s | 0.093s | PostgreSQL (27% faster) |
| DELETE | 0.128s | 0.143s | SQLite (12% faster) |
| **Total** | **0.416s** | **0.404s** | **PostgreSQL (3% faster)** |

### Performance Goals

**After Optimization:**
| Operation | Target | Improvement Goal |
|-----------|--------|------------------|
| INSERT | < 0.080s | 20-30% faster |
| SELECT | < 0.040s | 30-40% faster |
| UPDATE | < 0.070s | 20-30% faster |
| DELETE | < 0.100s | 20-30% faster |
| **Total** | **< 0.300s** | **25-30% faster** |

**Methods:**
- Add strategic indexes
- Optimize queries (remove SELECT *)
- Use prepared statements
- Connection pool optimization
- Query result caching

---

## Success Criteria

### Phase 1: Test Cleanup ✅
- [ ] Database initialization errors fixed (100 → 0)
- [ ] SQL injection tests fixed or removed (10-15 → 0)
- [ ] Other test failures investigated and categorized
- [ ] Test pass rate: 85%+ for both databases
- [ ] All changes documented

### Phase 2: Code Cleanup ✅
- [ ] Zero dead code references
- [ ] All dependencies actively used
- [ ] Linting issues resolved
- [ ] Documentation updated
- [ ] Code quality score: 90%+

### Phase 3: Query Optimization ✅
- [ ] Zero N+1 query patterns
- [ ] Strategic indexes added
- [ ] Query performance improved 25%+
- [ ] All queries under 50ms (P95)
- [ ] Optimization results documented

### Phase 4: Application Performance ✅
- [ ] Caching strategy implemented
- [ ] Async operations optimized
- [ ] API response times improved
- [ ] P95 response time < 200ms
- [ ] Memory usage optimized

### Phase 5: Monitoring ✅
- [ ] Database monitoring in place
- [ ] Application metrics tracked
- [ ] Alerts configured
- [ ] Performance dashboards created
- [ ] Baseline documentation complete

---

## Prompt Library

### Available Prompts

1. **CLEANUP_PHASE1_TEST_FIXES.md** ✅
   - **Phase:** 1 (Test Cleanup)
   - **Purpose:** Fix 100+ pre-existing test failures
   - **Duration:** 4-6 hours
   - **Status:** Ready to use
   - **Fixes:** Database init errors (100), SQL injection tests (10-15), misc failures (30-40)
   - **Target:** 85-89% test pass rate

### Pending Prompts

2. **CLEANUP_PHASE2_CODE_QUALITY.md**
   - **Phase:** 2 (Code Cleanup)
   - **Purpose:** Remove dead code and improve quality
   - **Duration:** 3-4 hours
   - **Create When:** After Phase 1 complete

3. **OPTIMIZATION_PHASE3_QUERIES.md**
   - **Phase:** 3 (Query Optimization)
   - **Purpose:** Optimize database queries and eliminate N+1 patterns
   - **Duration:** 4-6 hours
   - **Create When:** After Phase 2 complete
   - **Focus:** N+1 queries, indexes, query optimization

4. **OPTIMIZATION_PHASE4_APPLICATION.md**
   - **Phase:** 4 (Application Performance)
   - **Purpose:** Optimize application-level performance
   - **Duration:** 3-4 hours
   - **Create When:** After Phase 3 complete

5. **OPTIMIZATION_PHASE5_MONITORING.md**
   - **Phase:** 5 (Monitoring)
   - **Purpose:** Set up comprehensive monitoring
   - **Duration:** 2-3 hours
   - **Create When:** After Phase 4 complete

---

## Known Issues (From Testing)

### High Priority

1. **Database Initialization Errors** (100 errors)
   - File: `core/workflow_history_utils/test_database.py`
   - Error: Various initialization failures
   - Impact: 13% of all tests
   - Affects: Both SQLite and PostgreSQL equally

2. **SQL Injection Tests** (10-15 failures)
   - Missing: `core/sql_processor.py`
   - Tests reference non-existent code
   - Impact: 1-2% of tests
   - Affects: Both databases equally

### Medium Priority

3. **Miscellaneous Test Failures** (30-40 failures)
   - Various test files
   - Need investigation to categorize
   - Impact: 4-5% of tests

### Low Priority (Future Enhancements)

4. **N+1 Query Patterns**
   - Mentioned in CLAUDE.md
   - Example: `queue_routes.py:324-329`
   - Pattern: `get_all()` + loop to find one item
   - Should use: `find_by_id()` direct query

5. **Missing Indexes**
   - Need query analysis to identify
   - Look for slow queries in production logs
   - Add indexes based on actual usage patterns

---

## Timeline

### Estimated Timeline
- **Phase 1:** Test Cleanup (4-6 hours)
- **Phase 2:** Code Cleanup (3-4 hours)
- **Phase 3:** Query Optimization (4-6 hours)
- **Phase 4:** Application Performance (3-4 hours)
- **Phase 5:** Monitoring (2-3 hours)

**Total Estimated Time:** 16-23 hours

### Actual Timeline
- **Phase 1:** [TBD]
- **Phase 2:** [TBD]
- **Phase 3:** [TBD]
- **Phase 4:** [TBD]
- **Phase 5:** [TBD]

**Total Actual Time:** [TBD]

---

## Test Improvement Projections

### Current State
- SQLite: 620/766 (81.0%)
- PostgreSQL: 611/766 (79.8%)

### After Phase 1 (Test Cleanup)
- Target: 650-680/766 (85-89%)
- Improvement: +30-60 tests fixed
- Focus: Database init errors, SQL injection tests

### After Phase 2 (Code Cleanup)
- Target: 680-700/766 (89-91%)
- Improvement: +20-30 tests fixed
- Focus: Code quality issues causing test failures

### Final Target
- Target: 720-750/766 (94-98%)
- Total Improvement: +100-130 tests
- Remaining: Edge cases, flaky tests, future improvements

---

## Performance Improvement Projections

### Current Performance
- PostgreSQL: 0.404s for 400 operations (INSERT/SELECT/UPDATE/DELETE × 100)
- Average: ~1ms per operation

### After Phase 3 (Query Optimization)
- Target: 0.300s for 400 operations (25% improvement)
- Methods: Indexes, query optimization, N+1 elimination
- Average: ~0.75ms per operation

### After Phase 4 (Application Performance)
- API response times: P95 < 200ms
- Memory usage: Optimized
- CPU usage: Reduced

### After Phase 5 (Monitoring)
- Real-time performance visibility
- Proactive issue detection
- Continuous optimization capability

---

## Quick Reference

### File Locations

**Test Files:**
- Main test suite: `app/server/tests/`
- Database init errors: `core/workflow_history_utils/test_database.py`
- SQL injection tests: Various test files (need to locate)

**Performance-Related:**
- Queue routes (N+1 pattern): `app/server/routes/queue_routes.py:324-329`
- Database adapter: `app/server/database/db_adapter.py`
- Repositories: `app/server/repositories/`

**Documentation:**
- Migration tracker: `POSTGRES_MIGRATION_TRACKER.md`
- Test results: `POSTGRES_TEST_RESULTS.md`
- This tracker: `CLEANUP_OPTIMIZATION_TRACKER.md`

### Commands

**Run Tests:**
```bash
cd app/server
export DB_TYPE=sqlite  # or postgresql
uv run pytest tests/ -v --tb=short
```

**Performance Benchmark:**
```bash
cd app/server
uv run python benchmark_db_performance.py
```

**Find N+1 Patterns:**
```bash
cd app/server
grep -n "get_all" routes/*.py services/*.py | grep -B2 -A5 "for.*in"
```

**Check Code Quality:**
```bash
cd app/server
ruff check .  # or your linter
mypy .  # type checking
```

---

## Next Steps

### Immediate Actions

1. **Review Current State**
   - Read this tracker
   - Review POSTGRES_TEST_RESULTS.md
   - Understand scope of cleanup needed

2. **Create Phase 1 Prompt**
   - `CLEANUP_PHASE1_TEST_FIXES.md`
   - Detailed steps to fix 100+ test failures
   - Investigation plan for unknown failures

3. **Start Phase 1**
   - Fix database initialization errors (100 errors)
   - Fix SQL injection tests (10-15 failures)
   - Investigate remaining failures (30-40)
   - Target: 85%+ test pass rate

### For Next Session

**Copy this to new context:**
```
I'm working on cleanup and performance optimization for tac-webbuilder.

PostgreSQL migration is complete! Now cleaning up technical debt.

Current status:
- Test pass rate: 81% SQLite, 79.8% PostgreSQL
- Target: 95%+ for both databases
- Issues: 100 database init errors, 10-15 SQL injection test failures, 30-40 misc failures

Task: Fix pre-existing test failures (Phase 1)

Please read CLEANUP_OPTIMIZATION_TRACKER.md for full context.
```

---

**Last Updated:** 2025-11-28
**Status:** Ready to start Phase 1 (Test Cleanup)
**Total Estimated Time:** 16-23 hours
**Expected Outcome:** 95%+ test pass rate, 25%+ performance improvement
