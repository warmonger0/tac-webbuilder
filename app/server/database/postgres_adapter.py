"""
PostgreSQL Database Adapter

Implements DatabaseAdapter interface using psycopg2 with connection pooling.
"""

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Any, Generator, Optional
import os

from .connection import DatabaseAdapter


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL database adapter with connection pooling"""

    def __init__(self):
        """Initialize PostgreSQL adapter with connection pool"""
        self.pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=int(os.getenv("POSTGRES_POOL_MIN", "1")),
            maxconn=int(os.getenv("POSTGRES_POOL_MAX", "10")),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "tac_webbuilder"),
            user=os.getenv("POSTGRES_USER", "tac_user"),
            password=os.getenv("POSTGRES_PASSWORD"),
            cursor_factory=RealDictCursor  # Dict-like row access
        )

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

    def execute_query(self, query: str, params: Optional[tuple] = None) -> Any:
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
        if self.pool:
            self.pool.closeall()

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
