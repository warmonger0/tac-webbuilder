"""
Unit tests for the ADW monitor module.

Tests cover:
- State scanning and parsing
- Process checking
- Worktree validation
- Status determination
- Phase progress calculation
- Cost and error extraction
- Data aggregation
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import pytest
from core.adw_monitor import (
    aggregate_adw_monitor_data,
    build_workflow_status,
    calculate_phase_progress,
    determine_status,
    extract_cost_data,
    extract_error_info,
    get_agents_directory,
    get_last_activity_timestamp,
    get_trees_directory,
    is_process_running,
    scan_adw_states,
    worktree_exists,
)


class TestDirectoryHelpers:
    """Test directory helper functions"""

    def test_get_agents_directory(self):
        """Test agents directory path resolution"""
        agents_dir = get_agents_directory()
        assert agents_dir.name == "agents"
        assert agents_dir.is_absolute()

    def test_get_trees_directory(self):
        """Test trees directory path resolution"""
        trees_dir = get_trees_directory()
        assert trees_dir.name == "trees"
        assert trees_dir.is_absolute()


class TestScanAdwStates:
    """Test ADW state scanning functionality"""

    def test_scan_adw_states_no_directory(self, tmp_path):
        """Test scanning when agents directory doesn't exist"""
        with patch('core.adw_monitor.get_agents_directory', return_value=tmp_path / "nonexistent"):
            states = scan_adw_states()
            assert states == []

    def test_scan_adw_states_empty_directory(self, tmp_path):
        """Test scanning empty agents directory"""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir):
            states = scan_adw_states()
            assert states == []

    def test_scan_adw_states_with_valid_state(self, tmp_path):
        """Test scanning with valid state file"""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        adw_dir = agents_dir / "abc123"
        adw_dir.mkdir()

        state_data = {
            "issue_number": 42,
            "nl_input": "Test workflow",
            "status": "running",
            "workflow_template": "adw_sdlc_iso",
        }

        state_file = adw_dir / "adw_state.json"
        state_file.write_text(json.dumps(state_data))

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir):
            states = scan_adw_states()
            assert len(states) == 1
            assert states[0]["adw_id"] == "abc123"
            assert states[0]["issue_number"] == 42
            assert states[0]["nl_input"] == "Test workflow"

    def test_scan_adw_states_with_corrupt_json(self, tmp_path):
        """Test scanning with corrupt JSON file"""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        adw_dir = agents_dir / "corrupt123"
        adw_dir.mkdir()

        state_file = adw_dir / "adw_state.json"
        state_file.write_text("{ invalid json }")

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir):
            states = scan_adw_states()
            assert states == []

    def test_scan_adw_states_multiple_workflows(self, tmp_path):
        """Test scanning multiple workflows"""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        # Create multiple workflow directories
        for i in range(3):
            adw_dir = agents_dir / f"workflow_{i}"
            adw_dir.mkdir()

            state_data = {"issue_number": i, "status": "running"}
            state_file = adw_dir / "adw_state.json"
            state_file.write_text(json.dumps(state_data))

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir):
            states = scan_adw_states()
            assert len(states) == 3


class TestProcessChecking:
    """Test process checking functionality"""

    def test_is_process_running_true(self):
        """Test when process is running"""
        mock_result = Mock()
        mock_result.stdout = "user 1234 python aider.py abc123"

        with patch('subprocess.run', return_value=mock_result):
            assert is_process_running("abc123") is True

    def test_is_process_running_false(self):
        """Test when process is not running"""
        mock_result = Mock()
        mock_result.stdout = "user 1234 python other_script.py"

        with patch('subprocess.run', return_value=mock_result):
            assert is_process_running("abc123") is False

    def test_is_process_running_timeout(self):
        """Test process check timeout handling"""
        from subprocess import TimeoutExpired

        with patch('subprocess.run', side_effect=TimeoutExpired("ps", 5)):
            assert is_process_running("abc123") is False

    def test_is_process_running_exception(self):
        """Test process check exception handling"""
        with patch('subprocess.run', side_effect=Exception("Process check failed")):
            assert is_process_running("abc123") is False


