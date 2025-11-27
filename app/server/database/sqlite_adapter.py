"""
SQLite Database Adapter

Wraps existing SQLite connection logic from utils/db_connection.py
into the DatabaseAdapter interface for backward compatibility.
"""

import sqlite3
import time
from contextlib import contextmanager
from typing import Any, Generator, Optional

from .connection import DatabaseAdapter


class SQLiteAdapter(DatabaseAdapter):
    """SQLite database adapter (backward compatible with existing code)"""

    def __init__(
        self,
        db_path: str = "db/database.db",
        max_retries: int = 3,
        retry_delay: float = 0.1,
    ):
        """
        Initialize SQLite adapter.

        Args:
            db_path: Path to SQLite database file
            max_retries: Maximum connection retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.db_path = db_path
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager for SQLite connections (from existing db_connection.py).

        Provides:
        - Automatic commit on success
        - Automatic rollback on errors
        - Retry logic for SQLITE_BUSY
        - Dict-like row access via sqlite3.Row

        Yields:
            sqlite3.Connection: Database connection
        """
        conn = None
        last_error = None

        # Retry loop for SQLITE_BUSY errors
        for attempt in range(self.max_retries):
            try:
                conn = sqlite3.connect(str(self.db_path))
                conn.row_factory = sqlite3.Row  # Enable dict-like row access
                break  # Connection successful
            except sqlite3.OperationalError as e:
                last_error = e
                # SQLITE_BUSY has error message containing "database is locked"
                if "locked" in str(e).lower() and attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    # Non-busy error or final retry attempt
                    raise

        # If we couldn't establish a connection after retries
        if conn is None:
            raise last_error or sqlite3.OperationalError(
                "Failed to connect to database"
            )

        # Transaction management
        try:
            yield conn
        except Exception as e:
            # Rollback on any exception
            conn.rollback()
            raise e
        else:
            # Commit on successful completion
            conn.commit()
        finally:
            # Always close the connection
            conn.close()

    def execute_query(self, query: str, params: Optional[tuple] = None) -> Any:
        """
        Execute a query and return results.

        Args:
            query: SQL query string
            params: Query parameters (optional)

        Returns:
            List of rows (as sqlite3.Row objects)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()

    def placeholder(self) -> str:
        """
        Return SQLite placeholder character.

        Returns:
            '?' for SQLite
        """
        return "?"

    def now_function(self) -> str:
        """
        Return SQLite current timestamp function.

        Returns:
            "datetime('now')" for SQLite
        """
        return "datetime('now')"

    def close(self) -> None:
        """
        Clean up resources.

        SQLite doesn't have connection pools, so nothing to clean up.
        """
        pass

    def health_check(self) -> bool:
        """
        Check if SQLite database is accessible.

        Returns:
            True if database is healthy, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception:
            return False

    def get_db_type(self) -> str:
        """
        Get database type name.

        Returns:
            'sqlite'
        """
        return "sqlite"
