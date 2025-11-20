# Test Infrastructure Documentation

This directory contains the complete test infrastructure for the TAC WebBuilder server.

## Directory Structure

```
tests/
├── conftest.py                          # Shared fixtures for all tests
├── integration/
│   ├── conftest.py                      # Integration test fixtures
│   ├── test_api_contracts.py           # API contract tests (example)
│   └── test_server_startup.py          # Server startup validation
├── e2e/
│   ├── conftest.py                      # E2E test fixtures
│   └── test_workflow_journey.py        # Complete workflow journey tests (example)
├── core/                                # Core module unit tests
├── services/                            # Service layer unit tests
├── utils/                               # Utility module unit tests
└── README.md                            # This file
```

## Test Levels

### Unit Tests (`tests/`)
Fast, isolated tests for individual functions and classes.

**Characteristics:**
- No external dependencies
- Mock all I/O operations
- Fast execution (< 100ms per test)
- Test single units of functionality

**Example:**
```python
def test_calculate_cost(sample_workflow_data):
    cost = calculate_workflow_cost(sample_workflow_data)
    assert cost > 0
```

### Integration Tests (`tests/integration/`)
Tests validating component interactions with real services.

**Characteristics:**
- Use real FastAPI app
- Use real SQLite database (temporary)
- Mock only external APIs (GitHub, OpenAI, Anthropic)
- Validate API contracts and data flow
- Moderate execution time (< 5s per test)

**Example:**
```python
@pytest.mark.integration
def test_workflow_creation_flow(integration_client, db_with_workflows):
    response = integration_client.post("/api/workflows/create", json={...})
    assert response.status_code == 200
```

### E2E Tests (`tests/e2e/`)
Complete user journey tests simulating real-world usage.

**Characteristics:**
- Minimal mocking (only external APIs)
- Full system validation
- Multi-step workflows
- Performance monitoring
- Slower execution (> 5s per test)

**Example:**
```python
@pytest.mark.e2e
def test_complete_workflow_lifecycle(workflow_execution_harness):
    # Create workflow
    result = workflow_execution_harness.execute_workflow({...})
    # Monitor progress
    # Verify completion
    assert result["status"] == "completed"
```

## Available Fixtures

### Core Fixtures (tests/conftest.py)

#### Database Fixtures
- **`temp_test_db`**: Temporary SQLite database file path
- **`temp_db_connection`**: Open database connection with row factory
- **`init_workflow_history_schema`**: Database with workflow_history schema

#### API Testing Fixtures
- **`test_client`**: FastAPI TestClient for endpoint testing
- **`test_client_with_db`**: TestClient with temporary database

#### Environment Fixtures
- **`mock_env_vars`**: Complete test environment variables
- **`mock_openai_api_key`**: Mock OpenAI API key
- **`mock_anthropic_api_key`**: Mock Anthropic API key

#### Mock Service Fixtures
- **`mock_websocket`**: Mock WebSocket for connection testing
- **`mock_github_client`**: Mock GitHub API client
- **`mock_llm_client`**: Mock LLM client (OpenAI/Anthropic)

#### Path Fixtures
- **`server_root`**: Path to app/server/ directory
- **`project_root`**: Path to tac-webbuilder/ root
- **`temp_directory`**: Temporary directory with auto-cleanup

#### Test Data Fixtures
- **`sample_workflow_data`**: Sample workflow metadata
- **`sample_github_issue`**: Sample GitHub issue data
- **`sample_sql_query_request`**: Sample query request

### Integration Fixtures (tests/integration/conftest.py)

#### Server Integration
- **`integration_test_db`**: Full database with complete schema
- **`integration_app`**: FastAPI app with test database
- **`integration_client`**: TestClient for integration testing

#### Database with Data
- **`db_with_workflows`**: Database pre-populated with sample workflows

#### WebSocket Integration
- **`websocket_manager`**: Real ConnectionManager instance
- **`connected_websocket`**: Pre-connected WebSocket mock

