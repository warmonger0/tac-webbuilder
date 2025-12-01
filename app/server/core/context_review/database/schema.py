"""
Database schema initialization for context review system.

This module handles schema creation for context review tables with support
for both SQLite and PostgreSQL databases.
"""

import logging

from database import get_database_adapter

logger = logging.getLogger(__name__)


def init_context_review_db():
    """
    Initialize the context review database schema.

    Creates three tables:
    - context_reviews: Main review records
    - context_suggestions: Integration suggestions per review
    - context_cache: Cached analysis results

    Safe to call multiple times - creates tables only if they don't exist.
    Supports both SQLite and PostgreSQL.
    """
    adapter = get_database_adapter()
    db_type = adapter.get_db_type()

    with adapter.get_connection() as conn:
        cursor = conn.cursor()

        # Use database-specific syntax for auto-incrementing primary key
        if db_type == "postgresql":
            pk_definition = "SERIAL PRIMARY KEY"
            timestamp_default = "NOW()"
            text_type = "TEXT"
        else:  # sqlite
            pk_definition = "INTEGER PRIMARY KEY AUTOINCREMENT"
            timestamp_default = "CURRENT_TIMESTAMP"
            text_type = "TEXT"

        # Create context_reviews table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS context_reviews (
                id {pk_definition},
                workflow_id {text_type},
                issue_number INTEGER,
                change_description {text_type} NOT NULL,
                project_path {text_type} NOT NULL,
                analysis_timestamp TIMESTAMP DEFAULT {timestamp_default},
                analysis_duration_seconds REAL,
                agent_cost REAL,
                status {text_type} NOT NULL CHECK(status IN ('pending', 'analyzing', 'complete', 'failed')),
                result {text_type}
            )
        """)

        # Create context_suggestions table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS context_suggestions (
                id {pk_definition},
                review_id INTEGER NOT NULL,
                suggestion_type {text_type} NOT NULL CHECK(suggestion_type IN (
                    'file-to-modify', 'file-to-create', 'reference', 'risk', 'strategy'
                )),
                suggestion_text {text_type} NOT NULL,
                confidence REAL,
                priority INTEGER,
                rationale {text_type},
                FOREIGN KEY (review_id) REFERENCES context_reviews(id)
            )
        """)

        # Create context_cache table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS context_cache (
                id {pk_definition},
                cache_key {text_type} NOT NULL UNIQUE,
                analysis_result {text_type} NOT NULL,
                created_at TIMESTAMP DEFAULT {timestamp_default},
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP
            )
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_context_reviews_workflow
            ON context_reviews(workflow_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_context_reviews_issue
            ON context_reviews(issue_number)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_context_reviews_status
            ON context_reviews(status)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_context_suggestions_review
            ON context_suggestions(review_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_context_suggestions_type
            ON context_suggestions(suggestion_type)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_context_cache_key
            ON context_cache(cache_key)
        """)

        logger.info(f"[DB] Context review database initialized (type: {db_type})")
