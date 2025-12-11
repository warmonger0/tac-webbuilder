"""
Database Adapter Factory

Provides database adapter with support for both SQLite and PostgreSQL.
Automatically selects the appropriate adapter based on environment configuration.
"""

import os
from typing import TYPE_CHECKING, Union

from .connection import DatabaseAdapter

if TYPE_CHECKING:
    pass

# Global adapter instance (singleton pattern)
_adapter: Union[DatabaseAdapter, None] = None


def get_database_adapter() -> DatabaseAdapter:
    """
    Get the appropriate database adapter based on environment configuration.

    Database selection:
    - If DB_TYPE=sqlite or env vars for PostgreSQL are missing, use SQLiteAdapter
    - If DB_TYPE=postgresql, use PostgreSQLAdapter
    - Default: Use PostgreSQL if all required env vars are present, else SQLite

    Returns:
        DatabaseAdapter: Appropriate adapter instance (SQLite or PostgreSQL)

    Raises:
        ImportError: If required database driver is not installed
    """
    global _adapter

    if _adapter is None:
        db_type = os.getenv("DB_TYPE", "").lower()

        # Explicit SQLite selection
        if db_type == "sqlite":
            from .sqlite_adapter import SQLiteAdapter
            _adapter = SQLiteAdapter()
        # Explicit PostgreSQL selection
        elif db_type == "postgresql":
            from .postgres_adapter import PostgreSQLAdapter
            _adapter = PostgreSQLAdapter()
        # Auto-detect based on environment
        else:
            # Check if PostgreSQL env vars are configured
            pg_required_vars = [
                "POSTGRES_HOST",
                "POSTGRES_PORT",
                "POSTGRES_DB",
                "POSTGRES_USER",
                "POSTGRES_PASSWORD",
            ]

            pg_available = all(os.getenv(var) for var in pg_required_vars)

            if pg_available:
                # Use PostgreSQL if all credentials are provided
                from .postgres_adapter import PostgreSQLAdapter
                _adapter = PostgreSQLAdapter()
            else:
                # Fall back to SQLite for testing and local development
                from .sqlite_adapter import SQLiteAdapter
                _adapter = SQLiteAdapter()

    return _adapter


def close_database_adapter() -> None:
    """Close the database adapter (cleanup pools, etc.)"""
    global _adapter
    if _adapter is not None:
        _adapter.close()
        _adapter = None
