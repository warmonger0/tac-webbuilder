"""
Integration tests for work log API routes.

Tests API endpoints for work log management:
- Creating work log entries
- Retrieving work logs with pagination
- Filtering by session
- Deleting entries
"""

from datetime import datetime
from unittest.mock import patch

import pytest


@pytest.mark.integration
class TestWorkLogEndpoints:
    """Test work log API endpoints."""

    def test_get_work_logs_empty_database(self, integration_client):
        """Verify work log endpoint returns empty list when no entries exist."""
        response = integration_client.get("/api/v1/work-log")

        assert response.status_code == 200
        data = response.json()

        assert "entries" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert isinstance(data["entries"], list)
        assert data["total"] == 0

    def test_get_work_logs_with_pagination(self, integration_client):
        """Verify pagination parameters are respected."""
        response = integration_client.get("/api/v1/work-log?limit=10&offset=0")

        assert response.status_code == 200
        data = response.json()

        assert data["limit"] == 10
        assert data["offset"] == 0

    def test_create_work_log_entry(self, integration_client):
        """Verify creating a new work log entry."""
        payload = {
            "session_id": "test-session-123",
            "summary": "Implemented work log endpoints",
            "issue_number": 42,
            "workflow_id": "adw-test-123",
            "tags": ["backend", "api"]
        }

        response = integration_client.post("/api/v1/work-log", json=payload)

        assert response.status_code == 201
        data = response.json()

        assert data["session_id"] == "test-session-123"
        assert data["summary"] == "Implemented work log endpoints"
        assert data["issue_number"] == 42
        assert data["workflow_id"] == "adw-test-123"
        assert data["tags"] == ["backend", "api"]
        assert "id" in data
        assert "timestamp" in data
        assert "created_at" in data

    def test_create_work_log_validates_summary_length(self, integration_client):
        """Verify summary length validation."""
        payload = {
            "session_id": "test-session",
            "summary": "x" * 281,  # Over 280 character limit
            "tags": []
        }

        response = integration_client.post("/api/v1/work-log", json=payload)

        assert response.status_code == 400

    def test_create_work_log_minimal_fields(self, integration_client):
        """Verify creating entry with only required fields."""
        payload = {
            "session_id": "test-session",
            "summary": "Minimal test entry",
            "tags": []
        }

        response = integration_client.post("/api/v1/work-log", json=payload)

        assert response.status_code == 201
        data = response.json()

        assert data["session_id"] == "test-session"
        assert data["summary"] == "Minimal test entry"
        assert data["chat_file_link"] is None
        assert data["issue_number"] is None
        assert data["workflow_id"] is None

    def test_get_work_logs_by_session(self, integration_client):
        """Verify filtering work logs by session ID."""
        # Create entries for different sessions
        integration_client.post("/api/v1/work-log", json={
            "session_id": "session-A",
            "summary": "Entry for session A",
            "tags": []
        })
        integration_client.post("/api/v1/work-log", json={
            "session_id": "session-B",
            "summary": "Entry for session B",
            "tags": []
        })

        response = integration_client.get("/api/v1/work-log/session/session-A")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # All entries should be for session-A
        for entry in data:
            assert entry["session_id"] == "session-A"

    def test_delete_work_log_entry(self, integration_client):
        """Verify deleting a work log entry."""
        # Create entry
        create_response = integration_client.post("/api/v1/work-log", json={
            "session_id": "test-session",
            "summary": "Entry to delete",
            "tags": []
        })
        entry_id = create_response.json()["id"]

        # Delete entry
        delete_response = integration_client.delete(f"/api/v1/work-log/{entry_id}")

        assert delete_response.status_code == 204

        # Verify entry no longer exists
        get_response = integration_client.get("/api/v1/work-log")
        data = get_response.json()
        entry_ids = [entry["id"] for entry in data["entries"]]
        assert entry_id not in entry_ids

    def test_delete_nonexistent_entry(self, integration_client):
        """Verify deleting non-existent entry returns 404."""
        response = integration_client.delete("/api/v1/work-log/99999")

        assert response.status_code == 404

    def test_work_log_timeline_order(self, integration_client):
        """Verify work logs are returned in reverse chronological order."""
        # Create multiple entries
        for i in range(3):
            integration_client.post("/api/v1/work-log", json={
                "session_id": f"session-{i}",
                "summary": f"Entry {i}",
                "tags": []
            })

        response = integration_client.get("/api/v1/work-log")
        data = response.json()

        if len(data["entries"]) >= 2:
            # Most recent should be first
            timestamps = [entry["timestamp"] for entry in data["entries"]]
            # Verify descending order
            for i in range(len(timestamps) - 1):
                assert timestamps[i] >= timestamps[i + 1]

    def test_work_log_with_special_characters(self, integration_client):
        """Verify work logs handle special characters in summary."""
        payload = {
            "session_id": "test-session",
            "summary": "Fixed bug with SQL: SELECT * FROM table WHERE id = '123'; -- comment",
            "tags": ["sql", "security"]
        }

        response = integration_client.post("/api/v1/work-log", json=payload)

        assert response.status_code == 201
        data = response.json()

        # Should preserve special characters
        assert "SELECT * FROM table" in data["summary"]
        assert "--" in data["summary"]

    def test_work_log_tags_json_handling(self, integration_client):
        """Verify tags are properly stored and retrieved as JSON array."""
        payload = {
            "session_id": "test-session",
            "summary": "Test entry",
            "tags": ["tag1", "tag2", "tag3"]
        }

        create_response = integration_client.post("/api/v1/work-log", json=payload)
        entry_id = create_response.json()["id"]

        # Retrieve and verify tags
        get_response = integration_client.get("/api/v1/work-log")
        entries = get_response.json()["entries"]

        matching_entry = next((e for e in entries if e["id"] == entry_id), None)
        assert matching_entry is not None
        assert matching_entry["tags"] == ["tag1", "tag2", "tag3"]


@pytest.mark.integration
class TestWorkLogErrorHandling:
    """Test error handling in work log endpoints."""

    def test_create_work_log_missing_required_field(self, integration_client):
        """Verify validation error for missing required fields."""
        payload = {
            "summary": "Missing session_id",
            "tags": []
        }

        response = integration_client.post("/api/v1/work-log", json=payload)

        assert response.status_code == 422  # Validation error

    def test_create_work_log_invalid_types(self, integration_client):
        """Verify validation error for invalid field types."""
        payload = {
            "session_id": 123,  # Should be string
            "summary": "Test",
            "tags": "not-a-list"  # Should be array
        }

        response = integration_client.post("/api/v1/work-log", json=payload)

        assert response.status_code == 422

    def test_get_work_logs_invalid_pagination(self, integration_client):
        """Verify handling of invalid pagination parameters."""
        response = integration_client.get("/api/v1/work-log?limit=-1&offset=-1")

        # Should either reject or normalize to valid values
        assert response.status_code in [200, 400, 422]
