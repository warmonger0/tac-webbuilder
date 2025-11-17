"""
Comprehensive test suite for the build_checker module.

Tests cover:
- BuildChecker class methods (type checking, building, backend validation)
- Error parsing functions for TypeScript, Vite, and mypy
- BuildError and BuildSummary dataclasses
- result_to_dict() helper function
- Edge cases (timeouts, missing tools, empty output)
- Coverage of all check combinations
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
from typing import List

import pytest

# Add parent directory to path for imports
import sys
from pathlib import Path as PathlibPath
sys.path.insert(0, str(PathlibPath(__file__).parent.parent))

from adw_modules.build_checker import (
    BuildChecker,
    BuildError,
    BuildSummary,
    BuildResult,
    result_to_dict,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def project_root(tmp_path):
    """Create a temporary project structure for testing."""
    # Create directory structure
    frontend_dir = tmp_path / "app" / "client"
    backend_dir = tmp_path / "app" / "server"
    frontend_dir.mkdir(parents=True, exist_ok=True)
    backend_dir.mkdir(parents=True, exist_ok=True)

    # Create dummy files
    (frontend_dir / "tsconfig.json").write_text('{}')
    (backend_dir / "setup.py").write_text('')

    return tmp_path


@pytest.fixture
def build_checker(project_root):
    """Create a BuildChecker instance with temporary project root."""
    return BuildChecker(project_root)


@pytest.fixture
def tsc_error_single():
    """Sample TypeScript error output (single error)."""
    return (
        'src/components/Button.tsx(42,23): error TS2345: '
        "Type 'string' is not assignable to type 'number'."
    )


@pytest.fixture
def tsc_error_multiple():
    """Sample TypeScript error output (multiple errors)."""
    return """src/components/Button.tsx(42,23): error TS2345: Type 'string' is not assignable to type 'number'.
src/utils/helpers.ts(10,5): warning TS1110: Type expected.
src/App.tsx(100,1): error TS7053: Element implicitly has an 'any' type."""


@pytest.fixture
def tsc_no_errors():
    """Sample TypeScript output with no errors."""
    return ""


@pytest.fixture
def vite_error_single():
    """Sample Vite build error output (single error)."""
    return """ERROR src/App.tsx:42:23: Some build error
Failed to build"""


@pytest.fixture
def vite_error_multiple():
    """Sample Vite build error output (multiple errors)."""
    return """ERROR src/components/Button.tsx:10:5: Build error one
Additional context here
ERROR src/utils/index.ts:25:3: Build error two
More context
Build failed with errors"""


@pytest.fixture
def vite_no_errors():
    """Sample Vite output with no errors (successful build)."""
    return """vite v5.0.0 building for production...
✓ 100 modules transformed
dist/index.html         2.50 kB │ gzip: 1.20 kB
dist/assets/index.js    50.00 kB │ gzip: 15.20 kB
Build successful!"""


@pytest.fixture
def mypy_error_single():
    """Sample mypy error output (single error)."""
    return 'server.py:42: error: Name "undefined_var" is not defined [name-defined]'


@pytest.fixture
def mypy_error_multiple():
    """Sample mypy error output (multiple errors)."""
    return """models.py:10: error: Incompatible types in assignment [assignment]
utils.py:25: warning: Unused "type: ignore" comment [unused-ignore]
schemas.py:5: error: Name "missing_import" is not defined [name-defined]
summary: 2 errors, 1 warning in 1 file"""


@pytest.fixture
def mypy_no_errors():
    """Sample mypy output with no errors."""
    return "Success: no issues found in 10 source files"


@pytest.fixture
def mypy_notes_output():
    """Sample mypy output with notes (should be ignored)."""
    return """models.py:10: error: Incompatible types [assignment]
