#!/usr/bin/env python3
"""
Run pattern approvals migration on PostgreSQL
"""
import os
import sys

# Add app/server to path to import database module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'server'))

# Set environment to use PostgreSQL
os.environ['DB_TYPE'] = 'postgresql'
os.environ['POSTGRES_HOST'] = os.getenv('POSTGRES_HOST', 'localhost')
os.environ['POSTGRES_PORT'] = os.getenv('POSTGRES_PORT', '5432')
os.environ['POSTGRES_DB'] = os.getenv('POSTGRES_DB', 'tac_webbuilder')
os.environ['POSTGRES_USER'] = os.getenv('POSTGRES_USER', 'tac_user')
os.environ['POSTGRES_PASSWORD'] = os.getenv('POSTGRES_PASSWORD', 'changeme')

from database import get_database_adapter

def main():
    """Run the migration"""
    migration_file = os.path.join(
        os.path.dirname(__file__),
        '..',
        'app',
        'server',
        'db',
        'migrations',
        '016_add_pattern_approvals_postgres.sql'
    )

    print(f"Reading migration from: {migration_file}")

    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    adapter = get_database_adapter()
    print(f"Using adapter: {type(adapter).__name__}")

    with adapter.get_connection() as conn:
        cursor = conn.cursor()

        # Execute migration
        print("Running migration...")
        cursor.execute(migration_sql)
        conn.commit()
        print("Migration completed successfully!")

        # Verify tables exist
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name LIKE '%pattern%'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print("\nPattern tables in PostgreSQL:")
        for table in tables:
            print(f"  - {table['table_name']}")

if __name__ == '__main__':
    main()
