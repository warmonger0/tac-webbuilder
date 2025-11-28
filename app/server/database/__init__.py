"""
Database Abstraction Layer

Provides unified interface for both SQLite and PostgreSQL.
"""

from .connection import DatabaseAdapter
from .factory import close_database_adapter, get_database_adapter
from .postgres_adapter import PostgreSQLAdapter
from .sqlite_adapter import SQLiteAdapter

__all__ = [
    "DatabaseAdapter",
    "SQLiteAdapter",
    "PostgreSQLAdapter",
    "get_database_adapter",
    "close_database_adapter",
]
