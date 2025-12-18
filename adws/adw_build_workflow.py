#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ADW Build Workflow - External build/typecheck validation tool

This workflow runs TypeScript type checking and build processes,
returning only errors with precise locations to minimize context.

Usage:
    # As standalone tool
    uv run adw_build_workflow.py --check-type=both --target=frontend

    # As invoked tool (from another ADW)
    from adw_modules.tool_registry import ToolRegistry
    registry = ToolRegistry()
    result = registry.invoke_tool("run_build_workflow", {
        "check_type": "both",
        "target": "frontend"
    })

Input Schema:
    {
        "check_type": "typecheck" | "build" | "both",
        "target": "frontend" | "backend" | "both",
        "strict_mode": bool (default: True)
    }

Output Schema:
    {
        "success": bool,
        "summary": {
            "total_errors": int,
            "type_errors": int,
            "build_errors": int,
            "warnings": int,
            "duration_seconds": float
        },
        "errors": [{
            "file": str,
            "line": int,
            "column": int,
            "error_type": str,
            "severity": "error" | "warning",
            "message": str
        }],
        "next_steps": [str]
    }
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from adw_modules.build_checker import BuildChecker, result_to_dict
from adw_modules.tool_call_tracker import ToolCallTracker


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run build/typecheck and return errors only"
    )
    parser.add_argument(
        "--check-type",
        type=str,
        choices=["typecheck", "build", "both"],
        default="both",
        help="What to check"
    )
    parser.add_argument(
        "--target",
        type=str,
        choices=["frontend", "backend", "both"],
        default="both",
        help="Which codebase to check"
    )
    parser.add_argument(
        "--strict-mode",
        action="store_true",
        default=True,
        help="Enable strict TypeScript checking"
    )
    parser.add_argument(
        "--json-input",
        type=str,
        default=None,
        help="JSON string with input parameters (alternative to CLI args)"
    )

    return parser.parse_args()


def run_workflow(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the build workflow.

    Args:
        params: Input parameters matching the input schema

    Returns:
        Output matching the output schema
    """
    # Extract parameters
    check_type = params.get("check_type", "both")
    target = params.get("target", "both")
    strict_mode = params.get("strict_mode", True)
    adw_id = params.get("adw_id", "unknown")
    issue_number = params.get("issue_number", 0)

    # Get project root (2 levels up from this file)
    project_root = Path(__file__).parent.parent

    # Use ToolCallTracker to track build tools automatically
    with ToolCallTracker(
        adw_id=adw_id,
        issue_number=int(issue_number) if issue_number else 0,
        phase_name="Build",
        phase_number=3,
        workflow_template="adw_build_workflow"
    ) as tracker:
        # Initialize build checker with tracker
        checker = BuildChecker(project_root, tracker=tracker)

        # Execute checks - tools are automatically tracked
        results = checker.check_all(
            check_type=check_type,
            target=target,
            strict_mode=strict_mode
        )

    # Combine results
    all_errors = []
    total_duration = 0.0
    total_type_errors = 0
    total_build_errors = 0
    total_warnings = 0

    for check_name, result in results.items():
        all_errors.extend(result.errors)
        total_duration += result.summary.duration_seconds
        total_type_errors += result.summary.type_errors
        total_build_errors += result.summary.build_errors
        total_warnings += result.summary.warnings

    # Generate next steps
    next_steps = []
    if all_errors:
        # Group errors by file
        files_with_errors = {}
        for error in all_errors:
            if error.file not in files_with_errors:
                files_with_errors[error.file] = []
            files_with_errors[error.file].append(error)

        # Add next steps for first 3 files
        for file_path, errors in list(files_with_errors.items())[:3]:
            error_count = len(errors)
            first_error = errors[0]
            next_steps.append(
                f"Fix {error_count} error(s) in {file_path} "
                f"(starting at line {first_error.line}: {first_error.error_type})"
            )
    else:
        next_steps.append("All checks passed!")

    success = len(all_errors) == 0

    return {
        "success": success,
        "summary": {
            "total_errors": len(all_errors),
            "type_errors": total_type_errors,
            "build_errors": total_build_errors,
            "warnings": total_warnings,
            "duration_seconds": total_duration
        },
        "errors": [
            {
                "file": e.file,
                "line": e.line,
                "column": e.column,
                "error_type": e.error_type,
                "severity": e.severity,
                "message": e.message,
                "code_snippet": e.code_snippet
            }
            for e in all_errors
        ],
        "next_steps": next_steps
    }


def main():
    """Main entry point."""
    args = parse_args()

    # Build parameters from either JSON input or CLI args
    if args.json_input:
        try:
            params = json.loads(args.json_input)
        except json.JSONDecodeError as e:
            print(json.dumps({
                "success": False,
                "error": {
                    "type": "JSONDecodeError",
                    "message": f"Invalid JSON input: {str(e)}"
                },
                "next_steps": ["Fix JSON input format"]
            }), file=sys.stderr)
            sys.exit(1)
    else:
        params = {
            "check_type": args.check_type,
            "target": args.target,
            "strict_mode": args.strict_mode
        }

    # Execute workflow
    try:
        result = run_workflow(params)

        # Output JSON result
        print(json.dumps(result, indent=2))

        # Exit with appropriate code
        sys.exit(0 if result.get("success", False) else 1)

    except Exception as e:
        # Handle unexpected errors
        error_result = {
            "success": False,
            "error": {
                "type": type(e).__name__,
                "message": str(e),
                "details": "Unexpected error during build checking"
            },
            "next_steps": [f"Investigate {type(e).__name__}: {str(e)}"]
        }
        print(json.dumps(error_result, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
