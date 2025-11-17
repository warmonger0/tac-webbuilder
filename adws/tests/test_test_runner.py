"""
Comprehensive test suite for test_runner.py module.

Tests cover:
- TestRunner class initialization and methods
- run_pytest() with success and failure scenarios
- run_vitest() with success and failure scenarios
- run_all() for combined execution
- Helper function result_to_dict()
- Edge cases: timeouts, parsing errors, missing files
- Fixtures for mock subprocess results
- File I/O operations with mocking
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open
from dataclasses import asdict
import subprocess
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from adw_modules.test_runner import (
    TestRunner,
    TestFailure,
    TestSummary,
    Coverage,
    TestResult,
    result_to_dict,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def project_root(tmp_path):
    """Create a mock project root directory structure."""
    project = tmp_path / "test_project"
    project.mkdir()
    (project / "app" / "server").mkdir(parents=True)
    (project / "app" / "client").mkdir(parents=True)
    return project


@pytest.fixture
def test_runner(project_root):
    """Create a TestRunner instance with mock project root."""
    return TestRunner(project_root)


@pytest.fixture
def pytest_success_report():
    """Sample successful pytest JSON report."""
    return {
        "summary": {
            "total": 10,
            "passed": 10,
            "failed": 0,
            "skipped": 0,
        },
        "duration": 5.23,
        "tests": [
            {
                "nodeid": "tests/test_module.py::TestClass::test_method",
                "outcome": "passed",
                "call": {"longrepr": ""},
            },
            {
                "nodeid": "tests/test_module.py::test_function",
                "outcome": "passed",
                "call": {"longrepr": ""},
            },
        ],
    }


@pytest.fixture
def pytest_failure_report():
    """Sample pytest JSON report with failures."""
    return {
        "summary": {
            "total": 5,
            "passed": 3,
            "failed": 2,
            "skipped": 0,
        },
        "duration": 2.15,
        "tests": [
            {
                "nodeid": "tests/test_module.py::test_pass",
                "outcome": "passed",
                "call": {"longrepr": ""},
            },
            {
                "nodeid": "tests/test_module.py::test_fail_1",
                "outcome": "failed",
                "call": {
                    "longrepr": """
tests/test_module.py:42: AssertionError
assert 1 == 2
AssertionError: assert 1 == 2
"""
                },
            },
            {
                "nodeid": "tests/test_module.py::test_fail_2",
                "outcome": "error",
                "call": {
                    "longrepr": """
