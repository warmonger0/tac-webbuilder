# Task: PostgreSQL Migration - Phase 6: Post-Migration Optimization

## Context
I'm working on the tac-webbuilder project. Phase 5 is complete (PostgreSQL in production, stable for 24+ hours). Now in **Phase 6 of 6** - optimizing PostgreSQL, cleaning up, and documenting the completed migration.

## Objective
Optimize PostgreSQL performance, archive SQLite databases, update documentation, and celebrate successful migration!

## Background Information
- **Phase 5 Status:** ✅ Complete - PostgreSQL stable in production
- **Current State:** Running on PostgreSQL, SQLite still on disk
- **Focus:** Performance tuning, cleanup, documentation
- **Risk Level:** Low (production already stable)
- **Estimated Time:** 1 hour

## Step-by-Step Instructions

### Step 1: Analyze Query Performance

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U tac_user -d tac_webbuilder

# Enable query logging for analysis
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s
SELECT pg_reload_conf();

# Check slow queries (run after some usage)
SELECT
  calls,
  mean_exec_time,
  query
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Step 2: Add Missing Indexes (if needed)

Based on query analysis, add indexes for frequently queried columns:

```sql
-- Example: If workflow_history queries by workflow_type are slow
CREATE INDEX CONCURRENTLY idx_workflow_type_status
ON workflow_history(workflow_type, status)
WHERE status IN ('pending', 'running');

-- Example: If tool_calls queries by called_at are slow
CREATE INDEX CONCURRENTLY idx_tool_calls_recent
ON tool_calls(called_at DESC)
WHERE called_at > NOW() - INTERVAL '30 days';

-- Verify indexes
\di
```

### Step 3: Optimize PostgreSQL Settings

Update PostgreSQL configuration for production workload:

```bash
# Edit PostgreSQL config
docker-compose exec postgres bash -c "cat >> /var/lib/postgresql/data/postgresql.conf << 'EOF'

# TAC WebBuilder Production Optimizations

# Memory
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Checkpoints
checkpoint_completion_target = 0.9
wal_buffers = 16MB

# Query Planner
random_page_cost = 1.1  # For SSD
effective_io_concurrency = 200

# Connections
max_connections = 100

# Logging
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_checkpoints = on
log_autovacuum_min_duration = 0

EOF"

# Restart PostgreSQL to apply
docker-compose restart postgres
```

### Step 4: Set Up Automated Maintenance

Create `migration/postgres_maintenance.sh`:

```bash
#!/bin/bash
# PostgreSQL Automated Maintenance Script

echo "=== PostgreSQL Maintenance: $(date) ==="

# Vacuum and analyze all tables
docker-compose exec postgres psql -U tac_user -d tac_webbuilder -c "
  VACUUM ANALYZE;
"

# Reindex if fragmentation detected
docker-compose exec postgres psql -U tac_user -d tac_webbuilder -c "
  REINDEX DATABASE tac_webbuilder;
"

# Clean up old data (optional - adjust retention as needed)
docker-compose exec postgres psql -U tac_user -d tac_webbuilder -c "
  -- Archive workflows older than 6 months
  INSERT INTO workflow_history_archive
  SELECT *, CURRENT_TIMESTAMP, 'auto_archive'
  FROM workflow_history
  WHERE created_at < NOW() - INTERVAL '6 months';

  DELETE FROM workflow_history
  WHERE created_at < NOW() - INTERVAL '6 months';
"

echo "✅ Maintenance complete"
```

Add to crontab:

```bash
# Run weekly
crontab -e
# Add: 0 2 * * 0 /path/to/tac-webbuilder/migration/postgres_maintenance.sh
```

### Step 5: Archive SQLite Databases

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Create archive directory
mkdir -p db/archived_sqlite

# Move SQLite databases to archive
mv db/database.db db/archived_sqlite/database_$(date +%Y%m%d).db
mv db/workflow_history.db db/archived_sqlite/workflow_history_$(date +%Y%m%d).db

