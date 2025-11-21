"""
GitHub API client for workflow history.

This module provides functions for interacting with GitHub to fetch
issue state and other metadata.
"""

import logging

from utils.process_runner import ProcessRunner

logger = logging.getLogger(__name__)


def fetch_github_issue_state(issue_number: int) -> str | None:
    """
    Fetch the current state of a GitHub issue using gh CLI.

    Args:
        issue_number: GitHub issue number

    Returns:
        'open', 'closed', or None if unable to fetch
    """
    try:
        result = ProcessRunner.run_gh_command(
            ["issue", "view", str(issue_number), "--json", "state", "--jq", ".state"],
            timeout=5
        )
        if result.success:
            state = result.stdout.strip().lower()
            return state if state in ['open', 'closed'] else None
        return None
    except Exception as e:
        logger.debug(f"Failed to fetch GitHub issue state for #{issue_number}: {e}")
        return None
