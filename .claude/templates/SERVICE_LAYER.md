# Template: Service Layer

## File Location
`app/server/services/<service_name>_service.py`

## Standard Structure

```python
#!/usr/bin/env python3
"""
<Service Name> Service

Business logic for <domain> operations.

Responsibilities:
- <Responsibility 1>
- <Responsibility 2>
- <Responsibility 3>
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from app.server.db.database import get_connection

logger = logging.getLogger(__name__)


@dataclass
class <ModelName>:
    """Data model for <domain>."""
    # Add fields here
    id: Optional[int] = None
    created_at: Optional[str] = None

    def to_dict(self):
        return asdict(self)


class <ServiceName>Service:
    """Service for <domain> operations."""

    def get_all(self, limit: int = 100) -> List[<ModelName>]:
        """
        Get all <items>.

        Args:
            limit: Maximum number of items to return

        Returns:
            List of <ModelName> objects
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM <table_name>
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            items = [self._row_to_model(row) for row in rows]

            logger.info(f"[{self.__class__.__name__}] Found {len(items)} items")
            return items

    def get_by_id(self, item_id: int) -> Optional[<ModelName>]:
        """
        Get item by ID.

        Args:
            item_id: Item identifier

        Returns:
            <ModelName> or None if not found
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM <table_name> WHERE id = ?", (item_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_model(row)

    def create(self, data: Dict) -> <ModelName>:
        """
        Create new item.

        Args:
            data: Item data dictionary

        Returns:
            Created <ModelName>
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO <table_name> (column1, column2)
                VALUES (?, ?)
            """, (data['column1'], data['column2']))

            item_id = cursor.lastrowid
            conn.commit()

            logger.info(f"[{self.__class__.__name__}] Created item {item_id}")
            return self.get_by_id(item_id)

    def update(self, item_id: int, data: Dict) -> Optional[<ModelName>]:
        """
        Update existing item.

        Args:
            item_id: Item identifier
            data: Updated data dictionary

        Returns:
            Updated <ModelName> or None if not found
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE <table_name>
                SET column1 = ?, column2 = ?
                WHERE id = ?
            """, (data['column1'], data['column2'], item_id))

            conn.commit()

            logger.info(f"[{self.__class__.__name__}] Updated item {item_id}")
            return self.get_by_id(item_id)

    def delete(self, item_id: int) -> bool:
        """
        Delete item.

        Args:
            item_id: Item identifier

        Returns:
            True if deleted, False if not found
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM <table_name> WHERE id = ?", (item_id,))
            deleted = cursor.rowcount > 0
            conn.commit()

            if deleted:
                logger.info(f"[{self.__class__.__name__}] Deleted item {item_id}")

            return deleted

    def _row_to_model(self, row) -> <ModelName>:
        """Convert database row to model object."""
        if not row:
            return None

        return <ModelName>(
            id=row[0],
            # Map columns to fields
            created_at=row[-1]
        )
```

## Usage Example

```python
from app.server.services.<service_name>_service import <ServiceName>Service

service = <ServiceName>Service()

# Get all
items = service.get_all(limit=50)

# Get by ID
item = service.get_by_id(123)

# Create
new_item = service.create({'column1': 'value1', 'column2': 'value2'})

# Update
updated = service.update(123, {'column1': 'new_value'})

# Delete
deleted = service.delete(123)
```

## Testing

See `PYTEST_TESTS.md` template for service testing patterns.

## Common Patterns

**Filtering:**
```python
def get_by_status(self, status: str) -> List[<ModelName>]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM <table> WHERE status = ?", (status,))
        return [self._row_to_model(row) for row in cursor.fetchall()]
```

**Aggregation:**
```python
def get_statistics(self) -> Dict:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, COUNT(*) FROM <table> GROUP BY status")
        return {row[0]: row[1] for row in cursor.fetchall()}
```

**Batch Operations:**
```python
def create_batch(self, items: List[Dict]) -> List[<ModelName>]:
    with get_connection() as conn:
        cursor = conn.cursor()
        for item in items:
            cursor.execute("INSERT INTO <table> ...", (...))
        conn.commit()
    return [self.get_by_id(i) for i in range(cursor.lastrowid - len(items) + 1, cursor.lastrowid + 1)]
```
