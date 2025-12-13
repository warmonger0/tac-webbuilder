# TypeError Fixes in test_hopper_sorter.py

## Root Cause
The test file `tests/services/test_hopper_sorter.py` was attempting to pass a `db_path` parameter to both `HopperSorter` and `PhaseQueueService` constructors, but these classes did not accept this parameter. This caused 8 TypeErrors:

```
TypeError: HopperSorter.__init__() got an unexpected keyword argument 'db_path'
TypeError: PhaseQueueService.__init__() got an unexpected keyword argument 'db_path'
```

## Solution Overview
Modified three classes to support an optional `db_path` parameter that allows using a custom SQLite database for testing:

1. **HopperSorter** - Accept `db_path` and create SQLiteAdapter if provided
2. **PhaseQueueService** - Accept `db_path` and pass to repository
3. **PhaseQueueRepository** - Accept `db_path` and create SQLiteAdapter if provided

## Files Modified

### 1. `/Users/Warmonger0/tac/tac-webbuilder/app/server/services/hopper_sorter.py`

**Changes:**
- Added import: `from database.sqlite_adapter import SQLiteAdapter`
- Modified `__init__` signature:
  ```python
  def __init__(self, db_path: str | None = None):
  ```
- Added conditional logic:
  - If `db_path` is provided: Create `SQLiteAdapter(db_path=db_path)`
  - Otherwise: Use `get_database_adapter()` (default behavior)

**Why:** Allows tests to provide custom test database path while maintaining backward compatibility.

### 2. `/Users/Warmonger0/tac/tac-webbuilder/app/server/services/phase_queue_service.py`

**Changes:**
- Modified `__init__` signature to add `db_path` parameter:
  ```python
  def __init__(
      self,
      repository: PhaseQueueRepository | None = None,
      dependency_tracker: PhaseDependencyTracker | None = None,
      db_path: str | None = None,
  ):
  ```
- Updated repository initialization:
  ```python
  if repository is None:
      self.repository = PhaseQueueRepository(db_path=db_path) if db_path else PhaseQueueRepository()
  else:
      self.repository = repository
  ```

**Why:** Passes custom database path through to repository, enabling test isolation.

### 3. `/Users/Warmonger0/tac/tac-webbuilder/app/server/repositories/phase_queue_repository.py`

**Changes:**
- Added import: `from database.sqlite_adapter import SQLiteAdapter`
- Modified `__init__` signature:
  ```python
  def __init__(self, db_path: str | None = None):
  ```
- Added conditional logic:
  - If `db_path` is provided: Create `SQLiteAdapter(db_path=db_path)`
  - Otherwise: Use `get_database_adapter()` (default behavior)

**Why:** Enables repository to use custom test database path.

## Test Impact

All 8 tests in `tests/services/test_hopper_sorter.py` should now pass:

1. `test_priority_ordering` - Tests priority-based phase selection
2. `test_fifo_within_priority` - Tests FIFO ordering within same priority
3. `test_empty_hopper` - Tests behavior with no ready phases
4. `test_parallel_execution` - Tests getting multiple phases in parallel
5. `test_running_parent_count` - Tests counting running parent issues
6. `test_can_start_more_parents` - Tests concurrency limit checking
7. `test_priority_stats` - Tests priority statistics
8. `test_deterministic_tiebreaker` - Tests parent_issue as tiebreaker

## Backward Compatibility

All changes maintain full backward compatibility:
- `db_path` is an optional parameter with default value `None`
- When `db_path` is `None`, classes use the default database adapter from the factory
- Existing code that doesn't pass `db_path` continues to work unchanged

## Pattern Usage

The test fixtures create temporary SQLite databases:
```python
@pytest.fixture
def test_db(tmp_path):
    """Create temporary test database"""
    db_path = tmp_path / "test_queue.db"
    # ... setup schema ...
    return str(db_path)

@pytest.fixture
def sorter(test_db):
    """Create HopperSorter instance with test database"""
    return HopperSorter(db_path=test_db)

@pytest.fixture
def queue_service(test_db):
    """Create PhaseQueueService instance with test database"""
    return PhaseQueueService(db_path=test_db)
```

This pattern:
1. Creates an isolated temporary database per test
2. Sets up the schema required for phase queue operations
3. Provides instances configured to use that database
4. Ensures test isolation and no cross-test pollution

## Verification

Run tests with:
```bash
env POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder_test POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql .venv/bin/pytest tests/services/test_hopper_sorter.py -xvs --tb=short
```

Expected result: All 8 tests pass with no TypeErrors.
