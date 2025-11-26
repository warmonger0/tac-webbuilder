# PostgreSQL Migration Strategy

## Executive Summary
Migration plan from SQLite to PostgreSQL for production scalability and multi-user concurrency support.

**Timeline:** 2-3 days (19 hours total)
**Risk Level:** High (database migration, potential data loss)
**Rollback Strategy:** Database backups + feature flags + dual-database testing
**Current Database Size:** ~50MB (workflow_history.db)
**Tables to Migrate:** 26 tables
**Code Files Affected:** 23 files (79 get_connection calls)

---

## Current State Analysis

### Database Architecture
- **Primary Database:** `app/server/db/database.db` (444KB)
- **Largest Database:** `app/server/db/workflow_history.db` (50MB)
- **Connection Manager:** `app/server/utils/db_connection.py`
- **Pattern:** Context manager with auto-commit/rollback
- **Tables:** 26 total
- **Indexes:** 41 indexes (including Session 3 optimizations)

### Key Tables
```sql
-- Core workflow tables
adw_locks               -- ADW workflow locking
workflow_history        -- Execution history (50MB - largest)
phase_queue            -- Multi-phase workflow queue
tool_calls             -- Tool usage tracking
operation_patterns     -- Pattern learning
pattern_occurrences    -- Pattern matching
hook_events            -- Hook execution tracking
adw_tools              -- Tool definitions
cost_savings_log       -- Cost optimization tracking
queue_config           -- Queue configuration

-- Test/demo tables
employees, users, products, staff, people, data, etc.
```

### Database Metrics
- **Schema Lines:** 564 lines
- **Files Using SQLite:** 23 Python files
- **Connection Calls:** 79 occurrences
- **Query Placeholders:** 160 `?` placeholders to convert to `%s`
- **AUTOINCREMENT Usage:** 7 files
- **datetime() Functions:** 9 files

---

## Phase 1: Preparation (4 hours)

### 1.1 Schema Translation

**SQLite → PostgreSQL Conversions:**

```sql
-- BEFORE (SQLite)
CREATE TABLE workflow_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    adw_id TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    start_time TEXT,
    end_time TEXT,
    duration_seconds INTEGER
);

-- AFTER (PostgreSQL)
CREATE TABLE workflow_history (
    id BIGSERIAL PRIMARY KEY,
    adw_id VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds INTEGER
);
```

**Type Mapping:**
- `INTEGER PRIMARY KEY AUTOINCREMENT` → `BIGSERIAL PRIMARY KEY`
- `TEXT` → `TEXT` or `VARCHAR(n)` (decide based on usage)
- `TEXT` (dates) → `TIMESTAMP`
- `BLOB` → `BYTEA` (if any)
- `REAL` → `NUMERIC` or `DOUBLE PRECISION`
- `INTEGER` (booleans) → `BOOLEAN`
- `CURRENT_TIMESTAMP` → `NOW()`
- `datetime('now')` → `NOW()`

**Checklist:**
- [ ] Extract full schema: `sqlite3 db/database.db ".schema" > migration/sqlite_schema.sql`
- [ ] Translate to PostgreSQL DDL: `migration/postgres_schema.sql`
- [ ] Convert AUTOINCREMENT to SERIAL/BIGSERIAL
- [ ] Replace datetime('now') with NOW()
- [ ] Add explicit schema (use `public` or `tac_webbuilder`)
- [ ] Preserve all indexes from Session 3:
  - `idx_phase_queue_status`
  - `idx_phase_queue_parent`
  - `idx_phase_queue_issue`
  - `idx_phase_queue_priority`
  - And 37 others...
- [ ] Add PostgreSQL-specific optimizations (see Phase 6)

### 1.2 Connection Management

**Install Dependencies:**
```bash
# PostgreSQL adapter (choose one)
uv add psycopg2-binary  # Recommended (no build required)
# OR
uv add asyncpg          # If going async (future consideration)

# Optional: Connection pooling
# psycopg2 has built-in ThreadedConnectionPool
```

**Configuration:**
```bash
# .env additions
DB_TYPE=postgresql        # or 'sqlite' for rollback
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tac_webbuilder
POSTGRES_USER=tac_user
POSTGRES_PASSWORD=<secure_password>
POSTGRES_POOL_MIN=1
POSTGRES_POOL_MAX=10
POSTGRES_TIMEOUT=30
```

**Docker Compose (for local testing):**
```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: tac_webbuilder
      POSTGRES_USER: tac_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./migration/postgres_schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U tac_user"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

**Checklist:**
- [ ] Add psycopg2-binary to dependencies
- [ ] Create .env.example with PostgreSQL variables
- [ ] Create docker-compose.yml
- [ ] Test PostgreSQL connection
- [ ] Implement connection pool
- [ ] Add health checks
- [ ] Document connection strings

### 1.3 Environment Detection

**Feature Flag Pattern:**
```python
# config.py
import os

DB_TYPE = os.getenv("DB_TYPE", "sqlite")  # Default to sqlite for now

def is_postgres() -> bool:
    return DB_TYPE == "postgresql"

def get_db_config():
    if is_postgres():
        return {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("POSTGRES_DB", "tac_webbuilder"),
            "user": os.getenv("POSTGRES_USER", "tac_user"),
            "password": os.getenv("POSTGRES_PASSWORD"),
            "pool_min": int(os.getenv("POSTGRES_POOL_MIN", "1")),
            "pool_max": int(os.getenv("POSTGRES_POOL_MAX", "10")),
        }
    else:
        return {
            "db_path": "db/database.db"
        }
```

---

## Phase 2: Code Changes (6 hours)

### 2.1 Database Abstraction Layer (3 hours)

**Create:** `app/server/database/` directory structure:

```
app/server/database/
├── __init__.py
├── connection.py        # Abstract base class
├── sqlite_adapter.py    # SQLite implementation
├── postgres_adapter.py  # PostgreSQL implementation
└── factory.py          # Factory to select adapter
```

**Abstract Interface:**
```python
# database/connection.py
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Generator

class DatabaseAdapter(ABC):
    """Abstract database adapter interface"""

    @abstractmethod
    @contextmanager
    def get_connection(self) -> Generator[Any, None, None]:
        """Get database connection context manager"""
        pass

    @abstractmethod
    def execute_query(self, query: str, params: tuple) -> Any:
        """Execute a query and return results"""
        pass

    @abstractmethod
    def placeholder(self) -> str:
        """Return the placeholder character for this database"""
        pass

    @abstractmethod
    def close(self) -> None:
        """Clean up resources (close pools, etc.)"""
        pass
```

**SQLite Adapter:**
```python
# database/sqlite_adapter.py
import sqlite3
import time
from contextlib import contextmanager
from typing import Generator

from .connection import DatabaseAdapter

