# Test Infrastructure Architecture

## Directory Structure

```
tests/
├── conftest.py                              # 20 shared fixtures
├── README.md                                 # Comprehensive documentation
├── QUICK_START.md                            # Quick reference guide
├── INFRASTRUCTURE_SUMMARY.md                 # This summary
├── ARCHITECTURE.md                           # Architecture overview
│
├── integration/                              # Integration Tests
│   ├── conftest.py                          # 18 integration fixtures
│   ├── test_api_contracts.py                # Example API contract tests
│   └── test_server_startup.py               # Existing server startup tests
│
├── e2e/                                      # End-to-End Tests
│   ├── __init__.py                          # Package initialization
│   ├── conftest.py                          # 14 E2E fixtures
│   └── test_workflow_journey.py             # Example user journey tests
│
├── core/                                     # Core Module Tests
│   ├── test_file_processor.py
│   ├── test_llm_processor.py
│   ├── test_sql_processor.py
│   └── workflow_history_utils/
│       ├── test_github_client.py
│       ├── test_metrics.py
│       └── test_models.py
│
├── services/                                 # Service Layer Tests
│   ├── test_health_service.py
│   └── test_websocket_manager.py
│
└── utils/                                    # Utility Tests
    ├── test_db_connection.py
    └── test_process_runner.py
```

## Test Pyramid

```
                        ┌─────────────┐
                        │  E2E Tests  │  ← Slowest, Most Comprehensive
                        │   (e2e/)    │     - Complete user journeys
                        │             │     - Full system integration
                        │ ~5-30s each │     - Minimal mocking
                        └─────────────┘
                              ▲
                              │
                    ┌─────────────────────┐
                    │ Integration Tests   │  ← Medium Speed, Real Components
                    │   (integration/)    │     - API contract testing
                    │                     │     - Database operations
                    │    ~1-5s each       │     - Service interactions
                    └─────────────────────┘     - Mock external APIs
                              ▲
                              │
                ┌───────────────────────────────┐
                │        Unit Tests             │  ← Fast, Isolated
                │   (core/, services/, utils/)  │     - Pure functions
                │                               │     - Single components
                │         <100ms each           │     - Heavy mocking
                └───────────────────────────────┘
```

## Fixture Hierarchy

```
conftest.py (Root - 20 fixtures)
├── Database Fixtures
│   ├── temp_test_db ──────────────────┐
│   ├── temp_db_connection             │
│   └── init_workflow_history_schema   │
│                                       │
├── API Testing Fixtures                │
│   ├── test_client                     │
│   └── test_client_with_db ────────────┤
│                                       │
├── Environment Fixtures                │
│   ├── mock_env_vars                   │
│   ├── mock_openai_api_key             │
│   └── mock_anthropic_api_key          │
│                                       │
└── Mock Service Fixtures               │
    ├── mock_websocket                  │
    ├── mock_github_client              │
    └── mock_llm_client                 │
                                        │
integration/conftest.py (18 fixtures)  │
├── Integration Setup                   │
│   ├── integration_test_db ────────────┘
│   ├── integration_app
│   └── integration_client
│
├── Database with Data
│   └── db_with_workflows
│
├── External API Mocks
│   ├── mock_github_api
│   ├── mock_openai_api
│   └── mock_anthropic_api
│
└── Service Instances
    ├── health_service
    ├── workflow_service
    └── websocket_manager
                    │
e2e/conftest.py (14 fixtures)
├── E2E Environment            │
│   ├── e2e_test_environment   │
│   └── e2e_database ──────────┘
│
├── ADW Workflow Testing
│   ├── adw_test_workspace
│   └── adw_state_fixture
│
├── User Journey Testing
│   ├── user_journey_context
│   └── e2e_test_client
│
└── Performance & Validation
    ├── performance_monitor
    ├── workflow_execution_harness
    └── response_validator
```

## Data Flow in Tests

### Unit Test Flow
```
Test Function
    ↓
Mock Dependencies
    ↓
Execute Function
    ↓
Assert Results
```

