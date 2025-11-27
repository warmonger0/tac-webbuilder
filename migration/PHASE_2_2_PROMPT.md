# Task: PostgreSQL Migration - Phase 2.2: Convert Query Placeholders

## Context
I'm working on the tac-webbuilder project. We're migrating from SQLite to PostgreSQL. Phase 2.1 is complete (all get_connection() calls updated). Now in **Phase 2.2 of 6** - converting query placeholders to be database-agnostic.

## Objective
Convert all hardcoded `?` placeholders to use `adapter.placeholder()` method, enabling the same queries to work with both SQLite (`?`) and PostgreSQL (`%s`).

## Background Information
- **Phase 2.1 Status:** ✅ Complete - All files using adapter pattern
- **Current Pattern:** Hardcoded `?` placeholders (SQLite-only)
- **Target Pattern:** Dynamic placeholders via `adapter.placeholder()`
- **Total Occurrences:** ~160 `?` placeholders in queries
- **Risk Level:** High (SQL syntax changes, must test thoroughly)
- **Estimated Time:** 2 hours

## Step-by-Step Instructions

### Step 1: Find All Query Placeholders

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Find all ? in SQL queries (in execute calls)
grep -rn '\.execute.*".*\?' . --include="*.py" | wc -l

# Find all ? in SQL queries (in execute calls with """")
grep -rn '\.execute.*""".*\?' . --include="*.py" | wc -l
```

**Expected:** ~160 occurrences

### Step 2: Understand the Pattern

**Current (SQLite-only):**
```python
cursor.execute("SELECT * FROM table WHERE id = ?", (id_value,))
cursor.execute("INSERT INTO table (a, b) VALUES (?, ?)", (val1, val2))
```

**Target (Database-agnostic):**
```python
adapter = get_database_adapter()
ph = adapter.placeholder()

cursor.execute(f"SELECT * FROM table WHERE id = {ph}", (id_value,))
cursor.execute(f"INSERT INTO table (a, b) VALUES ({ph}, {ph})", (val1, val2))
```

**For multiple placeholders:**
```python
# Before
query = "INSERT INTO table (a, b, c) VALUES (?, ?, ?)"

# After - Method 1: Manual f-string
ph = adapter.placeholder()
query = f"INSERT INTO table (a, b, c) VALUES ({ph}, {ph}, {ph})"

# After - Method 2: Helper function (create this first)
def build_placeholders(count: int) -> str:
    """Generate comma-separated placeholders"""
    adapter = get_database_adapter()
    ph = adapter.placeholder()
    return ", ".join([ph] * count)

query = f"INSERT INTO table (a, b, c) VALUES ({build_placeholders(3)})"
```

### Step 3: Create Helper Functions

Create `utils/query_helpers.py`:

```python
"""
Query helper functions for database-agnostic SQL.
"""

from database import get_database_adapter


def get_placeholder() -> str:
    """
    Get the current database's placeholder character.

    Returns:
        '?' for SQLite, '%s' for PostgreSQL
    """
    return get_database_adapter().placeholder()


def build_placeholders(count: int) -> str:
    """
    Generate comma-separated placeholders.

    Args:
        count: Number of placeholders needed

    Returns:
        String like "?, ?, ?" (SQLite) or "%s, %s, %s" (PostgreSQL)

    Example:
        >>> build_placeholders(3)
        '?, ?, ?'  # for SQLite
        '%s, %s, %s'  # for PostgreSQL
    """
    ph = get_placeholder()
    return ", ".join([ph] * count)


def build_update_set(fields: list[str]) -> str:
    """
    Generate SET clause for UPDATE statements.

    Args:
        fields: List of field names

    Returns:
        String like "a = ?, b = ?, c = ?" (SQLite)

    Example:
        >>> build_update_set(['name', 'age'])
        'name = ?, age = ?'  # for SQLite
    """
    ph = get_placeholder()
    return ", ".join([f"{field} = {ph}" for field in fields])
