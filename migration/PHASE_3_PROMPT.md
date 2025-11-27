# Task: PostgreSQL Migration - Phase 3: Data Migration & Validation

## Context
I'm working on the tac-webbuilder project. We're migrating from SQLite to PostgreSQL. Phase 2 is complete (all code updated). Now in **Phase 3 of 6** - migrating actual data from SQLite to PostgreSQL.

## Objective
Create migration script to copy all data from SQLite databases to PostgreSQL, validate data integrity, and ensure nothing is lost.

## Background Information
- **Phase 2 Status:** ✅ Complete - Code supports both databases
- **Data to Migrate:**
  - `db/database.db` (444KB) - 26 tables
  - `db/workflow_history.db` (50MB) - same schema, different data
- **Estimated Rows:** ~500-1000 workflows, ~10,000 tool calls
- **Risk Level:** Critical (data migration - backup first!)
- **Estimated Time:** 2 hours

## Step-by-Step Instructions

### Step 1: Backup SQLite Databases

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Create backup directory
mkdir -p db/backups

# Backup with timestamp
timestamp=$(date +%Y%m%d_%H%M%S)
cp db/database.db db/backups/database_${timestamp}.db
cp db/workflow_history.db db/backups/workflow_history_${timestamp}.db

# Verify backups
ls -lh db/backups/
```

**Expected:** Two backup files with current timestamp

### Step 2: Ensure PostgreSQL is Running

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

# Start PostgreSQL
docker-compose up -d postgres

# Verify it's healthy
docker-compose ps | grep postgres

# Test connection
docker-compose exec postgres psql -U tac_user -d tac_webbuilder -c "SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public';"
```

**Expected:** Should show 26 tables

### Step 3: Create Migration Script

Create `migration/migrate_to_postgres.py`:

