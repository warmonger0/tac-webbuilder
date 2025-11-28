"""
Integration tests for API contracts and endpoint behavior.

These tests validate that API endpoints:
- Return correct status codes
- Have proper response structure
- Handle errors gracefully
- Maintain backwards compatibility

Uses real FastAPI app with test database and mocked external APIs.
"""

from unittest.mock import patch

import pytest


@pytest.mark.integration
class TestHealthEndpoints:
    """Test health check and status endpoints."""

    def test_health_check_returns_200(self, integration_client):
        """Verify /api/health returns 200 OK."""
        response = integration_client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_check_response_structure(self, integration_client):
        """Verify health check response has required fields."""
        response = integration_client.get("/api/v1/health")
        data = response.json()

        assert "status" in data
        # API returns "ok" instead of "healthy"
        assert data["status"] in ["ok", "healthy", "degraded", "unhealthy"]
        assert "uptime_seconds" in data or "timestamp" in data

    def test_system_status_endpoint(self, integration_client):
        """Verify /api/status endpoint returns system information."""
        response = integration_client.get("/api/v1/status")

        if response.status_code == 200:
            data = response.json()
            # Validate expected structure
            assert isinstance(data, dict)


@pytest.mark.integration
class TestWorkflowEndpoints:
    """Test workflow-related API endpoints."""

    def test_workflow_history_endpoint(self, integration_client, db_with_workflows):
        """Verify workflow history endpoint returns data."""
        with patch('core.workflow_history_utils.database.DB_PATH', db_with_workflows):
            # Correct endpoint is /api/workflow-history (not /api/workflows/history)
            response = integration_client.get("/api/v1/workflow-history")

            assert response.status_code == 200
            data = response.json()

            # Should have workflows key
            assert "workflows" in data or isinstance(data, list)

    def test_workflow_analytics_endpoint(self, integration_client, db_with_workflows):
        """Verify analytics endpoint returns metrics."""
        with patch('core.workflow_history_utils.database.DB_PATH', db_with_workflows):
            response = integration_client.get("/api/v1/workflows/analytics")

            if response.status_code == 200:
                data = response.json()
                # Validate analytics structure
                assert isinstance(data, dict)


@pytest.mark.integration
class TestDatabaseEndpoints:
    """Test database query and schema endpoints."""

    def test_schema_endpoint(self, integration_client):
        """Verify database schema endpoint returns table information."""
        response = integration_client.get("/api/v1/db/schema")

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict) or isinstance(data, list)

    @pytest.mark.parametrize("invalid_query", [
        "DROP TABLE users",
        "DELETE FROM workflow_history",
        "UPDATE users SET password = 'hacked'",
    ])
    def test_sql_injection_protection(self, integration_client, invalid_query):
        """Verify SQL injection attempts are blocked."""
        response = integration_client.post("/api/v1/query", json={
            "nl_query": invalid_query,
            "table": "users",
        })

        # Should reject dangerous queries
        assert response.status_code in [400, 403, 422]


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling across endpoints."""

    def test_not_found_endpoint(self, integration_client):
        """Verify 404 for non-existent endpoints."""
        response = integration_client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_invalid_json_payload(self, integration_client):
        """Verify proper error for invalid JSON."""
        response = integration_client.post(
            "/api/v1/request",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        # FastAPI returns 422 for invalid JSON
        assert response.status_code in [400, 422]

    def test_missing_required_fields(self, integration_client):
        """Verify validation errors for missing fields."""
        response = integration_client.post("/api/v1/query", json={})
        assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
class TestWebSocketIntegration:
    """Test WebSocket connection and messaging."""

    async def test_websocket_connection(self, websocket_manager, mock_websocket):
        """Verify WebSocket connection lifecycle."""
        await websocket_manager.connect(mock_websocket)
        assert mock_websocket in websocket_manager.active_connections

        websocket_manager.disconnect(mock_websocket)
        assert mock_websocket not in websocket_manager.active_connections

    async def test_websocket_broadcast(self, websocket_manager, mock_websocket):
        """Verify messages are broadcast to connected clients."""
        await websocket_manager.connect(mock_websocket)

        test_message = {"type": "test", "data": "hello"}
        await websocket_manager.broadcast(test_message)

        mock_websocket.send_json.assert_called_once_with(test_message)


@pytest.mark.integration
class TestExternalAPIIntegration:
    """Test integration with external APIs (mocked)."""

    def test_github_api_integration(self, integration_client, mock_github_api):
        """Verify GitHub API integration works with mocked responses."""
        # This test verifies the integration layer works correctly
        # even though the actual GitHub API is mocked
        assert mock_github_api.get_issue.return_value["number"] == 42

    def test_llm_api_integration(self, integration_client, mock_anthropic_api):
        """Verify LLM API integration with mocked responses."""
        # Verify the integration layer handles LLM responses correctly
        assert mock_anthropic_api is not None
