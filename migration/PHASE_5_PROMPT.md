# Task: PostgreSQL Migration - Phase 5: Deployment

## Context
I'm working on the tac-webbuilder project. Phase 4 is complete (all tests passing). Now in **Phase 5 of 6** - deploying PostgreSQL to production with feature flags and monitoring.

## Objective
Deploy PostgreSQL to production safely with DB_TYPE feature flag, monitoring, and easy rollback capability.

## Background Information
- **Phase 4 Status:** ✅ Complete - All tests passing, production ready
- **Deployment Strategy:** Feature flag (DB_TYPE) for easy rollback
- **Monitoring:** Track errors, performance, connection pool health
- **Risk Level:** High (production deployment)
- **Estimated Time:** 2 hours

## Step-by-Step Instructions

### Step 1: Update .env for Production

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

# Backup current .env
cp .env .env.backup

# Update .env for PostgreSQL
cat >> .env << 'EOF'

# PostgreSQL Migration - Production
DB_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tac_webbuilder
POSTGRES_USER=tac_user
POSTGRES_PASSWORD=CHANGE_THIS_TO_SECURE_PASSWORD
POSTGRES_POOL_MIN=2
POSTGRES_POOL_MAX=20
POSTGRES_TIMEOUT=30
EOF
```

**Important:** Use a secure password for production!

### Step 2: Create Deployment Checklist

Create `migration/DEPLOYMENT_CHECKLIST.md`:

```markdown
# PostgreSQL Deployment Checklist

## Pre-Deployment
- [ ] All tests passing (Phase 4)
- [ ] SQLite databases backed up
- [ ] PostgreSQL data migrated
- [ ] Data integrity validated
- [ ] .env updated with secure credentials
- [ ] Docker Compose configured
- [ ] Monitoring ready

## Deployment Steps
- [ ] Stop application
- [ ] Start PostgreSQL
- [ ] Set DB_TYPE=postgresql
- [ ] Start application
- [ ] Verify health checks
- [ ] Monitor logs for 15 minutes
- [ ] Test critical workflows
- [ ] Verify real-time features

## Post-Deployment
- [ ] Monitor for 24 hours
- [ ] Check error rates
- [ ] Verify performance metrics
- [ ] User acceptance testing

## Rollback Plan (if needed)
- [ ] Stop application
- [ ] Set DB_TYPE=sqlite
- [ ] Start application
- [ ] Verify functionality
- [ ] Investigate issues
```

### Step 3: Deploy PostgreSQL

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

# Stop current application
./scripts/webbuilder stop

# Start PostgreSQL (if not already running)
docker-compose up -d postgres

# Wait for healthy
docker-compose ps | grep postgres
# Should show "healthy"

# Set environment
export DB_TYPE=postgresql
export POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD

# Start application
./scripts/webbuilder start
```

### Step 4: Health Check Verification

```bash
# Check system health
curl http://localhost:8000/api/v1/system-status | jq

# Should show:
# - overall_status: "healthy"
# - database: "PostgreSQL"
# - All services healthy
```

### Step 5: Monitor Application Logs

```bash
# Terminal 1: Backend logs
tail -f app/server/logs/app.log

# Terminal 2: PostgreSQL logs
docker-compose logs -f postgres

# Watch for:
# ✅ No connection errors
# ✅ No query errors
# ✅ Reasonable query times
# ⚠️ Any ERROR messages
```

### Step 6: Test Critical Workflows

```bash
# Test 1: Create a workflow
curl -X POST http://localhost:8000/api/v1/submit \
  -H "Content-Type: application/json" \
  -d '{"nl_input": "Test workflow", "auto_post": false}'

# Test 2: Get workflow history
curl http://localhost:8000/api/v1/workflows | jq

# Test 3: Get queue
curl http://localhost:8000/api/v1/queue | jq

# All should work without errors
```

### Step 7: Verify UI Functionality

Open browser to http://localhost:5173

**Test Checklist:**
1. [ ] Home page loads
2. [ ] Create new request works
3. [ ] Workflow history loads
4. [ ] Queue displays correctly
5. [ ] System status shows PostgreSQL
6. [ ] Real-time updates work
7. [ ] No console errors

### Step 8: Monitor Connection Pool

```bash
# Check PostgreSQL connections
docker-compose exec postgres psql -U tac_user -d tac_webbuilder -c "
  SELECT count(*) as active_connections
  FROM pg_stat_activity
  WHERE datname = 'tac_webbuilder';
"

# Should show 2-10 connections (within pool limits)
```

### Step 9: Set Up Monitoring Alerts

Create `migration/monitor_postgres.sh`:

