# PostgreSQL Migration - Phase Prompts Index

## Overview

This directory contains **8 detailed prompts** for migrating TAC WebBuilder from SQLite to PostgreSQL. Each prompt is a complete, standalone task that can be copied into a new Claude Code chat session.

**Total Time:** 19 hours across 6 phases
**Risk Level:** High (database migration)
**Rollback:** Supported via DB_TYPE feature flag

---

## Migration Prompts (In Order)

### Phase 1: Setup & Preparation
**File:** `PHASE_1_PROMPT.md`
**Time:** 4 hours
**Status:** ⬜ Not Started

**What It Does:**
- Extracts SQLite schemas (26 tables)
- Translates to PostgreSQL DDL (858 lines)
- Creates database abstraction layer
- Sets up Docker Compose
- Installs psycopg2-binary
- Tests both adapters

**Success Criteria:**
- ✅ PostgreSQL schema created
- ✅ Docker running PostgreSQL
- ✅ Abstraction layer working
- ✅ Both adapters tested

**Next:** Phase 2.1

---

### Phase 2.1: Update get_connection() Calls
**File:** `PHASE_2_1_PROMPT.md`
**Time:** 2 hours
**Status:** ⬜ Not Started

**What It Does:**
- Updates 79 `get_connection()` calls
- Migrates to adapter pattern
- Updates repositories, services, routes
- Tests with both databases

**Success Criteria:**
- ✅ All get_connection() calls migrated
- ✅ No direct imports remain
- ✅ All tests passing

**Depends On:** Phase 1 complete
**Next:** Phase 2.2

---

### Phase 2.2: Convert Query Placeholders
**File:** `PHASE_2_2_PROMPT.md`
**Time:** 2 hours
**Status:** ⬜ Not Started

**What It Does:**
- Converts ~160 `?` placeholders
- Creates query helper functions
- Makes queries database-agnostic
- Tests with both databases

**Success Criteria:**
- ✅ All placeholders converted
- ✅ Helper functions created
- ✅ Both databases work

**Depends On:** Phase 2.1 complete
**Next:** Phase 2.3

---

### Phase 2.3: Convert Datetime Functions
**File:** `PHASE_2_3_PROMPT.md`
**Time:** 1 hour
**Status:** ⬜ Not Started

**What It Does:**
- Converts ~40 `datetime('now')` calls
- Adds get_now_function() helper
- Makes datetime logic database-agnostic

**Success Criteria:**
- ✅ All datetime calls converted
- ✅ Helper function created
- ✅ Phase 2 complete!

**Depends On:** Phase 2.2 complete
**Next:** Phase 3

---

### Phase 3: Data Migration & Validation
**File:** `PHASE_3_PROMPT.md`
**Time:** 2 hours
**Status:** ⬜ Not Started
**⚠️ CRITICAL:** Backup SQLite first!

**What It Does:**
- Backs up SQLite databases
- Migrates all data to PostgreSQL
- Validates data integrity
- Tests application with PostgreSQL

**Success Criteria:**
- ✅ SQLite backed up
- ✅ All data migrated
- ✅ Validation passing
- ✅ App works with PostgreSQL

**Depends On:** Phase 2 complete
**Next:** Phase 4

---

### Phase 4: Testing & Verification
**File:** `PHASE_4_PROMPT.md`
**Time:** 4 hours
**Status:** ⬜ Not Started

**What It Does:**
- Runs full test suite
- Performance benchmarking
- Load testing
- Manual QA
- Data integrity checks

**Success Criteria:**
- ✅ All tests pass
- ✅ Performance acceptable
- ✅ Load tests successful
- ✅ Manual QA complete

**Depends On:** Phase 3 complete
**Next:** Phase 5

---

### Phase 5: Deployment
**File:** `PHASE_5_PROMPT.md`
**Time:** 2 hours
**Status:** ⬜ Not Started
**⚠️ PRODUCTION:** Live deployment!

**What It Does:**
- Deploys PostgreSQL to production
- Enables DB_TYPE feature flag
- 24-hour monitoring
- Rollback capability verified

**Success Criteria:**
- ✅ PostgreSQL in production
- ✅ All health checks passing
- ✅ 24h stable
- ✅ Rollback tested

**Depends On:** Phase 4 complete
**Next:** Phase 6

---

### Phase 6: Post-Migration Optimization
**File:** `PHASE_6_PROMPT.md`
**Time:** 1 hour
**Status:** ⬜ Not Started

**What It Does:**
- Optimizes PostgreSQL settings
- Adds missing indexes
- Archives SQLite databases
- Updates documentation
- Creates migration summary

**Success Criteria:**
- ✅ PostgreSQL optimized
- ✅ SQLite archived
- ✅ Docs updated
- ✅ Migration complete! 🎉

**Depends On:** Phase 5 complete
**Next:** Celebration! 🍾

---

## Quick Start

### 1. Choose Your Phase

