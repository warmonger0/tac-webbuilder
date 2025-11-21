# Test Infrastructure Quick Start Guide

## TL;DR - Start Testing in 5 Minutes

### 1. Run Existing Tests
```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server
pytest
```

### 2. Run Only Fast Tests
```bash
pytest -m "not slow"
```

### 3. Run Integration Tests
```bash
pytest -m integration
```

## Quick Fixture Reference

### Need a Test Database?
```python
def test_my_feature(temp_test_db):
    # temp_test_db is a path to an isolated SQLite database
    conn = sqlite3.connect(temp_test_db)
    # ... your test code ...
    # Database is automatically deleted after test
```

### Need to Test an API Endpoint?
```python
def test_api_endpoint(integration_client):
    response = integration_client.get("/api/health")
    assert response.status_code == 200
```

### Need a Database with Schema?
```python
def test_with_schema(temp_db_connection, init_workflow_history_schema):
    cursor = temp_db_connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM workflow_history")
    # Schema is already created
```

### Need Sample Data?
```python
def test_with_data(sample_workflow_data, sample_github_issue):
    # sample_workflow_data and sample_github_issue are ready to use
    assert sample_workflow_data["adw_id"] == "TEST-001"
```

### Need to Mock External APIs?
```python
@pytest.mark.integration
def test_github_integration(integration_client, mock_github_api):
    # GitHub API calls are automatically mocked
    # No real API calls, no API key needed
    pass
```

## Common Test Patterns

### Pattern 1: Simple Unit Test
```python
import pytest

@pytest.mark.unit
def test_calculation():
    """Test a pure function."""
    from core.my_module import calculate_something
    result = calculate_something(10, 20)
    assert result == 30
```

### Pattern 2: API Integration Test
```python
@pytest.mark.integration
def test_api_contract(integration_client):
    """Test API endpoint returns correct structure."""
    response = integration_client.get("/api/workflows/history")

    assert response.status_code == 200
    data = response.json()
    assert "workflows" in data or isinstance(data, list)
```

### Pattern 3: Database Integration Test
```python
@pytest.mark.integration
def test_database_operation(integration_test_db):
    """Test database operations with real schema."""
    from core.workflow_history import insert_workflow_history, get_workflow_by_adw_id

    with pytest.mock.patch('core.workflow_history_utils.database.DB_PATH', integration_test_db):
        # Insert workflow
        row_id = insert_workflow_history(
            adw_id="TEST-001",
            issue_number=42,
            status="completed"
        )

        # Retrieve workflow
        workflow = get_workflow_by_adw_id("TEST-001")
        assert workflow["adw_id"] == "TEST-001"
```

### Pattern 4: WebSocket Test
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_websocket(websocket_manager, mock_websocket):
    """Test WebSocket connection and messaging."""
    await websocket_manager.connect(mock_websocket)

    await websocket_manager.broadcast({"type": "test", "data": "hello"})

    mock_websocket.send_json.assert_called_once()
```

### Pattern 5: E2E User Journey Test
```python
@pytest.mark.e2e
def test_complete_workflow(e2e_test_client, e2e_database):
    """Test complete user workflow from start to finish."""
    from unittest.mock import patch

    with patch('core.workflow_history_utils.database.DB_PATH', e2e_database):
        # Step 1: Create workflow
        create_response = e2e_test_client.post("/api/workflows/create", json={
            "nl_input": "Test workflow",
            "issue_number": 999
        })

        # Step 2: Check status
        status_response = e2e_test_client.get("/api/workflows/status")
        assert status_response.status_code == 200
