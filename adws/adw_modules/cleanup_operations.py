"""
Standalone cleanup operations that can be called directly without ADW workflow overhead.

This module provides pure Python functions for cleanup that don't require:
- ADW state loading
- GitHub comment posting
- Workflow tracking

Use these functions when you want to perform cleanup operations programmatically
without the full ADW workflow machinery.
"""

import os
import logging
from typing import Dict, Any, Optional

from .doc_cleanup import cleanup_adw_documentation
from .worktree_ops import remove_worktree, release_ports_for_adw
from .state import ADWState


def cleanup_shipped_issue(
    issue_number: str,
    adw_id: str,
    skip_worktree: bool = False,
    dry_run: bool = False,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Perform complete cleanup for a shipped issue.

    This is a standalone function that can be called directly without
    the ADW workflow overhead. It performs:
    1. Documentation organization
    2. Worktree removal (optional)
    3. State updates

    Args:
        issue_number: GitHub issue number
        adw_id: ADW workflow ID
        skip_worktree: If True, don't remove worktree
        dry_run: If True, don't actually move files or remove worktree
        logger: Optional logger instance

    Returns:
        Dictionary with cleanup results:
        {
            "success": bool,
            "docs_moved": int,
            "worktree_removed": bool,
            "errors": List[str],
            "summary": str
        }
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    result = {
        "success": True,
        "docs_moved": 0,
        "worktree_removed": False,
        "errors": [],
        "summary": ""
    }

    # Load state
    state = ADWState.load(adw_id, logger)
    if not state:
        result["success"] = False
        result["errors"].append(f"No state found for ADW ID: {adw_id}")
        return result

    # Update issue number from state if available
    issue_number = state.get("issue_number", issue_number)

    try:
        # 1. Cleanup documentation
        logger.info("Starting documentation cleanup...")
        doc_result = cleanup_adw_documentation(
            issue_number=issue_number,
            adw_id=adw_id,
            state=state,
            logger=logger,
            dry_run=dry_run
        )

        result["docs_moved"] = doc_result.get("files_moved", 0)
        result["errors"].extend(doc_result.get("errors", []))

        if not doc_result.get("success", False):
            result["success"] = False

        # 2. Remove worktree
        if not skip_worktree:
            logger.info("Removing worktree...")
            worktree_path = state.get("worktree_path")

            if worktree_path:
                if not dry_run:
                    success, error = remove_worktree(adw_id, logger)
                    if success:
                        result["worktree_removed"] = True
                        logger.info(f"Worktree removed: {worktree_path}")

                        # Release ports back to pool
                        release_ports_for_adw(adw_id, logger)
                    else:
                        result["errors"].append(f"Worktree removal failed: {error}")
                else:
                    logger.info(f"[DRY RUN] Would remove worktree: {worktree_path}")
                    result["worktree_removed"] = True  # In dry-run mode
            else:
                logger.info("No worktree path in state - skipping worktree removal")

        # 3. Save state
        if not dry_run:
            state.save("cleanup_operations")

        # 4. Build summary
        summary_parts = []
        if result["docs_moved"] > 0:
            summary_parts.append(f"Moved {result['docs_moved']} documentation files")
        if result["worktree_removed"]:
            summary_parts.append("Removed worktree and freed resources")
        if result["errors"]:
            summary_parts.append(f"{len(result['errors'])} errors/warnings")

        result["summary"] = ", ".join(summary_parts) if summary_parts else "No cleanup needed"

    except Exception as e:
        logger.error(f"Unexpected error during cleanup: {e}")
        result["success"] = False
        result["errors"].append(str(e))

    return result


def cleanup_documentation_only(
    issue_number: str,
    adw_id: str,
    dry_run: bool = False,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Perform only documentation cleanup, without worktree removal.

    Use this when you want to organize docs but keep the worktree around.

    Args:
        issue_number: GitHub issue number
        adw_id: ADW workflow ID
        dry_run: If True, don't actually move files
        logger: Optional logger instance

    Returns:
        Dictionary with cleanup results
    """
    return cleanup_shipped_issue(
        issue_number=issue_number,
        adw_id=adw_id,
        skip_worktree=True,
        dry_run=dry_run,
        logger=logger
    )


def cleanup_worktree_only(
    adw_id: str,
    dry_run: bool = False,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Remove only the worktree, without organizing documentation.

    Use this for quick cleanup when docs are already organized.

    Args:
        adw_id: ADW workflow ID
        dry_run: If True, don't actually remove worktree
        logger: Optional logger instance

    Returns:
        Dictionary with cleanup results
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    result = {
        "success": True,
        "worktree_removed": False,
        "errors": [],
        "summary": ""
    }

    # Load state
    state = ADWState.load(adw_id, logger)
    if not state:
        result["success"] = False
        result["errors"].append(f"No state found for ADW ID: {adw_id}")
        return result

    try:
        worktree_path = state.get("worktree_path")
        if worktree_path:
            if not dry_run:
                success, error = remove_worktree(adw_id, logger)
                if success:
                    result["worktree_removed"] = True
                    result["summary"] = f"Removed worktree: {worktree_path}"
                    logger.info(result["summary"])

                    # Release ports back to pool
                    release_ports_for_adw(adw_id, logger)
                else:
                    result["success"] = False
                    result["errors"].append(f"Failed to remove worktree: {error}")
                    result["summary"] = "Worktree removal failed"
            else:
                logger.info(f"[DRY RUN] Would remove worktree: {worktree_path}")
                result["worktree_removed"] = True
                result["summary"] = f"[DRY RUN] Would remove: {worktree_path}"
        else:
            result["summary"] = "No worktree to remove"
            logger.info("No worktree path in state")

    except Exception as e:
        logger.error(f"Error removing worktree: {e}")
        result["success"] = False
        result["errors"].append(str(e))
        result["summary"] = "Worktree removal failed"

    return result
