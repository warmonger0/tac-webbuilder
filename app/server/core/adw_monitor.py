"""
ADW Monitor module for real-time workflow status tracking.

This module provides functionality to aggregate and monitor ADW workflow states
by scanning state files, checking process status, and calculating progress metrics.
"""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Cache for monitoring data (5-second TTL)
_monitor_cache: dict[str, Any] = {
    "data": None,
    "timestamp": None,
    "ttl_seconds": 5
}


def get_agents_directory() -> Path:
    """
    Get the path to the agents directory.

    Returns:
        Path: Absolute path to the agents directory
    """
    # Navigate from app/server/core/adw_monitor.py to project root
    project_root = Path(__file__).parent.parent.parent.parent
    return project_root / "agents"


def get_trees_directory() -> Path:
    """
    Get the path to the worktrees directory.

    Returns:
        Path: Absolute path to the trees directory
    """
    project_root = Path(__file__).parent.parent.parent.parent
    return project_root / "trees"


def scan_adw_states() -> list[dict[str, Any]]:
    """
    Scan the agents directory for ADW state files and extract metadata.

    Returns:
        List[Dict]: List of workflow state dictionaries with metadata
    """
    agents_dir = get_agents_directory()

    if not agents_dir.exists():
        logger.warning(f"Agents directory not found: {agents_dir}")
        return []

    states = []

    for adw_dir in agents_dir.iterdir():
        if not adw_dir.is_dir():
            continue

        adw_id = adw_dir.name
        state_file = adw_dir / "adw_state.json"

        if not state_file.exists():
            logger.debug(f"No adw_state.json found for {adw_id}")
            continue

        try:
            with open(state_file, encoding='utf-8') as f:
                state_data = json.load(f)

            # Add adw_id to state data
            state_data["adw_id"] = adw_id
            state_data["state_file_path"] = str(state_file)
            state_data["agent_dir_path"] = str(adw_dir)

            states.append(state_data)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse state file for {adw_id}: {e}")
            continue
        except Exception as e:
            logger.error(f"Error reading state file for {adw_id}: {e}")
            continue

    return states


def is_process_running(adw_id: str) -> bool:
    """
    Check if a workflow process is currently running.

    Args:
        adw_id: The ADW workflow identifier

    Returns:
        bool: True if process is running, False otherwise
    """
    try:
        # Use ps to check for running processes containing the adw_id
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Look for the adw_id in process list
        # Common patterns: python aider.py, uv run, etc.
        for line in result.stdout.splitlines():
            if adw_id in line and "aider" in line.lower():
                return True

        return False

    except subprocess.TimeoutExpired:
        logger.warning(f"Process check timed out for {adw_id}")
        return False
    except Exception as e:
        logger.error(f"Error checking process for {adw_id}: {e}")
        return False


def worktree_exists(adw_id: str) -> bool:
    """
    Check if a worktree directory exists for the given ADW ID.

    Args:
        adw_id: The ADW workflow identifier

    Returns:
        bool: True if worktree exists, False otherwise
    """
    trees_dir = get_trees_directory()
    worktree_path = trees_dir / adw_id

    return worktree_path.exists() and worktree_path.is_dir()


def get_last_activity_timestamp(adw_id: str) -> datetime | None:
    """
    Get the last activity timestamp for a workflow.

    Checks the modification time of the state file and any recent log files.

    Args:
        adw_id: The ADW workflow identifier

    Returns:
        datetime | None: Last activity timestamp or None if not available
    """
    agents_dir = get_agents_directory()
    adw_dir = agents_dir / adw_id

    if not adw_dir.exists():
        return None

    # Check state file modification time
    state_file = adw_dir / "adw_state.json"
    if not state_file.exists():
        return None

    try:
        mtime = state_file.stat().st_mtime
        return datetime.fromtimestamp(mtime)
    except Exception as e:
        logger.error(f"Error getting last activity for {adw_id}: {e}")
        return None


