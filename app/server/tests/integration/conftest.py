"""
Integration test fixtures and configuration.

This module provides fixtures specifically for integration tests that validate
component interactions, API contracts, database operations, and full workflow
execution across the server stack.

Integration tests use real components (database, FastAPI app, services) with
mocked external dependencies (GitHub API, OpenAI/Anthropic APIs).
"""

import asyncio
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
from collections.abc import Generator
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

# ============================================================================
# Python Path Setup for Integration Tests
# ============================================================================

# Ensure app/server directory is in Python path
server_root = Path(__file__).parent.parent.parent
if str(server_root) not in sys.path:
    sys.path.insert(0, str(server_root))

# ============================================================================
# Server Integration Fixtures
# ============================================================================


@pytest.fixture
def integration_test_db(monkeypatch) -> Generator[Path, None, None]:
    """
    Create temporary databases for integration tests (Post-Session 19).

    **Dual-Database Architecture:**
    This fixture sets up TWO separate databases:

    1. **workflow_history database** (SQLite):
       - Stores ADW workflow execution history
       - Uses DB_PATH constant (patched to temp file)
       - Legacy direct-access pattern (NOT via adapter)

    2. **Main application database** (PostgreSQL):
       - Stores phase_queue, planned_features, etc.
       - Uses adapter pattern via get_database_adapter()
       - Configured via environment variables (POSTGRES_*)

    **Why Two Databases?**
    - workflow_history predates Session 19 refactoring, still uses DB_PATH
    - Main database refactored to adapter pattern in Session 19
    - Both coexist during transition period

    **Fixture Setup:**
    - Creates temp SQLite file for workflow_history
    - Patches core.workflow_history_utils.database.schema.DB_PATH
    - Sets PostgreSQL env vars for main database adapter
    - Resets adapter factory cache before/after test

    Usage:
        def test_workflow_lifecycle(integration_test_db):
            from core.workflow_history_utils.database import insert_workflow_history
            row_id = insert_workflow_history(adw_id="TEST-001", ...)
            assert row_id > 0  # Uses SQLite via patched DB_PATH
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db_path = Path(f.name)

    # Reset database adapter before test to ensure clean state
    try:
        from database.factory import close_database_adapter
        close_database_adapter()
    except Exception:
        pass

    # Use monkeypatch to replace DB_PATH in schema module (only module that has it)
    import core.workflow_history_utils.database.schema as schema_module

    monkeypatch.setattr(schema_module, 'DB_PATH', temp_db_path)

    # Also reset the _db_adapter cache in schema module
    if hasattr(schema_module, '_db_adapter'):
        monkeypatch.setattr(schema_module, '_db_adapter', None)

    # Set environment variables for PostgreSQL adapter (required by get_database_adapter)
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "tac_webbuilder_test")
    monkeypatch.setenv("POSTGRES_USER", "tac_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "changeme")
    monkeypatch.setenv("DB_TYPE", "postgresql")

    # Initialize database schemas (with error handling)
    try:
        from core.workflow_history_utils.database import init_db
        init_db()
    except Exception as e:
        # Log but don't fail fixture - some tests may not use workflow_history DB
        import traceback
        print(f"\nWarning: workflow_history database initialization failed: {e}")
        traceback.print_exc()

    try:
        from services.phase_queue_schema import init_phase_queue_db
        init_phase_queue_db()
    except Exception as e:
        # Log but don't fail fixture - some tests may not use phase_queue DB
        import traceback
        print(f"\nWarning: phase_queue database initialization failed: {e}")
        traceback.print_exc()

    try:
        from services.work_log_schema import init_work_log_db
        init_work_log_db()
    except Exception as e:
        # Log but don't fail fixture - some tests may not use work_log DB
        import traceback
        print(f"\nWarning: work_log database initialization failed: {e}")
        traceback.print_exc()

    try:
        from core.context_review.database.schema import init_context_review_db
        init_context_review_db()
    except Exception as e:
        # Log but don't fail fixture - some tests may not use context_review DB
        import traceback
        print(f"\nWarning: context_review database initialization failed: {e}")
        traceback.print_exc()

    try:
        from core.workflow_history_utils.database import init_db
        init_db()
    except Exception as e:
        # Log but don't fail fixture - some tests may not use workflow_history DB
        import traceback
        print(f"\nWarning: workflow_history database initialization failed: {e}")
        traceback.print_exc()

    try:
        from core.adw_lock import init_adw_locks_table
        init_adw_locks_table()
    except Exception as e:
        # Log but don't fail fixture - some tests may not use adw_locks table
        import traceback
        print(f"\nWarning: adw_locks table initialization failed: {e}")
        traceback.print_exc()

    # Initialize PostgreSQL tables for integration tests
    try:
        from database import get_database_adapter
        adapter = get_database_adapter()
        # Verify connection works
        with adapter.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1, "PostgreSQL connection test failed"
        print(f"\n✓ PostgreSQL connection successful (tac_webbuilder_test)")
    except Exception as e:
        import traceback
        print(f"\nWarning: PostgreSQL connection test failed: {e}")
        traceback.print_exc()

    yield temp_db_path

    # Cleanup
    try:
        temp_db_path.unlink(missing_ok=True)
    except Exception:
        pass

    # Reset adapter after test
    try:
        from database.factory import close_database_adapter
        close_database_adapter()
    except Exception:
        pass


@pytest.fixture
def integration_app(integration_test_db: Path, monkeypatch):
    """
    Create FastAPI app instance with dual-database setup (Post-Session 19).

    **App Configuration:**
    - Fully configured FastAPI application
    - Real service instances (no mocking)
    - Test database isolation (SQLite + PostgreSQL)

    **Database Setup (Inherited from integration_test_db):**
    1. workflow_history → SQLite (via patched DB_PATH)
    2. Main database → PostgreSQL (via adapter pattern)

    **Additional Setup:**
    - Sets required server env vars (GITHUB_TOKEN, ports, etc.)
    - Resets adapter factory cache to pick up test env vars
    - Patches DB_PATH context for workflow_history import
    - Reloads database modules to apply patches

    **Adapter Reset Strategy:**
    Session 19 uses singleton adapter pattern. This fixture:
    - Closes existing adapter before test (close_database_adapter())
    - Forces factory to create new adapter with test env vars
    - Ensures no state leakage from previous tests

    Usage:
        def test_api_workflow(integration_app):
            client = TestClient(integration_app)
            response = client.get("/api/v1/health")
            assert response.status_code == 200
    """
    # Set required environment variables for server startup
    monkeypatch.setenv("FRONTEND_PORT", "3000")
    monkeypatch.setenv("BACKEND_PORT", "8000")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token-123")
    monkeypatch.setenv("GITHUB_REPO", "test/repo")

    # Set PostgreSQL environment variables (already set in integration_test_db, but ensure here)
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "tac_webbuilder_test")
    monkeypatch.setenv("POSTGRES_USER", "tac_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "changeme")
    monkeypatch.setenv("DB_TYPE", "postgresql")

    # Session 19: Reset global database adapter cache when environment changes
    # This ensures the adapter factory creates a new instance with updated env vars
    try:
        from database.factory import close_database_adapter
        close_database_adapter()
    except Exception:
        pass

    # Also reset the schema module's _db_adapter cache if it exists
    try:
        import core.workflow_history_utils.database.schema as schema_module
        if hasattr(schema_module, '_db_adapter'):
            schema_module._db_adapter = None
    except Exception:
        pass

    # Patch database path at module level before importing server
    import core.workflow_history_utils.database.schema as schema_module
    original_db_path = getattr(schema_module, 'DB_PATH', None)
    monkeypatch.setattr(schema_module, 'DB_PATH', integration_test_db)

    try:
        # Import server app (DB_PATH is now patched at module level)
        from server import app
        yield app
    except Exception as e:
        # If app import fails, provide detailed error
        import traceback
        print(f"\nError importing server app: {e}")
        traceback.print_exc()
        raise
    finally:
        # Restore original DB_PATH
        if original_db_path is not None:
            monkeypatch.setattr(schema_module, 'DB_PATH', original_db_path)


@pytest.fixture
def integration_client(integration_app) -> Generator[TestClient, None, None]:
    """
    Create TestClient for integration testing with full app context.

    This client can make requests to all API endpoints with a real database
    and service layer, but with mocked external dependencies.

    Usage:
        def test_submit_workflow(integration_client):
            response = integration_client.post("/api/v1/submit", json={
                "nl_query": "Show all users",
                "table": "users"
            })
            assert response.status_code == 200
    """
    with TestClient(integration_app) as client:
        # Clean up database tables before each test
        try:
            from database import get_database_adapter
            adapter = get_database_adapter()
            with adapter.get_connection() as conn:
                cursor = conn.cursor()
                # Clean up all test tables including adw_locks and workflow_history
                tables_to_clean = ['work_log', 'phase_queue', 'webhook_events', 'task_log', 'adw_locks', 'workflow_history']
                for table in tables_to_clean:
                    try:
                        # Use TRUNCATE for PostgreSQL if available (faster and resets sequences)
                        if adapter.get_db_type() == "postgresql":
                            cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
                        else:
                            cursor.execute(f"DELETE FROM {table}")
                    except Exception as table_error:
                        # Table might not exist yet, that's ok
                        print(f"Note: Could not clean {table}: {table_error}")
        except Exception as e:
            # Database might not be ready yet, that's ok
            print(f"Warning: Could not clean tables before test: {e}")
            pass

        yield client

        # Clean up database tables after each test
        try:
            from database import get_database_adapter
            adapter = get_database_adapter()
            with adapter.get_connection() as conn:
                cursor = conn.cursor()
                # Clean up all test tables including adw_locks and workflow_history
                tables_to_clean = ['work_log', 'phase_queue', 'webhook_events', 'task_log', 'adw_locks', 'workflow_history']
                for table in tables_to_clean:
                    try:
                        # Use TRUNCATE for PostgreSQL if available (faster and resets sequences)
                        if adapter.get_db_type() == "postgresql":
                            cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
                        else:
                            cursor.execute(f"DELETE FROM {table}")
                    except Exception as table_error:
                        # Table might not exist, that's ok
                        pass
        except Exception as e:
            # Cleanup failure shouldn't break tests
            print(f"Warning: Could not clean tables after test: {e}")
            pass


# ============================================================================
# Database Integration Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def cleanup_integration_test_data(request):
    """
    Automatically clean integration test data before and after each test.

    This ensures test isolation for integration tests using PostgreSQL.
    """
    # Skip cleanup for tests that use integration_client (it has its own cleanup)
    if 'integration_client' in request.fixturenames:
        yield
        return

    # Clean before test
    try:
        from database import get_database_adapter
        adapter = get_database_adapter()
        if adapter.get_db_type() == "postgresql":
            with adapter.get_connection() as conn:
                cursor = conn.cursor()
                tables_to_clean = ['work_log', 'phase_queue', 'webhook_events', 'task_log', 'adw_locks', 'workflow_history']
                for table in tables_to_clean:
                    try:
                        cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
                    except Exception:
                        pass
    except Exception:
        pass

    yield

    # Clean after test
    try:
        from database import get_database_adapter
        adapter = get_database_adapter()
        if adapter.get_db_type() == "postgresql":
            with adapter.get_connection() as conn:
                cursor = conn.cursor()
                tables_to_clean = ['work_log', 'phase_queue', 'webhook_events', 'task_log', 'adw_locks', 'workflow_history']
                for table in tables_to_clean:
                    try:
                        cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
                    except Exception:
                        pass
    except Exception:
        pass


@pytest.fixture
def db_with_workflows(integration_test_db: Path, monkeypatch) -> Path:
    """
    Create a test database pre-populated with sample workflow data.

    Provides realistic test data for validating queries and analytics.

    Note: This fixture returns the path to the SQLite workflow_history database
    and patches DB_PATH for tests that need it.

    Usage:
        def test_workflow_analytics(db_with_workflows):
            from core.workflow_history_utils.database import get_workflow_history
            with patch('core.workflow_history_utils.database.DB_PATH', db_with_workflows):
                workflows = get_workflow_history(limit=10)
                assert len(workflows) > 0
    """
    # Ensure DB_PATH is patched for this fixture
    import core.workflow_history_utils.database.schema as schema_module
    monkeypatch.setattr(schema_module, 'DB_PATH', integration_test_db)

    # Initialize with sample data
    conn = sqlite3.connect(str(integration_test_db))
    cursor = conn.cursor()

    # Insert sample workflows
    sample_workflows = [
        {
            "adw_id": "TEST-001",
            "issue_number": 42,
            "nl_input": "Fix authentication bug",
            "github_url": "https://github.com/test/repo/issues/42",
            "workflow_template": "adw_sdlc_iso",
            "model_used": "claude-sonnet-4-5",
            "status": "completed",
            "duration_seconds": 900,
            "input_tokens": 5000,
            "output_tokens": 2000,
            "total_tokens": 7000,
            "actual_cost_total": 0.35,
        },
        {
            "adw_id": "TEST-002",
            "issue_number": 43,
            "nl_input": "Add user profile feature",
            "github_url": "https://github.com/test/repo/issues/43",
            "workflow_template": "adw_sdlc_iso",
            "model_used": "claude-sonnet-4-5",
            "status": "running",
            "duration_seconds": 450,
            "input_tokens": 3000,
            "output_tokens": 1500,
            "total_tokens": 4500,
            "actual_cost_total": 0.22,
        },
        {
            "adw_id": "TEST-003",
            "issue_number": 44,
            "nl_input": "Optimize database queries",
            "github_url": "https://github.com/test/repo/issues/44",
            "workflow_template": "adw_sdlc_iso",
            "model_used": "claude-sonnet-4-5",
            "status": "failed",
            "duration_seconds": 120,
            "error_message": "Database connection timeout",
            "input_tokens": 1000,
            "output_tokens": 500,
            "total_tokens": 1500,
            "actual_cost_total": 0.08,
        },
    ]

    for workflow in sample_workflows:
        cursor.execute("""
            INSERT INTO workflow_history (
                adw_id, issue_number, nl_input, github_url, workflow_template,
                model_used, status, duration_seconds, input_tokens, output_tokens,
                total_tokens, actual_cost_total, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            workflow["adw_id"],
            workflow["issue_number"],
            workflow["nl_input"],
            workflow["github_url"],
            workflow["workflow_template"],
            workflow["model_used"],
            workflow["status"],
            workflow.get("duration_seconds"),
            workflow["input_tokens"],
            workflow["output_tokens"],
            workflow["total_tokens"],
            workflow["actual_cost_total"],
            workflow.get("error_message"),
        ))

    conn.commit()
    conn.close()

    return integration_test_db