### Integration Test Flow
```
Test Function
    ↓
integration_client (FastAPI TestClient)
    ↓
Real FastAPI App
    ↓
Real Database (integration_test_db)
    ↓
Mock External APIs (GitHub, OpenAI, Anthropic)
    ↓
Assert Response
```

### E2E Test Flow
```
Test Function
    ↓
e2e_test_client
    ↓
Full Application Stack
    ├── HTTP Endpoints
    ├── WebSocket Connections
    ├── Real Database (e2e_database)
    ├── Service Layer
    └── Mock External APIs
    ↓
Multi-Step User Journey
    ├── Step 1: Create Resource
    ├── Step 2: Monitor Status
    ├── Step 3: Retrieve Results
    └── Step 4: Validate Analytics
    ↓
Assert Complete Workflow
```

## Fixture Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│                     temp_test_db                            │
│                   (Base Database)                           │
└──────────────┬──────────────────────────────────────────────┘
               │
               ├──────────────────────────────────────────┐
               │                                          │
               ▼                                          ▼
┌──────────────────────────┐              ┌───────────────────────────┐
│  temp_db_connection      │              │  integration_test_db      │
│  (Open Connection)       │              │  (Full Schema)            │
└──────────────┬───────────┘              └───────────┬───────────────┘
               │                                      │
               ▼                                      │
┌──────────────────────────┐                         │
│ init_workflow_history_   │                         │
│ schema (With Tables)     │                         │
└──────────────────────────┘                         │
                                                      ▼
                                           ┌───────────────────────────┐
                                           │  db_with_workflows        │
                                           │  (With Sample Data)       │
                                           └───────────┬───────────────┘
                                                       │
                                                       ▼
                                           ┌───────────────────────────┐
                                           │  integration_client       │
                                           │  (Full API Testing)       │
                                           └───────────────────────────┘
```

## Test Execution Workflow

### Running Integration Tests

```
pytest -m integration
    ↓
Load conftest.py (root)
    ├── Register markers
    ├── Load shared fixtures
    └── Set up pytest configuration
    ↓
Load integration/conftest.py
    ├── Load integration fixtures
    ├── Create test database
    └── Set up external API mocks
    ↓
Execute Integration Tests
    ├── Create integration_client
    ├── Initialize test database
    ├── Mock external dependencies
    └── Run test scenarios
    ↓
Cleanup
    ├── Close database connections
    ├── Delete temporary files
    └── Reset mocks
```

### Running E2E Tests

```
pytest -m e2e
    ↓
Load conftest.py (root)
    ↓
Load integration/conftest.py
    ↓
Load e2e/conftest.py
    ├── Create e2e_test_environment
    ├── Initialize e2e_database with seed data
    ├── Set up ADW workspace
    └── Configure performance monitoring
    ↓
Execute E2E Tests
    ├── Simulate user journey
    ├── Execute multi-step workflows
    ├── Track performance metrics
    └── Validate complete system behavior
    ↓
Cleanup
    ├── Remove test environment
    ├── Delete databases
    ├── Clean up workspaces
    └── Generate performance reports
```

## Mocking Strategy

### What We Mock

```
External APIs (Always Mocked)
├── GitHub API
│   ├── Issue retrieval
│   ├── Comment posting
│   └── Status updates
│
├── OpenAI API
│   ├── Chat completions
│   ├── SQL generation
│   └── Token usage
│
└── Anthropic API
    ├── Message creation
    ├── SQL generation
    └── Token usage
```

### What We Don't Mock

```
Internal Components (Real in Integration/E2E)
├── FastAPI Application
│   ├── Route handlers
│   ├── Request validation
│   └── Response serialization
│
├── SQLite Database
│   ├── Schema creation
│   ├── Query execution
│   └── Transaction management
│
├── Service Layer
│   ├── HealthService
│   ├── WorkflowService
│   └── WebSocketManager
│
└── Core Business Logic
    ├── SQL processing
    ├── Workflow history
    └── Analytics calculation