class SQLiteAdapter(DatabaseAdapter):
    """SQLite database adapter (backward compatible)"""

    def __init__(self, db_path: str = "db/database.db", max_retries: int = 3):
        self.db_path = db_path
        self.max_retries = max_retries
        self.retry_delay = 0.1

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for SQLite connections (from existing db_connection.py)"""
        conn = None
        last_error = None

        # Retry loop for SQLITE_BUSY
        for attempt in range(self.max_retries):
            try:
                conn = sqlite3.connect(str(self.db_path))
                conn.row_factory = sqlite3.Row
                break
            except sqlite3.OperationalError as e:
                last_error = e
                if "locked" in str(e).lower() and attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    raise

        if conn is None:
            raise last_error or sqlite3.OperationalError("Failed to connect")

        try:
            yield conn
        except Exception as e:
            conn.rollback()
            raise e
        else:
            conn.commit()
        finally:
            conn.close()

    def placeholder(self) -> str:
        return "?"

    def close(self) -> None:
        pass  # SQLite doesn't need connection pooling cleanup
```

**PostgreSQL Adapter:**
```python
# database/postgres_adapter.py
import psycopg2
import psycopg2.pool
import psycopg2.extras
from contextlib import contextmanager
from typing import Generator, Dict, Any

from .connection import DatabaseAdapter

class PostgresAdapter(DatabaseAdapter):
    """PostgreSQL database adapter with connection pooling"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize PostgreSQL connection pool.

        Args:
            config: Database configuration dict with keys:
                   host, port, database, user, password, pool_min, pool_max
        """
        self.config = config
        self.pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=config.get("pool_min", 1),
            maxconn=config.get("pool_max", 10),
            host=config["host"],
            port=config["port"],
            database=config["database"],
            user=config["user"],
            password=config["password"],
            cursor_factory=psycopg2.extras.RealDictCursor  # Dict-like rows
        )

    @contextmanager
    def get_connection(self) -> Generator[Any, None, None]:
        """Context manager for PostgreSQL connections with auto-commit/rollback"""
        conn = self.pool.getconn()
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            raise e
        else:
            conn.commit()
        finally:
            self.pool.putconn(conn)

    def placeholder(self) -> str:
        return "%s"  # PostgreSQL uses %s for psycopg2

    def close(self) -> None:
        """Close all connections in the pool"""
        if self.pool:
            self.pool.closeall()
```

**Factory:**
```python
# database/factory.py
import os
from .connection import DatabaseAdapter
from .sqlite_adapter import SQLiteAdapter
from .postgres_adapter import PostgresAdapter

_adapter = None  # Singleton

def get_adapter() -> DatabaseAdapter:
    """
    Get the appropriate database adapter based on environment.

    Returns:
        DatabaseAdapter: SQLite or PostgreSQL adapter
    """
    global _adapter

    if _adapter is not None:
        return _adapter

    db_type = os.getenv("DB_TYPE", "sqlite")

    if db_type == "postgresql":
        config = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("POSTGRES_DB", "tac_webbuilder"),
            "user": os.getenv("POSTGRES_USER", "tac_user"),
            "password": os.getenv("POSTGRES_PASSWORD"),
            "pool_min": int(os.getenv("POSTGRES_POOL_MIN", "1")),
            "pool_max": int(os.getenv("POSTGRES_POOL_MAX", "10")),
        }
        _adapter = PostgresAdapter(config)
    else:
        db_path = os.getenv("SQLITE_DB_PATH", "db/database.db")
        _adapter = SQLiteAdapter(db_path)

    return _adapter

def reset_adapter():
    """Reset the adapter (for testing)"""
    global _adapter
    if _adapter:
        _adapter.close()
    _adapter = None
```

**Checklist:**
- [ ] Create `database/` directory
- [ ] Implement `DatabaseAdapter` abstract class
- [ ] Implement `SQLiteAdapter` (copy from utils/db_connection.py)
- [ ] Implement `PostgresAdapter` with connection pooling
- [ ] Implement `factory.py` with environment detection
- [ ] Add unit tests for each adapter
- [ ] Test connection pool under load

### 2.2 Update Existing Connection Utility (1 hour)

**Backward Compatible Wrapper:**
```python
# utils/db_connection.py (updated)
"""
DEPRECATED: Use database.factory.get_adapter() instead.

This wrapper maintained for backward compatibility during migration.
"""
from contextlib import contextmanager
from database.factory import get_adapter

@contextmanager
def get_connection(db_path: str = "db/database.db", max_retries: int = 3, retry_delay: float = 0.1):
    """
    Legacy wrapper for database connections.

    WARNING: This function is deprecated. Use database.factory.get_adapter() instead.

    This wrapper delegates to the new adapter pattern for backward compatibility.
    The db_path parameter is ignored when DB_TYPE=postgresql.
    """
    adapter = get_adapter()
    with adapter.get_connection() as conn:
        yield conn
```

**Checklist:**
- [ ] Add deprecation warning to `utils/db_connection.py`
- [ ] Update to use factory internally
- [ ] Ensure backward compatibility (no code breaks)

### 2.3 Query Translation (2 hours)

**Placeholder Conversion:**

Find and replace `?` with `%s` in all SQL queries when using PostgreSQL.

**Strategy:**
1. Use adapter.placeholder() in repositories
2. Dynamically build queries based on database type
3. OR: Convert all queries to use %s (psycopg2 style)

**Example Repository Update:**
```python
# repositories/phase_queue_repository.py (BEFORE)
cursor = conn.execute(
    "SELECT * FROM phase_queue WHERE queue_id = ?",
    (queue_id,)
)

# repositories/phase_queue_repository.py (AFTER - Option 1: Dynamic)
from database.factory import get_adapter
adapter = get_adapter()
ph = adapter.placeholder()
cursor = conn.execute(
    f"SELECT * FROM phase_queue WHERE queue_id = {ph}",
    (queue_id,)
)

# AFTER - Option 2: Just use %s (works with both after adapter update)
cursor = conn.execute(
    "SELECT * FROM phase_queue WHERE queue_id = %s",
    (queue_id,)
)
```

**Files to Update (23 files with db_connection imports):**
- `routes/system_routes.py`
- `routes/data_routes.py`
- `routes/issue_completion_routes.py`
- `services/phase_coordination/*.py`
- `services/health_service.py`
- `services/github_issue_service.py`
- `repositories/phase_queue_repository.py`
- `core/workflow_history_utils/database/*.py`
- `core/adw_lock.py`
- `core/sql_processor.py`
- `core/insights.py`
- And 12 more...

**Datetime Function Conversion (9 files):**
```python
# BEFORE (SQLite)
"INSERT INTO table (created_at) VALUES (datetime('now'))"

# AFTER (PostgreSQL compatible)
"INSERT INTO table (created_at) VALUES (NOW())"

# OR use Python datetime (database-agnostic)
from datetime import datetime
created_at = datetime.now().isoformat()
"INSERT INTO table (created_at) VALUES (?)", (created_at,)
```

**Files with datetime() usage:**
- `tests/manual/query_pattern_stats.py`
- `repositories/phase_queue_repository.py`
- `core/pattern_predictor.py`
- `core/adw_lock.py`
- `core/pattern_persistence.py`
- And 4 more...

**Checklist:**
- [ ] Audit all 160 query placeholders
- [ ] Convert `?` → `%s` (or use dynamic placeholders)
- [ ] Replace `datetime('now')` → `NOW()`
- [ ] Test transaction handling (BEGIN/COMMIT/ROLLBACK)
- [ ] Test concurrent transactions
- [ ] Verify LIMIT/OFFSET work (same in both)
- [ ] Test row factory (dict-like access)

---

## Phase 3: Data Migration (2 hours)

### 3.1 Migration Script

**Create:** `scripts/migrate_to_postgres.py`

```python
#!/usr/bin/env python3
"""
Migrate data from SQLite to PostgreSQL with validation.

