"""
End-to-end test fixtures and configuration.

This module provides fixtures for E2E tests that validate complete user journeys,
full ADW workflow execution, and multi-component system integration.

E2E tests simulate real-world usage scenarios with minimal mocking, using actual
services, databases, and workflow orchestration where possible.
"""

import asyncio
import contextlib
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# ============================================================================
# E2E Test Environment Setup
# ============================================================================


@pytest.fixture(scope="session")
def e2e_test_environment():
    """
    Set up complete E2E test environment.

    Creates isolated environment with:
    - Temporary database directory
    - Test configuration
    - Mock external service endpoints

    This fixture is session-scoped to avoid repeated setup overhead.

    Usage:
        def test_complete_workflow(e2e_test_environment):
            env = e2e_test_environment
            # Access env["db_dir"], env["config"], etc.
    """
    import shutil

    # Create temporary directory structure
    test_dir = Path(tempfile.mkdtemp(prefix="e2e_test_"))
    db_dir = test_dir / "db"
    agents_dir = test_dir / "agents"
    logs_dir = test_dir / "logs"

    db_dir.mkdir(exist_ok=True)
    agents_dir.mkdir(exist_ok=True)
    logs_dir.mkdir(exist_ok=True)

    env = {
        "test_dir": test_dir,
        "db_dir": db_dir,
        "agents_dir": agents_dir,
        "logs_dir": logs_dir,
        "config": {
            "ENV": "e2e_test",
            "LOG_LEVEL": "DEBUG",
            "DB_PATH": str(db_dir / "workflow_history.db"),
        },
    }

    yield env

    # Cleanup
    shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def e2e_database(e2e_test_environment):
    """
    Create a fully initialized database for E2E testing.

    Includes complete schema and realistic seed data.

    Session-scoped to prevent UNIQUE constraint violations from re-inserting seed data.

    Usage:
        def test_workflow_query_journey(e2e_database):
            # Database is ready with schema and seed data
            from core.workflow_history import get_workflow_history
            workflows = get_workflow_history(limit=10)
            assert len(workflows) > 0
    """
    db_path = Path(e2e_test_environment["config"]["DB_PATH"])

    # Initialize database with full schema
    from core.workflow_history import init_db

    with patch('core.workflow_history_utils.database.DB_PATH', db_path):
        init_db()

        # Add seed data for realistic testing
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        seed_workflows = [
            {
                "adw_id": "E2E-001",
                "issue_number": 1,
                "nl_input": "Create user authentication system",
                "github_url": "https://github.com/test/repo/issues/1",
                "workflow_template": "adw_sdlc_iso",
                "model_used": "claude-sonnet-4-5",
                "status": "completed",
                "duration_seconds": 1200,
                "input_tokens": 10000,
                "output_tokens": 5000,
                "total_tokens": 15000,
                "actual_cost_total": 0.75,
            },
            {
                "adw_id": "E2E-002",
                "issue_number": 2,
                "nl_input": "Add password reset functionality",
                "github_url": "https://github.com/test/repo/issues/2",
                "workflow_template": "adw_sdlc_iso",
                "model_used": "claude-sonnet-4-5",
                "status": "completed",
                "duration_seconds": 800,
                "input_tokens": 6000,
                "output_tokens": 3000,
                "total_tokens": 9000,
                "actual_cost_total": 0.45,
            },
            {
                "adw_id": "E2E-003",
                "issue_number": 3,
                "nl_input": "Implement email verification",
                "github_url": "https://github.com/test/repo/issues/3",
                "workflow_template": "adw_sdlc_iso",
                "model_used": "claude-sonnet-4-5",
                "status": "running",
                "duration_seconds": 300,
                "input_tokens": 3000,
                "output_tokens": 1500,
                "total_tokens": 4500,
                "actual_cost_total": 0.22,
            },
        ]

        for workflow in seed_workflows:
            cursor.execute("""
                INSERT INTO workflow_history (
                    adw_id, issue_number, nl_input, github_url, workflow_template,
                    model_used, status, duration_seconds, input_tokens, output_tokens,
                    total_tokens, actual_cost_total
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                workflow["adw_id"],
                workflow["issue_number"],
                workflow["nl_input"],
                workflow["github_url"],
                workflow["workflow_template"],
                workflow["model_used"],
                workflow["status"],
                workflow["duration_seconds"],
                workflow["input_tokens"],
                workflow["output_tokens"],
                workflow["total_tokens"],
                workflow["actual_cost_total"],
            ))

        conn.commit()
        conn.close()

    return db_path


# ============================================================================
# ADW Workflow E2E Fixtures
# ============================================================================


@pytest.fixture
def adw_test_workspace(e2e_test_environment):
    """
    Create a complete ADW test workspace with worktree structure.

    Simulates the full ADW environment including:
    - Agents directory with ADW state
    - Worktree directory structure
    - Test project files

    Usage:
        def test_adw_workflow_execution(adw_test_workspace):
            workspace = adw_test_workspace
            adw_id = workspace["adw_id"]
            worktree = workspace["worktree_path"]
            # Execute ADW workflow tests
    """
    import shutil

    agents_dir = e2e_test_environment["agents_dir"]
    adw_id = "E2E-ADW-001"
    adw_dir = agents_dir / adw_id

    # Create ADW state directory
    adw_dir.mkdir(exist_ok=True)

    # Create worktree structure
    worktree_path = e2e_test_environment["test_dir"] / "worktree" / adw_id
    worktree_path.mkdir(parents=True, exist_ok=True)

    # Create minimal project structure in worktree
    (worktree_path / "app").mkdir(exist_ok=True)
    (worktree_path / "app" / "server").mkdir(exist_ok=True)
    (worktree_path / "app" / "client").mkdir(exist_ok=True)

    # Create ADW state file
    state_file = adw_dir / "state.json"
    state_data = {
        "adw_id": adw_id,
        "issue_number": "999",
        "branch_name": "feature/e2e-test",
        "plan_file": f"agents/{adw_id}/plan.md",
        "issue_class": "/feature",
        "worktree_path": str(worktree_path),
        "backend_port": 8765,
        "frontend_port": 5173,
        "model_set": "base",
    }

    with open(state_file, 'w') as f:
        json.dump(state_data, f, indent=2)

    workspace = {
        "adw_id": adw_id,
        "adw_dir": adw_dir,
        "worktree_path": worktree_path,
        "state_file": state_file,
        "state_data": state_data,
    }

    yield workspace

    # Cleanup
    shutil.rmtree(adw_dir, ignore_errors=True)
    shutil.rmtree(worktree_path, ignore_errors=True)


@pytest.fixture
def adw_state_fixture(adw_test_workspace):
    """
    Create an ADW state object for E2E workflow testing.

    Returns a configured ADW state ready for workflow execution.

    Usage:
        def test_adw_lifecycle(adw_state_fixture):
            state = adw_state_fixture
            assert state.data["adw_id"] == "E2E-ADW-001"
            # Use state for workflow operations
    """
    # This would import ADW state management if available
    # For now, return the workspace data
    return adw_test_workspace


# ============================================================================
# Complete User Journey Fixtures
# ============================================================================


@pytest.fixture
def user_journey_context(e2e_database):
    """
    Provide context for testing complete user journeys.

    Simulates a user's interaction path through the system, including:
    - Database with historical data
    - Session state
    - User preferences

    Usage:
        def test_user_creates_and_monitors_workflow(user_journey_context):
            context = user_journey_context
            # Simulate user journey from creation to completion
    """
    return {
        "database": e2e_database,
        "user_id": "e2e_test_user",
        "session_id": "e2e_session_001",
        "preferences": {
            "default_model": "claude-sonnet-4-5",
            "default_template": "adw_sdlc_iso",
        },
        "history": [],  # Track user actions during journey
    }


@pytest.fixture
def mock_external_services_e2e():
    """
    Mock all external services for E2E testing.

    Provides comprehensive mocking of:
    - GitHub API
    - OpenAI API
    - Anthropic API
    - Any other external dependencies

    Usage:
        def test_full_workflow_journey(mock_external_services_e2e):
            mocks = mock_external_services_e2e
            # External API calls are mocked but system behavior is real
    """
    mocks = {}

    # Mock GitHub API
    with patch('core.github_poster.GitHubPoster') as mock_github:
        github_instance = Mock()
        github_instance.post_comment.return_value = {
            "id": 12345,
            "body": "E2E test comment",
            "created_at": "2025-11-20T10:00:00Z",
        }
        github_instance.get_issue.return_value = {
            "number": 999,
            "title": "E2E Test Issue",
            "state": "open",
            "body": "E2E test description",
            "labels": [{"name": "e2e-test"}],
        }
        mock_github.return_value = github_instance
        mocks["github"] = github_instance

        # Mock OpenAI API
        with patch('openai.ChatCompletion.create') as mock_openai:
            mock_openai.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": "SELECT * FROM users WHERE created_at > '2025-01-01'",
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 200,
                    "completion_tokens": 100,
                    "total_tokens": 300,
                },
            }
            mocks["openai"] = mock_openai

            # Mock Anthropic API
            with patch('anthropic.Anthropic') as mock_anthropic:
                anthropic_client = Mock()
                anthropic_message = Mock()
                anthropic_message.content = [
                    Mock(text="SELECT * FROM workflow_history WHERE status = 'completed'")
                ]
                anthropic_message.usage = Mock(
                    input_tokens=200,
                    output_tokens=100,
                )
                anthropic_client.messages.create.return_value = anthropic_message
                mock_anthropic.return_value = anthropic_client
                mocks["anthropic"] = anthropic_client

                yield mocks


# ============================================================================
# E2E Test Client Fixtures
# ============================================================================


@pytest.fixture
def e2e_test_db_cleanup(e2e_database):
    """
    Fixture to clean up test database between E2E tests.

    Prevents UNIQUE constraint violations by clearing workflow_history table
    between tests while keeping the database initialized and seed data.

    Usage:
        def test_github_flow(e2e_test_client, e2e_test_db_cleanup):
            # Database is clean for this test
            response = e2e_test_client.post("/api/request", json={...})
            # Cleanup happens automatically after test
    """
    import sqlite3

    # Cleanup BEFORE test to ensure clean state
    try:
        conn = sqlite3.connect(str(e2e_database), timeout=10.0)
        cursor = conn.cursor()

        # Delete any records created during previous tests
        cursor.execute("""
            DELETE FROM workflow_history
            WHERE adw_id NOT IN ('E2E-001', 'E2E-002', 'E2E-003')
        """)

        # Also clear adw_locks if the table exists
        try:  # noqa: SIM105
            cursor.execute("""
                DELETE FROM adw_locks
                WHERE adw_id NOT IN ('E2E-001', 'E2E-002', 'E2E-003')
            """)
        except sqlite3.OperationalError:
            pass  # Table might not exist

        conn.commit()
        conn.close()
        time.sleep(0.1)  # Allow DB lock to fully release
    except Exception as e:
        import logging
        logging.warning(f"Failed to cleanup E2E test database before test: {e}")

    yield e2e_database

    # Cleanup AFTER test as well
    try:
        conn = sqlite3.connect(str(e2e_database), timeout=10.0)
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM workflow_history
            WHERE adw_id NOT IN ('E2E-001', 'E2E-002', 'E2E-003')
        """)

        with contextlib.suppress(sqlite3.OperationalError):
            cursor.execute("""
                DELETE FROM adw_locks
                WHERE adw_id NOT IN ('E2E-001', 'E2E-002', 'E2E-003')
            """)

        conn.commit()
        conn.close()
        time.sleep(0.1)  # Allow DB lock to fully release
    except Exception as e:
        import logging
        logging.warning(f"Failed to cleanup E2E test database after test: {e}")


