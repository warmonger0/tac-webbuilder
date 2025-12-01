#!/usr/bin/env python3
"""
SQLite to PostgreSQL Data Migration Script

Migrates data from SQLite databases to PostgreSQL while preserving
relationships and data integrity.

Usage:
    python migrate_to_postgres.py [--dry-run] [--tables TABLE1,TABLE2,...]
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import psycopg2
import psycopg2.extras


# Database paths (relative to project root)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
SQLITE_DB_PATH = PROJECT_ROOT / "app/server/db/database.db"
SQLITE_WORKFLOW_PATH = PROJECT_ROOT / "app/server/db/workflow_history.db"

# PostgreSQL connection params
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
PG_DB = os.getenv("POSTGRES_DB", "tac_webbuilder")
PG_USER = os.getenv("POSTGRES_USER", "tac_user")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "changeme")

# Tables to migrate (in dependency order)
CORE_TABLES = [
    "workflow_history",
    "phase_queue",
    "queue_config",
    "operation_patterns",
    "pattern_occurrences",
    "adw_locks",
    "adw_tools",
    "hook_events",
    "tool_calls",
    "cost_savings_log",
]


class MigrationStats:
    """Track migration statistics."""

    def __init__(self):
        self.tables_migrated = 0
        self.rows_migrated = 0
        self.errors = []
        self.start_time = datetime.now()

    def add_table(self, table_name: str, row_count: int):
        self.tables_migrated += 1
        self.rows_migrated += row_count
        print(f"  ✅ {table_name}: {row_count} rows")

    def add_error(self, error: str):
        self.errors.append(error)
        print(f"  ❌ {error}")

    def summary(self):
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print(f"\n{'='*60}")
        print(f"Migration Summary")
        print(f"{'='*60}")
        print(f"Tables migrated: {self.tables_migrated}")
        print(f"Rows migrated: {self.rows_migrated}")
        print(f"Errors: {len(self.errors)}")
        print(f"Duration: {elapsed:.2f}s")
        if self.errors:
            print(f"\nErrors encountered:")
            for error in self.errors:
                print(f"  - {error}")
        print(f"{'='*60}\n")


def get_sqlite_connection(db_path: Path) -> sqlite3.Connection:
    """Connect to SQLite database."""
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite database not found: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_postgres_connection() -> psycopg2.extensions.connection:
    """Connect to PostgreSQL database."""
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        database=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
        cursor_factory=psycopg2.extras.RealDictCursor
    )


def table_exists_in_sqlite(conn: sqlite3.Connection, table_name: str) -> bool:
    """Check if table exists in SQLite."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def get_row_count(conn: sqlite3.Connection, table_name: str) -> int:
    """Get row count from SQLite table."""
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
    return cursor.fetchone()[0]


