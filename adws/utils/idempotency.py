"""
Idempotency helpers for ADW phases.

Provides shared utilities for implementing idempotent phases according to
the pattern defined in docs/adw/idempotency.md.

Usage:
    from utils.idempotency import is_phase_complete, check_and_skip_if_complete

    # In phase main function:
    if check_and_skip_if_complete('plan', issue_number, logger):
        return True

    # ... execute phase logic ...

    # Validate completion:
    if not is_phase_complete('plan', issue_number, logger):
        raise ValueError("Phase incomplete after execution")
"""

from pathlib import Path
from typing import Optional, Dict, Any
import logging
import json
import sys
import os

# Add parent directory to path for imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, parent_dir)

from adws.utils.state_validator import StateValidator
from adws.adw_modules.state import ADWState
from adws.adw_modules.utils import setup_database_imports

# Setup database imports for app.server access
setup_database_imports()


def is_phase_complete(phase: str, issue_number: int, logger: logging.Logger) -> bool:
    """Check if phase is complete with valid outputs.

    Args:
        phase: Phase name (plan, validate, build, lint, test, etc.)
        issue_number: GitHub issue number
        logger: Logger instance

    Returns:
        True if phase outputs exist and are valid, False otherwise
    """
    try:
        logger.debug(f"Checking if {phase} phase is complete for issue {issue_number}")

        # Use StateValidator to check outputs
        validator = StateValidator(phase=phase)
        result = validator.validate_outputs(issue_number)

        if not result.is_valid:
            logger.debug(f"{phase.capitalize()} phase incomplete: {', '.join(result.errors)}")
            return False

        if result.warnings:
            logger.warning(f"{phase.capitalize()} phase warnings: {', '.join(result.warnings)}")

        logger.debug(f"✓ {phase.capitalize()} phase outputs are valid")
        return True

    except Exception as e:
        logger.debug(f"{phase.capitalize()} phase validation failed: {e}")
        return False


def check_and_skip_if_complete(phase: str, issue_number: int, logger: logging.Logger) -> bool:
    """Check if phase is complete and log appropriate message.

    This is the canonical way to implement idempotency in phase main functions.

    Args:
        phase: Phase name
        issue_number: GitHub issue number
        logger: Logger instance

    Returns:
        True if phase should be skipped (already complete), False if should execute
    """
    if is_phase_complete(phase, issue_number, logger):
        logger.info(f"✓ {phase.capitalize()} phase already complete, skipping")
        return True

    logger.info(f"→ {phase.capitalize()} phase not complete, executing")
    return False


def validate_phase_completion(phase: str, issue_number: int, logger: logging.Logger) -> None:
    """Validate that phase completed successfully.

    Raises ValueError if phase is not complete after execution.

    Args:
        phase: Phase name
        issue_number: GitHub issue number
        logger: Logger instance

    Raises:
        ValueError: If phase is not complete
    """
    if not is_phase_complete(phase, issue_number, logger):
        error_msg = f"{phase.capitalize()} phase incomplete after execution"
        logger.error(f"✗ {error_msg}")
        raise ValueError(error_msg)

    logger.info(f"✓ {phase.capitalize()} phase validated as complete")


def get_or_create_state(issue_number: int, adw_id: Optional[str], logger: logging.Logger) -> Dict[str, Any]:
    """Get existing state or create new one.

    Args:
        issue_number: GitHub issue number
        adw_id: ADW identifier (optional)
        logger: Logger instance

    Returns:
        State dictionary
    """
    try:
        if adw_id:
            state = ADWState.load(adw_id, logger)
            if state:
                logger.debug(f"Loaded existing state for ADW {adw_id}")
                return state

        # Try to find state by issue number
        from app.server.repositories.phase_queue_repository import PhaseQueueRepository
        repo = PhaseQueueRepository()
        workflows = repo.get_all_by_feature_id(issue_number)
        workflow = workflows[0] if workflows else None

        if workflow and workflow.adw_id:
            state = ADWState.load(workflow.adw_id, logger)
            if state:
                logger.debug(f"Loaded existing state for issue {issue_number}")
                return state

        logger.debug(f"No existing state found for issue {issue_number}")
        return {}

    except Exception as e:
        logger.warning(f"Failed to load state: {e}")
        return {}


def check_plan_file_valid(plan_file_path: str, logger: logging.Logger) -> bool:
    """Check if plan file is valid.

    Args:
        plan_file_path: Path to plan file
        logger: Logger instance

    Returns:
        True if plan file exists and is valid
    """
    try:
        plan_path = Path(plan_file_path)

        if not plan_path.exists():
            logger.debug(f"Plan file does not exist: {plan_file_path}")
            return False

        # Check file size
        file_size = plan_path.stat().st_size
        if file_size < 100:
            logger.warning(f"Plan file suspiciously small ({file_size} bytes): {plan_file_path}")
            return False

        # Check for required sections
        content = plan_path.read_text()
        required_sections = ['## Objective', '## Implementation', '## Testing']

        for section in required_sections:
            if section not in content:
                logger.warning(f"Plan file missing section '{section}': {plan_file_path}")
                return False

        logger.debug(f"✓ Plan file is valid: {plan_file_path}")
        return True

    except Exception as e:
        logger.warning(f"Failed to validate plan file: {e}")
        return False


