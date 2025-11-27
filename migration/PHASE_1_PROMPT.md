# Task: PostgreSQL Migration - Phase 1: Setup & Preparation

## Context
I'm working on the tac-webbuilder project. We're migrating from SQLite to PostgreSQL for production scalability and multi-user concurrency support. This is **Phase 1 of 6** (4 hours of 19 total).

## Objective
Set up PostgreSQL environment, extract and translate schemas, create database abstraction layer, and verify everything works before making code changes.

## Background Information
- **Current State:** Using SQLite (2 databases)
  - `db/database.db` (444KB) - Main application data
  - `db/workflow_history.db` (50MB) - Largest database
- **Target:** PostgreSQL 15+ with unified schema
- **Tables to Migrate:** 26 tables
- **Indexes:** 41 indexes (including Session 3 optimizations)
- **Views:** 4 views
- **Triggers:** 4 triggers
- **Risk Level:** High (database migration) - mitigated with backups + rollback plan
- **Estimated Time:** 4 hours

## Step-by-Step Instructions

### Step 1: Create Migration Directory

```bash
cd /Users/Warmonger0/tac/tac-webbuilder
mkdir -p migration
cd migration
```

### Step 2: Extract SQLite Schemas

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Extract schema from database.db
sqlite3 db/database.db ".schema" > ../../migration/sqlite_schema_database.sql

# Extract schema from workflow_history.db
sqlite3 db/workflow_history.db ".schema" > ../../migration/sqlite_schema_workflow_history.sql

# Verify extraction
wc -l ../../migration/sqlite_schema_*.sql
```

**Expected:** Should see ~565 lines for database.db, ~420 lines for workflow_history.db

### Step 3: Count Tables and Indexes

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/migration

# Count tables
grep "CREATE TABLE" sqlite_schema_*.sql | wc -l

# Count indexes
grep "CREATE INDEX" sqlite_schema_*.sql | wc -l

# Count views
grep "CREATE VIEW" sqlite_schema_*.sql | wc -l

# Count triggers
grep "CREATE TRIGGER" sqlite_schema_*.sql | wc -l
```

**Expected:** 26 tables, 41+ indexes, 4 views, 4 triggers

### Step 4: Create PostgreSQL Schema

Create `migration/postgres_schema.sql` with the translated schema.

**Key Translations:**
- `INTEGER PRIMARY KEY AUTOINCREMENT` → `BIGSERIAL PRIMARY KEY`
- `TEXT` (for dates) → `TIMESTAMP WITHOUT TIME ZONE`
- `TEXT` (for JSON) → `JSONB`
- `INTEGER` (for booleans) → `BOOLEAN`
- `REAL` (for money) → `NUMERIC(10,4)`
- `REAL` (for floats) → `DOUBLE PRECISION`
- `datetime('now')` → `NOW()`
- `CURRENT_TIMESTAMP` → `CURRENT_TIMESTAMP` (same)

**Important Tables to Translate:**
1. `workflow_history` (largest - 50MB, main table)
2. `phase_queue` (multi-phase workflows)
3. `tool_calls` (cost tracking)
4. `operation_patterns` (pattern learning)
5. `hook_events` (event tracking)
6. `adw_tools` (tool registry)
7. `cost_savings_log` (savings tracking)

**PostgreSQL-Specific Enhancements:**
```sql
-- Use JSONB instead of TEXT for JSON columns
structured_input JSONB,  -- Better performance than TEXT
cost_breakdown JSONB,
token_breakdown JSONB,

-- Proper foreign keys with CASCADE
FOREIGN KEY (workflow_id) REFERENCES workflow_history(workflow_id) ON DELETE CASCADE

-- Triggers use functions in PostgreSQL
CREATE OR REPLACE FUNCTION trigger_update_pattern_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_pattern_timestamp
BEFORE UPDATE ON operation_patterns
FOR EACH ROW
EXECUTE FUNCTION trigger_update_pattern_timestamp();
```

**Full schema template:** See migration plan doc for complete 858-line schema

### Step 5: Create Docker Compose

Create `docker-compose.yml` in project root:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: tac-webbuilder-postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-tac_webbuilder}
      POSTGRES_USER: ${POSTGRES_USER:-tac_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./migration/postgres_schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-tac_user}"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
