## Workflow 3A.2: Extract database.py Module

**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** Workflow 3A.1

**Input Files:**
- `app/server/core/workflow_history_original.py.bak` (lines 196-613)

**Output Files:**
- `app/server/core/workflow_history/database.py` (new)

**Tasks:**

1. **Create database.py module header**
   ```python
   """
   Database operations for workflow history.

   Provides CRUD operations for workflow history database including:
   - Database initialization and schema creation
   - Workflow insertion and updates
   - Workflow retrieval with filtering
   - History queries with pagination
   """

   import json
   import logging
   import sqlite3
   from pathlib import Path
   from typing import Dict, List, Optional, Tuple
   from datetime import datetime
   from contextlib import contextmanager

   from core.data_models import CostData

   logger = logging.getLogger(__name__)

   # Database path
   DB_PATH = Path(__file__).parent.parent.parent / "db" / "workflow_history.db"
   ```

2. **Extract database initialization** (lines 196-270)
   ```python
   def init_db() -> None:
       """
       Initialize the workflow history database with required tables.

       Creates:
       - workflow_history table with all workflow metadata
       - Indexes for common query patterns
       """
       # Implementation from original lines 196-270
   ```

3. **Extract workflow insertion** (lines 271-380)
   ```python
   def insert_workflow(workflow_data: Dict) -> bool:
       """
       Insert a new workflow into the database.

       Args:
           workflow_data: Complete workflow data dictionary

       Returns:
           True if insertion successful, False otherwise
       """
       # Implementation from original lines 271-380
   ```

4. **Extract workflow update** (lines 381-476)
   ```python
   def update_workflow(workflow_id: str, workflow_data: Dict) -> bool:
       """
       Update an existing workflow in the database.

       Args:
           workflow_id: Workflow identifier
           workflow_data: Updated workflow data

       Returns:
           True if update successful, False otherwise
       """
       # Implementation from original lines 381-476
   ```

5. **Extract workflow retrieval** (lines 477-542)
   ```python
   def get_workflow_by_id(workflow_id: str) -> Optional[Dict]:
       """
       Retrieve a single workflow by ID.

       Args:
           workflow_id: Workflow identifier

       Returns:
           Workflow data dictionary or None if not found
       """
       # Implementation from original lines 477-542
   ```

6. **Extract history query** (lines 543-613)
   ```python
   def get_workflow_history(
       limit: int = 50,
       offset: int = 0,
       status: Optional[str] = None,
       search: Optional[str] = None,
       sort_by: str = "created_at",
       sort_order: str = "DESC"
   ) -> Dict:
       """
       Get workflow history with filtering, pagination, and sorting.

       Args:
           limit: Maximum number of results (default: 50)
           offset: Number of results to skip (default: 0)
           status: Filter by status (completed, failed, running, etc.)
           search: Search term for nl_input field
           sort_by: Column to sort by (default: created_at)
           sort_order: ASC or DESC (default: DESC)

       Returns:
           Dictionary with:
           - workflows: List of workflow dictionaries
           - total: Total count (before pagination)
           - limit: Applied limit
           - offset: Applied offset
       """
       # Implementation from original lines 543-613
   ```

7. **Add helper functions for JSON serialization**
   ```python
   def _serialize_workflow(row: sqlite3.Row) -> Dict:
       """Convert database row to workflow dictionary."""
       # Helper implementation

   def _deserialize_json_field(value: Optional[str]) -> Optional[Dict]:
       """Safely deserialize JSON field from database."""
       # Helper implementation
   ```

8. **Update __init__.py to import from database.py**
   ```python
   # In __init__.py, replace backup imports with:
   from .database import (
       init_db,
       get_workflow_by_id,
       insert_workflow,
       update_workflow,
       get_workflow_history,
   )
   ```

**Code Example - Before/After:**

```python
# BEFORE (in monolithic workflow_history.py):
def init_db() -> None:
    """Initialize the workflow history database"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflow_history (
            id TEXT PRIMARY KEY,
            nl_input TEXT,
            -- ... 40+ columns ...
        )
    """)
    conn.commit()
    conn.close()

# AFTER (in workflow_history/database.py):
def init_db() -> None:
    """
    Initialize the workflow history database with required tables.

    Creates:
    - workflow_history table with all workflow metadata
    - Indexes for common query patterns
    """
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cursor = conn.cursor()

        # Create main table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_history (
                id TEXT PRIMARY KEY,
                nl_input TEXT,
                -- ... 40+ columns ...
            )
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at
            ON workflow_history(created_at)
        """)

        conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        conn.rollback()
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        conn.close()
```

**Acceptance Criteria:**
- [ ] database.py created with all DB operations
- [ ] All functions have type hints and docstrings
- [ ] Error handling and logging added
- [ ] Imports updated in __init__.py
- [ ] Original functionality preserved
- [ ] No breaking changes to callers

**Verification Commands:**
```bash
# Test database operations
python -c "
from app.server.core.workflow_history import init_db, get_workflow_by_id
init_db()
print('Database operations work')
"

# Run database-specific tests
cd app/server && pytest tests/test_workflow_history.py::test_init_db -v
cd app/server && pytest tests/test_workflow_history.py::test_insert_workflow -v
```

**Status:** Not Started

---