tests/test_module.py:50: ValueError
ValueError: Invalid argument
"""
                },
            },
        ],
    }


@pytest.fixture
def coverage_report():
    """Sample coverage JSON report."""
    return {
        "totals": {
            "num_statements": 500,
            "covered_lines": 450,
            "percent_covered": 90.0,
        },
        "files": {
            "src/module.py": {
                "summary": {"percent_covered": 95},
            },
            "src/untested.py": {
                "summary": {"percent_covered": 0},
            },
        },
    }


@pytest.fixture
def vitest_success_report():
    """Sample successful vitest JSON report."""
    return {
        "numTotalTests": 8,
        "numPassedTests": 8,
        "numFailedTests": 0,
        "numPendingTests": 0,
        "testResults": [
            {
                "name": "tests/component.test.ts",
                "assertionResults": [
                    {
                        "title": "renders component",
                        "status": "passed",
                        "failureMessages": [],
                    },
                    {
                        "title": "handles click",
                        "status": "passed",
                        "failureMessages": [],
                    },
                ],
                "perfStats": {"runtime": 1500},
            }
        ],
    }


@pytest.fixture
def vitest_failure_report():
    """Sample vitest JSON report with failures."""
    return {
        "numTotalTests": 5,
        "numPassedTests": 3,
        "numFailedTests": 2,
        "numPendingTests": 0,
        "testResults": [
            {
                "name": "tests/component.test.ts",
                "assertionResults": [
                    {
                        "title": "renders component",
                        "status": "passed",
                        "failureMessages": [],
                    },
                    {
                        "title": "fails assertion",
                        "status": "failed",
                        "location": {"line": 25},
                        "failureMessages": [
                            "AssertionError: expected true to be false"
                        ],
                    },
                    {
                        "title": "throws error",
                        "status": "error",
                        "location": {"line": 35},
                        "failureMessages": [
                            "TypeError: Cannot read property 'name' of undefined"
                        ],
                    },
                ],
                "perfStats": {"runtime": 1200},
            }
        ],
    }


@pytest.fixture
def invalid_json_output():
    """Invalid JSON output for parsing error scenarios."""
    return "This is not valid JSON { invalid }"


# ============================================================================
# TestRunner Initialization Tests
# ============================================================================


class TestTestRunnerInit:
    """Test TestRunner initialization."""

    def test_init_with_path_object(self, project_root):
        """Test initialization with Path object."""
        runner = TestRunner(project_root)
        assert runner.project_root == project_root

    def test_init_with_string_path(self, project_root):
        """Test initialization with string path."""
        runner = TestRunner(str(project_root))
        assert runner.project_root == project_root

    def test_project_root_is_path_object(self, project_root):
        """Test that project_root is converted to Path object."""
        runner = TestRunner(project_root)
        assert isinstance(runner.project_root, Path)


# ============================================================================
# run_pytest() Tests - Success Cases
# ============================================================================


class TestRunPytestSuccess:
    """Test successful pytest execution."""

    @patch("subprocess.run")
    def test_run_pytest_success(self, mock_run, test_runner, pytest_success_report, tmp_path):
        """Test successful pytest execution with all tests passing."""
        # Setup
        pytest_path = test_runner.project_root / "app" / "server"
        json_report_path = pytest_path / ".pytest_report.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)

        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        # Write report file
        with open(json_report_path, "w") as f:
            json.dump(pytest_success_report, f)

        # Execute
        result = test_runner.run_pytest()

        # Verify
        assert result.success is True
        assert result.summary.total == 10
        assert result.summary.passed == 10
        assert result.summary.failed == 0
        assert len(result.failures) == 0
        assert "All tests passed!" in result.next_steps

    @patch("subprocess.run")
    def test_run_pytest_with_test_path(self, mock_run, test_runner, pytest_success_report, tmp_path):
        """Test pytest with specific test path."""
        pytest_path = test_runner.project_root / "app" / "server"
        json_report_path = pytest_path / ".pytest_report.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)

        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        with open(json_report_path, "w") as f:
            json.dump(pytest_success_report, f)

        # Execute with specific test path
        result = test_runner.run_pytest(test_path="tests/test_specific.py")

        # Verify command includes test path
        call_args = mock_run.call_args
        assert "tests/test_specific.py" in call_args[0][0]
        assert result.success is True

    @patch("subprocess.run")
    def test_run_pytest_fail_fast_flag(self, mock_run, test_runner, pytest_success_report, tmp_path):
        """Test pytest with fail_fast enabled."""
        pytest_path = test_runner.project_root / "app" / "server"
        json_report_path = pytest_path / ".pytest_report.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)

        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        with open(json_report_path, "w") as f:
            json.dump(pytest_success_report, f)

        # Execute with fail_fast
        result = test_runner.run_pytest(fail_fast=True)

        # Verify command includes -x flag
        call_args = mock_run.call_args
        assert "-x" in call_args[0][0]

    @patch("subprocess.run")
    def test_run_pytest_verbose_flag(self, mock_run, test_runner, pytest_success_report, tmp_path):
        """Test pytest with verbose enabled."""
        pytest_path = test_runner.project_root / "app" / "server"
        json_report_path = pytest_path / ".pytest_report.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)

        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        with open(json_report_path, "w") as f:
            json.dump(pytest_success_report, f)

        # Execute with verbose
        result = test_runner.run_pytest(verbose=True)

        # Verify command includes -v flag
        call_args = mock_run.call_args
        assert "-v" in call_args[0][0]

    @patch("subprocess.run")
    def test_run_pytest_with_coverage(self, mock_run, test_runner, pytest_success_report, coverage_report, tmp_path):
        """Test pytest with coverage report."""
        pytest_path = test_runner.project_root / "app" / "server"
        json_report_path = pytest_path / ".pytest_report.json"
        coverage_path = pytest_path / "coverage.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)

        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        with open(json_report_path, "w") as f:
            json.dump(pytest_success_report, f)
        with open(coverage_path, "w") as f:
            json.dump(coverage_report, f)

        # Execute
        result = test_runner.run_pytest()

        # Verify coverage
        assert result.coverage is not None
        assert result.coverage.percentage == 90.0
        assert result.coverage.lines_covered == 450
        assert result.coverage.lines_total == 500

    @patch("subprocess.run")
    def test_run_pytest_coverage_above_threshold(self, mock_run, test_runner, pytest_success_report, coverage_report, tmp_path):
        """Test pytest with coverage above threshold."""
        pytest_path = test_runner.project_root / "app" / "server"
        json_report_path = pytest_path / ".pytest_report.json"
        coverage_path = pytest_path / "coverage.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)

        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        with open(json_report_path, "w") as f:
            json.dump(pytest_success_report, f)
        with open(coverage_path, "w") as f:
            json.dump(coverage_report, f)

        # Execute with threshold
        result = test_runner.run_pytest(coverage_threshold=85.0)

        # Coverage is 90%, threshold is 85%, so success
        assert result.success is True

    @patch("subprocess.run")
    def test_run_pytest_identifies_uncovered_files(self, mock_run, test_runner, pytest_success_report, coverage_report, tmp_path):
        """Test that pytest identifies files with zero coverage."""
        pytest_path = test_runner.project_root / "app" / "server"
        json_report_path = pytest_path / ".pytest_report.json"
        coverage_path = pytest_path / "coverage.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)

        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        with open(json_report_path, "w") as f:
            json.dump(pytest_success_report, f)
        with open(coverage_path, "w") as f:
            json.dump(coverage_report, f)

        # Execute
        result = test_runner.run_pytest()

        # Verify uncovered files are identified
        assert result.coverage.missing_files == ["src/untested.py"]


# ============================================================================
# run_pytest() Tests - Failure Cases
# ============================================================================


class TestRunPytestFailures:
    """Test pytest execution with failures."""

    @patch("subprocess.run")
    def test_run_pytest_with_failures(self, mock_run, test_runner, pytest_failure_report, tmp_path):
        """Test pytest execution with test failures."""
        pytest_path = test_runner.project_root / "app" / "server"
        json_report_path = pytest_path / ".pytest_report.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)

        mock_run.return_value = Mock(stdout="", stderr="", returncode=1)

        with open(json_report_path, "w") as f:
            json.dump(pytest_failure_report, f)

        # Execute
        result = test_runner.run_pytest()

        # Verify
        assert result.success is False
        assert result.summary.failed == 2
        assert result.summary.passed == 3
        assert len(result.failures) == 2

    @patch("subprocess.run")
    def test_run_pytest_failure_extraction(self, mock_run, test_runner, pytest_failure_report, tmp_path):
        """Test that failures are correctly extracted from report."""
        pytest_path = test_runner.project_root / "app" / "server"
        json_report_path = pytest_path / ".pytest_report.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)

        mock_run.return_value = Mock(stdout="", stderr="", returncode=1)

        with open(json_report_path, "w") as f:
            json.dump(pytest_failure_report, f)

        # Execute
        result = test_runner.run_pytest()

        # Verify first failure
        assert result.failures[0].test_name == "tests/test_module.py::test_fail_1"
        assert "test_module.py" in result.failures[0].file
        assert result.failures[0].error_type == "AssertionError"

    @patch("subprocess.run")
    def test_run_pytest_generates_next_steps_for_failures(self, mock_run, test_runner, pytest_failure_report, tmp_path):
        """Test that next steps are generated for failures."""
        pytest_path = test_runner.project_root / "app" / "server"
        json_report_path = pytest_path / ".pytest_report.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)

        mock_run.return_value = Mock(stdout="", stderr="", returncode=1)

        with open(json_report_path, "w") as f:
            json.dump(pytest_failure_report, f)

        # Execute
        result = test_runner.run_pytest()

        # Verify next steps include fixes
        assert any("Fix test failure" in step for step in result.next_steps)

    @patch("subprocess.run")
    def test_run_pytest_timeout(self, mock_run, test_runner):
        """Test pytest timeout handling."""
        mock_run.side_effect = subprocess.TimeoutExpired("pytest", 300)

        # Execute
        result = test_runner.run_pytest()

        # Verify timeout handling
        assert result.success is False
        assert result.summary.failed == 1
        assert len(result.failures) == 1
        assert result.failures[0].error_type == "TimeoutError"
        assert "timed out" in result.failures[0].error_message

    @patch("subprocess.run")
    def test_run_pytest_missing_json_report(self, mock_run, test_runner):
        """Test pytest handling when JSON report is missing."""
        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        # Execute (report file doesn't exist)
        result = test_runner.run_pytest()

        # Should handle gracefully
        assert result.summary.total == 0
        assert result.summary.passed == 0

    @patch("subprocess.run")
    def test_run_pytest_coverage_below_threshold(self, mock_run, test_runner, pytest_success_report, coverage_report, tmp_path):
        """Test pytest failure when coverage is below threshold."""
        pytest_path = test_runner.project_root / "app" / "server"
        json_report_path = pytest_path / ".pytest_report.json"
        coverage_path = pytest_path / "coverage.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)

        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        with open(json_report_path, "w") as f:
            json.dump(pytest_success_report, f)
        with open(coverage_path, "w") as f:
            json.dump(coverage_report, f)

        # Execute with high threshold
        result = test_runner.run_pytest(coverage_threshold=95.0)

        # Success is False because coverage (90%) < threshold (95%)
        assert result.success is False
        assert any("Increase coverage" in step for step in result.next_steps)


# ============================================================================
# run_vitest() Tests - Success Cases
# ============================================================================


class TestRunVitestSuccess:
    """Test successful vitest execution."""

    @patch("subprocess.run")
    def test_run_vitest_success(self, mock_run, test_runner, vitest_success_report):
        """Test successful vitest execution."""
        mock_run.return_value = Mock(
            stdout=json.dumps(vitest_success_report),
            stderr="",
            returncode=0
        )

        # Execute
        result = test_runner.run_vitest()

        # Verify
        assert result.success is True
        assert result.summary.total == 8
        assert result.summary.passed == 8
        assert result.summary.failed == 0
        assert len(result.failures) == 0

    @patch("subprocess.run")
    def test_run_vitest_with_test_path(self, mock_run, test_runner, vitest_success_report):
        """Test vitest with specific test path."""
        mock_run.return_value = Mock(
            stdout=json.dumps(vitest_success_report),
            stderr="",
            returncode=0
        )

        # Execute with test path
        result = test_runner.run_vitest(test_path="tests/component.test.ts")

        # Verify command includes test path
        call_args = mock_run.call_args
        assert "tests/component.test.ts" in call_args[0][0]

    @patch("subprocess.run")
    def test_run_vitest_fail_fast_flag(self, mock_run, test_runner, vitest_success_report):
        """Test vitest with fail_fast enabled."""
        mock_run.return_value = Mock(
            stdout=json.dumps(vitest_success_report),
            stderr="",
            returncode=0
        )

        # Execute with fail_fast
        result = test_runner.run_vitest(fail_fast=True)

        # Verify command includes bail flag
        call_args = mock_run.call_args
        assert "--bail=1" in call_args[0][0]

    @patch("subprocess.run")
    def test_run_vitest_coverage_flag(self, mock_run, test_runner, vitest_success_report):
        """Test that vitest includes coverage flag."""
        mock_run.return_value = Mock(
            stdout=json.dumps(vitest_success_report),
            stderr="",
            returncode=0
        )

        # Execute
        result = test_runner.run_vitest()

        # Verify command includes coverage
        call_args = mock_run.call_args
        assert "--coverage" in call_args[0][0]


# ============================================================================
# run_vitest() Tests - Failure Cases
# ============================================================================


class TestRunVitestFailures:
    """Test vitest execution with failures."""

    @patch("subprocess.run")
    def test_run_vitest_with_failures(self, mock_run, test_runner, vitest_failure_report):
        """Test vitest execution with test failures."""
        mock_run.return_value = Mock(
            stdout=json.dumps(vitest_failure_report),
            stderr="",
            returncode=1
        )

        # Execute
        result = test_runner.run_vitest()

        # Verify
        assert result.success is False
        assert result.summary.failed == 2
        assert result.summary.passed == 3
        assert len(result.failures) == 2

    @patch("subprocess.run")
    def test_run_vitest_failure_extraction(self, mock_run, test_runner, vitest_failure_report):
        """Test that vitest failures are correctly extracted."""
        mock_run.return_value = Mock(
            stdout=json.dumps(vitest_failure_report),
            stderr="",
            returncode=1
        )

        # Execute
        result = test_runner.run_vitest()

        # Verify failures
        assert result.failures[0].test_name == "fails assertion"
        assert "component.test.ts" in result.failures[0].file
        assert result.failures[0].line == 25

    @patch("subprocess.run")
    def test_run_vitest_timeout(self, mock_run, test_runner):
        """Test vitest timeout handling."""
        mock_run.side_effect = subprocess.TimeoutExpired("vitest", 300)

        # Execute
        result = test_runner.run_vitest()

        # Verify timeout handling
        assert result.success is False
        assert result.summary.failed == 1
        assert result.failures[0].error_type == "TimeoutError"

    @patch("subprocess.run")
    def test_run_vitest_invalid_json_output(self, mock_run, test_runner):
        """Test vitest handling of invalid JSON output."""
        mock_run.return_value = Mock(
            stdout="This is not valid JSON { invalid }",
            stderr="",
            returncode=1
        )

        # Execute
        result = test_runner.run_vitest()

        # Should handle gracefully with parse error
        assert result.success is False
        assert len(result.failures) == 1
        assert result.failures[0].error_type == "ParseError"

    @patch("subprocess.run")
    def test_run_vitest_empty_output(self, mock_run, test_runner):
        """Test vitest handling of empty output."""
        mock_run.return_value = Mock(
            stdout="",
            stderr="",
            returncode=1
        )

        # Execute
        result = test_runner.run_vitest()

        # Should handle gracefully
        assert result.success is False


# ============================================================================
# run_all() Tests
# ============================================================================


class TestRunAll:
    """Test run_all() method."""

    @patch("TestRunner.run_pytest")
    @patch("TestRunner.run_vitest")
    def test_run_all_both_success(self, mock_vitest, mock_pytest, test_runner):
        """Test run_all with both pytest and vitest succeeding."""
        pytest_result = TestResult(
            success=True,
            summary=TestSummary(total=10, passed=10, failed=0),
            failures=[],
            coverage=Coverage(percentage=90.0),
            next_steps=["All tests passed!"]
        )
        vitest_result = TestResult(
            success=True,
            summary=TestSummary(total=8, passed=8, failed=0),
            failures=[],
            coverage=None,
            next_steps=["All tests passed!"]
        )

        mock_pytest.return_value = pytest_result
        mock_vitest.return_value = vitest_result

        # Execute
        results = test_runner.run_all()

        # Verify both results are present
        assert "pytest" in results
        assert "vitest" in results
        assert results["pytest"].success is True
        assert results["vitest"].success is True

    @patch("TestRunner.run_pytest")
    @patch("TestRunner.run_vitest")
    def test_run_all_pytest_fails(self, mock_vitest, mock_pytest, test_runner):
        """Test run_all with pytest failing."""
        pytest_result = TestResult(
            success=False,
            summary=TestSummary(total=10, passed=8, failed=2),
            failures=[
                TestFailure(
                    test_name="test_fail",
                    file="test_module.py",
                    line=42,
                    error_type="AssertionError",
                    error_message="assert 1 == 2"
                )
            ],
            coverage=None,
            next_steps=["Fix test failures"]
        )
        vitest_result = TestResult(
            success=True,
            summary=TestSummary(total=8, passed=8, failed=0),
            failures=[],
            coverage=None,
            next_steps=["All tests passed!"]
        )

        mock_pytest.return_value = pytest_result
        mock_vitest.return_value = vitest_result

        # Execute
        results = test_runner.run_all()

        # Verify
        assert results["pytest"].success is False
        assert results["vitest"].success is True

    @patch("TestRunner.run_pytest")
    @patch("TestRunner.run_vitest")
    def test_run_all_with_test_path(self, mock_vitest, mock_pytest, test_runner):
        """Test run_all passes test_path to both runners."""
        pytest_result = TestResult(
            success=True,
            summary=TestSummary(total=1, passed=1, failed=0),
            failures=[],
            coverage=None,
            next_steps=["All tests passed!"]
        )
        vitest_result = TestResult(
            success=True,
            summary=TestSummary(total=1, passed=1, failed=0),
            failures=[],
            coverage=None,
            next_steps=["All tests passed!"]
        )

        mock_pytest.return_value = pytest_result
        mock_vitest.return_value = vitest_result

        # Execute
        test_runner.run_all(test_path="tests/specific.py")

        # Verify test_path is passed to both
        mock_pytest.assert_called_once()
        mock_vitest.assert_called_once()

    @patch("TestRunner.run_pytest")
    @patch("TestRunner.run_vitest")
    def test_run_all_with_coverage_threshold(self, mock_vitest, mock_pytest, test_runner):
        """Test run_all passes coverage_threshold to both runners."""
        pytest_result = TestResult(
            success=True,
            summary=TestSummary(total=10, passed=10, failed=0),
            failures=[],
            coverage=None,
            next_steps=["All tests passed!"]
        )
        vitest_result = TestResult(
            success=True,
            summary=TestSummary(total=8, passed=8, failed=0),
            failures=[],
            coverage=None,
            next_steps=["All tests passed!"]
        )

        mock_pytest.return_value = pytest_result
        mock_vitest.return_value = vitest_result

        # Execute
        test_runner.run_all(coverage_threshold=85.0)

        # Verify coverage_threshold is passed
        assert mock_pytest.call_args[1]["coverage_threshold"] == 85.0


# ============================================================================
# result_to_dict() Tests
# ============================================================================


class TestResultToDict:
    """Test result_to_dict helper function."""

    def test_result_to_dict_success(self):
        """Test converting successful TestResult to dict."""
        result = TestResult(
            success=True,
            summary=TestSummary(total=10, passed=10, failed=0),
            failures=[],
            coverage=Coverage(percentage=90.0),
            next_steps=["All tests passed!"]
        )

        result_dict = result_to_dict(result)

        # Verify structure
        assert isinstance(result_dict, dict)
        assert result_dict["success"] is True
        assert result_dict["summary"]["total"] == 10
        assert result_dict["summary"]["passed"] == 10
        assert result_dict["failures"] == []
        assert result_dict["coverage"]["percentage"] == 90.0

    def test_result_to_dict_with_failures(self):
        """Test converting TestResult with failures to dict."""
        failure = TestFailure(
            test_name="test_fail",
            file="test_module.py",
            line=42,
            error_type="AssertionError",
            error_message="assert 1 == 2",
            stack_trace="traceback here"
        )
        result = TestResult(
            success=False,
            summary=TestSummary(total=5, passed=3, failed=2),
            failures=[failure],
            coverage=None,
            next_steps=["Fix test failure"]
        )

        result_dict = result_to_dict(result)

        # Verify failure details
        assert len(result_dict["failures"]) == 1
        assert result_dict["failures"][0]["test_name"] == "test_fail"
        assert result_dict["failures"][0]["line"] == 42
        assert result_dict["failures"][0]["error_type"] == "AssertionError"

    def test_result_to_dict_no_coverage(self):
        """Test converting TestResult with no coverage to dict."""
        result = TestResult(
            success=True,
            summary=TestSummary(total=5, passed=5, failed=0),
            failures=[],
            coverage=None,
            next_steps=["All tests passed!"]
        )

        result_dict = result_to_dict(result)

        # Verify coverage is None
        assert result_dict["coverage"] is None

    def test_result_to_dict_json_serializable(self):
        """Test that result_to_dict output is JSON serializable."""
        result = TestResult(
            success=True,
            summary=TestSummary(total=10, passed=10, failed=0, skipped=0, duration_seconds=5.23),
            failures=[],
            coverage=Coverage(percentage=90.0, lines_covered=450, lines_total=500, missing_files=["src/uncovered.py"]),
            next_steps=["All tests passed!"]
        )

        result_dict = result_to_dict(result)

        # Should be JSON serializable
        json_str = json.dumps(result_dict)
        parsed = json.loads(json_str)
        assert parsed["success"] is True
        assert parsed["coverage"]["percentage"] == 90.0


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    @patch("subprocess.run")
    def test_pytest_with_empty_failures_list(self, mock_run, test_runner, tmp_path):
        """Test pytest handling of empty failures list."""
        pytest_path = test_runner.project_root / "app" / "server"
        json_report_path = pytest_path / ".pytest_report.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "summary": {"total": 3, "passed": 3, "failed": 0, "skipped": 0},
            "duration": 1.5,
            "tests": []
        }

        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        with open(json_report_path, "w") as f:
            json.dump(report, f)

        # Execute
        result = test_runner.run_pytest()

        # Verify
        assert result.summary.total == 3
        assert len(result.failures) == 0

    @patch("subprocess.run")
    def test_pytest_malformed_longrepr(self, mock_run, test_runner, tmp_path):
        """Test pytest handling of malformed longrepr."""
        pytest_path = test_runner.project_root / "app" / "server"
        json_report_path = pytest_path / ".pytest_report.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "summary": {"total": 1, "passed": 0, "failed": 1, "skipped": 0},
            "duration": 0.5,
            "tests": [
                {
                    "nodeid": "test_module.py::test_fail",
                    "outcome": "failed",
                    "call": {
                        "longrepr": {"some": "object"}  # Not a string
                    }
                }
            ]
        }

        mock_run.return_value = Mock(stdout="", stderr="", returncode=1)

        with open(json_report_path, "w") as f:
            json.dump(report, f)

        # Execute (should not crash)
        result = test_runner.run_pytest()

        # Verify it handles gracefully
        assert result.success is False
        assert len(result.failures) == 1

    @patch("subprocess.run")
    def test_pytest_missing_nodeid(self, mock_run, test_runner, tmp_path):
        """Test pytest handling of missing nodeid."""
        pytest_path = test_runner.project_root / "app" / "server"
        json_report_path = pytest_path / ".pytest_report.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "summary": {"total": 1, "passed": 0, "failed": 1, "skipped": 0},
            "duration": 0.5,
            "tests": [
                {
                    "outcome": "failed",
                    "call": {"longrepr": "Error occurred"}
                    # Missing nodeid
                }
            ]
        }

        mock_run.return_value = Mock(stdout="", stderr="", returncode=1)

        with open(json_report_path, "w") as f:
            json.dump(report, f)

        # Execute
        result = test_runner.run_pytest()

        # Verify fallback to "unknown"
        assert result.failures[0].test_name == "unknown"

    @patch("subprocess.run")
    def test_vitest_missing_failure_messages(self, mock_run, test_runner):
        """Test vitest handling of missing failureMessages."""
        report = {
            "numTotalTests": 1,
            "numPassedTests": 0,
            "numFailedTests": 1,
            "numPendingTests": 0,
            "testResults": [
                {
                    "name": "test.ts",
                    "assertionResults": [
                        {
                            "title": "test fails",
                            "status": "failed",
                            "location": {"line": 10}
                            # Missing failureMessages
                        }
                    ],
                    "perfStats": {"runtime": 100}
                }
            ]
        }

        mock_run.return_value = Mock(
            stdout=json.dumps(report),
            stderr="",
            returncode=1
        )

        # Execute
        result = test_runner.run_vitest()

        # Verify fallback
        assert result.failures[0].error_message == "Test failed"

    @patch("subprocess.run")
    def test_vitest_missing_location(self, mock_run, test_runner):
        """Test vitest handling of missing location."""
        report = {
            "numTotalTests": 1,
            "numPassedTests": 0,
            "numFailedTests": 1,
            "numPendingTests": 0,
            "testResults": [
                {
                    "name": "test.ts",
                    "assertionResults": [
                        {
                            "title": "test fails",
                            "status": "failed",
                            "failureMessages": ["Error: something"]
                            # Missing location
                        }
                    ],
                    "perfStats": {"runtime": 100}
                }
            ]
        }

        mock_run.return_value = Mock(
            stdout=json.dumps(report),
            stderr="",
            returncode=1
        )

        # Execute
        result = test_runner.run_vitest()

        # Verify line defaults to 0
        assert result.failures[0].line == 0

    @patch("subprocess.run")
    def test_pytest_coverage_no_files_key(self, mock_run, test_runner, tmp_path):
        """Test pytest coverage handling when files key is missing."""
        pytest_path = test_runner.project_root / "app" / "server"
        json_report_path = pytest_path / ".pytest_report.json"
        coverage_path = pytest_path / "coverage.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)

        test_report = {
            "summary": {"total": 1, "passed": 1, "failed": 0, "skipped": 0},
            "duration": 0.5,
            "tests": []
        }

        coverage = {
            "totals": {
                "num_statements": 100,
                "covered_lines": 80,
                "percent_covered": 80.0
            }
            # Missing files key
        }

        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        with open(json_report_path, "w") as f:
            json.dump(test_report, f)
        with open(coverage_path, "w") as f:
            json.dump(coverage, f)

        # Execute (should not crash)
        result = test_runner.run_pytest()

        # Verify coverage is still parsed
        assert result.coverage is not None
        assert result.coverage.percentage == 80.0
        assert result.coverage.missing_files == []

    @patch("subprocess.run")
    def test_pytest_parses_line_number_from_traceback(self, mock_run, test_runner, tmp_path):
        """Test pytest correctly parses line numbers from traceback."""
        pytest_path = test_runner.project_root / "app" / "server"
        json_report_path = pytest_path / ".pytest_report.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "summary": {"total": 1, "passed": 0, "failed": 1, "skipped": 0},
            "duration": 0.5,
            "tests": [
                {
                    "nodeid": "tests/test_module.py::test_fail",
                    "outcome": "failed",
                    "call": {
                        "longrepr": """tests/test_module.py:42: AssertionError