```

### Step 6: Update .env.sample

Add PostgreSQL configuration to `.env.sample`:

```bash
# -----------------------------------------------------------------------------
# DATABASE CONFIGURATION
# -----------------------------------------------------------------------------
# (Optional) Database type: sqlite or postgresql
# Default: sqlite (for backward compatibility)
DB_TYPE=sqlite

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tac_webbuilder
POSTGRES_USER=tac_user
POSTGRES_PASSWORD=changeme_secure_password_here
POSTGRES_POOL_MIN=1
POSTGRES_POOL_MAX=10
POSTGRES_TIMEOUT=30
```

### Step 7: Install psycopg2

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server
uv add psycopg2-binary
```

**Expected:** Should install psycopg2-binary==2.9.11

### Step 8: Create Database Abstraction Layer

Create `app/server/database/` directory structure:

```bash
mkdir -p app/server/database
touch app/server/database/__init__.py
touch app/server/database/connection.py
touch app/server/database/sqlite_adapter.py
touch app/server/database/postgres_adapter.py
touch app/server/database/factory.py
```

**File 1: `database/connection.py`** (Abstract Interface)

```python
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Generator, Optional

class DatabaseAdapter(ABC):
    """Abstract database adapter interface"""

    @abstractmethod
    @contextmanager
    def get_connection(self) -> Generator[Any, None, None]:
        pass

    @abstractmethod
    def placeholder(self) -> str:
        """'?' for SQLite, '%s' for PostgreSQL"""
        pass

    @abstractmethod
    def now_function(self) -> str:
        """datetime('now') for SQLite, NOW() for PostgreSQL"""
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    @abstractmethod
    def health_check(self) -> bool:
        pass

    @abstractmethod
    def get_db_type(self) -> str:
        pass
```

**File 2: `database/sqlite_adapter.py`** (Backward Compatible)

Copy existing logic from `utils/db_connection.py` into adapter pattern.

**File 3: `database/postgres_adapter.py`** (New)

```python
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import os

class PostgreSQLAdapter(DatabaseAdapter):
    def __init__(self):
        self.pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=int(os.getenv("POSTGRES_POOL_MIN", "1")),
            maxconn=int(os.getenv("POSTGRES_POOL_MAX", "10")),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "tac_webbuilder"),
            user=os.getenv("POSTGRES_USER", "tac_user"),
            password=os.getenv("POSTGRES_PASSWORD"),
            cursor_factory=RealDictCursor
        )

    def placeholder(self) -> str:
        return "%s"

    def now_function(self) -> str:
        return "NOW()"

    # ... implement all abstract methods
```

**File 4: `database/factory.py`** (Adapter Factory)

```python
import os
from .sqlite_adapter import SQLiteAdapter
from .postgres_adapter import PostgreSQLAdapter

_adapter = None

def get_database_adapter():
    global _adapter
    if _adapter is None:
        db_type = os.getenv("DB_TYPE", "sqlite").lower()
        _adapter = PostgreSQLAdapter() if db_type == "postgresql" else SQLiteAdapter()
    return _adapter
```

### Step 9: Start PostgreSQL

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

# Start PostgreSQL (schema auto-loads)
docker-compose up -d postgres

# Check status
docker-compose ps

# View logs
docker-compose logs postgres | tail -20
```

**Expected:** "database system is ready to accept connections"

### Step 10: Test PostgreSQL Connection

```bash
# Direct connection test
docker-compose exec postgres psql -U tac_user -d tac_webbuilder -c "SELECT version();"

# Count tables
docker-compose exec postgres psql -U tac_user -d tac_webbuilder -c "\dt" | grep "public |" | wc -l

# Should show 26 tables
```

### Step 11: Create Test Script

Create `migration/test_adapters.py`:

```python
import os
import sys
sys.path.insert(0, "../app/server")

from database import get_database_adapter

def test_adapter():
    adapter = get_database_adapter()
    print(f"Testing {adapter.get_db_type()}...")

    if adapter.health_check():
        print(f"✅ Health check passed")
    else:
        print(f"❌ Health check failed")
        return False

    print(f"✅ Placeholder: {adapter.placeholder()}")
    print(f"✅ Now function: {adapter.now_function()}")
    return True

# Test both
os.environ["DB_TYPE"] = "sqlite"
print("\n--- SQLite ---")
sqlite_ok = test_adapter()