def determine_status(adw_id: str, state: dict[str, Any]) -> str:
    """
    Determine the current status of a workflow.

    Status logic:
    - running: Process is actively running
    - completed: Workflow marked as completed in state
    - failed: Workflow marked as failed in state
    - paused: Worktree exists, no process, no activity >10 minutes
    - queued: State exists but workflow not started

    Args:
        adw_id: The ADW workflow identifier
        state: The workflow state dictionary

    Returns:
        str: One of: running, completed, failed, paused, queued
    """
    # Check explicit status from state file first
    state_status = state.get("status", "").lower()

    if state_status == "completed":
        return "completed"

    if state_status == "failed":
        return "failed"

    # Check if process is running
    if is_process_running(adw_id):
        return "running"

    # Check if worktree exists but no process
    if worktree_exists(adw_id):
        # Check last activity
        last_activity = get_last_activity_timestamp(adw_id)
        if last_activity:
            time_since_activity = (datetime.now() - last_activity).total_seconds()
            # If no activity for more than 10 minutes, consider paused
            if time_since_activity > 600:
                return "paused"

        # If we have a worktree but no process and recent activity, likely paused
        return "paused"

    # Default to queued
    return "queued"


def calculate_phase_progress(adw_id: str, state: dict[str, Any]) -> tuple[str | None, float]:
    """
    Calculate the current phase and overall progress percentage.

    Progress is based on completed phase directories in the agents/{adw_id}/ folder.
    Standard SDLC phases: plan, build, lint, test, review, doc, ship, cleanup

    Args:
        adw_id: The ADW workflow identifier
        state: The workflow state dictionary

    Returns:
        tuple: (current_phase, progress_percentage)
    """
    # Standard SDLC phases
    phases = ["plan", "build", "lint", "test", "review", "doc", "ship", "cleanup"]
    total_phases = len(phases)

    agents_dir = get_agents_directory()
    adw_dir = agents_dir / adw_id

    if not adw_dir.exists():
        return None, 0.0

    # Get list of subdirectories in the agent directory
    try:
        subdirs = [d.name.lower() for d in adw_dir.iterdir() if d.is_dir()]
    except Exception as e:
        logger.error(f"Error reading agent directory for {adw_id}: {e}")
        return None, 0.0

    # Count completed phases (directories that match phase names)
    completed_phases = []
    for phase in phases:
        # Check if any subdirectory contains this phase name
        if any(phase in subdir for subdir in subdirs):
            completed_phases.append(phase)

    # Calculate base progress
    base_progress = (len(completed_phases) / total_phases) * 100

    # Get current phase from state
    current_phase = state.get("current_phase")

    # If we have a current phase that's not in completed phases,
    # add partial progress (50% of one phase)
    if current_phase and current_phase not in completed_phases:
        base_progress += (100 / total_phases) * 0.5

    # Cap at 100%
    progress = min(base_progress, 100.0)

    return current_phase, round(progress, 1)


def extract_cost_data(state: dict[str, Any]) -> tuple[float | None, float | None]:
    """
    Extract current and estimated total cost from state data.

    Args:
        state: The workflow state dictionary

    Returns:
        tuple: (current_cost, estimated_total_cost)
    """
    current_cost = state.get("current_cost")
    estimated_cost = state.get("estimated_cost_total") or state.get("estimated_cost")

    # Convert to float if string
    try:
        if current_cost is not None:
            current_cost = float(current_cost)
    except (ValueError, TypeError):
        current_cost = None

    try:
        if estimated_cost is not None:
            estimated_cost = float(estimated_cost)
    except (ValueError, TypeError):
        estimated_cost = None

    return current_cost, estimated_cost


