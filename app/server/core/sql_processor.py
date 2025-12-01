from typing import Any

from database import get_database_adapter

from .sql_security import SQLSecurityError, execute_query_safely, validate_sql_query


def execute_sql_safely(sql_query: str) -> dict[str, Any]:
    """
    Execute SQL query with safety checks
    """
    try:
        # Validate the SQL query for dangerous operations
        validate_sql_query(sql_query)

        # Connect to database
        adapter = get_database_adapter()
        with adapter.get_connection() as conn:
            # Execute query safely
            # Note: Since this is a user-provided complete SQL query,
            # we can't use parameterization. The validate_sql_query
            # function provides protection against dangerous operations.
            cursor = conn.cursor()
            cursor.execute(sql_query)

            # Get results
            rows = cursor.fetchall()

            # Convert rows to dictionaries
            results = []
            columns = []

            if rows:
                columns = list(rows[0].keys())
                for row in rows:
                    results.append(dict(row))

            return {
                'results': results,
                'columns': columns,
                'error': None
            }

    except SQLSecurityError as e:
        return {
            'results': [],
            'columns': [],
            'error': f"Security error: {str(e)}"
        }
    except Exception as e:
        return {
            'results': [],
            'columns': [],
            'error': str(e)
        }

def get_database_schema() -> dict[str, Any]:
    """
    Get complete database schema information
    """
    try:
        adapter = get_database_adapter()
        db_type = adapter.get_db_type()

        with adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Get all tables safely with database-specific queries
            if db_type == "postgresql":
                cursor.execute("""
                    SELECT tablename FROM pg_catalog.pg_tables
                    WHERE schemaname = 'public'
                """)
            else:  # sqlite
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")

            tables = cursor.fetchall()

            schema = {'tables': {}}

            for table in tables:
                table_name = table[0]

                # Skip system tables
                if table_name.startswith('sqlite_') or table_name.startswith('pg_'):
                    continue

                try:
                    # Get columns for each table using database-specific queries
                    if db_type == "postgresql":
                        cursor.execute("""
                            SELECT column_name, data_type, is_nullable
                            FROM information_schema.columns
                            WHERE table_schema = 'public' AND table_name = %s
                            ORDER BY ordinal_position
                        """, (table_name,))
                        columns_info = cursor.fetchall()
                    else:  # sqlite
                        cursor_info = execute_query_safely(
                            conn,
                            "PRAGMA table_info({table})",
                            identifier_params={'table': table_name}
                        )
                        columns_info = cursor_info.fetchall()

                    columns = {}
                    if db_type == "postgresql":
                        # PostgreSQL returns: (column_name, data_type, is_nullable)
                        for col in columns_info:
                            columns[col[0]] = col[1]  # column_name: data_type
                    else:
                        # SQLite PRAGMA returns: (cid, name, type, notnull, dflt_value, pk)
                        for col in columns_info:
                            columns[col[1]] = col[2]  # column_name: data_type

                    # Get row count safely
                    cursor_count = execute_query_safely(
                        conn,
                        "SELECT COUNT(*) FROM {table}",
                        identifier_params={'table': table_name}
                    )
                    row_count = cursor_count.fetchone()[0]

                    schema['tables'][table_name] = {
                        'columns': columns,
                        'row_count': row_count
                    }

                except SQLSecurityError:
                    # Skip tables with invalid names
                    continue

            return schema

    except Exception as e:
        return {'tables': {}, 'error': str(e)}
