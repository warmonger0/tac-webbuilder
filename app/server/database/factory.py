"""
Database Adapter Factory

Selects the appropriate database adapter based on environment configuration.
"""

import os
from typing import Union

from .connection import DatabaseAdapter
from .postgres_adapter import PostgreSQLAdapter
from .sqlite_adapter import SQLiteAdapter

# Global adapter instance (singleton pattern)
_adapter: Union[DatabaseAdapter, None] = None


def get_database_adapter() -> DatabaseAdapter:
    """
    Get the configured database adapter.

    Returns database adapter based on DB_TYPE environment variable:
    - 'sqlite' (default): SQLiteAdapter
    - 'postgresql': PostgreSQLAdapter

    Returns:
        DatabaseAdapter: Configured adapter instance
    """
    global _adapter

    if _adapter is None:
        db_type = os.getenv("DB_TYPE", "sqlite").lower()

        _adapter = PostgreSQLAdapter() if db_type == "postgresql" else SQLiteAdapter()

    return _adapter


def close_database_adapter() -> None:
    """Close the database adapter (cleanup pools, etc.)"""
    global _adapter
    if _adapter is not None:
        _adapter.close()
        _adapter = None