Start with Phase 1 and work through sequentially:

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/migration

# Read Phase 1 prompt
cat PHASE_1_PROMPT.md
```

### 2. Copy Prompt to New Chat

Open a **new Claude Code chat** and copy the entire contents of `PHASE_X_PROMPT.md`

### 3. Execute the Phase

Follow the step-by-step instructions in the prompt.

### 4. Verify Success

Check the "Success Criteria" section at the end of each prompt.

### 5. Move to Next Phase

Once a phase is complete, proceed to the next prompt file.

---

## Progress Tracking

Update this table as you complete each phase:

| Phase | File | Time | Status | Completed |
|-------|------|------|--------|-----------|
| 1 | PHASE_1_PROMPT.md | 4h | ⬜ Not Started | YYYY-MM-DD |
| 2.1 | PHASE_2_1_PROMPT.md | 2h | ⬜ Not Started | YYYY-MM-DD |
| 2.2 | PHASE_2_2_PROMPT.md | 2h | ⬜ Not Started | YYYY-MM-DD |
| 2.3 | PHASE_2_3_PROMPT.md | 1h | ⬜ Not Started | YYYY-MM-DD |
| 3 | PHASE_3_PROMPT.md | 2h | ⬜ Not Started | YYYY-MM-DD |
| 4 | PHASE_4_PROMPT.md | 4h | ⬜ Not Started | YYYY-MM-DD |
| 5 | PHASE_5_PROMPT.md | 2h | ⬜ Not Started | YYYY-MM-DD |
| 6 | PHASE_6_PROMPT.md | 1h | ⬜ Not Started | YYYY-MM-DD |

**Total:** 18 hours (19 with final docs)

---

## Important Notes

### ⚠️ Before Starting

1. **Backup everything:** `cp -r app/server/db app/server/db.backup`
2. **Read Phase 1 fully** before starting
3. **Use separate chats** for each phase (fresh context)
4. **Don't skip phases** - each builds on the previous

### 🔄 Rollback Plan

If anything goes wrong:

```bash
# Stop application
./scripts/webbuilder stop

# Switch to SQLite
export DB_TYPE=sqlite

# Restore from backup (if needed)
cp -r app/server/db.backup/* app/server/db/

# Restart
./scripts/webbuilder start
```

### 📋 Checklist Before Each Phase

- [ ] Previous phase complete
- [ ] All tests passing
- [ ] Git committed
- [ ] Backup current state
- [ ] Read next prompt fully
- [ ] Open new Claude Code chat

---

## Files in This Directory

### Prompt Files (8 total)
- `PHASE_1_PROMPT.md` - Setup & Preparation
- `PHASE_2_1_PROMPT.md` - Update get_connection calls
- `PHASE_2_2_PROMPT.md` - Convert placeholders
- `PHASE_2_3_PROMPT.md` - Convert datetime functions
- `PHASE_3_PROMPT.md` - Data Migration
- `PHASE_4_PROMPT.md` - Testing
- `PHASE_5_PROMPT.md` - Deployment
- `PHASE_6_PROMPT.md` - Post-Migration

### Generated Files (created during migration)
- `sqlite_schema_database.sql` - Phase 1
- `sqlite_schema_workflow_history.sql` - Phase 1
- `postgres_schema.sql` - Phase 1 (858 lines)
- `migrate_to_postgres.py` - Phase 3
- `validate_migration.py` - Phase 3
- `benchmark_databases.py` - Phase 4
- `test_adapters.py` - Phase 1
- `monitor_postgres.sh` - Phase 5
- `postgres_maintenance.sh` - Phase 6

### Documentation Files
- `README.md` - Migration overview
- `PROMPTS_INDEX.md` - This file
- `MIGRATION_COMPLETE.md` - Created in Phase 6
- `TEST_RESULTS.md` - Created in Phase 4
- `DEPLOYMENT_REPORT.md` - Created in Phase 5

---

## Support

### If You Get Stuck

1. **Check the prompt's Troubleshooting section** - common issues covered
2. **Review previous phase** - might have missed something
3. **Check git commits** - see what changed
4. **Rollback if needed** - DB_TYPE=sqlite
5. **Ask for help** - describe what you tried

### Common Issues

**"Tests failing after Phase 2.1"**
→ Check adapter initialization

**"Migration fails in Phase 3"**
→ Verify PostgreSQL is running: `docker-compose ps`

**"Performance slow in Phase 4"**
→ Run VACUUM ANALYZE, check indexes

**"Can't connect to PostgreSQL in Phase 5"**
→ Check POSTGRES_PASSWORD in .env

---

## Success Metrics

When all phases are complete:

- ✅ Zero data loss
- ✅ All tests passing (100%)
- ✅ Performance same or better
- ✅ Production stable (24h+)
- ✅ Rollback capability confirmed
- ✅ Documentation complete

---

**Ready to start?** Open `PHASE_1_PROMPT.md` and let's migrate to PostgreSQL! 🚀
