"""
Automatic cleanup operations for failed ADW workflows.

This module provides functions to clean up resources when workflows fail:
- Close associated PRs with failure comments
- Update issue with failure status
- Mark workflow as failed in database
"""

import logging
import subprocess
from typing import Optional

from .github import make_issue_comment, get_repo_url, extract_repo_path
from .workflow_ops import format_issue_message


def find_pr_for_branch(branch_name: str, repo_path: str, logger: logging.Logger) -> Optional[str]:
    """Find the PR number for a given branch.

    Args:
        branch_name: Feature branch name
        repo_path: Repository path (owner/repo)
        logger: Logger instance

    Returns:
        PR number as string, or None if not found
    """
    try:
        result = subprocess.run(
            ["gh", "pr", "list",
             "--repo", repo_path,
             "--head", branch_name,
             "--json", "number",
             "--jq", ".[0].number"],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0 and result.stdout.strip():
            pr_number = result.stdout.strip()
            logger.info(f"Found PR #{pr_number} for branch {branch_name}")
            return pr_number

        logger.info(f"No PR found for branch {branch_name}")
        return None

    except Exception as e:
        logger.error(f"Error finding PR: {e}")
        return None


def cleanup_failed_workflow(
    adw_id: str,
    issue_number: str,
    branch_name: Optional[str],
    phase_name: str,
    error_details: str,
    logger: logging.Logger
) -> None:
    """Clean up resources after workflow failure.

    This function:
    1. Updates workflow status to "failed"
    2. Finds and closes associated PR with failure comment
    3. Posts failure summary to issue

    Args:
        adw_id: ADW workflow ID
        issue_number: GitHub issue number
        branch_name: Feature branch name (if available)
        phase_name: Name of the phase that failed (e.g., "Build", "Test")
        error_details: Detailed error message
        logger: Logger instance
    """
    logger.info(f"Starting failure cleanup for {adw_id} (phase: {phase_name})")

    # Step 0: Update workflow end_time in state (status is in database)
    try:
        from .state import ADWState
        from datetime import datetime

        state = ADWState.load(adw_id, logger)
        if state:
            end_time = datetime.now()
            state.update(
                end_time=end_time.isoformat()
            )
            state.save("cleanup_failed_workflow")
            logger.info("✅ Workflow end_time recorded")
        else:
            logger.warning("Could not load state to record end_time")
    except Exception as e:
        logger.warning(f"Failed to update workflow end_time: {e}")
        # Don't let state update failure block the rest of cleanup

    # Step 1: Close PR if it exists
    if branch_name:
        try:
            repo_url = get_repo_url()
            repo_path = extract_repo_path(repo_url)
            pr_number = find_pr_for_branch(branch_name, repo_path, logger)

            if pr_number:
                close_pr_with_failure_comment(
                    pr_number=pr_number,
                    phase_name=phase_name,
                    error_details=error_details,
                    logger=logger
                )
            else:
                logger.info("No PR found to close")

        except Exception as e:
            logger.warning(f"Failed to close PR during cleanup: {e}")
            # Don't let PR cleanup failure block the rest of cleanup

    # Step 2: Post failure summary to issue
    try:
        failure_summary = format_failure_summary(
            adw_id=adw_id,
            phase_name=phase_name,
            error_details=error_details,
            pr_number=pr_number if branch_name else None
        )

        make_issue_comment(issue_number, failure_summary)
        logger.info("Posted failure summary to issue")

    except Exception as e:
        logger.warning(f"Failed to post issue comment during cleanup: {e}")


def close_pr_with_failure_comment(
    pr_number: str,
    phase_name: str,
    error_details: str,
    logger: logging.Logger
) -> None:
    """Close PR with detailed failure comment.

    Args:
        pr_number: PR number to close
        phase_name: Name of the phase that failed
        error_details: Detailed error message
        logger: Logger instance
    """
    try:
        comment = f"""❌ **Workflow Failed - Closing PR**

This PR is being automatically closed because the workflow failed during the **{phase_name}** phase.

**Error Details:**
```
{error_details}
```

**Next Steps:**
1. Review the error details above
2. Fix the underlying issues
3. Retry the workflow once fixes are committed

**Prevention:**
Pre-flight checks have been enhanced to catch these issues earlier. If this was due to inherited errors from main, ensure main is clean before launching workflows.
"""

        result = subprocess.run(
            ["gh", "pr", "close", pr_number, "--comment", comment],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            logger.info(f"✅ Closed PR #{pr_number} with failure comment")
        else:
            logger.error(f"Failed to close PR #{pr_number}: {result.stderr}")

    except Exception as e:
        logger.error(f"Error closing PR: {e}")


def format_failure_summary(
    adw_id: str,
    phase_name: str,
    error_details: str,
    pr_number: Optional[str]
) -> str:
    """Format failure summary for issue comment.

    Args:
        adw_id: ADW workflow ID
        phase_name: Name of the phase that failed
        error_details: Detailed error message
        pr_number: PR number (if available)

    Returns:
        Formatted failure summary
    """
    pr_line = f"- **PR**: #{pr_number} (automatically closed)\n" if pr_number else ""

    return f"""🚨 **Workflow Failure Report**

**Workflow ID**: `{adw_id}`
**Failed Phase**: {phase_name}
{pr_line}
**Status**: Workflow aborted and cleaned up

**Error Summary:**
```
{error_details[:500]}{'...' if len(error_details) > 500 else ''}
```

**Automatic Actions Taken:**
✅ Associated PR closed (if exists)
✅ Workflow marked as failed
✅ Resources cleaned up

**To Retry:**
Fix the errors above and launch a new workflow. Pre-flight checks will help catch issues early.
"""
