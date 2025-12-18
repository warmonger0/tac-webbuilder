#!/usr/bin/env python3
"""
Migration: Make feature_id nullable in phase_queue table

The feature_id column should be nullable because not all workflows
come from planned features. Some workflows are ad-hoc or come from
external issues.
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path for database module
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_database_adapter

logger = logging.getLogger(__name__)


def run_migration():
    """Make feature_id column nullable in phase_queue table."""
    adapter = get_database_adapter()
    db_type = adapter.get_db_type()

    logger.info("Running migration: make feature_id nullable in phase_queue")

    try:
        with adapter.get_connection() as conn:
            cursor = conn.cursor()

            if db_type == "postgresql":
                # PostgreSQL: ALTER COLUMN to DROP NOT NULL
                cursor.execute("""
                    ALTER TABLE phase_queue
                    ALTER COLUMN feature_id DROP NOT NULL;
                """)
                logger.info("Made feature_id nullable in phase_queue (PostgreSQL)")

            else:  # SQLite
                # SQLite doesn't support ALTER COLUMN, need to recreate table
                # First check if we need to migrate
                cursor.execute("PRAGMA table_info(phase_queue)")
                columns = cursor.fetchall()

                # Check if feature_id is NOT NULL
                feature_id_col = [col for col in columns if col[1] == 'feature_id'][0]
                if feature_id_col[3] == 1:  # notnull = 1
                    logger.info("SQLite: feature_id is NOT NULL, migrating...")

                    # Create new table with nullable feature_id
                    cursor.execute("""
                        CREATE TABLE phase_queue_new (
                            queue_id TEXT PRIMARY KEY,
                            feature_id INTEGER,  -- Now nullable
                            phase_number INTEGER NOT NULL,
                            issue_number INTEGER NOT NULL,
                            status TEXT NOT NULL,
                            phase_data TEXT,
                            created_at TEXT,
                            updated_at TEXT,
                            depends_on_phases TEXT,
                            adw_id TEXT,
                            parent_queue_id TEXT,
                            estimated_hours REAL,
                            actual_hours REAL,
                            model_override TEXT,
                            timeout_override INTEGER,
                            tags TEXT,
                            current_phase TEXT
                        )
                    """)

                    # Copy data
                    cursor.execute("""
                        INSERT INTO phase_queue_new
                        SELECT * FROM phase_queue
                    """)

                    # Drop old table
                    cursor.execute("DROP TABLE phase_queue")

                    # Rename new table
                    cursor.execute("ALTER TABLE phase_queue_new RENAME TO phase_queue")

                    logger.info("Made feature_id nullable in phase_queue (SQLite)")
                else:
                    logger.info("feature_id already nullable (SQLite)")

            conn.commit()
            logger.info("Migration completed successfully")
            return True

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    success = run_migration()
    sys.exit(0 if success else 1)