```

### Step 4: Update Simple Single-Placeholder Queries

Start with simple queries (1-2 placeholders):

```bash
# Find simple patterns
grep -rn '\.execute.*".*= \?"' . --include="*.py"
```

**Pattern:**
```python
# Before
cursor.execute("SELECT * FROM table WHERE id = ?", (id_val,))

# After
from utils.query_helpers import get_placeholder
ph = get_placeholder()
cursor.execute(f"SELECT * FROM table WHERE id = {ph}", (id_val,))
```

### Step 5: Update INSERT Statements

```bash
# Find INSERT statements
grep -rn '\.execute.*"INSERT INTO' . --include="*.py" | head -20
```

**Pattern:**
```python
# Before
cursor.execute(
    "INSERT INTO table (a, b, c) VALUES (?, ?, ?)",
    (val1, val2, val3)
)

# After
from utils.query_helpers import build_placeholders
placeholders = build_placeholders(3)
cursor.execute(
    f"INSERT INTO table (a, b, c) VALUES ({placeholders})",
    (val1, val2, val3)
)

# Or inline
from utils.query_helpers import get_placeholder
ph = get_placeholder()
cursor.execute(
    f"INSERT INTO table (a, b, c) VALUES ({ph}, {ph}, {ph})",
    (val1, val2, val3)
)
```

### Step 6: Update UPDATE Statements

```bash
# Find UPDATE statements
grep -rn '\.execute.*"UPDATE' . --include="*.py" | head -20
```

**Pattern:**
```python
# Before
cursor.execute(
    "UPDATE table SET name = ?, age = ? WHERE id = ?",
    (name, age, id)
)

# After
from utils.query_helpers import build_update_set, get_placeholder
set_clause = build_update_set(['name', 'age'])
ph = get_placeholder()
cursor.execute(
    f"UPDATE table SET {set_clause} WHERE id = {ph}",
    (name, age, id)
)
```

### Step 7: Update Complex Queries

For queries with many placeholders or complex logic:

```python
# Before
cursor.execute("""
    INSERT INTO workflow_history (
        adw_id, issue_number, status, start_time,
        input_tokens, output_tokens, total_tokens
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
""", (adw_id, issue, status, start, input_tok, output_tok, total))

# After
from utils.query_helpers import build_placeholders
placeholders = build_placeholders(7)
cursor.execute(f"""
    INSERT INTO workflow_history (
        adw_id, issue_number, status, start_time,
        input_tokens, output_tokens, total_tokens
    ) VALUES ({placeholders})
""", (adw_id, issue, status, start, input_tok, output_tok, total))
```

### Step 8: Update Repository Files

Update all repository files systematically:

**Example: `repositories/phase_queue_repository.py`**

```python
from database import get_database_adapter
from utils.query_helpers import get_placeholder, build_placeholders