models.py:10: note: See https://mypy.readthedocs.io/en/stable/error_codes.html
utils.py:25: note: Consider using Optional[int] instead"""


@pytest.fixture
def sample_build_error():
    """Create a sample BuildError for testing."""
    return BuildError(
        file="src/components/Button.tsx",
        line=42,
        column=23,
        error_type="TS2345",
        severity="error",
        message="Type 'string' is not assignable to type 'number'.",
        code_snippet="",
    )


@pytest.fixture
def sample_build_summary():
    """Create a sample BuildSummary for testing."""
    return BuildSummary(
        total_errors=5,
        type_errors=3,
        build_errors=2,
        warnings=1,
        duration_seconds=5.5,
    )


@pytest.fixture
def sample_build_result(sample_build_error, sample_build_summary):
    """Create a sample BuildResult for testing."""
    return BuildResult(
        success=False,
        summary=sample_build_summary,
        errors=[sample_build_error],
        next_steps=["Fix TS2345 in src/components/Button.tsx:42"],
    )


# ============================================================================
# Tests for BuildError dataclass
# ============================================================================


class TestBuildError:
    """Test BuildError dataclass."""

    def test_build_error_creation(self):
        """Test creating a BuildError instance."""
        error = BuildError(
            file="test.tsx",
            line=1,
            column=1,
            error_type="TS1234",
            severity="error",
            message="Test error",
        )
        assert error.file == "test.tsx"
        assert error.line == 1
        assert error.column == 1
        assert error.error_type == "TS1234"
        assert error.severity == "error"
        assert error.message == "Test error"

    def test_build_error_with_code_snippet(self):
        """Test BuildError with code snippet."""
        error = BuildError(
            file="test.tsx",
            line=5,
            column=10,
            error_type="TS2345",
            severity="error",
            message="Test error",
            code_snippet="const x: number = 'string';",
        )
        assert error.code_snippet == "const x: number = 'string';"

    def test_build_error_severity_warning(self):
        """Test BuildError with warning severity."""
        error = BuildError(
            file="test.ts",
            line=20,
            column=5,
            error_type="TS1110",
            severity="warning",
            message="Type expected",
        )
        assert error.severity == "warning"


# ============================================================================
# Tests for BuildSummary dataclass
# ============================================================================


class TestBuildSummary:
    """Test BuildSummary dataclass."""

    def test_build_summary_creation(self):
        """Test creating a BuildSummary instance."""
        summary = BuildSummary(
            total_errors=10,
            type_errors=5,
            build_errors=3,
            warnings=2,
            duration_seconds=5.5,
        )
        assert summary.total_errors == 10
        assert summary.type_errors == 5
        assert summary.build_errors == 3
        assert summary.warnings == 2
        assert summary.duration_seconds == 5.5

    def test_build_summary_default_duration(self):
        """Test BuildSummary with default duration."""
        summary = BuildSummary(
            total_errors=0,
            type_errors=0,
            build_errors=0,
            warnings=0,
        )
        assert summary.duration_seconds == 0.0


# ============================================================================
# Tests for result_to_dict() helper function
# ============================================================================


class TestResultToDict:
    """Test result_to_dict() helper function."""

    def test_result_to_dict_basic(self, sample_build_result):
        """Test converting BuildResult to dictionary."""
        result_dict = result_to_dict(sample_build_result)

        assert isinstance(result_dict, dict)
        assert "success" in result_dict
        assert "summary" in result_dict
        assert "errors" in result_dict
        assert "next_steps" in result_dict

    def test_result_to_dict_success_field(self, sample_build_result):
        """Test success field in converted result."""
        result_dict = result_to_dict(sample_build_result)
        assert result_dict["success"] is False

    def test_result_to_dict_summary_is_dict(self, sample_build_result):
        """Test summary is converted to dictionary."""
        result_dict = result_to_dict(sample_build_result)
        assert isinstance(result_dict["summary"], dict)
        assert "total_errors" in result_dict["summary"]
        assert "type_errors" in result_dict["summary"]
        assert "build_errors" in result_dict["summary"]
        assert "warnings" in result_dict["summary"]
        assert "duration_seconds" in result_dict["summary"]

    def test_result_to_dict_errors_list(self, sample_build_result):
        """Test errors are converted to list of dictionaries."""
        result_dict = result_to_dict(sample_build_result)
        assert isinstance(result_dict["errors"], list)
        assert len(result_dict["errors"]) > 0
        assert isinstance(result_dict["errors"][0], dict)

    def test_result_to_dict_error_fields(self, sample_build_result):
        """Test error dictionary contains expected fields."""
        result_dict = result_to_dict(sample_build_result)
        error = result_dict["errors"][0]

        assert "file" in error
        assert "line" in error
        assert "column" in error
        assert "error_type" in error
        assert "severity" in error
        assert "message" in error
        assert "code_snippet" in error

    def test_result_to_dict_next_steps(self, sample_build_result):
        """Test next_steps in converted result."""
        result_dict = result_to_dict(sample_build_result)
        assert isinstance(result_dict["next_steps"], list)
        assert len(result_dict["next_steps"]) > 0

    def test_result_to_dict_json_serializable(self, sample_build_result):
        """Test that result_to_dict output is JSON serializable."""
        result_dict = result_to_dict(sample_build_result)
        json_str = json.dumps(result_dict)
        assert isinstance(json_str, str)
        # Verify we can parse it back
        parsed = json.loads(json_str)
        assert parsed["success"] is False

    def test_result_to_dict_empty_errors(self):
        """Test result_to_dict with no errors."""
        result = BuildResult(
            success=True,
            summary=BuildSummary(0, 0, 0, 0),
            errors=[],
            next_steps=["No errors found!"],
        )
        result_dict = result_to_dict(result)
        assert result_dict["success"] is True
        assert result_dict["errors"] == []
        assert result_dict["summary"]["total_errors"] == 0


# ============================================================================
# Tests for _parse_tsc_output()
# ============================================================================


class TestParseTscOutput:
    """Test TypeScript compiler output parsing."""

    def test_parse_tsc_single_error(self, build_checker, tsc_error_single):
        """Test parsing single TypeScript error."""
        errors = build_checker._parse_tsc_output(tsc_error_single)

        assert len(errors) == 1
        assert errors[0].file == "src/components/Button.tsx"
        assert errors[0].line == 42
        assert errors[0].column == 23
        assert errors[0].error_type == "TS2345"
        assert errors[0].severity == "error"
        assert "Type 'string' is not assignable" in errors[0].message

    def test_parse_tsc_multiple_errors(self, build_checker, tsc_error_multiple):
        """Test parsing multiple TypeScript errors."""
        errors = build_checker._parse_tsc_output(tsc_error_multiple)

        assert len(errors) == 3
        assert errors[0].file == "src/components/Button.tsx"
        assert errors[0].error_type == "TS2345"
        assert errors[0].severity == "error"

        assert errors[1].file == "src/utils/helpers.ts"
        assert errors[1].error_type == "TS1110"
        assert errors[1].severity == "warning"

        assert errors[2].file == "src/App.tsx"
        assert errors[2].error_type == "TS7053"

    def test_parse_tsc_empty_output(self, build_checker, tsc_no_errors):
        """Test parsing empty TypeScript output (no errors)."""
        errors = build_checker._parse_tsc_output(tsc_no_errors)
        assert len(errors) == 0

    def test_parse_tsc_preserves_message(self, build_checker):
        """Test that full error message is preserved."""
        output = (
            "src/App.tsx(1,1): error TS1000: "
            "This is a very long error message with multiple parts"
        )
        errors = build_checker._parse_tsc_output(output)

        assert len(errors) == 1
        assert errors[0].message == "This is a very long error message with multiple parts"

    def test_parse_tsc_various_error_types(self, build_checker):
        """Test parsing various TypeScript error codes."""
        output = """a.ts(1,1): error TS1005: Error message
