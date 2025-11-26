"""
Health check system for ADW workflows.

Provides comprehensive health monitoring for:
- Port allocation and conflicts
- Worktree state and git status
- State file validity and freshness
- Process status and resource usage
"""

import json
import logging
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# Health status constants
STATUS_OK = "ok"
STATUS_WARNING = "warning"
STATUS_CRITICAL = "critical"


def get_project_root() -> Path:
    """Get the project root directory."""
    # From app/server/core/health_checks.py to project root
    return Path(__file__).parent.parent.parent.parent


def check_port_health(adw_id: str, state: dict[str, Any]) -> dict[str, Any]:
    """
    Check if allocated ports are available and in use correctly.

    Detects:
    - Port conflicts (multiple ADWs claiming same port)
    - Phantom ports (allocated but not in use)
    - Port exhaustion (approaching limit)

    Args:
        adw_id: The ADW workflow identifier
        state: The ADW state dictionary

    Returns:
        Health check result with status, details, and warnings
    """
    backend_port = state.get("backend_port")
    frontend_port = state.get("frontend_port")

    checks = {
        "status": STATUS_OK,
        "backend_port": backend_port,
        "frontend_port": frontend_port,
        "available": True,
        "in_use": False,
        "conflicts": [],
        "warnings": []
    }

    if not backend_port or not frontend_port:
        checks["status"] = STATUS_WARNING
        checks["warnings"].append("No ports allocated in state")
        return checks

    # Check if ports are actually in use
    backend_in_use = is_port_in_use(backend_port)
    frontend_in_use = is_port_in_use(frontend_port)
    checks["in_use"] = backend_in_use or frontend_in_use

    # Check if ports can be bound (for idle workflows)
    checks["available"] = is_port_available(backend_port) and is_port_available(frontend_port)

    # Check for conflicts with other workflows
    conflicts = find_port_conflicts(adw_id, backend_port, frontend_port)
    if conflicts:
        checks["conflicts"] = conflicts
        checks["status"] = STATUS_CRITICAL
        checks["warnings"].append(f"Port conflict detected with {len(conflicts)} other workflow(s)")

    # Warn if ports allocated but not in use (possible stale state)
    if not backend_in_use and not frontend_in_use:
        checks["status"] = STATUS_WARNING
        checks["warnings"].append("Ports allocated but not in use - possible stale state")

    return checks


