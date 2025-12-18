"""
Tests for ToolCallTracker - Tool usage tracking in ADW workflows.

Verifies:
- Context manager behavior
- Tool call recording
- Success/failure detection
- Error message capture
- Observability integration
"""

import subprocess
from datetime import datetime
from unittest.mock import MagicMock, patch, call
import pytest

from adw_modules.tool_call_tracker import ToolCallTracker


class TestToolCallTrackerBasics:
    """Test basic ToolCallTracker functionality."""

    def test_tracker_initialization(self):
        """Verify tracker initializes with correct parameters."""
        tracker = ToolCallTracker(
            adw_id="adw-test-123",
            issue_number=42,
            phase_name="Build",
            phase_number=3,
            workflow_template="adw_sdlc_complete_iso"
        )

        assert tracker.adw_id == "adw-test-123"
        assert tracker.issue_number == 42
        assert tracker.phase_name == "Build"
        assert tracker.phase_number == 3
        assert tracker.workflow_template == "adw_sdlc_complete_iso"
        assert tracker.tool_calls == []

    def test_phase_number_inference(self):
        """Verify phase number is inferred from phase name if not provided."""
        phase_mappings = {
            "Plan": 1,
            "Validate": 2,
            "Build": 3,
            "Lint": 4,
            "Test": 5,
            "Review": 6,
            "Document": 7,
            "Ship": 8,
            "Cleanup": 9,
            "Verify": 10,
        }

        for phase_name, expected_number in phase_mappings.items():
            tracker = ToolCallTracker(
                adw_id="adw-test",
                issue_number=1,
                phase_name=phase_name
            )
            assert tracker.phase_number == expected_number

    def test_unknown_phase_defaults_to_zero(self):
        """Verify unknown phase names default to phase number 0."""
        tracker = ToolCallTracker(
            adw_id="adw-test",
            issue_number=1,
            phase_name="UnknownPhase"
        )
        assert tracker.phase_number == 0


class TestToolTracking:
    """Test tool call tracking functionality."""

    def test_track_successful_tool_call(self):
        """Verify successful tool call is tracked correctly."""
        tracker = ToolCallTracker(
            adw_id="adw-test",
            issue_number=1,
            phase_name="Build"
        )

        def successful_tool():
            return "success"

        result = tracker.track(
            tool_name="test_tool",
            callable_fn=successful_tool,
            parameters={"param1": "value1"}
        )

        assert result == "success"
        assert len(tracker.tool_calls) == 1

        tool_call = tracker.tool_calls[0]
        assert tool_call["tool_name"] == "test_tool"
        assert tool_call["success"] is True
        assert tool_call["error_message"] is None
        assert tool_call["parameters"] == {"param1": "value1"}
        assert "started_at" in tool_call
        assert "completed_at" in tool_call
        assert "duration_ms" in tool_call
        assert tool_call["duration_ms"] >= 0

    def test_track_failed_tool_call(self):
        """Verify failed tool call captures error message."""
        tracker = ToolCallTracker(
            adw_id="adw-test",
            issue_number=1,
            phase_name="Test"
        )

        def failing_tool():
            raise ValueError("Test error")

        result = tracker.track(
            tool_name="failing_tool",
            callable_fn=failing_tool
        )

        assert result is None
        assert len(tracker.tool_calls) == 1

        tool_call = tracker.tool_calls[0]
        assert tool_call["tool_name"] == "failing_tool"
        assert tool_call["success"] is False
        assert "ValueError: Test error" in tool_call["error_message"]

    def test_track_multiple_tools(self):
        """Verify multiple tool calls are tracked in order."""
        tracker = ToolCallTracker(
            adw_id="adw-test",
            issue_number=1,
            phase_name="Build"
        )

        tracker.track("tool1", lambda: "result1")
        tracker.track("tool2", lambda: "result2")
        tracker.track("tool3", lambda: "result3")

        assert len(tracker.tool_calls) == 3
        assert tracker.tool_calls[0]["tool_name"] == "tool1"
        assert tracker.tool_calls[1]["tool_name"] == "tool2"
        assert tracker.tool_calls[2]["tool_name"] == "tool3"

    def test_track_with_result_capture(self):
        """Verify result capture for subprocess.CompletedProcess."""
        tracker = ToolCallTracker(
            adw_id="adw-test",
            issue_number=1,
            phase_name="Test"
        )

        # Simulate successful subprocess
        mock_result = MagicMock(spec=subprocess.CompletedProcess)
        mock_result.returncode = 0

        result = tracker.track(
            tool_name="pytest",
            callable_fn=lambda: mock_result,
            capture_result=True
        )

        assert len(tracker.tool_calls) == 1
        tool_call = tracker.tool_calls[0]
        assert tool_call["success"] is True
        assert tool_call["result_summary"] == "returncode=0"

    def test_track_subprocess_failure(self):
        """Verify subprocess failures are captured correctly."""
        tracker = ToolCallTracker(
            adw_id="adw-test",
            issue_number=1,
            phase_name="Test"
        )

        # Simulate failed subprocess
        mock_result = MagicMock(spec=subprocess.CompletedProcess)
        mock_result.returncode = 1
        mock_result.stderr = b"Error output"

        result = tracker.track(
            tool_name="failing_test",
            callable_fn=lambda: mock_result,
            capture_result=True
        )

        assert len(tracker.tool_calls) == 1
        tool_call = tracker.tool_calls[0]
        assert tool_call["success"] is False
        assert "Non-zero exit code: 1" in tool_call["error_message"]
        assert "Error output" in tool_call["error_message"]