#### External API Mocks
- **`mock_github_api`**: Mocked GitHub API responses
- **`mock_openai_api`**: Mocked OpenAI API responses
- **`mock_anthropic_api`**: Mocked Anthropic API responses

#### Service Integration
- **`health_service`**: HealthService instance
- **`workflow_service`**: WorkflowService with test DB
- **`github_issue_service`**: GitHubIssueService with mocked API

#### Background Tasks
- **`background_task_manager`**: BackgroundTaskManager instance

#### Full Server
- **`running_server`**: Real server instance (slow, use sparingly)

### E2E Fixtures (tests/e2e/conftest.py)

#### Environment Setup
- **`e2e_test_environment`**: Complete isolated test environment
- **`e2e_database`**: Full database with realistic seed data

#### ADW Workflow Testing
- **`adw_test_workspace`**: Complete ADW workspace structure
- **`adw_state_fixture`**: ADW state for workflow testing

#### User Journey Testing
- **`user_journey_context`**: Context for complete user journeys
- **`e2e_test_client`**: Fully configured client for E2E testing

#### Performance Monitoring
- **`performance_monitor`**: Track response times and metrics

#### Workflow Execution
- **`workflow_execution_harness`**: Complete workflow execution testing
- **`workflow_factory`**: Factory for creating test workflows

#### Full Stack
- **`full_stack_context`**: Complete stack (HTTP, WebSocket, DB)
- **`mock_external_services_e2e`**: All external services mocked

#### Validation
- **`response_validator`**: Helpers for validating API responses

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Level
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# E2E tests only
pytest -m e2e
```

### Run Fast Tests (Exclude Slow)
```bash
pytest -m "not slow"
```

### Run with Coverage
```bash
pytest --cov=. --cov-report=html
```

### Run Specific Test File
```bash
pytest tests/integration/test_api_contracts.py
```

### Run Specific Test
```bash
pytest tests/integration/test_api_contracts.py::TestHealthEndpoints::test_health_check_returns_200
```

### Run with Verbose Output
```bash
pytest -v
```

### Run with Print Statements
```bash
pytest -s
```

## Test Markers

Available pytest markers for organizing tests:

- **`@pytest.mark.unit`**: Unit tests (fast, isolated)
- **`@pytest.mark.integration`**: Integration tests (real components)
- **`@pytest.mark.e2e`**: End-to-end tests (complete journeys)
- **`@pytest.mark.slow`**: Slow tests (> 5 seconds)
- **`@pytest.mark.requires_api_key`**: Tests requiring API keys
- **`@pytest.mark.requires_github`**: Tests requiring GitHub integration
- **`@pytest.mark.asyncio`**: Async tests (auto-detected by pytest-asyncio)

### Using Markers
```python
@pytest.mark.integration
@pytest.mark.slow
def test_complex_integration():
    # This test is marked as both integration and slow
    pass
```

## Writing New Tests

### Unit Test Example
```python
# tests/core/test_my_module.py
import pytest

@pytest.mark.unit
def test_my_function():
    """Test my_function with isolated inputs."""
    result = my_function("input")
    assert result == "expected"
```

### Integration Test Example
```python
# tests/integration/test_my_integration.py
import pytest

@pytest.mark.integration
def test_api_endpoint(integration_client, integration_test_db):
    """Test API endpoint with real database."""
    response = integration_client.post("/api/endpoint", json={...})
    assert response.status_code == 200
```

### E2E Test Example
```python
# tests/e2e/test_my_journey.py
import pytest

@pytest.mark.e2e
def test_user_journey(e2e_test_client, e2e_database):
    """Test complete user workflow from start to finish."""
    # Step 1: Create resource
    create_response = e2e_test_client.post("/api/create", json={...})
    assert create_response.status_code == 201

    # Step 2: Retrieve resource
    get_response = e2e_test_client.get("/api/resource/1")
    assert get_response.status_code == 200

    # Step 3: Update resource
    update_response = e2e_test_client.put("/api/resource/1", json={...})
    assert update_response.status_code == 200