def test_something():
>   assert False
E   AssertionError: assert False"""
                    }
                }
            ]
        }

        mock_run.return_value = Mock(stdout="", stderr="", returncode=1)

        with open(json_report_path, "w") as f:
            json.dump(report, f)

        # Execute
        result = test_runner.run_pytest()

        # Verify line number is extracted
        assert result.failures[0].line == 42

    @patch("subprocess.run")
    def test_pytest_generates_three_failure_steps(self, mock_run, test_runner, tmp_path):
        """Test that only first 3 failures generate next steps."""
        pytest_path = test_runner.project_root / "app" / "server"
        json_report_path = pytest_path / ".pytest_report.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "summary": {"total": 5, "passed": 1, "failed": 4, "skipped": 0},
            "duration": 1.0,
            "tests": [
                {
                    "nodeid": f"tests/test_module.py::test_fail_{i}",
                    "outcome": "failed",
                    "call": {"longrepr": f"Error {i}"}
                }
                for i in range(4)
            ]
        }

        mock_run.return_value = Mock(stdout="", stderr="", returncode=1)

        with open(json_report_path, "w") as f:
            json.dump(report, f)

        # Execute
        result = test_runner.run_pytest()

        # Verify only 3 next steps for failures
        failure_steps = [s for s in result.next_steps if "Fix test failure" in s]
        assert len(failure_steps) == 3

    def test_coverage_post_init(self):
        """Test Coverage dataclass post_init."""
        coverage = Coverage(percentage=85.0)
        assert coverage.missing_files == []

    def test_test_failure_defaults(self):
        """Test TestFailure dataclass defaults."""
        failure = TestFailure(
            test_name="test",
            file="test.py",
            line=10,
            error_type="Error",
            error_message="Failed"
        )
        assert failure.stack_trace == ""

    def test_test_summary_defaults(self):
        """Test TestSummary dataclass defaults."""
        summary = TestSummary(total=5, passed=5, failed=0)
        assert summary.skipped == 0
        assert summary.duration_seconds == 0.0


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for TestRunner."""

    @patch("subprocess.run")
    def test_complete_pytest_workflow(self, mock_run, test_runner, pytest_failure_report, coverage_report, tmp_path):
        """Test complete pytest workflow with failures and coverage."""
        pytest_path = test_runner.project_root / "app" / "server"
        json_report_path = pytest_path / ".pytest_report.json"
        coverage_path = pytest_path / "coverage.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)

        mock_run.return_value = Mock(stdout="", stderr="", returncode=1)

        with open(json_report_path, "w") as f:
            json.dump(pytest_failure_report, f)
        with open(coverage_path, "w") as f:
            json.dump(coverage_report, f)

        # Execute
        result = test_runner.run_pytest(coverage_threshold=85.0)

        # Verify complete result
        assert result.success is False  # Has failures and missing files
        assert result.summary.failed == 2
        assert result.coverage.percentage == 90.0
        assert len(result.failures) == 2
        assert len(result.next_steps) >= 3

    @patch("subprocess.run")
    def test_complete_vitest_workflow(self, mock_run, test_runner, vitest_failure_report):
        """Test complete vitest workflow with failures."""
        mock_run.return_value = Mock(
            stdout=json.dumps(vitest_failure_report),
            stderr="",
            returncode=1
        )

        # Execute
        result = test_runner.run_vitest()

        # Verify complete result
        assert result.success is False
        assert result.summary.failed == 2
        assert len(result.failures) == 2
        assert all(f.file == "tests/component.test.ts" for f in result.failures)

    def test_result_serialization_roundtrip(self):
        """Test that result can be serialized and deserialized."""
        original = TestResult(
            success=False,
            summary=TestSummary(total=5, passed=3, failed=2, skipped=0, duration_seconds=1.5),
            failures=[
                TestFailure(
                    test_name="test_fail",
                    file="test_module.py",
                    line=42,
                    error_type="AssertionError",
                    error_message="assert 1 == 2",
                    stack_trace="traceback"
                )
            ],
            coverage=Coverage(percentage=85.0, lines_covered=850, lines_total=1000, missing_files=[]),
            next_steps=["Fix failure"]
        )

        # Convert to dict and back
        result_dict = result_to_dict(original)
        json_str = json.dumps(result_dict)
        parsed = json.loads(json_str)

        # Verify structure is preserved
        assert parsed["success"] is False
        assert parsed["summary"]["failed"] == 2
        assert len(parsed["failures"]) == 1
        assert parsed["coverage"]["percentage"] == 85.0


