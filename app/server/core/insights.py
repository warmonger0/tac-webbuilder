
from database import get_database_adapter

from core.data_models import ColumnInsight

from .sql_security import SQLSecurityError, execute_query_safely, validate_identifier


def generate_insights(table_name: str, column_names: list[str] | None = None) -> list[ColumnInsight]:
    """
    Generate statistical insights for table columns
    """
    try:
        # Validate table name
        validate_identifier(table_name, "table")

        adapter = get_database_adapter()
        db_type = adapter.get_db_type()

        with adapter.get_connection() as conn:
            # Get table schema using database-specific queries
            if db_type == "postgresql":
                cursor_info = conn.cursor()
                cursor_info.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                columns_info = cursor_info.fetchall()
                # Convert PostgreSQL format to SQLite-like format: [(cid, name, type, ...)]
                columns_info = [(i, col[0], col[1], None, None, None) for i, col in enumerate(columns_info)]
            else:  # sqlite
                cursor_info = execute_query_safely(
                    conn,
                    "PRAGMA table_info({table})",
                    identifier_params={'table': table_name}
                )
                columns_info = cursor_info.fetchall()

            # If no specific columns requested, analyze all
            if not column_names:
                column_names = [col[1] for col in columns_info]
            else:
                # Validate provided column names
                for col in column_names:
                    try:
                        validate_identifier(col, "column")
                    except SQLSecurityError:
                        raise Exception(f"Invalid column name: {col}") from None

            insights = []

            for col_info in columns_info:
                col_name = col_info[1]
                col_type = col_info[2]

                if col_name not in column_names:
                    continue

                # Validate column name
                try:
                    validate_identifier(col_name, "column")
                except SQLSecurityError:
                    # Skip columns with invalid names
                    continue

                # Basic statistics using safe query execution
                cursor_distinct = execute_query_safely(
                    conn,
                    "SELECT COUNT(DISTINCT {column}) FROM {table}",
                    identifier_params={'column': col_name, 'table': table_name}
                )
                unique_values = cursor_distinct.fetchone()[0]

                cursor_null = execute_query_safely(
                    conn,
                    "SELECT COUNT(*) FROM {table} WHERE {column} IS NULL",
                    identifier_params={'table': table_name, 'column': col_name}
                )
                null_count = cursor_null.fetchone()[0]

                insight = ColumnInsight(
                    column_name=col_name,
                    data_type=col_type,
                    unique_values=unique_values,
                    null_count=null_count
                )

                # Type-specific insights
                if col_type in ['INTEGER', 'REAL', 'NUMERIC']:
                    # Numeric insights using safe query execution
                    cursor_stats = execute_query_safely(
                        conn,
                        """
                        SELECT
                            MIN({column}) as min_val,
                            MAX({column}) as max_val,
                            AVG({column}) as avg_val
                        FROM {table}
                        WHERE {column} IS NOT NULL
                        """,
                        identifier_params={'column': col_name, 'table': table_name}
                    )
                    result = cursor_stats.fetchone()
                    if result:
                        insight.min_value = result[0]
                        insight.max_value = result[1]
                        insight.avg_value = result[2]

                # Most common values (for all types) using safe query execution
                cursor_common = execute_query_safely(
                    conn,
                    """
                    SELECT {column}, COUNT(*) as count
                    FROM {table}
                    WHERE {column} IS NOT NULL
                    GROUP BY {column}
                    ORDER BY count DESC
                    LIMIT 5
                    """,
                    identifier_params={'column': col_name, 'table': table_name}
                )
                most_common = cursor_common.fetchall()
                if most_common:
                    insight.most_common = [
                        {"value": val, "count": count}
                        for val, count in most_common
                    ]

                insights.append(insight)

            return insights

    except Exception as e:
        raise Exception(f"Error generating insights: {str(e)}") from e
