"""
Test Runner Module - Execute pytest/vitest and return compact results

This module handles the execution of test frameworks (pytest, vitest) and
parses their output to return only failures with precise error locations.

Key Features:
- Executes pytest with JSON output
- Executes vitest with JSON reporter
- Parses test results and extracts failures only
- Calculates coverage percentage
- Returns compact JSON format (reduces context by 90%)
"""

import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any
import os


@dataclass
class TestFailure:
    """Represents a single test failure."""
    test_name: str
    file: str
    line: int
    error_type: str
    error_message: str
    stack_trace: str = ""


@dataclass
class TestSummary:
    """Summary statistics for test run."""
    total: int
    passed: int
    failed: int
    skipped: int = 0
    duration_seconds: float = 0.0


@dataclass
class Coverage:
    """Coverage information."""
    percentage: float
    lines_covered: int = 0
    lines_total: int = 0
    missing_files: List[str] = None

    def __post_init__(self):
        if self.missing_files is None:
            self.missing_files = []


@dataclass
class TestResult:
    """Complete test run result."""
    success: bool
    summary: TestSummary
    failures: List[TestFailure]
    coverage: Optional[Coverage]
    next_steps: List[str]


class TestRunner:
    """Executes tests and returns compact results."""

    def __init__(self, project_root: Path):
        """
        Initialize test runner.

        Args:
            project_root: Path to project root directory
        """
        self.project_root = Path(project_root)

    def run_pytest(
        self,
        test_path: Optional[str] = None,
        coverage_threshold: float = 80.0,
        fail_fast: bool = False,
        verbose: bool = True
    ) -> TestResult:
        """
        Run pytest and return compact results.

        Args:
            test_path: Optional path to specific tests
            coverage_threshold: Minimum coverage percentage
            fail_fast: Stop on first failure
            verbose: Include verbose output for failures

        Returns:
            TestResult with failures only
        """
        # Build pytest command
        pytest_path = self.project_root / "app" / "server"
        cmd = ["uv", "run", "pytest"]

        if test_path:
            cmd.append(test_path)

        # Add coverage flags
        cmd.extend(["--cov=core", "--cov=routers", "--cov-report=json"])

        # Add JSON report for parsing
        json_report_path = pytest_path / ".pytest_report.json"
        cmd.extend([f"--json-report", f"--json-report-file={json_report_path}"])

        # Fail fast if requested
        if fail_fast:
            cmd.append("-x")

        # Verbose mode
        if verbose:
            cmd.append("-v")

        # Execute pytest
        try:
            # Set up environment with PYTHONPATH for worktree imports
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.project_root)

            result = subprocess.run(
                cmd,
                cwd=pytest_path,
                env=env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
        except subprocess.TimeoutExpired:
            return TestResult(
                success=False,
                summary=TestSummary(total=0, passed=0, failed=1),
                failures=[TestFailure(
                    test_name="pytest_execution",
                    file="",
                    line=0,
                    error_type="TimeoutError",
                    error_message="pytest execution timed out after 5 minutes"
                )],
                coverage=None,
                next_steps=["Investigate slow tests or infinite loops"]
            )

        # Parse JSON report
        failures = []
        summary = TestSummary(total=0, passed=0, failed=0)

        if json_report_path.exists():
            with open(json_report_path) as f:
                report = json.load(f)

            summary = TestSummary(
                total=report.get("summary", {}).get("total", 0),
                passed=report.get("summary", {}).get("passed", 0),
                failed=report.get("summary", {}).get("failed", 0),
                skipped=report.get("summary", {}).get("skipped", 0),
                duration_seconds=report.get("duration", 0.0)
            )

            # Extract failures
            for test in report.get("tests", []):
                if test.get("outcome") in ["failed", "error"]:
                    # Parse test location
                    nodeid = test.get("nodeid", "")
                    file_path = nodeid.split("::")[0] if "::" in nodeid else ""

                    # Get line number from call info
                    line = 0
                    if "call" in test and "longrepr" in test["call"]:
                        longrepr = test["call"]["longrepr"]
                        if isinstance(longrepr, str) and "line" in longrepr:
                            # Try to parse line number from traceback
                            for line_part in longrepr.split("\n"):
                                if file_path in line_part and ":" in line_part:
                                    try:
                                        line = int(line_part.split(":")[1].split(",")[0].strip())
                                        break
                                    except (ValueError, IndexError):
                                        pass

                    # Get error message
                    error_msg = ""
                    error_type = "AssertionError"
                    if "call" in test and "longrepr" in test["call"]:
                        longrepr = test["call"]["longrepr"]
                        if isinstance(longrepr, str):
                            error_msg = longrepr.split("\n")[-1] if "\n" in longrepr else longrepr
                            # Try to extract error type
                            if ":" in error_msg:
                                error_type = error_msg.split(":")[0].strip()

                    failures.append(TestFailure(
                        test_name=test.get("nodeid", "unknown"),
                        file=file_path,
                        line=line,
                        error_type=error_type,
                        error_message=error_msg or "Test failed",
                        stack_trace=test.get("call", {}).get("longrepr", "") if isinstance(test.get("call", {}).get("longrepr"), str) else ""
                    ))

        # Parse coverage
        coverage = None
        coverage_json_path = pytest_path / "coverage.json"
        if coverage_json_path.exists():
            with open(coverage_json_path) as f:
                cov_data = json.load(f)

            total_statements = cov_data.get("totals", {}).get("num_statements", 0)
            covered_statements = cov_data.get("totals", {}).get("covered_lines", 0)
            coverage_pct = cov_data.get("totals", {}).get("percent_covered", 0.0)

            # Find files with 0% coverage
            missing_files = []
            for file_path, file_data in cov_data.get("files", {}).items():
                if file_data.get("summary", {}).get("percent_covered", 100) == 0:
                    missing_files.append(file_path)

            coverage = Coverage(
                percentage=coverage_pct,
                lines_covered=covered_statements,
                lines_total=total_statements,
                missing_files=missing_files
            )

        # Generate next steps
        next_steps = []
        if failures:
            for f in failures[:3]:  # Only first 3 failures
                next_steps.append(f"Fix test failure in {f.file}:{f.line} - {f.error_type}")
        if coverage and coverage.percentage < coverage_threshold:
            next_steps.append(f"Increase coverage from {coverage.percentage:.1f}% to {coverage_threshold}%")
        if coverage and coverage.missing_files:
            next_steps.append(f"Add tests for {len(coverage.missing_files)} uncovered file(s)")

        success = summary.failed == 0 and (not coverage or coverage.percentage >= coverage_threshold)

        return TestResult(
            success=success,
            summary=summary,
            failures=failures,
            coverage=coverage,
            next_steps=next_steps if next_steps else ["All tests passed!"]
        )

    def run_vitest(
        self,
        test_path: Optional[str] = None,
        coverage_threshold: float = 80.0,
        fail_fast: bool = False
    ) -> TestResult:
        """
        Run vitest and return compact results.

        Args:
            test_path: Optional path to specific tests
            coverage_threshold: Minimum coverage percentage
            fail_fast: Stop on first failure

        Returns:
            TestResult with failures only
        """
        # Build vitest command
        vitest_path = self.project_root / "app" / "client"
        json_report_path = vitest_path / ".vitest_report.json"

        cmd = ["bun", "run", "vitest", "run", "--reporter=json"]

        if test_path:
            cmd.append(test_path)

        # Add coverage
        cmd.append("--coverage")

        # Fail fast
        if fail_fast:
            cmd.append("--bail=1")

        # Execute vitest
        try:
            result = subprocess.run(
                cmd,
                cwd=vitest_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            # Vitest outputs JSON to stdout with --reporter=json
            output = result.stdout

        except subprocess.TimeoutExpired:
            return TestResult(
                success=False,
                summary=TestSummary(total=0, passed=0, failed=1),
                failures=[TestFailure(
                    test_name="vitest_execution",
                    file="",
                    line=0,
                    error_type="TimeoutError",
                    error_message="vitest execution timed out after 5 minutes"
                )],
                coverage=None,
                next_steps=["Investigate slow tests or infinite loops"]
            )

        # Parse vitest output
        failures = []
        summary = TestSummary(total=0, passed=0, failed=0)

        try:
            # Parse JSON output
            report = json.loads(output)

            # Vitest JSON format: {testResults: [...], numTotalTests, numPassedTests, numFailedTests}
            summary = TestSummary(
                total=report.get("numTotalTests", 0),
                passed=report.get("numPassedTests", 0),
                failed=report.get("numFailedTests", 0),
                skipped=report.get("numPendingTests", 0),
                duration_seconds=report.get("testResults", [{}])[0].get("perfStats", {}).get("runtime", 0) / 1000 if report.get("testResults") else 0
            )

            # Extract failures
            for test_file in report.get("testResults", []):
                for assertion in test_file.get("assertionResults", []):
                    if assertion.get("status") in ["failed", "error"]:
                        failures.append(TestFailure(
                            test_name=assertion.get("title", "unknown"),
                            file=test_file.get("name", ""),
                            line=assertion.get("location", {}).get("line", 0),
                            error_type=assertion.get("failureMessages", ["Error"])[0].split(":")[0] if assertion.get("failureMessages") else "Error",
                            error_message=assertion.get("failureMessages", ["Test failed"])[0],
                            stack_trace="\n".join(assertion.get("failureMessages", []))
                        ))

        except json.JSONDecodeError:
            # Fallback: couldn't parse JSON
            summary = TestSummary(total=0, passed=0, failed=1)
            failures = [TestFailure(
                test_name="vitest_parsing",
                file="",
                line=0,
                error_type="ParseError",
                error_message="Could not parse vitest JSON output"
            )]

        # TODO: Parse vitest coverage (similar to pytest)
        coverage = None

        # Generate next steps
        next_steps = []
        if failures:
            for f in failures[:3]:
                next_steps.append(f"Fix test failure in {f.file}:{f.line}")

        success = summary.failed == 0

        return TestResult(
            success=success,
            summary=summary,
            failures=failures,
            coverage=coverage,
            next_steps=next_steps if next_steps else ["All tests passed!"]
        )

    def run_all(
        self,
        test_path: Optional[str] = None,
        coverage_threshold: float = 80.0,
        fail_fast: bool = False
    ) -> Dict[str, TestResult]:
        """
        Run both pytest and vitest.

        Args:
            test_path: Optional path to specific tests
            coverage_threshold: Minimum coverage percentage
            fail_fast: Stop on first failure

        Returns:
            Dict with 'pytest' and 'vitest' TestResult objects
        """
        results = {}

        # Run pytest
        pytest_result = self.run_pytest(test_path, coverage_threshold, fail_fast)
        results["pytest"] = pytest_result

        # Run vitest
        vitest_result = self.run_vitest(test_path, coverage_threshold, fail_fast)
        results["vitest"] = vitest_result

        return results


def result_to_dict(result: TestResult) -> Dict[str, Any]:
    """
    Convert TestResult to dictionary for JSON serialization.

    Args:
        result: TestResult object

    Returns:
        Dictionary representation
    """
    return {
        "success": result.success,
        "summary": asdict(result.summary),
        "failures": [asdict(f) for f in result.failures],
        "coverage": asdict(result.coverage) if result.coverage else None,
        "next_steps": result.next_steps
    }


# Example usage
if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Get project root (3 levels up from this file)
    project_root = Path(__file__).parent.parent.parent

    runner = TestRunner(project_root)

    # Run pytest
    print("Running pytest...")
    pytest_result = runner.run_pytest()
    print(json.dumps(result_to_dict(pytest_result), indent=2))

    print("\n" + "="*80 + "\n")

    # Run vitest
    print("Running vitest...")
    vitest_result = runner.run_vitest()
    print(json.dumps(result_to_dict(vitest_result), indent=2))
