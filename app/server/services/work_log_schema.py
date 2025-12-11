"""
Database schema initialization for work log system.

This module handles schema creation for work log tables with support
for both SQLite and PostgreSQL databases.
"""

import logging

from database import get_database_adapter

logger = logging.getLogger(__name__)


def init_work_log_db():
    """
    Initialize the work log database schema.

    Creates the work_log table with support for storing work session logs.

    Safe to call multiple times - creates tables only if they don't exist.
    Supports both SQLite and PostgreSQL.
    """
    adapter = get_database_adapter()
    db_type = adapter.get_db_type()

    with adapter.get_connection() as conn:
        cursor = conn.cursor()

        # Database-specific timestamp defaults and ID type
        if db_type == "postgresql":
            timestamp_default = "NOW()"
            id_type = "SERIAL"
        else:  # sqlite
            timestamp_default = "CURRENT_TIMESTAMP"
            id_type = "INTEGER"

        # Create work_log table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS work_log (
                id {id_type} PRIMARY KEY,
                session_id TEXT NOT NULL,
                summary TEXT NOT NULL,
                chat_file_link TEXT,
                issue_number INTEGER,
                workflow_id TEXT,
                tags TEXT,
                timestamp TIMESTAMP DEFAULT {timestamp_default},
                created_at TIMESTAMP DEFAULT {timestamp_default}
            )
        """)

        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_work_log_session_id ON work_log(session_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_work_log_timestamp ON work_log(timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_work_log_issue_number ON work_log(issue_number)
        """)

        logger.info(f"[DB] Work log database initialized (type: {db_type})")
