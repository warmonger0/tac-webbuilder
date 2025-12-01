import io
import sqlite3

import pandas as pd

try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


def _is_postgresql_connection(conn) -> bool:
    """Check if a connection is PostgreSQL."""
    if PSYCOPG2_AVAILABLE:
        return isinstance(conn, psycopg2.extensions.connection)
    return False


def generate_csv_from_data(data: list[dict], columns: list[str]) -> bytes:
    """
    Generate CSV file from data and columns.

    Args:
        data: List of dictionaries containing the data
        columns: List of column names

    Returns:
        bytes: CSV file content as bytes
    """
    if not data and not columns:
        return b""

    if not columns and data:
        columns = list(data[0].keys()) if data else []

    df = pd.DataFrame(data, columns=columns)

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_content = csv_buffer.getvalue()
    csv_buffer.close()

    return csv_content.encode('utf-8')


def generate_csv_from_table(conn: sqlite3.Connection, table_name: str) -> bytes:
    """
    Generate CSV file from a database table.

    Args:
        conn: Database connection (SQLite or PostgreSQL)
        table_name: Name of the table to export

    Returns:
        bytes: CSV file content as bytes

    Raises:
        ValueError: If table doesn't exist
    """
    cursor = conn.cursor()

    # Check if table exists using database-specific query
    if _is_postgresql_connection(conn):
        cursor.execute("""
            SELECT COUNT(*) FROM pg_catalog.pg_tables
            WHERE schemaname = 'public' AND tablename = %s
        """, (table_name,))
        result = cursor.fetchone()
        if not result or result[0] == 0:
            raise ValueError(f"Table '{table_name}' does not exist")
    else:  # SQLite
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
        """, (table_name,))
        if not cursor.fetchone():
            raise ValueError(f"Table '{table_name}' does not exist")

    query = f'SELECT * FROM "{table_name}"'
    df = pd.read_sql_query(query, conn)

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_content = csv_buffer.getvalue()
    csv_buffer.close()

    return csv_content.encode('utf-8')
