"""
Pre-flight checks for ADW workflows to prevent duplicate/unnecessary work.

This module provides comprehensive checks before starting workflows to:
- Prevent work on already-closed issues
- Detect active/concurrent workflows
- Enforce cooldown periods between retries
- Validate issue state and linked PRs
"""

import logging
import subprocess
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class PreflightResult:
    """Result of pre-flight checks."""
    should_proceed: bool
    reason: str
    details: Dict[str, Any]


def run_gh_command(cmd: List[str]) -> Dict[str, Any]:
    """Run gh CLI command and return JSON result."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
        return {}
    except Exception as e:
        return {"error": str(e)}


def check_issue_status(issue_number: int, logger: logging.Logger) -> PreflightResult:
    """
    Check if issue is already closed or has merged PRs.

    Args:
        issue_number: GitHub issue number
        logger: Logger instance

    Returns:
        PreflightResult indicating if workflow should proceed
    """
    logger.info(f"Running pre-flight check for issue #{issue_number}")

    # Get issue details
    issue_data = run_gh_command([
        "gh", "issue", "view", str(issue_number),
        "--json", "state,title,closedAt,url"
    ])

    if "error" in issue_data:
        logger.warning(f"Failed to get issue status: {issue_data['error']}")
        return PreflightResult(
            should_proceed=True,
            reason="Could not verify issue status, proceeding with caution",
            details={"warning": issue_data["error"]}
        )

    # Check if issue is closed
    if issue_data.get("state") == "CLOSED":
        logger.warning(f"Issue #{issue_number} is already CLOSED")

        # Check for linked PRs
        prs_data = run_gh_command([
            "gh", "pr", "list",
            "--search", f"{issue_number} in:title",
            "--state", "all",
            "--json", "number,state,mergedAt,url"
        ])

        if isinstance(prs_data, list):
            merged_prs = [pr for pr in prs_data if pr.get("state") == "MERGED"]

            if merged_prs:
                merged_pr = merged_prs[0]
                return PreflightResult(
                    should_proceed=False,
                    reason=f"Issue #{issue_number} already resolved by PR #{merged_pr['number']}",
                    details={
                        "issue_state": "closed",
                        "merged_pr": merged_pr["number"],
                        "merged_at": merged_pr.get("mergedAt"),
                        "pr_url": merged_pr["url"]
                    }
                )

        return PreflightResult(
            should_proceed=False,
            reason=f"Issue #{issue_number} is closed but no merged PR found",
            details={
                "issue_state": "closed",
                "closed_at": issue_data.get("closedAt"),
                "recommendation": "Verify if work is actually complete before retrying"
            }
        )

    # Check for open PRs
    prs_data = run_gh_command([
        "gh", "pr", "list",
        "--search", f"{issue_number} in:title",
        "--state", "open",
        "--json", "number,url,createdAt"
    ])

    if isinstance(prs_data, list) and len(prs_data) > 0:
        open_pr = prs_data[0]
        return PreflightResult(
            should_proceed=False,
            reason=f"Issue #{issue_number} already has an open PR #{open_pr['number']}",
            details={
                "issue_state": "open",
                "open_pr": open_pr["number"],
                "pr_url": open_pr["url"],
                "created_at": open_pr.get("createdAt"),
                "recommendation": "Check if existing PR needs work or should be closed first"
            }
        )

    # All checks passed
    return PreflightResult(
        should_proceed=True,
        reason=f"Issue #{issue_number} is open with no existing PRs",
        details={"issue_state": "open"}
    )


def check_cooldown_period(
    issue_number: int,
    cooldown_minutes: int = 60,
    logger: Optional[logging.Logger] = None
) -> PreflightResult:
    """
    Check if sufficient time has passed since last workflow attempt.

    Args:
        issue_number: GitHub issue number
        cooldown_minutes: Minimum minutes between attempts (default: 60)
        logger: Logger instance

    Returns:
        PreflightResult indicating if cooldown period has elapsed
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    logger.info(f"Checking cooldown period for issue #{issue_number}")

    # Get recent comments
    comments_data = run_gh_command([
        "gh", "api",
        f"repos/{{owner}}/{{repo}}/issues/{issue_number}/comments",
        "--jq", ".[(-15):]"  # Last 15 comments
    ])

    if not isinstance(comments_data, list):
        logger.warning("Could not retrieve issue comments, skipping cooldown check")
        return PreflightResult(
            should_proceed=True,
            reason="Could not verify cooldown period",
            details={"warning": "Comment retrieval failed"}
        )

    # Find most recent ops comment (workflow start indicator)
    last_ops_time = None
    for comment in reversed(comments_data):
        body = comment.get("body", "")
        if "_ops:" in body or "[ADW-AGENTS]" in body:
            created_at = comment.get("created_at")
            if created_at:
                last_ops_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                break

    if last_ops_time:
        time_since_last = datetime.now(last_ops_time.tzinfo) - last_ops_time
        minutes_elapsed = time_since_last.total_seconds() / 60

        if minutes_elapsed < cooldown_minutes:
            return PreflightResult(
                should_proceed=False,
                reason=f"Cooldown active: Last attempt was {minutes_elapsed:.1f} minutes ago",
                details={
                    "last_attempt": last_ops_time.isoformat(),
                    "minutes_elapsed": round(minutes_elapsed, 1),
                    "cooldown_minutes": cooldown_minutes,
                    "minutes_remaining": round(cooldown_minutes - minutes_elapsed, 1)
                }
            )

    return PreflightResult(
        should_proceed=True,
        reason="Cooldown period elapsed or no recent attempts found",
        details={"cooldown_minutes": cooldown_minutes}
    )


