"""
Database Adapter Abstract Interface

This module defines the abstract base class for database adapters.
Supports both SQLite and PostgreSQL through a unified interface.
"""

from abc import ABC, abstractmethod
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any


class DatabaseAdapter(ABC):
    """Abstract database adapter interface for TAC WebBuilder"""

    @abstractmethod
    @contextmanager
    def get_connection(self) -> Generator[Any, None, None]:
        """
        Get database connection context manager.

        Yields:
            Database connection object (sqlite3.Connection or psycopg2.Connection)

        Example:
            with adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM table")
        """
        pass

    @abstractmethod
    def execute_query(self, query: str, params: tuple | None = None) -> Any:
        """
        Execute a query and return results.

        Args:
            query: SQL query string
            params: Query parameters (optional)

        Returns:
            Query results (format depends on database type)
        """
        pass

    @abstractmethod
    def placeholder(self) -> str:
        """
        Return the placeholder character for this database.

        Returns:
            '?' for SQLite, '%s' for PostgreSQL
        """
        pass

    @abstractmethod
    def now_function(self) -> str:
        """
        Return the current timestamp function for this database.

        Returns:
            "datetime('now')" for SQLite, "NOW()" for PostgreSQL
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Clean up resources (close pools, connections, etc.)

        Called during application shutdown.
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if database is accessible and healthy.

        Returns:
            True if database is healthy, False otherwise
        """
        pass

    @abstractmethod
    def get_db_type(self) -> str:
        """
        Get the database type name.

        Returns:
            'sqlite' or 'postgresql'
        """
        pass