# ============================================================================
# WebSocket Integration Fixtures
# ============================================================================


@pytest.fixture
def mock_websocket():
    """
    Create a mock WebSocket object for integration testing.

    Usage:
        @pytest.mark.asyncio
        async def test_websocket_connection(mock_websocket):
            await manager.connect(mock_websocket)
            assert mock_websocket.accept.called
    """
    websocket = Mock()
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.close = AsyncMock()

    return websocket


@pytest.fixture
def websocket_manager():
    """
    Create a real WebSocket ConnectionManager for integration testing.

    Usage:
        @pytest.mark.asyncio
        async def test_websocket_broadcast(websocket_manager, mock_websocket):
            await websocket_manager.connect(mock_websocket)
            await websocket_manager.broadcast({"type": "test", "data": "hello"})
            mock_websocket.send_json.assert_called()
    """
    from services.websocket_manager import ConnectionManager

    return ConnectionManager()


@pytest.fixture
def connected_websocket(websocket_manager):
    """
    Create a connected WebSocket for integration testing.

    Returns a mock websocket that's already connected to the manager.

    Usage:
        @pytest.mark.asyncio
        async def test_message_broadcast(connected_websocket, websocket_manager):
            await websocket_manager.broadcast({"type": "update"})
            connected_websocket.send_json.assert_called_once()
    """
    mock_ws = Mock()
    mock_ws.accept = AsyncMock()
    mock_ws.send_json = AsyncMock()
    mock_ws.send_text = AsyncMock()

    # Add to manager's active connections
    websocket_manager.active_connections.add(mock_ws)

    yield mock_ws

    # Cleanup
    websocket_manager.disconnect(mock_ws)


