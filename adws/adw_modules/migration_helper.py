#!/usr/bin/env python3
"""
Migration Helper - Auto-forwarding for deprecated ADW workflows

This module provides functionality to automatically forward deprecated workflows
to their complete replacements while logging usage for tracking.
"""

import sys
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, List


# Workflow mapping
WORKFLOW_MAPPING = {
    "adw_sdlc_iso.py": "adw_sdlc_complete_iso.py",
    "adw_sdlc_zte_iso.py": "adw_sdlc_complete_zte_iso.py",
    "adw_plan_build_iso.py": "adw_sdlc_complete_iso.py",
    "adw_plan_build_test_iso.py": "adw_sdlc_complete_iso.py",
    "adw_plan_build_test_review_iso.py": "adw_sdlc_complete_iso.py",
    "adw_plan_build_review_iso.py": "adw_sdlc_complete_iso.py",
    "adw_plan_build_document_iso.py": "adw_sdlc_complete_iso.py",
}


def log_migration(deprecated_workflow: str, replacement_workflow: str, args: List[str]) -> None:
    """
    Log migration event for tracking.

    Args:
        deprecated_workflow: Name of deprecated workflow
        replacement_workflow: Name of replacement workflow
        args: Command line arguments passed
    """
    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "workflow_migrations.jsonl"

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "deprecated_workflow": deprecated_workflow,
        "replacement_workflow": replacement_workflow,
        "args": args,
        "auto_forwarded": True
    }

    try:
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        print(f"Warning: Could not write migration log: {e}", file=sys.stderr)


def should_auto_forward(args: List[str]) -> bool:
    """
    Check if auto-forwarding should be enabled.

    Args:
        args: Command line arguments

    Returns:
        True if --forward-to-complete flag is present
    """
    return "--forward-to-complete" in args


def get_forwarding_args(args: List[str]) -> List[str]:
    """
    Get arguments for forwarding, removing migration-specific flags.

    Args:
        args: Original command line arguments

    Returns:
        Cleaned arguments list
    """
    # Remove migration-specific flags
    return [arg for arg in args if arg != "--forward-to-complete"]


def forward_to_complete(
    deprecated_workflow: str,
    script_dir: str,
    args: List[str],
    show_warning: bool = True
) -> None:
    """
    Forward execution to complete workflow replacement.

    Args:
        deprecated_workflow: Name of current (deprecated) workflow file
        script_dir: Directory containing workflow scripts
        args: Command line arguments (excluding script name)
        show_warning: Whether to show deprecation warning

    This function does not return - it replaces the current process.
    """
    # Get replacement workflow
    replacement_workflow = WORKFLOW_MAPPING.get(deprecated_workflow)

    if not replacement_workflow:
        print(f"Error: No replacement workflow defined for {deprecated_workflow}", file=sys.stderr)
        sys.exit(1)

    replacement_path = os.path.join(script_dir, replacement_workflow)

    # Check if replacement exists
    if not os.path.exists(replacement_path):
        print(f"Error: Replacement workflow not found: {replacement_path}", file=sys.stderr)
        sys.exit(1)

    # Log migration
    log_migration(deprecated_workflow, replacement_workflow, args)

    # Show forwarding message
    if show_warning:
        print("=" * 80)
        print("🔄 AUTO-FORWARDING TO COMPLETE WORKFLOW")
        print("=" * 80)
        print(f"Deprecated: {deprecated_workflow}")
        print(f"Forwarding to: {replacement_workflow}")
        print("")
        print("This workflow has been deprecated. You are being automatically")
        print("forwarded to the complete version.")
        print("")
        print("To update your scripts:")
        print(f"  sed -i 's/{deprecated_workflow}/{replacement_workflow}/g' <file>")
        print("")
        print("Or run the migration helper:")
        print("  ./scripts/migrate_workflow_refs.sh")
        print("=" * 80)
        print("")

    # Get cleaned arguments
    forwarding_args = get_forwarding_args(args)

    # Build command
    cmd = ["uv", "run", replacement_path] + forwarding_args

    # Replace current process with new workflow
    # This is the most transparent way to forward - the user won't see a subprocess
    os.execvp("uv", cmd)


def check_and_forward(
    deprecated_workflow: str,
    script_dir: Optional[str] = None,
    args: Optional[List[str]] = None
) -> bool:
    """
    Check if auto-forwarding is requested and forward if so.

    Args:
        deprecated_workflow: Name of current workflow file
        script_dir: Directory containing workflows (defaults to current script's dir)
        args: Command line arguments (defaults to sys.argv[1:])

    Returns:
        True if forwarded (won't actually return), False if not forwarding

    Usage in deprecated workflow:
        from adw_modules.migration_helper import check_and_forward

        # At the top of main()
        if check_and_forward("adw_sdlc_iso.py"):
            return  # Never reached, but for clarity
    """
    if script_dir is None:
        # Get directory of calling script
        import inspect
        caller_frame = inspect.stack()[1]
        caller_file = caller_frame.filename
        script_dir = os.path.dirname(os.path.abspath(caller_file))

    if args is None:
        args = sys.argv[1:]

    # Check if auto-forwarding is enabled
    if should_auto_forward(args):
        forward_to_complete(deprecated_workflow, script_dir, args, show_warning=True)
        # Never returns

    return False


def print_deprecation_notice(
    workflow_name: str,
    missing_phases: List[str],
    replacement: str
) -> None:
    """
    Print standard deprecation notice.

    Args:
        workflow_name: Name of deprecated workflow
        missing_phases: List of phases that are missing
        replacement: Name of replacement workflow
    """
    print("=" * 80)
    print("⚠️  DEPRECATION WARNING")
    print("=" * 80)
    print(f"Workflow: {workflow_name}")
    print(f"Status: DEPRECATED")
    print("")
    print(f"Missing phases: {', '.join(missing_phases)}")
    print(f"Recommended replacement: {replacement}")
    print("")
    print("This workflow will continue to work but is missing critical phases.")
    print("")
    print("To migrate:")
    print(f"  1. Replace {workflow_name} with {replacement} in your scripts")
    print("  2. Or use auto-forward: <workflow> <args> --forward-to-complete")
    print("  3. Or run: ./scripts/migrate_workflow_refs.sh")
    print("")
    print("Migration guide:")
    print("  docs/planned_features/workflow-enhancements/MIGRATION_GUIDE.md")
    print("")
    print("Continuing with deprecated workflow...")
    print("=" * 80)
    print("")
