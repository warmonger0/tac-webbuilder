# Repository Naming Standards

All repository classes MUST follow this naming convention for consistency and maintainability.

## Standard Method Names

### Create
```python
def create(self, item: ModelCreate) -> Model:
    """Create a new record.

    Args:
        item: Pydantic model with creation data

    Returns:
        Created model with ID populated
    """
```

### Read (Single Record)
```python
def get_by_id(self, id: int) -> Optional[Model]:
    """Get single record by primary key.

    Args:
        id: Primary key value

    Returns:
        Model if found, None otherwise
    """
```

### Read (By Field)
```python
def get_by_<field>(self, value: Any) -> Optional[Model]:
    """Get single record by unique field.

    Args:
        value: Field value to search for

    Returns:
        Model if found, None otherwise
    """

# For one-to-many relationships
def get_all_by_<field>(self, value: Any, limit: int = 100) -> List[Model]:
    """Get all records matching field value.

    Args:
        value: Field value to filter by
        limit: Maximum records to return

    Returns:
        List of matching models
    """
```

### Read (All)
```python
def get_all(self, limit: int = 100, offset: int = 0) -> List[Model]:
    """Get all records with pagination.

    Args:
        limit: Maximum records to return
        offset: Number of records to skip

    Returns:
        List of models
    """
```

### Update
```python
def update(self, id: int, data: ModelUpdate) -> Optional[Model]:
    """Update existing record.

    Args:
        id: Primary key of record to update
        data: Pydantic model with update data

    Returns:
        Updated model if found, None otherwise
    """
```

### Delete
```python
def delete(self, id: int) -> bool:
    """Delete record by primary key.

    Args:
        id: Primary key of record to delete

    Returns:
        True if deleted, False if not found
    """
```

### Custom Queries
```python
def find_<custom_criteria>(self, ...) -> List[Model]:
    """Custom query with descriptive name.

    Use 'find_' prefix for complex queries that don't fit
    standard patterns.

    Examples:
    - find_ready_phases()
    - find_pending_with_priority()
    - find_expired_sessions()
    """
```

## Migration Checklist

When renaming methods:
1. ✅ Update repository method name
2. ✅ Update all service callers
3. ✅ Update all route callers
4. ✅ Update tests
5. ✅ Run full test suite
6. ✅ Commit with clear migration message

## Rationale

This standardized naming convention provides:
- **Predictability**: Developers can guess method names without checking documentation
- **Consistency**: Same operations use same names across all repositories
- **Clarity**: Clear semantic distinction between read (`get_*`) and write (`create/update/delete`) operations
- **Maintainability**: Easier to onboard new developers and reduce context switching

## Examples

### PhaseQueueRepository (Standardized)
```python
# Create
created_item = repository.create(phase_item)

# Read by ID
phase = repository.get_by_id(queue_id)

# Read by parent issue
phases = repository.get_all_by_parent_issue(parent_issue, limit=50)

# Read all with pagination
all_phases = repository.get_all(limit=100, offset=0)

# Delete
success = repository.delete(queue_id)
```

### WorkLogRepository (Standardized)
```python
# Create
created_log = repository.create(work_log_item)

# Read all with pagination
logs = repository.get_all(limit=50, offset=0)

# Delete
success = repository.delete(log_id)
```