class TestBashTracking:
    """Test track_bash convenience method."""

    @patch('adw_modules.tool_call_tracker.subprocess.run')
    def test_track_bash_with_list_command(self, mock_run):
        """Verify track_bash handles list commands correctly."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["npm", "install"],
            returncode=0,
            stdout="",
            stderr=""
        )

        tracker = ToolCallTracker(
            adw_id="adw-test",
            issue_number=1,
            phase_name="Build"
        )

        result = tracker.track_bash(
            tool_name="npm_install",
            command=["npm", "install"],
            cwd="/test/path"
        )

        assert result.returncode == 0
        assert len(tracker.tool_calls) == 1

        tool_call = tracker.tool_calls[0]
        assert tool_call["tool_name"] == "npm_install"
        assert tool_call["parameters"]["command"] == "npm install"
        assert tool_call["parameters"]["cwd"] == "/test/path"

        # Verify subprocess.run was called correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["npm", "install"]
        assert call_args[1]["cwd"] == "/test/path"
        assert call_args[1]["capture_output"] is True
        assert call_args[1]["check"] is False

    @patch('adw_modules.tool_call_tracker.subprocess.run')
    def test_track_bash_with_string_command(self, mock_run):
        """Verify track_bash handles string commands correctly."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["pytest", "tests/"],
            returncode=0,
            stdout="",
            stderr=""
        )

        tracker = ToolCallTracker(
            adw_id="adw-test",
            issue_number=1,
            phase_name="Test"
        )

        result = tracker.track_bash(
            tool_name="pytest",
            command="pytest tests/"
        )

        assert result.returncode == 0
        # Verify command was split correctly
        call_args = mock_run.call_args
        assert call_args[0][0] == ["pytest", "tests/"]


class TestSummaryGeneration:
    """Test summary generation functionality."""

    def test_get_summary_empty(self):
        """Verify summary for tracker with no tool calls."""
        tracker = ToolCallTracker(
            adw_id="adw-test",
            issue_number=1,
            phase_name="Build"
        )

        summary = tracker.get_summary()
        assert summary["total_calls"] == 0
        assert summary["successful_calls"] == 0
        assert summary["failed_calls"] == 0
        assert summary["total_duration_ms"] == 0
        assert summary["tools_used"] == []

    def test_get_summary_with_calls(self):
        """Verify summary with mixed successful and failed calls."""
        tracker = ToolCallTracker(
            adw_id="adw-test",
            issue_number=1,
            phase_name="Test"
        )

        # Add successful calls
        tracker.track("tool1", lambda: "success")
        tracker.track("tool2", lambda: "success")

        # Add failed call
        def failing():
            raise Exception("fail")
        tracker.track("tool3", failing)

        summary = tracker.get_summary()
        assert summary["total_calls"] == 3
        assert summary["successful_calls"] == 2
        assert summary["failed_calls"] == 1
        assert summary["total_duration_ms"] >= 0  # Duration can be 0ms for fast operations
        assert set(summary["tools_used"]) == {"tool1", "tool2", "tool3"}