Usage:
    python scripts/migrate_to_postgres.py --validate  # Dry run
    python scripts/migrate_to_postgres.py --migrate   # Execute migration
"""

import sqlite3
import psycopg2
import psycopg2.extras
import argparse
import sys
from typing import List, Tuple
from datetime import datetime

# Configuration
SQLITE_DB = "db/database.db"
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "tac_webbuilder",
    "user": "tac_user",
    "password": "your_password",  # From environment
}

# Tables to migrate (in dependency order)
TABLES_ORDER = [
    # Core tables first (no dependencies)
    "workflow_history",
    "adw_locks",
    "phase_queue",
    "tool_calls",
    "operation_patterns",
    "pattern_occurrences",
    "hook_events",
    "adw_tools",
    "cost_savings_log",
    "queue_config",
    # Demo/test tables
    "employees", "users", "products", "staff",
    "people", "data", "empty", "large", "special",
    "file0", "file1", "file2", "file3", "file4", "wide",
]

BATCH_SIZE = 1000

def connect_sqlite() -> sqlite3.Connection:
    """Connect to SQLite database"""
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    return conn

def connect_postgres() -> psycopg2.extensions.connection:
    """Connect to PostgreSQL database"""
    return psycopg2.connect(**POSTGRES_CONFIG)

def get_table_columns(sqlite_conn: sqlite3.Connection, table: str) -> List[str]:
    """Get column names for a table"""
    cursor = sqlite_conn.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cursor.fetchall()]

def get_row_count(conn, table: str, is_postgres: bool = False) -> int:
    """Get total row count for a table"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    return cursor.fetchone()[0]

def copy_table_data(
    sqlite_conn: sqlite3.Connection,
    pg_conn: psycopg2.extensions.connection,
    table: str
) -> Tuple[int, int]:
    """
    Copy data from SQLite to PostgreSQL in batches.

    Returns:
        (rows_copied, rows_verified)
    """
    print(f"\n[{table}] Starting migration...")

    # Get table structure
    columns = get_table_columns(sqlite_conn, table)
    total_rows = get_row_count(sqlite_conn, table)

    if total_rows == 0:
        print(f"  [{table}] No data to migrate (empty table)")
        return (0, 0)

    print(f"  [{table}] Total rows: {total_rows:,}")

    # Prepare INSERT statement
    placeholders = ", ".join(["%s"] * len(columns))
    insert_sql = f"""
        INSERT INTO {table} ({', '.join(columns)})
        VALUES ({placeholders})
    """

    # Copy in batches
    offset = 0
    rows_copied = 0

    with pg_conn.cursor() as pg_cursor:
        while offset < total_rows:
            # Fetch batch from SQLite
            select_sql = f"SELECT * FROM {table} LIMIT {BATCH_SIZE} OFFSET {offset}"
            sqlite_cursor = sqlite_conn.execute(select_sql)
            rows = sqlite_cursor.fetchall()

            if not rows:
                break

            # Convert sqlite3.Row to tuples
            rows_data = [tuple(row) for row in rows]

            # Bulk insert into PostgreSQL
            psycopg2.extras.execute_batch(pg_cursor, insert_sql, rows_data, page_size=BATCH_SIZE)
            pg_conn.commit()

            rows_copied += len(rows)
            offset += len(rows)

            progress = (rows_copied / total_rows) * 100
            print(f"  [{table}] Progress: {rows_copied:,}/{total_rows:,} ({progress:.1f}%)")

    # Verify row count
    pg_count = get_row_count(pg_conn, table, is_postgres=True)
    print(f"  [{table}] Migration complete: {rows_copied:,} rows copied, {pg_count:,} rows verified")

    if rows_copied != pg_count:
        print(f"  [WARNING] Row count mismatch! Expected {rows_copied}, got {pg_count}")

    return (rows_copied, pg_count)

def migrate_all_tables(validate_only: bool = False):
    """Migrate all tables from SQLite to PostgreSQL"""
    print("=" * 60)
    print("PostgreSQL Migration Tool")
    print("=" * 60)

    if validate_only:
        print("\n[MODE] Validation only (dry run)")
    else:
        print("\n[MODE] Full migration")

    # Connect to both databases
    print("\n[1] Connecting to databases...")
    sqlite_conn = connect_sqlite()
    pg_conn = connect_postgres()
    print("  ✓ Connected to SQLite")
    print("  ✓ Connected to PostgreSQL")

    # Validate schema exists in PostgreSQL
    print("\n[2] Validating PostgreSQL schema...")
    with pg_conn.cursor() as cursor:
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        pg_tables = {row[0] for row in cursor.fetchall()}

    missing_tables = set(TABLES_ORDER) - pg_tables
    if missing_tables:
        print(f"  ✗ Missing tables in PostgreSQL: {missing_tables}")
        print("  Run schema creation script first!")
        sys.exit(1)

    print(f"  ✓ All {len(TABLES_ORDER)} tables exist in PostgreSQL")

    if validate_only:
        print("\n[3] Validation complete!")
        return

    # Migrate each table
    print("\n[3] Migrating data...")
    total_copied = 0
    total_verified = 0
    failed_tables = []

    for table in TABLES_ORDER:
        try:
            copied, verified = copy_table_data(sqlite_conn, pg_conn, table)
            total_copied += copied
            total_verified += verified

            if copied != verified:
                failed_tables.append(table)

        except Exception as e:
            print(f"  [ERROR] Failed to migrate {table}: {e}")
            failed_tables.append(table)

    # Create indexes
    print("\n[4] Creating indexes...")
    print("  (Indexes created during schema setup)")

    # Run VACUUM ANALYZE
    print("\n[5] Optimizing PostgreSQL...")
    pg_conn.set_isolation_level(0)  # AUTOCOMMIT for VACUUM
    with pg_conn.cursor() as cursor:
        cursor.execute("VACUUM ANALYZE")
    print("  ✓ VACUUM ANALYZE complete")

    # Summary
    print("\n" + "=" * 60)
    print("MIGRATION SUMMARY")
    print("=" * 60)
    print(f"Total rows copied: {total_copied:,}")
    print(f"Total rows verified: {total_verified:,}")

    if failed_tables:
        print(f"\n⚠ FAILED TABLES ({len(failed_tables)}):")
        for table in failed_tables:
            print(f"  - {table}")
    else:
        print("\n✓ All tables migrated successfully!")

    # Cleanup
    sqlite_conn.close()
    pg_conn.close()

