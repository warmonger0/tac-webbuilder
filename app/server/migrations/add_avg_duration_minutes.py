#!/usr/bin/env python3
"""
Migration: Add avg_duration_minutes column to operation_patterns table

This column stores the average workflow duration for pattern caching.
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path for database module
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_database_adapter

logger = logging.getLogger(__name__)


def run_migration():
    """Add avg_duration_minutes column to operation_patterns if it doesn't exist."""
    adapter = get_database_adapter()
    db_type = adapter.get_db_type()

    logger.info("Running migration: add avg_duration_minutes to operation_patterns")

    try:
        with adapter.get_connection() as conn:
            cursor = conn.cursor()

            if db_type == "postgresql":
                # PostgreSQL: Add column if not exists
                cursor.execute("""
                    ALTER TABLE operation_patterns
                    ADD COLUMN IF NOT EXISTS avg_duration_minutes INTEGER DEFAULT 0;
                """)
                logger.info("Added avg_duration_minutes column to operation_patterns (PostgreSQL)")

            else:  # SQLite
                # SQLite: Check if column exists first
                cursor.execute("PRAGMA table_info(operation_patterns)")
                columns = [row[1] for row in cursor.fetchall()]

                if "avg_duration_minutes" not in columns:
                    cursor.execute("""
                        ALTER TABLE operation_patterns
                        ADD COLUMN avg_duration_minutes INTEGER DEFAULT 0;
                    """)
                    logger.info("Added avg_duration_minutes column to operation_patterns (SQLite)")
                else:
                    logger.info("Column avg_duration_minutes already exists (SQLite)")

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