```

### Async Test Example
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_websocket_connection(websocket_manager, mock_websocket):
    """Test WebSocket connection lifecycle."""
    await websocket_manager.connect(mock_websocket)
    assert mock_websocket in websocket_manager.active_connections
```

## Best Practices

### 1. Use Appropriate Test Level
- **Unit**: Testing pure functions, calculations, data transformations
- **Integration**: Testing API endpoints, database operations, service interactions
- **E2E**: Testing complete user workflows, multi-step processes

### 2. Leverage Fixtures
```python
# Good: Use fixtures for setup
def test_with_fixture(temp_test_db, sample_workflow_data):
    # Test uses pre-configured dependencies
    pass

# Avoid: Manual setup in every test
def test_without_fixture():
    db = create_temp_database()  # Repetitive
    data = {...}  # Repetitive
    # Test code
```

### 3. Mock External Dependencies
```python
# Good: Mock external APIs
@pytest.mark.integration
def test_with_mock(integration_client, mock_github_api):
    # GitHub API calls are mocked
    response = integration_client.get("/api/github/issues/42")
    assert response.status_code == 200

# Avoid: Real API calls in tests (slow, costly, unreliable)
```

### 4. Clean Test Data
```python
# Good: Fixtures handle cleanup automatically
def test_with_cleanup(temp_directory):
    test_file = temp_directory / "test.txt"
    test_file.write_text("data")
    # Cleanup happens automatically

# Avoid: Manual cleanup (can be missed)
def test_manual_cleanup():
    create_file("test.txt")
    # What if test fails before cleanup?
    cleanup_file("test.txt")
```

### 5. Write Descriptive Test Names
```python
# Good: Clear what is being tested
def test_workflow_creation_returns_201_with_valid_data():
    pass

# Avoid: Vague test names
def test_workflow():
    pass
```

### 6. Test One Thing Per Test
```python
# Good: Focused test
def test_workflow_status_updates_correctly():
    # Test only status updates
    pass

# Avoid: Testing multiple unrelated things
def test_everything():
    # Tests workflow, database, API, WebSocket all at once
    pass
```

### 7. Use Parametrize for Similar Tests
```python
# Good: Parameterized test
@pytest.mark.parametrize("status,expected_code", [
    ("completed", 200),
    ("failed", 200),
    ("pending", 200),
])
def test_workflow_status_codes(status, expected_code):
    # Test multiple scenarios efficiently
    pass
```

## Debugging Tests

### Run Failed Tests Only
```bash
pytest --lf  # Run last failed
pytest --ff  # Run failed first, then others
```

### Run with Debugger
```bash
pytest --pdb  # Drop into debugger on failure
```

### Show Print Statements
```bash
pytest -s  # Show print() output
```

### Verbose Output
```bash
pytest -vv  # Extra verbose
```

### Show Fixture Setup
```bash
pytest --setup-show
```

## Common Issues and Solutions

### Issue: Tests can't find modules
**Solution**: Ensure you're running pytest from `/app/server/` directory:
```bash
cd /path/to/tac-webbuilder/app/server
pytest
```

### Issue: Database locked errors
**Solution**: Use `temp_test_db` fixture to ensure isolated databases:
```python
def test_with_isolated_db(temp_test_db):
    # Each test gets its own database
    pass
```

### Issue: Async tests not working
**Solution**: Add `@pytest.mark.asyncio` decorator:
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

### Issue: External API calls during tests
**Solution**: Use mock fixtures from conftest.py:
```python
def test_with_mocked_api(mock_github_api, mock_anthropic_api):
    # All external APIs are mocked
    pass
```

## CI/CD Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    cd app/server
    pytest -m "not slow" --cov=. --cov-report=xml
```

## Contributing New Tests

When adding new tests:

1. **Choose appropriate test level** (unit/integration/e2e)
2. **Use existing fixtures** where possible
3. **Add new fixtures** to appropriate conftest.py if needed
4. **Mark tests** with appropriate markers
5. **Document complex test scenarios** with docstrings
6. **Ensure cleanup** happens automatically
7. **Test both success and failure paths**

## Further Reading

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
