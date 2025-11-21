"""
Unit tests for workflow_history.github_client module.

Tests GitHub API client functions.
"""

from unittest.mock import patch

from core.workflow_history_utils.github_client import fetch_github_issue_state
from utils.process_runner import ProcessResult


class TestFetchGitHubIssueState:
    """Tests for fetch_github_issue_state function."""

    @patch('core.workflow_history_utils.github_client.ProcessRunner.run_gh_command')
    def test_fetch_open_issue(self, mock_run_gh):
        """Test fetching an open issue."""
        mock_run_gh.return_value = ProcessResult(
            success=True,
            stdout="open\n",
            stderr="",
            returncode=0,
            command="gh issue view 123 --json state --jq .state"
        )

        result = fetch_github_issue_state(123)

        assert result == "open"
        mock_run_gh.assert_called_once_with(
            ["issue", "view", "123", "--json", "state", "--jq", ".state"],
            timeout=5
        )

    @patch('core.workflow_history_utils.github_client.ProcessRunner.run_gh_command')
    def test_fetch_closed_issue(self, mock_run_gh):
        """Test fetching a closed issue."""
        mock_run_gh.return_value = ProcessResult(
            success=True,
            stdout="closed\n",
            stderr="",
            returncode=0,
            command="gh issue view 456 --json state --jq .state"
        )

        result = fetch_github_issue_state(456)

        assert result == "closed"
        mock_run_gh.assert_called_once_with(
            ["issue", "view", "456", "--json", "state", "--jq", ".state"],
            timeout=5
        )

    @patch('core.workflow_history_utils.github_client.ProcessRunner.run_gh_command')
    def test_fetch_with_whitespace(self, mock_run_gh):
        """Test that whitespace is properly stripped."""
        mock_run_gh.return_value = ProcessResult(
            success=True,
            stdout="  open  \n",
            stderr="",
            returncode=0,
            command="gh issue view 789 --json state --jq .state"
        )

        result = fetch_github_issue_state(789)

        assert result == "open"

    @patch('core.workflow_history_utils.github_client.ProcessRunner.run_gh_command')
    def test_fetch_with_uppercase(self, mock_run_gh):
        """Test that uppercase states are lowercased."""
        mock_run_gh.return_value = ProcessResult(
            success=True,
            stdout="OPEN",
            stderr="",
            returncode=0,
            command="gh issue view 999 --json state --jq .state"
        )

        result = fetch_github_issue_state(999)

        assert result == "open"

    @patch('core.workflow_history_utils.github_client.ProcessRunner.run_gh_command')
    def test_fetch_invalid_state(self, mock_run_gh):
        """Test handling of invalid state values."""
        mock_run_gh.return_value = ProcessResult(
            success=True,
            stdout="invalid_state",
            stderr="",
            returncode=0,
            command="gh issue view 111 --json state --jq .state"
        )

        result = fetch_github_issue_state(111)

        assert result is None

    @patch('core.workflow_history_utils.github_client.ProcessRunner.run_gh_command')
    def test_fetch_command_failure(self, mock_run_gh):
        """Test handling of command failure."""
        mock_run_gh.return_value = ProcessResult(
            success=False,
            stdout="",
            stderr="Error: issue not found",
            returncode=1,
            command="gh issue view 222 --json state --jq .state"
        )

        result = fetch_github_issue_state(222)

        assert result is None

    @patch('core.workflow_history_utils.github_client.ProcessRunner.run_gh_command')
    def test_fetch_with_exception(self, mock_run_gh):
        """Test handling of exceptions."""
        mock_run_gh.side_effect = Exception("Network error")

        result = fetch_github_issue_state(333)

        assert result is None

    @patch('core.workflow_history_utils.github_client.ProcessRunner.run_gh_command')
    def test_fetch_with_timeout(self, mock_run_gh):
        """Test that timeout parameter is passed correctly."""
        mock_run_gh.return_value = ProcessResult(
            success=True,
            stdout="open",
            stderr="",
            returncode=0,
            command="gh issue view 444 --json state --jq .state"
        )

        fetch_github_issue_state(444)

        # Verify timeout is set to 5 seconds
        call_args = mock_run_gh.call_args
        assert call_args[1]["timeout"] == 5

    @patch('core.workflow_history_utils.github_client.ProcessRunner.run_gh_command')
    def test_fetch_empty_response(self, mock_run_gh):
        """Test handling of empty response."""
        mock_run_gh.return_value = ProcessResult(
            success=True,
            stdout="",
            stderr="",
            returncode=0,
            command="gh issue view 555 --json state --jq .state"
        )

        result = fetch_github_issue_state(555)

        assert result is None