# ============================================================================
# External API Mock Fixtures
# ============================================================================


@pytest.fixture
def mock_github_api():
    """
    Mock GitHub API responses for integration testing.

    Prevents real API calls while maintaining realistic response structure.

    Usage:
        def test_github_integration(mock_github_api, integration_client):
            response = integration_client.post("/api/v1/github/issues/42/comment", json={
                "body": "Test comment"
            })
            assert response.status_code == 200
    """
    with patch('core.github_poster.GitHubPoster') as mock_poster:
        poster_instance = Mock()
        poster_instance.post_comment.return_value = {
            "id": 12345,
            "body": "Test comment",
            "created_at": "2025-11-20T10:00:00Z",
        }
        poster_instance.get_issue.return_value = {
            "number": 42,
            "title": "Test Issue",
            "state": "open",
            "body": "Test description",
        }
        mock_poster.return_value = poster_instance

        yield poster_instance


@pytest.fixture
def mock_openai_api():
    """
    Mock OpenAI API responses for integration testing.

    Prevents real API calls and associated costs during testing.

    Usage:
        def test_sql_generation(mock_openai_api, integration_client):
            response = integration_client.post("/api/v1/query", json={
                "nl_query": "Show all users",
                "provider": "openai"
            })
            assert response.status_code == 200
    """
    with patch('openai.ChatCompletion.create') as mock_create:
        mock_create.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "SELECT * FROM users",
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            },
        }

        yield mock_create


