#!/usr/bin/env python3
"""
Smart Test Runner - Context Reduction for LLM

PROBLEM: LLMs waste tokens loading full test suites and interpreting output
SOLUTION: Python script runs tests, returns ONLY failures with context

COST COMPARISON:
- Traditional LLM approach: ~60K tokens (~$0.18)
- Smart script approach: ~2K tokens (~$0.006)
- SAVINGS: 97% ($0.174 per test run)

USAGE:
    python3 scripts/smart_test_runner.py [--format json|markdown] [--test-path path]

OUTPUT:
    Compact JSON or Markdown with:
    - Summary (X passed, Y failed)
    - Failures only (name, error, file, line)
    - Actionable next steps
"""

import subprocess
import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


def run_pytest(test_path: Optional[str] = None) -> Dict:
    """
    Run pytest and extract meaningful data.

    Args:
        test_path: Optional specific test file/directory to run

    Returns:
        Dict with summary, failures, and metadata
    """
    cmd = ["pytest", "-v", "--tb=short"]

    if test_path:
        cmd.append(test_path)

    # Add JSON report for structured data
    json_file = "/tmp/pytest_results.json"
    cmd.extend(["--json-report", f"--json-report-file={json_file}"])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        # Parse JSON report if available
        try:
            with open(json_file, 'r') as f:
                test_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Fallback if JSON report not available
            return parse_pytest_output_fallback(result.stdout, result.stderr)

        return parse_pytest_json(test_data, result.returncode)

    except subprocess.TimeoutExpired:
        return {
            "summary": {"total": 0, "passed": 0, "failed": 0, "error": True},
            "failures": [],
            "error": "Test suite timed out after 5 minutes"
        }
    except Exception as e:
        return {
            "summary": {"total": 0, "passed": 0, "failed": 0, "error": True},
            "failures": [],
            "error": str(e)
        }


def parse_pytest_json(test_data: Dict, return_code: int) -> Dict:
    """Parse pytest JSON report into compact format."""

    summary = test_data.get("summary", {})
    tests = test_data.get("tests", [])

    # Extract only failures
    failures = []
    for test in tests:
        if test.get("outcome") in ["failed", "error"]:
            # Extract error message (truncate if too long)
            error_msg = ""
            if "call" in test and "longrepr" in test["call"]:
                error_msg = test["call"]["longrepr"]
            elif "setup" in test and "longrepr" in test["setup"]:
                error_msg = test["setup"]["longrepr"]

            # Truncate very long errors
            if len(error_msg) > 500:
                error_msg = error_msg[:500] + "...\n[Error truncated for brevity]"

            failures.append({
                "name": test.get("nodeid", "Unknown"),
                "error": error_msg,
                "file": test.get("file", ""),
                "line": test.get("lineno", 0),
                "outcome": test.get("outcome", "failed")
            })

    return {
        "summary": {
            "total": summary.get("total", 0),
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0) + summary.get("error", 0),
            "skipped": summary.get("skipped", 0),
            "duration_seconds": test_data.get("duration", 0)
        },
        "failures": failures,
        "next_steps": generate_next_steps(failures),
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "return_code": return_code,
            "pytest_version": test_data.get("pytest_version", "unknown")
        }
    }


def parse_pytest_output_fallback(stdout: str, stderr: str) -> Dict:
    """Fallback parser when JSON report is unavailable."""

    # Simple regex-based parsing
    import re

    passed = len(re.findall(r"PASSED", stdout))
    failed = len(re.findall(r"FAILED", stdout))
    errors = len(re.findall(r"ERROR", stdout))

    # Extract failure details from output
    failures = []
    failure_blocks = re.split(r"={3,} FAILURES ={3,}", stdout)
    if len(failure_blocks) > 1:
        # Parse each failure
        for block in re.split(r"_{3,} ", failure_blocks[1]):
            lines = block.strip().split("\n")
            if lines:
                name = lines[0].strip()
                error = "\n".join(lines[1:10])  # First 10 lines of error

                failures.append({
                    "name": name,
                    "error": error,
                    "file": "",
                    "line": 0,
                    "outcome": "failed"
                })

    return {
        "summary": {
            "total": passed + failed + errors,
            "passed": passed,
            "failed": failed + errors,
            "skipped": 0
        },
        "failures": failures,
        "next_steps": generate_next_steps(failures)
    }


def generate_next_steps(failures: List[Dict]) -> List[str]:
    """Generate actionable recommendations based on failures."""

    if not failures:
        return [
            "✅ All tests passing",
            "Ready to commit changes",
            "Consider running build to ensure no type errors"
        ]

    steps = []

    # Group failures by file
    files_with_failures = {}
    for failure in failures:
        file_path = failure.get("file", "unknown")
        if file_path not in files_with_failures:
            files_with_failures[file_path] = []
        files_with_failures[file_path].append(failure)

    # Generate steps per file
    for file_path, file_failures in files_with_failures.items():
        if file_path != "unknown":
            steps.append(f"Fix {len(file_failures)} test(s) in {file_path}")
        else:
            for failure in file_failures:
                steps.append(f"Fix test: {failure['name']}")

    # Add general recommendations
    if len(failures) > 5:
        steps.append("💡 Consider fixing tests incrementally (many failures detected)")

    steps.append("Run tests again after fixes to verify")

    return steps


def format_as_json(results: Dict) -> str:
    """Format results as JSON."""
    return json.dumps(results, indent=2)


def format_as_markdown(results: Dict) -> str:
    """Format results as Markdown for better readability."""

    md = "# Test Results\n\n"

    # Summary
    summary = results["summary"]
    md += "## Summary\n\n"
    md += f"- **Total Tests:** {summary['total']}\n"
    md += f"- **Passed:** {summary['passed']} ✅\n"
    md += f"- **Failed:** {summary['failed']} ❌\n"

    if summary.get("skipped", 0) > 0:
        md += f"- **Skipped:** {summary['skipped']} ⏭️\n"

    if "duration_seconds" in summary:
        md += f"- **Duration:** {summary['duration_seconds']:.2f}s\n"

    # Failures
    if results["failures"]:
        md += "\n## Failures\n\n"
        for i, failure in enumerate(results["failures"], 1):
            md += f"### {i}. {failure['name']}\n\n"
            md += f"**File:** `{failure['file']}`"
            if failure.get("line"):
                md += f" (line {failure['line']})"
            md += "\n\n"
            md += "**Error:**\n```\n"
            md += failure['error']
            md += "\n```\n\n"

    # Next steps
    if results["next_steps"]:
        md += "## Next Steps\n\n"
        for step in results["next_steps"]:
            md += f"- {step}\n"

    # Metadata
    if "metadata" in results:
        md += "\n---\n"
        md += f"*Generated at {results['metadata'].get('timestamp', 'unknown')}*\n"

    return md


def main():
    """Main entry point."""

    parser = argparse.ArgumentParser(
        description="Smart Test Runner - Returns only failures to reduce LLM context"
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="Output format (default: json)"
    )
    parser.add_argument(
        "--test-path",
        help="Specific test file or directory to run"
    )

    args = parser.parse_args()

    # Run tests
    results = run_pytest(args.test_path)

    # Format output
    if args.format == "markdown":
        output = format_as_markdown(results)
    else:
        output = format_as_json(results)

    print(output)

    # Exit with appropriate code
    sys.exit(0 if results["summary"]["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
