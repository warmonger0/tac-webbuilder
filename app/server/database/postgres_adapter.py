"""
PostgreSQL Database Adapter

Implements DatabaseAdapter interface using psycopg2 with connection pooling.
"""

import os
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor

from .connection import DatabaseAdapter


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL database adapter with connection pooling"""

    def __init__(self):
        """Initialize PostgreSQL adapter (lazy connection pool)"""
        self._pool = None
        self._pool_config = {
            "minconn": int(os.getenv("POSTGRES_POOL_MIN", "1")),
            "maxconn": int(os.getenv("POSTGRES_POOL_MAX", "10")),
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("POSTGRES_DB", "tac_webbuilder"),
            "user": os.getenv("POSTGRES_USER", "tac_user"),
            "password": os.getenv("POSTGRES_PASSWORD"),
            "cursor_factory": RealDictCursor,  # Dict-like row access
        }

    @property
    def pool(self):
        """Lazy-initialize connection pool on first access"""
        if self._pool is None:
            self._pool = psycopg2.pool.ThreadedConnectionPool(**self._pool_config)
        return self._pool

    @contextmanager
    def get_connection(self) -> Generator[Any, None, None]:
        """Get PostgreSQL connection from pool"""
        conn = self.pool.getconn()
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            raise e
        else:
            conn.commit()
        finally:
            self.pool.putconn(conn)

    def execute_query(self, query: str, params: tuple | None = None) -> Any:
        """Execute query and return results"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()

    def placeholder(self) -> str:
        """Return PostgreSQL placeholder"""
        return "%s"

    def now_function(self) -> str:
        """Return PostgreSQL timestamp function"""
        return "NOW()"

    def close(self) -> None:
        """Close connection pool"""
        if self._pool:
            self._pool.closeall()
            self._pool = None  # Reset to allow lazy re-initialization

    def health_check(self) -> bool:
        """Check PostgreSQL health"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception:
            return False

    def get_db_type(self) -> str:
        """Get database type"""
        return "postgresql"