b.ts(2,2): error TS2300: Another message
c.ts(3,3): warning TS3000: Warning message"""

        errors = build_checker._parse_tsc_output(output)

        assert len(errors) == 3
        error_codes = [e.error_type for e in errors]
        assert "TS1005" in error_codes
        assert "TS2300" in error_codes
        assert "TS3000" in error_codes

    def test_parse_tsc_ignores_non_matching_lines(self, build_checker):
        """Test that non-matching lines are ignored."""
        output = """This is some random output
src/App.tsx(1,1): error TS1000: Valid error
Some other text that doesn't match
Another valid line: src/Button.tsx(5,10): error TS2000: Error message"""

        errors = build_checker._parse_tsc_output(output)

        # Only valid format lines should be parsed
        assert len(errors) == 2
        assert errors[0].file == "src/App.tsx"
        assert errors[1].file == "src/Button.tsx"


# ============================================================================
# Tests for _parse_vite_output()
# ============================================================================


class TestParseViteOutput:
    """Test Vite build output parsing."""

    def test_parse_vite_single_error(self, build_checker, vite_error_single):
        """Test parsing single Vite build error."""
        errors = build_checker._parse_vite_output(vite_error_single)

        assert len(errors) == 1
        assert errors[0].file == "src/App.tsx"
        assert errors[0].line == 42
        assert errors[0].column == 23
        assert errors[0].error_type == "BuildError"
        assert errors[0].severity == "error"

    def test_parse_vite_multiple_errors(self, build_checker, vite_error_multiple):
        """Test parsing multiple Vite build errors."""
        errors = build_checker._parse_vite_output(vite_error_multiple)

        assert len(errors) == 2
        assert errors[0].file == "src/components/Button.tsx"
        assert errors[0].line == 10
        assert errors[0].column == 5

        assert errors[1].file == "src/utils/index.ts"
        assert errors[1].line == 25
        assert errors[1].column == 3

    def test_parse_vite_no_errors(self, build_checker, vite_no_errors):
        """Test parsing successful Vite output."""
        errors = build_checker._parse_vite_output(vite_no_errors)
        assert len(errors) == 0

    def test_parse_vite_case_insensitive_error(self, build_checker):
        """Test that error detection is case insensitive."""
        output = """error in src/App.tsx:1:1: Something went wrong