```

## Test Isolation Strategy

```
Each Test Gets:
├── Fresh Database
│   └── Temporary file deleted after test
│
├── Isolated Environment
│   └── Mock environment variables
│
├── Clean Service State
│   └── New service instances per test
│
└── Independent Mocks
    └── Reset mocks between tests
```

## Performance Characteristics

```
Unit Tests
├── Execution Time: < 100ms each
├── Total Suite: < 10 seconds
└── Run Frequency: Every commit

Integration Tests
├── Execution Time: 1-5s each
├── Total Suite: < 2 minutes
└── Run Frequency: Before merge

E2E Tests
├── Execution Time: 5-30s each
├── Total Suite: < 10 minutes
└── Run Frequency: Before release
```

## Extension Points

### Adding New Fixtures

```
1. Choose Appropriate conftest.py
   ├── tests/conftest.py → All tests
   ├── tests/integration/conftest.py → Integration tests
   └── tests/e2e/conftest.py → E2E tests

2. Follow Naming Convention
   ├── test_* → Test functions
   ├── mock_* → Mock fixtures
   └── *_fixture → Data/context fixtures

3. Document Fixture
   ├── Docstring with usage example
   ├── Type hints for parameters
   └── Note cleanup behavior
```

### Adding New Test Markers

```python
# In conftest.py pytest_configure()
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "custom: marks tests as custom category"
    )
```

### Adding New Test Categories

```
1. Create Directory
   tests/new_category/

2. Add conftest.py
   tests/new_category/conftest.py

3. Add Category-Specific Fixtures
   @pytest.fixture
   def category_specific_fixture():
       pass

4. Write Tests
   tests/new_category/test_*.py
```

## Key Design Decisions

### 1. Temporary Databases
**Why**: Ensures test isolation and prevents pollution of production DB
**How**: Each test gets a fresh temporary SQLite file

### 2. Real Components in Integration Tests
**Why**: Validates actual component interactions
**How**: Use real FastAPI app, real database, real services

### 3. Mocked External APIs
**Why**: Prevents costs, flaky tests, and external dependencies
**How**: Mock at the API client level, not the business logic level

### 4. Fixture Hierarchy
**Why**: Promotes reuse and composition
**How**: Base fixtures in root, specialized fixtures in subdirectories

### 5. Automatic Cleanup
**Why**: Prevents test pollution and resource leaks
**How**: Use pytest fixture yield pattern and context managers

## Integration with CI/CD

```yaml
# Example GitHub Actions
- name: Run Unit Tests
  run: pytest -m unit --cov=. --cov-report=xml

- name: Run Integration Tests
  run: pytest -m integration --cov=. --cov-report=xml

- name: Run E2E Tests (Nightly)
  run: pytest -m e2e --cov=. --cov-report=xml
  if: github.event_name == 'schedule'
```

## Troubleshooting Decision Tree

```
Test Fails
    │
    ├─→ ImportError?
    │   └─→ Check: Running from app/server/ directory?
    │
    ├─→ Database Locked?
    │   └─→ Use: temp_test_db fixture for isolation
    │
    ├─→ Fixture Not Found?
    │   └─→ Check: Fixture in correct conftest.py?
    │
    ├─→ Async Test Hangs?
    │   └─→ Add: @pytest.mark.asyncio decorator
    │
    └─→ External API Error?
        └─→ Use: mock_github_api, mock_openai_api fixtures
```

## Summary

This architecture provides:

- **Clear Separation**: Unit/Integration/E2E clearly delineated
- **Reusable Components**: 52 fixtures across 3 levels
- **Fast Feedback**: Tests organized by speed
- **Isolation**: Each test independent
- **Realistic Testing**: Real components where appropriate
- **Comprehensive Coverage**: From unit to full system
- **Easy Extension**: Add fixtures and tests easily
- **CI/CD Ready**: Designed for automated testing

The infrastructure follows testing best practices while being practical and easy to use.
