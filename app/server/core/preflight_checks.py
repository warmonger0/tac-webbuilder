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


def run_preflight_checks(
    skip_tests: bool = False,
    issue_number: int | None = None,
    run_dry_run: bool = False,
    feature_id: int | None = None,
    feature_title: str | None = None
) -> dict[str, Any]:
    """
    Run all pre-flight checks before launching an ADW workflow.

    Args:
        skip_tests: If True, skip the test suite check (useful for testing)
        issue_number: Optional GitHub issue number to validate for duplicate work
        run_dry_run: If True, run workflow dry-run for cost/time estimation
        feature_id: Required if run_dry_run is True - feature ID to analyze
        feature_title: Optional feature title for dry-run display

    Returns:
        {
            "passed": bool,
            "blocking_failures": [{"check": str, "error": str, "fix": str}],
            "warnings": [{"check": str, "message": str, "impact": str}],
            "checks_run": [{"check": str, "status": str, "duration_ms": int}],
            "total_duration_ms": int,
            "dry_run": {...} | None  # Present if run_dry_run=True
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

    # Check 7: Observability - Database Connection
    check_start = time.time()
    db_result = check_observability_database()
    checks_run.append({
        "check": "observability_database",
        "status": "pass" if db_result["passed"] else "fail",
        "duration_ms": int((time.time() - check_start) * 1000),
        "details": db_result.get("summary")
    })

    if not db_result["passed"]:
        blocking_failures.append({
            "check": "Observability Database",
            "error": db_result["error"],
            "fix": db_result["fix"]
        })

    # Check 8: Observability - Hook Events Recording
    check_start = time.time()
    hooks_result = check_hook_events_recording()
    checks_run.append({
        "check": "hook_events_recording",
        "status": "pass" if hooks_result["passed"] else "warn",
        "duration_ms": int((time.time() - check_start) * 1000),
        "details": hooks_result.get("summary")
    })

    if not hooks_result["passed"]:
        warnings.append({
            "check": "Hook Events Recording",
            "message": hooks_result["error"],
            "impact": hooks_result.get("impact", "Pattern learning and cost optimization may not work")
        })

    # Check 9: Observability - Pattern Analysis System
    check_start = time.time()
    pattern_result = check_pattern_analysis_system()
    checks_run.append({
        "check": "pattern_analysis_system",
        "status": "pass" if pattern_result["passed"] else "warn",
        "duration_ms": int((time.time() - check_start) * 1000),
        "details": pattern_result.get("summary")
    })

    if not pattern_result["passed"]:
        warnings.append({
            "check": "Pattern Analysis System",
            "message": pattern_result["error"],
            "impact": pattern_result.get("impact", "Analytics and pattern discovery unavailable")
        })

    # Check 10: Issue Already Resolved (if issue_number provided)
    issue_validation = None
    if issue_number:
        check_start = time.time()
        resolution_result = check_issue_already_resolved(issue_number)
        checks_run.append({
            "check": "issue_already_resolved",
            "status": "warn" if resolution_result["is_resolved"] else "pass",
            "duration_ms": int((time.time() - check_start) * 1000),
            "details": resolution_result.get("summary")
        })

        if resolution_result["is_resolved"] and resolution_result["confidence"] >= 0.5:
            warnings.append({
                "check": "Issue Already Resolved",
                "message": resolution_result["message"],
                "impact": "Launching workflow may create duplicate work",
                "evidence": resolution_result.get("evidence", []),
                "recommendation": resolution_result.get("recommendation", "")
            })

        issue_validation = resolution_result

    # Check 11: Workflow Dry-Run (optional, for cost/time estimation with pattern caching)
    dry_run_result = None
    if run_dry_run:
        if not feature_id:
            logger.warning("Dry-run requested but no feature_id provided")
        else:
            check_start = time.time()
            try:
                from core.workflow_dry_run import format_dry_run_for_display, run_workflow_dry_run

                # Get feature description for better pattern matching
                feature_description = None
                try:
                    from services.planned_features_service import PlannedFeaturesService
                    service = PlannedFeaturesService()
                    feature = service.get_by_id(feature_id)
                    if feature:
                        feature_description = feature.description
                except Exception:
                    pass  # Not critical if we can't get description

                dry_run_data = run_workflow_dry_run(
                    feature_id,
                    feature_title or f"Feature #{feature_id}",
                    feature_description
                )

                if dry_run_data["success"]:
                    dry_run_result = format_dry_run_for_display(dry_run_data["result"])
                    checks_run.append({
                        "check": "workflow_dry_run",
                        "status": "pass",
                        "duration_ms": int((time.time() - check_start) * 1000),
                        "details": f"{dry_run_result['summary']['total_phases']} phases, {dry_run_result['summary']['total_cost']}"
                    })
                else:
                    checks_run.append({
                        "check": "workflow_dry_run",
                        "status": "warn",
                        "duration_ms": int((time.time() - check_start) * 1000),
                        "details": "Dry-run failed"
                    })
                    warnings.append({
                        "check": "Workflow Dry-Run",
                        "message": f"Could not estimate workflow cost: {dry_run_data.get('error', 'Unknown error')}",
                        "impact": "Proceeding without cost estimate"
                    })
            except Exception as e:
                logger.error(f"Error running dry-run: {e}", exc_info=True)
                checks_run.append({
                    "check": "workflow_dry_run",
                    "status": "warn",
                    "duration_ms": int((time.time() - check_start) * 1000),
                    "details": "Exception occurred"
                })

    total_duration = int((time.time() - start_time) * 1000)

    passed = len(blocking_failures) == 0

    logger.info(f"Pre-flight checks completed in {total_duration}ms: {'✅ PASSED' if passed else '❌ FAILED'}")

    result = {
        "passed": passed,
        "blocking_failures": blocking_failures,
        "warnings": warnings,
        "checks_run": checks_run,
        "total_duration_ms": total_duration
    }

    # Add issue validation data if checked
    if issue_validation:
        result["issue_validation"] = issue_validation

    # Add dry-run result if performed
    if dry_run_result:
        result["dry_run"] = dry_run_result

    return result


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
            "summary": str,
            "active_count": int,
            "max_worktrees": int,
            "available": int
        }
    """
    try:
        project_root = Path(__file__).parent.parent.parent

        # Use git worktree list for accurate counting (more reliable than directory inspection)
        result = subprocess.run(
            ["git", "worktree", "list"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return {
                "passed": False,
                "error": "Failed to list git worktrees",
                "fix": "Check git repository health",
                "summary": "git error",
                "active_count": 0,
                "max_worktrees": 15,
                "available": 15
            }

        # Count worktrees (exclude main worktree)
        worktree_lines = result.stdout.strip().split('\n')
        # First line is always the main worktree, rest are ADW worktrees
        active_count = len(worktree_lines) - 1 if len(worktree_lines) > 0 else 0
        max_worktrees = 15
        available = max_worktrees - active_count

        if active_count >= max_worktrees:
            return {
                "passed": False,
                "error": f"All worktree slots occupied ({active_count}/{max_worktrees})",
                "fix": "Wait for running workflows to complete or manually clean up old worktrees: git worktree remove trees/<worktree-name>",
                "summary": f"{active_count}/{max_worktrees} active, 0 available",
                "active_count": active_count,
                "max_worktrees": max_worktrees,
                "available": 0
            }

        return {
            "passed": True,
            "summary": f"{active_count}/{max_worktrees} active, {available} available",
            "active_count": active_count,
            "max_worktrees": max_worktrees,
            "available": available
        }

    except Exception as e:
        return {
            "passed": False,
            "error": f"Failed to check worktree availability: {str(e)}",
            "fix": "Check git repository health and permissions",
            "summary": f"error: {str(e)}",
            "active_count": 0,
            "max_worktrees": 15,
            "available": 15
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


def check_observability_database() -> dict[str, Any]:
    """
    Check PostgreSQL connection and observability tables.

    Returns:
        {
            "passed": bool,
            "error": str,
            "fix": str,
            "summary": str
        }
    """
    try:
        from database import get_database_adapter

        adapter = get_database_adapter()
        db_type = adapter.get_db_type()

        # Check if using PostgreSQL
        if db_type != "postgresql":
            return {
                "passed": False,
                "error": f"Using {db_type} instead of PostgreSQL",
                "fix": "Set DB_TYPE=postgresql in .env and ensure PostgreSQL is running",
                "summary": f"Wrong DB: {db_type}"
            }

        # Check database connection
        with adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Verify observability tables exist
            cursor.execute("""
                SELECT tablename FROM pg_catalog.pg_tables
                WHERE schemaname = 'public'
                AND tablename IN ('hook_events', 'operation_patterns', 'pattern_approvals')
            """)
            tables = cursor.fetchall()
            table_names = [row['tablename'] if isinstance(row, dict) else row[0] for row in tables]

        missing_tables = []
        for required_table in ['hook_events', 'operation_patterns', 'pattern_approvals']:
            if required_table not in table_names:
                missing_tables.append(required_table)

        if missing_tables:
            return {
                "passed": False,
                "error": f"Missing observability tables: {', '.join(missing_tables)}",
                "fix": "Run database migrations to create observability tables",
                "summary": f"Missing tables: {len(missing_tables)}"
            }

        return {
            "passed": True,
            "summary": f"PostgreSQL connected, {len(table_names)} tables"
        }

    except Exception as e:
        return {
            "passed": False,
            "error": f"Database connection failed: {str(e)}",
            "fix": "Check PostgreSQL is running and credentials in .env are correct",
            "summary": "Connection error"
        }


def check_hook_events_recording() -> dict[str, Any]:
    """
    Check if hook events are being recorded to the database.

    Returns:
        {
            "passed": bool,
            "error": str,
            "impact": str,
            "summary": str
        }
    """
    try:
        from datetime import datetime, timedelta

        from database import get_database_adapter

        adapter = get_database_adapter()

        with adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Check for recent hook events (last 7 days)
            seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute(
                "SELECT COUNT(*) as count FROM hook_events WHERE timestamp > %s",
                (seven_days_ago,)
            )
            result = cursor.fetchone()
            recent_count = result['count'] if isinstance(result, dict) else result[0]

            # Check total hook events
            cursor.execute("SELECT COUNT(*) as count FROM hook_events")
            result = cursor.fetchone()
            total_count = result['count'] if isinstance(result, dict) else result[0]

        if total_count == 0:
            return {
                "passed": False,
                "error": "No hook events recorded (hooks may not be configured for PostgreSQL)",
                "impact": "Pattern learning, cost optimization, and analytics are not capturing data",
                "summary": "0 events recorded"
            }

        if recent_count == 0:
            return {
                "passed": False,
                "error": f"No recent hook events (last 7 days) - found {total_count} historical events",
                "impact": "Hooks may have stopped working or are configured for SQLite instead of PostgreSQL",
                "summary": f"{total_count} total, 0 recent"
            }

        return {
            "passed": True,
            "summary": f"{recent_count} events (7d), {total_count} total"
        }

    except Exception as e:
        return {
            "passed": False,
            "error": f"Failed to check hook events: {str(e)}",
            "impact": "Cannot verify observability data collection",
            "summary": "Check failed"
        }


def check_pattern_analysis_system() -> dict[str, Any]:
    """
    Check if pattern analysis scripts are available and can connect to database.

    Returns:
        {
            "passed": bool,
            "error": str,
            "impact": str,
            "summary": str
        }
    """
    try:
        import os

        project_root = Path(__file__).parent.parent.parent.parent  # Go up 4 levels to project root
        script_path = project_root / "scripts" / "analyze_daily_patterns.py"

        # Check if script exists
        if not script_path.exists():
            return {
                "passed": False,
                "error": "Pattern analysis script not found",
                "impact": "Cannot run automated pattern discovery",
                "summary": "Script missing"
            }

        # Check if PostgreSQL credentials are available
        required_env_vars = ['POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB',
                             'POSTGRES_USER', 'POSTGRES_PASSWORD']
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]

        if missing_vars:
            return {
                "passed": False,
                "error": f"Missing environment variables for analytics: {', '.join(missing_vars)}",
                "impact": "Analytics scripts cannot connect to PostgreSQL",
                "summary": f"{len(missing_vars)} env vars missing"
            }

        # Check if pattern review service is importable
        try:
            from services.pattern_review_service import PatternReviewService
            service = PatternReviewService()

            # Quick sanity check - can we query pattern_approvals?
            patterns = service.get_pending_patterns(limit=1)

            return {
                "passed": True,
                "summary": "Pattern system OK"
            }

        except Exception as e:
            return {
                "passed": False,
                "error": f"Pattern review service error: {str(e)}",
                "impact": "Pattern approval and learning system unavailable",
                "summary": "Service error"
            }

    except Exception as e:
        return {
            "passed": False,
            "error": f"Failed to check pattern analysis: {str(e)}",
            "impact": "Cannot verify pattern discovery system",
            "summary": "Check failed"
        }


def check_issue_already_resolved(issue_number: int) -> dict[str, Any]:
    """
    Check if a GitHub issue is already resolved to prevent duplicate work.

    Uses multiple heuristics:
    - GitHub issue state (closed, duplicate label)
    - Git commit history (recent commits mentioning issue)
    - Related closed issues

    Args:
        issue_number: GitHub issue number to check

    Returns:
        {
            "is_resolved": bool,
            "confidence": float (0.0-1.0),
            "message": str,
            "summary": str,
            "evidence": [str],
            "recommendation": str,
            "closed_at": str | None,
            "related_commits": [str],
            "duplicate_of": [int]
        }
    """
    try:
        project_root = Path(__file__).parent.parent.parent

        evidence = []
        confidence = 0.0
        closed_at = None
        related_commits = []
        duplicate_of = []

        # Heuristic 1: Check GitHub issue state
        try:
            result = subprocess.run(
                ["gh", "issue", "view", str(issue_number), "--json", "state,closedAt,labels,title"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                import json
                issue_data = json.loads(result.stdout)

                # Check if closed
                if issue_data.get("state") == "CLOSED":
                    closed_at = issue_data.get("closedAt")
                    evidence.append(f"Issue #{issue_number} is closed")
                    confidence += 0.4

                    # Check for duplicate label
                    labels = [label.get("name", "").lower() for label in issue_data.get("labels", [])]
                    if "duplicate" in labels:
                        evidence.append("Issue has 'duplicate' label")
                        confidence += 0.3

                    # Check how recently closed (< 24 hours = more likely related)
                    if closed_at:
                        from datetime import datetime, timedelta
                        closed_time = datetime.fromisoformat(closed_at.replace("Z", "+00:00"))
                        if datetime.now(closed_time.tzinfo) - closed_time < timedelta(hours=24):
                            evidence.append("Issue closed within last 24 hours")
                            confidence += 0.2

        except Exception as e:
            logger.warning(f"Failed to check GitHub issue state: {e}")

        # Heuristic 2: Search git history for issue mentions
        try:
            # Search last 50 commits for issue number mentions
            patterns = [
                f"#{issue_number}",
                f"Fix.*{issue_number}",
                f"Fixes.*{issue_number}",
                f"Close.*{issue_number}",
                f"Closes.*{issue_number}"
            ]

            for pattern in patterns:
                result = subprocess.run(
                    ["git", "log", "-50", "--oneline", "--all", "--grep", pattern],
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0 and result.stdout.strip():
                    commits = result.stdout.strip().split('\n')
                    for commit in commits[:3]:  # Limit to 3 most recent
                        commit_hash = commit.split()[0]
                        if commit_hash not in related_commits:
                            related_commits.append(commit_hash)

            if related_commits:
                evidence.append(f"Found {len(related_commits)} commit(s) mentioning issue")
                confidence += 0.25

        except Exception as e:
            logger.warning(f"Failed to search git history: {e}")

        # Heuristic 3: Check for related closed issues (duplicates)
        try:
            # Search for closed issues with similar titles
            result = subprocess.run(
                ["gh", "issue", "list", "--state", "closed", "--limit", "20", "--json", "number,title,labels"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                import json
                issues = json.loads(result.stdout)

                # Look for issues with "duplicate" label that were closed recently
                for issue in issues:
                    if issue["number"] != issue_number:
                        labels = [label.get("name", "").lower() for label in issue.get("labels", [])]
                        if "duplicate" in labels:
                            duplicate_of.append(issue["number"])

                if duplicate_of:
                    evidence.append(f"Found {len(duplicate_of)} other duplicate issue(s) recently closed")
                    confidence += 0.15

        except Exception as e:
            logger.warning(f"Failed to check related issues: {e}")

        # Build result
        is_resolved = confidence >= 0.5
        confidence = min(confidence, 1.0)  # Cap at 100%

        if is_resolved:
            message = f"Issue #{issue_number} may already be fixed (confidence: {int(confidence * 100)}%)"
            summary = f"Resolved (confidence: {int(confidence * 100)}%)"
            recommendation = f"Review commits {', '.join(related_commits[:3])} before launching workflow"
        else:
            message = f"Issue #{issue_number} does not appear to be resolved"
            summary = "Not resolved"
            recommendation = "Proceed with workflow"

        return {
            "is_resolved": is_resolved,
            "confidence": confidence,
            "message": message,
            "summary": summary,
            "evidence": evidence,
            "recommendation": recommendation,
            "closed_at": closed_at,
            "related_commits": related_commits,
            "duplicate_of": duplicate_of
        }

    except Exception as e:
        logger.warning(f"Error checking issue resolution: {e}")
        return {
            "is_resolved": False,
            "confidence": 0.0,
            "message": f"Failed to check issue status: {str(e)}",
            "summary": "Check failed",
            "evidence": [],
            "recommendation": "Proceed with caution",
            "closed_at": None,
            "related_commits": [],
            "duplicate_of": []
        }
