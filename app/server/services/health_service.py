"""
Health Service Module

This module provides centralized health checking for all critical system services.
It monitors Backend API, Database, Webhook Service, Cloudflare Tunnel, GitHub Webhook,
and Frontend to provide real-time system status information.

The HealthService class encapsulates all health check logic that was previously
embedded in server.py, making it reusable, testable, and maintainable. It uses
async methods for non-blocking health checks and returns standardized ServiceHealth
objects for consistent status reporting.

Usage:
    from services.health_service import HealthService, ServiceStatus

    # Initialize with default configuration
    health_service = HealthService()

    # Initialize with custom configuration
    health_service = HealthService(
        db_path="custom/path/database.db",
        webhook_url="http://localhost:9000/webhook-status",
        frontend_url="http://localhost:3000"
    )

    # Check all services
    health_status = await health_service.check_all()
    for service_name, health in health_status.items():
        print(f"{service_name}: {health.status}")
"""

import asyncio
import json
import logging
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from enum import Enum

from core.data_models import ServiceHealth
from utils.db_connection import get_connection
from utils.process_runner import ProcessRunner

logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    """
    Standard status values for service health checks.

    This enum provides consistent status values across all health checks,
    making it easier to aggregate and compare service health states.

    Values:
        HEALTHY: Service is operating normally with no issues
        DEGRADED: Service is operational but experiencing issues or reduced performance
        UNHEALTHY: Service is not operational or experiencing critical failures
        UNKNOWN: Service status cannot be determined (e.g., timeout, unreachable)

    Example:
        >>> status = ServiceStatus.HEALTHY
        >>> print(status)
        healthy
        >>> print(status.value)
        healthy
    """

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthService:
    """
    Centralized health checking service for all system components.

    This service provides methods to check the health of all critical system
    services including backend API, database, webhook service, Cloudflare tunnel,
    GitHub webhook endpoint, and frontend. Each check returns a ServiceHealth
    object with status, message, and optional details.

    The service is designed to be used by the /api/system-status endpoint but
    can also be used by CLI tools, monitoring scripts, or other parts of the
    system that need health information.

    Attributes:
        db_path: Path to the SQLite database file
        webhook_url: URL of the webhook service to check
        cloudflare_tunnel_name: Name of the Cloudflare tunnel (optional)
        frontend_url: URL of the frontend application
        backend_port: Port number for the backend API

    Example:
        >>> health_service = HealthService()
        >>> results = await health_service.check_all()
        >>> print(results["backend_api"].status)
        healthy

        >>> # Custom configuration
        >>> health_service = HealthService(
        ...     db_path="/custom/db.db",
        ...     webhook_url="http://webhook:8001/health"
        ... )
    """

    def __init__(
        self,
        db_path: str = "db/database.db",
        webhook_url: str = "http://localhost:8001/webhook-status",
        cloudflare_tunnel_name: str | None = None,
        frontend_url: str = "http://localhost:5173",
        backend_port: str = "8000",
        app_start_time: datetime | None = None,
        github_repo: str = "warmonger0/tac-webbuilder"
    ):
        """
        Initialize the HealthService with configuration for all health check targets.

        Args:
            db_path: Path to the SQLite database file (default: "db/database.db")
            webhook_url: URL of the webhook service health endpoint
                        (default: "http://localhost:8001/webhook-status")
            cloudflare_tunnel_name: Name of the Cloudflare tunnel to check, or None
                                   if no tunnel is configured (default: None)
            frontend_url: URL of the frontend application
                         (default: "http://localhost:5173")
            backend_port: Port number for the backend API (default: "8000")
            app_start_time: When the application started (for uptime calculation)
            github_repo: GitHub repository for webhook checks

        Example:
            >>> # Development environment
            >>> hs = HealthService()

            >>> # Production environment
            >>> hs = HealthService(
            ...     db_path="/var/lib/tac/database.db",
            ...     webhook_url="https://webhook.example.com/health",
            ...     cloudflare_tunnel_name="tac-production",
            ...     frontend_url="https://app.example.com",
            ...     backend_port="8000"
            ... )
        """
        self.db_path = db_path
        self.webhook_url = webhook_url
        self.cloudflare_tunnel_name = cloudflare_tunnel_name
        self.frontend_url = frontend_url
        self.backend_port = backend_port
        self.app_start_time = app_start_time or datetime.now()
        self.github_repo = github_repo
        logger.info(
            f"HealthService initialized with db_path={db_path}, "
            f"webhook_url={webhook_url}, frontend_url={frontend_url}"
        )

    @staticmethod
    def _format_uptime(seconds: float) -> str:
        """Format uptime seconds into human-readable string"""
        td = timedelta(seconds=int(seconds))
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        if td.days > 0:
            return f"{td.days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    async def check_all(self) -> dict[str, ServiceHealth]:
        """
        Check the health of all system services in parallel.

        This method performs health checks on all configured services and returns
        a dictionary mapping service names to their health status. The checks are
        performed concurrently using asyncio.gather() to minimize total check time.

        Returns:
            Dictionary mapping service names to ServiceHealth objects. Keys include:
            - "backend_api": Backend FastAPI service
            - "database": SQLite database
            - "webhook": Webhook service
            - "cloudflare_tunnel": Cloudflare tunnel (if configured)
            - "github_webhook": GitHub webhook endpoint
            - "frontend": React frontend application

        Example:
            >>> health_service = HealthService()
            >>> results = await health_service.check_all()
            >>> for service_name, health in results.items():
            ...     print(f"{service_name}: {health.status} - {health.message}")
            backend_api: healthy - Running on port 8000
            database: healthy - 15 tables available
            ...

        Note:
            All checks are executed in parallel for optimal performance.
            Exceptions are caught per-check to prevent one failure from blocking others.
        """
        logger.debug("Running parallel health checks for all services")

        # Run all health checks in parallel using asyncio.gather
        # return_exceptions=True ensures one failure doesn't stop others
        results = await asyncio.gather(
            self._async_check_backend(),
            self._async_check_database(),
            self.check_webhook(),
            self._async_check_cloudflare(),
            self.check_github_webhook(),
            self.check_frontend(),
            return_exceptions=True
        )

        # Map results to service names
        service_names = [
            "backend_api",
            "database",
            "webhook",
            "cloudflare_tunnel",
            "github_webhook",
            "frontend"
        ]

        health_status = {}
        for name, result in zip(service_names, results, strict=False):
            if isinstance(result, Exception):
                # If a check raised an exception, return error status
                logger.error(f"Health check failed for {name}: {result}")
                health_status[name] = ServiceHealth(
                    name=name.replace("_", " ").title(),
                    status="error",
                    message=f"Check failed: {str(result)[:50]}"
                )
            else:
                health_status[name] = result

        return health_status

    async def _async_check_backend(self) -> ServiceHealth:
        """Async wrapper for check_backend"""
        return self.check_backend()

    async def _async_check_database(self) -> ServiceHealth:
        """Async wrapper for check_database"""
        return self.check_database()

    async def _async_check_cloudflare(self) -> ServiceHealth:
        """Async wrapper for check_cloudflare_tunnel"""
        return self.check_cloudflare_tunnel()

    def check_backend(self) -> ServiceHealth:
        """Check the health of the Backend API service"""
        try:
            uptime = (datetime.now() - self.app_start_time).total_seconds()
            return ServiceHealth(
                name="Backend API",
                status="healthy",
                uptime_seconds=uptime,
                uptime_human=self._format_uptime(uptime),
                message=f"Running on port {self.backend_port}",
                details={"port": self.backend_port}
            )
        except Exception as e:
            return ServiceHealth(
                name="Backend API",
                status="error",
                message=str(e)
            )

    def check_database(self) -> ServiceHealth:
        """Check the health of the SQLite database"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()

            return ServiceHealth(
                name="Database",
                status="healthy",
                message=f"{len(tables)} tables available",
                details={"tables_count": len(tables), "path": self.db_path}
            )
        except Exception as e:
            return ServiceHealth(
                name="Database",
                status="error",
                message=f"Connection failed: {str(e)}"
            )

    async def check_webhook(self) -> ServiceHealth:
        """Check the health of the Webhook Service"""
        try:
            with urllib.request.urlopen(self.webhook_url, timeout=2) as response:
                if response.status == 200:
                    webhook_data = json.loads(response.read().decode())
                    stats = webhook_data.get('stats', {})
                    total_received = stats.get('total_received', 0)
                    successful = stats.get('successful', 0)

                    return ServiceHealth(
                        name="Webhook Service",
                        status=webhook_data.get("status", "unknown"),
                        uptime_seconds=webhook_data.get("uptime", {}).get("seconds"),
                        uptime_human=webhook_data.get("uptime", {}).get("human"),
                        message=f"Port 8001 • {successful}/{total_received} webhooks processed",
                        details={
                            "port": 8001,
                            "webhooks_processed": f"{successful}/{total_received}",
                            "failed": stats.get('failed', 0)
                        }
                    )
                else:
                    return ServiceHealth(
                        name="Webhook Service",
                        status="error",
                        message=f"HTTP {response.status} on port 8001"
                    )
        except urllib.error.URLError:
            return ServiceHealth(
                name="Webhook Service",
                status="error",
                message="Not running (port 8001)"
            )
        except Exception as e:
            return ServiceHealth(
                name="Webhook Service",
                status="error",
                message=f"Error on port 8001: {str(e)}"
            )

    def check_cloudflare_tunnel(self) -> ServiceHealth:
        """Check the health of the Cloudflare Tunnel"""
        try:
            result = ProcessRunner.run(
                ["ps", "aux"],
                timeout=2
            )
            if "cloudflared tunnel run" in result.stdout:
                return ServiceHealth(
                    name="Cloudflare Tunnel",
                    status="healthy",
                    message="Tunnel is running"
                )
            else:
                return ServiceHealth(
                    name="Cloudflare Tunnel",
                    status="error",
                    message="Tunnel process not found"
                )
        except Exception as e:
            return ServiceHealth(
                name="Cloudflare Tunnel",
                status="unknown",
                message=f"Check failed: {str(e)}"
            )

    async def check_github_webhook(self) -> ServiceHealth:
        """Check the health of the GitHub Webhook endpoint"""
        try:
            webhook_id = os.environ.get("GITHUB_WEBHOOK_ID", "580534779")

            # Check recent webhook deliveries
            result = ProcessRunner.run_gh_command(
                ["api", f"repos/{self.github_repo}/hooks/{webhook_id}/deliveries", "--jq", ".[0].status_code"],
                timeout=3
            )

            if result.success and result.stdout.strip():
                status_code = int(result.stdout.strip())
                if status_code == 200:
                    return ServiceHealth(
                        name="GitHub Webhook",
                        status="healthy",
                        message=f"Latest delivery successful (HTTP {status_code})",
                        details={"webhook_url": "webhook.directmyagent.com"}
                    )
                elif status_code >= 500:
                    return ServiceHealth(
                        name="GitHub Webhook",
                        status="error",
                        message=f"Latest delivery failed (HTTP {status_code})",
                        details={"webhook_url": "webhook.directmyagent.com"}
                    )
                else:
                    return ServiceHealth(
                        name="GitHub Webhook",
                        status="degraded",
                        message=f"Latest delivery status: HTTP {status_code}",
                        details={"webhook_url": "webhook.directmyagent.com"}
                    )
            else:
                # Fallback: try to access webhook endpoint
                try:
                    with urllib.request.urlopen("https://webhook.directmyagent.com/health", timeout=3):
                        return ServiceHealth(
                            name="GitHub Webhook",
                            status="healthy",
                            message="Webhook endpoint accessible",
                            details={"webhook_url": "webhook.directmyagent.com"}
                        )
                except Exception:
                    return ServiceHealth(
                        name="GitHub Webhook",
                        status="unknown",
                        message="Cannot verify deliveries",
                        details={"webhook_url": "webhook.directmyagent.com"}
                    )
        except Exception as e:
            return ServiceHealth(
                name="GitHub Webhook",
                status="unknown",
                message=f"Check failed: {str(e)[:50]}"
            )

    async def check_frontend(self) -> ServiceHealth:
        """Check the health of the Frontend application"""
        try:
            frontend_port = os.environ.get("FRONTEND_PORT", "5173")
            with urllib.request.urlopen(f"http://localhost:{frontend_port}", timeout=2) as response:
                return ServiceHealth(
                    name="Frontend",
                    status="healthy" if response.status == 200 else "degraded",
                    message=f"Serving on port {frontend_port}",
                    details={"port": frontend_port}
                )
        except urllib.error.URLError:
            return ServiceHealth(
                name="Frontend",
                status="error",
                message="Not responding"
            )
        except Exception as e:
            return ServiceHealth(
                name="Frontend",
                status="unknown",
                message=str(e)
            )

    async def get_system_status(self) -> dict:
        """
        Get comprehensive system status for all services.

        Returns:
            Dictionary with overall_status, timestamp, services, and summary
        """
        services = await self.check_all()

        # Determine overall status
        statuses = [s.status for s in services.values()]
        if any(s == "error" for s in statuses):
            overall_status = "error"
        elif any(s == "degraded" for s in statuses):
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        # Summary
        healthy_count = sum(1 for s in statuses if s == "healthy")
        total_count = len(services)

        return {
            "overall_status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "services": services,
            "summary": {
                "healthy_services": healthy_count,
                "total_services": total_count,
                "health_percentage": round((healthy_count / total_count) * 100, 1) if total_count > 0 else 0
            }
        }
