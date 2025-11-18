### Workflow 1.1: Create DatabaseManager Module
**Estimated Time:** 2-3 hours
**Complexity:** Low
**Dependencies:** None

**Input Files:**
- `app/server/core/workflow_history.py` (database connection examples)
- `app/server/core/file_processor.py` (database connection examples)

**Output Files:**
- `app/server/core/database.py` (new)

**Tasks:**
1. Create DatabaseManager class with context managers
2. Implement `get_connection()` context manager
3. Implement `get_cursor()` context manager
4. Add automatic commit/rollback handling
5. Add row factory support
6. Add logging for database operations
7. Add path validation and directory creation

**Class Structure:**
```python
from contextlib import contextmanager
import sqlite3
from pathlib import Path
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Centralized database connection management with automatic commit/rollback"""

    def __init__(self, db_path: str = "db/database.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"DatabaseManager initialized with path: {self.db_path}")

    @contextmanager
    def get_connection(self, row_factory: Optional[Callable] = None):
        """
        Context manager for database connections with automatic commit/rollback

        Args:
            row_factory: Optional row factory (e.g., sqlite3.Row)

        Yields:
            sqlite3.Connection: Database connection

        Example:
            with db.get_connection(sqlite3.Row) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM workflows")
                results = cursor.fetchall()
        """
        conn = sqlite3.connect(str(self.db_path))
        if row_factory:
            conn.row_factory = row_factory
        try:
            yield conn
            conn.commit()
            logger.debug("Database transaction committed")
        except Exception as e:
            conn.rollback()
            logger.error(f"Database transaction rolled back: {e}")
            raise e
        finally:
            conn.close()

    @contextmanager
    def get_cursor(self, row_factory: Optional[Callable] = None):
        """
        Context manager for database cursor (convenience wrapper)

        Args:
            row_factory: Optional row factory (e.g., sqlite3.Row)

        Yields:
            sqlite3.Cursor: Database cursor

        Example:
            with db.get_cursor(sqlite3.Row) as cursor:
                cursor.execute("SELECT * FROM workflows")
                results = cursor.fetchall()
        """
        with self.get_connection(row_factory) as conn:
            yield conn.cursor()

    def execute_query(
        self,
        query: str,
        params: tuple = (),
        row_factory: Optional[Callable] = None
    ) -> list:
        """
        Execute a SELECT query and return results

        Args:
            query: SQL query string
            params: Query parameters
            row_factory: Optional row factory

        Returns:
            List of query results
        """
        with self.get_cursor(row_factory) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_update(
        self,
        query: str,
        params: tuple = ()
    ) -> int:
        """
        Execute an INSERT/UPDATE/DELETE query

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Number of affected rows
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
```

**Acceptance Criteria:**
- [ ] DatabaseManager class created
- [ ] Context managers handle commit/rollback automatically
- [ ] Row factory support works
- [ ] Directory creation works
- [ ] All methods have type hints and docstrings
- [ ] Logging implemented

**Verification Command:**
```bash
python -c "
from app.server.core.database import DatabaseManager
import sqlite3

db = DatabaseManager('test.db')
with db.get_connection(sqlite3.Row) as conn:
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE test (id INTEGER, name TEXT)')
    cursor.execute('INSERT INTO test VALUES (1, \"test\")')

with db.get_cursor(sqlite3.Row) as cursor:
    cursor.execute('SELECT * FROM test')
    row = cursor.fetchone()
    print(f'Row: {dict(row)}')

import os
os.remove('test.db')
print('DatabaseManager test passed')
"
```

---
