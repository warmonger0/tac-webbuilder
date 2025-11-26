"""
Unit tests for workflow_history_utils.filesystem module.

Tests filesystem scanning and workflow state parsing functionality.
Covers edge cases including:
- Empty/missing directories
- Invalid issue numbers
- Blacklisted issue numbers
- Status inference logic
- Malformed JSON handling
- Permission errors
"""

import json
import logging
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from core.workflow_history_utils.filesystem import scan_agents_directory


class TestScanAgentsDirectory:
    """Tests for scan_agents_directory function."""

    def test_agents_directory_not_exists(self, tmp_path, caplog):
        """Test when agents directory doesn't exist."""
        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            # Mock the path resolution to point to non-existent directory
            mock_project_root = Mock()
            mock_agents_dir = Mock()
            mock_agents_dir.exists.return_value = False
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            with caplog.at_level(logging.WARNING):
                result = scan_agents_directory()

            assert result == []
            assert any("Agents directory not found" in record.message for record in caplog.records)

    def test_empty_agents_directory(self, tmp_path):
        """Test scanning an empty agents directory."""
        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            # Create mock empty agents directory
            mock_agents_dir = Mock()
            mock_agents_dir.exists.return_value = True
            mock_agents_dir.iterdir.return_value = []

            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            result = scan_agents_directory()

            assert result == []

    def test_skips_non_directory_entries(self, tmp_path):
        """Test that non-directory entries in agents/ are skipped."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        # Create a regular file (not a directory)
        (agents_dir / "README.md").write_text("# Agents")

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            result = scan_agents_directory()

            assert result == []

    def test_skips_directory_without_state_file(self, tmp_path, caplog):
        """Test that directories without adw_state.json are skipped."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        # Create directory without state file
        workflow_dir = agents_dir / "workflow-001"
        workflow_dir.mkdir()

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            with caplog.at_level(logging.DEBUG):
                result = scan_agents_directory()

            assert result == []
            assert any("No adw_state.json found" in record.message for record in caplog.records)

    def test_valid_state_file_with_complete_data(self, tmp_path):
        """Test parsing a valid state file with all fields populated."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        workflow_dir = agents_dir / "workflow-001"
        workflow_dir.mkdir()

        state_data = {
            "issue_number": 42,
            "nl_input": "Fix authentication bug",
            "github_url": "https://github.com/test/repo/issues/42",
            "workflow_template": "adw_sdlc_iso",
            "model_used": "claude-sonnet-4-5",
            "status": "completed",
            "start_time": "2025-11-20T10:00:00",
            "current_phase": "test",
            "backend_port": 8000,
            "frontend_port": 3000,
            "branch_name": "fix/auth-bug",
            "plan_file": "plan.md"
        }

        state_file = workflow_dir / "adw_state.json"
        state_file.write_text(json.dumps(state_data))

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            result = scan_agents_directory()

            assert len(result) == 1
            workflow = result[0]

            assert workflow["adw_id"] == "workflow-001"
            assert workflow["issue_number"] == 42
            assert workflow["nl_input"] == "Fix authentication bug"
            assert workflow["github_url"] == "https://github.com/test/repo/issues/42"
            assert workflow["workflow_template"] == "adw_sdlc_iso"
            assert workflow["model_used"] == "claude-sonnet-4-5"
            assert workflow["status"] == "completed"
            assert workflow["start_time"] == "2025-11-20T10:00:00"
            assert workflow["current_phase"] == "test"
            assert workflow["backend_port"] == 8000
            assert workflow["frontend_port"] == 3000
            assert str(workflow_dir) in workflow["worktree_path"]

    def test_invalid_issue_number_negative(self, tmp_path, caplog):
        """Test that negative issue numbers are rejected."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        workflow_dir = agents_dir / "workflow-001"
        workflow_dir.mkdir()

        state_data = {
            "issue_number": -5,
            "nl_input": "Test workflow",
            "status": "running"
        }

        state_file = workflow_dir / "adw_state.json"
        state_file.write_text(json.dumps(state_data))

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            with caplog.at_level(logging.WARNING):
                result = scan_agents_directory()

            assert result == []
            assert any("issue_number must be positive" in record.message for record in caplog.records)

    def test_invalid_issue_number_zero(self, tmp_path, caplog):
        """Test that zero issue number is rejected."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        workflow_dir = agents_dir / "workflow-002"
        workflow_dir.mkdir()

        state_data = {
            "issue_number": 0,
            "nl_input": "Test workflow",
            "status": "running"
        }

        state_file = workflow_dir / "adw_state.json"
        state_file.write_text(json.dumps(state_data))

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            with caplog.at_level(logging.WARNING):
                result = scan_agents_directory()

            assert result == []
            assert any("issue_number must be positive" in record.message for record in caplog.records)

    def test_invalid_issue_number_string(self, tmp_path, caplog):
        """Test that non-numeric issue numbers are rejected."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        workflow_dir = agents_dir / "workflow-003"
        workflow_dir.mkdir()

        state_data = {
            "issue_number": "not-a-number",
            "nl_input": "Test workflow",
            "status": "running"
        }

        state_file = workflow_dir / "adw_state.json"
        state_file.write_text(json.dumps(state_data))

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            with caplog.at_level(logging.WARNING):
                result = scan_agents_directory()

            assert result == []
            assert any("invalid issue_number" in record.message for record in caplog.records)
            assert any("expected integer" in record.message for record in caplog.records)

    def test_invalid_issue_number_float(self, tmp_path, caplog):
        """Test that float issue numbers are converted to int if valid."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        workflow_dir = agents_dir / "workflow-004"
        workflow_dir.mkdir()

        state_data = {
            "issue_number": 42.5,
            "nl_input": "Test workflow",
            "status": "completed"
        }

        state_file = workflow_dir / "adw_state.json"
        state_file.write_text(json.dumps(state_data))

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            result = scan_agents_directory()

            # Float should be converted to int (42)
            assert len(result) == 1
            assert result[0]["issue_number"] == 42

    @pytest.mark.parametrize("blacklisted_issue", [6, 13, 999])
    def test_blacklisted_issue_numbers(self, tmp_path, blacklisted_issue, caplog):
        """Test that blacklisted issue numbers (6, 13, 999) are skipped."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        workflow_dir = agents_dir / f"workflow-{blacklisted_issue}"
        workflow_dir.mkdir()

        state_data = {
            "issue_number": blacklisted_issue,
            "nl_input": "Test workflow",
            "status": "running"
        }

        state_file = workflow_dir / "adw_state.json"
        state_file.write_text(json.dumps(state_data))

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            with caplog.at_level(logging.WARNING):
                result = scan_agents_directory()

            assert result == []
            assert any("is in invalid list" in record.message for record in caplog.records)

    def test_status_inference_error_log_exists(self, tmp_path):
        """Test status is inferred as 'failed' when error.log exists."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        workflow_dir = agents_dir / "workflow-005"
        workflow_dir.mkdir()

        # Create error.log file
        error_log = workflow_dir / "error.log"
        error_log.write_text("Error: Something went wrong")

        state_data = {
            "issue_number": 42,
            "nl_input": "Test workflow",
            "status": "running"  # Will be overridden to "failed"
        }

        state_file = workflow_dir / "adw_state.json"
        state_file.write_text(json.dumps(state_data))

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            result = scan_agents_directory()

            assert len(result) == 1
            assert result[0]["status"] == "failed"

    def test_status_inference_completed_with_phases(self, tmp_path):
        """Test status is inferred as 'completed' with 3+ phases and artifacts."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        workflow_dir = agents_dir / "workflow-006"
        workflow_dir.mkdir()

        # Create phase directories
        (workflow_dir / "adw_plan").mkdir()
        (workflow_dir / "adw_build").mkdir()
        (workflow_dir / "adw_test").mkdir()

        state_data = {
            "issue_number": 42,
            "nl_input": "Test workflow",
            "status": "running",  # Will be overridden to "completed"
            "plan_file": "plan.md",
            "branch_name": "feature/test"
        }

        state_file = workflow_dir / "adw_state.json"
        state_file.write_text(json.dumps(state_data))

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            result = scan_agents_directory()

            assert len(result) == 1
            assert result[0]["status"] == "completed"

    def test_status_inference_running_with_incomplete_phases(self, tmp_path):
        """Test status remains 'running' with phases but missing artifacts."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        workflow_dir = agents_dir / "workflow-007"
        workflow_dir.mkdir()

        # Create phase directories but no plan_file or branch_name
        (workflow_dir / "adw_plan").mkdir()
        (workflow_dir / "adw_build").mkdir()
        (workflow_dir / "adw_test").mkdir()

        state_data = {
            "issue_number": 42,
            "nl_input": "Test workflow",
            "status": "unknown"  # Will be set to "running"
        }

        state_file = workflow_dir / "adw_state.json"
        state_file.write_text(json.dumps(state_data))

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            result = scan_agents_directory()

            assert len(result) == 1
            assert result[0]["status"] == "running"

    def test_status_inference_failed_single_phase_no_plan(self, tmp_path):
        """Test status is inferred as 'failed' with only 1 phase and no plan file."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        workflow_dir = agents_dir / "workflow-008"
        workflow_dir.mkdir()

        # Create only one phase directory
        (workflow_dir / "adw_plan").mkdir()

        state_data = {
            "issue_number": 42,
            "nl_input": "Test workflow",
            "status": "running"  # Will be overridden to "failed"
        }

        state_file = workflow_dir / "adw_state.json"
        state_file.write_text(json.dumps(state_data))

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            result = scan_agents_directory()

            assert len(result) == 1
            assert result[0]["status"] == "failed"

    def test_status_inference_running_with_few_phases(self, tmp_path):
        """Test status remains 'running' with 2 phases."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        workflow_dir = agents_dir / "workflow-009"
        workflow_dir.mkdir()

        # Create two phase directories
        (workflow_dir / "adw_plan").mkdir()
        (workflow_dir / "adw_build").mkdir()

        state_data = {
            "issue_number": 42,
            "nl_input": "Test workflow",
            "status": "unknown"  # Will be set to "running"
        }

        state_file = workflow_dir / "adw_state.json"
        state_file.write_text(json.dumps(state_data))

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            result = scan_agents_directory()

            assert len(result) == 1
            assert result[0]["status"] == "running"

    def test_missing_optional_fields(self, tmp_path):
        """Test parsing state file with only required fields."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        workflow_dir = agents_dir / "workflow-010"
        workflow_dir.mkdir()

        # Minimal state data - only issue_number
        state_data = {
            "issue_number": 42
        }

        state_file = workflow_dir / "adw_state.json"
        state_file.write_text(json.dumps(state_data))

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            result = scan_agents_directory()

            assert len(result) == 1
            workflow = result[0]

            assert workflow["adw_id"] == "workflow-010"
            assert workflow["issue_number"] == 42
            assert workflow["nl_input"] is None
            assert workflow["github_url"] is None
            assert workflow["workflow_template"] is None
            assert workflow["model_used"] is None
            assert workflow["status"] == "running"  # Inferred as no error.log and no phases
            assert workflow["start_time"] is None
            assert workflow["current_phase"] is None
            assert workflow["backend_port"] is None
            assert workflow["frontend_port"] is None

    def test_legacy_field_names(self, tmp_path):
        """Test that legacy field names (workflow, model) are mapped correctly."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        workflow_dir = agents_dir / "workflow-011"
        workflow_dir.mkdir()

        # Use legacy field names
        state_data = {
            "issue_number": 42,
            "workflow": "adw_legacy_workflow",  # Legacy name
            "model": "gpt-4",  # Legacy name
            "status": "completed"
        }

        state_file = workflow_dir / "adw_state.json"
        state_file.write_text(json.dumps(state_data))

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            result = scan_agents_directory()

            assert len(result) == 1
            assert result[0]["workflow_template"] == "adw_legacy_workflow"
            assert result[0]["model_used"] == "gpt-4"

    def test_malformed_json_file(self, tmp_path, caplog):
        """Test that malformed JSON files are handled gracefully."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        workflow_dir = agents_dir / "workflow-012"
        workflow_dir.mkdir()

        state_file = workflow_dir / "adw_state.json"
        state_file.write_text("{invalid json content}")

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            with caplog.at_level(logging.ERROR):
                result = scan_agents_directory()

            assert result == []
            assert any("Error parsing" in record.message for record in caplog.records)

    def test_permission_error_reading_file(self, tmp_path, caplog):
        """Test handling of permission errors when reading state files."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        workflow_dir = agents_dir / "workflow-013"
        workflow_dir.mkdir()

        state_file = workflow_dir / "adw_state.json"
        state_file.write_text(json.dumps({"issue_number": 42}))

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            # Mock open to raise PermissionError
            with patch("builtins.open", side_effect=PermissionError("Access denied")):
                with caplog.at_level(logging.ERROR):
                    result = scan_agents_directory()

                assert result == []
                assert any("Error parsing" in record.message for record in caplog.records)

    def test_multiple_valid_workflows(self, tmp_path):
        """Test scanning directory with multiple valid workflows."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        # Create first workflow
        workflow_dir1 = agents_dir / "workflow-001"
        workflow_dir1.mkdir()
        state_data1 = {
            "issue_number": 42,
            "nl_input": "First workflow",
            "status": "completed"
        }
        (workflow_dir1 / "adw_state.json").write_text(json.dumps(state_data1))

        # Create second workflow
        workflow_dir2 = agents_dir / "workflow-002"
        workflow_dir2.mkdir()
        state_data2 = {
            "issue_number": 43,
            "nl_input": "Second workflow",
            "status": "running"
        }
        (workflow_dir2 / "adw_state.json").write_text(json.dumps(state_data2))

        # Create third workflow
        workflow_dir3 = agents_dir / "workflow-003"
        workflow_dir3.mkdir()
        state_data3 = {
            "issue_number": 44,
            "nl_input": "Third workflow",
            "status": "failed"
        }
        (workflow_dir3 / "adw_state.json").write_text(json.dumps(state_data3))

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            result = scan_agents_directory()

            assert len(result) == 3

            # Check all workflows are present (order may vary)
            adw_ids = {w["adw_id"] for w in result}
            assert adw_ids == {"workflow-001", "workflow-002", "workflow-003"}

            issue_numbers = {w["issue_number"] for w in result}
            assert issue_numbers == {42, 43, 44}

    def test_mixed_valid_and_invalid_workflows(self, tmp_path, caplog):
        """Test scanning directory with mix of valid and invalid workflows."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        # Valid workflow
        workflow_dir1 = agents_dir / "workflow-001"
        workflow_dir1.mkdir()
        state_data1 = {
            "issue_number": 42,
            "nl_input": "Valid workflow",
            "status": "completed"
        }
        (workflow_dir1 / "adw_state.json").write_text(json.dumps(state_data1))

        # Invalid workflow (blacklisted issue)
        workflow_dir2 = agents_dir / "workflow-002"
        workflow_dir2.mkdir()
        state_data2 = {
            "issue_number": 999,  # Blacklisted
            "nl_input": "Invalid workflow",
            "status": "running"
        }
        (workflow_dir2 / "adw_state.json").write_text(json.dumps(state_data2))

        # Invalid workflow (negative issue)
        workflow_dir3 = agents_dir / "workflow-003"
        workflow_dir3.mkdir()
        state_data3 = {
            "issue_number": -1,  # Invalid
            "nl_input": "Another invalid workflow",
            "status": "failed"
        }
        (workflow_dir3 / "adw_state.json").write_text(json.dumps(state_data3))

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            with caplog.at_level(logging.WARNING):
                result = scan_agents_directory()

            # Only the valid workflow should be returned
            assert len(result) == 1
            assert result[0]["issue_number"] == 42

    def test_none_issue_number(self, tmp_path):
        """Test handling of None issue_number (should be allowed)."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        workflow_dir = agents_dir / "workflow-014"
        workflow_dir.mkdir()

        state_data = {
            "issue_number": None,
            "nl_input": "Test workflow without issue",
            "status": "completed"
        }

        state_file = workflow_dir / "adw_state.json"
        state_file.write_text(json.dumps(state_data))

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            result = scan_agents_directory()

            assert len(result) == 1
            assert result[0]["issue_number"] is None

    def test_missing_issue_number_field(self, tmp_path):
        """Test handling of missing issue_number field (should be allowed)."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        workflow_dir = agents_dir / "workflow-015"
        workflow_dir.mkdir()

        state_data = {
            "nl_input": "Test workflow without issue field",
            "status": "completed"
        }

        state_file = workflow_dir / "adw_state.json"
        state_file.write_text(json.dumps(state_data))

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            result = scan_agents_directory()

            assert len(result) == 1
            assert result[0]["issue_number"] is None

    def test_status_not_overridden_if_already_set(self, tmp_path):
        """Test that explicit non-running status is not overridden."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        workflow_dir = agents_dir / "workflow-016"
        workflow_dir.mkdir()

        # Create phases but status is already 'completed'
        (workflow_dir / "adw_plan").mkdir()

        state_data = {
            "issue_number": 42,
            "nl_input": "Test workflow",
            "status": "completed"  # Should NOT be overridden
        }

        state_file = workflow_dir / "adw_state.json"
        state_file.write_text(json.dumps(state_data))

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            result = scan_agents_directory()

            assert len(result) == 1
            assert result[0]["status"] == "completed"

    def test_worktree_path_is_absolute(self, tmp_path):
        """Test that worktree_path is set to absolute path."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        workflow_dir = agents_dir / "workflow-017"
        workflow_dir.mkdir()

        state_data = {
            "issue_number": 42,
            "nl_input": "Test workflow",
            "status": "completed"
        }

        state_file = workflow_dir / "adw_state.json"
        state_file.write_text(json.dumps(state_data))

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            result = scan_agents_directory()

            assert len(result) == 1
            # Should be an absolute path (contains the full tmp_path)
            assert Path(result[0]["worktree_path"]).is_absolute()

    def test_logging_debug_messages(self, tmp_path, caplog):
        """Test that debug logging messages are generated correctly."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        workflow_dir = agents_dir / "workflow-018"
        workflow_dir.mkdir()

        state_data = {
            "issue_number": 42,
            "nl_input": "Test workflow",
            "status": "completed"
        }

        state_file = workflow_dir / "adw_state.json"
        state_file.write_text(json.dumps(state_data))

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            with caplog.at_level(logging.DEBUG):
                result = scan_agents_directory()

            assert len(result) == 1

            # Check for debug messages
            debug_messages = [r.message for r in caplog.records if r.levelname == "DEBUG"]
            assert any("Found workflow" in msg for msg in debug_messages)
            assert any("Scanned agents directory" in msg for msg in debug_messages)

    def test_type_error_on_issue_number_conversion(self, tmp_path, caplog):
        """Test TypeError handling when converting issue_number."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        workflow_dir = agents_dir / "workflow-019"
        workflow_dir.mkdir()

        # Use a dict as issue_number (will cause TypeError)
        state_data = {
            "issue_number": {"invalid": "type"},
            "nl_input": "Test workflow",
            "status": "running"
        }

        state_file = workflow_dir / "adw_state.json"
        state_file.write_text(json.dumps(state_data))

        with patch("core.workflow_history_utils.filesystem.Path") as mock_path:
            mock_agents_dir = agents_dir
            mock_project_root = Mock()
            mock_project_root.__truediv__ = Mock(return_value=mock_agents_dir)

            mock_file_path = Mock()
            mock_file_path.parent.parent.parent.parent.parent = mock_project_root
            mock_path.return_value = mock_file_path
            mock_path.__file__ = "/fake/path/filesystem.py"

            with caplog.at_level(logging.WARNING):
                result = scan_agents_directory()

            assert result == []
            assert any("invalid issue_number" in record.message for record in caplog.records)