class TestContextManager:
    """Test context manager behavior."""

    @patch('adw_modules.tool_call_tracker.log_task_completion')
    def test_context_manager_success(self, mock_log):
        """Verify context manager logs tool calls on successful exit."""
        mock_log.return_value = True

        with ToolCallTracker(
            adw_id="adw-test-123",
            issue_number=42,
            phase_name="Build"
        ) as tracker:
            tracker.track("npm_install", lambda: "success")
            tracker.track("npm_build", lambda: "success")

        # Verify log_task_completion was called
        assert mock_log.called
        call_kwargs = mock_log.call_args[1]

        assert call_kwargs["adw_id"] == "adw-test-123"
        assert call_kwargs["issue_number"] == 42
        assert call_kwargs["phase_name"] == "Build"
        assert call_kwargs["phase_number"] == 3
        assert call_kwargs["phase_status"] == "completed"
        assert len(call_kwargs["tool_calls"]) == 2
        assert call_kwargs["tool_calls"][0]["tool_name"] == "npm_install"
        assert call_kwargs["tool_calls"][1]["tool_name"] == "npm_build"

    @patch('adw_modules.tool_call_tracker.log_task_completion')
    def test_context_manager_with_exception(self, mock_log):
        """Verify context manager handles exceptions and logs failure."""
        mock_log.return_value = True

        with pytest.raises(RuntimeError):
            with ToolCallTracker(
                adw_id="adw-test",
                issue_number=1,
                phase_name="Test"
            ) as tracker:
                tracker.track("tool1", lambda: "success")
                raise RuntimeError("Test exception")

        # Verify failure was logged
        assert mock_log.called
        call_kwargs = mock_log.call_args[1]
        assert call_kwargs["phase_status"] == "failed"
        assert "RuntimeError: Test exception" in call_kwargs["error_message"]

    @patch('adw_modules.tool_call_tracker.log_task_completion')
    def test_context_manager_logging_failure_non_blocking(self, mock_log):
        """Verify logging failures don't block workflow (zero-overhead)."""
        mock_log.side_effect = Exception("Logging failed")

        # Should not raise exception
        with ToolCallTracker(
            adw_id="adw-test",
            issue_number=1,
            phase_name="Build"
        ) as tracker:
            tracker.track("tool1", lambda: "success")

        # Verify log_task_completion was attempted
        assert mock_log.called

    @patch('adw_modules.tool_call_tracker.log_task_completion')
    def test_context_manager_with_failed_tools(self, mock_log):
        """Verify phase with failed tools still completes (not failed status)."""
        mock_log.return_value = True

        with ToolCallTracker(
            adw_id="adw-test",
            issue_number=1,
            phase_name="Test"
        ) as tracker:
            tracker.track("passing_test", lambda: "success")
            tracker.track("failing_test", lambda: (_ for _ in ()).throw(Exception("fail")))

        # Phase should be "completed" even with tool failures
        # Individual tool errors are in tool_calls array
        call_kwargs = mock_log.call_args[1]
        assert call_kwargs["phase_status"] == "completed"
        assert call_kwargs["error_message"] is None
        assert len(call_kwargs["tool_calls"]) == 2
        assert call_kwargs["tool_calls"][0]["success"] is True
        assert call_kwargs["tool_calls"][1]["success"] is False


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_tool_with_empty_parameters(self):
        """Verify tools can be tracked without parameters."""
        tracker = ToolCallTracker(
            adw_id="adw-test",
            issue_number=1,
            phase_name="Build"
        )

        tracker.track("simple_tool", lambda: "result")

        assert len(tracker.tool_calls) == 1
        assert tracker.tool_calls[0]["parameters"] == {}

    def test_error_message_truncation(self):
        """Verify long error messages are truncated."""
        tracker = ToolCallTracker(
            adw_id="adw-test",
            issue_number=1,
            phase_name="Test"
        )

        long_error = "X" * 1000

        def failing():
            raise ValueError(long_error)

        tracker.track("tool", failing)

        # Error message should be truncated to 500 chars
        error_msg = tracker.tool_calls[0]["error_message"]
        assert len(error_msg) <= 520  # "ValueError: " + 500 chars + some buffer

    def test_result_summary_truncation(self):
        """Verify long result summaries are truncated."""
        tracker = ToolCallTracker(
            adw_id="adw-test",
            issue_number=1,
            phase_name="Build"
        )

        long_result = "Y" * 500

        result = tracker.track(
            "tool",
            lambda: long_result,
            capture_result=True
        )

        # Result summary should be truncated to 200 chars
        assert len(tracker.tool_calls[0]["result_summary"]) <= 200

    def test_duration_calculation(self):
        """Verify duration is calculated correctly."""
        tracker = ToolCallTracker(
            adw_id="adw-test",
            issue_number=1,
            phase_name="Test"
        )

        import time

        def slow_tool():
            time.sleep(0.01)  # 10ms
            return "done"

        tracker.track("slow_tool", slow_tool)

        # Duration should be at least 10ms
        assert tracker.tool_calls[0]["duration_ms"] >= 10
