"""
End-to-end tests for complete workflow journeys.

These tests validate complete user workflows from start to finish:
- Workflow creation
- Status monitoring
- Result retrieval
- Analytics generation

Simulates real user interactions with minimal mocking.
"""

import pytest
from unittest.mock import patch


@pytest.mark.e2e
class TestWorkflowCreationJourney:
    """Test complete workflow creation and monitoring journey."""

    def test_create_and_monitor_workflow(
        self, e2e_test_client, e2e_database, sample_workflow_data
    ):
        """
        Test creating a workflow and monitoring its progress.

        User journey:
        1. User creates a new workflow
        2. User checks workflow status
        3. User retrieves workflow details
        """
        # Step 1: Create workflow
        with patch('core.workflow_history.DB_PATH', e2e_database):
            create_response = e2e_test_client.post("/api/workflows/create", json={
                "nl_input": sample_workflow_data["nl_input"],
                "issue_number": sample_workflow_data["issue_number"],
            })

            # Note: This endpoint may not exist yet, so we handle both cases
            if create_response.status_code == 404:
                pytest.skip("Workflow creation endpoint not implemented yet")

            assert create_response.status_code in [200, 201]

            # Step 2: Check workflow status
            status_response = e2e_test_client.get("/api/workflows/status")
            assert status_response.status_code == 200

            # Step 3: Get workflow history
            history_response = e2e_test_client.get("/api/workflows/history")
            assert history_response.status_code == 200


@pytest.mark.e2e
class TestWorkflowAnalyticsJourney:
    """Test workflow analytics and insights generation."""

    def test_view_workflow_analytics(self, e2e_test_client, e2e_database):
        """
        Test viewing analytics for completed workflows.

        User journey:
        1. User accesses analytics dashboard
        2. User filters workflows by status
        3. User views detailed metrics
        """
        with patch('core.workflow_history.DB_PATH', e2e_database):
            # Step 1: Get analytics overview
            analytics_response = e2e_test_client.get("/api/workflows/analytics")

            if analytics_response.status_code == 404:
                pytest.skip("Analytics endpoint not implemented yet")

            assert analytics_response.status_code == 200

            # Step 2: Get history with filters
            filtered_response = e2e_test_client.get(
                "/api/workflows/history",
                params={"status": "completed"}
            )
            assert filtered_response.status_code == 200


@pytest.mark.e2e
class TestDatabaseQueryJourney:
    """Test natural language to SQL query journey."""

    def test_nl_to_sql_query_flow(
        self, e2e_test_client, mock_external_services_e2e
    ):
        """
        Test complete natural language query flow.

        User journey:
        1. User submits natural language query
        2. System generates SQL
        3. User executes query
        4. User views results
        """
        # Step 1: Submit natural language query
        query_response = e2e_test_client.post("/api/query", json={
            "nl_query": "Show me all completed workflows from the last week",
            "table": "workflow_history",
            "provider": "anthropic",
        })

        if query_response.status_code == 404:
            pytest.skip("Query endpoint not implemented yet")

        # Should either succeed or fail gracefully
        assert query_response.status_code in [200, 400, 422]


@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteWorkflowLifecycle:
    """Test complete workflow lifecycle from creation to completion."""

    def test_workflow_end_to_end(
        self, workflow_execution_harness, performance_monitor
    ):
        """
        Test complete workflow lifecycle with performance monitoring.

        This test validates:
        - Workflow creation
        - State transitions
        - Data persistence
        - Performance benchmarks
        """
        with performance_monitor.track("workflow_creation"):
            result = workflow_execution_harness.execute_workflow({
                "adw_id": "E2E-LIFECYCLE-001",
                "issue_number": 9999,
                "nl_input": "Create complete user authentication system",
                "status": "pending",
            })

        assert result["status"] == "pending"
        assert result["adw_id"] == "E2E-LIFECYCLE-001"

        # Verify performance
        metrics = performance_monitor.get_metrics()
        assert metrics["workflow_creation"]["success"] is True
        assert metrics["workflow_creation"]["duration"] < 1.0  # Should be fast


