"""
Quality Control Metrics Service.

Analyzes codebase quality metrics including:
- Test coverage
- Naming conventions
- File structure compliance
- Linting issues
- File size and complexity metrics
"""

import asyncio
import json
import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CoverageMetrics:
    """Test coverage metrics."""
    overall_coverage: float
    backend_coverage: float
    frontend_coverage: float
    adws_coverage: float
    total_lines: int
    covered_lines: int
    total_tests: int


@dataclass
class NamingConventionMetrics:
    """Naming convention compliance metrics."""
    total_files_checked: int
    compliant_files: int
    violations: list[dict[str, str]]
    compliance_rate: float


@dataclass
class FileStructureMetrics:
    """File and folder structure metrics."""
    total_files: int
    oversized_files: list[dict[str, any]]
    long_files: list[dict[str, any]]
    misplaced_files: list[dict[str, str]]
    avg_file_size_kb: float


@dataclass
class LintingMetrics:
    """Linting issues across the codebase."""
    backend_issues: int
    frontend_issues: int
    backend_errors: int
    backend_warnings: int
    frontend_errors: int
    frontend_warnings: int
    total_issues: int


@dataclass
class QCMetrics:
    """Complete QC metrics for the codebase."""
    coverage: CoverageMetrics
    naming: NamingConventionMetrics
    file_structure: FileStructureMetrics
    linting: LintingMetrics
    overall_score: float
    last_updated: str


