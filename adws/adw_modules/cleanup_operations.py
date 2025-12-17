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
import glob
import shutil
import json
import logging
from typing import Dict, Any, Optional, List

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


def cleanup_stale_workflow(
    issue_number: int,
    dry_run: bool = False,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Clean up ALL stale workflow state for a given issue number.

    This performs a complete cleanup to enable a fresh start:
    1. Finds all agent directories for this issue
    2. Removes their worktrees
    3. Removes the agent directories
    4. Clears database phase_queue entries

    Use this when you want to retry a workflow from scratch, discarding
    all previous state. Use --clean-start flag in workflows to trigger this.

    Args:
        issue_number: GitHub issue number to clean up
        dry_run: If True, don't actually delete anything (just report)
        logger: Optional logger instance

    Returns:
        Dictionary with cleanup results:
        {
            "success": bool,
            "agent_dirs_found": int,
            "agent_dirs_removed": int,
            "worktrees_removed": int,
            "db_entries_removed": int,
            "errors": List[str],
            "summary": str
        }
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    result = {
        "success": True,
        "agent_dirs_found": 0,
        "agent_dirs_removed": 0,
        "worktrees_removed": 0,
        "db_entries_removed": 0,
        "errors": [],
        "summary": ""
    }

    issue_number_str = str(issue_number)

    try:
        # Step 1: Find all agent directories for this issue
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        agents_dir = os.path.join(project_root, "agents")

        if not os.path.exists(agents_dir):
            result["summary"] = "No agents directory found"
            logger.info("No agents directory found")
            return result

        # Find agent directories that match this issue number
        agent_dirs_to_remove: List[tuple[str, str]] = []  # (adw_id, agent_dir_path)

        for adw_id in os.listdir(agents_dir):
            agent_dir = os.path.join(agents_dir, adw_id)

            # Skip if not a directory or archived
            if not os.path.isdir(agent_dir) or adw_id.startswith("_"):
                continue

            # Check if this agent directory is for our issue
            state_file = os.path.join(agent_dir, "adw_state.json")
            if os.path.exists(state_file):
                try:
                    with open(state_file, 'r') as f:
                        state_data = json.load(f)
                        if state_data.get("issue_number") == issue_number_str or \
                           state_data.get("issue_number") == issue_number:
                            agent_dirs_to_remove.append((adw_id, agent_dir))
                            logger.info(f"Found agent directory for issue #{issue_number}: {adw_id}")
                except Exception as e:
                    logger.warning(f"Could not read state file {state_file}: {e}")

        result["agent_dirs_found"] = len(agent_dirs_to_remove)

        if not agent_dirs_to_remove:
            result["summary"] = f"No agent directories found for issue #{issue_number}"
            logger.info(result["summary"])
            return result

        logger.info(f"Found {len(agent_dirs_to_remove)} agent directories to clean up")

        # Step 2: For each agent directory, remove worktree and directory
        for adw_id, agent_dir in agent_dirs_to_remove:
            try:
                # Remove worktree first (if it exists)
                if not dry_run:
                    success, error = remove_worktree(adw_id, logger)
                    if success:
                        result["worktrees_removed"] += 1
                        logger.info(f"Removed worktree for {adw_id}")

                        # Release ports
                        release_ports_for_adw(adw_id, logger)
                    else:
                        if error and "not found" not in error.lower():
                            logger.warning(f"Failed to remove worktree for {adw_id}: {error}")
                        else:
                            logger.info(f"No worktree found for {adw_id}")
                else:
                    logger.info(f"[DRY RUN] Would remove worktree for {adw_id}")
                    result["worktrees_removed"] += 1

                # Remove agent directory
                if not dry_run:
                    shutil.rmtree(agent_dir)
                    result["agent_dirs_removed"] += 1
                    logger.info(f"Removed agent directory: {agent_dir}")
                else:
                    logger.info(f"[DRY RUN] Would remove agent directory: {agent_dir}")
                    result["agent_dirs_removed"] += 1

            except Exception as e:
                error_msg = f"Error cleaning up {adw_id}: {e}"
                logger.error(error_msg)
                result["errors"].append(error_msg)
                result["success"] = False

        # Step 3: Clear database phase_queue entries
        try:
            # Import here to avoid circular dependencies
            import sys
            sys.path.insert(0, os.path.join(project_root, "app", "server"))
            from repositories.phase_queue_repository import PhaseQueueRepository

            repo = PhaseQueueRepository()

            # Get all queue items for this feature_id
            queue_items = repo.get_all_by_feature_id(issue_number)

            if queue_items:
                logger.info(f"Found {len(queue_items)} phase_queue entries to delete")

                if not dry_run:
                    for item in queue_items:
                        try:
                            repo.delete(str(item.queue_id))
                            result["db_entries_removed"] += 1
                        except Exception as e:
                            error_msg = f"Failed to delete queue_id {item.queue_id}: {e}"
                            logger.error(error_msg)
                            result["errors"].append(error_msg)
                    logger.info(f"Deleted {result['db_entries_removed']} phase_queue entries")
                else:
                    logger.info(f"[DRY RUN] Would delete {len(queue_items)} phase_queue entries")
                    result["db_entries_removed"] = len(queue_items)
            else:
                logger.info(f"No phase_queue entries found for issue #{issue_number}")

        except Exception as e:
            error_msg = f"Error cleaning up database entries: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
            result["success"] = False

        # Step 4: Build summary
        summary_parts = []
        if result["agent_dirs_removed"] > 0:
            summary_parts.append(f"Removed {result['agent_dirs_removed']} agent directories")
        if result["worktrees_removed"] > 0:
            summary_parts.append(f"Removed {result['worktrees_removed']} worktrees")
        if result["db_entries_removed"] > 0:
            summary_parts.append(f"Deleted {result['db_entries_removed']} database entries")
        if result["errors"]:
            summary_parts.append(f"{len(result['errors'])} errors")

        result["summary"] = ", ".join(summary_parts) if summary_parts else "No cleanup needed"

        if dry_run:
            result["summary"] = "[DRY RUN] " + result["summary"]

    except Exception as e:
        logger.error(f"Unexpected error during stale workflow cleanup: {e}")
        result["success"] = False
        result["errors"].append(str(e))
        result["summary"] = f"Cleanup failed: {e}"

    return result
