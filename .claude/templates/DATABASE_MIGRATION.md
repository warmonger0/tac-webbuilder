# Template: Database Migration

## File Location
`app/server/db/migrations/XXX_<migration_name>.sql`

## Standard Structure

```sql
-- Migration XXX: <Migration Title>
-- Created: YYYY-MM-DD
-- Purpose: <One-line description>

-- Main table
CREATE TABLE IF NOT EXISTS <table_name> (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- Add columns here
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_<table>_<column> ON <table_name>(<column>);

-- Update timestamp trigger
CREATE TRIGGER IF NOT EXISTS update_<table>_timestamp
AFTER UPDATE ON <table_name>
BEGIN
    UPDATE <table_name> SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
```

## PostgreSQL Compatibility

For PostgreSQL, change:
- `INTEGER PRIMARY KEY AUTOINCREMENT` → `SERIAL PRIMARY KEY`
- `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` → `TIMESTAMP DEFAULT NOW()`
- Triggers use `CREATE OR REPLACE FUNCTION` pattern

## Running Migration

```bash
# SQLite
cd app/server
sqlite3 db/workflow_history.db < db/migrations/XXX_<migration_name>.sql

# PostgreSQL
PGPASSWORD=changeme psql -h 127.0.0.1 -U tac_user -d tac_webbuilder \
  -f db/migrations/XXX_<migration_name>.sql
```

## Verify Migration

```bash
# Check table exists
sqlite3 db/workflow_history.db "SELECT name FROM sqlite_master WHERE type='table' AND name='<table_name>'"

# Check schema
sqlite3 db/workflow_history.db ".schema <table_name>"
```

## Testing Migration

```bash
# Test insert
sqlite3 db/workflow_history.db "INSERT INTO <table_name> (column1) VALUES ('test')"

# Test select
sqlite3 db/workflow_history.db "SELECT * FROM <table_name> LIMIT 1"

# Test trigger (updated_at should change)
sqlite3 db/workflow_history.db "UPDATE <table_name> SET column1='updated' WHERE id=1"
sqlite3 db/workflow_history.db "SELECT updated_at FROM <table_name> WHERE id=1"
```

## Rollback (if needed)

```bash
# Drop table
sqlite3 db/workflow_history.db "DROP TABLE IF EXISTS <table_name>"
```
