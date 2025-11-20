"""
Pytest configuration and shared fixtures for server tests.

This file provides shared test fixtures and configuration for all test levels:
- Unit tests (tests/*)
- Integration tests (tests/integration/*)
- E2E tests (tests/e2e/*)

Fixtures provided:
- test_client: FastAPI TestClient for API endpoint testing
- temp_test_db: Isolated SQLite test database
- cleanup_test_data: Automatic cleanup of test artifacts
- mock_env_vars: Environment variable configuration for tests
"""

import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers for server tests."""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (uses real components)"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests (full system validation)"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "requires_api_key: marks tests requiring API keys (OpenAI/Anthropic)"
    )
    config.addinivalue_line(
        "markers", "requires_github: marks tests requiring GitHub integration"
    )


# ============================================================================
# Path Fixtures
# ============================================================================


@pytest.fixture
def server_root() -> Path:
    """Get the server root directory (/app/server/)."""
    return Path(__file__).parent.parent


@pytest.fixture
def project_root(server_root: Path) -> Path:
    """Get the project root directory (tac-webbuilder/)."""
    return server_root.parent.parent


@pytest.fixture
def temp_directory() -> Generator[Path, None, None]:
    """
    Create a temporary directory for test files.

    Automatically cleaned up after test execution.
    """
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest.fixture
def temp_test_db() -> Generator[str, None, None]:
    """
    Create a temporary test database with isolated schema.

    Returns the path to the temporary database file.
    Automatically cleaned up after test execution.

    Usage:
        def test_database_operation(temp_test_db):
            conn = sqlite3.connect(temp_test_db)
            # ... perform test operations ...
            conn.close()
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db_path = f.name

    yield temp_db_path

    # Cleanup
    Path(temp_db_path).unlink(missing_ok=True)


@pytest.fixture
def temp_db_connection(temp_test_db: str) -> Generator[sqlite3.Connection, None, None]:
    """
    Create a database connection to a temporary test database.

    Returns an open connection with row_factory configured.
    Automatically commits and closes after test execution.

    Usage:
        def test_query(temp_db_connection):
            cursor = temp_db_connection.cursor()
            cursor.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            cursor.execute("INSERT INTO test VALUES (1, 'Alice')")
            # Connection auto-commits on successful test exit
    """
    conn = sqlite3.connect(temp_test_db)
    conn.row_factory = sqlite3.Row

    yield conn

    # Cleanup
    conn.commit()
    conn.close()


# ============================================================================
# FastAPI TestClient Fixtures
# ============================================================================


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """
    Create a FastAPI TestClient for testing API endpoints.

    This fixture imports and creates a test client for the FastAPI app.
    The client can make synchronous HTTP requests to test endpoints without
    starting an actual server.

    Usage:
        def test_api_endpoint(test_client):
            response = test_client.get("/api/health")
            assert response.status_code == 200

        def test_post_endpoint(test_client):
            response = test_client.post("/api/submit", json={"query": "test"})
            assert response.status_code == 200

    Note: The server module is imported within the fixture to avoid
    import issues with test discovery.
    """
    # Import server here to avoid import errors during test collection
    from server import app

    with TestClient(app) as client:
        yield client


@pytest.fixture
def test_client_with_db(temp_test_db: str) -> Generator[TestClient, None, None]:
    """
    Create a TestClient with a temporary test database.

    This fixture patches the database path to use a temporary database,
    ensuring tests don't modify the production database.

    Usage:
        def test_database_endpoint(test_client_with_db):
            response = test_client_with_db.post("/api/workflow/create", json={...})
            assert response.status_code == 200
    """
    from server import app

    # Patch database paths to use temp database
    with patch('utils.db_connection.get_connection') as mock_get_conn:
        # Configure mock to use temp database
        def get_temp_connection(*args, **kwargs):
            from utils.db_connection import get_connection
            return get_connection(db_path=temp_test_db)

        mock_get_conn.side_effect = get_temp_connection

        with TestClient(app) as client:
            yield client


# ============================================================================
# Environment Variable Fixtures
# ============================================================================


