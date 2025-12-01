"""
Database Abstraction Layer

Provides unified interface for both SQLite and PostgreSQL.
"""

import os
from typing import TYPE_CHECKING

from .connection import DatabaseAdapter
from .factory import close_database_adapter, get_database_adapter

# Lazy import adapters to avoid importing psycopg2 when using SQLite
if TYPE_CHECKING:
    from .postgres_adapter import PostgreSQLAdapter
    from .sqlite_adapter import SQLiteAdapter

__all__ = [
    "DatabaseAdapter",
    "SQLiteAdapter",
    "PostgreSQLAdapter",
    "get_database_adapter",
    "close_database_adapter",
]


# Dynamic imports for adapters
def __getattr__(name: str):
    """Lazy load database adapters to avoid unnecessary dependencies."""
    if name == "SQLiteAdapter":
        from .sqlite_adapter import SQLiteAdapter
        return SQLiteAdapter
    elif name == "PostgreSQLAdapter":
        from .postgres_adapter import PostgreSQLAdapter
        return PostgreSQLAdapter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
