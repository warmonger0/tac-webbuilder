"""Tests for context review API routes."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from routes import context_review_routes
from server import app


@pytest.fixture
def mock_service():
    """Mock context review service."""
    return MagicMock()


@pytest.fixture
def client(mock_service):
    """Create test client with mocked service."""
    context_review_routes.init_context_review_routes(mock_service)
    return TestClient(app)


class TestContextReviewRoutes:
    """Test suite for context review API endpoints."""

    def test_analyze_context_success(self, client, mock_service):
        """Test POST /context-review/analyze success."""
        mock_service.start_analysis = AsyncMock(return_value=123)
        mock_service.get_review_result = AsyncMock(return_value={
            "review": {"id": 123, "status": "analyzing"},
            "suggestions": []
        })

        response = client.post("/api/v1/context-review/analyze", json={
            "change_description": "Add user authentication module",
            "project_path": "/test/project"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["review_id"] == 123
        assert data["status"] in ["pending", "analyzing", "complete"]

    def test_analyze_context_missing_fields(self, client):
        """Test POST /context-review/analyze with missing fields."""
        response = client.post("/api/v1/context-review/analyze", json={
            "change_description": "Test"
        })

        assert response.status_code == 422  # Validation error

    def test_get_review_result_success(self, client, mock_service):
        """Test GET /context-review/{id} success."""
        mock_service.get_review_result = AsyncMock(return_value={
            "review": {"id": 123, "status": "complete"},
            "suggestions": [{"id": 1, "type": "file-to-modify"}]
        })

        response = client.get("/api/v1/context-review/123")

        assert response.status_code == 200
        data = response.json()
        assert "review" in data
        assert "suggestions" in data

    def test_get_review_result_not_found(self, client, mock_service):
        """Test GET /context-review/{id} not found."""
        mock_service.get_review_result = AsyncMock(return_value=None)

        response = client.get("/api/v1/context-review/999")

        assert response.status_code == 404

    def test_get_suggestions_success(self, client, mock_service):
        """Test GET /context-review/{id}/suggestions success."""
        mock_service.get_review_result = AsyncMock(return_value={
            "review": {"id": 123},
            "suggestions": [
                {"id": 1, "type": "file-to-modify"},
                {"id": 2, "type": "risk"}
            ]
        })

        response = client.get("/api/v1/context-review/123/suggestions")

        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) == 2

    def test_check_cache_hit(self, client, mock_service):
        """Test POST /context-review/cache-lookup with cache hit."""
        mock_service.check_cache_for_description = AsyncMock(return_value={
            "cached": True,
            "result": {"integration_strategy": "Cached strategy"}
        })

        response = client.post("/api/v1/context-review/cache-lookup", json={
            "change_description": "Add feature",
            "project_path": "/test/path"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["cached"] is True
        assert "result" in data

    def test_check_cache_miss(self, client, mock_service):
        """Test POST /context-review/cache-lookup with cache miss."""
        mock_service.check_cache_for_description = AsyncMock(return_value={
            "cached": False
        })

        response = client.post("/api/v1/context-review/cache-lookup", json={
            "change_description": "Add feature",
            "project_path": "/test/path"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["cached"] is False

    def test_health_check(self, client, mock_service):
        """Test GET /context-review/health."""
        mock_service.agent.api_key = "test-key"
        mock_service.repository.get_recent_reviews = MagicMock(return_value=[])

        response = client.get("/api/v1/context-review/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service_initialized" in data