ERROR in src/Button.tsx:5:5: Another error"""

        errors = build_checker._parse_vite_output(output)

        # Both lowercase "error" and uppercase "ERROR" should be caught
        assert len(errors) == 2

    def test_parse_vite_uses_next_line_for_message(self, build_checker):
        """Test that Vite parser uses next line as message when available."""
        output = """ERROR src/App.tsx:1:1: Error line 1
This is the error message on the next line
More context"""

        errors = build_checker._parse_vite_output(output)

        assert len(errors) == 1
        assert "This is the error message" in errors[0].message


# ============================================================================
# Tests for _parse_mypy_output()
# ============================================================================


class TestParseMyPyOutput:
    """Test mypy output parsing."""

    def test_parse_mypy_single_error(self, build_checker, mypy_error_single):
        """Test parsing single mypy error."""
        errors = build_checker._parse_mypy_output(mypy_error_single)

        assert len(errors) == 1
        assert errors[0].file == "server.py"
        assert errors[0].line == 42
        assert errors[0].column == 0
        assert errors[0].severity == "error"
        assert errors[0].error_type == "name-defined"
        assert "undefined_var" in errors[0].message

    def test_parse_mypy_multiple_errors(self, build_checker, mypy_error_multiple):
        """Test parsing multiple mypy errors."""
        errors = build_checker._parse_mypy_output(mypy_error_multiple)

        assert len(errors) == 3
        severities = [e.severity for e in errors]
        assert severities.count("error") == 2
        assert severities.count("warning") == 1

    def test_parse_mypy_no_errors(self, build_checker, mypy_no_errors):
        """Test parsing successful mypy output."""
        errors = build_checker._parse_mypy_output(mypy_no_errors)
        assert len(errors) == 0

    def test_parse_mypy_ignores_notes(self, build_checker, mypy_notes_output):
        """Test that mypy notes are ignored."""
        errors = build_checker._parse_mypy_output(mypy_notes_output)

        # Should only have 1 error, notes should be filtered out
        assert len(errors) == 1
        assert all(e.severity != "note" for e in errors)

    def test_parse_mypy_error_codes(self, build_checker):
        """Test that mypy error codes are extracted."""
        output = """file.py:1: error: Message one [assignment]
