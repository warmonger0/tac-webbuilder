"""
Automatic success operations for completed ADW workflows.

This module provides functions to handle successful workflow completion:
- Close associated issues with success comments
- Post success summaries
- Mark workflows as complete
- Update queue status to "completed"
- Learn patterns from completed workflows (automatic pattern caching)

Mirrors the structure of failure_cleanup.py for consistency.
"""

import logging
import subprocess
import requests
import sys
from typing import Optional, Tuple

from .github import make_issue_comment
from .workflow_ops import format_issue_message

# Backend API configuration
BACKEND_URL = "http://localhost:8000"

# Add app/server to path for pattern caching imports
sys.path.insert(0, '/Users/Warmonger0/tac/tac-webbuilder/app/server')
from core.workflow_pattern_cache import save_completed_workflow_pattern  # noqa: E402


def complete_queue_for_issue(issue_number: str, logger: logging.Logger) -> Tuple[bool, Optional[str]]:
    """Update queue status to 'completed' for all phases of an issue.

    Args:
        issue_number: GitHub issue number
        logger: Logger instance

    Returns:
        Tuple of (success, error_message)
    """
    try:
        logger.info(f"Updating queue status to 'completed' for issue #{issue_number}...")

        response = requests.post(
            f"{BACKEND_URL}/api/issue/{issue_number}/complete",
            json={"issue_number": int(issue_number)},
            timeout=10
        )

        if response.status_code == 200:
            logger.info(f"✅ Queue status updated to 'completed' for issue #{issue_number}")
            return True, None
        else:
            error_msg = f"Failed to update queue: {response.status_code} - {response.text}"
            logger.warning(error_msg)
            return False, error_msg

    except Exception as e:
        error_msg = f"Exception while updating queue: {e}"
        logger.warning(error_msg)
        return False, error_msg


def close_issue_on_success(
    adw_id: str,
    issue_number: str,
    branch_name: str,
    agent_name: str,
    logger: logging.Logger
) -> Tuple[bool, Optional[str]]:
    """Close issue after successful workflow completion.

    This function:
    1. Updates queue status to "completed"
    2. Closes issue with success comment
    3. Posts success summary
    4. Handles errors gracefully (best-effort)

    Args:
        adw_id: ADW workflow ID
        issue_number: GitHub issue number
        branch_name: Feature branch that was merged
        agent_name: Name of agent posting (e.g., "shipper")
        logger: Logger instance

    Returns:
        Tuple of (success, error_message)
    """
    logger.info(f"Completing issue #{issue_number} after successful ship...")

    # Step 1: Update queue status to "completed"
    queue_success, queue_error = complete_queue_for_issue(issue_number, logger)
    if not queue_success:
        logger.warning(f"Queue update failed but continuing with issue close: {queue_error}")

    # Step 1.5: Learn pattern from completed workflow (automatic pattern caching)
    try:
        logger.info(f"Learning workflow pattern from completed issue #{issue_number}...")
        pattern_saved = save_completed_workflow_pattern(
            feature_id=int(issue_number),
            logger=logger
        )
        if pattern_saved:
            logger.info(f"✅ Pattern saved for future dry-run acceleration")
        else:
            logger.info("Pattern not saved (may already exist or insufficient data)")
    except Exception as e:
        # Best-effort - don't fail completion if pattern saving fails
        logger.warning(f"Failed to save workflow pattern: {e}")

    try:
        # Step 2: Format success comment
        success_comment = format_success_comment(branch_name)

        # Step 3: Close issue with comment
        result = subprocess.run(
            ["gh", "issue", "close", issue_number, "--comment", success_comment],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            logger.info(f"✅ Closed issue #{issue_number} with success comment")

            # Post additional success message for context
            post_success_summary(
                adw_id=adw_id,
                issue_number=issue_number,
                branch_name=branch_name,
                agent_name=agent_name
            )

            return True, None
        else:
            error_msg = f"Failed to close issue #{issue_number}: {result.stderr}"
            logger.warning(error_msg)

            # Post manual reminder as fallback
            post_manual_close_reminder(
                adw_id=adw_id,
                issue_number=issue_number,
                agent_name=agent_name
            )

            return False, error_msg

    except Exception as e:
        error_msg = f"Exception while closing issue: {e}"
        logger.warning(error_msg)
        # Best-effort - don't fail ship if issue closing fails
        return False, error_msg


def format_success_comment(branch_name: str) -> str:
    """Format success comment for issue closing.

    Args:
        branch_name: Feature branch that was merged

    Returns:
        Formatted success comment
    """
    return f"""🎉 **Successfully Shipped!**

✅ PR merged to main via GitHub API
✅ Branch `{branch_name}` deployed to production
✅ All validation checks passed

**Ship Summary:**
- Validated all state fields
- Found and merged PR successfully
- Verified commits landed on main
- Code is now in production

**Issue Status:** Automatically closing as resolved.
"""


def post_success_summary(
    adw_id: str,
    issue_number: str,
    branch_name: str,
    agent_name: str
) -> None:
    """Post success summary to issue (additional context).

    Args:
        adw_id: ADW workflow ID
        issue_number: GitHub issue number
        branch_name: Feature branch that was merged
        agent_name: Name of agent posting
    """
    try:
        summary = format_issue_message(
            adw_id, agent_name,
            f"🎉 **Successfully shipped!**\n\n"
            f"✅ Validated all state fields\n"
            f"✅ Found and merged PR via GitHub API\n"
            f"✅ Branch `{branch_name}` merged to main\n\n"
            f"🚢 Code has been deployed to production!"
        )

        make_issue_comment(issue_number, summary)

    except Exception as e:
        # Best-effort - don't throw if this fails
        logging.warning(f"Failed to post success summary: {e}")


def post_manual_close_reminder(
    adw_id: str,
    issue_number: str,
    agent_name: str
) -> None:
    """Post reminder to manually close issue if auto-close fails.

    Args:
        adw_id: ADW workflow ID
        issue_number: GitHub issue number
        agent_name: Name of agent posting
    """
    try:
        reminder = format_issue_message(
            adw_id, agent_name,
            "⚠️ Could not automatically close issue\n"
            "Please close manually - ship was successful!"
        )

        make_issue_comment(issue_number, reminder)

    except Exception as e:
        # Best-effort - don't throw if this fails
        logging.warning(f"Failed to post manual close reminder: {e}")
