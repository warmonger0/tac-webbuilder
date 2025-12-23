"""
Phase Continuation System - Automatically triggers next phase when a phase completes.

This module handles automatic workflow progression by:
1. Detecting phase completion events
2. Determining the next phase based on workflow type
3. Triggering the next phase script in background

Architecture:
- Called by /adw-phase-update endpoint when status="completed"
- Uses workflow_template from ADW state to determine phase sequence
- Launches next phase via subprocess (non-blocking)
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

# Phase sequences for each workflow type
WORKFLOW_PHASE_SEQUENCES: Dict[str, List[str]] = {
    # Complete SDLC workflows (10 phases)
    "adw_sdlc_complete_iso": [
        "Plan",
        "Validate",
        "Build",
        "Lint",
        "Test",
        "Review",
        "Document",
        "Ship",
        "Cleanup",
        "Verify"
    ],
    "adw_sdlc_complete_zte_iso": [
        "Plan",
        "Validate",
        "Build",
        "Lint",
        "Test",
        "Review",
        "Document",
        "Ship",
        "Cleanup",
        "Verify"
    ],

    # Legacy SDLC workflows (missing Validate, Lint, Cleanup, Verify)
    "adw_sdlc_iso": [
        "Plan",
        "Build",
        "Test",
        "Review",
        "Document",
        "Ship"
    ],
    "adw_sdlc_zte_iso": [
        "Plan",
        "Build",
        "Test",
        "Review",
        "Document",
        "Ship"
    ],

    # Partial workflows
    "adw_plan_build_iso": [
        "Plan",
        "Build"
    ],
    "adw_plan_build_test_iso": [
        "Plan",
        "Build",
        "Test"
    ],
    "adw_plan_build_test_review_iso": [
        "Plan",
        "Build",
        "Test",
        "Review"
    ],
    "adw_plan_build_document_iso": [
        "Plan",
        "Build",
        "Document"
    ],
    "adw_plan_build_review_iso": [
        "Plan",
        "Build",
        "Review"
    ],

    # From-build workflows (start from Build phase)
    "adw_sdlc_from_build_iso": [
        "Build",
        "Lint",
        "Test",
        "Review",
        "Document",
        "Ship",
        "Cleanup",
        "Verify"
    ],

    # Lightweight workflow
    "adw_lightweight_iso": [
        "Plan",
        "Build",
        "Test"
    ],
}

# Map phase names to script names
PHASE_TO_SCRIPT: Dict[str, str] = {
    "Plan": "adw_plan_iso.py",
    "Validate": "adw_validate_iso.py",
    "Build": "adw_build_iso.py",
    "Lint": "adw_lint_iso.py",
    "Test": "adw_test_iso.py",
    "Review": "adw_review_iso.py",
    "Document": "adw_document_iso.py",
    "Ship": "adw_ship_iso.py",
    "Cleanup": "adw_cleanup_iso.py",  # Special: handled in orchestrator (pure Python)
    "Verify": "adw_verify_iso.py",
}


def get_next_phase(workflow_template: str, current_phase: str) -> Optional[str]:
    """
    Get the next phase in the sequence for a given workflow.

    Args:
        workflow_template: Workflow type (e.g., "adw_sdlc_complete_iso")
        current_phase: Current phase name (e.g., "Build")

    Returns:
        Next phase name or None if current phase is last or workflow unknown
    """
    phase_sequence = WORKFLOW_PHASE_SEQUENCES.get(workflow_template)

    if not phase_sequence:
        logger.warning(f"Unknown workflow template: {workflow_template}")
        return None

    try:
        current_index = phase_sequence.index(current_phase)
        if current_index < len(phase_sequence) - 1:
            return phase_sequence[current_index + 1]
        else:
            logger.info(f"Phase {current_phase} is the last phase in {workflow_template}")
            return None
    except ValueError:
        logger.error(f"Phase {current_phase} not found in {workflow_template} sequence")
        return None


def trigger_next_phase(
    adw_id: str,
    issue_number: str,
    workflow_template: str,
    current_phase: str,
    workflow_flags: Optional[Dict[str, bool]] = None
) -> bool:
    """
    Trigger the next phase in the workflow sequence.

    Args:
        adw_id: ADW workflow identifier
        issue_number: GitHub issue number
        workflow_template: Workflow type (e.g., "adw_sdlc_complete_iso")
        current_phase: Current phase that just completed
        workflow_flags: Optional flags (skip_e2e, skip_resolution, no_external)

    Returns:
        True if next phase triggered successfully, False otherwise
    """
    next_phase = get_next_phase(workflow_template, current_phase)

    if not next_phase:
        logger.info(f"No next phase after {current_phase} for workflow {workflow_template}")
        return False

    # Special case: Cleanup phase runs inline in orchestrator (not a separate script)
    if next_phase == "Cleanup":
        logger.info("Cleanup phase should be handled by orchestrator, skipping auto-trigger")
        return False

    script_name = PHASE_TO_SCRIPT.get(next_phase)
    if not script_name:
        logger.error(f"No script mapping found for phase: {next_phase}")
        return False

    # Get path to ADW scripts directory
    # From app/server/core/ -> ../../adws/
    server_dir = Path(__file__).parent.parent
    project_root = server_dir.parent.parent
    adws_dir = project_root / "adws"
    script_path = adws_dir / script_name

    if not script_path.exists():
        logger.error(f"Phase script not found: {script_path}")
        return False

    # Build command
    cmd = ["uv", "run", str(script_path), issue_number, adw_id]

    # Add workflow flags if provided
    if workflow_flags:
        if workflow_flags.get("skip_e2e"):
            cmd.append("--skip-e2e")
        if workflow_flags.get("skip_resolution"):
            cmd.append("--skip-resolution")
        if workflow_flags.get("no_external"):
            cmd.append("--no-external")

    # Launch next phase in background
    try:
        logger.info(f"🚀 Triggering next phase: {next_phase} for ADW {adw_id}")
        logger.info(f"   Command: {' '.join(cmd)}")

        # Launch in background (non-blocking)
        # Use Popen with detached process to ensure it continues after API response
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,  # Detach from parent process
            cwd=str(adws_dir)
        )

        logger.info(f"✅ Next phase {next_phase} triggered successfully (PID: {process.pid})")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to trigger next phase {next_phase}: {e}", exc_info=True)
        return False


def should_continue_workflow(status: str, current_phase: str) -> bool:
    """
    Determine if workflow should automatically continue to next phase.

    Args:
        status: Phase status (running, completed, failed)
        current_phase: Current phase name

    Returns:
        True if workflow should continue, False otherwise
    """
    # Only continue on successful completion
    if status != "completed":
        return False

    # Don't auto-continue after final phases (handled by orchestrator)
    terminal_phases = ["Ship", "Verify", "Cleanup"]
    if current_phase in terminal_phases:
        return False

    return True