file.py:2: error: Message two [name-defined]
file.py:3: error: Message three [no-redef]"""

        errors = build_checker._parse_mypy_output(output)

        assert len(errors) == 3
        error_codes = [e.error_type for e in errors]
        assert "assignment" in error_codes
        assert "name-defined" in error_codes
        assert "no-redef" in error_codes

    def test_parse_mypy_error_without_code(self, build_checker):
        """Test mypy error without error code (should default to 'type-error')."""
        output = "file.py:10: error: Some error message"
        errors = build_checker._parse_mypy_output(output)

        assert len(errors) == 1
        assert errors[0].error_type == "type-error"

    def test_parse_mypy_warning_severity(self, build_checker):
        """Test parsing mypy warnings."""
        output = "file.py:5: warning: Unused variable [unused-ignore]"
        errors = build_checker._parse_mypy_output(output)

        assert len(errors) == 1
        assert errors[0].severity == "warning"


# ============================================================================
# Tests for check_frontend_types()
# ============================================================================


class TestCheckFrontendTypes:
    """Test check_frontend_types() method."""

    @patch("subprocess.run")
    def test_check_frontend_types_success(self, mock_run, build_checker):
        """Test successful frontend type check."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )

        result = build_checker.check_frontend_types()

        assert result.success is True
        assert result.summary.total_errors == 0
        assert result.summary.type_errors == 0
        assert len(result.errors) == 0

    @patch("subprocess.run")
    def test_check_frontend_types_with_errors(self, mock_run, build_checker):
        """Test frontend type check with errors."""
        error_output = (
            'src/App.tsx(10,5): error TS2345: Type error message'
        )
        mock_run.return_value = MagicMock(
            returncode=2,
            stdout=error_output,
            stderr="",
        )

        result = build_checker.check_frontend_types()

        assert result.success is False
        assert result.summary.total_errors == 1
        assert result.summary.type_errors == 1
        assert len(result.errors) == 1

    @patch("subprocess.run")
    def test_check_frontend_types_with_warnings(self, mock_run, build_checker):
        """Test frontend type check with warnings."""
        error_output = (
            'src/App.tsx(10,5): warning TS1110: Type warning'
        )
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=error_output,
            stderr="",
        )

        result = build_checker.check_frontend_types()

        assert result.success is True  # Warnings don't fail
        assert result.summary.warnings == 1
        assert result.summary.total_errors == 0

    @patch("subprocess.run")
    def test_check_frontend_types_strict_mode(self, mock_run, build_checker):
        """Test that strict mode is passed to tsc."""
        mock_run.return_value = MagicMock(stdout="", stderr="")

        build_checker.check_frontend_types(strict_mode=True)

        call_args = mock_run.call_args
        assert "--strict" in call_args[0][0]

    @patch("subprocess.run")
    def test_check_frontend_types_non_strict_mode(self, mock_run, build_checker):
        """Test that strict mode is not passed when disabled."""
        mock_run.return_value = MagicMock(stdout="", stderr="")

        build_checker.check_frontend_types(strict_mode=False)

        call_args = mock_run.call_args
        assert "--strict" not in call_args[0][0]

    @patch("subprocess.run")
    def test_check_frontend_types_timeout(self, mock_run, build_checker):
        """Test timeout handling in frontend type check."""
        mock_run.side_effect = subprocess.TimeoutExpired("tsc", 120)

        result = build_checker.check_frontend_types()

        assert result.success is False
        assert result.summary.total_errors == 1
        assert len(result.errors) == 1
        assert result.errors[0].error_type == "TimeoutError"

    @patch("subprocess.run")
    def test_check_frontend_types_next_steps_no_errors(self, mock_run, build_checker):
        """Test next_steps when no errors found."""
        mock_run.return_value = MagicMock(stdout="", stderr="")

        result = build_checker.check_frontend_types()

        assert len(result.next_steps) > 0
        assert "No type errors found" in result.next_steps[0]

    @patch("subprocess.run")
    def test_check_frontend_types_next_steps_with_errors(self, mock_run, build_checker):
        """Test next_steps when errors found."""
        error_output = """src/App.tsx(10,5): error TS2345: Error 1
src/Button.tsx(20,10): error TS1234: Error 2
src/Utils.ts(30,15): error TS5678: Error 3"""

        mock_run.return_value = MagicMock(
            returncode=2,
            stdout=error_output,
            stderr="",
        )

        result = build_checker.check_frontend_types()

        assert len(result.next_steps) >= 1
        assert any("Fix" in step for step in result.next_steps)

    @patch("subprocess.run")
    def test_check_frontend_types_cwd(self, mock_run, build_checker):
        """Test that correct working directory is used."""
        mock_run.return_value = MagicMock(stdout="", stderr="")

        build_checker.check_frontend_types()

        call_args = mock_run.call_args
        assert "app/client" in str(call_args.kwargs["cwd"])

    @patch("subprocess.run")
    def test_check_frontend_types_command(self, mock_run, build_checker):
        """Test that correct tsc command is used."""
        mock_run.return_value = MagicMock(stdout="", stderr="")

        build_checker.check_frontend_types()

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "tsc" in cmd
        assert "--noEmit" in cmd


# ============================================================================
# Tests for check_frontend_build()
# ============================================================================