def extract_error_info(adw_id: str, state: dict[str, Any]) -> tuple[int, str | None]:
    """
    Extract error count and last error message.

    Args:
        adw_id: The ADW workflow identifier
        state: The workflow state dictionary

    Returns:
        tuple: (error_count, last_error_message)
    """
    error_count = state.get("error_count", 0)
    last_error = state.get("last_error")

    # Check for error.log file
    agents_dir = get_agents_directory()
    error_file = agents_dir / adw_id / "error.log"

    if error_file.exists() and not last_error:
        try:
            with open(error_file, encoding='utf-8') as f:
                last_error = f.read().strip()
                if last_error:
                    error_count = max(error_count, 1)
        except Exception as e:
            logger.error(f"Error reading error.log for {adw_id}: {e}")

    return error_count, last_error


def build_workflow_status(state: dict[str, Any]) -> dict[str, Any]:
    """
    Build a complete workflow status object from state data.

    Args:
        state: The workflow state dictionary

    Returns:
        dict: Complete workflow status with all fields
    """
    adw_id = state.get("adw_id", "unknown")

    # Determine status
    status = determine_status(adw_id, state)

    # Calculate phase progress
    current_phase, progress = calculate_phase_progress(adw_id, state)

    # Extract costs
    current_cost, estimated_cost = extract_cost_data(state)

    # Extract error info
    error_count, last_error = extract_error_info(adw_id, state)

    # Build workflow status object
    workflow_status = {
        "adw_id": adw_id,
        "issue_number": state.get("issue_number"),
        "issue_class": state.get("issue_class") or state.get("classification") or "",
        "title": state.get("nl_input", "")[:100],  # Truncate to 100 chars
        "status": status,
        "current_phase": current_phase,
        "phase_progress": progress,
        "workflow_template": state.get("workflow_template", state.get("workflow", "")),
        "start_time": state.get("start_time"),
        "end_time": state.get("end_time"),
        "duration_seconds": state.get("duration_seconds"),
        "github_url": state.get("github_url"),
        "worktree_path": state.get("worktree_path"),
        "current_cost": current_cost,
        "estimated_cost_total": estimated_cost,
        "error_count": error_count,
        "last_error": last_error,
        "is_process_active": is_process_running(adw_id),
        "phases_completed": [],  # Could be enhanced to list phase names
        "total_phases": 8,  # Standard SDLC has 8 phases
    }

    return workflow_status


def aggregate_adw_monitor_data() -> dict[str, Any]:
    """
    Aggregate all ADW workflow status data.

    This is the main entry point for the ADW monitor functionality.
    Returns comprehensive status for all workflows.

    Returns:
        dict: Complete monitor response with summary and workflow list
    """
    # Check cache
    if _monitor_cache["data"] and _monitor_cache["timestamp"]:
        elapsed = (datetime.now() - _monitor_cache["timestamp"]).total_seconds()
        if elapsed < _monitor_cache["ttl_seconds"]:
            logger.debug("Returning cached ADW monitor data")
            return _monitor_cache["data"]

    # Scan for ADW states
    states = scan_adw_states()

    # Build workflow status for each state
    workflows = []
    for state in states:
        try:
            workflow_status = build_workflow_status(state)
            workflows.append(workflow_status)
        except Exception as e:
            logger.error(f"Error building status for {state.get('adw_id')}: {e}")
            continue

    # Sort by start time (most recent first)
    workflows.sort(
        key=lambda w: w.get("start_time") or "",
        reverse=True
    )

    # Calculate summary statistics
    summary = {
        "total": len(workflows),
        "running": sum(1 for w in workflows if w["status"] == "running"),
        "completed": sum(1 for w in workflows if w["status"] == "completed"),
        "failed": sum(1 for w in workflows if w["status"] == "failed"),
        "paused": sum(1 for w in workflows if w["status"] == "paused"),
    }

    # Build response
    response = {
        "summary": summary,
        "workflows": workflows,
        "last_updated": datetime.now().isoformat(),
    }

    # Update cache
    _monitor_cache["data"] = response
    _monitor_cache["timestamp"] = datetime.now()

    return response