# ============================================================================
# Command Construction Tests
# ============================================================================


class TestCommandConstruction:
    """Test that commands are constructed correctly."""

    @patch("subprocess.run")
    def test_pytest_command_structure(self, mock_run, test_runner, pytest_success_report, tmp_path):
        """Test pytest command is correctly constructed."""
        pytest_path = test_runner.project_root / "app" / "server"
        json_report_path = pytest_path / ".pytest_report.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)

        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        with open(json_report_path, "w") as f:
            json.dump(pytest_success_report, f)

        # Execute
        test_runner.run_pytest()

        # Verify command structure
        call_args = mock_run.call_args
        cmd = call_args[0][0]

        assert cmd[0] == "uv"
        assert cmd[1] == "run"
        assert cmd[2] == "pytest"
        assert "--cov=core" in cmd
        assert "--cov=routers" in cmd
        assert "--cov-report=json" in cmd
        assert "--json-report" in cmd

    @patch("subprocess.run")
    def test_vitest_command_structure(self, mock_run, test_runner, vitest_success_report):
        """Test vitest command is correctly constructed."""
        mock_run.return_value = Mock(
            stdout=json.dumps(vitest_success_report),
            stderr="",
            returncode=0
        )

        # Execute
        test_runner.run_vitest()

        # Verify command structure
        call_args = mock_run.call_args
        cmd = call_args[0][0]

        assert cmd[0] == "bun"
        assert cmd[1] == "run"
        assert cmd[2] == "vitest"
        assert cmd[3] == "run"
        assert "--reporter=json" in cmd
        assert "--coverage" in cmd

    @patch("subprocess.run")
    def test_pytest_cwd_is_correct(self, mock_run, test_runner, pytest_success_report, tmp_path):
        """Test pytest is executed in correct working directory."""
        pytest_path = test_runner.project_root / "app" / "server"
        json_report_path = pytest_path / ".pytest_report.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)

        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        with open(json_report_path, "w") as f:
            json.dump(pytest_success_report, f)

        # Execute
        test_runner.run_pytest()

        # Verify cwd
        call_args = mock_run.call_args
        assert call_args[1]["cwd"] == pytest_path

    @patch("subprocess.run")
    def test_vitest_cwd_is_correct(self, mock_run, test_runner, vitest_success_report):
        """Test vitest is executed in correct working directory."""
        mock_run.return_value = Mock(
            stdout=json.dumps(vitest_success_report),
            stderr="",
            returncode=0
        )

        # Execute
        test_runner.run_vitest()

        # Verify cwd
        call_args = mock_run.call_args
        vitest_path = test_runner.project_root / "app" / "client"
        assert call_args[1]["cwd"] == vitest_path
