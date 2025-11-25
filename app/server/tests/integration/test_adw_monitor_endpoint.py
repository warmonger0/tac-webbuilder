"""
Integration tests for the ADW monitor endpoint.

These tests validate that the /api/adw-monitor endpoint:
- Returns correct status codes
- Has proper response structure
- Handles empty state gracefully
- Handles errors gracefully
- Returns valid data for multiple workflows
- Respects caching behavior

Uses real FastAPI app with mocked filesystem.
"""

import json
from unittest.mock import patch

import pytest


@pytest.mark.integration
class TestAdwMonitorEndpoint:
    """Test the /api/adw-monitor endpoint."""

    def test_adw_monitor_endpoint_exists(self, integration_client):
        """Verify /api/adw-monitor endpoint is available."""
        response = integration_client.get("/api/adw-monitor")
        # Should return 200 even with no workflows
        assert response.status_code == 200

    def test_adw_monitor_response_structure(self, integration_client):
        """Verify response has required fields."""
        response = integration_client.get("/api/adw-monitor")
        assert response.status_code == 200

        data = response.json()

        # Verify top-level structure
        assert "summary" in data
        assert "workflows" in data
        assert "last_updated" in data

        # Verify summary structure
        summary = data["summary"]
        assert "total" in summary
        assert "running" in summary
        assert "completed" in summary
        assert "failed" in summary
        assert "paused" in summary

        # Verify workflows is a list
        assert isinstance(data["workflows"], list)

    def test_adw_monitor_empty_state(self, integration_client, tmp_path):
        """Test endpoint with no workflows present."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir):
            response = integration_client.get("/api/adw-monitor")
            assert response.status_code == 200

            data = response.json()
            assert data["summary"]["total"] == 0
            assert data["summary"]["running"] == 0
            assert data["summary"]["completed"] == 0
            assert data["summary"]["failed"] == 0
            assert data["summary"]["paused"] == 0
            assert data["workflows"] == []

    def test_adw_monitor_single_workflow(self, integration_client, tmp_path):
        """Test endpoint with a single workflow."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        adw_dir = agents_dir / "abc123"
        adw_dir.mkdir()

        state_data = {
            "issue_number": 42,
            "nl_input": "Fix authentication bug",
            "status": "running",
            "workflow_template": "adw_sdlc_iso",
            "start_time": "2025-01-01T10:00:00",
            "github_url": "https://github.com/test/repo/issues/42",
            "current_cost": 1.23,
            "estimated_cost_total": 5.67,
        }

        state_file = adw_dir / "adw_state.json"
        state_file.write_text(json.dumps(state_data))

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir), \
             patch('core.adw_monitor.is_process_running', return_value=True):
            response = integration_client.get("/api/adw-monitor")
            assert response.status_code == 200

            data = response.json()
            assert data["summary"]["total"] == 1
            assert len(data["workflows"]) == 1

            workflow = data["workflows"][0]
            assert workflow["adw_id"] == "abc123"
            assert workflow["issue_number"] == 42
            assert workflow["status"] == "running"
            assert workflow["current_cost"] == 1.23
            assert workflow["estimated_cost_total"] == 5.67

    def test_adw_monitor_multiple_workflows(self, integration_client, tmp_path):
        """Test endpoint with multiple workflows in different states."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        # Create workflows in different states
        workflows_data = [
            ("running_123", {"issue_number": 1, "status": "running", "nl_input": "Feature A"}),
            ("completed_456", {"issue_number": 2, "status": "completed", "nl_input": "Feature B"}),
            ("failed_789", {"issue_number": 3, "status": "failed", "nl_input": "Feature C"}),
        ]

        for adw_id, state_data in workflows_data:
            adw_dir = agents_dir / adw_id
            adw_dir.mkdir()

            state_file = adw_dir / "adw_state.json"
            state_file.write_text(json.dumps(state_data))

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir), \
             patch('core.adw_monitor.is_process_running', return_value=False):
            response = integration_client.get("/api/adw-monitor")
            assert response.status_code == 200

            data = response.json()
            assert data["summary"]["total"] == 3
            assert data["summary"]["running"] == 0  # No processes running
            assert data["summary"]["completed"] == 1
            assert data["summary"]["failed"] == 1
            assert len(data["workflows"]) == 3

    def test_adw_monitor_workflow_schema_validation(self, integration_client, tmp_path):
        """Test that workflow objects match the expected schema."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        adw_dir = agents_dir / "test123"
        adw_dir.mkdir()

        state_data = {
            "issue_number": 42,
            "nl_input": "Test workflow",
            "status": "running",
            "workflow_template": "adw_sdlc_iso",
        }

        state_file = adw_dir / "adw_state.json"
        state_file.write_text(json.dumps(state_data))

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir), \
             patch('core.adw_monitor.is_process_running', return_value=False):
            response = integration_client.get("/api/adw-monitor")
            assert response.status_code == 200

            data = response.json()
            workflow = data["workflows"][0]

            # Verify all required fields are present
            required_fields = [
                "adw_id", "issue_number", "issue_class", "title", "status",
                "current_phase", "phase_progress", "workflow_template",
                "start_time", "end_time", "duration_seconds", "github_url",
                "worktree_path", "current_cost", "estimated_cost_total",
                "error_count", "last_error", "is_process_active",
                "phases_completed", "total_phases"
            ]

            for field in required_fields:
                assert field in workflow, f"Missing required field: {field}"

    def test_adw_monitor_handles_corrupt_json(self, integration_client, tmp_path):
        """Test that endpoint handles corrupt JSON gracefully."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        adw_dir = agents_dir / "corrupt123"
        adw_dir.mkdir()

        state_file = adw_dir / "adw_state.json"
        state_file.write_text("{ invalid json }")

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir):
            response = integration_client.get("/api/adw-monitor")
            # Should still return 200, just skip the corrupt workflow
            assert response.status_code == 200

            data = response.json()
            # Corrupt workflow should be skipped
            assert data["summary"]["total"] == 0
            assert len(data["workflows"]) == 0

    def test_adw_monitor_with_phase_progress(self, integration_client, tmp_path):
        """Test endpoint includes phase progress calculation."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        adw_dir = agents_dir / "progress123"
        adw_dir.mkdir()

        # Create phase directories
        (adw_dir / "plan_phase").mkdir()
        (adw_dir / "build_phase").mkdir()

        state_data = {
            "issue_number": 42,
            "nl_input": "Test workflow",
            "status": "running",
            "current_phase": "build",
        }

        state_file = adw_dir / "adw_state.json"
        state_file.write_text(json.dumps(state_data))

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir), \
             patch('core.adw_monitor.is_process_running', return_value=False):
            response = integration_client.get("/api/adw-monitor")
            assert response.status_code == 200

            data = response.json()
            workflow = data["workflows"][0]

            # Should have phase progress calculated
            assert workflow["current_phase"] == "build"
            assert workflow["phase_progress"] > 0
            assert workflow["total_phases"] == 8

    def test_adw_monitor_with_error_tracking(self, integration_client, tmp_path):
        """Test endpoint includes error tracking."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        adw_dir = agents_dir / "error123"
        adw_dir.mkdir()

        # Create error log
        error_file = adw_dir / "error.log"
        error_file.write_text("Connection timeout error")

        state_data = {
            "issue_number": 42,
            "nl_input": "Test workflow",
            "status": "failed",
            "error_count": 3,
        }

        state_file = adw_dir / "adw_state.json"
        state_file.write_text(json.dumps(state_data))

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir), \
             patch('core.adw_monitor.is_process_running', return_value=False):
            response = integration_client.get("/api/adw-monitor")
            assert response.status_code == 200

            data = response.json()
            workflow = data["workflows"][0]

            # Should include error information
            assert workflow["error_count"] == 3
            assert workflow["last_error"] == "Connection timeout error"
            assert workflow["status"] == "failed"

    def test_adw_monitor_summary_calculations(self, integration_client, tmp_path):
        """Test that summary statistics are calculated correctly."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        # Create workflows with specific statuses
        statuses = ["running", "running", "completed", "completed", "completed", "failed"]

        for i, status in enumerate(statuses):
            adw_dir = agents_dir / f"workflow_{i}"
            adw_dir.mkdir()

            state_data = {
                "issue_number": i,
                "status": status,
                "nl_input": f"Test {i}",
            }

            state_file = adw_dir / "adw_state.json"
            state_file.write_text(json.dumps(state_data))

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir), \
             patch('core.adw_monitor.is_process_running', return_value=False):
            response = integration_client.get("/api/adw-monitor")
            assert response.status_code == 200

            data = response.json()
            summary = data["summary"]

            assert summary["total"] == 6
            assert summary["running"] == 0  # Processes not actually running
            assert summary["completed"] == 3
            assert summary["failed"] == 1

    def test_adw_monitor_sorts_by_start_time(self, integration_client, tmp_path):
        """Test that workflows are sorted by start time (most recent first)."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        # Create workflows with different start times
        workflows = [
            ("old_workflow", "2025-01-01T10:00:00"),
            ("newer_workflow", "2025-01-01T11:00:00"),
            ("newest_workflow", "2025-01-01T12:00:00"),
        ]

        for adw_id, start_time in workflows:
            adw_dir = agents_dir / adw_id
            adw_dir.mkdir()

            state_data = {
                "issue_number": 1,
                "nl_input": adw_id,
                "status": "running",
                "start_time": start_time,
            }

            state_file = adw_dir / "adw_state.json"
            state_file.write_text(json.dumps(state_data))

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir), \
             patch('core.adw_monitor.is_process_running', return_value=False):
            response = integration_client.get("/api/adw-monitor")
            assert response.status_code == 200

            data = response.json()
            workflow_titles = [w["title"] for w in data["workflows"]]

            # Should be sorted newest first
            assert workflow_titles[0] == "newest_workflow"
            assert workflow_titles[-1] == "old_workflow"

    def test_adw_monitor_error_handling(self, integration_client):
        """Test that endpoint handles internal errors gracefully."""
        # Simulate an error by patching the aggregation function
        with patch('core.adw_monitor.aggregate_adw_monitor_data', side_effect=Exception("Test error")):
            response = integration_client.get("/api/adw-monitor")

            # Should still return 200 with empty response
            assert response.status_code == 200

            data = response.json()
            assert data["summary"]["total"] == 0
            assert data["workflows"] == []

    def test_adw_monitor_last_updated_format(self, integration_client, tmp_path):
        """Test that last_updated is in ISO format."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir):
            response = integration_client.get("/api/adw-monitor")
            assert response.status_code == 200

            data = response.json()

            # Verify ISO format timestamp
            last_updated = data["last_updated"]
            assert "T" in last_updated
            # Should be parseable as ISO format
            from datetime import datetime
            datetime.fromisoformat(last_updated.replace("Z", "+00:00"))


@pytest.mark.integration
class TestAdwMonitorCaching:
    """Test caching behavior of the ADW monitor endpoint."""

    def test_adw_monitor_caching_works(self, integration_client, tmp_path):
        """Test that responses are cached for 5 seconds."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir):
            # First request
            response1 = integration_client.get("/api/adw-monitor")
            data1 = response1.json()
            timestamp1 = data1["last_updated"]

            # Second request immediately after
            response2 = integration_client.get("/api/adw-monitor")
            data2 = response2.json()
            timestamp2 = data2["last_updated"]

            # Should return cached data with same timestamp
            assert timestamp1 == timestamp2
