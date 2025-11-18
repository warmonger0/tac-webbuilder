"""Commit message generation and git operations for ADW workflows.

This module provides Python functions to generate commit messages and create commits
without AI calls. Uses template-based generation for consistent, deterministic commits.
"""

import os
import subprocess
import logging
import re
from typing import Tuple, Optional
from adw_modules.data_types import GitHubIssue


def generate_commit_message(
    agent_name: str,
    issue_type: str,
    issue: GitHubIssue,
    max_length: int = 50
) -> str:
    """Generate a commit message using templates based on issue type.

    Format: <agent_name>: <issue_type>: <commit message>

    Args:
        agent_name: Name of the agent creating the commit (e.g., "sdlc_planner")
        issue_type: Type of issue (/feature, /bug, /chore) - slash will be removed
        issue: GitHub issue object
        max_length: Maximum length of commit message portion (default: 50)

    Returns:
        Formatted commit message string
    """
    # Remove leading slash from issue_type
    issue_type_clean = issue_type.replace("/", "").lower()

    # Sanitize and shorten title for commit message
    title = issue.title.strip()

    # Remove common prefixes/suffixes from title
    title = re.sub(r'^(feat|feature|bug|fix|chore)[:\s]+', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s+(issue|#\d+)\s*$', '', title, flags=re.IGNORECASE)

    # Convert to lowercase and simplify
    title = title.lower()

    # Generate verb prefix based on issue type
    verb_map = {
        "feature": "add",
        "feat": "add",
        "bug": "fix",
        "fix": "fix",
        "chore": "update"
    }
    verb = verb_map.get(issue_type_clean, "update")

    # If title doesn't start with a verb, prepend one
    if not any(title.startswith(v) for v in ["add", "fix", "update", "remove", "create", "implement"]):
        title = f"{verb} {title}"

    # Truncate to max_length
    if len(title) > max_length:
        title = title[:max_length].rsplit(' ', 1)[0]  # Break at word boundary

    # Format: agent_name: issue_type: message
    commit_message = f"{agent_name}: {issue_type_clean}: {title}"

    return commit_message


def create_commit(
    commit_message: str,
    working_dir: Optional[str] = None,
    logger: Optional[logging.Logger] = None
) -> Tuple[bool, Optional[str]]:
    """Create a git commit with the given message.

    This performs:
    1. git add -A (stage all changes)
    2. git commit -m "<message>" (create commit)

    Args:
        commit_message: Commit message to use
        working_dir: Directory where git commands should run (defaults to cwd)
        logger: Optional logger instance

    Returns:
        Tuple of (success, error_message)
    """
    cwd = working_dir or os.getcwd()

    if logger:
        logger.info(f"Creating commit: {commit_message}")

    # Stage all changes
    result = subprocess.run(
        ["git", "add", "-A"],
        cwd=cwd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        error_msg = f"Failed to stage changes: {result.stderr}"
        if logger:
            logger.error(error_msg)
        return False, error_msg

    # Check if there are any changes to commit
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=cwd,
        capture_output=True,
        text=True
    )

    # Exit code 0 means no changes, 1 means there are changes
    if result.returncode == 0:
        msg = "No changes to commit"
        if logger:
            logger.warning(msg)
        # This is not necessarily an error - return success
        return True, None

    # Create commit
    result = subprocess.run(
        ["git", "commit", "-m", commit_message],
        cwd=cwd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        error_msg = f"Failed to create commit: {result.stderr}"
        if logger:
            logger.error(error_msg)
        return False, error_msg

    if logger:
        logger.info(f"✅ Commit created: {commit_message}")

    return True, None


def generate_and_commit(
    agent_name: str,
    issue_type: str,
    issue: GitHubIssue,
    working_dir: Optional[str] = None,
    logger: Optional[logging.Logger] = None
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Generate commit message and create commit in one step.

    This is a convenience function that combines generate_commit_message()
    and create_commit().

    Args:
        agent_name: Name of the agent creating the commit
        issue_type: Type of issue (/feature, /bug, /chore)
        issue: GitHub issue object
        working_dir: Directory where git commands should run
        logger: Optional logger instance

    Returns:
        Tuple of (success, commit_message, error_message)
    """
    # Generate commit message
    commit_message = generate_commit_message(agent_name, issue_type, issue)

    # Create commit
    success, error = create_commit(commit_message, working_dir, logger)

    if success:
        return True, commit_message, None
    else:
        return False, commit_message, error


def get_git_diff_summary(
    working_dir: Optional[str] = None,
    logger: Optional[logging.Logger] = None
) -> Tuple[bool, str]:
    """Get a summary of current git changes.

    Returns output similar to `git diff --stat`.

    Args:
        working_dir: Directory where git command should run
        logger: Optional logger instance

    Returns:
        Tuple of (success, diff_output)
    """
    cwd = working_dir or os.getcwd()

    result = subprocess.run(
        ["git", "diff", "--stat"],
        cwd=cwd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        error_msg = f"Failed to get diff: {result.stderr}"
        if logger:
            logger.error(error_msg)
        return False, error_msg

    return True, result.stdout
