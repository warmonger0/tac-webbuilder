# Testing Examples for E2E Integration Testing

This document provides concrete examples of tests that can now be written with the installed testing infrastructure.

## 1. API Endpoint Testing Examples

### Basic HTTP Endpoint Test

```python
def test_health_endpoint(test_client):
    """Test the health check endpoint."""
    response = test_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
```

### POST Request with JSON Payload

```python
def test_create_workflow(test_client):
    """Test creating a new workflow via API."""
    payload = {
        "nl_input": "Fix authentication bug in login flow",
        "table": "issues",
        "provider": "anthropic"
    }
    response = test_client.post("/api/workflows", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "adw_id" in data
    assert data["status"] == "pending"


def test_create_workflow_invalid_input(test_client):
    """Test workflow creation with invalid input."""
    response = test_client.post(
        "/api/workflows",
        json={"table": "issues"}  # Missing required nl_input
    )
    assert response.status_code == 422  # Validation error


def test_query_endpoint(test_client):
    """Test SQL query generation endpoint."""
    payload = {
        "nl_query": "Show me all users who signed up this week",
        "table": "users",
        "provider": "anthropic"
    }
    response = test_client.post("/api/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert data["query"].startswith("SELECT")
```

### File Upload Test

```python
def test_upload_database_file(test_client):
    """Test uploading a database file."""
    with open("test_database.db", "rb") as f:
        files = {"file": ("test.db", f, "application/octet-stream")}
        response = test_client.post("/api/upload", files=files)
    assert response.status_code == 200
    assert "file_path" in response.json()
```

### Query Parameters Test

```python
def test_list_workflows_with_filters(test_client):
    """Test listing workflows with filtering."""
    response = test_client.get(
        "/api/workflows?status=completed&limit=10&offset=0"
    )
    assert response.status_code == 200
    workflows = response.json()
    assert len(workflows) <= 10
    for workflow in workflows:
        assert workflow["status"] == "completed"
```

## 2. Async Test Examples

### Async HTTP Request

```python
import pytest

@pytest.mark.asyncio
async def test_async_http_client():
    """Test using httpx async client."""
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/api/health")
        assert response.status_code == 200
```

### Async Database Operation

```python
@pytest.mark.asyncio
async def test_async_db_query():
    """Test async database operations."""
    from core.workflow_history import get_workflow_history_async

    workflows = await get_workflow_history_async(limit=5)
    assert len(workflows) >= 0
    if len(workflows) > 0:
        assert "adw_id" in workflows[0]
```

### Async Service Call

```python
@pytest.mark.asyncio
async def test_async_service(integration_client):
    """Test async service integration."""
    response = integration_client.get("/api/health")
    assert response.status_code == 200
```

## 3. Database Integration Test Examples

### Database Transaction Test

```python
def test_workflow_creation_in_db(integration_client, db_with_workflows):
    """Test workflow creation and database persistence."""
    payload = {
        "nl_input": "Create new user table",
        "table": "schema",
        "provider": "anthropic"
    }
    response = integration_client.post("/api/workflows", json=payload)
    assert response.status_code == 201

    # Verify it was persisted
    response = integration_client.get("/api/workflows")
    workflows = response.json()
    assert len(workflows) > 0
```

### Database Query Validation

```python
def test_workflow_history_query(integration_client, db_with_workflows):
    """Test querying workflow history."""
    response = integration_client.get("/api/workflows?status=completed")
    assert response.status_code == 200
    workflows = response.json()
    # Should have at least the sample data
    assert len(workflows) > 0
    # Verify sample data is present
    assert any(w["adw_id"] == "TEST-001" for w in workflows)
```

### Database Isolation Test

