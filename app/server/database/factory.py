"""
Database Adapter Factory

Provides PostgreSQL database adapter (SQLite support has been removed).
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
    Get the PostgreSQL database adapter.

    Note: SQLite support has been removed. This now only returns PostgreSQLAdapter.

    Returns:
        DatabaseAdapter: PostgreSQL adapter instance
    """
    global _adapter

    if _adapter is None:
        from .postgres_adapter import PostgreSQLAdapter
        _adapter = PostgreSQLAdapter()

    return _adapter


def close_database_adapter() -> None:
    """Close the database adapter (cleanup pools, etc.)"""
    global _adapter
    if _adapter is not None:
        _adapter.close()
        _adapter = None