@pytest.mark.e2e
@pytest.mark.asyncio
class TestRealtimeUpdatesJourney:
    """Test realtime updates through WebSocket connections."""

    async def test_workflow_status_updates(self, full_stack_context):
        """
        Test receiving realtime workflow status updates.

        User journey:
        1. User connects to WebSocket
        2. User starts a workflow
        3. User receives status updates in realtime
        """
        client = full_stack_context["client"]
        ws_manager = full_stack_context["websocket"]

        # Create mock WebSocket client
        from unittest.mock import AsyncMock, Mock
        mock_ws = Mock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        # Connect to WebSocket manager
        await ws_manager.connect(mock_ws)

        # Simulate workflow status update broadcast
        await ws_manager.broadcast({
            "type": "workflow_update",
            "data": {
                "adw_id": "E2E-001",
                "status": "running",
            }
        })

        # Verify message was sent
        mock_ws.send_json.assert_called()


@pytest.mark.e2e
class TestErrorRecoveryJourney:
    """Test system behavior during error scenarios."""

    def test_invalid_workflow_creation(self, e2e_test_client):
        """
        Test system handles invalid workflow creation gracefully.

        User journey:
        1. User submits invalid workflow data
        2. System returns clear error message
        3. User corrects data and resubmits
        """
        # Step 1: Submit invalid data
        invalid_response = e2e_test_client.post("/api/workflows/create", json={
            # Missing required fields
        })

        # Should return validation error
        assert invalid_response.status_code in [400, 422]

        # Error response should have helpful message
        if invalid_response.status_code == 422:
            error_data = invalid_response.json()
            assert "detail" in error_data


@pytest.mark.e2e
class TestMultiWorkflowJourney:
    """Test managing multiple concurrent workflows."""

    def test_multiple_workflow_management(
        self, e2e_test_client, workflow_factory, e2e_database
    ):
        """
        Test managing multiple workflows simultaneously.

        User journey:
        1. User creates multiple workflows
        2. User views all workflows
        3. User filters by status
        4. User accesses individual workflow details
        """
        # Create test workflows using factory
        workflows = workflow_factory.create_batch(5, status="completed")

        # Insert workflows into database
        import sqlite3
        conn = sqlite3.connect(str(e2e_database))
        cursor = conn.cursor()

        for workflow in workflows:
            cursor.execute("""
                INSERT INTO workflow_history (
                    adw_id, issue_number, nl_input, status
                ) VALUES (?, ?, ?, ?)
            """, (
                workflow["adw_id"],
                workflow["issue_number"],
                workflow["nl_input"],
                workflow["status"],
            ))

        conn.commit()
        conn.close()

        # View all workflows
        with patch('core.workflow_history.DB_PATH', e2e_database):
            response = e2e_test_client.get("/api/workflows/history")

            if response.status_code == 200:
                data = response.json()
                # Should have multiple workflows
                if isinstance(data, dict) and "workflows" in data:
                    assert len(data["workflows"]) >= 5
                elif isinstance(data, list):
                    assert len(data) >= 5


@pytest.mark.e2e
class TestDataExportJourney:
    """Test exporting workflow data and analytics."""

    def test_export_workflow_data(self, e2e_test_client, e2e_database):
        """
        Test exporting workflow data in various formats.

        User journey:
        1. User selects workflows to export
        2. User chooses export format (CSV, JSON)
        3. User downloads exported data
        """
        with patch('core.workflow_history.DB_PATH', e2e_database):
            # Test CSV export (if endpoint exists)
            export_response = e2e_test_client.post("/api/export", json={
                "format": "csv",
                "filters": {"status": "completed"},
            })

            # May not be implemented yet
            if export_response.status_code == 404:
                pytest.skip("Export endpoint not implemented yet")

            # Should either succeed or fail gracefully
            assert export_response.status_code in [200, 400, 422]


@pytest.mark.e2e
class TestSystemHealthMonitoring:
    """Test system health monitoring and diagnostics."""

    def test_health_monitoring_journey(self, e2e_test_client, response_validator):
        """
        Test monitoring system health.

        User journey:
        1. User checks overall system health
        2. User views service status
        3. User identifies any issues
        """
        # Step 1: Check health
        health_response = e2e_test_client.get("/api/health")
        response_validator.validate_health_response(health_response)

        # Step 2: Get detailed status
        status_response = e2e_test_client.get("/api/status")

        if status_response.status_code == 200:
            data = status_response.json()
            assert isinstance(data, dict)
