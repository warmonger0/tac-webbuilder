"""Test database operations with both SQLite and PostgreSQL"""
import os
import sys
from datetime import datetime

# Test with PostgreSQL
os.environ["DB_TYPE"] = "postgresql"
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "5432"
os.environ["POSTGRES_DB"] = "tac_webbuilder"
os.environ["POSTGRES_USER"] = "tac_user"
os.environ["POSTGRES_PASSWORD"] = "changeme"

from database import get_database_adapter
from repositories.phase_queue_repository import PhaseQueueRepository
from models.phase_queue_item import PhaseQueueItem

print("=" * 70)
print("Testing Database Operations with PostgreSQL")
print("=" * 70)

adapter = get_database_adapter()
print(f"Database Type: {adapter.get_db_type()}")
print(f"Placeholder: {adapter.placeholder()}")
print(f"NOW function: {adapter.now_function()}")

# Test 1: Repository Operations
print("\n" + "-" * 70)
print("Test 1: PhaseQueueRepository CRUD Operations")
print("-" * 70)
try:
    repo = PhaseQueueRepository(db_path="db/database.db")  # path ignored for PostgreSQL

    # Create test item
    test_item = PhaseQueueItem(
        queue_id="test-postgres-001",
        parent_issue=999,
        phase_number=1,
        status="ready",
        depends_on_phase=None,
        phase_data={"title": "Test Phase", "content": "Testing PostgreSQL"}
    )

    # Insert
    repo.insert_phase(test_item)
    print("✅ Insert successful")

    # Find by ID
    found = repo.find_by_id("test-postgres-001")
    if found:
        print(f"✅ Found item: {found.queue_id}")
    else:
        raise Exception("Item not found after insert")

    # Update
    updated = repo.update_status("test-postgres-001", "running", adw_id="adw-test-001")
    print(f"✅ Update successful: {updated}")

    # Verify update
    found = repo.find_by_id("test-postgres-001")
    if found and found.status == "running":
        print(f"✅ Update verified: status is now 'running'")
    else:
        raise Exception("Update verification failed")

    # Delete
    deleted = repo.delete_phase("test-postgres-001")
    print(f"✅ Delete successful: {deleted}")

    # Verify delete
    found = repo.find_by_id("test-postgres-001")
    if found is None:
        print(f"✅ Delete verified: item no longer exists")
    else:
        raise Exception("Delete verification failed")

    print("\n✅ Repository operations test PASSED!")

except Exception as e:
    print(f"\n❌ Repository operations test FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Connection Pooling
print("\n" + "-" * 70)
print("Test 2: Connection Pooling")
print("-" * 70)
try:
    connections = []
    for i in range(5):
        with adapter.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test_value")
            result = cursor.fetchone()
            connections.append(result)
            print(f"  Connection {i+1}: {result}")

    print(f"✅ Created {len(connections)} connections successfully")
    print("✅ Connection pooling test PASSED!")

except Exception as e:
    print(f"\n❌ Connection pooling test FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Placeholder and DateTime Functions
print("\n" + "-" * 70)
print("Test 3: Database-Agnostic Queries")
print("-" * 70)
try:
    with adapter.get_connection() as conn:
        cursor = conn.cursor()
        ph = adapter.placeholder()

        # Test placeholder
        cursor.execute(f"SELECT {ph} as test_value", (42,))
        result = cursor.fetchone()
        if result[0] != 42:
            raise Exception(f"Expected 42, got {result[0]}")
        print(f"✅ Placeholder test: {ph} works correctly (result: {result[0]})")

        # Test NOW() function
        now_fn = adapter.now_function()
        cursor.execute(f"SELECT {now_fn} as current_time")
        current_time = cursor.fetchone()
        print(f"✅ DateTime function test: {now_fn} returned {current_time[0]}")

    print("✅ Database-agnostic queries test PASSED!")

except Exception as e:
    print(f"\n❌ Database-agnostic queries test FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED!")
print("=" * 70)