def get_worktree_path(issue_number: int, adw_id: Optional[str] = None) -> Optional[str]:
    """Get worktree path for issue.

    Args:
        issue_number: GitHub issue number
        adw_id: ADW identifier (optional)

    Returns:
        Absolute path to worktree or None if not found
    """
    try:
        # Try to get from database first
        from app.server.repositories.phase_queue_repository import PhaseQueueRepository
        repo = PhaseQueueRepository()
        workflows = repo.get_all_by_feature_id(issue_number)
        workflow = workflows[0] if workflows else None

        if workflow and workflow.adw_id:
            adw_id = workflow.adw_id

        if not adw_id:
            return None

        # Try multiple possible locations
        possible_paths = [
            Path(f"trees/{adw_id}"),
            Path(f"trees/adw-{adw_id}"),
        ]

        for path in possible_paths:
            if path.exists():
                return str(path.absolute())

        return None

    except Exception:
        return None


def check_pr_exists(issue_number: int, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """Check if pull request exists for issue.

    Args:
        issue_number: GitHub issue number
        logger: Logger instance

    Returns:
        PR dictionary if exists, None otherwise
    """
    try:
        import subprocess

        result = subprocess.run(
            ['gh', 'pr', 'list', '--search', f'{issue_number}',
             '--json', 'url,number,title,state,isDraft'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0 and result.stdout.strip():
            prs = json.loads(result.stdout)
            if prs:
                logger.debug(f"Found existing PR for issue {issue_number}: {prs[0]['url']}")
                return prs[0]

        logger.debug(f"No existing PR found for issue {issue_number}")
        return None

    except Exception as e:
        logger.warning(f"Failed to check for existing PR: {e}")
        return None


def check_worktree_exists(adw_id: str, logger: logging.Logger) -> bool:
    """Check if worktree exists for ADW.

    Args:
        adw_id: ADW identifier
        logger: Logger instance

    Returns:
        True if worktree exists
    """
    try:
        possible_paths = [
            Path(f"trees/{adw_id}"),
            Path(f"trees/adw-{adw_id}"),
        ]

        for path in possible_paths:
            if path.exists():
                logger.debug(f"✓ Worktree exists: {path}")
                return True

        logger.debug(f"Worktree does not exist for ADW {adw_id}")
        return False

    except Exception as e:
        logger.warning(f"Failed to check worktree existence: {e}")
        return False


def ensure_database_state(
    issue_number: int,
    status: str,
    current_phase: str,
    logger: logging.Logger,
    **extra_fields
) -> None:
    """Ensure database has correct state for phase.

    This updates the database SSoT if state is incorrect. Database updates
    are optional - if database is unavailable, this will log a warning and return.

    Args:
        issue_number: GitHub issue number
        status: Expected status
        current_phase: Expected current phase
        logger: Logger instance
        **extra_fields: Additional fields to update
    """
    try:
        # Lazy import - only if database modules are available
        from app.server.repositories.phase_queue_repository import PhaseQueueRepository

        repo = PhaseQueueRepository()
        # For Panel 5 multi-phase: feature_id may differ from issue_number
        # (e.g., feature #106 → issues #258, #259 for phases)
        # So we filter by issue_number instead
        all_phases = repo.get_all()
        workflows = [p for p in all_phases if p.issue_number == issue_number]
        workflow = workflows[0] if workflows else None

        if not workflow:
            logger.warning(f"Workflow not found in database for issue {issue_number} - skipping database update")
            return

        # Check if update needed
        needs_update = False
        update_fields = {}

        if workflow.status != status:
            logger.info(f"Updating database status: {workflow.status} → {status}")
            update_fields['status'] = status
            needs_update = True

        if workflow.current_phase != current_phase:
            logger.info(f"Updating database current_phase: {workflow.current_phase} → {current_phase}")
            update_fields['current_phase'] = current_phase
            needs_update = True

        # Add extra fields
        for key, value in extra_fields.items():
            if hasattr(workflow, key) and getattr(workflow, key) != value:
                logger.info(f"Updating database {key}: {getattr(workflow, key)} → {value}")
                update_fields[key] = value
                needs_update = True

        if needs_update:
            # Update phase coordination state (current_phase + status)
            if 'current_phase' in update_fields and 'status' in update_fields:
                repo.update_phase(
                    queue_id=workflow.queue_id,
                    current_phase=update_fields['current_phase'],
                    status=update_fields['status']
                )
            elif 'status' in update_fields:
                # Status-only update
                repo.update_status(
                    queue_id=workflow.queue_id,
                    status=update_fields['status'],
                    adw_id=update_fields.get('adw_id')
                )

            # Handle other field updates
            if 'error_message' in update_fields:
                repo.update_error_message(workflow.queue_id, update_fields['error_message'])

            logger.info(f"✓ Database state updated for issue {issue_number}")
        else:
            logger.debug(f"✓ Database state already correct for issue {issue_number}")

    except ImportError as e:
        # Database modules not available (psycopg2 not installed) - skip database update
        logger.warning(f"Database not available ({str(e)}) - skipping database update")
    except Exception as e:
        # Database query/update failed - log but don't fail the phase
        logger.warning(f"Failed to update database state: {e} - continuing without database update")


def log_idempotency_check(phase: str, is_complete: bool, logger: logging.Logger) -> None:
    """Log idempotency check result.

    Args:
        phase: Phase name
        is_complete: Whether phase is complete
        logger: Logger instance
    """
    if is_complete:
        logger.info(f"{'='*60}")
        logger.info(f"🔄 IDEMPOTENCY: {phase.upper()} phase already complete")
        logger.info(f"{'='*60}")
    else:
        logger.info(f"{'='*60}")
        logger.info(f"▶ EXECUTING: {phase.upper()} phase")
        logger.info(f"{'='*60}")
