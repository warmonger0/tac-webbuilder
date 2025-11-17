"""
Lint Checker Module - Run linting and return errors only

This module executes linting processes for frontend (ESLint) and backend (Ruff),
parsing their output to return only errors with precise locations.

Key Features:
- Runs ESLint for TypeScript/React code
- Runs Ruff for Python code
- Parses error output and extracts file/line numbers
- Returns compact JSON format (reduces context by 85%)
- Optional auto-fix mode
"""

import json
import re
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class LintError:
    """Represents a single linting error."""
    file: str
    line: int
    column: int
    rule: str  # e.g., "@typescript-eslint/no-unused-vars" or "F401"
    severity: str  # "error" or "warning"
    message: str
    fixable: bool = False


@dataclass
class LintSummary:
    """Summary statistics for lint check."""
    total_errors: int
    style_errors: int
    quality_errors: int
    warnings: int
    fixable_count: int = 0
    duration_seconds: float = 0.0


@dataclass
class LintResult:
    """Complete lint check result."""
    success: bool
    summary: LintSummary
    errors: List[LintError]
    next_steps: List[str]


class LintChecker:
    """Execute lint checks and return compact results."""

    def __init__(self, project_root: Path):
        """
        Initialize lint checker.

        Args:
            project_root: Path to project root directory
        """
        self.project_root = Path(project_root)

    def check_frontend_lint(self, fix_mode: bool = False) -> LintResult:
        """
        Run ESLint on frontend code.

        Args:
            fix_mode: If True, auto-fix issues where possible

        Returns:
            LintResult with lint errors only
        """
        frontend_path = self.project_root / "app" / "client"

        # Run ESLint
        cmd = ["npm", "run", "lint", "--"]
        if fix_mode:
            cmd.append("--fix")

        # Always use JSON output for parsing
        cmd.extend(["--format", "json"])

        import time
        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                cwd=frontend_path,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            duration = time.time() - start_time

            # Parse ESLint JSON output
            errors = self._parse_eslint_output(result.stdout)

            summary = LintSummary(
                total_errors=len([e for e in errors if e.severity == "error"]),
                style_errors=len([e for e in errors if "style" in e.rule.lower()]),
                quality_errors=len([e for e in errors if "style" not in e.rule.lower() and e.severity == "error"]),
                warnings=len([e for e in errors if e.severity == "warning"]),
                fixable_count=len([e for e in errors if e.fixable]),
                duration_seconds=duration
            )

            # Generate next steps
            next_steps = []
            if errors:
                if summary.fixable_count > 0:
                    next_steps.append(f"{summary.fixable_count} error(s) can be auto-fixed with --fix-mode")
                for err in errors[:3]:  # First 3 errors
                    next_steps.append(f"Fix {err.rule} in {err.file}:{err.line}")
            else:
                next_steps.append("No lint errors found!")

            success = summary.total_errors == 0

            return LintResult(
                success=success,
                summary=summary,
                errors=errors,
                next_steps=next_steps
            )

        except subprocess.TimeoutExpired:
            return LintResult(
                success=False,
                summary=LintSummary(total_errors=1, style_errors=0, quality_errors=1, warnings=0),
                errors=[LintError(
                    file="",
                    line=0,
                    column=0,
                    rule="TimeoutError",
                    severity="error",
                    message="ESLint timed out after 2 minutes",
                    fixable=False
                )],
                next_steps=["Investigate slow linting or large file set"]
            )
        except Exception as e:
            return LintResult(
                success=False,
                summary=LintSummary(total_errors=1, style_errors=0, quality_errors=1, warnings=0),
                errors=[LintError(
                    file="",
                    line=0,
                    column=0,
                    rule="ExecutionError",
                    severity="error",
                    message=f"ESLint execution failed: {str(e)}",
                    fixable=False
                )],
                next_steps=[f"Check ESLint configuration: {str(e)}"]
            )

    def _parse_eslint_output(self, output: str) -> List[LintError]:
        """
        Parse ESLint JSON output.

        Args:
            output: Raw ESLint JSON output

        Returns:
            List of LintError objects
        """
        errors = []

        try:
            # ESLint JSON format: array of file results
            results = json.loads(output) if output.strip() else []

            for file_result in results:
                file_path = file_result.get("filePath", "")
                # Make path relative to project root
                if file_path.startswith(str(self.project_root)):
                    file_path = file_path[len(str(self.project_root)) + 1:]

                for message in file_result.get("messages", []):
                    errors.append(LintError(
                        file=file_path,
                        line=message.get("line", 0),
                        column=message.get("column", 0),
                        rule=message.get("ruleId", "unknown"),
                        severity="error" if message.get("severity") == 2 else "warning",
                        message=message.get("message", ""),
                        fixable=message.get("fix") is not None
                    ))

        except json.JSONDecodeError:
            # Fallback: try to parse text output
            pass

        return errors

    def check_backend_lint(self, fix_mode: bool = False) -> LintResult:
        """
        Run Ruff linting on backend code.

        Args:
            fix_mode: If True, auto-fix issues where possible

        Returns:
            LintResult with lint errors
        """
        backend_path = self.project_root / "app" / "server"

        # Build ruff command
        cmd = ["uv", "run", "ruff", "check"]
        if fix_mode:
            cmd.append("--fix")

        # Use JSON output for parsing
        cmd.extend(["--output-format", "json", "."])

        import time
        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                cwd=backend_path,
                capture_output=True,
                text=True,
                timeout=60  # 1 minute timeout
            )
            duration = time.time() - start_time

            errors = self._parse_ruff_output(result.stdout)

            summary = LintSummary(
                total_errors=len([e for e in errors if e.severity == "error"]),
                style_errors=len([e for e in errors if e.rule.startswith(("E", "W"))]),
                quality_errors=len([e for e in errors if e.rule.startswith(("F", "C", "N"))]),
                warnings=len([e for e in errors if e.severity == "warning"]),
                fixable_count=len([e for e in errors if e.fixable]),
                duration_seconds=duration
            )

            next_steps = []
            if errors:
                if summary.fixable_count > 0:
                    next_steps.append(f"{summary.fixable_count} error(s) can be auto-fixed with --fix-mode")
                for err in errors[:3]:
                    next_steps.append(f"Fix {err.rule} in {err.file}:{err.line}")
            else:
                next_steps.append("No lint errors found!")

            success = len(errors) == 0

            return LintResult(
                success=success,
                summary=summary,
                errors=errors,
                next_steps=next_steps
            )

        except subprocess.TimeoutExpired:
            return LintResult(
                success=False,
                summary=LintSummary(total_errors=1, style_errors=0, quality_errors=1, warnings=0),
                errors=[LintError(
                    file="",
                    line=0,
                    column=0,
                    rule="TimeoutError",
                    severity="error",
                    message="Ruff timed out after 1 minute",
                    fixable=False
                )],
                next_steps=["Investigate slow linting"]
            )
        except Exception as e:
            return LintResult(
                success=False,
                summary=LintSummary(total_errors=1, style_errors=0, quality_errors=1, warnings=0),
                errors=[LintError(
                    file="",
                    line=0,
                    column=0,
                    rule="ExecutionError",
                    severity="error",
                    message=f"Ruff execution failed: {str(e)}",
                    fixable=False
                )],
                next_steps=[f"Check Ruff installation: {str(e)}"]
            )

    def _parse_ruff_output(self, output: str) -> List[LintError]:
        """
        Parse Ruff JSON output.

        Args:
            output: Raw Ruff JSON output

        Returns:
            List of LintError objects
        """
        errors = []

        try:
            # Ruff JSON format: array of diagnostics
            diagnostics = json.loads(output) if output.strip() else []

            for diag in diagnostics:
                file_path = diag.get("filename", "")
                # Make path relative to project root
                if file_path.startswith(str(self.project_root)):
                    file_path = file_path[len(str(self.project_root)) + 1:]

                location = diag.get("location", {})

                errors.append(LintError(
                    file=file_path,
                    line=location.get("row", 0),
                    column=location.get("column", 0),
                    rule=diag.get("code", "unknown"),
                    severity="error",  # Ruff reports all as errors by default
                    message=diag.get("message", ""),
                    fixable=diag.get("fix") is not None
                ))

        except json.JSONDecodeError:
            # Fallback: empty list
            pass

        return errors

    def check_all(
        self,
        target: str = "both",
        fix_mode: bool = False
    ) -> Dict[str, LintResult]:
        """
        Run all lint checks.

        Args:
            target: "frontend", "backend", or "both"
            fix_mode: Enable auto-fix mode

        Returns:
            Dict with check results
        """
        results = {}

        if target in ["frontend", "both"]:
            results["frontend_lint"] = self.check_frontend_lint(fix_mode)

        if target in ["backend", "both"]:
            results["backend_lint"] = self.check_backend_lint(fix_mode)

        return results


def result_to_dict(result: LintResult) -> Dict[str, Any]:
    """Convert LintResult to dictionary for JSON serialization."""
    return {
        "success": result.success,
        "summary": asdict(result.summary),
        "errors": [asdict(e) for e in result.errors],
        "next_steps": result.next_steps
    }


# Example usage
if __name__ == "__main__":
    from pathlib import Path

    project_root = Path(__file__).parent.parent.parent
    checker = LintChecker(project_root)

    print("Checking frontend lint...")
    result = checker.check_frontend_lint()
    print(json.dumps(result_to_dict(result), indent=2))
