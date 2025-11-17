#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ADW Test Generation Workflow - Auto-generate tests using templates

This workflow analyzes source code and generates tests automatically using
templates for simple functions and flagging complex functions for LLM review.

Usage:
    # As standalone tool
    uv run adw_test_gen_workflow.py \
      --target-path=app/server/core/new_feature.py \
      --coverage-goal=85 \
      --generation-strategy=hybrid

    # As invoked tool (from another ADW)
    from adw_modules.tool_registry import ToolRegistry
    registry = ToolRegistry()
    result = registry.invoke_tool("generate_tests_workflow", {
        "target_path": "app/server/core/new_feature.py",
        "coverage_goal": 85
    })

Input Schema:
    {
        "target_path": str (required),
        "test_type": "unit" | "integration" | "e2e" | "all",
        "coverage_goal": float (default: 85.0),
        "generation_strategy": "template" | "pynguin" | "hypothesis" | "hybrid",
        "max_llm_budget": int (default: 10000)
    }

Output Schema:
    {
        "success": bool,
        "auto_generated": {
            "count": int,
            "files": [str],
            "coverage_achieved": float,
            "generation_method": {
                "template": int,
                "pynguin": int,
                "hypothesis": int,
                "llm": int
            }
        },
        "needs_llm_review": [{
            "function": str,
            "file": str,
            "line": int,
            "reason": str,
            "complexity_score": float
        }],
        "coverage_gap": {
            "percentage_needed": float,
            "uncovered_lines": [int]
        },
        "tokens_used": int,
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

from adw_modules.test_generator import TestGenerator, result_to_dict


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Auto-generate tests using templates and analysis"
    )
    parser.add_argument(
        "--target-path",
        type=str,
        required=True,
        help="Path to file/directory to generate tests for"
    )
    parser.add_argument(
        "--test-type",
        type=str,
        choices=["unit", "integration", "e2e", "all"],
        default="unit",
        help="Type of tests to generate"
    )
    parser.add_argument(
        "--coverage-goal",
        type=float,
        default=85.0,
        help="Target coverage percentage"
    )
    parser.add_argument(
        "--generation-strategy",
        type=str,
        choices=["template", "pynguin", "hypothesis", "hybrid", "llm"],
        default="hybrid",
        help="Generation approach to use"
    )
    parser.add_argument(
        "--max-llm-budget",
        type=int,
        default=10000,
        help="Maximum tokens to spend on LLM-generated tests"
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
    Execute the test generation workflow.

    Args:
        params: Input parameters matching the input schema

    Returns:
        Output matching the output schema
    """
    # Extract parameters
    target_path_str = params.get("target_path")
    if not target_path_str:
        return {
            "success": False,
            "error": {
                "type": "InvalidInputError",
                "message": "target_path is required",
                "details": "Must provide a file or directory path"
            },
            "next_steps": ["Provide target_path parameter"]
        }

    test_type = params.get("test_type", "unit")
    coverage_goal = params.get("coverage_goal", 85.0)
    generation_strategy = params.get("generation_strategy", "hybrid")
    max_llm_budget = params.get("max_llm_budget", 10000)

    # Get project root (2 levels up from this file)
    project_root = Path(__file__).parent.parent

    # Resolve target path
    target_path = project_root / target_path_str
    if not target_path.exists():
        return {
            "success": False,
            "error": {
                "type": "FileNotFoundError",
                "message": f"Target path does not exist: {target_path}",
                "details": "Verify the path is correct"
            },
            "next_steps": [f"Check path exists: {target_path}"]
        }

    # Initialize test generator
    generator = TestGenerator(project_root)

    # Determine file type and generate appropriate tests
    if target_path.suffix == ".py":
        result = generator.generate_pytest_test(
            target_path=target_path,
            coverage_goal=coverage_goal
        )
    elif target_path.suffix in [".ts", ".tsx", ".js", ".jsx"]:
        result = generator.generate_vitest_test(
            target_path=target_path,
            coverage_goal=coverage_goal
        )
    else:
        return {
            "success": False,
            "error": {
                "type": "UnsupportedFileTypeError",
                "message": f"Unsupported file extension: {target_path.suffix}",
                "details": "Supported extensions: .py, .ts, .tsx, .js, .jsx"
            },
            "next_steps": ["Use a supported file type"]
        }

    return result_to_dict(result)


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
            "target_path": args.target_path,
            "test_type": args.test_type,
            "coverage_goal": args.coverage_goal,
            "generation_strategy": args.generation_strategy,
            "max_llm_budget": args.max_llm_budget
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
                "details": "Unexpected error during test generation"
            },
            "next_steps": [f"Investigate {type(e).__name__}: {str(e)}"]
        }
        print(json.dumps(error_result, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
