"""
Database schema initialization for phase queue system.

This module handles schema creation for phase queue tables with support
for both SQLite and PostgreSQL databases.
"""

import logging

from database import get_database_adapter

logger = logging.getLogger(__name__)


def init_phase_queue_db():
    """
    Initialize the phase queue database schema.

    Creates the phase_queue table and associated indexes.

    Safe to call multiple times - creates tables only if they don't exist.
    Supports both SQLite and PostgreSQL.
    """
    adapter = get_database_adapter()
    db_type = adapter.get_db_type()

    with adapter.get_connection() as conn:
        cursor = conn.cursor()

        # Database-specific timestamp defaults
        if db_type == "postgresql":
            timestamp_default = "NOW()"
        else:  # sqlite
            timestamp_default = "CURRENT_TIMESTAMP"

        # Create phase_queue table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS phase_queue (
                queue_id TEXT PRIMARY KEY,
                parent_issue INTEGER NOT NULL,
                phase_number INTEGER NOT NULL,
                issue_number INTEGER,
                status TEXT CHECK(status IN ('queued', 'ready', 'running', 'completed', 'blocked', 'failed')) DEFAULT 'queued',
                depends_on_phase INTEGER,
                phase_data TEXT,
                created_at TIMESTAMP DEFAULT {timestamp_default},
                updated_at TIMESTAMP DEFAULT {timestamp_default},
                error_message TEXT,
                adw_id TEXT,
                pr_number INTEGER,
                priority INTEGER DEFAULT 50,
                queue_position INTEGER,
                ready_timestamp TIMESTAMP,
                started_timestamp TIMESTAMP
            )
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_phase_queue_status ON phase_queue(status)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_phase_queue_parent ON phase_queue(parent_issue)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_phase_queue_issue ON phase_queue(issue_number)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_phase_queue_depends ON phase_queue(depends_on_phase)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_phase_queue_adw_id ON phase_queue(adw_id)
        """)

        # Create queue_config table for global queue settings
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS queue_config (
                config_key TEXT PRIMARY KEY,
                config_value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT {timestamp_default}
            )
        """)

        # Initialize with queue not paused by default
        cursor.execute("""
            INSERT INTO queue_config (config_key, config_value)
            VALUES ('queue_paused', 'false')
            ON CONFLICT (config_key) DO NOTHING
        """)

        logger.info(f"[DB] Phase queue database initialized (type: {db_type})")