def main():
    parser = argparse.ArgumentParser(description="Migrate SQLite to PostgreSQL")
    parser.add_argument("--validate", action="store_true", help="Validate setup (dry run)")
    parser.add_argument("--migrate", action="store_true", help="Execute migration")

    args = parser.parse_args()

    if not (args.validate or args.migrate):
        parser.print_help()
        sys.exit(1)

    migrate_all_tables(validate_only=args.validate)

if __name__ == "__main__":
    main()
```

**Checklist:**
- [ ] Create migration script
- [ ] Test on empty PostgreSQL database
- [ ] Verify batch processing works
- [ ] Test with sample data (10-100 rows)
- [ ] Test with large table (workflow_history - 50MB)
- [ ] Add progress bars (optional: use tqdm)
- [ ] Add error recovery (resume from table N)

### 3.2 Validation Script

**Create:** `scripts/validate_migration.py`

```python
#!/usr/bin/env python3
"""
Validate PostgreSQL migration was successful.

Checks:
- Row counts match
- Sample data matches
- Indexes exist
- Foreign key constraints work
- Query performance is acceptable
"""

import sqlite3
import psycopg2
import hashlib
from typing import List, Dict

def validate_row_counts():
    """Compare row counts for all tables"""
    print("\n[1] Validating row counts...")
    # Implementation...

def validate_sample_data():
    """Compare sample rows from each table"""
    print("\n[2] Validating sample data...")
    # Implementation...

def validate_indexes():
    """Verify all indexes were created"""
    print("\n[3] Validating indexes...")
    # Implementation...

def validate_constraints():
    """Test foreign key constraints"""
    print("\n[4] Validating constraints...")
    # Implementation...

def validate_performance():
    """Compare query performance"""
    print("\n[5] Validating performance...")
    # Run sample queries on both databases
    # Compare execution times
    # Implementation...

if __name__ == "__main__":
    validate_row_counts()
    validate_sample_data()
    validate_indexes()
    validate_constraints()
    validate_performance()
    print("\n✓ All validations passed!")
```

**Checklist:**
- [ ] Create validation script
- [ ] Implement row count checks
- [ ] Implement data integrity checks (checksums)
- [ ] Test foreign key constraints
- [ ] Test unique constraints
- [ ] Run sample queries and compare results

---

## Phase 4: Testing (4 hours)

### 4.1 Dual-Database Testing (2 hours)

**Test Strategy:**
1. Run full test suite against SQLite (baseline)
2. Switch to PostgreSQL (`DB_TYPE=postgresql`)
3. Run same test suite
4. Compare results (should be identical)

**Test Commands:**
```bash
# Baseline (SQLite)
export DB_TYPE=sqlite
cd app/server
uv run pytest --cov --cov-report=term -v > test_results_sqlite.log

# PostgreSQL
export DB_TYPE=postgresql
uv run pytest --cov --cov-report=term -v > test_results_postgres.log

# Compare
diff test_results_sqlite.log test_results_postgres.log
```

**Test Coverage:**
- [ ] All unit tests pass (both databases)
- [ ] All integration tests pass
- [ ] All e2e tests pass
- [ ] Test results are identical
- [ ] Code coverage unchanged (should be same)

### 4.2 Integration Testing (1 hour)

**Full ADW Workflow Test:**
```bash
# Start PostgreSQL backend
export DB_TYPE=postgresql
cd app/server
uv run python server.py

# In another terminal: Run ADW workflow
cd adws
uv run python adw_sdlc_iso.py 123  # Test issue

# Verify:
# - Workflow completes successfully
# - Database records created correctly
# - No connection pool exhaustion
# - No data corruption
```

**Concurrent ADW Test:**
```bash
# Run 5 ADWs simultaneously
for i in {100..104}; do
    uv run python adw_sdlc_iso.py $i &
done
wait

# Verify:
# - All workflows complete
# - No database lock errors
# - Connection pool handles load
# - Data integrity maintained
```

**Checklist:**
- [ ] Single ADW workflow completes
- [ ] Multi-phase workflow works (5+ phases)
- [ ] Concurrent workflows (5 simultaneous)
- [ ] Connection pool stress test (15 concurrent)
- [ ] Large dataset queries (workflow_history - 50MB)
- [ ] Backup/restore procedures tested

### 4.3 Performance Testing (1 hour)

**Benchmark Script:**
```python
# scripts/benchmark_database.py
import time
from database.factory import get_adapter

def benchmark_query(query: str, params: tuple, iterations: int = 100):
    """Run query multiple times and measure performance"""
    adapter = get_adapter()

    times = []
    for _ in range(iterations):
        start = time.time()
        with adapter.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
        duration = time.time() - start
        times.append(duration)

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    return {
        "avg": avg_time,
        "min": min_time,
        "max": max_time,
        "rows": len(results),
    }

# Test queries
queries = [
    ("SELECT * FROM workflow_history WHERE status = %s", ("completed",)),
    ("SELECT * FROM phase_queue WHERE parent_issue = %s", (123,)),
    ("SELECT COUNT(*) FROM tool_calls WHERE workflow_id = %s", ("adw-001",)),
]

for query, params in queries:
    stats = benchmark_query(query, params)
    print(f"Query: {query[:50]}...")
    print(f"  Avg: {stats['avg']*1000:.2f}ms")
    print(f"  Min: {stats['min']*1000:.2f}ms")
    print(f"  Max: {stats['max']*1000:.2f}ms")
    print(f"  Rows: {stats['rows']}")
