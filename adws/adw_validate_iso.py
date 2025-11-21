#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ADW Validate Iso - Pre-build validation and baseline error detection

Usage: uv run adw_validate_iso.py <issue-number> <adw-id>

This phase runs BEFORE implementation to:
1. Establish baseline error state of worktree
2. Detect inherited errors from main branch
3. Enable differential error detection in Build phase
4. Prevent false positives from blocking work

This phase NEVER fails - it only collects baseline data.
"""

import sys
import os
import time
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adw_modules.state import ADWState
from adw_modules.github import make_issue_comment
from adw_modules.workflow_ops import format_issue_message
from adw_modules.utils import setup_logger


def run_baseline_validation(
    adw_id: str,
    issue_number: str,
    logger
) -> Dict[str, Any]:
    """
    Run baseline validation on unmodified worktree.

    Returns baseline error state.
    """
    # Load state
    state = ADWState.load(adw_id)
    if not state:
        logger.error("No state found")
        return {"error": "No state found"}

    worktree_path = state.get("worktree_path")
    if not worktree_path:
        logger.error("No worktree path in state")
        return {"error": "No worktree path in state"}

    logger.info(f"Running baseline validation on worktree: {worktree_path}")

    # Import build external tool
    script_dir = Path(__file__).parent
    build_external_script = script_dir / "adw_build_external.py"

    if not build_external_script.exists():
        logger.error("Build external script not found")
        return {"error": "Build external script not found"}

    # Run build check on UNMODIFIED worktree
    import subprocess
    cmd = ["uv", "run", str(build_external_script), issue_number, adw_id]

    logger.info(f"Executing baseline check: {' '.join(cmd)}")
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration = time.time() - start_time

    # Reload state to get build results
    reloaded_state = ADWState.load(adw_id)
    if not reloaded_state:
        logger.error("Failed to reload state")
        return {"error": "Failed to reload state"}

    build_results = reloaded_state.get("external_build_results", {})

    # Extract baseline errors
    baseline = {
        "frontend": {
            "type_errors": build_results.get("summary", {}).get("type_errors", 0),
            "build_errors": build_results.get("summary", {}).get("build_errors", 0),
            "warnings": build_results.get("summary", {}).get("warnings", 0),
            "error_details": build_results.get("errors", [])
        },
        "validation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "worktree_base_commit": get_worktree_base_commit(worktree_path),
        "duration_seconds": duration
    }

    logger.info(f"Baseline validation complete: {baseline['frontend']['type_errors']} type errors")

    return baseline


def get_worktree_base_commit(worktree_path: str) -> str:
    """Get the base commit hash of the worktree."""
    import subprocess
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=worktree_path,
        capture_output=True,
        text=True
    )
    return result.stdout.strip()


def format_baseline_report(baseline: Dict[str, Any]) -> str:
    """Format baseline validation report for GitHub comment."""
    frontend = baseline.get("frontend", {})
    total_errors = frontend.get("type_errors", 0) + frontend.get("build_errors", 0)

    if total_errors == 0:
        return (
            f"📊 **Baseline Validation Complete**\n\n"
            f"**Worktree Base**: `{baseline.get('worktree_base_commit')}` ({baseline.get('validation_timestamp')})\n\n"
            f"✅ **No inherited errors detected** - Clean baseline!\n\n"
            f"Any errors detected in Build phase will be considered NEW and will block the workflow.\n\n"
            f"**Status**: ✅ Validation complete - proceeding to Build phase"
        )

    error_details = frontend.get("error_details", [])

    report = (
        f"📊 **Baseline Validation Complete**\n\n"
        f"**Worktree Base**: `{baseline.get('worktree_base_commit')}` ({baseline.get('validation_timestamp')})\n\n"
        f"### Inherited Errors from Main Branch\n"
        f"⚠️ **{total_errors} errors detected** (will be ignored in Build phase)\n\n"
    )

    # List first 5 errors
    for i, error in enumerate(error_details[:5]):
        file_path = error.get("file", "unknown")
        line = error.get("line", "?")
        column = error.get("column", "?")
        message = error.get("message", "unknown error")
        report += f"- `{file_path}:{line}:{column}` - {message}\n"

    if len(error_details) > 5:
        report += f"... and {len(error_details) - 5} more errors\n"

    report += (
        f"\nℹ️ These errors exist on main branch and will **NOT block this workflow**.\n"
        f"Only NEW errors introduced by this implementation will cause failures.\n\n"
        f"**Status**: ✅ Validation complete - proceeding to Build phase"
    )

    return report


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: uv run adw_validate_iso.py <issue-number> <adw-id>")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2]

    # Setup logger
    logger = setup_logger(adw_id, "adw_validate_iso")
    logger.info(f"Starting validation phase - Issue: {issue_number}, ADW: {adw_id}")

    # Post starting comment
    make_issue_comment(
        issue_number,
        format_issue_message(
            adw_id,
            "validator",
            "🔍 Running baseline validation to detect inherited errors..."
        )
    )

    # Run baseline validation
    baseline = run_baseline_validation(adw_id, issue_number, logger)

    if "error" in baseline:
        logger.error(f"Validation failed: {baseline['error']}")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                "validator",
                f"⚠️ Validation encountered an issue: {baseline['error']}\n\n"
                f"Continuing to Build phase without baseline data."
            )
        )
        # Don't fail - just continue without baseline
        sys.exit(0)

    # Store baseline in state
    state = ADWState.load(adw_id)
    state.update(baseline_errors=baseline)
    logger.info("Baseline errors stored in state")

    # Post validation report
    report = format_baseline_report(baseline)
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "validator", report)
    )

    logger.info("Validation phase completed successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()
