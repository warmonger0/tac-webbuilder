"""
Database Abstraction Layer

Provides unified interface for both SQLite and PostgreSQL.
"""

from .connection import DatabaseAdapter
from .sqlite_adapter import SQLiteAdapter
from .postgres_adapter import PostgreSQLAdapter
from .factory import get_database_adapter, close_database_adapter

__all__ = [
    "DatabaseAdapter",
    "SQLiteAdapter",
    "PostgreSQLAdapter",
    "get_database_adapter",
    "close_database_adapter",
]