@pytest.fixture
def mock_anthropic_api():
    """
    Mock Anthropic API responses for integration testing.

    Prevents real API calls and associated costs during testing.

    Usage:
        def test_sql_generation_anthropic(mock_anthropic_api, integration_client):
            response = integration_client.post("/api/v1/query", json={
                "nl_query": "Show all users",
                "provider": "anthropic"
            })
            assert response.status_code == 200
    """
    with patch('anthropic.Anthropic') as mock_anthropic:
        mock_client = Mock()
        mock_message = Mock()
        mock_message.content = [Mock(text="SELECT * FROM users")]
        mock_message.usage = Mock(
            input_tokens=100,
            output_tokens=50,
        )
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        yield mock_client


# ============================================================================
# Service Integration Fixtures
# ============================================================================


@pytest.fixture
def health_service():
    """
    Create a HealthService instance for integration testing.

    Usage:
        @pytest.mark.asyncio
        async def test_health_check(health_service):
            status = await health_service.check_all_services()
            assert status["overall_health"] in ["healthy", "degraded", "unhealthy"]
    """
    from services.health_service import HealthService

    return HealthService()


@pytest.fixture
def workflow_service(integration_test_db: Path):
    """
    Create a WorkflowService instance with test database.

    Usage:
        @pytest.mark.asyncio
        async def test_workflow_creation(workflow_service):
            workflow = await workflow_service.create_workflow({
                "nl_input": "Test workflow"
            })
            assert workflow["adw_id"] is not None
    """
    from services.workflow_service import WorkflowService

    with patch('core.workflow_history_utils.database.DB_PATH', integration_test_db):
        return WorkflowService()


