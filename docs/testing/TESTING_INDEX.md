# Testing Setup Index

Complete index of testing resources, documentation, and guides for the FastAPI server.

## Quick Links

### Getting Started
- **[TESTING.md](TESTING.md)** - Main testing documentation and setup guide
- **[TESTING_EXAMPLES.md](TESTING_EXAMPLES.md)** - 50+ concrete test examples
- **[E2E_TESTING_REPORT.md](E2E_TESTING_REPORT.md)** - Complete installation report

### Configuration Files
- `pyproject.toml` - Project configuration with test dependencies
- `tests/conftest.py` - Shared test fixtures and configuration
- `tests/integration/conftest.py` - Integration test fixtures

### Test Directories
- `tests/` - Unit and integration tests
- `tests/integration/` - Integration tests
- `tests/core/` - Core module tests
- `tests/utils/` - Utility tests

## What's Installed

### Testing Framework
- **pytest** 8.4.1 - Test runner
- **pytest-asyncio** 1.3.0 - Async test support
- **pytest-cov** 7.0.0 - Coverage plugin
- **coverage** 7.12.0 - Code coverage tool

### HTTP Testing
- **httpx** 0.28.1 - Async HTTP client
- **FastAPI TestClient** - Synchronous HTTP testing
- **requests** - Already available

### Testing Utilities
- **pytest-mock** 3.15.1 - Enhanced mocking
- **pytest-xdist** 3.8.0 - Parallel test execution
- **pytest-clarity** 1.0.1 - Better assertion output

### WebSocket Support
- **websockets** 15.0.1 - WebSocket protocol
- **wsproto** 1.3.1 - WebSocket implementation

## Available Test Fixtures

### HTTP Testing (30+ fixtures)
```python
# From tests/conftest.py
test_client
test_client_with_db
integration_client
temp_test_db
temp_db_connection
integration_test_db
db_with_workflows
```

### WebSocket Testing
```python
mock_websocket
websocket_manager
connected_websocket
```

### API Mocking
```python
mock_github_api
mock_openai_api
mock_anthropic_api
```

### Environment Configuration
```python
mock_env_vars
mock_openai_api_key
mock_anthropic_api_key
```

### Test Data
```python
sample_workflow_data
sample_github_issue
sample_sql_query_request
sample_workflow_lifecycle_data
```

## Running Tests

### Basic Commands
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_workflow_history.py

# Run specific test class
pytest tests/test_workflow_history.py::TestWorkflowHistory

# Run specific test function
pytest tests/test_workflow_history.py::test_function_name
```

### By Category
```bash
# Run only integration tests
pytest -m integration

# Run only E2E tests
pytest -m e2e

# Run only WebSocket tests
pytest -m websocket

# Run only async tests
pytest -m asyncio

# Exclude slow tests
pytest -m "not slow"
```

### With Coverage
```bash
# Generate HTML coverage report
pytest --cov=app --cov=core --cov=services --cov=utils --cov-report=html

# Show coverage in terminal
pytest --cov=app --cov=core --cov=services --cov=utils --cov-report=term-missing

# Enforce minimum coverage
pytest --cov=app --cov-fail-under=80
```

### Parallel Execution
```bash
# Run tests in parallel (auto-detect CPU count)
pytest -n auto

# Run with specific number of workers
pytest -n 4

# Show distribution of tests
pytest -n auto -v
```

### Performance Analysis
```bash
# Show 10 slowest tests
pytest --durations=10

# Only run tests marked as "not slow"
pytest -m "not slow"

# Run with timing information
pytest -v --tb=short --durations=5
```

## Writing Tests

### Basic API Test
```python
def test_health_endpoint(test_client):
    """Test health check endpoint."""
    response = test_client.get("/api/health")
    assert response.status_code == 200
```

### Async Test
```python
@pytest.mark.asyncio
async def test_async_operation():
    """Test async function."""
    result = await some_async_function()
    assert result is not None
```

### WebSocket Test
```python
@pytest.mark.asyncio
@pytest.mark.websocket
async def test_websocket(websocket_manager, mock_websocket):
    """Test WebSocket functionality."""
    await websocket_manager.connect(mock_websocket)
    assert mock_websocket in websocket_manager.active_connections
```

### Database Test
```python
def test_database_operation(integration_client, db_with_workflows):
    """Test with pre-populated database."""
    response = integration_client.get("/api/workflows")
    assert response.status_code == 200
    assert len(response.json()) > 0
```

### Mocked API Test
```python
def test_with_mocked_api(integration_client, mock_github_api):
    """Test with mocked external API."""
    response = integration_client.post("/api/issues/42/process")
    assert response.status_code == 200