class PhaseQueueRepository:
    def __init__(self):
        self.adapter = get_database_adapter()

    def find_by_id(self, queue_id: str):
        ph = get_placeholder()
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM phase_queue WHERE queue_id = {ph}",
                (queue_id,)
            )
            return cursor.fetchone()

    def create(self, queue_data):
        placeholders = build_placeholders(5)  # 5 fields
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO phase_queue
                (queue_id, parent_issue, phase_number, status, phase_data)
                VALUES ({placeholders})
            """, (queue_data['id'], queue_data['parent'], ...))
```

### Step 9: Test Each File After Update

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Test with SQLite (should still work)
DB_TYPE=sqlite pytest tests/repositories/test_phase_queue_repository.py -v

# Test the same file with PostgreSQL (if DB is ready)
DB_TYPE=postgresql pytest tests/repositories/test_phase_queue_repository.py -v
```

### Step 10: Update All Files Systematically

Process files in this order (lowest to highest risk):

1. **Repositories** (5-10 files) - Data access layer
2. **Services** (10-15 files) - Business logic
3. **Routes** (6 files) - API endpoints
4. **Utils** (2-3 files) - Utilities

For each file:
```bash
# 1. Update placeholders
# 2. Run tests with SQLite
DB_TYPE=sqlite pytest tests/.../test_[file].py -v

# 3. If PostgreSQL DB ready, test with it too
DB_TYPE=postgresql pytest tests/.../test_[file].py -v
```

### Step 11: Verify No Hardcoded Placeholders Remain

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Find remaining ? in SQL
# Exclude comments and strings that aren't SQL
grep -rn '\.execute.*".*\?' . --include="*.py" | grep -v "query_helpers.py"
```

**Expected:** 0 occurrences (except in helper file)

### Step 12: Run Full Test Suite

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Test with SQLite (must pass)
DB_TYPE=sqlite pytest tests/ -v --tb=short

# Test with PostgreSQL (if ready)
DB_TYPE=postgresql pytest tests/ -v --tb=short
```

**Expected:** All tests passing with both databases

### Step 13: Commit Changes

```bash
git add app/server/
git commit -m "$(cat <<'EOF'
refactor: Convert to database-agnostic placeholders (Phase 2.2)

Replaced all hardcoded ? placeholders with dynamic placeholders.

Phase 2.2 Complete (2 hours):
✅ Converted ~160 query placeholders
✅ Created query helper functions
✅ All repositories use dynamic placeholders
✅ All services use dynamic placeholders
✅ All routes use dynamic placeholders
✅ Tests passing with both SQLite and PostgreSQL

Query Helper Functions:
- get_placeholder() - Returns ? or %s
- build_placeholders(count) - Generates n placeholders
- build_update_set(fields) - Generates SET clause

Migration Pattern:
OLD: cursor.execute("SELECT * WHERE id = ?", (id,))
NEW: ph = get_placeholder()
     cursor.execute(f"SELECT * WHERE id = {ph}", (id,))

Benefits:
- Same queries work with SQLite and PostgreSQL
- Centralized placeholder logic
- Type-safe query building
- Easy to test both databases

Files Modified:
+ utils/query_helpers.py (new helper functions)
~ repositories/*.py (10 files)
~ services/*.py (15 files)
~ routes/*.py (6 files)

Testing:
- SQLite: All tests passing ✅
- PostgreSQL: All tests passing ✅
- Dual-database testing confirmed

Next: Phase 2.3 - Convert datetime functions (2 hours)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Success Criteria

- ✅ All ~160 query placeholders converted
- ✅ Query helper functions created
- ✅ No hardcoded `?` in SQL queries
- ✅ All tests passing with SQLite
- ✅ All tests passing with PostgreSQL (if DB ready)
- ✅ Backward compatible
- ✅ Changes committed

## Files Expected to Change

**New:**
- `utils/query_helpers.py` (~60 lines)

**Modified (~30 files):**
- `repositories/*.py` (10 files)
- `services/*.py` (15 files)
- `routes/*.py` (6 files)

## Troubleshooting

**If f-string errors occur:**
```python
# Make sure to use f-strings properly
# WRONG: "SELECT * WHERE id = {ph}"  # Missing f
# RIGHT: f"SELECT * WHERE id = {ph}"
```

**If tests fail with "wrong number of parameters":**
- Check that placeholder count matches parameter count
- Example: `build_placeholders(3)` needs exactly 3 parameters

**If PostgreSQL tests fail but SQLite works:**
```bash
# Check placeholder is correct
python -c "from database import PostgreSQLAdapter; print(PostgreSQLAdapter().placeholder())"
# Should print: %s
```

## Next Steps

After completing Phase 2.2, report:
- "Phase 2.2 complete - All placeholders converted ✅"
- Tests passing with both SQLite and PostgreSQL
- Number of queries updated

**Next Task:** Phase 2.3 - Convert datetime functions (datetime('now') → NOW(), 2 hours)

---

**Ready to copy into a new chat!** 🚀
