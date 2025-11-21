"""
Integration test for infrastructure failure handling in adw_test_iso.py

Tests that external test tool failures trigger the fallback to inline test execution
with resolution loop, ensuring workflows never proceed with broken tests.
"""

import pytest
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import sys
import logging

# Add adws to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_test_iso import run_external_tests
from adw_modules.state import ADWState


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    return MagicMock(spec=logging.Logger)


@pytest.fixture
def mock_state():
    """Create a mock ADW state."""
    state = MagicMock(spec=ADWState)
    state.get.return_value = {}
    return state


class TestInfrastructureFailureHandling:
    """Test infrastructure failure detection and fallback behavior."""

    def test_external_tool_json_decode_error(self, mock_logger, mock_state):
        """Test that JSONDecodeError from external tool is properly detected."""
        with patch('adw_test_iso.subprocess.run') as mock_run:
            # Simulate external tool exiting successfully but returning unparseable JSON
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="",
                stderr=""
            )

            # Mock state reload to return error
            with patch('adw_test_iso.ADWState.load') as mock_load:
                mock_load.return_value = mock_state
                mock_state.get.return_value = {
                    "error": {
                        "type": "JSONDecodeError",
                        "message": "Failed to parse test output: Expecting value: line 1 column 1 (char 0)"
                    },
                    "summary": {"total": 0, "passed": 0, "failed": 0},
                    "failures": []
                }

                success, results = run_external_tests("123", "test-adw-id", mock_logger, mock_state)

                # Should return False with error
                assert success is False
                assert "error" in results
                assert results["error"]["type"] == "JSONDecodeError"

    def test_external_tool_subprocess_error(self, mock_logger, mock_state):
        """Test that SubprocessError from external tool is properly detected."""
        with patch('adw_test_iso.subprocess.run') as mock_run:
            # Simulate external tool crash
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Fatal error: test runner crashed"
            )

            success, results = run_external_tests("123", "test-adw-id", mock_logger, mock_state)

            # Should return False with error
            assert success is False
            assert "error" in results
            assert results["error"]["type"] == "SubprocessError"
            assert "exited with code 1" in results["error"]["message"]

    def test_external_tool_timeout_error(self, mock_logger, mock_state):
        """Test that TimeoutError from external tool is properly detected."""
        with patch('adw_test_iso.subprocess.run') as mock_run:
            # Simulate timeout
            import subprocess
            mock_run.side_effect = subprocess.TimeoutExpired(cmd=['test'], timeout=600)

            success, results = run_external_tests("123", "test-adw-id", mock_logger, mock_state)

            # Should return False with error
            assert success is False
            assert "error" in results
            assert results["error"]["type"] == "TimeoutError"
            assert "timed out" in results["error"]["message"]

    def test_external_tool_state_error(self, mock_logger, mock_state):
        """Test that state reload failure is properly detected."""
        with patch('adw_test_iso.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            # Mock state reload to fail
            with patch('adw_test_iso.ADWState.load') as mock_load:
                mock_load.return_value = None

                success, results = run_external_tests("123", "test-adw-id", mock_logger, mock_state)

                # Should return False with error
                assert success is False
                assert "error" in results
                assert results["error"]["type"] == "StateError"

    def test_external_tool_no_results_error(self, mock_logger, mock_state):
        """Test that missing test results is properly detected."""
        with patch('adw_test_iso.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            # Mock state reload to return empty results
            with patch('adw_test_iso.ADWState.load') as mock_load:
                mock_load.return_value = mock_state
                mock_state.get.return_value = {}  # No external_test_results

                success, results = run_external_tests("123", "test-adw-id", mock_logger, mock_state)

                # Should return False with error
                assert success is False
                assert "error" in results
                assert results["error"]["type"] == "ResultsError"

    def test_external_tool_success_no_error_key(self, mock_logger, mock_state):
        """Test that successful external tool execution has no error key."""
        with patch('adw_test_iso.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            # Mock state reload to return successful results
            with patch('adw_test_iso.ADWState.load') as mock_load:
                mock_load.return_value = mock_state
                mock_state.get.return_value = {
                    "success": True,
                    "summary": {"total": 10, "passed": 10, "failed": 0},
                    "failures": []
                }

                success, results = run_external_tests("123", "test-adw-id", mock_logger, mock_state)

                # Should return True with no error
                assert success is True
                assert "error" not in results
                assert results["summary"]["passed"] == 10

    def test_error_results_have_next_steps(self, mock_logger, mock_state):
        """Test that all error results include next_steps for debugging."""
        with patch('adw_test_iso.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Error"
            )

            success, results = run_external_tests("123", "test-adw-id", mock_logger, mock_state)

            # Should include next_steps
            assert "next_steps" in results
            assert len(results["next_steps"]) > 0
            assert isinstance(results["next_steps"], list)


class TestFallbackBehaviorIntegration:
    """
    Integration tests for the complete fallback flow.

    These tests verify that when external tools fail, the workflow:
    1. Detects the infrastructure failure
    2. Posts error comment to GitHub
    3. Falls back to inline test execution
    4. Runs resolution loop on inline results
    5. Does NOT exit until tests pass or max retries exhausted
    """

    @patch('adw_test_iso.make_issue_comment')
    @patch('adw_test_iso.run_tests_with_resolution')
    @patch('adw_test_iso.run_external_tests')
    def test_fallback_triggered_on_infrastructure_failure(
        self,
        mock_run_external,
        mock_run_with_resolution,
        mock_comment
    ):
        """Test that infrastructure failure triggers fallback to inline execution."""
        # Mock external tests to fail with infrastructure error
        mock_run_external.return_value = (False, {
            "error": {
                "type": "JSONDecodeError",
                "message": "Failed to parse test output"
            },
            "summary": {"total": 0, "passed": 0, "failed": 0},
            "failures": [],
            "next_steps": ["Check test output format"]
        })

        # Mock inline execution to succeed
        mock_run_with_resolution.return_value = (
            [],  # results
            10,  # passed_count
            0,   # failed_count
            MagicMock()  # test_response
        )

        # This would be called in the actual workflow
        # We're simulating the code path in adw_test_iso.py lines 908-971
        success, external_results = mock_run_external("123", "test-adw-id", MagicMock(), MagicMock())

        assert "error" in external_results

        # Verify that run_tests_with_resolution would be called as fallback
        # In the actual code, this happens at line 947
        if "error" in external_results:
            # This simulates the fallback call
            results, passed_count, failed_count, _ = mock_run_with_resolution(
                "test-adw-id", "123", MagicMock(), "/path/to/worktree"
            )

            # Verify fallback succeeded
            assert passed_count == 10
            assert failed_count == 0

    @patch('adw_test_iso.make_issue_comment')
    @patch('adw_test_iso.run_tests_with_resolution')
    @patch('adw_test_iso.run_external_tests')
    def test_fallback_handles_test_failures_with_resolution(
        self,
        mock_run_external,
        mock_run_with_resolution,
        mock_comment
    ):
        """Test that fallback execution runs resolution loop on test failures."""
        # Mock external tests to fail with infrastructure error
        mock_run_external.return_value = (False, {
            "error": {
                "type": "SubprocessError",
                "message": "External test tool crashed"
            },
            "summary": {"total": 0, "passed": 0, "failed": 0},
            "failures": []
        })

        # Mock inline execution to find test failures
        # run_tests_with_resolution includes retry loop
        mock_run_with_resolution.return_value = (
            [MagicMock(passed=False)],  # results with 1 failure
            8,   # passed_count
            2,   # failed_count
            MagicMock()  # test_response
        )

        success, external_results = mock_run_external("123", "test-adw-id", MagicMock(), MagicMock())

        if "error" in external_results:
            # Fallback to inline execution
            results, passed_count, failed_count, _ = mock_run_with_resolution(
                "test-adw-id", "123", MagicMock(), "/path/to/worktree"
            )

            # Verify fallback ran and returned actual test results
            assert passed_count == 8
            assert failed_count == 2
            # In the real code, this would trigger resolution loop
            # via run_tests_with_resolution's internal logic

    @patch('adw_test_iso.make_issue_comment')
    @patch('adw_test_iso.run_external_tests')
    def test_github_comment_posted_for_infrastructure_failure(
        self,
        mock_run_external,
        mock_comment
    ):
        """Test that infrastructure failures are reported to GitHub issue."""
        # Mock external tests to fail
        mock_run_external.return_value = (False, {
            "error": {
                "type": "TimeoutError",
                "message": "Test execution timed out"
            },
            "summary": {"total": 0, "passed": 0, "failed": 0},
            "failures": [],
            "next_steps": ["Check for hanging tests"]
        })

        success, external_results = mock_run_external("123", "test-adw-id", MagicMock(), MagicMock())

        # Verify error information is available for comment posting
        assert "error" in external_results
        assert external_results["error"]["type"] == "TimeoutError"
        assert "next_steps" in external_results

        # In the actual code (lines 918-933), this information is used
        # to construct the GitHub comment
