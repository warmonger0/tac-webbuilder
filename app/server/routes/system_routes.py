"""
System health and service control endpoints.
"""
import logging
from datetime import datetime

from core.data_models import (
    AdwHealthCheckResponse,
    AdwMonitorResponse,
    HealthCheckResponse,
    SystemStatusResponse,
)
from core.preflight_checks import run_preflight_checks
from fastapi import APIRouter, Query
from database import get_database_adapter

logger = logging.getLogger(__name__)

# Router will be created with dependencies injected from server.py
router = APIRouter(prefix="", tags=["System"])

# Cache for system status (TTL: 10 seconds)
_system_status_cache = None
_system_status_cache_time = None
SYSTEM_STATUS_CACHE_TTL = 10  # seconds

# Cache for ADW monitor (TTL: 5 seconds)
_adw_monitor_cache = None
_adw_monitor_cache_time = None
ADW_MONITOR_CACHE_TTL = 5  # seconds


def init_system_routes(health_service, service_controller, app_start_time):
    """
    Initialize system routes with service dependencies.

    This function is called from server.py to inject service dependencies.
    """

    @router.get("/health", response_model=HealthCheckResponse)
    async def health_check() -> HealthCheckResponse:
        """Health check endpoint with database status"""
        try:
            # Check database connection
            adapter = get_database_adapter()
            with adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()

            uptime = (datetime.now() - app_start_time).total_seconds()

            response = HealthCheckResponse(
                status="ok",
                database_connected=True,
                tables_count=len(tables),
                uptime_seconds=uptime
            )
            logger.info(f"[SUCCESS] Health check: OK, {len(tables)} tables, uptime: {uptime}s")
            return response
        except Exception as e:
            logger.error(f"[ERROR] Health check failed: {str(e)}")
            return HealthCheckResponse(
                status="error",
                database_connected=False,
                tables_count=0,
                uptime_seconds=0
            )

    @router.get("/system-status", response_model=SystemStatusResponse)
    async def get_system_status() -> SystemStatusResponse:
        """
        Comprehensive system health check - delegates to HealthService.

        This endpoint uses a 10-second cache to prevent excessive health checks.
        """
        global _system_status_cache, _system_status_cache_time

        # Check if cache is valid
        now = datetime.now()
        if _system_status_cache and _system_status_cache_time:
            cache_age = (now - _system_status_cache_time).total_seconds()
            if cache_age < SYSTEM_STATUS_CACHE_TTL:
                logger.debug(f"Returning cached system status (age: {cache_age:.1f}s)")
                return _system_status_cache

        # Cache miss or expired - fetch fresh data
        logger.debug("Cache miss - fetching fresh system status")
        status_data = await health_service.get_system_status()
        response = SystemStatusResponse(**status_data)

        # Update cache
        _system_status_cache = response
        _system_status_cache_time = now

        return response

    @router.get("/adw-monitor", response_model=AdwMonitorResponse)
    async def get_adw_monitor_status() -> AdwMonitorResponse:
        """
        Get real-time status of all ADW workflows.

        Aggregates workflow data from:
        - ADW state files (agents/*/adw_state.json)
        - Running process checks
        - Worktree existence validation
        - Phase progress calculation
        - Cost tracking

        Returns comprehensive status for monitoring active, paused, and recent workflows.

        This endpoint uses a 5-second cache to reduce file system overhead.
        """
        global _adw_monitor_cache, _adw_monitor_cache_time
        from core.adw_monitor import aggregate_adw_monitor_data

        # Check if cache is valid
        now = datetime.now()
        if _adw_monitor_cache and _adw_monitor_cache_time:
            cache_age = (now - _adw_monitor_cache_time).total_seconds()
            if cache_age < ADW_MONITOR_CACHE_TTL:
                logger.debug(f"Returning cached ADW monitor data (age: {cache_age:.1f}s)")
                return _adw_monitor_cache

        # Cache miss or expired - fetch fresh data
        logger.debug("Cache miss - fetching fresh ADW monitor data")
        try:
            monitor_data = aggregate_adw_monitor_data()
            response = AdwMonitorResponse(**monitor_data)

            # Update cache
            _adw_monitor_cache = response
            _adw_monitor_cache_time = now

            return response
        except Exception as e:
            logger.error(f"Error getting ADW monitor status: {e}")
            # Return empty response on error
            return AdwMonitorResponse(
                summary={"total": 0, "running": 0, "completed": 0, "failed": 0, "paused": 0},
                workflows=[],
                last_updated=datetime.now().isoformat()
            )

    @router.get("/adw-monitor/{adw_id}/health", response_model=AdwHealthCheckResponse)
    async def get_adw_health(adw_id: str) -> AdwHealthCheckResponse:
        """
        Get comprehensive health check for a specific ADW workflow.

        Performs health checks on:
        - Port allocation and conflicts
        - Worktree state and git status
        - State file validity and freshness
        - Process status and resource usage

        Returns detailed health information with warnings and recommendations.
        """
        from core.adw_monitor import scan_adw_states
        from core.health_checks import get_overall_health

        try:
            # Find the state for this ADW
            states = scan_adw_states()
            state = next((s for s in states if s.get("adw_id") == adw_id), None)

            if not state:
                # Return critical health if state not found
                return AdwHealthCheckResponse(
                    adw_id=adw_id,
                    overall_health="critical",
                    checks={
                        "ports": {"status": "critical", "warnings": ["ADW state not found"]},
                        "worktree": {"status": "critical", "warnings": ["ADW state not found"]},
                        "state_file": {"status": "critical", "warnings": ["ADW state not found"]},
                        "process": {"status": "critical", "warnings": ["ADW state not found"]}
                    },
                    warnings=["ADW state not found - workflow may not exist"],
                    checked_at=datetime.now().isoformat()
                )

            # Run comprehensive health checks
            health_result = get_overall_health(adw_id, state)
            return AdwHealthCheckResponse(**health_result)

        except Exception as e:
            logger.error(f"Error getting health check for {adw_id}: {e}")
            # Return error response
            return AdwHealthCheckResponse(
                adw_id=adw_id,
                overall_health="critical",
                checks={
                    "ports": {"status": "critical", "warnings": [f"Health check failed: {str(e)}"]},
                    "worktree": {"status": "critical", "warnings": [f"Health check failed: {str(e)}"]},
                    "state_file": {"status": "critical", "warnings": [f"Health check failed: {str(e)}"]},
                    "process": {"status": "critical", "warnings": [f"Health check failed: {str(e)}"]}
                },
                warnings=[f"Health check failed: {str(e)}"],
                checked_at=datetime.now().isoformat()
            )

    @router.post("/services/webhook/start")
    async def start_webhook_service() -> dict:
        """Start the webhook service - delegates to ServiceController"""
        return service_controller.start_webhook_service()

    @router.post("/services/cloudflare/restart")
    async def restart_cloudflare_tunnel() -> dict:
        """Restart the Cloudflare tunnel - delegates to ServiceController"""
        return service_controller.restart_cloudflare_tunnel()

    @router.get("/services/github-webhook/health")
    async def get_github_webhook_health() -> dict:
        """Check GitHub webhook health - delegates to ServiceController"""
        return service_controller.get_github_webhook_health()

    @router.post("/services/github-webhook/redeliver")
    async def redeliver_github_webhook() -> dict:
        """Redeliver GitHub webhook - delegates to ServiceController"""
        return service_controller.redeliver_github_webhook()

    @router.get("/preflight-checks")
    async def run_preflight_health_checks(skip_tests: bool = Query(False)) -> dict:
        """
        Run pre-flight checks before launching ADW workflows.

        Checks:
        - Critical test failures (PhaseCoordinator, ADW Monitor, Database)
        - Port availability (9100-9114, 9200-9214)
        - Git repository state (uncommitted changes)
        - Disk space (minimum 1GB free)
        - Python environment (uv availability)

        Args:
            skip_tests: Skip the test suite check (for faster checks)

        Returns:
            Pre-flight check results with pass/fail status and detailed diagnostics
        """
        try:
            result = run_preflight_checks(skip_tests=skip_tests)
            status = "✅ PASSED" if result["passed"] else "❌ FAILED"
            logger.info(f"Pre-flight checks: {status} ({result['total_duration_ms']}ms)")
            return result
        except Exception as e:
            logger.error(f"Pre-flight check error: {str(e)}")
            return {
                "passed": False,
                "blocking_failures": [{
                    "check": "System Error",
                    "error": str(e),
                    "fix": "Check logs for details"
                }],
                "warnings": [],
                "checks_run": [],
                "total_duration_ms": 0
            }
