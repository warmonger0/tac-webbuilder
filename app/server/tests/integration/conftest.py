"""
Integration test fixtures and configuration.

This module provides fixtures specifically for integration tests that validate
component interactions, API contracts, database operations, and full workflow
execution across the server stack.

Integration tests use real components (database, FastAPI app, services) with
mocked external dependencies (GitHub API, OpenAI/Anthropic APIs).
"""

import asyncio
import json
import os
import sqlite3
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Generator
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient


# ============================================================================
# Server Integration Fixtures
# ============================================================================


@pytest.fixture
def integration_test_db(monkeypatch) -> Generator[Path, None, None]:
    """
    Create a temporary database for integration tests with full schema.

    This fixture initializes a complete database schema matching production,
    including all tables, indexes, and constraints.

    Usage:
        def test_workflow_lifecycle(integration_test_db):
            from core.workflow_history_utils.database import insert_workflow_history
            # No need to patch - fixture already handles it
            row_id = insert_workflow_history(adw_id="TEST-001", ...)
            assert row_id > 0
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db_path = Path(f.name)

    # Use monkeypatch to replace DB_PATH in all modules
    import core.workflow_history_utils.database.schema as schema_module
    import core.workflow_history_utils.database.mutations as mutations_module
    import core.workflow_history_utils.database.queries as queries_module
    import core.workflow_history_utils.database.analytics as analytics_module

    monkeypatch.setattr(schema_module, 'DB_PATH', temp_db_path)
    monkeypatch.setattr(mutations_module, 'DB_PATH', temp_db_path)
    monkeypatch.setattr(queries_module, 'DB_PATH', temp_db_path)
    monkeypatch.setattr(analytics_module, 'DB_PATH', temp_db_path)

    # Initialize database schema
    from core.workflow_history_utils.database import init_db
    init_db()

    yield temp_db_path

    # Cleanup
    temp_db_path.unlink(missing_ok=True)


@pytest.fixture
def integration_app(integration_test_db: Path):
    """
    Create FastAPI app instance with test database for integration testing.

    This fixture provides a fully configured FastAPI application with:
    - Test database (isolated from production)
    - Real service instances
    - Mocked external API calls

    Usage:
        def test_api_workflow(integration_app):
            client = TestClient(integration_app)
            response = client.get("/api/health")
            assert response.status_code == 200
    """
    # Patch database path before importing server
    with patch('core.workflow_history_utils.database.DB_PATH', integration_test_db):
        from server import app
        yield app


@pytest.fixture
def integration_client(integration_app) -> Generator[TestClient, None, None]:
    """
    Create TestClient for integration testing with full app context.

    This client can make requests to all API endpoints with a real database
    and service layer, but with mocked external dependencies.

    Usage:
        def test_submit_workflow(integration_client):
            response = integration_client.post("/api/submit", json={
                "nl_query": "Show all users",
                "table": "users"
            })
            assert response.status_code == 200
    """
    with TestClient(integration_app) as client:
        yield client


# ============================================================================
# Database Integration Fixtures
# ============================================================================


@pytest.fixture
def db_with_workflows(integration_test_db: Path) -> Generator[Path, None, None]:
    """
    Create a test database pre-populated with sample workflow data.

    Provides realistic test data for validating queries and analytics.

    Usage:
        def test_workflow_analytics(db_with_workflows):
            from core.workflow_history_utils.database import get_workflow_history
            with patch('core.workflow_history_utils.database.DB_PATH', db_with_workflows):
                workflows = get_workflow_history(limit=10)
                assert len(workflows) > 0
    """
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

    yield integration_test_db


# ============================================================================
# WebSocket Integration Fixtures
# ============================================================================


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
            response = integration_client.post("/api/github/issues/42/comment", json={
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
            response = integration_client.post("/api/query", json={
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
            response = integration_client.post("/api/query", json={
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