@pytest.fixture
def github_issue_service(mock_github_api):
    """
    Create a GitHubIssueService instance with mocked API.

    Usage:
        @pytest.mark.asyncio
        async def test_issue_fetch(github_issue_service):
            issue = await github_issue_service.get_issue(42)
            assert issue["number"] == 42
    """
    from services.github_issue_service import GitHubIssueService

    return GitHubIssueService()


# ============================================================================
# Background Task Integration Fixtures
# ============================================================================


@pytest.fixture
def background_task_manager():
    """
    Create a BackgroundTaskManager for integration testing.

    Usage:
        @pytest.mark.asyncio
        async def test_background_task(background_task_manager):
            task_id = await background_task_manager.submit_task(some_function)
            status = await background_task_manager.get_task_status(task_id)
            assert status in ["pending", "running", "completed", "failed"]
    """
    from services.background_tasks import BackgroundTaskManager

    return BackgroundTaskManager()


# ============================================================================
# Full Server Integration Fixtures
# ============================================================================


@pytest.fixture
def running_server():
    """
    Start a real server instance for full integration testing.

    WARNING: This is slow and should only be used for critical E2E tests.

    Starts the server in a subprocess and waits for it to be ready.

    Usage:
        def test_full_server(running_server):
            import requests
            response = requests.get(f"{running_server}/api/health")
            assert response.status_code == 200
    """
    server_root = Path(__file__).parent.parent.parent
    port = 8765

    # Start server process
    process = subprocess.Popen(
        ["python", "server.py"],
        cwd=server_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "PORT": str(port)},
    )

    # Wait for server to be ready
    base_url = f"http://localhost:{port}"
    max_retries = 30
    for _ in range(max_retries):
        try:
            import requests
            response = requests.get(f"{base_url}/api/health", timeout=1)
            if response.status_code == 200:
                break
        except Exception:
            time.sleep(1)
    else:
        process.terminate()
        process.wait()
        raise RuntimeError("Server failed to start within timeout")

    yield base_url

    # Cleanup
    process.terminate()
    process.wait(timeout=5)


