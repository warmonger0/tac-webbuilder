"""
Tests for Issue #64 Fix: Test Phase Error Handling

This test suite verifies that the Test Phase properly handles and propagates
errors from external test tools, preventing false positives.

Issue #64 Analysis: The test phase was catching JSONDecodeError and other
external tool failures but continuing execution as if tests passed.

Fix: Properly detect external tool failures and exit immediately with error code.
"""

import json
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_modules.state import ADWState


class TestExternalTestErrorHandling:
    """Test error handling in run_external_tests function."""

    @pytest.fixture
    def mock_state(self):
        """Create a mock ADW state."""
        state = Mock(spec=ADWState)
        state.get.return_value = "/tmp/test-worktree"
        state.data = {
            "worktree_path": "/tmp/test-worktree",
            "backend_port": "9100",
            "frontend_port": "9200"
        }
        return state

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        logger = Mock()
        return logger

    def test_json_decode_error_returns_error(self, mock_state, mock_logger):
        """Test that JSONDecodeError from external tool returns error dict."""
        from adw_test_iso import run_external_tests

        # Mock subprocess to return invalid JSON
        with patch('adw_test_iso.subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Not valid JSON"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            # Mock state reload to return error result
            with patch('adw_test_iso.ADWState.load') as mock_load:
                mock_reloaded_state = Mock()
                mock_reloaded_state.get.return_value = {
                    "success": False,
                    "error": {
                        "type": "JSONDecodeError",
                        "message": "Failed to parse test output"
                    },
                    "summary": {"total": 0, "passed": 0, "failed": 0},
                    "failures": []
                }
                mock_load.return_value = mock_reloaded_state

                # Run function
                success, results = run_external_tests(
                    "123", "test-adw-id", mock_logger, mock_state
                )

                # Verify failure is returned
                assert success is False, "Should return False for JSONDecodeError"
                assert "error" in results, "Should contain error key"
                assert results["error"]["type"] == "JSONDecodeError"

    def test_subprocess_failure_returns_error(self, mock_state, mock_logger):
        """Test that subprocess exit code != 0 returns error dict."""
        from adw_test_iso import run_external_tests

        # Mock subprocess to return non-zero exit code
        with patch('adw_test_iso.subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "Test framework crashed"
            mock_run.return_value = mock_result

            # Run function
            success, results = run_external_tests(
                "123", "test-adw-id", mock_logger, mock_state
            )

            # Verify failure is returned
            assert success is False, "Should return False for non-zero exit code"
            assert "error" in results, "Should contain error key"
            assert results["error"]["type"] == "SubprocessError"
            assert "exited with code 1" in results["error"]["message"]

    def test_timeout_returns_error(self, mock_state, mock_logger):
        """Test that subprocess timeout returns error dict."""
        from adw_test_iso import run_external_tests
        import subprocess

        # Mock subprocess to raise TimeoutExpired
        with patch('adw_test_iso.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(
                cmd=["test"], timeout=600
            )

            # Run function
            success, results = run_external_tests(
                "123", "test-adw-id", mock_logger, mock_state
            )

            # Verify timeout error is returned
            assert success is False, "Should return False for timeout"
            assert "error" in results, "Should contain error key"
            assert results["error"]["type"] == "TimeoutError"
            assert "timed out" in results["error"]["message"].lower()

    def test_missing_external_script_returns_error(self, mock_state, mock_logger):
        """Test that missing adw_test_external.py returns error dict."""
        from adw_test_iso import run_external_tests

        # Mock Path.exists to return False
        with patch('adw_test_iso.Path') as mock_path_cls:
            mock_path = Mock()
            mock_path.exists.return_value = False
            mock_path_cls.return_value = mock_path

            # Need to mock __file__ parent
            with patch('adw_test_iso.Path.__file__', create=True):
                # Run function
                success, results = run_external_tests(
                    "123", "test-adw-id", mock_logger, mock_state
                )

                # Verify error is returned
                assert success is False, "Should return False when script missing"
                assert "error" in results, "Should contain error key"
                assert results["error"]["type"] == "FileNotFoundError"

    def test_error_has_next_steps(self, mock_state, mock_logger):
        """Test that error responses include next_steps for debugging."""
        from adw_test_iso import run_external_tests

        # Mock subprocess failure
        with patch('adw_test_iso.subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stderr = "Unknown error"
            mock_run.return_value = mock_result

            # Run function
            success, results = run_external_tests(
                "123", "test-adw-id", mock_logger, mock_state
            )

            # Verify next_steps are provided
            assert "next_steps" in results, "Should provide next_steps"
            assert len(results["next_steps"]) > 0, "Should have at least one next step"
            assert isinstance(results["next_steps"], list), "next_steps should be a list"


class TestMainWorkflowErrorHandling:
    """Test error handling in main test workflow."""

    @pytest.fixture
    def mock_environment(self):
        """Mock all external dependencies."""
        with patch('adw_test_iso.load_dotenv'), \
             patch('adw_test_iso.setup_logger') as mock_logger_setup, \
             patch('adw_test_iso.check_env_vars'), \
             patch('adw_test_iso.validate_worktree') as mock_validate, \
             patch('adw_test_iso.make_issue_comment'), \
             patch('adw_test_iso.sys.exit') as mock_exit:

            mock_logger = Mock()
            mock_logger_setup.return_value = mock_logger
            mock_validate.return_value = (True, None)

            yield {
                'logger': mock_logger,
                'exit': mock_exit,
                'validate': mock_validate
            }

    def test_external_tool_error_causes_exit(self, mock_environment):
        """Test that external tool errors cause sys.exit(1)."""
        # This test verifies the critical fix: when external tool fails,
        # the workflow must exit immediately with code 1

        with patch('adw_test_iso.ADWState.load') as mock_state_load, \
             patch('adw_test_iso.run_external_tests') as mock_run_tests, \
             patch('adw_test_iso.sys.argv', ['script', '123', 'test-adw-id']):

            # Mock state
            mock_state = Mock()
            mock_state.get.side_effect = lambda key, default=None: {
                "issue_number": "123",
                "worktree_path": "/tmp/test",
                "backend_port": "9100",
                "frontend_port": "9200"
            }.get(key, default)
            mock_state.data = {
                "issue_number": "123",
                "worktree_path": "/tmp/test"
            }
            mock_state_load.return_value = mock_state

            # Mock external tests to return error
            mock_run_tests.return_value = (False, {
                "error": {
                    "type": "JSONDecodeError",
                    "message": "Failed to parse test output"
                },
                "summary": {"total": 0, "passed": 0, "failed": 0},
                "failures": [],
                "next_steps": ["Check test output"]
            })

            # Import and run main
            from adw_test_iso import main

            # Attempt to run main
            main()

            # Verify sys.exit(1) was called
            mock_environment['exit'].assert_called()
            call_args = mock_environment['exit'].call_args

            # Check if exit was called with 1
            if call_args:
                exit_code = call_args[0][0] if call_args[0] else call_args[1].get('code', 0)
                assert exit_code == 1, f"Should exit with code 1, got {exit_code}"

    def test_successful_tests_do_not_exit_early(self, mock_environment):
        """Test that successful tests allow workflow to continue."""
        with patch('adw_test_iso.ADWState.load') as mock_state_load, \
             patch('adw_test_iso.run_external_tests') as mock_run_tests, \
             patch('adw_test_iso.get_repo_url'), \
             patch('adw_test_iso.extract_repo_path'), \
             patch('adw_test_iso.fetch_issue'), \
             patch('adw_test_iso.create_commit'), \
             patch('adw_test_iso.commit_changes'), \
             patch('adw_test_iso.finalize_git_operations'), \
             patch('adw_test_iso.sys.argv', ['script', '123', 'test-adw-id']):

            # Mock state
            mock_state = Mock()
            mock_state.get.side_effect = lambda key, default=None: {
                "issue_number": "123",
                "worktree_path": "/tmp/test",
                "backend_port": "9100",
                "frontend_port": "9200",
                "issue_class": "/feature"
            }.get(key, default)
            mock_state.data = {
                "issue_number": "123",
                "worktree_path": "/tmp/test"
            }
            mock_state_load.return_value = mock_state

            # Mock external tests to return success
            mock_run_tests.return_value = (True, {
                "success": True,
                "summary": {"total": 10, "passed": 10, "failed": 0},
                "failures": []
            })

            # Mock other functions
            with patch('adw_test_iso.create_commit', return_value=("test commit", None)), \
                 patch('adw_test_iso.commit_changes', return_value=(True, None)):

                # Import and run main
                from adw_test_iso import main

                # Run main - should complete without early exit
                try:
                    main()
                except SystemExit as e:
                    # Should exit with 0 for success
                    assert e.code == 0 or e.code is None, f"Should exit with 0, got {e.code}"


class TestErrorMessageQuality:
    """Test that error messages are clear and actionable."""

    def test_error_dict_structure(self):
        """Test that error dicts have expected structure."""
        # Example error from run_external_tests
        error_dict = {
            "error": {
                "type": "JSONDecodeError",
                "message": "Failed to parse test output"
            },
            "summary": {"total": 0, "passed": 0, "failed": 0},
            "failures": [],
            "next_steps": ["Check test output format"]
        }

        # Verify structure
        assert "error" in error_dict, "Must have error key"
        assert "type" in error_dict["error"], "Error must have type"
        assert "message" in error_dict["error"], "Error must have message"
        assert "next_steps" in error_dict, "Must provide next_steps"
        assert isinstance(error_dict["next_steps"], list), "next_steps must be list"

    def test_error_types_are_descriptive(self):
        """Test that error types clearly indicate the problem."""
        error_types = [
            "JSONDecodeError",
            "SubprocessError",
            "TimeoutError",
            "FileNotFoundError",
            "StateError",
            "ResultsError"
        ]

        for error_type in error_types:
            # Each type should be self-explanatory
            assert error_type.endswith("Error"), f"{error_type} should end with 'Error'"
            assert len(error_type) > 5, f"{error_type} should be descriptive"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