```

**Expected Results:**
- PostgreSQL should be **similar or faster** than SQLite for most queries
- Concurrent queries: PostgreSQL **much faster** (better locking)
- Large table scans: PostgreSQL **faster** (better query planner)
- Small single-row lookups: Similar (both fast with indexes)

**Checklist:**
- [ ] Benchmark common queries (10-20 queries)
- [ ] Compare SQLite vs PostgreSQL performance
- [ ] Test with realistic data volumes
- [ ] Test concurrent query performance
- [ ] Identify any performance regressions
- [ ] Optimize slow queries (add indexes if needed)

---

## Phase 5: Deployment (2 hours)

### 5.1 Deployment Strategy

**Option A: Big Bang Migration (1 hour downtime)**

**Timeline:**
1. **T-24h:** Announce maintenance window
2. **T-1h:** Stop accepting new workflows
3. **T-0:** Stop application
4. **T+10m:** Backup SQLite database
5. **T+15m:** Run migration script
6. **T+30m:** Validate data
7. **T+35m:** Update config (`DB_TYPE=postgresql`)
8. **T+40m:** Start application
9. **T+50m:** Smoke tests
10. **T+60m:** Monitor for 1 hour

**Pros:**
- Simple and straightforward
- Complete control over migration
- Lower risk of data inconsistency

**Cons:**
- Requires downtime (1 hour)
- All-or-nothing approach

**Option B: Blue-Green Deployment (Zero downtime)**

**Timeline:**
1. **Day 1:** Set up PostgreSQL (green environment)
2. **Day 2:** Initial data sync (historical data)
3. **Day 3:** Continuous replication (read-only queries to PostgreSQL)
4. **Day 4:** Cut over writes to PostgreSQL (5 min downtime)
5. **Day 5-11:** Monitor both databases (PostgreSQL primary, SQLite backup)
6. **Day 12:** Deprecate SQLite

**Pros:**
- Minimal downtime (5 minutes for cutover)
- Can test PostgreSQL in production with read-only queries
- Easy rollback (just switch back)

**Cons:**
- More complex setup
- Requires replication mechanism
- Longer timeline (1-2 weeks)

**Recommendation:**
- **Development/Staging:** Option A (big bang)
- **Production:** Option B (blue-green) if >100 active users

### 5.2 Rollback Plan

**Immediate Rollback (< 5 minutes):**
```bash
# 1. Stop application
sudo systemctl stop tac-webbuilder

# 2. Switch back to SQLite
export DB_TYPE=sqlite
# Update .env file
sed -i 's/DB_TYPE=postgresql/DB_TYPE=sqlite/' .env

# 3. Restart application
sudo systemctl start tac-webbuilder

# 4. Verify
curl http://localhost:8000/health
```

**Rollback Conditions:**
- Error rate > 5% (baseline: < 0.1%)
- Response time > 2x baseline
- Database connection errors
- Data corruption detected
- Any critical bug in PostgreSQL adapter

**Post-Rollback:**
- Keep PostgreSQL running (investigate offline)
- Collect logs and error reports
- Fix issues and plan retry
- Communicate with team

**Checklist:**
- [ ] Document rollback procedure
- [ ] Test rollback in staging
- [ ] Define rollback triggers (error thresholds)
- [ ] Assign rollback decision-maker
- [ ] Have SQLite backup accessible (keep for 30 days)

### 5.3 Monitoring

**Metrics to Track:**

**Database Performance:**
- Query latency (p50, p95, p99)
- Slow query count (> 100ms)
- Connection pool utilization
- Connection errors
- Transaction rollback rate

**Application Health:**
- Request error rate
- Request latency
- ADW workflow success rate
- Background job completion rate

**PostgreSQL-Specific:**
- Active connections
- Idle connections
- Lock waits
- Deadlocks
- Table bloat
- Index usage

**Monitoring Tools:**
```bash
# PostgreSQL stats
psql -U tac_user -d tac_webbuilder -c "
    SELECT * FROM pg_stat_activity
    WHERE datname = 'tac_webbuilder'
"

# Slow query log (enable in postgresql.conf)
log_min_duration_statement = 100  # Log queries > 100ms

# Connection pool stats (in application)
# Log pool size every 60 seconds
```

**Alerts:**
- Connection pool exhausted (> 90% utilization)
- Slow queries (> 500ms)
- Error rate spike (> 1%)
- Database unreachable

**Checklist:**
- [ ] Set up database monitoring
- [ ] Configure slow query log
- [ ] Add application metrics (latency, errors)
- [ ] Create dashboards (Grafana/similar)
- [ ] Set up alerts (email/Slack)
- [ ] Document monitoring procedures

---

## Phase 6: Post-Migration Optimization (1 hour)

### 6.1 PostgreSQL Optimization

**VACUUM and ANALYZE:**
```sql
-- After initial data load
VACUUM ANALYZE;

-- Schedule regular VACUUM (usually automatic, but verify)
-- Check autovacuum settings in postgresql.conf
```

**Query Plan Analysis:**
```sql
-- Check query plans for common queries
EXPLAIN ANALYZE
SELECT * FROM workflow_history
WHERE status = 'completed'
ORDER BY created_at DESC
LIMIT 10;

-- Look for:
-- - Sequential Scans (bad) vs Index Scans (good)
-- - High cost estimates
-- - Slow execution time
```

**Additional Indexes (if needed):**
```sql
-- Example: If queries filtering by model + status are slow
CREATE INDEX idx_workflow_history_model_status
ON workflow_history(model_used, status);

-- Composite index for common query patterns
CREATE INDEX idx_phase_queue_status_priority
ON phase_queue(status, priority DESC);

-- Partial index for active workflows only
CREATE INDEX idx_workflow_history_active
ON workflow_history(status, created_at)
WHERE status IN ('pending', 'running');
```

**Connection Pooling (PgBouncer - Optional):**
```bash
# If connection pool exhaustion occurs
sudo apt-get install pgbouncer

# Configure pgbouncer
# /etc/pgbouncer/pgbouncer.ini
[databases]
tac_webbuilder = host=localhost port=5432 dbname=tac_webbuilder

[pgbouncer]
pool_mode = transaction
max_client_conn = 100
default_pool_size = 20

# Use pgbouncer port in application (6432 instead of 5432)
```

**Autovacuum Tuning:**
```sql
-- Check current settings
SHOW autovacuum;

-- Tune for heavy write workload (if needed)
ALTER TABLE workflow_history SET (
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);
```

**Checklist:**
- [ ] Run initial VACUUM ANALYZE
- [ ] Review query plans for top 10 queries
- [ ] Add missing indexes (if any)
- [ ] Configure autovacuum (if heavy writes)
- [ ] Consider PgBouncer (if connection issues)
- [ ] Set up pg_stat_statements (query stats)

### 6.2 Documentation

**Update Files:**

1. **README.md:**
```markdown
## Database Setup

### PostgreSQL (Production)
docker-compose up -d postgres
python scripts/migrate_to_postgres.py --migrate

### SQLite (Development)
export DB_TYPE=sqlite
# Database auto-created on first run
```

2. **DEPLOYMENT.md:**
```markdown
## Database Migration

See docs/postgresql_migration_plan.md for full migration strategy.

### Quick Start
1. Set up PostgreSQL: `docker-compose up -d postgres`
2. Create schema: `psql < migration/postgres_schema.sql`
3. Migrate data: `python scripts/migrate_to_postgres.py --migrate`
4. Validate: `python scripts/validate_migration.py`
5. Update .env: `DB_TYPE=postgresql`
6. Restart: `sudo systemctl restart tac-webbuilder`
```

3. **.env.example:**
```bash
# Database Configuration
DB_TYPE=sqlite  # or 'postgresql'

