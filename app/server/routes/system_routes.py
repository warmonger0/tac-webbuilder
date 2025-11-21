"""
System health and service control endpoints.
"""
import logging
from datetime import datetime

from core.data_models import (
    AdwMonitorResponse,
    HealthCheckResponse,
    SystemStatusResponse,
)
from fastapi import APIRouter
from utils.db_connection import get_connection

logger = logging.getLogger(__name__)

# Router will be created with dependencies injected from server.py
router = APIRouter(prefix="", tags=["System"])


def init_system_routes(health_service, service_controller, app_start_time):
    """
    Initialize system routes with service dependencies.

    This function is called from server.py to inject service dependencies.
    """

    @router.get("/api/health", response_model=HealthCheckResponse)
    async def health_check() -> HealthCheckResponse:
        """Health check endpoint with database status"""
        try:
            # Check database connection
            with get_connection() as conn:
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

    @router.get("/api/system-status", response_model=SystemStatusResponse)
    async def get_system_status() -> SystemStatusResponse:
        """Comprehensive system health check - delegates to HealthService"""
        status_data = await health_service.get_system_status()
        return SystemStatusResponse(**status_data)

    @router.get("/api/adw-monitor", response_model=AdwMonitorResponse)
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
        """
        from core.adw_monitor import aggregate_adw_monitor_data

        try:
            monitor_data = aggregate_adw_monitor_data()
            return AdwMonitorResponse(**monitor_data)
        except Exception as e:
            logger.error(f"Error getting ADW monitor status: {e}")
            # Return empty response on error
            return AdwMonitorResponse(
                summary={"total": 0, "running": 0, "completed": 0, "failed": 0, "paused": 0},
                workflows=[],
                last_updated=datetime.now().isoformat()
            )

    @router.post("/api/services/webhook/start")
    async def start_webhook_service() -> dict:
        """Start the webhook service - delegates to ServiceController"""
        return service_controller.start_webhook_service()

    @router.post("/api/services/cloudflare/restart")
    async def restart_cloudflare_tunnel() -> dict:
        """Restart the Cloudflare tunnel - delegates to ServiceController"""
        return service_controller.restart_cloudflare_tunnel()

    @router.get("/api/services/github-webhook/health")
    async def get_github_webhook_health() -> dict:
        """Check GitHub webhook health - delegates to ServiceController"""
        return service_controller.get_github_webhook_health()

    @router.post("/api/services/github-webhook/redeliver")
    async def redeliver_github_webhook() -> dict:
        """Redeliver GitHub webhook - delegates to ServiceController"""
        return service_controller.redeliver_github_webhook()