class TestCheckFrontendBuild:
    """Test check_frontend_build() method."""

    @patch("subprocess.run")
    def test_check_frontend_build_success(self, mock_run, build_checker):
        """Test successful frontend build."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Build successful",
            stderr="",
        )

        result = build_checker.check_frontend_build()

        assert result.success is True
        assert result.summary.total_errors == 0
        assert result.summary.build_errors == 0
        assert len(result.errors) == 0

    @patch("subprocess.run")
    def test_check_frontend_build_with_errors(self, mock_run, build_checker):
        """Test frontend build with errors."""
        error_output = "ERROR src/App.tsx:42:23: Build error"
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout=error_output,
            stderr="",
        )

        result = build_checker.check_frontend_build()

        assert result.success is False
        assert result.summary.total_errors == 1
        assert result.summary.build_errors == 1

    @patch("subprocess.run")
    def test_check_frontend_build_timeout(self, mock_run, build_checker):
        """Test timeout handling in frontend build."""
        mock_run.side_effect = subprocess.TimeoutExpired("bun", 180)

        result = build_checker.check_frontend_build()

        assert result.success is False
        assert result.summary.total_errors == 1
        assert result.errors[0].error_type == "TimeoutError"

    @patch("subprocess.run")
    def test_check_frontend_build_cwd(self, mock_run, build_checker):
        """Test that correct working directory is used."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        build_checker.check_frontend_build()

        call_args = mock_run.call_args
        assert "app/client" in str(call_args.kwargs["cwd"])

    @patch("subprocess.run")
    def test_check_frontend_build_command(self, mock_run, build_checker):
        """Test that correct bun command is used."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        build_checker.check_frontend_build()

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert cmd == ["bun", "run", "build"]

    @patch("subprocess.run")
    def test_check_frontend_build_next_steps(self, mock_run, build_checker):
        """Test next_steps generation for build."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = build_checker.check_frontend_build()

        assert len(result.next_steps) > 0
        assert "Build successful" in result.next_steps[0]


# ============================================================================
# Tests for check_backend_types()
# ============================================================================