```python
def test_database_isolation(temp_test_db):
    """Test that temp databases are properly isolated."""
    import sqlite3

    conn1 = sqlite3.connect(temp_test_db)
    conn2 = sqlite3.connect(temp_test_db)

    cursor1 = conn1.cursor()
    cursor2 = conn2.cursor()

    cursor1.execute("""
        CREATE TABLE IF NOT EXISTS test (
            id INTEGER PRIMARY KEY,
            value TEXT
        )
    """)
    conn1.commit()

    # Verify second connection can see the table
    cursor2.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor2.fetchall()
    assert len(tables) > 0

    conn1.close()
    conn2.close()
```

## 4. WebSocket Test Examples

### WebSocket Connection Test

```python
import pytest

@pytest.mark.asyncio
@pytest.mark.websocket
async def test_websocket_connection(websocket_manager, mock_websocket):
    """Test WebSocket connection handling."""
    await websocket_manager.connect(mock_websocket)
    assert mock_websocket in websocket_manager.active_connections


@pytest.mark.asyncio
@pytest.mark.websocket
async def test_websocket_broadcast(websocket_manager, connected_websocket):
    """Test WebSocket message broadcasting."""
    message = {
        "type": "workflow_update",
        "data": {
            "adw_id": "TEST-001",
            "status": "completed"
        }
    }

    await websocket_manager.broadcast(message)

    # Verify message was sent to connected clients
    connected_websocket.send_json.assert_called_once()
```

### WebSocket Disconnect Test

```python
@pytest.mark.asyncio
@pytest.mark.websocket
async def test_websocket_disconnect(websocket_manager, mock_websocket):
    """Test WebSocket disconnection handling."""
    await websocket_manager.connect(mock_websocket)
    assert mock_websocket in websocket_manager.active_connections

    websocket_manager.disconnect(mock_websocket)
    assert mock_websocket not in websocket_manager.active_connections
```

## 5. Mock External API Test Examples

### Mocked GitHub Integration

```python
def test_github_workflow_integration(integration_client, mock_github_api):
    """Test workflow that calls GitHub API."""
    response = integration_client.post(
        "/api/issues/42/process",
        json={"template": "adw_sdlc_iso"}
    )
    assert response.status_code == 200

    # Verify GitHub client was called
    mock_github_api.get_issue.assert_called_once_with(42)
```

### Mocked OpenAI Integration

```python
def test_sql_generation_openai(integration_client, mock_openai_api):
    """Test SQL generation using mocked OpenAI."""
    payload = {
        "nl_query": "Get all users from last month",
        "provider": "openai"
    }
    response = integration_client.post("/api/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "SELECT" in data["query"]
```

### Mocked Anthropic Integration

```python
def test_sql_generation_anthropic(integration_client, mock_anthropic_api):
    """Test SQL generation using mocked Anthropic."""
    payload = {
        "nl_query": "Count users by country",
        "provider": "anthropic"
    }
    response = integration_client.post("/api/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "SELECT" in data.get("query", "")
```

## 6. Error Handling Test Examples

### 404 Not Found

```python
def test_nonexistent_endpoint(test_client):
    """Test accessing non-existent endpoint."""
    response = test_client.get("/api/nonexistent")
    assert response.status_code == 404
```

### 500 Server Error

```python
def test_server_error_handling(test_client):
    """Test server error handling."""
    # Assuming an endpoint that can trigger an error
    response = test_client.post(
        "/api/query",
        json={"nl_query": None}  # Invalid input
    )
    assert response.status_code in [400, 422]  # Bad request or validation error
```

### Timeout Handling

```python
@pytest.mark.asyncio
async def test_api_timeout():
    """Test handling of API timeouts."""
    import httpx

    # Configure short timeout
    async with httpx.AsyncClient(timeout=0.1) as client:
        try:
            response = await client.get("http://slow-endpoint.com/api")
            assert False, "Should have timed out"
        except httpx.TimeoutException:
            pass  # Expected
```

## 7. Coverage and Performance Examples

### Running Tests with Coverage

