"""
Database connection utility for centralized SQLite connection management.

This module provides a context manager for handling SQLite database connections
with automatic transaction management, retry logic for busy databases, and
consistent row factory configuration.

Usage:
    Basic usage with default database path:

    >>> from utils.db_connection import get_connection
    >>> with get_connection() as conn:
    ...     cursor = conn.cursor()
    ...     cursor.execute("SELECT * FROM users")
    ...     rows = cursor.fetchall()
    ...     # Access columns by name: rows[0]["username"]

    Custom database path:

    >>> with get_connection(db_path="data/custom.db") as conn:
    ...     # Connection automatically commits on successful exit
    ...     conn.execute("INSERT INTO logs (message) VALUES (?)", ("test",))

    Error handling (automatic rollback):

    >>> try:
    ...     with get_connection() as conn:
    ...         conn.execute("INSERT INTO users (id) VALUES (1)")
    ...         raise ValueError("Something went wrong")
    ... except ValueError:
    ...     pass  # Transaction was automatically rolled back

Benefits:
    - Eliminates duplicate connection patterns across the codebase
    - Automatic commit on success, rollback on errors
    - Retry logic for transient SQLITE_BUSY errors
    - Dict-like row access via sqlite3.Row factory
    - Guaranteed connection cleanup in all cases
"""

import sqlite3
import time
from collections.abc import Generator
from contextlib import contextmanager


@contextmanager
def get_connection(
    db_path: str = "db/database.db",
    max_retries: int = 3,
    retry_delay: float = 0.1,
) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for SQLite database connections with retry logic.

    Provides automatic transaction management:
    - Commits on successful exit
    - Rolls back on exceptions
    - Ensures connection is closed in all cases

    Implements retry logic for SQLITE_BUSY errors (error code 5) to handle
    concurrent access scenarios gracefully.

    Args:
        db_path: Path to the SQLite database file. Defaults to "db/database.db".
                 Relative paths are resolved from the current working directory.
        max_retries: Maximum number of connection attempts for SQLITE_BUSY errors.
                    Defaults to 3.
        retry_delay: Delay in seconds between retry attempts. Defaults to 0.1.

    Yields:
        sqlite3.Connection: Database connection with row_factory set to sqlite3.Row
                           for dict-like row access.

    Raises:
        sqlite3.OperationalError: If connection fails after all retry attempts or
                                 for non-SQLITE_BUSY database errors.
        Exception: Any exception raised within the context block is re-raised
                  after automatic rollback.

    Examples:
        Successful transaction (auto-commit):
        >>> with get_connection() as conn:
        ...     conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
        ...     conn.execute("INSERT INTO test VALUES (1, 'Alice')")
        ...     # Commits automatically here

        Failed transaction (auto-rollback):
        >>> try:
        ...     with get_connection() as conn:
        ...         conn.execute("INSERT INTO test VALUES (2, 'Bob')")
        ...         raise ValueError("Validation failed")
        ... except ValueError:
        ...     pass  # Data not committed, rollback occurred

        Dict-like row access:
        >>> with get_connection() as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT id, name FROM test")
        ...     row = cursor.fetchone()
        ...     print(row["name"])  # Access by column name
        ...     print(row[1])       # Also works with index
    """
    conn = None
    last_error = None

    # Retry loop for SQLITE_BUSY errors
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row  # Enable dict-like row access
            break  # Connection successful
        except sqlite3.OperationalError as e:
            last_error = e
            # SQLITE_BUSY has error message containing "database is locked"
            if "locked" in str(e).lower() and attempt < max_retries - 1:
                time.sleep(retry_delay)
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
