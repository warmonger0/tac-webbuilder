#!/usr/bin/env python3
"""
Example: Using ToolCallTracker with BuildChecker

This example demonstrates how to use ToolCallTracker to capture
tool usage in the Build phase and automatically log to observability.

Usage:
    python examples/build_with_tracking_example.py <issue-number> <adw-id>
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_modules.tool_call_tracker import ToolCallTracker
from adw_modules.build_checker import BuildChecker


def run_build_with_tracking(issue_number: int, adw_id: str):
    """
    Example of running build checks with tool call tracking.

    Args:
        issue_number: GitHub issue number
        adw_id: ADW workflow ID
    """
    project_root = Path(__file__).parent.parent.parent  # tac-webbuilder root

    # Use ToolCallTracker context manager
    with ToolCallTracker(
        adw_id=adw_id,
        issue_number=issue_number,
        phase_name="Build",
        phase_number=3,
        workflow_template="adw_build_iso"
    ) as tracker:
        # Create BuildChecker with tracker
        checker = BuildChecker(project_root, tracker=tracker)

        # Run build checks - tools are automatically tracked
        print("Running frontend type checks...")
        frontend_types_result = checker.check_frontend_types()
        print(f"  ✓ Type errors: {frontend_types_result.summary.type_errors}")

        print("Running frontend build...")
        frontend_build_result = checker.check_frontend_build()
        print(f"  ✓ Build errors: {frontend_build_result.summary.build_errors}")

        print("Running backend type checks...")
        backend_types_result = checker.check_backend_types()
        print(f"  ✓ Type errors: {backend_types_result.summary.type_errors}")

        # Get summary of tracked tools
        summary = tracker.get_summary()
        print(f"\nTool Tracking Summary:")
        print(f"  Total calls: {summary['total_calls']}")
        print(f"  Successful: {summary['successful_calls']}")
        print(f"  Failed: {summary['failed_calls']}")
        print(f"  Total duration: {summary['total_duration_ms']}ms")
        print(f"  Tools used: {', '.join(summary['tools_used'])}")

    # When context exits, tool_calls are automatically logged to observability system
    print("\n✓ Tool calls logged to observability system!")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python build_with_tracking_example.py <issue-number> <adw-id>")
        sys.exit(1)

    issue_num = int(sys.argv[1])
    adw_id = sys.argv[2]

    run_build_with_tracking(issue_num, adw_id)