```

## Fixture Cheat Sheet

| Need | Fixture | Import |
|------|---------|--------|
| Temp database path | `temp_test_db` | Auto-imported |
| Open DB connection | `temp_db_connection` | Auto-imported |
| DB with schema | `init_workflow_history_schema` | Auto-imported |
| API test client | `test_client` | Auto-imported |
| Integration client | `integration_client` | Auto-imported |
| Mock WebSocket | `mock_websocket` | Auto-imported |
| Mock GitHub API | `mock_github_api` | Auto-imported |
| Mock env vars | `mock_env_vars` | Auto-imported |
| Sample workflow data | `sample_workflow_data` | Auto-imported |
| Full E2E setup | `e2e_test_client` | Auto-imported |

**All fixtures are auto-imported from conftest.py files!**

## Test Command Cheat Sheet

| Task | Command |
|------|---------|
| Run all tests | `pytest` |
| Run unit tests only | `pytest -m unit` |
| Run integration tests | `pytest -m integration` |
| Run E2E tests | `pytest -m e2e` |
| Run fast tests only | `pytest -m "not slow"` |
| Run specific file | `pytest tests/integration/test_api_contracts.py` |
| Run with coverage | `pytest --cov=. --cov-report=html` |
| Run verbose | `pytest -v` |
| Show print output | `pytest -s` |
| Run last failed | `pytest --lf` |
| Drop to debugger on fail | `pytest --pdb` |
| Run parallel (if pytest-xdist installed) | `pytest -n auto` |

## Quick Debugging Tips

### Test Fails - Can't See Why?
```bash
pytest -vv -s  # Very verbose + show prints
```

### Need to Debug a Test?
```bash
pytest --pdb  # Drops into debugger on failure
```

### Only Want to Run Failed Tests?
```bash
pytest --lf  # Last failed
```

### Want to See Fixture Setup?
```bash
pytest --setup-show
```

## Common Gotchas

### 1. Wrong Directory
**Error**: `ModuleNotFoundError: No module named 'core'`

**Solution**: Run pytest from `/app/server/`:
```bash
cd /path/to/tac-webbuilder/app/server
pytest
```

### 2. Database Locked
**Error**: `sqlite3.OperationalError: database is locked`

**Solution**: Use `temp_test_db` fixture for isolated databases:
```python
def test_isolated(temp_test_db):  # Each test gets own DB
    pass
```

### 3. Async Test Not Running
**Error**: Test seems to hang or doesn't run

**Solution**: Add `@pytest.mark.asyncio`:
```python
@pytest.mark.asyncio
async def test_async():
    pass
```

### 4. Fixture Not Found
**Error**: `fixture 'my_fixture' not found`

**Solution**: Check fixture is in:
- `tests/conftest.py` (all tests)
- `tests/integration/conftest.py` (integration tests)
- `tests/e2e/conftest.py` (e2e tests)

## Creating Your First Test

### Step 1: Choose Test Type
- **Unit**: Testing a function in isolation? → `tests/core/test_my_module.py`
- **Integration**: Testing API or database? → `tests/integration/test_my_feature.py`
- **E2E**: Testing complete workflow? → `tests/e2e/test_my_journey.py`

### Step 2: Create Test File
```python
# tests/integration/test_my_feature.py
import pytest

@pytest.mark.integration
def test_my_feature(integration_client):
    """Test my new feature works correctly."""
    response = integration_client.post("/api/my-endpoint", json={
        "data": "test"
    })

    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

### Step 3: Run Your Test
```bash
pytest tests/integration/test_my_feature.py -v
```

### Step 4: Add More Test Cases
```python
@pytest.mark.parametrize("input_data,expected", [
    ({"value": 10}, 20),
    ({"value": 5}, 10),
])
def test_with_multiple_inputs(integration_client, input_data, expected):
    response = integration_client.post("/api/calculate", json=input_data)
    assert response.json()["result"] == expected
```

## Next Steps

1. **Read the full README**: `tests/README.md`
2. **Explore existing tests**: See patterns in `tests/integration/test_api_contracts.py`
3. **Check fixtures**: Look at `tests/conftest.py` for all available fixtures
4. **Write tests for your features**: Follow the patterns above

## Getting Help

- **Full documentation**: See `tests/README.md`
- **Pytest docs**: https://docs.pytest.org/
- **FastAPI testing**: https://fastapi.tiangolo.com/tutorial/testing/
- **Example tests**: Check `tests/integration/` and `tests/e2e/` directories

## Quick Examples by Use Case

### Testing a New API Endpoint
```python
@pytest.mark.integration
def test_new_endpoint(integration_client, mock_anthropic_api):
    response = integration_client.post("/api/new-endpoint", json={
        "query": "test query"
    })
    assert response.status_code == 200
```

### Testing Database Operations
```python
@pytest.mark.integration
def test_db_operation(integration_test_db):
    from core.workflow_history import insert_workflow_history

    with pytest.mock.patch('core.workflow_history_utils.database.DB_PATH', integration_test_db):
        row_id = insert_workflow_history(adw_id="TEST", status="completed")
        assert row_id > 0
```

### Testing a Complete User Flow
```python
@pytest.mark.e2e
def test_user_flow(e2e_test_client, e2e_database):
    from unittest.mock import patch

    with patch('core.workflow_history_utils.database.DB_PATH', e2e_database):
        # Create
        create_resp = e2e_test_client.post("/api/create", json={...})
        assert create_resp.status_code == 201

        # Read
        read_resp = e2e_test_client.get("/api/items/1")
        assert read_resp.status_code == 200

        # Update
        update_resp = e2e_test_client.put("/api/items/1", json={...})
        assert update_resp.status_code == 200
```

Happy Testing!
