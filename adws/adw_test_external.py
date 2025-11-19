#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ADW Test External - External test runner ADW workflow

This ADW workflow executes tests externally (pytest/vitest) and returns
compact results (failures only) to minimize context consumption.

Usage:
  uv run adw_test_external.py <issue-number> <adw-id> [--test-type=all]

Workflow:
1. Load state from agents/{adw_id}/adw_state.json
2. Get worktree_path from state
3. Execute adw_test_workflow.py in worktree context
4. Store compact results in state under 'external_test_results' key
5. Exit with 0 (success) or 1 (failures detected)

This workflow is designed to be chained from adw_test_iso.py via subprocess.
"""

import json
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adw_modules.state import ADWState
from adw_modules.utils import setup_logger


def run_external_tests(
    adw_id: str,
    test_type: str = "all",
    coverage_threshold: float = 80.0
) -> Dict[str, Any]:
    """
    Run tests using external test workflow.

    Args:
        adw_id: ADW ID for state management
        test_type: "pytest", "vitest", or "all"
        coverage_threshold: Minimum coverage percentage

    Returns:
        Test results dictionary
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
            "summary": {"total": 0, "passed": 0, "failed": 0},
            "failures": [],
            "next_steps": ["Create worktree with adw_plan_iso.py"]
        }

    # Get worktree path (where to run tests)
    worktree_path = state.get("worktree_path")
    if not worktree_path:
        return {
            "success": False,
            "error": {
                "type": "StateError",
                "message": "No worktree_path in state. Run adw_plan_iso.py first."
            },
            "summary": {"total": 0, "passed": 0, "failed": 0},
            "failures": [],
            "next_steps": ["Create worktree with adw_plan_iso.py"]
        }

    # Get project root
    project_root = Path(__file__).parent.parent

    # Build command to call the external test workflow
    test_workflow_script = project_root / "adws" / "adw_test_workflow.py"

    cmd = [
        "uv", "run",
        str(test_workflow_script),
        "--json-input", json.dumps({
            "test_type": test_type,
            "coverage_threshold": coverage_threshold,
            "fail_fast": False,
            "verbose": True
        })
    ]

    # Execute in worktree context
    try:
        result = subprocess.run(
            cmd,
            cwd=worktree_path,  # Run in the isolated worktree
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )

        # Parse JSON output
        try:
            test_results = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            # Fallback if JSON parsing fails
            test_results = {
                "success": False,
                "error": {
                    "type": "JSONDecodeError",
                    "message": f"Failed to parse test output: {str(e)}",
                    "details": result.stdout[:500]
                },
                "summary": {"total": 0, "passed": 0, "failed": 1},
                "failures": [],
                "next_steps": ["Check test workflow output format"]
            }

        return test_results

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": {
                "type": "TimeoutError",
                "message": "Test execution timed out after 10 minutes"
            },
            "summary": {"total": 0, "passed": 0, "failed": 0},
            "failures": [],
            "next_steps": ["Investigate slow tests or infinite loops"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": {
                "type": type(e).__name__,
                "message": str(e)
            },
            "summary": {"total": 0, "passed": 0, "failed": 0},
            "failures": [],
            "next_steps": [f"Investigate error: {str(e)}"]
        }


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: uv run adw_test_external.py <issue-number> <adw-id> [--test-type=all]")
        print("\nThis ADW workflow runs tests externally and stores compact results in state.")
        print("It is designed to be chained from adw_test_iso.py via subprocess.")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2]

    # Parse optional flags
    test_type = "all"
    for arg in sys.argv[3:]:
        if arg.startswith("--test-type="):
            test_type = arg.split("=")[1]

    # Setup logging
    logger = setup_logger(f"adw_test_external_{adw_id}")
    logger.info(f"Starting external test workflow for issue #{issue_number}, ADW {adw_id}")

    # Run tests
    logger.info(f"Running tests with type: {test_type}")
    results = run_external_tests(adw_id, test_type=test_type)

    # Load state to save results
    state = ADWState.load(adw_id)
    if not state:
        logger.error("Failed to load state for saving results")
        sys.exit(1)

    # Store results in state
    state.data["external_test_results"] = results
    state.save(workflow_step="test_external")

    # Log summary
    if results.get("success"):
        logger.info(f"✅ All {results['summary']['total']} tests passed!")
        print(f"✅ All {results['summary']['total']} tests passed!")
    else:
        failed_count = results.get("summary", {}).get("failed", 0)
        logger.warning(f"❌ {failed_count} test(s) failed")
        print(f"❌ {failed_count} test(s) failed")

        # Print failures
        for failure in results.get("failures", []):
            failure_msg = f"  - {failure.get('file', '?')}:{failure.get('line', '?')} - {failure.get('error_message', 'Unknown error')}"
            logger.error(failure_msg)
            print(failure_msg)

    # Exit with appropriate code
    exit_code = 0 if results.get("success") else 1
    logger.info(f"Exiting with code {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
