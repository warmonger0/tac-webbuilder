#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ADW Build External - External build/typecheck ADW workflow

This ADW workflow executes build/typecheck externally and returns
compact results (errors only) to minimize context consumption.

Usage:
  uv run adw_build_external.py <issue-number> <adw-id> [--check-type=both] [--target=both]

Workflow:
1. Load state from agents/{adw_id}/adw_state.json
2. Get worktree_path from state
3. Execute adw_build_workflow.py in worktree context
4. Store compact results in state under 'external_build_results' key
5. Exit with 0 (success) or 1 (errors detected)

This workflow is designed to be chained from adw_build_iso.py via subprocess.
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


def run_external_build_check(
    adw_id: str,
    check_type: str = "both",
    target: str = "both",
    strict_mode: bool = True
) -> Dict[str, Any]:
    """
    Run build/typecheck using external build workflow.

    Args:
        adw_id: ADW ID for state management
        check_type: "typecheck", "build", or "both"
        target: "frontend", "backend", or "both"
        strict_mode: Enable strict TypeScript checking

    Returns:
        Build results dictionary
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
            "summary": {"total_errors": 0, "type_errors": 0, "build_errors": 0},
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
            "summary": {"total_errors": 0, "type_errors": 0, "build_errors": 0},
            "errors": [],
            "next_steps": ["Create worktree with adw_plan_iso.py"]
        }

    # Get issue number from state for observability tracking
    issue_number = state.get("issue_number", 0)

    # Get project root
    project_root = Path(__file__).parent.parent

    # Build command to call the external build workflow
    build_workflow_script = project_root / "adws" / "adw_build_workflow.py"

    cmd = [
        "uv", "run",
        str(build_workflow_script),
        "--json-input", json.dumps({
            "check_type": check_type,
            "target": target,
            "strict_mode": strict_mode,
            "adw_id": adw_id,  # Pass adw_id for tool tracking
            "issue_number": issue_number  # Pass issue_number for tool tracking
        })
    ]

    # Execute in worktree context
    try:
        result = subprocess.run(
            cmd,
            cwd=worktree_path,  # Run in the isolated worktree
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        # Parse JSON output
        try:
            build_results = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            # Fallback if JSON parsing fails
            build_results = {
                "success": False,
                "error": {
                    "type": "JSONDecodeError",
                    "message": f"Failed to parse build output: {str(e)}",
                    "details": result.stdout[:500]
                },
                "summary": {"total_errors": 1, "type_errors": 0, "build_errors": 1},
                "errors": [],
                "next_steps": ["Check build workflow output format"]
            }

        return build_results

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": {
                "type": "TimeoutError",
                "message": "Build check timed out after 5 minutes"
            },
            "summary": {"total_errors": 1, "type_errors": 0, "build_errors": 1},
            "errors": [],
            "next_steps": ["Investigate slow compilation or circular dependencies"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": {
                "type": type(e).__name__,
                "message": str(e)
            },
            "summary": {"total_errors": 1, "type_errors": 0, "build_errors": 1},
            "errors": [],
            "next_steps": [f"Investigate error: {str(e)}"]
        }


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: uv run adw_build_external.py <issue-number> <adw-id> [--check-type=both] [--target=both]")
        print("\nThis ADW workflow runs build/typecheck externally and stores compact results in state.")
        print("It is designed to be chained from adw_build_iso.py via subprocess.")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2]

    # Parse optional flags
    check_type = "both"
    target = "both"
    strict_mode = True

    for arg in sys.argv[3:]:
        if arg.startswith("--check-type="):
            check_type = arg.split("=")[1]
        elif arg.startswith("--target="):
            target = arg.split("=")[1]
        elif arg == "--no-strict":
            strict_mode = False

    # Setup logging
    logger = setup_logger(f"adw_build_external_{adw_id}")
    logger.info(f"Starting external build workflow for issue #{issue_number}, ADW {adw_id}")

    # Run build checks
    logger.info(f"Running build checks: {check_type} on {target}")
    results = run_external_build_check(
        adw_id,
        check_type=check_type,
        target=target,
        strict_mode=strict_mode
    )

    # Load state to save results
    state = ADWState.load(adw_id)
    if not state:
        logger.error("Failed to load state for saving results")
        sys.exit(1)

    # Store results in state
    state.data["external_build_results"] = results
    state.save(workflow_step="build_external")

    # Log summary
    if results.get("success"):
        logger.info("✅ No build errors found!")
        print("✅ No build errors found!")
    else:
        error_count = results.get("summary", {}).get("total_errors", 0)
        logger.warning(f"❌ {error_count} build error(s) found")
        print(f"❌ {error_count} build error(s) found")

        # Print errors
        for error in results.get("errors", [])[:5]:  # First 5 errors
            error_msg = f"  - {error.get('file', '?')}:{error.get('line', '?')} - {error.get('error_type', '?')}: {error.get('message', 'Unknown error')}"
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
