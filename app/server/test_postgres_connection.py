"""Test PostgreSQL connection and basic operations"""
import os
import sys

# Configure PostgreSQL connection
os.environ["DB_TYPE"] = "postgresql"
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "5432"
os.environ["POSTGRES_DB"] = "tac_webbuilder"
os.environ["POSTGRES_USER"] = "tac_user"
os.environ["POSTGRES_PASSWORD"] = "changeme"

from database import get_database_adapter

print("=" * 70)
print("PostgreSQL Connection Test")
print("=" * 70)

try:
    adapter = get_database_adapter()
    print(f"✅ Adapter type: {adapter.get_db_type()}")
    print(f"✅ Placeholder: {adapter.placeholder()}")
    print(f"✅ NOW function: {adapter.now_function()}")

    # Test connection
    with adapter.get_connection() as conn:
        cursor = conn.cursor()

        # Get PostgreSQL version
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        print(f"✅ PostgreSQL version: {version[0][:50]}...")

        # Count tables
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        table_count = cursor.fetchone()[0]
        print(f"✅ Tables in database: {table_count}")

        # List tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print(f"✅ Tables: {', '.join([t[0] for t in tables[:5]])}{'...' if len(tables) > 5 else ''}")

    print("\n" + "=" * 70)
    print("✅ PostgreSQL connection test PASSED!")
    print("=" * 70)
    sys.exit(0)

except Exception as e:
    print(f"\n❌ PostgreSQL connection test FAILED: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "=" * 70)
    print("💡 Troubleshooting:")
    print("  1. Make sure Docker is running: docker ps")
    print("  2. Start PostgreSQL: docker-compose up -d postgres")
    print("  3. Check logs: docker-compose logs postgres")
    print("=" * 70)
    sys.exit(1)
