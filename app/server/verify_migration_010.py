#!/usr/bin/env python3
"""Verify migration 010 tables exist in PostgreSQL"""

import os
import sys

# Set up environment for PostgreSQL
os.environ["DB_TYPE"] = "postgresql"
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "5432"
os.environ["POSTGRES_DB"] = "tac_webbuilder"
os.environ["POSTGRES_USER"] = "tac_user"
os.environ["POSTGRES_PASSWORD"] = "changeme"

# Import after environment is set
from database.factory import get_database_adapter


def verify_tables():
    """Verify migration 010 tables exist"""
    adapter = get_database_adapter()

    print(f"Verifying migration 010 tables in {adapter.get_db_type()}...")
    print()

    tables_to_check = [
        ("operation_patterns", [
            "id", "pattern_signature", "pattern_type", "automation_status",
            "detection_count", "last_detected", "prediction_count",
            "prediction_accuracy", "last_predicted", "created_at"
        ]),
        ("pattern_predictions", [
            "id", "request_id", "pattern_id", "confidence_score",
            "reasoning", "predicted_at", "was_correct", "validated_at"
        ])
    ]

    try:
        with adapter.get_connection() as conn:
            cursor = conn.cursor()

            for table_name, expected_columns in tables_to_check:
                # Check if table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = %s
                    )
                """, (table_name,))

                result = cursor.fetchone()
                exists = result['exists'] if isinstance(result, dict) else result[0]

                if exists:
                    # Get column names
                    cursor.execute("""
                        SELECT column_name, data_type
                        FROM information_schema.columns
                        WHERE table_name = %s
                        ORDER BY ordinal_position
                    """, (table_name,))

                    columns = cursor.fetchall()
                    column_names = [col['column_name'] if isinstance(col, dict) else col[0] for col in columns]

                    print(f"✓ Table '{table_name}' exists")
                    print(f"  Columns: {', '.join(column_names)}")

                    # Verify expected columns
                    missing = set(expected_columns) - set(column_names)
                    if missing:
                        print(f"  ⚠ Missing columns: {', '.join(missing)}")
                    else:
                        print("  ✓ All expected columns present")

                    # Check indexes
                    cursor.execute("""
                        SELECT indexname
                        FROM pg_indexes
                        WHERE tablename = %s
                    """, (table_name,))

                    indexes = cursor.fetchall()
                    if indexes:
                        index_names = [idx['indexname'] if isinstance(idx, dict) else idx[0] for idx in indexes]
                        print(f"  Indexes: {', '.join(index_names)}")

                    print()
                else:
                    print(f"✗ Table '{table_name}' NOT found!")
                    sys.exit(1)

            print("✓ All migration 010 tables verified successfully!")

    except Exception as e:
        print(f"✗ Error verifying tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_tables()