# ============================================================================
# Event Loop Fixture for Async Integration Tests
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for async integration tests.

    This session-scoped fixture ensures the same event loop is used
    across all async integration tests.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Temporary Directory Fixture (inherited from root conftest but re-exported)
# ============================================================================


@pytest.fixture
def temp_directory(tmp_path):
    """
    Create a temporary directory for integration test files.

    This fixture wraps pytest's tmp_path to ensure it's available in integration tests.
    It automatically cleans up after test execution.

    Usage:
        def test_with_temp_files(temp_directory):
            test_file = temp_directory / "test.json"
            test_file.write_text("{}")
            # File automatically cleaned up after test
    """
    return tmp_path


# ============================================================================
# Integration Test Data Fixtures
# ============================================================================


@pytest.fixture
def sample_workflow_lifecycle_data():
    """
    Provide complete workflow lifecycle data for integration testing.

    Returns data representing all stages of a workflow execution.
    """
    return {
        "initial": {
            "adw_id": "INT-TEST-001",
            "issue_number": 100,
            "nl_input": "Integration test workflow",
            "status": "pending",
        },
        "running": {
            "status": "running",
            "start_time": "2025-11-20T10:00:00",
        },
        "completed": {
            "status": "completed",
            "end_time": "2025-11-20T10:15:00",
            "duration_seconds": 900,
            "input_tokens": 5000,
            "output_tokens": 2000,
            "total_tokens": 7000,
            "actual_cost_total": 0.35,
        },
        "failed": {
            "status": "failed",
            "error_message": "Integration test failure",
            "end_time": "2025-11-20T10:05:00",
        },
    }


@pytest.fixture
def sample_api_requests():
    """
    Provide sample API request payloads for integration testing.

    Returns common API request formats for testing endpoints.
    """
    return {
        "query_request": {
            "nl_query": "Show me all users who signed up this week",
            "table": "users",
            "provider": "anthropic",
        },
        "submit_request": {
            "nl_query": "Create a new user table with email and password fields",
            "provider": "openai",
        },
        "insights_request": {
            "query": "SELECT * FROM users WHERE created_at > '2025-01-01'",
            "results": [
                {"id": 1, "email": "user1@test.com"},
                {"id": 2, "email": "user2@test.com"},
            ],
        },
        "export_request": {
            "query": "SELECT * FROM workflows WHERE status = 'completed'",
            "format": "csv",
        },
    }