class QCMetricsService:
    """Service for analyzing codebase quality metrics."""

    def __init__(self, project_root: Path | None = None):
        """Initialize QC metrics service.

        Args:
            project_root: Root directory of the project. Defaults to tac-webbuilder root.
        """
        if project_root is None:
            # Default to the tac-webbuilder root (3 levels up from this file)
            self.project_root = Path(__file__).parent.parent.parent.parent
        else:
            self.project_root = Path(project_root)

        logger.info(f"QCMetricsService initialized with project root: {self.project_root}")

    async def get_coverage_metrics(self) -> CoverageMetrics:
        """Get test coverage metrics for the entire project (parallelized).

        Returns:
            Coverage metrics including overall and per-subsystem coverage.
        """
        try:
            # Run all coverage checks in parallel using asyncio.gather()
            backend_cov, frontend_cov, adws_cov, total_tests = await asyncio.gather(
                self._get_backend_coverage_async(),
                self._get_frontend_coverage_async(),
                self._get_adws_coverage_async(),
                self._count_total_tests_async(),
                return_exceptions=True
            )

            # Handle exceptions from gather
            backend_coverage = backend_cov if not isinstance(backend_cov, Exception) else 0.0
            frontend_coverage = frontend_cov if not isinstance(frontend_cov, Exception) else 0.0
            adws_coverage = adws_cov if not isinstance(adws_cov, Exception) else 0.0
            test_count = total_tests if not isinstance(total_tests, Exception) else 0

            # Calculate overall coverage (weighted by lines of code)
            backend_weight = 0.5  # Backend is larger
            frontend_weight = 0.3
            adws_weight = 0.2

            overall = (
                backend_coverage * backend_weight +
                frontend_coverage * frontend_weight +
                adws_coverage * adws_weight
            )

            return CoverageMetrics(
                overall_coverage=round(overall, 2),
                backend_coverage=round(backend_coverage, 2),
                frontend_coverage=round(frontend_coverage, 2),
                adws_coverage=round(adws_coverage, 2),
                total_lines=0,  # Would need coverage.json to get exact numbers
                covered_lines=0,
                total_tests=test_count
            )

        except Exception as e:
            logger.error(f"Error getting coverage metrics: {e}")
            return CoverageMetrics(
                overall_coverage=0.0,
                backend_coverage=0.0,
                frontend_coverage=0.0,
                adws_coverage=0.0,
                total_lines=0,
                covered_lines=0,
                total_tests=0
            )

    async def _get_backend_coverage_async(self) -> float:
        """Get backend test coverage from pytest (async).

        Returns:
            Coverage percentage (0-100)
        """
        try:
            # Check if coverage data exists
            coverage_file = self.project_root / "app" / "server" / ".coverage"
            if not coverage_file.exists():
                logger.warning("No backend coverage data found")
                return 0.0

            # Run coverage report to get percentage (non-blocking)
            proc = await asyncio.create_subprocess_exec(
                "uv", "run", "coverage", "report", "--precision=2",
                cwd=self.project_root / "app" / "server",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)

            if proc.returncode == 0:
                # Parse TOTAL line: "TOTAL    10234    2345    77.12%"
                for line in stdout.decode().split('\n'):
                    if 'TOTAL' in line:
                        match = re.search(r'(\d+\.?\d*)%', line)
                        if match:
                            return float(match.group(1))

            return 0.0

        except Exception as e:
            logger.error(f"Error getting backend coverage: {e}")
            return 0.0

    def _get_backend_coverage(self) -> float:
        """Get backend test coverage from pytest (sync wrapper for backwards compat).

        Returns:
            Coverage percentage (0-100)
        """
        try:
            # Check if coverage data exists
            coverage_file = self.project_root / "app" / "server" / ".coverage"
            if not coverage_file.exists():
                logger.warning("No backend coverage data found")
                return 0.0

            # Run coverage report to get percentage
            result = subprocess.run(
                ["uv", "run", "coverage", "report", "--precision=2"],
                cwd=self.project_root / "app" / "server",
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                # Parse TOTAL line: "TOTAL    10234    2345    77.12%"
                for line in result.stdout.split('\n'):
                    if 'TOTAL' in line:
                        match = re.search(r'(\d+\.?\d*)%', line)
                        if match:
                            return float(match.group(1))

            return 0.0

        except Exception as e:
            logger.error(f"Error getting backend coverage: {e}")
            return 0.0

    async def _get_frontend_coverage_async(self) -> float:
        """Get frontend test coverage from vitest (async).

        Returns:
            Coverage percentage (0-100)
        """
        try:
            # Check if coverage summary exists
            coverage_file = self.project_root / "app" / "client" / "coverage" / "coverage-summary.json"
            if not coverage_file.exists():
                logger.warning("No frontend coverage data found")
                return 0.0

            # Read file asynchronously (runs in executor)
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: json.loads(coverage_file.read_text()))
            total = data.get('total', {})
            lines = total.get('lines', {})
            return float(lines.get('pct', 0.0))

        except Exception as e:
            logger.error(f"Error getting frontend coverage: {e}")
            return 0.0

    def _get_frontend_coverage(self) -> float:
        """Get frontend test coverage from vitest (sync wrapper).

        Returns:
            Coverage percentage (0-100)
        """
        try:
            # Check if coverage summary exists
            coverage_file = self.project_root / "app" / "client" / "coverage" / "coverage-summary.json"
            if not coverage_file.exists():
                logger.warning("No frontend coverage data found")
                return 0.0

            with open(coverage_file) as f:
                data = json.load(f)
                total = data.get('total', {})
                lines = total.get('lines', {})
                return float(lines.get('pct', 0.0))

        except Exception as e:
            logger.error(f"Error getting frontend coverage: {e}")
            return 0.0

    async def _get_adws_coverage_async(self) -> float:
        """Get ADWs test coverage (async).

        Returns:
            Coverage percentage (0-100)
        """
        try:
            coverage_file = self.project_root / "adws" / "tests" / ".coverage"
            if not coverage_file.exists():
                logger.warning("No ADWs coverage data found")
                return 0.0

            # Run coverage report (non-blocking)
            proc = await asyncio.create_subprocess_exec(
                "uv", "run", "coverage", "report", "--precision=2",
                cwd=self.project_root / "adws" / "tests",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)

            if proc.returncode == 0:
                for line in stdout.decode().split('\n'):
                    if 'TOTAL' in line:
                        match = re.search(r'(\d+\.?\d*)%', line)
                        if match:
                            return float(match.group(1))

            return 0.0

        except Exception as e:
            logger.error(f"Error getting ADWs coverage: {e}")
            return 0.0

    def _get_adws_coverage(self) -> float:
        """Get ADWs test coverage (sync wrapper).

        Returns:
            Coverage percentage (0-100)
        """
        try:
            coverage_file = self.project_root / "adws" / "tests" / ".coverage"
            if not coverage_file.exists():
                logger.warning("No ADWs coverage data found")
                return 0.0

            # Run coverage report
            result = subprocess.run(
                ["uv", "run", "coverage", "report", "--precision=2"],
                cwd=self.project_root / "adws" / "tests",
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'TOTAL' in line:
                        match = re.search(r'(\d+\.?\d*)%', line)
                        if match:
                            return float(match.group(1))

            return 0.0

        except Exception as e:
            logger.error(f"Error getting ADWs coverage: {e}")
            return 0.0

    async def _count_total_tests_async(self) -> int:
        """Count total number of tests across all test suites (async).

        Returns:
            Total test count
        """
        total = 0

        # Backend tests (run in parallel with frontend)
        try:
            proc = await asyncio.create_subprocess_exec(
                "uv", "run", "pytest", "--collect-only", "-q",
                cwd=self.project_root / "app" / "server",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            if proc.returncode == 0:
                # Last line typically shows: "878 tests collected"
                match = re.search(r'(\d+) tests? collected', stdout.decode())
                if match:
                    total += int(match.group(1))
        except Exception as e:
            logger.error(f"Error counting backend tests: {e}")

        # Frontend tests
        try:
            proc = await asyncio.create_subprocess_exec(
                "bun", "test", "--reporter=json",
                cwd=self.project_root / "app" / "client",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            if proc.returncode == 0:
                # Parse JSON output for test count
                match = re.search(r'"numTotalTests":\s*(\d+)', stdout.decode())
                if match:
                    total += int(match.group(1))
        except Exception as e:
            logger.error(f"Error counting frontend tests: {e}")

        return total

    def _count_total_tests(self) -> int:
        """Count total number of tests across all test suites (sync wrapper).

        Returns:
            Total test count
        """
        total = 0

        # Backend tests
        try:
            result = subprocess.run(
                ["uv", "run", "pytest", "--collect-only", "-q"],
                cwd=self.project_root / "app" / "server",
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                # Last line typically shows: "878 tests collected"
                match = re.search(r'(\d+) tests? collected', result.stdout)
                if match:
                    total += int(match.group(1))
        except Exception as e:
            logger.error(f"Error counting backend tests: {e}")

        # Frontend tests
        try:
            result = subprocess.run(
                ["bun", "test", "--reporter=json"],
                cwd=self.project_root / "app" / "client",
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                # Parse JSON output for test count
                match = re.search(r'"numTotalTests":\s*(\d+)', result.stdout)
                if match:
                    total += int(match.group(1))
        except Exception as e:
            logger.error(f"Error counting frontend tests: {e}")

        return total

    def get_naming_convention_metrics(self) -> NamingConventionMetrics:
        """Analyze naming convention compliance.

        Checks:
        - Python files use snake_case
        - TypeScript/React files use PascalCase for components, camelCase for utils
        - Folders use kebab-case or snake_case

        Returns:
            Naming convention compliance metrics
        """
        violations = []
        total_files = 0
        compliant_files = 0

        # Define naming patterns
        patterns = {
            'python_file': re.compile(r'^[a-z][a-z0-9_]*\.py$'),
            'typescript_component': re.compile(r'^[A-Z][A-Za-z0-9]*\.tsx?$'),
            'typescript_util': re.compile(r'^[a-z][a-zA-Z0-9]*\.tsx?$'),
            'folder': re.compile(r'^[a-z][a-z0-9_-]*$'),
        }

        # Check Python files (excluding venv/node_modules BEFORE enumeration)
        for py_file in self.project_root.rglob('*.py'):
            # Fast path filtering - check string representation for exclusions
            file_str = str(py_file)
            if any(exclude in file_str for exclude in ['venv', '.venv', 'node_modules', '__pycache__', '.git']):
                continue

            total_files += 1
            filename = py_file.name

            if patterns['python_file'].match(filename):
                compliant_files += 1
            else:
                violations.append({
                    'file': str(py_file.relative_to(self.project_root)),
                    'issue': 'Python file should use snake_case',
                    'severity': 'warning'
                })

        # Check TypeScript/React files (excluding node_modules BEFORE enumeration)
        for ts_file in self.project_root.rglob('*.ts*'):
            # Fast path filtering - check string representation for exclusions
            file_str = str(ts_file)
            if any(exclude in file_str for exclude in ['node_modules', 'venv', '.venv', 'dist', 'coverage', '.git']):
                continue

            total_files += 1
            filename = ts_file.name

            # Components should be PascalCase
            if filename.endswith('.tsx'):
                if patterns['typescript_component'].match(filename):
                    compliant_files += 1
                else:
                    violations.append({
                        'file': str(ts_file.relative_to(self.project_root)),
                        'issue': 'React component should use PascalCase',
                        'severity': 'warning'
                    })
            # Utils can be camelCase or PascalCase
            else:
                if patterns['typescript_component'].match(filename) or patterns['typescript_util'].match(filename):
                    compliant_files += 1
                else:
                    violations.append({
                        'file': str(ts_file.relative_to(self.project_root)),
                        'issue': 'TypeScript file should use camelCase or PascalCase',
                        'severity': 'info'
                    })

        compliance_rate = (compliant_files / total_files * 100) if total_files > 0 else 100.0

        return NamingConventionMetrics(
            total_files_checked=total_files,
            compliant_files=compliant_files,
            violations=violations[:50],  # Limit to first 50 violations
            compliance_rate=round(compliance_rate, 2)
        )

    def get_file_structure_metrics(self) -> FileStructureMetrics:
        """Analyze file and folder structure.

        Returns:
            File structure metrics including oversized files and misplaced files
        """
        total_files = 0
        oversized_files = []
        long_files = []
        total_size = 0

        # Define thresholds
        max_file_size_kb = 500  # 500 KB
        max_file_lines = 1000   # 1000 lines

        # Check all code files (excluding venv/node_modules BEFORE enumeration)
        for ext in ['*.py', '*.ts', '*.tsx', '*.js', '*.jsx']:
            for file in self.project_root.rglob(ext):
                # Fast path filtering - check string representation for exclusions
                file_str = str(file)
                if any(exclude in file_str for exclude in ['venv', '.venv', 'node_modules', 'dist', 'coverage', '__pycache__', '.git']):
                    continue

                total_files += 1

                # Check file size
                size_kb = file.stat().st_size / 1024
                total_size += size_kb

                if size_kb > max_file_size_kb:
                    oversized_files.append({
                        'file': str(file.relative_to(self.project_root)),
                        'size_kb': round(size_kb, 2)
                    })

                # Check line count
                try:
                    with open(file, encoding='utf-8') as f:
                        line_count = sum(1 for _ in f)

                    if line_count > max_file_lines:
                        long_files.append({
                            'file': str(file.relative_to(self.project_root)),
                            'lines': line_count
                        })
                except Exception as e:
                    logger.warning(f"Error reading file {file}: {e}")

        avg_size = (total_size / total_files) if total_files > 0 else 0.0

        return FileStructureMetrics(
            total_files=total_files,
            oversized_files=oversized_files[:20],  # Top 20 largest
            long_files=sorted(long_files, key=lambda x: x['lines'], reverse=True)[:20],  # Top 20 longest
            misplaced_files=[],  # Could add logic to detect misplaced files
            avg_file_size_kb=round(avg_size, 2)
        )

    def get_linting_metrics(self) -> LintingMetrics:
        """Get linting issue counts from backend and frontend.

        Returns:
            Linting metrics from ruff/mypy (backend) and eslint (frontend)
        """
        backend_issues = 0
        backend_errors = 0
        backend_warnings = 0
        frontend_issues = 0
        frontend_errors = 0
        frontend_warnings = 0

        # Backend: Ruff check
        try:
            result = subprocess.run(
                ["uv", "run", "ruff", "check", ".", "--output-format=json"],
                cwd=self.project_root / "app" / "server",
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.stdout:
                try:
                    issues = json.loads(result.stdout)
                    backend_issues = len(issues)
                    # Ruff doesn't distinguish errors/warnings, consider all as warnings
                    backend_warnings = backend_issues
                except json.JSONDecodeError:
                    logger.warning("Could not parse ruff output")

        except Exception as e:
            logger.error(f"Error running ruff: {e}")

        # Frontend: ESLint
        try:
            result = subprocess.run(
                ["npx", "eslint", "src/", "--format=json"],
                cwd=self.project_root / "app" / "client",
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.stdout:
                try:
                    eslint_results = json.loads(result.stdout)
                    for file_result in eslint_results:
                        for message in file_result.get('messages', []):
                            frontend_issues += 1
                            if message.get('severity') == 2:
                                frontend_errors += 1
                            else:
                                frontend_warnings += 1
                except json.JSONDecodeError:
                    logger.warning("Could not parse eslint output")

        except Exception as e:
            logger.error(f"Error running eslint: {e}")

        return LintingMetrics(
            backend_issues=backend_issues,
            frontend_issues=frontend_issues,
            backend_errors=backend_errors,
            backend_warnings=backend_warnings,
            frontend_errors=frontend_errors,
            frontend_warnings=frontend_warnings,
            total_issues=backend_issues + frontend_issues
        )

    def calculate_overall_score(
        self,
        coverage: CoverageMetrics,
        naming: NamingConventionMetrics,
        file_structure: FileStructureMetrics,
        linting: LintingMetrics
    ) -> float:
        """Calculate overall QC score (0-100).

        Weights:
        - Coverage: 40%
        - Naming: 20%
        - File Structure: 15%
        - Linting: 25%

        Returns:
            Overall score (0-100)
        """
        # Coverage score (0-100)
        coverage_score = coverage.overall_coverage

        # Naming score (0-100)
        naming_score = naming.compliance_rate

        # File structure score (penalize oversized and long files)
        max_oversized_penalty = 10
        max_long_penalty = 10
        oversized_penalty = min(len(file_structure.oversized_files), max_oversized_penalty)
        long_penalty = min(len(file_structure.long_files), max_long_penalty)
        file_structure_score = 100 - oversized_penalty - long_penalty

        # Linting score (penalize errors more than warnings)
        max_lint_penalty = 100
        lint_penalty = min(
            (linting.backend_errors + linting.frontend_errors) * 2 +
            (linting.backend_warnings + linting.frontend_warnings),
            max_lint_penalty
        )
        linting_score = max(0, 100 - lint_penalty)

        # Weighted average
        overall = (
            coverage_score * 0.40 +
            naming_score * 0.20 +
            file_structure_score * 0.15 +
            linting_score * 0.25
        )

        return round(overall, 2)

    async def get_all_metrics_async(self) -> dict:
        """Get all QC metrics in one call (parallelized for performance).

        Returns:
            Complete QC metrics dictionary
        """
        from datetime import datetime

        logger.info("Gathering all QC metrics (parallelized)...")

        # Run coverage async, others are CPU-bound file operations
        coverage, naming, file_structure, linting = await asyncio.gather(
            self.get_coverage_metrics(),  # async - parallelizes subprocesses
            asyncio.to_thread(self.get_naming_convention_metrics),  # CPU-bound - run in thread
            asyncio.to_thread(self.get_file_structure_metrics),  # CPU-bound - run in thread
            asyncio.to_thread(self.get_linting_metrics),  # CPU-bound with subprocess
            return_exceptions=True
        )

        # Handle exceptions from gather
        if isinstance(coverage, Exception):
            logger.error(f"Coverage metrics failed: {coverage}")
            coverage = CoverageMetrics(0.0, 0.0, 0.0, 0.0, 0, 0, 0)
        if isinstance(naming, Exception):
            logger.error(f"Naming metrics failed: {naming}")
            naming = NamingConventionMetrics(0, 0, [], 0.0)
        if isinstance(file_structure, Exception):
            logger.error(f"File structure metrics failed: {file_structure}")
            file_structure = FileStructureMetrics(0, [], [], [], 0.0)
        if isinstance(linting, Exception):
            logger.error(f"Linting metrics failed: {linting}")
            linting = LintingMetrics(0, 0, 0, 0, 0, 0, 0)

        overall_score = self.calculate_overall_score(
            coverage, naming, file_structure, linting
        )

        return {
            'coverage': {
                'overall_coverage': coverage.overall_coverage,
                'backend_coverage': coverage.backend_coverage,
                'frontend_coverage': coverage.frontend_coverage,
                'adws_coverage': coverage.adws_coverage,
                'total_tests': coverage.total_tests
            },
            'naming': {
                'total_files_checked': naming.total_files_checked,
                'compliant_files': naming.compliant_files,
                'violations': naming.violations,
                'compliance_rate': naming.compliance_rate
            },
            'file_structure': {
                'total_files': file_structure.total_files,
                'oversized_files': file_structure.oversized_files,
                'long_files': file_structure.long_files,
                'avg_file_size_kb': file_structure.avg_file_size_kb
            },
            'linting': {
                'backend_issues': linting.backend_issues,
                'frontend_issues': linting.frontend_issues,
                'backend_errors': linting.backend_errors,
                'backend_warnings': linting.backend_warnings,
                'frontend_errors': linting.frontend_errors,
                'frontend_warnings': linting.frontend_warnings,
                'total_issues': linting.total_issues
            },
            'overall_score': overall_score,
            'last_updated': datetime.utcnow().isoformat()
        }

    def get_all_metrics(self) -> dict:
        """Get all QC metrics in one call (sync wrapper for backwards compat).

        Returns:
            Complete QC metrics dictionary
        """
        from datetime import datetime

        logger.info("Gathering all QC metrics...")

        coverage = asyncio.run(self.get_coverage_metrics()) if asyncio.get_event_loop().is_running() else self.get_coverage_metrics()
        naming = self.get_naming_convention_metrics()
        file_structure = self.get_file_structure_metrics()
        linting = self.get_linting_metrics()

        overall_score = self.calculate_overall_score(
            coverage, naming, file_structure, linting
        )

        return {
            'coverage': {
                'overall_coverage': coverage.overall_coverage,
                'backend_coverage': coverage.backend_coverage,
                'frontend_coverage': coverage.frontend_coverage,
                'adws_coverage': coverage.adws_coverage,
                'total_tests': coverage.total_tests
            },
            'naming': {
                'total_files_checked': naming.total_files_checked,
                'compliant_files': naming.compliant_files,
                'violations': naming.violations,
                'compliance_rate': naming.compliance_rate
            },
            'file_structure': {
                'total_files': file_structure.total_files,
                'oversized_files': file_structure.oversized_files,
                'long_files': file_structure.long_files,
                'avg_file_size_kb': file_structure.avg_file_size_kb
            },
            'linting': {
                'backend_issues': linting.backend_issues,
                'frontend_issues': linting.frontend_issues,
                'backend_errors': linting.backend_errors,
                'backend_warnings': linting.backend_warnings,
                'frontend_errors': linting.frontend_errors,
                'frontend_warnings': linting.frontend_warnings,
                'total_issues': linting.total_issues
            },
            'overall_score': overall_score,
            'last_updated': datetime.utcnow().isoformat()
        }