```bash
# Generate coverage report
pytest --cov=app --cov=core --cov=services --cov=utils \
       --cov-report=html --cov-report=term-missing

# Check coverage threshold
pytest --cov=app --cov-fail-under=80
```

### Running Tests in Parallel

```bash
# Run tests in parallel for speed
pytest -n auto

# Run with 4 workers
pytest -n 4
```

### Measuring Test Performance

```bash
# Show slowest tests
pytest --durations=10

# Mark slow tests
@pytest.mark.slow
def test_slow_operation():
    """This test takes a while."""
    # Long running test
    pass

# Run without slow tests
pytest -m "not slow"
```

## 8. End-to-End Workflow Test

```python
@pytest.mark.e2e
def test_complete_workflow(integration_client, mock_github_api, mock_anthropic_api):
    """Test complete workflow from issue to completion."""
    # Step 1: Create workflow from GitHub issue
    issue_payload = {
        "issue_number": 42,
        "template": "adw_sdlc_iso"
    }
    response = integration_client.post("/api/workflows/from-issue", json=issue_payload)
    assert response.status_code == 201
    workflow_data = response.json()
    adw_id = workflow_data["adw_id"]

    # Step 2: Process the workflow
    response = integration_client.post(f"/api/workflows/{adw_id}/process")
    assert response.status_code == 200

    # Step 3: Verify completion
    response = integration_client.get(f"/api/workflows/{adw_id}")
    assert response.status_code == 200
    final_workflow = response.json()
    assert final_workflow["status"] == "completed"

    # Step 4: Verify GitHub was updated
    mock_github_api.post_comment.assert_called()
```

## 9. Test Fixture Composition Examples

### Combining Multiple Fixtures

```python
def test_workflow_with_mocked_apis(
    integration_client,
    db_with_workflows,
    mock_github_api,
    mock_anthropic_api,
    mock_env_vars
):
    """Test workflow with multiple mocked dependencies."""
    # All fixtures are available and properly configured
    response = integration_client.get("/api/workflows")
    assert response.status_code == 200

    # Environment variables are mocked
    import os
    assert os.getenv("ANTHROPIC_API_KEY") == "test-anthropic-key-12345"
```

### Custom Test Data with Fixtures

```python
def test_with_sample_data(
    integration_client,
    sample_workflow_data,
    sample_github_issue,
    sample_sql_query_request
):
    """Test using sample data fixtures."""
    # Use sample data in tests
    assert sample_workflow_data["adw_id"] == "TEST-001"
    assert sample_github_issue["number"] == 42
    assert "nl_query" in sample_sql_query_request
```

## Running These Examples

```bash
# Run all examples
pytest TESTING_EXAMPLES.md

# Run only API tests
pytest TESTING_EXAMPLES.md::*api*

# Run only async tests
pytest TESTING_EXAMPLES.md -m asyncio

# Run only WebSocket tests
pytest TESTING_EXAMPLES.md -m websocket

# Run with coverage
pytest TESTING_EXAMPLES.md --cov

# Run with verbose output
pytest TESTING_EXAMPLES.md -v
```

## Key Testing Patterns

1. **Isolation**: Each test uses isolated fixtures (temp_test_db, temp_client)
2. **Mocking**: External APIs are mocked (mock_github_api, mock_anthropic_api)
3. **Async Support**: Use @pytest.mark.asyncio for async tests
4. **Fixtures**: Compose fixtures for test setup (test_client, integration_client)
5. **Markers**: Tag tests for selective execution (@pytest.mark.integration, @pytest.mark.e2e)
6. **Cleanup**: Fixtures handle automatic cleanup
7. **Type Hints**: Use type hints for better IDE support

## Next Steps

1. Copy these examples into your test files
2. Adapt them to your specific endpoints and use cases
3. Add assertions specific to your application
4. Mark tests with appropriate markers
5. Run tests with `pytest -v`
6. Generate coverage reports
7. Integrate into CI/CD pipeline