class TestWorktreeValidation:
    """Test worktree existence checking"""

    def test_worktree_exists_true(self, tmp_path):
        """Test when worktree exists"""
        trees_dir = tmp_path / "trees"
        trees_dir.mkdir()

        worktree = trees_dir / "abc123"
        worktree.mkdir()

        with patch('core.adw_monitor.get_trees_directory', return_value=trees_dir):
            assert worktree_exists("abc123") is True

    def test_worktree_exists_false(self, tmp_path):
        """Test when worktree doesn't exist"""
        trees_dir = tmp_path / "trees"
        trees_dir.mkdir()

        with patch('core.adw_monitor.get_trees_directory', return_value=trees_dir):
            assert worktree_exists("abc123") is False


class TestLastActivity:
    """Test last activity timestamp retrieval"""

    def test_get_last_activity_timestamp(self, tmp_path):
        """Test getting last activity timestamp"""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        adw_dir = agents_dir / "abc123"
        adw_dir.mkdir()

        state_file = adw_dir / "adw_state.json"
        state_file.write_text("{}")

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir):
            timestamp = get_last_activity_timestamp("abc123")
            assert timestamp is not None
            assert isinstance(timestamp, datetime)

    def test_get_last_activity_timestamp_no_dir(self, tmp_path):
        """Test when workflow directory doesn't exist"""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir):
            timestamp = get_last_activity_timestamp("nonexistent")
            assert timestamp is None


class TestStatusDetermination:
    """Test workflow status determination logic"""

    def test_determine_status_completed(self):
        """Test completed status"""
        state = {"status": "completed"}

        with patch('core.adw_monitor.is_process_running', return_value=False):
            status = determine_status("abc123", state)
            assert status == "completed"

    def test_determine_status_failed(self):
        """Test failed status"""
        state = {"status": "failed"}

        with patch('core.adw_monitor.is_process_running', return_value=False):
            status = determine_status("abc123", state)
            assert status == "failed"

    def test_determine_status_running(self):
        """Test running status"""
        state = {"status": "running"}

        with patch('core.adw_monitor.is_process_running', return_value=True):
            status = determine_status("abc123", state)
            assert status == "running"

    def test_determine_status_paused(self):
        """Test paused status (worktree exists, no process, old activity)"""
        state = {"status": "running"}

        # Mock old activity (more than 10 minutes ago)
        from datetime import timedelta
        old_time = datetime.now() - timedelta(minutes=15)

        with patch('core.adw_monitor.is_process_running', return_value=False), \
             patch('core.adw_monitor.worktree_exists', return_value=True), \
             patch('core.adw_monitor.get_last_activity_timestamp', return_value=old_time):
            status = determine_status("abc123", state)
            assert status == "paused"

    def test_determine_status_queued(self):
        """Test queued status (no worktree, no process)"""
        state = {"status": "pending"}

        with patch('core.adw_monitor.is_process_running', return_value=False), \
             patch('core.adw_monitor.worktree_exists', return_value=False):
            status = determine_status("abc123", state)
            assert status == "queued"


class TestPhaseProgress:
    """Test phase progress calculation"""

    def test_calculate_phase_progress_no_directory(self, tmp_path):
        """Test progress when agent directory doesn't exist"""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir):
            phase, progress = calculate_phase_progress("nonexistent", {})
            assert phase is None
            assert progress == 0.0

    def test_calculate_phase_progress_no_phases(self, tmp_path):
        """Test progress with no completed phases"""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        adw_dir = agents_dir / "abc123"
        adw_dir.mkdir()

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir):
            phase, progress = calculate_phase_progress("abc123", {})
            assert phase is None
            assert progress == 0.0

    def test_calculate_phase_progress_some_phases(self, tmp_path):
        """Test progress with some completed phases"""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        adw_dir = agents_dir / "abc123"
        adw_dir.mkdir()

        # Create phase directories
        (adw_dir / "plan_phase").mkdir()
        (adw_dir / "build_phase").mkdir()

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir):
            phase, progress = calculate_phase_progress("abc123", {})
            # 2 phases out of 8 = 25%
            assert progress == 25.0

    def test_calculate_phase_progress_current_phase(self, tmp_path):
        """Test progress with current phase"""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        adw_dir = agents_dir / "abc123"
        adw_dir.mkdir()

        # Create one completed phase
        (adw_dir / "plan_phase").mkdir()

        state = {"current_phase": "build"}

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir):
            phase, progress = calculate_phase_progress("abc123", state)
            assert phase == "build"
            # 1 phase completed (12.5%) + 0.5 * 12.5% for current phase = 18.75%
            # But we round to 1 decimal place
            assert progress > 12.5  # Should include partial progress