def migrate_table(
    sqlite_conn: sqlite3.Connection,
    pg_conn: psycopg2.extensions.connection,
    table_name: str,
    dry_run: bool = False
) -> int:
    """
    Migrate data from SQLite table to PostgreSQL.

    Returns number of rows migrated.
    """
    if not table_exists_in_sqlite(sqlite_conn, table_name):
        print(f"  ⏭️  Skipping {table_name} (not found in SQLite)")
        return 0

    row_count = get_row_count(sqlite_conn, table_name)
    if row_count == 0:
        print(f"  ⏭️  Skipping {table_name} (no data)")
        return 0

    print(f"  📦 Migrating {table_name} ({row_count} rows)...")

    if dry_run:
        print(f"  🔍 DRY RUN: Would migrate {row_count} rows")
        return row_count

    # Read all rows from SQLite
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    columns = [description[0] for description in sqlite_cursor.description]
    rows = sqlite_cursor.fetchall()

    # Insert into PostgreSQL
    pg_cursor = pg_conn.cursor()
    migrated = 0

    for row in rows:
        # Convert SQLite row to dict
        row_dict = {col: row[col] for col in columns}

        # Get PostgreSQL column types to handle conversions
        pg_cursor_types = pg_conn.cursor()
        pg_cursor_types.execute(f"""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
        """)
        pg_col_types = {row['column_name']: row['data_type'] for row in pg_cursor_types.fetchall()}

        # Handle type conversions
        for key, value in row_dict.items():
            if value is None:
                continue

            # Convert booleans (SQLite stores as INTEGER 0/1, PostgreSQL uses BOOLEAN)
            if pg_col_types.get(key) == 'boolean' and isinstance(value, int):
                row_dict[key] = bool(value)

            # Handle JSON fields (SQLite stores as TEXT, PostgreSQL uses JSONB)
            elif isinstance(value, str) and pg_col_types.get(key) in ['json', 'jsonb']:
                try:
                    # Verify it's valid JSON
                    json.loads(value)
                    # Keep as string, PostgreSQL will convert
                except (json.JSONDecodeError, TypeError):
                    # Not valid JSON, store as empty dict or null
                    row_dict[key] = None

            # Also check by field naming convention for JSON
            elif value and isinstance(value, str) and (
                key.endswith('_data') or
                key.endswith('_config') or
                key in ['metadata', 'phase_data', 'patterns', 'filter_criteria']
            ):
                try:
                    # Verify it's valid JSON
                    json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    pass  # Not JSON, keep as is

        # Build INSERT statement
        placeholders = ', '.join(['%s'] * len(columns))
        column_names = ', '.join(columns)
        insert_sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"

        try:
            values = [row_dict[col] for col in columns]
            pg_cursor.execute(insert_sql, values)
            migrated += 1
        except psycopg2.Error as e:
            # On conflict, try update instead (for tables with unique constraints)
            if 'duplicate key' in str(e).lower():
                # Skip duplicates
                pg_conn.rollback()
                continue
            raise

    pg_conn.commit()
    return migrated


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description='Migrate SQLite to PostgreSQL')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be migrated without actually migrating')
    parser.add_argument('--tables', type=str, help='Comma-separated list of tables to migrate (default: all core tables)')
    args = parser.parse_args()

    stats = MigrationStats()

    # Determine which tables to migrate
    tables_to_migrate = CORE_TABLES
    if args.tables:
        tables_to_migrate = [t.strip() for t in args.tables.split(',')]

    print(f"\n{'='*60}")
    print(f"SQLite → PostgreSQL Migration")
    print(f"{'='*60}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE MIGRATION'}")
    print(f"Tables: {', '.join(tables_to_migrate)}")
    print(f"{'='*60}\n")

    try:
        # Connect to databases
        print("📡 Connecting to databases...")
        sqlite_db_conn = get_sqlite_connection(SQLITE_DB_PATH)
        sqlite_wf_conn = get_sqlite_connection(SQLITE_WORKFLOW_PATH)
        pg_conn = get_postgres_connection()
        print("  ✅ Connected to SQLite (database.db)")
        print("  ✅ Connected to SQLite (workflow_history.db)")
        print("  ✅ Connected to PostgreSQL\n")

        # Migrate tables
        print("📦 Migrating tables...\n")

        for table_name in tables_to_migrate:
            try:
                # Try workflow_history database first (it has most tables)
                if table_exists_in_sqlite(sqlite_wf_conn, table_name):
                    migrated = migrate_table(sqlite_wf_conn, pg_conn, table_name, args.dry_run)
                    if migrated > 0:
                        stats.add_table(table_name, migrated)
                # Fall back to main database
                elif table_exists_in_sqlite(sqlite_db_conn, table_name):
                    migrated = migrate_table(sqlite_db_conn, pg_conn, table_name, args.dry_run)
                    if migrated > 0:
                        stats.add_table(table_name, migrated)
                else:
                    print(f"  ⏭️  Skipping {table_name} (not found in any database)")

            except Exception as e:
                error_msg = f"{table_name}: {str(e)}"
                stats.add_error(error_msg)

        # Close connections
        sqlite_db_conn.close()
        sqlite_wf_conn.close()
        pg_conn.close()

        # Print summary
        stats.summary()

        if stats.errors:
            sys.exit(1)

        if not args.dry_run:
            print("✅ Migration completed successfully!")
            print("\nNext steps:")
            print("1. Update .env file: DB_TYPE=postgresql")
            print("2. Restart the application")
            print("3. Verify data integrity\n")

    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
