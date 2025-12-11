#!/usr/bin/env python3
"""Apply migration 010 to PostgreSQL database"""

import os
import sys
from pathlib import Path

# Set up environment for PostgreSQL
os.environ["DB_TYPE"] = "postgresql"
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "5432"
os.environ["POSTGRES_DB"] = "tac_webbuilder"
os.environ["POSTGRES_USER"] = "tac_user"
os.environ["POSTGRES_PASSWORD"] = "changeme"

# Import after environment is set
from database.factory import get_database_adapter

def apply_migration():
    """Apply migration 010 to PostgreSQL"""
    migration_file = Path(__file__).parent / "db" / "migrations" / "010_add_pattern_predictions_postgres.sql"

    if not migration_file.exists():
        print(f"Error: Migration file not found: {migration_file}")
        sys.exit(1)

    # Read migration SQL
    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    # Get database adapter
    adapter = get_database_adapter()

    print(f"Applying migration: {migration_file.name}")
    print(f"Database type: {adapter.get_db_type()}")

    try:
        # Split migration into individual statements (PostgreSQL can handle multiple statements)
        # But we'll execute as one block for simplicity
        with adapter.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(migration_sql)
            print("✓ Migration applied successfully!")

    except Exception as e:
        print(f"✗ Error applying migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    apply_migration()
