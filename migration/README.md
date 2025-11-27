# PostgreSQL Migration

This directory contains all files needed to migrate TAC WebBuilder from SQLite to PostgreSQL.

## 📁 Directory Contents

### Schema Files
- **`sqlite_schema_database.sql`** - Extracted schema from `database.db` (SQLite)
- **`sqlite_schema_workflow_history.sql`** - Extracted schema from `workflow_history.db` (SQLite)
- **`postgres_schema.sql`** - Translated PostgreSQL schema (ready to deploy)

### Migration Scripts
- **`migrate_to_postgres.py`** - Main data migration script (Phase 3)
- **`validate_migration.py`** - Validation script to verify data integrity (Phase 3)

## 🚀 Quick Start

### 1. Start PostgreSQL (Docker)

```bash
# Start PostgreSQL database
docker-compose up -d postgres

# Wait for PostgreSQL to be ready (check health)
docker-compose ps

# Optional: Start pgAdmin for database management
docker-compose --profile admin up -d pgadmin
```

### 2. Configure Environment

```bash
# Copy .env.sample to .env if not already done
cp .env.sample .env

# Edit .env and set:
DB_TYPE=postgresql
POSTGRES_PASSWORD=your_secure_password_here
```

### 3. Run Migration

```bash
# From project root
cd migration
python migrate_to_postgres.py

# Validate migration
python validate_migration.py
```

### 4. Switch Application

```bash
# In .env file, change:
DB_TYPE=postgresql

# Restart application
./scripts/webbuilder restart
```

## 📊 Migration Details

### What Gets Migrated

- **26 tables** from 2 SQLite databases
- **~50MB** of workflow history data
- **All indexes** (41 total)
- **All triggers** (4 total)
- **All views** (4 total)

### Key Conversions

| SQLite | PostgreSQL |
|--------|------------|
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `BIGSERIAL PRIMARY KEY` |
| `TEXT` (dates) | `TIMESTAMP WITHOUT TIME ZONE` |
| `TEXT` (JSON) | `JSONB` |
| `INTEGER` (boolean) | `BOOLEAN` |
| `REAL` (money) | `NUMERIC(10,4)` |
| `REAL` (float) | `DOUBLE PRECISION` |
| `datetime('now')` | `NOW()` |
| `?` placeholders | `%s` placeholders |

### Schema Highlights

- **JSONB columns** for better JSON query performance
- **Proper foreign keys** with CASCADE options
- **Auto-vacuum tuning** for large tables
- **Table comments** for documentation
- **Connection pooling** via psycopg2

## 🔄 Rollback Plan

If migration fails or issues arise:

```bash
# 1. Stop application
./scripts/webbuilder stop

# 2. Switch back to SQLite in .env
DB_TYPE=sqlite

# 3. Restart application
./scripts/webbuilder start

# Your SQLite data is unchanged!
```

## 🧪 Testing

### Dual-Database Testing

Before full migration, test with both databases:

```bash
# Test SQLite (existing)
DB_TYPE=sqlite pytest app/server/tests/

# Test PostgreSQL (new)
DB_TYPE=postgresql pytest app/server/tests/
```

### Performance Comparison

```bash
# Run benchmarks
python scripts/benchmark_database.py
```

## 📝 Migration Checklist

Phase 1: Preparation
- [x] Extract SQLite schemas
- [x] Translate to PostgreSQL DDL
- [x] Create docker-compose.yml
- [x] Update .env.sample with PostgreSQL variables
- [x] Install psycopg2-binary
- [ ] Create database abstraction layer
- [ ] Test PostgreSQL connection

Phase 2: Code Changes
- [ ] Implement PostgreSQL adapter
- [ ] Update query placeholders (? → %s)
- [ ] Convert datetime functions
- [ ] Update all 79 get_connection() calls

Phase 3: Data Migration
- [ ] Create migration script
- [ ] Run migration (SQLite → PostgreSQL)
- [ ] Validate data integrity
- [ ] Test all queries work

Phase 4: Testing
- [ ] Run full test suite with PostgreSQL
- [ ] Performance testing
- [ ] Load testing
- [ ] Integration testing

Phase 5: Deployment
- [ ] Deploy with DB_TYPE=postgresql
- [ ] Monitor for errors
- [ ] Verify all features work

Phase 6: Post-Migration
- [ ] Optimize queries
- [ ] Tune PostgreSQL settings
- [ ] Update documentation
- [ ] Archive SQLite databases

## 🛠 Troubleshooting

### Connection Issues

```bash
# Test PostgreSQL connection
docker-compose exec postgres psql -U tac_user -d tac_webbuilder -c "SELECT version();"
```

### Migration Failures

```bash
# Check logs
docker-compose logs postgres

# Check migration script output
cat migration/migration.log
```

### Performance Issues

```bash
# Check query plans
docker-compose exec postgres psql -U tac_user -d tac_webbuilder

# In psql:
EXPLAIN ANALYZE SELECT * FROM workflow_history LIMIT 10;
```

## 📚 Resources

- [PostgreSQL 15 Documentation](https://www.postgresql.org/docs/15/)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)
- [Migration Plan](../docs/postgresql_migration_plan.md)

## ⚠️ Important Notes

- **Backup SQLite databases before migration**: `cp -r app/server/db app/server/db.backup`
- **Don't delete SQLite databases** until PostgreSQL is fully validated
- **Monitor disk space**: PostgreSQL may use more space than SQLite initially
- **Test rollback procedure** before production migration

---

**Status:** Phase 1 Complete ✅ | Phase 2 In Progress 🚧
**Last Updated:** 2025-11-26
