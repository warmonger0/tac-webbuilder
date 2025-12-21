"""
Migration: Add generated_plan column to planned_features table

This migration adds the generated_plan column to support persisting
AI-generated implementation plans so they don't need to be regenerated.

The column stores the full PlanSummary JSON object including phases,
estimated hours, and markdown prompts.
"""

import sys
sys.path.insert(0, '/Users/Warmonger0/tac/tac-webbuilder/app/server')

from database import get_database_adapter


def migrate():
    """Add generated_plan column to planned_features table"""
    adapter = get_database_adapter()
    db_type = adapter.get_db_type()

    with adapter.get_connection() as conn:
        cursor = conn.cursor()

        # Check if column already exists
        if db_type == "postgresql":
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'planned_features' AND column_name = 'generated_plan'
            """)
        else:  # sqlite
            cursor.execute("PRAGMA table_info(planned_features)")
            columns = {row[1] for row in cursor.fetchall()}
            if 'generated_plan' in columns:
                print("✓ generated_plan column already exists")
                return

        if db_type == "postgresql" and cursor.fetchone():
            print("✓ generated_plan column already exists")
            return

        print("Adding generated_plan column to planned_features table...")

        # Add the column (JSONB for PostgreSQL, TEXT for SQLite)
        if db_type == "postgresql":
            cursor.execute("""
                ALTER TABLE planned_features
                ADD COLUMN generated_plan JSONB
            """)
        else:  # sqlite
            cursor.execute("""
                ALTER TABLE planned_features
                ADD COLUMN generated_plan TEXT
            """)

        conn.commit()
        print("✓ Successfully added generated_plan column")


def rollback():
    """Remove generated_plan column from planned_features table"""
    adapter = get_database_adapter()

    with adapter.get_connection() as conn:
        cursor = conn.cursor()

        print("Removing generated_plan column from planned_features table...")

        cursor.execute("""
            ALTER TABLE planned_features
            DROP COLUMN IF EXISTS generated_plan
        """)

        conn.commit()
        print("✓ Successfully removed generated_plan column")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback()
    else:
        migrate()