class TestCostExtraction:
    """Test cost data extraction"""

    def test_extract_cost_data_with_values(self):
        """Test extracting cost data when present"""
        state = {
            "current_cost": 1.23,
            "estimated_cost_total": 5.67,
        }

        current, estimated = extract_cost_data(state)
        assert current == 1.23
        assert estimated == 5.67

    def test_extract_cost_data_none_values(self):
        """Test extracting cost data when missing"""
        state = {}

        current, estimated = extract_cost_data(state)
        assert current is None
        assert estimated is None

    def test_extract_cost_data_string_conversion(self):
        """Test converting string costs to float"""
        state = {
            "current_cost": "1.23",
            "estimated_cost_total": "5.67",
        }

        current, estimated = extract_cost_data(state)
        assert current == 1.23
        assert estimated == 5.67


class TestErrorExtraction:
    """Test error information extraction"""

    def test_extract_error_info_from_state(self):
        """Test extracting error info from state"""
        state = {
            "error_count": 3,
            "last_error": "Connection timeout",
        }

        with patch('core.adw_monitor.get_agents_directory', return_value=Path("/tmp/agents")):
            error_count, last_error = extract_error_info("abc123", state)
            assert error_count == 3
            assert last_error == "Connection timeout"

    def test_extract_error_info_from_file(self, tmp_path):
        """Test extracting error info from error.log file"""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        adw_dir = agents_dir / "abc123"
        adw_dir.mkdir()

        error_file = adw_dir / "error.log"
        error_file.write_text("Fatal error occurred")

        state = {}

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir):
            error_count, last_error = extract_error_info("abc123", state)
            assert error_count == 1
            assert last_error == "Fatal error occurred"


class TestBuildWorkflowStatus:
    """Test workflow status building"""

    def test_build_workflow_status_complete(self, tmp_path):
        """Test building complete workflow status"""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        adw_dir = agents_dir / "abc123"
        adw_dir.mkdir()

        state = {
            "adw_id": "abc123",
            "issue_number": 42,
            "nl_input": "Fix authentication bug",
            "status": "completed",
            "workflow_template": "adw_sdlc_iso",
            "start_time": "2025-01-01T10:00:00",
            "github_url": "https://github.com/test/repo/issues/42",
        }

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir), \
             patch('core.adw_monitor.is_process_running', return_value=False), \
             patch('core.adw_monitor.determine_status', return_value="completed"):
            status = build_workflow_status(state)

            assert status["adw_id"] == "abc123"
            assert status["issue_number"] == 42
            assert status["status"] == "completed"
            assert status["workflow_template"] == "adw_sdlc_iso"
            assert status["is_process_active"] is False


class TestAggregateAdwMonitorData:
    """Test data aggregation functionality"""

    def test_aggregate_adw_monitor_data_empty(self, tmp_path):
        """Test aggregation with no workflows"""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir):
            data = aggregate_adw_monitor_data()

            assert data["summary"]["total"] == 0
            assert data["summary"]["running"] == 0
            assert data["summary"]["completed"] == 0
            assert data["summary"]["failed"] == 0
            assert data["summary"]["paused"] == 0
            assert data["workflows"] == []
            assert "last_updated" in data

    def test_aggregate_adw_monitor_data_with_workflows(self, tmp_path):
        """Test aggregation with multiple workflows"""
        # Clear cache before test
        from core.adw_monitor import _monitor_cache
        _monitor_cache["data"] = None
        _monitor_cache["timestamp"] = None

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        # Create multiple workflow states
        for i, status in enumerate(["running", "completed", "failed"]):
            adw_dir = agents_dir / f"workflow_{i}"
            adw_dir.mkdir()

            state_data = {
                "issue_number": i,
                "status": status,
                "nl_input": f"Test workflow {i}",
            }
            state_file = adw_dir / "adw_state.json"
            state_file.write_text(json.dumps(state_data))

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir), \
             patch('core.adw_monitor.is_process_running', return_value=False):
            data = aggregate_adw_monitor_data()

            assert data["summary"]["total"] == 3
            assert len(data["workflows"]) == 3

    def test_aggregate_adw_monitor_data_caching(self, tmp_path):
        """Test that data is cached properly"""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        with patch('core.adw_monitor.get_agents_directory', return_value=agents_dir):
            # First call
            data1 = aggregate_adw_monitor_data()
            timestamp1 = data1["last_updated"]

            # Second call should return cached data
            data2 = aggregate_adw_monitor_data()
            timestamp2 = data2["last_updated"]

            # Should be the same cached data
            assert timestamp1 == timestamp2