@pytest.fixture
def e2e_test_client(e2e_database, mock_external_services_e2e, e2e_test_db_cleanup):
    """
    Create a fully configured test client for E2E testing.

    This client has:
    - Real database with seed data
    - Mocked external APIs
    - Full service stack
    - Automatic cleanup between tests

    Usage:
        def test_complete_api_flow(e2e_test_client):
            # Test complete user flow through API
            response = e2e_test_client.post("/api/submit", json={...})
            assert response.status_code == 200
            # Continue multi-step workflow
    """
    from fastapi.testclient import TestClient

    with patch('core.workflow_history_utils.database.DB_PATH', e2e_database):
        from server import app

        with TestClient(app) as client:
            yield client


# ============================================================================
# Performance and Load Testing Fixtures
# ============================================================================


@pytest.fixture
def performance_monitor():
    """
    Monitor performance metrics during E2E tests.

    Tracks:
    - Response times
    - Memory usage
    - Database query performance

    Usage:
        def test_workflow_performance(performance_monitor):
            with performance_monitor.track("workflow_creation"):
                # Execute workflow
                pass
            metrics = performance_monitor.get_metrics()
            assert metrics["workflow_creation"]["duration"] < 5.0
    """

    class PerformanceMonitor:
        def __init__(self):
            self.metrics = {}

        def track(self, operation_name):
            return self.OperationTracker(self, operation_name)

        class OperationTracker:
            def __init__(self, monitor, operation_name):
                self.monitor = monitor
                self.operation_name = operation_name
                self.start_time = None

            def __enter__(self):
                self.start_time = time.time()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = time.time() - self.start_time
                self.monitor.metrics[self.operation_name] = {
                    "duration": duration,
                    "success": exc_type is None,
                }

        def get_metrics(self):
            return self.metrics

        def reset(self):
            self.metrics = {}

    return PerformanceMonitor()