@pytest.fixture
def mock_env_vars() -> Generator[dict, None, None]:
    """
    Mock environment variables for testing.

    Provides test API keys and configuration without requiring actual credentials.
    Automatically restores original environment after test execution.

    Usage:
        def test_with_env(mock_env_vars):
            import os
            assert os.getenv("OPENAI_API_KEY") == "test-openai-key"
            # ... test code that uses env vars ...

    Returns:
        dict: Dictionary of mocked environment variables
    """
    original_env = os.environ.copy()

    test_env = {
        "OPENAI_API_KEY": "test-openai-key-12345",
        "ANTHROPIC_API_KEY": "test-anthropic-key-12345",
        "GITHUB_TOKEN": "test-github-token-12345",
        "GITHUB_REPO": "test-owner/test-repo",
        "ENV": "test",
        "LOG_LEVEL": "DEBUG",
    }

    # Apply test environment
    os.environ.update(test_env)

    yield test_env

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_openai_api_key():
    """Mock OPENAI_API_KEY environment variable."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-openai-key"}):
        yield "test-openai-key"


@pytest.fixture
def mock_anthropic_api_key():
    """Mock ANTHROPIC_API_KEY environment variable."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-anthropic-key"}):
        yield "test-anthropic-key"


# ============================================================================
# Cleanup Fixtures
# ============================================================================


@pytest.fixture
def cleanup_test_data(temp_directory: Path) -> Generator[Path, None, None]:
    """
    Provide a temporary directory and ensure cleanup after test.

    Use this fixture when your test creates files that need guaranteed cleanup.

    Usage:
        def test_file_operations(cleanup_test_data):
            test_file = cleanup_test_data / "test.txt"
            test_file.write_text("test data")
            # File automatically cleaned up after test
    """
    yield temp_directory

    # Cleanup is handled by temp_directory fixture


@pytest.fixture
def cleanup_db_files():
    """
    Track and cleanup test database files.

    Returns a list to which test database paths can be added for cleanup.

    Usage:
        def test_creates_db(cleanup_db_files):
            db_path = Path("test_temp.db")
            cleanup_db_files.append(db_path)
            # Create and use database
            # Database automatically cleaned up after test
    """
    db_files = []

    yield db_files

    # Cleanup all registered database files
    for db_file in db_files:
        Path(db_file).unlink(missing_ok=True)


# ============================================================================
# Mock Service Fixtures
# ============================================================================


@pytest.fixture
def mock_websocket():
    """
    Create a mock WebSocket object for testing.

    Usage:
        def test_websocket_connection(mock_websocket):
            await manager.connect(mock_websocket)
            assert mock_websocket.accept.called
    """
    from unittest.mock import AsyncMock, Mock

    websocket = Mock()
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.close = AsyncMock()

    return websocket


@pytest.fixture
def mock_github_client():
    """
    Create a mock GitHub client for testing.

    Mocks common GitHub API operations without making real API calls.

    Usage:
        def test_github_integration(mock_github_client):
            issue = mock_github_client.get_issue(42)
            assert issue["number"] == 42
    """
    from unittest.mock import Mock

    client = Mock()
    client.get_issue.return_value = {
        "number": 42,
        "title": "Test Issue",
        "state": "open",
        "body": "Test issue description",
        "html_url": "https://github.com/test/repo/issues/42",
    }
    client.create_comment.return_value = {"id": 1, "body": "Test comment"}
    client.update_issue.return_value = {"state": "closed"}

    return client


@pytest.fixture
def mock_llm_client():
    """
    Create a mock LLM client for testing.

    Mocks OpenAI/Anthropic API calls without making real requests.

    Usage:
        def test_llm_query(mock_llm_client):
            response = mock_llm_client.generate("SELECT * FROM users")
            assert "SELECT" in response
    """
    from unittest.mock import Mock

    client = Mock()
    client.generate.return_value = "SELECT * FROM users WHERE id = 1"
    client.generate_sql.return_value = {
        "query": "SELECT * FROM users",
        "confidence": 0.95,
    }
    client.generate_insights.return_value = {
        "insights": ["Test insight 1", "Test insight 2"],
        "summary": "Test summary",
    }

    return client


