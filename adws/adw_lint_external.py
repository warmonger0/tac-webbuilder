#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ADW Lint External - External linting ADW workflow

This ADW workflow executes linting externally and returns
compact results (errors only) to minimize context consumption.

Usage:
  uv run adw_lint_external.py <issue-number> <adw-id> [--target=both] [--fix-mode]

Workflow:
1. Load state from agents/{adw_id}/adw_state.json
2. Get worktree_path from state
3. Execute adw_lint_workflow.py in worktree context
4. Store compact results in state under 'external_lint_results' key
5. Exit with 0 (success) or 1 (errors detected)

This workflow is designed to be chained from adw_lint_iso.py via subprocess.
"""

import json
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adw_modules.state import ADWState
from adw_modules.utils import setup_logger


def run_external_lint_check(
    adw_id: str,
    target: str = "both",
    fix_mode: bool = False
) -> Dict[str, Any]:
    """
    Run linting using external lint workflow.

    Args:
        adw_id: ADW ID for state management
        target: "frontend", "backend", or "both"
        fix_mode: Enable auto-fix mode

    Returns:
        Lint results dictionary
    """
    # Load state
    state = ADWState.load(adw_id)
    if not state:
        return {
            "success": False,
            "error": {
                "type": "StateError",
                "message": "No state file found. Run adw_plan_iso.py first."
            },
            "summary": {
                "total_errors": 0,
                "style_errors": 0,
                "quality_errors": 0,
                "warnings": 0,
                "fixable_count": 0
            },
            "errors": [],
            "next_steps": ["Create worktree with adw_plan_iso.py"]
        }

    # Get worktree path
    worktree_path = state.get("worktree_path")
    if not worktree_path:
        return {
            "success": False,
            "error": {
                "type": "StateError",
                "message": "No worktree_path in state. Run adw_plan_iso.py first."
            },
            "summary": {
                "total_errors": 0,
                "style_errors": 0,
                "quality_errors": 0,
                "warnings": 0,
                "fixable_count": 0
            },
            "errors": [],
            "next_steps": ["Create worktree with adw_plan_iso.py"]
        }

    # Get project root
    project_root = Path(__file__).parent.parent

    # Build command to call the external lint workflow
    lint_workflow_script = project_root / "adws" / "adw_lint_workflow.py"

    cmd = [
        "uv", "run",
        str(lint_workflow_script),
        "--json-input", json.dumps({
            "target": target,
            "fix_mode": fix_mode
        })
    ]

    # Execute in worktree context
    try:
        result = subprocess.run(
            cmd,
            cwd=worktree_path,  # Run in the isolated worktree
            capture_output=True,
            text=True,
            timeout=180  # 3 minute timeout
        )

        # Parse JSON output
        try:
            lint_results = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            # Fallback if JSON parsing fails
            lint_results = {
                "success": False,
                "error": {
                    "type": "JSONDecodeError",
                    "message": f"Failed to parse lint output: {str(e)}",
                    "details": result.stdout[:500]
                },
                "summary": {
                    "total_errors": 1,
                    "style_errors": 0,
                    "quality_errors": 1,
                    "warnings": 0,
                    "fixable_count": 0
                },
                "errors": [],
                "next_steps": ["Check lint workflow output format"]
            }

        return lint_results

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": {
                "type": "TimeoutError",
                "message": "Lint check timed out after 3 minutes"
            },
            "summary": {
                "total_errors": 1,
                "style_errors": 0,
                "quality_errors": 1,
                "warnings": 0,
                "fixable_count": 0
            },
            "errors": [],
            "next_steps": ["Investigate slow linting or large file set"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": {
                "type": type(e).__name__,
                "message": str(e)
            },
            "summary": {
                "total_errors": 1,
                "style_errors": 0,
                "quality_errors": 1,
                "warnings": 0,
                "fixable_count": 0
            },
            "errors": [],
            "next_steps": [f"Investigate error: {str(e)}"]
        }


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: uv run adw_lint_external.py <issue-number> <adw-id> [--target=both] [--fix-mode]")
        print("\nThis ADW workflow runs linting externally and stores compact results in state.")
        print("It is designed to be chained from adw_lint_iso.py via subprocess.")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2]

    # Parse optional flags
    target = "both"
    fix_mode = False

    for arg in sys.argv[3:]:
        if arg.startswith("--target="):
            target = arg.split("=")[1]
        elif arg == "--fix-mode":
            fix_mode = True

    # Setup logging
    logger = setup_logger(f"adw_lint_external_{adw_id}")
    logger.info(f"Starting external lint workflow for issue #{issue_number}, ADW {adw_id}")

    # Run lint checks
    logger.info(f"Running lint checks on {target}{' with auto-fix' if fix_mode else ''}")
    results = run_external_lint_check(
        adw_id,
        target=target,
        fix_mode=fix_mode
    )

    # Load state to save results
    state = ADWState.load(adw_id)
    if not state:
        logger.error("Failed to load state for saving results")
        sys.exit(1)

    # Store results in state
    state.data["external_lint_results"] = results
    state.save(workflow_step="lint_external")

    # Log summary
    if results.get("success"):
        logger.info("✅ No lint errors found!")
        print("✅ No lint errors found!")
    else:
        error_count = results.get("summary", {}).get("total_errors", 0)
        fixable_count = results.get("summary", {}).get("fixable_count", 0)
        logger.warning(f"❌ {error_count} lint error(s) found ({fixable_count} fixable)")
        print(f"❌ {error_count} lint error(s) found ({fixable_count} fixable)")

        # Print errors
        for error in results.get("errors", [])[:5]:  # First 5 errors
            fixable_marker = "🔧" if error.get("fixable") else "  "
            error_msg = (
                f"{fixable_marker} {error.get('file', '?')}:{error.get('line', '?')} - "
                f"{error.get('rule', '?')}: {error.get('message', 'Unknown error')}"
            )
            logger.error(error_msg)
            print(error_msg)

        if len(results.get("errors", [])) > 5:
            remaining = len(results["errors"]) - 5
            print(f"  ... and {remaining} more error(s)")

    # Exit with appropriate code
    exit_code = 0 if results.get("success") else 1
    logger.info(f"Exiting with code {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