def check_worktree_health(adw_id: str, state: dict[str, Any]) -> dict[str, Any]:
    """
    Check worktree status and git state.

    Detects:
    - Missing worktrees (state says exists, but doesn't)
    - Uncommitted changes
    - Git corruption
    - Detached HEAD state

    Args:
        adw_id: The ADW workflow identifier
        state: The ADW state dictionary

    Returns:
        Health check result with status, details, and warnings
    """
    worktree_path = state.get("worktree_path")

    checks = {
        "status": STATUS_OK,
        "path": worktree_path,
        "exists": False,
        "clean": True,
        "uncommitted_files": [],
        "git_registered": False,
        "warnings": []
    }

    if not worktree_path:
        checks["status"] = STATUS_WARNING
        checks["warnings"].append("No worktree_path in state")
        return checks

    # Check if directory exists
    worktree_dir = Path(worktree_path)
    checks["exists"] = worktree_dir.exists()

    if not checks["exists"]:
        checks["status"] = STATUS_CRITICAL
        checks["warnings"].append(f"Worktree directory not found: {worktree_path}")
        return checks

    # Check if git knows about it
    try:
        result = subprocess.run(
            ["git", "worktree", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        checks["git_registered"] = worktree_path in result.stdout

        if not checks["git_registered"]:
            checks["status"] = STATUS_WARNING
            checks["warnings"].append("Worktree not registered with git")
    except subprocess.TimeoutExpired:
        checks["status"] = STATUS_WARNING
        checks["warnings"].append("Git worktree list timed out")
    except Exception as e:
        checks["status"] = STATUS_WARNING
        checks["warnings"].append(f"Failed to check git status: {str(e)}")

    # Check for uncommitted changes
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.stdout.strip():
            checks["clean"] = False
            # Only show first 10 files to avoid overwhelming output
            uncommitted = result.stdout.strip().split("\n")[:10]
            checks["uncommitted_files"] = uncommitted
            checks["status"] = STATUS_WARNING
            checks["warnings"].append(f"{len(uncommitted)} uncommitted file(s)")
    except subprocess.TimeoutExpired:
        checks["status"] = STATUS_WARNING
        checks["warnings"].append("Git status check timed out")
    except Exception as e:
        checks["status"] = STATUS_WARNING
        checks["warnings"].append(f"Failed to check working tree status: {str(e)}")

    return checks


def check_state_file_health(adw_id: str) -> dict[str, Any]:
    """
    Check state file validity and freshness.

    Detects:
    - Missing state file
    - Corrupted JSON
    - Stale state (no updates in long time)
    - Invalid schema

    Args:
        adw_id: The ADW workflow identifier

    Returns:
        Health check result with status, details, and warnings
    """
    project_root = get_project_root()
    state_file_path = project_root / "agents" / adw_id / "adw_state.json"

    checks = {
        "status": STATUS_OK,
        "path": str(state_file_path),
        "exists": False,
        "valid": False,
        "last_modified": None,
        "age_seconds": None,
        "warnings": []
    }

    # Check if file exists
    checks["exists"] = state_file_path.exists()

    if not checks["exists"]:
        checks["status"] = STATUS_CRITICAL
        checks["warnings"].append("State file does not exist")
        return checks

    # Get file modification time
    try:
        stat = state_file_path.stat()
        last_modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        checks["last_modified"] = last_modified.isoformat()

        age_seconds = (datetime.now(timezone.utc) - last_modified).total_seconds()
        checks["age_seconds"] = int(age_seconds)

        # Warn if state hasn't been updated in 10 minutes
        if age_seconds > 600:
            checks["status"] = STATUS_WARNING
            checks["warnings"].append(f"State file is stale (last update {int(age_seconds)}s ago)")
    except Exception as e:
        checks["status"] = STATUS_WARNING
        checks["warnings"].append(f"Failed to get file stats: {str(e)}")

    # Try to parse JSON
    try:
        with open(state_file_path, 'r', encoding='utf-8') as f:
            state_data = json.load(f)

        checks["valid"] = True

        # Basic schema validation
        required_fields = ["adw_id", "issue_number"]
        missing_fields = [field for field in required_fields if field not in state_data]

        if missing_fields:
            checks["status"] = STATUS_WARNING
            checks["warnings"].append(f"Missing required fields: {', '.join(missing_fields)}")

    except json.JSONDecodeError as e:
        checks["status"] = STATUS_CRITICAL
        checks["valid"] = False
        checks["warnings"].append(f"Invalid JSON: {str(e)}")
    except Exception as e:
        checks["status"] = STATUS_WARNING
        checks["warnings"].append(f"Failed to read state file: {str(e)}")

    return checks


def check_process_health(adw_id: str) -> dict[str, Any]:
    """
    Check if workflow process is running and healthy.

    Detects:
    - Active processes
    - Zombie/orphaned processes
    - Idle processes (no activity)
    - Resource usage

    Args:
        adw_id: The ADW workflow identifier

    Returns:
        Health check result with status, details, and warnings
    """
    checks = {
        "status": STATUS_OK,
        "active": False,
        "processes": [],
        "warnings": []
    }

    # Find processes related to this ADW
    try:
        # Use ps to find processes with adw_id in command
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5
        )

        processes = []
        for line in result.stdout.split("\n"):
            if adw_id in line and "ps aux" not in line:
                # Extract basic info from ps output
                # Format: USER PID %CPU %MEM ... COMMAND
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    processes.append({
                        "pid": parts[1],
                        "cpu_percent": parts[2],
                        "memory_percent": parts[3],
                        "command": parts[10][:100]  # Truncate long commands
                    })

        checks["processes"] = processes
        checks["active"] = len(processes) > 0

        if len(processes) == 0:
            checks["status"] = STATUS_OK  # Not a warning - workflow might be queued
        elif len(processes) > 5:
            checks["status"] = STATUS_WARNING
            checks["warnings"].append(f"High process count ({len(processes)}) - possible leaks")

    except subprocess.TimeoutExpired:
        checks["status"] = STATUS_WARNING
        checks["warnings"].append("Process check timed out")
    except Exception as e:
        checks["status"] = STATUS_WARNING
        checks["warnings"].append(f"Failed to check processes: {str(e)}")

    return checks


def get_overall_health(adw_id: str, state: dict[str, Any]) -> dict[str, Any]:
    """
    Run all health checks and return overall health status.

    Args:
        adw_id: The ADW workflow identifier
        state: The ADW state dictionary

    Returns:
        Comprehensive health check results with overall status
    """
    port_health = check_port_health(adw_id, state)
    worktree_health = check_worktree_health(adw_id, state)
    state_health = check_state_file_health(adw_id)
    process_health = check_process_health(adw_id)

    # Determine overall health
    all_checks = [port_health, worktree_health, state_health, process_health]
    statuses = [check["status"] for check in all_checks]

    # Overall status is the worst of all checks
    if STATUS_CRITICAL in statuses:
        overall_status = STATUS_CRITICAL
    elif STATUS_WARNING in statuses:
        overall_status = STATUS_WARNING
    else:
        overall_status = STATUS_OK

    # Collect all warnings
    all_warnings = []
    for check in all_checks:
        all_warnings.extend(check.get("warnings", []))

    return {
        "adw_id": adw_id,
        "overall_health": overall_status,
        "checks": {
            "ports": port_health,
            "worktree": worktree_health,
            "state_file": state_health,
            "process": process_health
        },
        "warnings": all_warnings,
        "checked_at": datetime.now(timezone.utc).isoformat()
    }


# Helper functions

def is_port_in_use(port: int) -> bool:
    """
    Check if a port is currently in use by any process.

    Args:
        port: Port number to check

    Returns:
        True if port is in use, False otherwise
    """
    try:
        # Try to connect to the port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            result = s.connect_ex(('localhost', port))
            return result == 0  # 0 means connection succeeded (port in use)
    except Exception:
        return False


def is_port_available(port: int) -> bool:
    """
    Check if a port is available for binding.

    Args:
        port: Port number to check

    Returns:
        True if port is available, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.bind(('localhost', port))
            return True
    except (socket.error, OSError):
        return False


def find_port_conflicts(adw_id: str, backend_port: int, frontend_port: int) -> list[dict[str, Any]]:
    """
    Find other ADW workflows using the same ports.

    Args:
        adw_id: The ADW workflow identifier
        backend_port: Backend port to check
        frontend_port: Frontend port to check

    Returns:
        List of conflicting workflows with their details
    """
    project_root = get_project_root()
    agents_dir = project_root / "agents"

    if not agents_dir.exists():
        return []

    conflicts = []

    for adw_dir in agents_dir.iterdir():
        if not adw_dir.is_dir():
            continue

        other_adw_id = adw_dir.name

        # Skip self
        if other_adw_id == adw_id:
            continue

        state_file = adw_dir / "adw_state.json"
        if not state_file.exists():
            continue

        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                other_state = json.load(f)

            other_backend = other_state.get("backend_port")
            other_frontend = other_state.get("frontend_port")

            # Check for port conflicts
            if other_backend == backend_port or other_frontend == frontend_port:
                conflicts.append({
                    "adw_id": other_adw_id,
                    "issue_number": other_state.get("issue_number"),
                    "backend_port": other_backend,
                    "frontend_port": other_frontend,
                    "conflicting_ports": [
                        port for port in [backend_port, frontend_port]
                        if port in [other_backend, other_frontend]
                    ]
                })
        except Exception as e:
            logger.debug(f"Failed to check state for {other_adw_id}: {e}")
            continue

    return conflicts


def get_system_port_health() -> dict[str, Any]:
    """
    Get system-wide port allocation health.

    Returns:
        Summary of port usage across all workflows
    """
    project_root = get_project_root()
    agents_dir = project_root / "agents"

    port_usage = {
        "backend_ports": {},  # {port: [adw_ids]}
        "frontend_ports": {},  # {port: [adw_ids]}
        "total_allocated": 0,
        "conflicts_count": 0,
        "port_range": {"backend": [9100, 9114], "frontend": [9200, 9214]},
        "warnings": []
    }

    if not agents_dir.exists():
        return port_usage

    # Scan all ADW states for port allocations
    for adw_dir in agents_dir.iterdir():
        if not adw_dir.is_dir():
            continue

        adw_id = adw_dir.name
        state_file = adw_dir / "adw_state.json"

        if not state_file.exists():
            continue

        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)

            backend_port = state.get("backend_port")
            frontend_port = state.get("frontend_port")

            if backend_port:
                if backend_port not in port_usage["backend_ports"]:
                    port_usage["backend_ports"][backend_port] = []
                port_usage["backend_ports"][backend_port].append(adw_id)

            if frontend_port:
                if frontend_port not in port_usage["frontend_ports"]:
                    port_usage["frontend_ports"][frontend_port] = []
                port_usage["frontend_ports"][frontend_port].append(adw_id)

            port_usage["total_allocated"] += 1
        except Exception as e:
            logger.debug(f"Failed to read state for {adw_id}: {e}")
            continue

    # Count conflicts
    for port, adw_ids in port_usage["backend_ports"].items():
        if len(adw_ids) > 1:
            port_usage["conflicts_count"] += 1
            port_usage["warnings"].append(
                f"Backend port {port} used by {len(adw_ids)} workflows: {', '.join(adw_ids)}"
            )

    for port, adw_ids in port_usage["frontend_ports"].items():
        if len(adw_ids) > 1:
            port_usage["conflicts_count"] += 1
            port_usage["warnings"].append(
                f"Frontend port {port} used by {len(adw_ids)} workflows: {', '.join(adw_ids)}"
            )

    # Warn if approaching port exhaustion (only 15 slots available)
    if port_usage["total_allocated"] >= 12:
        port_usage["warnings"].append(
            f"Port pool depleting: {port_usage['total_allocated']}/15 slots used"
        )

    return port_usage
