#!/usr/bin/env python3
"""
Planned Features Database Schema Initialization

Initializes the planned_features table and related indexes for SQLite.
"""

import logging
import os
from database import get_database_adapter

logger = logging.getLogger(__name__)


def init_planned_features_db():
    """
    Initialize planned_features database schema.

    Creates the planned_features table with all necessary indexes and triggers
    if it doesn't already exist.
    """
    try:
        adapter = get_database_adapter()

        # Determine which schema file to use based on database type
        db_type = adapter.get_db_type()

        if db_type == "postgresql":
            schema_file = "017_add_planned_features_postgres.sql"
        else:  # sqlite
            schema_file = "017_add_planned_features_sqlite.sql"

        schema_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "db",
            "migrations",
            schema_file
        )

        if not os.path.exists(schema_path):
            logger.warning(
                f"[INIT] Planned features schema file not found: {schema_path}"
            )
            return

        logger.info(f"[INIT] Initializing planned_features schema from {schema_file}")

        with open(schema_path, "r") as f:
            schema = f.read()

        with adapter.get_connection() as conn:
            cursor = conn.cursor()

            if db_type == "postgresql":
                # Execute each statement separately for PostgreSQL
                statements = [s.strip() for s in schema.split(";") if s.strip()]
                for statement in statements:
                    cursor.execute(statement)
            else:
                # SQLite can handle executescript
                cursor.executescript(schema)

            conn.commit()

        logger.info("[INIT] Planned features database schema initialized successfully")

    except Exception as e:
        logger.error(f"[INIT] Error initializing planned_features schema: {e}")
        raise