# ============================================================================
# Async Test Helpers
# ============================================================================


@pytest.fixture
def event_loop():
    """
    Create an event loop for async tests.

    This fixture ensures async tests have a fresh event loop.
    """
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Test Data Fixtures
# ============================================================================


@pytest.fixture
def sample_workflow_data() -> dict:
    """
    Provide sample workflow data for testing.

    Returns a dictionary with realistic workflow metadata.
    """
    return {
        "adw_id": "TEST-001",
        "issue_number": 42,
        "nl_input": "Fix authentication bug in login flow",
        "github_url": "https://github.com/test/repo/issues/42",
        "workflow_template": "adw_sdlc_iso",
        "model_used": "claude-sonnet-4-5",
        "status": "completed",
        "start_time": "2025-11-20T10:00:00",
        "end_time": "2025-11-20T10:15:00",
        "duration_seconds": 900,
        "input_tokens": 5000,
        "output_tokens": 2000,
        "total_tokens": 7000,
        "actual_cost_total": 0.35,
    }


@pytest.fixture
def sample_github_issue() -> dict:
    """
    Provide sample GitHub issue data for testing.

    Returns a dictionary matching GitHub API issue response format.
    """
    return {
        "number": 42,
        "title": "Fix authentication bug",
        "body": "Users are unable to log in with valid credentials",
        "state": "open",
        "labels": [{"name": "bug"}, {"name": "priority:high"}],
        "html_url": "https://github.com/test/repo/issues/42",
        "created_at": "2025-11-20T09:00:00Z",
        "updated_at": "2025-11-20T09:30:00Z",
        "user": {
            "login": "testuser",
            "html_url": "https://github.com/testuser",
        },
    }


@pytest.fixture
def sample_sql_query_request() -> dict:
    """
    Provide sample SQL query request data for testing.

    Returns a dictionary matching the QueryRequest model.
    """
    return {
        "nl_query": "Show me all users who signed up this week",
        "table": "users",
        "provider": "anthropic",
    }


# ============================================================================
# Database Schema Fixtures
# ============================================================================


@pytest.fixture
def init_workflow_history_schema(temp_db_connection: sqlite3.Connection):
    """
    Initialize workflow_history table schema in test database.

    Creates the complete workflow_history table with all indexes.

    Usage:
        def test_workflow_query(temp_db_connection, init_workflow_history_schema):
            cursor = temp_db_connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM workflow_history")
            assert cursor.fetchone()[0] == 0
    """
    cursor = temp_db_connection.cursor()

    # Create workflow_history table (simplified schema for testing)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflow_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adw_id TEXT NOT NULL UNIQUE,
            issue_number INTEGER,
            nl_input TEXT,
            github_url TEXT,
            gh_issue_state TEXT,
            workflow_template TEXT,
            model_used TEXT,
            status TEXT NOT NULL CHECK(status IN ('pending', 'running', 'completed', 'failed')),
            start_time TEXT,
            end_time TEXT,
            duration_seconds INTEGER,
            error_message TEXT,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            estimated_cost_total REAL DEFAULT 0.0,
            actual_cost_total REAL DEFAULT 0.0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_status ON workflow_history(status)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_issue_number ON workflow_history(issue_number)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_created_at ON workflow_history(created_at)
    """)

    temp_db_connection.commit()

    yield temp_db_connection


# ============================================================================
# Utility Functions
# ============================================================================


def create_test_database_with_data(db_path: str, data: list[dict]) -> None:
    """
    Create a test database and populate it with data.

    Args:
        db_path: Path to the database file
        data: List of dictionaries containing workflow data to insert

    Usage:
        create_test_database_with_data("test.db", [
            {"adw_id": "TEST-001", "status": "completed"},
            {"adw_id": "TEST-002", "status": "failed"},
        ])
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create basic workflow_history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflow_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adw_id TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert data
    for item in data:
        adw_id = item.get("adw_id", "TEST")
        status = item.get("status", "pending")
        cursor.execute(
            "INSERT INTO workflow_history (adw_id, status) VALUES (?, ?)",
            (adw_id, status)
        )

    conn.commit()
    conn.close()
