# Testing Setup and E2E Integration Testing Guide

## Overview

The server project now has a comprehensive testing stack configured for API endpoint testing, WebSocket integration, and end-to-end workflow validation.

### Testing Stack Installed

This document describes the complete testing infrastructure for the FastAPI backend server.

## Installed Dependencies

### Core Testing Framework
- **pytest** 8.4.1 - Test framework with powerful assertion introspection
- **pytest-asyncio** 1.3.0 - Support for async/await test functions
- **pytest-cov** 7.0.0 - Coverage measurement plugin
- **coverage** 7.12.0 - Code coverage tool

### HTTP Testing
- **httpx** 0.28.1 - Modern async HTTP client (used by FastAPI TestClient)
- **FastAPI TestClient** (from fastapi 0.115.13) - Synchronous HTTP client for testing endpoints

### Async Support
- **pytest-asyncio** 1.3.0 - Enables async test functions with `@pytest.mark.asyncio`
- **websockets** 15.0.1 - WebSocket protocol implementation

### Testing Utilities
- **pytest-mock** 3.15.1 - Enhanced mocking and fixture support
- **pytest-xdist** 3.8.0 - Parallel test execution (use `-n auto` flag)
- **pytest-clarity** 1.0.1 - Better assertion output formatting

### Data Validation
- **pydantic** 2.11.7 - Model validation (already in dependencies)

## Pytest Configuration

File: `/Users/Warmonger0/tac/tac-webbuilder/app/server/pyproject.toml`

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
asyncio_mode = "auto"
addopts = "-v --strict-markers"
markers = [
    "asyncio: marks tests as async",
    "integration: marks tests as integration tests",
    "e2e: marks tests as end-to-end tests",
    "websocket: marks tests that use WebSocket",
]
```

## Available Test Fixtures

### FastAPI HTTP Testing
- **test_client** - FastAPI TestClient for synchronous endpoint testing
- **test_client_with_db** - TestClient with isolated test database
- **integration_client** - Full integration test client with real app

### Database Testing
- **temp_test_db** - Isolated temporary SQLite database
- **temp_db_connection** - Direct database connection to temp test DB
- **integration_test_db** - Full-schema test database
- **db_with_workflows** - Pre-populated test database with sample workflows
- **init_workflow_history_schema** - Database schema initialization

### WebSocket Testing
- **mock_websocket** - Mock WebSocket connection
- **websocket_manager** - Real WebSocket ConnectionManager
- **connected_websocket** - Pre-connected mock WebSocket

### Environment & Configuration
- **mock_env_vars** - Mocked environment variables for tests
- **mock_openai_api_key** - Mocked OpenAI credentials
- **mock_anthropic_api_key** - Mocked Anthropic credentials
- **mock_github_api** - Mocked GitHub API responses
- **mock_openai_api** - Mocked OpenAI API responses
- **mock_anthropic_api** - Mocked Anthropic API responses

### Test Data
- **sample_workflow_data** - Sample workflow metadata
- **sample_github_issue** - Sample GitHub issue data
- **sample_sql_query_request** - Sample SQL query request
- **sample_workflow_lifecycle_data** - Complete workflow lifecycle data

### Utilities
- **server_root** - Path to server directory
- **project_root** - Path to project root
- **temp_directory** - Temporary directory for test files
- **cleanup_test_data** - Cleanup fixture for test artifacts
- **cleanup_db_files** - Cleanup fixture for database files

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_specific.py

# Run specific test class
pytest tests/test_specific.py::TestClassName

# Run specific test function
pytest tests/test_specific.py::test_function_name
```

### Running by Test Category

```bash
# Run only unit tests (exclude integration)
pytest -m "not integration"

# Run only integration tests
pytest -m integration

# Run only E2E tests
pytest -m e2e

# Run WebSocket tests
pytest -m websocket

# Run async tests
pytest -m asyncio
```

### Running with Coverage

```bash
# Generate coverage report
pytest --cov=app --cov=core --cov=services --cov=utils --cov-report=html

# View coverage in terminal
pytest --cov=app --cov=core --cov=services --cov=utils --cov-report=term-missing

# Set coverage threshold
pytest --cov=app --cov-fail-under=80
```

### Parallel Execution

```bash
# Run tests in parallel (requires pytest-xdist)
pytest -n auto

# Run with specific number of workers
pytest -n 4
```

### Watch Mode (with pytest-watch)

```bash
# Auto-run tests on file changes (requires pytest-watch)
ptw -- -v
```

## Writing Tests

### API Endpoint Test Example

```python
def test_api_health_check(test_client):
    """Test the health check endpoint."""
    response = test_client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_workflow(test_client):
    """Test workflow creation endpoint."""
    response = test_client.post(
        "/api/workflows",
        json={
            "nl_input": "Fix authentication bug",
            "table": "issues"
        }
    )
    assert response.status_code == 201
    assert "adw_id" in response.json()
```

