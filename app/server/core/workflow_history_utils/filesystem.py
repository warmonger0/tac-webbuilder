"""
Filesystem operations for workflow history tracking.

This module handles scanning and parsing of ADW workflow state files
from the agents directory.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


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

            # Validate issue_number type before processing
            issue_number_raw = state_data.get("issue_number")
            issue_number = None
            if issue_number_raw is not None:
                try:
                    # Attempt to convert to int, skip record if invalid
                    issue_number = int(issue_number_raw)
                    if issue_number <= 0:
                        logger.warning(
                            f"[SCAN] Skipping workflow {adw_id}: issue_number must be positive, got {issue_number_raw}"
                        )
                        continue
                    # Skip obviously invalid issue numbers (like 999 which is a placeholder)
                    # or issues that don't exist (6, 13, etc.)
                    # These are likely test data or failed workflow attempts
                    invalid_issues = {6, 13, 999}
                    if issue_number in invalid_issues:
                        logger.warning(
                            f"[SCAN] Skipping workflow {adw_id}: issue_number {issue_number} is in invalid list"
                        )
                        continue
                except (ValueError, TypeError):
                    logger.warning(
                        f"[SCAN] Skipping workflow {adw_id}: invalid issue_number '{issue_number_raw}' "
                        f"(expected integer, got {type(issue_number_raw).__name__})"
                    )
                    continue

            # Extract metadata from state file
            workflow = {
                "adw_id": adw_id,
                "issue_number": issue_number,
                "nl_input": state_data.get("nl_input"),
                "github_url": state_data.get("github_url"),
                "workflow_template": state_data.get("workflow_template", state_data.get("workflow")),
                "model_used": state_data.get("model_used", state_data.get("model")),
                "status": state_data.get("status", "unknown"),
                "start_time": state_data.get("start_time"),
                "current_phase": state_data.get("current_phase"),
                "worktree_path": str(adw_dir),
                "backend_port": state_data.get("backend_port"),
                "frontend_port": state_data.get("frontend_port"),
            }

            # Infer status if not explicitly set or if still showing as "running"
            # This makes status detection more dynamic and reality-based
            if workflow["status"] in ("unknown", "running"):
                # Check if there's an error file first
                error_file = adw_dir / "error.log"
                if error_file.exists():
                    workflow["status"] = "failed"
                    logger.debug(f"[SCAN] Workflow {adw_id} failed (error.log exists)")
                else:
                    # Check for completion indicators based on ADW lifecycle
                    completed_phases = [
                        d for d in adw_dir.iterdir()
                        if d.is_dir() and d.name.startswith("adw_")
                    ]

                    # Check if workflow has completed all expected phases
                    # Most workflows complete with at least plan + build + test (3+ phases)
                    if len(completed_phases) >= 3:
                        # Additional check: if there's a plan file and branch, likely completed
                        plan_file = state_data.get("plan_file")
                        branch_name = state_data.get("branch_name")
                        if plan_file and branch_name:
                            workflow["status"] = "completed"
                            logger.debug(f"[SCAN] Workflow {adw_id} completed (3+ phases, has plan & branch)")
                        else:
                            # Has phases but missing key artifacts - might be in progress
                            workflow["status"] = "running"
                            logger.debug(f"[SCAN] Workflow {adw_id} still running (phases exist but incomplete)")
                    elif len(completed_phases) == 1 and state_data.get("plan_file") is None:
                        # Only has planning phase and no plan file created - likely failed early
                        workflow["status"] = "failed"
                        logger.debug(f"[SCAN] Workflow {adw_id} failed (only 1 phase, no plan file)")
                    else:
                        # In progress or unknown state
                        workflow["status"] = "running"
                        logger.debug(f"[SCAN] Workflow {adw_id} running ({len(completed_phases)} phases)")

            workflows.append(workflow)
            logger.debug(f"[SCAN] Found workflow {adw_id}: {workflow['status']}")

        except Exception as e:
            logger.error(f"[SCAN] Error parsing {state_file}: {e}")
            continue

    logger.debug(f"[SCAN] Scanned agents directory, found {len(workflows)} workflows")
    return workflows
