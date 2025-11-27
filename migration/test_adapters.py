"""
Test database adapters (SQLite vs PostgreSQL)
"""

import os
import sys

# Add server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../app/server"))

from database import get_database_adapter, close_database_adapter


def test_adapter():
    """Test current database adapter"""
    adapter = get_database_adapter()

    print(f"Testing {adapter.get_db_type()} adapter...")

    # Health check
    if adapter.health_check():
        print(f"✅ Health check passed")
    else:
        print(f"❌ Health check failed")
        return False

    # Test query
    try:
        results = adapter.execute_query("SELECT 1 as test")
        print(f"✅ Query executed: {results}")
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False

    # Test placeholder
    print(f"✅ Placeholder: {adapter.placeholder()}")
    print(f"✅ Now function: {adapter.now_function()}")

    return True


if __name__ == "__main__":
    # Test SQLite
    os.environ["DB_TYPE"] = "sqlite"
    print("\n--- Testing SQLite ---")
    sqlite_ok = test_adapter()
    close_database_adapter()  # Clean up between tests

    # Test PostgreSQL
    os.environ["DB_TYPE"] = "postgresql"
    os.environ["POSTGRES_PASSWORD"] = "changeme"  # Match docker-compose
    os.environ["POSTGRES_HOST"] = "localhost"
    os.environ["POSTGRES_PORT"] = "5432"
    os.environ["POSTGRES_DB"] = "tac_webbuilder"
    os.environ["POSTGRES_USER"] = "tac_user"
    print("\n--- Testing PostgreSQL ---")
    postgres_ok = test_adapter()
    close_database_adapter()  # Clean up

    print("\n" + "=" * 50)
    if sqlite_ok and postgres_ok:
        print("✅ Both adapters working!")
        sys.exit(0)
    elif sqlite_ok:
        print("⚠️  SQLite working, PostgreSQL failed")
        print("   (This is expected if Docker is not running)")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)