# Compress archives
tar -czf db/archived_sqlite/sqlite_databases_$(date +%Y%m%d).tar.gz \
  db/archived_sqlite/*.db

# Remove uncompressed files
rm db/archived_sqlite/*.db

echo "✅ SQLite databases archived"
```

### Step 6: Update Documentation

Update `README.md`:

```markdown
# TAC WebBuilder

...

## Database

**Current:** PostgreSQL 15

TAC WebBuilder uses PostgreSQL for production. Previously used SQLite (migrated Nov 2025).

### Database Connection

Configure in `.env`:
```bash
DB_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tac_webbuilder
POSTGRES_USER=tac_user
POSTGRES_PASSWORD=your_secure_password
```

### Database Management

```bash
# Connect to database
docker-compose exec postgres psql -U tac_user -d tac_webbuilder

# Backup database
docker-compose exec postgres pg_dump -U tac_user tac_webbuilder > backup.sql

# Restore database
docker-compose exec -T postgres psql -U tac_user -d tac_webbuilder < backup.sql

# Monitor database
./migration/monitor_postgres.sh
```

### Migration History

PostgreSQL migration completed: 2025-11-26
- Migrated from SQLite (2 databases, 26 tables)
- ~XXXX rows migrated
- Migration documentation: `migration/README.md`
- SQLite backups: `app/server/db/archived_sqlite/`
```

### Step 7: Create Migration Summary

Create `migration/MIGRATION_COMPLETE.md`:

```markdown
# PostgreSQL Migration - Complete Summary

## Migration Overview

**Start Date:** 2025-11-26
**Completion Date:** 2025-11-XX
**Total Time:** 19 hours (across 6 phases)
**Status:** ✅ COMPLETE & STABLE

## Migration Phases

### Phase 1: Setup & Preparation (4 hours)
✅ Extracted SQLite schemas
✅ Translated to PostgreSQL DDL
✅ Created database abstraction layer
✅ Set up Docker Compose

### Phase 2: Code Changes (6 hours)
✅ 2.1: Updated get_connection() calls (79)
✅ 2.2: Converted placeholders (160)
✅ 2.3: Converted datetime functions (40)

### Phase 3: Data Migration (2 hours)
✅ Migrated all data (XXXX rows)
✅ Validated data integrity
✅ Zero data loss

### Phase 4: Testing (4 hours)
✅ Full test suite passing
✅ Integration tests passing
✅ Performance testing: PostgreSQL comparable/better
✅ Load testing: No errors
✅ Manual QA: All features working

### Phase 5: Deployment (2 hours)
✅ Deployed to production
✅ 24-hour monitoring: Stable
✅ Rollback capability tested

### Phase 6: Optimization (1 hour)
✅ Performance tuning
✅ Automated maintenance
✅ SQLite databases archived
✅ Documentation updated

## Technical Details

### Database Statistics
- Tables: 26
- Indexes: 41
- Views: 4
- Triggers: 4
- Total rows migrated: ~XXXX
- Database size: XXX MB

### Performance Improvements
- Connection pooling: 2-20 connections
- Query performance: Similar or better than SQLite
- JSONB columns: Faster JSON queries
- Proper foreign keys: Data integrity enforced
- Concurrent access: No locking issues

### Code Changes
- Files modified: ~30 files
- Lines changed: ~500 lines
- New files: ~15 files
- Tests updated: ~20 files

## Benefits Achieved

✅ **Scalability:** Connection pooling for concurrent users
✅ **Performance:** Better for complex queries
✅ **Data Integrity:** Foreign key constraints enforced
✅ **JSON Queries:** JSONB indexing and querying
✅ **Concurrency:** No more SQLITE_BUSY errors
✅ **Production Ready:** Industry-standard database
✅ **Monitoring:** Built-in PostgreSQL monitoring tools
✅ **Backup/Restore:** Standard pg_dump/pg_restore

## Rollback Plan

If needed, can revert to SQLite:
1. Stop application
2. Set DB_TYPE=sqlite in .env
3. Restore from archived_sqlite/
4. Restart application

SQLite backups preserved in:
- `app/server/db/archived_sqlite/`

## Maintenance

### Daily
- Monitor logs: `docker-compose logs postgres`
- Check health: `./migration/monitor_postgres.sh`

### Weekly
- Run maintenance: `./migration/postgres_maintenance.sh`
- Check slow queries
- Review connection pool usage

### Monthly
- Database backup: `pg_dump`
- Review and archive old data
- Performance review

## Migration Files

### Schema
- `migration/sqlite_schema_*.sql` - Original SQLite schemas
- `migration/postgres_schema.sql` - PostgreSQL schema (858 lines)

### Scripts
- `migration/migrate_to_postgres.py` - Data migration
- `migration/validate_migration.py` - Validation
- `migration/benchmark_databases.py` - Performance testing
- `migration/monitor_postgres.sh` - Monitoring
- `migration/postgres_maintenance.sh` - Maintenance

### Documentation
- `migration/README.md` - Migration guide
- `migration/PHASE_*_PROMPT.md` - Detailed phase instructions
- `migration/TEST_RESULTS.md` - Test results
- `migration/DEPLOYMENT_REPORT.md` - Deployment report
- `migration/MIGRATION_COMPLETE.md` - This file

## Lessons Learned

1. **Database abstraction layer was key** - Made migration smooth
2. **Feature flag (DB_TYPE) enabled safe rollback** - Peace of mind
3. **Thorough testing prevented production issues** - Time well spent
4. **Performance testing validated migration** - Confidence before deploy
5. **24-hour monitoring before declaring success** - Caught edge cases

## Next Steps

- ✅ Migration complete - no further action needed
- Monitor performance over next month
- Consider removing SQLite adapter after 3 months of stability
- Celebrate! 🎉

## Success Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Data loss | 0% | 0% | ✅ |
| Test pass rate | 100% | 100% | ✅ |
| Downtime | <30min | XXmin | ✅ |
| Performance | Similar | Better | ✅ |
| Rollback ready | Yes | Yes | ✅ |
| 24h stability | Yes | Yes | ✅ |

## Conclusion

✅ **MIGRATION SUCCESSFUL**

PostgreSQL migration completed successfully. All data migrated, all tests passing, production stable. TAC WebBuilder is now running on a production-grade database with improved scalability and performance.

**Project Status:** PostgreSQL Production Deployment - STABLE ✅
```

### Step 8: Commit Final Changes

```bash
git add migration/ README.md app/server/db/ docs/
git commit -m "$(cat <<'EOF'
docs: PostgreSQL migration complete (Phase 6)

Migration complete! All optimization and cleanup done.

Phase 6 Complete (1 hour):
✅ PostgreSQL performance optimized
✅ Additional indexes added (if needed)
✅ PostgreSQL settings tuned for production
✅ Automated maintenance configured
✅ SQLite databases archived
✅ Documentation updated
✅ Migration summary created

Optimizations:
- Shared buffers: 256MB
- Connection pooling: Tuned
- Maintenance: Automated (weekly)
- Indexes: Optimized for workload
- Logging: Enhanced for monitoring

Cleanup:
- SQLite databases archived
- Old test data removed (if any)
- Migration scripts organized
- Documentation complete

Final Statistics:
- Total time: 19 hours (across 6 phases)
- Data migrated: XXXX rows
- Zero data loss: ✅
- Downtime: XXmin
- Performance: Better than SQLite

Files:
+ migration/MIGRATION_COMPLETE.md
+ migration/postgres_maintenance.sh
~ README.md (updated for PostgreSQL)
~ docs/ (updated database docs)
~ app/server/db/ (SQLite archived)

MIGRATION COMPLETE! 🎉

PostgreSQL is:
✅ In production
✅ Stable (XX days)
✅ Optimized
✅ Monitored
✅ Documented
✅ Maintained

All 6 phases complete:
✅ Phase 1: Setup (4h)
✅ Phase 2: Code Changes (6h)
✅ Phase 3: Data Migration (2h)
✅ Phase 4: Testing (4h)
✅ Phase 5: Deployment (2h)
✅ Phase 6: Optimization (1h)

Total: 19 hours

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### Step 9: Celebrate! 🎉

```bash
echo "
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🎉 POSTGRESQL MIGRATION COMPLETE! 🎉                  ║
║                                                              ║
║  ✅ All 6 phases complete (19 hours)                        ║
║  ✅ Zero data loss                                          ║
║  ✅ All tests passing                                       ║
║  ✅ Production stable                                       ║
║  ✅ Performance optimized                                   ║
║                                                              ║
║  TAC WebBuilder is now running on PostgreSQL!                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"
```

### Step 10: Future Considerations

After 3 months of stable PostgreSQL operation, consider:

```bash
# Remove SQLite adapter (if desired)
# 1. Remove database/sqlite_adapter.py
# 2. Update factory.py to only return PostgreSQL adapter
# 3. Remove utils/db_connection.py (old SQLite code)
# 4. Update .env.sample to remove DB_TYPE option

# Or keep for backward compatibility/testing
```

## Success Criteria

- ✅ PostgreSQL optimized for production
- ✅ Automated maintenance configured
- ✅ SQLite databases archived
- ✅ Documentation updated
- ✅ Migration summary created
- ✅ All 6 phases complete
- ✅ Production stable
- ✅ Changes committed
- ✅ 🎉 Migration celebrated!

## Troubleshooting

**If performance degrades:**
```sql
-- Check table bloat
SELECT schemaname, tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Vacuum full if needed
VACUUM FULL ANALYZE;
```

**If disk space issues:**
```bash
# Check PostgreSQL data size
docker-compose exec postgres du -sh /var/lib/postgresql/data

# Archive old data
# (Use workflow_history_archive table)
```

## Final Report

**PostgreSQL Migration: COMPLETE** ✅

All phases done, production stable, well-documented.

---

**Congratulations! The PostgreSQL migration is complete!** 🎉🚀
