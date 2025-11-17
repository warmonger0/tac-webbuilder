#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ADW Test Workflow - External test execution tool

This workflow executes tests (pytest/vitest) and returns only failures
with precise error locations, dramatically reducing context consumption.

Usage:
    # As standalone tool
    uv run adw_test_workflow.py --test-type=all --coverage-threshold=80

    # As invoked tool (from another ADW)
    from adw_modules.tool_registry import ToolRegistry
    registry = ToolRegistry()
    result = registry.invoke_tool("run_test_workflow", {
        "test_type": "all",
        "coverage_threshold": 80
    })

Input Schema:
    {
        "test_path": Optional[str],
        "test_type": "pytest" | "vitest" | "all",
        "coverage_threshold": float (default: 80.0),
        "fail_fast": bool (default: False),
        "verbose": bool (default: True)
    }

Output Schema:
    {
        "success": bool,
        "summary": {
            "total": int,
            "passed": int,
            "failed": int,
            "duration_seconds": float
        },
        "failures": [{
            "test_name": str,
            "file": str,
            "line": int,
            "error_type": str,
            "error_message": str
        }],
        "coverage": {
            "percentage": float,
            "missing_files": [str]
        },
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

from adw_modules.test_runner import TestRunner, result_to_dict


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run test suite and return failures only"
    )
    parser.add_argument(
        "--test-path",
        type=str,
        default=None,
        help="Optional path to specific tests"
    )
    parser.add_argument(
        "--test-type",
        type=str,
        choices=["pytest", "vitest", "all"],
        default="all",
        help="Which test framework to use"
    )
    parser.add_argument(
        "--coverage-threshold",
        type=float,
        default=80.0,
        help="Minimum coverage percentage required"
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first failure"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=True,
        help="Include verbose output for failures"
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
    Execute the test workflow.

    Args:
        params: Input parameters matching the input schema

    Returns:
        Output matching the output schema
    """
    # Extract parameters
    test_path = params.get("test_path")
    test_type = params.get("test_type", "all")
    coverage_threshold = params.get("coverage_threshold", 80.0)
    fail_fast = params.get("fail_fast", False)
    verbose = params.get("verbose", True)

    # Get project root (2 levels up from this file)
    project_root = Path(__file__).parent.parent

    # Initialize test runner
    runner = TestRunner(project_root)

    # Execute tests based on type
    if test_type == "pytest":
        result = runner.run_pytest(
            test_path=test_path,
            coverage_threshold=coverage_threshold,
            fail_fast=fail_fast,
            verbose=verbose
        )
        return result_to_dict(result)

    elif test_type == "vitest":
        result = runner.run_vitest(
            test_path=test_path,
            coverage_threshold=coverage_threshold,
            fail_fast=fail_fast
        )
        return result_to_dict(result)

    elif test_type == "all":
        results = runner.run_all(
            test_path=test_path,
            coverage_threshold=coverage_threshold,
            fail_fast=fail_fast
        )

        # Combine results
        total_tests = (results["pytest"].summary.total +
                      results["vitest"].summary.total)
        total_passed = (results["pytest"].summary.passed +
                       results["vitest"].summary.passed)
        total_failed = (results["pytest"].summary.failed +
                       results["vitest"].summary.failed)
        total_duration = (results["pytest"].summary.duration_seconds +
                         results["vitest"].summary.duration_seconds)

        all_failures = results["pytest"].failures + results["vitest"].failures

        # Use pytest coverage (more comprehensive)
        coverage = results["pytest"].coverage

        # Combine next steps
        next_steps = []
        if results["pytest"].failures:
            next_steps.extend([f"[pytest] {step}" for step in results["pytest"].next_steps[:2]])
        if results["vitest"].failures:
            next_steps.extend([f"[vitest] {step}" for step in results["vitest"].next_steps[:2]])
        if not next_steps:
            next_steps = ["All tests passed!"]

        success = total_failed == 0 and (not coverage or coverage.percentage >= coverage_threshold)

        return {
            "success": success,
            "summary": {
                "total": total_tests,
                "passed": total_passed,
                "failed": total_failed,
                "skipped": 0,
                "duration_seconds": total_duration
            },
            "failures": [result_to_dict(f) if hasattr(f, '__dict__') else f for f in all_failures],
            "coverage": {
                "percentage": coverage.percentage if coverage else 0.0,
                "lines_covered": coverage.lines_covered if coverage else 0,
                "lines_total": coverage.lines_total if coverage else 0,
                "missing_files": coverage.missing_files if coverage else []
            } if coverage else None,
            "next_steps": next_steps
        }

    else:
        return {
            "success": False,
            "error": {
                "type": "InvalidInputError",
                "message": f"Invalid test_type: {test_type}",
                "details": "Must be 'pytest', 'vitest', or 'all'"
            },
            "next_steps": ["Fix test_type parameter"]
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
            "test_path": args.test_path,
            "test_type": args.test_type,
            "coverage_threshold": args.coverage_threshold,
            "fail_fast": args.fail_fast,
            "verbose": args.verbose
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
                "details": "Unexpected error during test execution"
            },
            "next_steps": [f"Investigate {type(e).__name__}: {str(e)}"]
        }
        print(json.dumps(error_result, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
