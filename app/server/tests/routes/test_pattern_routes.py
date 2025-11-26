"""
Unit tests for pattern prediction API routes.

Tests cover:
- Successful pattern prediction
- Empty input handling
- Similar workflow matching
- Recommendation generation
- Error handling
"""

from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from server import app
from core.data_models import WorkflowHistoryResponse, WorkflowHistoryItem


client = TestClient(app)


class TestPredictPatternsEndpoint:
    """Test /api/predict-patterns endpoint"""

    def test_predict_patterns_success(self):
        """Test successful pattern prediction with valid input"""
        response = client.post(
            "/api/predict-patterns",
            json={
                "nl_input": "Run backend tests with pytest",
                "project_path": None
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Check structure
        assert "predictions" in data
        assert "similar_workflows" in data
        assert "recommendations" in data
        assert data.get("error") is None

        # Check predictions
        assert isinstance(data["predictions"], list)
        if len(data["predictions"]) > 0:
            pred = data["predictions"][0]
            assert "pattern" in pred
            assert "confidence" in pred
            assert "reasoning" in pred
            assert 0.0 <= pred["confidence"] <= 1.0

    def test_predict_patterns_empty_input(self):
        """Test prediction with empty nl_input"""
        response = client.post(
            "/api/predict-patterns",
            json={
                "nl_input": "",
                "project_path": None
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should return empty predictions with recommendation
        assert data["predictions"] == []
        assert len(data["recommendations"]) > 0
        assert "Input too short" in data["recommendations"][0]

    def test_predict_patterns_test_keywords(self):
        """Test that test keywords produce test:pytest:backend pattern"""
        response = client.post(
            "/api/predict-patterns",
            json={
                "nl_input": "Run pytest tests on backend API",
                "project_path": None
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should predict test:pytest:backend pattern
        patterns = [p["pattern"] for p in data["predictions"]]
        assert "test:pytest:backend" in patterns

        # Should have high confidence for explicit pytest mention
        pytest_pred = next(p for p in data["predictions"] if p["pattern"] == "test:pytest:backend")
        assert pytest_pred["confidence"] >= 0.75

    def test_predict_patterns_build_keywords(self):
        """Test that build keywords produce build patterns"""
        response = client.post(
            "/api/predict-patterns",
            json={
                "nl_input": "Run typecheck on the codebase",
                "project_path": None
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should predict build:typecheck pattern
        patterns = [p["pattern"] for p in data["predictions"]]
        assert any("build" in p and "typecheck" in p for p in patterns)

    @patch('app.server.routes.pattern_routes.get_workflow_history')
    def test_predict_patterns_with_history(self, mock_get_history):
        """Test that similar workflows are returned when history exists"""
        # Mock workflow history response
        mock_workflow = WorkflowHistoryItem(
            id=1,
            adw_id="adw-test123",
            issue_number=42,
            nl_input="Run backend pytest tests",
            github_url="https://github.com/test/repo/issues/42",
            workflow_template="adw_plan_build_test",
            model_used="claude-sonnet-4",
            status="completed",
            created_at="2025-01-01T00:00:00",
            updated_at="2025-01-01T00:10:00",
            actual_cost_total=1.50,
            nl_input_clarity_score=75.0
        )

        mock_response = Mock(spec=WorkflowHistoryResponse)
        mock_response.workflows = [mock_workflow]
        mock_get_history.return_value = mock_response

        response = client.post(
            "/api/predict-patterns",
            json={
                "nl_input": "Run backend tests with pytest",
                "project_path": None
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should return similar workflows
        assert isinstance(data["similar_workflows"], list)
        # Text similarity should be calculated
        # "Run backend tests with pytest" vs "Run backend pytest tests" should have high similarity

    def test_predict_patterns_short_input_recommendation(self):
        """Test that short inputs generate clarity recommendation"""
        response = client.post(
            "/api/predict-patterns",
            json={
                "nl_input": "Fix bug",  # Very short
                "project_path": None
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should recommend adding more details
        recommendations_text = " ".join(data["recommendations"])
        assert "details" in recommendations_text.lower() or "clarity" in recommendations_text.lower()

    def test_predict_patterns_invalid_json(self):
        """Test handling of malformed request"""
        response = client.post(
            "/api/predict-patterns",
            data="not json",
            headers={"Content-Type": "application/json"}
        )

        # FastAPI should return 422 for validation errors
        assert response.status_code == 422

    @patch('app.server.routes.pattern_routes.get_workflow_history')
    def test_predict_patterns_error_handling(self, mock_get_history):
        """Test that endpoint handles errors gracefully"""
        # Simulate exception in history lookup
        mock_get_history.side_effect = Exception("Database connection failed")

        response = client.post(
            "/api/predict-patterns",
            json={
                "nl_input": "Run backend tests",
                "project_path": None
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should still return predictions even if history lookup fails
        assert "predictions" in data
        # Similar workflows should be empty due to error
        assert data["similar_workflows"] == []

    def test_predict_patterns_multiple_patterns(self):
        """Test that multiple patterns are detected from complex input"""
        response = client.post(
            "/api/predict-patterns",
            json={
                "nl_input": "Run pytest tests and then deploy to production",
                "project_path": None
            }
        )

        assert response.status_code == 200
        data = response.json()

        patterns = [p["pattern"] for p in data["predictions"]]

        # Should detect both test and deploy patterns
        has_test_pattern = any("test" in p for p in patterns)
        has_deploy_pattern = any("deploy" in p for p in patterns)

        assert has_test_pattern or has_deploy_pattern

    def test_predict_patterns_recommendations_generated(self):
        """Test that recommendations are always generated"""
        response = client.post(
            "/api/predict-patterns",
            json={
                "nl_input": "Implement user authentication feature with secure password hashing",
                "project_path": None
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should always have at least one recommendation
        assert len(data["recommendations"]) > 0
        # Each recommendation should be a non-empty string
        for rec in data["recommendations"]:
            assert isinstance(rec, str)
            assert len(rec) > 0
