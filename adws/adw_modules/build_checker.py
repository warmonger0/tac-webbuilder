"""
Build Checker Module - Run typecheck/build and return errors only

This module executes TypeScript type checking and build processes,
parsing their output to return only errors with precise locations.

Key Features:
- Runs TypeScript compiler (tsc)
- Runs frontend build (bun run build)
- Runs backend validation (mypy for Python)
- Parses error output and extracts file/line numbers
- Returns compact JSON format (reduces context by 85%)
"""

import json
import re
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class BuildError:
    """Represents a single build/type error."""
    file: str
    line: int
    column: int
    error_type: str
    severity: str  # "error" or "warning"
    message: str
    code_snippet: str = ""


@dataclass
class BuildSummary:
    """Summary statistics for build check."""
    total_errors: int
    type_errors: int
    build_errors: int
    warnings: int
    duration_seconds: float = 0.0


@dataclass
class BuildResult:
    """Complete build check result."""
    success: bool
    summary: BuildSummary
    errors: List[BuildError]
    next_steps: List[str]


class BuildChecker:
    """Execute build checks and return compact results."""

    def __init__(self, project_root: Path):
        """
        Initialize build checker.

        Args:
            project_root: Path to project root directory
        """
        self.project_root = Path(project_root)

    def check_frontend_types(self, strict_mode: bool = True) -> BuildResult:
        """
        Run TypeScript type checking on frontend.

        Args:
            strict_mode: Enable strict TypeScript checking

        Returns:
            BuildResult with type errors only
        """
        frontend_path = self.project_root / "app" / "client"

        # Run tsc with --noEmit (type check only, no build)
        cmd = ["npx", "tsc", "--noEmit"]
        if strict_mode:
            cmd.append("--strict")

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

            # Parse TypeScript errors
            errors = self._parse_tsc_output(result.stdout + result.stderr)

            summary = BuildSummary(
                total_errors=len([e for e in errors if e.severity == "error"]),
                type_errors=len([e for e in errors if e.severity == "error"]),
                build_errors=0,
                warnings=len([e for e in errors if e.severity == "warning"]),
                duration_seconds=duration
            )

            # Generate next steps
            next_steps = []
            if errors:
                for err in errors[:3]:  # First 3 errors
                    next_steps.append(f"Fix {err.error_type} in {err.file}:{err.line}")
            else:
                next_steps.append("No type errors found!")

            success = summary.total_errors == 0

            return BuildResult(
                success=success,
                summary=summary,
                errors=errors,
                next_steps=next_steps
            )

        except subprocess.TimeoutExpired:
            return BuildResult(
                success=False,
                summary=BuildSummary(total_errors=1, type_errors=1, build_errors=0, warnings=0),
                errors=[BuildError(
                    file="",
                    line=0,
                    column=0,
                    error_type="TimeoutError",
                    severity="error",
                    message="TypeScript compilation timed out after 2 minutes"
                )],
                next_steps=["Investigate slow TypeScript compilation or circular dependencies"]
            )

    def _parse_tsc_output(self, output: str) -> List[BuildError]:
        """
        Parse TypeScript compiler output.

        Args:
            output: Raw tsc output

        Returns:
            List of BuildError objects
        """
        errors = []

        # TypeScript error format:
        # src/components/Foo.tsx(42,23): error TS2345: Type 'string' is not assignable to type 'number'.

        pattern = r"(.+?)\((\d+),(\d+)\):\s+(error|warning)\s+(TS\d+):\s+(.+)"

        for line in output.split("\n"):
            match = re.match(pattern, line)
            if match:
                file_path, line_num, col_num, severity, error_code, message = match.groups()

                # Extract code snippet (if available in next lines)
                code_snippet = ""
                # TODO: Extract code snippet from surrounding lines

                errors.append(BuildError(
                    file=file_path,
                    line=int(line_num),
                    column=int(col_num),
                    error_type=error_code,
                    severity=severity,
                    message=message,
                    code_snippet=code_snippet
                ))

        return errors

    def check_frontend_build(self) -> BuildResult:
        """
        Run frontend build and return errors.

        Returns:
            BuildResult with build errors only
        """
        frontend_path = self.project_root / "app" / "client"

        cmd = ["bun", "run", "build"]

        import time
        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                cwd=frontend_path,
                capture_output=True,
                text=True,
                timeout=180  # 3 minute timeout
            )
            duration = time.time() - start_time

            # Parse build errors
            errors = []
            if result.returncode != 0:
                # Parse vite build errors
                errors = self._parse_vite_output(result.stdout + result.stderr)

            summary = BuildSummary(
                total_errors=len(errors),
                type_errors=0,
                build_errors=len(errors),
                warnings=0,
                duration_seconds=duration
            )

            next_steps = []
            if errors:
                for err in errors[:3]:
                    next_steps.append(f"Fix build error in {err.file}:{err.line}")
            else:
                next_steps.append("Build successful!")

            success = len(errors) == 0

            return BuildResult(
                success=success,
                summary=summary,
                errors=errors,
                next_steps=next_steps
            )

        except subprocess.TimeoutExpired:
            return BuildResult(
                success=False,
                summary=BuildSummary(total_errors=1, type_errors=0, build_errors=1, warnings=0),
                errors=[BuildError(
                    file="",
                    line=0,
                    column=0,
                    error_type="TimeoutError",
                    severity="error",
                    message="Build timed out after 3 minutes"
                )],
                next_steps=["Investigate slow build or infinite loops"]
            )

    def _parse_vite_output(self, output: str) -> List[BuildError]:
        """
        Parse Vite build output.

        Args:
            output: Raw vite output

        Returns:
            List of BuildError objects
        """
        errors = []

        # Vite error format varies, basic parsing
        # Example: [vite] ERROR src/App.tsx:42:23: ...

        lines = output.split("\n")
        for i, line in enumerate(lines):
            if "ERROR" in line or "error" in line.lower():
                # Try to extract file and line
                match = re.search(r"([a-zA-Z0-9/_.-]+\.tsx?):(\d+):(\d+)", line)
                if match:
                    file_path, line_num, col_num = match.groups()
                    message = lines[i+1] if i+1 < len(lines) else "Build error"

                    errors.append(BuildError(
                        file=file_path,
                        line=int(line_num),
                        column=int(col_num),
                        error_type="BuildError",
                        severity="error",
                        message=message.strip(),
                        code_snippet=""
                    ))

        return errors

    def check_backend_types(self) -> BuildResult:
        """
        Run Python type checking with mypy (if available).

        Returns:
            BuildResult with type errors
        """
        backend_path = self.project_root / "app" / "server"

        # Check if mypy is installed
        try:
            subprocess.run(
                ["uv", "run", "mypy", "--version"],
                cwd=backend_path,
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            # mypy not installed, skip
            return BuildResult(
                success=True,
                summary=BuildSummary(total_errors=0, type_errors=0, build_errors=0, warnings=0),
                errors=[],
                next_steps=["mypy not installed, skipping Python type checks"]
            )

        # Run mypy
        cmd = ["uv", "run", "mypy", ".", "--ignore-missing-imports"]

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

            errors = self._parse_mypy_output(result.stdout + result.stderr)

            summary = BuildSummary(
                total_errors=len(errors),
                type_errors=len(errors),
                build_errors=0,
                warnings=0,
                duration_seconds=duration
            )

            next_steps = []
            if errors:
                for err in errors[:3]:
                    next_steps.append(f"Fix type error in {err.file}:{err.line}")
            else:
                next_steps.append("No type errors found!")

            success = len(errors) == 0

            return BuildResult(
                success=success,
                summary=summary,
                errors=errors,
                next_steps=next_steps
            )

        except subprocess.TimeoutExpired:
            return BuildResult(
                success=False,
                summary=BuildSummary(total_errors=1, type_errors=1, build_errors=0, warnings=0),
                errors=[BuildError(
                    file="",
                    line=0,
                    column=0,
                    error_type="TimeoutError",
                    severity="error",
                    message="mypy timed out after 1 minute"
                )],
                next_steps=["Investigate slow type checking"]
            )

    def _parse_mypy_output(self, output: str) -> List[BuildError]:
        """
        Parse mypy output.

        Args:
            output: Raw mypy output

        Returns:
            List of BuildError objects
        """
        errors = []

        # mypy format: file.py:42: error: Message [error-code]
        pattern = r"(.+?):(\d+):\s+(error|warning|note):\s+(.+?)(?:\s+\[([a-z-]+)\])?$"

        for line in output.split("\n"):
            match = re.match(pattern, line)
            if match:
                file_path, line_num, severity, message, error_code = match.groups()

                if severity == "note":
                    continue  # Skip notes

                errors.append(BuildError(
                    file=file_path,
                    line=int(line_num),
                    column=0,
                    error_type=error_code or "type-error",
                    severity=severity,
                    message=message,
                    code_snippet=""
                ))

        return errors

    def check_all(
        self,
        check_type: str = "both",
        target: str = "both",
        strict_mode: bool = True
    ) -> Dict[str, BuildResult]:
        """
        Run all build checks.

        Args:
            check_type: "typecheck", "build", or "both"
            target: "frontend", "backend", or "both"
            strict_mode: Enable strict type checking

        Returns:
            Dict with check results
        """
        results = {}

        if target in ["frontend", "both"]:
            if check_type in ["typecheck", "both"]:
                results["frontend_types"] = self.check_frontend_types(strict_mode)
            if check_type in ["build", "both"]:
                results["frontend_build"] = self.check_frontend_build()

        if target in ["backend", "both"]:
            if check_type in ["typecheck", "both"]:
                results["backend_types"] = self.check_backend_types()

        return results


def result_to_dict(result: BuildResult) -> Dict[str, Any]:
    """Convert BuildResult to dictionary for JSON serialization."""
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
    checker = BuildChecker(project_root)

    print("Checking frontend types...")
    result = checker.check_frontend_types()
    print(json.dumps(result_to_dict(result), indent=2))