# PostgreSQL (only if DB_TYPE=postgresql)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tac_webbuilder
POSTGRES_USER=tac_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_POOL_MIN=1
POSTGRES_POOL_MAX=10
```

4. **docs/database/BACKUP_PROCEDURES.md:**
```markdown
## PostgreSQL Backups

### Daily Backup
pg_dump -U tac_user -d tac_webbuilder -F c -f backup_$(date +%Y%m%d).dump

### Restore
pg_restore -U tac_user -d tac_webbuilder -c backup_20250101.dump

### Automated Backups
# Add to crontab
0 2 * * * /usr/local/bin/backup_postgres.sh
```

**Checklist:**
- [ ] Update README.md with PostgreSQL setup
- [ ] Create DEPLOYMENT.md with migration steps
- [ ] Update .env.example
- [ ] Document backup procedures
- [ ] Document restore procedures
- [ ] Create runbook for common issues
- [ ] Update developer onboarding guide

---

## Risk Assessment

### High Risk Areas

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Data Loss** | Low | Critical | • Multiple backups before migration<br>• Validation script<br>• Keep SQLite for 30 days |
| **Downtime** | Medium | High | • Practice migration in staging<br>• Have rollback ready<br>• Use blue-green if critical |
| **Performance Regression** | Low | Medium | • Benchmark before/after<br>• Add indexes as needed<br>• Query optimization |
| **Connection Pool Exhaustion** | Medium | Medium | • Load test with 15 concurrent ADWs<br>• Monitor pool utilization<br>• Use PgBouncer if needed |
| **Data Corruption** | Very Low | Critical | • Transaction management<br>• Foreign key constraints<br>• Validation checks |
| **Cost Overrun** | Low | Low | • Use free tier (AWS RDS, DigitalOcean)<br>• Or self-hosted (Docker) |

### Compatibility Concerns

1. **Query Syntax:**
   - SQLite: `?` placeholders → PostgreSQL: `%s` placeholders
   - **Mitigation:** Database abstraction layer handles this

2. **Data Types:**
   - SQLite: TEXT for dates → PostgreSQL: TIMESTAMP
   - **Mitigation:** Schema translation in Phase 1

3. **Transaction Isolation:**
   - SQLite: Serializable → PostgreSQL: Read Committed (default)
   - **Mitigation:** Explicitly set isolation level if needed

4. **Concurrency:**
   - SQLite: Database-level locking → PostgreSQL: Row-level locking
   - **Impact:** Better concurrency in PostgreSQL (positive!)

5. **Date/Time Handling:**
   - SQLite: Strings → PostgreSQL: Native types
   - **Mitigation:** Use Python datetime objects (database-agnostic)

---

## Timeline Summary

| Phase | Tasks | Duration | Can Parallelize? | Dependencies |
|-------|-------|----------|------------------|--------------|
| **1. Preparation** | Schema translation, connection setup, config | 4 hours | Partially | None |
| **2. Code Changes** | Abstraction layer, query updates | 6 hours | Partially | Phase 1 |
| **3. Data Migration** | Migration script, validation | 2 hours | No | Phase 1, 2 |
| **4. Testing** | Dual-DB testing, integration, performance | 4 hours | Partially | Phase 3 |
| **5. Deployment** | Deploy, monitor, rollback plan | 2 hours | No | Phase 4 |
| **6. Post-Migration** | Optimization, documentation | 1 hour | Partially | Phase 5 |
| **TOTAL** | | **19 hours** | | **2-3 days** |

**Parallelization Opportunities:**
- Phase 1 & 2: Schema translation (1.1) can overlap with abstraction layer (2.1)
- Phase 4: Different tests can run concurrently
- Phase 6: Documentation while monitoring deployment

**Critical Path:**
1. Schema translation (1.1) → 2 hours
2. Abstraction layer (2.1) → 3 hours
3. Query updates (2.3) → 2 hours
4. Migration script (3.1) → 1 hour
5. Execution + validation (3.2) → 1 hour
6. Testing (4) → 4 hours
7. Deployment (5) → 2 hours

**Minimum Timeline:** ~15 hours (with aggressive parallelization)

---

## Cost/Benefit Analysis

### Benefits

**Scalability:**
- Support for 1000s of concurrent users (vs 10s with SQLite)
- No database locking issues with concurrent ADWs
- Better handling of long-running transactions
- Can scale vertically (bigger server) or horizontally (replication)

**Performance:**
- Row-level locking (vs database-level in SQLite)
- Better query optimizer for complex joins
- Parallel query execution (PostgreSQL 14+)
- Concurrent writes without blocking reads

**Features:**
- Full ACID compliance with tunable isolation levels
- Advanced indexing (GIN, GiST, BRIN)
- Partitioning for large tables (workflow_history - 50MB and growing)
- Full-text search (better than SQLite FTS)
- JSON operations (if using JSON columns)
- Triggers, views, stored procedures

**Operational:**
- Industry-standard database (easier to hire DBAs)
- Better monitoring tools (pg_stat_*, pgAdmin, Datadog)
- Point-in-time recovery (PITR)
- Streaming replication for high availability
- Proven at enterprise scale

**Developer Experience:**
- Better error messages
- Rich ecosystem of tools
- More Stack Overflow answers
- Better ORM support (if migrating to SQLAlchemy later)

### Costs

**Development:**
- 19 hours implementation time (~2-3 days)
- Testing and validation time
- Team training on PostgreSQL
- Documentation updates

**Infrastructure:**
- **Self-Hosted (Docker):** $0 (already have server)
- **AWS RDS (db.t4g.micro):** $13/month (free tier available)
- **DigitalOcean Managed:** $15/month
- **Google Cloud SQL (db-f1-micro):** $10/month
- **Azure Database:** $12/month

**Operational:**
- Backup storage costs (~$1-5/month)
- Monitoring tools (optional: Datadog $15-31/month)
- Additional complexity in deployment
- Need PostgreSQL expertise on team

**Total Cost (Year 1):**
- Development: 19 hours × $100/hour = $1,900 (one-time)
- Hosting: $15/month × 12 = $180/year
- **Total:** ~$2,100 first year, ~$180/year after

### When to Migrate?

**Migrate NOW if:**
- ✅ Planning production deployment
- ✅ Expecting >10 concurrent ADW workflows
- ✅ Database size growing rapidly (>1GB)
- ✅ Experiencing SQLite locking issues
- ✅ Need better concurrency
- ✅ Want advanced PostgreSQL features

**Defer if:**
- ❌ Still in early development/prototyping
- ❌ Single-user or low concurrency (<5 concurrent users)
- ❌ Database small (<100MB)
- ❌ SQLite working fine
- ❌ Other higher-priority features needed

**Recommendation:**
- Migrate when planning **production deployment** or when **concurrent ADW workflows > 5**
- Current state (50MB workflow_history.db) suggests migration is **justified**
- Implementation should happen **before** production launch

---

## Pre-Migration Checklist

- [ ] Full database backup created (all .db files)
- [ ] PostgreSQL server provisioned (local Docker or cloud)
- [ ] Database abstraction layer implemented and tested
- [ ] All unit tests passing on SQLite (baseline)
- [ ] Migration script tested on copy of data
- [ ] Validation script created
- [ ] Rollback procedure documented and tested
- [ ] Team notified of migration schedule
- [ ] Monitoring dashboards ready
- [ ] Rollback conditions defined
  - Error rate > 5%
  - Latency > 2x baseline
  - Connection errors
- [ ] Backup retention policy defined (30 days)

---

## Migration Day Checklist

- [ ] Announce maintenance window (if using big bang)
- [ ] Create final SQLite backup
  ```bash
  mkdir -p db/backups/pre_postgres_$(date +%Y%m%d)
  cp -r db/*.db db/backups/pre_postgres_$(date +%Y%m%d)/
  ```
- [ ] Stop application (if using big bang)
  ```bash
  sudo systemctl stop tac-webbuilder
  ```
- [ ] Run migration script
  ```bash
  python scripts/migrate_to_postgres.py --migrate
  ```
- [ ] Validate data integrity
  ```bash
  python scripts/validate_migration.py
  ```
- [ ] Update configuration
  ```bash
  # .env
  DB_TYPE=postgresql
  ```
- [ ] Start application
  ```bash
  sudo systemctl start tac-webbuilder
  ```
- [ ] Run smoke tests
  ```bash
  curl http://localhost:8000/health
  curl http://localhost:8000/api/v1/workflows
  ```
- [ ] Monitor error rates for 1 hour
  ```bash
  # Watch logs
  tail -f logs/tac-webbuilder.log | grep ERROR

  # Check PostgreSQL connections
  psql -U tac_user -d tac_webbuilder -c "SELECT count(*) FROM pg_stat_activity"
  ```
- [ ] Run sample ADW workflow (end-to-end test)
  ```bash
  cd adws
  uv run python adw_sdlc_iso.py 999  # Test issue
  ```
- [ ] Declare success or rollback
  - If error rate < 1% and tests pass: **SUCCESS**
  - Otherwise: **ROLLBACK** (see rollback plan)

---

## Post-Migration Checklist

- [ ] Run VACUUM ANALYZE
  ```sql
  VACUUM ANALYZE;
  ```
- [ ] Verify all indexes created
  ```sql
  SELECT tablename, indexname
  FROM pg_indexes
  WHERE schemaname = 'public'
  ORDER BY tablename, indexname;
  ```
- [ ] Check query performance
  ```bash
  python scripts/benchmark_database.py > benchmark_postgres.log
  # Compare with baseline: benchmark_sqlite.log
  ```
- [ ] Update documentation
  - [ ] README.md (database setup)
  - [ ] DEPLOYMENT.md (migration guide)
  - [ ] .env.example (PostgreSQL variables)
  - [ ] docs/database/BACKUP_PROCEDURES.md
- [ ] Archive SQLite database
  ```bash
  # Keep for 30 days, then delete
  tar -czf db_sqlite_backup_$(date +%Y%m%d).tar.gz db/*.db
  mv db_sqlite_backup_*.tar.gz db/backups/
  ```
- [ ] Schedule follow-up review (1 week)
  - Review performance metrics
  - Check for any issues
  - Optimize queries if needed
  - Consider removing SQLite dependency (after 30 days)

---

## Next Steps

### Immediate (Before Migration)
1. **Review this plan** with the team
2. **Test migration** in development environment
3. **Create backup strategy** (automated backups)
4. **Schedule migration date** (coordinate with users)

### Short-term (After Migration)
1. **Monitor performance** for 1 week
2. **Optimize queries** based on slow query log
3. **Document lessons learned**
4. **Remove SQLite adapter** (after 30 days if no issues)

### Long-term (Ongoing)
1. **Set up replication** (if high availability needed)
2. **Implement partitioning** for large tables (workflow_history)
3. **Consider read replicas** (if read-heavy workload)
4. **Evaluate PostgreSQL 16** features (parallel query improvements)

---

## Appendix A: Schema Translation Example

### SQLite (Current)
```sql
CREATE TABLE phase_queue (
    queue_id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_issue INTEGER,
    phase_number INTEGER,
    status TEXT CHECK(status IN ('pending', 'ready', 'running', 'completed', 'failed')),
    depends_on_phase INTEGER,
    phase_data TEXT,  -- JSON
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    priority INTEGER DEFAULT 50,
    queue_position INTEGER NOT NULL,
    ready_timestamp TEXT,
    UNIQUE(queue_id)
);

-- Indexes from Session 3
CREATE INDEX idx_phase_queue_status ON phase_queue(status);
CREATE INDEX idx_phase_queue_parent ON phase_queue(parent_issue);
CREATE INDEX idx_phase_queue_issue ON phase_queue(parent_issue, status);
CREATE INDEX idx_phase_queue_priority ON phase_queue(status, priority DESC, queue_position ASC);
```

### PostgreSQL (Target)
```sql
CREATE TABLE phase_queue (
    queue_id BIGSERIAL PRIMARY KEY,  -- AUTOINCREMENT → BIGSERIAL
    parent_issue INTEGER,
    phase_number INTEGER,
    status VARCHAR(20) CHECK(status IN ('pending', 'ready', 'running', 'completed', 'failed')),
    depends_on_phase INTEGER,
    phase_data JSONB,  -- Better than TEXT for JSON
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),  -- TEXT → TIMESTAMP
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    priority INTEGER DEFAULT 50,
    queue_position INTEGER NOT NULL,
    ready_timestamp TIMESTAMP,  -- TEXT → TIMESTAMP
    CONSTRAINT queue_id_unique UNIQUE(queue_id)
);

-- Indexes (preserved from Session 3)
CREATE INDEX idx_phase_queue_status ON phase_queue(status);
CREATE INDEX idx_phase_queue_parent ON phase_queue(parent_issue);
CREATE INDEX idx_phase_queue_issue ON phase_queue(parent_issue, status);
CREATE INDEX idx_phase_queue_priority ON phase_queue(status, priority DESC, queue_position ASC);

-- Additional PostgreSQL optimizations
CREATE INDEX idx_phase_queue_jsonb ON phase_queue USING GIN (phase_data);  -- For JSON queries
```

### Workflow History (Largest Table)
```sql
-- SQLite
CREATE TABLE workflow_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    adw_id TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- ... 40+ columns
);

-- PostgreSQL (with partitioning for 50MB+ table)
CREATE TABLE workflow_history (
    id BIGSERIAL,
    adw_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    -- ... 40+ columns
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE workflow_history_2024_11 PARTITION OF workflow_history
    FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');

CREATE TABLE workflow_history_2024_12 PARTITION OF workflow_history
    FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');

-- Auto-create future partitions with pg_partman extension (optional)
```

---

## Appendix B: Database Abstraction Layer Example

### Repository Before (SQLite-only)
```python
# repositories/phase_queue_repository.py (BEFORE)
import sqlite3
from utils.db_connection import get_connection

class PhaseQueueRepository:
    def __init__(self, db_path: str = "db/database.db"):
        self.db_path = db_path

    def find_by_id(self, queue_id: str):
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM phase_queue WHERE queue_id = ?",  # SQLite placeholder
                (queue_id,)
            )
            row = cursor.fetchone()
        return PhaseQueueItem.from_db_row(row) if row else None
```

### Repository After (Database-Agnostic)
```python
# repositories/phase_queue_repository.py (AFTER)
from database.factory import get_adapter

class PhaseQueueRepository:
    def __init__(self):
        self.adapter = get_adapter()  # Auto-detects SQLite or PostgreSQL

    def find_by_id(self, queue_id: str):
        # Placeholder automatically handled by adapter
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM phase_queue WHERE queue_id = %s",  # Works with both
                (queue_id,)
            )
            row = cursor.fetchone()

        # Row factory (dict-like access) works with both adapters
        return PhaseQueueItem.from_db_row(row) if row else None
```

### Usage (No Changes Required)
```python
# Application code (unchanged)
from repositories.phase_queue_repository import PhaseQueueRepository

repo = PhaseQueueRepository()
phase = repo.find_by_id("adw-001-phase-1")
```

---

## Appendix C: Performance Comparison

### Expected Performance Changes

| Operation | SQLite | PostgreSQL | Change | Why |
|-----------|--------|------------|--------|-----|
| **Single row lookup (indexed)** | 0.5ms | 0.5ms | No change | Both fast with indexes |
| **Single row insert** | 1ms | 1ms | No change | Both fast |
| **100 row insert (transaction)** | 10ms | 8ms | +20% faster | Better batch handling |
| **1000 row table scan** | 15ms | 12ms | +20% faster | Better query planner |
| **Complex JOIN (3 tables)** | 50ms | 30ms | +40% faster | Better optimizer |
| **Concurrent reads (10 users)** | 100ms | 20ms | **5x faster** | Row-level locking |
| **Concurrent writes (5 users)** | 500ms | 50ms | **10x faster** | No database lock |
| **Full table scan (50MB)** | 2000ms | 1500ms | +25% faster | Parallel scan |

### Real-World Example: ADW Workflow
```
Scenario: 5 concurrent ADW workflows, each with 10 database operations

SQLite:
- Database-level locking forces serialization
- Total time: 5 × (10 × 5ms) = 250ms
- Frequent SQLITE_BUSY errors (mitigated by retry logic)

PostgreSQL:
- Row-level locking allows parallelization
- Total time: 10 × 5ms = 50ms (parallelized)
- No locking errors
- 5x faster for concurrent workloads
```

---

## Appendix D: Troubleshooting Guide

### Issue: Migration Script Fails with "Table not found"
**Cause:** PostgreSQL schema not created
**Fix:**
```bash
# Create schema first
psql -U tac_user -d tac_webbuilder < migration/postgres_schema.sql

# Then retry migration
python scripts/migrate_to_postgres.py --migrate
```

### Issue: Row count mismatch after migration
**Cause:** Migration interrupted or transaction not committed
**Fix:**
```bash
# Check actual row counts
sqlite3 db/database.db "SELECT COUNT(*) FROM workflow_history"
psql -U tac_user -d tac_webbuilder -c "SELECT COUNT(*) FROM workflow_history"

# If mismatch: re-run migration for that table
python scripts/migrate_table.py workflow_history
```

### Issue: Connection pool exhausted errors
**Cause:** Too many concurrent connections
**Fix:**
```python
# Increase pool size in .env
POSTGRES_POOL_MAX=20  # Increase from 10

# Or install PgBouncer for connection pooling
sudo apt-get install pgbouncer
```

### Issue: Queries slower on PostgreSQL
**Cause:** Missing indexes or outdated statistics
**Fix:**
```sql
-- Update statistics
ANALYZE workflow_history;

-- Check if indexes are being used
EXPLAIN ANALYZE SELECT * FROM workflow_history WHERE status = 'completed';

-- If Sequential Scan: add index
CREATE INDEX idx_workflow_history_status ON workflow_history(status);
```

### Issue: "psycopg2.OperationalError: FATAL: password authentication failed"
**Cause:** Wrong credentials or PostgreSQL authentication config
**Fix:**
```bash
# Check credentials in .env
echo $POSTGRES_PASSWORD

# Reset PostgreSQL password
psql -U postgres
ALTER USER tac_user WITH PASSWORD 'new_password';

# Update pg_hba.conf if needed (local trust vs md5)
sudo nano /etc/postgresql/15/main/pg_hba.conf
```

### Issue: Tests fail on PostgreSQL but pass on SQLite
**Cause:** Different transaction isolation or type handling
**Fix:**
```python
# Explicit transaction isolation (if needed)
with adapter.get_connection() as conn:
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)
    # ... your test code

# Or: Fix test assumptions about data types (TEXT vs TIMESTAMP)
```

---

## Appendix E: References

### Documentation
- [PostgreSQL Official Docs](https://www.postgresql.org/docs/)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)
- [SQLite → PostgreSQL Migration](https://wiki.postgresql.org/wiki/Converting_from_other_Databases_to_PostgreSQL)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)

### Tools
- [pgAdmin](https://www.pgadmin.org/) - PostgreSQL GUI
- [DBeaver](https://dbeaver.io/) - Universal database tool
- [PgBouncer](https://www.pgbouncer.org/) - Connection pooling
- [pg_stat_statements](https://www.postgresql.org/docs/current/pgstatstatements.html) - Query statistics

### Migration Tools
- [pgloader](https://pgloader.io/) - Fast data loading (alternative to custom script)
- [pg_dump/pg_restore](https://www.postgresql.org/docs/current/backup-dump.html) - Backup/restore
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM (future consideration)

### Monitoring
- [pg_stat_activity](https://www.postgresql.org/docs/current/monitoring-stats.html) - Active connections
- [pg_stat_statements](https://www.postgresql.org/docs/current/pgstatstatements.html) - Query stats
- [Datadog PostgreSQL Integration](https://docs.datadoghq.com/integrations/postgres/)

---

**End of Migration Plan**

*This document should be reviewed and updated as the codebase evolves. Last updated: 2025-11-26*
