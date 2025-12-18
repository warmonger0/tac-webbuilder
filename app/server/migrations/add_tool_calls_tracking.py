#!/usr/bin/env python3
"""
Migration: Add tool_calls JSONB column to task_logs table

Purpose:
    Adds a tool_calls JSONB column to task_logs to track detailed tool usage
    within ADW workflow phases. This enables pattern detection and automation
    opportunities.

Schema Change:
    ALTER TABLE task_logs
    ADD COLUMN tool_calls JSONB DEFAULT '[]'::jsonb;

    CREATE INDEX idx_task_logs_tool_calls ON task_logs USING GIN (tool_calls);

Rollback:
    ALTER TABLE task_logs DROP COLUMN IF EXISTS tool_calls;
    DROP INDEX IF EXISTS idx_task_logs_tool_calls;

Usage:
    # Apply migration
    python app/server/migrations/add_tool_calls_tracking.py

    # With explicit database config
    POSTGRES_HOST=localhost POSTGRES_PORT=5432 \\
    POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user \\
    POSTGRES_PASSWORD=changeme DB_TYPE=postgresql \\
    python app/server/migrations/add_tool_calls_tracking.py

    # Rollback
    python app/server/migrations/add_tool_calls_tracking.py --rollback
"""

import argparse
import sys
from pathlib import Path

# Add parent directories to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "app" / "server"))

from database import get_database_adapter


def apply_migration():
    """Apply the migration: add tool_calls column and index."""
    print("=" * 80)
    print("MIGRATION: Add tool_calls tracking to task_logs")
    print("=" * 80)

    adapter = get_database_adapter()
    print(f"✓ Connected to database: {type(adapter).__name__}")

    try:
        with adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Check if column already exists
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'task_logs'
                AND column_name = 'tool_calls'
            """)

            if cursor.fetchone():
                print("⚠️  Column 'tool_calls' already exists in task_logs table")
                print("   Migration may have already been applied")
                return False

            # Add tool_calls column
            print("\n1. Adding tool_calls JSONB column...")
            cursor.execute("""
                ALTER TABLE task_logs
                ADD COLUMN tool_calls JSONB DEFAULT '[]'::jsonb
            """)
            print("   ✓ Column added: tool_calls JSONB DEFAULT '[]'::jsonb")

            # Create GIN index for efficient JSONB queries
            print("\n2. Creating GIN index for tool_calls...")
            cursor.execute("""
                CREATE INDEX idx_task_logs_tool_calls
                ON task_logs USING GIN (tool_calls)
            """)
            print("   ✓ Index created: idx_task_logs_tool_calls (GIN)")

            # Commit transaction
            conn.commit()
            print("\n✅ Migration applied successfully!")
            print("\nNext steps:")
            print("  1. Update TaskLogCreate model to include tool_calls field")
            print("  2. Modify observability.py to add tool_calls parameter")
            print("  3. Update TaskLogRepository.create() to handle tool_calls")
            print("  4. Add ToolCallTracker helper class for phase tracking")

            return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def rollback_migration():
    """Rollback the migration: remove tool_calls column and index."""
    print("=" * 80)
    print("ROLLBACK: Remove tool_calls tracking from task_logs")
    print("=" * 80)

    adapter = get_database_adapter()
    print(f"✓ Connected to database: {type(adapter).__name__}")

    try:
        with adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Drop index if exists
            print("\n1. Dropping GIN index...")
            cursor.execute("""
                DROP INDEX IF EXISTS idx_task_logs_tool_calls
            """)
            print("   ✓ Index dropped: idx_task_logs_tool_calls")

            # Drop column if exists
            print("\n2. Dropping tool_calls column...")
            cursor.execute("""
                ALTER TABLE task_logs
                DROP COLUMN IF EXISTS tool_calls
            """)
            print("   ✓ Column dropped: tool_calls")

            # Commit transaction
            conn.commit()
            print("\n✅ Rollback completed successfully!")

            return True

    except Exception as e:
        print(f"\n❌ Rollback failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_migration():
    """Verify the migration was applied correctly."""
    print("\n" + "=" * 80)
    print("VERIFICATION: Checking tool_calls column")
    print("=" * 80)

    adapter = get_database_adapter()

    try:
        with adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Check column exists
            cursor.execute("""
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = 'task_logs'
                AND column_name = 'tool_calls'
            """)

            row = cursor.fetchone()
            if not row:
                print("❌ Column 'tool_calls' NOT found in task_logs")
                return False

            print(f"✓ Column exists: {row['column_name']}")
            print(f"  Data type: {row['data_type']}")
            print(f"  Nullable: {row['is_nullable']}")
            print(f"  Default: {row['column_default']}")

            # Check index exists
            cursor.execute("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'task_logs'
                AND indexname = 'idx_task_logs_tool_calls'
            """)

            idx_row = cursor.fetchone()
            if not idx_row:
                print("❌ Index 'idx_task_logs_tool_calls' NOT found")
                return False

            print(f"\n✓ Index exists: {idx_row['indexname']}")
            print(f"  Definition: {idx_row['indexdef']}")

            print("\n✅ Migration verified successfully!")
            return True

    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Add tool_calls tracking to task_logs table",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Apply migration
  python app/server/migrations/add_tool_calls_tracking.py

  # Rollback migration
  python app/server/migrations/add_tool_calls_tracking.py --rollback

  # Verify migration
  python app/server/migrations/add_tool_calls_tracking.py --verify

  # With explicit PostgreSQL config
  POSTGRES_HOST=localhost POSTGRES_PORT=5432 \\
  POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user \\
  POSTGRES_PASSWORD=changeme DB_TYPE=postgresql \\
  python app/server/migrations/add_tool_calls_tracking.py
        """
    )

    parser.add_argument(
        '--rollback',
        action='store_true',
        help='Rollback the migration (remove column and index)'
    )

    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify the migration was applied correctly'
    )

    args = parser.parse_args()

    try:
        if args.verify:
            success = verify_migration()
        elif args.rollback:
            success = rollback_migration()
        else:
            success = apply_migration()
            if success:
                verify_migration()

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