class TestCheckBackendTypes:
    """Test check_backend_types() method."""

    @patch("subprocess.run")
    def test_check_backend_types_mypy_not_installed(self, mock_run, build_checker):
        """Test when mypy is not installed."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "mypy")

        result = build_checker.check_backend_types()

        assert result.success is True  # Treated as success when mypy not installed
        assert result.summary.total_errors == 0
        assert "mypy not installed" in result.next_steps[0]

    @patch("subprocess.run")
    def test_check_backend_types_mypy_not_found(self, mock_run, build_checker):
        """Test when mypy command is not found."""
        mock_run.side_effect = FileNotFoundError("mypy")

        result = build_checker.check_backend_types()

        assert result.success is True
        assert result.summary.total_errors == 0

    @patch("subprocess.run")
    def test_check_backend_types_success(self, mock_run, build_checker):
        """Test successful backend type check."""
        # First call is version check, second is mypy check
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="mypy 1.0.0", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),
        ]

        result = build_checker.check_backend_types()

        assert result.success is True
        assert result.summary.total_errors == 0

    @patch("subprocess.run")
    def test_check_backend_types_with_errors(self, mock_run, build_checker):
        """Test backend type check with errors."""
        error_output = "models.py:10: error: Type error message [error-code]"

        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="mypy 1.0.0", stderr=""),
            MagicMock(returncode=1, stdout=error_output, stderr=""),
        ]

        result = build_checker.check_backend_types()

        assert result.success is False
        assert result.summary.total_errors == 1
        assert len(result.errors) == 1

    @patch("subprocess.run")
    def test_check_backend_types_timeout(self, mock_run, build_checker):
        """Test timeout handling in backend type check."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="mypy 1.0.0", stderr=""),
            subprocess.TimeoutExpired("mypy", 60),
        ]

        result = build_checker.check_backend_types()

        assert result.success is False
        assert result.summary.total_errors == 1
        assert result.errors[0].error_type == "TimeoutError"

    @patch("subprocess.run")
    def test_check_backend_types_cwd(self, mock_run, build_checker):
        """Test that correct working directory is used."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),
        ]

        build_checker.check_backend_types()

        # Check all calls use correct cwd
        for call in mock_run.call_args_list:
            assert "app/server" in str(call.kwargs["cwd"])


# ============================================================================
# Tests for check_all()
# ============================================================================


class TestCheckAll:
    """Test check_all() method."""

    @patch.object(BuildChecker, "check_frontend_types")
    @patch.object(BuildChecker, "check_frontend_build")
    @patch.object(BuildChecker, "check_backend_types")
    def test_check_all_both_targets(
        self,
        mock_backend,
        mock_build,
        mock_types,
        build_checker,
    ):
        """Test check_all with both frontend and backend."""
        mock_result = BuildResult(
            success=True,
            summary=BuildSummary(0, 0, 0, 0),
            errors=[],
            next_steps=[],
        )
        mock_types.return_value = mock_result
        mock_build.return_value = mock_result
        mock_backend.return_value = mock_result

        results = build_checker.check_all(check_type="both", target="both")

        assert "frontend_types" in results
        assert "frontend_build" in results
        assert "backend_types" in results
        assert len(results) == 3

    @patch.object(BuildChecker, "check_frontend_types")
    @patch.object(BuildChecker, "check_frontend_build")
    @patch.object(BuildChecker, "check_backend_types")
    def test_check_all_frontend_only(
        self,
        mock_backend,
        mock_build,
        mock_types,
        build_checker,
    ):
        """Test check_all with frontend only."""
        mock_result = BuildResult(
            success=True,
            summary=BuildSummary(0, 0, 0, 0),
            errors=[],
            next_steps=[],
        )
        mock_types.return_value = mock_result
        mock_build.return_value = mock_result

        results = build_checker.check_all(target="frontend")

        assert "frontend_types" in results
        assert "frontend_build" in results
        assert "backend_types" not in results

    @patch.object(BuildChecker, "check_backend_types")
    def test_check_all_backend_only(self, mock_backend, build_checker):
        """Test check_all with backend only."""
        mock_result = BuildResult(
            success=True,
            summary=BuildSummary(0, 0, 0, 0),
            errors=[],
            next_steps=[],
        )
        mock_backend.return_value = mock_result

        results = build_checker.check_all(target="backend")

        assert "backend_types" in results
        assert "frontend_types" not in results
        assert "frontend_build" not in results

    @patch.object(BuildChecker, "check_frontend_types")
    def test_check_all_typecheck_only(self, mock_types, build_checker):
        """Test check_all with typecheck only."""
        mock_result = BuildResult(
            success=True,
            summary=BuildSummary(0, 0, 0, 0),
            errors=[],
            next_steps=[],
        )
        mock_types.return_value = mock_result

        results = build_checker.check_all(check_type="typecheck", target="frontend")

        assert "frontend_types" in results
        assert "frontend_build" not in results

    @patch.object(BuildChecker, "check_frontend_build")
    def test_check_all_build_only(self, mock_build, build_checker):
        """Test check_all with build only."""
        mock_result = BuildResult(
            success=True,
            summary=BuildSummary(0, 0, 0, 0),
            errors=[],
            next_steps=[],
        )
        mock_build.return_value = mock_result

        results = build_checker.check_all(check_type="build", target="frontend")

        assert "frontend_build" in results
        assert "frontend_types" not in results

    @patch.object(BuildChecker, "check_frontend_types")
    def test_check_all_passes_strict_mode(self, mock_types, build_checker):
        """Test that strict_mode is passed through check_all."""
        mock_result = BuildResult(
            success=True,
            summary=BuildSummary(0, 0, 0, 0),
            errors=[],
            next_steps=[],
        )
        mock_types.return_value = mock_result

        build_checker.check_all(strict_mode=False)

        mock_types.assert_called_with(False)

    @patch.object(BuildChecker, "check_frontend_types")
    @patch.object(BuildChecker, "check_frontend_build")
    @patch.object(BuildChecker, "check_backend_types")
    def test_check_all_empty_result(
        self,
        mock_backend,
        mock_build,
        mock_types,
        build_checker,
    ):
        """Test check_all with no checks requested."""
        results = build_checker.check_all(target="invalid")
        assert len(results) == 0


# ============================================================================
# Tests for BuildChecker initialization and path handling
# ============================================================================


class TestBuildCheckerInitialization:
    """Test BuildChecker initialization and path handling."""

    def test_init_with_path_object(self, tmp_path):
        """Test initialization with Path object."""
        checker = BuildChecker(tmp_path)
        assert checker.project_root == tmp_path

    def test_init_with_string_path(self, tmp_path):
        """Test initialization with string path."""
        checker = BuildChecker(str(tmp_path))
        assert isinstance(checker.project_root, Path)
        assert checker.project_root == tmp_path

    def test_init_converts_to_path(self):
        """Test that project_root is always a Path object."""
        checker = BuildChecker("/some/path")
        assert isinstance(checker.project_root, Path)


# ============================================================================
# Integration and Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @patch("subprocess.run")
    def test_parse_output_with_special_characters(self, mock_run, build_checker):
        """Test parsing output with special characters."""
        error_output = (
            "src/App.tsx(10,5): error TS2345: "
            "Type 'string | undefined' is not assignable to type 'number & readonly string[]'"
        )
        mock_run.return_value = MagicMock(stdout=error_output, stderr="")

        errors = build_checker._parse_tsc_output(error_output)

        assert len(errors) == 1
        assert "string | undefined" in errors[0].message

    @patch("subprocess.run")
    def test_parse_mypy_multiline_message(self, mock_run, build_checker):
        """Test that mypy messages with special formatting are parsed."""
        output = """file.py:10: error: "variable" is not defined [name-defined]"""

        errors = build_checker._parse_mypy_output(output)

        assert len(errors) == 1
        assert '"variable" is not defined' in errors[0].message

    def test_build_result_with_many_errors(self):
        """Test BuildResult with many errors."""
        errors = [
            BuildError(
                file=f"file{i}.tsx",
                line=i,
                column=i,
                error_type=f"TS{1000 + i}",
                severity="error",
                message=f"Error {i}",
            )
            for i in range(100)
        ]

        result = BuildResult(
            success=False,
            summary=BuildSummary(
                total_errors=100,
                type_errors=100,
                build_errors=0,
                warnings=0,
            ),
            errors=errors,
            next_steps=[f"Fix error {i}" for i in range(100)],
        )

        result_dict = result_to_dict(result)
        assert len(result_dict["errors"]) == 100
        assert len(result_dict["next_steps"]) == 100

    @patch("subprocess.run")
    def test_check_with_stderr_output(self, mock_run, build_checker):
        """Test that stderr is included in parsing."""
        mock_run.return_value = MagicMock(
            returncode=2,
            stdout="",
            stderr="src/App.tsx(1,1): error TS1000: Error in stderr",
        )

        result = build_checker.check_frontend_types()

        assert result.success is False
        assert len(result.errors) == 1

    def test_dataclass_field_types(self):
        """Test that dataclass fields have correct types."""
        error = BuildError(
            file="test.tsx",
            line=10,
            column=5,
            error_type="TS1234",
            severity="error",
            message="Test",
        )

        assert isinstance(error.file, str)
        assert isinstance(error.line, int)
        assert isinstance(error.column, int)
        assert isinstance(error.error_type, str)
        assert isinstance(error.severity, str)
        assert isinstance(error.message, str)

    def test_build_summary_validation(self):
        """Test BuildSummary with edge case values."""
        summary = BuildSummary(
            total_errors=0,
            type_errors=0,
            build_errors=0,
            warnings=0,
            duration_seconds=0.001,  # Very fast
        )

        assert summary.total_errors == 0
        assert summary.duration_seconds == 0.001

        summary2 = BuildSummary(
            total_errors=1000,
            type_errors=500,
            build_errors=300,
            warnings=200,
            duration_seconds=300.0,
        )

        assert summary2.total_errors == 1000


# ============================================================================
# Timeout and Performance Tests
# ============================================================================


class TestTimeoutHandling:
    """Test timeout handling across all check methods."""

    @patch("subprocess.run")
    def test_frontend_types_timeout_message(self, mock_run, build_checker):
        """Test timeout error message for frontend types."""
        mock_run.side_effect = subprocess.TimeoutExpired("tsc", 120)

        result = build_checker.check_frontend_types()

        assert "timed out" in result.errors[0].message.lower()
        assert "2 minutes" in result.errors[0].message

    @patch("subprocess.run")
    def test_frontend_build_timeout_message(self, mock_run, build_checker):
        """Test timeout error message for frontend build."""
        mock_run.side_effect = subprocess.TimeoutExpired("bun", 180)

        result = build_checker.check_frontend_build()

        assert "timed out" in result.errors[0].message.lower()
        assert "3 minutes" in result.errors[0].message

    @patch("subprocess.run")
    def test_backend_types_timeout_message(self, mock_run, build_checker):
        """Test timeout error message for backend types."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""),
            subprocess.TimeoutExpired("mypy", 60),
        ]

        result = build_checker.check_backend_types()

        assert "timed out" in result.errors[0].message.lower()
        assert "1 minute" in result.errors[0].message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
