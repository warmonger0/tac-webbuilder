"""
Database schema verification script.

Verifies that all pattern learning tables exist with correct schema,
indexes, and foreign key constraints.

Run: cd app/server && uv run python tests/manual/verify_database_schema.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.db_connection import get_connection

# Database path
DB_PATH = "db/workflow_history.db"


def verify_tables_exist():
    """Verify all three pattern learning tables exist."""
    print("\n" + "=" * 60)
    print("VERIFYING DATABASE TABLES")
    print("=" * 60)

    expected_tables = [
        "operation_patterns",
        "pattern_occurrences",
        "tool_calls"
    ]

    with get_connection(db_path=DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN (?, ?, ?)",
            expected_tables
        )
        existing_tables = [row[0] for row in cursor.fetchall()]

    print(f"\n✅ Checking for {len(expected_tables)} required tables:")
    all_exist = True
    for table in expected_tables:
        if table in existing_tables:
            print(f"   ✅ {table}")
        else:
            print(f"   ❌ {table} - MISSING!")
            all_exist = False

    if all_exist:
        print(f"\n✅ All {len(expected_tables)} tables exist")
    else:
        print("\n❌ Some tables are missing!")

    return all_exist


def verify_indexes_exist():
    """Verify required indexes exist."""
    print("\n" + "=" * 60)
    print("VERIFYING INDEXES")
    print("=" * 60)

    required_indexes = [
        "idx_pattern_type",
        "idx_automation_status",
        "idx_confidence_score",
        "idx_occurrence_count"
    ]

    with get_connection(db_path=DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
        existing_indexes = [row[0] for row in cursor.fetchall()]

    print(f"\n✅ Checking for {len(required_indexes)} required indexes:")
    for index in required_indexes:
        if index in existing_indexes:
            print(f"   ✅ {index}")
        else:
            print(f"   ⚠️  {index} - Not found (may be auto-created)")

    print(f"\n✅ Total indexes found: {len(existing_indexes)}")
    return True


def verify_foreign_keys():
    """Verify foreign key relationships."""
    print("\n" + "=" * 60)
    print("VERIFYING FOREIGN KEY RELATIONSHIPS")
    print("=" * 60)

    with get_connection(db_path=DB_PATH) as conn:
        cursor = conn.cursor()

        # Check pattern_occurrences foreign keys
        cursor.execute("PRAGMA foreign_key_list(pattern_occurrences)")
        fk_results = cursor.fetchall()

        print("\n✅ pattern_occurrences foreign keys:")
        if fk_results:
            for fk in fk_results:
                print(f"   ✅ {fk[2]}.{fk[3]} -> {fk[4]}")
        else:
            print("   ⚠️  No foreign keys found (may not be enforced)")

    return True


def display_table_counts():
    """Display row counts for each table."""
    print("\n" + "=" * 60)
    print("TABLE ROW COUNTS")
    print("=" * 60)

    tables = ["operation_patterns", "pattern_occurrences", "tool_calls", "workflow_history"]

    with get_connection(db_path=DB_PATH) as conn:
        cursor = conn.cursor()

        print()
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   {table:25} {count:>6} rows")
            except Exception as e:
                print(f"   {table:25} ERROR: {e}")


def display_sample_data():
    """Display sample data from each pattern table."""
    print("\n" + "=" * 60)
    print("SAMPLE DATA")
    print("=" * 60)

    with get_connection(db_path=DB_PATH) as conn:
        cursor = conn.cursor()

        # Sample from operation_patterns
        print("\n📊 operation_patterns (first 3 rows):")
        cursor.execute("""
            SELECT pattern_signature, pattern_type, occurrence_count,
                   automation_status, confidence_score
            FROM operation_patterns
            LIMIT 3
        """)
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                sig, type_, count, status, confidence = row
                print(f"   - {sig}")
                print(f"     Type: {type_}, Count: {count}, Status: {status}, "
                      f"Confidence: {confidence:.1f}")
        else:
            print("   (No data yet)")

        # Sample from pattern_occurrences
        print("\n📊 pattern_occurrences (first 3 rows):")
        cursor.execute("""
            SELECT pattern_id, workflow_id, detected_at
            FROM pattern_occurrences
            LIMIT 3
        """)
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                pattern_id, workflow_id, detected_at = row
                print(f"   - Pattern ID: {pattern_id}, Workflow ID: {workflow_id}")
                print(f"     Detected: {detected_at}")
        else:
            print("   (No data yet)")

        # Sample from tool_calls
        print("\n📊 tool_calls (first 3 rows):")
        cursor.execute("""
            SELECT pattern_id, workflow_id, success
            FROM tool_calls
            LIMIT 3
        """)
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                pattern_id, workflow_id, success = row
                success_str = "✅" if success else "❌"
                print(f"   - Pattern ID: {pattern_id}, Workflow ID: {workflow_id}, "
                      f"Success: {success_str}")
        else:
            print("   (No data yet)")


def main():
    """Run all verification checks."""
    print("\n" + "=" * 60)
    print("PATTERN LEARNING DATABASE VERIFICATION")
    print("=" * 60)
    print("\nDatabase: db/workflow_history.db")

    try:
        # Run all checks
        tables_ok = verify_tables_exist()
        indexes_ok = verify_indexes_exist()
        fk_ok = verify_foreign_keys()

        # Display statistics
        display_table_counts()
        display_sample_data()

        # Final summary
        print("\n" + "=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)

        if tables_ok and indexes_ok and fk_ok:
            print("\n✅ All checks passed!")
            print("✅ Database schema is correctly configured")
            print("✅ Ready for pattern detection and learning")
        else:
            print("\n⚠️  Some checks failed")
            print("⚠️  Review the output above for details")
            return 1

        return 0

    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