```

## Pytest Configuration

### Custom Markers
Located in `pyproject.toml`:
- `@pytest.mark.asyncio` - Async tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.websocket` - WebSocket tests
- `@pytest.mark.slow` - Slow tests (optional)

### Async Configuration
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

This automatically handles event loop creation and teardown for async tests.

## Documentation Files

### TESTING.md (Comprehensive Guide)
- Testing stack overview
- Framework configuration
- Available fixtures
- Running tests commands
- Writing tests guide
- Coverage configuration
- CI/CD integration
- Troubleshooting

### TESTING_EXAMPLES.md (Code Examples)
- 9 categories of examples
- 50+ concrete code snippets
- All testing patterns covered
- Copy-paste ready code

### E2E_TESTING_REPORT.md (Technical Report)
- Installation verification
- Requirement fulfillment
- Configuration details
- Package versions
- Capability matrix
- Best practices

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── test_*.py                      # Unit tests
├── core/                          # Core module tests
│   ├── test_*.py
│   └── workflow_history_utils/
│       └── test_*.py
├── utils/                         # Utility tests
│   └── test_*.py
├── integration/                   # Integration tests
│   ├── conftest.py               # Integration fixtures
│   └── test_*.py
└── e2e/                          # E2E tests (if added)
    └── test_*.py
```

## Coverage Goals

Recommended minimum coverage:
- **Target**: 80% line coverage
- **Modules**: app, core, services, utils
- **Excluded**: __init__.py, test files

Run coverage:
```bash
pytest --cov=app --cov=core --cov=services --cov=utils \
       --cov-report=html --cov-report=term-missing
```

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run tests with coverage
  run: |
    pytest --cov=app --cov=core --cov=services --cov=utils \
           --cov-report=xml --cov-fail-under=80
```

### Test Suite Phases
1. **Fast tests** (unit): < 1 second
2. **Integration tests**: < 30 seconds
3. **E2E tests**: < 5 minutes
4. **Coverage report**: < 1 minute

## Troubleshooting

### Async Test Issues
- Ensure `@pytest.mark.asyncio` is present
- Check `asyncio_mode = "auto"` in pyproject.toml
- Verify pytest-asyncio is installed

### Database Locks
- Use isolated fixtures (temp_test_db)
- Avoid production database paths
- Ensure proper connection cleanup

### Import Errors
- Check pytest is installed: `pytest --version`
- Verify plugins are loaded: `pytest --version` (look for plugin list)
- Ensure Python path is correct

### WebSocket Errors
- Mark tests with `@pytest.mark.asyncio`
- Use proper mock/real WebSocket fixtures
- Check websockets package is installed

## Version Compatibility

**Tested with:**
- Python: 3.12.11 (compatible with 3.10+)
- FastAPI: 0.115.13
- pytest: 8.4.1
- All dependencies: See pyproject.toml

## Support Resources

### Official Documentation
- [pytest docs](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [FastAPI testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [httpx docs](https://www.python-httpx.org/)

### Common Patterns
See TESTING_EXAMPLES.md for patterns:
- API endpoint testing
- Async operations
- Database transactions
- WebSocket connections
- API mocking
- Error handling
- Full workflows

## Next Steps

1. **Review documentation**
   - Start with TESTING.md
   - Look at TESTING_EXAMPLES.md

2. **Write your first test**
   - Use a simple example from TESTING_EXAMPLES.md
   - Run with `pytest -v`
   - Verify it passes

3. **Expand test coverage**
   - Add tests for each endpoint
   - Cover happy path and error cases
   - Use appropriate fixtures

4. **Setup CI/CD**
   - Add test runner to pipeline
   - Configure coverage gates
   - Setup automated testing

5. **Monitor quality**
   - Generate coverage reports
   - Track test performance
   - Add more E2E tests

## Quick Reference

### Install Test Dependencies
```bash
# All test dependencies
pip install pytest pytest-asyncio pytest-cov httpx pytest-mock pytest-xdist pytest-clarity

# Or via pyproject.toml
pip install -e ".[test,integration]"
```

### Run Common Commands
```bash
pytest                              # All tests
pytest -v                           # Verbose
pytest -m integration               # Integration only
pytest --cov --cov-report=html     # With coverage
pytest -n auto                      # Parallel
pytest -k "workflow"                # By name pattern
pytest --lf                         # Last failed
pytest --durations=10               # Slowest tests
```

### Check Status
```bash
pytest --collect-only              # List all tests
pytest --markers                   # List all markers
pytest -p no:cacheprovider --version  # Pytest version
```

## Summary

The testing infrastructure is fully operational with:
- 11 installed testing packages
- 30+ reusable fixtures
- 3 comprehensive documentation files
- 50+ code examples
- All 5 required capabilities
- Full async/WebSocket support
- Database isolation
- API mocking
- Coverage measurement

Ready for comprehensive E2E integration testing.