```bash
#!/bin/bash
# PostgreSQL Monitoring Script

DB_TYPE=postgresql
POSTGRES_PASSWORD=YOUR_PASSWORD

# Check connection pool
echo "=== Connection Pool Status ==="
docker-compose exec postgres psql -U tac_user -d tac_webbuilder -c "
  SELECT
    count(*) FILTER (WHERE state = 'active') as active,
    count(*) FILTER (WHERE state = 'idle') as idle,
    count(*) as total
  FROM pg_stat_activity
  WHERE datname = 'tac_webbuilder';
"

# Check slow queries
echo ""
echo "=== Slow Queries (>1s) ==="
docker-compose exec postgres psql -U tac_user -d tac_webbuilder -c "
  SELECT
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query
  FROM pg_stat_activity
  WHERE state = 'active'
    AND now() - pg_stat_activity.query_start > interval '1 second'
  ORDER BY duration DESC;
"

# Check database size
echo ""
echo "=== Database Size ==="
docker-compose exec postgres psql -U tac_user -d tac_webbuilder -c "
  SELECT pg_size_pretty(pg_database_size('tac_webbuilder'));
"

# Check table sizes
echo ""
echo "=== Largest Tables ==="
docker-compose exec postgres psql -U tac_user -d tac_webbuilder -c "
  SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
  FROM pg_tables
  WHERE schemaname = 'public'
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
  LIMIT 5;
"
```

Make executable and run:

```bash
chmod +x migration/monitor_postgres.sh
./migration/monitor_postgres.sh
```

### Step 10: Document Deployment

Create `migration/DEPLOYMENT_REPORT.md`:

```markdown
# PostgreSQL Deployment Report

## Deployment Date: [YYYY-MM-DD HH:MM]

### Pre-Deployment Status
- SQLite databases backed up: ✅
- All tests passing: ✅
- Data migrated: ✅ (XXXX rows)
- Feature flag ready: ✅

### Deployment Process
- Start time: [HH:MM]
- PostgreSQL started: ✅
- Application restarted: ✅
- Health checks passing: ✅
- Completion time: [HH:MM]
- Total downtime: XX minutes

### Post-Deployment Verification
- Health status: ✅ Healthy
- Connection pool: X/20 connections
- Database size: XXX MB
- Query performance: Normal
- UI functionality: ✅ All features working
- Real-time updates: ✅ Working

### Monitoring (First 24 Hours)
- Error rate: 0% ✅
- Average query time: XXms
- Peak connections: XX
- No incidents: ✅

### Issues Encountered
- None ✅

### Rollback Readiness
- Feature flag: DB_TYPE=sqlite (ready)
- SQLite backups: Available
- Rollback tested: ✅

## Status: SUCCESS ✅

PostgreSQL is live and stable.
```

### Step 11: 24-Hour Monitoring

Run monitoring for 24 hours:

```bash
# Run monitoring every hour
while true; do
  echo "=== Monitoring at $(date) ==="
  ./migration/monitor_postgres.sh

  # Check error logs
  echo "=== Recent Errors ==="
  tail -100 app/server/logs/app.log | grep ERROR

  sleep 3600  # 1 hour
done
```

### Step 12: Commit Deployment

After 24 hours of stable operation:

```bash
git add migration/ .env.sample
git commit -m "$(cat <<'EOF'
deploy: PostgreSQL production deployment complete (Phase 5)

Successfully deployed PostgreSQL to production.

Phase 5 Complete (2 hours):
✅ PostgreSQL deployed to production
✅ Feature flag enabled (DB_TYPE=postgresql)
✅ All health checks passing
✅ Connection pooling working (2-20 connections)
✅ UI fully functional
✅ 24-hour monitoring: No issues

Deployment Details:
- Database: PostgreSQL 15
- Connection pool: 2-20 connections
- Data migrated: XXXX rows
- Downtime: XX minutes
- Rollback plan: Tested and ready

Monitoring Results (24 hours):
- Uptime: 100%
- Error rate: 0%
- Avg query time: XXms
- Peak connections: XX
- Database size: XXX MB

Performance:
- Similar or better than SQLite
- No connection issues
- No query timeouts
- Real-time features working

Rollback Capability:
- Feature flag: DB_TYPE (ready)
- SQLite backups: Preserved
- Rollback tested: ✅

Files Created:
+ migration/DEPLOYMENT_CHECKLIST.md
+ migration/DEPLOYMENT_REPORT.md
+ migration/monitor_postgres.sh

Status: PRODUCTION STABLE ✅

Next: Phase 6 - Post-Migration Optimization (1 hour)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Success Criteria

- ✅ PostgreSQL deployed to production
- ✅ DB_TYPE feature flag working
- ✅ All health checks passing
- ✅ Connection pool healthy
- ✅ UI fully functional
- ✅ 24-hour monitoring complete (no issues)
- ✅ Rollback plan tested
- ✅ Deployment documented
- ✅ Changes committed

## Troubleshooting

**If application won't start:**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check credentials
echo $POSTGRES_PASSWORD

# Check connection
docker-compose exec postgres psql -U tac_user -d tac_webbuilder -c "SELECT 1;"
```

**If connection pool exhausted:**
```bash
# Increase pool size in .env
POSTGRES_POOL_MAX=30

# Restart application
./scripts/webbuilder restart
```

**If need to rollback:**
```bash
# Stop application
./scripts/webbuilder stop

# Switch to SQLite
export DB_TYPE=sqlite
unset POSTGRES_PASSWORD

# Start application
./scripts/webbuilder start
```

## Next Steps

After completing Phase 5, report:
- "Phase 5 complete - PostgreSQL in production ✅"
- 24-hour stability confirmed
- No rollback needed

**Next Task:** Phase 6 - Post-Migration Optimization (1 hour)

---

**Ready to copy into a new chat!** 🚀
