#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ADW Lint Workflow - External linting validation tool

This workflow runs ESLint and Ruff linting processes,
returning only errors with precise locations to minimize context.

Usage:
    # As standalone tool
    uv run adw_lint_workflow.py --target=both --fix-mode

    # As invoked tool (from another ADW)
    from adw_modules.tool_registry import ToolRegistry
    registry = ToolRegistry()
    result = registry.invoke_tool("run_lint_workflow", {
        "target": "frontend",
        "fix_mode": False
    })

Input Schema:
    {
        "target": "frontend" | "backend" | "both",
        "fix_mode": bool (default: False),
        "changed_files_only": bool (default: False)
    }

Output Schema:
    {
        "success": bool,
        "summary": {
            "total_errors": int,
            "style_errors": int,
            "quality_errors": int,
            "warnings": int,
            "fixable_count": int,
            "duration_seconds": float
        },
        "errors": [{
            "file": str,
            "line": int,
            "column": int,
            "rule": str,
            "severity": "error" | "warning",
            "message": str,
            "fixable": bool
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

from adw_modules.lint_checker import LintChecker, result_to_dict


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run linting and return errors only"
    )
    parser.add_argument(
        "--target",
        type=str,
        choices=["frontend", "backend", "both"],
        default="both",
        help="Which codebase to lint"
    )
    parser.add_argument(
        "--fix-mode",
        action="store_true",
        default=False,
        help="Enable auto-fix mode"
    )
    parser.add_argument(
        "--changed-files-only",
        action="store_true",
        default=False,
        help="Only lint changed files vs main branch"
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
    Execute the lint workflow.

    Args:
        params: Input parameters matching the input schema

    Returns:
        Output matching the output schema
    """
    # Extract parameters
    target = params.get("target", "both")
    fix_mode = params.get("fix_mode", False)
    changed_files_only = params.get("changed_files_only", False)

    # Get project root (2 levels up from this file)
    project_root = Path(__file__).parent.parent

    # Initialize lint checker
    checker = LintChecker(project_root)

    # Execute checks
    results = checker.check_all(
        target=target,
        fix_mode=fix_mode,
        changed_files_only=changed_files_only
    )

    # Combine results
    all_errors = []
    total_duration = 0.0
    total_style_errors = 0
    total_quality_errors = 0
    total_warnings = 0
    total_fixable = 0

    for check_name, result in results.items():
        all_errors.extend(result.errors)
        total_duration += result.summary.duration_seconds
        total_style_errors += result.summary.style_errors
        total_quality_errors += result.summary.quality_errors
        total_warnings += result.summary.warnings
        total_fixable += result.summary.fixable_count

    # Generate next steps
    next_steps = []
    if all_errors:
        if total_fixable > 0:
            next_steps.append(f"{total_fixable} error(s) can be auto-fixed with --fix-mode")

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
                f"(starting at line {first_error.line}: {first_error.rule})"
            )
    else:
        next_steps.append("All lint checks passed!")

    success = len(all_errors) == 0

    return {
        "success": success,
        "summary": {
            "total_errors": len(all_errors),
            "style_errors": total_style_errors,
            "quality_errors": total_quality_errors,
            "warnings": total_warnings,
            "fixable_count": total_fixable,
            "duration_seconds": total_duration
        },
        "errors": [
            {
                "file": e.file,
                "line": e.line,
                "column": e.column,
                "rule": e.rule,
                "severity": e.severity,
                "message": e.message,
                "fixable": e.fixable
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
            "target": args.target,
            "fix_mode": args.fix_mode,
            "changed_files_only": args.changed_files_only
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
                "details": "Unexpected error during lint checking"
            },
            "next_steps": [f"Investigate {type(e).__name__}: {str(e)}"]
        }
        print(json.dumps(error_result, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
