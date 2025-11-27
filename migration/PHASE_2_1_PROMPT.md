# Task: PostgreSQL Migration - Phase 2.1: Update get_connection() Calls

## Context
I'm working on the tac-webbuilder project. We're migrating from SQLite to PostgreSQL. Phase 1 is complete (database abstraction layer created). Now in **Phase 2.1 of 6** - updating all `get_connection()` calls to use the new adapter pattern.

## Objective
Replace all direct `get_connection()` imports and calls with the new database adapter factory, maintaining backward compatibility while enabling PostgreSQL support.

## Background Information
- **Phase 1 Status:** ✅ Complete - Database abstraction layer created
- **Current Pattern:** Direct import from `utils.db_connection`
- **Target Pattern:** Use `database.factory.get_database_adapter()`
- **Files to Update:** 23 Python files
- **Total Occurrences:** 79 `get_connection()` calls
- **Risk Level:** Medium (well-tested pattern, gradual migration)
- **Estimated Time:** 2 hours

## Step-by-Step Instructions

### Step 1: Find All get_connection() Usage

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Find all imports
grep -r "from.*db_connection import get_connection" . --include="*.py"

# Count occurrences
grep -r "get_connection(" . --include="*.py" | wc -l
```

**Expected:** ~79 occurrences across ~23 files

### Step 2: Categorize Files by Usage Pattern

```bash
# List all files using get_connection
grep -r "from.*db_connection import get_connection" . --include="*.py" | cut -d: -f1 | sort | uniq
```

**Expected files:**
- `routes/*.py` (6 route files)
- `services/*.py` (10+ service files)
- `repositories/*.py` (5+ repository files)
- `utils/*.py` (health service, etc.)

### Step 3: Create Migration Helper

The pattern for each file:

**Before:**
```python
from utils.db_connection import get_connection

def some_function():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM table")
```

**After:**
```python
from database import get_database_adapter

def some_function():
    adapter = get_database_adapter()
    with adapter.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM table")
```

### Step 4: Update Repository Files First (Low Risk)

Start with repository files (data access layer):

```bash
# List repository files
ls -la repositories/*.py
```

**Update pattern for each repository:**

```python
# OLD
from utils.db_connection import get_connection

class SomeRepository:
    def find_all(self):
        with get_connection() as conn:
            # ...

# NEW
from database import get_database_adapter

class SomeRepository:
    def __init__(self):
        self.adapter = get_database_adapter()

    def find_all(self):
        with self.adapter.get_connection() as conn:
            # ...
```

**Files to update:**
1. `repositories/phase_queue_repository.py`
2. `repositories/workflow_history_repository.py`
3. `repositories/adw_lock_repository.py`
4. And others...

### Step 5: Update Service Files

```bash
# List service files
ls -la services/*.py
```

**Update pattern:**

```python
# OLD
from utils.db_connection import get_connection

class SomeService:
    def do_something(self):
        with get_connection() as conn:
            # ...

# NEW
from database import get_database_adapter

class SomeService:
    def __init__(self):
        self.adapter = get_database_adapter()

    def do_something(self):
        with self.adapter.get_connection() as conn:
            # ...
```

**Important services:**
- `services/phase_queue_service.py`
- `services/github_issue_service.py`
- `services/workflow_history_service.py`
- `services/health_service.py`

### Step 6: Update Route Files

```bash
# List route files
ls -la routes/*.py
```

**Update pattern for routes:**

```python
# OLD
from utils.db_connection import get_connection

@router.get("/some-endpoint")
def endpoint():
    with get_connection() as conn:
        # ...

# NEW
from database import get_database_adapter

@router.get("/some-endpoint")
def endpoint():
    adapter = get_database_adapter()
    with adapter.get_connection() as conn:
        # ...
```

**Route files:**
1. `routes/data_routes.py`
2. `routes/github_routes.py`
3. `routes/queue_routes.py`
4. `routes/workflow_routes.py`
5. `routes/system_routes.py`
6. `routes/issue_completion_routes.py`

### Step 7: Handle Special Cases

**Case 1: Multiple db_path parameters**

Some files use custom database paths (e.g., `workflow_history.db`):

```python
# OLD
with get_connection(db_path="db/workflow_history.db") as conn:
    # ...

# NEW
# For now, create separate adapter instances
from database import SQLiteAdapter  # Import directly
adapter = SQLiteAdapter(db_path="db/workflow_history.db")
with adapter.get_connection() as conn:
    # ...

# TODO Phase 3: Merge into unified PostgreSQL database
```

**Case 2: Test files**

```bash
# Find test usage
grep -r "get_connection" tests/ --include="*.py"
```

Update test files similarly, but they can continue using SQLite:

```python
# tests/conftest.py or similar
from database import SQLiteAdapter

@pytest.fixture
def db_connection():
    adapter = SQLiteAdapter(db_path=":memory:")  # In-memory for tests
    return adapter
```

### Step 8: Run Tests After Each File

After updating each file, run its tests:

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Test specific file
pytest tests/repositories/test_phase_queue_repository.py -v

# Test all repositories
pytest tests/repositories/ -v

# Test all services
pytest tests/services/ -v

# Test all routes
pytest tests/routes/ -v
```

### Step 9: Verify No Direct Imports Remain

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Should return 0 (only utils/db_connection.py itself)
grep -r "from utils.db_connection import get_connection" . --include="*.py" | grep -v "db_connection.py" | wc -l
```

**Expected:** 0 occurrences (all migrated)

### Step 10: Run Full Test Suite

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Run all tests with SQLite (default)
DB_TYPE=sqlite pytest tests/ -v

# Verify coverage
pytest tests/ --cov=. --cov-report=term-missing
```

**Expected:** All tests passing with SQLite

### Step 11: Commit Changes

```bash
git add app/server/
git commit -m "$(cat <<'EOF'
refactor: Migrate to database adapter pattern (Phase 2.1)

Updated all get_connection() calls to use database abstraction layer.

Phase 2.1 Complete (2 hours):
✅ Updated 79 get_connection() calls across 23 files
✅ All repositories migrated to adapter pattern
✅ All services migrated to adapter pattern
✅ All routes migrated to adapter pattern
✅ Test files updated
✅ All tests passing with SQLite

Migration Pattern:
OLD: from utils.db_connection import get_connection
NEW: from database import get_database_adapter

Benefits:
- Supports both SQLite and PostgreSQL via DB_TYPE
- Backward compatible (SQLite by default)
- Centralized database configuration
- Connection pooling ready (PostgreSQL)
- Health checks built-in

Files Modified:
~ repositories/*.py (5 files)
~ services/*.py (10 files)
~ routes/*.py (6 files)
~ tests/*.py (2 files)

Testing:
- All repository tests passing
- All service tests passing
- All route tests passing
- Full test suite: 100% passing with SQLite

Next: Phase 2.2 - Convert placeholders (? → %s, 2 hours)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Success Criteria

- ✅ All 79 `get_connection()` calls updated
- ✅ No direct imports from `utils.db_connection` (except in db_connection.py itself)
- ✅ All repository tests passing
- ✅ All service tests passing
- ✅ All route tests passing
- ✅ Full test suite passing with SQLite
- ✅ Backward compatible (SQLite still default)
- ✅ Changes committed

## Files Expected to Change

**Repositories (~5 files):**
- `repositories/phase_queue_repository.py`
- `repositories/workflow_history_repository.py`
- `repositories/adw_lock_repository.py`
- Others...

**Services (~10 files):**
- `services/phase_queue_service.py`
- `services/github_issue_service.py`
- `services/workflow_history_service.py`
- `services/health_service.py`
- Others...

**Routes (~6 files):**
- `routes/data_routes.py`
- `routes/github_routes.py`
- `routes/queue_routes.py`
- `routes/workflow_routes.py`
- `routes/system_routes.py`
- `routes/issue_completion_routes.py`

**Tests (~2 files):**
- `tests/conftest.py`
- Others...

## Troubleshooting

**If tests fail after migration:**
```bash
# Check adapter is initialized
python -c "from database import get_database_adapter; print(get_database_adapter().get_db_type())"
```

**If import errors occur:**
```bash
# Verify database package exists
ls -la app/server/database/
```

**If "module not found":**
```bash
# Add __init__.py if missing
touch app/server/database/__init__.py
```

**If multiple database paths cause issues:**
For now, use direct `SQLiteAdapter(db_path="...")` imports. Phase 3 will unify databases.

## Next Steps

After completing Phase 2.1, report:
- "Phase 2.1 complete - All get_connection() calls migrated ✅"
- Number of files updated
- Test suite status (should be 100% passing)

**Next Task:** Phase 2.2 - Convert query placeholders (? → %s, 160 occurrences, 2 hours)

---

**Ready to copy into a new chat!** 🚀
