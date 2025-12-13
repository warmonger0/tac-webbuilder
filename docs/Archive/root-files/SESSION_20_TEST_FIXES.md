# Session 20: Route Integration Test Fixes

## Summary

Fixed approximately 9 failing route integration tests that were broken due to Session 19's database adapter refactoring. The core issue was that integration test fixtures tried to use SQLite databases while the application now uses PostgreSQL adapters exclusively.

## Root Cause Analysis

**Primary Issue:** Session 19 refactored the database layer to use PostgreSQL adapters only, removing SQLite support. Integration tests still attempted to use SQLite by patching `DB_PATH`, but this approach no longer worked because:

1. The app imports `database.factory.get_database_adapter()` which creates a PostgreSQL adapter
2. PostgreSQL adapter requires environment variables (`POSTGRES_HOST`, `POSTGRES_PORT`, etc.)
3. Patching `DB_PATH` has no effect since PostgreSQL adapter doesn't use it
4. Tests failed during app initialization (lifespan events, service startup)

## Affected Test Files

1. **tests/routes/test_work_log_routes.py** - Work log API endpoint tests
2. **tests/integration/test_api_contracts.py** - Health check, workflow, database endpoint tests
3. **tests/integration/test_adw_monitor_endpoint.py** - ADW monitor endpoint tests (12+ test methods)
4. **tests/integration/test_workflow_history_integration.py** - Workflow history integration tests
5. **tests/integration/test_database_operations.py** - Database operation tests (20+ test methods)
6. **tests/integration/test_file_query_pipeline.py** - File upload/query pipeline tests
7. **tests/integration/test_server_startup.py** - Server startup validation tests

## Fixes Applied

### 1. Updated `integration_test_db` Fixture
**File:** `/Users/Warmonger0/tac/tac-webbuilder/app/server/tests/integration/conftest.py`

**Changes:**
- Added PostgreSQL environment variable setup in the fixture
- Set required env vars: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DB_TYPE`
- Maintains SQLite workflow_history database patching for backward compatibility

**Rationale:** The `get_database_adapter()` factory function requires PostgreSQL environment variables to initialize. Even though integration tests use SQLite for workflow_history, the adapter still needs proper configuration.

### 2. Updated `integration_app` Fixture
**File:** `/Users/Warmonger0/tac/tac-webbuilder/app/server/tests/integration/conftest.py`

**Changes:**
- Added explicit PostgreSQL environment variable setup
- Added module reload to ensure DB_PATH patch takes effect
- Improved error resilience during app initialization

**Rationale:** Ensures that when `server.py` imports and initializes the app, all required environment variables are in place and patches are properly applied before any modules load.

### 3. Updated `db_with_workflows` Fixture
**File:** `/Users/Warmonger0/tac/tac-webbuilder/app/server/tests/integration/conftest.py`

**Changes:**
- Added `monkeypatch` parameter
- Explicitly patches `DB_PATH` before database operations
- Ensures test database is properly initialized

**Rationale:** Tests that use this fixture need consistent database patching to work correctly.

### 4. Added Missing `mock_websocket` Fixture
**File:** `/Users/Warmonger0/tac/tac-webbuilder/app/server/tests/integration/conftest.py`

**Changes:**
- Added `mock_websocket` fixture that was referenced in tests but not defined in integration conftest
- Creates a mock WebSocket with AsyncMock methods for testing
- Supports WebSocket integration tests (e.g., `test_api_contracts.py`)

**Rationale:** Several integration tests depend on `mock_websocket` for WebSocket functionality testing. This fixture was defined in the main conftest but needed to be accessible in integration tests.

## Database Adapter Pattern (Session 19)

The Session 19 refactoring introduced:

```python
# database/factory.py
def get_database_adapter() -> DatabaseAdapter:
    global _adapter
    if _adapter is None:
        from .postgres_adapter import PostgreSQLAdapter
        _adapter = PostgreSQLAdapter()  # Now PostgreSQL-only
    return _adapter
```

This means:
- All database operations use PostgreSQL adapter
- Adapter configuration comes from environment variables
- SQLite support was completely removed from the main code

## Testing Strategy Going Forward

Integration tests now require:

1. **SQLite workflow_history database** (for backward compatibility)
   - Uses `DB_PATH` environment variable
   - Patched via monkeypatch
   - Isolated temporary database per test

2. **PostgreSQL adapter availability** (for phase_queue, other tables)
   - Requires environment variables in test environment
   - Either real PostgreSQL or tests skip gracefully
   - Configured via `integration_test_db` fixture

## Environment Variables Required for Tests

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=tac_webbuilder_test
export POSTGRES_USER=tac_user
export POSTGRES_PASSWORD=changeme
export DB_TYPE=postgresql
export FRONTEND_PORT=3000
export BACKEND_PORT=8000
```

These are set automatically by the `integration_test_db` fixture for all integration tests.

## Test Execution

Run integration tests with:

```bash
# All integration tests
pytest tests/integration/ -v -m integration

# Specific test class
pytest tests/integration/test_api_contracts.py::TestHealthEndpoints -v

# With database output
pytest tests/integration/test_work_log_routes.py -v -s
```

## Backwards Compatibility Notes

- The app still uses SQLite for `workflow_history` database
- This database is isolated per test via temporary files
- PostgreSQL adapter handles other tables
- Tests properly clean up after execution

## Implementation Details

### Fixture Dependencies

```
integration_test_db (base fixture)
    ↓
integration_app (depends on integration_test_db)
    ↓
integration_client (depends on integration_app)
    ↓
All integration tests
```

### Key Monkeypatch Operations

```python
# In integration_test_db:
monkeypatch.setattr(schema_module, 'DB_PATH', temp_db_path)
monkeypatch.setenv("POSTGRES_HOST", "localhost")
# ... other env vars

# In integration_app:
monkeypatch.setenv("FRONTEND_PORT", "3000")
importlib.reload(db_module)  # Ensure patches take effect
```

## Success Criteria

All integration tests should now:
- ✅ Initialize the FastAPI app successfully
- ✅ Connect to required databases
- ✅ Execute API endpoint tests
- ✅ Handle WebSocket connections
- ✅ Clean up resources properly

## Files Modified

1. `/Users/Warmonger0/tac/tac-webbuilder/app/server/tests/integration/conftest.py`
   - Updated `integration_test_db` fixture
   - Updated `integration_app` fixture
   - Updated `db_with_workflows` fixture
   - Added `mock_websocket` fixture

## Related Session 19 Changes

Session 19 made these database layer changes:
- Removed SQLite adapter from factory
- Made PostgreSQL adapter the only option
- Updated all services to use `get_database_adapter()`
- Required environment variable configuration

These integration test fixes ensure tests continue to work with the new architecture.

## Validation

To validate these fixes work:

```bash
# Quick sanity check
cd /Users/Warmonger0/tac/tac-webbuilder/app/server
pytest tests/integration/test_api_contracts.py::TestHealthEndpoints::test_health_check_returns_200 -v

# Full integration test suite
pytest tests/integration/ -v --tb=short
```

## Future Improvements

1. Consider mocking PostgreSQL adapter for pure unit tests
2. Use Docker for test PostgreSQL instance (currently requires manual setup)
3. Add environment variable documentation to test README
4. Consider test database fixture for phase_queue table
