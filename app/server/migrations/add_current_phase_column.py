"""
Migration: Add current_phase column to phase_queue table

This migration adds the current_phase column to support SSoT architecture
where coordination state (status, current_phase) is stored in the database.

See: docs/adw/state-management-ssot.md
"""

import sys
sys.path.insert(0, '/Users/Warmonger0/tac/tac-webbuilder/app/server')

from database import get_database_adapter


def migrate():
    """Add current_phase column to phase_queue table"""
    adapter = get_database_adapter()

    with adapter.get_connection() as conn:
        cursor = conn.cursor()

        # Check if column already exists
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'phase_queue' AND column_name = 'current_phase'
        """)

        if cursor.fetchone():
            print("✓ current_phase column already exists")
            return

        print("Adding current_phase column to phase_queue table...")

        # Add the column with a default value
        cursor.execute("""
            ALTER TABLE phase_queue
            ADD COLUMN current_phase TEXT DEFAULT 'init'
        """)

        # Update existing rows to derive current_phase from phase_number
        # Map phase_number to phase names: 1=plan, 2=validate, 3=build, etc.
        phase_map = {
            1: 'plan',
            2: 'validate',
            3: 'build',
            4: 'lint',
            5: 'test',
            6: 'review',
            7: 'document',
            8: 'ship',
            9: 'cleanup',
            10: 'verify'
        }

        for phase_num, phase_name in phase_map.items():
            cursor.execute(f"""
                UPDATE phase_queue
                SET current_phase = %s
                WHERE phase_number = %s
            """, (phase_name, phase_num))

        # Make column NOT NULL after populating
        cursor.execute("""
            ALTER TABLE phase_queue
            ALTER COLUMN current_phase SET NOT NULL
        """)

        conn.commit()
        print("✓ Successfully added current_phase column")


def rollback():
    """Remove current_phase column from phase_queue table"""
    adapter = get_database_adapter()

    with adapter.get_connection() as conn:
        cursor = conn.cursor()

        print("Removing current_phase column from phase_queue table...")

        cursor.execute("""
            ALTER TABLE phase_queue
            DROP COLUMN IF EXISTS current_phase
        """)

        conn.commit()
        print("✓ Successfully removed current_phase column")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback()
    else:
        migrate()