# ============================================================================
# E2E Test Fixtures (for test_workflow_journey.py)
# ============================================================================


@pytest.fixture
def e2e_test_client(integration_client):
    """Alias for e2e tests that use integration_client"""
    return integration_client


@pytest.fixture
def e2e_database(integration_test_db):
    """Alias for e2e tests that use integration_test_db"""
    return integration_test_db


@pytest.fixture
def mock_external_services_e2e():
    """Mock external services for E2E tests"""
    with patch('anthropic.Anthropic') as mock_anthropic:
        mock_client = Mock()
        mock_message = Mock()
        mock_message.content = [Mock(text="SELECT * FROM test")]
        mock_message.usage = Mock(input_tokens=100, output_tokens=50)
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client
        yield mock_client


@pytest.fixture
def workflow_execution_harness():
    """Harness for executing workflows in E2E tests"""
    class WorkflowHarness:
        def execute_workflow(self, workflow_data):
            """Execute a workflow and return result"""
            return {
                "status": workflow_data.get("status", "pending"),
                "adw_id": workflow_data.get("adw_id"),
                "issue_number": workflow_data.get("issue_number"),
            }

    return WorkflowHarness()


@pytest.fixture
def performance_monitor():
    """Monitor performance metrics during tests"""
    class PerformanceMonitor:
        def __init__(self):
            self.metrics = {}

        def track(self, operation_name):
            """Context manager for tracking operation performance"""
            return self._TrackingContext(self, operation_name)

        def get_metrics(self):
            """Get collected metrics"""
            return self.metrics

        class _TrackingContext:
            def __init__(self, monitor, operation_name):
                self.monitor = monitor
                self.operation_name = operation_name

            def __enter__(self):
                import time
                self.start_time = time.time()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                import time
                duration = time.time() - self.start_time
                self.monitor.metrics[self.operation_name] = {
                    "duration": duration,
                    "success": exc_type is None
                }

    return PerformanceMonitor()


@pytest.fixture
def full_stack_context(integration_app, websocket_manager):
    """Full stack context for E2E tests"""
    from fastapi.testclient import TestClient

    return {
        "client": TestClient(integration_app),
        "websocket": websocket_manager,
        "app": integration_app
    }


@pytest.fixture
def response_validator():
    """Validator for API responses"""
    class ResponseValidator:
        def validate_health_response(self, response):
            """Validate health check response"""
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            return data

    return ResponseValidator()


@pytest.fixture
def workflow_factory():
    """Factory for creating test workflows"""
    class WorkflowFactory:
        def create_batch(self, count, **defaults):
            """Create multiple test workflows"""
            workflows = []
            for i in range(count):
                workflow = {
                    "adw_id": defaults.get("adw_id", f"TEST-E2E-{i+1:03d}"),
                    "issue_number": defaults.get("issue_number", 10000 + i),
                    "nl_input": defaults.get("nl_input", f"Test workflow {i+1}"),
                    "status": defaults.get("status", "pending"),
                }
                workflows.append(workflow)
            return workflows

    return WorkflowFactory()


# ============================================================================
# Cleanup Helpers
# ============================================================================


@pytest.fixture
def cleanup_integration_artifacts():
    """
    Track and cleanup integration test artifacts.

    Returns a dictionary to register files/directories for cleanup.

    Usage:
        def test_creates_files(cleanup_integration_artifacts):
            test_file = Path("integration_test.tmp")
            cleanup_integration_artifacts["files"].append(test_file)
            test_file.write_text("test")
            # File automatically cleaned up after test
    """
    artifacts = {
        "files": [],
        "directories": [],
        "databases": [],
    }

    yield artifacts

    # Cleanup files
    for file_path in artifacts["files"]:
        Path(file_path).unlink(missing_ok=True)

    # Cleanup directories
    import shutil
    for dir_path in artifacts["directories"]:
        if Path(dir_path).exists():
            shutil.rmtree(dir_path, ignore_errors=True)

    # Cleanup databases
    for db_path in artifacts["databases"]:
        Path(db_path).unlink(missing_ok=True)