### Async Test Example

```python
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    """Test async function."""
    result = await some_async_function()
    assert result is not None
```

### WebSocket Test Example

```python
import pytest

@pytest.mark.asyncio
@pytest.mark.websocket
async def test_websocket_connection(websocket_manager, mock_websocket):
    """Test WebSocket connection and message handling."""
    await websocket_manager.connect(mock_websocket)

    # Broadcast message to all connections
    await websocket_manager.broadcast({
        "type": "workflow_update",
        "data": {"adw_id": "TEST-001", "status": "completed"}
    })

    # Verify message was sent
    mock_websocket.send_json.assert_called()
```

### Integration Test with Database

```python
def test_workflow_integration(integration_client, db_with_workflows):
    """Test full workflow integration."""
    response = integration_client.get("/api/workflows?limit=10")
    assert response.status_code == 200
    workflows = response.json()
    assert len(workflows) > 0
    assert workflows[0]["adw_id"] == "TEST-001"
```

### Mocking External APIs

```python
def test_github_integration(integration_client, mock_github_api):
    """Test GitHub API integration with mock."""
    response = integration_client.post(
        "/api/issues/42/comment",
        json={"body": "Test comment"}
    )
    assert response.status_code == 200
```

## Conftest Files

### Main Configuration: `tests/conftest.py`

Contains:
- Path fixtures (server_root, project_root)
- Database fixtures
- FastAPI TestClient fixtures
- Environment variable mocking
- Service mock fixtures
- Test data fixtures
- Pytest configuration with custom markers

### Integration Configuration: `tests/integration/conftest.py`

Contains:
- Full app integration fixtures
- Service integration fixtures
- External API mock fixtures
- WebSocket integration fixtures
- Background task fixtures

## Test Structure

```
tests/
├── conftest.py                          # Shared fixtures
├── __init__.py
├── test_workflow_analytics.py           # Unit tests
├── test_template_router.py              # Unit tests
├── test_workflow_history.py             # Unit tests
├── core/                                # Core module tests
│   ├── __init__.py
│   ├── test_llm_processor.py
│   ├── test_file_processor.py
│   ├── test_sql_processor.py
│   └── workflow_history_utils/
│       └── test_*.py
├── utils/                               # Utility tests
│   └── test_*.py
├── integration/                         # Integration tests
│   ├── conftest.py                      # Integration fixtures
│   ├── __init__.py
│   └── test_server_startup.py
└── e2e/                                 # E2E tests (optional)
    └── test_*.py
```

## Coverage Goals

Current coverage configuration targets:
- Minimum line coverage: 80%
- Core modules (app, core, services, utils)
- Test data directories excluded

Run: `pytest --cov=app --cov=core --cov=services --cov=utils --cov-report=html`

## CI/CD Integration

The testing stack is ready for CI/CD pipelines:

```bash
# Full test suite with coverage
pytest --cov=app --cov=core --cov=services --cov=utils \
       --cov-report=xml --cov-report=term-missing \
       --junitxml=test-results.xml

# Fast subset for quick checks
pytest -m "not slow" --tb=short

# Parallel execution for speed
pytest -n auto --tb=short
```

## Troubleshooting

### AsyncIO Test Issues

If async tests fail with "no running event loop" error:
- Ensure `asyncio_mode = "auto"` is in `pytest.ini_options`
- Use `@pytest.mark.asyncio` on async test functions
- Import `pytest_asyncio` is installed

### Database Lock Issues

If database tests fail with "database is locked":
- Use `temp_test_db` or `integration_test_db` fixtures
- Don't use production database paths
- Ensure proper connection cleanup in fixtures

### TestClient Import Issues

If TestClient import fails:
- Verify FastAPI is installed: `pip list | grep fastapi`
- Verify httpx is installed: `pip list | grep httpx`
- Restart Python environment

### WebSocket Test Issues

If WebSocket tests fail:
- Use `@pytest.mark.asyncio` for async WebSocket tests
- Use `mock_websocket` or `connected_websocket` fixtures
- Import `websockets` is installed

## Additional Resources

### Testing Best Practices
- Use fixtures for shared test setup
- Mark slow tests with `@pytest.mark.slow`
- Separate unit, integration, and E2E tests
- Mock external API calls
- Use temporary databases for data tests

### Documentation
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [httpx Documentation](https://www.python-httpx.org/)

## Dependency Versions

Last Updated: November 20, 2025

All dependencies are pinned in `pyproject.toml` under `[dependency-groups.test]` and `[dependency-groups.integration]` for reproducible test environments.