# ============================================================================
# Workflow Execution E2E Fixtures
# ============================================================================


@pytest.fixture
def workflow_execution_harness(e2e_database, adw_test_workspace):
    """
    Provide a complete harness for testing workflow execution.

    Includes:
    - Database setup
    - Workspace configuration
    - Execution tracking
    - Result validation

    Usage:
        def test_workflow_end_to_end(workflow_execution_harness):
            harness = workflow_execution_harness
            result = harness.execute_workflow({
                "nl_input": "Create authentication",
                "issue_number": 999,
            })
            assert result["status"] == "completed"
    """
    class WorkflowExecutionHarness:
        def __init__(self, database, workspace):
            self.database = database
            self.workspace = workspace
            self.execution_history = []

        def execute_workflow(self, workflow_data):
            """Execute a workflow and track results."""
            from core.workflow_history import insert_workflow_history

            with patch('core.workflow_history_utils.database.DB_PATH', self.database):
                # Insert workflow
                row_id = insert_workflow_history(
                    adw_id=workflow_data.get("adw_id", "E2E-EXEC-001"),
                    issue_number=workflow_data.get("issue_number", 999),
                    nl_input=workflow_data.get("nl_input", "E2E test workflow"),
                    status=workflow_data.get("status", "pending"),
                )

                result = {
                    "row_id": row_id,
                    "status": workflow_data.get("status", "pending"),
                    "adw_id": workflow_data.get("adw_id", "E2E-EXEC-001"),
                }

                self.execution_history.append(result)
                return result

        def get_execution_history(self):
            """Get history of all executed workflows in this session."""
            return self.execution_history

    return WorkflowExecutionHarness(e2e_database, adw_test_workspace)