```python
"""
SQLite to PostgreSQL Data Migration Script

Migrates all data from SQLite databases to PostgreSQL.
"""

import sqlite3
import sys
import os
from pathlib import Path

# Add server to path
sys.path.insert(0, str(Path(__file__).parent.parent / "app" / "server"))

from database import get_database_adapter, SQLiteAdapter, PostgreSQLAdapter

# Table migration order (respects foreign keys)
MIGRATION_ORDER = [
    # Core tables first
    "workflow_history",
    "adw_locks",
    "queue_config",
    "phase_queue",

    # Dependent tables
    "tool_calls",
    "operation_patterns",
    "pattern_occurrences",
    "hook_events",
    "adw_tools",
    "cost_savings_log",
    "schema_migrations",
    "workflow_history_archive",

    # Test/demo tables
    "employees", "users", "products", "staff", "empty",
    "large", "special", "people", "file1", "file2",
    "file3", "file4", "file0", "wide", "data",
]

BATCH_SIZE = 1000  # Rows per transaction


def get_table_columns(adapter, table_name):
    """Get column names for a table"""
    with adapter.get_connection() as conn:
        cursor = conn.cursor()

        if adapter.get_db_type() == "sqlite":
            cursor.execute(f"PRAGMA table_info({table_name})")
            return [row[1] for row in cursor.fetchall()]
        else:  # PostgreSQL
            cursor.execute(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """)
            return [row[0] for row in cursor.fetchall()]


def migrate_table(source_adapter, dest_adapter, table_name):
    """Migrate a single table"""
    print(f"\n📋 Migrating table: {table_name}")

    # Get columns
    columns = get_table_columns(source_adapter, table_name)
    if not columns:
        print(f"  ⚠️  Table {table_name} has no columns or doesn't exist, skipping")
        return 0

    # Get row count
    with source_adapter.get_connection() as source_conn:
        cursor = source_conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_rows = cursor.fetchone()[0]

    if total_rows == 0:
        print(f"  ℹ️  Table {table_name} is empty, skipping")
        return 0

    print(f"  📊 Total rows: {total_rows}")

    # Prepare INSERT statement
    from utils.query_helpers import build_placeholders
    placeholders = build_placeholders(len(columns))
    column_list = ", ".join(columns)
    insert_sql = f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})"

    # Migrate in batches
    migrated = 0
    with source_adapter.get_connection() as source_conn:
        source_cursor = source_conn.cursor()
        source_cursor.execute(f"SELECT * FROM {table_name}")

        with dest_adapter.get_connection() as dest_conn:
            dest_cursor = dest_conn.cursor()

            batch = []
            for row in source_cursor:
                # Convert Row to tuple
                row_data = tuple(row[col] for col in columns)
                batch.append(row_data)

                if len(batch) >= BATCH_SIZE:
                    # Insert batch
                    for row_data in batch:
                        dest_cursor.execute(insert_sql, row_data)
                    migrated += len(batch)
                    print(f"  ✅ Migrated {migrated}/{total_rows} rows")
                    batch = []

            # Insert remaining rows
            if batch:
                for row_data in batch:
                    dest_cursor.execute(insert_sql, row_data)
                migrated += len(batch)

    print(f"  ✅ Completed: {migrated} rows migrated")
    return migrated


def main():
    """Main migration function"""
    print("=" * 60)
    print("SQLite → PostgreSQL Migration")
    print("=" * 60)

    # Initialize adapters
    sqlite_db = SQLiteAdapter(db_path="../app/server/db/database.db")
    sqlite_wh = SQLiteAdapter(db_path="../app/server/db/workflow_history.db")

    os.environ["DB_TYPE"] = "postgresql"
    postgres = get_database_adapter()

    # Test connections
    print("\n🔌 Testing connections...")
    if not sqlite_db.health_check():
        print("❌ SQLite database.db connection failed")
        return 1
    print("✅ SQLite database.db connected")

    if not sqlite_wh.health_check():
        print("❌ SQLite workflow_history.db connection failed")
        return 1
    print("✅ SQLite workflow_history.db connected")

    if not postgres.health_check():
        print("❌ PostgreSQL connection failed")
        return 1
    print("✅ PostgreSQL connected")

    # Migrate tables
    total_migrated = 0
    for table in MIGRATION_ORDER:
        try:
            # Try database.db first
            rows = migrate_table(sqlite_db, postgres, table)
            if rows == 0:
                # Try workflow_history.db
                rows = migrate_table(sqlite_wh, postgres, table)
            total_migrated += rows
        except Exception as e:
            print(f"❌ Error migrating {table}: {e}")
            import traceback
            traceback.print_exc()
            return 1

    print("\n" + "=" * 60)
    print(f"✅ Migration Complete!")
    print(f"📊 Total rows migrated: {total_migrated}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### Step 4: Create Validation Script

Create `migration/validate_migration.py`:

```python
"""
Migration Validation Script

Validates that data was migrated correctly from SQLite to PostgreSQL.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "app" / "server"))

from database import SQLiteAdapter, PostgreSQLAdapter


TABLES_TO_CHECK = [
    "workflow_history",
    "phase_queue",
    "tool_calls",
    "adw_locks",
]


def validate_table(sqlite_adapter, postgres_adapter, table_name):
    """Validate row counts match"""
    print(f"\n🔍 Validating: {table_name}")

    # Count SQLite rows
    with sqlite_adapter.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        sqlite_count = cursor.fetchone()[0]

    # Count PostgreSQL rows
    with postgres_adapter.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        postgres_count = cursor.fetchone()[0]

    print(f"  SQLite: {sqlite_count} rows")
    print(f"  PostgreSQL: {postgres_count} rows")

    if sqlite_count == postgres_count:
        print(f"  ✅ Match!")
        return True
    else:
        print(f"  ❌ Mismatch! Difference: {abs(sqlite_count - postgres_count)}")
        return False


def main():
    """Main validation function"""
    print("=" * 60)
    print("Migration Validation")
    print("=" * 60)

    sqlite_db = SQLiteAdapter(db_path="../app/server/db/database.db")
    postgres = PostgreSQLAdapter()

    all_valid = True
    for table in TABLES_TO_CHECK:
        if not validate_table(sqlite_db, postgres, table):
            all_valid = False

    print("\n" + "=" * 60)
    if all_valid:
        print("✅ All validations passed!")
        return 0
    else:
        print("❌ Some validations failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

### Step 5: Run Migration

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/migration

# Set environment
export DB_TYPE=postgresql
export POSTGRES_PASSWORD=changeme  # Match docker-compose

# Run migration
python migrate_to_postgres.py

# Expected: "✅ Migration Complete! Total rows migrated: ~XXXX"
```

### Step 6: Validate Migration

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/migration

# Run validation
python validate_migration.py

# Expected: "✅ All validations passed!"
```

### Step 7: Verify Data Manually

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U tac_user -d tac_webbuilder

# In psql:
-- Check row counts
SELECT 'workflow_history', COUNT(*) FROM workflow_history
UNION ALL
SELECT 'phase_queue', COUNT(*) FROM phase_queue
UNION ALL
SELECT 'tool_calls', COUNT(*) FROM tool_calls;

-- Check recent data
SELECT adw_id, status, created_at
FROM workflow_history
ORDER BY created_at DESC
LIMIT 5;

-- Exit
\q
```

### Step 8: Run Application Tests with PostgreSQL

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Set to use PostgreSQL
export DB_TYPE=postgresql
export POSTGRES_PASSWORD=changeme

# Run tests
pytest tests/ -v

# Expected: All tests should pass
```

### Step 9: Test Application Manually

```bash
# Stop current application
./scripts/webbuilder stop

# Start with PostgreSQL
export DB_TYPE=postgresql
./scripts/webbuilder start

# Access UI at http://localhost:5173
# Verify:
# - Workflow history loads
# - Queue shows phases
# - System status displays
```

### Step 10: Commit Migration Scripts

```bash
git add migration/
git commit -m "$(cat <<'EOF'
feat: PostgreSQL data migration complete (Phase 3)

Created migration scripts to copy SQLite data to PostgreSQL.

Phase 3 Complete (2 hours):
✅ All data migrated successfully
✅ Validation confirms data integrity
✅ Application tests pass with PostgreSQL
✅ Manual verification complete

Migration Details:
- Source: SQLite (database.db + workflow_history.db)
- Target: PostgreSQL (unified database)
- Tables migrated: 26
- Total rows: ~XXXX (varies by installation)
- Batch size: 1000 rows per transaction

Scripts Created:
+ migration/migrate_to_postgres.py (data migration)
+ migration/validate_migration.py (validation)

Validation Results:
✅ workflow_history: XXXX rows
✅ phase_queue: XXXX rows
✅ tool_calls: XXXX rows
✅ All other tables verified

Next: Phase 4 - Testing (4 hours)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Success Criteria

- ✅ SQLite databases backed up
- ✅ PostgreSQL running and healthy
- ✅ Migration script created
- ✅ All data migrated successfully
- ✅ Validation script confirms row counts match
- ✅ Application tests pass with PostgreSQL
- ✅ Manual verification confirms data loads
- ✅ Changes committed

## Troubleshooting

**If migration fails with foreign key errors:**
```python
# Disable foreign key checks temporarily (PostgreSQL)
# Add to migration script:
cursor.execute("SET session_replication_role = 'replica';")
# ... migrate ...
cursor.execute("SET session_replication_role = 'origin';")
```

**If row counts don't match:**
```bash
# Check for duplicates in workflow_history.db
sqlite3 db/workflow_history.db "SELECT adw_id, COUNT(*) FROM workflow_history GROUP BY adw_id HAVING COUNT(*) > 1"
```

**If JSONB conversion fails:**
```python
# Validate JSON before insert
import json
json_data = json.dumps(data) if data else None
```

## Next Steps

After completing Phase 3, report:
- "Phase 3 complete - Data migration successful ✅"
- Total rows migrated
- Validation results

**Next Task:** Phase 4 - Testing (4 hours)

---

**Ready to copy into a new chat!** 🚀