def check_active_workflows(
    issue_number: int,
    logger: Optional[logging.Logger] = None
) -> PreflightResult:
    """
    Check if there are active workflows for this issue in the database.

    Args:
        issue_number: GitHub issue number
        logger: Logger instance

    Returns:
        PreflightResult indicating if active workflows exist
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    logger.info(f"Checking for active workflows for issue #{issue_number}")

    try:
        # Import here to avoid circular dependencies
        import os
        import sys

        # Add app/server to path
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.path.insert(0, os.path.join(project_root, "app", "server"))

        from repositories.phase_queue_repository import PhaseQueueRepository

        repo = PhaseQueueRepository()
        workflows = repo.get_all_by_feature_id(issue_number)

        # =============================================================================
        # SCHEMA CONSTRAINT: phase_queue.status
        # =============================================================================
        # ALLOWED: 'queued', 'ready', 'running', 'completed', 'blocked', 'failed'
        # FORBIDDEN: 'pending', 'planned', 'building', 'linting', 'testing', etc.
        # =============================================================================
        # Filter for active statuses
        active_statuses = ["queued", "ready", "running"]
        active_workflows = [w for w in workflows if w.status in active_statuses]

        if active_workflows:
            active = active_workflows[0]
            return PreflightResult(
                should_proceed=False,
                reason=f"Active workflow already running for issue #{issue_number}",
                details={
                    "adw_id": active.adw_id,
                    "phase": active.phase_name,
                    "status": active.status,
                    "recommendation": "Wait for current workflow to complete or use --clean-start to override"
                }
            )

        return PreflightResult(
            should_proceed=True,
            reason="No active workflows found in database",
            details={}
        )

    except Exception as e:
        logger.warning(f"Could not check database for active workflows: {e}")
        return PreflightResult(
            should_proceed=True,
            reason="Could not verify active workflows (database unavailable)",
            details={"warning": str(e)}
        )


def run_all_preflight_checks(
    issue_number: int,
    skip_cooldown: bool = False,
    logger: Optional[logging.Logger] = None
) -> PreflightResult:
    """
    Run all pre-flight checks before starting workflow.

    Args:
        issue_number: GitHub issue number
        skip_cooldown: If True, skip cooldown check (for --clean-start)
        logger: Logger instance

    Returns:
        PreflightResult with combined result of all checks
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    logger.info(f"{'='*60}")
    logger.info(f"RUNNING PRE-FLIGHT CHECKS FOR ISSUE #{issue_number}")
    logger.info(f"{'='*60}")

    all_details = {}

    # Check 1: Issue status
    result = check_issue_status(issue_number, logger)
    all_details["issue_status"] = result.details

    if not result.should_proceed:
        logger.warning(f"❌ Pre-flight failed: {result.reason}")
        return result

    logger.info(f"✅ Issue status: {result.reason}")

    # Check 2: Active workflows (database)
    result = check_active_workflows(issue_number, logger)
    all_details["active_workflows"] = result.details

    if not result.should_proceed:
        logger.warning(f"❌ Pre-flight failed: {result.reason}")
        return result

    logger.info(f"✅ Active workflows: {result.reason}")

    # Check 3: Cooldown period (skip if requested)
    if not skip_cooldown:
        result = check_cooldown_period(issue_number, cooldown_minutes=60, logger=logger)
        all_details["cooldown"] = result.details

        if not result.should_proceed:
            logger.warning(f"❌ Pre-flight failed: {result.reason}")
            return result

        logger.info(f"✅ Cooldown: {result.reason}")
    else:
        logger.info("⏭️  Cooldown check skipped (--clean-start mode)")
        all_details["cooldown"] = {"skipped": True}

    # All checks passed
    logger.info(f"{'='*60}")
    logger.info(f"✅ ALL PRE-FLIGHT CHECKS PASSED")
    logger.info(f"{'='*60}")

    return PreflightResult(
        should_proceed=True,
        reason="All pre-flight checks passed",
        details=all_details
    )