# ============================================================================
# Multi-Component Integration Fixtures
# ============================================================================


@pytest.fixture
def full_stack_context(e2e_test_client, websocket_manager, e2e_database):
    """
    Provide complete stack context for E2E testing.

    Combines:
    - HTTP client
    - WebSocket manager
    - Database
    - All services

    Usage:
        @pytest.mark.asyncio
        async def test_realtime_workflow_updates(full_stack_context):
            client = full_stack_context["client"]
            ws_manager = full_stack_context["websocket"]
            # Test realtime updates during workflow execution
    """
    from services.websocket_manager import ConnectionManager

    ws_manager = ConnectionManager()

    return {
        "client": e2e_test_client,
        "websocket": ws_manager,
        "database": e2e_database,
    }


@pytest.fixture
def websocket_manager():
    """Create a WebSocket manager for E2E testing."""
    from services.websocket_manager import ConnectionManager

    return ConnectionManager()


# ============================================================================
# Test Data Factories
# ============================================================================


@pytest.fixture
def workflow_factory():
    """
    Provide a factory for creating workflow test data.

    Usage:
        def test_multiple_workflows(workflow_factory):
            workflow1 = workflow_factory.create(status="completed")
            workflow2 = workflow_factory.create(status="failed")
            # Use workflows in test
    """
    class WorkflowFactory:
        def __init__(self):
            self.counter = 0

        def create(self, **overrides):
            """Create workflow data with optional overrides."""
            self.counter += 1
            base_data = {
                "adw_id": f"E2E-FACTORY-{self.counter:03d}",
                "issue_number": 1000 + self.counter,
                "nl_input": f"E2E test workflow {self.counter}",
                "github_url": f"https://github.com/test/repo/issues/{1000 + self.counter}",
                "workflow_template": "adw_sdlc_iso",
                "model_used": "claude-sonnet-4-5",
                "status": "pending",
            }
            base_data.update(overrides)
            return base_data

        def create_batch(self, count, **overrides):
            """Create multiple workflows."""
            return [self.create(**overrides) for _ in range(count)]

    return WorkflowFactory()


# ============================================================================
# Async E2E Test Helpers
# ============================================================================


@pytest.fixture(scope="session")
def e2e_event_loop():
    """
    Create an event loop for async E2E tests.

    Session-scoped to share across all E2E tests.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Validation Helpers
# ============================================================================


@pytest.fixture
def response_validator():
    """
    Provide helpers for validating API responses in E2E tests.

    Usage:
        def test_api_response(e2e_test_client, response_validator):
            response = e2e_test_client.get("/api/health")
            response_validator.validate_health_response(response)
    """
    class ResponseValidator:
        @staticmethod
        def validate_health_response(response):
            """Validate health check response structure."""
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            # HealthCheckResponse uses "ok" or "error", not "healthy"/"degraded"/"unhealthy"
            assert data["status"] in ["ok", "error"]
            assert "database_connected" in data
            assert "tables_count" in data

        @staticmethod
        def validate_workflow_response(response):
            """Validate workflow creation/update response."""
            assert response.status_code in [200, 201]
            data = response.json()
            assert "adw_id" in data or "id" in data

        @staticmethod
        def validate_error_response(response, expected_code=None):
            """Validate error response structure."""
            if expected_code:
                assert response.status_code == expected_code
            assert response.status_code >= 400
            data = response.json()
            assert "detail" in data or "error" in data

    return ResponseValidator()
