#!/usr/bin/env python3
"""
Database Migration Runner

Applies SQL migrations from app/server/db/migrations/ directory.
Tracks applied migrations to prevent re-running.
"""

import sqlite3
import sys
from pathlib import Path
from typing import List, Tuple

# Database path
DB_PATH = Path(__file__).parent.parent / "app" / "server" / "db" / "workflow_history.db"
MIGRATIONS_DIR = Path(__file__).parent.parent / "app" / "server" / "db" / "migrations"


def init_migrations_table(conn: sqlite3.Connection):
    """Create migrations tracking table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            migration_file TEXT UNIQUE NOT NULL,
            applied_at TEXT DEFAULT (datetime('now')),
            checksum TEXT
        )
    """)
    conn.commit()


def get_applied_migrations(conn: sqlite3.Connection) -> set:
    """Get set of already applied migration filenames."""
    cursor = conn.execute("SELECT migration_file FROM schema_migrations")
    return {row[0] for row in cursor.fetchall()}


def get_pending_migrations(applied: set) -> List[Tuple[str, Path]]:
    """Get list of pending migrations sorted by filename."""
    if not MIGRATIONS_DIR.exists():
        return []

    all_migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))
    pending = []

    for migration_path in all_migrations:
        filename = migration_path.name
        if filename not in applied:
            pending.append((filename, migration_path))

    return pending


def apply_migration(conn: sqlite3.Connection, filename: str, migration_path: Path):
    """Apply a single migration file."""
    print(f"\n📦 Applying migration: {filename}")

    # Read migration SQL
    sql = migration_path.read_text()

    # Execute in transaction
    try:
        # Split on semicolons to execute statements individually
        # This is needed because SQLite doesn't support multiple statements in executescript with FOREIGN KEY
        statements = [s.strip() for s in sql.split(';') if s.strip()]

        for statement in statements:
            # Skip comments
            if statement.startswith('--'):
                continue
            conn.execute(statement)

        # Record migration as applied
        conn.execute(
            "INSERT INTO schema_migrations (migration_file) VALUES (?)",
            (filename,)
        )

        conn.commit()
        print(f"✅ Applied: {filename}")

    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to apply {filename}: {e}")
        raise


def main():
    """Main migration runner."""
    print("🗄️  Database Migration Runner")
    print(f"Database: {DB_PATH}")
    print(f"Migrations: {MIGRATIONS_DIR}")

    # Ensure database exists
    if not DB_PATH.exists():
        print(f"\n⚠️  Database does not exist: {DB_PATH}")
        print("Creating database...")
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Connect to database
    conn = sqlite3.connect(str(DB_PATH))

    try:
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")

        # Initialize migrations tracking
        init_migrations_table(conn)

        # Get applied and pending migrations
        applied = get_applied_migrations(conn)
        pending = get_pending_migrations(applied)

        if not pending:
            print("\n✨ No pending migrations. Database is up to date!")
            return 0

        print(f"\n📋 Found {len(pending)} pending migration(s)")
        print(f"📋 Already applied: {len(applied)} migration(s)")

        # Apply each pending migration
        for filename, migration_path in pending:
            apply_migration(conn, filename, migration_path)

        print(f"\n✅ Successfully applied {len(pending)} migration(s)")
        return 0

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return 1

    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
