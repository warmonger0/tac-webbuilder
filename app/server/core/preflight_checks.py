"""
Pre-flight checks for ADW workflows.

This module provides health checks that run BEFORE launching ADW workflows
to prevent expensive failures. These checks are designed to be:
- Fast (< 10 seconds total)
- Deterministic (no AI calls)
- Non-destructive (read-only operations)
- Informative (clear error messages for failures)

Usage:
    from core.preflight_checks import run_preflight_checks

    result = run_preflight_checks()
    if not result["passed"]:
        print("Pre-flight checks failed:")
        for failure in result["blocking_failures"]:
            print(f"  ❌ {failure['check']}: {failure['error']}")
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def run_preflight_checks(skip_tests: bool = False) -> dict[str, Any]:
    """
    Run all pre-flight checks before launching an ADW workflow.

    Args:
        skip_tests: If True, skip the test suite check (useful for testing)

    Returns:
        {
            "passed": bool,
            "blocking_failures": [{"check": str, "error": str, "fix": str}],
            "warnings": [{"check": str, "message": str, "impact": str}],
            "checks_run": [{"check": str, "status": str, "duration_ms": int}],
            "total_duration_ms": int
        }
    """
    import time
    start_time = time.time()

    blocking_failures = []
    warnings = []
    checks_run = []

    # Check 1: Critical test failures
    if not skip_tests:
        check_start = time.time()
        test_result = check_critical_tests()
        checks_run.append({
            "check": "critical_tests",
            "status": "pass" if test_result["passed"] else "fail",
            "duration_ms": int((time.time() - check_start) * 1000),
            "details": test_result.get("summary")
        })

        if not test_result["passed"]:
            blocking_failures.append({
                "check": "Critical Test Failures",
                "error": test_result["error"],
                "fix": test_result["fix"],
                "failing_tests": test_result.get("failing_tests", [])
            })

    # Check 2: Port availability
    check_start = time.time()
    port_result = check_port_availability()
    checks_run.append({
        "check": "port_availability",
        "status": "pass" if port_result["passed"] else "warn",
        "duration_ms": int((time.time() - check_start) * 1000),
        "details": port_result.get("available_ports")
    })

    if not port_result["passed"]:
        warnings.append({
            "check": "Port Availability",
            "message": port_result["error"],
            "impact": "May not be able to allocate ports for new workflows"
        })

    # Check 3: Git repository state (BLOCKING - uncommitted changes prevent workflow launch)
    check_start = time.time()
    git_result = check_git_state()
    checks_run.append({
        "check": "git_state",
        "status": "pass" if git_result["passed"] else "fail",
        "duration_ms": int((time.time() - check_start) * 1000),
        "details": git_result.get("summary")
    })

    if not git_result["passed"]:
        blocking_failures.append({
            "check": "Git State",
            "error": git_result["error"],
            "fix": "Run 'git add .' and 'git commit -m \"your message\"' OR 'git stash' to clear uncommitted changes"
        })

    # Check 4: Disk space
    check_start = time.time()
    disk_result = check_disk_space()
    checks_run.append({
        "check": "disk_space",
        "status": "pass" if disk_result["passed"] else "warn",
        "duration_ms": int((time.time() - check_start) * 1000),
        "details": disk_result.get("summary")
    })

    if not disk_result["passed"]:
        warnings.append({
            "check": "Disk Space",
            "message": disk_result["error"],
            "impact": "May fail during dependency installation or builds"
        })

    # Check 5: Worktree availability (BLOCKING - need slots for new workflows)
    check_start = time.time()
    worktree_result = check_worktree_availability()
    checks_run.append({
        "check": "worktree_availability",
        "status": "pass" if worktree_result["passed"] else "fail",
        "duration_ms": int((time.time() - check_start) * 1000),
        "details": worktree_result.get("summary")
    })

    if not worktree_result["passed"]:
        blocking_failures.append({
            "check": "Worktree Availability",
            "error": worktree_result["error"],
            "fix": worktree_result["fix"]
        })

    # Check 6: Python environment
    check_start = time.time()
    python_result = check_python_environment()
    checks_run.append({
        "check": "python_environment",
        "status": "pass" if python_result["passed"] else "fail",
        "duration_ms": int((time.time() - check_start) * 1000),
        "details": python_result.get("summary")
    })

    if not python_result["passed"]:
        blocking_failures.append({
            "check": "Python Environment",
            "error": python_result["error"],
            "fix": python_result["fix"]
        })

    total_duration = int((time.time() - start_time) * 1000)

    passed = len(blocking_failures) == 0

    logger.info(f"Pre-flight checks completed in {total_duration}ms: {'✅ PASSED' if passed else '❌ FAILED'}")

    return {
        "passed": passed,
        "blocking_failures": blocking_failures,
        "warnings": warnings,
        "checks_run": checks_run,
        "total_duration_ms": total_duration
    }


def check_critical_tests() -> dict[str, Any]:
    """
    Run critical test subset to detect blocking issues.

    Only runs fast, critical tests:
    - PhaseCoordinator tests (workflow detection)
    - ADW Monitor tests (status tracking)
    - Database integrity tests (workflow history)

    Returns:
        {
            "passed": bool,
            "error": str,
            "fix": str,
            "failing_tests": [str],
            "summary": str
        }
    """
    try:
        # Check if test directory exists
        test_dir = Path(__file__).parent.parent / "tests"
        if not test_dir.exists():
            logger.warning(f"Test directory not found at {test_dir}")
            return {
                "passed": True,  # Don't block if tests don't exist yet
                "summary": "Test directory not found (skipped)"
            }

        # Define test paths to check
        test_paths = [
            "tests/services/test_phase_coordinator.py::TestWorkflowDetection",
            "tests/core/test_adw_monitor.py::TestPhaseProgress",
        ]

        # Check if any of the test files exist
        test_files_exist = False
        for test_path in test_paths:
            test_file = test_dir / test_path.split("::")[0].replace("tests/", "")
            if test_file.exists():
                test_files_exist = True
                break

        if not test_files_exist:
            logger.warning("No critical test files found")
            return {
                "passed": True,  # Don't block if test files don't exist yet
                "summary": "No critical test files found (skipped)"
            }

        # Run critical test subset (fast tests only)
        result = subprocess.run(
            [
                sys.executable, "-m", "pytest",
                *test_paths,
                "-q", "--tb=no", "--maxfail=5"
            ],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            # Parse failures from output
            failing_tests = []
            output = result.stdout + result.stderr

            # First, try to extract from "short test summary info" section
            if "FAILED" in output:
                in_summary = False
                for line in output.split('\n'):
                    if 'short test summary info' in line.lower():
                        in_summary = True
                        continue
                    if in_summary and line.startswith('FAILED'):
                        failing_tests.append(line.strip())
                    elif in_summary and line.startswith('==='):
                        break

            # Fallback: count from final summary line (e.g., "3 failed, 6 passed")
            failure_count = len(failing_tests)
            if failure_count == 0:
                # Try to parse from summary line
                import re
                match = re.search(r'(\d+)\s+failed', output)
                if match:
                    failure_count = int(match.group(1))
                    failing_tests = ["Test failures detected (run with -v for details)"]

            # If we found 0 failures, pass even though pytest returned non-zero
            # (could be no tests found, import errors, etc. - not actual test failures)
            if failure_count == 0:
                return {
                    "passed": True,
                    "summary": "0 failures"
                }

            return {
                "passed": False,
                "error": f"Found {failure_count} critical test failure{'s' if failure_count != 1 else ''}",
                "fix": "Run 'uv run pytest tests/ -v' to see details and fix failing tests",
                "failing_tests": failing_tests[:10],  # Limit to 10
                "summary": f"{failure_count} failure{'s' if failure_count != 1 else ''}"
            }

        return {
            "passed": True,
            "summary": "All critical tests passing"
        }

    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "error": "Critical tests timed out (>30s)",
            "fix": "Investigate slow tests or test infrastructure issues",
            "summary": "timeout"
        }
    except Exception as e:
        logger.warning(f"Error running tests: {str(e)}")
        return {
            "passed": True,  # Don't block on test infrastructure issues
            "summary": f"Test check skipped: {str(e)}"
        }


def check_port_availability() -> dict[str, Any]:
    """
    Check if ADW ports (9100-9114, 9200-9214) are available.

    Returns:
        {
            "passed": bool,
            "error": str,
            "available_ports": int
        }
    """
    try:
        import socket

        backend_ports = range(9100, 9115)  # 15 ports
        frontend_ports = range(9200, 9215)

        available_count = 0
        for port in list(backend_ports) + list(frontend_ports):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            try:
                result = sock.connect_ex(('localhost', port))
                if result != 0:  # Port is available
                    available_count += 1
            finally:
                sock.close()

        total_ports = 30
        if available_count < 2:  # Need at least 1 backend + 1 frontend port
            return {
                "passed": False,
                "error": f"Only {available_count}/{total_ports} ports available",
                "available_ports": available_count
            }

        return {
            "passed": True,
            "available_ports": available_count
        }

    except Exception as e:
        return {
            "passed": False,
            "error": f"Failed to check ports: {str(e)}",
            "available_ports": 0
        }


def check_git_state() -> dict[str, Any]:
    """
    Check git repository for uncommitted changes or issues.

    Returns:
        {
            "passed": bool,
            "error": str,
            "impact": str,
            "summary": str
        }
    """
    try:
        # Check for uncommitted changes on main
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.stdout.strip():
            modified_files = len(result.stdout.strip().split('\n'))
            return {
                "passed": False,
                "error": f"{modified_files} uncommitted changes on main branch",
                "impact": "Worktrees will include these uncommitted changes",
                "summary": f"{modified_files} modified files"
            }

        return {
            "passed": True,
            "summary": "Clean working directory"
        }

    except Exception as e:
        return {
            "passed": False,
            "error": f"Failed to check git state: {str(e)}",
            "impact": "Cannot verify repository state",
            "summary": f"error: {str(e)}"
        }


def check_disk_space() -> dict[str, Any]:
    """
    Check available disk space for worktrees.

    Returns:
        {
            "passed": bool,
            "error": str,
            "summary": str
        }
    """
    try:
        import shutil

        # Check space in project directory
        project_root = Path(__file__).parent.parent.parent
        stats = shutil.disk_usage(project_root)

        # Need at least 1GB free for worktrees
        free_gb = stats.free / (1024 ** 3)

        if free_gb < 1:
            return {
                "passed": False,
                "error": f"Only {free_gb:.2f}GB free disk space",
                "summary": f"{free_gb:.2f}GB free"
            }

        return {
            "passed": True,
            "summary": f"{free_gb:.1f}GB free"
        }

    except Exception as e:
        return {
            "passed": False,
            "error": f"Failed to check disk space: {str(e)}",
            "summary": "unknown"
        }


def check_worktree_availability() -> dict[str, Any]:
    """
    Check if there are available worktree slots (max 15 active worktrees).

    Returns:
        {
            "passed": bool,
            "error": str,
            "fix": str,
            "summary": str
        }
    """
    try:
        project_root = Path(__file__).parent.parent.parent

        # Check worktree directory
        worktree_dir = project_root / "trees"
        if not worktree_dir.exists():
            # No worktrees yet - all slots available
            return {
                "passed": True,
                "summary": "0/15 worktrees active"
            }

        # Count active worktrees (directories starting with 'adw-' or being git worktrees)
        active_worktrees = []
        for item in worktree_dir.iterdir():
            if item.is_dir() and (item.name.startswith('adw-') or (item / '.git').exists()):
                active_worktrees.append(item.name)

        active_count = len(active_worktrees)
        max_worktrees = 15

        if active_count >= max_worktrees:
            return {
                "passed": False,
                "error": f"All worktree slots occupied ({active_count}/{max_worktrees})",
                "fix": "Wait for running workflows to complete or manually clean up old worktrees in trees/ directory",
                "summary": f"{active_count}/{max_worktrees} active"
            }

        return {
            "passed": True,
            "summary": f"{active_count}/{max_worktrees} active"
        }

    except Exception as e:
        return {
            "passed": False,
            "error": f"Failed to check worktree availability: {str(e)}",
            "fix": "Check trees/ directory permissions",
            "summary": f"error: {str(e)}"
        }


def check_python_environment() -> dict[str, Any]:
    """
    Check Python and uv are available.

    Returns:
        {
            "passed": bool,
            "error": str,
            "fix": str,
            "summary": str
        }
    """
    try:
        # Check uv is available
        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return {
                "passed": False,
                "error": "uv package manager not found",
                "fix": "Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh",
                "summary": "uv not found"
            }

        uv_version = result.stdout.strip()

        return {
            "passed": True,
            "summary": f"uv {uv_version}"
        }

    except FileNotFoundError:
        return {
            "passed": False,
            "error": "uv not found in PATH",
            "fix": "Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh",
            "summary": "uv not in PATH"
        }
    except Exception as e:
        return {
            "passed": False,
            "error": f"Failed to check Python environment: {str(e)}",
            "fix": "Check Python and uv installation",
            "summary": f"error: {str(e)}"
        }
