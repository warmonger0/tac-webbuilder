"""Benchmark database performance: SQLite vs PostgreSQL"""
import os
import sys
import time
from datetime import datetime

def benchmark_operations(db_type, iterations=100):
    """Benchmark basic operations"""
    # Set environment
    os.environ["DB_TYPE"] = db_type

    if db_type == "postgresql":
        os.environ["POSTGRES_HOST"] = "127.0.0.1"
        os.environ["POSTGRES_PORT"] = "5432"
        os.environ["POSTGRES_DB"] = "tac_webbuilder"
        os.environ["POSTGRES_USER"] = "tac_user"
        os.environ["POSTGRES_PASSWORD"] = "changeme"

    # Force reimport to get correct adapter
    if 'database' in sys.modules:
        del sys.modules['database']
        del sys.modules['database.factory']
        del sys.modules['database.postgres_adapter']
        del sys.modules['database.sqlite_adapter']

    from database import get_database_adapter, close_database_adapter
    from repositories.phase_queue_repository import PhaseQueueRepository
    from models.phase_queue_item import PhaseQueueItem

    adapter = get_database_adapter()
    repo = PhaseQueueRepository()

    print(f"\n{'='*70}")
    print(f"Benchmarking {db_type.upper()}")
    print(f"{'='*70}")

    # Benchmark 1: INSERT
    start = time.time()
    for i in range(iterations):
        item = PhaseQueueItem(
            queue_id=f"bench-{db_type}-{i}",
            parent_issue=1000 + i,
            phase_number=1,
            status="ready",
            depends_on_phase=None,
            phase_data={"title": f"Benchmark {i}", "content": "Performance test"}
        )
        repo.insert_phase(item)
    insert_time = time.time() - start
    print(f"INSERT ({iterations} items): {insert_time:.3f}s ({iterations/insert_time:.1f} ops/sec)")

    # Benchmark 2: SELECT by ID
    start = time.time()
    for i in range(iterations):
        repo.find_by_id(f"bench-{db_type}-{i}")
    select_time = time.time() - start
    print(f"SELECT by ID ({iterations} queries): {select_time:.3f}s ({iterations/select_time:.1f} ops/sec)")

    # Benchmark 3: UPDATE
    start = time.time()
    for i in range(iterations):
        repo.update_status(f"bench-{db_type}-{i}", "completed")
    update_time = time.time() - start
    print(f"UPDATE ({iterations} items): {update_time:.3f}s ({iterations/update_time:.1f} ops/sec)")

    # Benchmark 4: DELETE
    start = time.time()
    for i in range(iterations):
        repo.delete_phase(f"bench-{db_type}-{i}")
    delete_time = time.time() - start
    print(f"DELETE ({iterations} items): {delete_time:.3f}s ({iterations/delete_time:.1f} ops/sec)")

    total_time = insert_time + select_time + update_time + delete_time
    print(f"\nTotal time: {total_time:.3f}s")

    # Clean up
    close_database_adapter()

    return {
        "insert": insert_time,
        "select": select_time,
        "update": update_time,
        "delete": delete_time,
        "total": total_time
    }

print("=" * 70)
print("DATABASE PERFORMANCE BENCHMARK")
print("=" * 70)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Iterations per operation: 100")
print("=" * 70)

try:
    # Run benchmarks
    sqlite_results = benchmark_operations("sqlite", iterations=100)
    postgres_results = benchmark_operations("postgresql", iterations=100)

    # Compare results
    print(f"\n{'='*70}")
    print("PERFORMANCE COMPARISON")
    print(f"{'='*70}")
    print(f"{'Operation':<15} {'SQLite':<15} {'PostgreSQL':<15} {'Winner'}")
    print("-" * 70)

    for op in ["insert", "select", "update", "delete", "total"]:
        sqlite_time = sqlite_results[op]
        postgres_time = postgres_results[op]
        winner = "SQLite" if sqlite_time < postgres_time else "PostgreSQL"
        speedup = max(sqlite_time, postgres_time) / min(sqlite_time, postgres_time)
        print(f"{op.upper():<15} {sqlite_time:>6.3f}s      {postgres_time:>6.3f}s      {winner} ({speedup:.1f}x)")

    print("\n" + "=" * 70)
    print("✅ Benchmark complete!")
    print("=" * 70)

except Exception as e:
    print(f"\n❌ Benchmark failed: {e}")
    import traceback
    traceback.print_exc()
    print("\n💡 Make sure both SQLite and PostgreSQL are available")
    sys.exit(1)