os.environ["DB_TYPE"] = "postgresql"
os.environ["POSTGRES_PASSWORD"] = "changeme"
print("\n--- PostgreSQL ---")
postgres_ok = test_adapter()

if sqlite_ok and postgres_ok:
    print("\n✅ Both adapters working!")
else:
    print("\n❌ Tests failed")
    sys.exit(1)
```

Run test:

```bash
cd migration
python test_adapters.py
```

### Step 12: Create Migration README

Create `migration/README.md` documenting:
- Directory contents
- Quick start guide
- Migration checklist
- Troubleshooting
- Rollback procedure

### Step 13: Commit Phase 1

```bash
git add migration/ app/server/database/ docker-compose.yml .env.sample
git commit -m "$(cat <<'EOF'
feat: PostgreSQL migration Phase 1 - Setup complete

Created PostgreSQL environment and database abstraction layer.

Phase 1 Complete (4 hours):
✅ Extracted SQLite schemas (26 tables, 41 indexes)
✅ Translated to PostgreSQL DDL (858 lines)
✅ Created database abstraction layer
✅ Set up Docker Compose (PostgreSQL 15)
✅ Installed psycopg2-binary==2.9.11
✅ Both adapters tested successfully

Database Abstraction Layer:
- DatabaseAdapter (abstract interface)
- SQLiteAdapter (backward compatible)
- PostgreSQLAdapter (connection pooling)
- Factory pattern (DB_TYPE env var)

Key Features:
- Supports both SQLite and PostgreSQL
- Connection pooling (1-10 connections)
- Dict-like row access
- Automatic transaction management
- Health check endpoints
- Rollback-safe design

Files Created:
+ migration/postgres_schema.sql (858 lines)
+ migration/sqlite_schema_*.sql
+ migration/README.md
+ migration/test_adapters.py
+ app/server/database/ (abstraction layer)
+ docker-compose.yml

Next: Phase 2 - Code Changes (6 hours)
- Update 79 get_connection() calls
- Convert 160 query placeholders
- Convert datetime functions

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Success Criteria

- ✅ SQLite schemas extracted (2 files)
- ✅ PostgreSQL schema translated (26 tables, 41 indexes, 4 views, 4 triggers)
- ✅ Docker Compose running PostgreSQL successfully
- ✅ Database abstraction layer created (5 files)
- ✅ psycopg2-binary installed
- ✅ Both SQLite and PostgreSQL adapters tested
- ✅ Health checks passing
- ✅ Changes committed

## Files Expected to Change

**New Files:**
- `migration/sqlite_schema_database.sql` (~565 lines)
- `migration/sqlite_schema_workflow_history.sql` (~420 lines)
- `migration/postgres_schema.sql` (~858 lines)
- `migration/README.md` (~200 lines)
- `migration/test_adapters.py` (~40 lines)
- `app/server/database/__init__.py`
- `app/server/database/connection.py` (~80 lines)
- `app/server/database/sqlite_adapter.py` (~140 lines)
- `app/server/database/postgres_adapter.py` (~120 lines)
- `app/server/database/factory.py` (~30 lines)
- `docker-compose.yml` (~40 lines)

**Modified:**
- `.env.sample` (add PostgreSQL section)

## Troubleshooting

**If PostgreSQL won't start:**
```bash
docker-compose down
docker volume rm tac-webbuilder_postgres_data
docker-compose up -d postgres
docker-compose logs postgres
```

**If schema doesn't load:**
```bash
# Manual schema load
docker-compose exec postgres psql -U tac_user -d tac_webbuilder -f /docker-entrypoint-initdb.d/01-schema.sql
```

**If psycopg2 import fails:**
```bash
cd app/server
uv remove psycopg2-binary
uv add psycopg2-binary
```

**If test fails:**
Check `.env` has correct POSTGRES_PASSWORD matching docker-compose.yml

## Next Steps

After completing Phase 1, report:
- "Phase 1 complete - PostgreSQL environment ready ✅"
- PostgreSQL version (should be 15.x)
- Number of tables created (should be 26)
- Both adapter tests passing

**Next Task:** Phase 2.1 - Update get_connection() calls (79 occurrences, 2 hours)

---

**Ready to copy into a new chat!** 🚀
