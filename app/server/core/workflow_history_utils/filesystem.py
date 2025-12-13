"""
Filesystem operations for workflow history tracking.

This module handles scanning and parsing of ADW workflow state files
from the agents directory.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def _validate_issue_number(adw_id: str, issue_number_raw) -> int | None:
    """Validate and convert issue number. Returns None if invalid."""
    if issue_number_raw is None:
        return None

    try:
        issue_number = int(issue_number_raw)
        if issue_number <= 0:
            logger.warning(
                f"[SCAN] Skipping workflow {adw_id}: issue_number must be positive, got {issue_number_raw}"
            )
            return None

        # Skip obviously invalid issue numbers
        invalid_issues = {6, 13, 999}
        if issue_number in invalid_issues:
            logger.warning(
                f"[SCAN] Skipping workflow {adw_id}: issue_number {issue_number} is in invalid list"
            )
            return None

        return issue_number
    except (ValueError, TypeError):
        logger.warning(
            f"[SCAN] Skipping workflow {adw_id}: invalid issue_number '{issue_number_raw}' "
            f"(expected integer, got {type(issue_number_raw).__name__})"
        )
        return None


def _extract_workflow_metadata(adw_id: str, adw_dir: Path, state_data: dict) -> dict:
    """Extract workflow metadata from state data."""
    return {
        "adw_id": adw_id,
        "issue_number": None,  # Will be set by caller
        "nl_input": state_data.get("nl_input"),
        "github_url": state_data.get("github_url"),
        "workflow_template": state_data.get("workflow_template", state_data.get("workflow")),
        "model_used": state_data.get("model_used", state_data.get("model")),
        "status": state_data.get("status") or "pending",
        "start_time": state_data.get("start_time"),
        "end_time": state_data.get("end_time"),
        "current_phase": state_data.get("current_phase"),
        "worktree_path": str(adw_dir),
        "backend_port": state_data.get("backend_port"),
        "frontend_port": state_data.get("frontend_port"),
        "branch_name": state_data.get("branch_name"),
        "plan_file": state_data.get("plan_file"),
        "issue_class": state_data.get("issue_class"),
    }


def _infer_status_from_filesystem(workflow: dict, adw_dir: Path, state_data: dict, state_file: Path) -> None:
    """Infer workflow status from filesystem state (modifies workflow dict in place)."""
    if workflow["status"] in ("completed", "failed"):
        return

    # Check for error file first
    error_file = adw_dir / "error.log"
    if error_file.exists():
        workflow["status"] = "failed"
        if not workflow.get("end_time"):
            error_mtime = error_file.stat().st_mtime
            workflow["end_time"] = datetime.fromtimestamp(error_mtime).isoformat()
        logger.debug(f"[SCAN] Workflow {workflow['adw_id']} failed (error.log exists)")
        return

    # Check completion based on phases
    completed_phases = [
        d for d in adw_dir.iterdir()
        if d.is_dir() and d.name.startswith("adw_")
    ]

    if len(completed_phases) >= 3:
        # Check for completion indicators
        plan_file = state_data.get("plan_file")
        branch_name = state_data.get("branch_name")
        if plan_file and branch_name:
            workflow["status"] = "completed"
            if not workflow.get("end_time"):
                state_mtime = state_file.stat().st_mtime
                workflow["end_time"] = datetime.fromtimestamp(state_mtime).isoformat()
            logger.debug(f"[SCAN] Workflow {workflow['adw_id']} completed (3+ phases, has plan & branch)")
        else:
            workflow["status"] = "running"
            logger.debug(f"[SCAN] Workflow {workflow['adw_id']} still running (phases exist but incomplete)")
    elif len(completed_phases) == 1 and state_data.get("plan_file") is None:
        # Only planning phase, no plan file - likely failed early
        workflow["status"] = "failed"
        if not workflow.get("end_time"):
            state_mtime = state_file.stat().st_mtime
            workflow["end_time"] = datetime.fromtimestamp(state_mtime).isoformat()
        logger.debug(f"[SCAN] Workflow {workflow['adw_id']} failed (only 1 phase, no plan file)")
    else:
        # In progress
        workflow["status"] = "running"
        logger.debug(f"[SCAN] Workflow {workflow['adw_id']} running ({len(completed_phases)} phases)")


def scan_agents_directory() -> list[dict]:
    """
    Scan the agents directory for workflow state files and extract metadata.

    Returns:
        List[Dict]: List of workflow metadata dictionaries
    """
    # Locate agents directory
    project_root = Path(__file__).parent.parent.parent.parent.parent
    agents_dir = project_root / "agents"

    if not agents_dir.exists():
        logger.warning(f"[SCAN] Agents directory not found: {agents_dir}")
        return []

    workflows = []

    # Iterate through subdirectories in agents/
    for adw_dir in agents_dir.iterdir():
        if not adw_dir.is_dir():
            continue

        adw_id = adw_dir.name
        state_file = adw_dir / "adw_state.json"

        if not state_file.exists():
            logger.debug(f"[SCAN] No adw_state.json found for {adw_id}")
            continue

        try:
            with open(state_file) as f:
                state_data = json.load(f)

            # Validate issue number
            issue_number = _validate_issue_number(adw_id, state_data.get("issue_number"))
            if state_data.get("issue_number") is not None and issue_number is None:
                # Validation failed, skip this workflow
                continue

            # Extract metadata
            workflow = _extract_workflow_metadata(adw_id, adw_dir, state_data)
            workflow["issue_number"] = issue_number

            # Infer status from filesystem
            _infer_status_from_filesystem(workflow, adw_dir, state_data, state_file)

            workflows.append(workflow)
            logger.debug(f"[SCAN] Found workflow {adw_id}: {workflow['status']}")

        except Exception as e:
            logger.error(f"[SCAN] Error parsing {state_file}: {e}")
            continue

    logger.debug(f"[SCAN] Scanned agents directory, found {len(workflows)} workflows")
    return workflows
