"""Database migration utilities for context review feature."""

import logging
import os
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


def init_context_review_db(db_path: str = "db/database.db") -> None:
    """
    Initialize context review database tables.

    Creates the following tables:
    - context_reviews: Main review records
    - context_suggestions: Individual suggestions from analysis
    - context_cache: Cached analysis results for cost optimization

    Args:
        db_path: Path to the SQLite database file
    """
    # Ensure db directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    # Read migration SQL
    migrations_dir = Path(__file__).parent
    migration_file = migrations_dir / "001_add_context_review.sql"

    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_file}")
        raise FileNotFoundError(f"Migration file not found: {migration_file}")

    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    # Execute migration
    try:
        conn = sqlite3.connect(db_path)
        conn.executescript(migration_sql)
        conn.commit()
        conn.close()
        logger.info(f"Context review database initialized at {db_path}")
    except sqlite3.Error as e:
        logger.error(f"Failed to initialize context review database: {e}")
        raise
