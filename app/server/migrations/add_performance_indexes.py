#!/usr/bin/env python3
"""
Migration: Add performance indexes for common queries

This migration adds indexes to improve query performance for:
- Phase queue queries (by feature_id, adw_id, status)
- Planned features queries (by status, priority, created_at)
- Workflow history queries (by issue_number, status)
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path for database module
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_database_adapter

logger = logging.getLogger(__name__)


def run_migration():
    """Add performance indexes to key tables."""
    adapter = get_database_adapter()
    db_type = adapter.get_db_type()

    logger.info("Running migration: add performance indexes")

    try:
        with adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Phase queue indexes
            logger.info("Creating phase_queue indexes...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_phase_queue_feature_id
                ON phase_queue(feature_id);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_phase_queue_adw_id
                ON phase_queue(adw_id);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_phase_queue_status
                ON phase_queue(status);
            """)

            # Planned features indexes
            logger.info("Creating planned_features indexes...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_planned_features_status
                ON planned_features(status);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_planned_features_priority
                ON planned_features(priority);
            """)

            if db_type == "postgresql":
                # PostgreSQL uses DESC in index
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_planned_features_created
                    ON planned_features(created_at DESC);
                """)
            else:
                # SQLite doesn't support DESC in CREATE INDEX
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_planned_features_created
                    ON planned_features(created_at);
                """)

            # Workflow history indexes
            logger.info("Creating workflow_history indexes...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_workflow_history_issue
                ON workflow_history(issue_number);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_workflow_history_status
                ON workflow_history(status);
            """)

            conn.commit()
            logger.info("Migration completed successfully - all indexes created")
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
